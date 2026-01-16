/**
 * STEP NEXT-133: Slot-Driven Clarification UI
 *
 * This module provides utilities to determine what information is missing
 * and should be shown in clarification UI, based on resolved vs missing slots.
 *
 * Constitutional Principles:
 * 1. Resolved Slot Non-Reask: If a slot is resolved, NEVER show UI for it again
 * 2. Dynamic Panel: Only show missing slots, not a fixed form
 * 3. No hardcoded insurer count text
 * 4. Same logic for EX1→EX2/EX3/EX4 entry
 */

import { AssistantMessageVM } from "@/lib/types";

export interface MissingSlots {
  insurers: boolean;
  coverage: boolean;
  disease_subtypes: boolean;
}

export interface ResolvedSlots {
  insurers: string[] | null;
  coverage: string[] | null;
  disease_subtypes: string[] | null;
}

export interface ClarificationState {
  showClarification: boolean;
  missingSlots: MissingSlots;
  resolvedSlots: ResolvedSlots;
  examType: "EX1_DETAIL" | "EX2" | "EX3" | "EX4" | null;
}

interface DeriveClarificationInput {
  // Current draft payload (what user just entered/selected)
  requestPayload: {
    insurers?: string[] | string;
    coverage_names?: string[] | string;
    disease_name?: string;
    message?: string;
  };
  // Last server response
  lastResponseVm?: AssistantMessageVM | null;
  // Last user message text
  lastUserText: string;
  // Conversation context (locked values)
  conversationContext?: {
    lockedInsurers: string[] | null;
    lockedCoverageNames: string[] | null;
  };
}

/**
 * Detect exam type from user message (deterministic)
 *
 * STEP NEXT-138: Added single-insurer explanation detection
 * Priority:
 * 1. EX1_DETAIL: "설명", "알려줘" (single insurer only)
 * 2. EX3: "비교", "차이" (2+ insurers)
 * 3. EX4: disease subtypes
 * 4. EX2: "담보 중", "보장한도가 다른"
 */
function detectExamType(message: string): "EX1_DETAIL" | "EX2" | "EX3" | "EX4" | null {
  const isExplanation = message.includes("설명해") || message.includes("설명") ||
    message.includes("알려줘") || message.includes("알려주세요");
  const isEX2 = message.includes("담보 중") || message.includes("보장한도가 다른");
  const isEX3 = message.includes("비교") || message.includes("차이") || message.includes("VS") || message.includes("vs");
  const isEX4 = message.includes("보장여부") || message.includes("보장내용에 따라") ||
    message.includes("제자리암") || message.includes("경계성종양");

  // STEP NEXT-138: Single-insurer explanation takes priority over comparison
  if (isExplanation && !isEX3) return "EX1_DETAIL";
  if (isEX3) return "EX3";
  if (isEX4) return "EX4";
  if (isEX2) return "EX2";
  return null;
}

/**
 * Parse insurers from user message (STEP NEXT-138)
 */
function parseInsurersFromMessage(message: string): string[] {
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

  const found: string[] = [];
  const seenCodes = new Set<string>();

  for (const [keyword, code] of Object.entries(insurerMap)) {
    if (normalized.includes(keyword) && !seenCodes.has(code)) {
      found.push(code);
      seenCodes.add(code);
    }
  }

  return found;
}

/**
 * Parse coverage names from user message (simple extraction)
 */
function parseCoverageFromMessage(message: string): string[] {
  // Simple heuristic: common coverage keywords
  const coverageKeywords = [
    "암진단비", "암직접입원비", "수술비", "입원비",
    "진단비", "치료비", "통원비"
  ];

  const found: string[] = [];
  for (const keyword of coverageKeywords) {
    if (message.includes(keyword)) {
      found.push(keyword);
    }
  }
  return found;
}

/**
 * Parse disease subtypes from user message (simple extraction)
 */
function parseDiseaseSubtypesFromMessage(message: string): string[] {
  const subtypeKeywords = ["제자리암", "경계성종양", "유사암", "소액암"];
  const found: string[] = [];
  for (const keyword of subtypeKeywords) {
    if (message.includes(keyword)) {
      found.push(keyword);
    }
  }
  return found;
}

/**
 * Derive clarification state based on resolved vs missing slots
 *
 * Priority for determining "resolved":
 * 1. requestPayload (current draft)
 * 2. conversationContext (locked values)
 * 3. lastUserText (parsed values)
 */
