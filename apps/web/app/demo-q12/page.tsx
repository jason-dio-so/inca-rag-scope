/**
 * Q12 Demo Page - Customer-Facing Report
 *
 * Purpose: Display Q12 report (Table + Summary + Recommendation)
 * Scope: A4200_1 (암진단비 유사암제외)
 * Mode: Report view (fallback to debug view if q12_report missing)
 */

'use client';

import { useState, useEffect } from 'react';
import { Q12ReportView } from '@/components/cards/Q12ReportView';

const INSURER_CONFIGS = [
  { id: '2-insurer', label: '2-insurer (N01, N08)', codes: ['N01', 'N08'] },
  { id: '4-insurer', label: '4-insurer (N01, N02, N08, N10)', codes: ['N01', 'N02', 'N08', 'N10'] },
  { id: '8-insurer', label: '8-insurer (All)', codes: ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'] },
];

interface CompareV2Response {
  coverage_code: string;
  canonical_name: string;
  as_of_date: string;
  insurer_rows: any[];
  q12_report?: any;
}

export default function DemoQ12Page() {
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
          throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Q12 fetch error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [selectedConfig]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-600">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600">
          <p className="font-semibold">오류 발생</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">
          Q12: 암진단비 비교 리포트
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          고객 요구 화면 (표 + 종합판단 + 최종추천)
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-700 mb-2">
            보험사 선택
          </label>
          <div className="flex gap-2">
            {INSURER_CONFIGS.map((config) => (
              <button
                key={config.id}
                onClick={() => setSelectedConfig(config)}
                className={`px-4 py-2 text-sm font-medium border rounded transition-colors ${
                  selectedConfig.id === config.id
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {config.label}
              </button>
            ))}
          </div>
        </div>

        <div className="text-xs text-gray-600">
          <strong>Current:</strong> {selectedConfig.label} |
          <strong className="ml-2">Insurers:</strong> {selectedConfig.codes.join(', ')} |
          <strong className="ml-2">Coverage:</strong> A4200_1 |
          <strong className="ml-2">q12_report:</strong> {data?.q12_report ? '✅ Available' : '❌ Missing'}
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          {data?.q12_report ? (
            <Q12ReportView report={data.q12_report} />
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <p className="text-yellow-800 font-semibold">q12_report 데이터가 없습니다</p>
              <p className="text-sm text-yellow-700 mt-2">
                build_q12_report_payload.py를 실행하여 q12_report를 생성하세요.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white px-6 py-3 text-xs">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <strong>Endpoint:</strong> GET /compare_v2
          </div>
          <div>
            <strong>Mode:</strong> 📊 Report (Customer)
          </div>
          <div>
            <strong>Source:</strong> compare_table_v2.payload.q12_report
          </div>
        </div>
      </div>
    </div>
  );
}
