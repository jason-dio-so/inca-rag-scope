"""
Comparison Table Builder - STEP NEXT-68

Converts Step3 gated output to comparison rows and tables.

NO LLM. NO inference. Evidence-first only.
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


class CompareRowBuilder:
    """Builds CompareRow from Step3 gated coverage"""

    SLOT_NAMES = [
        "start_date",
        "exclusions",
        "payout_limit",
        "reduction",
        "entry_age",
        "waiting_period"
    ]

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
        """Build all comparison slots"""
        slots = {}

        evidence_status = coverage.get("evidence_status", {})
        evidence_slots = coverage.get("evidence_slots", {})
        evidences = coverage.get("evidence", [])

        for slot_name in self.SLOT_NAMES:
            status = evidence_status.get(slot_name, "UNKNOWN")

            # Get slot metadata
            slot_meta = evidence_slots.get(slot_name, {})
            value = slot_meta.get("value")
            reason = slot_meta.get("reason")

            # Get evidences for this slot
            slot_evidences = [
                self._build_evidence_reference(ev)
                for ev in evidences
                if ev.get("slot_key") == slot_name
            ]

            # Build notes from reason or gate status
            notes = reason if reason else None

            slots[slot_name] = SlotValue(
                status=status,
                value=value,
                evidences=slot_evidences,
                notes=notes
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

    def __init__(self):
        self.row_builder = CompareRowBuilder()
        self.table_builder = CompareTableBuilder()

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