export function deriveClarificationState(
  input: DeriveClarificationInput
): ClarificationState {
  const {
    requestPayload,
    lastResponseVm,
    lastUserText,
    conversationContext,
  } = input;

  // Detect exam type
  const examType = detectExamType(lastUserText);

  // STEP NEXT-138: Parse insurers from message (context reset if explicitly mentioned)
  const parsedInsurers = parseInsurersFromMessage(lastUserText);

  // Resolve insurers
  const payloadInsurers = requestPayload.insurers
    ? Array.isArray(requestPayload.insurers)
      ? requestPayload.insurers
      : [requestPayload.insurers]
    : null;

  // STEP NEXT-141-δ: EX4 MUST NOT use context fallback for insurers
  // EX4 preset sets disease_subtypes in message, but insurers MUST be explicitly selected
  // For other exam types, context fallback is allowed
  let resolvedInsurers: string[] | null = null;

  if (examType === "EX4") {
    // STEP NEXT-141-δ: EX4 NO CONTEXT FALLBACK (insurers must be explicit)
    resolvedInsurers = payloadInsurers ?? (parsedInsurers.length > 0 ? parsedInsurers : null);
  } else {
    // STEP NEXT-138: If insurers are explicitly mentioned in message, use those (RESET context)
    // Otherwise, use payload → locked context fallback
    resolvedInsurers =
      payloadInsurers ||
      (parsedInsurers.length > 0 ? parsedInsurers : conversationContext?.lockedInsurers) ||
      null;
  }

  // Resolve coverage
  const payloadCoverage = requestPayload.coverage_names
    ? Array.isArray(requestPayload.coverage_names)
      ? requestPayload.coverage_names
      : [requestPayload.coverage_names]
    : null;

  const parsedCoverage = parseCoverageFromMessage(lastUserText);

  const resolvedCoverage =
    payloadCoverage ||
    conversationContext?.lockedCoverageNames ||
    (parsedCoverage.length > 0 ? parsedCoverage : null);

  // Resolve disease subtypes (EX4 only)
  const parsedSubtypes = parseDiseaseSubtypesFromMessage(lastUserText);
  const resolvedSubtypes = parsedSubtypes.length > 0 ? parsedSubtypes : null;

  // Determine missing slots based on exam type
  let missingInsurers = false;
  let missingCoverage = false;
  let missingSubtypes = false;

  if (examType === "EX1_DETAIL") {
    // STEP NEXT-138: EX1_DETAIL (explanation) requires 1 insurer + 1 coverage
    // If coverage is resolved, only insurer might be missing
    missingInsurers = !resolvedInsurers || resolvedInsurers.length === 0;
    missingCoverage = !resolvedCoverage || resolvedCoverage.length === 0;
  } else if (examType === "EX3") {
    // EX3 requires 2 insurers + 1 coverage
    missingInsurers = !resolvedInsurers || resolvedInsurers.length < 2;
    missingCoverage = !resolvedCoverage || resolvedCoverage.length === 0;
  } else if (examType === "EX2") {
    // STEP NEXT-133: EXAM2 NEVER shows clarification UI
    // EXAM2 is self-contained: auto-expand insurers, proceed with coverage from message
    missingInsurers = false;  // ABSOLUTE: EXAM2 never requires insurer selection
    missingCoverage = false;  // ABSOLUTE: EXAM2 never requires coverage re-input
  } else if (examType === "EX4") {
    // STEP NEXT-141-ζ: EX4 requires 1+ insurers + disease subtypes ONLY
    // EX4 uses disease_subtypes (질병 서브타입), NOT coverage (담보)
    // Coverage slot MUST NOT gate EX4 clarification
    missingInsurers = !resolvedInsurers || resolvedInsurers.length === 0;
    missingSubtypes = !resolvedSubtypes || resolvedSubtypes.length === 0;
    missingCoverage = false;  // ABSOLUTE: EX4 never requires coverage
  }

  // Show clarification if ANY slot is missing
  const showClarification = missingInsurers || missingCoverage || missingSubtypes;

  // STEP NEXT-141-ζζ: Debug logging for EX4 coverage slot issue
  if (examType === "EX4") {
    console.log("[clarificationUtils EX4 RETURN]", {
      examType,
      missingInsurers,
      missingCoverage,  // Should be false
      missingSubtypes,
      resolvedInsurers,
      resolvedCoverage,
      resolvedSubtypes,
    });
  }

  return {
    showClarification,
    missingSlots: {
      insurers: missingInsurers,
      coverage: missingCoverage,
      disease_subtypes: missingSubtypes,
    },
    resolvedSlots: {
      insurers: resolvedInsurers,
      coverage: resolvedCoverage,
      disease_subtypes: resolvedSubtypes,
    },
    examType,
  };
}
