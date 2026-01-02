/**
 * STEP NEXT-76: KPI Condition Badge
 *
 * 조건 KPI 표시 (면책/감액/대기기간/갱신)
 * - 존재하는 조건만 badge로 표시
 * - 순서 고정: 면책 > 대기기간 > 감액 > 갱신
 * - ⓘ 아이콘 클릭 시 근거 modal 표시
 */

export interface KPICondition {
  waiting_period?: string | null;
  reduction_condition?: string | null;
  exclusion_condition?: string | null;
  renewal_condition?: string | null;
  condition_evidence_refs?: string[];
  extraction_notes?: string;
}

interface KPIConditionBadgeProps {
  kpiCondition: KPICondition | null;
  onEvidenceClick?: (refs: string[]) => void;
}

export function KPIConditionBadge({
  kpiCondition,
  onEvidenceClick,
}: KPIConditionBadgeProps) {
  if (!kpiCondition) {
    return (
      <div className="text-sm text-gray-500">
        조건 특이사항 없음
      </div>
    );
  }

  const {
    waiting_period,
    reduction_condition,
    exclusion_condition,
    renewal_condition,
    condition_evidence_refs = [],
  } = kpiCondition;

  // 조건이 하나도 없으면 "특이사항 없음" 표시
  const hasAnyCondition =
    waiting_period || reduction_condition || exclusion_condition || renewal_condition;

  if (!hasAnyCondition) {
    return (
      <div className="text-sm text-gray-500">
        조건 특이사항 없음
      </div>
    );
  }

  // 조건 배지 구성 (순서 고정)
  const conditions = [
    {
      label: "면책",
      value: exclusion_condition,
      className: "bg-red-100 text-red-800 border-red-300"
    },
    {
      label: "대기기간",
      value: waiting_period,
      className: "bg-blue-100 text-blue-800 border-blue-300"
    },
    {
      label: "감액",
      value: reduction_condition,
      className: "bg-amber-100 text-amber-800 border-amber-300"
    },
    {
      label: "갱신",
      value: renewal_condition,
      className: "bg-gray-100 text-gray-800 border-gray-300"
    },
  ].filter((c) => c.value);

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {conditions.map((condition, idx) => (
        <span
          key={idx}
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${condition.className}`}
        >
          {condition.label}: {condition.value}
        </span>
      ))}

      {/* Evidence refs 있으면 ⓘ 아이콘 표시 */}
      {condition_evidence_refs.length > 0 && onEvidenceClick && (
        <button
          onClick={() => onEvidenceClick(condition_evidence_refs)}
          className="text-gray-500 hover:text-gray-700 transition-colors"
          title="근거 자료 확인"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
