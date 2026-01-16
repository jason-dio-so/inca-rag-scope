"use client";

/**
 * STEP NEXT-75: KPI Badge Component
 * Displays payment type and limit summary
 */

interface KPIBadgeProps {
  paymentType: string;  // "LUMP_SUM" | "PER_DAY" | "PER_EVENT" | "REIMBURSEMENT" | "UNKNOWN"
  limitSummary?: string | null;
  kpiEvidenceRefs?: string[];
  onInfoClick?: () => void;
}

const PAYMENT_TYPE_LABELS: Record<string, string> = {
  'LUMP_SUM': '정액형',
  'PER_DAY': '일당형',
  'PER_EVENT': '건별',
  'REIMBURSEMENT': '실손',
  'UNKNOWN': '표현 없음',
};

export default function KPIBadge({
  paymentType,
  limitSummary,
  kpiEvidenceRefs,
  onInfoClick
}: KPIBadgeProps) {
  const paymentLabel = PAYMENT_TYPE_LABELS[paymentType] || paymentType;
  const hasRefs = kpiEvidenceRefs && kpiEvidenceRefs.length > 0;

  return (
    <div className="flex items-start gap-2 text-xs">
      <div className="flex-1 space-y-1">
        {/* Payment Type */}
        <div className="flex items-center gap-1">
          <span className="text-gray-500">지급유형:</span>
          <span
            className={`inline-block px-2 py-0.5 rounded ${
              paymentType === 'UNKNOWN'
                ? 'bg-gray-100 text-gray-500'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {paymentLabel}
          </span>
        </div>

        {/* Limit Summary */}
        <div className="flex items-center gap-1">
          <span className="text-gray-500">한도:</span>
          <span className="text-gray-700 truncate">
            {limitSummary || '한도 표현 없음'}
          </span>
        </div>
      </div>

      {/* Info Icon */}
      {hasRefs && onInfoClick && (
        <button
          onClick={onInfoClick}
          className="text-blue-500 hover:text-blue-700 flex-shrink-0 mt-0.5"
          title="KPI 근거 보기"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </div>
  );
}
