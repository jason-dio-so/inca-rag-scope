/**
 * STEP NEXT-79-FE: Overall Evaluation Card
 *
 * EX4_ELIGIBILITY 전용 종합평가 섹션 렌더링
 *
 * DESIGN RULES:
 * 1. Decision badge (RECOMMEND/NOT_RECOMMEND/NEUTRAL)
 * 2. Summary sentence (1 line, factual)
 * 3. Reasons list with refs (lazy load on click)
 * 4. Fixed order (no reordering)
 *
 * FORBIDDEN:
 * - ❌ Scores, percentages, star ratings
 * - ❌ Emotional phrases ("좋습니다", "추천합니다")
 * - ❌ Mixing with other section types
 */

import React, { useState } from 'react';
import { OverallEvaluationSection, OverallDecision } from '@/lib/types';
import { Info } from 'lucide-react';

interface OverallEvaluationCardProps {
  section: OverallEvaluationSection;
}

const OverallEvaluationCard: React.FC<OverallEvaluationCardProps> = ({ section }) => {
  const { overall_evaluation } = section;
  const { decision, summary, reasons, notes } = overall_evaluation;

  // Decision badge styling (locked)
  const getDecisionBadgeStyle = (decision: OverallDecision): string => {
    switch (decision) {
      case 'RECOMMEND':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'NOT_RECOMMEND':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'NEUTRAL':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getDecisionLabel = (decision: OverallDecision): string => {
    switch (decision) {
      case 'RECOMMEND':
        return '추천';
      case 'NOT_RECOMMEND':
        return '비추천';
      case 'NEUTRAL':
        return '판단 유보';
      default:
        return '판단 유보';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-4">
      {/* Title */}
      <h3 className="text-lg font-semibold mb-4 text-gray-900">
        {section.title || '종합 평가'}
      </h3>

      {/* Decision Badge (Fixed at top) */}
      <div className="mb-4">
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getDecisionBadgeStyle(
            decision
          )}`}
        >
          {getDecisionLabel(decision)}
        </span>
      </div>

      {/* Summary (1 line, mandatory) */}
      <div className="mb-4">
        <p className="text-gray-800 font-medium">{summary}</p>
      </div>

      {/* Reasons List (with refs) */}
      {reasons && reasons.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">판단 근거</h4>
          <ul className="space-y-2">
            {reasons.map((reason, idx) => (
              <ReasonItem key={idx} reason={reason} />
            ))}
          </ul>
        </div>
      )}

      {/* Notes (fixed template) */}
      {notes && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">{notes}</p>
        </div>
      )}
    </div>
  );
};

interface ReasonItemProps {
  reason: {
    type: string;
    description: string;
    refs: string[];
  };
}

const ReasonItem: React.FC<ReasonItemProps> = ({ reason }) => {
  const [showRefs, setShowRefs] = useState(false);

  return (
    <li className="flex items-start space-x-2">
      <span className="text-gray-400 mt-1">•</span>
      <div className="flex-1">
        <div className="flex items-start space-x-2">
          <span className="text-gray-700">{reason.description}</span>
          {reason.refs && reason.refs.length > 0 && (
            <button
              onClick={() => setShowRefs(!showRefs)}
              className="text-blue-600 hover:text-blue-800 transition-colors"
              title="근거 자료 보기"
            >
              <Info className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Refs Accordion (reuses Step73R lazy load logic) */}
        {showRefs && reason.refs && reason.refs.length > 0 && (
          <div className="mt-2 ml-4 p-3 bg-gray-50 rounded border border-gray-200">
            <p className="text-xs font-semibold text-gray-600 mb-2">참조 문서</p>
            <ul className="space-y-1">
              {reason.refs.map((ref, refIdx) => (
                <li key={refIdx} className="text-xs text-gray-600">
                  {ref}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* No refs fallback */}
        {(!reason.refs || reason.refs.length === 0) && (
          <p className="text-xs text-gray-500 mt-1 ml-4">근거 문서 없음</p>
        )}
      </div>
    </li>
  );
};

export default OverallEvaluationCard;
