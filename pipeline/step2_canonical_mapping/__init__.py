"""
⚠️⚠️⚠️ STEP2-B DISABLED ⚠️⚠️⚠️

This module is DISABLED as of STEP PIPELINE-V2-BLOCK-STEP2B-01.

REASON:
- coverage_code must come from SSOT input (Step1 V2), not from string-based assignment
- Contaminated path (data/sources/mapping/) is FORBIDDEN
- String matching for coverage_code generation is a CONSTITUTIONAL VIOLATION

Use Step1 V2 (pipeline.step1_targeted_v2) instead.

⚠️⚠️⚠️ STEP2-B DISABLED ⚠️⚠️⚠️

---

HISTORICAL DOCUMENTATION (DO NOT USE):

STEP NEXT-47: Step2-b Canonical Mapping
=========================================

Purpose:
    Map sanitized coverage names to 신정원 unified coverage codes.

Constitutional rules:
    1. 신정원 통일코드 is absolute reference
    2. Deterministic only (NO LLM, NO inference)
    3. Unmapped when ambiguous (never guess)
    4. NO row reduction (anti-contamination)

Input:
    data/scope_v3/{insurer}_{variant?}_step2_sanitized_scope_v1.jsonl

Output:
    data/scope_v3/{insurer}_{variant?}_step2_canonical_scope_v1.jsonl
    data/scope_v3/{insurer}_{variant?}_step2_mapping_report.jsonl

Canonical source:
    ❌ CONTAMINATED PATH - DO NOT USE
    data/sources/mapping/담보명mapping자료.xlsx (신정원 v2024.12)

    ✅ CORRECT PATH (Step1 V2):
    data/sources/insurers/담보명mapping자료.xlsx
"""
