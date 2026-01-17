/**
 * Chat UI v2 - Unified Comparison Interface (Kiwoom-style Layout)
 *
 * Features:
 * - Overview Landing (onboarding with KPIs)
 * - Split Workspace (Chat + Context Panel)
 * - Filter panel (sort, type, age, gender)
 * - 4 response types: Q1(Premium), Q2(Limit Diff), Q3(3-part), Q4(Matrix)
 * - All insurers (8) compared by default
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Q1PremiumView } from '@/components/chat/Q1PremiumView';
import { Q2LimitDiffView } from '@/components/chat/Q2LimitDiffView';
import { Q3ThreePartView } from '@/components/chat/Q3ThreePartView';
import { Q4SupportMatrixView } from '@/components/chat/Q4SupportMatrixView';

// Default: 전체 보험사 (8개)
const ALL_INSURERS = ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'];

// KPI Data (hardcoded)
const KPI_DATA = {
  insurers: 8,
  database: 'inca_ssot',
  asOfDate: '2025-11-26',
  canonicalCoverages: 45,  // Example
};

type WorkspaceMode = 'overview' | 'workspace';
type ViewMode = 'split' | 'chat-only' | 'context-only';

export default function ChatPage() {
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>('overview');
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(true);
  const [result, setResult] = useState<any>(null);

  // RUNTIME GUARD: Prevent legacy UI from loading in /chat
  useEffect(() => {
    const bodyText = document.body.textContent || '';
    const forbiddenPatterns = [
      '보험 상품 비교 도우미',
      '옵션 숨기기',
      'LLM: OFF',
      'LLM: ON'
    ];

    for (const pattern of forbiddenPatterns) {
      if (bodyText.includes(pattern)) {
        throw new Error(`[UI Mixing Guard] Legacy UI element detected in /chat: "${pattern}"`);
      }
    }
  }, []);

  // Filter states
  const [sortBy, setSortBy] = useState<'total' | 'monthly'>('total');
  const [productType, setProductType] = useState<'all' | 'standard' | 'no_refund'>('all');
  const [age, setAge] = useState<number>(40);
  const [gender, setGender] = useState<'M' | 'F'>('M');

  const handleSubmit = async () => {
    if (!query.trim()) {
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
          ins_cds: ALL_INSURERS, // 전체 보험사 (8개)
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

        // ANTI-LEGACY GUARD: Prevent regression to legacy response structure
        if (data.kind === 'Q1') {
          // Q1 MUST use viewModel (Chat UI v2), NOT sections/title/summary
          if (!data.viewModel) {
            throw new Error('[Q1 Anti-Legacy Guard] Q1 response must have viewModel field');
          }
          if (data.sections || data.title || data.summary_bullets) {
            throw new Error('[Q1 Anti-Legacy Guard] Q1 must NOT have legacy fields (sections/title/summary)');
          }
        }

        setResult(data);
      } else {
        const errorText = await response.text();
        console.error('Query failed:', response.status, errorText);
        setResult({
          kind: 'UNKNOWN',
          viewModel: {
            error: `서버 오류가 발생했습니다 (${response.status})`,
            details: errorText.substring(0, 200)
          },
        });
      }
    } catch (err) {
      console.error('Query error:', err);
      setResult({
        kind: 'UNKNOWN',
        viewModel: {
          error: '요청 처리 중 오류가 발생했습니다.',
          details: err instanceof Error ? err.message : String(err)
        },
      });
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

      {/* Filter Panel */}
      <div className="bg-blue-50 border-b border-blue-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 text-sm font-semibold text-gray-900"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-90' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                비교 조건 설정
              </button>
              <p className="text-xs text-gray-600 mt-1 ml-6">
                보험료 비교 시 연령, 성별, 정렬 기준이 적용됩니다
              </p>
            </div>
          </div>

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
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            질문을 입력하세요
          </label>
          <p className="text-xs text-gray-500 mb-3">
            💡 보험료 비교: "저렴한 보험료 4개 추천" | 담보 비교: "암진단비 담보 비교" | 지원 여부: "제자리암 지원 여부"
          </p>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 저렴한 보험료 4개 상품만 추천해줘"
            rows={3}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="mt-4 flex items-center justify-between">
            <div className="text-xs text-gray-600">
              비교 조건: 전체 보험사 (8개) | {age}세 / {gender === 'M' ? '남성' : '여성'}
            </div>
            <button
              onClick={handleSubmit}
              disabled={!query.trim() || loading}
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
            {result.kind === 'Q1' && <Q1PremiumView data={result.viewModel} />}
            {result.kind === 'Q2' && <Q2LimitDiffView data={result.viewModel} />}
            {result.kind === 'Q3' && <Q3ThreePartView data={result.viewModel} />}
            {result.kind === 'Q4' && <Q4SupportMatrixView data={result.viewModel} />}
            {result.kind === 'UNKNOWN' && result.viewModel?.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <p className="font-semibold text-red-800 mb-2">{result.viewModel.error}</p>
                {result.viewModel.details && (
                  <pre className="text-xs text-red-700 mt-2 p-3 bg-red-100 rounded overflow-x-auto">
                    {result.viewModel.details}
                  </pre>
                )}
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
