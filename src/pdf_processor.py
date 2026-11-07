"""Page-aware text extraction for the PolyU 2026/27 Student Handbook.

Member 1 — Handbook Processing & Data (COMP4431 group project).

This module turns the supplied handbook PDF into an ordered list of
:class:`PageRecord` objects.  Each body page carries its printed (footer) page
number, its 1-based PDF page number, and a list of paragraphs annotated with the
handbook section they belong to.

Design notes live in ``docs/member1_protocol.md``.  Read that first; the code
below implements it literally.

The module is deliberately free of network, clock and randomness so that the
same PDF always produces the same output.
"""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path

try:  # PyMuPDF >= 1.24 exposes the modern module name.
    import pymupdf
except ImportError as exc:  # pragma: no cover - dependency error path
    raise ImportError(
        "PyMuPDF is required for handbook processing. "
        "Install it with: pip install 'pymupdf>=1.24'"
    ) from exc


# --------------------------------------------------------------------------- #
# Tunables that describe the physical layout of the supplied file
# --------------------------------------------------------------------------- #

#: Everything at or below this distance from the bottom of the page is footer
#: territory.  Printed page numbers live at roughly y = 810-831 on an 842 pt page.
FOOTER_ZONE_PT = 70.0

#: Font size at or above which a line is a chapter-level heading (22 pt in this file).
CHAPTER_HEADING_MIN_SIZE = 21.0

#: Font size at or above which a line is a subsection heading (16 pt in this file).
SUBSECTION_HEADING_MIN_SIZE = 15.5

#: Maximum vertical gap (pt) between two heading lines that belong to one wrapped
#: heading.  Wrapped headings in this file are 17-19 pt apart.
HEADING_LINE_MAX_GAP_PT = 30.0

#: Lines that start with one of these markers keep their own line when joined.
_BULLET_RE = re.compile(r"^\s*(?:[•◦▪‣·]|[a-zA-Z]\)|\d+\)|[ivxlcdm]+\.)\s")

_SPACE_FIXES = {
    " ": " ",  # no-break space
    " ": " ",  # figure space
    " ": " ",  # narrow no-break space
    "​": "",   # zero-width space
    "‌": "",   # zero-width non-joiner
    "‍": "",   # zero-width joiner
    "﻿": "",   # byte-order mark
}

#: Prefix normalisation: "A.Introduction" -> "A. Introduction",
#: "10.Notes..." -> "10. Notes...", "Appendix 1.Something" -> "Appendix 1. Something".
_PREFIX_NO_SPACE_RE = re.compile(r"^(Appendix\s+\d+|\d+|[A-Z])\.(?=\S)")

_CHAPTER_RE = re.compile(r"^(\d+)\.\s*(.+)$")
_APPENDIX_RE = re.compile(r"^Appendix\s+(\d+)\.\s*(.+)$")
_SUBSECTION_RE = re.compile(r"^([A-Z])\.\s*(.+)$")


class HandbookFormatError(RuntimeError):
    """Raised when the PDF does not match the layout this pipeline expects."""


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Paragraph:
    """One paragraph of handbook text, tagged with its section."""

    section_key: str
    section_label: str
    text: str
    is_heading: bool = False


@dataclass(frozen=True)
class PageRecord:
    """One numbered body page of the handbook."""

    pdf_page: int
    printed_page: int
    paragraphs: tuple[Paragraph, ...]


@dataclass(frozen=True)
class DocumentModel:
    """The extracted handbook."""

    pages: tuple[PageRecord, ...]
    front_matter_pages: tuple[int, ...]
    divider_pages: tuple[int, ...]
    pdf_page_count: int
    title: str

    @property
    def max_printed_page(self) -> int:
        return max(page.printed_page for page in self.pages)


@dataclass(frozen=True)
class _Line:
    text: str
    size: float
    top: float
    bottom: float

    @property
    def is_blank(self) -> bool:
        return not self.text.strip()

    @property
    def is_chapter_heading(self) -> bool:
        return self.size >= CHAPTER_HEADING_MIN_SIZE

    @property
    def is_subsection_heading(self) -> bool:
        return self.size >= SUBSECTION_HEADING_MIN_SIZE


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def _normalise_inline(text: str) -> str:
    """Normalise a single line of extracted text."""

    for old, new in _SPACE_FIXES.items():
        text = text.replace(old, new)
    text = text.replace("\t", " ")
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _join_lines(lines: list[str]) -> str:
    """Join the physical lines of one paragraph.

    A hyphen at the end of a line is kept, so a word broken across lines becomes
    ``non-refundable`` rather than ``nonrefundable``.  Bullet / list markers start
    a new line so that lists stay readable.
    """

    out = ""
    for raw in lines:
        line = _normalise_inline(raw)
        if not line:
            continue
        if not out:
            out = line
        elif out.endswith("-"):
            out += line
        elif _BULLET_RE.match(line):
            out += "\n" + line
        else:
            out += " " + line
    return out


