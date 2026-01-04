/**
 * STEP NEXT-132: EX3 Report Types (EXAM3 Report View v0)
 *
 * PURPOSE:
 * - Customer-requested "1-page report" view for EX3_COMPARE results only
 * - SSOT: EX3_COMPARE ViewModel (NO EX4/EX2 mixing)
 * - Deterministic only (NO LLM)
 * - NO recommendation/judgment (structural comparison ONLY)
 *
 * CONSTITUTIONAL RULES:
 * - EX3 SSOT only (kind === "EX3_COMPARE")
 * - NO LLM usage
 * - NO recommendation/superiority claims ("더 좋다", "추천", "유리" forbidden)
 * - Structural explanations and fact summaries are allowed
 * - Report wording must be verifiable from data + fixed templates
 * - Insurer count: Currently 2 (samsung/meritz), but model is column-array based for extensibility
 */

import { ComparisonTableSection, CommonNotesSection } from '../types';

/**
 * EX3ReportDoc: Complete report document for EX3_COMPARE
 *
 * Structure (1-page layout):
 * 1. Header: title + subtitle
 * 2. Summary Box: summary_lines (max 3 lines)
 * 3. Comparison Table: table (from EX3 comparison_table section)
 * 4. Notes: notes (from EX3 common_notes section)
 */
export interface EX3ReportDoc {
  /**
   * Report title
   * Example: "{coverage_display} 비교 요약"
   */
  title: string;

  /**
   * Subtitle lines (insurer names + source note)
   * Example: ["삼성화재 vs 메리츠화재", "가입설계서 기준 비교입니다"]
   */
  subtitle: string[];

  /**
   * Summary lines (max 3, deterministic template + data)
   * Line 1: "{A}와 {B}의 {coverage} 보장 정의 기준 차이를 정리했습니다."
   * Line 2: (if "보장 정의 기준" row exists) "{A}: {cellA} / {B}: {cellB}"
   * Line 3: (if "핵심 보장 내용" row exists) "{A}: {cellA} / {B}: {cellB}"
   *
   * Empty lines are omitted (no blank lines)
   */
  summary_lines: string[];

  /**
   * Comparison table (from EX3 comparison_table section)
   * Direct reference/copy from EX3_COMPARE message
   */
  table: ComparisonTableSection;

  /**
   * Notes (from EX3 common_notes section)
   * Direct copy from EX3_COMPARE message (NO creation)
   */
  notes: string[];
}
