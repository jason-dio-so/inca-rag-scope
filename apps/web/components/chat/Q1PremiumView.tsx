/**
 * Q1 Premium Ranking View
 *
 * Evidence-Mandatory + Rail-Only Design
 * per STEP_NEXT_CHAT_UI_V2_SPEC.md Section 2a
 *
 * Fixed order: Header + Table + Note
 * Evidence Rail: Separate component (evidence is Rail-Only, not in main table)
 */

import type {
  Q1ViewModel,
  Q1PremiumRow,
  BasePremiumEvidence,
  RateMultiplierEvidence
} from '@/types/premium';
import { useState } from 'react';

interface Q1ViewProps {
  data: Q1ViewModel;
}

export function Q1PremiumView({ data }: Q1ViewProps) {
  const [selectedRow, setSelectedRow] = useState<Q1PremiumRow | null>(null);

  if (data.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="font-semibold text-red-800">{data.error}</p>
        {data.note && (
          <p className="text-sm text-red-600 mt-2">{data.note}</p>
        )}
      </div>
    );
  }

  // Helper: Format premium (won to 만원)
  const formatPremium = (won: number | null | undefined): string => {
    if (won === null || won === undefined) return '—';
    return `${Math.floor(won / 10000).toLocaleString()}만원`;
  };

  return (
    <div className="flex gap-6">
      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Header Block */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h2 className="text-lg font-bold text-gray-900">
            보험료 비교 (Top {data.query_params.top_n})
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            연령: {data.query_params.age}세 | 성별: {data.query_params.sex === 'M' ? '남' : '여'}
            {' | '}
            기준일: {data.query_params.as_of_date}
          </p>
        </div>

        {/* Comparison Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">순위</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">보험사</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">상품명</th>
                  {data.query_params.plan_variant !== 'GENERAL' && (
                    <>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">
                        무해지 월납
                      </th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">
                        무해지 총납
                      </th>
                    </>
                  )}
                  {data.query_params.plan_variant !== 'NO_REFUND' && (
                    <>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">
                        일반 월납
                      </th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">
                        일반 총납
                      </th>
                    </>
                  )}
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">
                    근거
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.rows.map((row, idx) => {
                  const isSelected = selectedRow?.product_id === row.product_id &&
                                    selectedRow?.ins_cd === row.ins_cd;

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-gray-50 cursor-pointer ${
                        isSelected ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedRow(row)}
                    >
                      <td className="px-4 py-3 text-gray-900 font-medium">{row.rank}</td>
                      <td className="px-4 py-3 text-gray-900 font-medium">
                        {row.insurer_name}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {row.product_name || '—'}
                      </td>
                      {data.query_params.plan_variant !== 'GENERAL' && (
                        <>
                          <td className="px-4 py-3 text-right text-gray-900">
                            {formatPremium(row.premium_monthly_no_refund)}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-900">
                            {formatPremium(row.premium_total_no_refund)}
                          </td>
                        </>
                      )}
                      {data.query_params.plan_variant !== 'NO_REFUND' && (
                        <>
                          <td className="px-4 py-3 text-right text-gray-900">
                            {formatPremium(row.premium_monthly_general)}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-900">
                            {formatPremium(row.premium_total_general)}
                          </td>
                        </>
                      )}
                      <td className="px-4 py-3 text-center">
                        <button
                          className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                          onClick={() => setSelectedRow(row)}
                        >
                          보기
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Guidance Notice (Rail-Only hint) */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-gray-700">
            <strong>안내:</strong> 일반 보험료는 무해지 기준 보험료와 요율표를 기반으로 산출되며,
            근거는 우측 Evidence에서 확인할 수 있습니다.
          </p>
        </div>

        {/* Note Block */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-600">
            <strong>안내:</strong> 모든 보험료는 DB 기준 (as_of_date: {data.query_params.as_of_date})입니다.
            "—"는 정보가 없음을 의미합니다. 최종 가입 전 약관을 직접 확인하시기 바랍니다.
          </p>
        </div>
      </div>

      {/* Evidence Rail (Right Side) */}
      {selectedRow && (
        <div className="w-96 space-y-4">
          <div className="sticky top-4">
            {/* Evidence Header */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <h3 className="text-md font-semibold text-gray-900">
                근거 (Evidence)
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {selectedRow.insurer_name} - {selectedRow.product_name || selectedRow.product_id}
              </p>
            </div>

            {/* Base Premium Evidence */}
            <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">
                1. Base Premium Evidence
              </h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Source Table:</span>
                  <span className="text-gray-600 ml-2">
                    {selectedRow.evidence.base_premium.source_table}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Conditions:</span>
                  <span className="text-gray-600 ml-2">
                    age={selectedRow.evidence.base_premium.age},
                    sex={selectedRow.evidence.base_premium.sex},
                    as_of_date={selectedRow.evidence.base_premium.as_of_date}
                  </span>
                </div>
                {selectedRow.evidence.base_premium.no_refund && (
                  <div className="mt-3 p-2 bg-gray-50 rounded">
                    <div className="font-medium text-gray-700 mb-1">NO_REFUND:</div>
                    <div className="text-xs text-gray-600">
                      월납: {formatPremium(selectedRow.evidence.base_premium.no_refund.premium_monthly)}
                      {' | '}
                      총납: {formatPremium(selectedRow.evidence.base_premium.no_refund.premium_total)}
                    </div>
                  </div>
                )}
                {selectedRow.evidence.base_premium.general && (
                  <div className="mt-2 p-2 bg-gray-50 rounded">
                    <div className="font-medium text-gray-700 mb-1">GENERAL:</div>
                    <div className="text-xs text-gray-600">
                      월납: {formatPremium(selectedRow.evidence.base_premium.general.premium_monthly)}
                      {' | '}
                      총납: {formatPremium(selectedRow.evidence.base_premium.general.premium_total)}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Rate Multiplier Evidence (GENERAL only) */}
            {selectedRow.evidence.rate_multiplier && (
              <div className="bg-white border border-orange-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">
                  2. Rate Multiplier Evidence
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Source Table:</span>
                    <span className="text-gray-600 ml-2">
                      {selectedRow.evidence.rate_multiplier.source_table}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Multiplier:</span>
                    <span className="text-gray-600 ml-2 font-mono">
                      {selectedRow.evidence.rate_multiplier.multiplier_percent}%
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Coverage:</span>
                    <span className="text-gray-600 ml-2 text-xs">
                      {selectedRow.evidence.rate_multiplier.coverage_code}
                    </span>
                  </div>
                  <div className="mt-3 p-2 bg-orange-50 rounded text-xs text-gray-600">
                    <strong>설명:</strong> 일반보험료 산출에 사용됨
                    <br />
                    계산식: 일반 = 무해지 × (multiplier / 100)
                  </div>
                </div>
              </div>
            )}

            {/* No Multiplier Warning (if GENERAL but no multiplier) */}
            {selectedRow.premium_monthly_general && !selectedRow.evidence.rate_multiplier && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  ⚠️ GENERAL variant이지만 multiplier evidence를 찾을 수 없습니다.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* No Selection Prompt (if no row selected) */}
      {!selectedRow && (
        <div className="w-96">
          <div className="sticky top-4 bg-gray-50 border border-gray-300 rounded-lg p-6 text-center">
            <p className="text-gray-600 text-sm">
              ← 좌측 테이블에서 행을 클릭하면
              <br />
              Evidence 근거를 확인할 수 있습니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