def _footer_number(page) -> int | None:
    """Return the printed page number in the footer, or ``None``."""

    height = page.rect.height
    candidates: list[tuple[float, int]] = []
    for block in page.get_text("blocks"):
        text = block[4].strip()
        if block[3] >= height - FOOTER_ZONE_PT and re.fullmatch(r"\d{1,3}", text):
            candidates.append((block[3], int(text)))
    if not candidates:
        return None
    return max(candidates)[1]


def _page_lines(page) -> list[_Line]:
    """Return every text line on the page, in the order the PDF stores them."""

    lines: list[_Line] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type", 0) != 0:  # 1 == image block
            continue
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            text = "".join(s["text"] for s in line.get("spans", []))
            size = max((s["size"] for s in spans), default=0.0)
            x0, y0, _x1, y1 = line["bbox"]
            lines.append(_Line(text=text, size=size, top=y0, bottom=y1))
    return lines


def _strip_footer_lines(lines: list[_Line], page_height: float) -> list[_Line]:
    """Drop the printed page-number line from the page content."""

    kept = []
    for line in lines:
        if line.bottom >= page_height - FOOTER_ZONE_PT and re.fullmatch(
            r"\s*\d{1,3}\s*", line.text
        ):
            continue
        kept.append(line)
    return kept


# --------------------------------------------------------------------------- #
# Page map
# --------------------------------------------------------------------------- #


def _detect_page_map(doc) -> tuple[dict[int, int], list[int], list[int]]:
    """Work out which PDF pages are numbered body pages.

    Returns ``(body_pages, front_matter_pages, divider_pages)`` where
    ``body_pages`` maps ``pdf_page -> printed_page``.

    The rule (see protocol §3.3) is: accept a page when its footer equals the next
    expected printed number *and* the following page does not repeat that number.
    The second condition rejects decorative numerals on divider pages, e.g. PDF
    127 displays "108" in its artwork while PDF 128 is the real printed page 108.
    """

    page_count = doc.page_count
    candidates = {p: _footer_number(doc[p - 1]) for p in range(1, page_count + 1)}

    start = None
    for p in range(1, page_count + 1):
        if candidates.get(p) == 1:
            start = p
            break
    if start is None:
        raise HandbookFormatError(
            "Could not find the start of the numbered body pages: no page has "
            "footer '1'. The PDF may be a different edition."
        )

    body: dict[int, int] = {}
    dividers: list[int] = []
    expected = 1
    for p in range(start, page_count + 1):
        number = candidates.get(p)
        if number is None:
            # Unnumbered page between body pages: a chapter divider.
            dividers.append(p)
            continue
        repeats_next = candidates.get(p + 1) == number
        if number == expected and not repeats_next:
            body[p] = number
            expected += 1
        else:
            dividers.append(p)

    printed = list(body.values())
    if printed != list(range(1, len(printed) + 1)):
        raise HandbookFormatError(
            f"Printed page numbers are not a contiguous 1..N sequence: {printed[:20]}..."
        )

    front_matter = list(range(1, start))
    return body, front_matter, dividers


def _toc_divider_pages(doc) -> list[int]:
    """Chapter divider pages, taken from level-1 entries of the embedded outline."""

    try:
        toc = doc.get_toc(simple=True)
    except Exception:  # pragma: no cover - defensive
        return []
    return sorted({page for level, _title, page in toc if level == 1 and page >= 8})


# --------------------------------------------------------------------------- #
# Section parsing
# --------------------------------------------------------------------------- #


def _parse_heading(
    text: str, current_chapter: tuple[str, str] | None
) -> tuple[str, str, str] | None:
    """Parse a heading line into ``(kind, section_key, section_label)``.

    ``kind`` is ``"chapter"``, ``"appendix"`` or ``"subsection"``.
    """

    cleaned = _PREFIX_NO_SPACE_RE.sub(r"\1. ", text).strip()

    match = _APPENDIX_RE.match(cleaned)
    if match:
        number, title = match.group(1), match.group(2).strip()
        return "appendix", f"app{number}", f"Appendix {number}. {title}"

    match = _CHAPTER_RE.match(cleaned)
    if match:
        number, title = match.group(1), match.group(2).strip()
        return "chapter", f"sec{number}", f"{number}. {title}"

    match = _SUBSECTION_RE.match(cleaned)
    if match and current_chapter is not None:
        letter, title = match.group(1), match.group(2).strip()
        chapter_key, chapter_label = current_chapter
        if chapter_key.startswith("app"):
            label = f"{chapter_label.split('.')[0]}.{letter} {title}"
        else:
            number = chapter_label.split(".")[0]
            label = f"{number}.{letter} {title}"
        return "subsection", f"{chapter_key}_{letter}", label

    return None


# --------------------------------------------------------------------------- #
# Page extraction
# --------------------------------------------------------------------------- #


