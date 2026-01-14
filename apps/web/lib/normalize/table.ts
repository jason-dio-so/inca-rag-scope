/**
 * STEP NEXT-UI-02-FIX7: Table Section Normalizer
 *
 * Purpose: Normalize ANY table shape from backend into a consistent UI contract
 * to eliminate [object Object] rendering.
 *
 * UI Render Contract (SSOT):
 * {
 *   title: string;
 *   columns: string[];
 *   rows: Array<{ label: string; values: string[] }>;
 * }
 *
 * Constitutional: NO LLM, NO OCR, NO Embedding
 */

import { renderCellValue } from "@/lib/renderers/valueRenderer";

// EVIDENCE-FIRST: Cell-level evidence support
export interface NormalizedCell {
  text: string;
  evidence_ref_id?: string;
  evidences?: any[];  // STEP DEMO-EVIDENCE-RELEVANCE-01: Slot-specific evidence objects
  slotName?: string;  // STEP DEMO-EVIDENCE-RELEVANCE-01: Slot identifier (e.g., "duration_limit_days")
}

export interface NormalizedTable {
  title: string;
  columns: string[];
  rows: Array<{
    label: string;
    values: (string | NormalizedCell)[];  // EVIDENCE-FIRST: Support cell-level evidence
    meta?: {
      proposal_detail_ref?: string;
      evidence_refs?: string[];
      evidences?: any[];  // STEP DEMO-EVIDENCE-VIS-01: Direct evidence objects for overlay responses (DEPRECATED - use cell.evidences)
      productName?: string;  // STEP DEMO-Q11-POLISH-01: Product name for insurer
      note?: string;  // STEP DEMO-Q11-POLISH-01: Reference note
      productEvidences?: any[];  // STEP DEMO-EVIDENCE-RELEVANCE-01: Product name evidence
      kpi_summary?: {
        payment_type: string;
        limit_summary?: string | null;
        kpi_evidence_refs?: string[];
        extraction_notes?: string;
      };
      // STEP NEXT-76: KPI Condition metadata
      kpi_condition?: {
        waiting_period?: string | null;
        reduction_condition?: string | null;
        exclusion_condition?: string | null;
        renewal_condition?: string | null;
        condition_evidence_refs?: string[];
        extraction_notes?: string;
      };
    };
  }>;
}

/**
 * Normalizes a comparison_table section into the UI render contract.
 * Handles various backend shapes and ensures all cells are strings.
 */
export function normalizeTableSection(section: any): NormalizedTable {
  // Safety guards
  if (!section || typeof section !== "object") {
    return {
      title: "Invalid Section",
      columns: [],
      rows: [],
    };
  }

  const title = typeof section.title === "string" ? section.title : "Untitled Table";

  // Normalize columns (must be string array)
  const columns: string[] = normalizeColumns(section.columns);

  // Normalize rows (must be Array<{label: string, values: string[]}>)
  const rows = normalizeRows(section.rows, columns.length);

  return {
    title,
    columns,
    rows,
  };
}

function normalizeColumns(cols: unknown): string[] {
  if (!Array.isArray(cols)) return [];

  return cols.map((col, idx) => {
    // Column should be a string
    if (typeof col === "string") return col;
    if (typeof col === "number") return String(col);
    if (col && typeof col === "object") {
      // Try common fields
      const obj = col as Record<string, any>;
      if (typeof obj.name === "string") return obj.name;
      if (typeof obj.label === "string") return obj.label;
      if (typeof obj.text === "string") return obj.text;
      // Fallback: use renderCellValue
      return renderCellValue(col);
    }
    return `Column ${idx + 1}`;
  });
}

/**
 * EVIDENCE-FIRST: Normalize a cell while preserving evidence metadata
 * Backend contract: cell.meta.doc_ref (NOT evidence_ref_id)
 * STEP DEMO-RENDER-CONTRACT-BLOCK-01: Preserve evidences/slotName from overlayToVm
 */
function normalizeCell(cell: unknown): string | NormalizedCell {
  if (cell === null || cell === undefined) return "-";
  if (typeof cell === "string") return cell;
  if (typeof cell === "number" || typeof cell === "boolean") return renderCellValue(cell);

  if (typeof cell === "object" && !Array.isArray(cell)) {
    const cellObj = cell as Record<string, any>;

    // STEP DEMO-RENDER-CONTRACT-BLOCK-01: Check if already a NormalizedCell from overlayToVm
    if (cellObj.text !== undefined) {
      // This is already a NormalizedCell object - preserve ALL fields
      return {
        text: String(cellObj.text),
        evidence_ref_id: cellObj.evidence_ref_id,
        evidences: cellObj.evidences,  // Preserve evidences array
        slotName: cellObj.slotName,    // Preserve slot identifier
      } as NormalizedCell;
    }

    const text = renderCellValue(cell);

    // Preserve doc_ref (backend evidence reference) as evidence_ref_id (frontend contract)
    // Backend field: cell.meta.doc_ref
    // Frontend field: NormalizedCell.evidence_ref_id
    const docRef = cellObj.meta?.doc_ref || cellObj.meta?.evidence_ref_id;
    if (docRef) {
      return {
        text,
        evidence_ref_id: docRef,
      };
    }

    return text;
  }

  return renderCellValue(cell);
}

