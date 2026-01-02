"use client";

import { NormalizedTable } from "@/lib/normalize/table";

interface CoverageLimitCardProps {
  section: NormalizedTable;
}

export default function CoverageLimitCard({
  section,
}: CoverageLimitCardProps) {
  // STEP NEXT-UI-02-FIX7: section is now NormalizedTable with all strings
  // No need for renderCellValue since normalizer already converted everything
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
              <tr key={idx} className="border-t border-gray-200 hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-700">
                  {row.label}
                </td>
                {row.values.map((cell, cellIdx) => (
                  <td
                    key={cellIdx}
                    className="px-4 py-2 text-sm"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
