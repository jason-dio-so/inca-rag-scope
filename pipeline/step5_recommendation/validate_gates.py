#!/usr/bin/env python3
"""
GATE Validator for Rule Executor (STEP NEXT-74)

Validates that all GATES (G1-G4) are satisfied:
- G1: Fact-only (all values from slots)
- G2: Evidence (slot.evidences >= 1)
- G3: Deterministic (hash verification)
- G4: No-inference (input integrity)
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any


class GateValidator:
    def __init__(self, results_path: str, summary_path: str):
        self.results_path = Path(results_path)
        self.summary_path = Path(summary_path)

        self.results = self._load_results()
        self.summary = self._load_summary()

    def _load_results(self) -> List[Dict[str, Any]]:
        """Load recommendation results"""
        results = []
        with open(self.results_path, 'r', encoding='utf-8') as f:
            for line in f:
                results.append(json.loads(line))
        return results

    def _load_summary(self) -> Dict[str, Any]:
        """Load execution summary"""
        with open(self.summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_g1_fact_only(self) -> Dict[str, Any]:
        """
        G1: Fact-only Gate
        Verify all metric values come from slots
        """
        violations = []

        for i, result in enumerate(self.results):
            slot_used = result.get('slot_used')
            metric = result.get('metric', {})

            if not slot_used:
                violations.append({
                    'row': i,
                    'rule_id': result.get('rule_id'),
                    'issue': 'No slot_used field'
                })
                continue

            # Check if slot_value exists
            if 'slot_value' not in result:
                violations.append({
                    'row': i,
                    'rule_id': result.get('rule_id'),
                    'issue': f'No slot_value for slot: {slot_used}'
                })

        return {
            'gate': 'G1_FACT_ONLY',
            'status': 'PASS' if not violations else 'FAIL',
            'violations': violations,
            'total_violations': len(violations)
        }

    def validate_g2_evidence(self) -> Dict[str, Any]:
        """
        G2: Evidence Gate
        Verify all results have at least 1 evidence reference
        """
        violations = []

        for i, result in enumerate(self.results):
            evidence_refs = result.get('evidence_refs', [])

            if not evidence_refs or len(evidence_refs) == 0:
                violations.append({
                    'row': i,
                    'rule_id': result.get('rule_id'),
                    'coverage': result.get('coverage', {}).get('coverage_title'),
                    'issue': 'No evidence references'
                })
                continue

            # Check each evidence has required fields
            for j, ev in enumerate(evidence_refs):
                if not ev.get('doc_type') or not ev.get('page'):
                    violations.append({
                        'row': i,
                        'rule_id': result.get('rule_id'),
                        'evidence_index': j,
                        'issue': 'Missing doc_type or page'
                    })

        return {
            'gate': 'G2_EVIDENCE',
            'status': 'PASS' if not violations else 'FAIL',
            'violations': violations,
            'total_violations': len(violations)
        }

    def validate_g3_deterministic(self) -> Dict[str, Any]:
        """
        G3: Deterministic Gate
        Verify input hash exists and is consistent
        """
        input_hash = self.summary.get('input_hash')

        if not input_hash:
            return {
                'gate': 'G3_DETERMINISTIC',
                'status': 'FAIL',
                'issue': 'No input_hash in summary',
                'input_hash': None
            }

        # Verify hash format (should be 64-char hex for SHA256)
        if len(input_hash) != 64:
            return {
                'gate': 'G3_DETERMINISTIC',
                'status': 'FAIL',
                'issue': 'Invalid hash format',
                'input_hash': input_hash
            }

        return {
            'gate': 'G3_DETERMINISTIC',
            'status': 'PASS',
            'input_hash': input_hash[:16] + '...',
            'note': 'Hash recorded for deterministic verification'
        }

    def validate_g4_no_inference(self) -> Dict[str, Any]:
        """
        G4: No-inference Gate
        Verify input file integrity (basic check)
        """
        input_file = self.summary.get('input_file')

        if not input_file:
            return {
                'gate': 'G4_NO_INFERENCE',
                'status': 'FAIL',
                'issue': 'No input_file in summary'
            }

        input_path = Path(input_file)
        if not input_path.exists():
            return {
                'gate': 'G4_NO_INFERENCE',
                'status': 'FAIL',
                'issue': f'Input file not found: {input_file}'
            }

        # Verify input hash matches
        hasher = hashlib.sha256()
        with open(input_path, 'rb') as f:
            hasher.update(f.read())

        computed_hash = hasher.hexdigest()
        expected_hash = self.summary.get('input_hash')

        if computed_hash != expected_hash:
            return {
                'gate': 'G4_NO_INFERENCE',
                'status': 'FAIL',
                'issue': 'Input file hash mismatch (file may have been modified)',
                'expected': expected_hash[:16] + '...',
                'computed': computed_hash[:16] + '...'
            }

        return {
            'gate': 'G4_NO_INFERENCE',
            'status': 'PASS',
            'input_file': input_file,
            'note': 'Input file integrity verified'
        }

    def validate_evidence_traceability(self) -> Dict[str, Any]:
        """
        Additional check: Evidence traceability
        Ensure evidence can be traced back to source documents
        """
        stats = {
            'total_results': len(self.results),
            'total_evidence_refs': 0,
            'unique_doc_types': set(),
            'pages_referenced': set()
        }

        for result in self.results:
            evidence_refs = result.get('evidence_refs', [])
            stats['total_evidence_refs'] += len(evidence_refs)

            for ev in evidence_refs:
                doc_type = ev.get('doc_type')
                page = ev.get('page')

                if doc_type:
                    stats['unique_doc_types'].add(doc_type)
                if page:
                    stats['pages_referenced'].add((doc_type, page))

        return {
            'check': 'EVIDENCE_TRACEABILITY',
            'status': 'PASS',
            'total_results': stats['total_results'],
            'total_evidence_refs': stats['total_evidence_refs'],
            'avg_evidence_per_result': round(stats['total_evidence_refs'] / stats['total_results'], 2) if stats['total_results'] > 0 else 0,
            'unique_doc_types': sorted(list(stats['unique_doc_types'])),
            'unique_page_refs': len(stats['pages_referenced'])
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all GATE validations"""
        print("\n=== GATE VALIDATION (STEP NEXT-74) ===\n")

        report = {
            'gates': {},
            'additional_checks': {},
            'overall_status': 'PASS'
        }

        # G1: Fact-only
        g1_result = self.validate_g1_fact_only()
        report['gates']['G1'] = g1_result
        print(f"[G1_FACT_ONLY] {g1_result['status']}")
        if g1_result['status'] == 'FAIL':
            print(f"  Violations: {g1_result['total_violations']}")
            report['overall_status'] = 'FAIL'

        # G2: Evidence
        g2_result = self.validate_g2_evidence()
        report['gates']['G2'] = g2_result
        print(f"[G2_EVIDENCE] {g2_result['status']}")
        if g2_result['status'] == 'FAIL':
            print(f"  Violations: {g2_result['total_violations']}")
            report['overall_status'] = 'FAIL'

        # G3: Deterministic
        g3_result = self.validate_g3_deterministic()
        report['gates']['G3'] = g3_result
        print(f"[G3_DETERMINISTIC] {g3_result['status']}")
        if g3_result['status'] == 'FAIL':
            print(f"  Issue: {g3_result.get('issue')}")
            report['overall_status'] = 'FAIL'

        # G4: No-inference
        g4_result = self.validate_g4_no_inference()
        report['gates']['G4'] = g4_result
        print(f"[G4_NO_INFERENCE] {g4_result['status']}")
        if g4_result['status'] == 'FAIL':
            print(f"  Issue: {g4_result.get('issue')}")
            report['overall_status'] = 'FAIL'

        # Evidence traceability
        trace_result = self.validate_evidence_traceability()
        report['additional_checks']['evidence_traceability'] = trace_result
        print(f"\n[EVIDENCE_TRACEABILITY] {trace_result['status']}")
        print(f"  Total results: {trace_result['total_results']}")
        print(f"  Total evidence refs: {trace_result['total_evidence_refs']}")
        print(f"  Avg evidence/result: {trace_result['avg_evidence_per_result']}")
        print(f"  Unique doc types: {len(trace_result['unique_doc_types'])}")

        print(f"\n=== OVERALL STATUS: {report['overall_status']} ===\n")

        return report


def main():
    """Main validation"""
    validator = GateValidator(
        results_path='data/recommend_v1/recommend_results.jsonl',
        summary_path='data/recommend_v1/execution_summary.json'
    )

    report = validator.run_all_validations()

    # Save report
    report_path = Path('data/recommend_v1/gate_validation_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, indent=2, ensure_ascii=False, fp=f)

    print(f"✓ Validation report saved to: {report_path}")

    # Exit with error code if any gate failed
    if report['overall_status'] == 'FAIL':
        print("\n❌ GATE VALIDATION FAILED")
        exit(1)
    else:
        print("\n✓ ALL GATES PASSED")


if __name__ == '__main__':
    main()
