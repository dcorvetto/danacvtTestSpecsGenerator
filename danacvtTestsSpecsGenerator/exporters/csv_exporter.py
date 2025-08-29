import csv
import pandas as pd
from typing import List
from danacvtTestsSpecsGenerator.models import TestCase

def export_csv(cases: List[TestCase], out_path: str) -> None:
    rows = [c.to_row() for c in cases]
    cols = list(rows[0].keys()) if rows else ["ID","Title","Description","Preconditions","Steps","Expected Result","Priority","Type","Tags","Trace To"]
    if pd is None:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
            for r in rows: w.writerow(r)
    else:
        pd.DataFrame(rows, columns=cols).to_csv(out_path, index=False, encoding="utf-8")