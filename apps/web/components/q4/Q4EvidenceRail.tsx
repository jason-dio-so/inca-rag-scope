/**
 * Q4EvidenceRail - Evidence Panel for Support Matrix Cell Details
 *
 * Purpose: Show detailed evidence/sources for selected matrix cell (O/X/△)
 * Rules:
 * - Rail-only display (NO forbidden terms in main Q4 result table)
 * - Display status, coverage kind, evidence refs
 */

'use client';

import { EvidenceRailBase, EvidenceSection } from '../evidence/EvidenceRailBase';

export interface Q4CellData {
  status_icon: string;
  display: string;
  color: string;
  coverage_kind?: string;
  evidence_refs?: string[];
}

export interface Q4SelectedCell {
  insurer_key: string;
  insurer_name: string;
  cellType: 'in_situ' | 'borderline';
  cellData: Q4CellData;
}

interface Q4EvidenceRailProps {
  selectedCell: Q4SelectedCell | null;
  onClose: () => void;
}

function getStatusDescription(statusIcon: string): string {
  switch (statusIcon) {
    case '✅':
      return 'O - 진단비로 보장 (사용 가능)';
    case '❌':
      return 'X - 명시적으로 제외됨';
    case '⚠️':
      return '⚠️ - 진단비 아님 (치료비 트리거)';
    case '—':
      return '— - 정보 없음';
    default:
      return statusIcon;
  }
}

function getCoverageTypeLabel(cellType: 'in_situ' | 'borderline'): string {
  return cellType === 'in_situ' ? '제자리암 (상피내암)' : '경계성종양';
}

export function Q4EvidenceRail({
  selectedCell,
  onClose
}: Q4EvidenceRailProps) {
  if (!selectedCell) return null;

  const { cellData, cellType, insurer_name } = selectedCell;

  const sections: EvidenceSection[] = [
    // Section 1: 판정
    {
      heading: '1. 판정',
      body: (
        <div className="bg-purple-50 rounded-lg p-4 space-y-3">
          <div className="bg-white rounded p-3 border border-purple-200">
            <p className="text-xs text-gray-600 mb-1">담보 유형</p>
            <p className="text-base font-bold text-gray-900">
              {getCoverageTypeLabel(cellType)}
            </p>
          </div>
          <div className="bg-white rounded p-3 border border-purple-200">
            <p className="text-xs text-gray-600 mb-1">보장 여부</p>
            <p className="text-base font-bold text-gray-900">
              {getStatusDescription(cellData.status_icon)}
            </p>
          </div>
          {cellData.coverage_kind && (
            <div className="bg-orange-50 border border-orange-200 rounded p-3">
              <p className="text-xs text-orange-700 font-semibold mb-1">주의</p>
              <p className="text-sm text-orange-800">
                {cellData.coverage_kind === 'treatment_trigger'
                  ? '이 담보는 진단비가 아니라 치료비 트리거로만 언급됩니다. 직접 진단 시 보장되는지 약관 확인이 필요합니다.'
                  : cellData.coverage_kind}
              </p>
            </div>
          )}
        </div>
      )
    },

    // Section 2: 근거
    {
      heading: '2. 근거',
      body: (
        <div className="bg-blue-50 rounded-lg p-4 space-y-2">
          {cellData.evidence_refs && cellData.evidence_refs.length > 0 ? (
            <>
              <p className="text-sm text-gray-700 font-semibold mb-2">
                약관 출처:
              </p>
              <ul className="text-sm text-gray-700 space-y-1">
                {cellData.evidence_refs.map((ref, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>{ref}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-3 pt-3 border-t border-blue-200">
                <p className="text-xs text-gray-600">
                  <span className="font-semibold">출처:</span> SSOT DB (policy document extraction)
                </p>
              </div>
            </>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 space-y-2">
              <p className="text-sm font-semibold text-gray-900">약관에서 확인되지 않음</p>
              <p className="text-sm text-gray-700">
                <span className="font-semibold">사유:</span> 해당 담보에 대한 명시적 언급을
                약관에서 찾지 못했습니다. 이는 보장하지 않는다는 의미일 수도 있으나,
                최종 판단은 약관 전문과 보험사 확인이 필요합니다.
              </p>
            </div>
          )}
        </div>
      )
    },

    // Section 3: 주의사항
    {
      heading: '3. 주의사항',
      body: (
        <div className="bg-gray-50 rounded-lg p-4">
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>
                모든 판정은 약관 분석 결과를 기반으로 하며, SSOT DB에서 추출되었습니다.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>
                "—" (정보 없음)은 약관에서 해당 담보가 확인되지 않았다는 의미이며,
                보장 여부는 최종적으로 약관 전문과 보험사 확인이 필요합니다.
              </span>
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

  return (
    <EvidenceRailBase
      title={insurer_name}
      subtitle={getCoverageTypeLabel(cellType)}
      isOpen={true}
      onClose={onClose}
      sections={sections}
    />
  );
}
