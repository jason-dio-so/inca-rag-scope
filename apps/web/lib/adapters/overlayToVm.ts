/**
 * STEP DEMO-LAUNCHER-FIX-01: Overlay to VM Adapter
 *
 * PURPOSE:
 * - Convert overlay JSON responses (query_id/items/...) to AssistantMessageVM (kind/title/sections)
 * - Enable ResultDock to render overlay results
 *
 * CONSTITUTIONAL:
 * - Evidence-first: Preserve all evidence (doc_type/page/excerpt)
 * - No inference: UNKNOWN if no evidence
 * - No backend changes
 */

import { AssistantMessageVM } from "@/lib/types";

/**
 * STEP DEMO-EVIDENCE-RELEVANCE-01: Evidence filtering and ranking utilities
 */

// Dedup evidence by (doc_type, page, excerpt)
function dedupEvidences(evidences: any[]): any[] {
  const seen = new Set<string>();
  return evidences.filter((ev) => {
    const key = `${ev.doc_type || ""}|${ev.page || ""}|${(ev.excerpt || "").substring(0, 100)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// Calculate relevance score for evidence based on slot keywords
function calculateRelevanceScore(evidence: any, slotKeywords: string[], docTypePriority: Record<string, number>): number {
  let score = 0;
  const excerpt = (evidence.excerpt || "").toLowerCase();

  // Keyword matching (highest weight)
  for (const keyword of slotKeywords) {
    if (excerpt.includes(keyword.toLowerCase())) {
      score += 100;
    }
  }

  // Doc type priority (medium weight)
  const docType = evidence.doc_type || "";
  score += docTypePriority[docType] || 0;

  // Page number (lower is better, small weight)
  const page = evidence.page || 999;
  score -= page * 0.1;

  return score;
}

// Filter and rank evidences for a specific slot
function filterAndRankEvidences(
  evidences: any[],
  slotName: string,
  maxCount: number = 1
): any[] {
  if (!evidences || evidences.length === 0) return [];

  // Dedup first
  const deduped = dedupEvidences(evidences);

  // Define slot-specific keywords
  const slotKeywords: Record<string, string[]> = {
    duration_limit_days: ["180일", "1일-180일", "~180일", "한도", "90일", "일한도"],
    daily_benefit_amount_won: ["2만원", "10,000원", "1일당", "일당", "만원", "원"],
  };

  // Define doc type priority
  const docTypePriority: Record<string, number> = {
    "가입설계서": 40,
    "사업방법서": 30,
    "약관": 20,
    "상품요약서": 10,
  };

  const keywords = slotKeywords[slotName] || [];

  // Score and sort
  const scored = deduped.map((ev) => ({
    evidence: ev,
    score: calculateRelevanceScore(ev, keywords, docTypePriority),
  }));

  scored.sort((a, b) => b.score - a.score);

  // Trim excerpts to 240-320 chars
  const topN = scored.slice(0, maxCount).map((item) => {
    const ev = { ...item.evidence };
    if (ev.excerpt && ev.excerpt.length > 320) {
      ev.excerpt = ev.excerpt.substring(0, 320) + "...";
    }
    return ev;
  });

  return topN;
}

/**
 * Main adapter: Detect overlay response and convert to VM
 */
export function overlayToVm(payload: any): AssistantMessageVM {
  // Check if this is an overlay response
  if (!payload || typeof payload !== "object") {
    throw new Error("Invalid overlay payload");
  }

  // If already has VM structure (kind/sections), return as-is
  if (payload.kind && Array.isArray(payload.sections)) {
    return payload as AssistantMessageVM;
  }

  // Detect overlay by query_id presence
  if (!payload.query_id) {
    throw new Error("Overlay payload missing query_id");
  }

  const queryId = payload.query_id;

  // Route to specific converter
  switch (queryId) {
    case "Q11":
      return convertQ11ToVm(payload);
    case "Q13":
      return convertQ13ToVm(payload);
    case "Q5":
      return convertQ5ToVm(payload);
    case "Q7":
      return convertQ7ToVm(payload);
    case "Q8":
      return convertQ8ToVm(payload);
    default:
      return convertGenericOverlayToVm(payload);
  }
}

/**
 * Q11: Cancer Direct Treatment Hospitalization Daily Benefit
 * STEP DEMO-Q11-POLISH-01: Deduplicate, merge references, show product names
 */
function convertQ11ToVm(payload: any): AssistantMessageVM {
  const items = payload.items || [];
  const references = payload.references || [];
  const coverageName = items[0]?.coverage_name || "암직접치료입원일당";

  // STEP DEMO-Q11-POLISH-01: Deduplicate items by insurer_key
  // Priority: evidence exists > no evidence, FOUND > other statuses
  const itemsByInsurer = new Map<string, any>();

  for (const item of items) {
    const key = item.insurer_key;
    if (!itemsByInsurer.has(key)) {
      itemsByInsurer.set(key, item);
    } else {
      const existing = itemsByInsurer.get(key);

      // Check priority: evidence first
      const itemHasEvidence = !!item.evidence;
      const existingHasEvidence = !!existing.evidence;

      if (itemHasEvidence && !existingHasEvidence) {
        itemsByInsurer.set(key, item);
      } else if (itemHasEvidence && existingHasEvidence) {
        // Both have evidence, check FOUND status
        const itemIsFOUND = item.daily_benefit_amount_won?.status === "FOUND";
        const existingIsFOUND = existing.daily_benefit_amount_won?.status === "FOUND";

        if (itemIsFOUND && !existingIsFOUND) {
          itemsByInsurer.set(key, item);
        }
      }
    }
  }

  // Merge references into items (as separate rows)
  const allItems = [...itemsByInsurer.values(), ...references];

  // Build table rows
  const rows = allItems.map((item: any) => {
    const insurerKey = item.insurer_key || "UNKNOWN";
    const insurerDisplay = getInsurerDisplay(insurerKey);

    // STEP Q11-PRODUCT-NAME-FIX-01: Extract product name from backend (string only)
    const productName = item.product_full_name?.value || "상품명 확인 불가";

    // Check if this is a reference item
    const isReference = item.badge === "REFERENCE_ONLY_NOT_IN_PROPOSAL";
    const referenceLabel = isReference ? " (참조)" : "";

    const durationLimit = item.duration_limit_days?.value ?? item.duration_limit_days ?? "확인 불가";
    const dailyBenefit = item.daily_benefit_amount_won?.value
      ? `${item.daily_benefit_amount_won.value.toLocaleString()}원`
      : item.daily_benefit_amount_won ?? "확인 불가";

    // STEP DEMO-EVIDENCE-RELEVANCE-01: Filter and rank evidence per slot
    const durationEvidences = filterAndRankEvidences(
      item.duration_limit_days?.evidences || [],
      "duration_limit_days",
      1  // top-1 only
    );

    const benefitEvidences = filterAndRankEvidences(
      item.daily_benefit_amount_won?.evidences || [],
      "daily_benefit_amount_won",
      1  // top-1 only
    );

    // Product name evidence (for row-level meta)
    const productEvidences = [];
    if (item.product_full_name?.evidence && Object.keys(item.product_full_name.evidence).length > 0) {
      productEvidences.push(item.product_full_name.evidence);
    }

    return {
      label: `${insurerDisplay}${referenceLabel}`,
      values: [
        // Cell 0: Duration limit with slot-specific evidence
        {
          text: `${durationLimit}일`,
          evidences: durationEvidences.length > 0 ? durationEvidences : undefined,
          slotName: "duration_limit_days",
        },
        // Cell 1: Daily benefit with slot-specific evidence
        {
          text: dailyBenefit,
          evidences: benefitEvidences.length > 0 ? benefitEvidences : undefined,
          slotName: "daily_benefit_amount_won",
        },
      ],
      meta: {
        productName: productName,  // STEP Q11-PRODUCT-NAME-FIX-01: Store as string
        note: isReference ? item.note : undefined,
        productEvidences: productEvidences.length > 0 ? productEvidences : undefined,  // STEP DEMO-EVIDENCE-RELEVANCE-01: Product evidence for label cell
      },
    };
  });

  return {
    kind: "Q11_OVERLAY",
    title: `${coverageName} 비교`,
    summary_bullets: [
      "암 직접치료 입원 시 1일당 지급액 비교",
      "보장 기간 한도(일수) 확인",
    ],
    sections: [
      {
        kind: "comparison_table",
        table_kind: "COVERAGE_DETAIL",
        title: `${coverageName}`,
        columns: ["보험사", "보장 한도(일)", "1일당 지급액"],
        rows: rows,
      },
    ],
  };
}

/**
 * Q13: Cancer Subtype Coverage Matrix
 */
function convertQ13ToVm(payload: any): AssistantMessageVM {
  // Q13 already returns VM-compatible structure from backend
  // Just ensure it has required fields
  return {
    kind: "Q13_OVERLAY",
    title: payload.title || "암 세부 유형 보장 매트릭스",
    summary_bullets: payload.summary_bullets || [
      "제자리암, 경계성종양 보장 여부 확인",
    ],
    sections: payload.sections || [],
  };
}

/**
 * Q5: Waiting Period by Coverage
 */
function convertQ5ToVm(payload: any): AssistantMessageVM {
  const items = payload.items || [];

  const rows = items.map((item: any) => {
    const insurerKey = item.insurer || "UNKNOWN";
    const insurerDisplay = getInsurerDisplay(insurerKey);

    const waitingPeriod = item.waiting_period_days ?? "확인 불가";

    // Collect evidences - STEP DEMO-EVIDENCE-VIS-01: Store actual objects
    const evidences = item.evidence_refs || item.evidences || [];

    return {
      label: insurerDisplay,
      values: [
        item.coverage_name || "확인 불가",
        `${waitingPeriod}일`,
      ],
      meta: {
        evidences: evidences.length > 0 ? evidences : undefined,
      },
    };
  });

  return {
    kind: "Q5_OVERLAY",
    title: "담보별 대기 기간 비교",
    summary_bullets: [
      "계약 후 보장 개시까지 대기 기간 확인",
    ],
    sections: [
      {
        kind: "comparison_table",
        table_kind: "COVERAGE_DETAIL",
        title: "대기 기간",
        columns: ["보험사", "담보명", "대기 기간"],
        rows: rows,
      },
    ],
  };
}

/**
 * Q7: Premium Waiver Policy
 */
function convertQ7ToVm(payload: any): AssistantMessageVM {
  const items = payload.items || [];

  const rows = items.map((item: any) => {
    const insurerKey = item.insurer || "UNKNOWN";
    const insurerDisplay = getInsurerDisplay(insurerKey);

    const waiverCondition = item.waiver_condition || "확인 불가";

    // Collect evidences - STEP DEMO-EVIDENCE-VIS-01: Store actual objects
    const evidences = item.evidence_refs || item.evidences || [];

    return {
      label: insurerDisplay,
      values: [
        waiverCondition,
      ],
      meta: {
        evidences: evidences.length > 0 ? evidences : undefined,
      },
    };
  });

  return {
    kind: "Q7_OVERLAY",
    title: "보험료 납입 면제 조건 비교",
    summary_bullets: [
      "장해, 암 진단 등으로 보험료 납입 면제되는 조건 확인",
    ],
    sections: [
      {
        kind: "comparison_table",
        table_kind: "COVERAGE_DETAIL",
        title: "납입 면제 조건",
        columns: ["보험사", "면제 조건"],
        rows: rows,
      },
    ],
  };
}

/**
 * Q8: Surgery Repeat Payment Policy
 */
function convertQ8ToVm(payload: any): AssistantMessageVM {
  const items = payload.items || [];

  const rows = items.map((item: any) => {
    const insurerKey = item.insurer || "UNKNOWN";
    const insurerDisplay = getInsurerDisplay(insurerKey);

    const repeatPolicy = item.repeat_payment_policy || "확인 불가";

    // Collect evidences - STEP DEMO-EVIDENCE-VIS-01: Store actual objects
    const evidences = item.evidence_refs || item.evidences || [];

    return {
      label: insurerDisplay,
      values: [
        repeatPolicy,
      ],
      meta: {
        evidences: evidences.length > 0 ? evidences : undefined,
      },
    };
  });

  return {
    kind: "Q8_OVERLAY",
    title: "수술비 반복 지급 정책 비교",
    summary_bullets: [
      "동일 부위 재수술 시 지급 여부 확인",
    ],
    sections: [
      {
        kind: "comparison_table",
        table_kind: "COVERAGE_DETAIL",
        title: "반복 지급 정책",
        columns: ["보험사", "반복 지급 정책"],
        rows: rows,
      },
    ],
  };
}

/**
 * Generic fallback for unknown overlay types
 */
function convertGenericOverlayToVm(payload: any): AssistantMessageVM {
  return {
    kind: "OVERLAY_GENERIC",
    title: `${payload.query_id || "Overlay"} 결과`,
    summary_bullets: [
      "Overlay 응답 (자동 변환됨)",
    ],
    sections: [
      {
        kind: "common_notes",
        title: "Raw Data",
        bullets: [
          JSON.stringify(payload, null, 2).substring(0, 500) + "...",
        ],
      },
    ],
  };
}

/**
 * Helper: Get insurer display name from key
 */
function getInsurerDisplay(key: string): string {
  const mapping: Record<string, string> = {
    kb: "KB손해보험",
    samsung: "삼성화재",
    hyundai: "현대해상",
    db: "DB손해보험",
    meritz: "메리츠화재",
    hanwha: "한화손해보험",
    heungkuk: "흥국화재",
    lotte: "롯데손해보험",
  };

  return mapping[key.toLowerCase()] || key.toUpperCase();
}
