"use client";

import { AssistantMessageVM, Section } from "@/lib/types";
import { normalizeTableSection, debugLogTable } from "@/lib/normalize/table";
import PremiumCompareCard from "./cards/PremiumCompareCard";
import CoverageLimitCard from "./cards/CoverageLimitCard";
import TwoInsurerCompareCard from "./cards/TwoInsurerCompareCard";
import SubtypeEligibilityCard from "./cards/SubtypeEligibilityCard";
import { CoverageDiffCard } from "./cards/CoverageDiffCard";
import EvidenceToggle from "./cards/EvidenceToggle";
import UnsupportedCard from "./cards/UnsupportedCard";

interface ResultDockProps {
  response?: AssistantMessageVM;
}

export default function ResultDock({ response }: ResultDockProps) {
  if (!response) {
    return null;
  }

  // Defensive guards for array fields
  const sections = Array.isArray(response?.sections) ? response.sections : [];
  const summaryBullets = Array.isArray(response?.summary_bullets) ? response.summary_bullets : [];

  // Debug guard: Detect [object Object] in rendered output (dev mode only)
  const hasObjectObjectIssue =
    typeof window !== "undefined" &&
    process.env.NODE_ENV === "development" &&
    JSON.stringify(response).includes("[object Object]");

  const renderSection = (section: Section, idx: number) => {
    switch (section.kind) {
      case "coverage_diff_result":
        // STEP NEXT-COMPARE-FILTER: Diff result card
        return <CoverageDiffCard key={idx} section={section} />;

      case "comparison_table":
        // STEP NEXT-UI-02-FIX7: Normalize table data before rendering
        // This ensures all cells are strings and prevents [object Object]
        debugLogTable(section, `section_${idx}_${section.table_kind}`);
        const normalizedTable = normalizeTableSection(section);

        // Route based on table_kind (sections-first approach)
        // table_kind is the SSOT, not message.kind
        if (section.table_kind === "COVERAGE_DETAIL") {
          return <CoverageLimitCard key={idx} section={normalizedTable} />;
        } else if (section.table_kind === "INTEGRATED_COMPARE") {
          return <TwoInsurerCompareCard key={idx} section={normalizedTable} />;
        } else if (section.table_kind === "ELIGIBILITY_MATRIX") {
          return <SubtypeEligibilityCard key={idx} section={normalizedTable} />;
        } else if (section.table_kind === "PREMIUM_COMPARE") {
          return <PremiumCompareCard key={idx} section={normalizedTable} />;
        }

        // Fallback: Use CoverageLimitCard as default table renderer
        // This ensures ANY comparison_table will render even if table_kind is unknown
        return <CoverageLimitCard key={idx} section={normalizedTable} />;

      case "common_notes":
        return (
          <div key={idx} className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-800 mb-3">{section.title}</h3>
            {section.bullets && section.bullets.length > 0 && (
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {section.bullets.map((bullet, bIdx) => (
                  <li key={bIdx}>{bullet}</li>
                ))}
              </ul>
            )}
            {section.groups && section.groups.length > 0 && (
              <div className="space-y-3">
                {section.groups.map((group, gIdx) => {
                  const groupBullets = Array.isArray(group.bullets) ? group.bullets : [];
                  return (
                    <div key={gIdx}>
                      <h4 className="font-medium text-sm text-gray-700 mb-1">
                        {group.title}
                      </h4>
                      {groupBullets.length > 0 && (
                        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 ml-2">
                          {groupBullets.map((bullet, bIdx) => (
                            <li key={bIdx}>{bullet}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );

      case "evidence_accordion":
        return (
          <EvidenceToggle
            key={idx}
            items={section.items ?? []}
            defaultCollapsed={section.defaultCollapsed ?? true}
          />
        );

      default:
        return <UnsupportedCard key={idx} type={(section as any).kind || "unknown"} />;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      {/* Debug Warning: [object Object] detected */}
      {hasObjectObjectIssue && (
        <div className="border border-red-300 bg-red-50 rounded-lg p-3 mb-4">
          <div className="flex items-start gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">
                Renderer 미적용 가능성 감지
              </p>
              <p className="text-xs text-red-700 mt-1">
                테이블 셀에 [object Object]가 포함되어 있을 수 있습니다.
                renderCellValue()가 모든 셀에 적용되었는지 확인하세요.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Title */}
      <div className="border-b border-gray-200 pb-3">
        <h2 className="text-xl font-bold text-gray-800">{response.title ?? "결과"}</h2>
        {summaryBullets.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm text-gray-600">
            {summaryBullets.map((bullet, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Sections */}
      <div className="space-y-4">
        {sections.length > 0 ? (
          sections.map((section, idx) => renderSection(section, idx))
        ) : (
          <div className="border border-yellow-200 bg-yellow-50 rounded-lg p-4">
            <p className="text-sm font-medium text-yellow-800">
              ⚠️ 섹션 데이터가 없습니다
            </p>
            <div className="mt-2 text-xs text-yellow-700 space-y-1">
              <p>kind: <code className="bg-yellow-100 px-1 rounded">{response.kind || "undefined"}</code></p>
              <p>title: <code className="bg-yellow-100 px-1 rounded">{response.title || "undefined"}</code></p>
              <p>sections.length: <code className="bg-yellow-100 px-1 rounded">{sections.length}</code></p>
            </div>
            <details className="mt-3 text-xs text-yellow-700">
              <summary className="cursor-pointer hover:text-yellow-900 font-medium">
                전체 VM 구조 보기
              </summary>
              <pre className="mt-2 bg-yellow-100 p-2 rounded overflow-x-auto text-xs">
                {JSON.stringify(response, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>

      {/* Lineage (debug info) */}
      {response.lineage && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <details className="text-xs text-gray-500">
            <summary className="cursor-pointer hover:text-gray-700">
              처리 정보
            </summary>
            <div className="mt-2 bg-gray-50 p-2 rounded">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(response.lineage, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
