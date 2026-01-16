# Chat UI v2 - Unified Comparison Interface

## Overview
Single-page chatbot interface for all 4 comparison types with dynamic routing.

## Route
**`/chat`** - Main entry point

## Components
1. **Insurer Selection**: Multiselect (2-8 insurers) + presets
2. **Filter Panel**: Collapsible (sort, type, age, gender)
3. **Query Input**: Text box with classification
4. **Result Views**: Q1/Q2/Q3/Q4 specialized renderers

## Query Classification (Rule-based)
- **Q1** (Premium): `보험료 + (저렴|정렬|top)`
- **Q2** (Limit Diff): `(보장한도|한도) + (다른|차이)`
- **Q3** (3-part): `(비교|종합) + (진단|암)`
- **Q4** (Matrix): `제자리암|경계성종양|(지원 + 여부)`

## Response Flow
1. User inputs query → `/api/chat_query` (Next.js API route)
2. Classify → Extract coverage_code (fuzzy match)
3. Call backend:
   - Q2/Q3 → `/compare_v2`
   - Q4 → `/q13`
   - Q1 → (Not yet implemented, returns placeholder)
4. Transform to viewModel → Render appropriate view

## View Types
- **Q2**: Table (보장한도, 일일보장금액)
- **Q3**: 3-part (table + summary + recommendation), uses Q12ReportView when q12_report available
- **Q4**: Matrix (제자리암/경계성종양 O/X/—)
- **Q1**: Placeholder (Premium data not connected)

## Status
✅ Q2, Q3, Q4 implemented | ⏳ Q1 pending (Premium SSOT)
