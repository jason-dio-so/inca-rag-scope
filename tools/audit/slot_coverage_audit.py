#!/usr/bin/env python3
"""
STEP NEXT-V0: Slot Coverage Audit Script (JSONL + DB + Premium Gate)

Purpose:
  Deterministically measure slot presence/absence in compare_rows_v1.jsonl
  and report insurer-level coverage without LLM estimation or imputation.

SSOT Input:
  - data/compare_v1/compare_rows_v1.jsonl (340 rows)
  - data/policy/question_card_routing.json (policy-based expected slots)

SSOT Output:
  - docs/audit/STEP_NEXT_V0_SLOT_COVERAGE_REPORT.md
  - docs/audit/STEP_NEXT_V0_SLOT_COVERAGE_REPORT.csv
  - (optional) docs/audit/STEP_NEXT_V0_SLOT_COVERAGE_REPORT.json

Rules:
  ✅ Measure/aggregate only (existence/missing/count/join)
  ✅ Slot "present" = non-empty value (not None/""/{}/[])
  ✅ Q12 premium follows G10 Gate: "if ANY insurer has missing premium → FAIL"
  ❌ NO LLM estimation
  ❌ NO imputation/averaging/normalization
  ❌ NO JSONL modification (read-only)
"""

import argparse
import json
import csv
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Tuple


