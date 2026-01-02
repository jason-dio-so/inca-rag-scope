/**
 * STEP NEXT-UI-02: API Wrapper (fetch-only)
 * Future: Will be wrapped by SWR in useChat.ts
 *
 * STEP NEXT-73R: Store API added
 */

import { ChatRequest, ChatResponse, ProposalDetailStoreItem, EvidenceStoreItem } from "./types";

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

// STEP NEXT-73R: Store API functions

/**
 * Get proposal detail by ref
 * @param ref - proposal_detail_ref (e.g., "PD:samsung:A4200_1")
 */
export async function getProposalDetail(ref: string): Promise<ProposalDetailStoreItem | null> {
  try {
    const response = await fetch(`${API_BASE}/store/proposal-detail/${encodeURIComponent(ref)}`);

    if (!response.ok) {
      console.error(`[Store API] Proposal detail not found: ${ref}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`[Store API] Error fetching proposal detail ${ref}:`, error);
    return null;
  }
}

/**
 * Get evidence by ref
 * @param ref - evidence_ref (e.g., "EV:samsung:A4200_1:01")
 */
export async function getEvidence(ref: string): Promise<EvidenceStoreItem | null> {
  try {
    const response = await fetch(`${API_BASE}/store/evidence/${encodeURIComponent(ref)}`);

    if (!response.ok) {
      console.error(`[Store API] Evidence not found: ${ref}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`[Store API] Error fetching evidence ${ref}:`, error);
    return null;
  }
}

/**
 * Batch get evidence by refs
 * @param refs - Array of evidence_refs
 */
export async function batchGetEvidence(refs: string[]): Promise<Record<string, EvidenceStoreItem>> {
  try {
    const response = await fetch(`${API_BASE}/store/evidence/batch`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refs }),
    });

    if (!response.ok) {
      console.error(`[Store API] Batch evidence fetch failed`);
      return {};
    }

    return await response.json();
  } catch (error) {
    console.error(`[Store API] Error batch fetching evidence:`, error);
    return {};
  }
}
