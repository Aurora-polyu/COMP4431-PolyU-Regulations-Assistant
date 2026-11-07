"""Evidence-grounded answer service for the PolyU regulations assistant.

The service retrieves passages with Member 2's interface, asks the language
model to answer from those passages only, and validates every citation against
the retrieved set. It never falls back to unsupported content.
"""

import json
import os
import re

from src.citations import format_evidence, is_fixture, validate_citations
from src.llm_client import DeepSeekClient, LlmError

MAX_HISTORY_TURNS = 6
TOP_K = 5

FIXTURE_WARNING = (
    "[Development data: these passages are fictional. This is not a PolyU regulation.]"
)
NO_EVIDENCE_ANSWER = (
    "The provided 2026/27 Student Handbook does not appear to cover this question. "
    "Please check with the Academic Registry or your programme office."
)

SYSTEM_PROMPT = """You answer questions about PolyU academic regulations for taught programmes.

Use only the evidence passages below. They are the complete permitted source.
Rules:
- Do not use outside knowledge, guess, or invent rules, numbers, deadlines or form codes.
- Copy numbers, thresholds, dates and codes exactly as written.
- Do not decide whether a particular student is eligible. State the rule and its conditions, and point to the responsible office where the handbook does.
- If the evidence is incomplete, or two passages conflict, say so instead of resolving the conflict.
- If no passage answers the question, say the provided handbook does not cover it.
- Answer in plain English, at most about 150 words unless the question needs more.

EVIDENCE
{evidence}

Reply with a JSON object only:
{{"answer": "your answer", "citation_ids": ["<chunk_id>", "..."], "clarification_question": null}}

Citation IDs must be taken from the labels in square brackets above. Every factual sentence must be supported by at least one cited passage."""

REWRITE_PROMPT = """Rewrite the student's latest message as a standalone search query for a handbook search.
Resolve pronouns and references using the conversation. Keep names, codes and numbers.
Return only the query, on one line, with no quotes or explanation."""

JSON_RETRY_PROMPT = "Return only a valid JSON object matching the requested schema, with no code fences or extra text."


def _response(
    *,
    answer: str = "",
    citation_chunk_ids: list[str] | None = None,
    cited_chunks: list[dict] | None = None,
    clarification_question: str | None = None,
    status: str,
    evidence_source: str = "handbook",
) -> dict:
    return {
        "answer": answer,
        "citation_chunk_ids": citation_chunk_ids or [],
        "cited_chunks": cited_chunks or [],
        "clarification_question": clarification_question,
        "status": status,
        "evidence_source": evidence_source,
    }


def _normalise_history(history: object) -> list[dict]:
    turns: list[dict] = []
    if not isinstance(history, list):
        return turns
    for turn in history:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            turns.append({"role": role, "content": content.strip()})
    return turns[-MAX_HISTORY_TURNS:]


def _default_retriever():
    backend = os.environ.get("RETRIEVAL_BACKEND", "real").strip().lower()
    if backend == "mock":
        from src.mock_retriever import retrieve
    else:
        from src.retriever import retrieve
    return retrieve


def _fallback_query(question: str, history: list[dict]) -> str:
    previous = [turn["content"] for turn in history if turn["role"] == "user"][-2:]
    return " ".join(previous + [question])


def build_retrieval_query(question: str, history: list[dict], llm) -> str:
    """Turn a follow-up into a standalone query; fall back to concatenation."""
    if not any(turn["role"] == "user" for turn in history):
        return question
    transcript = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)
    messages = [
        {"role": "system", "content": REWRITE_PROMPT},
        {"role": "user", "content": f"{transcript}\n\nLatest message: {question}"},
    ]
    try:
        rewritten = llm.complete(messages, max_tokens=80).strip()
    except LlmError:
        return _fallback_query(question, history)
    rewritten = rewritten.splitlines()[0].strip().strip("\"'")
    if not rewritten or len(rewritten) > 300:
        return _fallback_query(question, history)
    return rewritten


def _build_messages(question: str, history: list[dict], chunks: list[dict]) -> list[dict]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(evidence=format_evidence(chunks))}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


def _parse_output(text: str) -> dict | None:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def _complete_json(llm, messages: list[dict]) -> dict | None:
    raw = llm.complete(messages)
    parsed = _parse_output(raw)
    if parsed is not None:
        return parsed
    retry_messages = messages + [
        {"role": "assistant", "content": raw},
        {"role": "user", "content": JSON_RETRY_PROMPT},
    ]
    return _parse_output(llm.complete(retry_messages))


def answer_question(
    question: str,
    history: list[dict] | None = None,
    *,
    retrieve=None,
    llm=None,
    top_k: int = TOP_K,
) -> dict:
    """Answer one question from retrieved handbook evidence.

    `retrieve` and `llm` are injectable for tests. Without them the service
    uses Member 2's retriever (see RETRIEVAL_BACKEND) and DeepSeek.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a nonblank string")
    question = question.strip()
    history = _normalise_history(history)

    if retrieve is None:
        try:
            retrieve = _default_retriever()
        except Exception as exc:
            return _response(
                status="error",
                answer=f"Retrieval is not available: {exc}. Install the retrieval dependencies and build the index.",
            )

    if llm is None:
        try:
            llm = DeepSeekClient()
        except LlmError as exc:
            return _response(status="error", answer=str(exc))

    query = build_retrieval_query(question, history, llm)
    try:
        chunks = retrieve(query, top_k=top_k)
    except ValueError:
        raise
    except Exception as exc:
        return _response(
            status="error",
            answer=(
                f"Retrieval failed: {exc}. Rebuild the index with "
                "`python scripts/build_index.py` and try again."
            ),
        )

    if not chunks:
        return _response(status="insufficient_evidence", answer=NO_EVIDENCE_ANSWER)

    messages = _build_messages(question, history, chunks)
    try:
        parsed = _complete_json(llm, messages)
    except LlmError as exc:
        return _response(status="error", answer=str(exc))

    if parsed is None:
        return _response(status="insufficient_evidence", answer=NO_EVIDENCE_ANSWER)

    answer = parsed.get("answer") if isinstance(parsed.get("answer"), str) else ""
    answer = answer.strip()
    clarification = parsed.get("clarification_question")
    if not isinstance(clarification, str) or not clarification.strip():
        clarification = None
    else:
        clarification = clarification.strip()

    citation_ids, cited_chunks = validate_citations(parsed.get("citation_ids"), chunks)
    source = "fixture" if is_fixture(chunks) else "handbook"

    if clarification:
        return _response(
            status="needs_clarification",
            answer=answer,
            citation_chunk_ids=citation_ids,
            cited_chunks=cited_chunks,
            clarification_question=clarification,
            evidence_source=source,
        )

    if not answer or not citation_ids:
        return _response(status="insufficient_evidence", answer=NO_EVIDENCE_ANSWER, evidence_source=source)

    if source == "fixture":
        answer = f"{FIXTURE_WARNING}\n\n{answer}"

    return _response(
        status="answered",
        answer=answer,
        citation_chunk_ids=citation_ids,
        cited_chunks=cited_chunks,
        evidence_source=source,
    )
