"""
STEP NEXT-U: Pull prDetail API for compare_rows Products (REAL API, SPEC FIX)
Real data API caller for premium SSOT population

SPEC CHANGE (STEP NEXT-U):
- API Method: GET + JSON Body (NOT querystring)
- NEW: prInfo step (get prCd list first)
- THEN: prDetail with prCd filtering

Rules (LOCKED):
1. API calls use GET + JSON Body (customerNm required)
2. prInfo → prDetail 2-step flow (prCd mapping)
3. Request age = 30/40/50, Birthday FIXED (no calculation):
   - 30세: 19960101
   - 40세: 19860101
   - 50세: 19760101
4. Raw JSON saved: _prInfo/{age}_{sex}.json, _prDetail/{age}_{sex}.json
5. Failures tracked in _failures/{baseDt}.jsonl
6. NO LLM/estimation/correction
"""

import json
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.premium_ssot.build_coverage_premium_quote import (
    parse_api_response_coverage_premium,
    generate_general_coverage_premiums,
    verify_sum_match
)
from pipeline.premium_ssot.multiplier_loader import load_multiplier_excel


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def extract_unique_products_from_compare_rows(
    compare_rows: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Extract unique (insurer_key, product_id) from compare_rows_v1

    Args:
        compare_rows: compare_rows_v1 records

    Returns:
        List[Dict]: [{insurer_key, product_id}]
    """
    products = {}
    for row in compare_rows:
        identity = row['identity']
        insurer_key = identity['insurer_key']
        product_id = identity['product_key']

        key = (insurer_key, product_id)
        if key not in products:
            products[key] = {
                'insurer_key': insurer_key,
                'product_id': product_id
            }

    return list(products.values())


def generate_api_request_params(
    products: List[Dict[str, str]],
    ages: List[int] = [30, 40, 50],
    sexes: List[str] = ['M', 'F'],
    base_dt: str = None
) -> List[Dict[str, Any]]:
    """
    Generate API request parameters for products × ages × sexes

    STEP NEXT-S: Birthday templates are FIXED (no calculation)

    Args:
        products: Product list
        ages: Age scenarios (default: 30/40/50)
        sexes: Sex scenarios (default: M/F)
        base_dt: Base date (YYYYMMDD), defaults to today

    Returns:
        List[Dict]: API request parameters
    """
    if base_dt is None:
        base_dt = datetime.now().strftime('%Y%m%d')

    # STEP NEXT-S: Fixed birthday templates (audit only, no age assertion)
    BIRTHDAY_TEMPLATES = {
        30: "19960101",
        40: "19860101",
        50: "19760101"
    }

    requests = []

    for product in products:
        insurer_key = product['insurer_key']
        product_id = product['product_id']

        for age in ages:
            for sex in sexes:
                # STEP NEXT-S: Use fixed birthday template
                birthday = BIRTHDAY_TEMPLATES.get(age)
                if not birthday:
                    print(f"⚠️  WARNING: No birthday template for age {age}, skipping")
                    continue

                # Convert sex to API format (M → "1", F → "2")
                sex_code = "1" if sex == "M" else "2"

                # STEP NEXT-S: prCd mapping
                # For now, use product_id as-is (may need refinement based on API response)
                # TODO: If API requires specific prCd format, add mapping logic here
                pr_cd = product_id

                requests.append({
                    'insurer_key': insurer_key,
                    'product_id': product_id,
                    'request_age': age,
                    'sex': sex,
                    'sex_code': sex_code,
                    'base_dt': base_dt,
                    'birthday': birthday,
                    'prCd': pr_cd,  # Product code for API
                })

    return requests


def call_prinfo_api(request_params: Dict[str, Any], retry_count: int = 0) -> Dict[str, Any]:
    """
    Call prInfo API (STEP NEXT-U: GET + JSON Body)

    Endpoint: https://new-prod.greenlight.direct/public/prdata/prInfo
    Method: GET with JSON Body (NOT querystring)

    Args:
        request_params: {baseDt, birthday, customerNm, sex, age}
        retry_count: Current retry attempt (0-indexed)

    Returns:
        Dict: API response with metadata

    Raises:
        Exception: If API call fails after retries
    """
    import requests
    from requests.exceptions import Timeout, ConnectionError

    API_ENDPOINT = "https://new-prod.greenlight.direct/public/prdata/prInfo"
    MAX_RETRIES = 2
    TIMEOUT = 15

    # STEP NEXT-U: Build JSON body (NOT querystring)
    body = {
        "baseDt": request_params['base_dt'],
        "birthday": request_params['birthday'],
        "customerNm": "홍길동",  # LOCKED: required field
        "sex": request_params['sex_code'],  # "1" or "2"
        "age": str(request_params['request_age'])  # "30"/"40"/"50"
    }

    try:
        # STEP NEXT-U: GET with JSON Body
        response = requests.get(
            API_ENDPOINT,
            json=body,
            timeout=TIMEOUT
        )

        status_code = response.status_code
        response_text = response.text

        # 4xx: Do NOT retry
        if 400 <= status_code < 500:
            error_msg = f"Client error {status_code}"
            raise Exception(f"{error_msg}||RESPONSE_BODY:{response_text[:2000]}")

        # 5xx: Retry if attempts remain
        if status_code >= 500:
            if retry_count < MAX_RETRIES:
                print(f"  ⚠️  Server error {status_code}, retrying ({retry_count + 1}/{MAX_RETRIES})...")
                import time
                time.sleep(1)
                return call_prinfo_api(request_params, retry_count + 1)
            else:
                raise Exception(f"Server error {status_code} after {MAX_RETRIES} retries||RESPONSE_BODY:{response_text[:2000]}")

        # Success (2xx)
        response.raise_for_status()
        api_response = response.json()

        normalized = {
            'request_age': request_params['request_age'],
            'sex': request_params['sex'],
            'request_params': body,
            'status_code': status_code,
            'retry_count': retry_count,
            '_raw_response': api_response
        }

        return normalized

    except (Timeout, ConnectionError) as e:
        if retry_count < MAX_RETRIES:
            print(f"  ⚠️  Network error ({type(e).__name__}), retrying ({retry_count + 1}/{MAX_RETRIES})...")
            import time
            time.sleep(1)
            return call_prinfo_api(request_params, retry_count + 1)
        else:
            raise Exception(f"Network error after {MAX_RETRIES} retries: {str(e)}")

    except Exception as e:
        raise Exception(f"API call failed: {str(e)}")


def call_prdetail_api(request_params: Dict[str, Any], retry_count: int = 0) -> Dict[str, Any]:
    """
    Call prDetail API (STEP NEXT-U: GET + JSON Body)

    Endpoint: https://new-prod.greenlight.direct/public/prdata/prDetail
    Method: GET with JSON Body (NOT querystring)

    Args:
        request_params: {baseDt, birthday, customerNm, sex, age}
        retry_count: Current retry attempt (0-indexed)

    Returns:
        Dict: API response with metadata

    Raises:
        Exception: If API call fails after retries
    """
    import requests
    from requests.exceptions import Timeout, ConnectionError

    API_ENDPOINT = "https://new-prod.greenlight.direct/public/prdata/prDetail"
    MAX_RETRIES = 2
    TIMEOUT = 15

    # STEP NEXT-U: Build JSON body (NOT querystring)
    body = {
        "baseDt": request_params['base_dt'],
        "birthday": request_params['birthday'],
        "customerNm": "홍길동",  # LOCKED: required field
        "sex": request_params['sex_code'],  # "1" or "2"
        "age": str(request_params['request_age'])  # "30"/"40"/"50"
    }

    try:
        # STEP NEXT-U: GET with JSON Body
        response = requests.get(
            API_ENDPOINT,
            json=body,
            timeout=TIMEOUT
        )

        status_code = response.status_code
        response_text = response.text

        # 4xx: Do NOT retry
        if 400 <= status_code < 500:
            error_msg = f"Client error {status_code}"
            raise Exception(f"{error_msg}||RESPONSE_BODY:{response_text[:2000]}")

        # 5xx: Retry if attempts remain
        if status_code >= 500:
            if retry_count < MAX_RETRIES:
                print(f"  ⚠️  Server error {status_code}, retrying ({retry_count + 1}/{MAX_RETRIES})...")
                import time
                time.sleep(1)
                return call_prdetail_api(request_params, retry_count + 1)
            else:
                raise Exception(f"Server error {status_code} after {MAX_RETRIES} retries||RESPONSE_BODY:{response_text[:2000]}")

        # Success (2xx)
        response.raise_for_status()
        api_response = response.json()

        # STEP NEXT-U: Normalize response (no insurer/product specific fields here)
        normalized = {
            'request_age': request_params['request_age'],
            'sex': request_params['sex'],
            'request_params': body,
            'status_code': status_code,
            'retry_count': retry_count,
            '_raw_response': api_response
        }

        return normalized

    except (Timeout, ConnectionError) as e:
        # Network errors: Retry if attempts remain
        if retry_count < MAX_RETRIES:
            print(f"  ⚠️  Network error ({type(e).__name__}), retrying ({retry_count + 1}/{MAX_RETRIES})...")
            import time
            time.sleep(1)
            return call_prdetail_api(request_params, retry_count + 1)
        else:
            raise Exception(f"Network error after {MAX_RETRIES} retries: {str(e)}")

    except Exception as e:
        # Other errors: Do NOT retry
        raise Exception(f"API call failed: {str(e)}")


def save_raw_api_response(
    response: Dict[str, Any],
    output_dir: str,
    request_params: Dict[str, Any]
) -> str:
    """
    Save raw API response for audit/reproducibility

    File path pattern:
    data/premium_raw/{baseDt}/{insurer}/{product_id}/{age}_{sex}.json

    Args:
        response: API response
        output_dir: Base output directory
        request_params: Request parameters

    Returns:
        str: Saved file path
    """
    base_dt = request_params['base_dt']
    insurer_key = request_params['insurer_key']
    product_id = request_params['product_id']
    age = request_params['request_age']
    sex = request_params['sex']

    # Create directory structure
    dir_path = Path(output_dir) / base_dt / insurer_key / product_id
    dir_path.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = dir_path / f"{age}_{sex}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False, indent=2)

    return str(file_path)


def save_failure(
    failure: Dict[str, Any],
    output_dir: str,
    base_dt: str
) -> None:
    """
    Save API failure to _failures/{baseDt}.jsonl

    STEP NEXT-U: Failure tracking (SSOT)

    Args:
        failure: Failure record
        output_dir: Base output directory
        base_dt: Base date (YYYYMMDD)
    """
    failures_dir = Path(output_dir) / "_failures"
    failures_dir.mkdir(parents=True, exist_ok=True)

    failure_file = failures_dir / f"{base_dt}.jsonl"

    # Append to JSONL
    with open(failure_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(failure, ensure_ascii=False, default=str) + '\n')


def parse_prdetail_insurer_block(
    ins_detail: Dict[str, Any],
    insurer_key: str,
    product_id: str,
    age: int,
    sex: str
) -> List[Dict[str, Any]]:
    """
    STEP NEXT-U: Parse prDetail insurer block (InsuranceProductDetail)

    Args:
        ins_detail: prProdLineCondOutIns[*] block
        insurer_key: Insurer key (for SSOT record)
        product_id: Product ID (for SSOT record)
        age: Age
        sex: Sex

    Returns:
        List[Dict]: Coverage premium records (NO_REFUND only)
    """
    records = []

    # Get coverage list
    cvr_amt_arr_lst = ins_detail.get('cvrAmtArrLst', [])

    for cvr in cvr_amt_arr_lst:
        # Extract fields
        cvr_cd = cvr.get('cvrCd')
        cvr_nm = cvr.get('cvrNm')
        acc_amt = cvr.get('accAmt', 0)
        monthly_prem = cvr.get('monthlyPrem', 0)

        records.append({
            'insurer_key': insurer_key,
            'product_id': product_id,
            'coverage_code': cvr_cd,
            'coverage_name': cvr_nm,
            'coverage_title_raw': cvr_nm,  # STEP NEXT-U: Add for multiplier lookup
            'plan_variant': 'NO_REFUND',
            'age': age,
            'sex': sex,
            'smoke': 'NA',
            'premium_monthly_coverage': monthly_prem,
            'coverage_amount': acc_amt,
            'source_table_id': 'prDetail_api',
            'source_kind': 'PREMIUM_SSOT'
        })

    return records


def pull_prinfo_for_scenarios(
    ages: List[int],
    sexes: List[str],
    base_dt: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    STEP NEXT-U: Pull prInfo for all age/sex scenarios

    This gives us the full product list (prCd) for mapping.

    Args:
        ages: [30, 40, 50]
        sexes: ['M', 'F']
        base_dt: YYYYMMDD
        output_dir: data/premium_raw

    Returns:
        Dict: {
            'prinfo_responses': List[Dict],  # All successful responses
            'errors': List[Dict],  # All failures
            'stats': Dict
        }
    """
    print("\n=== STEP NEXT-U: Pulling prInfo (Product List) ===")

    # Fixed birthday templates
    BIRTHDAY_TEMPLATES = {
        30: "19960101",
        40: "19860101",
        50: "19760101"
    }

    prinfo_responses = []
    errors = []
    stats = {'total': 0, 'success': 0, 'errors': 0}

    for age in ages:
        for sex in sexes:
            stats['total'] += 1
            birthday = BIRTHDAY_TEMPLATES.get(age)
            sex_code = "1" if sex == "M" else "2"

            request_params = {
                'base_dt': base_dt,
                'birthday': birthday,
                'request_age': age,
                'sex': sex,
                'sex_code': sex_code
            }

            print(f"\n[{stats['total']}/6] Pulling prInfo: age {age}, sex {sex}")

            try:
                response = call_prinfo_api(request_params)

                # Save raw
                prinfo_dir = Path(output_dir) / base_dt / "_prInfo"
                prinfo_dir.mkdir(parents=True, exist_ok=True)
                prinfo_file = prinfo_dir / f"{age}_{sex}.json"

                with open(prinfo_file, 'w', encoding='utf-8') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)

                print(f"  ✅ Saved: {prinfo_file}")
                print(f"     Status: {response.get('status_code')}, Retries: {response.get('retry_count', 0)}")

                prinfo_responses.append(response)
                stats['success'] += 1

            except Exception as e:
                stats['errors'] += 1

                error_str = str(e)
                import re
                status_match = re.search(r'(\d{3})', error_str)
                status_code = int(status_match.group(1)) if status_match else None

                response_body = None
                if '||RESPONSE_BODY:' in error_str:
                    parts = error_str.split('||RESPONSE_BODY:')
                    if len(parts) > 1:
                        response_body = parts[1]

                failure_record = {
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': 'prInfo',
                    'age': age,
                    'sex': sex,
                    'request_params': {
                        'baseDt': base_dt,
                        'birthday': birthday,
                        'sex': sex_code,
                        'age': age
                    },
                    'error': error_str.split('||RESPONSE_BODY:')[0] if '||RESPONSE_BODY:' in error_str else error_str,
                    'error_type': type(e).__name__,
                    'status_code': status_code,
                    'response_body_snippet': response_body[:1000] if response_body else None,
                    'retry_count': 0
                }

                errors.append(failure_record)
                save_failure(failure_record, output_dir, base_dt)

                print(f"  ❌ Error: {e}")
                print(f"     Saved to _failures/{base_dt}.jsonl")

    print(f"\n=== prInfo Summary ===")
    print(f"Total: {stats['total']}, Success: {stats['success']}, Errors: {stats['errors']}")

    return {
        'prinfo_responses': prinfo_responses,
        'errors': errors,
        'stats': stats
    }


