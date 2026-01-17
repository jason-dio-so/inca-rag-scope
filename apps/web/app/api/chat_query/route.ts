/**
 * Chat Query API Route
 *
 * Handles query classification and response generation
 * Routes to appropriate handler based on query type
 */

import { NextRequest, NextResponse } from 'next/server';

interface ChatQueryRequest {
  query_text: string;
  ins_cds: string[];
  filters: {
    sort_by: 'total' | 'monthly';
    product_type: 'all' | 'standard' | 'no_refund';
    age: number;
    gender: 'M' | 'F';
  };
}

interface ChatQueryResponse {
  kind: 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'UNKNOWN';
  viewModel: any;
  error?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const AS_OF_DATE = '2025-11-26';

/**
 * Classify query into Q1/Q2/Q3/Q4
 */
function classifyQuery(query: string): 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'UNKNOWN' {
  const q = query.toLowerCase();

  // Q1: Premium ranking (보험료, 저렴, 정렬, Top)
  if (q.includes('보험료') && (q.includes('저렴') || q.includes('정렬') || q.includes('top') || q.includes('순'))) {
    return 'Q1';
  }

  // Q2: Limit difference (보장한도, 다른, 차이)
  if ((q.includes('보장한도') || q.includes('한도')) && (q.includes('다른') || q.includes('차이'))) {
    return 'Q2';
  }

  // Q3: 3-part comparison (비교, 암진단비, 종합)
  if ((q.includes('비교') || q.includes('종합')) && (q.includes('진단') || q.includes('암'))) {
    return 'Q3';
  }

  // Q4: Support matrix (제자리암, 경계성종양, 지원, 보장 여부)
  if (q.includes('제자리암') || q.includes('경계성종양') || (q.includes('지원') && q.includes('여부'))) {
    return 'Q4';
  }

  return 'UNKNOWN';
}

/**
 * Extract coverage code from query
 */
function extractCoverageCode(query: string): string | null {
  // Try pattern matching for coverage codes
  const codeMatch = query.match(/A\d{4}(_\d)?/i);
  if (codeMatch) {
    return codeMatch[0].toUpperCase();
  }

  // Try fuzzy matching for coverage names
  const q = query.toLowerCase();

  if (q.includes('암진단비') || q.includes('암 진단')) {
    if (q.includes('유사암') && q.includes('제외')) {
      return 'A4200_1';
    }
    return 'A4200_1'; // Default
  }

  if (q.includes('암직접입원') || q.includes('암 직접 입원')) {
    return 'A6200';
  }

  if (q.includes('유사암')) {
    return 'A4210';
  }

  if (q.includes('암수술') || q.includes('암 수술')) {
    return 'A5200';
  }

  return null;
}

/**
 * Handle Q2: Coverage limit difference comparison
 */
async function handleQ2(request: ChatQueryRequest): Promise<any> {
  const coverageCode = extractCoverageCode(request.query_text);

  if (!coverageCode) {
    return {
      error: '담보 코드를 찾을 수 없습니다. 예: "암진단비", "A4200_1" 등을 포함해 주세요.',
      suggestions: ['A4200_1 (암진단비)', 'A6200 (암직접입원비)', 'A4210 (유사암진단비)'],
    };
  }

  try {
    const insCdsParam = request.ins_cds.join(',');
    const url = `${API_BASE}/compare_v2?coverage_code=${coverageCode}&as_of_date=${AS_OF_DATE}&ins_cds=${insCdsParam}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    // Transform to Q2 viewModel
    return {
      coverage_code: data.coverage_code,
      canonical_name: data.canonical_name,
      insurer_rows: data.insurer_rows || [],
    };
  } catch (error) {
    console.error('Q2 handler error:', error);
    return {
      error: '데이터를 불러올 수 없습니다.',
    };
  }
}

/**
 * Handle Q3: 3-part comparison (Table + Summary + Recommendation)
 */
async function handleQ3(request: ChatQueryRequest): Promise<any> {
  const coverageCode = extractCoverageCode(request.query_text);

  if (!coverageCode) {
    return {
      error: '담보 코드를 찾을 수 없습니다.',
    };
  }

  try {
    const insCdsParam = request.ins_cds.join(',');
    const url = `${API_BASE}/compare_v2?coverage_code=${coverageCode}&as_of_date=${AS_OF_DATE}&ins_cds=${insCdsParam}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    // Check if q12_report exists (contains LLM-generated parts)
    if (data.q12_report) {
      return data.q12_report;
    }

    // Fallback: Return table only
    return {
      coverage_code: data.coverage_code,
      canonical_name: data.canonical_name,
      insurer_rows: data.insurer_rows || [],
      overall_assessment: null,
      recommendation: null,
    };
  } catch (error) {
    console.error('Q3 handler error:', error);
    return {
      error: '데이터를 불러올 수 없습니다.',
    };
  }
}

/**
 * Handle Q4: Support matrix (O/X/-)
 */
async function handleQ4(request: ChatQueryRequest): Promise<any> {
  // Q4 uses /q13 endpoint
  try {
    const insurersParam = request.ins_cds.join(',');
    const url = `${API_BASE}/q13?insurers=${insurersParam}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Q4 handler error:', error);
    return {
      error: '데이터를 불러올 수 없습니다.',
    };
  }
}

/**
 * Handle Q1: Premium ranking (Top 4)
 */
async function handleQ1(request: ChatQueryRequest): Promise<any> {
  try {
    // Extract age and gender from filters
    const age = request.filters?.age || 40;
    const gender = request.filters?.gender || 'M';
    const sort_by = request.filters?.sort_by === 'monthly' ? 'monthly_total' : 'total';
    const plan_variant = request.filters?.product_type === 'no_refund' ? 'NO_REFUND' :
                         request.filters?.product_type === 'standard' ? 'GENERAL' : 'BOTH';

    // Call Python backend /premium/ranking
    const url = `${API_BASE}/premium/ranking?age=${age}&sex=${gender}&plan_variant=${plan_variant}&sort_by=${sort_by}&top_n=4&as_of_date=${AS_OF_DATE}`;

    const response = await fetch(url);
    if (!response.ok) {
      if (response.status === 404) {
        return {
          error: '해당 조건에 대한 보험료 데이터가 없습니다.',
          note: `age=${age}, sex=${gender}, as_of_date=${AS_OF_DATE}`
        };
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    // Return data as-is (/premium/ranking returns { kind, query_params, rows })
    // This matches Q1ViewModel structure
    return data;

  } catch (error) {
    console.error('Q1 handler error:', error);
    return {
      error: '보험료 데이터를 불러오는 중 오류가 발생했습니다.',
      note: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * POST /api/chat_query
 */
export async function POST(req: NextRequest) {
  try {
    const body: ChatQueryRequest = await req.json();

    // Validate request
    if (!body.query_text || !body.ins_cds || body.ins_cds.length < 2) {
      return NextResponse.json(
        { error: 'Invalid request: query_text and at least 2 ins_cds required' },
        { status: 400 }
      );
    }

    // Classify query
    const kind = classifyQuery(body.query_text);

    if (kind === 'UNKNOWN') {
      return NextResponse.json({
        kind: 'UNKNOWN',
        viewModel: {
          error: '질문을 이해할 수 없습니다. 다음 형식 중 하나로 질문해 주세요:',
          suggestions: [
            'Q1: "가장 저렴한 보험료 순서대로 4개만 비교"',
            'Q2: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"',
            'Q3: "삼성/메리츠 암진단비 비교"',
            'Q4: "제자리암/경계성종양 지원 여부 비교"',
          ],
        },
      });
    }

    // Route to appropriate handler
    let viewModel: any;
    switch (kind) {
      case 'Q1':
        viewModel = await handleQ1(body);
        break;
      case 'Q2':
        viewModel = await handleQ2(body);
        break;
      case 'Q3':
        viewModel = await handleQ3(body);
        break;
      case 'Q4':
        viewModel = await handleQ4(body);
        break;
      default:
        viewModel = { error: 'Unknown query type' };
    }

    const response: ChatQueryResponse = {
      kind,
      viewModel,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Chat query error:', error);
    return NextResponse.json(
      { error: 'Internal server error', kind: 'UNKNOWN', viewModel: null },
      { status: 500 }
    );
  }
}
