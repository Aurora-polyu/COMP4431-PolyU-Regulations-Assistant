"""Build a new immutable local Chroma generation and atomically publish it."""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.retriever import (COLLECTION, DEFAULT_INDEX, DEFAULT_MODEL, FORMAT_VERSION,
                           QUERY_PREFIX, ROOT, encode_documents, file_hash,
                           load_model, model_revision, validate_chunks)


def build_index(source: Path, index_dir: Path, model_name: str = DEFAULT_MODEL) -> None:
    import chromadb
    source, index_dir = source.expanduser().resolve(), index_dir.expanduser().resolve()
    # Hash the exact bytes parsed, and check again before publishing.
    raw = source.read_bytes()
    import hashlib
    source_hash = hashlib.sha256(raw).hexdigest()
    chunks = validate_chunks(json.loads(raw))
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
    parser.add_argument("--chunks", type=Path, default=ROOT / "data/sample_chunks.json")
    parser.add_argument("--index-dir", type=Path, default=Path(os.environ.get("RETRIEVAL_INDEX_DIR", str(DEFAULT_INDEX))))
    parser.add_argument("--model", default=os.environ.get("RETRIEVAL_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()
    try:
        build_index(args.chunks, args.index_dir, args.model)
    except Exception as exc:
        parser.exit(1, f"Index build failed: {exc}\n")
    print(f"Built index at {args.index_dir.resolve()} from {args.chunks.resolve()}")


if __name__ == "__main__":
    main()
