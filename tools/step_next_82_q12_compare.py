#!/usr/bin/env python3
"""
STEP NEXT-82-Q12: Cross-Insurer Compare + Judgment + Recommendation (LOCK, NO LLM)

PURPOSE:
- Complete Q12 customer query with real output
- Input: {insurers=[SAMSUNG, meritz], target_coverage="암진단비(유사암제외)"}
- Output: (1) comparison table + (2) judgment + (3) recommendation
- HARD LOCK: NO LLM / NO inference / evidence required / deterministic

SSOT:
- Step2-b canonical: data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl
- Step3 gated evidence: data/scope_v3/{insurer}_step3_evidence_enriched_v1_gated.jsonl
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Target coverage code (cancer diagnosis excluding similar cancers)
TARGET_COVERAGE_CODE = "A4200_1"
TARGET_COVERAGE_NAME = "암진단비(유사암제외)"

# Required slots (core 6 + extended 4)
CORE_SLOTS = [
    "start_date",
    "waiting_period",
    "reduction",
    "payout_limit",
    "entry_age",
    "exclusions",
]

EXTENDED_SLOTS = [
    "underwriting_condition",
    "mandatory_dependency",
    "payout_frequency",
    "industry_aggregate_limit",
]

ALL_SLOTS = CORE_SLOTS + EXTENDED_SLOTS


def load_canonical_coverage(insurer: str, coverage_code: str) -> Optional[Dict]:
    """Load canonical coverage from Step2-b output"""
    canonical_path = Path(f"data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl")

    if not canonical_path.exists():
        print(f"❌ Canonical file not found: {canonical_path}", file=sys.stderr)
        return None

    with open(canonical_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("coverage_code") == coverage_code:
                return row

    return None


def load_evidence(insurer: str, product_key: str, coverage_name: str) -> tuple[Dict, Dict]:
    """
    Load evidence from Step3 gated output.
    Returns: (evidence_list, evidence_slots_dict)
    """
    evidence_path = Path(f"data/scope_v3/{insurer}_step3_evidence_enriched_v1_gated.jsonl")

    if not evidence_path.exists():
        print(f"⚠️  Evidence file not found: {evidence_path}", file=sys.stderr)
        return [], {}

    with open(evidence_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)

            # Match by product_key and coverage_name
            if (row.get("product", {}).get("product_key") == product_key and
                row.get("coverage_name_normalized") == coverage_name):
                evidence_list = row.get("evidence", [])
                evidence_slots = row.get("evidence_slots", {})
                return evidence_list, evidence_slots

    return [], {}


def build_comparison_row(insurer: str, coverage_code: str) -> Optional[Dict]:
    """
    Build comparison row for one insurer's coverage.
    GATE G1: MUST use Step2-b canonical as base.
    GATE G2: Each slot cell with FOUND/FOUND_GLOBAL/CONFLICT must have evidence_ref>=1.
    """
    # Load canonical coverage (G1: SSOT Input Gate)
    canonical = load_canonical_coverage(insurer, coverage_code)
    if not canonical:
        print(f"❌ G1 VIOLATION: No canonical coverage found for {insurer}/{coverage_code}")
        return None

    # Load evidence from Step3
    product_key = canonical.get("product", {}).get("product_key", "")
    coverage_name = canonical.get("coverage_name_normalized", "")
    evidence_list, evidence_slots = load_evidence(insurer, product_key, coverage_name)

    # Build row
    row = {
        "insurer_key": insurer.lower(),
        "product_key": product_key,
        "product_name": canonical.get("product", {}).get("product_name_normalized", ""),
        "variant_key": canonical.get("variant", {}).get("variant_key", "default"),
        "coverage_name": coverage_name,
        "coverage_code": coverage_code,
        "anchored": canonical.get("anchored", False),
        "coverage_code_source": canonical.get("coverage_code_source", ""),
        "slots": {},
    }

    # Process each slot
    for slot_key in ALL_SLOTS:
        slot_data = evidence_slots.get(slot_key, {})

        status = slot_data.get("status", "UNKNOWN")
        value = slot_data.get("value", "")

        # Find evidence for this slot from evidence_list
        slot_evidences = [ev for ev in evidence_list if ev.get("slot_key") == slot_key]

        # G2: Evidence Gate - FOUND/FOUND_GLOBAL/CONFLICT must have evidence
        if status in ["FOUND", "FOUND_GLOBAL", "CONFLICT"]:
            if not slot_evidences or len(slot_evidences) == 0:
                print(f"⚠️  G2 WARNING: {insurer}/{slot_key} has status={status} but no evidence")

        # Build evidence_refs
        evidence_refs = []
        for ev in slot_evidences[:3]:  # Top 3 evidence
            evidence_refs.append({
                "doc_type": ev.get("doc_type", ""),
                "page": f"{ev.get('page_start', '')}-{ev.get('page_end', '')}" if ev.get("page_start") else "",
                "excerpt": ev.get("excerpt", "")[:200],  # Limit excerpt length
                "locator": ev.get("locator", {}),
            })

        row["slots"][slot_key] = {
            "status": status,
            "value": value if value else "",
            "evidence_refs": evidence_refs,
            "evidence_count": len(slot_evidences),
        }

    return row


def generate_judgment_bullets(rows: List[Dict]) -> List[Dict]:
    """
    Generate judgment bullets from comparison rows.
    LOCK: Rule-based only, no LLM, no inference.
    Each bullet MUST have evidence_ref.
    """
    bullets = []

    if len(rows) != 2:
        return bullets

    row_a, row_b = rows[0], rows[1]
    insurer_a = row_a["insurer_key"]
    insurer_b = row_b["insurer_key"]

    # Compare waiting_period
    wp_a = row_a["slots"].get("waiting_period", {})
    wp_b = row_b["slots"].get("waiting_period", {})

    if wp_a["status"] == "FOUND" and wp_b["status"] == "FOUND":
        bullets.append({
            "subject": "면책기간 비교",
            "rule": "waiting_period_comparison",
            "finding": f"{insurer_a}: {wp_a['value']}, {insurer_b}: {wp_b['value']}",
            "evidence_refs": {
                insurer_a: wp_a.get("evidence_refs", []),
                insurer_b: wp_b.get("evidence_refs", []),
            }
        })

    # Compare reduction
    red_a = row_a["slots"].get("reduction", {})
    red_b = row_b["slots"].get("reduction", {})

    if red_a["status"] == "FOUND" and red_b["status"] == "FOUND":
        bullets.append({
            "subject": "감액기간 비교",
            "rule": "reduction_comparison",
            "finding": f"{insurer_a}: {red_a['value']}, {insurer_b}: {red_b['value']}",
            "evidence_refs": {
                insurer_a: red_a.get("evidence_refs", []),
                insurer_b: red_b.get("evidence_refs", []),
            }
        })

    # Compare payout_limit
    pl_a = row_a["slots"].get("payout_limit", {})
    pl_b = row_b["slots"].get("payout_limit", {})

    if pl_a["status"] in ["FOUND", "FOUND_GLOBAL"] and pl_b["status"] in ["FOUND", "FOUND_GLOBAL"]:
        bullets.append({
            "subject": "보장한도/지급금액 비교",
            "rule": "payout_limit_comparison",
            "finding": f"{insurer_a}: {pl_a['value']}, {insurer_b}: {pl_b['value']}",
            "evidence_refs": {
                insurer_a: pl_a.get("evidence_refs", []),
                insurer_b: pl_b.get("evidence_refs", []),
            }
        })

    # Compare entry_age
    ea_a = row_a["slots"].get("entry_age", {})
    ea_b = row_b["slots"].get("entry_age", {})

    if ea_a["status"] in ["FOUND", "FOUND_GLOBAL"] and ea_b["status"] in ["FOUND", "FOUND_GLOBAL"]:
        bullets.append({
            "subject": "가입나이 비교",
            "rule": "entry_age_comparison",
            "finding": f"{insurer_a}: {ea_a['value']}, {insurer_b}: {ea_b['value']}",
            "evidence_refs": {
                insurer_a: ea_a.get("evidence_refs", []),
                insurer_b: ea_b.get("evidence_refs", []),
            }
        })

    # Check for CONFLICT status
    for slot_key in ALL_SLOTS:
        slot_a = row_a["slots"].get(slot_key, {})
        slot_b = row_b["slots"].get(slot_key, {})

        if slot_a["status"] == "CONFLICT" or slot_b["status"] == "CONFLICT":
            bullets.append({
                "subject": f"{slot_key} 상충",
                "rule": "conflict_detected",
                "finding": f"문서 내 상충 발견: {insurer_a if slot_a['status']=='CONFLICT' else insurer_b}",
                "evidence_refs": {
                    insurer_a: slot_a.get("evidence_refs", []) if slot_a["status"] == "CONFLICT" else [],
                    insurer_b: slot_b.get("evidence_refs", []) if slot_b["status"] == "CONFLICT" else [],
                }
            })

    return bullets


def generate_recommendation_cards(rows: List[Dict], bullets: List[Dict]) -> List[Dict]:
    """
    Generate recommendation cards based on comparison.
    LOCK: Rule-based templates only.
    """
    if len(rows) != 2:
        return []

    row_a, row_b = rows[0], rows[1]

    # Simple rule: Recommend based on payout_limit if available
    pl_a = row_a["slots"].get("payout_limit", {})
    pl_b = row_b["slots"].get("payout_limit", {})

    cards = []

    # Card 1: Coverage amount comparison
    if pl_a["status"] in ["FOUND", "FOUND_GLOBAL"] and pl_b["status"] in ["FOUND", "FOUND_GLOBAL"]:
        cards.append({
            "rank": 1,
            "subject": "보장금액 비교",
            "template_id": "payout_limit_comparison",
            "explanation_bullets": [
                f"{row_a['insurer_key']}: {pl_a['value']}",
                f"{row_b['insurer_key']}: {pl_b['value']}",
            ],
            "evidence_refs": {
                row_a['insurer_key']: pl_a.get("evidence_refs", []),
                row_b['insurer_key']: pl_b.get("evidence_refs", []),
            }
        })

    # Card 2: Waiting period comparison
    wp_a = row_a["slots"].get("waiting_period", {})
    wp_b = row_b["slots"].get("waiting_period", {})

    if wp_a["status"] == "FOUND" and wp_b["status"] == "FOUND":
        cards.append({
            "rank": 2,
            "subject": "면책기간 비교",
            "template_id": "waiting_period_comparison",
            "explanation_bullets": [
                f"{row_a['insurer_key']}: {wp_a['value']}",
                f"{row_b['insurer_key']}: {wp_b['value']}",
            ],
            "evidence_refs": {
                row_a['insurer_key']: wp_a.get("evidence_refs", []),
                row_b['insurer_key']: wp_b.get("evidence_refs", []),
            }
        })

    return cards[:3]  # Max 3 cards


def format_markdown_table(rows: List[Dict]) -> str:
    """Format comparison table as Markdown"""
    lines = []

    # Header
    lines.append("| 슬롯 | " + " | ".join([row["insurer_key"] for row in rows]) + " |")
    lines.append("|------|" + "|".join(["------" for _ in rows]) + "|")

    # Rows
    for slot_key in ALL_SLOTS:
        row_cells = [slot_key]
        for row in rows:
            slot_data = row["slots"].get(slot_key, {})
            status = slot_data.get("status", "UNKNOWN")
            value = slot_data.get("value", "")

            if status == "FOUND":
                cell = f"✅ {value}"
            elif status == "FOUND_GLOBAL":
                cell = f"🌐 {value}"
            elif status == "CONFLICT":
                cell = f"⚠️ CONFLICT"
            else:
                cell = f"❓ {status}"

            row_cells.append(cell)

        lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(lines)


def validate_gates(rows: List[Dict]) -> Dict:
    """
    Validate GATES G1-G4.
    G1: SSOT Input Gate - only Step2-b canonical used
    G2: Evidence Gate - FOUND/FOUND_GLOBAL/CONFLICT must have evidence
    G3: Anchor Gate - anchored = (coverage_code != null)
    G4: Deterministic Gate - same input → same output
    """
    results = {
        "G1_ssot_input": {"passed": True, "failures": []},
        "G2_evidence": {"passed": True, "failures": []},
        "G3_anchor": {"passed": True, "failures": []},
        "G4_deterministic": {"passed": True, "notes": "Manual verification required"},
    }

    for row in rows:
        # G1: Check canonical source
        if not row.get("coverage_code"):
            results["G1_ssot_input"]["passed"] = False
            results["G1_ssot_input"]["failures"].append({
                "insurer": row["insurer_key"],
                "reason": "No coverage_code (not from canonical)"
            })

        # G2: Check evidence for FOUND/FOUND_GLOBAL/CONFLICT slots
        for slot_key, slot_data in row["slots"].items():
            status = slot_data.get("status", "")
            evidence_count = slot_data.get("evidence_count", 0)

            if status in ["FOUND", "FOUND_GLOBAL", "CONFLICT"] and evidence_count == 0:
                results["G2_evidence"]["passed"] = False
                results["G2_evidence"]["failures"].append({
                    "insurer": row["insurer_key"],
                    "slot": slot_key,
                    "status": status,
                    "evidence_count": evidence_count
                })

        # G3: Check anchor definition
        anchored = row.get("anchored", False)
        coverage_code = row.get("coverage_code", "")

        if anchored and not coverage_code:
            results["G3_anchor"]["passed"] = False
            results["G3_anchor"]["failures"].append({
                "insurer": row["insurer_key"],
                "anchored": anchored,
                "coverage_code": coverage_code
            })

    return results


def main():
    insurers = ["SAMSUNG", "meritz"]
    coverage_code = TARGET_COVERAGE_CODE

    print("=" * 70)
    print("STEP NEXT-82-Q12: Cross-Insurer Compare (LOCK, NO LLM)")
    print("=" * 70)
    print(f"Target: {TARGET_COVERAGE_NAME} ({coverage_code})")
    print(f"Insurers: {', '.join(insurers)}")
    print()

    # Build comparison rows
    print("Building comparison rows...")
    rows = []
    for insurer in insurers:
        row = build_comparison_row(insurer, coverage_code)
        if row:
            rows.append(row)
            print(f"  ✅ {insurer}: {row['coverage_name']}")
        else:
            print(f"  ❌ {insurer}: Failed to build row")

    if len(rows) != 2:
        print(f"❌ ERROR: Expected 2 rows, got {len(rows)}")
        return 1

    print()

    # Generate judgment
    print("Generating judgment bullets...")
    bullets = generate_judgment_bullets(rows)
    print(f"  Generated {len(bullets)} bullets")

    # Generate recommendations
    print("Generating recommendation cards...")
    cards = generate_recommendation_cards(rows, bullets)
    print(f"  Generated {len(cards)} cards")

    # Validate GATES
    print()
    print("Validating GATES...")
    gate_results = validate_gates(rows)

    for gate_id, result in gate_results.items():
        if gate_id == "G4_deterministic":
            print(f"  {gate_id}: ℹ️  {result['notes']}")
        elif result["passed"]:
            print(f"  {gate_id}: ✅ PASS")
        else:
            print(f"  {gate_id}: ❌ FAIL ({len(result['failures'])} failures)")

    # Save outputs
    print()
    print("Saving outputs...")

    output_dir = Path("docs/audit")
    output_dir.mkdir(exist_ok=True)

    # JSONL output
    jsonl_path = output_dir / "q12_cancer_compare.jsonl"
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f"  ✅ {jsonl_path}")

    # Judgment JSONL
    judgment_path = output_dir / "q12_judgment.jsonl"
    with open(judgment_path, 'w', encoding='utf-8') as f:
        for bullet in bullets:
            f.write(json.dumps(bullet, ensure_ascii=False) + '\n')
    print(f"  ✅ {judgment_path}")

    # Recommendation cards
    cards_path = output_dir / "q12_recommend_cards.jsonl"
    with open(cards_path, 'w', encoding='utf-8') as f:
        for card in cards:
            f.write(json.dumps(card, ensure_ascii=False) + '\n')
    print(f"  ✅ {cards_path}")

    # Markdown report
    md_path = output_dir / "q12_cancer_compare.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Q12: {TARGET_COVERAGE_NAME} 비교\n\n")
        f.write(f"**비교 대상:** {' vs '.join(insurers)}\n\n")
        f.write("## 비교 테이블\n\n")
        f.write(format_markdown_table(rows))
        f.write("\n\n")

        f.write("## 종합 판단\n\n")
        for bullet in bullets:
            f.write(f"- **{bullet['subject']}**: {bullet['finding']}\n")

        f.write("\n## 추천\n\n")
        for i, card in enumerate(cards, 1):
            f.write(f"### {i}. {card['subject']}\n\n")
            for expl in card["explanation_bullets"]:
                f.write(f"- {expl}\n")
            f.write("\n")

    print(f"  ✅ {md_path}")

    # Gate validation results
    gate_path = output_dir / "q12_gate_validation.json"
    with open(gate_path, 'w', encoding='utf-8') as f:
        json.dump(gate_results, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {gate_path}")

    print()
    print("=" * 70)

    # Check if all gates passed
    all_passed = all(
        result["passed"] for gate_id, result in gate_results.items()
        if gate_id != "G4_deterministic"
    )

    if all_passed:
        print("✅ DoD PASSED")
        print(f"   - {TARGET_COVERAGE_NAME} 비교 테이블 완성 (10 slots)")
        print(f"   - 종합 판단 {len(bullets)} bullets (all with evidence)")
        print(f"   - 추천 {len(cards)} cards (all with evidence)")
        print(f"   - GATES G1-G3 PASS")
        return 0
    else:
        print("❌ DoD FAILED - Some gates did not pass")
        return 1


if __name__ == "__main__":
    exit(main())
