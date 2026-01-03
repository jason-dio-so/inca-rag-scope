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
import { extractDiseaseName } from "@/lib/diseaseName";  // STEP NEXT-86
import {
  isInsurerSwitchUtterance,
  extractInsurerFromSwitch,
  isLimitFindPattern,
  getInsurerDisplayName,
} from "@/lib/contextUtils";  // STEP NEXT-102
import SidebarCategories from "@/components/SidebarCategories";
import ChatPanel from "@/components/ChatPanel";
import ResultDock from "@/components/ResultDock";
import LlmModeToggle from "@/components/LlmModeToggle";

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

  // STEP NEXT-101: Conversation context carryover
  const [conversationContext, setConversationContext] = useState<ConversationContext>({
    lockedInsurers: null,
    lockedCoverageNames: null,
    isLocked: false,
  });

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

  // STEP NEXT-80-FE: Send with explicit kind (accepts overrides for example buttons)
  const handleSendWithKind = async (
    kind: MessageKind,
    messageOverride?: string,
    insurersOverride?: string[],
    coverageNamesOverride?: string[]
  ) => {
    const messageToSend = messageOverride || input;
    if (!messageToSend.trim() || !config) return;

    setError(null);

    // STEP NEXT-101: Sync UI state when example button clicked
    if (insurersOverride) {
      setSelectedInsurers(insurersOverride);
    }
    if (coverageNamesOverride && coverageNamesOverride.length > 0) {
      setCoverageInput(coverageNamesOverride.join(", "));
    }

    const userMessage: Message = {
      role: "user",
      content: messageToSend,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // STEP NEXT-86: Auto-fill disease_name for EX4_ELIGIBILITY from message
      let diseaseNameToSend: string | undefined = undefined;
      if (kind === "EX4_ELIGIBILITY") {
        diseaseNameToSend = extractDiseaseName(messageToSend) || undefined;
      }

      // STEP NEXT-101: Use buildChatPayload SSOT
      const requestPayload = buildChatPayload(
        messageToSend,
        kind,
        insurersOverride,
        coverageNamesOverride,
        diseaseNameToSend
      );

      console.log("[page.tsx handleSendWithKind] Request payload:", requestPayload);

      const response = await postChat(requestPayload);

      console.log("[page.tsx] Chat response:", response);

      // Validate response structure
      if (!response || typeof response !== "object") {
        throw new Error("Invalid response from server");
      }

      // STEP NEXT-80: Handle need_more_info (NOT an error)
      if (response.need_more_info === true) {
        // Clarification needed - show slot selection UI
        setClarification({
          missing_slots: response.missing_slots || [],
          options: response.clarification_options || {},
          draftRequest: requestPayload,
        });
        return; // Don't show as error
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
        // No message field AND not a clarification request = truly empty
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
          console.log("[page.tsx handleSendWithKind] Locked conversation context:", {
            insurers: requestPayload.insurers,
            coverage_names: requestPayload.coverage_names,
          });
        }

        // STEP NEXT-81B: Use bubble_markdown if available, otherwise build from title+bullets
        let summaryText: string;
        if (vm?.bubble_markdown) {
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

  const handleSend = async () => {
    if (!input.trim() || !config) return;

    setError(null);

    // STEP NEXT-101: Capture message before clearing input
    const messageToSend = input;

    // STEP NEXT-103: Detect insurer switch BEFORE payload generation
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

    // STEP NEXT-102: Detect LIMIT_FIND pattern and validate multi-insurer requirement
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
      // STEP NEXT-103: Use buildChatPayload with effective overrides (insurer switch)
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

      // STEP NEXT-101: Handle need_more_info (show clarification UI)
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

        // STEP NEXT-81B: Use bubble_markdown if available, otherwise build from title+bullets
        let summaryText: string;
        if (vm?.bubble_markdown) {
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

    // Clear clarification state
    setClarification(null);
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
              onSendWithKind={handleSendWithKind}
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
