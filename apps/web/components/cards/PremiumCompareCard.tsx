"use client";

import { NormalizedTable } from "@/lib/normalize/table";

interface PremiumCompareCardProps {
  section: NormalizedTable;
}

export default function PremiumCompareCard({
  section,
}: PremiumCompareCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
        <h3 className="font-medium text-gray-800">{section.title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              {section.columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-2 text-left text-sm font-medium text-gray-700"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {section.rows.map((row, idx) => (
              <tr key={idx} className="border-t border-gray-200">
                <td className="px-4 py-2 font-medium text-gray-700">
                  {row.label}
                </td>
                {row.values.map((cell, cellIdx) => (
                  <td key={cellIdx} className="px-4 py-2">
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
