/**
 * STEP NEXT-132: EX3 Report View Component (EXAM3 Report View v0)
 *
 * PURPOSE:
 * - Display 1-page report for EX3_COMPARE results
 * - Print/capture-friendly layout
 * - Clean, professional styling
 *
 * CONSTITUTIONAL RULES:
 * - EX3 SSOT only (NO EX4/EX2 mixing)
 * - NO LLM usage
 * - NO recommendation/judgment display
 * - Deterministic rendering only
 */

import React from 'react';
import { EX3ReportDoc } from '../../lib/report/ex3ReportTypes';

interface EX3ReportViewProps {
  report: EX3ReportDoc | null;
}

/**
 * EX3ReportView: 1-page report display for EX3_COMPARE
 *
 * Layout:
 * 1. Header (title + subtitle)
 * 2. Summary Box (핵심 요약)
 * 3. Comparison Table (비교 표)
 * 4. Notes (유의사항)
 */
export function EX3ReportView({ report }: EX3ReportViewProps) {
  if (!report) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 text-sm">
        보고서는 비교(EXAM3) 결과가 있을 때만 생성됩니다.
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="mb-6 border-b-2 border-gray-800 pb-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {report.title}
        </h1>
        {report.subtitle.map((line, idx) => (
          <p key={idx} className="text-sm text-gray-600">
            {line}
          </p>
        ))}
      </div>

      {/* Summary Box */}
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-lg font-bold text-gray-900 mb-3">핵심 요약</h2>
        <div className="space-y-2">
          {report.summary_lines.map((line, idx) => (
            <p key={idx} className="text-sm text-gray-800 leading-relaxed">
              {line}
            </p>
          ))}
        </div>
      </div>

      {/* Comparison Table */}
      <div className="mb-6">
        <h2 className="text-lg font-bold text-gray-900 mb-3">
          {report.table.title}
        </h2>
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300">
            {/* Table Header */}
            <thead>
              <tr className="bg-gray-100">
                {report.table.columns?.map((col, idx) => (
                  <th
                    key={idx}
                    className="px-4 py-2 text-left text-sm font-semibold text-gray-900 border border-gray-300"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>

            {/* Table Body */}
            <tbody>
              {report.table.rows?.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-gray-50">
                  {row.cells?.map((cell, cellIdx) => (
                    <td
                      key={cellIdx}
                      className={`px-4 py-3 text-sm border border-gray-300 ${
                        cellIdx === 0
                          ? 'font-semibold bg-gray-50'
                          : 'text-gray-800'
                      }`}
                    >
                      {cell.text || ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Notes */}
      {report.notes.length > 0 && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h2 className="text-lg font-bold text-gray-900 mb-3">유의사항</h2>
          <ul className="list-disc list-inside space-y-1">
            {report.notes.map((note, idx) => (
              <li key={idx} className="text-sm text-gray-800">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer (optional - for print) */}
      <div className="mt-8 pt-4 border-t border-gray-300 text-center text-xs text-gray-500">
        이 보고서는 가입설계서 기준으로 작성되었으며, 실제 보장 여부는 약관을 직접 확인하시기 바랍니다.
      </div>
    </div>
  );
}
