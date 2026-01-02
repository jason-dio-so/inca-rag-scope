"""
STEP NEXT-72: Build Slim Coverage Cards + Split Detail/Evidence Stores

입력:
- data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl
- data/evidence_pack/{INSURER}_evidence_pack.jsonl

출력:
- data/compare/{INSURER}_coverage_cards_slim.jsonl (경량 카드, refs만)
- data/detail/{INSURER}_proposal_detail_store.jsonl (가입설계서 DETAIL)
- data/detail/{INSURER}_evidence_store.jsonl (사업방법서/상품요약서/약관 근거)
"""

import argparse
import csv
import json
import hashlib
from pathlib import Path
import sys
from typing import List, Dict, Optional

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.compare_types import (
    CoverageCardSlim,
    ProposalDetailRecord,
    EvidenceRecord,
    Evidence,
    CustomerView,
    CompareStats,
    KPISummary,
    KPIConditionSummary
)
from core.customer_view_builder import build_customer_view
from core.kpi_extractor import extract_kpi_from_text, PaymentType
from core.kpi_condition_extractor import KPIConditionExtractor


def _calculate_hash(text: str) -> str:
    """SHA256 해시 계산"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _generate_proposal_detail_ref(insurer: str, coverage_code: str) -> str:
    """가입설계서 DETAIL ref 생성: PD:{insurer}:{coverage_code}"""
    return f"PD:{insurer}:{coverage_code}"


def _generate_evidence_ref(insurer: str, coverage_code: str, index: int) -> str:
    """근거 자료 ref 생성: EV:{insurer}:{coverage_code}:{nn}"""
    return f"EV:{insurer}:{coverage_code}:{index:02d}"


def _select_diverse_evidences(evidences: List[Evidence], max_count: int = 3) -> List[Evidence]:
    """
    Evidence diversity selection (기존 Step5 로직 유지)

    Rules:
    1. Dedup by (doc_type, file_path, page, snippet)
    2. Fallback 판정: 'fallback_' 포함 OR 'token_and(' 시작
    3. Priority: Non-fallback > 약관 > 사업방법서 > 상품요약서 > page asc
    4. Diversity pass: 각 doc_type 1개씩
    5. Fill-up pass: max_count까지 채우기
    """
    if not evidences:
        return []

    def dedup_key(ev: Evidence) -> tuple:
        return (ev.doc_type, ev.file_path, ev.page, ev.snippet)

    def is_fallback(ev: Evidence) -> bool:
        if not ev.match_keyword:
            return False
        mk_lower = ev.match_keyword.lower()
        return 'fallback_' in mk_lower or ev.match_keyword.startswith('token_and(')

    doc_type_priority_map = {
        '가입설계서': -1,
        '약관': 0,
        '사업방법서': 1,
        '상품요약서': 2
    }

    def doc_type_priority_index(ev: Evidence) -> int:
        return doc_type_priority_map.get(ev.doc_type, 999)

    def sort_key(ev: Evidence):
        return (
            is_fallback(ev),
            doc_type_priority_index(ev),
            ev.page,
            ev.file_path,
            ev.snippet
        )

    # 중복 제거
    seen_keys = set()
    unique_evidences = []
    for ev in evidences:
        key = dedup_key(ev)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_evidences.append(ev)

    # doc_type별 그룹화
    by_doc_type = {}
    for ev in unique_evidences:
        doc_type = ev.doc_type
        if doc_type not in by_doc_type:
            by_doc_type[doc_type] = []
        by_doc_type[doc_type].append(ev)

    # 각 doc_type 내 정렬
    for doc_type in by_doc_type:
        by_doc_type[doc_type].sort(key=sort_key)

    selected = []
    doc_type_priority = ['가입설계서', '약관', '사업방법서', '상품요약서']

    # 1차: 각 doc_type 1개씩
    for doc_type in doc_type_priority:
        if doc_type in by_doc_type and len(selected) < max_count:
            selected.append(by_doc_type[doc_type][0])

    # 2차: Fill-up
    if len(selected) < max_count:
        selected_set = set(id(ev) for ev in selected)
        remaining = [ev for ev in unique_evidences if id(ev) not in selected_set]
        remaining.sort(key=sort_key)
        for ev in remaining:
            if len(selected) >= max_count:
                break
            selected.append(ev)

    return selected[:max_count]


def build_coverage_cards_slim(
    scope_canonical_jsonl: str,
    evidence_pack_jsonl: str,
    insurer: str,
    output_cards_slim_jsonl: str,
    output_proposal_detail_store_jsonl: str,
    output_evidence_store_jsonl: str
) -> CompareStats:
    """
    STEP NEXT-72: 경량 Coverage Cards + 분리 저장소 생성

    Args:
        scope_canonical_jsonl: Step2-b canonical scope JSONL
        evidence_pack_jsonl: Step4 evidence pack JSONL
        insurer: 보험사명
        output_cards_slim_jsonl: 경량 카드 출력 경로
        output_proposal_detail_store_jsonl: DETAIL 저장소 출력 경로
        output_evidence_store_jsonl: 근거 저장소 출력 경로

    Returns:
        CompareStats: 통계
    """
    # 1. Scope canonical JSONL 읽기 (proposal_facts, proposal_detail_facts 포함)
    scope_data = {}
    proposal_facts_map = {}
    proposal_detail_facts_map = {}

    with open(scope_canonical_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            coverage_name_raw = row['coverage_name_raw']
            coverage_code = row.get('coverage_code', '')

            scope_data[coverage_name_raw] = {
                'coverage_code': coverage_code if coverage_code else None,
                'coverage_name_canonical': row.get('canonical_name', ''),
                'mapping_status': 'matched' if row.get('mapping_method') != 'unmapped' else 'unmatched'
            }

            if 'proposal_facts' in row:
                proposal_facts_map[coverage_name_raw] = row['proposal_facts']

            if 'proposal_detail_facts' in row and row['proposal_detail_facts']:
                proposal_detail_facts_map[coverage_name_raw] = row['proposal_detail_facts']

    # 2. Evidence pack JSONL 읽기
    evidence_data = {}
    with open(evidence_pack_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)

            # Skip meta record
            if item.get('record_type') == 'meta':
                continue

            coverage_name_raw = item['coverage_name_raw']
            evidences = [Evidence.from_dict(e) for e in item.get('evidences', [])]

            evidence_data[coverage_name_raw] = {
                'evidences': evidences
            }

    # 3. 저장소 및 카드 생성
    cards_slim: List[CoverageCardSlim] = []
    proposal_detail_store: List[ProposalDetailRecord] = []
    evidence_store: List[EvidenceRecord] = []

    proposal_detail_hash_map = {}  # hash -> ref (dedup)
    evidence_hash_map = {}  # hash -> ref (dedup)

    stats = {
        'total': 0,
        'matched': 0,
        'unmatched': 0,
        'evidence_found': 0,
        'evidence_not_found': 0
    }

    for coverage_name_raw, scope_info in scope_data.items():
        stats['total'] += 1

        coverage_code = scope_info['coverage_code']
        coverage_name_canonical = scope_info['coverage_name_canonical']
        mapping_status = scope_info['mapping_status']

        if mapping_status == 'matched':
            stats['matched'] += 1
        else:
            stats['unmatched'] += 1

        # 4. Proposal DETAIL 처리 (DETAIL store에 저장, slim card에는 ref만)
        proposal_detail_ref = None
        proposal_detail_facts = proposal_detail_facts_map.get(coverage_name_raw)

        if proposal_detail_facts and coverage_code:
            benefit_text = proposal_detail_facts.get('benefit_description_text', '')
            page = proposal_detail_facts.get('detail_page', 0)

            if benefit_text:
                # Hash 계산
                detail_hash_input = f"{insurer}|{coverage_code}|{page}|{benefit_text}"
                detail_hash = _calculate_hash(detail_hash_input)

                # Dedup 확인
                if detail_hash in proposal_detail_hash_map:
                    proposal_detail_ref = proposal_detail_hash_map[detail_hash]
                else:
                    proposal_detail_ref = _generate_proposal_detail_ref(insurer, coverage_code)
                    proposal_detail_hash_map[detail_hash] = proposal_detail_ref

                    # DETAIL store에 추가
                    detail_record = ProposalDetailRecord(
                        proposal_detail_ref=proposal_detail_ref,
                        insurer=insurer,
                        coverage_code=coverage_code,
                        doc_type='가입설계서',
                        page=page,
                        benefit_description_text=benefit_text,
                        hash=detail_hash
                    )
                    proposal_detail_store.append(detail_record)

        # 5. Evidence 처리 (diversity selection → evidence store에 저장, slim card에는 refs만)
        evidence_refs = []
        ev_data = evidence_data.get(coverage_name_raw, {'evidences': []})
        evidences = ev_data['evidences']

        if evidences:
            stats['evidence_found'] += 1
        else:
            stats['evidence_not_found'] += 1

        # Diversity selection (최대 3개)
        selected_evidences = _select_diverse_evidences(evidences, max_count=3)

        for idx, ev in enumerate(selected_evidences, start=1):
            # Hash 계산
            ev_hash_input = f"{ev.doc_type}|{ev.page}|{ev.snippet}"
            ev_hash = _calculate_hash(ev_hash_input)

            # Dedup 확인
            if ev_hash in evidence_hash_map:
                ev_ref = evidence_hash_map[ev_hash]
            else:
                # coverage_code가 없으면 raw name 사용 (fallback)
                code_for_ref = coverage_code if coverage_code else coverage_name_raw.replace(' ', '_')
                ev_ref = _generate_evidence_ref(insurer, code_for_ref, idx)
                evidence_hash_map[ev_hash] = ev_ref

                # Evidence store에 추가
                ev_record = EvidenceRecord(
                    evidence_ref=ev_ref,
                    insurer=insurer,
                    coverage_code=coverage_code if coverage_code else '',
                    doc_type=ev.doc_type,
                    page=ev.page,
                    snippet=ev.snippet,
                    match_keyword=ev.match_keyword,
                    hash=ev_hash
                )
                evidence_store.append(ev_record)

            evidence_refs.append(ev_ref)

        # 6. Customer view 생성 (DETAIL 원문 대신 ref 기반)
        customer_view = None
        if selected_evidences or proposal_detail_facts:
            # Evidence dicts 준비
            evidences_dicts = [ev.to_dict() for ev in selected_evidences]

            # Customer view 생성 (기존 로직 유지)
            customer_view_dict = build_customer_view(
                evidences_dicts,
                proposal_detail_facts=proposal_detail_facts,
                insurer=insurer,
                coverage_name_raw=coverage_name_raw
            )
            customer_view = CustomerView.from_dict(customer_view_dict)

        # 6b. STEP NEXT-74: KPI 추출 (지급유형 / 한도)
        kpi_summary = None
        kpi_extraction_notes = []
        benefit_text_for_condition = None

        # Priority 1: 가입설계서 DETAIL
        if proposal_detail_facts and proposal_detail_facts.get('benefit_description_text'):
            benefit_text = proposal_detail_facts['benefit_description_text']
            benefit_text_for_condition = benefit_text
            kpi_result = extract_kpi_from_text(benefit_text)

            kpi_evidence_refs = []
            if proposal_detail_ref:
                kpi_evidence_refs.append(proposal_detail_ref)

            kpi_summary = KPISummary(
                payment_type=kpi_result['payment_type'].value,
                limit_summary=kpi_result['limit_summary'],
                kpi_evidence_refs=kpi_evidence_refs,
                extraction_notes=f"Extracted from proposal DETAIL (page {proposal_detail_facts.get('detail_page', 0)})"
            )
        # Priority 2-4: Fallback to evidences (사업방법서 > 상품요약서 > 약관)
        elif selected_evidences:
            # Try evidences in priority order
            doc_type_priority = ['사업방법서', '상품요약서', '약관']
            kpi_result = None
            source_evidence = None

            for doc_type in doc_type_priority:
                for ev in selected_evidences:
                    if ev.doc_type == doc_type and ev.snippet:
                        candidate_kpi = extract_kpi_from_text(ev.snippet)
                        # Accept if we got meaningful extraction
                        if candidate_kpi['payment_type'] != PaymentType.UNKNOWN or candidate_kpi['limit_summary']:
                            kpi_result = candidate_kpi
                            source_evidence = ev
                            break
                if kpi_result:
                    break

            # If still no result, try first evidence with any extraction
            if not kpi_result:
                for ev in selected_evidences:
                    if ev.snippet:
                        candidate_kpi = extract_kpi_from_text(ev.snippet)
                        if candidate_kpi['payment_type'] != PaymentType.UNKNOWN or candidate_kpi['limit_summary']:
                            kpi_result = candidate_kpi
                            source_evidence = ev
                            break

            # Create KPI summary if we found anything
            if kpi_result:
                kpi_evidence_refs = []
                # Find the ref for source evidence
                if source_evidence:
                    for idx, ev in enumerate(selected_evidences, start=1):
                        if ev == source_evidence and evidence_refs:
                            # Find corresponding ref
                            if idx <= len(evidence_refs):
                                kpi_evidence_refs.append(evidence_refs[idx-1])
                            break

                kpi_summary = KPISummary(
                    payment_type=kpi_result['payment_type'].value,
                    limit_summary=kpi_result['limit_summary'],
                    kpi_evidence_refs=kpi_evidence_refs,
                    extraction_notes=f"Extracted from {source_evidence.doc_type if source_evidence else 'evidence'}" if source_evidence else "Extracted from evidence"
                )
            else:
                # No meaningful extraction - create UNKNOWN
                kpi_summary = KPISummary(
                    payment_type=PaymentType.UNKNOWN.value,
                    limit_summary=None,
                    kpi_evidence_refs=[],
                    extraction_notes="No KPI patterns matched"
                )
        else:
            # No sources available
            kpi_summary = KPISummary(
                payment_type=PaymentType.UNKNOWN.value,
                limit_summary=None,
                kpi_evidence_refs=[],
                extraction_notes="No evidence or proposal detail available"
            )

        # 6c. STEP NEXT-76: KPI Condition 추출 (면책/감액/대기기간/갱신)
        kpi_condition = None

        # Evidence records 준비 (KPIConditionExtractor가 요구하는 형식)
        evidence_records_for_condition = []
        for idx, ev in enumerate(selected_evidences):
            if idx < len(evidence_refs):
                evidence_records_for_condition.append({
                    'doc_type': ev.doc_type,
                    'snippet': ev.snippet,
                    'evidence_ref': evidence_refs[idx]
                })

        # Extract conditions
        kpi_condition = KPIConditionExtractor.extract(
            proposal_detail_text=benefit_text_for_condition,
            evidence_records=evidence_records_for_condition,
            proposal_detail_ref=proposal_detail_ref
        )

        # 7. Slim card 생성
        refs = {
            'proposal_detail_ref': proposal_detail_ref,
            'evidence_refs': evidence_refs
        }

        card_slim = CoverageCardSlim(
            insurer=insurer,
            coverage_code=coverage_code,
            coverage_name_canonical=coverage_name_canonical if coverage_name_canonical else None,
            coverage_name_raw=coverage_name_raw,
            mapping_status=mapping_status,
            proposal_facts=proposal_facts_map.get(coverage_name_raw),
            customer_view=customer_view,
            refs=refs,
            kpi_summary=kpi_summary,
            kpi_condition=kpi_condition
        )
        cards_slim.append(card_slim)

    # 8. 정렬
    cards_slim.sort(key=lambda c: c.sort_key())

    # 9. JSONL 저장
    # Slim cards
    with open(output_cards_slim_jsonl, 'w', encoding='utf-8') as f:
        for card in cards_slim:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + '\n')

    # Proposal detail store
    with open(output_proposal_detail_store_jsonl, 'w', encoding='utf-8') as f:
        for detail in proposal_detail_store:
            f.write(json.dumps(detail.to_dict(), ensure_ascii=False) + '\n')

    # Evidence store
    with open(output_evidence_store_jsonl, 'w', encoding='utf-8') as f:
        for ev in evidence_store:
            f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + '\n')

    print(f"\n[STEP NEXT-72] Coverage Cards Slim 생성 완료")
    print(f"  - Slim cards: {len(cards_slim)} 건")
    print(f"  - Proposal detail store: {len(proposal_detail_store)} 건")
    print(f"  - Evidence store: {len(evidence_store)} 건")

    return CompareStats(
        total_coverages=stats['total'],
        matched=stats['matched'],
        unmatched=stats['unmatched'],
        evidence_found=stats['evidence_found'],
        evidence_not_found=stats['evidence_not_found']
    )


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Build slim coverage cards + split stores')
    parser.add_argument('--insurer', type=str, required=True, help='보험사명')
    args = parser.parse_args()

    insurer = args.insurer
    base_dir = Path(__file__).parent.parent.parent

    # 입력 파일
    scope_canonical_jsonl = base_dir / "data" / "scope_v3" / f"{insurer}_step2_canonical_scope_v1.jsonl"
    evidence_pack_jsonl = base_dir / "data" / "evidence_pack" / f"{insurer}_evidence_pack.jsonl"

    if not scope_canonical_jsonl.exists():
        print(f"[ERROR] Scope canonical JSONL not found: {scope_canonical_jsonl}")
        sys.exit(1)

    if not evidence_pack_jsonl.exists():
        print(f"[ERROR] Evidence pack JSONL not found: {evidence_pack_jsonl}")
        sys.exit(1)

    # 출력 디렉토리 생성
    output_cards_slim_jsonl = base_dir / "data" / "compare" / f"{insurer}_coverage_cards_slim.jsonl"
    output_proposal_detail_store_jsonl = base_dir / "data" / "detail" / f"{insurer}_proposal_detail_store.jsonl"
    output_evidence_store_jsonl = base_dir / "data" / "detail" / f"{insurer}_evidence_store.jsonl"

    output_cards_slim_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_proposal_detail_store_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_evidence_store_jsonl.parent.mkdir(parents=True, exist_ok=True)

    print(f"[STEP NEXT-72] Build Slim Coverage Cards")
    print(f"  Insurer: {insurer}")
    print(f"  Input scope: {scope_canonical_jsonl}")
    print(f"  Input evidence: {evidence_pack_jsonl}")

    # 생성
    stats = build_coverage_cards_slim(
        str(scope_canonical_jsonl),
        str(evidence_pack_jsonl),
        insurer,
        str(output_cards_slim_jsonl),
        str(output_proposal_detail_store_jsonl),
        str(output_evidence_store_jsonl)
    )

    print(f"\n[STEP NEXT-72] 통계:")
    print(f"  - Total coverages: {stats.total_coverages}")
    print(f"  - Matched: {stats.matched}")
    print(f"  - Unmatched: {stats.unmatched}")
    print(f"  - Evidence found: {stats.evidence_found}")
    print(f"  - Evidence not found: {stats.evidence_not_found}")
    print(f"\n✓ Slim cards: {output_cards_slim_jsonl}")
    print(f"✓ Proposal detail store: {output_proposal_detail_store_jsonl}")
    print(f"✓ Evidence store: {output_evidence_store_jsonl}")


if __name__ == "__main__":
    main()
