# Demo FAQ
**STEP NEXT-38-E: Constitutional Compliance Q&A**

**Purpose**: Answers to customer questions that **enforce constitutional rules** (no recommendations, evidence-based, scope-limited, read-only)

---

## Category 1: Recommendations & Advice (PROHIBITED)

### Q: "Which product do you recommend?"
**A**: "We do not make recommendations. Our system compares insurance products based on documented evidence (policy terms, proposals). The choice depends on your personal situation, priorities, and risk profile. We provide comparison; you make the decision."

**Why**: Recommendation = financial advice. We are not licensed advisors.

---

### Q: "Is this product better for me?"
**A**: "We cannot determine what is 'better' for you. We can show you how the products differ in coverage amounts, conditions, and exclusions. Your definition of 'better' depends on factors we don't assess (age, health, budget, priorities)."

**Why**: "Better" is subjective and requires personalized advice.

---

### Q: "Should I buy this insurance?"
**A**: "That decision is yours to make. We show you what each product covers, under what conditions, and with what limitations—all based on the official documents. Consult with a licensed advisor if you need personalized guidance."

**Why**: Buy/don't buy = advice. Prohibited.

---

### Q: "What's the best value for money?"
**A**: "We don't calculate 'value' because it depends on individual risk assessment and financial planning. We can show you the premium reference (from proposals) and coverage details, but value judgment is yours to make."

**Why**: Value = subjective analysis. Prohibited.

---

## Category 2: Evidence & Source Verification

### Q: "How do I know this information is accurate?"
**A**: "Every piece of information we display includes:
- **Source**: Which document (policy, proposal, product summary)
- **Page/Section**: Exact location in the document
- **Snippet**: Direct quote from the original text

You can (and should) verify by checking the original document. We extract, not interpret."

**Why**: Transparency builds trust. Evidence is king.

---

### Q: "Where is this evidence from?"
**A**: "Click on the evidence reference (e.g., '약관 p.27'). It will show you the document type, page number, and text snippet. The full document should be reviewed directly from the insurer."

**Why**: Encourage direct document review.

---

### Q: "What if the evidence is wrong?"
**A**: "If you find a discrepancy between our display and the official document, please report it. We extract text programmatically; if the source document was incorrect or if our extraction failed, we will correct it. Evidence accuracy is our top priority."

**Why**: Admit fallibility, commit to correction.

---

### Q: "Can you summarize this coverage in simple terms?"
**A**: "We provide the original text from the policy. Summarizing risks misinterpretation. If the policy language is unclear, consult the insurer or a professional advisor who can explain it in context."

**Why**: Summarization = interpretation. Prohibited.

---

## Category 3: Scope & Coverage Matching

### Q: "Can you compare [담보명 X] across products?"
**A**: "Only if [담보명 X] exists in our mapping dataset (`담보명mapping자료.xlsx`). If it's not mapped, we return 'not found' to avoid incorrect matches. Fuzzy matching is prohibited to prevent false comparisons."

**Why**: Scope gate. Only mapped coverages.

---

### Q: "Why doesn't this coverage show up?"
**A**: "Three possible reasons:
1. **Not in mapping file**: Coverage is not in our canonical mapping dataset
2. **Not in policy**: Coverage doesn't exist in this product's policy documents
3. **Name mismatch**: Coverage exists but under a different name (requires manual mapping update)

We only match exact mappings to avoid errors."

**Why**: Explain not_found without making excuses.

---

### Q: "Can you add more coverages to the comparison?"
**A**: "Yes, but they must first be added to the mapping file by a human operator. We don't auto-detect or guess coverage names because that leads to incorrect matches."

**Why**: Human-in-the-loop for mapping. No AI guessing.

---

### Q: "Why can't you search for similar coverages?"
**A**: "Similar ≠ same. Insurance terms are legally precise. 'Similar' matching could mislead you into thinking two different coverages are comparable. We require exact mapping to maintain accuracy."

**Why**: Legal precision > convenience.

---

## Category 4: Premium & Calculations (PROHIBITED)

### Q: "Can you calculate my premium?"
**A**: "No. We do not calculate premiums. Premium calculation requires:
- Underwriting rules
- Personal data (age, gender, health)
- Actuarial models
- Real-time insurer pricing

