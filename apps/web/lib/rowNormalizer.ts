/**
 * STEP NEXT-UI-02-FINAL-FIX: Row Normalization Utility
 *
 * Purpose: Convert all possible server row formats into a single normalized structure
 * to prevent runtime crashes from undefined row.values access.
 *
 * Supported formats:
 * - Case A: { label: string, values: TableCell[] }
 * - Case B: ["label", "val1", "val2", ...]
 * - Case C: { cells: [...] }
 */

import { TableRow, TableCell } from "./types";

export interface NormalizedRow {
  label: string;
  values: TableCell[];
}

/**
 * Normalizes a row from any supported format into { label, values }.
 * Returns null if row cannot be normalized.
 */
export function normalizeRow(row: any): NormalizedRow | null {
  if (!row) return null;

  // Case A: { label, values } - already normalized
  if (typeof row === "object" && !Array.isArray(row) && Array.isArray(row.values)) {
    return {
      label: String(row.label ?? ""),
      values: row.values.map((v: any) => normalizeCell(v)),
    };
  }

  // Case B: ["label", v1, v2, ...] - array format
  if (Array.isArray(row) && row.length >= 2) {
    return {
      label: String(row[0]),
      values: row.slice(1).map((v: any) => normalizeCell(v)),
    };
  }

  // Case C: { cells: [...] } - cells format
  if (typeof row === "object" && !Array.isArray(row) && Array.isArray(row.cells)) {
    return {
      label: String(row.cells[0] ?? ""),
      values: row.cells.slice(1).map((v: any) => normalizeCell(v)),
    };
  }

  return null;
}

/**
 * Normalizes a cell value into TableCell format.
 */
function normalizeCell(cell: any): TableCell {
  // Already a TableCell
  if (typeof cell === "object" && cell !== null && "value_text" in cell) {
    return {
      value_text: String(cell.value_text ?? ""),
      meta: cell.meta,
    };
  }

  // Primitive value
  return {
    value_text: String(cell ?? ""),
  };
}

/**
 * Normalizes an array of rows, filtering out invalid entries.
 */
export function normalizeRows(rows: any[]): NormalizedRow[] {
  if (!Array.isArray(rows)) return [];
  return rows.map(normalizeRow).filter((r): r is NormalizedRow => r !== null);
}
