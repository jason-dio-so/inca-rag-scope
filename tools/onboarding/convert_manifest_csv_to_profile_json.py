import csv
import json
import sys
from pathlib import Path

"""
Convert evidence_sources/*_manifest.csv into profile_builder_v3-compatible JSON manifest.

Input CSV header example:
  doc_type,file_path

profile_builder_v3 observed required item keys:
- insurer
- variant
(and likely uses doc_type + file_path)

We inject:
- insurer: from CLI arg
- variant: default "default" (unless CSV already has it)
We also provide aliases:
- pdf_path/path from file_path
- document_type/type from doc_type
"""

def main():
    if len(sys.argv) != 4:
        print("Usage: convert_manifest_csv_to_profile_json.py <in.csv> <out.json> <insurer>", file=sys.stderr)
        return 2

    in_csv = Path(sys.argv[1])
    out_json = Path(sys.argv[2])
    insurer = sys.argv[3]

    if not in_csv.exists():
        print(f"ERROR: input csv not found: {in_csv}", file=sys.stderr)
        return 2

    items = []
    with in_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print(f"ERROR: CSV appears empty or missing header: {in_csv}", file=sys.stderr)
            return 2

        for r in reader:
            doc_type = (r.get("doc_type") or "").strip()
            file_path = (r.get("file_path") or "").strip()

            item = dict(r)  # preserve originals
            item["insurer"] = item.get("insurer") or insurer
            item["variant"] = item.get("variant") or "default"

            # Provide common aliases to avoid downstream key mismatches
            if file_path:
                item["pdf_path"] = file_path
                item["path"] = file_path

            if doc_type:
                item["document_type"] = doc_type
                item["type"] = doc_type

            items.append(item)

    manifest = {
        "version": "v1",
        "items": items,
        "source": {"type": "csv", "path": str(in_csv)},
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} rows -> {out_json}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