function normalizeRows(
  rows: unknown,
  expectedColumnCount: number
): Array<{ label: string; values: (string | NormalizedCell)[]; meta?: { proposal_detail_ref?: string; evidence_refs?: string[]; evidences?: any[]; productName?: string; note?: string; kpi_summary?: any; kpi_condition?: any } }> {
  if (!Array.isArray(rows)) return [];

  return rows.map((row, rowIdx) => {
    if (!row || typeof row !== "object") {
      return {
        label: `Row ${rowIdx + 1}`,
        values: Array(Math.max(0, expectedColumnCount - 1)).fill("-"),
      };
    }

    const rowObj = row as Record<string, any>;

    // Debug: log first row to see structure
    if (rowIdx === 0) {
      console.log("[normalizeRows] First row structure:", {
        row: rowObj,
        keys: Object.keys(rowObj),
        label: rowObj.label,
        values: rowObj.values,
        cells: rowObj.cells,
        meta: rowObj.meta,
      });
    }

    // Extract label and values
    let label: string;
    let values: (string | NormalizedCell)[];

    // Pattern 1: row.cells exists (EX2_DETAIL pattern)
    // First cell is label, rest are values
    if (Array.isArray(rowObj.cells)) {
      // EVIDENCE-FIRST: Use normalizeCell to preserve evidence
      const allCells = rowObj.cells.map((cell: unknown) => normalizeCell(cell));
      const firstCell = allCells[0];
      label = (typeof firstCell === "string" ? firstCell : firstCell.text) || `Row ${rowIdx + 1}`;
      values = allCells.slice(1);

      if (rowIdx === 0) {
        console.log("[normalizeRows] cells pattern:", {
          allCells,
          label,
          values,
        });
      }
    }
    // Pattern 2: row.label + row.values exists
    else if (rowObj.label !== undefined && Array.isArray(rowObj.values)) {
      label = typeof rowObj.label === "string"
        ? rowObj.label
        : renderCellValue(rowObj.label);
      // EVIDENCE-FIRST: Use normalizeCell to preserve evidence
      values = rowObj.values.map((cell: unknown) => normalizeCell(cell));
    }
    // Pattern 3: row is an array itself
    else if (Array.isArray(row)) {
      const arr = row as unknown[];
      label = renderCellValue(arr[0]);
      values = arr.slice(1).map((cell) => normalizeCell(cell));
    }
    // Pattern 4: only row.label exists
    else if (rowObj.label !== undefined) {
      label = typeof rowObj.label === "string"
        ? rowObj.label
        : renderCellValue(rowObj.label);
      values = [];
    }
    // Pattern 5: fallback
    else {
      label = `Row ${rowIdx + 1}`;
      values = [];
    }

    // Pad/trim to expected length
    const targetLength = Math.max(0, expectedColumnCount - 1);
    while (values.length < targetLength) {
      values.push("-");
    }
    if (values.length > targetLength) {
      values = values.slice(0, targetLength);
    }

    // STEP NEXT-73R-P2: Preserve row.meta for lazy loading
    const meta = rowObj.meta && typeof rowObj.meta === "object"
      ? {
          proposal_detail_ref: rowObj.meta.proposal_detail_ref,
          evidence_refs: Array.isArray(rowObj.meta.evidence_refs) ? rowObj.meta.evidence_refs : undefined,
          evidences: Array.isArray(rowObj.meta.evidences) ? rowObj.meta.evidences : undefined,  // STEP DEMO-EVIDENCE-VIS-01
          productName: rowObj.meta.productName,  // STEP DEMO-Q11-POLISH-01
          note: rowObj.meta.note,  // STEP DEMO-Q11-POLISH-01
          kpi_summary: rowObj.meta.kpi_summary,  // STEP NEXT-75
          kpi_condition: rowObj.meta.kpi_condition,  // STEP NEXT-76
        }
      : undefined;

    return {
      label,
      values,
      ...(meta && { meta }),
    };
  });
}

/**
 * STEP NEXT-139C: Formatting moved to backend (ex3_compare_composer.py)
 * Frontend now just renders pre-formatted strings from backend.
 * See: `format_payment_type()`, `format_amount_display()`, `format_limit_display()`
 */

/**
 * Debug helper: Deep log table structure for troubleshooting
 */
export function debugLogTable(section: any, name: string = "table") {
  console.group(`[Table Debug] ${name}`);
  console.log("Raw section:", section);
  console.log("Title:", section?.title);
  console.log("Columns:", section?.columns);
  console.log("Rows count:", Array.isArray(section?.rows) ? section.rows.length : 0);
  if (Array.isArray(section?.rows) && section.rows.length > 0) {
    console.log("First row:", section.rows[0]);
    console.log("First row type:", typeof section.rows[0]);
    if (section.rows[0] && typeof section.rows[0] === "object") {
      console.log("First row keys:", Object.keys(section.rows[0]));
      console.log("First row label:", section.rows[0].label);
      console.log("First row label type:", typeof section.rows[0].label);
      console.log("First row values:", section.rows[0].values);
      console.log("First row cells:", section.rows[0].cells);
    }
  }
  console.groupEnd();
}
