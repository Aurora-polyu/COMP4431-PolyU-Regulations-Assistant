"""Local Stage E runner. Use only after authorized review of cases and scoring."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.conversation import answer_question
from src.llm_client import DeepSeekClient
from src.retriever import retrieve


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(case, actual_retrieve=retrieve, model=None):
    trace = []
    def record(query, top_k=5):
        started = time.perf_counter()
        chunks = actual_retrieve(query, top_k=top_k)
        trace.append({'query': query, 'seconds': time.perf_counter() - started, 'chunks': chunks})
        return chunks
    started = time.perf_counter()
    result = answer_question(case['question'], case['history'], retrieve=record, llm=model)
    elapsed = time.perf_counter() - started
    if result['status'] == 'error':
        result['answer'] = '[error details withheld; inspect configuration without recording credentials]'
    found = {c['chunk_id'] for t in trace for c in t['chunks'][:5]}
    items = case['evidence_items']
    recall = (sum(any(a['id'] in found for a in item['acceptable_chunks']) for item in items) / len(items)) if items and trace else None
    return {'id': case['id'], 'category': case['category'], 'elapsed_seconds': elapsed,
            'retrieval': trace, 'response': result, 'evidence_item_recall_at_5': recall,
            'manual_correctness': None, 'manual_claim_support': None, 'manual_abstention': None, 'review_notes': None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reviewer', required=True, help='Name or role of the person approving questions and scoring')
    p.add_argument('--reviewed-sha256', required=True, help='SHA-256 of the reviewed question JSON')
    p.add_argument('--output', required=True, help='New, local ignored JSONL output path')
    args = p.parse_args()
    source = ROOT / 'data/stage_e_questions.json'
    output = Path(args.output).resolve()
    if not args.reviewer.strip() or digest(source) != args.reviewed_sha256:
        p.error('Reviewer and exact reviewed question-file SHA-256 are required.')
    if not output.is_relative_to(ROOT / 'data'):
        p.error('Place results in the ignored local data directory.')
    if os.environ.get('RETRIEVAL_BACKEND', 'real').lower() != 'real':
        p.error('The real retriever is required.')
    index = Path(os.environ['RETRIEVAL_INDEX_DIR']).resolve()
    manifest = json.loads((index / 'manifest.json').read_text())
    questions = json.loads(source.read_text())
    if digest(ROOT / 'data/handbook.pdf') != questions['source_pdf_sha256'] or digest(ROOT / 'data/chunks.jsonl') != questions['chunks_sha256']:
        p.error('Source hashes do not match the reviewed question set.')
    if manifest['source_sha256'] != questions['chunks_sha256'] or Path(manifest['source_path']).resolve() != (ROOT / 'data/chunks.jsonl').resolve():
        p.error('Index is not tied to the approved local chunks.')
    if len(questions['cases']) != 30:
        p.error('Expected exactly 30 reviewed cases.')
    client = DeepSeekClient()
    metadata = {'type':'metadata', 'timestamp_utc':datetime.now(timezone.utc).isoformat(), 'reviewer':args.reviewer,
                'questions_sha256':digest(source), 'pdf_sha256':questions['source_pdf_sha256'], 'chunks_sha256':questions['chunks_sha256'],
                'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'git_status':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),
                'working_tree_diff_sha256':hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=ROOT)).hexdigest(),
                'source_file_sha256':{str(p.relative_to(ROOT)):digest(p) for p in (ROOT / 'src/retriever.py', ROOT / 'src/conversation.py')},
                'index_dir':str(index), 'manifest':manifest, 'llm_model':client.model, 'python':sys.version,
                'platform':platform.platform(), 'pip_freeze':subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines(),
                'timing':'First case is cold process; subsequent cases warm. Times include answer service and network; no browser rendering.',
                'note':'Manual correctness, claim support and abstention remain unscored until review.'}
    with output.open('x', encoding='utf-8') as f:
        def write(obj):
            f.write(json.dumps(obj, ensure_ascii=False)+'\n'); f.flush()
        write(metadata)
        for case in questions['cases']:
            try:
                result = run_case(case, model=client)
            except Exception:
                result = {'id':case['id'], 'category':case['category'], 'runner_error':'Unexpected exception; details withheld', 'manual_correctness':None}
            write({'type':'case', **result})
            print(case['id'], result.get('response',{}).get('status','runner_error'), flush=True)

if __name__ == '__main__':
    main()
