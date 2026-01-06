# pipeline/step1_sanitize_scope/run.py
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, Tuple, Optional, Any


_CONDITION_SENTENCE_PATTERNS = [
    r".+한\s*경우$",          # "입원한 경우"
    r".+된\s*경우$",          # "진단확정된 경우"
    r".+일\s*경우$",          # "해당할 경우" 류
    r".+시$",                 # "수술시" 같은 케이스(보수적으로)
]


def _norm(s: Optional[str]) -> str:
    return (s or "").strip()


def normalize_mapping_status(value: Optional[str]) -> str:
    # 테스트 요구: lowercase + strip
    return _norm(value).lower()


def should_drop_row(
    coverage_name_raw: str,
    coverage_code: str,
    mapping_status: str,
) -> Tuple[bool, Optional[str]]:
    """
    Test contract:
      - returns (should_drop: bool, reason: str|None)
      - drop "condition sentences" like "...한 경우"
      - do NOT drop valid coverages even if matched/unmatched is mixed
    """
    name = _norm(coverage_name_raw)
    code = _norm(coverage_code)
    status = normalize_mapping_status(mapping_status)

    if not name:
        return True, "empty_name"

    # Drop if looks like a condition sentence (demo scope noise)
    for pat in _CONDITION_SENTENCE_PATTERNS:
        if re.search(pat, name):
            return True, "condition_sentence"

    # (Conservative) do not drop anything else by default
    return False, None


def sanitize_scope_mapped(
    input_csv: str | Path,
    output_csv: str | Path,
    filtered_jsonl: str | Path,
) -> Dict[str, Any]:
    """
    Test contract:
      - reads input_csv
      - writes output_csv with SAME header order
      - normalizes mapping_status (lower + strip)
      - drops condition sentences; writes them to filtered_jsonl as JSONL
      - returns stats dict
    """
    in_path = Path(input_csv)
    out_path = Path(output_csv)
    filtered_path = Path(filtered_jsonl)

    if not in_path.exists():
        raise FileNotFoundError(str(in_path))

    with in_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    kept = 0
    dropped = 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as out_f, \
         filtered_path.open("w", encoding="utf-8") as filt_f:

        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            # pull required fields (safe defaults)
            name = row.get("coverage_name_raw", "")
            code = row.get("coverage_code", "")
            status = row.get("mapping_status", "")

            drop, reason = should_drop_row(name, code, status)
            if drop:
                dropped += 1
                filt_f.write(json.dumps({
                    "coverage_name_raw": name,
                    "coverage_code": code,
                    "mapping_status": status,
                    "reason": reason,
                }, ensure_ascii=False) + "\n")
                continue

            # normalize mapping_status (lowercase + strip)
            if "mapping_status" in row:
                row["mapping_status"] = normalize_mapping_status(row.get("mapping_status"))

            writer.writerow(row)
            kept += 1

    return {
        "input_rows": len(rows),
        "kept_rows": kept,
        "dropped_rows": dropped,
        "output_csv": str(out_path),
        "filtered_jsonl": str(filtered_path),
    }