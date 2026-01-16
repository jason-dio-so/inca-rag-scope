/**
 * STEP NEXT-COMPARE-FILTER-DETAIL-02: Enriched Coverage Difference Result Card
 *
 * Displays grouped comparison results with:
 * - Normalized value summaries
 * - Per-insurer evidence details (accordion)
 * - Extraction notes for "명시 없음" cases
 *
 * Example: "암직접입원비 보장한도가 다른 상품 찾아줘"
 */

'use client';

import { useState } from 'react';
import type { CoverageDiffResultSection, DiffGroup, InsurerDetail, EvidenceRef } from '../../lib/types';

// Insurer code to display name mapping
const INSURER_NAMES: Record<string, string> = {
  samsung: '삼성화재',
  meritz: '메리츠화재',
  db: 'DB손해보험',
  kb: 'KB손해보험',
  hanwha: '한화손해보험',
  hyundai: '현대해상',
  lotte: '롯데손해보험',
  heungkuk: '흥국화재',
};

function getInsurerDisplay(code: string): string {
  return INSURER_NAMES[code] || code;
}

// Normalized value summary renderer
function renderNormalizedSummary(normalized: Record<string, any> | undefined): string | null {
  if (!normalized) return null;

  const parts: string[] = [];

  // Limit fields
  if (normalized.count !== undefined && normalized.count !== null) {
    const periodMap: Record<string, string> = {
      lifetime: '평생',
      annual: '연간',
      monthly: '월',
      per_event: '건당',
    };
    const period = normalized.period ? periodMap[normalized.period] || normalized.period : '';
    parts.push(`횟수=${normalized.count}${period}회`);
  }

  if (normalized.range) {
    const { min, max, unit } = normalized.range;
    parts.push(`범위=${min}~${max}${unit || '일'}`);
  }

  if (Array.isArray(normalized.qualifier) && normalized.qualifier.length > 0) {
    parts.push(`조건=${normalized.qualifier.join(', ')}`);
  }

  // Payment type fields
  if (normalized.kind) {
    const kindMap: Record<string, string> = {
      lump_sum: '일시금',
      per_day: '일당',
      per_event: '건당',
      unknown: '미분류',
    };
    parts.push(`유형=${kindMap[normalized.kind] || normalized.kind}`);
  }

  // Condition tags
  if (Array.isArray(normalized.tags) && normalized.tags.length > 0) {
    parts.push(`태그=${normalized.tags.join(', ')}`);
  }

  return parts.length > 0 ? parts.join(' | ') : null;
}

// Evidence list renderer
function EvidenceList({ refs }: { refs: EvidenceRef[] }) {
  if (!Array.isArray(refs) || refs.length === 0) {
    return <div className="text-xs text-gray-400">근거 없음</div>;
  }

  return (
    <div className="space-y-2">
      {refs.slice(0, 3).map((ref, idx) => (
        <div key={idx} className="text-xs bg-gray-50 rounded p-2 border border-gray-200">
          <div className="flex items-baseline gap-2 mb-1">
            <span className="font-semibold text-gray-700">{String(ref.doc_type || '문서')}</span>
            <span className="text-gray-500">p.{ref.page || '?'}</span>
          </div>
          {ref.snippet && (
            <div className="text-gray-600 line-clamp-2">
              {String(ref.snippet)}
            </div>
          )}
        </div>
      ))}
      {refs.length > 3 && (
        <div className="text-xs text-gray-400">+ {refs.length - 3}개 근거 더보기</div>
      )}
    </div>
  );
}

