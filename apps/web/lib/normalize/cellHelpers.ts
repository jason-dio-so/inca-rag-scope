/**
 * EVIDENCE-FIRST: Cell Helper Utilities
 *
 * Purpose: Extract text and evidence metadata from normalized cells
 * Handles backwards compatibility (string | NormalizedCell)
 */

import { NormalizedCell } from "./table";

/**
 * Extract display text from a normalized cell (string or NormalizedCell)
 */
export function getCellText(cell: string | NormalizedCell): string {
  if (typeof cell === "string") return cell;
  return cell.text;
}

/**
 * Check if cell has evidence
 * STEP DEMO-EVIDENCE-RELEVANCE-01: Also check for cell.evidences array
 */
export function cellHasEvidence(cell: string | NormalizedCell): boolean {
  if (typeof cell === "string") return false;
  return Boolean(cell.evidence_ref_id) || Boolean(cell.evidences && cell.evidences.length > 0);
}

/**
 * Get evidence ref ID from cell (or undefined if no evidence)
 */
export function getCellEvidenceRefId(cell: string | NormalizedCell): string | undefined {
  if (typeof cell === "string") return undefined;
  return cell.evidence_ref_id;
}
