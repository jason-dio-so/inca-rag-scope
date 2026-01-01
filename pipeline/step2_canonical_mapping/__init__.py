"""
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
    data/sources/mapping/담보명mapping자료.xlsx (신정원 v2024.12)
"""
