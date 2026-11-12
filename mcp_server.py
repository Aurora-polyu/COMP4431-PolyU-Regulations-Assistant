"""Local MCP server (stdio) exposing read-only search over the PolyU Student Handbook.

Run:  RETRIEVAL_INDEX_DIR=/abs/path/handbook-index .venv/bin/python mcp_server.py
Test: .venv/bin/mcp dev mcp_server.py
Setup for Claude Desktop, Claude Code and Codex: docs/mcp.md.
"""

import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from src.retriever import retrieve

# stdout carries the MCP protocol, so all logs go to stderr.
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("handbook-mcp")

CHUNKS_PATH = Path(__file__).resolve().parent / "data" / "chunks.jsonl"
CHECK_OFFICIAL = (
    "Passages come from the PolyU Student Handbook. Always tell the user to confirm "
    "details in the official handbook and with the responsible office (department or Academic Registry)."
)
HOW_TO_CITE = (
    "Cite the section and printed page inline. End the answer with a 'Sources' list: one line per "
    "passage you used, as 'Section <section>, p. <printed_page> (PDF p. <pdf_page>): \"<short verbatim "
    "quote from the passage text>\"'. Quote the handbook exactly; do not paraphrase inside the quotes."
)
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


@asynccontextmanager
async def warm_up(_server):
    # Load the embedding model and index now; otherwise the first search takes about 9 s.
    log.info("Loading retrieval model and index...")
    retrieve("warm up", top_k=1)
    log.info("Ready.")
    yield {}


server = MCPServer("polyu-handbook", instructions=HOW_TO_CITE + " " + CHECK_OFFICIAL, lifespan=warm_up)


@server.tool(annotations=READ_ONLY, description=(
    "Search the PolyU Student Handbook and return the 5 most relevant passages with their "
    "section and page numbers. " + HOW_TO_CITE + " " + CHECK_OFFICIAL
))
def search_handbook(query: str) -> list[dict]:
    if not query.strip():
        raise ToolError("query must not be empty")
    return [
        {k: c[k] for k in ("chunk_id", "section", "printed_page", "pdf_page", "text")}
        for c in retrieve(query, top_k=5)
    ]


def _section_id(section: str) -> str:
    return section.split()[0]


@server.tool(annotations=READ_ONLY, description=(
    "Return every passage of one handbook section, in order. Pass a section id such as '4.H' "
    "(Deferment of Study) or '4' for a whole chapter. " + HOW_TO_CITE + " " + CHECK_OFFICIAL
))
def get_section(section: str) -> list[dict]:
    chunks = [json.loads(line) for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    found = [c for c in chunks if c["section"].startswith(section.strip())]
    if found:
        return found
    ids = list(dict.fromkeys(_section_id(c["section"]) for c in chunks))
    chapter = section.strip().split(".")[0]
    nearby = [i for i in ids if i.split(".")[0] == chapter] or ids
    raise ToolError(f"No section starts with {section!r}. Valid ids include: {', '.join(nearby)}")


if __name__ == "__main__":
    server.run()
