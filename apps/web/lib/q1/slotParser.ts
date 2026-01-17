/**
 * Q1 Slot Parser - Deterministic slot extraction from Korean text
 *
 * Purpose: Extract slots (sex, age_band, premium_mode) from user input
 * Rules:
 * - NO LLM, regex-based only
 * - Korean text normalization
 * - Fixed mapping rules
 */

export interface Q1Slots {
  sex?: 'M' | 'F';
  age_band?: 30 | 40 | 50;
  premium_mode?: 'TOTAL' | 'BY_COVERAGE';
  coverage_query_text?: string;
  sort_by?: 'total' | 'monthly';
  plan_variant_scope?: 'all' | 'standard' | 'no_refund';
}

/**
 * Normalize Korean text for matching
 */
function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[^\w가-힣]/g, '');
}

/**
 * Extract sex from text
 */
export function extractSex(text: string): 'M' | 'F' | null {
  const normalized = normalize(text);

  // Male patterns
  if (/남|남자|남성|male|m(?![a-z])/.test(normalized)) {
    return 'M';
  }

  // Female patterns
  if (/여|여자|여성|female|f(?![a-z])/.test(normalized)) {
    return 'F';
  }

  return null;
}

/**
 * Extract age band from text
 * Maps actual ages to nearest band: 30/40/50
 */
export function extractAgeBand(text: string): 30 | 40 | 50 | null {
  const normalized = normalize(text);

  // Direct band mention (e.g., "30대", "40대")
  if (/30대/.test(normalized)) return 30;
  if (/40대/.test(normalized)) return 40;
  if (/50대/.test(normalized)) return 50;

  // Specific age (e.g., "35세", "42", "48살")
  const ageMatch = normalized.match(/(\d{2})(?:세|살|년|대)?/);
  if (ageMatch) {
    const age = parseInt(ageMatch[1], 10);

    // Map to nearest band
    if (age >= 20 && age <= 34) return 30;
    if (age >= 35 && age <= 44) return 40;
    if (age >= 45 && age <= 80) return 50;
  }

  return null;
}

/**
 * Extract premium mode from text
 */
export function extractPremiumMode(text: string): 'TOTAL' | 'BY_COVERAGE' | null {
  const normalized = normalize(text);

  // TOTAL patterns
  if (/전체|총|total|전체보험료|총보험료/.test(normalized)) {
    return 'TOTAL';
  }

  // BY_COVERAGE patterns
  if (/담보|coverage|담보별|담보기준/.test(normalized)) {
    return 'BY_COVERAGE';
  }

  return null;
}

/**
 * Extract sort preference from text
 */
export function extractSortBy(text: string): 'total' | 'monthly' | null {
  const normalized = normalize(text);

  if (/총납|총납입|전체납입/.test(normalized)) {
    return 'total';
  }

  if (/월납|월보험료|매월/.test(normalized)) {
    return 'monthly';
  }

  return null;
}

/**
 * Extract plan variant scope from text
 */
export function extractPlanVariant(text: string): 'all' | 'standard' | 'no_refund' | null {
  const normalized = normalize(text);

  if (/전체비교|모두|전부/.test(normalized)) {
    return 'all';
  }

  if (/일반만|일반형만|일반보험/.test(normalized)) {
    return 'standard';
  }

  if (/무해지만|무해지형만|무해지보험/.test(normalized)) {
    return 'no_refund';
  }

  return null;
}

/**
 * Parse all slots from user input
 */
export function parseSlots(text: string, existingSlots?: Q1Slots): Q1Slots {
  const slots: Q1Slots = { ...existingSlots };

  const sex = extractSex(text);
  if (sex) slots.sex = sex;

  const ageBand = extractAgeBand(text);
  if (ageBand) slots.age_band = ageBand;

  const premiumMode = extractPremiumMode(text);
  if (premiumMode) slots.premium_mode = premiumMode;

  const sortBy = extractSortBy(text);
  if (sortBy) slots.sort_by = sortBy;

  const planVariant = extractPlanVariant(text);
  if (planVariant) slots.plan_variant_scope = planVariant;

  // If premium_mode is BY_COVERAGE and we haven't extracted coverage yet,
  // store the raw text for coverage resolution
  if (slots.premium_mode === 'BY_COVERAGE' && !slots.coverage_query_text) {
    // Try to extract coverage name from text
    // Simple heuristic: remove known slot keywords and keep the rest
    const cleaned = text
      .replace(/(남|여|남자|여자|남성|여성)/g, '')
      .replace(/(\d+)(대|세|살)/g, '')
      .replace(/(담보별|담보|coverage)/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    if (cleaned && cleaned.length > 1) {
      slots.coverage_query_text = cleaned;
    }
  }

  return slots;
}

/**
 * Check if all required slots are filled for execution
 */
export function areSlotsComplete(slots: Q1Slots): boolean {
  // Always need sex and age_band
  if (!slots.sex || !slots.age_band) return false;

  // Always need premium_mode
  if (!slots.premium_mode) return false;

  // If BY_COVERAGE, need coverage_query_text
  if (slots.premium_mode === 'BY_COVERAGE' && !slots.coverage_query_text) {
    return false;
  }

  return true;
}

/**
 * Get missing slot names for clarification
 */
export function getMissingSlots(slots: Q1Slots): string[] {
  const missing: string[] = [];

  if (!slots.sex || !slots.age_band) {
    missing.push('sex_age');
  }

  if (!slots.premium_mode) {
    missing.push('premium_mode');
  }

  if (slots.premium_mode === 'BY_COVERAGE' && !slots.coverage_query_text) {
    missing.push('coverage_query_text');
  }

  return missing;
}

/**
 * Generate clarification prompt based on missing slots
 */
export function generateClarificationPrompt(slots: Q1Slots): string {
  const missing = getMissingSlots(slots);

  if (missing.includes('sex_age')) {
    return '연령대와 성별을 알려주세요. 예) 40대 남성, 30대 여성';
  }

  if (missing.includes('premium_mode')) {
    return '비교 기준을 선택해주세요:\n(1) 전체보험료\n(2) 담보별 보험료';
  }

  if (missing.includes('coverage_query_text')) {
    return '어떤 담보 기준으로 비교할까요? 예) 암진단비, 뇌졸중진단비, 입원일당';
  }

  return '정보가 부족합니다. 다시 입력해 주세요.';
}
