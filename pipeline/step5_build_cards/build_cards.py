"""
Step 5: Build Coverage Cards

입력:
- data/scope/{INSURER}_scope_mapped.csv
- data/evidence_pack/{INSURER}_evidence_pack.jsonl

출력:
- data/compare/{INSURER}_coverage_cards.jsonl
"""

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.scope_gate import load_scope_gate, resolve_scope_csv
from core.compare_types import CoverageCard, Evidence, CompareStats, CustomerView
from core.customer_view_builder import build_customer_view


def _select_diverse_evidences(evidences: List[Evidence], max_count: int = 3) -> List[Evidence]:
    """
    STEP 6-ε.2: Doc-Type Diversity Evidence Selection with Dedup + Real-Fallback Priority LOCK

    Args:
        evidences: 전체 evidence 목록
        max_count: 최대 선택 개수 (기본 3)

    Returns:
        List[Evidence]: 선택된 evidence (최대 max_count개, 중복 제거됨)

    규칙:
        Rule 6-ε.2.1: Evidence Dedup (LOCK)
            - (doc_type, file_path, page, snippet) 기준 중복 제거
        Rule 6-ε.2.2: Fallback 판정 보정 (LOCK)
            - 'fallback_' 포함 OR 'token_and(' 시작 → fallback
        Rule 6-ε.2.3: Evidence Selection Priority (최종 LOCK)
            1. Non-fallback 우선
            2. doc_type priority: 약관 > 사업방법서 > 상품요약서
            3. page 오름차순
            4. file_path 오름차순
            5. snippet 오름차순 (동률 방지)
        Rule 6-ε.2.4: Fill-up 유지 (LOCK)
            - 중복 제거 후에도 max_count까지 보충
    """
    if not evidences:
        return []

    # Helper: dedup key (Rule 6-ε.2.1)
    def dedup_key(ev: Evidence) -> tuple:
        return (ev.doc_type, ev.file_path, ev.page, ev.snippet)

    # Helper: fallback 판정 (Rule 6-ε.2.2 — 보정)
    def is_fallback(ev: Evidence) -> bool:
        if not ev.match_keyword:
            return False
        mk_lower = ev.match_keyword.lower()
        # 'fallback_' 포함 OR 'token_and(' 시작
        return 'fallback_' in mk_lower or ev.match_keyword.startswith('token_and(')

    # Helper: doc_type priority index (STEP NEXT-64: 가입설계서 최우선)
    doc_type_priority_map = {
        '가입설계서': -1,  # STEP NEXT-64: Proposal evidence 최우선
        '약관': 0,
        '사업방법서': 1,
        '상품요약서': 2
    }

    def doc_type_priority_index(ev: Evidence) -> int:
        return doc_type_priority_map.get(ev.doc_type, 999)

    # Helper: sort key (Rule 6-ε.2.3)
    def sort_key(ev: Evidence):
        return (
            is_fallback(ev),           # 1. Non-fallback 우선
            doc_type_priority_index(ev),  # 2. doc_type priority
            ev.page,                   # 3. page 오름차순
            ev.file_path,              # 4. file_path 오름차순
            ev.snippet                 # 5. snippet 오름차순 (동률 방지)
        )

    # 중복 제거 (Rule 6-ε.2.1)
    seen_keys = set()
    unique_evidences = []
    for ev in evidences:
        key = dedup_key(ev)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_evidences.append(ev)

    # 1차 선택 (Diversity pass): 약관/사업방법서/상품요약서 각 1개씩
    by_doc_type = {}
    for ev in unique_evidences:
        doc_type = ev.doc_type
        if doc_type not in by_doc_type:
            by_doc_type[doc_type] = []
        by_doc_type[doc_type].append(ev)

    # 각 doc_type 내에서 정렬
    for doc_type in by_doc_type:
        by_doc_type[doc_type].sort(key=sort_key)

    selected = []
    # STEP NEXT-64: 가입설계서 최우선 추가
    doc_type_priority = ['가입설계서', '약관', '사업방법서', '상품요약서']

    # 1차 선택: 각 doc_type에서 1개씩 (가입설계서 최우선)
    for doc_type in doc_type_priority:
        if doc_type in by_doc_type and len(selected) < max_count:
            selected.append(by_doc_type[doc_type][0])

    # 2차 보충 (Fill-up pass): max_count까지 채우기 (Rule 6-ε.2.4)
    if len(selected) < max_count:
        # 선택되지 않은 evidence pool 구축 (이미 중복 제거된 unique_evidences 사용)
        selected_set = set(id(ev) for ev in selected)
        remaining = [ev for ev in unique_evidences if id(ev) not in selected_set]

        # 정렬 후 부족분 채우기
        remaining.sort(key=sort_key)
        for ev in remaining:
            if len(selected) >= max_count:
                break
            selected.append(ev)

    return selected[:max_count]


