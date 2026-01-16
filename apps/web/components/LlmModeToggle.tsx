"use client";

import { LlmMode } from "@/lib/types";

interface LlmModeToggleProps {
  mode: LlmMode;
  onChange: (mode: LlmMode) => void;
}

export default function LlmModeToggle({ mode, onChange }: LlmModeToggleProps) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-600">LLM:</span>
      <button
        onClick={() => onChange(mode === "OFF" ? "ON" : "OFF")}
        className={`px-3 py-1 rounded font-medium ${
          mode === "OFF"
            ? "bg-green-100 text-green-700 border border-green-300"
            : "bg-orange-100 text-orange-700 border border-orange-300"
        }`}
      >
        {mode}
      </button>
      {mode === "OFF" && (
        <span className="text-xs text-gray-500">결정론적 모드</span>
      )}
    </div>
  );
}
