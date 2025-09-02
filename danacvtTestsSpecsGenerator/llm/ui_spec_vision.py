import base64
import os
import time
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

def _b64_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def llm_flow_spec_from_images(
    image_paths: List[str],
    scope: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 4000,
) -> str:
    """
    Combine multiple mockups into ONE Markdown flow spec.
    Order is the order of image_paths.
    """
    if OpenAI is None:
        raise RuntimeError("openai package not installed")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI()
    imgs = [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64_image(p)}"}} for p in image_paths]

    prompt = f"""
You are a senior QA/UX specialist. These mockups represent the flow: "{scope}".
Generate ONE unified Markdown UI specification with sections:

- Overview — purpose and goals
- Layout & Major Components,
- Flow Overview
- Per-screen Components (for each screen: inputs, lists, toggles, buttons, key labels/states)
- Interaction Flow
- Validation & Edge Cases
- Accessibility
- General Data & Validation
- Telemetry
- Open Questions / Assumptions

Be concise but specific. Use bullet points. No code fences.
Include screen references like [Screen 1], [Screen 2] to match order.
""".strip()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": prompt}] + imgs
        }],
    )

    md = (resp.choices[0].message.content or "").strip()
    if md.startswith("```"):
        md = md.strip("`").split("\n", 1)[-1]
    # add a timestamp header
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"# Flow Spec — {scope}\n\n_Generated: {ts}_\n\n"
    return header + md