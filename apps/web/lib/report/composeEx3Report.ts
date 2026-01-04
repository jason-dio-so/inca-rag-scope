/**
 * STEP NEXT-132: EX3 Report Composer (EXAM3 Report View v0)
 *
 * PURPOSE:
 * - Compose 1-page report from latest EX3_COMPARE message
 * - Deterministic only (NO LLM)
 * - Fixed templates + data extraction
 *
 * CONSTITUTIONAL RULES:
 * - EX3 SSOT only (ignore EX4/EX2 messages)
 * - NO LLM usage
 * - NO recommendation/judgment
 * - NO creation (only extraction from EX3 data)
 */

import { AssistantMessageVM, ComparisonTableSection, CommonNotesSection } from '../types';
import { EX3ReportDoc } from './ex3ReportTypes';

/**
 * Extract insurer names from table columns
 *
 * Rules:
 * - Skip first column (usually "비교 항목" or similar header)
 * - Return remaining columns as insurer names
 * - Deterministic extraction (NO guessing)
 */
function extractInsurerNames(table: ComparisonTableSection): string[] {
  if (!table.columns || table.columns.length < 2) {
    return [];
  }

  // Skip first column (category label), return rest as insurer names
  return table.columns.slice(1);
}

/**
 * Find table row by category label (first cell text)
 *
 * Args:
 *   table: ComparisonTableSection
 *   categoryLabel: Category to find (e.g., "보장 정의 기준")
 *
 * Returns:
 *   Row if found, null otherwise
 */
function findRowByCategory(
  table: ComparisonTableSection,
  categoryLabel: string
): { cells: Array<{ text?: string }> } | null {
  if (!table.rows || table.rows.length === 0) {
    return null;
  }

  for (const row of table.rows) {
    if (!row.cells || row.cells.length === 0) continue;

    const firstCell = row.cells[0];
    const cellText = firstCell.text || '';

    if (cellText.includes(categoryLabel)) {
      return { cells: row.cells };
    }
  }

  return null;
}

/**
 * Build summary line from table row
 *
 * Format: "{A}: {cellA} / {B}: {cellB}"
 *
 * Args:
 *   row: Table row with cells
 *   insurers: Insurer names from columns
 *
 * Returns:
 *   Summary line or null if insufficient data
 */
function buildSummaryLineFromRow(
  row: { cells: Array<{ text?: string }> },
  insurers: string[]
): string | null {
  if (!row.cells || row.cells.length < 3) {
    // Need at least: [category, insurer1, insurer2]
    return null;
  }

  if (insurers.length < 2) {
    return null;
  }

  // Skip first cell (category label), extract insurer values
  const cell1 = row.cells[1]?.text || '표현 없음';
  const cell2 = row.cells[2]?.text || '표현 없음';

  return `${insurers[0]}: ${cell1} / ${insurers[1]}: ${cell2}`;
}

/**
 * Compose EX3 report from conversation messages
 *
 * Rules:
 * 1. Find latest EX3_COMPARE message
 * 2. Extract title (from message.title or coverage name)
 * 3. Extract subtitle (insurers from table columns + source note from notes)
 * 4. Build summary_lines (3 lines max, deterministic template)
 * 5. Copy table and notes directly
 *
 * Returns:
 *   EX3ReportDoc if EX3_COMPARE exists, null otherwise
 */
export function composeEx3Report(messages: AssistantMessageVM[]): EX3ReportDoc | null {
  // Step 1: Find latest EX3_COMPARE message
  let latestEX3: AssistantMessageVM | null = null;

  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].kind === 'EX3_COMPARE') {
      latestEX3 = messages[i];
      break;
    }
  }

  if (!latestEX3) {
    return null;
  }

  // Step 2: Find comparison_table section
  const tableSection = latestEX3.sections?.find(
    (s) => s.kind === 'comparison_table'
  ) as ComparisonTableSection | undefined;

  if (!tableSection) {
    // EX3_COMPARE must have comparison_table
    return null;
  }

  // Step 3: Extract insurer names from table columns
  const insurers = extractInsurerNames(tableSection);

  if (insurers.length === 0) {
    return null;
  }

  // Step 4: Build title
  const coverageName = latestEX3.title || '담보';
  const title = `${coverageName} 비교 요약`;

  // Step 5: Build subtitle
  const subtitle: string[] = [];

  // Line 1: Insurer names
  if (insurers.length === 2) {
    subtitle.push(`${insurers[0]} vs ${insurers[1]}`);
  } else {
    // Extensible: support 3+ insurers
    subtitle.push(insurers.join(' vs '));
  }

  // Line 2: Source note (from common_notes if exists)
  const notesSection = latestEX3.sections?.find(
    (s) => s.kind === 'common_notes'
  ) as CommonNotesSection | undefined;

  if (notesSection?.bullets && notesSection.bullets.length > 0) {
    // Find "가입설계서 기준" or similar note
    const sourceNote = notesSection.bullets.find((b) => b.includes('기준'));
    if (sourceNote) {
      subtitle.push(sourceNote);
    }
  }

  // Step 6: Build summary_lines (max 3 lines)
  const summary_lines: string[] = [];

  // Line 1: Fixed template
  if (insurers.length >= 2) {
    summary_lines.push(
      `${insurers[0]}와 ${insurers[1]}의 ${coverageName} 보장 정의 기준 차이를 정리했습니다.`
    );
  }

  // Line 2: "보장 정의 기준" row (if exists)
  const basisRow = findRowByCategory(tableSection, '보장 정의 기준');
  if (basisRow) {
    const line = buildSummaryLineFromRow(basisRow, insurers);
    if (line) {
      summary_lines.push(line);
    }
  }

  // Line 3: "핵심 보장 내용" row (if exists)
  const contentRow = findRowByCategory(tableSection, '핵심 보장 내용');
  if (contentRow) {
    const line = buildSummaryLineFromRow(contentRow, insurers);
    if (line) {
      summary_lines.push(line);
    }
  }

  // Step 7: Extract notes
  const notes: string[] = notesSection?.bullets || [];

  // Step 8: Build report
  return {
    title,
    subtitle,
    summary_lines,
    table: tableSection,
    notes,
  };
}
