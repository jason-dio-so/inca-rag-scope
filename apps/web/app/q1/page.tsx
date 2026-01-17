/**
 * Q1 Page - 보험료 비교
 *
 * Purpose: Compare insurance premiums by age, gender, payment conditions
 * Rules:
 * - NO preset buttons (2/4/8)
 * - NO insurer selection UI
 * - All insurers (8) used by default
 * - Chat interface with deterministic slot parsing
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Q1PremiumTable } from '@/components/q1/Q1PremiumTable';
import { Q1ChatPanel, ChatMessage } from '@/components/q1/Q1ChatPanel';
import {
  Q1Slots,
  parseSlots,
  areSlotsComplete,
  generateClarificationPrompt,
} from '@/lib/q1/slotParser';

// All insurers (SSOT eligible list)
const ALL_INSURERS = ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'];

interface CoverageCandidate {
  coverage_code: string;
  canonical_name: string;
  score: number;
  match_reason: string;
}

export default function Q1Page() {
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [slots, setSlots] = useState<Q1Slots>({});

  // Form state (synced from slots)
  const [sortBy, setSortBy] = useState<'total' | 'monthly'>('total');
  const [productType, setProductType] = useState<'all' | 'standard' | 'no_refund'>('all');
  const [ageRange, setAgeRange] = useState<'30' | '40' | '50'>('40');
  const [gender, setGender] = useState<'M' | 'F'>('M');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Candidate selection state
  const [pendingCandidates, setPendingCandidates] = useState<CoverageCandidate[]>([]);
  const [pendingSlots, setPendingSlots] = useState<Q1Slots | null>(null);

  // Result state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Execute BY_COVERAGE query
  const executeCoverageRanking = async (querySlots: Q1Slots & { selected_coverage_codes: string[] }) => {
    setLoading(true);
    setError(null);

    try {
      // Hardcoded to Next.js server (not backend)
      const response = await fetch('http://localhost:3000/api/q1/coverage_ranking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ins_cds: ALL_INSURERS,
          age: querySlots.age_band || parseInt(ageRange),
          gender: querySlots.sex || gender,
          sort_by: querySlots.sort_by || sortBy,
          plan_variant_scope: querySlots.plan_variant_scope || productType,
          coverage_codes: querySlots.selected_coverage_codes,
          as_of_date: '2025-11-26'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Q1 BY_COVERAGE result:', data);
        setResult(data);

        // Add success message to chat
        const coverage_label = data.viewModel?.coverage_labels?.[0]?.canonical_name || querySlots.selected_coverage_codes[0];
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `담보별 비교 결과를 생성했습니다.\n기준: ${coverage_label}\n아래 표를 확인하세요.`,
          timestamp: new Date(),
        }]);
      } else {
        const errorText = await response.text();
        setError(`서버 오류: ${response.status}`);
        console.error('Q1 coverage_ranking failed:', response.status, errorText);
      }
    } catch (err) {
      console.error('Q1 coverage_ranking error:', err);
      setError('요청 처리 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Execute query (called from both chat and form)
  const executeQuery = async (querySlots: Q1Slots) => {
    setLoading(true);
    setError(null);

    try {
      // Hardcoded to Next.js server (not backend)
      const response = await fetch('http://localhost:3000/api/chat_query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query_text: '가장 저렴한 보험료 순서대로 4개만 비교해줘',
          ins_cds: ALL_INSURERS,
          filters: {
            sort_by: querySlots.sort_by || sortBy,
            product_type: querySlots.plan_variant_scope || productType,
            age: querySlots.age_band || parseInt(ageRange),
            gender: querySlots.sex || gender,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Q1 result:', data);
        setResult(data);

        // Add success message to chat
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '비교 결과를 생성했습니다. 아래 표를 확인하세요.',
          timestamp: new Date(),
        }]);
      } else {
        const errorText = await response.text();
        setError(`서버 오류: ${response.status}`);
        console.error('Q1 query failed:', response.status, errorText);
      }
    } catch (err) {
      console.error('Q1 query error:', err);
      setError('요청 처리 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Handle chat message
  const handleSendMessage = async (text: string) => {
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: text,
      timestamp: new Date(),
    }]);

    // Check if we're waiting for candidate selection
    if (pendingCandidates.length > 0 && pendingSlots) {
      const choice = text.trim();
      const choiceNum = parseInt(choice);

      if (choiceNum >= 1 && choiceNum <= pendingCandidates.length) {
        const selected = pendingCandidates[choiceNum - 1];

        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `"${selected.canonical_name}" (${selected.coverage_code})로 비교합니다.`,
          timestamp: new Date(),
        }]);

        // Clear pending state
        setPendingCandidates([]);
        const slotsToUse = pendingSlots;
        setPendingSlots(null);

        // Execute ranking with selected coverage code
        await executeCoverageRanking({
          ...slotsToUse,
          selected_coverage_codes: [selected.coverage_code]
        });
        return;
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `유효한 번호를 입력해 주세요 (1~${pendingCandidates.length})`,
          timestamp: new Date(),
        }]);
        return;
      }
    }

    // Parse slots
    const newSlots = parseSlots(text, slots);
    setSlots(newSlots);

    // Sync slots → form state
    if (newSlots.sex) setGender(newSlots.sex);
    if (newSlots.age_band) setAgeRange(String(newSlots.age_band) as '30' | '40' | '50');
    if (newSlots.sort_by) setSortBy(newSlots.sort_by);
    if (newSlots.plan_variant_scope) setProductType(newSlots.plan_variant_scope);

    // Check completeness
    if (!areSlotsComplete(newSlots)) {
      const prompt = generateClarificationPrompt(newSlots);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: prompt,
        timestamp: new Date(),
      }]);
      return;
    }

    // Handle BY_COVERAGE mode
    if (newSlots.premium_mode === 'BY_COVERAGE') {
      if (!newSlots.coverage_query_text) {
        // Need coverage input
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '어떤 담보 기준으로 볼까요?\n예) 암진단비, 뇌졸중진단비\n또는 담보코드 직접 입력 (예: A4200_1)',
          timestamp: new Date(),
        }]);
        return;
      }

      const query_text = newSlots.coverage_query_text.trim();

      // Check if it's a direct coverage_code (starts with A followed by digits)
      if (/^A\d+/.test(query_text)) {
        // Treat as coverage_code directly
        await executeCoverageRanking({
          ...newSlots,
          selected_coverage_codes: [query_text]
        });
        return;
      }

      // Free text: resolve to candidates
      try {
        setLoading(true);
        // Hardcoded to Next.js server (not backend)
        const response = await fetch('http://localhost:3000/api/q1/coverage_candidates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query_text: query_text,
            max_candidates: 3
          }),
        });

        if (response.ok) {
          const data = await response.json();
          const candidates: CoverageCandidate[] = data.candidates || [];

          if (candidates.length === 0) {
            // No matches
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `"${query_text}"에 해당하는 담보를 찾지 못했습니다.\n다른 담보명을 입력하거나 담보코드를 직접 입력해 주세요.\n예) 암진단비, A4200_1`,
              timestamp: new Date(),
            }]);
            setLoading(false);
            return;
          }

          if (candidates.length === 1) {
            // Auto-select single candidate
            const candidate = candidates[0];
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `"${candidate.canonical_name}" (${candidate.coverage_code})로 비교합니다.`,
              timestamp: new Date(),
            }]);
            setLoading(false);

            await executeCoverageRanking({
              ...newSlots,
              selected_coverage_codes: [candidate.coverage_code]
            });
            return;
          }

          // Multiple candidates: show selection UI
          setPendingCandidates(candidates);
          setPendingSlots(newSlots);

          const options = candidates.map((c, i) =>
            `${i + 1}) ${c.canonical_name} (${c.coverage_code})`
          ).join('\n');

          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `다음 중 선택해 주세요:\n${options}\n\n번호를 입력하세요 (1, 2, 3)`,
            timestamp: new Date(),
          }]);
          setLoading(false);
          return;

        } else {
          throw new Error(`Backend error: ${response.status}`);
        }
      } catch (err) {
        console.error('Coverage candidates error:', err);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '담보 검색 중 오류가 발생했습니다. 다시 시도해 주세요.',
          timestamp: new Date(),
        }]);
        setLoading(false);
        return;
      }
    }

    // Execute TOTAL mode
    await executeQuery(newSlots);
  };

  // Handle form submit
  const handleFormSubmit = async () => {
    await executeQuery({
      sex: gender,
      age_band: parseInt(ageRange) as 30 | 40 | 50,
      sort_by: sortBy,
      plan_variant_scope: productType,
      premium_mode: 'TOTAL',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <Link href="/" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
            ← 메인으로
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Q1 보험료 비교
          </h1>
          <p className="text-sm text-gray-600 mt-2">
            같은 기준에서 보험사별 보험료를 저렴한 순으로 비교합니다
          </p>
        </div>
      </div>

      {/* Main Content: Chat + Controls */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chat Panel */}
          <div className="h-[600px]">
            <Q1ChatPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              loading={loading}
              disabled={loading}
            />
          </div>

          {/* Advanced Controls (Collapsible) */}
          <div>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
              >
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    고급 옵션
                  </h2>
                  <p className="text-xs text-gray-600 mt-1">
                    수동으로 조건을 설정하고 비교
                  </p>
                </div>
                <span className="text-gray-400">
                  {showAdvanced ? '▲' : '▼'}
                </span>
              </button>

              {showAdvanced && (
                <div className="p-6 border-t border-gray-200">
                  <div className="grid grid-cols-1 gap-4">
                    {/* Sort By */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        정렬 기준
                      </label>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setSortBy('total')}
                          className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                            sortBy === 'total'
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          총납입
                        </button>
                        <button
                          onClick={() => setSortBy('monthly')}
                          className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                            sortBy === 'monthly'
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          월납
                        </button>
                      </div>
                    </div>

                    {/* Product Type */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        보험 종류
                      </label>
                      <select
                        value={productType}
                        onChange={(e) => setProductType(e.target.value as any)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">전체비교</option>
                        <option value="standard">일반만</option>
                        <option value="no_refund">무해지만</option>
                      </select>
                    </div>

                    {/* Age Range */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        연령대
                      </label>
                      <div className="flex gap-2">
                        {(['30', '40', '50'] as const).map((age) => (
                          <button
                            key={age}
                            onClick={() => setAgeRange(age)}
                            className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                              ageRange === age
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {age}대
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Gender */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        성별
                      </label>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setGender('M')}
                          className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                            gender === 'M'
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          남성
                        </button>
                        <button
                          onClick={() => setGender('F')}
                          className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                            gender === 'F'
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          여성
                        </button>
                      </div>
                    </div>

                    {/* Execute Button */}
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm text-gray-600 mb-3">
                        비교 대상: 전체 보험사 (8개) | {ageRange}세 / {gender === 'M' ? '남성' : '여성'}
                      </p>
                      <button
                        onClick={handleFormSubmit}
                        disabled={loading}
                        className="w-full px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        {loading ? '처리 중...' : '비교 생성'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Slot Status Display */}
            <div className="mt-4 bg-gray-50 rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                현재 설정
              </h3>
              <div className="text-xs text-gray-600 space-y-1">
                <p>• 성별: {slots.sex ? (slots.sex === 'M' ? '남성' : '여성') : '미설정'}</p>
                <p>• 연령대: {slots.age_band ? `${slots.age_band}대` : '미설정'}</p>
                <p>• 비교 모드: {slots.premium_mode || '미설정'}</p>
                {slots.sort_by && <p>• 정렬: {slots.sort_by === 'total' ? '총납입' : '월납'}</p>}
                {slots.plan_variant_scope && <p>• 보험 종류: {slots.plan_variant_scope === 'all' ? '전체' : slots.plan_variant_scope === 'standard' ? '일반만' : '무해지만'}</p>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Result Area */}
      <div className="max-w-7xl mx-auto px-6 pb-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <p className="font-semibold text-red-800">{error}</p>
          </div>
        )}

        {!result ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <p className="text-gray-500">
              비교 조건을 설정하고 "비교 생성"을 클릭하세요
            </p>
          </div>
        ) : result.kind === 'Q1' && result.viewModel ? (
          <Q1PremiumTable
            rows={result.viewModel.rows || result.viewModel.top4 || []}
            productType={productType}
            age={parseInt(ageRange)}
            gender={gender}
          />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-800 font-semibold">
              예상치 못한 응답 형식입니다
            </p>
            <pre className="text-xs text-yellow-700 mt-2 p-3 bg-yellow-100 rounded overflow-x-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
