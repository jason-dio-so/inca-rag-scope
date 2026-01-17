/**
 * Q2 Compare Proxy Route
 *
 * Purpose: Transform Q2 request to CompareRequest schema and proxy to backend /compare
 * Rules:
 * - MUST transform ins_cds → insurers (ENUM)
 * - MUST construct CompareRequest payload (NO PASSTHROUGH)
 * - MUST include all required fields: intent, products, query, insurers, age, gender, coverage_codes, sort_by, plan_variant_scope, as_of_date
 * - MUST accept both coverage_codes[] (array) and coverage_code (single) from frontend
 * - MUST validate coverage_code is not empty (return 400 if missing)
 * - Backend handles Q2 logic (coverage limit comparison)
 */

import { NextRequest, NextResponse } from 'next/server';

// INSURER CODE → ENUM mapping (MANDATORY)
const INSURER_CODE_TO_ENUM: Record<string, string> = {
  N01: "MERITZ",
  N02: "DB",
  N03: "HANWHA",
  N05: "LOTTE",
  N08: "KB",
  N09: "HYUNDAI",
  N10: "SAMSUNG",
  N13: "HEUNGKUK",
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Extract Q2 fields (support both coverage_codes[] and coverage_code)
    const {
      query,                                     // UI query (use as-is)
      coverage_codes,                            // array (priority)
      coverage_code,                             // single (fallback)
      age,
      gender,
      ins_cds = [],
      sort_by = "monthly",
      plan_variant_scope = "all",
      as_of_date = "2025-11-26",
    } = body;

    // Extract coverage_code with priority: coverage_codes[0] > coverage_code
    let resolvedCoverageCode: string | undefined;
    if (Array.isArray(coverage_codes) && coverage_codes.length > 0) {
      resolvedCoverageCode = String(coverage_codes[0]).trim();
    } else if (coverage_code) {
      resolvedCoverageCode = String(coverage_code).trim();
    }

    // Validate coverage_code is not empty (MANDATORY)
    if (!resolvedCoverageCode) {
      return NextResponse.json(
        {
          error: "Missing coverage_code",
          detail: "coverage_codes[0] or coverage_code is required and must not be empty"
        },
        { status: 400 }
      );
    }

    // Transform ins_cds → insurers (ENUM)
    const insurers = ins_cds
      .map((cd: string) => INSURER_CODE_TO_ENUM[cd])
      .filter(Boolean);

    // Filter out null/undefined from coverage_codes (MANDATORY)
    const safeCoverageCodes = [resolvedCoverageCode].filter(
      (c): c is string => typeof c === "string" && c.length > 0
    );

    if (safeCoverageCodes.length === 0) {
      return NextResponse.json(
        {
          error: "Invalid coverage_code",
          detail: "coverage_codes must contain at least one valid string"
        },
        { status: 400 }
      );
    }

    // Build CompareRequest payload (NO PASSTHROUGH)
    const comparePayload = {
      intent: "Q2_COVERAGE_LIMIT_COMPARE",       // REQUIRED (Q2-specific intent)
      products: [],                              // REQUIRED (empty array for Q2)
      query: query || "",                        // Use UI query as-is (natural language)
      insurers,                                  // ENUM ARRAY (REQUIRED)
      age,                                       // number (REQUIRED)
      gender,                                    // "M" | "F" (REQUIRED)
      coverage_codes: safeCoverageCodes,         // array (REQUIRED, null filtered)
      sort_by,                                   // "monthly" | "total"
      plan_variant_scope,                        // "all" | "standard" | "no_refund"
      as_of_date,                                // "YYYY-MM-DD"
    };

    // MANDATORY DEBUG LOGS (TEMP)
    console.log("[Q2][compare] payload =", JSON.stringify(comparePayload, null, 2));
    console.log("[Q2][compare] insurers =", insurers);
    console.log("[Q2][compare] coverage_codes =", comparePayload.coverage_codes);

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    const backendUrl = `${API_BASE}/compare`;

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(comparePayload),
    });

    // DEBUG: Log response status and body
    const text = await response.text();
    console.log("[Q2][compare] status =", response.status);
    console.log("[Q2][compare] response =", text);

    if (!response.ok) {
      console.error(`Q2 compare proxy error: ${response.status}`, text);
      return NextResponse.json(
        { error: `Backend error: ${response.status}`, details: text },
        { status: response.status }
      );
    }

    const data = JSON.parse(text);
    return NextResponse.json(data);

  } catch (error) {
    console.error('Q2 compare proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    );
  }
}
