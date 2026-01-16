/**
 * EVIDENCE-FIRST: Cell Helper Utilities
 *
 * Purpose: Extract text and evidence metadata from normalized cells
 * Handles backwards compatibility (string | NormalizedCell)
 */

import { NormalizedCell } from "./table";
import { renderCellValue } from "@/lib/renderers/valueRenderer";

/**
 * Extract display text from a normalized cell (string or NormalizedCell)
 * STEP RENDER-CONTRACT-V2: ALWAYS use renderCellValue for object → string conversion
 */
export function getCellText(cell: string | NormalizedCell): string {
  if (typeof cell === "string") return cell;

  // RENDER CONTRACT V2: Use renderCellValue as single source of truth
  // Pass slotName for SlotValue suffix handling (e.g., "180일", "100,000원")
  return renderCellValue(cell.text, cell.slotName);
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

/**
 * STEP DEMO-RENDER-CONTRACT-BLOCK-01: Single Source of Truth for Evidence Rendering
 *
 * RENDERING CONTRACT:
 * - If evidences exist (length > 0), UI MUST render evidence area
 * - "Hidden by default" is allowed, but NO rendering is forbidden
 * - This function is the ONLY authority on whether evidence should be rendered
 */
export function hasRenderableEvidence(meta: {
  evidences?: any[];
  evidence_refs?: any[];
  productEvidences?: any[];
}): boolean {
  return (
    (Array.isArray(meta?.evidences) && meta.evidences.length > 0) ||
    (Array.isArray(meta?.productEvidences) && meta.productEvidences.length > 0)
  );
}

/**
 * STEP DEMO-RENDER-CONTRACT-BLOCK-01: Check if cell has renderable evidence
 */
export function cellHasRenderableEvidence(cell: string | NormalizedCell): boolean {
  if (typeof cell === "string") return false;
  return Array.isArray(cell.evidences) && cell.evidences.length > 0;
}
