from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import csv

try:
    import pandas as pd
except Exception:
    pd = None

from ..models import TestCase

MERGE_KEY = "Title"   # default match key

def _load_csv_dicts(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    if pd is not None:
        df = pd.read_csv(p)
        return df.to_dict(orient="records")
    # stdlib fallback
    with p.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        return list(r)

def _write_csv_dicts(path: str, rows: List[Dict[str, str]]):
    if pd is not None:
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
        return
    if not rows:
        # write empty with default headers
        headers = ["ID","Title","Description","Preconditions","Steps","Expected Result","Priority","Type","Tags","Trace To","Status"]
    else:
        headers = list(rows[0].keys())
        if "Status" not in headers:
            headers.append("Status")
            for r in rows:
                r.setdefault("Status","active")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def merge_cases_into_csv(
    csv_path: str,
    new_cases: List[TestCase],
    match_key: str = MERGE_KEY,
    prune: bool = False
) -> int:
    """
    Merge a list of TestCase into an existing CSV by 'match_key' (default Title).
    - If match_key matches existing row → update fields but keep old ID.
    - If not found → append a new row (with new ID).
    - prune=True → mark rows missing in new set as Status='obsolete'.
    Returns number of rows written.
    """
    existing = _load_csv_dicts(csv_path)
    by_key = { (r.get(match_key,"") or "").strip().casefold(): (i, r) for i, r in enumerate(existing) }

    new_title_keys = set()
    for case in new_cases:
        row = case.to_row()
        row.setdefault("Status","active")
        key = (row.get(match_key,"") or "").strip().casefold()
        new_title_keys.add(key)

        if key in by_key:
            idx, old = by_key[key]
            # preserve old ID if present
            row["ID"] = old.get("ID", row["ID"])
            # merge/overwrite values
            merged = { **old, **row }
            existing[idx] = merged
        else:
            existing.append(row)

    if prune and existing:
        for r in existing:
            key = (r.get(match_key,"") or "").strip().casefold()
            if key and key not in new_title_keys:
                r["Status"] = "obsolete"

    _write_csv_dicts(csv_path, existing)
    return len(existing)
