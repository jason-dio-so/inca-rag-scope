/**
 * STEP NEXT-UI-02: API Wrapper (fetch-only)
 * Future: Will be wrapped by SWR in useChat.ts
 */

import { ChatRequest, ChatResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(req),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        ok: false,
        error: {
          message: `HTTP ${response.status}: ${response.statusText}`,
          detail: errorData.detail || JSON.stringify(errorData),
        },
      };
    }

    // Backend already returns ChatResponse shape, return it directly
    const data = await response.json();
    return data;
  } catch (error) {
    return {
      ok: false,
      error: {
        message: error instanceof Error ? error.message : "Unknown error",
        detail: "네트워크 오류가 발생했습니다. API 서버가 실행 중인지 확인하세요.",
      },
    };
  }
}

export async function fetchUIConfig() {
  const response = await fetch("/ui_config.json");
  return response.json();
}
