> SSOT Location: docs/active_constitution.md  
> (Moved from project root on 2026-01-08, content unchanged)

Insurance Coverage Canonical Mapping Pipeline

This document defines absolute, non-negotiable rules governing the insurance coverage pipeline.
All agents (Claude, Codex, scripts) MUST comply.
Any violation is a hard failure, not a warning.

⸻

0. Scope & Authority

This constitution governs ALL steps of the pipeline:
	•	Step1: Proposal extraction
	•	Step2-a: Scope sanitization
	•	Step2-b: Canonical mapping
	•	Step3+: Comparison / Analysis
	•	Audit & Reporting scripts

If any instruction conflicts with this document, THIS DOCUMENT WINS.

⸻

1. SSOT (Single Source of Truth)

1.1 Data SSOT
	•	All intermediate and final artifacts MUST live under:

data/scope_v3/


	•	No other directory is allowed for pipeline outputs.

1.2 Mapping SSOT
	•	Canonical coverage definitions = 신정원 통일코드
	•	Mapping reference file:

data/sources/mapping/담보명mapping자료.xlsx


	•	No ad-hoc mappings, no inline dictionaries, no inferred codes.

⸻

2. Identity Model (4D Identity)

Every row in Step2-a and beyond MUST carry 4D identity:

Dimension	Field	Rule
Insurer	insurer_key	Deterministic, lowercase
Product	product.product_key	From proposal page 1 only
Variant	variant.variant_key	From proposal context only
Coverage	coverage_name_normalized	Deterministic normalization

2.1 Product Rules
	•	Product name:
	•	Extracted ONLY from proposal page 1
	•	NEVER inferred from filename
	•	product_key = {insurer_key}__{normalized_product_name}
	•	Missing product_key = HARD FAIL

2.2 Variant Rules
	•	Variant derived ONLY from proposal context block:
	•	Sex (male / female)
	•	Age (under40 / over41)
	•	If no variant exists → variant_key = "default"
	•	Filename-based inference is FORBIDDEN

⸻

3. GATES (Hard Enforcement)

GATE-1 (Step1)
	•	Product identity MUST exist
	•	Missing → exit code 2

GATE-2 (Step1)
	•	Variant extraction mismatch → WARNING
	•	Variant missing → default assigned

GATE-3 (Step2-a & Step2-b)
	•	Required fields:
	•	insurer_key
	•	product.product_key
	•	variant.variant_key
	•	Missing ANY → HARD FAIL (exit 2)

⸻

4. Normalization Rules

4.1 Normalization Order (ABSOLUTE)
	1.	Normalize coverage name
	2.	THEN apply drop / keep logic

4.2 Normalized Field Priority

When displaying or matching coverage names:
	1.	coverage_name_normalized
	2.	coverage_name_raw
	3.	coverage_name

⸻

5. Step2-a (Sanitize Scope)

5.1 Purpose
	•	Remove noise / fragments
	•	PRESERVE all legitimate coverage axes

5.2 Premium Waiver Rule
	•	Items related to 보험료 납입면제:
	•	MUST NOT be dropped
	•	MUST be tagged:

{
  "coverage_kind": "premium_waiver",
  "coverage_axis": ["waiver"]
}



5.3 Dropped Items
	•	Dropped items MUST:
	•	Be written to {insurer}_step2_dropped.jsonl
	•	Preserve full identity fields (4D)

⸻

6. Step2-b (Canonical Mapping)

6.1 Mapping Key (ABSOLUTE)

Mapping logic uses ONLY:

(insurer_key, coverage_name_normalized)

❌ NOT allowed in mapping logic:
	•	ins_cd
	•	product_key
	•	variant_key
	•	source_doc_type

6.2 Identity Carry-Through
	•	Step2-b output and mapping_report MUST include:
	•	insurer_key
	•	product_key
	•	variant_key
	•	coverage_name_raw
	•	coverage_name_normalized

6.3 Unmapped Definition

A row is unmapped if and only if:

mapping_method == "unmapped"


⸻

7. Reporting & Audit Rules

7.1 SSOT Line Counts
	•	All counts MUST be line-based
	•	Deduplicated counts are DISPLAY ONLY
	•	Any mismatch between report counts and SSOT lines = BUG

7.2 Unmapped Classification

Unmapped rows are classified into:
	•	Excel-hit unmapped → pipeline bug
	•	Excel-miss unmapped → mapping gap

This classification is ANALYSIS ONLY
No automatic fixing allowed.

⸻

8. Pipeline Execution (STEP NEXT-73: ZERO-TOLERANCE)

8.1 Single Entry Point (MANDATORY)

ALL pipeline execution MUST use:

python3 tools/run_pipeline.py --stage {step2b|step3|step4|all}


❌ FORBIDDEN: Direct module execution
	•	NO: python -m pipeline.step2_canonical_mapping.run
	•	NO: python pipeline/step3_evidence_resolver/run.py
	•	NO: Direct imports of pipeline modules

Violation → Exit 2 (hard fail)

8.2 INPUT GATES (MANDATORY)

Each step MUST validate inputs BEFORE execution:

Step2-b INPUT:
	•	File pattern: *_step2_sanitized_scope_v1.jsonl
	•	Schema: Step2-a sanitized output

Step3 INPUT:
	•	File pattern: *_step2_canonical_scope_v1.jsonl
	•	Required fields: insurer_key, product.product_key, variant.variant_key, coverage_code, mapping_method
	•	Schema: scope_v3_step2b_v1
	•	❌ REJECTS: Step1 (*_step1_*), Step2-a (*_step2_sanitized_*)

Step4 INPUT:
	•	File pattern: *_step3_evidence_enriched_v1_gated.jsonl
	•	Required fields: coverage_code, evidence_pack, insurer_key
	•	❌ REJECTS: Step1, Step2-a, Step2-b files

Violation → Exit 2 (hard fail)

8.3 Validation Scripts (MANDATORY PARAMETERS)

ALL validation scripts MUST receive explicit targets:

python3 tools/audit/validate_anchor_gate.py --input <FILE>
python3 tools/audit/validate_universe_gate.py --data-dir <DIR>


❌ NO default paths allowed
❌ Missing parameters → Exit 2

8.4 Execution Receipt (MANDATORY)

ALL pipeline runs MUST generate:

docs/audit/run_receipt.json


Contains:
	•	stage, timestamp
	•	input_files (path + sha256 + line_count)
	•	output_files (path + sha256 + line_count)
	•	metrics (mapped%, anchored%, etc.)

No receipt = execution did not complete

8.5 Forbidden Actions (ZERO TOLERANCE)
	•	❌ LLM-based inference
	•	❌ Filename-based product or variant inference
	•	❌ Modifying mapping logic to "improve rate"
	•	❌ Silent fallback when identity is missing
	•	❌ Mixing old and new schemas
	•	❌ Direct module execution (use tools/run_pipeline.py)
	•	❌ Validation without --input or --data-dir parameters
	•	❌ Bypassing INPUT GATES

⸻

9. Definition of Success

The pipeline is considered correct when:
	•	Unmapped rows carry full 4D identity
	•	Every unmapped row is explainable as:
	•	Excel gap OR
	•	Deterministic pipeline bug
	•	Mapping rate changes ONLY when Excel changes
	•	No ambiguity remains about “why unmapped”

⸻

End of Constitution

⸻

다음 액션 (정확히 이 순서)
	1.	✅ 이 문서를 ACTIVE_CONSTITUTION.md로 저장
	2.	👉 Claude에게 다음 한 줄만 전달

All future actions MUST comply with ACTIVE_CONSTITUTION.md. Proceed with STEP NEXT-63-A.
