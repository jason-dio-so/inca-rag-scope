"use client";

import { useState, useEffect } from "react";
import {
  Message,
  LlmMode,
  Category,
  AssistantMessageVM,
  UIConfig,
} from "@/lib/types";
import { postChat } from "@/lib/api";
import SidebarCategories from "@/components/SidebarCategories";
import ChatPanel from "@/components/ChatPanel";
import ResultDock from "@/components/ResultDock";
import LlmModeToggle from "@/components/LlmModeToggle";

export default function Home() {
  const [config, setConfig] = useState<UIConfig | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedInsurers, setSelectedInsurers] = useState<string[]>([]);
  const [llmMode, setLlmMode] = useState<LlmMode>("OFF");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [coverageInput, setCoverageInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestResponse, setLatestResponse] =
    useState<AssistantMessageVM | null>(null);

  // Load UI config
  useEffect(() => {
    fetch("/ui_config.json")
      .then((res) => res.json())
      .then((data) => {
        setConfig(data);
        setLlmMode(data.ui_settings.default_llm_mode);
      })
      .catch((err) => {
        console.error("Failed to load UI config:", err);
      });
  }, []);

  // Clear results when category changes
  useEffect(() => {
    setMessages([]);
    setLatestResponse(null);
    setError(null);
  }, [selectedCategory]);

  const handleSend = async () => {
    if (!input.trim() || !config) return;

    setError(null);
    const userMessage: Message = {
      role: "user",
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Prepare request
      const categoryLabel = config.categories.find(
        (c) => c.id === selectedCategory
      )?.label;

      const coverageNames = coverageInput
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const response = await postChat({
        message: input,
        selected_category: categoryLabel,
        insurers: selectedInsurers.length > 0 ? selectedInsurers : undefined,
        coverage_names: coverageNames.length > 0 ? coverageNames : undefined,
        llm_mode: llmMode,
      });

      console.log("chat response:", response);

      // Validate response structure
      if (!response || typeof response !== "object") {
        throw new Error("Invalid response from server");
      }

      // Check for error response (from frontend wrapper)
      if (response.ok === false || response.error) {
        setError(
          response.error?.message || "알 수 없는 오류가 발생했습니다."
        );
        const errorMsg: Message = {
          role: "assistant",
          content: `오류: ${response.error?.message}\n\n${response.error?.detail || ""}`,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } else if (!response.message) {
        // No message field (empty response)
        setError("서버로부터 응답을 받지 못했습니다.");
        const errorMsg: Message = {
          role: "assistant",
          content: "오류: 서버 응답이 비어있습니다.",
        };
        setMessages((prev) => [...prev, errorMsg]);
      } else {
        // Success - response.message is AssistantMessageVM
        const vm = response.message;
        setLatestResponse(vm);

        // Build summary text with defensive guards
        const title = vm?.title ?? "결과";
        const bullets = Array.isArray(vm?.summary_bullets) ? vm.summary_bullets : [];
        const summaryParts = [title, ...bullets].filter(Boolean);
        const summaryText = summaryParts.join("\n\n");

        const assistantMsg: Message = {
          role: "assistant",
          content: summaryText,
          vm: vm,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setError("요청 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleInsurerToggle = (code: string) => {
    setSelectedInsurers((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  if (!config) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-600">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <SidebarCategories
        categories={config.categories}
        selectedCategory={selectedCategory}
        onSelectCategory={setSelectedCategory}
      />

      {/* Main area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-800">
            보험 상품 비교 도우미
          </h1>
          <LlmModeToggle mode={llmMode} onChange={setLlmMode} />
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat area */}
          <div className="flex-1 flex flex-col">
            <ChatPanel
              messages={messages}
              input={input}
              onInputChange={setInput}
              onSend={handleSend}
              isLoading={isLoading}
              selectedInsurers={selectedInsurers}
              availableInsurers={config.available_insurers}
              onInsurerToggle={handleInsurerToggle}
              coverageInput={coverageInput}
              onCoverageChange={setCoverageInput}
            />
          </div>

          {/* Result dock */}
          {latestResponse && (
            <div className="w-1/2 border-l border-gray-200 overflow-y-auto p-4 bg-gray-50">
              <ResultDock response={latestResponse} />
            </div>
          )}
        </div>

        {/* Error banner */}
        {error && (
          <div className="bg-red-50 border-t border-red-200 px-4 py-3">
            <div className="text-red-800 text-sm font-medium">오류</div>
            <div className="text-red-700 text-sm mt-1">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
