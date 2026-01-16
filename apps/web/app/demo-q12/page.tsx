/**
 * Q12 Report Page - Cancer Diagnosis Comparison
 *
 * Purpose: Display Q12 report (Premium + Coverage + Recommendation)
 * Scope: A4200_1 (암진단비 유사암제외)
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Q12ReportView } from '@/components/cards/Q12ReportView';

const INSURER_NAMES: Record<string, string> = {
  'N01': 'DB손해보험',
  'N02': '롯데손해보험',
  'N03': '메리츠화재',
  'N05': '삼성화재',
  'N08': '현대해상',
  'N09': '흥국화재',
  'N10': 'KB손해보험',
  'N13': '한화손해보험',
};

interface CompareV2Response {
  coverage_code: string;
  canonical_name: string;
  as_of_date: string;
  insurer_rows: any[];
  q12_report?: any;
}

export default function DemoQ12Page() {
  const [availableInsurers, setAvailableInsurers] = useState<string[]>([]);
  const [selectedInsurers, setSelectedInsurers] = useState<string[]>([]);
  const [data, setData] = useState<CompareV2Response | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const coverageCode = 'A4200_1';
  const asOfDate = '2025-11-26';

  // Load available insurers on mount
  useEffect(() => {
    async function fetchAvailableInsurers() {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const url = `${API_BASE}/coverage_status?coverage_code=${coverageCode}&as_of_date=${asOfDate}`;

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`보험사 목록을 불러올 수 없습니다 (${response.status})`);
        }
        const json = await response.json();
        const insurers = json.available_insurers || [];
        setAvailableInsurers(insurers);
        setSelectedInsurers(insurers); // Default: select all
      } catch (err) {
        console.error('Coverage status fetch error:', err);
        setError(err instanceof Error ? err.message : '보험사 목록 로딩 오류');
      } finally {
        setLoadingStatus(false);
      }
    }

    fetchAvailableInsurers();
  }, []);

  // Fetch comparison data when selection changes
  useEffect(() => {
    if (selectedInsurers.length < 2) {
      return; // Don't fetch if less than 2 insurers selected
    }

    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const insCdsParam = selectedInsurers.join(',');
        const url = `${API_BASE}/compare_v2?coverage_code=${coverageCode}&as_of_date=${asOfDate}&ins_cds=${insCdsParam}`;

        const response = await fetch(url);
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          if (response.status === 404) {
            throw new Error(`선택하신 보험사 조합의 비교 데이터가 준비되지 않았습니다. 다른 조합을 선택해 주세요.`);
          } else {
            throw new Error(errorData.detail || `데이터를 불러올 수 없습니다 (${response.status})`);
          }
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Q12 fetch error:', err);
        setError(err instanceof Error ? err.message : '데이터 로딩 오류');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [selectedInsurers]);

  const handleInsurerToggle = (insurerCode: string) => {
    setSelectedInsurers(prev => {
      if (prev.includes(insurerCode)) {
        const newSelection = prev.filter(code => code !== insurerCode);
        // Prevent deselecting if it would leave less than 2
        return newSelection.length >= 2 ? newSelection : prev;
      } else {
        const newSelection = [...prev, insurerCode];
        // Prevent selecting more than 8
        return newSelection.length <= 8 ? newSelection : prev;
      }
    });
  };

  const handleSelectAll = () => {
    setSelectedInsurers(availableInsurers);
  };

  const handleDeselectAll = () => {
    // Keep only first 2 to maintain minimum requirement
    setSelectedInsurers(availableInsurers.slice(0, 2));
  };

  if (loadingStatus) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-600">보험사 목록을 불러오는 중...</div>
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
              <Link href="/" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
                ← 리포트 선택으로 돌아가기
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">
                암진단비 비교 리포트
              </h1>
              <p className="text-sm text-gray-600 mt-2">
                보험료·보장 조건·종합 판단 및 추천
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-semibold text-gray-700">
              비교할 보험사 선택 ({selectedInsurers.length}개 선택됨, 최소 2개 ~ 최대 8개)
            </label>
            <div className="flex gap-2">
              <button
                onClick={handleSelectAll}
                className="px-4 py-2 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-all"
              >
                전체 선택
              </button>
              <button
                onClick={handleDeselectAll}
                className="px-4 py-2 text-xs font-medium text-gray-600 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-all"
              >
                전체 해제
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-3">
            {availableInsurers.map((code) => (
              <label
                key={code}
                className={`flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-all ${
                  selectedInsurers.includes(code)
                    ? 'bg-blue-50 border-blue-300 shadow-sm'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedInsurers.includes(code)}
                  onChange={() => handleInsurerToggle(code)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  {INSURER_NAMES[code] || code}
                </span>
              </label>
            ))}
          </div>
          {selectedInsurers.length < 2 && (
            <p className="mt-2 text-xs text-red-600">
              ⚠️ 최소 2개 이상의 보험사를 선택해야 합니다.
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <div className="text-gray-600">데이터를 불러오는 중...</div>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="font-semibold text-red-800 mb-2">데이터를 불러올 수 없습니다</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : data?.q12_report ? (
          <Q12ReportView report={data.q12_report} />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-800 font-semibold">비교 데이터를 찾을 수 없습니다</p>
            <p className="text-sm text-yellow-700 mt-2">
              선택하신 조건의 비교 데이터가 준비되지 않았습니다. 다른 조합을 선택해 주세요.
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="text-xs text-gray-500 space-y-2">
            <p>
              <strong className="text-gray-700">안내:</strong> 모든 비교 내용은 약관 및 상품 설명서를 기반으로 합니다.
            </p>
            <p>
              근거가 명확하지 않은 경우 "정보 없음"으로 표시되며, 최종 가입 전에는 반드시 약관을 직접 확인하시기 바랍니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
