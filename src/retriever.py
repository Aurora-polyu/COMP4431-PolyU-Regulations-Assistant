"""Local hybrid retrieval over a previously built Chroma index."""

import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path

from src.contracts import RetrievalError, RetrievedChunk

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = ROOT / "chroma_db"
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
COLLECTION = "chunks"
FORMAT_VERSION = 2


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def validate_chunks(chunks: object) -> list[RetrievedChunk]:
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("Chunk input must be a nonempty JSON array")
    required = {"chunk_id", "section", "printed_page", "pdf_page", "text"}
    seen = set()
    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict) or set(chunk) != required:
            raise ValueError(f"Chunk {i} must contain exactly {sorted(required)}")
        for field in ("chunk_id", "section", "text"):
            if not isinstance(chunk[field], str) or not chunk[field].strip():
                raise ValueError(f"Chunk {i}: {field} must be a nonblank string")
        for field in ("printed_page", "pdf_page"):
            if type(chunk[field]) is not int or chunk[field] <= 0:
                raise ValueError(f"Chunk {i}: {field} must be a positive integer")
        if chunk["chunk_id"] in seen:
            raise ValueError(f"Duplicate chunk_id: {chunk['chunk_id']}")
        seen.add(chunk["chunk_id"])
    return chunks


def rrf(rankings: list[list[str]], limit: int, k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen = set()
        for rank, chunk_id in enumerate(ranking, 1):
            if chunk_id not in seen:
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)
                seen.add(chunk_id)
    return sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))[:limit]


def load_model(name: str, *, local_only: bool, revision: str | None = None):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name, local_files_only=local_only, revision=revision)


def model_revision(model) -> str:
    """Obtain the immutable Hub commit used by the loaded transformer."""
    try:
        revision = model._first_module().auto_model.config._commit_hash
    except AttributeError as exc:
        raise ValueError("Embedding model does not expose a Hub commit; use a supported Hugging Face model") from exc
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Embedding model has no immutable Hub commit; use a supported Hugging Face model")
    return revision


def encode_documents(model, texts: list[str]):
    return model.encode(texts, normalize_embeddings=True).tolist()


def encode_query(model, query: str):
    return model.encode([QUERY_PREFIX + query], normalize_embeddings=True).tolist()[0]


def _manifest(index_dir: Path, model_name: str) -> tuple[dict, str]:
    try:
        raw = (index_dir / "manifest.json").read_text(encoding="utf-8")
        manifest = json.loads(raw)
        if (manifest["format_version"] != FORMAT_VERSION or manifest["model"] != model_name
                or manifest["query_prefix"] != QUERY_PREFIX):
            raise ValueError("index format or embedding configuration differs")
        source = Path(manifest["source_path"])
        if file_hash(source) != manifest["source_sha256"]:
            raise ValueError("source chunks have changed")
        revision = manifest["model_revision"]
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("invalid model revision")
        generation = manifest["generation"]
        if not isinstance(generation, str) or not re.fullmatch(r"[0-9a-f]{32}", generation):
            raise ValueError("invalid index generation")
        return manifest, raw
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RetrievalError(f"Index at {index_dir} is missing, stale, or incompatible ({exc}). Rebuild with python scripts/build_index.py using the intended chunks and model.") from exc


class HybridRetriever:
    def __init__(self, index_dir: Path, manifest: dict):
        try:
            import chromadb
            from rank_bm25 import BM25Plus
            self.client = chromadb.PersistentClient(path=str(index_dir / manifest["generation"]))
            self.collection = self.client.get_collection(COLLECTION, embedding_function=None)
            data = self.collection.get(include=["documents", "metadatas"])
            chunks = [dict(meta, chunk_id=chunk_id, text=text) for chunk_id, meta, text in zip(data["ids"], data["metadatas"], data["documents"])]
            validate_chunks(chunks)
            if len(chunks) != manifest["count"]:
                raise ValueError("indexed chunk count differs from manifest")
            self.chunks = {c["chunk_id"]: c for c in chunks}
            self.ids = sorted(self.chunks)
            self.tokens = [tokenize(self.chunks[i]["text"]) for i in self.ids]
            self.bm25 = BM25Plus(self.tokens) if any(self.tokens) else None
            self.model = load_model(manifest["model"], local_only=True, revision=manifest["model_revision"])
            if model_revision(self.model) != manifest["model_revision"]:
                raise ValueError("loaded embedding model revision differs from index")
        except Exception as exc:
            raise RetrievalError(f"Could not load index or local embedding model at {index_dir}: {exc}. Rebuild the index or install the documented dependencies.") from exc

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        count = min(len(self.ids), max(20, top_k))
        try:
            result = self.collection.query(query_embeddings=[encode_query(self.model, query)], n_results=count, include=[])
            vector_ids = result["ids"][0]
            query_tokens = tokenize(query)
            scores = self.bm25.get_scores(query_tokens) if self.bm25 else [0.0] * len(self.ids)
            # Exclude documents with no matching terms, even when their BM25 score is zero.
            keyword_ids = sorted((i for i, tokens in enumerate(self.tokens) if set(query_tokens) & set(tokens)), key=lambda i: (-scores[i], self.ids[i]))[:count]
            fused = rrf([vector_ids, [self.ids[i] for i in keyword_ids]], min(top_k, len(self.ids)))
            return [self.chunks[chunk_id].copy() for chunk_id in fused]
        except Exception as exc:
            raise RetrievalError(f"Retrieval failed: {exc}. Check the index and rebuild if necessary.") from exc


@lru_cache(maxsize=4)
def _load(index_dir: str, manifest_raw: str) -> HybridRetriever:
    return HybridRetriever(Path(index_dir), json.loads(manifest_raw))


def retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Return ranked passages; configure the index via RETRIEVAL_INDEX_DIR."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if not query.strip():
        return []
    index_dir = Path(os.environ.get("RETRIEVAL_INDEX_DIR", str(DEFAULT_INDEX))).expanduser().resolve()
    model_name = os.environ.get("RETRIEVAL_MODEL", DEFAULT_MODEL)
    _, raw = _manifest(index_dir, model_name)
    return _load(str(index_dir), raw).search(query, top_k)
