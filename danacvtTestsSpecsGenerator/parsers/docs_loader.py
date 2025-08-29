import re
import os
from pathlib import Path
from typing import Union
import docx   # for .docx
from typing import List, Dict, Tuple, Optional
from ..models import TestStep, TestCase
import pypandoc  # for conversion to markdown/plaintext


REQ_PATTERNS = [
    r".*\b(shall|should|must|needs to|is required to)\b.*",
    r"^\s*[-*]\s+.+",
    r"^\s*\d+\.\s+.+",
    r".*\b(user|admin|system)\b.*\b(can|cannot|is able to|is prevented from)\b.*",
]
CRITICAL_KEYWORDS = {"payment","checkout","authentication","login","security","reset","delete","payout","transfer","2fa","mfa"}
PERMISSIONS_KEYWORDS = {"admin","role","permission","access","authorize","authenticated","unauthorized"}
BOUNDARY_NUM_PAT = r"(?<![A-Za-z0-9])(\d+)(?![A-Za-z0-9])"

def load_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".txt",".md",".markdown",".csv",".log"]:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    if ext == ".docx":
        if not docx: raise RuntimeError("python-docx not installed.")
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)
    if ext == ".pdf":
        if not PyPDF2: raise RuntimeError("PyPDF2 not installed.")
        text = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try: text.append(page.extract_text() or "")
                except Exception: pass
        return "\n".join(text)
    raise RuntimeError(f"Unsupported text file: {ext}")

def extract_requirements(raw_text: str) -> List[Tuple[str,str]]:
    lines = [l.strip() for l in raw_text.splitlines()]
    reqs: List[str] = []
    for i, line in enumerate(lines):
        for pat in REQ_PATTERNS:
            if re.search(pat, line, flags=re.IGNORECASE):
                merged = line
                j = i + 1
                while j < len(lines) and (lines[j].startswith("  ") or lines[j].startswith("\t")):
                    merged += " " + lines[j].strip()
                    j += 1
                reqs.append(merged); break
    seen = set(); dedup = []
    for r in reqs:
        k = re.sub(r"\s+"," ", r.lower()).strip()
        if k not in seen: seen.add(k); dedup.append(r)
    return [(f"REQ-{i+1:03d}", t) for i, t in enumerate(dedup)]

def choose_priority(text: str) -> str:
    t = text.lower()
    if any(k in t for k in CRITICAL_KEYWORDS): return "P0"
    if "must" in t or "shall" in t or "is required" in t: return "P1"
    if "should" in t: return "P2"
    return "P3"

def detect_permissions(text: str) -> bool:
    return any(k in text.lower() for k in PERMISSIONS_KEYWORDS)

def find_numeric_bounds(text: str) -> List[int]:
    return [int(m.group(1)) for m in re.finditer(BOUNDARY_NUM_PAT, text)]

def base_steps_for_requirement(req: str, scope: str) -> List[TestStep]:
    return [
        TestStep(1, "Launch the application"),
        TestStep(2, f"Navigate to: {scope}"),
        TestStep(3, f"Perform action implied by: \"{truncate(req, 100)}\""),
    ]

def gen_functional(req_id: str, req_text: str, scope: str, tags: List[str]) -> TestCase:
    steps = base_steps_for_requirement(req_text, scope) + [TestStep(4, "Observe system behavior")]
    return TestCase(mk_id(), f"Verify {req_id}: {truncate(req_text, 60)}", f"Positive path for {req_id}.",
                    ["Test environment available","Valid account if required"], steps,
                    "System satisfies the requirement.", choose_priority(req_text), "functional", tags, req_id)

def gen_negative(req_id: str, req_text: str, scope: str, tags: List[str]) -> Optional[TestCase]:
    lower = req_text.lower()
    if any(w in lower for w in ["must","shall","should"," not ","prevent","deny","unauthorized","invalid"]):
        steps = base_steps_for_requirement(req_text, scope) + [TestStep(4, "Provide invalid/forbidden inputs")]
        return TestCase(mk_id(), f"Negative: {truncate(req_text, 60)}", f"Enforce constraint in {req_id}.",
                        ["Test environment available","Invalid data prepared"], steps,
                        "Rejected with clear error; state consistent.", choose_priority(req_text), "negative", ["negative"]+tags, req_id)
    return None

def gen_boundaries(req_id: str, req_text: str, scope: str, tags: List[str]) -> List[TestCase]:
    out: List[TestCase] = []
    for n in find_numeric_bounds(req_text):
        for delta, label in [(-1,"below"),(0,"at"),(1,"above")]:
            if n+delta < 0: continue
            steps = base_steps_for_requirement(req_text, scope) + [TestStep(4, f"Use boundary value {n+delta} (one {label} {n})")]
            out.append(TestCase(mk_id(), f"Boundary {label} {n}: {truncate(req_text, 50)}",
                                f"Boundary analysis around {n} from {req_id}.", ["Test environment available"],
                                steps, ("Accepted" if delta>=0 else "Rejected")+" per rules.",
                                choose_priority(req_text), "boundary", ["boundary"]+tags, req_id))
    return out

def gen_permissions(req_id: str, req_text: str, scope: str, tags: List[str]) -> List[TestCase]:
    if not detect_permissions(req_text): return []
    out = []
    for role, expect in [("Admin user","Operation succeeds for admin"),
                         ("Standard user","Operation blocked/limited for standard user (if restricted)"),
                         ("Unauthenticated user","Operation denied with proper error")]:
        steps = base_steps_for_requirement(req_text, scope)
        steps.insert(1, TestStep(2, f"Authenticate as {role}"))
        for i,s in enumerate(steps, start=1): s.number = i
        out.append(TestCase(mk_id(), f"Permissions: {role} — {truncate(req_text, 45)}",
                            f"Role-based access for {req_id}.", [f"Accounts exist for role '{role}'"],
                            steps, expect, choose_priority(req_text), "permissions", ["permissions"]+tags, req_id))
    return out

def generate_test_cases_from_text(raw_text: str, scope: str, tags: Optional[List[str]]=None, max_per_req: int=10) -> List[TestCase]:
    tags = tags or []
    cases: List[TestCase] = []
    for req_id, req_text in extract_requirements(raw_text):
        cases.append(gen_functional(req_id, req_text, scope, tags))
        neg = gen_negative(req_id, req_text, scope, tags)
        if neg: cases.append(neg)
        cases.extend(gen_boundaries(req_id, req_text, scope, tags))
        cases.extend(gen_permissions(req_id, req_text, scope, tags))
        if max_per_req:
            k = [c for c in cases if c.trace_to == req_id]
            if len(k) > max_per_req:
                keep, seen = [], 0
                for c in cases:
                    if c.trace_to == req_id:
                        if seen < max_per_req: keep.append(c); seen += 1
                    else: keep.append(c)
                cases = keep
    return cases
