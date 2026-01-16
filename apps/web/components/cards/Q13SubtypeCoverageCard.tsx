/**
 * PHASE2 Q13: Subtype Coverage Matrix Card (LIMITED MODE)
 *
 * Query: "제자리암/경계성종양 보장 비교해줘 (O/X 매트릭스)"
 *
 * Displays:
 * - Matrix: insurers × subtypes (in_situ, borderline)
 * - Cell values: ✅ (O), ⚠️ (treatment_trigger), — (NO_DATA)
 * - Evidence attribution on hover
 *
 * Rules (IMMUTABLE):
 * - diagnosis_benefit → "O" (✅, green)
 * - treatment_trigger → "⚠️ 진단비 아님(치료비 트리거)" (orange)
 * - NO_DATA → "—" (gray, NOT excluded)
 * - NEVER show treatment_trigger as "O"
 *
 * Policy: docs/audit/STEP_NEXT_82_Q13_OUTPUT_LOCK.md
 * SSOT: docs/audit/step_next_81c_subtype_coverage_locked.jsonl
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

interface EvidenceRef {
  doc_type: string;
  page: string | number;
  excerpt: string;
  locator?: {
    keyword: string;
    line_num: number;
    is_table: boolean;
  };
}

interface SubtypeCell {
  status_icon: string;
  coverage_kind: string | null;
  usable_as_coverage: boolean;
  display: string;
  color: string;
  evidence_refs: EvidenceRef[];
  coverage_name?: string;
  coverage_type?: string;
  reason?: string;
}

interface MatrixRow {
  insurer_key: string;
  in_situ: SubtypeCell;
  borderline: SubtypeCell;
}

interface Q13Response {
  query_id: string;
  ssot_source: string;
  data_completeness: {
    insurers_with_data: number;
    n_total: number;
  };
  matrix: MatrixRow[];
}

export function Q13SubtypeCoverageCard() {
  const [data, setData] = useState<Q13Response | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch('http://127.0.0.1:8000/q13');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Q13 fetch error:', err);
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
          <p className="font-semibold">Q13 로드 실패</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || data.matrix.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-500">데이터가 없습니다.</p>
      </div>
    );
  }

  const { data_completeness } = data;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-purple-50 border-b border-purple-100 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">
          질문: 제자리암/경계성종양 보장 비교해줘 (O/X 매트릭스)
        </h3>
        <p className="text-sm text-gray-600">
          암 서브타입(제자리암, 경계성종양) 보장 여부를 보험사별로 비교합니다.
        </p>
        <p className="text-xs text-gray-500 mt-1">
          SSOT: {data.ssot_source} | 데이터 보유: {data_completeness.insurers_with_data}/{data_completeness.n_total}개사
        </p>
      </div>

      {/* Warning notice for LIMITED MODE */}
      <div className="bg-amber-50 border-b border-amber-200 p-3">
        <p className="text-sm text-amber-800">
          ※ 일부 보험사는 서브타입 SSOT가 없어 '—'로 표시됩니다(미보장(X) 의미 아님).
        </p>
        <p className="text-xs text-amber-700 mt-1">
          ⚠️ = 진단비가 아님(치료비 지급 트리거) / — = 데이터 없음
        </p>
      </div>

      {/* Matrix Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-[20%]">
                보험사
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-[40%]">
                제자리암 (in situ)
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-[40%]">
                경계성종양 (borderline)
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.matrix.map((row) => (
              <tr key={row.insurer_key} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {getInsurerDisplay(row.insurer_key)}
                </td>

                {/* in_situ cell */}
                <td className={`px-4 py-3 text-center text-sm ${
                  row.in_situ.color === 'green' ? 'bg-green-50' :
                  row.in_situ.color === 'orange' ? 'bg-orange-50' :
                  row.in_situ.color === 'red' ? 'bg-red-50' :
                  'bg-gray-50'
                }`}>
                  <div className="group relative inline-block">
                    <span className={`font-semibold ${
                      row.in_situ.color === 'green' ? 'text-green-700' :
                      row.in_situ.color === 'orange' ? 'text-orange-700' :
                      row.in_situ.color === 'red' ? 'text-red-700' :
                      'text-gray-500'
                    }`}>
                      {row.in_situ.status_icon} {row.in_situ.display === 'NO_DATA' ? '—' : row.in_situ.display}
                    </span>

                    {/* Hover tooltip with evidence */}
                    {row.in_situ.evidence_refs.length > 0 && (
                      <div className="absolute z-10 invisible group-hover:visible bg-gray-800 text-white text-xs rounded p-3 w-80 -left-2 top-8 shadow-lg">
                        <p className="font-semibold mb-1">담보: {row.in_situ.coverage_name}</p>
                        <p className="mb-2">타입: {row.in_situ.coverage_type}</p>
                        <p className="font-semibold mb-1">근거:</p>
                        <div className="max-h-32 overflow-y-auto whitespace-pre-wrap">
                          {row.in_situ.evidence_refs[0].doc_type} p.{row.in_situ.evidence_refs[0].page}
                          <br />
                          {row.in_situ.evidence_refs[0].excerpt.substring(0, 150)}...
                        </div>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-800 transform rotate-45"></div>
                      </div>
                    )}

                    {/* NO_DATA tooltip */}
                    {row.in_situ.display === 'NO_DATA' && row.in_situ.reason && (
                      <div className="absolute z-10 invisible group-hover:visible bg-gray-600 text-white text-xs rounded p-2 w-48 -left-2 top-8 shadow-lg">
                        {row.in_situ.reason}
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-600 transform rotate-45"></div>
                      </div>
                    )}
                  </div>
                </td>

                {/* borderline cell */}
                <td className={`px-4 py-3 text-center text-sm ${
                  row.borderline.color === 'green' ? 'bg-green-50' :
                  row.borderline.color === 'orange' ? 'bg-orange-50' :
                  row.borderline.color === 'red' ? 'bg-red-50' :
                  'bg-gray-50'
                }`}>
                  <div className="group relative inline-block">
                    <span className={`font-semibold ${
                      row.borderline.color === 'green' ? 'text-green-700' :
                      row.borderline.color === 'orange' ? 'text-orange-700' :
                      row.borderline.color === 'red' ? 'text-red-700' :
                      'text-gray-500'
                    }`}>
                      {row.borderline.status_icon} {row.borderline.display === 'NO_DATA' ? '—' : row.borderline.display}
                    </span>

                    {/* Hover tooltip with evidence */}
                    {row.borderline.evidence_refs.length > 0 && (
                      <div className="absolute z-10 invisible group-hover:visible bg-gray-800 text-white text-xs rounded p-3 w-80 -left-2 top-8 shadow-lg">
                        <p className="font-semibold mb-1">담보: {row.borderline.coverage_name}</p>
                        <p className="mb-2">타입: {row.borderline.coverage_type}</p>
                        <p className="font-semibold mb-1">근거:</p>
                        <div className="max-h-32 overflow-y-auto whitespace-pre-wrap">
                          {row.borderline.evidence_refs[0].doc_type} p.{row.borderline.evidence_refs[0].page}
                          <br />
                          {row.borderline.evidence_refs[0].excerpt.substring(0, 150)}...
                        </div>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-800 transform rotate-45"></div>
                      </div>
                    )}

                    {/* NO_DATA tooltip */}
                    {row.borderline.display === 'NO_DATA' && row.borderline.reason && (
                      <div className="absolute z-10 invisible group-hover:visible bg-gray-600 text-white text-xs rounded p-2 w-48 -left-2 top-8 shadow-lg">
                        {row.borderline.reason}
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-600 transform rotate-45"></div>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer note */}
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <p className="text-xs text-gray-600">
          ✅ 보장 O (diagnosis_benefit) | ⚠️ 진단비 아님(치료비 트리거) | ❌ 보장 X (excluded) | — 데이터 없음 (NOT excluded)
        </p>
        <p className="text-xs text-gray-600 mt-1">
          ℹ️ treatment_trigger는 진단비가 아니라 치료비 지급 조건입니다(usable_as_coverage=false).
        </p>
        <p className="text-xs text-gray-500 mt-2">
          Policy: STEP_NEXT_82_Q13_OUTPUT_LOCK.md (HARD LOCK)
        </p>
      </div>
    </div>
  );
}
