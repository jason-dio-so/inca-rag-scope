"""
STEP NEXT-46: Step2 Sanitize Scope
====================================

Purpose:
    Clean raw Step1 extraction outputs by removing fragments, clauses, and noise.

Constitutional rules:
    1. Step1 outputs are CORRECT raw extraction (frozen)
    2. Step2 handles ALL sanitization (fragments, clauses, variants)
    3. Deterministic pattern matching only (no LLM, no inference)
    4. Audit trail required (dropped entries preserved)

Input:
    data/scope_v3/{insurer}_{variant?}_step1_raw_scope_v3.jsonl

Output:
    data/scope_v3/{insurer}_{variant?}_step2_sanitized_scope_v1.jsonl
    data/scope_v3/{insurer}_{variant?}_step2_dropped.jsonl (audit trail)
"""
