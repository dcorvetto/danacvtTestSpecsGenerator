from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
import re

SECTION_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.M)

def _split_sections(md: str):
    """Return list of (level, title, start_idx, end_idx) for all headings."""
    matches = list(SECTION_RE.finditer(md))
    sections = []
    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(md)
        sections.append((level, title, start, end))
    return sections

def _replace_section(md: str, section_title: str, new_body: str) -> str:
    secs = _split_sections(md)
    for (level, title, start, end) in secs:
        if title.lower() == section_title.lower():
            # keep the heading line, replace body
            head_line = md[start:md.find("\n", start)+1]
            return md[:start] + head_line + new_body.rstrip() + "\n" + md[end:]
    # If section not found, append as level-2
    block = f"\n## {section_title}\n{new_body.rstrip()}\n"
    return md.rstrip() + block + "\n"

def _ensure_change_log(md: str) -> str:
    if re.search(r"^##\s*Change Log\s*$", md, flags=re.M):
        return md
    return md.rstrip() + "\n\n## Change Log\n\n"  # ensure exists

def merge_ui_spec(
    existing_md_path: str,
    new_md_text: str,
    strategy: str = "append",           # "append" | "replace_sections"
    replace_sections: Optional[Iterable[str]] = None,
    source_label: str = "New input"
) -> str:
    """
    Merge a new UI spec snippet into an existing Markdown spec.
    - append: writes an Addendum and a Change Log entry
    - replace_sections: replaces specified section bodies if present, else appends new sections
    Returns the merged markdown string (also writes it to the same path).
    """
    p = Path(existing_md_path)
    old = p.read_text(encoding="utf-8") if p.exists() else "# UI Specification\n\n"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if strategy == "replace_sections" and replace_sections:
        merged = old
        for sec in replace_sections:
            merged = _replace_section(merged, sec, new_md_text)
        merged = _ensure_change_log(merged)
        merged += f"- {now}: Replaced sections {', '.join(replace_sections)} from **{source_label}**.\n"
    else:
        # default = append
        merged = _ensure_change_log(old)
        addendum = f"\n## Addendum — {source_label} ({now})\n\n" + new_md_text.strip() + "\n"
        merged = merged.rstrip() + addendum + f"\n- {now}: Added Addendum from **{source_label}**.\n"

    p.write_text(merged, encoding="utf-8")
    return merged