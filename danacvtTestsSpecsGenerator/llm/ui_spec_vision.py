import base64
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from danacvtTestsSpecsGenerator.models import TestCase
import pytesseract
from PIL import Image

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def llm_ui_spec_from_image(img_path: str, scope: str, model: str, temperature: float, max_tokens: int) -> Tuple[str, Dict]:
    if OpenAI is None:
        raise RuntimeError("openai package not installed. pip install openai")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set.")

    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}" if img_path.lower().endswith(".png") else f"data:image/jpeg;base64,{b64}"

    instruction = f"""
You are a senior UX/QA. Analyze the attached UI mockup and produce a **structured Markdown UI specification**.

Scope: "{scope}"

Include sections: Overview, Layout & Major Components, Interaction Flows, States & Empty/Error, Accessibility, Data & Validation, Telemetry, Open Questions.
Infer sensible details (inputs/buttons/save/edit/add/remove/toggles/search/lists/long-text/ counts) where visually clear.
""".strip()

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": data_uri}}
            ],
        }],
    )
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
        "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        "total_tokens": getattr(resp.usage, "total_tokens", None),
    }
    return resp.choices[0].message.content.strip(), usage