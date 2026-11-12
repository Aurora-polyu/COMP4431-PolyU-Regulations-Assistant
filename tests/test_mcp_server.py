import json

import pytest

import mcp_server
from mcp.server.mcpserver.exceptions import ToolError

CHUNKS = [
    {"chunk_id": "sec4F_001", "section": "4.F Leave of Absence", "printed_page": 10, "pdf_page": 18, "text": "Leave text"},
    {"chunk_id": "sec4H_001", "section": "4.H Deferment of Study*", "printed_page": 11, "pdf_page": 19, "text": "Defer one"},
    {"chunk_id": "sec4H_002", "section": "4.H Deferment of Study*", "printed_page": 12, "pdf_page": 20, "text": "Defer two"},
    {"chunk_id": "sec5A_001", "section": "5.A Subject Registration", "printed_page": 20, "pdf_page": 28, "text": "Register"},
]


@pytest.fixture
def chunks_file(tmp_path, monkeypatch):
    path = tmp_path / "chunks.jsonl"
    path.write_text("\n".join(json.dumps(c) for c in CHUNKS), encoding="utf-8")
    monkeypatch.setattr(mcp_server, "CHUNKS_PATH", path)


def test_search_handbook_returns_cited_passages(monkeypatch):
    calls = []

    def fake_retrieve(query, top_k):
        calls.append((query, top_k))
        return [dict(CHUNKS[1], score=0.9)]

    monkeypatch.setattr(mcp_server, "retrieve", fake_retrieve)
    assert mcp_server.search_handbook("How do I defer my study?") == [CHUNKS[1]]
    assert calls == [("How do I defer my study?", 5)]


def test_search_handbook_rejects_empty_query():
    with pytest.raises(ToolError):
        mcp_server.search_handbook("   ")


def test_get_section_returns_chunks_in_order(chunks_file):
    assert [c["chunk_id"] for c in mcp_server.get_section("4.H")] == ["sec4H_001", "sec4H_002"]
    assert len(mcp_server.get_section("4")) == 3


def test_get_section_unknown_lists_nearby_ids(chunks_file):
    with pytest.raises(ToolError) as err:
        mcp_server.get_section("4.Z")
    assert "4.F" in str(err.value) and "4.H" in str(err.value) and "5.A" not in str(err.value)
