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

export interface NormalizedTable {
  title: string;
  columns: string[];
  rows: Array<{
    label: string;
    values: string[];
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

function normalizeRows(
  rows: unknown,
  expectedColumnCount: number
): Array<{ label: string; values: string[] }> {
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
      });
    }

    // Extract label and values
    let label: string;
    let values: string[];

    // Pattern 1: row.cells exists (EX2_DETAIL pattern)
    // First cell is label, rest are values
    if (Array.isArray(rowObj.cells)) {
      const allCells = rowObj.cells.map((cell: unknown) => renderCellValue(cell));
      label = allCells[0] || `Row ${rowIdx + 1}`;
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
      values = rowObj.values.map((cell: unknown) => renderCellValue(cell));
    }
    // Pattern 3: row is an array itself
    else if (Array.isArray(row)) {
      const arr = row as unknown[];
      label = renderCellValue(arr[0]);
      values = arr.slice(1).map((cell) => renderCellValue(cell));
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

    return {
      label,
      values,
    };
  });
}

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
