#!/usr/bin/env python3
"""Generate Q8 audit document"""

import json
from pathlib import Path

ssot_path = Path("data/compare_v1/q8_surgery_repeat_policy_v1.jsonl")
output_path = Path("docs/audit/Q8_FACT_SNAPSHOT_2026-01-13.md")

# Read data
insurers_data = []
policy_counts = {}

with open(ssot_path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        data = json.loads(line)
        insurers_data.append(data)
        policy = data.get('repeat_payment_policy', '')
        policy_counts[policy] = policy_counts.get(policy, 0) + 1

# Generate markdown
output = []
output.append("# Q8 Fact Snapshot - 2026-01-13")
output.append("")
output.append("**Status**: FROZEN")
output.append("**SSOT**: data/compare_v1/q8_surgery_repeat_policy_v1.jsonl")
output.append("**Scope**: 질병수술비(1~5종) repeat payment policy ONLY")
output.append("**Out of Scope**: 대장용종 specific attribution, premium ranking, specific surgery recommendations")
output.append("")
output.append("---")
output.append("")
output.append("## Policy Distribution")
output.append("")

for policy in sorted(policy_counts.keys()):
    output.append(f"- **{policy}**: {policy_counts[policy]} insurers")

output.append("")
output.append("---")
output.append("")
output.append("## Evidence Summary by Insurer")
output.append("")

for data in insurers_data:
    insurer = data.get('insurer_key', '')
    policy = data.get('repeat_payment_policy', '')
    display = data.get('display_text', '')
    evidences = data.get('evidence_refs', [])

    output.append(f"### {insurer}")
    output.append("")
    output.append(f"**Policy**: `{policy}`")
    output.append(f"**Display**: {display}")
    output.append(f"**Evidence Count**: {len(evidences)}")
    output.append("")

    if len(evidences) > 0:
        output.append("**Evidence Sample** (first 3):")
        output.append("")
        for i, ev in enumerate(evidences[:3]):
            doc = ev.get('doc_type', '')
            page = ev.get('page', '')
            excerpt = ev.get('excerpt', '')[:100].replace('`', '')
            output.append(f"{i+1}. **Doc**: {doc}, **Page**: {page}")
            output.append(f"   **Excerpt**: `{excerpt}...`")
            output.append("")
    else:
        output.append("**UNKNOWN Justification**:")
        output.append("- No explicit repeat payment policy found in 질병수술비(1~5종) coverage documents")
        output.append("- Evidence-first approach: Cannot infer without documented evidence")
        output.append("")

    output.append("---")
    output.append("")

# Write output
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Audit document generated: {output_path}")
