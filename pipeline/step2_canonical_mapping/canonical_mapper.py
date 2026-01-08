#!/usr/bin/env python3
"""
STEP NEXT-47: Canonical Mapping Logic
=======================================

Deterministic pattern-based mapping to 신정원 unified coverage codes.

Mapping methods (in priority order):
    1. exact: Exact match with 담보명(가입설계서)
    2. normalized: After suffix/prefix removal (Ⅱ, (갱신형), 담보, etc)
    3. alias: Known alias table
    4. unmapped: No match found

Constitutional enforcement:
    - NO LLM / NO inference
    - NO arbitrary code generation
    - Unmapped when ambiguous
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd


# Insurer code mapping (신정원 ins_cd)
# STEP NEXT-50: Fixed DB code from N11 to N13
INSURER_CODE_MAP = {
    'meritz': 'N01',
    'hanwha': 'N02',
    'lotte': 'N03',
    'heungkuk': 'N05',
    'samsung': 'N08',
    'hyundai': 'N09',
    'kb': 'N10',
    'db': 'N13'  # Fixed: DB uses N13, not N11
}


class CanonicalMapper:
    """신정원 canonical coverage mapper (deterministic only)"""

    def __init__(self, mapping_excel_path: Path):
        self.mapping_excel_path = mapping_excel_path
        self.canonical_df = self._load_canonical_mapping()
        self.insurer_mappings = self._build_insurer_mappings()

    def _load_canonical_mapping(self) -> pd.DataFrame:
        """
        Load 신정원 canonical mapping Excel with audit logging.

        STEP NEXT-50: Added Excel loader audit and validation.
        """
        import logging
        logger = logging.getLogger(__name__)

        df = pd.read_excel(self.mapping_excel_path)

        # Expected columns: ins_cd, 보험사명, cre_cvr_cd, 신정원코드명, 담보명(가입설계서)
        required_cols = ['ins_cd', 'cre_cvr_cd', '신정원코드명', '담보명(가입설계서)']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns in mapping Excel: {required_cols}")

        # STEP NEXT-50: Audit logging
        logger.info(f"Excel loaded: {len(df)} total rows")

        # Per-insurer distribution
        insurer_counts = df['ins_cd'].value_counts().sort_index()
        for ins_cd, count in insurer_counts.items():
            logger.info(f"  {ins_cd}: {count} rows")

        # Verify DB (N13) exists
        db_rows = len(df[df['ins_cd'] == 'N13'])
        if db_rows == 0:
            logger.warning("No DB (N13) rows found in mapping Excel!")
        else:
            logger.info(f"DB (N13): {db_rows} rows found")

        return df

    def _build_insurer_mappings(self) -> Dict[str, Dict[str, Dict]]:
        """
        Build per-insurer mapping dictionaries.

        Returns:
            {
                'samsung': {
                    'exact': {
                        '질병사망': {'code': 'A1100', 'name': '질병사망'},
                        ...
                    },
                    'normalized': {
                        '질병사망': {'code': 'A1100', 'name': '질병사망'},
                        ...
                    }
                },
                ...
            }
        """
        mappings = {}

        for insurer, ins_cd in INSURER_CODE_MAP.items():
            insurer_df = self.canonical_df[self.canonical_df['ins_cd'] == ins_cd]

            # Build exact match dictionary
            exact_map = {}
            normalized_map = {}

            for _, row in insurer_df.iterrows():
                coverage_name = str(row['담보명(가입설계서)']).strip()
                match_info = {
                    'code': row['cre_cvr_cd'],
                    'name': row['신정원코드명'],
                    'original': coverage_name
                }

                # Exact match
                exact_map[coverage_name] = match_info

                # Normalized match
                normalized_name = self.normalize_coverage_name(coverage_name)
                if normalized_name:
                    # If multiple coverages normalize to same name, keep first
                    if normalized_name not in normalized_map:
                        normalized_map[normalized_name] = match_info

            mappings[insurer] = {
                'exact': exact_map,
                'normalized': normalized_map
            }

        return mappings

    @staticmethod
    def normalize_coverage_name(raw_name: str) -> str:
        """
        Normalize coverage name for fuzzy matching.

        STEP NEXT-56-C: Enhanced with common normalization rules.

        Removes:
            - Whitespace variations
            - Suffix markers: Ⅱ, Ⅲ, (갱신형), (1회한), (1년50%), etc
            - Fragment markers: )(갱신형)담보, 신형)담보
            - Prefix markers: [갱신형], [기본계약], etc
            - Trailing: 담보, 보장
            - Parentheses content variations
            - (기본) suffix (STEP NEXT-56-C)
            - Percent sign variations: 3%~100%, 3~100%, 3~100 % → normalized

        Args:
            raw_name: Raw coverage name from proposal

        Returns:
            Normalized name
        """
        name = raw_name.strip()

        # STEP NEXT-56-C: Remove bracket prefixes (common across insurers)
        # e.g., "[기본계약]", "[갱신형]"
        name = re.sub(r'^\[[^\]]+\]\s*', '', name)

        # Remove fragment patterns (Hyundai-specific)
        name = re.sub(r'\)\s*\(갱신형\)\s*담보', '', name)
        name = re.sub(r'신형\)\s*담보', '', name)

        # STEP NEXT-56-C: Remove (기본) suffix before other suffixes
        # e.g., "일반상해후유장해(20~100%)(기본)" → "일반상해후유장해(20~100%)"
        name = re.sub(r'\)\s*\(기본\)\s*$', ')', name)
        name = re.sub(r'\s*\(기본\)\s*$', '', name)

        # Remove suffix markers and conditions
        name = re.sub(r'[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹ]+$', '', name)
        name = re.sub(r'\s*\(갱신형\)\s*$', '', name)
        name = re.sub(r'\s*\(1회한\)\s*$', '', name)
        name = re.sub(r'\s*\(최초1회한\)\s*$', '', name)
        name = re.sub(r'\s*\(연간1회한\)\s*$', '', name)
        name = re.sub(r'\s*\(1년50%\)\s*$', '', name)
        name = re.sub(r'\s*\(1년\s*감액\)\s*$', '', name)
        name = re.sub(r'\s*\(1-180,요양병원제외\)\s*$', '', name)

        # STEP NEXT-56-C: Normalize percent sign variations
        # 3%~100% / 3~100% / 3~100 % / 3-100 → 3~100%
        # First, normalize tilde/hyphen: 3-100 → 3~100
        name = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1~\2', name)
        # Remove spaces around %
        name = re.sub(r'\s*%\s*', '%', name)
        # Remove % from first number in range: 3%~100% → 3~100%
        name = re.sub(r'(\d+)%~(\d+)', r'\1~\2', name)
        # Add % after range end ONLY if no % exists: 3~100 → 3~100%
        # Use word boundary to avoid matching "100" in "100%"
        name = re.sub(r'(\d+~\d+)(?!%)\b', r'\1%', name)

        # Remove parentheses content variations (after suffix removal)
        # e.g., "골절 진단비(치아파절(깨짐, 부러짐) 제외)" → "골절진단비(치아파절제외)"
        # First, remove nested content
        name = re.sub(r'\([^)]*\([^)]*\)[^)]*\)', lambda m: m.group(0).split('(')[0].strip(), name)
        # Simplify: "치아파절(깨짐, 부러짐) 제외" → "치아파절제외"
        name = re.sub(r'치아파절\([^)]+\)\s*제외', '치아파절제외', name)

        # Remove trailing keywords
        name = re.sub(r'\s*(담보|보장)\s*$', '', name)

        # Normalize whitespace (remove all spaces)
        name = re.sub(r'\s+', '', name)

        return name.strip()

    def map_coverage(
        self,
        insurer: str,
        coverage_name_normalized: str,
        coverage_name_raw: str = None
    ) -> Tuple[Optional[str], Optional[str], str, float, Dict]:
        """
        Map coverage to canonical code/name.

        STEP NEXT-55: Now uses coverage_name_normalized from Step2-a as primary input.
        STEP NEXT-56-R: Case-insensitive insurer lookup (samsung/SAMSUNG both work)

        Args:
            insurer: Insurer name (samsung, hanwha, etc) - case-insensitive
            coverage_name_normalized: Normalized coverage name from Step2-a
            coverage_name_raw: Raw coverage name (for audit trail only)

        Returns:
            (coverage_code, canonical_name, mapping_method, confidence, evidence)
        """
        # STEP NEXT-56-R: Force lowercase for lookup (samsung/SAMSUNG → samsung)
        insurer_key = insurer.strip().lower()

        if insurer_key not in self.insurer_mappings:
            return None, None, 'unmapped', 0.0, {'error': 'INSURER_NOT_FOUND', 'input_insurer': insurer}

        exact_map = self.insurer_mappings[insurer_key]['exact']
        normalized_map = self.insurer_mappings[insurer_key]['normalized']

        # Method 1: Exact match (using normalized name from Step2-a)
        if coverage_name_normalized in exact_map:
            match = exact_map[coverage_name_normalized]
            return (
                match['code'],
                match['name'],
                'exact',
                1.0,
                {'source': '신정원_v2024.12', 'matched_term': coverage_name_normalized}
            )

        # Method 2: Normalized match (apply canonical normalization on top of Step2-a normalized)
        canonical_normalized = self.normalize_coverage_name(coverage_name_normalized)
        if canonical_normalized and canonical_normalized in normalized_map:
            match = normalized_map[canonical_normalized]
            return (
                match['code'],
                match['name'],
                'normalized',
                0.9,
                {'source': '신정원_v2024.12', 'matched_term': match['original']}
            )

        # No match found
        return None, None, 'unmapped', 0.0, {'source': '신정원_v2024.12'}


def validate_step2a_identity_fields(entry: Dict, line_num: int, input_file: Path) -> None:
    """
    STEP NEXT-62-B: GATE-3 validation for Step2-b input (Hard Fail)

    Validates that Step2-a output contains required identity fields.
    Same validation as Step2-a, enforced at Step2-b input gate.

    Args:
        entry: Entry dict from Step2-a sanitized scope
        line_num: Line number in input file
        input_file: Input file path

    Raises:
        SystemExit(2) on validation failure
    """
    required_fields = ['insurer_key', 'product', 'variant']

    for field in required_fields:
        if field not in entry or entry[field] is None:
            print(f"❌ GATE-3 FAIL (Step2-b): Missing '{field}' field")
            print(f"   File: {input_file}")
            print(f"   Line: {line_num}")
            print(f"   Coverage: {entry.get('coverage_name_raw', 'UNKNOWN')}")
            exit(2)

    # Check product.product_key
    if 'product_key' not in entry['product'] or not entry['product']['product_key']:
        print(f"❌ GATE-3 FAIL (Step2-b): Missing or empty 'product.product_key'")
        print(f"   File: {input_file}")
        print(f"   Line: {line_num}")
        print(f"   Coverage: {entry.get('coverage_name_raw', 'UNKNOWN')}")
        exit(2)

    # Check variant.variant_key
    if 'variant_key' not in entry['variant'] or not entry['variant']['variant_key']:
        print(f"❌ GATE-3 FAIL (Step2-b): Missing or empty 'variant.variant_key'")
        print(f"   File: {input_file}")
        print(f"   Line: {line_num}")
        print(f"   Coverage: {entry.get('coverage_name_raw', 'UNKNOWN')}")
        exit(2)


def map_sanitized_scope(
    input_jsonl: Path,
    output_jsonl: Path,
    report_jsonl: Path,
    mapping_excel_path: Path
) -> Dict:
    """
    Map sanitized scope to canonical coverage codes.

    STEP NEXT-62-B: Preserves product/variant identity fields from Step2-a.

    Args:
        input_jsonl: Input Step2-a sanitized scope JSONL
        output_jsonl: Output canonical scope JSONL
        report_jsonl: Mapping report JSONL
        mapping_excel_path: 신정원 mapping Excel path

    Returns:
        Statistics dict
    """
    if not input_jsonl.exists():
        return {'error': 'INPUT_NOT_FOUND'}

    # Load mapper
    mapper = CanonicalMapper(mapping_excel_path)

    # Read input with GATE-3 validation
    entries = []
    line_num = 0
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            line_num += 1
            if not line.strip():
                continue

            entry = json.loads(line)

            # STEP NEXT-62-B: GATE-3 validation (Hard Fail)
            validate_step2a_identity_fields(entry, line_num, input_jsonl)

            entries.append(entry)

    # Map
    mapped_entries = []
    mapping_stats = {
        'exact': 0,
        'normalized': 0,
        'unmapped': 0
    }

    for entry in entries:
        # STEP NEXT-62-B: Use insurer_key (NOT ins_cd) for mapping lookup
        # Constitutional rule: Mapping key = (insurer_key, coverage_name_normalized) ONLY
        insurer_key = entry['insurer_key']
        coverage_name_raw = entry['coverage_name_raw']
        coverage_name_normalized = entry.get('coverage_name_normalized', coverage_name_raw)

        # STEP NEXT-55: Use normalized name from Step2-a
        # STEP NEXT-62-B: Pass insurer_key (lowercase insurer code) for mapping
        code, canonical_name, method, confidence, evidence = mapper.map_coverage(
            insurer_key, coverage_name_normalized, coverage_name_raw
        )

        # STEP NEXT-62-B: Preserve identity fields from Step2-a (explicit mapping)
        mapped_entry = {
            # Identity fields (STEP NEXT-62-B: carry-through from Step2-a)
            'insurer_key': entry['insurer_key'],
            'ins_cd': entry.get('ins_cd'),
            'product': entry['product'],
            'variant': entry['variant'],
            'proposal_context': entry.get('proposal_context'),

            # Coverage fields (existing from Step2-a)
            'coverage_name_raw': coverage_name_raw,
            'coverage_name_normalized': coverage_name_normalized,
            'normalization_applied': entry.get('normalization_applied', []),

            # Proposal facts (existing from Step2-a)
            'proposal_facts': entry.get('proposal_facts'),
            'proposal_detail_facts': entry.get('proposal_detail_facts'),

            # Metadata from Step2-a
            'sanitized': entry.get('sanitized', True),
            'drop_reason': entry.get('drop_reason'),

            # Mapping results (NEW from Step2-b)
            'coverage_code': code,
            'canonical_name': canonical_name,
            'mapping_method': method,
            'mapping_confidence': confidence,
            'evidence': evidence
        }

        mapped_entries.append(mapped_entry)
        mapping_stats[method] = mapping_stats.get(method, 0) + 1

    # Write output
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for entry in mapped_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # Write mapping report (STEP NEXT-62-B: Include identity fields)
    report_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(report_jsonl, 'w', encoding='utf-8') as f:
        for entry in mapped_entries:
            # STEP NEXT-62-B: Enhanced report with 4-dimension identity
            report_entry = {
                # Identity fields (STEP NEXT-62-B)
                'insurer_key': entry['insurer_key'],
                'ins_cd': entry['ins_cd'],
                'product_key': entry['product']['product_key'],
                'variant_key': entry['variant']['variant_key'],

                # Coverage fields
                'coverage_name_raw': entry['coverage_name_raw'],
                'coverage_name_normalized': entry['coverage_name_normalized'],

                # Mapping results
                'coverage_code': entry['coverage_code'],
                'canonical_name': entry['canonical_name'],
                'mapping_method': entry['mapping_method'],
                'mapping_confidence': entry['mapping_confidence'],

                # Mapping evidence (for debugging)
                'matched_term': entry['evidence'].get('matched_term'),
                'reason': 'NO_EXACT_MATCH' if entry['mapping_method'] == 'unmapped' else entry['mapping_method'].upper()
            }
            f.write(json.dumps(report_entry, ensure_ascii=False) + '\n')

    # Calculate statistics
    total = len(entries)
    mapped = total - mapping_stats.get('unmapped', 0)

    return {
        'input_total': total,
        'mapped': mapped,
        'unmapped': mapping_stats.get('unmapped', 0),
        'mapping_stats': mapping_stats,
        'mapping_rate': mapped / total if total > 0 else 0.0
    }


def verify_no_reduction(
    input_jsonl: Path,
    output_jsonl: Path
) -> Tuple[bool, str]:
    """
    Gate: Verify no row reduction (anti-contamination).

    Args:
        input_jsonl: Input Step2-a sanitized scope
        output_jsonl: Output canonical scope

    Returns:
        (is_valid, error_message)
    """
    if not input_jsonl.exists():
        return False, 'INPUT_NOT_FOUND'

    if not output_jsonl.exists():
        return False, 'OUTPUT_NOT_FOUND'

    # Count rows
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        input_count = sum(1 for line in f if line.strip())

    with open(output_jsonl, 'r', encoding='utf-8') as f:
        output_count = sum(1 for line in f if line.strip())

    if output_count < input_count:
        return False, f'ROW_REDUCTION: {input_count} → {output_count} ({input_count - output_count} rows lost)'

    return True, ''
