/**
 * STEP NEXT-126: EX3_COMPARE Fixed Bubble Template
 *
 * CONSTITUTIONAL RULE:
 * - EX3_COMPARE bubble MUST use this fixed 6-line template
 * - NO data-driven variation allowed
 * - NO summary_bullets/title/bubble_markdown from backend
 *
 * PURPOSE:
 * - Same input → same bubble (reproducibility)
 * - Predictable UX for customer testing
 */

import { getInsurerDisplayName } from "./contextUtils";

/**
 * Generate fixed 6-line EX3_COMPARE bubble template
 *
 * @param insurer1Code - First insurer code (e.g., "samsung")
 * @param insurer2Code - Second insurer code (e.g., "meritz")
 * @returns Fixed 6-line markdown template
 */
export function buildEX3FixedBubble(insurer1Code: string, insurer2Code: string): string {
  const insurer1 = getInsurerDisplayName(insurer1Code);
  const insurer2 = getInsurerDisplayName(insurer2Code);

  return `${insurer1}는 진단 시 **정해진 금액을 지급하는 구조**이고,
${insurer2}는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**

**즉,**
- ${insurer1}: 지급 금액이 명확한 정액 구조
- ${insurer2}: 지급 조건 해석이 중요한 한도 구조`;
}

/**
 * Extract insurer codes from EX3_COMPARE response
 * Priority: requestPayload.insurers (most reliable)
 *
 * @param requestPayload - Original request payload
 * @returns Array of insurer codes [insurer1, insurer2]
 */
export function extractInsurerCodesForEX3(requestPayload: any): [string, string] | null {
  // Priority 1: Request payload (SSOT)
  if (requestPayload?.insurers && Array.isArray(requestPayload.insurers)) {
    if (requestPayload.insurers.length >= 2) {
      return [requestPayload.insurers[0], requestPayload.insurers[1]];
    }
  }

  // Fallback: Cannot extract
  return null;
}
