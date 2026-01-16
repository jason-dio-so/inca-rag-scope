/**
 * Q13 Report Page - In-Situ / Borderline Tumor Coverage Matrix
 *
 * Purpose: Display Q13 matrix (제자리암/경계성종양 보장 여부)
 * Scope: Coverage O/X/- matrix only (no premium, no recommendation)
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Q13MatrixView } from '@/components/cards/Q13MatrixView';

const INSURER_CONFIGS = [
  { id: '2-insurer', label: '2개 보험사', codes: ['N01', 'N08'] },
  { id: '4-insurer', label: '4개 보험사', codes: ['N01', 'N02', 'N08', 'N10'] },
  { id: '8-insurer', label: '8개 보험사 (전체)', codes: ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'] },
];

const INSURER_NAMES: Record<string, string> = {
  N01: '삼성화재',
  N02: '현대해상',
  N03: 'DB손보',
  N05: '메리츠화재',
  N08: 'KB손해보험',
  N09: '한화손해보험',
  N10: '흥국화재',
  N13: '롯데손보',
};

interface CompareV2Response {
  coverage_code: string;
  canonical_name: string;
  as_of_date: string;
  insurer_rows: any[];
  q13_report?: any;
}

export default function Q13Page() {
  const [selectedConfig, setSelectedConfig] = useState(INSURER_CONFIGS[0]);
  const [data, setData] = useState<CompareV2Response | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const insCdsParam = selectedConfig.codes.join(',');
        const url = `${API_BASE}/compare_v2?coverage_code=A4200_1&as_of_date=2025-11-26&ins_cds=${insCdsParam}`;

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`데이터를 불러올 수 없습니다 (${response.status})`);
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Q13 fetch error:', err);
        setError(err instanceof Error ? err.message : '데이터 로딩 오류');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [selectedConfig]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <div className="text-gray-600">데이터를 불러오는 중...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="max-w-md mx-auto p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="font-semibold text-red-800 mb-2">데이터를 불러올 수 없습니다</p>
            <p className="text-sm text-red-600">{error}</p>
            <Link href="/" className="inline-block mt-4 text-sm text-purple-600 hover:text-purple-800">
              ← 메인으로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/" className="text-sm text-purple-600 hover:text-purple-800 mb-2 inline-block">
                ← 리포트 선택으로 돌아가기
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">
                제자리암/경계성종양 보장 여부 매트릭스
              </h1>
              <p className="text-sm text-gray-600 mt-2">
                제자리암·경계성종양 보장 여부 O / X / – 비교
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-purple-50 border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="text-sm text-purple-800">
              <p className="font-semibold mb-1">제자리암/경계성종양이란?</p>
              <p className="text-purple-700">
                제자리암(상피내암)과 경계성종양은 일반 암 진단비 대상이 아닌 초기 단계 병변입니다.
                보험사별로 보장 여부가 다를 수 있으니, 아래 표를 참고하여 확인하세요.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            비교할 보험사 수 선택
          </label>
          <div className="flex gap-3">
            {INSURER_CONFIGS.map((config) => (
              <button
                key={config.id}
                onClick={() => setSelectedConfig(config)}
                className={`px-6 py-3 text-sm font-medium border rounded-lg transition-all ${
                  selectedConfig.id === config.id
                    ? 'bg-purple-600 text-white border-purple-600 shadow-md'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'
                }`}
              >
                {config.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {data?.q13_report ? (
          <Q13MatrixView report={data.q13_report} insurerNames={INSURER_NAMES} />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-800 font-semibold">비교 데이터를 찾을 수 없습니다</p>
            <p className="text-sm text-yellow-700 mt-2">
              선택하신 조건의 비교 데이터가 준비되지 않았습니다. 다른 옵션을 선택해 주세요.
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="text-xs text-gray-500 space-y-2">
            <p>
              <strong className="text-gray-700">안내:</strong> 모든 보장 여부는 약관을 기반으로 판정합니다.
            </p>
            <p>
              <strong className="text-gray-700">범례:</strong> ✅ O = 보장, ❌ X = 제외, — = 정보 없음 (약관에서 명시 근거를 찾지 못함)
            </p>
            <p>
              최종 가입 전에는 반드시 약관을 직접 확인하시기 바랍니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
