/**
 * STEP NEXT-UI-02-FIX6: Complete Cell Value Renderer
 *
 * Purpose: Convert ANY cell value (primitives, objects, arrays) to displayable strings
 * to eliminate [object Object] rendering in React tables.
 *
 * Constitutional: NO LLM, NO OCR, NO Embedding - pure deterministic string conversion
 *
 * STEP NEXT-139A/B: View-layer formatting for EXAM3
 * - 139A: LIMIT + AMOUNT → "{한도 설명} (일당 {금액})"
 * - 139B: 일당형 amount → "일당 {금액}" (한글만), 정액형 → "{금액}" (한글만)
 */

export function renderCellValue(cell: unknown): string {
  if (cell === null || cell === undefined) return "-";

  // primitives
  if (typeof cell === "string") return cell.trim() || "-";
  if (typeof cell === "number") return Number.isFinite(cell) ? String(cell) : "-";
  if (typeof cell === "boolean") return cell ? "O" : "X";

  // arrays
  if (Array.isArray(cell)) {
    const parts = cell
      .map((x) => renderCellValue(x))
      .filter((s) => s && s !== "-");
    return parts.length ? parts.join(", ") : "-";
  }

  // objects
  if (typeof cell === "object") {
    const o = cell as Record<string, any>;

    // 1) most common display fields
    const display =
      o.text ?? o.display ?? o.label ?? o.name ?? o.title ?? o.value_text ?? o.valueText;
    if (typeof display === "string" && display.trim()) return display.trim();

    // 2) value + unit patterns
    if (o.value !== undefined && (typeof o.value === "string" || typeof o.value === "number")) {
      const v = typeof o.value === "number" ? String(o.value) : o.value.trim();
      const u = typeof o.unit === "string" ? o.unit.trim() : "";
      return (v + (u ? ` ${u}` : "")).trim();
    }
    if (o.amount !== undefined && (typeof o.amount === "number" || typeof o.amount === "string")) {
      const v = typeof o.amount === "number" ? formatWonMaybe(o.amount) : o.amount;
      const u = typeof o.currency === "string" ? o.currency : (typeof o.unit === "string" ? o.unit : "");
      return `${v}${u ? ` ${u}` : ""}`.trim();
    }

    // 3) Step8 amount structure pattern
    // amount_structure: { payment_type, conditions[], limit{...} } or direct keys
    const paymentType = o.payment_type ?? o.paymentType ?? o.type;
    const conditions = o.conditions ?? o.condition ?? o.condition_tags;
    const limit = o.limit ?? o.limits;

    const parts: string[] = [];
    if (typeof paymentType === "string" && paymentType) parts.push(paymentType);

    if (Array.isArray(conditions)) {
      const c = conditions.map((x) => renderCellValue(x)).filter(Boolean);
      if (c.length) parts.push(c.join("/"));
    } else if (typeof conditions === "string" && conditions.trim()) {
      parts.push(conditions.trim());
    }

    if (limit && typeof limit === "object") {
      const lo = limit as Record<string, any>;
      // try common fields
      const count = lo.count ?? lo.times ?? lo.max_count;
      const period = lo.period ?? lo.unit ?? lo.window;
      const limParts: string[] = [];
      if (count !== undefined) limParts.push(`${count}회`);
      if (typeof period === "string" && period) limParts.push(period);
      if (limParts.length) parts.push(limParts.join(" "));
    } else if (typeof limit === "string" && limit.trim()) {
      parts.push(limit.trim());
    }

    if (parts.length) return parts.join(" | ");

    // 4) insurer-ish
    const insurer = o.insurer ?? o.insurer_name ?? o.company ?? o.company_name;
    if (typeof insurer === "string" && insurer.trim()) return insurer.trim();

    // 5) final fallback: safe stringify (short)
    return safeStringify(o);
  }

  // fallback
  return String(cell);
}

function safeStringify(o: Record<string, any>): string {
  try {
    const s = JSON.stringify(
      o,
      (_k, v) => {
        if (typeof v === "string" && v.length > 120) return v.slice(0, 120) + "…";
        return v;
      },
      0
    );
    if (!s) return "-";
    return s.length > 160 ? s.slice(0, 160) + "…" : s;
  } catch {
    return "-";
  }
}

function formatWonMaybe(n: number): string {
  // if already looks like won amount (>= 10000), format with comma
  if (!Number.isFinite(n)) return "-";
  const abs = Math.abs(n);
  if (abs >= 10000) return n.toLocaleString("ko-KR");
  return String(n);
}

/**
 * Inline value renderer (alias for renderCellValue)
 */
export function renderInlineValue(cell: unknown): string {
  return renderCellValue(cell);
}

/**
 * STEP NEXT-139A/B: EXAM3 View-Layer Formatting
 *
 * NOTE: Formatting has been moved to `apps/web/lib/normalize/table.ts`
 * where it's applied DURING normalization (before renderCellValue is called).
 * This preserves access to meta.kpi_summary which is needed for formatting.
 *
 * See: `applyEX3FormattingDuringNormalization()` in table.ts
 */
