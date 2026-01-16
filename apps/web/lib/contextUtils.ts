/**
 * STEP NEXT-102: EX2 Context Continuity Utils
 *
 * Deterministic pattern matching for:
 * - Insurer switch detection ("메리츠는?")
 * - LIMIT_FIND pattern detection ("보장한도가 다른 상품 찾아줘")
 */

/**
 * Detect if message is an insurer switch utterance
 * Examples: "메리츠는?", "메리츠는요?", "메리츠도", "그럼 메리츠", "메리츠화재는?"
 */
export function isInsurerSwitchUtterance(message: string): boolean {
  if (!message) return false;

  const normalized = message.trim().toLowerCase();

  // Pattern 1: "[보험사명]는?" / "[보험사명]는요?" / "[보험사명]는요"
  const patterns = [
    /^(메리츠|삼성|한화|현대|kb|롯데|흥국|홍국)(\s*화재)?(\s*는요?|\s*는|\s*도|\s*는요|\s*는지)?\??$/,
    /^그럼\s+(메리츠|삼성|한화|현대|kb|롯데|흥국|홍국)(\s*화재)?(\s*는요?|\s*는|\s*도)?\??$/,
    /^(메리츠|삼성|한화|현대|kb|롯데|흥국|홍국)(\s*화재)?\s*상품(\s*은|\s*는)?\??$/,
  ];

  return patterns.some(pattern => pattern.test(normalized));
}

/**
 * Extract insurer code from switch utterance
 * Returns insurer code (e.g., "meritz", "samsung") or null
 */
export function extractInsurerFromSwitch(message: string): string | null {
  if (!message) return null;

  const normalized = message.trim().toLowerCase();

  const insurerMap: Record<string, string> = {
    '메리츠': 'meritz',
    '삼성': 'samsung',
    '한화': 'hanwha',
    '현대': 'hyundai',
    'kb': 'kb',
    '롯데': 'lotte',
    '흥국': 'heungkuk',
    '홍국': 'heungkuk',
  };

  for (const [keyword, code] of Object.entries(insurerMap)) {
    if (normalized.includes(keyword)) {
      return code;
    }
  }

  return null;
}

/**
 * Detect if message is a LIMIT_FIND pattern
 * Examples: "다른 담보", "보장한도가 다른", "차이 찾아줘"
 */
export function isLimitFindPattern(message: string): boolean {
  if (!message) return false;

  const normalized = message.trim().toLowerCase();

  // Pattern: mentions "다른" + "담보/상품/보장" + "한도/차이/찾"
  const keywords = {
    diff: ['다른', '차이', '비교'],
    target: ['담보', '상품', '보장'],
    action: ['한도', '찾', '알려'],
  };

  const hasDiff = keywords.diff.some(k => normalized.includes(k));
  const hasTarget = keywords.target.some(k => normalized.includes(k));
  const hasAction = keywords.action.some(k => normalized.includes(k));

  // Need at least 2 out of 3 categories
  const matchCount = [hasDiff, hasTarget, hasAction].filter(Boolean).length;

  return matchCount >= 2;
}

/**
 * Get insurer display name for UI
 */
export function getInsurerDisplayName(code: string): string {
  const displayMap: Record<string, string> = {
    'samsung': '삼성화재',
    'meritz': '메리츠화재',
    'hanwha': '한화손해보험',
    'hyundai': '현대해상',
    'kb': 'KB손해보험',
    'lotte': '롯데손해보험',
    'heungkuk': '흥국화재',
  };

  return displayMap[code] || code;
}

/**
 * STEP NEXT-121: Extract insurer codes from natural language message
 * Deterministic pattern matching for all known insurers
 */
export function extractInsurersFromMessage(message: string): string[] {
  if (!message) return [];

  const normalized = message.trim().toLowerCase();

  const insurerMap: Record<string, string> = {
    '삼성화재': 'samsung',
    '삼성': 'samsung',
    '메리츠화재': 'meritz',
    '메리츠': 'meritz',
    '한화손해보험': 'hanwha',
    '한화': 'hanwha',
    '현대해상': 'hyundai',
    '현대': 'hyundai',
    'kb손해보험': 'kb',
    'kb': 'kb',
    '롯데손해보험': 'lotte',
    '롯데': 'lotte',
    '흥국화재': 'heungkuk',
    '흥국': 'heungkuk',
    '홍국화재': 'heungkuk',
    '홍국': 'heungkuk',
  };

  const foundInsurers: string[] = [];
  const seenCodes = new Set<string>();

  // Extract all matching insurers (dedupe by code)
  for (const [keyword, code] of Object.entries(insurerMap)) {
    if (normalized.includes(keyword) && !seenCodes.has(code)) {
      foundInsurers.push(code);
      seenCodes.add(code);
    }
  }

  return foundInsurers;
}

/**
 * STEP NEXT-121: Extract coverage name from natural language message
 * Deterministic pattern matching for known coverage keywords
 */
export function extractCoverageNameFromMessage(message: string): string | null {
  if (!message) return null;

  const normalized = message.trim().toLowerCase();

  // Coverage keyword patterns (longest first for better matching)
  const coveragePatterns = [
    { keywords: ['암진단비(유사암제외)', '암진단비(유사암 제외)'], canonical: '암진단비(유사암제외)' },
    { keywords: ['암진단비', '암 진단비'], canonical: '암진단비' },
    { keywords: ['암직접입원비', '암 직접 입원비', '암직접 입원비'], canonical: '암직접입원비' },
    { keywords: ['암수술비', '암 수술비'], canonical: '암수술비' },
    { keywords: ['뇌출혈진단비', '뇌출혈 진단비'], canonical: '뇌출혈진단비' },
    { keywords: ['급성심근경색진단비', '급성심근경색 진단비'], canonical: '급성심근경색진단비' },
  ];

  // Find first matching pattern
  for (const pattern of coveragePatterns) {
    for (const keyword of pattern.keywords) {
      if (normalized.includes(keyword)) {
        return pattern.canonical;
      }
    }
  }

  return null;
}

/**
 * STEP NEXT-121 FINAL: Detect comparison intent (HARD-LOCK)
 *
 * RULE 1 — Comparison Intent Detection:
 * - insurers >= 2
 * - message contains comparison words (비교, 차이, 다른, vs, 와/과)
 * - message contains coverage keywords
 *
 * When TRUE: Force EX3_COMPARE, NO coverage selection UI, NO need_more_info
 */
export function isComparisonIntent(message: string, insurersCount: number): boolean {
  if (!message || insurersCount < 2) return false;

  const normalized = message.trim().toLowerCase();

  // Comparison keywords
  const comparisonKeywords = [
    '비교', '차이', '다른', '다르', 'vs', '대',
    '어떤 게', '어떤게', '어느', '뭐가', '무엇이'
  ];

  // Check if message contains comparison intent
  const hasComparisonKeyword = comparisonKeywords.some(k => normalized.includes(k));

  // Check if message contains "와/과" (comparison particles)
  const hasComparisonParticle = /[와과]/.test(normalized);

  // Check if message contains coverage keyword
  const hasCoverageKeyword = extractCoverageNameFromMessage(message) !== null;

  // HARD-LOCK: If insurers >= 2 AND (comparison keyword OR particle) AND coverage keyword
  // → Force comparison intent
  return hasCoverageKeyword && (hasComparisonKeyword || hasComparisonParticle);
}
