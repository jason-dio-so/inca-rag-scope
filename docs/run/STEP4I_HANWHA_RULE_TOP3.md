# STEP 4-ι – Hanwha Top-3 Rule Candidates

## Rule 1: T3_suffix_gap

**Affected rows: 15**

**Pattern:**
- from_pattern: `담보|특약|보장|진단비|진단|치료비|치료|수술비|수술|입원일당|입원` (any suffix)
- to_pattern: flexible suffix matching (expand search to include all suffix variants)
- condition: if raw/canonical contains any suffix token

**Affected coverage names:**
- 암 진단비(유사암 제외)
- 암(4대특정암 제외) 진단비
- 4대특정암 진단비(제자리암)
- 4대특정암 진단비(기타피부암)
- 4대특정암 진단비(갑상선암)
- ... (10 more)

## Rule 2: T4_term_gap

**Affected rows: 15**

**Pattern:**
- from_pattern: `특정암|4대특정암|유사암|4대유사암|8대유사암|표적항암|항암치료|재진단` (specific term)
- to_pattern: term variant expansion (search all related terms)
- condition: if raw/canonical contains any term variant

**Affected coverage names:**
- 암 진단비(유사암 제외)
- 암(4대특정암 제외) 진단비
- 4대특정암 진단비(제자리암)
- 4대특정암 진단비(기타피부암)
- 4대특정암 진단비(갑상선암)
- ... (10 more)

## Rule 3: T5_bracket_gap

**Affected rows: 15**

**Pattern:**
- from_pattern: `(괄호내용)|숫자+대|유사암제외` (bracket/numeric qualifiers)
- to_pattern: bracket-agnostic search (strip or expand brackets)
- condition: if raw/canonical contains brackets or numeric qualifiers

**Affected coverage names:**
- 암 진단비(유사암 제외)
- 암(4대특정암 제외) 진단비
- 4대특정암 진단비(제자리암)
- 4대특정암 진단비(기타피부암)
- 4대특정암 진단비(갑상선암)
- ... (10 more)

