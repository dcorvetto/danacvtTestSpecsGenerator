from typing import List
from danacvtTestsSpecsGenerator.models import TestCase, TestStep, mk_id
from danacvtTestsSpecsGenerator.parsers.ui_ocr_parser import parse_ui_from_ocr
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

def generate_ui_cases(meta: Dict, scope: str) -> List[TestCase]:
    cases: List[TestCase] = []
    trace = meta["title"] or scope

    def add(title, desc, steps_list, expected, typ="functional", pr="P2", tags=None):
        steps = [TestStep(i+1, s) for i,s in enumerate(steps_list)]
        cases.append(TestCase(mk_id(), title, desc, ["Screen reachable"], steps, expected, pr, typ, tags or [], trace))

    # Presence
    add(f"{scope}: screen loads", "Open screen.", ["Navigate to the screen"], "Screen displays correctly.", pr="P1", tags=["ui"])

    # Inputs
    for field in meta["inputs"]:
        add(f"{scope}: input accepts valid — {field}", f"Validate valid input for '{field}'.",
            [f"Focus '{field}'", "Enter valid value", "Submit/blur"], "Value accepted; no error.", pr="P1", tags=["input","positive"])
        add(f"{scope}: input rejects invalid — {field}", f"Validate invalid input for '{field}'.",
            [f"Focus '{field}'", "Enter invalid value", "Submit/blur"], "Clear error; state consistent; submit blocked if required.", typ="negative", pr="P1", tags=["input","negative"])
        add(f"{scope}: input boundary — {field}", "Min/Max length and special chars.",
            ["Try min-1, min, min+1 chars", "Try max-1, max, max+1 chars", "Try special characters"], "Accepted/rejected per rules; messages are clear.", typ="boundary", tags=["input","boundary"])

    # Buttons including add/remove/save/edit/back/cancel/login/checkout
    for btn in meta["buttons"]:
        add(f"{scope}: button works — {btn}", f"Validate button '{btn}' action.",
            [f"Locate '{btn}'", f"Click/Tap '{btn}'"], "Expected navigation/action occurs.", pr="P1", tags=["button","interaction"])

    # Flows
    if any(re.search(r"\b(edit)\b", b, re.I) for b in meta["buttons"]):
        add(f"{scope}: enter Edit mode", "Enable selection/editing.", ["Tap 'Edit'"], "Edit affordances appear.", tags=["edit"])
    if any(re.search(r"\b(save)\b", b, re.I) for b in meta["buttons"]):
        add(f"{scope}: save changes", "Persist changes.", ["Make changes", "Tap 'Save'"], "Changes are persisted; success feedback visible.", tags=["save"])
    if any(re.search(r"\b(add)\b", b, re.I) for b in meta["buttons"]):
        add(f"{scope}: add item", "Add an item/entity.", ["Tap 'Add'", "Fill required fields", "Save"], "Item added and visible in list.", tags=["add"])
    if any(re.search(r"\b(remove|delete)\b", b, re.I) for b in meta["buttons"]):
        add(f"{scope}: remove item", "Remove an item/entity.", ["Select item", "Tap 'Remove/Delete'", "Confirm"], "Item gone; counts update.", tags=["remove"])
    if any(re.search(r"\b(back|cancel)\b", b, re.I) for b in meta["buttons"]):
        add(f"{scope}: cancel/discard changes", "Discard unsaved changes.", ["Make changes", "Tap 'Cancel' or navigate back"], "Changes discarded; confirm dialog if needed.", typ="negative", tags=["cancel","back"])

    # Toggles
    if meta["toggles"]:
        add(f"{scope}: toggle on/off", "Validate toggle behavior.", ["Observe default state", "Toggle ON", "Toggle OFF"], "State toggles correctly; persists if applicable.", tags=["toggle"])
        add(f"{scope}: toggle access control", "Restricted toggle visibility/behavior.", ["Attempt toggle with insufficient permission"], "Toggle disabled or action denied.", typ="permissions", tags=["toggle","permissions"])

    # Search
    if meta["has_search"]:
        add(f"{scope}: search filters list", "Filter by query.", ["Focus search", "Type query"], "Only matching rows shown.", pr="P1", tags=["search"])
        add(f"{scope}: search no results", "Empty state for non-matching query.", ["Enter random query"], "No results message shown.", typ="negative", tags=["search","empty"])

    # Lists
    if meta["list_rows"]:
        add(f"{scope}: list visible/scrollable", "Rows visible and scrollable.", ["Open screen", "Scroll list"], "Rows remain visible and interactive.", tags=["list"])
        if meta["long_names"]:
            add(f"{scope}: long names render correctly", "No overflow or truncation bugs.", ["Locate items with long labels"], "No clipping; ellipsis or wrap per design; full value available.", tags=["list","long-names"])
        if meta["counts"]["available"] is not None:
            add(f"{scope}: list count matches header", "Header count equals list rows.", ["Count visible rows"], f"Count equals {meta['counts']['available']}.", tags=["list","count"])

    # Accessibility
    add(f"{scope}: accessibility labeling", "Accessible names/roles/focus order.", ["Inspect with screen reader"], "Correct roles/names; logical focus order; dynamic updates announced.", typ="usability", tags=["a11y"])

    return cases