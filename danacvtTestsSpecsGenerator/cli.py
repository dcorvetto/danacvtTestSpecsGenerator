from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

# Parsers
from .parsers.docs_loader import load_text
from .parsers.ocr import ocr_lines
from .parsers.ui_ocr_parser import parse_ui_from_ocr

# Generators
from .generators.doc_tests import generate_test_cases_from_text
from .generators.ui_tests import generate_ui_cases
from .generators.heuristic_ui_spec import write_heuristic_ui_spec

# LLM
from .llm.ui_spec_text import llm_ui_spec_from_ocr  # OCR -> text LLM
from .llm.ui_spec_vision import llm_ui_spec_from_image  # image -> vision LLM
from .llm.booster import llm_boosted_cases

# Exporters
from .exporters.csv_exporter import export_csv
from .exporters.feature_exporter import export_feature

# Updaters (incremental merge)
from .updaters.ui_spec_updater import merge_ui_spec
from .updaters.cvs_updater import merge_cases_into_csv

# Models
from .models import TestCase


# -----------------------------
# helpers
# -----------------------------
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DOC_EXTS = {".txt", ".md", ".docx", ".pdf"}

def _is_image(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS

def _is_doc(path: str) -> bool:
    return Path(path).suffix.lower() in DOC_EXTS

def _ensure_out_path(p: str) -> str:
    """If user provided just a filename, write to outputs/<filename>."""
    if not p:
        return p
    if os.path.dirname(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p
    os.makedirs("outputs", exist_ok=True)
    return os.path.join("outputs", p)

def _require_file_exists(p: str, flag: str):
    if not os.path.isfile(p):
        print(f"[error] {flag} not found: {p}")
        print("Tip: pass an absolute path or run from the folder where the file lives.")
        sys.exit(2)


# -----------------------------
# main
# -----------------------------
def main() -> int:
    ap = argparse.ArgumentParser("danacvt-gen")

    ap.add_argument("--file", required=True, help="Input file (doc or image)")
    ap.add_argument("--scope", required=True, help="High-level feature/screen scope (e.g., 'Login', 'Scene Members')")
    ap.add_argument("--tags", default="", help="Comma-separated tags to attach to generated test cases")

    # Primary outputs
    ap.add_argument("--out", default="testcases.csv", help="CSV for test cases (defaults to outputs/<name>.csv if no path)")
    ap.add_argument("--feature", default=None, help="Optional Gherkin .feature export")
    ap.add_argument("--ui-spec", default=None, help="Heuristic UI spec Markdown output (for images only)")

    # Generation controls
    ap.add_argument("--max-per-req", type=int, default=10, help="Cap tests per requirement (text docs)")

    # LLM toggles
    ap.add_argument("--use-llm", action="store_true", help="Enable LLM booster for extra test ideas")
    ap.add_argument("--llm-ui-spec", default=None, help="Write LLM-based UI spec Markdown here")
    ap.add_argument("--llm-model", default="gpt-4o-mini", help="LLM model name")
    ap.add_argument("--llm-vision", action="store_true", help="Use vision input (send image directly) instead of OCR+text mode")
    ap.add_argument("--llm-temperature", type=float, default=0.2, help="LLM temperature")
    ap.add_argument("--llm-max-tokens", type=int, default=1200, help="Max tokens for LLM responses")

    # Incremental update / merge
    ap.add_argument("--update-ui-spec", default=None, help="Existing Markdown spec to merge into (append/replace sections)")
    ap.add_argument("--replace-sections", default="", help="Comma-separated section titles to replace in --update-ui-spec")
    ap.add_argument("--update-csv", default=None, help="Existing master test cases CSV to merge into")
    ap.add_argument("--prune", action="store_true", help="Mark rows missing in the new run as Status=obsolete when merging CSV")

    args = ap.parse_args()

    _require_file_exists(args.file, "--file")

    # normalize outputs
    out_csv_path = _ensure_out_path(args.out) if args.out else None
    feature_path = _ensure_out_path(args.feature) if args.feature else None
    ui_spec_path = _ensure_out_path(args.ui_spec) if args.ui_spec else None
    llm_ui_spec_path = _ensure_out_path(args.llm_ui_spec) if args.llm_ui_spec else None
    update_ui_spec_path = _ensure_out_path(args.update_ui_spec) if args.update_ui_spec else None
    update_csv_path = _ensure_out_path(args.update_csv) if args.update_csv else None

    # parse tags
    tags: List[str] = [t.strip() for t in args.tags.split(",") if t.strip()]

    all_cases: List[TestCase] = []
    context_text_for_llm = ""  # booster context

    # -----------------------------
    # route based on input type
    # -----------------------------
    if _is_doc(args.file):
        raw = load_text(args.file)
        context_text_for_llm = raw
        text_cases = generate_test_cases_from_text(raw, scope=args.scope, tags=tags, max_per_req=args.max_per_req)
        all_cases.extend(text_cases)
        print(f"[INFO] Generated {len(text_cases)} text-based cases.")

    elif _is_image(args.file):
        # OCR → structured meta → UI cases
        lines = ocr_lines(args.file)
        meta = parse_ui_from_ocr(lines)
        context_text_for_llm = "\n".join(lines)

        ui_cases = generate_ui_cases(meta, scope=args.scope)
        all_cases.extend(ui_cases)
        print(f"[INFO] Generated {len(ui_cases)} UI (OCR) cases.")

        # heuristic UI spec if requested
        if ui_spec_path:
            write_heuristic_ui_spec(ui_spec_path, meta, args.scope)
            print(f"✅ Wrote heuristic UI spec → {ui_spec_path}")

    else:
        print(f"[error] Unsupported input type: {args.file}")
        print("Supported docs:", ", ".join(sorted(DOC_EXTS)))
        print("Supported images:", ", ".join(sorted(IMAGE_EXTS)))
        return 2

    # -----------------------------
    # LLM: UI spec generation (optional)
    # -----------------------------
    if llm_ui_spec_path:
        try:
            if args.llm_vision and _is_image(args.file):
                md = llm_ui_spec_from_image(
                    img_path=args.file,
                    scope=args.scope,
                    model=args.llm_model,
                    temperature=args.llm_temperature,
                    max_tokens=args.llm_max_tokens,
                )
            else:
                # OCR text → LLM spec (works for images w/ OCR lines or docs)
                md = llm_ui_spec_from_ocr(
                    ocr_text=context_text_for_llm or load_text(args.file),
                    img_path=args.file,
                    scope=args.scope,
                    model=args.llm_model,
                    temperature=args.llm_temperature,
                    max_tokens=args.llm_max_tokens,
                )
            if md and md.strip():
                Path(llm_ui_spec_path).write_text(md, encoding="utf-8")
                print(f"✅ Wrote LLM UI spec → {llm_ui_spec_path}")
            else:
                print("⚠️ Skipped LLM UI spec: empty content returned.")
        except Exception as e:
            print(f"⚠️ Skipped LLM UI spec: {e}")

    # -----------------------------
    # LLM: booster for extra cases (optional)
    # -----------------------------
    if args.use_llm:
        boosted = llm_boosted_cases(
            scope=args.scope,
            context_text=context_text_for_llm,
            model=args.llm_model,
            temperature=args.llm_temperature,
            max_tokens=args.llm_max_tokens,
            max_ideas=6,
        )
        if boosted:
            all_cases.extend(boosted)
            print(f"✅ Added {len(boosted)} LLM-boosted cases.")
        else:
            print("ℹ️ No LLM-boosted ideas added (see [LLM] logs above).")

    # -----------------------------
    # Incremental merge: UI spec
    # -----------------------------
    if update_ui_spec_path:
        incoming_md = None
        incoming_src = None
        # Prefer LLM spec if provided this run, else heuristic if provided this run
        if llm_ui_spec_path and os.path.isfile(llm_ui_spec_path):
            incoming_md = Path(llm_ui_spec_path).read_text(encoding="utf-8")
            incoming_src = f"LLM spec ({args.llm_model})"
        elif ui_spec_path and os.path.isfile(ui_spec_path):
            incoming_md = Path(ui_spec_path).read_text(encoding="utf-8")
            incoming_src = "Heuristic spec"

        if incoming_md:
            replace_sections = [s.strip() for s in args.replace_sections.split(",") if s.strip()]
            strategy = "replace_sections" if replace_sections else "append"
            merge_ui_spec(
                existing_md_path=update_ui_spec_path,
                new_md_text=incoming_md,
                strategy=strategy,
                replace_sections=replace_sections or None,
                source_label=incoming_src or "New input"
            )
            print(f"✅ Merged UI spec → {update_ui_spec_path} (strategy={strategy})")
        else:
            print("ℹ️ --update-ui-spec provided but no generated spec to merge (produce --ui-spec or --llm-ui-spec first).")

    # -----------------------------
    # Export / merge test cases
    # -----------------------------
    if not all_cases:
        print("ℹ️ No test cases produced.")
    else:
        # Gherkin feature export (optional)
        if feature_path:
            export_feature(all_cases, feature_path, feature_name=args.scope)
            print(f"✅ Wrote feature file → {feature_path}")

        # Merge into existing CSV or write fresh CSV
        if update_csv_path:
            total = merge_cases_into_csv(update_csv_path, all_cases, match_key="Title", prune=args.prune)
            print(f"✅ Merged {len(all_cases)} cases into {update_csv_path} (total rows now: {total})")
        elif out_csv_path:
            export_csv(all_cases, out_csv_path)
            print(f"✅ Wrote {len(all_cases)} test cases → {out_csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
