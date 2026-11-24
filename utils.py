"""
Utility functions for Meeting Minutes Generator.
Handles DeepSeek API calls, response parsing, and document export.
"""

import os
import re
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


# ---------------------------------------------------------------------------
# DeepSeek API
# ---------------------------------------------------------------------------

def get_api_key(override_key: str | None = None) -> str | None:
    """Load the DeepSeek API key from override or .env / environment."""
    if override_key and override_key.strip():
        return override_key.strip()
    load_dotenv(override=True)
    return os.getenv("DEEPSEEK_API_KEY")


def get_deepseek_client(api_key: str | None = None) -> OpenAI:
    """Create and return a DeepSeek OpenAI-compatible client."""
    resolved_key = get_api_key(api_key)
    if not resolved_key:
        raise ValueError(
            "DEEPSEEK_API_KEY not found. Please set it in your .env file or enter it in the sidebar."
        )
    return OpenAI(api_key=resolved_key, base_url=DEEPSEEK_BASE_URL)


def _strip_outer_code_fence(text: str) -> str:
    """Remove accidental outer ```markdown ... ``` wrappers if returned by the model."""
    stripped = text.strip()
    match = re.match(r"^```(?:markdown|md)?\s*\n([\s\S]*?)\n```$", stripped)
    return match.group(1).strip() if match else stripped


def generate_minutes(
    transcript: str,
    system_prompt: str,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> str:
    """
    Send the meeting transcript to DeepSeek and return structured minutes.

    Args:
        transcript: Raw meeting transcript text.
        system_prompt: Instruction prompt for the LLM.
        model: DeepSeek model name ('deepseek-chat' or 'deepseek-reasoner').
        api_key: Optional API key override.

    Returns:
        Structured meeting minutes as a markdown string.
    """
    client = get_deepseek_client(api_key)
    request_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}"},
        ],
    }
    if model == "deepseek-chat":
        request_kwargs["temperature"] = 0.2

    response = client.chat.completions.create(**request_kwargs)
    content = response.choices[0].message.content or ""
    return _strip_outer_code_fence(content)


# ---------------------------------------------------------------------------
# Transcript & Minutes Analytics
# ---------------------------------------------------------------------------

def analyze_transcript(transcript: str) -> dict[str, int]:
    """Compute basic metrics for the input transcript."""
    cleaned = transcript.strip()
    if not cleaned:
        return {"words": 0, "chars": 0, "lines": 0, "speakers": 0}

    words = len(cleaned.split())
    lines = len([ln for ln in cleaned.splitlines() if ln.strip()])
    speaker_matches = set(
        re.findall(r"^([A-Z][a-zA-Z0-9 ._-]{1,30}):\s+", cleaned, flags=re.MULTILINE)
    )
    ignored_prefixes = {"Date", "Time", "Duration", "Platform", "Location", "Attendees", "Decisions", "Action items"}
    speakers = len([s for s in speaker_matches if s.strip() not in ignored_prefixes])

    return {
        "words": words,
        "chars": len(cleaned),
        "lines": lines,
        "speakers": speakers,
    }


def extract_minutes_stats(minutes_markdown: str) -> dict[str, int]:
    """Parse counts of attendees, decisions, and action items from generated minutes."""
    stats = {"attendees": 0, "decisions": 0, "action_items": 0}
    current_section = None

    for line in minutes_markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            heading = stripped.lower()
            if "attendees" in heading:
                current_section = "attendees"
            elif "decisions" in heading:
                current_section = "decisions"
            elif "action items" in heading:
                current_section = "action_items"
            else:
                current_section = None
            continue

        if current_section in ("attendees", "decisions") and (
            stripped.startswith("- ") or stripped.startswith("* ")
        ):
            stats[current_section] += 1
        elif current_section == "action_items" and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            is_separator = all(set(c.replace("-", "").replace(":", "")) == set() for c in cells)
            is_header = any(c.lower() in ("#", "action item", "owner", "deadline") for c in cells)
            if not is_separator and not is_header and any(cells):
                stats["action_items"] += 1

    return stats


# ---------------------------------------------------------------------------
# Document Export
# ---------------------------------------------------------------------------

