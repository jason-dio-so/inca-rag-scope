/**
 * Q1PremiumTable - Premium Comparison Table
 *
 * Purpose: Display premium comparison table (top 4)
 * Rules:
 * - Show/hide columns based on product type filter
 * - Numbers only (NO formulas/percentages in main table)
 * - Row click opens detail panel (visual highlight only, NO text)
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

interface Q1PremiumTableProps {
  rows: Q1PremiumRow[];
  productType: 'all' | 'standard' | 'no_refund';
  age: number;
  gender: 'M' | 'F';
  onRowClick?: (row: Q1PremiumRow) => void;
  selectedRow?: Q1PremiumRow | null;
}

function formatPremium(value: number | null | undefined): string {
  if (value == null) return '—';
  return value.toLocaleString('ko-KR') + '원';
}

export function Q1PremiumTable({
  rows,
  productType,
  age,
  gender,
  onRowClick,
  selectedRow
}: Q1PremiumTableProps) {
  const showGeneral = productType === 'all' || productType === 'standard';
  const showNoRefund = productType === 'all' || productType === 'no_refund';

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-blue-50 border-b border-blue-100 px-6 py-4">
        <h2 className="text-lg font-bold text-gray-900">
          보험료 비교 (Top 4)
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          기준: {age}세 / {gender === 'M' ? '남성' : '여성'} / 20년납·100세만기
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b-2 border-gray-300">
            <tr>
              <th className="px-4 py-3 text-center text-sm font-bold text-gray-700 w-16">
                순위
              </th>
              <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 w-32">
                보험사
              </th>
              <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">
                상품명
              </th>
              {showNoRefund && (
                <>
                  <th className="px-4 py-3 text-right text-sm font-bold text-gray-700 w-40">
                    무해지<br />총납입보험료
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-bold text-gray-700 w-40">
                    무해지<br />월납보험료
                  </th>
                </>
              )}
              {showGeneral && (
                <>
                  <th className="px-4 py-3 text-right text-sm font-bold text-gray-700 w-40">
                    일반<br />총납입보험료
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-bold text-gray-700 w-40">
                    일반<br />월납보험료
                  </th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {rows.map((row) => {
              const isSelected = selectedRow?.rank === row.rank;
              return (
                <tr
                  key={row.rank}
                  onClick={() => onRowClick?.(row)}
                  className={`
                    cursor-pointer transition-all
                    ${isSelected
                      ? 'bg-blue-50 ring-2 ring-blue-500 ring-inset'
                      : 'hover:bg-gray-50'
                    }
                  `}
                >
                  <td className="px-4 py-3 text-center text-base font-bold text-gray-900">
                    {row.rank}
                  </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {row.insurer_name}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {row.product_name || '—'}
                </td>
                {showNoRefund && (
                  <>
                    <td className="px-4 py-3 text-right text-sm font-semibold text-gray-900">
                      {formatPremium(row.premium_total)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-700">
                      {formatPremium(row.premium_monthly)}
                    </td>
                  </>
                )}
                {showGeneral && (
                  <>
                    <td className="px-4 py-3 text-right text-sm font-semibold text-gray-900">
                      {formatPremium(row.premium_total_general)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-700">
                      {formatPremium(row.premium_monthly_general)}
                    </td>
                  </>
                )}
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Note */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
        <p className="text-xs text-gray-600">
          ※ 보험료는 DB 기준 (2025-11-26) / 행을 클릭하면 상세 정보를 확인할 수 있습니다
        </p>
      </div>
    </div>
  );
}
