# STEP NEXT — Chat UI v2 Design Decisions

## Overview

This document records architectural and design decisions made during the Chat UI v2 specification process. All decisions follow the Evidence Mandatory principle and align with SSOT-based data integrity rules.

---

## Decision Log

### D001: Q1 Rate Multiplier Evidence is Rail-Only

**Date**: 2026-01-16
**Status**: ✅ Approved
**Category**: Q1 Premium Comparison
**Severity**: High (affects UX and evidence presentation)

#### Context

Q1 (Premium Comparison) displays both GENERAL and NO_REFUND premium values. GENERAL premiums are calculated using:

```
GENERAL Premium = NO_REFUND Premium × Rate Multiplier
```

Rate multipliers come from a fixed reference table (e.g., `일반보험요율예시.xlsx`) and vary by age and gender.

**Question**: Should rate multiplier values and calculation formulas be displayed in the main comparison table?

#### Decision

**Rate multipliers and calculation formulas are displayed ONLY in the Evidence Rail, NOT in the main table.**

#### Rationale

1. **Separation of Results and Evidence**
   - Main table should focus on final results (premium values, rankings)
   - Evidence Rail is the designated location for tracing data sources and calculation logic

2. **Reduces Visual Clutter**
   - Displaying formulas and multipliers in the main table creates cognitive overload
   - Users primarily need to compare final premium values, not intermediate calculations

3. **Maintains Evidence Mandatory Integrity**
   - Evidence Rail ensures all calculations are fully traceable
   - Users who need to verify calculations can access detailed evidence without cluttering the main view

4. **Consistency with Q2/Q3/Q4**
   - Other query types (Q2~Q4) also separate main results from evidence details
   - Maintains consistent UX pattern across all result views

#### Main Table — Displays

- Total premium (총납) and Monthly premium (월납)
- Product name, insurer name, rank
- Product type (GENERAL / NO_REFUND)

#### Evidence Rail — Displays

When a product (row) is selected:

1. **Base Premium Evidence**
   - Source: 가입설계서 / premium data table
   - Conditions: age, gender
   - Retrieved value

2. **Rate Multiplier Evidence**
   - Source: 일반보험요율예시.xlsx
   - Conditions: age, gender
   - Multiplier value (e.g., 1.35)
   - Explanation: "일반보험료 산출에 사용됨"

#### Allowed UI Guidance

A single-line informational notice is permitted in the main view:

> 일반 보험료는 무해지 기준 보험료와 요율표를 기반으로 산출되며,
> 근거는 우측 Evidence에서 확인할 수 있습니다.

#### Consequences

**Positive:**
- Cleaner, more scannable main table
- Users can focus on premium comparison without distraction
- Evidence traceability maintained in dedicated panel

**Negative:**
- Users must click/select a row to see calculation details
- Requires implementation of Evidence Rail interaction

#### Alternatives Considered

**Alternative A**: Display multipliers in main table
- ❌ Rejected: Creates visual clutter, mixes results with evidence

**Alternative B**: Display multipliers in tooltip on hover
- ❌ Rejected: Evidence should be persistent and accessible, not ephemeral

**Alternative C**: No evidence display at all
- ❌ Rejected: Violates Evidence Mandatory principle

---

## Decision Template (for future use)

```markdown
### D00X: [Decision Title]

**Date**: YYYY-MM-DD
**Status**: ✅ Approved | ⏳ Pending | ❌ Rejected
**Category**: Q1 | Q2 | Q3 | Q4 | General
**Severity**: High | Medium | Low

#### Context
[Background and problem statement]

#### Decision
[Clear statement of the decision]

#### Rationale
[Why this decision was made]

#### Consequences
**Positive:**
- [Benefit 1]
- [Benefit 2]

**Negative:**
- [Drawback 1]
- [Drawback 2]

#### Alternatives Considered
- [Alternative 1]: [Why rejected]
- [Alternative 2]: [Why rejected]
```

---

## Revision History

- 2026-01-16: D001 added (Q1 Rate Multiplier Evidence is Rail-Only)
