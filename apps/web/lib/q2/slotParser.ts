/**
 * Q2 Slot Parser - Deterministic slot extraction from Korean text
 *
 * Purpose: Extract slots (coverage_query, sex, age_band, plan_variant_scope) from user input
 * Rules:
 * - NO LLM, regex-based only
 * - Korean text normalization
 * - Fixed mapping rules
 * - Coverage query extraction
 */

export interface Q2Slots {
  coverage_query?: string;
  sex?: 'M' | 'F';
  age_band?: 30 | 40 | 50;
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

  if (/전체비교|모두|전부|둘다/.test(normalized)) {
    return 'all';
  }

  if (/일반만|일반형만|일반보험|일반으로/.test(normalized)) {
    return 'standard';
  }

  if (/무해지만|무해지형만|무해지보험|무해지로/.test(normalized)) {
    return 'no_refund';
  }

  return null;
}

/**
 * Extract coverage query from text
 * Remove known slot keywords and keep the coverage name
 */
export function extractCoverageQuery(text: string): string | null {
  const cleaned = text
    .replace(/(남|여|남자|여자|남성|여성)/g, '')
    .replace(/(\d+)(대|세|살)/g, '')
    .replace(/(비교|담보|보장한도|한도|차이)/g, '')
    .replace(/(전체|일반|무해지|총납|월납)/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (cleaned && cleaned.length > 1) {
    return cleaned;
  }

  return null;
}

/**
 * Parse all slots from user input
 */
export function parseSlots(text: string, existingSlots?: Q2Slots): Q2Slots {
  const slots: Q2Slots = { ...existingSlots };

  const sex = extractSex(text);
  if (sex) slots.sex = sex;

  const ageBand = extractAgeBand(text);
  if (ageBand) slots.age_band = ageBand;

  const sortBy = extractSortBy(text);
  if (sortBy) slots.sort_by = sortBy;

  const planVariant = extractPlanVariant(text);
  if (planVariant) slots.plan_variant_scope = planVariant;

  // Extract coverage query if not yet set
  if (!slots.coverage_query) {
    const coverageQuery = extractCoverageQuery(text);
    if (coverageQuery) {
      slots.coverage_query = coverageQuery;
    }
  }

  return slots;
}

/**
 * Check if all required slots are filled for execution
 */
export function areSlotsComplete(slots: Q2Slots): boolean {
  // Always need coverage_query, sex, and age_band
  if (!slots.coverage_query || !slots.sex || !slots.age_band) return false;

  return true;
}

/**
 * Get missing slot names for clarification
 */
export function getMissingSlots(slots: Q2Slots): string[] {
  const missing: string[] = [];

  if (!slots.coverage_query) {
    missing.push('coverage_query');
  }

  if (!slots.sex || !slots.age_band) {
    missing.push('sex_age');
  }

  return missing;
}

/**
 * Generate clarification prompt based on missing slots
 */
export function generateClarificationPrompt(slots: Q2Slots): string {
  const missing = getMissingSlots(slots);

  if (missing.includes('coverage_query')) {
    return '비교하고 싶은 담보명을 알려주세요. 예) 암진단비, 암직접입원비, 뇌졸중진단비';
  }

  if (missing.includes('sex_age')) {
    return '연령대와 성별을 알려주세요. 예) 40대 남성, 30대 여성';
  }

  return '정보가 부족합니다. 다시 입력해 주세요.';
}