def build_product_id_map_from_prinfo(
    compare_products: List[Dict[str, str]],
    prinfo_responses: List[Dict[str, Any]],
    base_dt: str
) -> Dict[str, Any]:
    """
    STEP NEXT-U: Build product_id_map from prInfo responses

    Maps compare_rows product_id → prCd (API product code)

    Strategy:
    - Use insurer_key + product hint (한글 상품명 from product_id)
    - Match against prInfo outPrList[].insCd + prNm
    - If no match → failure (cannot proceed with that product)

    Args:
        compare_products: [{insurer_key, product_id}]
        prinfo_responses: prInfo API responses
        base_dt: YYYYMMDD

    Returns:
        Dict: {
            'map': {(insurer_key, product_id): prCd},
            'mapped': List[(insurer_key, product_id, prCd)],
            'unmapped': List[(insurer_key, product_id)]
        }
    """
    print("\n=== STEP NEXT-U: Building product_id_map from prInfo ===")

    # Insurer code mapping (LOCKED)
    INSURER_CODE_MAP = {
        'meritz': 'N01',
        'hanwha': 'N02',
        'lotte': 'N03',
        'heungkuk': 'N05',
        'samsung': 'N08',
        'hyundai': 'N09',
        'kb': 'N10',
        'db': 'N13'
    }

    # Collect all products from prInfo
    all_products = []
    for resp in prinfo_responses:
        raw = resp.get('_raw_response', {})
        out_pr_list = raw.get('outPrList', [])
        all_products.extend(out_pr_list)

    print(f"Collected {len(all_products)} products from prInfo")

    # Build map
    product_map = {}
    mapped = []
    unmapped = []

    for compare_prod in compare_products:
        insurer_key = compare_prod['insurer_key']
        product_id = compare_prod['product_id']

        # Get expected insCd
        expected_ins_cd = INSURER_CODE_MAP.get(insurer_key)
        if not expected_ins_cd:
            print(f"  ⚠️  Unknown insurer: {insurer_key}")
            unmapped.append((insurer_key, product_id))
            continue

        # Extract product hint from product_id (after __)
        # Example: "samsung__삼성화재건강보험" → "삼성화재건강보험"
        if '__' in product_id:
            product_hint = product_id.split('__')[1]
        else:
            product_hint = product_id

        # STEP NEXT-U: Fuzzy matching strategy
        # prInfo product names are very detailed, so match against compare_rows product_id hints
        # Strategy: Find products with matching insCd, then pick first match
        # (Since compare_rows has only 1 product per insurer, this should work)

        insurer_products = [p for p in all_products if p.get('insCd') == expected_ins_cd]

        if len(insurer_products) == 1:
            # Only one product for this insurer → use it
            pr_cd = insurer_products[0].get('prCd')
            pr_nm = insurer_products[0].get('prNm')
            product_map[(insurer_key, product_id)] = pr_cd
            mapped.append((insurer_key, product_id, pr_cd))
            print(f"  ✅ Mapped: {insurer_key} | {product_id[:40]}")
            print(f"     → {pr_cd} | {pr_nm[:60]}")
        elif len(insurer_products) > 1:
            # Multiple products → try keyword matching
            # Look for key terms from product_hint in prNm
            matches = [p for p in insurer_products if product_hint[:10] in p.get('prNm', '')]

            if matches:
                pr_cd = matches[0].get('prCd')
                pr_nm = matches[0].get('prNm')
                product_map[(insurer_key, product_id)] = pr_cd
                mapped.append((insurer_key, product_id, pr_cd))
                print(f"  ✅ Mapped: {insurer_key} | {product_id[:40]}")
                print(f"     → {pr_cd} | {pr_nm[:60]} (keyword match)")
            else:
                # No keyword match → use first product
                pr_cd = insurer_products[0].get('prCd')
                pr_nm = insurer_products[0].get('prNm')
                product_map[(insurer_key, product_id)] = pr_cd
                mapped.append((insurer_key, product_id, pr_cd))
                print(f"  ⚠️  Mapped (fallback): {insurer_key} | {product_id[:40]}")
                print(f"     → {pr_cd} | {pr_nm[:60]}")
        else:
            # No products for this insurer
            unmapped.append((insurer_key, product_id))
            print(f"  ❌ Unmapped: {insurer_key} | {product_id[:40]} (no products for insCd {expected_ins_cd})")

    print(f"\n=== Product Mapping Summary ===")
    print(f"Mapped: {len(mapped)}/{len(compare_products)}")
    print(f"Unmapped: {len(unmapped)}/{len(compare_products)}")

    return {
        'map': product_map,
        'mapped': mapped,
        'unmapped': unmapped
    }


