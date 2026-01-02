"use client";

import { NormalizedTable } from "@/lib/normalize/table";

interface SubtypeEligibilityCardProps {
  section: NormalizedTable;
}

export default function SubtypeEligibilityCard({
  section,
}: SubtypeEligibilityCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-green-50 px-4 py-2 border-b border-green-200">
        <h3 className="font-medium text-green-800">{section.title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-green-100">
            <tr>
              {section.columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-2 text-left text-sm font-medium text-green-700"
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
                {row.values.map((cell, cellIdx) => {
                  return (
                    <td
                      key={cellIdx}
                      className={`px-4 py-2 text-sm ${
                        cellIdx === 0 ? "font-bold" : ""
                      } ${
                        cell === "O"
                          ? "text-green-600"
                          : cell === "X"
                          ? "text-red-600"
                          : cell.includes("△")
                          ? "text-orange-600"
                          : "text-gray-600"
                      }`}
                    >
                      {cell}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