We only display reference premiums from proposals **if available**, with a clear warning that they are examples, not your actual price."

**Why**: Premium calculation = underwriting. Prohibited.

---

### Q: "Why is the premium different from what you show?"
**A**: "The premium we display is from a **sample proposal** (if available). It reflects:
- Specific age/gender/coverage combination in that proposal
- Specific date of proposal
- Specific optional riders

Your actual premium depends on **your** profile. Always get a personalized quote from the insurer."

**Why**: Avoid premium confusion. Emphasize sample nature.

---

### Q: "Which product has the lowest premium?"
**A**: "We can show you the reference premiums from sample proposals (if available), but:
1. These are not your actual premiums
2. Lower premium ≠ better value (coverage matters)
3. We do not rank or recommend based on price

Compare coverage first, then get personalized quotes."

**Why**: Avoid premium-only decision making.

---

### Q: "Can you show premium by age/gender?"
**A**: "No. We do not have premium calculation capability. Contact the insurer for personalized premium quotes across different profiles."

**Why**: No calculation engine.

---

## Category 5: Conditions & Exclusions

### Q: "What are the exclusions for this coverage?"
**A**: "We extract major exclusions from the policy document (if explicitly listed). However, the full exclusion list and detailed conditions are in the official policy. You must read the complete policy or consult an advisor."

**Why**: We show what we find; full review is user's responsibility.

---

### Q: "Does this condition apply to me?"
**A**: "We cannot determine if a condition applies to your personal situation. We show you what the condition is (e.g., 'waiting period: 90 days'). Whether it affects you depends on your health, timing, and other factors. Consult an advisor."

**Why**: Personal application = advice. Prohibited.

---

### Q: "Is the waiting period longer for one product?"
**A**: "We display the waiting periods from each policy. You can compare them directly. Whether 'longer' is significant depends on your situation (e.g., if you need immediate coverage)."

**Why**: Provide data, not judgment.

---

### Q: "What does this policy term mean?"
**A**: "We display the term as written in the policy. For interpretation, consult:
- The insurer's customer service
- A licensed insurance advisor
- Legal/policy experts

We do not interpret legal language."

**Why**: Interpretation = legal risk. Prohibited.

---

## Category 6: Data & System Limitations

### Q: "Is this all the coverage in the product?"
**A**: "No. We only show coverages that:
1. Are in our mapping dataset
2. Are found in the policy documents we processed
3. Are in scope for this comparison

The full product may have additional coverages not displayed here. Review the complete policy."

**Why**: Admit scope limits. Prevent false completeness.

---

### Q: "Why are some fields blank or 'not found'?"
**A**: "Possible reasons:
- **Evidence not found**: We searched the policy but didn't find explicit text for this coverage
- **Document missing**: The policy document wasn't available for this product
- **Mapping missing**: Coverage is not in our mapping dataset

'Not found' ≠ 'does not exist'. It means we couldn't verify it. Check the policy directly."

**Why**: Honesty about data gaps.

---

### Q: "Can you check the latest policy version?"
**A**: "We process the policy documents we have on file. If a policy was recently updated, we may not have the latest version. Always verify with the insurer that you're reviewing the current policy."

**Why**: Data freshness disclaimer.

---

### Q: "Do you support all insurance companies?"
**A**: "Currently, we support products from companies in our mapping dataset:
- Samsung Fire & Marine
- Hanwha Life
- KB Insurance
- Meritz Fire & Marine
- Hyundai Marine & Fire (if mapped)

Adding new companies requires policy document acquisition and coverage mapping."

**Why**: Explicit scope. No overpromise.

---

## Category 7: System Functionality

### Q: "Can you generate a report I can print?"
**A**: "The current system displays comparisons on-screen. Print/export functionality depends on the implementation. Use browser print (Cmd/Ctrl+P) as a workaround."

**Why**: Feature availability.

---

### Q: "Can you save my comparison for later?"
**A**: "The current demo uses mock data and doesn't save state. In a production system, saving queries would be a feature request."

**Why**: Demo vs. production distinction.

---

