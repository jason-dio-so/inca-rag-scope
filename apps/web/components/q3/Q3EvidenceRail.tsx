/**
 * Q3EvidenceRail - Evidence Panel for Comprehensive Comparison Details
 *
 * Purpose: Show detailed evidence/sources for selected insurer row
 * Rules:
 * - Rail-only display (NO forbidden terms in main Q3 result table)
 * - Display slot details, assessment basis, sources
 */

'use client';

import { EvidenceRailBase, EvidenceSection } from '../evidence/EvidenceRailBase';

export interface Q3Row {
  ins_cd: string;
  insurer_name?: string;
  product_name?: string;
  slots?: Record<string, { value: any; evidence_refs?: string[] }>;
}

interface Q3EvidenceRailProps {
  selectedRow: Q3Row | null;
  coverageCode?: string;
  canonicalName?: string;
  onClose: () => void;
}

function formatValue(value: any): string {
  if (value == null) return '—';
  if (typeof value === 'number') {
    return value.toLocaleString('ko-KR');
  }
  return String(value);
}

export function Q3EvidenceRail({
  selectedRow,
  coverageCode,
  canonicalName,
  onClose
}: Q3EvidenceRailProps) {
  if (!selectedRow) return null;

  const slots = selectedRow.slots || {};
  const hasSlots = Object.keys(slots).length > 0;

  const sections: EvidenceSection[] = [
    // Section 1: 슬롯 상세
    {
      heading: '1. 슬롯 상세',
      body: (
        <div className="bg-green-50 rounded-lg p-4 space-y-3">
          {hasSlots ? (
            <div className="space-y-2">
              {Object.entries(slots).map(([slotName, slotData]) => (
                <div key={slotName} className="bg-white rounded p-3 border border-green-200">
                  <p className="text-xs text-gray-600 mb-1 font-semibold">{slotName}</p>
                  <p className="text-base font-bold text-gray-900">
                    {slotName.includes('amount') || slotName.includes('won')
                      ? `${formatValue(slotData.value)}원`
                      : formatValue(slotData.value)}
                  </p>
                  {slotData.evidence_refs && slotData.evidence_refs.length > 0 && (
                    <p className="text-xs text-gray-600 mt-2">
                      <span className="font-semibold">출처:</span>{' '}
                      {slotData.evidence_refs.join(', ')}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600">슬롯 정보 없음</p>
          )}
          {coverageCode && canonicalName && (
            <div className="mt-3 pt-3 border-t border-green-200">
              <p className="text-xs text-gray-700">
                <span className="font-semibold">담보:</span> {canonicalName} ({coverageCode})
              </p>
            </div>
          )}
        </div>
      )
    },

    // Section 2: 요약/추천의 입력 근거
    {
      heading: '2. 요약/추천의 입력 근거',
      body: (
        <div className="bg-blue-50 rounded-lg p-4 space-y-2">
          <p className="text-sm text-gray-700">
            <span className="font-semibold">기준:</span> 추출된 슬롯 값과 약관 정보를 바탕으로
            종합판단(Overall Assessment) 및 추천(Recommendation)이 생성됩니다.
          </p>
          {hasSlots && (
            <div className="mt-3 pt-3 border-t border-blue-200">
              <p className="text-xs text-gray-600 font-semibold mb-2">입력 조건:</p>
              <ul className="text-xs text-gray-700 space-y-1">
                {Object.entries(slots).map(([slotName, slotData]) => (
                  <li key={slotName} className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>
                      {slotName}: {formatValue(slotData.value)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )
    },

    // Section 3: 출처
    {
      heading: '3. 출처',
      body: (
        <div className="bg-gray-50 rounded-lg p-4">
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>모든 슬롯 값은 SSOT DB (약관/가입설계서 추출) 결과를 표시합니다.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>종합판단 및 추천은 LLM 기반으로 생성되며, 입력 근거는 위 슬롯 값입니다.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>
                근거/출처/사유/기준은 결과 테이블에 표시하지 않습니다(근거 레일 전용).
              </span>
            </li>
          </ul>
        </div>
      )
    }
  ];

  const insurerName = selectedRow.insurer_name || selectedRow.ins_cd;

  return (
    <EvidenceRailBase
      title={insurerName}
      subtitle={selectedRow.product_name}
      isOpen={true}
      onClose={onClose}
      sections={sections}
    />
  );
}
