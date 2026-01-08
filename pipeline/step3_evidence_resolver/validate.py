"""
Validation Script for STEP NEXT-67

DoD Verification:
- Select 5 KB coverages (including da Vinci)
- Verify:
  * At least 3 slots FOUND with evidence
  * Evidence includes page numbers and excerpts
  * UNKNOWN slots have reasons
  * Da Vinci coverage: exclusions/횟수/갱신 from Step1 + additional evidence
"""

import json
from pathlib import Path
from typing import List, Dict


class EvidenceValidator:
    """Validates evidence enrichment results"""

    def __init__(self, enriched_jsonl: Path):
        self.enriched_jsonl = enriched_jsonl
        self.coverages = self._load_coverages()

    def _load_coverages(self) -> List[Dict]:
        """Load all coverages from enriched file"""
        coverages = []
        with open(self.enriched_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    coverages.append(json.loads(line))
        return coverages

    def select_test_coverages(self, count: int = 5) -> List[Dict]:
        """
        Select diverse test coverages.

        Strategy:
        - Include da Vinci coverage (특수 coverage with exclusions/renewal)
        - Include basic coverages (상해, 질병)
        - Include diagnosis coverages (진단비)
        - Include surgery coverages (수술비)
        """
        selected = []

        # 1. Da Vinci coverage (priority)
        for cov in self.coverages:
            if "다빈치" in cov.get("coverage_name_raw", ""):
                selected.append(cov)
                break

        # 2. 암진단비 (exclusions present)
        for cov in self.coverages:
            name = cov.get("coverage_name_raw", "")
            if "암진단비" in name and "유사암제외" in name:
                selected.append(cov)
                break

        # 3. 상해사망 (basic coverage)
        for cov in self.coverages:
            if "상해사망" in cov.get("coverage_name_raw", ""):
                selected.append(cov)
                break

        # 4. 뇌혈관질환 (disease coverage)
        for cov in self.coverages:
            if "뇌혈관질환진단비" in cov.get("coverage_name_raw", ""):
                selected.append(cov)
                break

        # 5. 수술비 (surgery coverage)
        for cov in self.coverages:
            if "수술비" in cov.get("coverage_name_raw", ""):
                if cov not in selected:  # Avoid duplicates
                    selected.append(cov)
                    break

        return selected[:count]

    def validate_coverage(self, coverage: Dict) -> Dict:
        """
        Validate a single coverage.

        Returns validation result with pass/fail and details.
        """
        coverage_name = coverage.get("coverage_name_raw", "")
        evidence_status = coverage.get("evidence_status", {})
        evidence_slots = coverage.get("evidence_slots", {})
        evidence_list = coverage.get("evidence", [])

        result = {
            "coverage_name": coverage_name,
            "passed": True,
            "checks": {},
            "issues": []
        }

        # Check 1: At least 3 slots FOUND
        found_count = sum(1 for s in evidence_status.values() if s == "FOUND")
        result["checks"]["min_3_slots_found"] = found_count >= 3
        if found_count < 3:
            result["passed"] = False
            result["issues"].append(
                f"Only {found_count} slots found (expected >= 3)"
            )

        # Check 2: All FOUND slots have evidence entries
        for slot_key, status in evidence_status.items():
            if status == "FOUND":
                slot_evidences = [
                    e for e in evidence_list
                    if e.get("slot_key") == slot_key
                ]
                if not slot_evidences:
                    result["passed"] = False
                    result["issues"].append(
                        f"Slot '{slot_key}' marked FOUND but no evidence entries"
                    )

        # Check 3: Evidence entries have required fields
        for ev in evidence_list:
            required_fields = ["slot_key", "doc_type", "page_start", "excerpt"]
            missing = [f for f in required_fields if f not in ev]
            if missing:
                result["passed"] = False
                result["issues"].append(
                    f"Evidence missing fields: {missing}"
                )

        # Check 4: UNKNOWN slots have reasons
        for slot_key, status in evidence_status.items():
            if status == "UNKNOWN":
                slot_data = evidence_slots.get(slot_key, {})
                if not slot_data.get("reason"):
                    result["passed"] = False
                    result["issues"].append(
                        f"Slot '{slot_key}' is UNKNOWN but no reason provided"
                    )

        # Check 5 (da Vinci specific): Verify Step1 semantics preserved
        if "다빈치" in coverage_name:
            semantics = coverage.get("proposal_facts", {}).get(
                "coverage_semantics", {}
            )

            # Check exclusions preserved
            if semantics.get("exclusions"):
                result["checks"]["davinci_exclusions_preserved"] = True
            else:
                result["issues"].append("Da Vinci: exclusions not in semantics")

            # Check payout_limit preserved
            if semantics.get("payout_limit_count"):
                result["checks"]["davinci_payout_limit_preserved"] = True
            else:
                result["issues"].append("Da Vinci: payout_limit not in semantics")

            # Check renewal_flag preserved
            if semantics.get("renewal_flag"):
                result["checks"]["davinci_renewal_preserved"] = True
            else:
                result["issues"].append("Da Vinci: renewal_flag not in semantics")

        return result

    def run_validation(self):
        """Run full validation suite"""
        print("=" * 80)
        print("STEP NEXT-67: Evidence Resolver v1 - DoD Validation")
        print("=" * 80)
        print()

        # Select test coverages
        test_coverages = self.select_test_coverages(5)
        print(f"Selected {len(test_coverages)} test coverages:")
        for i, cov in enumerate(test_coverages, 1):
            print(f"  {i}. {cov.get('coverage_name_raw', 'Unknown')}")
        print()

        # Validate each
        all_passed = True
        for i, coverage in enumerate(test_coverages, 1):
            result = self.validate_coverage(coverage)

            print(f"[{i}] {result['coverage_name']}")
            print(f"    Status: {'✓ PASS' if result['passed'] else '✗ FAIL'}")

            # Print evidence stats
            evidence_status = coverage.get("evidence_status", {})
            found_slots = [k for k, v in evidence_status.items() if v == "FOUND"]
            unknown_slots = [k for k, v in evidence_status.items() if v == "UNKNOWN"]

            print(f"    Evidence slots:")
            print(f"      FOUND: {len(found_slots)} {found_slots}")
            print(f"      UNKNOWN: {len(unknown_slots)} {unknown_slots}")

            # Print sample evidence
            evidence_list = coverage.get("evidence", [])
            if evidence_list:
                sample = evidence_list[0]
                print(f"    Sample evidence:")
                print(f"      Slot: {sample.get('slot_key')}")
                print(f"      Doc: {sample.get('doc_type')}")
                print(f"      Page: {sample.get('page_start')}")
                excerpt = sample.get('excerpt', '')[:100]
                print(f"      Excerpt: {excerpt}...")

            # Print issues
            if result['issues']:
                print(f"    Issues:")
                for issue in result['issues']:
                    print(f"      - {issue}")

            print()

            if not result['passed']:
                all_passed = False

        # Final summary
        print("=" * 80)
        if all_passed:
            print("✓ VALIDATION PASSED: All DoD criteria met")
        else:
            print("✗ VALIDATION FAILED: Some criteria not met")
        print("=" * 80)

        return all_passed


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate STEP NEXT-67 evidence enrichment"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Enriched JSONL file to validate"
    )
    parser.add_argument(
        "--insurer",
        type=str,
        default="kb",
        help="Insurer key (default: kb)"
    )

    args = parser.parse_args()

    # Determine file path
    if args.file:
        enriched_file = Path(args.file)
    else:
        project_root = Path(__file__).parent.parent.parent
        enriched_file = (
            project_root / "data" / "scope_v3" /
            f"{args.insurer}_step3_evidence_enriched_v1.jsonl"
        )

    if not enriched_file.exists():
        print(f"Error: File not found: {enriched_file}")
        return 1

    # Run validation
    validator = EvidenceValidator(enriched_file)
    passed = validator.run_validation()

    return 0 if passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
