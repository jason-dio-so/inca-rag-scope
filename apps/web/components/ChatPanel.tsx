"use client";

import { Message, Insurer } from "@/lib/types";

interface ChatPanelProps {
  messages: Message[];
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  selectedInsurers: string[];
  availableInsurers: Insurer[];
  onInsurerToggle: (code: string) => void;
  coverageInput: string;
  onCoverageChange: (value: string) => void;
}

export default function ChatPanel({
  messages,
  input,
  onInputChange,
  onSend,
  isLoading,
  selectedInsurers,
  availableInsurers,
  onInsurerToggle,
  coverageInput,
  onCoverageChange,
}: ChatPanelProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg font-medium">보험 상품 비교 도우미</p>
            <p className="text-sm mt-2">
              좌측에서 카테고리를 선택하고 질문을 입력하세요
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        {/* Insurer selector */}
        <div className="mb-3">
          <label className="text-xs font-medium text-gray-700 mb-1 block">
            보험사 선택 (복수 가능)
          </label>
          <div className="flex flex-wrap gap-2">
            {availableInsurers.map((insurer) => (
              <button
                key={insurer.code}
                onClick={() => onInsurerToggle(insurer.code)}
                className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                  selectedInsurers.includes(insurer.code)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {insurer.display}
              </button>
            ))}
          </div>
        </div>

        {/* Coverage input */}
        <div className="mb-3">
          <label className="text-xs font-medium text-gray-700 mb-1 block">
            담보명 (선택사항, 쉼표로 구분)
          </label>
          <input
            type="text"
            value={coverageInput}
            onChange={(e) => onCoverageChange(e.target.value)}
            placeholder="예: 암진단비(유사암제외)"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Message input */}
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="질문을 입력하세요..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={onSend}
            disabled={isLoading || !input.trim()}
            className="px-6 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}
