#!/usr/bin/env python3
"""
STEP NEXT-18B: Step7 Amount Extraction & Coverage Cards Enrichment
===================================================================

Purpose:
    Extract amounts from proposal PDFs and enrich coverage_cards.jsonl with amount field.

    Applies Type A/B extraction strategy:
    - Parse proposal PDF tables to find coverage name + amount pairs
    - Match extracted coverage names to canonical coverage_code
    - Add amount field to existing coverage_cards.jsonl

Improvements (STEP NEXT-18B):
    1. Number prefix removal: "1 암진단비" → "암진단비"
    2. Parentheses extraction: "기본계약(암진단비)" → "암진단비"
    3. Improved coverage name matching

Usage:
    python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer hyundai
    python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer kb
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.scope_gate import resolve_scope_csv


@dataclass
class ProposalAmountPair:
    """Proposal에서 추출한 (담보명, 금액) 페어"""
    coverage_name_raw: str
    amount_text: str
    page_num: int
    line_text: str  # 증거 원문


@dataclass
class AmountDTO:
    """Amount 데이터 구조 (API contract 준수)"""
    status: str  # CONFIRMED | UNCONFIRMED | NOT_AVAILABLE
    value_text: Optional[str]
    source_doc_type: Optional[str]
    source_priority: Optional[str]
    evidence_ref: Optional[dict]
    notes: List[str]


def normalize_coverage_name_for_matching(raw_name: str) -> str:
    """
    STEP NEXT-18B: 담보명 정규화 (매칭용)

    Improvements:
    1. 번호 접두사 제거: ^\d+\s* → ""
    2. 괄호 담보명 추출: 기본계약(담보명) → 담보명
    3. 공백/특수문자 제거

    Args:
        raw_name: 원본 담보명

    Returns:
        normalized: 정규화된 담보명
    """
    # 1. 번호 접두사 제거: "1. 암진단비", "2 상해사망" → "암진단비", "상해사망"
    normalized = re.sub(r'^\d+\.?\s*', '', raw_name)

    # 2. 괄호 담보명 추출: "기본계약(암진단비)" → "암진단비"
    #    단, 괄호가 담보명의 일부인 경우는 유지 (예: "암진단비(유사암제외)")
    base_contract_match = re.search(r'^기본계약\(([^)]+)\)', normalized)
    if base_contract_match:
        normalized = base_contract_match.group(1)

    # 3. 전각/반각 공백 제거
    normalized = re.sub(r'\s+', '', normalized)

    # 4. 특수문자 제거 (단, 괄호 내용은 유지)
    # 예: "암진단비·후유장해" → "암진단비후유장해" (단, "암진단비(유사암제외)" 유지)
    normalized = re.sub(r'[·\-_\u2022\u2023\u25E6\u2043\u2219]', '', normalized)

    return normalized.strip()


def extract_amount_from_line(line_text: str) -> Optional[str]:
    """
    라인에서 금액 패턴 추출

    지원 패턴:
    - N천만원, N백만원, N십만원 (예: 3천만원, 5백만원)
    - N,NNN만원, NNNN만원 (예: 3,000만원, 1000만원)
    - NNN,NNN원 (예: 100,000원)

    Args:
        line_text: 검사할 텍스트 라인

    Returns:
        amount_text or None
    """
    # 패턴 1: N천만원, N백만원, N십만원 (우선순위 높음)
    pattern1 = re.search(r'(\d+[천백십]만?원)', line_text)
    if pattern1:
        return pattern1.group(1)

    # 패턴 2: N,NNN만원, NNNN만원
    pattern2 = re.search(r'(\d{1,3}(?:,\d{3})*만?원)', line_text)
    if pattern2:
        return pattern2.group(1)

    # 패턴 3: NNN,NNN원
    pattern3 = re.search(r'(\d{1,3}(?:,\d{3})+원)', line_text)
    if pattern3:
        return pattern3.group(1)

    # 패턴 4: N만원 (가장 낮은 우선순위)
    pattern4 = re.search(r'(\d+만?원)', line_text)
    if pattern4:
        return pattern4.group(1)

    return None


def extract_proposal_amount_pairs(proposal_page_jsonl: Path) -> List[ProposalAmountPair]:
    """
    가입설계서 page.jsonl에서 (담보명, 금액) 페어 추출

    Args:
        proposal_page_jsonl: 가입설계서 page.jsonl 경로

    Returns:
        List[ProposalAmountPair]
    """
    pairs = []

    if not proposal_page_jsonl.exists():
        print(f"[WARN] Proposal file not found: {proposal_page_jsonl}")
        return pairs

    with open(proposal_page_jsonl, 'r', encoding='utf-8') as f:
        for line_idx, line in enumerate(f):
            if not line.strip():
                continue

            try:
                page_data = json.loads(line)
                page_num = page_data.get('page', line_idx + 1)
                text = page_data.get('text', '')

                # 후보 페이지 필터링: 테이블 키워드 존재 여부
                if not any(kw in text for kw in ['가입금액', '보험가입금액', '보장금액', '담보가입현황', '담보별 보장내용']):
                    continue

                # 라인 단위로 분해
                lines = text.split('\n')
                i = 0
                while i < len(lines):
                    line_text = lines[i].strip()
                    i += 1

                    # 헤더 라인 스킵
                    if any(hdr in line_text for hdr in ['담보가입현황', '가입금액', '보험료', '납입기간', '피보험자']):
                        continue

                    # 빈 라인, 짧은 라인 스킵
                    if len(line_text) < 3:
                        continue

                    # 금액 패턴 체크
                    amount = extract_amount_from_line(line_text)

                    if amount:
                        # 금액 제거하여 담보명 추출
                        coverage_candidate = re.sub(r'\d{1,3}(?:,\d{3})*만?원', '', line_text)
                        coverage_candidate = re.sub(r'\d+[천백십]만?원', '', coverage_candidate)
                        coverage_candidate = re.sub(r'\d+', '', coverage_candidate).strip()

                        # 담보명 검증 (한글 포함 여부, 최소 길이)
                        if re.search(r'[가-힣]', coverage_candidate) and len(coverage_candidate) >= 3:
                            pairs.append(ProposalAmountPair(
                                coverage_name_raw=coverage_candidate,
                                amount_text=amount,
                                page_num=page_num,
                                line_text=line_text
                            ))
                    else:
                        # Case 2: 담보명과 금액이 다른 라인에 있는 경우 (테이블 row spanning)
                        if i < len(lines):
                            next_line = lines[i].strip()
                            next_amount = extract_amount_from_line(next_line)

                            if next_amount:
                                # 숫자만 있는 라인 제외 (보험료 라인 등)
                                if re.match(r'^[\d,\s]+$', line_text):
                                    continue

                                # 담보명 검증
                                if re.search(r'[가-힣]', line_text) and len(line_text) >= 3:
                                    pairs.append(ProposalAmountPair(
                                        coverage_name_raw=line_text,
                                        amount_text=next_amount,
                                        page_num=page_num,
                                        line_text=f"{line_text} / {next_line}"
                                    ))
                                    i += 1  # 다음 라인 스킵

            except json.JSONDecodeError:
                continue

    return pairs


def match_proposal_to_coverage_code(
    pairs: List[ProposalAmountPair],
    scope_mapped_csv: Path
) -> Dict[str, Tuple[str, int, str]]:
    """
    Proposal 페어를 coverage_code에 매칭

    Args:
        pairs: 추출된 proposal 페어 목록
        scope_mapped_csv: scope_mapped.csv 경로

    Returns:
        Dict[coverage_code, (amount_text, page_num, line_text)]
    """
    # Load scope_mapped.csv: coverage_name_raw -> coverage_code
    coverage_map = {}  # normalized_name -> (coverage_code, coverage_name_raw)

    if not scope_mapped_csv.exists():
        print(f"[WARN] scope_mapped.csv not found: {scope_mapped_csv}")
        return {}

    with open(scope_mapped_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = row.get('coverage_name_raw', '')
            code = row.get('coverage_code', '')
            status = row.get('mapping_status', '')

            if raw_name and code and status == 'matched':
                norm = normalize_coverage_name_for_matching(raw_name)
                coverage_map[norm] = (code, raw_name)

    # Match proposal pairs to coverage_code
    code_to_amount = {}  # coverage_code -> (amount_text, page_num, line_text)

    for pair in pairs:
        norm = normalize_coverage_name_for_matching(pair.coverage_name_raw)

        if norm in coverage_map:
            code, raw_name = coverage_map[norm]
            # 첫 번째 매칭만 사용 (중복 방지)
            if code not in code_to_amount:
                code_to_amount[code] = (pair.amount_text, pair.page_num, pair.line_text)

    return code_to_amount


def enrich_coverage_cards_with_amounts(
    coverage_cards_jsonl: Path,
    code_to_amount: Dict[str, Tuple[str, int, str]],
    output_jsonl: Path
):
    """
    기존 coverage_cards.jsonl에 amount 필드 추가

    Args:
        coverage_cards_jsonl: 입력 coverage_cards.jsonl
        code_to_amount: coverage_code -> (amount_text, page_num, line_text)
        output_jsonl: 출력 경로 (enriched coverage_cards.jsonl)
    """
    if not coverage_cards_jsonl.exists():
        print(f"[ERROR] Coverage cards not found: {coverage_cards_jsonl}")
        return

    enriched_cards = []
    stats = {'total': 0, 'confirmed': 0, 'unconfirmed': 0}

    with open(coverage_cards_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            card = json.loads(line)
            stats['total'] += 1

            coverage_code = card.get('coverage_code')

            # Amount 데이터 추가
            if coverage_code and coverage_code in code_to_amount:
                amount_text, page_num, line_text = code_to_amount[coverage_code]

                card['amount'] = {
                    'status': 'CONFIRMED',
                    'value_text': amount_text,
                    'source_doc_type': '가입설계서',
                    'source_priority': 'proposal_table',
                    'evidence_ref': {
                        'page_num': page_num,
                        'snippet': line_text[:200]
                    },
                    'notes': []
                }
                stats['confirmed'] += 1
            else:
                # Amount 미발견 → UNCONFIRMED
                card['amount'] = {
                    'status': 'UNCONFIRMED',
                    'value_text': None,
                    'source_doc_type': None,
                    'source_priority': None,
                    'evidence_ref': None,
                    'notes': []
                }
                stats['unconfirmed'] += 1

            enriched_cards.append(card)

    # Write enriched cards
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for card in enriched_cards:
            f.write(json.dumps(card, ensure_ascii=False) + '\n')

    print(f"\n[Step7 Amount Enrichment Stats]")
    print(f"  Total cards: {stats['total']}")
    print(f"  CONFIRMED: {stats['confirmed']} ({stats['confirmed']/stats['total']*100:.1f}%)")
    print(f"  UNCONFIRMED: {stats['unconfirmed']} ({stats['unconfirmed']/stats['total']*100:.1f}%)")
    print(f"\n✓ Output: {output_jsonl}")


def main():
    parser = argparse.ArgumentParser(description='Extract amounts from proposal and enrich coverage cards')
    parser.add_argument('--insurer', type=str, required=True, help='Insurer name (e.g., hyundai, kb)')
    args = parser.parse_args()

    insurer = args.insurer
    project_root = Path(__file__).resolve().parents[2]

    print(f"[Step7 Amount Extraction & Enrichment]")
    print(f"Insurer: {insurer}")
    print(f"")

    # Paths
    proposal_dir = project_root / 'data' / 'evidence_text' / insurer / '가입설계서'

    # STEP NEXT-18X: Use canonical resolver
    scope_mapped_csv = resolve_scope_csv(insurer, project_root / 'data' / 'scope')

    coverage_cards_jsonl = project_root / 'data' / 'compare' / f'{insurer}_coverage_cards.jsonl'
    output_jsonl = project_root / 'data' / 'compare' / f'{insurer}_coverage_cards.jsonl'

    # Step 1: Extract proposal amount pairs
    print(f"[1/3] Extracting amount pairs from proposal...")
    proposal_files = list(proposal_dir.glob('*.page.jsonl')) if proposal_dir.exists() else []

    if not proposal_files:
        print(f"[ERROR] No proposal files found in {proposal_dir}")
        return

    all_pairs = []
    for proposal_file in proposal_files:
        pairs = extract_proposal_amount_pairs(proposal_file)
        all_pairs.extend(pairs)
        print(f"  {proposal_file.name}: {len(pairs)} pairs")

    print(f"  Total: {len(all_pairs)} pairs")

    # Step 2: Match to coverage_code
    print(f"\n[2/3] Matching to coverage_code...")
    code_to_amount = match_proposal_to_coverage_code(all_pairs, scope_mapped_csv)
    print(f"  Matched: {len(code_to_amount)} coverage_code(s)")

    # Step 3: Enrich coverage_cards.jsonl
    print(f"\n[3/3] Enriching coverage_cards.jsonl...")
    enrich_coverage_cards_with_amounts(coverage_cards_jsonl, code_to_amount, output_jsonl)


if __name__ == '__main__':
    main()
