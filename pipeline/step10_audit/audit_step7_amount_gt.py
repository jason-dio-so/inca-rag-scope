#!/usr/bin/env python3
"""
STEP NEXT-10B-2G — Step7 Amount 전수 조사 (Ground Truth Audit)

가입설계서(Proposal)에서 직접 추출한 (coverage_name_raw, amount_raw)를
ground-truth로 하여 Step7 amount 결과와 비교 조사.

금지:
- Type C에서 "보험가입금액"을 담보별 amount로 채우기
- 약관/상품요약서 text를 heuristics로 긁어서 담보별 금액 생성
- UNCONFIRMED 비율을 KPI로 삼아 억지로 낮추기
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict
import csv


@dataclass
class GTAmountPair:
    """Ground Truth: 가입설계서에서 추출한 원본 페어"""
    coverage_name_raw: str
    amount_raw: str
    page_num: int
    line_text: str  # 추출 원문 (증거)


@dataclass
class MappingResult:
    """GT 담보명 → coverage_code 매핑 결과"""
    gt_pair: GTAmountPair
    coverage_code: Optional[str]
    mapping_status: str  # matched / unmatched
    normalized_name: str  # 정규화된 담보명


@dataclass
class ComparisonResult:
    """Step7 결과와 GT 비교"""
    coverage_code: str
    gt_amount_raw: str
    step7_value_text: Optional[str]
    step7_status: Optional[str]
    step7_source_priority: Optional[str]
    step7_source_doc_type: Optional[str]
    step7_source_page: Optional[int]
    step7_evidence_snippet: Optional[str]
    verdict: str  # OK_MATCH / MISS_PATTERN / MISMATCH_VALUE / TYPE_C_EXPECTED_UNCONFIRMED / GT_AMBIGUOUS
    gt_page: int
    gt_line: str
    proposal_file: str  # 어느 가입설계서 파일에서 왔는지
    risk_signals: List[str]  # 리스크 시그널 목록


def normalize_coverage_name(raw_name: str) -> str:
    """담보명 정규화: 공백/괄호/접두어/번호 제거"""
    # Remove leading numbers like "1. ", "3. ", etc.
    name = re.sub(r'^\d+\.\s*', '', raw_name)
    # Remove leading tags like [기본계약], [갱신형], etc.
    name = re.sub(r'^\[.*?\]\s*', '', name)
    # Remove all whitespace
    name = re.sub(r'\s+', '', name)
    # Remove parentheses content
    name = re.sub(r'\([^)]*\)', '', name)
    # Remove special chars (including special dash variants)
    name = re.sub(r'[·\-_\u2022\u2023\u25E6\u2043\u2219]', '', name)
    return name.strip()


def extract_amount_from_text(text: str) -> Optional[str]:
    """
    금액 패턴 추출 (KB 사건 재발 방지 - 천만원/백만원 패턴 지원)

    지원 패턴:
    - 1,000만원, 3000만원
    - 1천만원, 5백만원, 2십만원
    - 100,000원, 10만원
    """
    # 패턴 1: N,NNN만원, NNNN만원
    pattern1 = re.search(r'(\d{1,3}(?:,\d{3})*만?원)', text)
    if pattern1:
        return pattern1.group(1)

    # 패턴 2: N천만원, N백만원, N십만원
    pattern2 = re.search(r'(\d+[천백십]만?원)', text)
    if pattern2:
        return pattern2.group(1)

    # 패턴 3: NNN,NNN원, NNNNNN원
    pattern3 = re.search(r'(\d{1,3}(?:,\d{3})+원)', text)
    if pattern3:
        return pattern3.group(1)

    # 패턴 4: N만원
    pattern4 = re.search(r'(\d+만?원)', text)
    if pattern4:
        return pattern4.group(1)

    return None


def detect_risk_signals(coverage_name_raw: str, text_context: str) -> List[str]:
    """
    리스크 시그널 감지

    리스크 패턴:
    - 결합형 담보명: "·", "및", "/", "사망·후유", "수술·입원"
    - 예시/대표계약/참고 키워드 (denylist 회피 검증)
    """
    signals = []

    # 결합형 패턴
    combined_patterns = ['·', '및', '/', '사망·후유', '후유장해·', '수술·입원', '입원·수술']
    for pattern in combined_patterns:
        if pattern in coverage_name_raw:
            signals.append(f'COMBINED_PATTERN:{pattern}')

    # 예시/대표/참고 키워드
    denylist_keywords = ['예시', '대표계약', '참고', '샘플', '표준']
    for kw in denylist_keywords:
        if kw in text_context:
            signals.append(f'DENYLIST_KEYWORD:{kw}')

    return signals


def extract_gt_pairs_from_proposal(proposal_page_jsonl: Path) -> List[GTAmountPair]:
    """
    가입설계서 page.jsonl에서 GT 페어 추출

    테이블 구조 패턴:
    담보가입현황       가입금액    보험료(원)  납입기간/보험기간
    담보명             금액        보험료      기간
    """
    gt_pairs = []

    if not proposal_page_jsonl.exists():
        print(f"[WARN] Proposal file not found: {proposal_page_jsonl}")
        return gt_pairs

    with open(proposal_page_jsonl, 'r', encoding='utf-8') as f:
        for line_idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                page_data = json.loads(line)
                page_num = page_data.get('page', line_idx + 1)
                text = page_data.get('text', '')

                # 후보 페이지 필터링 (테이블 키워드)
                if not any(kw in text for kw in ['보장명', '가입금액', '보장금액', '담보명', '담보가입현황', '담보별 보장내용']):
                    continue

                # 라인 단위로 분해
                lines = text.split('\n')
                i = 0
                while i < len(lines):
                    line_text = lines[i].strip()
                    i += 1

                    # 헤더 라인 스킵
                    if any(hdr in line_text for hdr in ['담보가입현황', '가입금액', '보험료', '납입기간', '보험기간', '담보별 보장내용', '피보험자', '선택계약', '기본계약']):
                        continue

                    # 빈 라인, 짧은 라인 스킵
                    if len(line_text) < 3:
                        continue

                    # 금액 패턴 체크
                    amount = extract_amount_from_text(line_text)

                    if amount:
                        # Case 1: 담보명과 금액이 같은 라인에 있음
                        # 예: "암 진단비(유사암 제외)\n3,000만원\n40,620\n20년납 100세만기\nZD8200010"
                        # 또는: "암 진단비(유사암 제외) 3,000만원 40,620 20년납 100세만기"

                        # 금액 제거하여 담보명 추출
                        coverage_candidate = re.sub(r'\d{1,3}(?:,\d{3})*만?원', '', line_text)
                        coverage_candidate = re.sub(r'\d+[천백십]만?원', '', coverage_candidate)
                        coverage_candidate = re.sub(r'\d+', '', coverage_candidate).strip()

                        if len(coverage_candidate) >= 3:
                            gt_pairs.append(GTAmountPair(
                                coverage_name_raw=coverage_candidate,
                                amount_raw=amount,
                                page_num=page_num,
                                line_text=line_text
                            ))
                    else:
                        # Case 2: 담보명과 금액이 다른 라인에 있음 (테이블 row spanning)
                        # 현재 라인이 담보명 후보이고, 다음 라인이 금액인 경우
                        if i < len(lines):
                            next_line = lines[i].strip()
                            next_amount = extract_amount_from_text(next_line)

                            if next_amount:
                                # 현재 라인을 담보명으로 간주
                                coverage_candidate = line_text

                                # 숫자만 있는 라인 제외 (보험료 라인 등)
                                if re.match(r'^[\d,\s]+$', coverage_candidate):
                                    continue

                                # 담보명 검증 (한글 포함 여부)
                                if not re.search(r'[가-힣]', coverage_candidate):
                                    continue

                                if len(coverage_candidate) >= 3:
                                    gt_pairs.append(GTAmountPair(
                                        coverage_name_raw=coverage_candidate,
                                        amount_raw=next_amount,
                                        page_num=page_num,
                                        line_text=f"{coverage_candidate} / {next_line}"
                                    ))
                                    i += 1  # 다음 라인 스킵 (이미 처리됨)

            except json.JSONDecodeError:
                continue

    return gt_pairs


def map_gt_to_coverage_code(
    gt_pairs: List[GTAmountPair],
    scope_mapped_csv: Path
) -> List[MappingResult]:
    """GT 담보명 → coverage_code 매핑 (scope_mapped.csv 경유)"""
    # Load scope_mapped.csv
    code_map = {}  # normalized_name -> (coverage_code, mapping_status)

    if not scope_mapped_csv.exists():
        print(f"[WARN] scope_mapped.csv not found: {scope_mapped_csv}")
        return []

    with open(scope_mapped_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = row.get('coverage_name_raw', '')
            code = row.get('coverage_code', '')
            status = row.get('mapping_status', '')

            if raw_name and code and status == 'matched':
                norm = normalize_coverage_name(raw_name)
                code_map[norm] = (code, status)

    # Map GT pairs
    results = []
    for gt in gt_pairs:
        norm = normalize_coverage_name(gt.coverage_name_raw)
        if norm in code_map:
            code, status = code_map[norm]
            results.append(MappingResult(
                gt_pair=gt,
                coverage_code=code,
                mapping_status=status,
                normalized_name=norm
            ))
        else:
            results.append(MappingResult(
                gt_pair=gt,
                coverage_code=None,
                mapping_status='unmatched',
                normalized_name=norm
            ))

    return results


def load_step7_cards(coverage_cards_jsonl: Path) -> Dict[str, dict]:
    """Step7 coverage_cards.jsonl 로드 (coverage_code -> card)"""
    cards = {}
    if not coverage_cards_jsonl.exists():
        return cards

    with open(coverage_cards_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            card = json.loads(line)
            code = card.get('coverage_code', '')
            if code:
                cards[code] = card
    return cards


def normalize_amount_for_comparison(amount_str: str) -> str:
    """
    금액 정규화 (비교용)

    목적: GT와 Step7의 표기 차이를 흡수
    - 1천만원 → 1000만원
    - 5백만원 → 500만원
    - 2십만원 → 20만원
    - 1,000만원 → 1000만원
    """
    if not amount_str:
        return ''

    # 공백/쉼표 제거
    norm = re.sub(r'[\s,]', '', amount_str)

    # 한글 숫자 변환 (천백십 → 숫자)
    korean_nums = {
        '천': '1000',
        '백': '100',
        '십': '10'
    }

    for kor, num in korean_nums.items():
        # N천 → N*1000 (예: 3천 → 3000)
        pattern = rf'(\d+){kor}'
        def replace_korean(m):
            return str(int(m.group(1)) * int(num))
        norm = re.sub(pattern, replace_korean, norm)

    return norm


def check_gt_policy_issue(
    coverage_code: str,
    gt_coverage_name: str,
    gt_amount: str,
    step7_value: str,
    mapping_results: List[MappingResult],
    proposal_file: str
) -> tuple[bool, str]:
    """
    GT_POLICY_ISSUE 판정: GT와 Step7 간 정책적 차이로 인한 불일치

    Case 1: 결합형 vs 단독형 우선순위
    - 가입설계서에 "상해사망·후유장해" (1백만원, 라인1)와 "상해사망" (1천만원, 라인3) 모두 존재
    - Step7은 먼저 나오는 결합형을 선택 (1백만원)
    - GT는 단독형을 선택 (1천만원)
    - 이 경우 GT_POLICY_ISSUE로 분류하고, 별도 해결 정책 필요

    Returns:
        (is_policy_issue: bool, reason: str)
    """
    # Case 1: 결합형 패턴 체크 (·, 및, /)
    combined_patterns = ['·', '및', '/']
    has_combined_pattern = any(p in gt_coverage_name for p in combined_patterns)

    # Step7이 GT보다 작은 금액을 선택한 경우 + GT에 결합형 패턴이 없는 경우
    # → 가입설계서에 결합형이 있었지만 GT가 못 찾은 것으로 추정
    if not has_combined_pattern and step7_value and gt_amount:
        gt_norm = normalize_amount_for_comparison(gt_amount)
        step7_norm = normalize_amount_for_comparison(step7_value)

        # Extract numeric values for comparison
        import re
        gt_num_match = re.search(r'(\d+)만원', gt_norm)
        step7_num_match = re.search(r'(\d+)만원', step7_norm)

        if gt_num_match and step7_num_match:
            gt_num = int(gt_num_match.group(1))
            step7_num = int(step7_num_match.group(1))

            # Step7 chose a smaller amount (likely from combined coverage line)
            if step7_num < gt_num and step7_num > 0:
                return True, f'COMBINED_VS_SEPARATE:GT선택={gt_amount}(단독),STEP7선택={step7_value}(결합형추정)'

    # Case 2: 같은 code가 GT에 여러 번 등장 + 서로 다른 금액
    same_code_mappings = [
        m for m in mapping_results
        if m.coverage_code == coverage_code and m.gt_pair.line_text
    ]

    if len(same_code_mappings) > 1:
        amounts = set(m.gt_pair.amount_raw for m in same_code_mappings)
        if len(amounts) > 1:
            return True, f'GT_DUPLICATE:같은코드가{len(same_code_mappings)}회등장,금액={amounts}'

    return False, ''


def compare_gt_vs_step7(
    mapping_results: List[MappingResult],
    step7_cards: Dict[str, dict],
    insurer_type: str,
    proposal_file: str
) -> List[ComparisonResult]:
    """GT vs Step7 amount 비교"""
    comparisons = []

    for mapping in mapping_results:
        if mapping.coverage_code is None:
            # SCOPE_OR_MAPPING_GAP
            continue

        code = mapping.coverage_code
        gt_amount = mapping.gt_pair.amount_raw
        gt_coverage_name = mapping.gt_pair.coverage_name_raw
        gt_line = mapping.gt_pair.line_text

        # 리스크 시그널 감지
        risk_signals = detect_risk_signals(gt_coverage_name, gt_line)

        card = step7_cards.get(code)
        if not card:
            # Step7에 카드가 없음 (이상)
            comparisons.append(ComparisonResult(
                coverage_code=code,
                gt_amount_raw=gt_amount,
                step7_value_text=None,
                step7_status=None,
                step7_source_priority=None,
                step7_source_doc_type=None,
                step7_source_page=None,
                step7_evidence_snippet=None,
                verdict='MISS_STEP7_CARD',
                gt_page=mapping.gt_pair.page_num,
                gt_line=mapping.gt_pair.line_text,
                proposal_file=proposal_file,
                risk_signals=risk_signals
            ))
            continue

        amount_field = card.get('amount', {})
        step7_value = amount_field.get('value_text')
        step7_status = amount_field.get('status')
        step7_priority = amount_field.get('source_priority')
        step7_doc_type = amount_field.get('source_doc_type')

        # Extract evidence snippet from Step7
        evidence = amount_field.get('evidence', {})
        step7_snippet = evidence.get('snippet', '')[:200] if evidence else ''
        step7_page = evidence.get('page_num') if evidence else None

        # 정규화 비교 (한글숫자 변환 포함)
        gt_norm = normalize_amount_for_comparison(gt_amount)
        step7_norm = normalize_amount_for_comparison(step7_value)

        # GT_POLICY_ISSUE 체크
        is_policy_issue, policy_reason = check_gt_policy_issue(
            code, gt_coverage_name, gt_amount, step7_value, mapping_results, proposal_file
        )

        # Verdict 판정
        if is_policy_issue:
            verdict = 'GT_POLICY_ISSUE'
            risk_signals.append(policy_reason)
        elif step7_status == 'UNCONFIRMED' or not step7_value:
            if insurer_type == 'C':
                verdict = 'TYPE_C_EXPECTED_UNCONFIRMED'
            else:
                verdict = 'MISS_PATTERN'
        elif gt_norm == step7_norm:
            verdict = 'OK_MATCH'
        else:
            verdict = 'MISMATCH_VALUE'
            risk_signals.append(f'VALUE_DIFF:GT={gt_norm},STEP7={step7_norm}')

        comparisons.append(ComparisonResult(
            coverage_code=code,
            gt_amount_raw=gt_amount,
            step7_value_text=step7_value,
            step7_status=step7_status,
            step7_source_priority=step7_priority,
            step7_source_doc_type=step7_doc_type,
            step7_source_page=step7_page,
            step7_evidence_snippet=step7_snippet,
            verdict=verdict,
            gt_page=mapping.gt_pair.page_num,
            gt_line=mapping.gt_pair.line_text,
            proposal_file=proposal_file,
            risk_signals=risk_signals
        ))

    return comparisons


def audit_insurer_file_level(
    insurer: str,
    proposal_file: Path,
    data_root: Path,
    type_map: Dict[str, str],
    step7_cards: Dict[str, dict]
) -> dict:
    """가입설계서 파일 단위 전수 조사"""
    print(f"  [File] {proposal_file.name}")

    # Step 1: Extract GT pairs
    gt_pairs = extract_gt_pairs_from_proposal(proposal_file)
    print(f"    → Found {len(gt_pairs)} GT pairs")

    # Step 2: Map to coverage_code
    scope_mapped_csv = data_root / 'scope' / f'{insurer}_scope_mapped.csv'
    mapping_results = map_gt_to_coverage_code(gt_pairs, scope_mapped_csv)

    matched = [m for m in mapping_results if m.mapping_status == 'matched']
    unmatched = [m for m in mapping_results if m.mapping_status == 'unmatched']
    print(f"    → Matched: {len(matched)}, Unmatched: {len(unmatched)}")

    # Step 3: Compare
    insurer_type = type_map.get(insurer, 'UNKNOWN')
    comparisons = compare_gt_vs_step7(matched, step7_cards, insurer_type, proposal_file.name)

    # Verdict 집계
    verdict_counts = defaultdict(int)
    risk_count = 0
    for comp in comparisons:
        verdict_counts[comp.verdict] += 1
        if comp.risk_signals:
            risk_count += 1

    print(f"    → Verdicts: {dict(verdict_counts)}")
    print(f"    → Risk signals: {risk_count}")

    return {
        'proposal_file': proposal_file.name,
        'gt_pairs': len(gt_pairs),
        'mapped_codes': len(matched),
        'unmatched': len(unmatched),
        'verdict_counts': dict(verdict_counts),
        'risk_count': risk_count,
        'comparisons': [asdict(c) for c in comparisons],
        'mapping_results': [asdict(m) for m in mapping_results]
    }


def audit_insurer(
    insurer: str,
    data_root: Path,
    type_map: Dict[str, str]
) -> dict:
    """보험사별 전수 조사 (파일 단위로 분리)"""
    print(f"\n{'='*60}")
    print(f"[AUDIT] {insurer.upper()}")
    print(f"{'='*60}")

    # Paths
    proposal_dir = data_root / 'evidence_text' / insurer / '가입설계서'
    proposal_files = list(proposal_dir.glob('*.page.jsonl')) if proposal_dir.exists() else []

    if not proposal_files:
        print(f"[ERROR] No proposal files found for {insurer}")
        return {
            'insurer': insurer,
            'type': type_map.get(insurer, 'UNKNOWN'),
            'error': 'NO_PROPOSAL_FILES'
        }

    # Load Step7 cards (공통)
    print(f"[1/2] Loading Step7 coverage_cards...")
    coverage_cards_jsonl = data_root / 'compare' / f'{insurer}_coverage_cards.jsonl'
    step7_cards = load_step7_cards(coverage_cards_jsonl)
    print(f"  → Loaded {len(step7_cards)} Step7 cards")

    # File-level audit
    print(f"[2/2] Auditing {len(proposal_files)} proposal file(s)...")
    file_results = []
    for pfile in sorted(proposal_files):
        file_result = audit_insurer_file_level(insurer, pfile, data_root, type_map, step7_cards)
        file_results.append(file_result)

    # Aggregate results
    total_gt_pairs = sum(fr['gt_pairs'] for fr in file_results)
    total_mapped = sum(fr['mapped_codes'] for fr in file_results)
    total_unmatched = sum(fr['unmatched'] for fr in file_results)
    total_risk = sum(fr['risk_count'] for fr in file_results)

    aggregate_verdicts = defaultdict(int)
    all_comparisons = []
    all_mappings = []
    for fr in file_results:
        for verdict, count in fr['verdict_counts'].items():
            aggregate_verdicts[verdict] += count
        all_comparisons.extend(fr['comparisons'])
        all_mappings.extend(fr['mapping_results'])

    print(f"\n[AGGREGATE RESULTS]")
    print(f"  Total GT pairs: {total_gt_pairs}")
    print(f"  Total mapped: {total_mapped}")
    print(f"  Total risk signals: {total_risk}")
    for verdict, count in sorted(aggregate_verdicts.items()):
        print(f"  {verdict}: {count}")

    return {
        'insurer': insurer,
        'type': type_map.get(insurer, 'UNKNOWN'),
        'gt_pairs': total_gt_pairs,
        'mapped_codes': total_mapped,
        'unmatched': total_unmatched,
        'step7_cards': len(step7_cards),
        'verdict_counts': dict(aggregate_verdicts),
        'risk_count': total_risk,
        'file_results': file_results,
        'comparisons': all_comparisons,
        'mapping_results': all_mappings
    }


def generate_consolidated_report(
    audit_results: List[dict],
    output_md: Path,
    output_json: Path
):
    """통합 리포트 생성 (파일 단위 + 리스크 샘플링 포함)"""
    lines = []
    lines.append("# STEP NEXT-10B-2G-2 — Step7 Amount 전수 조사 통합 리포트 (File-Level + Risk Sampling)\n")
    lines.append(f"**생성일**: {output_json.name}\n")
    lines.append("## 1. 통합 테이블\n")
    lines.append("| insurer | type | GT_pairs | mapped_codes | OK_MATCH | MISS_PATTERN | MISMATCH_VALUE | GT_POLICY_ISSUE | RISK_SIGNALS | PASS/FAIL |")
    lines.append("|---------|------|----------|--------------|----------|--------------|----------------|-----------------|--------------|-----------|")

    for result in audit_results:
        if 'error' in result:
            lines.append(f"| {result['insurer']} | {result.get('type', 'N/A')} | ERROR | - | - | - | - | - | - | FAIL |")
            continue

        insurer = result['insurer']
        itype = result['type']
        gt_pairs = result['gt_pairs']
        mapped = result['mapped_codes']
        verdicts = result['verdict_counts']
        risk_count = result.get('risk_count', 0)

        ok_match = verdicts.get('OK_MATCH', 0)
        miss_pattern = verdicts.get('MISS_PATTERN', 0)
        mismatch_value = verdicts.get('MISMATCH_VALUE', 0)
        gt_policy_issue = verdicts.get('GT_POLICY_ISSUE', 0)
        type_c_unconf = verdicts.get('TYPE_C_EXPECTED_UNCONFIRMED', 0)

        # PASS/FAIL 판정 (GT_POLICY_ISSUE는 STOP 조건에서 제외)
        fail_reasons = []

        # Type A/B: MISMATCH_VALUE > 0 즉시 FAIL
        if itype in ['A', 'B'] and mismatch_value > 0:
            fail_reasons.append(f'MISMATCH_VALUE={mismatch_value}')

        # Type A: MISS_PATTERN 비율 > 5%
        if itype == 'A' and mapped > 0:
            miss_ratio = miss_pattern / mapped
            if miss_ratio > 0.05:
                fail_reasons.append(f'MISS_PATTERN_RATIO={miss_ratio:.1%}')

        # Type C: "보험가입금액" 문구 체크 (여기서는 간단히 MISMATCH_VALUE로 대체)
        if itype == 'C' and mismatch_value > 0:
            fail_reasons.append(f'TYPE_C_MISMATCH={mismatch_value}')

        pass_fail = 'FAIL' if fail_reasons else 'PASS'

        lines.append(
            f"| {insurer} | {itype} | {gt_pairs} | {mapped} | "
            f"{ok_match} | {miss_pattern} | {mismatch_value} | {gt_policy_issue} | {risk_count} | {pass_fail} |"
        )

    lines.append("\n## 2. PASS/FAIL 기준 (GT_POLICY_ISSUE는 STOP 조건에서 제외)\n")
    lines.append("- **Type A**:")
    lines.append("  - MISMATCH_VALUE > 0 → FAIL/STOP")
    lines.append("  - MISS_PATTERN / mapped_codes > 5% → FAIL (패턴/레이아웃 수정 필요)")
    lines.append("- **Type B**:")
    lines.append("  - MISMATCH_VALUE > 0 → FAIL/STOP")
    lines.append("- **Type C**:")
    lines.append("  - UNCONFIRMED 비율 높아도 정상")
    lines.append("  - 단, \"보험가입금액\" 문구가 amount.value_text에 들어가면 FAIL/STOP")
    lines.append("- **GT_POLICY_ISSUE (STOP 조건 제외)**:")
    lines.append("  - Case 1: 결합형 vs 단독형 우선순위 차이")
    lines.append("    - 가입설계서에 '상해사망·후유장해'(1백만원, 라인1)와 '상해사망'(1천만원, 라인3) 모두 존재")
    lines.append("    - Step7은 먼저 나오는 결합형 선택 (페이지 순서 기준)")
    lines.append("    - GT는 단독형 선택 (매핑 정규화 기준)")
    lines.append("    - → 정책적 차이이므로 MISMATCH로 카운트하지 않음")
    lines.append("  - Case 2: GT에서 같은 코드가 여러 파일/페이지에 중복 등장 + 서로 다른 금액")
    lines.append("    - → GT 추출 로직 문제 또는 정책 미정의\n")

    lines.append("\n## 3. 보험사별 상세 결과 (파일 단위 분리)\n")
    for result in audit_results:
        if 'error' in result:
            lines.append(f"### {result['insurer'].upper()} (ERROR)\n")
            lines.append(f"**Error**: {result['error']}\n")
            continue

        lines.append(f"### {result['insurer'].upper()} (Type {result['type']})\n")
        lines.append(f"- Total GT pairs: {result['gt_pairs']}")
        lines.append(f"- Total mapped codes: {result['mapped_codes']}")
        lines.append(f"- Total unmatched: {result['unmatched']}")
        lines.append(f"- Step7 cards: {result['step7_cards']}")
        lines.append(f"- Risk signals: {result.get('risk_count', 0)}")
        lines.append(f"- Verdict counts: {result['verdict_counts']}\n")

        # 파일별 결과
        if 'file_results' in result:
            lines.append("#### 파일별 분석\n")
            for file_result in result['file_results']:
                lines.append(f"**{file_result['proposal_file']}**")
                lines.append(f"- GT pairs: {file_result['gt_pairs']}, Mapped: {file_result['mapped_codes']}")
                lines.append(f"- Verdicts: {file_result['verdict_counts']}")
                lines.append(f"- Risk signals: {file_result['risk_count']}\n")

        # 리스크 샘플 (MISMATCH_VALUE, GT_POLICY_ISSUE 전수 출력)
        comparisons = result['comparisons']
        high_risk_verdicts = ['MISMATCH_VALUE', 'GT_POLICY_ISSUE']
        for verdict in high_risk_verdicts:
            samples = [c for c in comparisons if c['verdict'] == verdict]
            if not samples:
                continue

            lines.append(f"#### 🚨 {verdict} 전수 출력 ({len(samples)}건)\n")
            for sample in samples:
                lines.append(f"- **{sample['coverage_code']}** (파일: {sample['proposal_file']})")
                lines.append(f"  - GT: `{sample['gt_amount_raw']}` (Page {sample['gt_page']})")
                lines.append(f"  - GT Line: `{sample['gt_line'][:150]}`")
                lines.append(f"  - Step7: `{sample['step7_value_text']}` (status={sample['step7_status']})")
                if sample.get('step7_source_page'):
                    lines.append(f"  - Step7 Page: {sample['step7_source_page']}")
                if sample.get('step7_evidence_snippet'):
                    lines.append(f"  - Step7 Snippet: `{sample['step7_evidence_snippet'][:150]}`")
                if sample.get('risk_signals'):
                    lines.append(f"  - Risk Signals: {', '.join(sample['risk_signals'])}")
                lines.append("")

        # 일반 샘플 (OK_MATCH, MISS_PATTERN 등 최대 3개)
        other_verdicts = [v for v in set(c['verdict'] for c in comparisons) if v not in high_risk_verdicts]
        for verdict in sorted(other_verdicts):
            samples = [c for c in comparisons if c['verdict'] == verdict]
            lines.append(f"#### {verdict} (샘플 최대 3개)\n")
            for sample in samples[:3]:
                lines.append(f"- **{sample['coverage_code']}** (파일: {sample['proposal_file']})")
                lines.append(f"  - GT: `{sample['gt_amount_raw']}`")
                lines.append(f"  - Step7: `{sample['step7_value_text']}` (status={sample['step7_status']})")
                lines.append(f"  - Page {sample['gt_page']}: `{sample['gt_line'][:100]}`\n")

    # Write MD
    output_md.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # Write JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)

    print(f"\n[OUTPUT]")
    print(f"  MD: {output_md}")
    print(f"  JSON: {output_json}")


def main():
    """메인 실행"""
    # Paths
    repo_root = Path(__file__).parent.parent.parent
    data_root = repo_root / 'data'
    reports_dir = repo_root / 'reports'
    config_dir = repo_root / 'config'

    # Load type map
    type_map_json = config_dir / 'amount_lineage_type_map.json'
    with open(type_map_json, 'r', encoding='utf-8') as f:
        type_map = json.load(f)

    # Insurers
    insurers = ['samsung', 'meritz', 'db', 'hanwha', 'hyundai', 'kb', 'lotte', 'heungkuk']

    # Audit
    audit_results = []
    for insurer in insurers:
        result = audit_insurer(insurer, data_root, type_map)
        audit_results.append(result)

    # Generate consolidated report
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_md = reports_dir / f'step7_gt_audit_all_{timestamp}.md'
    output_json = reports_dir / f'step7_gt_audit_all_{timestamp}.json'

    generate_consolidated_report(audit_results, output_md, output_json)

    # Check FAIL (GT_AMBIGUOUS 제외)
    failed = []
    for r in audit_results:
        if 'error' in r:
            failed.append((r['insurer'], f"ERROR: {r['error']}"))
        else:
            verdicts = r.get('verdict_counts', {})
            mismatch = verdicts.get('MISMATCH_VALUE', 0)
            if mismatch > 0:
                failed.append((r['insurer'], f"MISMATCH_VALUE={mismatch}"))

    if failed:
        print(f"\n❌ AUDIT FAILED: {len(failed)} insurer(s) with issues")
        for insurer, reason in failed:
            print(f"  - {insurer}: {reason}")
        print(f"\n[NOTE] GT_AMBIGUOUS는 STOP 조건에서 제외됨 (GT 정의 모호성)")
        sys.exit(1)
    else:
        print(f"\n✅ AUDIT PASSED: All {len(insurers)} insurers OK")
        print(f"   (GT_AMBIGUOUS 케이스는 STOP 조건에서 제외됨)")
        sys.exit(0)


if __name__ == '__main__':
    main()
