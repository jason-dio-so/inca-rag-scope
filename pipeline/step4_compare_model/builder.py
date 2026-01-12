"""
Comparison Table Builder - STEP NEXT-68

Converts Step3 gated output to comparison rows and tables.

NO LLM. NO inference. Evidence-first only.

STEP NEXT-F: Coverage Attribution Gate (G5) integrated.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from .model import (
    CompareRow,
    CompareTable,
    CoverageIdentity,
    CoverageSemantics,
    SlotValue,
    EvidenceReference,
    extract_coverage_code,
    extract_coverage_title,
    normalize_coverage_title
)
from .gates import (
    DiagnosisCoverageRegistry,
    CoverageAttributionValidator,
    SlotGateValidator,
    SlotTierEnforcementGate,
    ConfidenceLabeler
)


class CompareRowBuilder:
    """
    Builds CompareRow from Step3 gated coverage.

    STEP NEXT-F: G5 Coverage Attribution Gate applied.
    """

    SLOT_NAMES = [
        "start_date",
        "exclusions",
        "payout_limit",
        "reduction",
        "entry_age",
        "waiting_period",
        # STEP NEXT-76-A: Extended slots
        "underwriting_condition",
        "mandatory_dependency",
        "payout_frequency",
        "industry_aggregate_limit",
        # STEP NEXT-R: Premium slot (Q12 only, injected separately)
        # "premium_monthly"  # Not from Step3 evidence
    ]

    def __init__(self):
        """Initialize with G5 gate validator and G6 tier enforcement"""
        self.gate_validator = SlotGateValidator()
        self.tier_gate = SlotTierEnforcementGate()

    def build_row(self, step3_coverage: Dict) -> CompareRow:
        """
        Build CompareRow from Step3 gated coverage.

        Args:
            step3_coverage: Coverage dict from step3_evidence_enriched_v1_gated.jsonl

        Returns:
            CompareRow instance
        """
        # Extract identity
        identity = self._build_identity(step3_coverage)

        # Extract semantics (optional)
        semantics = self._build_semantics(step3_coverage)

        # Extract slots
        slots = self._build_slots(step3_coverage)

        # Build renewal condition from semantics
        renewal_condition = self._build_renewal_condition(semantics)

        # Calculate metadata
        slot_status_summary = self._calculate_status_summary(step3_coverage)

        # Coverage-level conflict: TRUE if ANY slot has CONFLICT status
        # (Each slot can have CONFLICT when documents disagree within that slot)
        has_conflict = self._has_conflict(step3_coverage)

        # STEP NEXT-70-ANCHOR-FIX:
        # anchored := coverage_code exists (from Step2-b canonical mapping)
        # Absolute rule: unanchored = NOT bool(coverage_code)
        unanchored = not bool(identity.coverage_code)

        return CompareRow(
            identity=identity,
            semantics=semantics,
            **slots,
            renewal_condition=renewal_condition,
            slot_status_summary=slot_status_summary,
            has_conflict=has_conflict,
            unanchored=unanchored
        )

    def _build_identity(self, coverage: Dict) -> CoverageIdentity:
        """
        Build CoverageIdentity from Step3 coverage.

        STEP NEXT-70-ANCHOR-FIX:
        - coverage_code comes from Step2-b canonical mapping (SSOT: 신정원 통일코드)
        - NOT extracted via regex from coverage_name_raw
        - coverage_code exists IFF Step2-b mapping succeeded
        """
        coverage_name_raw = coverage.get("coverage_name_raw", "")

        # SSOT: Use coverage_code from Step2-b canonical mapping
        coverage_code = coverage.get("coverage_code")

        # Normalize to None if empty string
        if coverage_code == "":
            coverage_code = None

        # Extract title for display (still use regex helper)
        coverage_title = extract_coverage_title(coverage_name_raw)
        coverage_title = normalize_coverage_title(coverage_title)

        return CoverageIdentity(
            insurer_key=coverage.get("insurer_key", ""),
            product_key=coverage.get("product", {}).get("product_key", ""),
            variant_key=coverage.get("variant", {}).get("variant_key", "default"),
            coverage_code=coverage_code,
            coverage_title=coverage_title,
            coverage_name_raw=coverage_name_raw
        )

    def _build_semantics(self, coverage: Dict) -> Optional[CoverageSemantics]:
        """Build CoverageSemantics from Step1 proposal_facts"""
        semantics_dict = coverage.get("proposal_facts", {}).get("coverage_semantics", {})

        if not semantics_dict:
            return None

        return CoverageSemantics(
            exclusions=semantics_dict.get("exclusions", []),
            payout_limit_count=semantics_dict.get("payout_limit_count"),
            payout_limit_type=semantics_dict.get("payout_limit_type"),
            renewal_flag=semantics_dict.get("renewal_flag", False),
            renewal_type=semantics_dict.get("renewal_type"),
            coverage_modifiers=semantics_dict.get("coverage_modifiers", [])
        )

    def _build_slots(self, coverage: Dict) -> Dict[str, SlotValue]:
        """
        Build all comparison slots.

        STEP NEXT-F: Apply G5 Coverage Attribution Gate to all slots.
        STEP NEXT-I: Apply G6 Slot Tier Enforcement Gate.
        """
        slots = {}

        evidence_status = coverage.get("evidence_status", {})
        evidence_slots = coverage.get("evidence_slots", {})
        evidences = coverage.get("evidence", [])

        # Get coverage identity for G5 gate
        coverage_code = coverage.get("coverage_code")
        coverage_name = coverage.get("coverage_name_normalized", "")

        for slot_name in self.SLOT_NAMES:
            # STEP NEXT-I: G6 - Check if slot can be used in comparison
            tier_check = self.tier_gate.validate_comparison_usage(slot_name)
            if not tier_check["valid"]:
                # Skip Tier-C slots entirely (don't add to slots dict)
                continue

            status = evidence_status.get(slot_name, "UNKNOWN")

            # Get slot metadata
            slot_meta = evidence_slots.get(slot_name, {})
            value = slot_meta.get("value")
            reason = slot_meta.get("reason")

            # STEP NEXT-Y: For payout_limit, prioritize proposal_facts.coverage_amount_text
            # Evidence search with "회한" keywords extracts occurrence limits, NOT amounts
            # For diagnosis coverages (e.g., A4200_1), coverage_amount_text is the payout_limit
            from_proposal_facts = False
            if slot_name == "payout_limit":
                proposal_facts = coverage.get("proposal_facts", {})
                coverage_amount_text = proposal_facts.get("coverage_amount_text")

                if coverage_amount_text:
                    # Parse amount to integer (원 units)
                    parsed_amount = self._parse_amount_to_won(coverage_amount_text)
                    if parsed_amount is not None:
                        value = str(parsed_amount)
                        status = "FOUND"
                        from_proposal_facts = True
                        # Keep reason if evidence extraction also found something
                        if slot_meta.get("value"):
                            reason = f"proposal_facts (evidence: {slot_meta.get('value')})"
                        else:
                            reason = "proposal_facts.coverage_amount_text"

            # Get evidences for this slot
            slot_evidences = [
                self._build_evidence_reference(ev)
                for ev in evidences
                if ev.get("slot_key") == slot_name
            ]

            # Build notes from reason or gate status
            notes = reason if reason else None

            # STEP NEXT-F: Apply G5 Coverage Attribution Gate
            # STEP NEXT-Y: Skip G5 for payout_limit from proposal_facts (no evidence excerpts)
            # Build temporary slot_data for validation
            slot_data = {
                "status": status,
                "value": value,
                "evidences": [
                    {
                        "excerpt": ev.excerpt,
                        "doc_type": ev.doc_type,
                        "page": ev.page
                    }
                    for ev in slot_evidences
                ]
            }

            # Skip G5 gate if payout_limit comes from proposal_facts (trusted source)
            if from_proposal_facts:
                gate_result = {"valid": True}
            else:
                gate_result = self.gate_validator.validate_slot(
                    slot_name,
                    slot_data,
                    coverage_code or "",
                    coverage_name
                )

            # If gate validation failed, demote to UNKNOWN
            if not gate_result["valid"]:
                status = "UNKNOWN"
                value = None
                gate_violation = gate_result.get("gate_violation")
                gate_reason = gate_result.get("reason")

                # Update notes with gate violation info
                if gate_reason:
                    notes = f"G5 Gate: {gate_reason}" + (f" ({notes})" if notes else "")
                else:
                    notes = f"G5 Gate: {gate_violation}" + (f" ({notes})" if notes else "")

            # STEP NEXT-I: G6 - Apply tier-specific output policy
            tier_output = self.tier_gate.validate_value_output(
                slot_name,
                slot_data,
                gate_result if gate_result else None
            )

            # Use display_value from G6 (handles "❓ 정보 없음" and "(상품 기준)" suffix)
            if tier_output.get("display_value") is not None:
                value = tier_output["display_value"]

            # If G6 says display should be "❓ 정보 없음", update status
            if value == "❓ 정보 없음":
                status = "UNKNOWN"
                value = None

            # STEP NEXT-K: Assign confidence label (Tier-A only)
            evidence_dicts = [
                {
                    "doc_type": ev.doc_type,
                    "excerpt": ev.excerpt,
                    "page": ev.page
                }
                for ev in slot_evidences
            ]
            confidence = ConfidenceLabeler.assign_confidence(
                slot_name,
                status,
                evidence_dicts
            )

            slots[slot_name] = SlotValue(
                status=status,
                value=value,
                evidences=slot_evidences,
                notes=notes,
                confidence=confidence
            )

        return slots

    def _build_evidence_reference(self, evidence: Dict) -> EvidenceReference:
        """Build EvidenceReference from Step3 evidence entry"""
        return EvidenceReference(
            doc_type=evidence.get("doc_type", ""),
            page=evidence.get("page_start", 0),
            excerpt=evidence.get("excerpt", ""),
            locator=evidence.get("locator", {}),
            gate_status=evidence.get("gate_status")
        )

    def _parse_amount_to_won(self, amount_text: str) -> Optional[int]:
        """
        Parse Korean amount text to integer in 원 units.

        STEP NEXT-Y: Extract amount from coverage_amount_text for payout_limit.

        Examples:
            "3,000만원" -> 30000000
            "5천만원" -> 50000000
            "1억원" -> 100000000
            "500만원" -> 5000000

        Returns:
            Integer amount in 원, or None if parsing fails
        """
        import re

        if not amount_text:
            return None

        # Remove commas and spaces
        text = amount_text.replace(",", "").replace(" ", "")

        # Pattern: digits + unit (만원, 천만원, 억원, 원)
        # Example: "3000만원", "5천만원", "1억원"
        patterns = [
            (r'(\d+)억(\d+)만원', lambda m: int(m.group(1)) * 100000000 + int(m.group(2)) * 10000),
            (r'(\d+)억원', lambda m: int(m.group(1)) * 100000000),
            (r'(\d+)천만원', lambda m: int(m.group(1)) * 10000000),
            (r'(\d+)만원', lambda m: int(m.group(1)) * 10000),
            (r'(\d+)원', lambda m: int(m.group(1))),
        ]

        for pattern, converter in patterns:
            match = re.search(pattern, text)
            if match:
                return converter(match)

        return None

    def _build_renewal_condition(self, semantics: Optional[CoverageSemantics]) -> Optional[str]:
        """Build renewal condition string from semantics"""
        if not semantics or not semantics.renewal_flag:
            return None

        if semantics.renewal_type:
            return f"갱신형 ({semantics.renewal_type})"
        return "갱신형"

    def _calculate_status_summary(self, coverage: Dict) -> Dict[str, int]:
        """Calculate slot status distribution"""
        evidence_status = coverage.get("evidence_status", {})

        summary = defaultdict(int)
        for status in evidence_status.values():
            summary[status] += 1

        return dict(summary)

    def _has_conflict(self, coverage: Dict) -> bool:
        """
        Check if coverage has any slot-level conflicts.

        Definition: A coverage has conflict if ANY of its evidence slots
        has CONFLICT status (meaning documents disagree for that slot).

        This is coverage-level conflict, aggregated from slot-level conflicts.
        """
        evidence_status = coverage.get("evidence_status", {})
        return "CONFLICT" in evidence_status.values()


class CompareTableBuilder:
    """Builds CompareTable from multiple CompareRows"""

    def build_table(
        self,
        table_id: str,
        rows: List[CompareRow],
        insurers: List[str] = None
    ) -> CompareTable:
        """
        Build CompareTable from rows.

        Args:
            table_id: Table identifier
            rows: List of CompareRow instances
            insurers: Optional list of insurers (inferred if not provided)

        Returns:
            CompareTable instance
        """
        if not rows:
            return CompareTable(
                table_id=table_id,
                insurers=[],
                product_keys=[],
                variant_keys=[],
                coverage_rows=[],
                total_rows=0
            )

        # Infer insurers, products, variants if not provided
        if insurers is None:
            insurers = list(set(row.identity.insurer_key for row in rows))
            insurers.sort()

        product_keys = list(set(row.identity.product_key for row in rows))
        variant_keys = list(set(row.identity.variant_key for row in rows))

        # Sort rows by comparison_key for alignment
        sorted_rows = self._sort_rows_for_comparison(rows)

        # Calculate metadata
        total_rows = len(sorted_rows)
        conflict_count = sum(1 for row in sorted_rows if row.has_conflict)
        unknown_rate = self._calculate_unknown_rate(sorted_rows)

        # Generate warnings
        warnings = self._generate_warnings(sorted_rows, conflict_count, unknown_rate)

        return CompareTable(
            table_id=table_id,
            insurers=insurers,
            product_keys=product_keys,
            variant_keys=variant_keys,
            coverage_rows=sorted_rows,
            table_warnings=warnings,
            total_rows=total_rows,
            conflict_count=conflict_count,
            unknown_rate=unknown_rate
        )

    def _sort_rows_for_comparison(self, rows: List[CompareRow]) -> List[CompareRow]:
        """
        Sort rows for comparison table.

        Priority:
        1. Anchored rows (with coverage_code) first
        2. Then by coverage_code (alphanumeric sort)
        3. Unanchored rows last (sorted by title)

        STEP NEXT-70-ANCHOR-FIX:
        - coverage_code is alphanumeric (e.g., "A1300", "A4200_1")
        - Use string sort, not numeric
        """
        def sort_key(row: CompareRow):
            if row.unanchored:
                return (1, "", row.identity.coverage_title)
            else:
                code_str = row.identity.coverage_code or ""
                return (0, code_str, row.identity.coverage_title)

        return sorted(rows, key=sort_key)

    def _calculate_unknown_rate(self, rows: List[CompareRow]) -> float:
        """Calculate percentage of UNKNOWN slots"""
        if not rows:
            return 0.0

        total_slots = 0
        unknown_slots = 0

        for row in rows:
            summary = row.slot_status_summary
            total_slots += sum(summary.values())
            unknown_slots += summary.get("UNKNOWN", 0)

        if total_slots == 0:
            return 0.0

        return (unknown_slots / total_slots) * 100

    def _generate_warnings(
        self,
        rows: List[CompareRow],
        conflict_count: int,
        unknown_rate: float
    ) -> List[str]:
        """
        Generate table warnings based on quality metrics.

        Notes:
        - conflict_count = number of coverages with ANY slot having CONFLICT status
        - Each coverage's slot_status_summary shows per-slot conflict counts
        """
        warnings = []

        if conflict_count > 0:
            # Calculate total slot-level conflicts
            total_slot_conflicts = sum(
                row.slot_status_summary.get("CONFLICT", 0)
                for row in rows
            )
            warnings.append(
                f"CONFLICT detected in {conflict_count} coverages "
                f"({total_slot_conflicts} slot-level conflicts) (문서 불일치)"
            )

        if unknown_rate > 20:
            warnings.append(
                f"High UNKNOWN rate: {unknown_rate:.1f}% (근거 부족)"
            )

        unanchored_count = sum(1 for row in rows if row.unanchored)
        if unanchored_count > 0:
            warnings.append(
                f"{unanchored_count} coverages without coverage_code (정렬 제한)"
            )

        return warnings


class CompareBuilder:
    """High-level builder for comparison tables from Step3 files"""

    def __init__(self, db_conn=None):
        self.row_builder = CompareRowBuilder()
        self.table_builder = CompareTableBuilder()
        self.db_conn = db_conn  # STEP NEXT-R: For G10 Premium SSOT Gate

    def build_from_step3_files(
        self,
        step3_files: List[Path],
        output_dir: Path
    ) -> Dict[str, Path]:
        """
        Build comparison tables from Step3 gated files.

        Args:
            step3_files: List of step3_evidence_enriched_v1_gated.jsonl files
            output_dir: Output directory for compare_v1 files

        Returns:
            Dict with output file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build rows from all files
        all_rows = []
        insurer_keys = []

        for step3_file in step3_files:
            rows, insurer_key = self._load_rows_from_file(step3_file)
            all_rows.extend(rows)
            if insurer_key and insurer_key not in insurer_keys:
                insurer_keys.append(insurer_key)

        # Write compare_rows_v1.jsonl
        rows_file = output_dir / "compare_rows_v1.jsonl"
        self._write_rows(all_rows, rows_file)

        # Build comparison table
        table_id = f"compare_{'_'.join(insurer_keys)}"
        compare_table = self.table_builder.build_table(
            table_id,
            all_rows,
            insurers=insurer_keys
        )

        # Write compare_tables_v1.jsonl
        tables_file = output_dir / "compare_tables_v1.jsonl"
        self._write_table(compare_table, tables_file)

        return {
            "rows": rows_file,
            "tables": tables_file
        }

    def _load_rows_from_file(self, step3_file: Path) -> tuple[List[CompareRow], Optional[str]]:
        """Load CompareRows from a single Step3 gated file"""
        rows = []
        insurer_key = None

        with open(step3_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                coverage = json.loads(line)
                row = self.row_builder.build_row(coverage)
                rows.append(row)

                if insurer_key is None:
                    insurer_key = row.identity.insurer_key

        return rows, insurer_key

    def _write_rows(self, rows: List[CompareRow], output_file: Path):
        """Write CompareRows to JSONL"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')

    def _write_table(self, table: CompareTable, output_file: Path):
        """Write CompareTable to JSONL"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(table.to_dict(), ensure_ascii=False) + '\n')

    def inject_premium_for_q12(
        self,
        rows: List[CompareRow],
        question_id: str,
        age: int = 40,
        sex: str = "M",
        plan_variant: str = "NO_REFUND"
    ) -> List[CompareRow]:
        """
        Inject premium_monthly slot for Q12 comparison.

        STEP NEXT-R: G10 Premium SSOT Gate

        Args:
            rows: List of CompareRow instances
            question_id: Question identifier (must be Q12)
            age: Age for premium lookup (default: 40)
            sex: Sex for premium lookup (default: M)
            plan_variant: Plan variant (default: NO_REFUND)

        Returns:
            Updated rows with premium_monthly slot (if G10 PASS)
        """
        # Only inject premium for Q12
        if question_id != "Q12":
            return rows

        # Require database connection
        if not self.db_conn:
            # Skip premium injection if no DB connection
            return rows

        from .gates import PremiumSSOTGate

        premium_gate = PremiumSSOTGate(self.db_conn)

        # Group rows by insurer
        insurer_rows = {}
        for row in rows:
            insurer_key = row.identity.insurer_key
            if insurer_key not in insurer_rows:
                insurer_rows[insurer_key] = []
            insurer_rows[insurer_key].append(row)

        # Fetch premium for each insurer
        premium_results = []

        for insurer_key, insurer_row_list in insurer_rows.items():
            # Get product_id from first row
            if not insurer_row_list:
                continue

            product_id = insurer_row_list[0].identity.product_key

            # Fetch premium via G10 gate
            premium_result = premium_gate.fetch_premium(
                insurer_key=insurer_key,
                product_id=product_id,
                age=age,
                sex=sex,
                plan_variant=plan_variant
            )

            premium_results.append({
                "insurer_key": insurer_key,
                **premium_result
            })

            # If G10 PASS, inject premium_monthly slot into ALL rows for this insurer
            if premium_result["valid"]:
                premium_monthly = premium_result["premium_monthly"]
                source = premium_result["source"]
                conditions = premium_result["conditions"]

                # Build SlotValue for premium_monthly
                from .model import SlotValue

                premium_slot = SlotValue(
                    status="FOUND",
                    value={
                        "amount": premium_monthly,
                        "plan_variant": conditions["plan_variant"],
                        "currency": "KRW"
                    },
                    evidences=[],  # No DOC evidence for SSOT
                    notes=None,
                    confidence={
                        "level": "HIGH",
                        "basis": f"Premium SSOT ({source['table']})"
                    },
                    source_kind="PREMIUM_SSOT"
                )

                # Inject into all rows for this insurer
                for row in insurer_row_list:
                    row.premium_monthly = premium_slot

        # STEP NEXT-R: G10 HARD GATE - Q12 requires ALL insurers to have premium
        validation = premium_gate.validate_q12_premium_requirement(premium_results)

        if not validation["valid"]:
            # Q12 FAIL: Missing premium for some insurers
            # Log warning (actual enforcement happens in Step5/output layer)
            missing = validation["missing_insurers"]
            print(f"⚠️  G10 FAIL: Q12 requires premium for ALL insurers. Missing: {', '.join(missing)}")

        return rows
