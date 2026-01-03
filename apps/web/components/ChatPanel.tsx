"use client";

import { useRef, useEffect } from "react";
import { Message, Insurer, MessageKind } from "@/lib/types";

interface ChatPanelProps {
  messages: Message[];
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onSendWithKind?: (
    kind: MessageKind,
    messageOverride?: string,
    insurersOverride?: string[],
    coverageNamesOverride?: string[]
  ) => void;  // STEP NEXT-80-FE: Send with explicit kind + overrides
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
  onSendWithKind,
  isLoading,
  selectedInsurers,
  availableInsurers,
  onInsurerToggle,
  coverageInput,
  onCoverageChange,
}: ChatPanelProps) {
  // STEP NEXT-97: Auto-scroll management
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // STEP NEXT-97: Conversation context lock (conversation is active after first message)
  const conversationActive = messages.length > 0;

  // STEP NEXT-97: Auto-scroll to bottom when new message arrives (only if user is near bottom)
  useEffect(() => {
    if (messages.length === 0) return;

    const container = messagesContainerRef.current;
    if (!container) return;

    // Check if user is near bottom (within 100px threshold)
    const isNearBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 100;

    // Only auto-scroll if user is already near bottom (avoid disrupting manual scroll)
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  // STEP NEXT-80-FE: Example button handlers with explicit kind + message + slots
  const handleExampleClick = (
    kind: MessageKind,
    defaultPrompt: string,
    insurers?: string[],
    coverageNames?: string[]
  ) => {
    console.log(`[ChatPanel] Example button clicked:`, {
      kind,
      prompt: defaultPrompt,
      insurers,
      coverageNames
    });
    if (onSendWithKind) {
      console.log(`[ChatPanel] Calling onSendWithKind`);
      // CRITICAL: Pass all overrides directly to avoid React state timing issues
      onSendWithKind(kind, defaultPrompt, insurers, coverageNames);
    } else {
      onInputChange(defaultPrompt);
      onSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg font-medium">보험 상품 비교 도우미</p>
            <p className="text-sm mt-2">
              질문을 입력하세요
            </p>

            {/* STEP NEXT-80-FE: Example buttons with explicit kind + slots */}
            <div className="mt-6 max-w-2xl mx-auto">
              <p className="text-sm font-medium text-gray-700 mb-3">빠른 시작</p>
              <div className="grid grid-cols-2 gap-3">
                {/* STEP NEXT-86: EX2_DETAIL - 단일 보험사 설명 */}
                <button
                  onClick={() => handleExampleClick(
                    "EX2_DETAIL",
                    "삼성화재 암진단비 설명해주세요",
                    ["samsung"],  // insurers (single)
                    ["암진단비(유사암제외)"]  // coverage_names
                  )}
                  className="p-4 bg-white border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all text-left"
                  disabled={isLoading}
                >
                  <div className="font-medium text-sm text-gray-800 mb-1">
                    예제2: 담보 설명
                  </div>
                  <div className="text-xs text-gray-600">
                    삼성화재 암진단비 상세 안내
                  </div>
                </button>

                <button
                  onClick={() => handleExampleClick(
                    "EX3_COMPARE",
                    "삼성화재와 메리츠화재의 암진단비를 비교해주세요",
                    ["samsung", "meritz"],  // insurers
                    ["암진단비(유사암제외)"]  // coverage_names
                  )}
                  className="p-4 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
                  disabled={isLoading}
                >
                  <div className="font-medium text-sm text-gray-800 mb-1">
                    예제3: 2사 비교
                  </div>
                  <div className="text-xs text-gray-600">
                    삼성화재 vs 메리츠화재 암진단비
                  </div>
                </button>

                <button
                  onClick={() => handleExampleClick(
                    "EX4_ELIGIBILITY",
                    "제자리암 보장 가능한가요?",
                    ["samsung", "meritz"]  // insurers (no coverage_names for EX4)
                  )}
                  className="p-4 bg-white border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all text-left"
                  disabled={isLoading}
                >
                  <div className="font-medium text-sm text-gray-800 mb-1">
                    예제4: 보장 여부 확인
                  </div>
                  <div className="text-xs text-gray-600">
                    제자리암 보장 가능 여부 + 종합평가
                  </div>
                </button>

                {/* STEP NEXT-86: EX2_DETAIL - 한화손보 뇌출혈 */}
                <button
                  onClick={() => handleExampleClick(
                    "EX2_DETAIL",
                    "한화손해보험 뇌출혈진단비 설명해주세요",
                    ["hanwha"],  // insurers (single)
                    ["뇌출혈진단비"]  // coverage_names
                  )}
                  className="p-4 bg-white border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all text-left"
                  disabled={isLoading}
                >
                  <div className="font-medium text-sm text-gray-800 mb-1">
                    예제2-B: 뇌출혈 설명
                  </div>
                  <div className="text-xs text-gray-600">
                    한화손보 뇌출혈진단비 상세 안내
                  </div>
                </button>
              </div>
            </div>
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
        {/* STEP NEXT-97: Scroll anchor for auto-scroll */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        {/* STEP NEXT-97: Conversation context indicator (when locked) */}
        {conversationActive && selectedInsurers.length > 0 && (
          <div className="mb-3 flex items-center justify-between bg-blue-50 border border-blue-200 rounded px-3 py-2">
            <div className="text-xs text-blue-800">
              <span className="font-medium">현재 대화 조건:</span>{" "}
              {selectedInsurers.map((code) => {
                const insurer = availableInsurers.find((i) => i.code === code);
                return insurer?.display;
              }).join(" · ")}
            </div>
            <button
              onClick={() => {
                // Reset conversation to change context
                if (confirm("대화를 초기화하고 조건을 변경하시겠습니까?")) {
                  window.location.reload();
                }
              }}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              조건 변경
            </button>
          </div>
        )}

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
                disabled={conversationActive}
                className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                  selectedInsurers.includes(insurer.code)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                } ${conversationActive ? "opacity-50 cursor-not-allowed" : ""}`}
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
            onKeyDown={handleKeyDown}
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
