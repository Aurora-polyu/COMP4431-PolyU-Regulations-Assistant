"""Build a new immutable local Chroma generation and atomically publish it."""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.retriever import (COLLECTION, DEFAULT_INDEX, DEFAULT_MODEL, FORMAT_VERSION,
                           QUERY_PREFIX, ROOT, encode_documents, file_hash, is_sample_hash,
                           load_model, model_revision, validate_chunks)


def parse_chunks(raw: bytes, source: Path):
    """Parse a JSON array or UTF-8 JSON Lines and validate its records."""
    text = raw.decode("utf-8")
    if source.suffix.lower() == ".jsonl":
        chunks = []
        for number, line in enumerate(text.splitlines(), 1):
            if line.strip():
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON Lines at line {number}: {exc.msg}") from exc
    else:
        chunks = json.loads(text)
    return validate_chunks(chunks)


def build_index(source: Path, index_dir: Path, model_name: str = DEFAULT_MODEL) -> None:
    source, index_dir = source.expanduser().resolve(), index_dir.expanduser().resolve()
    # Hash the exact bytes parsed, and check again before publishing.
    raw = source.read_bytes()
    import hashlib
    source_hash = hashlib.sha256(raw).hexdigest()
    if is_sample_hash(source_hash):
        if index_dir == DEFAULT_INDEX.resolve():
            raise ValueError("The fictional sample must use a separate index directory")
        manifest_path = index_dir / "manifest.json"
        if manifest_path.exists():
            try:
                existing = json.loads(manifest_path.read_text(encoding="utf-8"))
                if not is_sample_hash(existing["source_sha256"]):
                    raise ValueError("The fictional sample cannot replace an existing non-sample index")
            except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError("Cannot verify the existing index; choose a separate sample directory") from exc
    chunks = parse_chunks(raw, source)
    import chromadb
    model = load_model(model_name, local_only=False)
    revision = model_revision(model)
    embeddings = encode_documents(model, [chunk["text"] for chunk in chunks])
    index_dir.mkdir(parents=True, exist_ok=True)
    generation = uuid.uuid4().hex
    generation_dir = index_dir / generation
    try:
        client = chromadb.PersistentClient(path=str(generation_dir))
        collection = client.create_collection(COLLECTION, embedding_function=None, metadata={"hnsw:space": "cosine"})
        collection.add(ids=[c["chunk_id"] for c in chunks], documents=[c["text"] for c in chunks],
                       metadatas=[{k: c[k] for k in ("section", "printed_page", "pdf_page")} for c in chunks], embeddings=embeddings)
        if file_hash(source) != source_hash:
            raise ValueError("Source changed during indexing; rerun the build")
        manifest = {"format_version": FORMAT_VERSION, "model": model_name, "query_prefix": QUERY_PREFIX,
                    "model_revision": revision, "source_path": str(source), "source_sha256": source_hash, "generation": generation, "count": len(chunks)}
        temporary = index_dir / f".{generation}.json"
        temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, index_dir / "manifest.json")
    except Exception:
        # Unpublished generations are safe to remove; published generations may be in use.
        import shutil
        shutil.rmtree(generation_dir, ignore_errors=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=ROOT / "data/chunks.jsonl")
    parser.add_argument("--index-dir", type=Path, default=None)
    parser.add_argument("--model", default=os.environ.get("RETRIEVAL_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()
    if not args.chunks.expanduser().is_file():
        parser.exit(1, f"Chunk file not found: {args.chunks}. Obtain Member 1's handoff or specify --chunks /path/to/chunks.jsonl.\n")
    if is_sample_hash(file_hash(args.chunks.expanduser())) and args.index_dir is None:
        parser.error("The fictional sample requires an explicit --index-dir separate from the handbook index")
    args.index_dir = args.index_dir or Path(os.environ.get("RETRIEVAL_INDEX_DIR", str(DEFAULT_INDEX)))
    try:
        build_index(args.chunks, args.index_dir, args.model)
    except Exception as exc:
        parser.exit(1, f"Index build failed: {exc}\n")
    print(f"Built index at {args.index_dir.resolve()} from {args.chunks.resolve()}")


if __name__ == "__main__":
    main()