def _extract_page_paragraphs(
    page,
    printed_page: int,
    start_chapter: tuple[str, str] | None,
    start_subsection: tuple[str, str] | None,
) -> tuple[list[Paragraph], tuple[str, str] | None, tuple[str, str] | None]:
    """Split one page into labelled paragraphs.

    Returns ``(paragraphs, chapter_state, subsection_state)`` so that both kinds of
    state can carry across page boundaries (a subsection often spans pages).
    """

    height = page.rect.height
    lines = _strip_footer_lines(_page_lines(page), height)

    paragraphs: list[Paragraph] = []

    chapter = start_chapter
    subsection = start_subsection

    heading_buffer: list[str] = []
    heading_class: str | None = None
    heading_last_bottom = 0.0
    body_buffer: list[str] = []

    def flush_heading() -> None:
        nonlocal chapter, subsection
        if not heading_buffer:
            return
        text = _normalise_inline(" ".join(part.strip() for part in heading_buffer))
        parsed = _parse_heading(text, chapter)
        heading_buffer.clear()
        if parsed is None:
            # Unknown large-font line: keep it as text under the current section.
            body_buffer.append(text)
            return

        kind, key, label = parsed
        if kind in ("chapter", "appendix"):
            chapter = (key, label)
            subsection = None
            section_key, section_label = key, label
        else:
            subsection = (key, label)
            section_key, section_label = key, label

        paragraphs.append(Paragraph(section_key, section_label, text, is_heading=True))

    def flush_body() -> None:
        if not body_buffer:
            return
        text = _join_lines(body_buffer)
        body_buffer.clear()
        if not text:
            return
        if subsection is not None:
            key, label = subsection
        elif chapter is not None:
            key, label = chapter
        else:
            raise HandbookFormatError(
                f"Body text before the first section heading on printed page "
                f"{printed_page}. The layout assumptions do not hold."
            )
        paragraphs.append(Paragraph(key, label, text))

    for line in lines:
        if line.is_blank:
            flush_heading()
            flush_body()
            continue

        if line.is_subsection_heading:
            flush_body()
            is_chapter_line = line.is_chapter_heading
            line_class = "chapter" if is_chapter_line else "subsection"
            continues = (
                heading_class == line_class
                and heading_buffer
                and line.top - heading_last_bottom <= HEADING_LINE_MAX_GAP_PT
            )
            if not continues:
                flush_heading()
                heading_class = line_class
            heading_buffer.append(line.text)
            heading_last_bottom = line.bottom
            continue

        flush_heading()
        body_buffer.append(line.text)

    flush_heading()
    flush_body()

    return paragraphs, chapter, subsection


def extract_handbook(pdf_path: str | Path) -> DocumentModel:
    """Extract the handbook into a :class:`DocumentModel`."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Handbook PDF not found: {path}")

    doc = pymupdf.open(path)
    try:
        body, front_matter, dividers = _detect_page_map(doc)

        toc_dividers = _toc_divider_pages(doc)
        # A chapter divider can sit after the front matter has technically ended
        # (PDF 8 is the divider for chapter 1).  Classify it as a divider, not as
        # front matter, so that the reported page sets match the protocol.
        front_matter = [page for page in front_matter if page not in toc_dividers]
        dividers = sorted(set(dividers) | (set(toc_dividers) - set(front_matter)))

        known_non_body = set(dividers) | set(front_matter)
        unexpected = sorted(set(toc_dividers) - known_non_body)
        if unexpected:
            raise HandbookFormatError(
                "The embedded outline lists chapter divider pages that the footer "
                f"scan did not detect: {unexpected}. Refusing to guess."
            )

        pages: list[PageRecord] = []
        chapter: tuple[str, str] | None = None
        subsection: tuple[str, str] | None = None
        for pdf_page in sorted(body):
            paragraphs, chapter, subsection = _extract_page_paragraphs(
                doc[pdf_page - 1], body[pdf_page], chapter, subsection
            )
            pages.append(
                PageRecord(
                    pdf_page=pdf_page,
                    printed_page=body[pdf_page],
                    paragraphs=tuple(paragraphs),
                )
            )

        title = (doc.metadata or {}).get("title", "") or "Student Handbook 2026/27"
        return DocumentModel(
            pages=tuple(pages),
            front_matter_pages=tuple(front_matter),
            divider_pages=tuple(dividers),
            pdf_page_count=doc.page_count,
            title=title,
        )
    finally:
        doc.close()


def find_tables_report(pdf_path: str | Path, skip_pages: set[int] | None = None) -> list[dict]:
    """Return one row per detected table, for the manual table checklist.

    ``skip_pages`` is a set of 1-based PDF pages to ignore (front matter and
    chapter dividers, which occasionally produce spurious 2x2 detections).
    """

    path = Path(pdf_path)
    skip_pages = skip_pages or set()
    doc = pymupdf.open(path)
    rows: list[dict] = []
    try:
        for page_index in range(doc.page_count):
            if page_index + 1 in skip_pages:
                continue
            page = doc[page_index]
            try:
                with redirect_stdout(io.StringIO()):
                    tables = page.find_tables()
            except Exception:
                continue
            for table_index, table in enumerate(tables.tables):
                rows.append(
                    {
                        "pdf_page": page_index + 1,
                        "table_index": table_index,
                        "rows": table.row_count,
                        "cols": table.col_count,
                        "x0": round(table.bbox[0], 1),
                        "y0": round(table.bbox[1], 1),
                        "x1": round(table.bbox[2], 1),
                        "y1": round(table.bbox[3], 1),
                    }
                )
    finally:
        doc.close()
    return rows