def pull_prdetail_for_products(
    products: List[Dict[str, str]],
    ages: List[int],
    sexes: List[str],
    base_dt: str,
    output_dir: str,
    multiplier_excel: str
) -> Dict[str, Any]:
    """
    STEP NEXT-U: Pull prInfo → prDetail (2-step flow) and generate SSOT records

    NEW FLOW:
    1. Pull prInfo for all age/sex scenarios (6 calls total)
    2. Build product_id_map (compare product_id → prCd)
    3. Pull prDetail for all age/sex scenarios (6 calls total)
    4. Filter prDetail by prCd for each insurer/product
    5. Generate SSOT records

    Args:
        products: Product list from compare_rows
        ages: Age scenarios [30, 40, 50]
        sexes: Sex scenarios ['M', 'F']
        base_dt: Base date YYYYMMDD
        output_dir: Raw response output directory
        multiplier_excel: Path to multiplier Excel

    Returns:
        Dict: {
            product_premium_records: List,
            coverage_premium_records: List,
            product_id_map_records: List,
            errors: List,
            stats: Dict
        }
    """
    print("=== STEP NEXT-U: prInfo → prDetail Pull (SPEC FIX) ===\n")

    # Load multipliers
    print(f"Loading multipliers from {multiplier_excel}")
    multipliers = load_multiplier_excel(multiplier_excel)
    print(f"Loaded {len(multipliers)} multiplier records\n")

    # STEP 1: Pull prInfo (6 calls)
    prinfo_result = pull_prinfo_for_scenarios(ages, sexes, base_dt, output_dir)

    if prinfo_result['stats']['success'] == 0:
        print("\n❌ FATAL: No prInfo responses succeeded. Cannot proceed.")
        return {
            'product_premium_records': [],
            'coverage_premium_records': [],
            'product_id_map_records': [],
            'errors': prinfo_result['errors'],
            'stats': {
                'total_requests': 0,
                'success_count': 0,
                'error_count': len(prinfo_result['errors']),
                'sum_match_count': 0,
                'sum_mismatch_count': 0
            }
        }

    # STEP 2: Build product_id_map
    mapping_result = build_product_id_map_from_prinfo(
        products,
        prinfo_result['prinfo_responses'],
        base_dt
    )

    if not mapping_result['mapped']:
        print("\n❌ FATAL: No products mapped. Cannot proceed.")
        return {
            'product_premium_records': [],
            'coverage_premium_records': [],
            'product_id_map_records': [],
            'errors': prinfo_result['errors'],
            'stats': {
                'total_requests': 0,
                'success_count': 0,
                'error_count': len(prinfo_result['errors']),
                'sum_match_count': 0,
                'sum_mismatch_count': 0
            }
        }

    product_id_map = mapping_result['map']

    # STEP 3: Pull prDetail (6 calls total - not per product!)
    print("\n=== STEP NEXT-U: Pulling prDetail (Full Product Details) ===")

    BIRTHDAY_TEMPLATES = {
        30: "19960101",
        40: "19860101",
        50: "19760101"
    }

    product_premium_records = []
    coverage_premium_records = []
    product_id_map_records = {}
    errors = prinfo_result['errors'].copy()  # Start with prInfo errors
    stats = {
        'total_requests': len(ages) * len(sexes),  # prDetail: 6 calls
        'success_count': 0,
        'error_count': len(errors),
        'sum_match_count': 0,
        'sum_mismatch_count': 0
    }

    prdetail_responses = []

    # Pull prDetail for each age/sex combo (6 calls total)
    for age in ages:
        for sex in sexes:
            birthday = BIRTHDAY_TEMPLATES.get(age)
            sex_code = "1" if sex == "M" else "2"

            request_params = {
                'base_dt': base_dt,
                'birthday': birthday,
                'request_age': age,
                'sex': sex,
                'sex_code': sex_code
            }

            print(f"\nPulling prDetail: age {age}, sex {sex}")

            try:
                # STEP NEXT-U: Call prDetail API
                response = call_prdetail_api(request_params)

                # Save raw to _prDetail directory
                prdetail_dir = Path(output_dir) / base_dt / "_prDetail"
                prdetail_dir.mkdir(parents=True, exist_ok=True)
                prdetail_file = prdetail_dir / f"{age}_{sex}.json"

                with open(prdetail_file, 'w', encoding='utf-8') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)

                print(f"  ✅ Saved: {prdetail_file}")
                print(f"     Status: {response.get('status_code')}, Retries: {response.get('retry_count', 0)}")

                prdetail_responses.append({
                    'age': age,
                    'sex': sex,
                    'response': response
                })
                stats['success_count'] += 1

            except Exception as e:
                stats['error_count'] += 1

                error_str = str(e)
                import re
                status_match = re.search(r'(\d{3})', error_str)
                status_code = int(status_match.group(1)) if status_match else None

                response_body = None
                if '||RESPONSE_BODY:' in error_str:
                    parts = error_str.split('||RESPONSE_BODY:')
                    if len(parts) > 1:
                        response_body = parts[1]

                failure_record = {
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': 'prDetail',
                    'age': age,
                    'sex': sex,
                    'request_params': {
                        'baseDt': base_dt,
                        'birthday': birthday,
                        'sex': sex_code,
                        'age': age
                    },
                    'error': error_str.split('||RESPONSE_BODY:')[0] if '||RESPONSE_BODY:' in error_str else error_str,
                    'error_type': type(e).__name__,
                    'status_code': status_code,
                    'response_body_snippet': response_body[:1000] if response_body else None,
                    'retry_count': 0
                }

                errors.append(failure_record)
                save_failure(failure_record, output_dir, base_dt)

                print(f"  ❌ Error: {e}")
                print(f"     Saved to _failures/{base_dt}.jsonl")

    # STEP 4: Process prDetail responses and filter by prCd for each product
    print("\n=== STEP NEXT-U: Processing prDetail Responses ===")

    for pr_resp in prdetail_responses:
        age = pr_resp['age']
        sex = pr_resp['sex']
        response = pr_resp['response']
        raw_api = response.get('_raw_response', {})

        # prDetail returns all insurers/products - need to filter
        pr_prod_line_cond_out_search_div = raw_api.get('prProdLineCondOutSearchDiv', [])

        for insurer_block in pr_prod_line_cond_out_search_div:
            ins_list = insurer_block.get('prProdLineCondOutIns', [])

            for ins_detail in ins_list:
                # Match by insCd and prCd
                ins_cd = ins_detail.get('insCd')
                pr_cd = ins_detail.get('prCd')

                # Find which product this belongs to
                matching_product = None
                for (insurer_key, product_id), mapped_pr_cd in product_id_map.items():
                    if mapped_pr_cd == pr_cd:
                        matching_product = (insurer_key, product_id)
                        break

                if not matching_product:
                    # This product is not in our compare_rows, skip
                    continue

                insurer_key, product_id = matching_product

                print(f"  Processing: {insurer_key} | {product_id[:40]} | age {age} | sex {sex}")

                # Parse NO_REFUND coverage premiums
                no_refund_records = parse_prdetail_insurer_block(ins_detail, insurer_key, product_id, age, sex)
                print(f"    Parsed {len(no_refund_records)} NO_REFUND coverages")

                # Get monthly_prem_sum from ins_detail for verification
                monthly_prem_sum = ins_detail.get('monthlyPremSum', 0)
                expected_sum = monthly_prem_sum

                # Verify sum
                verification = verify_sum_match(no_refund_records, expected_sum)

                if verification['match']:
                    stats['sum_match_count'] += 1
                    print(f"    ✅ Sum match: {verification['actual_sum']} == {verification['expected_sum']}")
                else:
                    stats['sum_mismatch_count'] += 1
                    print(f"    ⚠️  Sum mismatch: {verification['actual_sum']} != {verification['expected_sum']} (error: {verification['error']})")

                # Generate GENERAL coverage premiums
                general_records = generate_general_coverage_premiums(no_refund_records, multipliers)
                print(f"    Generated {len(general_records)} GENERAL coverages")

                # Combine
                coverage_premium_records.extend(no_refund_records)
                coverage_premium_records.extend(general_records)

                # Create product_premium_quote_v2 record
                total_prem_sum = ins_detail.get('totalPremSum', 0)
                pay_term_years = ins_detail.get('payTermYears', 0)
                ins_term_years = ins_detail.get('insTermYears', 0)

                # Calculate hash
                response_hash = hashlib.sha256(
                    json.dumps(ins_detail, sort_keys=True).encode()
                ).hexdigest()

                product_premium_records.append({
                    'insurer_key': insurer_key,
                    'product_id': product_id,
                    'plan_variant': 'NO_REFUND',
                    'age': age,
                    'sex': sex,
                    'smoke': 'NA',
                    'pay_term_years': pay_term_years,
                    'ins_term_years': ins_term_years,
                    'as_of_date': base_dt[:4] + '-' + base_dt[4:6] + '-' + base_dt[6:],
                    'premium_monthly_total': monthly_prem_sum,
                    'premium_total_total': total_prem_sum,
                    'calculated_monthly_sum': sum(r['premium_monthly_coverage'] for r in no_refund_records),
                    'sum_match_status': verification['status'] if no_refund_records else 'UNKNOWN',
                    'source_table_id': 'prDetail_api',
                    'api_response_hash': response_hash,
                    'response_age': age
                })

    # Build product_id_map records
    for (insurer_key, product_id), pr_cd in product_id_map.items():
        product_id_map_records[(insurer_key, product_id)] = {
            'insurer_key': insurer_key,
            'compare_product_id': product_id,
            'premium_product_id': pr_cd,
            'as_of_date': base_dt[:4] + '-' + base_dt[4:6] + '-' + base_dt[6:],
            'source': 'API',
            'evidence_ref': f"prInfo_api_{base_dt}"
        }

    return {
        'product_premium_records': product_premium_records,
        'coverage_premium_records': coverage_premium_records,
        'product_id_map_records': list(product_id_map_records.values()),
        'errors': errors,
        'stats': stats
    }


