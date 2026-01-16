/**
 * Chat UI v2 - Unified Comparison Interface
 *
 * Features:
 * - Insurer multiselect with preset options
 * - Collapsible filter panel (sort, type, age, gender)
 * - Single query input
 * - 4 response types: Q1(Premium), Q2(Limit Diff), Q3(3-part), Q4(Matrix)
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Q2LimitDiffView } from '@/components/chat/Q2LimitDiffView';
import { Q3ThreePartView } from '@/components/chat/Q3ThreePartView';
import { Q4SupportMatrixView } from '@/components/chat/Q4SupportMatrixView';

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

const PRESET_CONFIGS = [
  { id: '2-insurer', label: '2개', codes: ['N01', 'N08'] },
  { id: '4-insurer', label: '4개', codes: ['N01', 'N02', 'N08', 'N10'] },
  { id: '8-insurer', label: '8개 (전체)', codes: ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'] },
];

export default function ChatPage() {
  const [availableInsurers, setAvailableInsurers] = useState<string[]>([]);
  const [selectedInsurers, setSelectedInsurers] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Filter states
  const [sortBy, setSortBy] = useState<'total' | 'monthly'>('total');
  const [productType, setProductType] = useState<'all' | 'standard' | 'no_refund'>('all');
  const [age, setAge] = useState<number>(40);
  const [gender, setGender] = useState<'M' | 'F'>('M');

  // Load available insurers (using A4200_1 as default for now)
  useEffect(() => {
    async function fetchInsurers() {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const response = await fetch(`${API_BASE}/coverage_status?coverage_code=A4200_1&as_of_date=2025-11-26`);
        if (response.ok) {
          const data = await response.json();
          const insurers = data.available_insurers || [];
          setAvailableInsurers(insurers);
          setSelectedInsurers(insurers); // Default: all
        }
      } catch (err) {
        console.error('Failed to load insurers:', err);
        setAvailableInsurers(PRESET_CONFIGS[2].codes);
        setSelectedInsurers(PRESET_CONFIGS[2].codes);
      }
    }
    fetchInsurers();
  }, []);

  const handleInsurerToggle = (code: string) => {
    setSelectedInsurers(prev => {
      if (prev.includes(code)) {
        const newSelection = prev.filter(c => c !== code);
        return newSelection.length >= 2 ? newSelection : prev;
      } else {
        const newSelection = [...prev, code];
        return newSelection.length <= 8 ? newSelection : prev;
      }
    });
  };

  const handlePresetSelect = (preset: typeof PRESET_CONFIGS[0]) => {
    setSelectedInsurers(preset.codes);
  };

  const handleSubmit = async () => {
    if (!query.trim() || selectedInsurers.length < 2) {
      return;
    }

    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:3000';
      const response = await fetch(`${API_BASE}/api/chat_query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query_text: query,
          ins_cds: selectedInsurers,
          filters: {
            sort_by: sortBy,
            product_type: productType,
            age,
            gender,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Result:', data);
        setResult(data);
      } else {
        console.error('Query failed:', response.status);
        setResult({
          kind: 'UNKNOWN',
          viewModel: { error: '서버 오류가 발생했습니다.' },
        });
      }
    } catch (err) {
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
                ← 메인으로
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">
                보험 비교 챗봇
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                질문을 입력하면 자동으로 적합한 형식의 비교표를 생성합니다
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Insurer Selection */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-semibold text-gray-700">
              비교할 보험사 ({selectedInsurers.length}개 선택)
            </label>
            <div className="flex gap-2">
              {PRESET_CONFIGS.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetSelect(preset)}
                  className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 border border-gray-200 rounded hover:bg-gray-200"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2">
            {availableInsurers.map(code => (
              <label
                key={code}
                className={`flex items-center gap-2 p-2 border rounded cursor-pointer text-xs ${
                  selectedInsurers.includes(code)
                    ? 'bg-blue-50 border-blue-300'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedInsurers.includes(code)}
                  onChange={() => handleInsurerToggle(code)}
                  className="w-3 h-3 text-blue-600 rounded"
                />
                <span className="font-medium text-gray-700">
                  {INSURER_NAMES[code] || code}
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Filter Panel (Collapsible) */}
      <div className="bg-gray-100 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            필터 옵션 {showFilters ? '숨기기' : '보기'}
          </button>

          {showFilters && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Sort By */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">정렬 기준</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'total' | 'monthly')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded"
                >
                  <option value="total">총납입보험료</option>
                  <option value="monthly">월납보험료</option>
                </select>
              </div>

              {/* Product Type */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">보험 종류</label>
                <select
                  value={productType}
                  onChange={(e) => setProductType(e.target.value as any)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded"
                >
                  <option value="all">전체</option>
                  <option value="standard">일반</option>
                  <option value="no_refund">무해지</option>
                </select>
              </div>

              {/* Age */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">연령</label>
                <input
                  type="number"
                  value={age}
                  onChange={(e) => setAge(parseInt(e.target.value))}
                  min={20}
                  max={80}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded"
                />
              </div>

              {/* Gender */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">성별</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value as 'M' | 'F')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded"
                >
                  <option value="M">남성</option>
                  <option value="F">여성</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Query Input */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            질문을 입력하세요
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
            rows={3}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="mt-4 flex items-center justify-between">
            <div className="text-xs text-gray-500">
              {selectedInsurers.length < 2 && (
                <span className="text-red-600">⚠️ 최소 2개 보험사를 선택하세요</span>
              )}
            </div>
            <button
              onClick={handleSubmit}
              disabled={!query.trim() || selectedInsurers.length < 2 || loading}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {loading ? '처리 중...' : '비교 생성'}
            </button>
          </div>
        </div>
      </div>

      {/* Result Area */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {!result ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm text-gray-500 text-center">
              질문을 입력하고 "비교 생성"을 클릭하세요
            </p>
          </div>
        ) : (
          <div>
            {/* Result Type Badge */}
            <div className="mb-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {result.kind === 'Q1' && '보험료 비교'}
                {result.kind === 'Q2' && '보장한도 차이 비교'}
                {result.kind === 'Q3' && '3파트 비교'}
                {result.kind === 'Q4' && '지원여부 매트릭스'}
                {result.kind === 'UNKNOWN' && '알 수 없는 질문'}
              </span>
            </div>

            {/* Render based on kind */}
            {result.kind === 'Q2' && <Q2LimitDiffView data={result.viewModel} />}
            {result.kind === 'Q3' && <Q3ThreePartView data={result.viewModel} />}
            {result.kind === 'Q4' && <Q4SupportMatrixView data={result.viewModel} />}
            {result.kind === 'Q1' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <p className="text-yellow-800">Q1 보험료 비교는 아직 구현 중입니다.</p>
              </div>
            )}
            {result.kind === 'UNKNOWN' && result.viewModel?.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <p className="font-semibold text-red-800 mb-2">{result.viewModel.error}</p>
                {result.viewModel.suggestions && (
                  <ul className="text-sm text-red-700 mt-3 space-y-1">
                    {result.viewModel.suggestions.map((s: string, i: number) => (
                      <li key={i}>• {s}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
