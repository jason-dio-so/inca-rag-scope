/**
 * PHASE2 Q11: Cancer Hospitalization Comparison Card
 *
 * Query: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
 *
 * Displays:
 * - Daily benefit amount (일당)
 * - Duration limit days (보장일수)
 * - Evidence attribution
 *
 * Rules (IMMUTABLE):
 * - Sort: duration_limit_days DESC, daily_benefit_amount_won DESC, insurer_key ASC
 * - null values → "UNKNOWN (근거 부족)"
 * - Evidence: doc_type + page, with excerpt on hover
 */

'use client';

import { useState, useEffect } from 'react';

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

interface Q11Item {
  rank: number;
  insurer_key: string;
  coverage_name: string;
  daily_benefit_amount_won: number | null;
  duration_limit_days: number | null;
  evidence: {
    doc_type: string;
    page: number;
    excerpt: string;
  } | null;
}

interface Q11Response {
  query_id: string;
  as_of_date: string;
  items: Q11Item[];
}

export function Q11CancerHospitalizationCard() {
  const [data, setData] = useState<Q11Response | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch('http://127.0.0.1:8000/q11?as_of_date=2025-11-26');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Q11 fetch error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-red-600">
          <p className="font-semibold">Q11 로드 실패</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-500">데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-blue-50 border-b border-blue-100 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">
          질문: 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘
        </h3>
        <p className="text-sm text-gray-600">
          기준: 일당 금액과 최대 보장일수로 비교합니다.
        </p>
        <p className="text-xs text-gray-500 mt-1">
          데이터 기준일: {data.as_of_date}
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[10%]">
                순위
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[15%]">
                보험사
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[20%]">
                담보명
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[20%]">
                일당
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[20%]">
                보장일수
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[15%]">
                근거
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.items.map((item) => (
              <tr key={`${item.insurer_key}-${item.rank}`} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">{item.rank}</td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {getInsurerDisplay(item.insurer_key)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.coverage_name}</td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {item.daily_benefit_amount_won !== null
                    ? `${item.daily_benefit_amount_won.toLocaleString()}원/일`
                    : <span className="text-orange-600">UNKNOWN (근거 부족)</span>}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {item.duration_limit_days !== null
                    ? `최대 ${item.duration_limit_days}일`
                    : <span className="text-orange-600">UNKNOWN (근거 부족)</span>}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {item.evidence ? (
                    <div className="group relative">
                      <span className="cursor-help border-b border-dotted border-gray-400">
                        {item.evidence.doc_type} p.{item.evidence.page}
                      </span>
                      {/* Hover tooltip */}
                      {item.evidence.excerpt && (
                        <div className="absolute z-10 invisible group-hover:visible bg-gray-800 text-white text-xs rounded p-2 w-64 -left-2 top-6 shadow-lg">
                          <div className="max-h-32 overflow-y-auto whitespace-pre-wrap">
                            {item.evidence.excerpt}
                          </div>
                          <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-800 transform rotate-45"></div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer note */}
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <p className="text-xs text-gray-600">
          ⚠️ UNKNOWN 표기: 해당 슬롯에 대한 명확한 근거를 찾지 못한 경우입니다.
        </p>
        <p className="text-xs text-gray-600 mt-1">
          ℹ️ 정렬: 보장일수(DESC) → 일당 금액(DESC) → 보험사명(ASC) 순으로 정렬됩니다.
        </p>
      </div>
    </div>
  );
}
