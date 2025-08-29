from typing import List
from danacvtTestsSpecsGenerator.models import TestCase
from danacvtTestsSpecsGenerator.parsers.ui_ocr_parser import parse_ui_from_ocr
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def write_heuristic_ui_spec(md_path: str, meta: Dict, scope: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sample = "\n- " + "\n- ".join(meta["list_rows"][:8]) if meta["list_rows"] else "(none)"
    parts = []
    parts.append(f"# {meta['title']} — UI Specification (Heuristic)\n")
    parts.append(f"_Generated: {now}_\n")
    parts.append("## Overview\n")
    parts.append(f"Scope: **{scope}**\n")
    parts.append("## OCR Highlights\n")
    parts.append(f"- Search present: {'yes' if meta['has_search'] else 'no'}")
    parts.append(f"- Inputs detected: {len(meta['inputs'])}")
    parts.append(f"- Buttons detected: {len(meta['buttons'])}")
    parts.append(f"- Toggles detected: {len(meta['toggles'])}")
    parts.append(f"- List rows: {len(meta['list_rows'])}")
    parts.append(f"- Long names: {len(meta['long_names'])}")
    parts.append(f"- Counts: {meta['counts']}")
    parts.append(f"- Sample rows:\n{sample}\n")
    Path(md_path).write_text("\n".join(parts), encoding="utf-8")
    return md_path