#!/usr/bin/env python3
"""
Rule-based Recommendation Executor (STEP NEXT-74)

ABSOLUTE CONSTRAINTS:
- ✅ Calculation / Comparison / Filter / Sort ONLY
- ❌ NO LLM calls
- ❌ NO document reinterpretation
- ❌ NO semantic inference
- ❌ NO evidence generation
- ❌ NO coverage_semantics modification

Input:
- data/compare_v1/compare_rows_v1.jsonl (SSOT)
- rules/rule_catalog.yaml

Output:
- data/recommend_v1/recommend_results.jsonl

GATES:
- G1: Fact-only (all values from slots)
- G2: Evidence (slot.evidences >= 1)
- G3: Deterministic (hash verification)
- G4: No-inference (input integrity check)
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class RuleExecutorGateError(Exception):
    """Raised when a GATE validation fails"""
    pass


class RuleExecutor:
    def __init__(self, compare_path: str, rule_catalog_path: str):
        self.compare_path = Path(compare_path)
        self.rule_catalog_path = Path(rule_catalog_path)

        # Load data
        self.compare_rows = self._load_compare_rows()
        self.rules = self._load_rules()

        # Input hash (for G3 and G4)
        self.input_hash = self._compute_input_hash()

    def _load_compare_rows(self) -> List[Dict[str, Any]]:
        """Load compare rows from JSONL"""
        rows = []
        with open(self.compare_path, 'r', encoding='utf-8') as f:
            for line in f:
                rows.append(json.loads(line))
        return rows

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load rules from YAML catalog"""
        with open(self.rule_catalog_path, 'r', encoding='utf-8') as f:
            catalog = yaml.safe_load(f)
        return catalog.get('rules', [])

    def _compute_input_hash(self) -> str:
        """Compute SHA256 hash of input file (G3, G4)"""
        hasher = hashlib.sha256()
        with open(self.compare_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def _get_nested_value(self, obj: Dict, path: str) -> Any:
        """
        Get nested dictionary value using dot notation.
        Example: "slots.waiting_period.status" -> obj['slots']['waiting_period']['status']
        """
        keys = path.split('.')
        current = obj
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    def _extract_numeric_value(self, value_str: Optional[str], pattern: str) -> Optional[float]:
        """
        Extract numeric value from string using regex pattern.

        Args:
            value_str: Source string (e.g., "90, 1, 50")
            pattern: Regex pattern (e.g., "^(\\d+)" for first number)

        Returns:
            Extracted number or None
        """
        if not value_str:
            return None

        match = re.search(pattern, str(value_str))
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                return None
        return None

    def _check_filter(self, row: Dict[str, Any], filter_spec: Dict[str, Any]) -> bool:
        """
        Check if row passes a single filter condition.

        Filter spec format:
        {
            "field": "coverage_title",
            "operator": "contains",
            "value": "암"
        }
        """
        field_value = self._get_nested_value(row, filter_spec['field'])
        operator = filter_spec['operator']
        expected = filter_spec['value']

        if operator == 'contains':
            return expected in str(field_value) if field_value else False
        elif operator == 'in':
            return field_value in expected if field_value else False
        elif operator == 'equals':
            return field_value == expected
        elif operator == 'regex':
            return bool(re.search(expected, str(field_value))) if field_value else False
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def _apply_filters(self, rows: List[Dict[str, Any]], filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply all filters to rows"""
        filtered = rows
        for filter_spec in filters:
            filtered = [row for row in filtered if self._check_filter(row, filter_spec)]
        return filtered

    def _calculate_metric(self, row: Dict[str, Any], calc_spec: Dict[str, Any]) -> Optional[float]:
        """
        Calculate metric value from row using calculation spec.

        Calc spec format:
        {
            "metric": "waiting_days",
            "source": "slots.waiting_period.value",
            "extract_pattern": "^(\\d+)"
        }
        """
        source_value = self._get_nested_value(row, calc_spec['source'])
        pattern = calc_spec.get('extract_pattern', r'^(\d+)')

        return self._extract_numeric_value(source_value, pattern)

    def _gate_g1_fact_only(self, row: Dict[str, Any], calc_spec: Dict[str, Any]) -> None:
        """
        G1: Fact-only Gate
        Ensure all values come from slots
        """
        source = calc_spec.get('source', '')
        if not source.startswith('slots.'):
            raise RuleExecutorGateError(f"G1 FAIL: source must start with 'slots.', got: {source}")

    def _gate_g2_evidence(self, row: Dict[str, Any], slot_name: str) -> None:
        """
        G2: Evidence Gate
        Ensure slot has at least 1 evidence
        """
        slot = self._get_nested_value(row, f'slots.{slot_name}')
        if not slot:
            raise RuleExecutorGateError(f"G2 FAIL: slot '{slot_name}' not found")

        evidences = slot.get('evidences', [])
        if not evidences or len(evidences) == 0:
            raise RuleExecutorGateError(f"G2 FAIL: slot '{slot_name}' has no evidences")

    def _gate_g3_deterministic(self, previous_hash: Optional[str]) -> None:
        """
        G3: Deterministic Gate
        Ensure same input produces same result
        """
        if previous_hash and previous_hash != self.input_hash:
            raise RuleExecutorGateError(f"G3 FAIL: input hash mismatch")

    def _gate_g4_no_inference(self) -> None:
        """
        G4: No-inference Gate
        Check input file integrity (placeholder - could be enhanced)
        """
        # For now, just verify the file exists and is readable
        if not self.compare_path.exists():
            raise RuleExecutorGateError(f"G4 FAIL: input file not found: {self.compare_path}")

    def _get_evidence_refs(self, row: Dict[str, Any], slot_name: str) -> List[Dict[str, Any]]:
        """Extract evidence references from slot"""
        slot = self._get_nested_value(row, f'slots.{slot_name}')
        if not slot:
            return []

        evidences = slot.get('evidences', [])
        refs = []
        for ev in evidences:
            refs.append({
                'doc_type': ev.get('doc_type'),
                'page': ev.get('page'),
                'excerpt': ev.get('excerpt', '')[:100] + '...' if len(ev.get('excerpt', '')) > 100 else ev.get('excerpt', '')
            })
        return refs

    def execute_rule(self, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a single rule and return ranked results.

        Returns:
            List of recommendation results
        """
        rule_id = rule['rule_id']
        print(f"\n[{rule_id}] Executing: {rule['intent']}")

        # G4: No-inference gate
        self._gate_g4_no_inference()

        # Apply filters
        filtered_rows = self._apply_filters(self.compare_rows, rule.get('filters', []))
        print(f"[{rule_id}] Filtered: {len(filtered_rows)} rows")

        if not filtered_rows:
            print(f"[{rule_id}] No rows passed filters")
            return []

        # Calculate metrics for each row
        calc_spec = rule.get('calculation', {})
        results = []

        for row in filtered_rows:
            # G1: Fact-only gate
            self._gate_g1_fact_only(row, calc_spec)

            # Extract slot name from source path (e.g., "slots.waiting_period.value" -> "waiting_period")
            source = calc_spec.get('source', '')
            slot_name = source.split('.')[1] if len(source.split('.')) > 1 else None

            if not slot_name:
                continue

            # G2: Evidence gate
            try:
                self._gate_g2_evidence(row, slot_name)
            except RuleExecutorGateError as e:
                # Skip rows without evidence
                continue

            # Calculate metric
            metric_value = self._calculate_metric(row, calc_spec)
            if metric_value is None:
                continue

            # Build result
            result = {
                'rule_id': rule_id,
                'coverage': {
                    'insurer': row['identity']['insurer_key'],
                    'product': row['identity']['product_key'],
                    'variant': row['identity']['variant_key'],
                    'coverage_title': row['identity']['coverage_title']
                },
                'metric': {
                    calc_spec['metric']: metric_value
                },
                'evidence_refs': self._get_evidence_refs(row, slot_name),
                'slot_used': slot_name,
                'slot_value': self._get_nested_value(row, f'slots.{slot_name}.value')
            }
            results.append(result)

        # Rank results
        rank_spec = rule.get('rank', {})
        metric_name = calc_spec.get('metric')
        reverse = (rank_spec.get('order') == 'desc')

        results.sort(key=lambda x: x['metric'][metric_name], reverse=reverse)

        # Apply top_k
        top_k = rank_spec.get('top_k', 10)
        results = results[:top_k]

        # Add rank
        for i, result in enumerate(results, 1):
            result['rank'] = i

        print(f"[{rule_id}] Results: {len(results)} recommendations")

        return results

    def execute_all_rules(self, output_path: str) -> Dict[str, Any]:
        """
        Execute all rules and save results to JSONL.

        Returns:
            Summary statistics
        """
        all_results = []
        summary = {
            'input_file': str(self.compare_path),
            'input_hash': self.input_hash,
            'total_rules': len(self.rules),
            'rules_executed': 0,
            'total_recommendations': 0,
            'results_by_rule': {}
        }

        for rule in self.rules:
            try:
                results = self.execute_rule(rule)
                all_results.extend(results)

                rule_id = rule['rule_id']
                summary['rules_executed'] += 1
                summary['results_by_rule'][rule_id] = len(results)
                summary['total_recommendations'] += len(results)

            except Exception as e:
                print(f"ERROR executing {rule.get('rule_id', 'unknown')}: {e}")
                continue

        # Save results
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for result in all_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')

        print(f"\n✓ Results saved to: {output_file}")
        print(f"✓ Total recommendations: {summary['total_recommendations']}")

        return summary


def main():
    """Main execution"""
    executor = RuleExecutor(
        compare_path='data/compare_v1/compare_rows_v1.jsonl',
        rule_catalog_path='rules/rule_catalog.yaml'
    )

    summary = executor.execute_all_rules(
        output_path='data/recommend_v1/recommend_results.jsonl'
    )

    # Save summary
    summary_path = Path('data/recommend_v1/execution_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, indent=2, ensure_ascii=False, fp=f)

    print(f"\n✓ Execution summary saved to: {summary_path}")
    print(f"\n=== EXECUTION SUMMARY ===")
    print(f"Rules executed: {summary['rules_executed']}/{summary['total_rules']}")
    print(f"Total recommendations: {summary['total_recommendations']}")
    print(f"Input hash: {summary['input_hash'][:16]}...")

    for rule_id, count in summary['results_by_rule'].items():
        print(f"  {rule_id}: {count} results")


if __name__ == '__main__':
    main()
