"""
STEP NEXT-61: Product and Variant Identity Extraction

Constitutional rules:
1. Product name = ONLY from page 1 of proposal PDF
2. Variant context = ONLY from "상품명 바로 아래 블록" (page 1)
3. NO inference from file names / folder names
4. Explicit "default" when variant not found
"""

import re
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class ProductVariantExtractor:
    """Extract product name and variant context from proposal PDF page 1"""

    # Product name patterns (insurer-specific)
    PRODUCT_PATTERNS = {
        'kb': [
            r'(KB\s+[가-힣a-zA-Z\s]+건강보험[^\n]{0,50})',
            r'(KB\s+닥터플러스[^\n]{0,50})',
        ],
        'db': [
            r'(무배당\s+프로미라이프[^\n]{0,80})',
            r'(프로미라이프[^\n]{0,80}종합보험)',
        ],
        'lotte': [
            r'(무배당\s+let:smile[^\n]{0,80})',
            r'(let:smile[^\n]{0,80}건강보험)',
        ],
        'samsung': [
            r'(삼성화재\s+[^\n]{0,50}건강보험)',
        ],
        'hanwha': [
            r'(한화\s+[^\n]{0,50}보험)',
        ],
        'hyundai': [
            r'(현대해상\s+[^\n]{0,50}보험)',
        ],
        'meritz': [
            r'(메리츠\s+[^\n]{0,50}보험)',
        ],
        'heungkuk': [
            r'(흥국화재\s+[^\n]{0,50}보험)',
        ],
    }

    # Variant detection patterns
    VARIANT_PATTERNS = {
        'age_band': [
            (r'(\d+)[-~](\d+)세', 'age_range'),  # "15-40세", "41-60세"
            (r'(\d+)세\s*이하', 'age_max'),      # "40세이하"
            (r'(\d+)세\s*이상', 'age_min'),      # "41세이상"
        ],
        'sex': [
            (r'포맨|남자', 'male'),
            (r'포우먼|여자', 'female'),
        ],
    }

    def __init__(self, insurer: str, pdf_path: Path, variant_hint: Optional[str] = None):
        """
        Args:
            insurer: Insurer code (kb, db, lotte, etc.)
            pdf_path: Path to proposal PDF
            variant_hint: Optional variant hint from file name (for validation only)
        """
        self.insurer = insurer.lower()
        self.pdf_path = pdf_path
        self.variant_hint = variant_hint

    def extract(self) -> Dict[str, Any]:
        """
        Extract product and variant from proposal PDF page 1

        Returns:
            {
                "product": {
                    "product_name_raw": str,
                    "product_name_normalized": str,
                    "product_key": str
                },
                "variant": {
                    "variant_key": str,
                    "variant_axis": List[str],
                    "variant_values": Dict[str, Any]
                },
                "proposal_context": {
                    "context_block_raw": Optional[str],
                    "context_fields": Dict[str, Any]
                }
            }
        """
        # Open PDF and extract page 1 text
        doc = fitz.open(str(self.pdf_path))
        if len(doc) == 0:
            raise ValueError(f"PDF has no pages: {self.pdf_path}")

        page1 = doc[0]
        page1_text = page1.get_text()
        doc.close()

        # Extract product name
        product = self._extract_product(page1_text)

        # Extract variant context
        variant, proposal_context = self._extract_variant(page1_text, product)

        return {
            "product": product,
            "variant": variant,
            "proposal_context": proposal_context,
        }

    def _extract_product(self, page1_text: str) -> Dict[str, Any]:
        """Extract product name from page 1 text"""
        # Get insurer-specific patterns
        patterns = self.PRODUCT_PATTERNS.get(self.insurer, [])

        product_name_raw = None
        for pattern in patterns:
            match = re.search(pattern, page1_text, re.MULTILINE)
            if match:
                product_name_raw = match.group(1).strip()
                break

        # Fallback: search for general pattern (any line with "보험" in first 500 chars)
        if not product_name_raw:
            lines = page1_text[:500].split('\n')
            for line in lines:
                if '보험' in line and len(line) > 5 and len(line) < 100:
                    product_name_raw = line.strip()
                    logger.warning(
                        f"{self.insurer}: Product name found with fallback pattern: {product_name_raw}"
                    )
                    break

        if not product_name_raw:
            raise ValueError(
                f"{self.insurer}: Product name not found in page 1. "
                f"Page 1 text (first 200 chars): {page1_text[:200]}"
            )

        # Normalize product name (remove whitespace, parentheses content simplification)
        product_name_normalized = self._normalize_product_name(product_name_raw)

        # Generate product key
        product_key = f"{self.insurer}__{product_name_normalized}"

        return {
            "product_name_raw": product_name_raw,
            "product_name_normalized": product_name_normalized,
            "product_key": product_key,
        }

    def _normalize_product_name(self, raw: str) -> str:
        """
        Normalize product name for consistent key generation

        Rules:
        - Remove all whitespace
        - Keep Korean, English, numbers, colon only
        - Remove excessive parentheses content (keep short codes)
        """
        # Remove newlines, extra spaces
        normalized = re.sub(r'\s+', '', raw)

        # Remove long parentheses content (>15 chars), keep short codes
        normalized = re.sub(r'\([^)]{15,}\)', '', normalized)

        # Keep only Korean, English, numbers, colon
        normalized = re.sub(r'[^가-힣a-zA-Z0-9:]', '', normalized)

        return normalized

    def _extract_variant(
        self,
        page1_text: str,
        product: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract variant context from page 1 text

        Strategy:
        1. Find product_name line position
        2. Extract next 3-5 lines as context block
        3. Pattern match for age_band / sex
        4. If no match → variant_key = "default"

        Returns:
            (variant_dict, proposal_context_dict)
        """
        product_name_raw = product["product_name_raw"]
        lines = page1_text.split('\n')

        # Find product name line index
        product_line_idx = None
        for i, line in enumerate(lines):
            if product_name_raw[:30] in line:  # Match first 30 chars
                product_line_idx = i
                break

        # Extract context block (next 3-5 lines after product name)
        context_block_raw = None
        if product_line_idx is not None and product_line_idx + 5 < len(lines):
            context_lines = lines[product_line_idx + 1:product_line_idx + 6]
            context_block_raw = '\n'.join([l.strip() for l in context_lines if l.strip()])

        # If context block not found, use full page 1 first 500 chars
        if not context_block_raw:
            context_block_raw = page1_text[:500]

        # Pattern matching for variant
        variant_values = {}
        variant_axis = []

        # Check age_band patterns
        for pattern, field_name in self.VARIANT_PATTERNS['age_band']:
            match = re.search(pattern, context_block_raw)
            if match:
                if field_name == 'age_range':
                    age_min = int(match.group(1))
                    age_max = int(match.group(2))
                    variant_values['age_range'] = f"{age_min}-{age_max}세"
                    # Classify into age_band
                    if age_max <= 40:
                        variant_values['age_band'] = 'under40'
                    elif age_min >= 41:
                        variant_values['age_band'] = 'over41'
                    else:
                        variant_values['age_band'] = f"{age_min}_{age_max}"
                    variant_axis.append('age_band')
                elif field_name == 'age_max':
                    age_max = int(match.group(1))
                    variant_values['age_max'] = f"{age_max}세이하"
                    variant_values['age_band'] = f"under{age_max}"
                    variant_axis.append('age_band')
                elif field_name == 'age_min':
                    age_min = int(match.group(1))
                    variant_values['age_min'] = f"{age_min}세이상"
                    variant_values['age_band'] = f"over{age_min}"
                    variant_axis.append('age_band')
                break  # Take first match only

        # Check sex patterns
        for pattern, sex_value in self.VARIANT_PATTERNS['sex']:
            if re.search(pattern, context_block_raw):
                variant_values['sex'] = sex_value
                variant_axis.append('sex')
                break  # Take first match only

        # Generate variant_key
        if variant_axis:
            # Create variant_key from axis values
            key_parts = []
            if 'sex' in variant_axis:
                key_parts.append(variant_values['sex'])
            if 'age_band' in variant_axis:
                key_parts.append(variant_values['age_band'])
            variant_key = '_'.join(key_parts)
        else:
            variant_key = 'default'

        # Validate against hint (if provided)
        if self.variant_hint and variant_key != 'default' and self.variant_hint != variant_key:
            logger.warning(
                f"{self.insurer}: Variant mismatch - "
                f"hint: {self.variant_hint}, extracted: {variant_key}. "
                f"Using extracted value (hint is for reference only)."
            )

        variant_dict = {
            "variant_key": variant_key,
            "variant_axis": variant_axis,
            "variant_values": variant_values,
        }

        proposal_context_dict = {
            "context_block_raw": context_block_raw if variant_key != 'default' else None,
            "context_fields": variant_values,
        }

        return variant_dict, proposal_context_dict


def extract_insurer_code(insurer: str) -> str:
    """
    Map insurer name to standardized code (ins_cd)

    STEP NEXT-61: This is the SSOT for insurer code mapping.
    """
    INSURER_CODE_MAP = {
        'samsung': 'S01',
        'kb': 'K01',
        'meritz': 'M01',
        'hanwha': 'H01',
        'hyundai': 'Y01',
        'db': 'D01',
        'lotte': 'L01',
        'heungkuk': 'E01',
    }

    return INSURER_CODE_MAP.get(insurer.lower(), insurer.upper()[:3] + '01')
