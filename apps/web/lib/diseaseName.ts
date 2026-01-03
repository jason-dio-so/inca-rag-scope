/**
 * STEP NEXT-86: Disease name extraction utility (deterministic)
 *
 * Rules:
 * - NO LLM
 * - Conservative: Only extract when keyword is clearly present
 * - Priority order: 제자리암 > 경계성종양 > 유사암 > 기타피부암 > 갑상선암 > 대장점막내암
 */

const DISEASE_KEYWORDS = [
  "제자리암",
  "경계성종양",
  "유사암",
  "기타피부암",
  "갑상선암",
  "대장점막내암"
] as const;

/**
 * Extract disease_name from user message (deterministic)
 *
 * @param message User input message
 * @returns Extracted disease name or null if not found
 */
export function extractDiseaseName(message: string): string | null {
  if (!message) return null;

  const normalized = message.trim();

  // Check each keyword in priority order
  for (const keyword of DISEASE_KEYWORDS) {
    if (normalized.includes(keyword)) {
      return keyword;
    }
  }

  return null;
}
