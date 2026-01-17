/**
 * Q2EvidenceRail - Evidence Panel for Coverage Limit Details
 *
 * Purpose: Show detailed evidence/sources for selected coverage limit row
 * Rules:
 * - Rail-only display (NO forbidden terms in main Q2 result table)
 * - Display slot values, sources, and principles
 */

'use client';

import { EvidenceRailBase, EvidenceSection } from '../evidence/EvidenceRailBase';

export interface Q2Row {
  ins_cd: string;
  insurer_name?: string;
  product_name?: string;
  slots?: Record<string, { value: any; evidence_refs?: string[] }>;
}

interface Q2EvidenceRailProps {
  selectedRow: Q2Row | null;
  coverageCode: string;
  canonicalName: string;
  onClose: () => void;
}

function formatValue(value: any): string {
  if (value == null) return '—';
  if (typeof value === 'number') {
    return value.toLocaleString('ko-KR');
  }
  return String(value);
}

export function Q2EvidenceRail({
  selectedRow,
  coverageCode,
  canonicalName,
  onClose
}: Q2EvidenceRailProps) {
  if (!selectedRow) return null;

  const slots = selectedRow.slots || {};
  const durationLimit = slots.duration_limit_days?.value || null;
  const dailyBenefit = slots.daily_benefit_amount_won?.value || null;

  const sections: EvidenceSection[] = [
    // Section 1: 확인된 값
    {
      heading: '1. 확인된 값',
      body: (
        <div className="bg-blue-50 rounded-lg p-4 space-y-3">
          <div className="space-y-2">
            <div className="bg-white rounded p-3 border border-blue-200">
              <p className="text-xs text-gray-600 mb-1">보장한도 (일수)</p>
              <p className="text-base font-bold text-gray-900">
                {durationLimit ? `${formatValue(durationLimit)}일` : '—'}
              </p>
            </div>
            <div className="bg-white rounded p-3 border border-blue-200">
              <p className="text-xs text-gray-600 mb-1">일일보장금액 (원)</p>
              <p className="text-base font-bold text-gray-900">
                {dailyBenefit ? `${formatValue(dailyBenefit)}원` : '—'}
              </p>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-blue-200">
            <p className="text-xs text-gray-700">
              <span className="font-semibold">담보:</span> {canonicalName} ({coverageCode})
            </p>
          </div>
        </div>
      )
    },

    // Section 2: 출처/기준일
    {
      heading: '2. 출처/기준일',
      body: (
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <p className="text-sm text-gray-700">
            <span className="font-semibold">출처:</span> SSOT DB (slot extraction from policy documents)
          </p>
          <p className="text-sm text-gray-700">
            <span className="font-semibold">기준일:</span> 약관 기준일 (as_of_date)
          </p>
          {Object.keys(slots).length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-300">
              <p className="text-xs text-gray-600 font-semibold mb-2">추출된 슬롯:</p>
              <ul className="text-xs text-gray-700 space-y-1">
                {Object.entries(slots).map(([slotName, slotData]) => (
                  <li key={slotName} className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>
                      <strong>{slotName}:</strong> {formatValue(slotData.value)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )
    },

    // Section 3: 산출 원칙
    {
      heading: '3. 산출 원칙',
      body: (
        <div className="bg-gray-50 rounded-lg p-4">
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>모든 값은 약관/가입설계서에서 추출된 SSOT DB 결과를 표시합니다.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>UI에서 계산/추정/보정하지 않습니다.</span>
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