def write_jsonl(records: List[Dict[str, Any]], output_path: str) -> None:
    """Write records to JSONL"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')

    print(f"Written {len(records)} records to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pull prDetail API for compare_rows products")
    parser.add_argument(
        "--compare-rows",
        default="/Users/cheollee/inca-rag-scope/data/compare_v1/compare_rows_v1.jsonl",
        help="Path to compare_rows_v1 JSONL"
    )
    parser.add_argument(
        "--ages",
        nargs='+',
        type=int,
        default=[30, 40, 50],
        help="Age scenarios (space-separated)"
    )
    parser.add_argument(
        "--sexes",
        nargs='+',
        default=['M'],
        help="Sex scenarios (space-separated, default: M only for testing)"
    )
    parser.add_argument(
        "--baseDt",
        dest="base_dt",
        required=True,
        help="Base date (YYYYMMDD), e.g., 20251126"
    )
    parser.add_argument(
        "--output-dir",
        default="/Users/cheollee/inca-rag-scope/data/premium_raw",
        help="Raw API response output directory"
    )
    parser.add_argument(
        "--multiplier-excel",
        default="/Users/cheollee/inca-rag-scope/data/sources/insurers/4. 일반보험요율예시.xlsx",
        help="Path to multiplier Excel"
    )

    args = parser.parse_args()

    print("=== STEP NEXT-R: prDetail API Pull ===\n")

    # Load compare_rows
    print(f"Loading compare_rows: {args.compare_rows}")
    compare_rows = load_jsonl(args.compare_rows)
    print(f"Loaded {len(compare_rows)} compare_rows records")

    # Extract products
    products = extract_unique_products_from_compare_rows(compare_rows)
    print(f"Extracted {len(products)} unique products\n")

    # Pull API
    result = pull_prdetail_for_products(
        products,
        args.ages,
        args.sexes,
        args.base_dt,
        args.output_dir,
        args.multiplier_excel
    )

    # Save SSOT records
    print("\n=== Saving SSOT Records ===")

    write_jsonl(
        result['product_premium_records'],
        f"/tmp/product_premium_quote_v2_{args.base_dt}.jsonl"
    )

    write_jsonl(
        result['coverage_premium_records'],
        f"/tmp/coverage_premium_quote_{args.base_dt}.jsonl"
    )

    write_jsonl(
        result['product_id_map_records'],
        f"/tmp/product_id_map_{args.base_dt}.jsonl"
    )

    # Print stats
    print("\n=== Summary ===")
    print(f"Total requests: {result['stats']['total_requests']}")
    print(f"Success: {result['stats']['success_count']}")
    print(f"Errors: {result['stats']['error_count']}")
    print(f"Sum match: {result['stats']['sum_match_count']}")
    print(f"Sum mismatch: {result['stats']['sum_mismatch_count']}")

    if result['errors']:
        print("\nErrors:")
        for error in result['errors'][:5]:
            print(f"  {error}")
