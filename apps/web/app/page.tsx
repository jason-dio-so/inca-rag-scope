"use client";

import { useState, useEffect } from "react";
import {
  Message,
  LlmMode,
  AssistantMessageVM,
  UIConfig,
  MessageKind,
} from "@/lib/types";
import { postChat } from "@/lib/api";
import {
  isInsurerSwitchUtterance,
  extractInsurerFromSwitch,
  isLimitFindPattern,
} from "@/lib/contextUtils";  // STEP NEXT-102 (STEP NEXT-129R: Removed unused imports)
import SidebarCategories from "@/components/SidebarCategories";
import ChatPanel from "@/components/ChatPanel";
import ResultDock from "@/components/ResultDock";
import LlmModeToggle from "@/components/LlmModeToggle";
import { EX3ReportView } from "@/components/report/EX3ReportView";
import { composeEx3Report } from "@/lib/report/composeEx3Report";

// STEP NEXT-101: Conversation context type
interface ConversationContext {
  lockedInsurers: string[] | null;
  lockedCoverageNames: string[] | null;
  isLocked: boolean;
}

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
  const [clarification, setClarification] = useState<{
    missing_slots: string[];
    options: Record<string, string[]>;
    draftRequest: any;
  } | null>(null);

  // STEP NEXT-106: Track if clarification is for LIMIT_FIND (disable coverage input)
  const [isLimitFindClarification, setIsLimitFindClarification] = useState(false);

  // STEP NEXT-106: Track selected insurers for multi-select clarification
  const [clarificationSelectedInsurers, setClarificationSelectedInsurers] = useState<string[]>([]);

  // STEP NEXT-101: Conversation context carryover
  const [conversationContext, setConversationContext] = useState<ConversationContext>({
    lockedInsurers: null,
    lockedCoverageNames: null,
    isLocked: false,
  });

  // STEP NEXT-132: Report view mode toggle
  const [viewMode, setViewMode] = useState<"comparison" | "report">("comparison");

  // STEP NEXT-133: EX3 Gate state (front-trigger selection panel, NO backend need_more_info)
  const [pendingKind, setPendingKind] = useState<"EX3_COMPARE" | null>(null);
  const [ex3GateOpen, setEx3GateOpen] = useState(false);
  const [ex3GateMessageId, setEx3GateMessageId] = useState<string | null>(null);

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

  // STEP NEXT-101: Payload builder SSOT (state → context fallback)
  const buildChatPayload = (
    message: string,
    kindOverride?: MessageKind,
    insurersOverride?: string[],
    coverageNamesOverride?: string[],
    diseaseNameOverride?: string
  ) => {
    const categoryLabel = config?.categories.find(
      (c) => c.id === selectedCategory
    )?.label;

    // Priority 1: Override values (from example buttons)
    // Priority 2: Current UI state
    // Priority 3: Locked conversation context
    const insurersToSend =
      insurersOverride ||
      (selectedInsurers.length > 0 ? selectedInsurers : null) ||
      conversationContext.lockedInsurers;

    const coverageNamesFromInput = coverageInput
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const coverageNamesToSend =
      coverageNamesOverride ||
      (coverageNamesFromInput.length > 0 ? coverageNamesFromInput : null) ||
      conversationContext.lockedCoverageNames;

    return {
      message,
      kind: kindOverride,
      selected_category: categoryLabel,
      insurers: insurersToSend || undefined,
      coverage_names: coverageNamesToSend || undefined,
      disease_name: diseaseNameOverride,
      llm_mode: llmMode,
    };
  };

  const handleSend = async () => {
    if (!input.trim() || !config) return;

    setError(null);

    // STEP NEXT-129R: Capture message before clearing input (kept for logging)
    const messageToSend = input;

    // STEP NEXT-133: Detect EX3 intent FIRST (before any backend call)
    // Trigger EX3 Gate if user requests comparison
    const isEX3Intent =
      messageToSend.includes("비교") ||
      messageToSend.includes("차이") ||
      messageToSend.includes("VS") ||
      messageToSend.includes("vs");

    if (isEX3Intent && !ex3GateOpen) {
      // Check if requirements are met
      const currentInsurers = selectedInsurers.length > 0
        ? selectedInsurers
        : conversationContext.lockedInsurers || [];

      const coverageNamesFromInput = coverageInput
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const currentCoverageNames = coverageNamesFromInput.length > 0
        ? coverageNamesFromInput
        : conversationContext.lockedCoverageNames || [];

      // EX3 requires 2 insurers + 1 coverage
      if (currentInsurers.length < 2 || currentCoverageNames.length === 0) {
        console.log("[page.tsx STEP NEXT-133] EX3_GATE_OPEN: insufficient context", {
          insurers: currentInsurers.length,
          coverages: currentCoverageNames.length
        });

        // Add user message first
        const userMessage: Message = {
          role: "user",
          content: messageToSend,
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");

        // Generate unique message ID for gate message (avoid duplicates)
        const gateMessageId = `ex3-gate-${Date.now()}`;

        // Add EX3 gate assistant message
        const gateMessage: Message = {
          role: "assistant",
          content: "비교를 위해 담보와 보험사를 먼저 선택해 주세요.\n아래에서 보험사 2개와 담보명 1개를 고르면 바로 비교표를 보여드릴게요.",
        };
        setMessages((prev) => [...prev, gateMessage]);

        // Open EX3 gate panel
        setPendingKind("EX3_COMPARE");
        setEx3GateOpen(true);
        setEx3GateMessageId(gateMessageId);
        return;
      }
    }

    // STEP NEXT-129R: REMOVED silent payload correction (ROLLBACK)
    // STEP NEXT-129R: REMOVED comparison intent hard-lock (ROLLBACK)
    // STEP NEXT-129R: REMOVED need_more_info bypass (ROLLBACK)

    // STEP NEXT-103: Detect insurer switch BEFORE payload generation (KEPT)
    // Capture effective values for THIS request (override state)
    let effectiveInsurers: string[] | undefined = undefined;
    let effectiveCoverageNames: string[] | undefined = undefined;
    let effectiveKind: MessageKind | undefined = undefined;

    if (isInsurerSwitchUtterance(messageToSend)) {
      const newInsurer = extractInsurerFromSwitch(messageToSend);
      if (newInsurer) {
        console.log("[page.tsx] Insurer switch detected:", newInsurer);
        // STEP NEXT-103: Override payload for THIS request
        effectiveInsurers = [newInsurer];
        effectiveCoverageNames = conversationContext.lockedCoverageNames || undefined;
        effectiveKind = "EX2_DETAIL" as MessageKind;

        // Update state for future requests (async, won't affect current request)
        setSelectedInsurers([newInsurer]);
        setConversationContext({
          ...conversationContext,
          lockedInsurers: [newInsurer],
        });
      }
    }

    // STEP NEXT-102: Detect LIMIT_FIND pattern and validate multi-insurer requirement (KEPT)
    if (isLimitFindPattern(messageToSend)) {
      const currentInsurers = effectiveInsurers ||
        (selectedInsurers.length > 0 ? selectedInsurers : conversationContext.lockedInsurers || []);

      if (currentInsurers.length < 2) {
        // Need at least 2 insurers for LIMIT_FIND
        console.log("[page.tsx] LIMIT_FIND pattern detected but only 1 insurer, showing selection UI");

        // Add user message first
        const userMessage: Message = {
          role: "user",
          content: messageToSend,
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");

        // STEP NEXT-106: Mark this as LIMIT_FIND clarification (disable coverage input)
        setIsLimitFindClarification(true);

        // Show clarification with insurers selection
        setClarification({
          missing_slots: ["insurers"],
          options: {
            insurers: config.available_insurers.map(i => i.code),
          },
          draftRequest: {
            message: messageToSend,
            coverage_names: conversationContext.lockedCoverageNames || undefined,
            llm_mode: llmMode,
          },
        });
        return;
      }
    }

    const userMessage: Message = {
      role: "user",
      content: messageToSend,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // STEP NEXT-129R: Use buildChatPayload with effective overrides (insurer switch only, NO silent correction)
      const requestPayload = buildChatPayload(
        messageToSend,
        effectiveKind,
        effectiveInsurers,
        effectiveCoverageNames
      );

      console.log("[page.tsx handleSend] Request payload:", requestPayload);

      const response = await postChat(requestPayload);

      console.log("chat response:", response);

      // Validate response structure
      if (!response || typeof response !== "object") {
        throw new Error("Invalid response from server");
      }

      // STEP NEXT-129R: Handle need_more_info (NO bypass, ALWAYS show clarification UI)
      if (response.need_more_info === true) {
        setClarification({
          missing_slots: response.missing_slots || [],
          options: response.clarification_options || {},
          draftRequest: requestPayload,
        });
        return;
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

        // STEP NEXT-101: Lock conversation context on first successful response
        if (!conversationContext.isLocked && requestPayload.insurers) {
          setConversationContext({
            lockedInsurers: Array.isArray(requestPayload.insurers) ? requestPayload.insurers : [requestPayload.insurers],
            lockedCoverageNames: requestPayload.coverage_names ?
              (Array.isArray(requestPayload.coverage_names) ? requestPayload.coverage_names : [requestPayload.coverage_names]) : null,
            isLocked: true,
          });
          console.log("[page.tsx handleSend] Locked conversation context:", {
            insurers: requestPayload.insurers,
            coverage_names: requestPayload.coverage_names,
          });
        }

        // STEP NEXT-129R: Use backend bubble_markdown as SSOT (NO frontend override)
        let summaryText: string;
        if (vm?.bubble_markdown) {
          // Use bubble_markdown from backend (SSOT)
          summaryText = vm.bubble_markdown;
        } else {
          // Fallback to legacy summary (backward compatibility)
          const title = vm?.title ?? "결과";
          const bullets = Array.isArray(vm?.summary_bullets) ? vm.summary_bullets : [];
          const summaryParts = [title, ...bullets].filter(Boolean);
          summaryText = summaryParts.join("\n\n");
        }

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

  // STEP NEXT-129R: Removed handleExampleClick (no auto-context setup)

  // STEP NEXT-80: Handle clarification selection and auto-resend
  const handleClarificationSelect = async (slotName: string, value: string | string[]) => {
    if (!clarification) return;

    const updatedRequest = { ...clarification.draftRequest };

    if (slotName === "coverage_names") {
      updatedRequest.coverage_names = Array.isArray(value) ? value : [value];
      // STEP NEXT-100: Update UI state so next request includes this value
      setCoverageInput(Array.isArray(value) ? value.join(", ") : value);
    } else if (slotName === "insurers") {
      // STEP NEXT-102: For LIMIT_FIND flow, ADD to existing insurers (don't replace)
      const existingInsurers = conversationContext.lockedInsurers || [];
      const newInsurers = Array.isArray(value) ? value : [value];

      // Merge: keep existing + add new (dedupe)
      const mergedInsurers = [...new Set([...existingInsurers, ...newInsurers])];

      updatedRequest.insurers = mergedInsurers;
      // STEP NEXT-100: Update UI state so next request includes this value
      setSelectedInsurers(mergedInsurers);
    }

    // STEP NEXT-106: Clear clarification state (restore coverage input)
    setClarification(null);
    setIsLimitFindClarification(false);
    setClarificationSelectedInsurers([]);
    setIsLoading(true);

    try {
      const response = await postChat(updatedRequest);
      console.log("clarification resend response:", response);

      if (!response || typeof response !== "object") {
        throw new Error("Invalid response from server");
      }

      if (response.need_more_info === true) {
        // Still need more info
        setClarification({
          missing_slots: response.missing_slots || [],
          options: response.clarification_options || {},
          draftRequest: updatedRequest,
        });
        return;
      }

      if (response.ok === false || response.error) {
        setError(response.error?.message || "알 수 없는 오류가 발생했습니다.");
      } else if (!response.message) {
        setError("서버로부터 응답을 받지 못했습니다.");
      } else {
        const vm = response.message;
        setLatestResponse(vm);

        // STEP NEXT-101: Lock conversation context on successful clarification response
        if (!conversationContext.isLocked && updatedRequest.insurers) {
          setConversationContext({
            lockedInsurers: Array.isArray(updatedRequest.insurers) ? updatedRequest.insurers : [updatedRequest.insurers],
            lockedCoverageNames: updatedRequest.coverage_names ?
              (Array.isArray(updatedRequest.coverage_names) ? updatedRequest.coverage_names : [updatedRequest.coverage_names]) : null,
            isLocked: true,
          });
          console.log("[page.tsx handleClarificationSelect] Locked conversation context:", {
            insurers: updatedRequest.insurers,
            coverage_names: updatedRequest.coverage_names,
          });
        }

        // STEP NEXT-129R: Use backend bubble_markdown as SSOT (NO frontend override)
        let summaryText: string;
        if (vm?.bubble_markdown) {
          // Use bubble_markdown from backend (SSOT)
          summaryText = vm.bubble_markdown;
        } else {
          // Fallback to legacy summary (backward compatibility)
          const title = vm?.title ?? "결과";
          const bullets = Array.isArray(vm?.summary_bullets) ? vm.summary_bullets : [];
          const summaryParts = [title, ...bullets].filter(Boolean);
          summaryText = summaryParts.join("\n\n");
        }

        const assistantMsg: Message = {
          role: "assistant",
          content: summaryText,
          vm: vm,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err) {
      console.error("Clarification resend error:", err);
      setError("요청 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
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
              coverageInputDisabled={isLimitFindClarification}
            />
          </div>

          {/* STEP NEXT-114: Result dock hidden in initial state */}
          {/* STEP NEXT-132: Report view toggle */}
          {latestResponse && messages.length > 0 && (
            <div className="w-1/2 border-l border-gray-200 flex flex-col bg-gray-50">
              {/* Toggle header */}
              <div className="border-b border-gray-300 bg-white px-4 py-2 flex gap-2">
                <button
                  onClick={() => setViewMode("comparison")}
                  className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    viewMode === "comparison"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  비교 보기
                </button>
                <button
                  onClick={() => setViewMode("report")}
                  className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    viewMode === "report"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  보고서 보기
                </button>
              </div>

              {/* Content area */}
              <div className="flex-1 overflow-y-auto p-4">
                {viewMode === "comparison" ? (
                  <ResultDock response={latestResponse} />
                ) : (
                  <EX3ReportView
                    report={composeEx3Report(
                      messages
                        .filter((m) => m.role === "assistant" && m.vm)
                        .map((m) => m.vm!)
                    )}
                  />
                )}
              </div>
            </div>
          )}
        </div>

        {/* STEP NEXT-133: EX3 Gate UI (front-trigger selection, NO backend need_more_info) */}
        {ex3GateOpen && (
          <div className="bg-blue-50 border-t border-blue-200 px-4 py-4">
            <div className="text-blue-900 text-sm font-medium mb-2">
              비교를 위한 정보 선택
            </div>

            {/* Insurer selection (2 required) */}
            <div className="mb-3">
              <div className="text-blue-800 text-xs mb-2">
                비교할 보험사 (2개 선택)
              </div>
              <div className="flex flex-wrap gap-2">
                {config.available_insurers.map((insurer) => {
                  const isSelected = selectedInsurers.includes(insurer.code);
                  return (
                    <button
                      key={insurer.code}
                      onClick={() => {
                        setSelectedInsurers((prev) =>
                          prev.includes(insurer.code)
                            ? prev.filter((c) => c !== insurer.code)
                            : [...prev, insurer.code]
                        );
                      }}
                      className={`px-3 py-1.5 text-sm border rounded transition-colors ${
                        isSelected
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-gray-700 border-blue-300 hover:bg-blue-100"
                      }`}
                    >
                      {insurer.display}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Coverage input (1 required) */}
            <div className="mb-3">
              <div className="text-blue-800 text-xs mb-2">
                비교할 담보 (1개)
              </div>
              <input
                type="text"
                value={coverageInput}
                onChange={(e) => setCoverageInput(e.target.value)}
                placeholder="예: 암진단비"
                className="w-full px-3 py-2 text-sm border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Submit button */}
            <button
              onClick={async () => {
                // Validate requirements
                if (selectedInsurers.length < 2) {
                  alert("보험사를 2개 선택해 주세요.");
                  return;
                }

                const coverageNamesFromInput = coverageInput
                  .split(",")
                  .map((s) => s.trim())
                  .filter((s) => s.length > 0);

                if (coverageNamesFromInput.length === 0) {
                  alert("담보명을 입력해 주세요.");
                  return;
                }

                console.log("[page.tsx STEP NEXT-133] EX3_GATE_SUBMIT", {
                  insurers: selectedInsurers,
                  coverages: coverageNamesFromInput
                });

                // Close gate
                setEx3GateOpen(false);
                setIsLoading(true);

                try {
                  // Build EX3_COMPARE request
                  const requestPayload = {
                    message: "비교 요청",  // Generic message (user already sent their question)
                    kind: "EX3_COMPARE" as MessageKind,
                    insurers: selectedInsurers,
                    coverage_names: coverageNamesFromInput,
                    llm_mode: llmMode,
                  };

                  console.log("[page.tsx STEP NEXT-133] EX3_CHAT_REQUEST_SENT", requestPayload);

                  const response = await postChat(requestPayload);
                  console.log("EX3 gate response:", response);

                  if (!response || typeof response !== "object") {
                    throw new Error("Invalid response from server");
                  }

                  if (response.ok === false || response.error) {
                    setError(response.error?.message || "알 수 없는 오류가 발생했습니다.");
                  } else if (!response.message) {
                    setError("서버로부터 응답을 받지 못했습니다.");
                  } else {
                    const vm = response.message;
                    setLatestResponse(vm);

                    // Lock conversation context
                    setConversationContext({
                      lockedInsurers: selectedInsurers,
                      lockedCoverageNames: coverageNamesFromInput,
                      isLocked: true,
                    });

                    // Use backend bubble_markdown as SSOT
                    let summaryText: string;
                    if (vm?.bubble_markdown) {
                      summaryText = vm.bubble_markdown;
                    } else {
                      const title = vm?.title ?? "결과";
                      const bullets = Array.isArray(vm?.summary_bullets) ? vm.summary_bullets : [];
                      const summaryParts = [title, ...bullets].filter(Boolean);
                      summaryText = summaryParts.join("\n\n");
                    }

                    const assistantMsg: Message = {
                      role: "assistant",
                      content: summaryText,
                      vm: vm,
                    };
                    setMessages((prev) => [...prev, assistantMsg]);
                  }
                } catch (err) {
                  console.error("EX3 gate error:", err);
                  setError("요청 중 오류가 발생했습니다.");
                } finally {
                  setIsLoading(false);
                  setPendingKind(null);
                }
              }}
              disabled={selectedInsurers.length < 2 || !coverageInput.trim()}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              비교 시작 ({selectedInsurers.length}/2개 보험사, {coverageInput.trim() ? "담보 입력됨" : "담보 없음"})
            </button>
          </div>
        )}

        {/* STEP NEXT-80: Clarification UI */}
        {clarification && (
          <div className="bg-blue-50 border-t border-blue-200 px-4 py-4">
            <div className="text-blue-900 text-sm font-medium mb-2">
              추가 정보가 필요합니다
            </div>
            {clarification.missing_slots.includes("coverage_names") && clarification.options.coverage_names && (
              <div className="mb-3">
                <div className="text-blue-800 text-xs mb-2">담보를 선택하세요:</div>
                <div className="flex flex-wrap gap-2">
                  {clarification.options.coverage_names.map((coverage: string) => (
                    <button
                      key={coverage}
                      onClick={() => handleClarificationSelect("coverage_names", coverage)}
                      className="px-3 py-1.5 text-sm bg-white border border-blue-300 rounded hover:bg-blue-100 transition-colors"
                    >
                      {coverage}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {clarification.missing_slots.includes("insurers") && clarification.options.insurers && (
              <div>
                {/* STEP NEXT-106: Multi-select for LIMIT_FIND clarification */}
                {isLimitFindClarification ? (
                  <>
                    <div className="text-blue-800 text-xs mb-2">
                      비교를 위해 보험사를 선택하세요 (1개 이상):
                    </div>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {clarification.options.insurers.map((insurerCode: string) => {
                        const insurer = config.available_insurers.find(i => i.code === insurerCode);
                        const isSelected = clarificationSelectedInsurers.includes(insurerCode);
                        return (
                          <button
                            key={insurerCode}
                            onClick={() => {
                              setClarificationSelectedInsurers(prev =>
                                prev.includes(insurerCode)
                                  ? prev.filter(c => c !== insurerCode)
                                  : [...prev, insurerCode]
                              );
                            }}
                            className={`px-3 py-1.5 text-sm border rounded transition-colors ${
                              isSelected
                                ? "bg-blue-600 text-white border-blue-600"
                                : "bg-white text-gray-700 border-blue-300 hover:bg-blue-100"
                            }`}
                          >
                            {insurer?.display || insurerCode}
                          </button>
                        );
                      })}
                    </div>
                    <button
                      onClick={() => {
                        if (clarificationSelectedInsurers.length > 0) {
                          handleClarificationSelect("insurers", clarificationSelectedInsurers);
                        }
                      }}
                      disabled={clarificationSelectedInsurers.length === 0}
                      className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      확인 ({clarificationSelectedInsurers.length}개 선택됨)
                    </button>
                  </>
                ) : (
                  <>
                    <div className="text-blue-800 text-xs mb-2">보험사를 선택하세요:</div>
                    <div className="flex flex-wrap gap-2">
                      {clarification.options.insurers.map((insurer: string) => (
                        <button
                          key={insurer}
                          onClick={() => handleClarificationSelect("insurers", [insurer])}
                          className="px-3 py-1.5 text-sm bg-white border border-blue-300 rounded hover:bg-blue-100 transition-colors"
                        >
                          {insurer}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}

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
