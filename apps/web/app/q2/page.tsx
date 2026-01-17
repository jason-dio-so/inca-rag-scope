/**
 * Q2 Page - 보장한도 차이 비교 (Chat Mode)
 *
 * Purpose: Compare coverage limit differences across insurers via chat
 * Status: Chat-driven + Evidence Rail integrated
 * Rules:
 * - NO LLM, deterministic slot parsing
 * - Coverage candidates: 0/1/2~3 handling
 * - NO preset buttons
 * - Result/Evidence separation maintained
 */

'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { Q2LimitDiffView, Q2Row } from '@/components/chat/Q2LimitDiffView';
import { Q2EvidenceRail } from '@/components/q2/Q2EvidenceRail';
import { Q2ChatPanel, ChatMessage } from '@/components/q2/Q2ChatPanel';
import {
  parseSlots,
  areSlotsComplete,
  generateClarificationPrompt,
  Q2Slots
} from '@/lib/q2/slotParser';

type ChatState = 'collect_demographics' | 'collect_coverage_query' | 'selecting_candidate' | 'executing' | 'completed' | 'error';

interface CoverageCandidate {
  coverage_code: string;
  canonical_name: string;
  confidence?: number;
}

export default function Q2Page() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '연령과 성별을 함께 입력해주세요.\n예) 40대 남성, 50대 여성',
      timestamp: new Date()
    }
  ]);

  const [state, setState] = useState<ChatState>('collect_demographics');
  const [slots, setSlots] = useState<Q2Slots>({
    sort_by: 'monthly',
    plan_variant_scope: 'all'
  });

  const [pendingCoverageQuery, setPendingCoverageQuery] = useState<string | null>(null);

  const [candidates, setCandidates] = useState<CoverageCandidate[]>([]);
  const [selectedCoverageCode, setSelectedCoverageCode] = useState<string | null>(null);

  const [viewModel, setViewModel] = useState<any | null>(null);
  const [selectedRow, setSelectedRow] = useState<Q2Row | null>(null);

  const [loading, setLoading] = useState(false);

  const addMessage = useCallback((role: 'user' | 'assistant' | 'system', content: string) => {
    setMessages(prev => [...prev, { role, content, timestamp: new Date() }]);
  }, []);

  const fetchCoverageCandidates = useCallback(async (query: string): Promise<CoverageCandidate[]> => {
    try {
      // Empty query guard
      const qt = String(query ?? "").trim();
      if (!qt) {
        console.warn('[Q2] fetchCoverageCandidates: empty query_text, returning []');
        return [];
      }

      const body = { query_text: qt, max_candidates: 3 };
      console.log('[Q2] coverage_candidates request body =', body);

      const response = await fetch('/api/q2/coverage_candidates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        throw new Error(`Coverage candidates API error: ${response.status}`);
      }

      const data = await response.json();
      return data.candidates || [];
    } catch (error) {
      console.error('fetchCoverageCandidates error:', error);
      return [];
    }
  }, []);

  const executeQ2Compare = useCallback(async (coverageCode: string, ageBand: number, sex: string) => {
    try {
      // Guard: validate coverage_code
      if (!coverageCode || coverageCode.trim().length === 0) {
        addMessage('system', '비교할 담보를 선택해주세요.');
        setState('error');
        setLoading(false);
        return;
      }

      setState('executing');
      setLoading(true);

      // Fixed 8 insurers (no preset buttons)
      const insurers = ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'];

      const response = await fetch('/api/q2/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `보장한도 차이 비교`,            // Natural language query
          coverage_code: coverageCode,           // Single coverage_code
          age: ageBand,
          gender: sex,
          ins_cds: insurers,
          sort_by: 'monthly',
          plan_variant_scope: slots.plan_variant_scope || 'all',
          as_of_date: '2025-11-26'
        })
      });

      if (!response.ok) {
        throw new Error(`Q2 compare API error: ${response.status}`);
      }

      const data = await response.json();
      setViewModel(data);
      setState('completed');

      addMessage('assistant', `${data.canonical_name} 담보의 보장한도 차이를 확인했습니다. 아래 표를 확인해 주세요.`);
    } catch (error) {
      console.error('executeQ2Compare error:', error);
      setState('error');
      addMessage('system', `비교 실행 중 오류가 발생했습니다: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [slots.plan_variant_scope, addMessage]);

  const handleSendMessage = useCallback(async (message: string) => {
    addMessage('user', message);
    setLoading(true);

    try {
      // Parse slots from message
      const updatedSlots = parseSlots(message, slots);
      setSlots(updatedSlots);

      // State: Selecting candidate from number choice
      if (state === 'selecting_candidate') {
        const choiceMatch = message.match(/^(\d+)$/);
        if (choiceMatch) {
          const choiceNum = parseInt(choiceMatch[1], 10);
          if (choiceNum >= 1 && choiceNum <= candidates.length) {
            const selected = candidates[choiceNum - 1];
            setSelectedCoverageCode(selected.coverage_code);

            addMessage('assistant', `"${selected.canonical_name}" 담보로 비교를 시작합니다...`);

            // Execute Q2 compare
            await executeQ2Compare(selected.coverage_code, updatedSlots.age_band!, updatedSlots.sex!);
            return;
          } else {
            addMessage('system', `잘못된 번호입니다. 1~${candidates.length} 중 선택해 주세요.`);
            setLoading(false);
            return;
          }
        }
      }

      // State machine: demographics → coverage → execute

      // State: collect_demographics (age + sex together)
      if (state === 'collect_demographics') {
        // Check if coverage_query was provided (store as pending)
        if (updatedSlots.coverage_query && !pendingCoverageQuery) {
          setPendingCoverageQuery(updatedSlots.coverage_query);
        }

        const demographics_confirmed = Boolean(updatedSlots.age_band && updatedSlots.sex);

        if (!demographics_confirmed) {
          // Partial input handling - stay in collect_demographics state
          if (updatedSlots.age_band && !updatedSlots.sex) {
            addMessage('assistant', '연령은 확인되었습니다. 성별을 함께 입력해주세요.\n예) 40대 남성');
            setLoading(false);
            return;
          } else if (updatedSlots.sex && !updatedSlots.age_band) {
            addMessage('assistant', '성별은 확인되었습니다. 연령대를 함께 입력해주세요.\n예) 40대 남성');
            setLoading(false);
            return;
          } else {
            addMessage('assistant', '연령과 성별을 함께 입력해주세요.\n예) 40대 남성, 50대 여성');
            setLoading(false);
            return;
          }
        }

        // Demographics confirmed → Proceed to coverage
        if (pendingCoverageQuery || updatedSlots.coverage_query) {
          // Auto-proceed with pending or newly provided coverage
          const queryToUse = updatedSlots.coverage_query || pendingCoverageQuery!;

          setState('executing');
          const candidateList = await fetchCoverageCandidates(queryToUse);

          if (candidateList.length === 0) {
            addMessage('assistant', '해당 담보를 찾지 못했습니다. 담보명을 다시 입력해 주세요.\n예) 암진단비, 입원일당');
            setState('collect_coverage_query');
            setPendingCoverageQuery(null);
            setLoading(false);
            return;
          }

          if (candidateList.length === 1) {
            // Auto-select
            const selected = candidateList[0];
            setSelectedCoverageCode(selected.coverage_code);
            addMessage('assistant', `"${selected.canonical_name}" 담보로 비교를 시작합니다...`);

            await executeQ2Compare(selected.coverage_code, updatedSlots.age_band!, updatedSlots.sex!);
            return;
          }

          // 2~3 candidates → Ask user to choose
          setCandidates(candidateList);
          setState('selecting_candidate');

          let candidateMessage = '다음 중 어떤 담보를 비교할까요?\n\n';
          candidateList.forEach((c, idx) => {
            candidateMessage += `(${idx + 1}) ${c.canonical_name}\n`;
          });
          candidateMessage += '\n번호를 입력해 주세요.';

          addMessage('assistant', candidateMessage);
          setLoading(false);
          return;
        } else {
          // No coverage yet → Ask for coverage
          setState('collect_coverage_query');
          addMessage('assistant', '비교할 담보를 입력해 주세요.\n예) 암진단비, 암직접입원비, 뇌졸중진단비');
          setLoading(false);
          return;
        }
      }

      // State: collect_coverage_query
      if (state === 'collect_coverage_query') {
        if (updatedSlots.coverage_query) {
          // Coverage confirmed → Fetch candidates
          setState('executing');
          const candidateList = await fetchCoverageCandidates(updatedSlots.coverage_query);

          if (candidateList.length === 0) {
            addMessage('assistant', '해당 담보를 찾지 못했습니다. 다른 표현으로 다시 입력해 주세요.');
            setState('collect_coverage_query');
            setLoading(false);
            return;
          }

          if (candidateList.length === 1) {
            // Auto-select
            const selected = candidateList[0];
            setSelectedCoverageCode(selected.coverage_code);
            addMessage('assistant', `"${selected.canonical_name}" 담보로 비교를 시작합니다...`);

            await executeQ2Compare(selected.coverage_code, updatedSlots.age_band!, updatedSlots.sex!);
            return;
          }

          // 2~3 candidates → Ask user to choose
          setCandidates(candidateList);
          setState('selecting_candidate');

          let candidateMessage = '다음 중 어떤 담보를 비교할까요?\n\n';
          candidateList.forEach((c, idx) => {
            candidateMessage += `(${idx + 1}) ${c.canonical_name}\n`;
          });
          candidateMessage += '\n번호를 입력해 주세요.';

          addMessage('assistant', candidateMessage);
          setLoading(false);
          return;
        } else {
          // Coverage still missing
          addMessage('assistant', '비교할 담보를 입력해 주세요.\n예) 암진단비, 암직접입원비, 뇌졸중진단비');
          setLoading(false);
          return;
        }
      }

    } catch (error) {
      console.error('handleSendMessage error:', error);
      addMessage('system', `오류가 발생했습니다: ${error}`);
      setState('error');
    } finally {
      setLoading(false);
    }
  }, [state, slots, pendingCoverageQuery, candidates, addMessage, fetchCoverageCandidates, executeQ2Compare]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <Link href="/" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
            ← 메인으로
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Q2: 보장한도 차이 비교
          </h1>
          <p className="text-sm text-gray-600 mt-2">
            담보명, 연령대, 성별을 입력하여 보장한도를 비교하세요
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chat Panel */}
          <div className="h-[600px]">
            <Q2ChatPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              loading={loading}
              disabled={loading}
            />
          </div>

          {/* Result Panel */}
          <div>
            {viewModel ? (
              <Q2LimitDiffView
                data={viewModel}
                onRowClick={setSelectedRow}
                selectedRow={selectedRow}
              />
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-8 text-center h-full flex items-center justify-center">
                <div>
                  <p className="text-gray-500 text-sm mb-2">비교 결과가 여기에 표시됩니다</p>
                  <p className="text-gray-400 text-xs">
                    왼쪽 채팅창에서 담보명, 연령대, 성별을 입력하세요
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Evidence Rail */}
      {selectedRow && viewModel && (
        <Q2EvidenceRail
          selectedRow={selectedRow}
          coverageCode={viewModel.coverage_code}
          canonicalName={viewModel.canonical_name}
          onClose={() => setSelectedRow(null)}
        />
      )}
    </div>
  );
}
