"""
Generate Q8 Surgery Repeat Payment Policy SSOT

Runs surgery_repeat_policy_resolver for all insurers and outputs to:
data/compare_v1/q8_surgery_repeat_policy_v1.jsonl
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.step3_evidence_resolver.surgery_repeat_policy_resolver import resolve_surgery_repeat_policy


# All insurers (including variants)
INSURERS = [
    "hanwha",
    "heungkuk",
    "hyundai",
    "kb",
    "lotte_female",
    "lotte_male",
    "meritz",
    "samsung",
    "db_over41",
    "db_under40"
]


def main():
    """Generate q8_surgery_repeat_policy_v1.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "compare_v1" / "q8_surgery_repeat_policy_v1.jsonl"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = []

    print("=" * 80)
    print("Q8 SURGERY REPEAT PAYMENT POLICY GENERATION")
    print("=" * 80)
    print()

    for insurer_key in INSURERS:
        print(f"[{insurer_key}] Resolving surgery repeat payment policy...")

        try:
            result = resolve_surgery_repeat_policy(insurer_key)
            results.append(result)

            policy = result["repeat_payment_policy"]
            display_text = result["display_text"]
            evidence_count = len(result["evidence_refs"])

            print(f"[{insurer_key}] Policy: {policy}")
            print(f"[{insurer_key}] Display: {display_text}")
            print(f"[{insurer_key}] Evidence count: {evidence_count}")

            if evidence_count > 0:
                print(f"[{insurer_key}] First evidence:")
                first_ev = result["evidence_refs"][0]
                print(f"  - doc_type: {first_ev['doc_type']}")
                print(f"  - page: {first_ev['page']}")
                print(f"  - excerpt: {first_ev['excerpt'][:100]}...")

        except Exception as e:
            print(f"[{insurer_key}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            # Add UNKNOWN result on error
            results.append({
                "insurer_key": insurer_key,
                "repeat_payment_policy": "UNKNOWN",
                "display_text": "확인 불가 (근거 없음)",
                "evidence_refs": []
            })

        print()

    # Write to JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print("=" * 80)
    print(f"Output written to: {output_path}")
    print(f"Total insurers processed: {len(results)}")
    print("=" * 80)

    # Summary statistics
    policy_counts = {}
    for result in results:
        policy = result["repeat_payment_policy"]
        policy_counts[policy] = policy_counts.get(policy, 0) + 1

    print()
    print("POLICY DISTRIBUTION:")
    for policy, count in sorted(policy_counts.items()):
        print(f"  {policy}: {count}")


if __name__ == "__main__":
    main()
