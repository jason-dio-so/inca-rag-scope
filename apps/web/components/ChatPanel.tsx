"use client";

import { useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  coverageInputDisabled?: boolean;  // STEP NEXT-106: Disable during LIMIT_FIND clarification
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
  coverageInputDisabled = false,  // STEP NEXT-106: Default to enabled
}: ChatPanelProps) {
  // STEP NEXT-97: Auto-scroll management
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // STEP NEXT-97/114: Conversation context lock (conversation is active after first message)
  const conversationActive = messages.length > 0;

  // STEP NEXT-114: Initial state flag (before any messages)
  const isInitialState = messages.length === 0;

  // STEP NEXT-108: Collapsible options panel (ChatGPT style)
  const [isOptionsExpanded, setIsOptionsExpanded] = useState(false);

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

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* STEP NEXT-129R: First impression screen (1 line + 3 example buttons, NO auto-send) */}
        {isInitialState ? (
          <div className="flex justify-start mt-8">
            <div className="max-w-[65%] rounded-lg px-4 py-3 bg-gray-100 text-gray-800">
              <div className="text-sm leading-relaxed">
                <p className="mb-3">궁금한 담보를 그냥 말로 물어보세요.</p>
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      // STEP NEXT-129R: Fill input ONLY (NO auto-send, NO auto-context)
                      onInputChange("암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘");
                    }}
                    className="block w-full text-left px-3 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm"
                  >
                    예: 암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘
                  </button>
                  <button
                    onClick={() => {
                      // STEP NEXT-129R: Fill input ONLY (NO auto-send, NO auto-context)
                      onInputChange("삼성화재와 메리츠화재 암진단비 비교해줘");
                    }}
                    className="block w-full text-left px-3 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm"
                  >
                    예: 삼성화재와 메리츠화재 암진단비 비교해줘
                  </button>
                  <button
                    onClick={() => {
                      // STEP NEXT-129R: Fill input ONLY (NO auto-send, NO auto-context)
                      onInputChange("제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘");
                    }}
                    className="block w-full text-left px-3 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm"
                  >
                    예: 제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘
                  </button>
                </div>
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
                {/* STEP NEXT-108/110A: Render markdown for assistant messages (rich bubbles) */}
                {msg.role === "assistant" ? (
                  (() => {
                    // STEP NEXT-110A: Extract and style product header separately
                    const headerStart = msg.content.indexOf('<!-- PRODUCT_HEADER -->');
                    const headerEnd = msg.content.indexOf('<!-- /PRODUCT_HEADER -->');

                    if (headerStart !== -1 && headerEnd !== -1) {
                      const headerContent = msg.content.slice(
                        headerStart + '<!-- PRODUCT_HEADER -->'.length,
                        headerEnd
                      ).trim();
                      const bodyContent = msg.content.slice(headerEnd + '<!-- /PRODUCT_HEADER -->'.length).trim();

                      return (
                        <div className="text-sm prose prose-sm max-w-none prose-headings:text-gray-900 prose-h2:text-base prose-h2:font-semibold prose-h2:mt-0 prose-h2:mb-2 prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-table:text-xs prose-th:bg-gray-200 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-gray-300 prose-strong:text-gray-900 prose-strong:font-bold prose-hr:my-3 prose-hr:border-gray-300">
                          {/* Product Header with special styling */}
                          <div className="product-header mb-3">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                strong: ({ children }) => <strong className="text-lg block">{children}</strong>,
                              }}
                            >
                              {headerContent}
                            </ReactMarkdown>
                          </div>
                          {/* Body content with normal styling */}
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {bodyContent}
                          </ReactMarkdown>
                        </div>
                      );
                    }

                    // No header markers - render normally
                    return (
                      <div className="text-sm prose prose-sm max-w-none prose-headings:text-gray-900 prose-h2:text-base prose-h2:font-semibold prose-h2:mt-0 prose-h2:mb-2 prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-table:text-xs prose-th:bg-gray-200 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-gray-300 prose-strong:text-gray-900 prose-strong:font-bold prose-hr:my-3 prose-hr:border-gray-300">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    );
                  })()
                ) : (
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                )}
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

      {/* STEP NEXT-108: Input area - ChatGPT style (collapsed by default) */}
      <div className="border-t border-gray-200 bg-white">
        <div className="p-4">
          {/* STEP NEXT-108: Compact context indicator (always visible when active) */}
          {conversationActive && selectedInsurers.length > 0 && (
            <div className="mb-2 flex items-center justify-between text-xs text-gray-600">
              <div>
                <span className="font-medium">대화 중:</span>{" "}
                {selectedInsurers.map((code) => {
                  const insurer = availableInsurers.find((i) => i.code === code);
                  return insurer?.display;
                }).join(" · ")}
              </div>
              <button
                onClick={() => setIsOptionsExpanded(!isOptionsExpanded)}
                className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
              >
                옵션 {isOptionsExpanded ? "▴" : "▾"}
              </button>
            </div>
          )}

          {/* STEP NEXT-108: Collapsible options panel */}
          {isOptionsExpanded && (
            <div className="mb-3 p-3 bg-gray-50 border border-gray-200 rounded max-h-48 overflow-y-auto">
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
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1 block">
                  담보명 (선택사항)
                </label>
                <input
                  type="text"
                  value={coverageInput}
                  onChange={(e) => onCoverageChange(e.target.value)}
                  disabled={coverageInputDisabled}
                  placeholder={
                    coverageInputDisabled
                      ? "비교를 위해 보험사만 추가해주세요"
                      : "예: 암진단비(유사암제외)"
                  }
                  className={`w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    coverageInputDisabled
                      ? "bg-gray-100 text-gray-500 cursor-not-allowed"
                      : ""
                  }`}
                />
              </div>

              {/* Reset button */}
              <button
                onClick={() => {
                  if (confirm("대화를 초기화하고 조건을 변경하시겠습니까?")) {
                    window.location.reload();
                  }
                }}
                className="mt-3 text-xs text-red-600 hover:text-red-800 font-medium"
              >
                대화 초기화
              </button>
            </div>
          )}

          {/* STEP NEXT-108: Initial state - show options button */}
          {!conversationActive && (
            <button
              onClick={() => setIsOptionsExpanded(!isOptionsExpanded)}
              className="mb-2 text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
            >
              {isOptionsExpanded ? "옵션 숨기기 ▴" : "보험사/담보 선택 ▾"}
            </button>
          )}

          {/* STEP NEXT-108: Initial options panel (before first message) */}
          {!conversationActive && isOptionsExpanded && (
            <div className="mb-3 p-3 bg-gray-50 border border-gray-200 rounded">
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
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1 block">
                  담보명 (선택사항)
                </label>
                <input
                  type="text"
                  value={coverageInput}
                  onChange={(e) => onCoverageChange(e.target.value)}
                  placeholder="예: 암진단비(유사암제외)"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {/* STEP NEXT-120: Message input (comparison-first placeholder) */}
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="예: 삼성화재와 메리츠화재 암진단비 비교해줘"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={onSend}
              disabled={isLoading || !input.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              전송
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
