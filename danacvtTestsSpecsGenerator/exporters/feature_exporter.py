from typing import List
from danacvtTestsSpecsGenerator.models import TestCase

def export_feature(cases: List[TestCase], feature_path: str, feature_name: str) -> None:
    lines = [f"Feature: {feature_name} auto-generated tests",""]
    for c in cases:
        lines.append(f"  @auto @{c.type} @priority_{c.priority.lower()}")
        lines.append(f"  Scenario: {c.title}")
        lines.append("    Given the system/screen is ready")
        for s in c.steps:
            lines.append(f"    When {s.action}" if s.number == 1 else f"    And {s.action}")
        lines.append(f"    Then {c.expected_result}")
        lines.append("")
    Path(feature_path).write_text("\n".join(lines), encoding="utf-8")