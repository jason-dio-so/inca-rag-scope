"use client";

import { useState } from "react";
import { EvidenceItem } from "@/lib/types";

interface EvidenceToggleProps {
  items: EvidenceItem[];
  defaultCollapsed?: boolean;
}

export default function EvidenceToggle({
  items,
  defaultCollapsed = true,
}: EvidenceToggleProps) {
  const [isOpen, setIsOpen] = useState(!defaultCollapsed);

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 rounded-t-lg"
      >
        <span className="font-medium text-gray-700">
          근거 자료 ({items.length}개)
        </span>
        <svg
          className={`w-5 h-5 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          {items.map((item, idx) => (
            <div
              key={item.evidence_ref_id || idx}
              className="border-l-4 border-blue-300 pl-3 py-2 bg-blue-50 rounded"
            >
              <div className="text-sm font-medium text-gray-700">
                {item.insurer} - {item.coverage_name}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {item.doc_type}
                {item.page && ` p.${item.page}`}
              </div>
              {item.snippet && (
                <div className="text-xs text-gray-500 mt-2 italic">
                  {item.snippet}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
