import re
from typing import Dict, List, Tuple, Optional
from danacvtTestsSpecsGenerator.models import TestCase, TestStep, mk_id, truncate
from ..parsers.docs_loader import extract_requirements
from datetime import datetime

CRITICAL_KEYWORDS = {
    "payment","checkout","authentication","login","security",
    "reset","delete","payout","transfer","2fa","mfa"
}
PERMISSIONS_KEYWORDS = {"admin","role","permission","access","authorize","authenticated","unauthorized"}
BOUNDARY_NUM_PAT = r"(?<![A-Za-z0-9])(\d+)(?![A-Za-z0-9])"

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
    return TestCase(
        id=mk_id(),
        title=f"Verify {req_id}: {truncate(req_text, 60)}",
        description=f"Positive path for {req_id}.",
        preconditions=["Test environment available","Valid account if required"],
        steps=steps,
        expected_result="System satisfies the requirement.",
        priority=choose_priority(req_text),
        type="functional",
        tags=tags,
        trace_to=req_id
    )

def gen_negative(req_id: str, req_text: str, scope: str, tags: List[str]) -> Optional[TestCase]:
    lower = req_text.lower()
    if any(w in lower for w in ["must","shall","should"," not ","prevent","deny","unauthorized","invalid"]):
        steps = base_steps_for_requirement(req_text, scope) + [TestStep(4, "Provide invalid/forbidden inputs")]
        return TestCase(
            id=mk_id(),
            title=f"Negative: {truncate(req_text, 60)}",
            description=f"Enforce constraint in {req_id}.",
            preconditions=["Test environment available","Invalid data prepared"],
            steps=steps,
            expected_result="Rejected with clear error; state consistent.",
            priority=choose_priority(req_text),
            type="negative",
            tags=["negative"] + tags,
            trace_to=req_id
        )
    return None

def gen_boundaries(req_id: str, req_text: str, scope: str, tags: List[str]) -> List[TestCase]:
    out: List[TestCase] = []
    for n in find_numeric_bounds(req_text):
        for delta, label in [(-1,"below"),(0,"at"),(1,"above")]:
            if n+delta < 0: 
                continue
            steps = base_steps_for_requirement(req_text, scope) + [
                TestStep(4, f"Use boundary value {n+delta} (one {label} {n})")
            ]
            out.append(TestCase(
                id=mk_id(),
                title=f"Boundary {label} {n}: {truncate(req_text, 50)}",
                description=f"Boundary analysis around {n} from {req_id}.",
                preconditions=["Test environment available"],
                steps=steps,
                expected_result=("Accepted" if delta >= 0 else "Rejected") + " per rules.",
                priority=choose_priority(req_text),
                type="boundary",
                tags=["boundary"] + tags,
                trace_to=req_id
            ))
    return out

def gen_permissions(req_id: str, req_text: str, scope: str, tags: List[str]) -> List[TestCase]:
    if not detect_permissions(req_text):
        return []
    out: List[TestCase] = []
    for role, expect in [
        ("Admin user","Operation succeeds for admin"),
        ("Standard user","Operation blocked/limited for standard user (if restricted)"),
        ("Unauthenticated user","Operation denied with proper error"),
    ]:
        steps = base_steps_for_requirement(req_text, scope)
        steps.insert(1, TestStep(2, f"Authenticate as {role}"))
        for i, s in enumerate(steps, start=1):
            s.number = i
        out.append(TestCase(
            id=mk_id(),
            title=f"Permissions: {role} — {truncate(req_text, 45)}",
            description=f"Role-based access for {req_id}.",
            preconditions=[f"Accounts exist for role '{role}'"],
            steps=steps,
            expected_result=expect,
            priority=choose_priority(req_text),
            type="permissions",
            tags=["permissions"] + tags,
            trace_to=req_id
        ))
    return out

def generate_test_cases_from_text(
    raw_text: str,
    scope: str,
    tags: Optional[List[str]] = None,
    max_per_req: int = 10
) -> List[TestCase]:
    tags = tags or []
    cases: List[TestCase] = []

    for req_id, req_text in extract_requirements(raw_text):
        cases.append(gen_functional(req_id, req_text, scope, tags))
        neg = gen_negative(req_id, req_text, scope, tags)
        if neg:
            cases.append(neg)
        cases.extend(gen_boundaries(req_id, req_text, scope, tags))
        cases.extend(gen_permissions(req_id, req_text, scope, tags))

        if max_per_req:
            # cap per requirement
            per_req = [c for c in cases if c.trace_to == req_id]
            if len(per_req) > max_per_req:
                keep, seen = [], 0
                for c in cases:
                    if c.trace_to == req_id:
                        if seen < max_per_req:
                            keep.append(c); seen += 1
                    else:
                        keep.append(c)
                cases = keep

    return cases