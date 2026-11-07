"""Verify the reviewed layout annotations survive into the evidence source."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from stage_a_table_annotations import ANNOTATIONS, annotate
from citations import evidence_block
from src.conversation import answer_question


def test_promoted_chunks_include_reviewed_layout_and_keep_ids():
    chunks = [json.loads(line) for line in (ROOT / "data/chunks.jsonl").read_text().splitlines()]
    by_id = {c["chunk_id"]: c for c in chunks}
    assert len(by_id) == len(chunks)
    for key, annotation in ANNOTATIONS.items():
        assert annotation in by_id[key]["section"]
        assert annotation in evidence_block(by_id[key])
    assert "local full-time HK$47,000/academic year" in by_id["sec8_H_002"]["section"]
    assert "Faculty of Business doctoral programmes HK$1,200" in by_id["sec8_I_001"]["section"]
    assert "squash-court row continues the Kwong On" in by_id["sec12_C_010"]["section"]
    assert "Saturday 9.00 am–6.00 pm, Sunday and public holiday closed" in by_id["sec12_F_001"]["section"]
    assert "Saturday 11.00 am–8.30 pm, Sunday and public holiday closed" in by_id["sec12_F_002"]["section"]
    emergency = evidence_block(by_id["app3_H_001"])
    for pair in ("24-Hour Campus Emergency Hotline: 2766 7999", "Campus Control Centre: 2766 7666", "Health and Safety Office: 3400 8396", "University Health Service: 2766 5433"):
        assert pair in emergency
    clinic = evidence_block(by_id["sec12_D_002"])
    for pair in ("Medical Clinic: 2766 5433, Room A001", "Traditional Chinese Medicine Clinic: 2766 5553, Room A125", "Dental Clinic: 2330 9414, Room GH020"):
        assert pair in clinic


def test_missing_and_duplicate_annotations_are_rejected():
    with pytest.raises(ValueError, match="missing expected chunks"):
        annotate([])
    chunks = [json.loads(line) for line in (ROOT / "data/chunks.jsonl").read_text().splitlines()]
    with pytest.raises(ValueError, match="already annotated"):
        annotate(chunks)


def test_emergency_question_receives_both_source_checked_numbers():
    chunks = [json.loads(line) for line in (ROOT / "data/chunks.jsonl").read_text().splitlines()]
    contact = next(c for c in chunks if c["chunk_id"] == "app3_H_001")

    class InspectingModel:
        def complete(self, messages, **kwargs):
            evidence = "\n".join(m["content"] for m in messages)
            assert "24-Hour Campus Emergency Hotline: 2766 7999" in evidence
            assert "Campus Control Centre: 2766 7666" in evidence
            return json.dumps({"answer": "The two numbers differ.", "citation_ids": ["app3_H_001"], "clarification_question": None})

    result = answer_question(
        "What are the campus emergency and control centre numbers?",
        retrieve=lambda query, top_k=5: [contact], llm=InspectingModel(),
    )
    assert result["status"] == "answered"
    assert result["cited_chunks"][0]["pdf_page"] == 137
    assert result["cited_chunks"][0]["section"] == contact["section"]
