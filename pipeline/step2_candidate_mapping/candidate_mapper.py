#!/usr/bin/env python3
"""
STEP NEXT-57: Candidate Mapper (LEVEL 1 - Deterministic Only)

Generates candidate coverage_code suggestions for unmapped items using
deterministic token-based matching.

Constitutional enforcement:
- NO LLM usage
- NO inference beyond token matching
- Candidates are suggestions, NOT confirmations
- SSOT (신정원 unified codes) remains unchanged
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import Counter
import pandas as pd


# Keyword dictionaries (deterministic matching)
# STEP NEXT-58-E: Enhanced for HYUNDAI coverage patterns
DISEASE_KEYWORDS = {
    '암': 10,
    '유사암': 8,
    '제자리암': 7,
    '경계성종양': 7,
    '뇌': 9,
    '뇌혈관': 10,
    '뇌졸중': 10,
    '뇌출혈': 10,
    '심장': 9,
    '심혈관': 10,  # STEP NEXT-58-E
    '심혈관질환': 10,  # STEP NEXT-58-E
    '심장질환': 10,  # STEP NEXT-58-E
    '허혈성심장': 10,
    '후유장해': 10,
    '상해': 10,
    '질병': 8,
    '부정맥': 9,
    '골절': 9,
    '화상': 9,
}

ACTION_KEYWORDS = {
    '진단비': 10,
    '수술비': 10,
    '입원일당': 10,
    '입원비': 9,
    '통원': 8,
    '치료비': 9,
    '약물': 8,
    '방사선': 8,
    '항암': 9,
    '항암약물': 10,
    '항암방사선': 10,
}

SPECIAL_KEYWORDS = {
    '다빈치': 15,
    '로봇': 12,
    'CAR-T': 15,
    '카티': 12,
    '표적항암': 15,
    '표적': 10,
    '호르몬': 10,
    '혈전용해': 15,
}

MODIFIER_KEYWORDS = {
    '최초1회': 3,
    '최초1회한': 3,
    '연간1회한': 3,
    '갱신형': 2,
    '3~100%': 5,
    '20~100%': 5,
    '1-180': 5,
}


class CandidateMapper:
    """
    LEVEL 1 Candidate Mapper (Deterministic Token Matching)

    STEP NEXT-58-E: LEVEL 1.5 - HYUNDAI-specific normalization enhancement
    """

    def __init__(self, mapping_excel_path: Path):
        self.mapping_excel_path = mapping_excel_path
        self.canonical_df = self._load_canonical_mapping()
        self.canonical_index = self._build_canonical_index()

    def _load_canonical_mapping(self) -> pd.DataFrame:
        """Load 신정원 canonical mapping Excel (SSOT)."""
        df = pd.read_excel(self.mapping_excel_path)
        required_cols = ['ins_cd', 'cre_cvr_cd', '신정원코드명', '담보명(가입설계서)']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
        return df

    def _build_canonical_index(self) -> Dict[str, List[Dict]]:
        """
        Build canonical name index for candidate matching.

        Returns:
            {
                'canonical_name': [
                    {'code': 'A1234', 'name': '...', 'tokens': {...}},
                    ...
                ]
            }
        """
        # Get unique canonical names
        unique_canonical = self.canonical_df[['cre_cvr_cd', '신정원코드명']].drop_duplicates()

        index = {}
        for _, row in unique_canonical.iterrows():
            code = row['cre_cvr_cd']
            name = row['신정원코드명']

            tokens = self._tokenize(name)

            if name not in index:
                index[name] = []

            index[name].append({
                'code': code,
                'name': name,
                'tokens': tokens
            })

        return index

    @staticmethod
    def normalize_for_candidate_hyundai(text: str) -> str:
        """
        STEP NEXT-58-E: HYUNDAI-specific normalization for candidate matching.

        Cleanup rules (deterministic):
        1. Remove newlines/tabs
        2. Remove "담보" suffix and fragments
        3. Fix broken parentheses
        4. Remove short fragments

        Args:
            text: Original coverage name

        Returns:
            Normalized text for candidate matching
        """
        normalized = text

        # 1. Remove newlines/tabs, collapse whitespace
        normalized = re.sub(r'[\n\t]+', '', normalized)
        normalized = re.sub(r'\s{2,}', ' ', normalized)

        # 2. Remove "담보" suffix patterns
        # "(갱신형)담보" → "(갱신형)"
        # "Ⅱ담보" → "Ⅱ"
        # "담보" → ""
        normalized = re.sub(r'\)\s*\(갱신형\)\s*담보$', ')(갱신형)', normalized)
        normalized = re.sub(r'[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹ]+\s*담보$', '', normalized)
        normalized = re.sub(r'\s*담보$', '', normalized)

        # 3. Fix broken parentheses
        # Remove trailing "("
        normalized = re.sub(r'\($', '', normalized)
        # Remove leading ")"
        normalized = re.sub(r'^\)', '', normalized)

        # 4. Remove short fragments (length < 4 with only parens/numbers)
        tokens_before = normalized.split()
        tokens_after = []
        for token in tokens_before:
            # Keep if length >= 4 OR has Korean chars
            if len(token) >= 4 or re.search(r'[가-힣]', token):
                tokens_after.append(token)
        normalized = ' '.join(tokens_after)

        return normalized.strip()

    @staticmethod
    def expand_tokens_hyundai(text: str, base_tokens: Set[str]) -> Set[str]:
        """
        STEP NEXT-58-E: HYUNDAI-specific token expansion.

        Expansion rules (deterministic):
        - "I49" / "I-49" / "Ⅰ49" → add "부정맥" token
        - "CAR-T" / "카티" → ensure both present
        - "다빈치" / "로봇" → ensure both present
        - "주요심장염증" → add "심장", "염증"
        - "대동맥판막협착증" → add "대동맥", "판막"

        Args:
            text: Normalized text
            base_tokens: Base token set from _tokenize()

        Returns:
            Expanded token set
        """
        expanded = base_tokens.copy()

        text_lower = text.lower()

        # Rule 1: I49 variants → 부정맥
        if any(pattern in text for pattern in ['I49', 'I-49', 'Ⅰ49', '(I49)', '(Ⅰ49)']):
            expanded.add('부정맥')
            expanded.add('I49')

        # Rule 2: CAR-T / 카티 → both
        if 'CAR-T' in text or '카티' in text or 'car-t' in text_lower:
            expanded.add('CAR-T')
            expanded.add('카티')

        # Rule 3: 다빈치 / 로봇 → both
        if '다빈치' in text or '로봇' in text:
            expanded.add('다빈치')
            expanded.add('로봇')

        # Rule 4: 주요심장염증 → components
        if '주요심장염증' in text or '심장염증' in text:
            expanded.add('심장')
            expanded.add('염증')

        # Rule 5: 대동맥판막협착증 → components
        if '대동맥판막협착증' in text or '판막협착' in text:
            expanded.add('대동맥')
            expanded.add('판막')

        # Rule 6: 심근병증 → 심장 + 병증
        if '심근병증' in text:
            expanded.add('심장')
            expanded.add('병증')

        return expanded

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """
        Extract tokens from coverage name.

        Tokens include:
        - Korean words (2+ chars)
        - English words (CAR-T, etc)
        - Numbers with context (3~100%, 1-180, etc)
        - Special patterns (다빈치, 로봇, etc)
        """
        text_lower = text.lower()
        tokens = set()

        # Special patterns (exact match)
        special_patterns = [
            'CAR-T', '카티', '다빈치', '로봇', '표적항암', '혈전용해',
            '항암약물', '항암방사선', '항암', '후유장해', '부정맥'
        ]
        for pattern in special_patterns:
            if pattern.lower() in text_lower or pattern in text:
                tokens.add(pattern)

        # Korean words (2+ chars)
        korean_words = re.findall(r'[가-힣]{2,}', text)
        tokens.update(korean_words)

        # Number patterns (ranges, percentages)
        number_patterns = re.findall(r'\d+[~\-]\d+%?', text)
        tokens.update(number_patterns)

        # Single words (진단비, 수술비, etc)
        # STEP NEXT-58-E: Added more action keywords for better matching
        common_suffixes = [
            '진단비', '진단', '수술비', '수술', '입원일당', '입원비', '입원',
            '치료비', '치료', '약물', '방사선'
        ]
        for suffix in common_suffixes:
            if suffix in text:
                tokens.add(suffix)

        return tokens

    def score_candidate(
        self,
        query_tokens: Set[str],
        candidate_tokens: Set[str],
        query_normalized: str,
        candidate_name: str
    ) -> Tuple[float, List[str], List[str]]:
        """
        Score candidate based on token matching (deterministic).

        Scoring rules:
        1. Disease keyword match: +10 per match
        2. Action keyword match: +10 per match
        3. Special keyword match: +15 per match
        4. Modifier keyword match: +3 per match
        5. Total token overlap: +5 per token
        6. Penalty for mismatched disease/action: -20

        Args:
            query_tokens: Tokens from unmapped coverage name
            candidate_tokens: Tokens from canonical name
            query_normalized: Original query text (for context check)
            candidate_name: Canonical name (for context check)

        Returns:
            (score, rules_hit, matched_terms)
        """
        score = 0.0
        rules_hit = []
        matched_terms = []

        # Common tokens
        common_tokens = query_tokens & candidate_tokens
        if not common_tokens:
            return 0.0, [], []

        # Rule 1: Disease keyword match
        disease_matches = []
        for disease, weight in DISEASE_KEYWORDS.items():
            if any(disease in token for token in common_tokens):
                score += weight
                disease_matches.append(disease)

        if disease_matches:
            rules_hit.append(f"DISEASE_MATCH({len(disease_matches)})")
            matched_terms.extend(disease_matches)

        # Rule 2: Action keyword match
        action_matches = []
        for action, weight in ACTION_KEYWORDS.items():
            if any(action in token for token in common_tokens):
                score += weight
                action_matches.append(action)

        if action_matches:
            rules_hit.append(f"ACTION_MATCH({len(action_matches)})")
            matched_terms.extend(action_matches)

        # Rule 3: Special keyword match (high value)
        special_matches = []
        for special, weight in SPECIAL_KEYWORDS.items():
            if any(special.lower() in token.lower() for token in common_tokens):
                score += weight
                special_matches.append(special)

        if special_matches:
            rules_hit.append(f"SPECIAL_MATCH({len(special_matches)})")
            matched_terms.extend(special_matches)

        # Rule 4: Modifier keyword match
        modifier_matches = []
        for modifier, weight in MODIFIER_KEYWORDS.items():
            if any(modifier in token for token in common_tokens):
                score += weight
                modifier_matches.append(modifier)

        if modifier_matches:
            rules_hit.append(f"MODIFIER_MATCH({len(modifier_matches)})")
            matched_terms.extend(modifier_matches)

        # Rule 5: General token overlap
        overlap_score = len(common_tokens) * 5
        score += overlap_score
        rules_hit.append(f"TOKEN_OVERLAP({len(common_tokens)})")

        # Rule 6: Penalty for disease/action mismatch
        # Check if disease in query but different disease in candidate
        query_diseases = [d for d in DISEASE_KEYWORDS if d in query_normalized]
        candidate_diseases = [d for d in DISEASE_KEYWORDS if d in candidate_name]

        if query_diseases and candidate_diseases:
            if not any(qd in candidate_name for qd in query_diseases):
                score -= 20
                rules_hit.append("DISEASE_MISMATCH_PENALTY")

        # Same for actions
        query_actions = [a for a in ACTION_KEYWORDS if a in query_normalized]
        candidate_actions = [a for a in ACTION_KEYWORDS if a in candidate_name]

        if query_actions and candidate_actions:
            if not any(qa in candidate_name for qa in query_actions):
                score -= 20
                rules_hit.append("ACTION_MISMATCH_PENALTY")

        return max(0.0, score), rules_hit, matched_terms

    def find_candidates(
        self,
        coverage_name_normalized: str,
        top_k: int = 10,
        min_confidence: float = 0.75,
        insurer: str = None
    ) -> List[Dict]:
        """
        Find top-K candidate matches for unmapped coverage.

        STEP NEXT-58-E: LEVEL 1.5 - HYUNDAI-specific enhancement.

        Args:
            coverage_name_normalized: Normalized coverage name from Step2-a
            top_k: Number of top candidates to return
            min_confidence: Minimum confidence threshold (0-1)
            insurer: Insurer code for LEVEL 1.5 branching (optional)

        Returns:
            List of candidate dicts sorted by score
        """
        # STEP NEXT-58-E: HYUNDAI-specific preprocessing
        if insurer and insurer.lower() == 'hyundai':
            # Apply HYUNDAI normalization
            normalized_for_candidate = self.normalize_for_candidate_hyundai(coverage_name_normalized)
            base_tokens = self._tokenize(normalized_for_candidate)
            query_tokens = self.expand_tokens_hyundai(normalized_for_candidate, base_tokens)
            applied_rules = ['HYUNDAI_NORMALIZE', 'HYUNDAI_TOKEN_EXPAND']
        else:
            # Standard LEVEL 1 processing
            normalized_for_candidate = coverage_name_normalized
            query_tokens = self._tokenize(coverage_name_normalized)
            applied_rules = []

        if not query_tokens:
            return []

        candidates = []

        for canonical_name, entries in self.canonical_index.items():
            for entry in entries:
                candidate_tokens = entry['tokens']

                score, rules_hit, matched_terms = self.score_candidate(
                    query_tokens,
                    candidate_tokens,
                    normalized_for_candidate,
                    canonical_name
                )

                if score > 0:
                    candidates.append({
                        'candidate_coverage_code': entry['code'],
                        'candidate_canonical_name': entry['name'],
                        'raw_score': score,
                        'rules_hit': rules_hit,
                        'matched_terms': list(set(matched_terms)),
                        'applied_rules': applied_rules,  # STEP NEXT-58-E
                        'candidate_input_text': normalized_for_candidate  # STEP NEXT-58-E
                    })

        # Sort by score descending
        candidates.sort(key=lambda x: x['raw_score'], reverse=True)

        # Take top-K
        top_candidates = candidates[:top_k]

        # Normalize confidence (0-1 scale)
        if top_candidates:
            max_score = top_candidates[0]['raw_score']
            if max_score > 0:
                for cand in top_candidates:
                    cand['confidence'] = min(1.0, cand['raw_score'] / (max_score + 20))

        # Filter by min_confidence
        filtered = [c for c in top_candidates if c.get('confidence', 0) >= min_confidence]

        return filtered

    def generate_candidate_for_unmapped(
        self,
        unmapped_entry: Dict,
        top_k: int = 3,
        min_confidence: float = 0.5
    ) -> Optional[Dict]:
        """
        Generate candidate for single unmapped entry.

        STEP NEXT-58-E: Pass insurer to enable LEVEL 1.5 for HYUNDAI.

        Args:
            unmapped_entry: Unmapped entry from Step2-b mapping report
            top_k: Number of candidates to consider
            min_confidence: Minimum confidence threshold

        Returns:
            Candidate dict or None if no candidate found
        """
        coverage_name_normalized = unmapped_entry.get(
            'coverage_name_normalized',
            unmapped_entry['coverage_name_raw']
        )

        # STEP NEXT-58-E: Pass insurer for LEVEL 1.5
        insurer = unmapped_entry.get('insurer')

        candidates = self.find_candidates(
            coverage_name_normalized,
            top_k=top_k,
            min_confidence=min_confidence,
            insurer=insurer  # STEP NEXT-58-E
        )

        if not candidates:
            return None

        # Return best candidate
        best = candidates[0]

        return {
            'candidate_coverage_code': best['candidate_coverage_code'],
            'candidate_canonical_name': best['candidate_canonical_name'],
            'confidence': best['confidence'],
            'rules_hit': best['rules_hit'],
            'matched_terms': best['matched_terms'],
            'applied_rules': best.get('applied_rules', []),  # STEP NEXT-58-E
            'candidate_input_text': best.get('candidate_input_text', coverage_name_normalized),  # STEP NEXT-58-E
            'explain': self._generate_explain(
                coverage_name_normalized,
                best['candidate_canonical_name'],
                best['matched_terms'],
                best['confidence']
            )
        }

    @staticmethod
    def _generate_explain(
        query: str,
        candidate: str,
        matched_terms: List[str],
        confidence: float
    ) -> str:
        """Generate human-readable explanation for candidate."""
        if confidence >= 0.9:
            strength = "strong"
        elif confidence >= 0.75:
            strength = "good"
        else:
            strength = "weak"

        terms_str = ', '.join(matched_terms[:3])
        return f"{strength} match - shared tokens: {terms_str}"


def generate_candidate_report(
    mapping_report_jsonl: Path,
    output_jsonl: Path,
    mapping_excel_path: Path,
    min_confidence: float = 0.4  # STEP NEXT-58-E: Lowered from 0.5 for better recall
) -> Dict:
    """
    Generate candidate report for all unmapped entries.

    STEP NEXT-58-E: Lowered default min_confidence for better recall.

    Args:
        mapping_report_jsonl: Input Step2-b mapping report
        output_jsonl: Output candidate report path
        mapping_excel_path: 신정원 Excel path
        min_confidence: Minimum confidence threshold (default 0.4)

    Returns:
        Statistics dict
    """
    if not mapping_report_jsonl.exists():
        return {'error': 'INPUT_NOT_FOUND'}

    # Load mapper
    mapper = CandidateMapper(mapping_excel_path)

    # Read mapping report
    entries = []
    with open(mapping_report_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Filter unmapped
    unmapped = [e for e in entries if e.get('mapping_method') == 'unmapped']

    # Generate candidates
    candidate_count = 0
    no_candidate_count = 0

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for entry in unmapped:
            candidate = mapper.generate_candidate_for_unmapped(
                entry,
                min_confidence=min_confidence
            )

            output_entry = {
                'insurer': entry['insurer'],
                'coverage_name_raw': entry['coverage_name_raw'],
                'coverage_name_normalized': entry.get('coverage_name_raw'),  # Fallback
                'mapping_method': entry['mapping_method'],
                'candidate': candidate
            }

            if candidate:
                candidate_count += 1
            else:
                no_candidate_count += 1

            f.write(json.dumps(output_entry, ensure_ascii=False) + '\n')

    return {
        'total_unmapped': len(unmapped),
        'candidate_generated': candidate_count,
        'no_candidate': no_candidate_count,
        'candidate_rate': candidate_count / len(unmapped) if unmapped else 0.0
    }