def _set_cell_shading(cell, fill_hex: str) -> None:
    """Apply background fill color to a Word table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tc_pr.append(shd)


def _add_formatted_runs(paragraph, text: str) -> None:
    """Render **bold** inline segments inside a Word paragraph cleanly."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        else:
            paragraph.add_run(part.replace("**", ""))


def _add_heading(doc: Document, text: str, level: int) -> None:
    """Add a styled heading to the document."""
    heading = doc.add_heading(text, level=level)
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = heading.runs[0] if heading.runs else heading.add_run(text)
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)  # Deep Indigo


def _add_table_row(table, cells: list[str]) -> None:
    """Add a data row to a Word table, padding/truncating safely to column count."""
    row = table.add_row()
    col_count = len(table.columns)
    for i in range(col_count):
        cell_text = cells[i].strip() if i < len(cells) else ""
        para = row.cells[i].paragraphs[0]
        para.text = ""
        _add_formatted_runs(para, cell_text)


def create_docx(minutes_markdown: str) -> bytes:
    """
    Convert the markdown meeting minutes to a styled .docx file.

    Args:
        minutes_markdown: The structured minutes as a markdown string.

    Returns:
        Bytes of the .docx file.
    """
    doc = Document()

    # Base font
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(10.5)

    # Document margins
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Title
    title = doc.add_heading("Meeting Minutes", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if title.runs:
        title.runs[0].font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    # Parse and render markdown
    lines = minutes_markdown.split("\n")
    table = None
    table_started = False

    for line in lines:
        stripped = line.strip()

        # Skip horizontal rules
        if stripped in ("---", "***", "___"):
            table = None
            table_started = False
            continue

        # Headings
        if stripped.startswith("#### "):
            _add_heading(doc, stripped[5:].strip(), 4)
            table = None
            table_started = False
        elif stripped.startswith("### "):
            _add_heading(doc, stripped[4:].strip(), 3)
            table = None
            table_started = False
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            if "meeting minutes" not in heading_text.lower():
                _add_heading(doc, heading_text, 2)
            table = None
            table_started = False
        elif stripped.startswith("# "):
            _add_heading(doc, stripped[2:].strip(), 1)
            table = None
            table_started = False

        # Table rows
        elif stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            is_separator = all(set(c.replace("-", "").replace(":", "")) == set() for c in cells)

            if not table_started and not is_separator:
                table = doc.add_table(rows=1, cols=len(cells))
                table.style = "Table Grid"
                hdr_row = table.rows[0]
                for i, h in enumerate(cells):
                    cell = hdr_row.cells[i]
                    _set_cell_shading(cell, "1E3A8A")
                    para = cell.paragraphs[0]
                    para.text = ""
                    run = para.add_run(h.replace("**", ""))
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                table_started = True
            elif is_separator:
                continue
            elif table is not None:
                _add_table_row(table, cells)

        # Bullet points
        elif stripped.startswith("- ") or stripped.startswith("* "):
            table = None
            table_started = False
            para = doc.add_paragraph(style="List Bullet")
            _add_formatted_runs(para, stripped[2:])

        # Numbered list
        elif re.match(r"^\d+\.\s", stripped):
            table = None
            table_started = False
            text = re.sub(r"^\d+\.\s", "", stripped)
            para = doc.add_paragraph(style="List Number")
            _add_formatted_runs(para, text)

        # Normal paragraph
        elif stripped:
            table = None
            table_started = False
            para = doc.add_paragraph()
            _add_formatted_runs(para, stripped)

        else:
            table = None
            table_started = False

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def create_txt(minutes_markdown: str) -> bytes:
    """
    Convert the markdown minutes to a clean plain-text file.

    Args:
        minutes_markdown: The structured minutes as a markdown string.

    Returns:
        Bytes of the .txt file.
    """
    lines = minutes_markdown.split("\n")
    clean_lines = []
    for line in lines:
        line = re.sub(r"^#{1,4}\s*", "", line)        # headings
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)  # bold
        line = re.sub(r"\*(.+?)\*", r"\1", line)       # italic
        clean_lines.append(line)
    return "\n".join(clean_lines).encode("utf-8")