// Insurer details accordion
function InsurerDetailsAccordion({ details }: { details: InsurerDetail[] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!Array.isArray(details) || details.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t border-gray-200 pt-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        <span>{isOpen ? '▼' : '▶'}</span>
        <span>보험사별 근거 보기 ({details.length}개)</span>
      </button>

      {isOpen && (
        <div className="mt-3 space-y-4">
          {details.map((detail, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              {/* Insurer name */}
              <div className="font-semibold text-gray-900 mb-2">
                {getInsurerDisplay(detail.insurer)}
              </div>

              {/* Raw text */}
              {detail.raw_text && String(detail.raw_text).trim() && (
                <div className="mb-3">
                  <div className="text-xs text-gray-500 mb-1">원문</div>
                  <div className="text-sm text-gray-700 bg-white p-2 rounded border border-gray-200">
                    {String(detail.raw_text)}
                  </div>
                </div>
              )}

              {/* Notes */}
              {Array.isArray(detail.notes) && detail.notes.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs text-gray-500 mb-1">참고</div>
                  <ul className="text-sm text-amber-700 space-y-1">
                    {detail.notes.map((note, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span>•</span>
                        <span>{String(note)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Evidence refs */}
              {Array.isArray(detail.evidence_refs) && detail.evidence_refs.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">근거 문서</div>
                  <EvidenceList refs={detail.evidence_refs} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Group card renderer
function GroupCard({ group, fieldLabel }: { group: DiffGroup; fieldLabel: string }) {
  const isNotSpecified = group.value_display === '명시 없음' || group.value_display === '담보 미존재';
  const normalizedSummary = renderNormalizedSummary(group.value_normalized);

  return (
    <div
      className={`border rounded-lg p-4 ${
        isNotSpecified ? 'bg-yellow-50 border-yellow-300' : 'border-gray-200 bg-white'
      }`}
    >
      {/* Header: value + insurer count */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <span className="text-sm text-gray-500 block mb-1">{fieldLabel}</span>
          <span className="text-lg font-semibold text-gray-900">{String(group.value_display)}</span>
        </div>
        <div className="text-sm text-gray-500">
          {Array.isArray(group.insurers) ? group.insurers.length : 0}개 보험사
        </div>
      </div>

      {/* Normalized summary */}
      {normalizedSummary && (
        <div className="mb-3 text-xs text-gray-600 bg-blue-50 border border-blue-200 rounded p-2">
          <span className="font-semibold">정규화:</span> {normalizedSummary}
        </div>
      )}

      {/* Insurer badges */}
      <div className="flex flex-wrap gap-2">
        {Array.isArray(group.insurers) &&
          group.insurers.map((insurer, i) => (
            <span
              key={i}
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                isNotSpecified
                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                  : 'bg-gray-100 text-gray-800 border border-gray-300'
              }`}
            >
              {getInsurerDisplay(String(insurer))}
            </span>
          ))}
      </div>

      {/* Insurer details accordion */}
      {Array.isArray(group.insurer_details) && group.insurer_details.length > 0 && (
        <InsurerDetailsAccordion details={group.insurer_details} />
      )}
    </div>
  );
}

// Main component
export function CoverageDiffCard({ section }: { section: CoverageDiffResultSection }) {
  // Guard: ensure groups is an array
  const groups = Array.isArray(section.groups) ? section.groups : [];

  // ALL_SAME mode
  if (section.status === 'ALL_SAME') {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{String(section.title || '비교 결과')}</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-900 font-medium mb-2">
            선택한 보험사의 {String(section.field_label || '값')}는 모두 동일합니다
          </p>
          {groups[0] && (
            <div className="mt-2">
              <span className="text-sm text-blue-700">공통 값: </span>
              <span className="text-sm font-semibold text-blue-900">{String(groups[0].value_display)}</span>
            </div>
          )}
        </div>

        {/* Extraction notes (if any) */}
        {Array.isArray(section.extraction_notes) && section.extraction_notes.length > 0 && (
          <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-sm font-semibold text-gray-700 mb-2">추출 참고</div>
            <ul className="text-sm text-gray-600 space-y-1">
              {section.extraction_notes.map((note, idx) => (
                <li key={idx} className="flex items-start gap-1">
                  <span>•</span>
                  <span>{String(note)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // DIFF mode
  return (
    <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{String(section.title || '비교 결과')}</h3>

      {/* Diff summary banner */}
      {section.diff_summary && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-amber-900 font-semibold">{String(section.diff_summary)}</p>
        </div>
      )}

      {/* Groups */}
      <div className="space-y-4">
        {groups.map((group, idx) => (
          <GroupCard key={idx} group={group} fieldLabel={String(section.field_label || '값')} />
        ))}
      </div>

      {/* Extraction notes */}
      {Array.isArray(section.extraction_notes) && section.extraction_notes.length > 0 && (
        <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
          <div className="text-sm font-semibold text-gray-700 mb-2">추출 참고</div>
          <ul className="text-sm text-gray-600 space-y-1">
            {section.extraction_notes.map((note, idx) => (
              <li key={idx} className="flex items-start gap-1">
                <span>•</span>
                <span>{String(note)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer note */}
      <div className="mt-4 text-xs text-gray-500">* 가입설계서 및 약관 기준 비교 결과입니다</div>
    </div>
  );
}
