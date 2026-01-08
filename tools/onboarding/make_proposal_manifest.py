import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 4:
        print("Usage: make_proposal_manifest.py <insurer> <proposal_pdf_path> <out.json>", file=sys.stderr)
        return 2

    insurer = sys.argv[1]
    pdf_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    if not pdf_path.exists():
        print(f"ERROR: proposal pdf not found: {pdf_path}", file=sys.stderr)
        return 2

    manifest = {
        "version": "v1",
        "items": [
            {
                "insurer": insurer,
                "variant": "default",
                "doc_type": "가입설계서",
                "file_path": str(pdf_path),
                "pdf_path": str(pdf_path),
                "path": str(pdf_path),
            }
        ],
        "source": {"type": "generated", "purpose": "proposal_profile"},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote proposal manifest -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())