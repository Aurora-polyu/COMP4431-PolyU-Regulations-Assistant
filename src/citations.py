"""Citation handling for evidence-grounded answers.

Retrieved chunks follow the Member 2 contract: chunk_id, section,
printed_page, pdf_page and complete text.
"""

_FIXTURE_PREFIX = "sample_"


def evidence_block(chunk: dict) -> str:
    """Render one retrieved chunk for the prompt."""
    return (
        f"[{chunk['chunk_id']}] {chunk['section']} "
        f"(printed page {chunk['printed_page']})\n{chunk['text']}"
    )


def format_evidence(chunks: list[dict]) -> str:
    """Join all retrieved chunks into the evidence section of the prompt."""
    return "\n\n".join(evidence_block(chunk) for chunk in chunks)


def _clean_id(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    return raw.strip().strip("[]()\"' ").strip()


def validate_citations(raw_ids: object, retrieved: list[dict]) -> tuple[list[str], list[dict]]:
    """Keep only citations that exist in the retrieved set, deduplicated and in order."""
    by_id = {chunk["chunk_id"]: chunk for chunk in retrieved}
    ids: list[str] = []
    chunks: list[dict] = []
    seen: set[str] = set()
    if not isinstance(raw_ids, list):
        return ids, chunks
    for raw in raw_ids:
        chunk_id = _clean_id(raw)
        if not chunk_id or chunk_id in seen or chunk_id not in by_id:
            continue
        seen.add(chunk_id)
        ids.append(chunk_id)
        chunks.append(dict(by_id[chunk_id]))
    return ids, chunks


def is_fixture(chunks: list[dict]) -> bool:
    """True when every chunk comes from the fictional development fixture."""
    return bool(chunks) and all(
        str(chunk.get("chunk_id", "")).startswith(_FIXTURE_PREFIX) for chunk in chunks
    )
