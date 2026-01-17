/**
 * Q1EvidenceRail - Evidence Panel for Premium Details
 *
 * Purpose: Show detailed evidence/sources for selected premium row
 * Rules:
 * - Rail-only display (NO formulas in main table)
 * - Fixed copy for null GENERAL data
 * - Display source/date info from SSOT
 * - NO UI calculations
 */

'use client';

export interface Q1PremiumRow {
  rank: number;
  insurer_code: string;
  insurer_name: string;
  product_name?: string;
  premium_monthly: number;
  premium_total: number;
  premium_monthly_general?: number | null;
  premium_total_general?: number | null;
}

interface Q1EvidenceRailProps {
  selectedRow: Q1PremiumRow | null;
  onClose: () => void;
}

function formatPremium(value: number | null | undefined): string {
  if (value == null) return '—';
  return value.toLocaleString('ko-KR') + '원';
}

export function Q1EvidenceRail({ selectedRow, onClose }: Q1EvidenceRailProps) {
  // Hide panel if no row selected
  if (!selectedRow) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-300 shadow-xl overflow-y-auto z-50">
      {/* Header */}
      <div className="sticky top-0 bg-blue-600 text-white px-6 py-4 border-b border-blue-700">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-700 text-white text-sm font-bold">
                {selectedRow.rank}
              </span>
              <h2 className="text-lg font-bold">{selectedRow.insurer_name}</h2>
            </div>
            {selectedRow.product_name && (
              <p className="text-sm text-blue-100 line-clamp-2">
                {selectedRow.product_name}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-2 text-white hover:text-blue-200 transition-colors"
            aria-label="Close evidence rail"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-6 space-y-6">
        {/* Section 1: 기준 보험료 (NO_REFUND) */}
        <section className="space-y-3">
          <h3 className="text-base font-bold text-gray-900 border-b-2 border-blue-500 pb-2">
            1. 기준 보험료
          </h3>
          <div className="bg-blue-50 rounded-lg p-4 space-y-2">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">기준:</span> 무해지형(NO_REFUND)
            </p>
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="bg-white rounded p-3 border border-blue-200">
                <p className="text-xs text-gray-600 mb-1">월납보험료</p>
                <p className="text-base font-bold text-gray-900">
                  {formatPremium(selectedRow.premium_monthly)}
                </p>
              </div>
              <div className="bg-white rounded p-3 border border-blue-200">
                <p className="text-xs text-gray-600 mb-1">총납입보험료</p>
                <p className="text-base font-bold text-gray-900">
                  {formatPremium(selectedRow.premium_total)}
                </p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-blue-200">
              <p className="text-xs text-gray-600">
                <span className="font-semibold">출처:</span> SSOT DB (coverage_premium_quote)
              </p>
              <p className="text-xs text-gray-600 mt-1">
                <span className="font-semibold">기준일:</span> 2025-11-26
              </p>
            </div>
          </div>
        </section>

        {/* Section 2: 일반형 보험료 (GENERAL) */}
        <section className="space-y-3">
          <h3 className="text-base font-bold text-gray-900 border-b-2 border-blue-500 pb-2">
            2. 일반형 보험료
          </h3>
          {selectedRow.premium_monthly_general == null ? (
            // Fixed copy for null GENERAL data
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <p className="text-base font-semibold text-gray-900">데이터 없음</p>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3 space-y-2">
                <p className="text-sm text-gray-700">
                  <span className="font-semibold">사유:</span> 해당 기준일(as_of_date)에는
                  담보별 일반형(GENERAL) 보험료가 SSOT에 적재되지 않았습니다.
                </p>
                <p className="text-sm text-gray-700">
                  <span className="font-semibold">안내:</span> 일반형 산출식/배수/퍼센트 정보는
                  결과 테이블에 표시하지 않으며, 필요 시 별도 근거 레일에서만 제공합니다.
                </p>
              </div>
            </div>
          ) : (
            // Show GENERAL data if available
            <div className="bg-green-50 rounded-lg p-4 space-y-2">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">기준:</span> 일반형(GENERAL)
              </p>
              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="bg-white rounded p-3 border border-green-200">
                  <p className="text-xs text-gray-600 mb-1">월납보험료</p>
                  <p className="text-base font-bold text-gray-900">
                    {formatPremium(selectedRow.premium_monthly_general)}
                  </p>
                </div>
                <div className="bg-white rounded p-3 border border-green-200">
                  <p className="text-xs text-gray-600 mb-1">총납입보험료</p>
                  <p className="text-base font-bold text-gray-900">
                    {formatPremium(selectedRow.premium_total_general)}
                  </p>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-green-200">
                <p className="text-xs text-gray-600">
                  <span className="font-semibold">출처:</span> SSOT DB (coverage_premium_quote)
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  <span className="font-semibold">기준일:</span> 2025-11-26
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Section 3: 산출 원칙 */}
        <section className="space-y-3">
          <h3 className="text-base font-bold text-gray-900 border-b-2 border-blue-500 pb-2">
            3. 산출 원칙
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>모든 보험료 값은 SSOT DB 결과를 그대로 표시합니다.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>UI에서 계산/추정/보정하지 않습니다.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>
                  공식/배수/퍼센트는 결과 테이블에 표시하지 않습니다(근거 레일 전용).
                </span>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
