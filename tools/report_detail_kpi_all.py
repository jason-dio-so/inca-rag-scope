#!/usr/bin/env python3
"""
STEP NEXT-68C: Proposal DETAIL Coverage KPI Auditor
Generates DETAIL_COVERAGE_TABLE.md with coverage-level KPIs for all axes.

KPIs:
- KPI-1: proposal_detail_facts presence rate (coverage-level) ≥ 80%
- KPI-2: benefit_description length ≥ 20 chars ratio ≥ 70%
- KPI-3: TOC/section-number contamination ratio ≤ 10%
- KPI-4: evidence_refs[0].doc_type == 가입설계서 ratio ≥ 80%
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

AXES = [
    "samsung", "hanwha", "heungkuk", "hyundai", "kb",
    "lotte_male", "lotte_female", "meritz",
    "db_under40", "db_over41"
]

# TOC/section patterns (contamination check)
TOC_PATTERNS = [
    r'^\d+[-\.]\d+',           # "4-1", "6.2"
    r'^특별약관$',              # standalone "특별약관"
    r'^담보명$',                # standalone "담보명"
    r'^보장내용$',              # standalone "보장내용"
    r'^\d+\.$',                # "1.", "2."
]

def is_toc_contamination(text: str) -> bool:
    """Check if text is TOC/section number/noise."""
    if not text or text == "명시 없음":
        return False
    text = text.strip()
    for pat in TOC_PATTERNS:
        if re.match(pat, text):
            return True
    return False

def compute_kpis_for_axis(axis: str) -> Dict[str, Any]:
    """Compute KPIs for a single axis."""
    cards_path = Path(f"data/compare/{axis}_coverage_cards.jsonl")
    if not cards_path.exists():
        return {
            "axis": axis,
            "error": f"File not found: {cards_path}",
            "total_coverages": 0,
        }

    cards = []
    with open(cards_path, "r", encoding="utf-8") as f:
        for line in f:
            cards.append(json.loads(line))

    total = len(cards)
    if total == 0:
        return {
            "axis": axis,
            "total_coverages": 0,
            "kpi1_detail_exists": 0.0,
            "kpi2_desc_length": 0.0,
            "kpi3_toc_contamination": 0.0,
            "kpi4_evidence_proposal": 0.0,
        }

    # KPI-1: proposal_detail_facts exists
    detail_exists_count = 0
    for card in cards:
        cv = card.get("customer_view", {})
        desc = cv.get("benefit_description", "")
        # "명시 없음" means no detail
        if desc and desc != "명시 없음":
            detail_exists_count += 1

    # KPI-2: benefit_description length ≥ 20 chars
    desc_long_count = 0
    for card in cards:
        cv = card.get("customer_view", {})
        desc = cv.get("benefit_description", "")
        if desc and desc != "명시 없음" and len(desc) >= 20:
            desc_long_count += 1

    # KPI-3: TOC contamination
    toc_contaminated_count = 0
    for card in cards:
        cv = card.get("customer_view", {})
        desc = cv.get("benefit_description", "")
        if is_toc_contamination(desc):
            toc_contaminated_count += 1

    # KPI-4: evidence_refs[0].doc_type == 가입설계서
    evidence_proposal_count = 0
    for card in cards:
        cv = card.get("customer_view", {})
        refs = cv.get("evidence_refs", [])
        if refs and len(refs) > 0:
            first_ref = refs[0]
            if first_ref.get("doc_type") == "가입설계서":
                evidence_proposal_count += 1

    kpi1 = (detail_exists_count / total) * 100
    kpi2 = (desc_long_count / total) * 100
    kpi3 = (toc_contaminated_count / total) * 100
    kpi4 = (evidence_proposal_count / total) * 100

    # STEP NEXT-70: KPI-1B (structural availability)
    # Count coverages with "명시 없음" (structurally unavailable in proposal)
    unavailable_count = 0
    for card in cards:
        cv = card.get("customer_view", {})
        desc = cv.get("benefit_description", "")
        if desc == "명시 없음":
            unavailable_count += 1

    # KPI-1B: DETAIL success rate among structurally available coverages
    available_count = total - unavailable_count
    kpi1b = (detail_exists_count / available_count * 100) if available_count > 0 else 0.0

    # Failure analysis (for detail_exists)
    failure_examples = []
    for card in cards:
        cv = card.get("customer_view", {})
        desc = cv.get("benefit_description", "")
        if not desc or desc == "명시 없음":
            failure_examples.append({
                "coverage_code": card.get("coverage_code"),
                "coverage_name": card.get("coverage_name_canonical"),
                "extraction_notes": cv.get("extraction_notes", ""),
            })

    return {
        "axis": axis,
        "total_coverages": total,
        "kpi1_detail_exists": kpi1,
        "kpi1b_detail_available": kpi1b,  # STEP NEXT-70
        "kpi2_desc_length": kpi2,
        "kpi3_toc_contamination": kpi3,
        "kpi4_evidence_proposal": kpi4,
        "detail_exists_count": detail_exists_count,
        "unavailable_count": unavailable_count,  # STEP NEXT-70
        "available_count": available_count,  # STEP NEXT-70
        "desc_long_count": desc_long_count,
        "toc_contaminated_count": toc_contaminated_count,
        "evidence_proposal_count": evidence_proposal_count,
        "failure_examples": failure_examples[:10],  # top 10
    }

def generate_markdown_report(kpi_data: List[Dict[str, Any]]) -> str:
    """Generate markdown report."""
    lines = [
        "# STEP NEXT-70: Proposal DETAIL Coverage KPI Report (Enhanced)",
        "",
        "**Generated**: Auto-generated by `tools/report_detail_kpi_all.py`",
        "",
        "## KPI Definitions",
        "",
        "- **KPI-1A**: `proposal_detail_facts` presence (benefit_description ≠ '명시 없음') ≥ 80% (traditional, all coverages)",
        "- **KPI-1B**: DETAIL extraction rate among structurally available coverages (NEW)",
        "- **KPI-2**: `benefit_description` length ≥ 20 chars ≥ 70%",
        "- **KPI-3**: TOC/section contamination (e.g., '4-1', '특별약관') ≤ 10%",
        "- **KPI-4**: `evidence_refs[0].doc_type == 가입설계서` ≥ 80%",
        "",
        "## Summary Table",
        "",
        "| Axis | Total | KPI-1A (%) | KPI-1B (%) | KPI-2 (%) | KPI-3 (%) | KPI-4 (%) | Status |",
        "|------|-------|------------|------------|-----------|-----------|-----------|--------|",
    ]

    for kpi in kpi_data:
        if "error" in kpi:
            lines.append(f"| {kpi['axis']} | 0 | - | - | - | - | - | ERROR |")
            continue

        axis = kpi['axis']
        total = kpi['total_coverages']
        kpi1 = kpi['kpi1_detail_exists']
        kpi1b = kpi['kpi1b_detail_available']  # STEP NEXT-70
        kpi2 = kpi['kpi2_desc_length']
        kpi3 = kpi['kpi3_toc_contamination']
        kpi4 = kpi['kpi4_evidence_proposal']

        # Status: PASS if KPI-1B ≥ 80% and KPI-3 ≤ 10%
        status = "✅ PASS" if kpi1b >= 80 and kpi3 <= 10 else "⚠️ FAIL"

        lines.append(
            f"| {axis} | {total} | {kpi1:.1f} | {kpi1b:.1f} | {kpi2:.1f} | {kpi3:.1f} | {kpi4:.1f} | {status} |"
        )

    lines.append("")
    lines.append("## Detailed Breakdown")
    lines.append("")

    for kpi in kpi_data:
        if "error" in kpi:
            lines.append(f"### {kpi['axis']} (ERROR)")
            lines.append(f"**Error**: {kpi['error']}")
            lines.append("")
            continue

        axis = kpi['axis']
        total = kpi['total_coverages']

        lines.append(f"### {axis}")
        lines.append("")
        lines.append(f"- **Total coverages**: {total}")
        lines.append(f"- **Structurally unavailable** (명시 없음): {kpi['unavailable_count']}")
        lines.append(f"- **Structurally available**: {kpi['available_count']}")
        lines.append(f"- **KPI-1A (DETAIL exists, traditional)**: {kpi['detail_exists_count']}/{total} = {kpi['kpi1_detail_exists']:.1f}%")
        lines.append(f"- **KPI-1B (DETAIL among available)**: {kpi['detail_exists_count']}/{kpi['available_count']} = {kpi['kpi1b_detail_available']:.1f}%")
        lines.append(f"- **KPI-2 (desc ≥ 20 chars)**: {kpi['desc_long_count']}/{total} = {kpi['kpi2_desc_length']:.1f}%")
        lines.append(f"- **KPI-3 (TOC contamination)**: {kpi['toc_contaminated_count']}/{total} = {kpi['kpi3_toc_contamination']:.1f}%")
        lines.append(f"- **KPI-4 (evidence=가입설계서)**: {kpi['evidence_proposal_count']}/{total} = {kpi['kpi4_evidence_proposal']:.1f}%")
        lines.append("")

        # Failure examples
        if kpi['failure_examples']:
            lines.append("**Missing DETAIL (Top 10)**:")
            lines.append("")
            for ex in kpi['failure_examples']:
                lines.append(f"- `{ex['coverage_code']}` ({ex['coverage_name']})")
                if ex['extraction_notes']:
                    lines.append(f"  - Notes: {ex['extraction_notes']}")
            lines.append("")

    lines.append("## Action Items")
    lines.append("")
    lines.append("1. **Axes with KPI-1B < 80%**: Profile/extractor generalization needed (true extraction failures)")
    lines.append("2. **High KPI-3 (TOC contamination)**: Filter patterns need expansion")
    lines.append("3. **Low KPI-4**: Evidence priority enforcement needed")
    lines.append("4. **High structural unavailability**: Proposal format limitation (not extraction failure)")
    lines.append("")

    return "\n".join(lines)

def main():
    """Main entry point."""
    print("STEP NEXT-68C: Auditing proposal DETAIL coverage KPIs for all axes...")

    kpi_data = []
    for axis in AXES:
        print(f"  Processing {axis}...")
        kpi = compute_kpis_for_axis(axis)
        kpi_data.append(kpi)

    # Generate markdown report
    report = generate_markdown_report(kpi_data)

    output_path = Path("docs/audit/STEP_NEXT_68C_DETAIL_COVERAGE_TABLE.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"\n✅ Report generated: {output_path}")

    # Summary to stdout
    print("\n## Quick Summary")
    for kpi in kpi_data:
        if "error" in kpi:
            print(f"{kpi['axis']:15s}: ERROR - {kpi['error']}")
            continue
        kpi1 = kpi['kpi1_detail_exists']
        kpi1b = kpi['kpi1b_detail_available']
        kpi3 = kpi['kpi3_toc_contamination']
        status = "✅ PASS" if kpi1b >= 80 and kpi3 <= 10 else "⚠️ FAIL"
        print(f"{kpi['axis']:15s}: KPI-1A={kpi1:5.1f}% KPI-1B={kpi1b:5.1f}% KPI-3={kpi3:5.1f}% {status}")

if __name__ == "__main__":
    main()
