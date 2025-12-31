"""
Step 8: Single Coverage Extraction (Deterministic, No LLM)

특정 coverage_code에 대해 슬롯별 정보를 추출 (fact-only, deterministic)

입력:
- data/compare/{INSURER}_coverage_cards.jsonl
- data/evidence_pack/{INSURER}_evidence_pack.jsonl

출력:
- data/single/{INSURER}_{COVERAGE_CODE}_profile.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class SingleCoverageExtractor:
    """단일 담보에 대한 deterministic 슬롯 추출"""

    def __init__(self, insurer: str, coverage_code: str, base_dir: Path):
        self.insurer = insurer
        self.coverage_code = coverage_code
        self.base_dir = base_dir

    def _extract_slot_text(self, evidences: List[Dict], patterns: List[str], context_lines: int = 1) -> Dict:
        """
        정규식 패턴으로 슬롯 텍스트 추출

        Args:
            evidences: evidence 리스트
            patterns: 검색할 정규식 패턴 리스트
            context_lines: 전후 라인 수

        Returns:
            {
                'text': str (발견된 텍스트, 없으면 None),
                'refs': List[str] (evidence ref 리스트)
            }
        """
        matches = []
        refs = []

        for evidence in evidences:
            snippet = evidence['snippet']
            lines = snippet.split('\n')

            for i, line in enumerate(lines):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # 전후 context 추출
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = '\n'.join(lines[start:end]).strip()

                        matches.append(context)
                        ref = f"{evidence['doc_type']} p.{evidence['page']}"
                        if ref not in refs:
                            refs.append(ref)
                        break

        if matches:
            # 중복 제거 및 결합
            unique_matches = []
            for m in matches:
                if m not in unique_matches:
                    unique_matches.append(m)
            return {
                'text': ' | '.join(unique_matches[:3]),  # 최대 3개
                'refs': refs
            }
        else:
            return {
                'text': None,
                'refs': []
            }

    def extract_profile(self) -> Dict:
        """
        Coverage profile 추출

        Returns:
            Dict: profile 정보
        """
        # Coverage card 로드
        cards_file = self.base_dir / 'data' / 'compare' / f'{self.insurer}_coverage_cards.jsonl'
        card = None
        with open(cards_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('coverage_code') == self.coverage_code:
                        card = data
                        break

        if not card:
            raise ValueError(f"Coverage code {self.coverage_code} not found in {self.insurer} cards")

        # Evidence pack 로드
        pack_file = self.base_dir / 'data' / 'evidence_pack' / f'{self.insurer}_evidence_pack.jsonl'
        evidences = None
        with open(pack_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('coverage_code') == self.coverage_code:
                        evidences = data.get('evidences', [])
                        break

        if evidences is None:
            raise ValueError(f"Coverage code {self.coverage_code} not found in {self.insurer} evidence pack")

        # 슬롯 추출 (deterministic)
        profile = {
            'coverage_code': self.coverage_code,
            'canonical_name': card.get('coverage_name_canonical'),
            'raw_name': card.get('coverage_name_raw'),
            'insurer': self.insurer,
            'doc_type_coverage': card.get('hits_by_doc_type', {}),
        }

        # payout_amount_text
        payout_result = self._extract_slot_text(
            evidences,
            [r'만원|원|금액|지급액|보험금', r'\d+만원|\d+원']
        )
        profile['payout_amount'] = {
            'text': payout_result['text'],
            'refs': payout_result['refs'],
            'status': 'found' if payout_result['text'] else 'unknown',
            'reason': 'no evidence lines matched regex' if not payout_result['text'] else None
        }

        # waiting_period_text (STEP 7 quality patch)
        waiting_result = self._extract_slot_text(
            evidences,
            [r'대기|면책|90일|기간|책임개시|개시일|대기기간', r'\d+일']
        )
        profile['waiting_period'] = {
            'text': waiting_result['text'],
            'refs': waiting_result['refs'],
            'status': 'found' if waiting_result['text'] else 'unknown',
            'reason': 'no evidence lines matched regex' if not waiting_result['text'] else None
        }

        # reduction_period_text
        reduction_result = self._extract_slot_text(
            evidences,
            [r'감액|지급률|50%|1년', r'\d+년.*\d+%']
        )
        profile['reduction_period'] = {
            'text': reduction_result['text'],
            'refs': reduction_result['refs'],
            'status': 'found' if reduction_result['text'] else 'unknown',
            'reason': 'no evidence lines matched regex' if not reduction_result['text'] else None
        }

        # excluded_cancer_text
        excluded_result = self._extract_slot_text(
            evidences,
            [r'유사암|기타피부암|갑상선암|제외', r'소액암']
        )
        profile['excluded_cancer'] = {
            'text': excluded_result['text'],
            'refs': excluded_result['refs'],
            'status': 'found' if excluded_result['text'] else 'unknown',
            'reason': 'no evidence lines matched regex' if not excluded_result['text'] else None
        }

        # definition_excerpt
        definition_result = self._extract_slot_text(
            evidences,
            [r'정의|암의.*정의|진단|조직검사|병리', r'악성신생물'],
            context_lines=2
        )
        profile['definition_excerpt'] = {
            'text': definition_result['text'],
            'refs': definition_result['refs'],
            'status': 'found' if definition_result['text'] else 'unknown',
            'reason': 'no evidence lines matched regex' if not definition_result['text'] else None
        }

        # payment_condition_excerpt (STEP 7 quality patch)
        payment_result = self._extract_slot_text(
            evidences,
            [r'지급사유|지급조건|진단확정|최초.*1회|재진단|지급|회한|보험금.*지급|보험금 지급'],
            context_lines=2
        )
        profile['payment_condition_excerpt'] = {
            'text': payment_result['text'],
            'refs': payment_result['refs'],
            'status': 'found' if payment_result['text'] else 'unknown',
            'reason': 'no evidence lines matched regex' if not payment_result['text'] else None
        }

        # All evidence refs
        all_refs = set()
        for evidence in evidences:
            ref = f"{evidence['doc_type']} p.{evidence['page']}"
            all_refs.add(ref)
        profile['evidence_refs'] = sorted(list(all_refs))

        return profile


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Extract single coverage profile')
    parser.add_argument('--insurer', type=str, required=True, help='보험사명')
    parser.add_argument('--coverage-code', type=str, required=True, help='Coverage code (e.g., A4200_1)')
    args = parser.parse_args()

    insurer = args.insurer
    coverage_code = args.coverage_code
    base_dir = Path(__file__).parent.parent.parent

    print(f"[Step 8] Single Coverage Extraction")
    print(f"[Step 8] Insurer: {insurer}")
    print(f"[Step 8] Coverage Code: {coverage_code}")

    # Extract profile
    extractor = SingleCoverageExtractor(insurer, coverage_code, base_dir)
    profile = extractor.extract_profile()

    # Save profile
    output_dir = base_dir / 'data' / 'single'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'{insurer}_{coverage_code}_profile.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print(f"\n[Step 8] Profile extracted:")
    print(f"  - Coverage: {profile['canonical_name']} ({profile['raw_name']})")
    print(f"  - Doc type hits: {profile['doc_type_coverage']}")
    print(f"  - Payout: {profile['payout_amount']['status']}")
    print(f"  - Waiting period: {profile['waiting_period']['status']}")
    print(f"  - Reduction period: {profile['reduction_period']['status']}")
    print(f"  - Excluded cancer: {profile['excluded_cancer']['status']}")
    print(f"  - Definition: {profile['definition_excerpt']['status']}")
    print(f"  - Payment condition: {profile['payment_condition_excerpt']['status']}")
    print(f"\n✓ Profile: {output_file}")


if __name__ == '__main__':
    main()