class SlotCoverageAuditor:
    """Audit slot coverage in JSONL data with deterministic rules."""

    def __init__(self, jsonl_path: str, policy_json_path: Optional[str] = None,
                 premium_slot: str = "premium_monthly"):
        self.jsonl_path = jsonl_path
        self.policy_json_path = policy_json_path
        self.premium_slot = premium_slot

        # Data structures
        self.rows: List[Dict] = []
        self.insurer_stats: Dict[str, Dict] = defaultdict(lambda: {
            "row_count": 0,
            "slot_presence": defaultdict(int),
            "slot_missing": defaultdict(int)
        })
        self.all_slots: Set[str] = set()
        self.expected_slots: Set[str] = set()
        self.policy_data: Optional[Dict] = None

    def load_jsonl(self) -> int:
        """Load JSONL file and return row count."""
        print(f"[INFO] Loading JSONL from: {self.jsonl_path}")

        if not os.path.exists(self.jsonl_path):
            raise FileNotFoundError(f"JSONL not found: {self.jsonl_path}")

        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    self.rows.append(row)
                except json.JSONDecodeError as e:
                    print(f"[WARN] Failed to parse line {line_num}: {e}")

        print(f"[INFO] Loaded {len(self.rows)} rows from JSONL")
        return len(self.rows)

    def load_policy(self) -> None:
        """Load policy JSON to extract expected slots."""
        if not self.policy_json_path or not os.path.exists(self.policy_json_path):
            print(f"[INFO] Policy JSON not found or not specified, skipping expected slots extraction")
            return

        print(f"[INFO] Loading policy from: {self.policy_json_path}")
        with open(self.policy_json_path, 'r', encoding='utf-8') as f:
            self.policy_data = json.load(f)

        # Extract expected slots from policy (Q12 premium requirements, etc.)
        routing_rules = self.policy_data.get("routing_rules", {})
        for q_id, q_data in routing_rules.items():
            special_rules = q_data.get("special_rules", {})
            if special_rules.get("requires_premium"):
                self.expected_slots.add(self.premium_slot)
            # Add other expected slots based on policy (can be extended)

        print(f"[INFO] Extracted {len(self.expected_slots)} expected slots from policy")

    def extract_slots_from_row(self, row: Dict) -> Tuple[str, Dict[str, Any]]:
        """
        Extract insurer and slot dict from a row.

        Returns: (insurer_key, slot_dict)

        Slot extraction order:
          1. slots
          2. slot_values
          3. values
          4. fields

        If list form, reconstruct as dict.
        """
        # Extract insurer
        insurer = None
        if "identity" in row and isinstance(row["identity"], dict):
            insurer = row["identity"].get("insurer_key") or row["identity"].get("insurer")
        if not insurer:
            insurer = row.get("insurer_key") or row.get("insurer") or "UNKNOWN"

        # Extract slots
        slot_dict = None
        for key in ["slots", "slot_values", "values", "fields"]:
            if key in row:
                candidate = row[key]
                if isinstance(candidate, dict):
                    slot_dict = candidate
                    break
                elif isinstance(candidate, list):
                    # Reconstruct as dict from list of {key: ..., value: ...}
                    reconstructed = {}
                    for item in candidate:
                        if isinstance(item, dict):
                            # Try to find key/value pairs
                            item_key = item.get("key") or item.get("name") or item.get("slot")
                            item_value = item.get("value") or item.get("amount")
                            if item_key:
                                reconstructed[item_key] = item_value
                    if reconstructed:
                        slot_dict = reconstructed
                        break

        if slot_dict is None:
            slot_dict = {}

        return insurer, slot_dict

    def is_slot_present(self, value: Any) -> bool:
        """
        Determine if a slot value is "present" (not empty).

        Rules:
          - None → False
          - "" → False
          - {} → False
          - [] → False
          - dict with nested value/amount → check nested value
          - Otherwise → True
        """
        if value is None:
            return False
        if value == "":
            return False
        if isinstance(value, dict):
            if not value:  # empty dict
                return False
            # Check nested value/amount fields
            nested_val = value.get("value") or value.get("amount")
            if nested_val is not None:
                return self.is_slot_present(nested_val)
            # If dict has any content, consider present
            return True
        if isinstance(value, list):
            return len(value) > 0

        return True

    def audit_rows(self) -> None:
        """Process all rows and collect slot statistics."""
        print(f"[INFO] Auditing {len(self.rows)} rows...")

        for row in self.rows:
            insurer, slot_dict = self.extract_slots_from_row(row)

            # Update insurer row count
            self.insurer_stats[insurer]["row_count"] += 1

            # Track all slots discovered
            self.all_slots.update(slot_dict.keys())

            # Check presence for each slot
            for slot_key, slot_value in slot_dict.items():
                if self.is_slot_present(slot_value):
                    self.insurer_stats[insurer]["slot_presence"][slot_key] += 1
                else:
                    self.insurer_stats[insurer]["slot_missing"][slot_key] += 1

        # Merge expected slots from policy into all_slots
        self.all_slots.update(self.expected_slots)

        print(f"[INFO] Discovered {len(self.all_slots)} unique slots across all rows")
        print(f"[INFO] Found {len(self.insurer_stats)} insurers")

    def compute_global_stats(self) -> Dict[str, Dict]:
        """Compute global slot statistics across all insurers."""
        global_stats = {}

        for slot in self.all_slots:
            total_present = sum(
                stats["slot_presence"].get(slot, 0)
                for stats in self.insurer_stats.values()
            )
            total_missing = sum(
                stats["slot_missing"].get(slot, 0)
                for stats in self.insurer_stats.values()
            )
            total_rows = total_present + total_missing

            global_stats[slot] = {
                "present_count": total_present,
                "missing_count": total_missing,
                "total_count": total_rows,
                "present_ratio": total_present / total_rows if total_rows > 0 else 0.0
            }

        return global_stats

    def check_premium_gate_q12(self) -> Dict[str, Any]:
        """
        Check Q12 Premium Gate (G10) compliance.

        Rule: If ANY insurer has missing premium → FAIL

        Returns: {
            "premium_slot": str,
            "insurers": {insurer: {present: int, missing: int, ratio: float}},
            "gate_status": "PASS" | "FAIL",
            "reason": str
        }
        """
        premium_data = {
            "premium_slot": self.premium_slot,
            "insurers": {},
            "gate_status": "UNKNOWN",
            "reason": ""
        }

        has_any_missing = False

        for insurer, stats in self.insurer_stats.items():
            present = stats["slot_presence"].get(self.premium_slot, 0)
            missing = stats["slot_missing"].get(self.premium_slot, 0)
            total = present + missing
            ratio = present / total if total > 0 else 0.0

            premium_data["insurers"][insurer] = {
                "present": present,
                "missing": missing,
                "total": total,
                "ratio": ratio
            }

            if missing > 0:
                has_any_missing = True

        if has_any_missing:
            premium_data["gate_status"] = "FAIL"
            premium_data["reason"] = "G10 Gate: At least one insurer has missing premium data"
        else:
            premium_data["gate_status"] = "PASS"
            premium_data["reason"] = "All insurers have complete premium data"

        return premium_data

    def generate_markdown_report(self, output_path: str) -> None:
        """Generate comprehensive Markdown report."""
        print(f"[INFO] Generating Markdown report: {output_path}")

        global_stats = self.compute_global_stats()
        premium_gate = self.check_premium_gate_q12()

        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("# STEP NEXT-V0: Slot Coverage Audit Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**JSONL Source**: `{self.jsonl_path}`\n\n")
            f.write(f"**Total Rows**: {len(self.rows)}\n\n")
            f.write(f"**Total Insurers**: {len(self.insurer_stats)}\n\n")
            f.write(f"**Total Unique Slots**: {len(self.all_slots)}\n\n")

            if self.policy_json_path:
                f.write(f"**Policy Source**: `{self.policy_json_path}`\n\n")

            f.write("---\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write("This report provides a deterministic audit of slot coverage in `compare_rows_v1.jsonl`.\n\n")
            f.write("**Audit Rules**:\n")
            f.write("- ✅ Slot \"present\" = non-empty value (not None/\"\"/{}/(])\n")
            f.write("- ✅ Measurement only (no LLM estimation or imputation)\n")
            f.write("- ✅ Q12 Premium Gate (G10): FAIL if ANY insurer has missing premium\n\n")

            # Q12 Premium Gate Status
            f.write("---\n\n")
            f.write("## Q12 Premium Gate (G10) Status\n\n")
            f.write(f"**Premium Slot**: `{premium_gate['premium_slot']}`\n\n")
            f.write(f"**Gate Status**: **{premium_gate['gate_status']}**\n\n")
            f.write(f"**Reason**: {premium_gate['reason']}\n\n")

            f.write("### Premium Coverage by Insurer\n\n")
            f.write("| Insurer | Present | Missing | Total | Ratio |\n")
            f.write("|---------|---------|---------|-------|-------|\n")
            for insurer, pdata in sorted(premium_gate["insurers"].items()):
                f.write(f"| {insurer} | {pdata['present']} | {pdata['missing']} | "
                       f"{pdata['total']} | {pdata['ratio']:.2%} |\n")
            f.write("\n")

            # Insurer-Level Statistics
            f.write("---\n\n")
            f.write("## Insurer-Level Statistics\n\n")
            f.write("| Insurer | Row Count | Unique Slots (Present) |\n")
            f.write("|---------|-----------|------------------------|\n")
            for insurer in sorted(self.insurer_stats.keys()):
                stats = self.insurer_stats[insurer]
                unique_slots = len([s for s in stats["slot_presence"] if stats["slot_presence"][s] > 0])
                f.write(f"| {insurer} | {stats['row_count']} | {unique_slots} |\n")
            f.write("\n")

            # Global Slot Coverage (TOP 20 by presence)
            f.write("---\n\n")
            f.write("## Global Slot Coverage - TOP 20 (by Presence Ratio)\n\n")
            sorted_slots = sorted(global_stats.items(), key=lambda x: x[1]["present_ratio"], reverse=True)
            f.write("| Slot | Present | Missing | Total | Ratio |\n")
            f.write("|------|---------|---------|-------|-------|\n")
            for slot, gstats in sorted_slots[:20]:
                f.write(f"| {slot} | {gstats['present_count']} | {gstats['missing_count']} | "
                       f"{gstats['total_count']} | {gstats['present_ratio']:.2%} |\n")
            f.write("\n")

            # Global Slot Coverage (BOTTOM 20 by presence)
            f.write("---\n\n")
            f.write("## Global Slot Coverage - BOTTOM 20 (by Presence Ratio)\n\n")
            f.write("| Slot | Present | Missing | Total | Ratio |\n")
            f.write("|------|---------|---------|-------|-------|\n")
            for slot, gstats in sorted_slots[-20:]:
                f.write(f"| {slot} | {gstats['present_count']} | {gstats['missing_count']} | "
                       f"{gstats['total_count']} | {gstats['present_ratio']:.2%} |\n")
            f.write("\n")

            # Missing Slots by Insurer (TOP 20 most missing)
            f.write("---\n\n")
            f.write("## Missing Slots by Insurer (TOP 20)\n\n")

            # Aggregate missing counts per slot per insurer
            missing_by_insurer_slot = []
            for insurer, stats in self.insurer_stats.items():
                for slot, miss_count in stats["slot_missing"].items():
                    if miss_count > 0:
                        missing_by_insurer_slot.append((insurer, slot, miss_count))

            missing_by_insurer_slot.sort(key=lambda x: x[2], reverse=True)

            f.write("| Insurer | Slot | Missing Count |\n")
            f.write("|---------|------|---------------|\n")
            for insurer, slot, miss_count in missing_by_insurer_slot[:20]:
                f.write(f"| {insurer} | {slot} | {miss_count} |\n")
            f.write("\n")

            # Expected Slots (from Policy) with Zero Occurrence
            if self.expected_slots:
                f.write("---\n\n")
                f.write("## Policy-Expected Slots with Zero Occurrence\n\n")
                zero_occurrence = []
                for slot in self.expected_slots:
                    gstats = global_stats.get(slot, {"present_count": 0})
                    if gstats["present_count"] == 0:
                        zero_occurrence.append(slot)

                if zero_occurrence:
                    f.write("The following slots are expected by policy but have ZERO occurrences in JSONL:\n\n")
                    for slot in sorted(zero_occurrence):
                        f.write(f"- `{slot}`\n")
                    f.write("\n")
                else:
                    f.write("✅ All policy-expected slots have at least one occurrence in JSONL.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("## Metadata\n\n")
            f.write(f"- **Script**: `tools/audit/slot_coverage_audit.py`\n")
            f.write(f"- **Execution Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **JSONL Rows**: {len(self.rows)}\n")
            f.write(f"- **Insurers**: {len(self.insurer_stats)}\n")
            f.write(f"- **Unique Slots**: {len(self.all_slots)}\n")
            f.write(f"- **Premium Gate (Q12)**: **{premium_gate['gate_status']}**\n")
            f.write("\n")

        print(f"[INFO] Markdown report written to: {output_path}")

    def generate_csv_report(self, output_path: str) -> None:
        """Generate CSV report with slot coverage data."""
        print(f"[INFO] Generating CSV report: {output_path}")

        global_stats = self.compute_global_stats()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "insurer", "slot", "present_count", "missing_count",
                "total_count", "present_ratio"
            ])

            # Per-insurer slot data
            for insurer in sorted(self.insurer_stats.keys()):
                stats = self.insurer_stats[insurer]

                for slot in sorted(self.all_slots):
                    present = stats["slot_presence"].get(slot, 0)
                    missing = stats["slot_missing"].get(slot, 0)
                    total = present + missing
                    ratio = present / total if total > 0 else 0.0

                    writer.writerow([
                        insurer, slot, present, missing, total, f"{ratio:.4f}"
                    ])

        print(f"[INFO] CSV report written to: {output_path}")

    def generate_json_report(self, output_path: str) -> None:
        """Generate JSON report (machine-readable)."""
        print(f"[INFO] Generating JSON report: {output_path}")

        global_stats = self.compute_global_stats()
        premium_gate = self.check_premium_gate_q12()

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "jsonl_source": self.jsonl_path,
                "policy_source": self.policy_json_path,
                "total_rows": len(self.rows),
                "total_insurers": len(self.insurer_stats),
                "total_slots": len(self.all_slots)
            },
            "premium_gate_q12": premium_gate,
            "insurer_stats": {
                insurer: {
                    "row_count": stats["row_count"],
                    "slot_presence": dict(stats["slot_presence"]),
                    "slot_missing": dict(stats["slot_missing"])
                }
                for insurer, stats in self.insurer_stats.items()
            },
            "global_stats": global_stats
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"[INFO] JSON report written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-V0: Slot Coverage Audit for compare_rows_v1.jsonl"
    )
    parser.add_argument(
        "--jsonl",
        required=True,
        help="Path to compare_rows_v1.jsonl"
    )
    parser.add_argument(
        "--policy_json",
        default=None,
        help="Path to question_card_routing.json (optional)"
    )
    parser.add_argument(
        "--premium_slot",
        default="premium_monthly",
        help="Name of premium slot to check for Q12 gate (default: premium_monthly)"
    )
    parser.add_argument(
        "--out_md",
        required=True,
        help="Output path for Markdown report"
    )
    parser.add_argument(
        "--out_csv",
        required=True,
        help="Output path for CSV report"
    )
    parser.add_argument(
        "--out_json",
        default=None,
        help="Output path for JSON report (optional)"
    )

    args = parser.parse_args()

    # Create auditor
    auditor = SlotCoverageAuditor(
        jsonl_path=args.jsonl,
        policy_json_path=args.policy_json,
        premium_slot=args.premium_slot
    )

    # Execute audit
    auditor.load_jsonl()
    auditor.load_policy()
    auditor.audit_rows()

    # Generate reports
    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    auditor.generate_markdown_report(args.out_md)
    auditor.generate_csv_report(args.out_csv)

    if args.out_json:
        auditor.generate_json_report(args.out_json)

    # Print summary
    premium_gate = auditor.check_premium_gate_q12()
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)
    print(f"Total Rows: {len(auditor.rows)}")
    print(f"Total Insurers: {len(auditor.insurer_stats)}")
    print(f"Total Slots: {len(auditor.all_slots)}")
    print(f"Premium Gate (Q12): {premium_gate['gate_status']}")
    print(f"Reports Generated:")
    print(f"  - {args.out_md}")
    print(f"  - {args.out_csv}")
    if args.out_json:
        print(f"  - {args.out_json}")
    print("="*60)

    # Exit with status code based on premium gate
    if premium_gate['gate_status'] == "FAIL":
        print("[WARN] Premium gate check FAILED - some insurers have missing premium data")
        # Don't exit with error code, just report status

    return 0


if __name__ == "__main__":
    sys.exit(main())
