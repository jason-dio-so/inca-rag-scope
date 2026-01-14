"use client";

import React from "react";
import { NormalizedTable } from "@/lib/normalize/table";
import { getCellText, cellHasEvidence } from "@/lib/normalize/cellHelpers";
import EvidenceViewer from "@/components/EvidenceViewer";

interface CoverageLimitCardProps {
  section: NormalizedTable;
}

export default function CoverageLimitCard({
  section,
}: CoverageLimitCardProps) {
  // STEP NEXT-UI-02-FIX7: section is now NormalizedTable with all strings
  // EVIDENCE-FIRST: Cells now support NormalizedCell with evidence_ref_id
  console.log("[CoverageLimitCard] normalized section:", {
    title: section.title,
    columns_count: section.columns.length,
    rows_count: section.rows.length,
  });

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-blue-50 px-4 py-2 border-b border-blue-200">
        <h3 className="font-medium text-blue-800">{section.title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-blue-100">
            <tr>
              {section.columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-2 text-left text-sm font-medium text-blue-700"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {section.rows.map((row, idx) => (
              <React.Fragment key={idx}>
                <tr className="border-t border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <div className="font-medium text-gray-700">{row.label}</div>
                    {/* STEP DEMO-Q11-POLISH-01: Show product name below insurer */}
                    {row.meta?.productName && (
                      <div className="text-xs text-gray-500 mt-0.5">{row.meta.productName}</div>
                    )}
                  </td>
                  {row.values.map((cell, cellIdx) => (
                    <td
                      key={cellIdx}
                      className="px-4 py-2 text-sm"
                    >
                      <div className="flex items-center gap-1">
                        <span>{getCellText(cell)}</span>
                        {cellHasEvidence(cell) && (
                          <span className="inline-flex items-center justify-center w-4 h-4 text-xs text-blue-600 bg-blue-100 rounded-full" title="근거 있음">
                            ✓
                          </span>
                        )}
                      </div>
                    </td>
                  ))}
                </tr>
                {/* STEP DEMO-EVIDENCE-RELEVANCE-01: Per-cell evidence grid */}
                {(() => {
                  // Check if ANY cell or row meta has evidence
                  const hasCellEvidence = row.values.some((cell) => {
                    if (typeof cell === "string") return false;
                    return cell.evidences && cell.evidences.length > 0;
                  });
                  const hasProductEvidence = row.meta?.productEvidences && row.meta.productEvidences.length > 0;
                  const hasNote = !!row.meta?.note;

                  if (!hasCellEvidence && !hasProductEvidence && !hasNote) {
                    return null;
                  }

                  return (
                    <tr>
                      <td colSpan={section.columns.length} className="bg-gray-50 px-0 py-0 border-t border-gray-200">
                        {/* STEP DEMO-Q11-POLISH-01: Show reference note if exists */}
                        {hasNote && (
                          <div className="px-4 pt-3 pb-2">
                            <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                              <span className="font-medium">비고:</span> {row.meta?.note}
                            </div>
                          </div>
                        )}
                        {/* Evidence grid matching table columns */}
                        <div className="grid gap-0" style={{ gridTemplateColumns: `minmax(120px, 1fr) repeat(${section.columns.length - 1}, 1fr)` }}>
                          {/* Column 0: Label cell (product evidence) */}
                          <div className="px-4 py-3 border-r border-gray-200">
                            {hasProductEvidence && (
                              <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">상품명 근거</div>
                                {row.meta?.productEvidences?.map((ev: any, idx: number) => (
                                  <div key={idx} className="text-xs text-gray-600 bg-white border border-gray-200 rounded px-2 py-1.5">
                                    <div className="font-medium">{ev.doc_type} p.{ev.page}</div>
                                    <div className="mt-0.5 text-gray-500 line-clamp-2">{(ev.excerpt || "").substring(0, 120)}...</div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          {/* Columns 1+: Value cells */}
                          {row.values.map((cell, cellIdx) => {
                            if (typeof cell === "string" || !cell.evidences || cell.evidences.length === 0) {
                              return <div key={cellIdx} className="px-4 py-3 border-r border-gray-200 last:border-r-0"></div>;
                            }

                            const slotLabel = cell.slotName === "duration_limit_days" ? "보장 한도 근거" :
                                              cell.slotName === "daily_benefit_amount_won" ? "1일당 지급액 근거" : "근거";

                            return (
                              <div key={cellIdx} className="px-4 py-3 border-r border-gray-200 last:border-r-0">
                                <div className="text-xs font-medium text-gray-500 mb-1">{slotLabel}</div>
                                {cell.evidences.map((ev: any, idx: number) => (
                                  <div key={idx} className="text-xs text-gray-600 bg-white border border-gray-200 rounded px-2 py-1.5">
                                    <div className="font-medium">{ev.doc_type} p.{ev.page}</div>
                                    <div className="mt-0.5 text-gray-500 line-clamp-2">{ev.excerpt}</div>
                                  </div>
                                ))}
                              </div>
                            );
                          })}
                        </div>
                      </td>
                    </tr>
                  );
                })()}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
