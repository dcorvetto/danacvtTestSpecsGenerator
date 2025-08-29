from typing import List, Dict
from danacvtTestsSpecsGenerator.models import TestCase, TestStep
import re

def parse_ui_from_ocr(lines: List[str]) -> Dict:
    text = "\n".join(lines)
    title = ""
    for h in ["Login","Sign In","Checkout","Cart","Payment","Profile","Settings","Scene Members","Devices","Groups"]:
        if any(re.search(rf"\b{re.escape(h)}\b", l, re.I) for l in lines): title = h; break
    if not title:
        title = (lines[0][:40] if lines else "Screen").strip()

    has_search = any(re.search(r"\b(search|find)\b", l, re.I) for l in lines)
    inputs   = [l for l in lines if re.search(r"(username|email|password|address|phone|search|card|cvv|zip|name)", l, re.I)]
    buttons  = [l for l in lines if re.search(r"(login|sign in|submit|checkout|pay|next|back|edit|save|add|remove|delete|cancel|apply)", l, re.I)]
    toggles  = [l for l in lines if re.search(r"(toggle|switch|on|off|enable|disable|checkbox|radio)", l, re.I)]
    list_rows = [l for l in lines if re.match(r"^(\[.*\]|[-*•]\s+.+|[A-Za-z0-9].{8,})", l)]
    m_members   = re.search(r"members\s*\|\s*(\d+)", text, re.I)
    m_available = re.search(r"(available.*?\|)\s*(\d+)", text, re.I)
    counts = {"members": int(m_members.group(1)) if m_members else None,
              "available": int(m_available.group(2)) if m_available else None}
    long_names = [l for l in list_rows if len(l) >= 24]
    tabs = {"Login": any(re.search(r"\b(login|sign in)\b", l, re.I) for l in lines),
            "Checkout": any(re.search(r"\b(checkout|cart|payment)\b", l, re.I) for l in lines),
            "Generic": bool(list_rows)}
    return {
        "title": title, "has_search": has_search, "inputs": inputs, "buttons": buttons, "toggles": toggles,
        "list_rows": list_rows, "long_names": long_names, "counts": counts, "tabs": tabs, "ocr_text": text
    }