import os
from typing import Dict, List, Tuple, Optional
from danacvtTestsSpecsGenerator.models import TestCase
from danacvtTestsSpecsGenerator.parsers.ocr import ocr_lines
from datetime import datetime
import pytesseract
from PIL import Image

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def build_llm_text_prompt(scope: str, ocr_text: str) -> str:
    return f"""
You are a senior UX/QA writing a concise but complete UI specification for a single screen.

Scope: "{scope}"

Provide a **Markdown** document with these sections:
1. Overview — purpose and goals
2. Layout & Major Components
3. Interaction Flows
4. States & Empty/Error Handling
5. Accessibility (a11y)
6. Data & Validation Rules
7. Telemetry/Analytics
8. Open Questions

OCR excerpt (may be partial/noisy):
---
{ocr_text}
---
""".strip()

def llm_ui_spec_from_ocr(ocr_text: str, img_path: str, scope: str, model: str, temperature: float, max_tokens: int) -> Tuple[str, Dict]:
    if OpenAI is None:
        raise RuntimeError("openai package not installed. pip install openai")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set.")

    if not (Image and pytesseract):
        raise RuntimeError("Pillow + pytesseract required for OCR LLM mode.")

    ocr_text = pytesseract.image_to_string(Image.open(img_path))
    prompt = build_llm_text_prompt(scope, ocr_text)

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
        "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        "total_tokens": getattr(resp.usage, "total_tokens", None),
    }
    md = (resp.choices[0].message.content or "").strip()
    # normalize occasional code fences
    if md.startswith("```"):
        md = md.strip().strip("`")
        # crude fence removal if model wrapped output
        md = md.split("\n", 1)[-1]
    return md