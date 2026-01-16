/**
 * Q2 Limit Difference View
 *
 * Displays coverage limit comparison with differences highlighted
 * Format: Difference section + Common section + Comparison table
 */

interface Q2ViewProps {
  data: {
    coverage_code: string;
    canonical_name: string;
    insurer_rows: any[];
    error?: string;
    suggestions?: string[];
  };
}

export function Q2LimitDiffView({ data }: Q2ViewProps) {
  if (data.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="font-semibold text-red-800 mb-2">{data.error}</p>
        {data.suggestions && (
          <ul className="text-sm text-red-700 mt-3 space-y-1">
            {data.suggestions.map((s, i) => (
              <li key={i}>• {s}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  const INSURER_NAMES: Record<string, string> = {
    N01: 'DB손해보험',
    N02: '롯데손해보험',
    N03: '메리츠화재',
    N05: '삼성화재',
    N08: '현대해상',
    N09: '흥국화재',
    N10: 'KB손해보험',
    N13: '한화손해보험',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-lg font-bold text-gray-900">{data.canonical_name}</h2>
        <p className="text-sm text-gray-600 mt-1">
          담보코드: {data.coverage_code}
        </p>
      </div>

      {/* Comparison Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">순위</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">보험사</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">상품명</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">보장한도</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">일일보장금액</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.insurer_rows.map((row, idx) => {
                const insurerName = INSURER_NAMES[row.ins_cd] || row.ins_cd;
                const productName = row.product_name || '정보없음';

                // Extract duration_limit_days and daily_benefit_amount
                const slots = row.slots || {};
                const durationLimit = slots.duration_limit_days?.value || null;
                const dailyBenefit = slots.daily_benefit_amount_won?.value || null;

                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900 font-medium">{idx + 1}</td>
                    <td className="px-4 py-3 text-gray-900 font-medium">{insurerName}</td>
                    <td className="px-4 py-3 text-gray-700">{productName}</td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {durationLimit ? `${durationLimit}일` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {dailyBenefit ? `${dailyBenefit.toLocaleString()}원` : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Note */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-xs text-gray-600">
          <strong>안내:</strong> 모든 데이터는 약관 및 가입설계서를 기반으로 합니다.
          "—"는 정보가 없음을 의미합니다. 최종 가입 전 약관을 직접 확인하시기 바랍니다.
        </p>
      </div>
    </div>
  );
}
