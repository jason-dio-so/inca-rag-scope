#!/usr/bin/env python3
"""
STEP NEXT-72-OPS: Unified Pipeline Runner (Zero-Tolerance Execution Safety)

Single entry point for Step2-b → Step3 → Step4 execution.
Prevents mis-execution through strict input contract validation.

Constitutional Rules:
- NO direct module execution allowed
- EVERY step MUST pass INPUT GATE before execution
- ALL outputs MUST generate run_receipt.json
- Gate failures → exit 2 (hard fail)

Usage:
    python tools/run_pipeline.py --stage step2b
    python tools/run_pipeline.py --stage step3
    python tools/run_pipeline.py --stage step4
    python tools/run_pipeline.py --stage all  # Run Step2-b → Step3 → Step4
"""

import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class PipelineRunner:
    """Unified pipeline runner with zero-tolerance safety gates"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.ssot_dir = self.project_root / "data" / "scope_v3"
        self.receipt_file = self.project_root / "docs" / "audit" / "run_receipt.json"
        self.receipts = self._load_receipts()

    def _load_receipts(self) -> List[Dict]:
        """Load existing run receipts"""
        if self.receipt_file.exists():
            with open(self.receipt_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_receipt(self, receipt: Dict):
        """Save execution receipt"""
        self.receipts.append(receipt)
        self.receipt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.receipt_file, 'w', encoding='utf-8') as f:
            json.dump(self.receipts, f, indent=2, ensure_ascii=False)

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file"""
        if not file_path.exists():
            return ""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]  # First 16 chars

    def _count_lines(self, file_path: Path) -> int:
        """Count non-empty lines in JSONL file"""
        if not file_path.exists():
            return 0
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())

    def _validate_step2b_output(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate Step2-b output contract.

        Required:
        - Filename ends with _step2_canonical_scope_v1.jsonl
        - Contains required fields: coverage_code, mapping_method, insurer_key, product, variant
        - Schema: scope_v3_step2b_v1
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        if not file_path.name.endswith("_step2_canonical_scope_v1.jsonl"):
            return False, f"Invalid Step2-b filename: {file_path.name} (expected *_step2_canonical_scope_v1.jsonl)"

        # Reject Step1 or Step2-a files
        if "_step1_" in file_path.name or "_step2_sanitized_" in file_path.name:
            return False, f"REJECTED: Wrong step input detected: {file_path.name} (Step2-b requires *_step2_canonical_scope_v1.jsonl)"

        # Check schema
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line.strip():
                return False, "Empty file"

            try:
                obj = json.loads(first_line)

                # Required fields
                required_fields = ['coverage_code', 'mapping_method', 'insurer_key', 'product', 'variant']
                missing = [f for f in required_fields if f not in obj]
                if missing:
                    return False, f"Missing required Step2-b fields: {missing}"

                # Check product/variant structure
                if not isinstance(obj.get('product'), dict) or 'product_key' not in obj['product']:
                    return False, "Missing product.product_key"

                if not isinstance(obj.get('variant'), dict) or 'variant_key' not in obj['variant']:
                    return False, "Missing variant.variant_key"

            except json.JSONDecodeError:
                return False, "Invalid JSON"

        return True, ""

    def _validate_step3_output(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate Step3 output contract.

        Required:
        - Filename ends with _step3_evidence_enriched_v1_gated.jsonl
        - Contains required fields: evidence, evidence_status, insurer_key
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        if not file_path.name.endswith("_step3_evidence_enriched_v1_gated.jsonl"):
            # Also accept ungated for backwards compatibility
            if not file_path.name.endswith("_step3_evidence_enriched_v1.jsonl"):
                return False, f"Invalid Step3 filename: {file_path.name} (expected *_step3_evidence_enriched_v1_gated.jsonl)"

        # Reject Step1, Step2-a, or Step2-b files
        if "_step1_" in file_path.name or "_step2_" in file_path.name:
            return False, f"REJECTED: Wrong step input detected: {file_path.name} (Step4 requires *_step3_evidence_enriched_v1_gated.jsonl)"

        # Check schema
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line.strip():
                return False, "Empty file"

            try:
                obj = json.loads(first_line)
                required_fields = ['evidence', 'evidence_status', 'insurer_key']
                missing = [f for f in required_fields if f not in obj]
                if missing:
                    return False, f"Missing required Step3 fields: {missing}"
            except json.JSONDecodeError:
                return False, "Invalid JSON"

        return True, ""

    def _compute_step2b_metrics(self, output_files: List[Path]) -> Dict:
        """Compute Step2-b metrics (mapped%, unmapped%)"""
        total_entries = 0
        total_mapped = 0
        total_unmapped = 0

        for f in output_files:
            with open(f, 'r', encoding='utf-8') as file:
                for line in file:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        total_entries += 1
                        if obj.get('mapping_method') == 'unmapped':
                            total_unmapped += 1
                        else:
                            total_mapped += 1
                    except json.JSONDecodeError:
                        continue

        pct_mapped = (total_mapped / total_entries * 100) if total_entries > 0 else 0.0

        return {
            "total_entries": total_entries,
            "mapped": total_mapped,
            "unmapped": total_unmapped,
            "pct_mapped": round(pct_mapped, 1)
        }

    def run_step2b(self, mapping_source: str = "approved") -> Dict:
        """
        Run Step2-b canonical mapping with SSOT gate enforcement.

        Args:
            mapping_source: "approved" (SSOT only) or "local" (with overrides)
        """
        print("=" * 80)
        print("STAGE: Step2-b (Canonical Mapping - STEP NEXT-73)")
        print("=" * 80)
        print(f"🚦 Mapping source mode: {mapping_source.upper()}")
        if mapping_source == "local":
            print("⚠️  WARNING: Using unapproved local overrides (testing only)")
        print()

        # Run Step2-b with mapping source parameter
        cmd = [
            sys.executable, "-m", "pipeline.step2_canonical_mapping.run",
            "--mapping-source", mapping_source
        ]
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Step2-b FAILED")
            print(result.stdout)
            print(result.stderr)
            sys.exit(2)

        print(result.stdout)

        # Collect outputs
        outputs = sorted(self.ssot_dir.glob("*_step2_canonical_scope_v1.jsonl"))

        if not outputs:
            print("❌ ERROR: No Step2-b outputs generated")
            sys.exit(2)

        # Validate all outputs
        for output_file in outputs:
            is_valid, error = self._validate_step2b_output(output_file)
            if not is_valid:
                print(f"❌ OUTPUT VALIDATION FAILED: {output_file.name}")
                print(f"   Error: {error}")
                sys.exit(2)

        # Compute metrics
        metrics = self._compute_step2b_metrics(outputs)

        # Generate receipt (STEP NEXT-73: Include mapping source)
        receipt = {
            "stage": "step2b",
            "timestamp": datetime.now().isoformat(),
            "input_pattern": "*_step2_sanitized_scope_v1.jsonl",
            "mapping_source": mapping_source,  # STEP NEXT-73
            "outputs": [
                {
                    "file": str(f.relative_to(self.project_root)),
                    "sha256": self._compute_file_hash(f),
                    "line_count": self._count_lines(f),
                    "schema_version": "scope_v3_step2b_v1"
                }
                for f in outputs
            ],
            "metrics": metrics,
            "status": "success"
        }

        self._save_receipt(receipt)

        print()
        print(f"✅ Step2-b completed: {len(outputs)} output(s)")
        print(f"   Metrics: {metrics['mapped']}/{metrics['total_entries']} mapped ({metrics['pct_mapped']}%)")
        print(f"📝 Receipt saved: {self.receipt_file}")

        return receipt

    def run_step3(self) -> Dict:
        """Run Step3 evidence enrichment"""
        print("=" * 80)
        print("STAGE: Step3 (Evidence Enrichment)")
        print("=" * 80)
        print()

        # INPUT GATE: Verify Step2-b outputs exist and are valid
        step2b_outputs = sorted(self.ssot_dir.glob("*_step2_canonical_scope_v1.jsonl"))

        if not step2b_outputs:
            print("❌ INPUT GATE FAILED: No Step2-b canonical outputs found")
            print(f"   Expected: {self.ssot_dir}/*_step2_canonical_scope_v1.jsonl")
            print(f"   Run Step2-b first: python tools/run_pipeline.py --stage step2b")
            sys.exit(2)

        print(f"INPUT GATE: Validating {len(step2b_outputs)} Step2-b output(s)...")
        for input_file in step2b_outputs:
            is_valid, error = self._validate_step2b_output(input_file)
            if not is_valid:
                print(f"❌ INPUT GATE FAILED: {input_file.name}")
                print(f"   Error: {error}")
                print(f"   Step3 REQUIRES valid Step2-b canonical outputs")
                print(f"   This is a HARD FAILURE to prevent pipeline mis-execution")
                sys.exit(2)
            print(f"  ✅ {input_file.name}")

        print()
        print("✅ INPUT GATE PASSED: All Step2-b outputs validated")
        print()

        # Check if Step3 script exists
        step3_script = self.project_root / "pipeline" / "step3_evidence_resolver" / "run.py"
        if not step3_script.exists():
            print(f"⚠️  Step3 runner not found: {step3_script}")
            print(f"   Skipping Step3 execution")
            return {"stage": "step3", "status": "skipped", "reason": "runner_not_found"}

        # Run Step3
        cmd = [sys.executable, str(step3_script)]
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Step3 FAILED")
            print(result.stdout)
            print(result.stderr)
            sys.exit(2)

        print(result.stdout)

        # Collect outputs
        outputs = sorted(self.ssot_dir.glob("*_step3_evidence_enriched_v1_gated.jsonl"))

        if not outputs:
            print("⚠️  WARNING: No Step3 gated outputs found")
            outputs = sorted(self.ssot_dir.glob("*_step3_evidence_enriched_v1.jsonl"))

        # Generate receipt
        receipt = {
            "stage": "step3",
            "timestamp": datetime.now().isoformat(),
            "inputs": [str(f.relative_to(self.project_root)) for f in step2b_outputs],
            "outputs": [
                {
                    "file": str(f.relative_to(self.project_root)),
                    "sha256": self._compute_file_hash(f),
                    "line_count": self._count_lines(f),
                    "schema_version": "v1"
                }
                for f in outputs
            ],
            "status": "success"
        }

        self._save_receipt(receipt)

        print()
        print(f"✅ Step3 completed: {len(outputs)} output(s)")
        print(f"📝 Receipt saved: {self.receipt_file}")

        return receipt

    def run_step4(self) -> Dict:
        """Run Step4 comparison model"""
        print("=" * 80)
        print("STAGE: Step4 (Comparison Model)")
        print("=" * 80)
        print()

        # INPUT GATE: Verify Step3 outputs exist and are valid
        step3_outputs = sorted(self.ssot_dir.glob("*_step3_evidence_enriched_v1_gated.jsonl"))

        if not step3_outputs:
            # Try ungated
            step3_outputs = sorted(self.ssot_dir.glob("*_step3_evidence_enriched_v1.jsonl"))

        if not step3_outputs:
            print("❌ INPUT GATE FAILED: No Step3 evidence outputs found")
            print(f"   Expected: {self.ssot_dir}/*_step3_evidence_enriched_v1_gated.jsonl")
            print(f"   Run Step3 first: python tools/run_pipeline.py --stage step3")
            sys.exit(2)

        print(f"INPUT GATE: Found {len(step3_outputs)} Step3 output(s)")
        for input_file in step3_outputs:
            is_valid, error = self._validate_step3_output(input_file)
            if not is_valid:
                print(f"❌ INPUT GATE FAILED: {input_file.name}")
                print(f"   Error: {error}")
                print(f"   Step4 REQUIRES valid Step3 evidence outputs")
                print(f"   This is a HARD FAILURE to prevent pipeline mis-execution")
                sys.exit(2)
            print(f"  ✅ {input_file.name}")

        print()
        print("✅ INPUT GATE PASSED: All Step3 outputs validated")
        print()

        # Check if Step4 script exists
        step4_script = self.project_root / "pipeline" / "step4_compare_model" / "run.py"
        if not step4_script.exists():
            print(f"⚠️  Step4 runner not found: {step4_script}")
            print(f"   Skipping Step4 execution")
            return {"stage": "step4", "status": "skipped", "reason": "runner_not_found"}

        # Extract insurer keys from Step3 files
        insurers = []
        for step3_file in step3_outputs:
            # Extract insurer from filename: {insurer}_step3_evidence_enriched_v1_gated.jsonl
            insurer = step3_file.stem.replace("_step3_evidence_enriched_v1_gated", "").replace("_step3_evidence_enriched_v1", "")
            if insurer:
                insurers.append(insurer)

        # Run Step4 with module syntax
        cmd = [sys.executable, "-m", "pipeline.step4_compare_model.run", "--insurers"] + insurers
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Step4 FAILED")
            print(result.stdout)
            print(result.stderr)
            sys.exit(2)

        print(result.stdout)

        # Collect outputs
        compare_dir = self.project_root / "data" / "compare_v1"
        outputs = []
        if compare_dir.exists():
            outputs = sorted(compare_dir.glob("*.jsonl"))

        # Generate receipt
        receipt = {
            "stage": "step4",
            "timestamp": datetime.now().isoformat(),
            "inputs": [str(f.relative_to(self.project_root)) for f in step3_outputs],
            "outputs": [
                {
                    "file": str(f.relative_to(self.project_root)),
                    "sha256": self._compute_file_hash(f),
                    "line_count": self._count_lines(f),
                    "schema_version": "v1"
                }
                for f in outputs
            ],
            "status": "success"
        }

        self._save_receipt(receipt)

        print()
        print(f"✅ Step4 completed: {len(outputs)} output(s)")
        print(f"📝 Receipt saved: {self.receipt_file}")

        return receipt

    def run_all(self) -> List[Dict]:
        """Run Step2-b → Step3 → Step4"""
        print("=" * 80)
        print("UNIFIED PIPELINE: Step2-b → Step3 → Step4")
        print("=" * 80)
        print()

        receipts = []

        # Step2-b
        receipt_2b = self.run_step2b()
        receipts.append(receipt_2b)
        print()

        # Step3
        receipt_3 = self.run_step3()
        receipts.append(receipt_3)
        print()

        # Step4
        receipt_4 = self.run_step4()
        receipts.append(receipt_4)
        print()

        # Summary
        print("=" * 80)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        for receipt in receipts:
            stage = receipt['stage']
            status = receipt.get('status', 'unknown')
            output_count = len(receipt.get('outputs', []))
            print(f"  {stage:10s}: {status:10s} ({output_count} outputs)")

        print()
        print(f"✅ Full pipeline completed")
        print(f"📝 All receipts saved: {self.receipt_file}")

        return receipts


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="STEP NEXT-72-OPS: Unified Pipeline Runner (Zero-Tolerance Safety)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--stage",
        choices=["step2b", "step3", "step4", "all"],
        required=True,
        help="Pipeline stage to run"
    )

    args = parser.parse_args()

    runner = PipelineRunner()

    if args.stage == "step2b":
        runner.run_step2b()
    elif args.stage == "step3":
        runner.run_step3()
    elif args.stage == "step4":
        runner.run_step4()
    elif args.stage == "all":
        runner.run_all()

    return 0


if __name__ == "__main__":
    sys.exit(main())
