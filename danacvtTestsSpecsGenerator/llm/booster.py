from typing import Dict, List, Tuple, Optional
import os, json
from ..models import TestCase, TestStep, mk_id
from datetime import datetime
import re
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _strip_code_fences(text: str) -> str:
    """
    Remove triple backticks and optional language hint (```json).
    """
    text = text.strip()
    # ```json ... ```  or ``` ... ```
    if text.startswith("```"):
        # remove first line fence
        lines = text.splitlines()
        # drop the first fence line
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # drop the last fence line if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _normalize_quotes(text: str) -> str:
    """
    Replace ‘smart’ quotes with normal quotes to avoid JSONDecodeError.
    """
    return (
        text.replace("“", '"')
            .replace("”", '"')
            .replace("‘", "'")
            .replace("’", "'")
    )


def _first_json_block(text: str) -> str:
    """
    Try to extract the first {...} or [...] block using a permissive regex.
    """
    m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
    return m.group(1) if m else ""


def _strip_trailing_commas(s: str) -> str:
    """
    Attempt to remove trailing commas that break JSON.
    Very conservative: only removes a comma before ] or } with optional whitespace.
    """
    # remove ,] and ,}
    s = re.sub(r",\s*]", "]", s)
    s = re.sub(r",\s*}", "}", s)
    return s


def _safe_json_parse(raw: str):
    """
    Best-effort JSON parse:
      1) strip code fences, normalize quotes
      2) try direct json.loads
      3) extract first JSON block and try again
      4) strip trailing commas and try again
    Returns Python object or [] on failure.
    """
    if not raw:
        return []
    t = _strip_code_fences(raw)
    t = _normalize_quotes(t).strip()

    # 1st try: as-is
    try:
        return json.loads(t)
    except Exception:
        pass

    # 2nd try: extract first JSON block
    block = _first_json_block(t)
    if block:
        try:
            return json.loads(block)
        except Exception:
            # 3rd try: strip trailing commas and retry
            try:
                return json.loads(_strip_trailing_commas(block))
            except Exception:
                pass

    # 4th try: strip trailing commas on whole text
    try:
        return json.loads(_strip_trailing_commas(t))
    except Exception:
        return []


def llm_boosted_cases(
    scope: str,
    context_text: str,
    model: str,
    temperature: float,
    max_tokens: int,
    max_ideas: int = 6
) -> List[TestCase]:
    """
    Ask an LLM for extra high-signal test case ideas and return them
    as structured TestCase objects. Best-effort parsing of JSON output.
    """
    # Preconditions
    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI is None:
        print("[LLM] openai package not installed → skipping booster")
        return []
    if not api_key:
        print("[LLM] OPENAI_API_KEY not set → skipping booster")
        return []

    client = OpenAI()  # uses env var

    prompt = f"""
You are a senior QA. Scope: "{scope}".

Based on the following context (requirements or OCR from a mockup), propose up to {max_ideas} concise, high-signal TEST CASE ideas.

Return strictly a JSON array. Each item must be an object with:
- title (string)
- description (string)
- preconditions (array of strings)
- steps (array of strings, ordered)
- expected_result (string)
- type (string: "functional" | "negative" | "boundary" | "permissions" | "usability")
- priority (string: "P0" | "P1" | "P2" | "P3")
- tags (array of strings)

Context:
{context_text}
""".strip()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw = resp.choices[0].message.content or ""
    except Exception as e:
        print(f"[LLM] Booster error → skipping: {e}")
        return []

    ideas = _safe_json_parse(raw)
    if not isinstance(ideas, list) or not ideas:
        print("[LLM] Could not parse JSON ideas → skipping.")
        # Helpful peek for debugging
        print("[LLM] First 200 chars:", (raw or "")[:1000].replace("\n", " "))
        return []

    out: List[TestCase] = []
    for idea in ideas[:max_ideas]:
        # Guard for minimal fields
        title = idea.get("title", "LLM Idea").strip() if isinstance(idea, dict) else "LLM Idea"
        description = idea.get("description", "").strip() if isinstance(idea, dict) else ""
        pre = idea.get("preconditions", []) if isinstance(idea, dict) else []
        steps_strs = idea.get("steps", []) if isinstance(idea, dict) else []
        expected = idea.get("expected_result", "").strip() if isinstance(idea, dict) else ""
        prio = idea.get("priority", "P2")
        typ = idea.get("type", "functional")
        tags = idea.get("tags", []) if isinstance(idea, dict) else []

        # Normalize types
        if not isinstance(pre, list): pre = [str(pre)]
        if not isinstance(steps_strs, list): steps_strs = [str(steps_strs)]
        if not isinstance(tags, list): tags = [str(tags)]

        steps = [TestStep(i + 1, s) for i, s in enumerate(steps_strs)]
        out.append(TestCase(
            id=mk_id(prefix="LLM"),
            title=title,
            description=description,
            preconditions=[str(x) for x in pre],
            steps=steps,
            expected_result=expected or "Expected outcome is clearly met.",
            priority=str(prio),
            type=str(typ),
            tags=["llm"] + [str(t) for t in tags],
            trace_to=scope
        ))

    print(f"[LLM] Added {len(out)} boosted cases.")
    return out