### Q: "Why is the response slow?"
**A**: "In this demo, responses are instant (mock data). In production, response time depends on:
- Document search complexity
- Number of coverages compared
- Number of insurers

We prioritize accuracy over speed."

**Why**: Set performance expectations.

---

### Q: "Can you search by keyword?"
**A**: "We search by mapped coverage codes/names, not free-text keywords. This ensures precise matching. Keyword search risks returning unrelated results."

**Why**: Deterministic search only.

---

## Category 8: Demo-Specific Questions

### Q: "Is this real data?"
**A**: "No. This demo uses **mock fixtures** (example data) to demonstrate system functionality. Mock data is realistic but **not actual policy terms**. Real data integration is the next phase."

**Why**: Demo honesty.

---

### Q: "Can I test with my own insurance?"
**A**: "Not in this demo. This is a **prototype** with pre-loaded examples. To analyze your specific product, it must be:
1. Acquired (policy documents)
2. Processed (text extraction)
3. Mapped (coverage name matching)

This is a production workflow, not demo-ready."

**Why**: Manage expectations.

---

### Q: "When will the real system be available?"
**A**: "The real system requires:
- Database integration (coverage cards, evidence packs)
- Real-time document retrieval
- Production API deployment

Timeline depends on project roadmap. This demo validates the concept and interface."

**Why**: Roadmap transparency.

---

## Category 9: Trust & Liability

### Q: "Can I rely on this for my purchase decision?"
**A**: "You should use this comparison as **one input** among many:
- Official policy documents (read in full)
- Personalized insurer quotes
- Licensed advisor consultation
- Your personal risk assessment

We provide evidence-based comparison, not decision-making."

**Why**: Limit liability, encourage due diligence.

---

### Q: "What if I make a claim and this information was wrong?"
**A**: "Insurance claims are determined by the **official policy document**, not by any third-party comparison tool. Always verify coverage details with the insurer before purchase. We are not liable for policy interpretation or claim outcomes."

**Why**: Legal disclaimer. Policy is SSOT for claims.

---

### Q: "Who is responsible for data accuracy?"
**A**: "We are responsible for:
- Accurate extraction from source documents
- Transparent display of evidence sources
- Honesty about data gaps

Insurers are responsible for:
- Policy document accuracy
- Claim adjudication

You are responsible for:
- Verifying information before purchase
- Reading full policies
- Making informed decisions"

**Why**: Shared responsibility model.

---

## Category 10: Meta Questions (About the System)

### Q: "What technology do you use?"
**A**: "We use:
- Deterministic text search (no LLM summarization)
- Explicit coverage mapping (no fuzzy matching)
- Evidence-based retrieval (document + page + snippet)
- Read-only comparison (no calculations)

This ensures transparency and reproducibility."

**Why**: Technical transparency.

---

### Q: "Do you use AI?"
**A**: "We do **not** use AI/LLM for:
- Summarization
- Recommendations
- Coverage matching
- Text interpretation

We **may** use AI for (future):
- OCR (text extraction from PDFs)
- Quality checks

All AI usage is deterministic and auditable."

**Why**: AI usage policy.

---

### Q: "How often is the data updated?"
**A**: "Data update frequency depends on:
- Policy document release schedule (insurer-dependent)
- Manual mapping updates (as new coverages are added)

In production, we recommend quarterly updates or event-driven (when new policies are filed)."

**Why**: Data freshness policy.

---

## Response Template for Out-of-Scope Questions

**Q**: [Unexpected question outside constitutional rules]

**A**: "That's outside the scope of our comparison system. Our system is designed to:
1. Compare documented coverage terms
2. Display evidence sources
3. **Not** provide [recommendations / calculations / interpretations / predictions]

For [specific topic], please consult [insurer / licensed advisor / legal expert]."

---

**Constitutional Rules Summary** (Remind customer if needed):
1. **No recommendations**: We compare, you decide
2. **Evidence-based**: Every claim has a source
3. **Scope-limited**: Only mapped coverages
4. **Read-only**: No calculations, no simulations

---

**Last Updated**: 2025-12-31 (STEP NEXT-38-E)
**Usage**: Reference during/after customer demo
**Principle**: Honesty, transparency, constitutional compliance
