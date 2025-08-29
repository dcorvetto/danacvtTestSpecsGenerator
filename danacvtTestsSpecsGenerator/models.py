from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import uuid

@dataclass
class TestStep:
    number: int
    action: str
    data: Optional[str] = None  # optional payload for the step

@dataclass
class TestCase:
    id: str
    title: str
    description: str
    preconditions: List[str]
    steps: List[TestStep]
    expected_result: str
    priority: str           # e.g., P0/P1/P2/P3
    type: str               # e.g., functional/negative/boundary/permissions
    tags: List[str] = field(default_factory=list)
    trace_to: Optional[str] = None

    def to_row(self) -> Dict[str, str]:
        return {
            "ID": self.id,
            "Title": self.title,
            "Description": self.description,
            "Preconditions": "\n".join(self.preconditions),
            "Steps": "\n".join(
                f"{s.number}. {s.action}" + (f" [data: {s.data}]" if s.data else "")
                for s in self.steps
            ),
            "Expected Result": self.expected_result,
            "Priority": self.priority,
            "Type": self.type,
            "Tags": ",".join(self.tags),
            "Trace To": self.trace_to or "",
        }

def mk_id(prefix: str = "TC") -> str:
    return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"

def truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n-1] + "…"