def build_coverage_cards(
    scope_mapped_csv: str,
    evidence_pack_jsonl: str,
    insurer: str,
    output_cards_jsonl: str,
    proposal_facts_map: dict = None,
    proposal_detail_facts_map: dict = None  # STEP NEXT-67D
) -> CompareStats:
    """
    Coverage cards 생성

    Args:
        scope_mapped_csv: scope mapped CSV 경로
        evidence_pack_jsonl: evidence pack JSONL 경로
        insurer: 보험사명
        output_cards_jsonl: 출력 cards JSONL 경로

    Returns:
        CompareStats: 통계
    """
    # STEP NEXT-61: Scope gate is NOT needed - CSV is already filtered from canonical JSONL
    # scope_gate = load_scope_gate(insurer)  # DEPRECATED for STEP NEXT-61

    # Scope mapped CSV 읽기
    scope_data = {}
    with open(scope_mapped_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coverage_name_raw = row['coverage_name_raw']

            # STEP NEXT-61: Scope gate validation removed - CSV is pre-filtered
            # All rows in CSV are already in-scope by definition

            scope_data[coverage_name_raw] = {
                'coverage_code': row.get('coverage_code', ''),
                'coverage_name_canonical': row.get('coverage_name_canonical', ''),
                'mapping_status': row['mapping_status']
            }

    # STEP NEXT-61: Evidence pack JSONL 읽기 (meta record validation)
    # Note: Hash validation is skipped when using temp CSV (JSONL→CSV conversion)
    from pathlib import Path as PathlibPath

    evidence_data = {}
    meta_validated = False
    first_record_processed = False

    # STEP NEXT-61: Check if this is a temp CSV (from JSONL conversion)
    is_temp_csv = PathlibPath(scope_mapped_csv).name.startswith('step5_')

    with open(evidence_pack_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip empty lines
            if not line.strip():
                continue

            item = json.loads(line)

            # STEP NEXT-61: Validate meta record (first non-empty line)
            if not first_record_processed:
                first_record_processed = True

                if item.get('record_type') != 'meta':
                    raise RuntimeError(
                        f"\n[STEP NEXT-61 GATE FAILED]\n"
                        f"Evidence pack missing meta record (first non-empty line).\n"
                        f"File: {evidence_pack_jsonl}\n"
                        f"Action: Run step4_evidence_search again for {insurer}"
                    )

                # STEP NEXT-61: Skip hash validation for temp CSV (JSONL→CSV conversion)
                if is_temp_csv:
                    print(f"\n[STEP NEXT-61 Meta Validation]")
                    print(f"  Scope file: {PathlibPath(scope_mapped_csv).name} (temp CSV from JSONL)")
                    print(f"  Evidence pack created: {item.get('created_at')}")
                    print(f"  ✓ Hash validation skipped (JSONL→CSV conversion)")
                else:
                    # Legacy: Validate scope_content_hash for native CSV
                    from core.scope_gate import calculate_scope_content_hash
                    current_scope_hash = calculate_scope_content_hash(PathlibPath(scope_mapped_csv))
                    pack_scope_hash = item.get('scope_content_hash')
                    if pack_scope_hash != current_scope_hash:
                        raise RuntimeError(
                            f"\n[STEP NEXT-31-P3 GATE FAILED]\n"
                            f"Scope content hash mismatch - stale evidence_pack detected.\n"
                            f"Details:\n"
                            f"  - Insurer: {insurer}\n"
                            f"  - Scope file: {PathlibPath(scope_mapped_csv).name}\n"
                            f"  - Evidence pack created with hash: {pack_scope_hash}\n"
                            f"  - Current scope hash: {current_scope_hash}\n"
                            f"Action: Run step4_evidence_search again to regenerate evidence_pack"
                        )
                    print(f"\n[STEP NEXT-31-P3 Content-Hash Gate]")
                    print(f"  Scope file: {PathlibPath(scope_mapped_csv).name}")
                    print(f"  Scope hash: {current_scope_hash[:16]}...")
                    print(f"  Evidence pack created: {item.get('created_at')}")
                    print(f"  ✓ Content hash validated")

                meta_validated = True
                continue  # Skip meta record, process evidence records only

            # Process evidence records (non-meta)
            coverage_name_raw = item['coverage_name_raw']

            # STEP NEXT-61: Scope gate validation removed - evidence pack is pre-filtered
            # All evidence pack records are already in-scope by definition

            evidences = [Evidence.from_dict(e) for e in item.get('evidences', [])]
            hits_by_doc_type = item.get('hits_by_doc_type', {})
            flags = item.get('flags', [])
            evidence_data[coverage_name_raw] = {
                'evidences': evidences,
                'hits_by_doc_type': hits_by_doc_type,
                'flags': flags
            }

    # Ensure meta was validated
    if not meta_validated:
        raise RuntimeError(
            f"\n[STEP NEXT-31-P3 GATE FAILED]\n"
            f"Evidence pack has no meta record.\n"
            f"File: {evidence_pack_jsonl}\n"
            f"Action: Run step4_evidence_search again for {insurer}"
        )

    # STEP NEXT-31-P1: Join-rate Gate (95% threshold)
    scope_rows = len(scope_data)
    pack_rows = len(evidence_data)
    join_hits = sum(1 for coverage_name_raw in scope_data if coverage_name_raw in evidence_data)
    join_rate = join_hits / scope_rows if scope_rows > 0 else 0.0

    print(f"\n[STEP NEXT-31-P1 Join-rate Gate]")
    print(f"  Scope rows: {scope_rows}")
    print(f"  Evidence pack rows: {pack_rows}")
    print(f"  Join hits: {join_hits}")
    print(f"  Join rate: {join_rate:.2%}")

    # GATE-5-2 (STEP NEXT-61): join_rate < 95% → FAIL
    if join_rate < 0.95:
        raise RuntimeError(
            f"\n[GATE-5-2 FAILED] (STEP NEXT-61)\n"
            f"Join rate {join_rate:.2%} is below 95% threshold.\n"
            f"This indicates stale or mismatched evidence_pack.\n"
            f"Details:\n"
            f"  - Insurer: {insurer}\n"
            f"  - Scope rows: {scope_rows}\n"
            f"  - Evidence pack rows: {pack_rows}\n"
            f"  - Join hits: {join_hits}\n"
            f"  - Join rate: {join_rate:.2%}\n"
            f"Action: Re-run step4_evidence_search with the same canonical scope JSONL."
        )

    print(f"  ✓ GATE-5-2 passed: Join rate {join_rate:.2%} ≥ 95%")

    # GATE-5-1 (STEP NEXT-61): Coverage count must match Step2-b output
    # (Informational - exact count match is expected but not hard-failing due to scope_gate filtering)
    if scope_rows != pack_rows:
        print(f"  ⚠ GATE-5-1 WARNING: Coverage count mismatch (scope:{scope_rows} vs pack:{pack_rows})")
        print(f"    This may be due to scope_gate filtering. Verify if intentional.")
    else:
        print(f"  ✓ GATE-5-1 passed: Coverage count matches ({scope_rows})")

    # Coverage cards 생성
    cards: List[CoverageCard] = []
    stats = {
        'total': 0,
        'matched': 0,
        'unmatched': 0,
        'evidence_found': 0,
        'evidence_not_found': 0
    }

    for coverage_name_raw, scope_info in scope_data.items():
        stats['total'] += 1

        # Mapping status
        mapping_status = scope_info['mapping_status']
        if mapping_status == 'matched':
            stats['matched'] += 1
        else:
            stats['unmatched'] += 1

        # Evidence status
        ev_data = evidence_data.get(coverage_name_raw, {'evidences': [], 'hits_by_doc_type': {}, 'flags': []})
        evidences = ev_data['evidences']
        hits_by_doc_type = ev_data['hits_by_doc_type']
        flags = ev_data['flags']

        # STEP NEXT-64: Get proposal_facts from map
        proposal_facts = None
        if proposal_facts_map:
            proposal_facts = proposal_facts_map.get(coverage_name_raw)

        # STEP NEXT-64: Convert proposal_facts.evidences to Evidence objects (최우선)
        proposal_evidences = []
        if proposal_facts and proposal_facts.get('evidences'):
            for pf_ev in proposal_facts['evidences']:
                # proposal_facts.evidences는 raw_row를 가지고 있음
                # snippet을 담보명 + 금액 + 보험료 + 기간으로 구성
                raw_row = pf_ev.get('raw_row', [])
                # raw_row 예시: ["", "암 진단비(유사암 제외)", "3,000만원", "40,620", "20년납 100세만기\nZD8"]
                snippet_parts = []
                if len(raw_row) > 1:
                    snippet_parts.append(f"담보명: {raw_row[1]}")
                if len(raw_row) > 2 and raw_row[2]:
                    snippet_parts.append(f"가입금액: {raw_row[2]}")
                if len(raw_row) > 3 and raw_row[3]:
                    snippet_parts.append(f"보험료: {raw_row[3]}")
                if len(raw_row) > 4 and raw_row[4]:
                    snippet_parts.append(f"납입기간: {raw_row[4]}")

                proposal_evidence = Evidence(
                    doc_type='가입설계서',
                    file_path='proposal_table',  # 가상 경로
                    page=pf_ev.get('page', 0),
                    snippet='\n'.join(snippet_parts),
                    match_keyword='proposal_table_row'
                )
                proposal_evidences.append(proposal_evidence)

        # STEP NEXT-64: 가입설계서 evidence를 맨 앞에 추가
        all_evidences = proposal_evidences + evidences

        # Evidence status (가입설계서 포함)
        evidence_status = 'found' if all_evidences else 'not_found'

        if evidence_status == 'found':
            stats['evidence_found'] += 1
        else:
            stats['evidence_not_found'] += 1

        # Coverage code/canonical (없으면 None)
        coverage_code = scope_info['coverage_code'] if scope_info['coverage_code'] else None
        coverage_name_canonical = scope_info['coverage_name_canonical'] if scope_info['coverage_name_canonical'] else None

        # STEP NEXT-64: Doc-Type Diversity Evidence Selection (최대 3개, 가입설계서 최우선)
        selected_evidences = _select_diverse_evidences(all_evidences, max_count=3)

        # STEP NEXT-67D: Get proposal_detail_facts for this coverage
        proposal_detail_facts = None
        if proposal_detail_facts_map:
            proposal_detail_facts = proposal_detail_facts_map.get(coverage_name_raw)

        # STEP NEXT-65R + 67D: Build customer_view from selected evidences + proposal DETAIL
        customer_view = None
        if selected_evidences:
            # Convert Evidence objects to dicts for customer_view_builder
            evidences_dicts = [ev.to_dict() for ev in selected_evidences]
            # STEP NEXT-67D + KB NEXT PATCH: Pass proposal_detail_facts, insurer, coverage_name_raw
            customer_view_dict = build_customer_view(
                evidences_dicts,
                proposal_detail_facts=proposal_detail_facts,
                insurer=insurer,
                coverage_name_raw=coverage_name_raw
            )
            customer_view = CustomerView.from_dict(customer_view_dict)

        # Card 생성 (STEP NEXT-68H: Add proposal_detail_facts)
        card = CoverageCard(
            insurer=insurer,
            coverage_name_raw=coverage_name_raw,
            coverage_code=coverage_code,
            coverage_name_canonical=coverage_name_canonical,
            mapping_status=mapping_status,
            evidence_status=evidence_status,
            evidences=selected_evidences,
            hits_by_doc_type=hits_by_doc_type,
            flags=flags,
            proposal_facts=proposal_facts,
            proposal_detail_facts=proposal_detail_facts,  # STEP NEXT-68H
            customer_view=customer_view
        )
        cards.append(card)

    # 정렬
    cards.sort(key=lambda c: c.sort_key())

    # JSONL 저장
    with open(output_cards_jsonl, 'w', encoding='utf-8') as f:
        for card in cards:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + '\n')

    # 통계 반환
    return CompareStats(
        total_coverages=stats['total'],
        matched=stats['matched'],
        unmatched=stats['unmatched'],
        evidence_found=stats['evidence_found'],
        evidence_not_found=stats['evidence_not_found']
    )


def main():
    """CLI 엔트리포인트 (STEP NEXT-61: temporarily accepts both CSV and JSONL)"""
    parser = argparse.ArgumentParser(description='Build coverage cards')
    parser.add_argument('--insurer', type=str, default='samsung', help='보험사명')
    args = parser.parse_args()

    insurer = args.insurer
    base_dir = Path(__file__).parent.parent.parent

    # STEP NEXT-61: Try canonical JSONL first (scope_v3), fallback to legacy CSV
    scope_canonical_jsonl = base_dir / "data" / "scope_v3" / f"{insurer}_step2_canonical_scope_v1.jsonl"

    # STEP NEXT-UI-FIX-04 + 67D: Keep proposal_facts and proposal_detail_facts in memory
    proposal_facts_map = {}
    proposal_detail_facts_map = {}  # STEP NEXT-67D

    if scope_canonical_jsonl.exists():
        # STEP NEXT-61: Convert JSONL to temporary CSV for compatibility
        import tempfile
        import csv
        temp_csv_fd, temp_csv_path = tempfile.mkstemp(suffix='.csv', prefix=f'step5_{insurer}_')
        with open(scope_canonical_jsonl, 'r', encoding='utf-8') as jsonl_f:
            rows = [json.loads(line) for line in jsonl_f if line.strip()]

        # STEP NEXT-UI-FIX-04 + 67D: Extract proposal_facts and proposal_detail_facts
        for row in rows:
            coverage_name_raw = row['coverage_name_raw']
            if 'proposal_facts' in row:
                proposal_facts_map[coverage_name_raw] = row['proposal_facts']
            # STEP NEXT-67D: Extract proposal_detail_facts
            if 'proposal_detail_facts' in row and row['proposal_detail_facts']:
                proposal_detail_facts_map[coverage_name_raw] = row['proposal_detail_facts']

        with open(temp_csv_path, 'w', newline='', encoding='utf-8') as csv_f:
            if rows:
                fieldnames = ['coverage_name_raw', 'coverage_code', 'coverage_name_canonical', 'mapping_status']
                writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow({
                        'coverage_name_raw': row['coverage_name_raw'],
                        'coverage_code': row.get('coverage_code', ''),
                        'coverage_name_canonical': row.get('canonical_name', ''),
                        'mapping_status': 'matched' if row.get('mapping_method') != 'unmapped' else 'unmatched'
                    })
        scope_mapped_csv = Path(temp_csv_path)
        print(f"[Step 5] Using STEP NEXT-61 canonical JSONL (converted to temp CSV)")
        print(f"[Step 5] Extracted proposal_facts for {len(proposal_facts_map)} coverages")
        print(f"[Step 5] Extracted proposal_detail_facts for {len(proposal_detail_facts_map)} coverages")  # STEP NEXT-67D
    else:
        # Fallback to legacy CSV
        scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")
        print(f"[Step 5] Using legacy CSV")

    evidence_pack_jsonl = base_dir / "data" / "evidence_pack" / f"{insurer}_evidence_pack.jsonl"

    # 출력 파일
    output_cards_jsonl = base_dir / "data" / "compare" / f"{insurer}_coverage_cards.jsonl"
    output_cards_jsonl.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Step 5] Build Coverage Cards (STEP NEXT-61)")
    print(f"[Step 5] Insurer: {insurer}")
    print(f"[Step 5] Input scope: {scope_mapped_csv}")
    print(f"[Step 5] Input evidence: {evidence_pack_jsonl}")

    # Cards 생성 (STEP NEXT-67D: pass proposal_detail_facts_map)
    stats = build_coverage_cards(
        str(scope_mapped_csv),
        str(evidence_pack_jsonl),
        insurer,
        str(output_cards_jsonl),
        proposal_facts_map=proposal_facts_map,
        proposal_detail_facts_map=proposal_detail_facts_map  # STEP NEXT-67D
    )

    print(f"\n[Step 5] Coverage cards created:")
    print(f"  - Total coverages: {stats.total_coverages}")
    print(f"  - Matched: {stats.matched}")
    print(f"  - Unmatched: {stats.unmatched}")
    print(f"  - Evidence found: {stats.evidence_found}")
    print(f"  - Evidence not found: {stats.evidence_not_found}")
    print(f"\n✓ Cards: {output_cards_jsonl}")


if __name__ == "__main__":
    main()
