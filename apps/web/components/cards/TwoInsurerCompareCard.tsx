"use client";

import { NormalizedTable } from "@/lib/normalize/table";

interface TwoInsurerCompareCardProps {
  section: NormalizedTable;
}

export default function TwoInsurerCompareCard({
  section,
}: TwoInsurerCompareCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-purple-50 px-4 py-2 border-b border-purple-200">
        <h3 className="font-medium text-purple-800">{section.title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-purple-100">
            <tr>
              {section.columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-2 text-left text-sm font-medium text-purple-700"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {section.rows.map((row, idx) => (
              <tr key={idx} className="border-t border-gray-200 hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-700 bg-gray-50">
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
