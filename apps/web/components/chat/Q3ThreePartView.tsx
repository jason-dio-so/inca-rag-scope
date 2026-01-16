/**
 * Q3 Three-Part Comparison View
 *
 * Format:
 * 1. Comparison Table (with evidence)
 * 2. Overall Assessment (LLM-generated summary)
 * 3. Recommendation (LLM-generated winner + reasons)
 */

import { Q12ReportView } from '@/components/cards/Q12ReportView';

interface Q3ViewProps {
  data: {
    coverage_code?: string;
    canonical_name?: string;
    insurer_rows?: any[];
    overall_assessment?: string[] | null;
    recommendation?: {
      winner: string | null;
      reasons: string[];
    } | null;
    error?: string;
  };
}

export function Q3ThreePartView({ data }: Q3ViewProps) {
  if (data.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="font-semibold text-red-800">{data.error}</p>
      </div>
    );
  }

  // Check if this is q12_report format (has LLM-generated parts)
  const hasQ12Report = data.overall_assessment !== undefined || data.recommendation !== undefined;

  if (hasQ12Report) {
    // Use Q12ReportView for full 3-part rendering
    return <Q12ReportView report={data} />;
  }

  // Fallback: Table only (no LLM parts available)
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
        <h2 className="text-lg font-bold text-gray-900">{data.canonical_name || '비교 결과'}</h2>
        {data.coverage_code && (
          <p className="text-sm text-gray-600 mt-1">담보코드: {data.coverage_code}</p>
        )}
      </div>

      {/* Part 1: Comparison Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-md font-semibold text-gray-900">1. 비교표</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">보험사</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">상품명</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">보장금액</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.insurer_rows?.map((row, idx) => {
                const insurerName = INSURER_NAMES[row.ins_cd] || row.ins_cd;
                const productName = row.product_name || '정보없음';
                const slots = row.slots || {};

                // Try to extract amount from various slot types
                const amountSlot =
                  slots.diagnosis_benefit_amount ||
                  slots.benefit_amount_won ||
                  slots.coverage_amount ||
                  {};

                const amount = amountSlot.value;

                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900 font-medium">{insurerName}</td>
                    <td className="px-4 py-3 text-gray-700">{productName}</td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {amount ? `${amount.toLocaleString()}원` : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Part 2 & 3: Missing (LLM not available) */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <p className="text-sm font-semibold text-yellow-800 mb-2">
          ⚠️ 종합판단 및 추천은 현재 준비 중입니다
        </p>
        <p className="text-xs text-yellow-700">
          q12_report가 생성되지 않았습니다. build_q12_report_payload.py를 실행하여 LLM 기반 종합판단 및 추천을 생성하세요.
        </p>
      </div>

      {/* Note */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-xs text-gray-600">
          <strong>안내:</strong> 모든 데이터는 약관 및 가입설계서를 기반으로 합니다.
          최종 가입 전 약관을 직접 확인하시기 바랍니다.
        </p>
      </div>
    </div>
  );
}
