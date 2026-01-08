#!/usr/bin/env bash
set -euo pipefail

INSURER="${INSURER:-}"
if [[ -z "${INSURER}" ]]; then
  echo "ERROR: INSURER is required. e.g. INSURER=SAMSUNG tools/onboarding/run_gate.sh" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

CLEAN="${CLEAN:-0}"                      # 1이면 산출물 삭제 후 재생성
CLEAN_SCOPE_RAW="${CLEAN_SCOPE_RAW:-0}"  # 1이면 step1 raw도 삭제
STAGES="${STAGES:-PROFILE,SCOPE,EVIDENCE,CARDS,SLIM,ARTIFACTS,GATE}"

# Entry points (override 가능)
PROFILE_ENTRY="${PROFILE_ENTRY:-pipeline/step1_summary_first/profile_builder_v3.py}"
EXTRACTOR_ENTRY="${EXTRACTOR_ENTRY:-pipeline/step1_summary_first/extractor_v3.py}"
SCOPE_STEP2_SANITIZE="${SCOPE_STEP2_SANITIZE:-pipeline/step2_sanitize_scope/run.py}"
SCOPE_STEP2_CANON="${SCOPE_STEP2_CANON:-pipeline/step2_canonical_mapping/run.py}"
EVIDENCE_ENTRY="${EVIDENCE_ENTRY:-pipeline/step4_evidence_search/search_evidence.py}"
CARDS_ENTRY="${CARDS_ENTRY:-pipeline/step5_build_cards/build_cards.py}"
SLIM_ENTRY="${SLIM_ENTRY:-pipeline/step5_build_cards/build_cards_slim.py}"

insurer_lower="$(echo "${INSURER}" | tr '[:upper:]' '[:lower:]')"

# Outputs (일부는 discover로 찾는다)
PROFILE_OUT="data/profile/${insurer_lower}_proposal_profile_v3.json"
SCOPE_CSV="data/scope/${insurer_lower}_scope_mapped.sanitized.csv"
EVIDENCE_PACK="data/evidence_pack/${INSURER}_evidence_pack.jsonl"
CARDS_JSONL="data/compare/${insurer_lower}_coverage_cards.jsonl"
SLIM_JSONL="data/compare/${insurer_lower}_coverage_cards_slim.jsonl"

has_stage() { [[ ",${STAGES}," == *",${1},"* ]]; }

require_file() {
  local f="$1"
  [[ -f "${f}" ]] || { echo "ERROR: required file missing: ${f}" >&2; exit 1; }
}

auto_detect_proposal_pdf() {
  if [[ -n "${PROPOSAL_PDF:-}" ]]; then
    echo "${PROPOSAL_PDF}"
    return 0
  fi
  local dir="data/sources/insurers/${insurer_lower}/가입설계서"
  [[ -d "${dir}" ]] || { echo ""; return 0; }
  ls -1 "${dir}"/*.pdf 2>/dev/null | head -n 1 || true
}

write_proposal_manifest() {
  local out="$1"
  local pdf="$2"
  python - <<PY
import json
from pathlib import Path
out=Path("${out}")
pdf=Path("${pdf}")
manifest={
  "version":"v1",
  "items":[{
    "insurer":"${INSURER}",
    "variant":"default",
    "doc_type":"가입설계서",
    "file_path":str(pdf),
    "pdf_path":str(pdf),
    "path":str(pdf),
  }],
  "source":{"type":"generated","purpose":"proposal_step1"},
}
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote proposal manifest -> {out}")
PY
}

discover_step1_raw_scope() {
  # extractor_v3가 대문자/소문자 insurer를 어떻게 쓰든 "최신"을 잡는다
  local hit=""
  hit="$(ls -1t data/scope_v3/"${INSURER}"_step1_raw_scope_v3.jsonl 2>/dev/null | head -n 1 || true)"
  [[ -n "${hit}" ]] && { echo "${hit}"; return 0; }
  hit="$(ls -1t data/scope_v3/"${insurer_lower}"_step1_raw_scope_v3.jsonl 2>/dev/null | head -n 1 || true)"
  [[ -n "${hit}" ]] && { echo "${hit}"; return 0; }
  hit="$(ls -1t data/scope_v3/*_step1_raw_scope_v3.jsonl 2>/dev/null | grep -i "^data/scope_v3/${insurer_lower}\|^data/scope_v3/${INSURER}" | head -n 1 || true)"
  echo "${hit}"
}

discover_canon_scope() {
  local hit=""
  hit="$(ls -1t data/scope_v3/"${INSURER}"_*step2_canonical_scope_v1.jsonl 2>/dev/null | head -n 1 || true)"
  [[ -n "${hit}" ]] && { echo "${hit}"; return 0; }
  hit="$(ls -1t data/scope_v3/"${insurer_lower}"_*step2_canonical_scope_v1.jsonl 2>/dev/null | head -n 1 || true)"
  [[ -n "${hit}" ]] && { echo "${hit}"; return 0; }
  hit="$(ls -1t data/scope_v3/*step2_canonical_scope_v1.jsonl 2>/dev/null | grep -i "^data/scope_v3/${insurer_lower}\|^data/scope_v3/${INSURER}" | head -n 1 || true)"
  echo "${hit}"
}

echo "== Onboarding Gate (safe v3: Step1 manifest + robust discovery) =="
echo "INSURER=${INSURER}"
echo "insurer_lower=${insurer_lower}"
echo "ROOT=${ROOT}"
echo "CLEAN=${CLEAN}"
echo "CLEAN_SCOPE_RAW=${CLEAN_SCOPE_RAW}"
echo "STAGES=${STAGES}"
echo

# CLEAN
if [[ "${CLEAN}" == "1" ]]; then
  echo "== CLEAN =="
  rm -f "${PROFILE_OUT}" "${EVIDENCE_PACK}" "${CARDS_JSONL}" "${SLIM_JSONL}" "${SCOPE_CSV}" 2>/dev/null || true

  # step2 산출물만 기본 삭제 (안전)
  rm -f data/scope_v3/"${insurer_lower}"_step2_*.jsonl 2>/dev/null || true
  rm -f data/scope_v3/"${INSURER}"_step2_*.jsonl 2>/dev/null || true

  # 필요할 때만 step1 raw 삭제
  if [[ "${CLEAN_SCOPE_RAW}" == "1" ]]; then
    rm -f data/scope_v3/"${insurer_lower}"_step1_raw_scope_v3.jsonl 2>/dev/null || true
    rm -f data/scope_v3/"${INSURER}"_step1_raw_scope_v3.jsonl 2>/dev/null || true
  fi
  echo
fi

# Shared manifest for Step1-a/b
tmp_manifest="/tmp/${insurer_lower}_proposal_manifest_for_step1.json"
proposal_pdf=""

if has_stage "PROFILE" || has_stage "SCOPE"; then
  proposal_pdf="$(auto_detect_proposal_pdf)"
  if [[ -z "${proposal_pdf}" || ! -f "${proposal_pdf}" ]]; then
    echo "ERROR: proposal pdf not found. Set PROPOSAL_PDF=/path/to/proposal.pdf" >&2
    exit 1
  fi
  echo "PROPOSAL_PDF=${proposal_pdf}"
  write_proposal_manifest "${tmp_manifest}" "${proposal_pdf}"
  echo
fi

# 1) PROFILE
if has_stage "PROFILE"; then
  echo "== 1) PROFILE (proposal-only) =="
  require_file "${PROFILE_ENTRY}"
  echo "RUN: python ${PROFILE_ENTRY} --manifest ${tmp_manifest}"
  python "${PROFILE_ENTRY}" --manifest "${tmp_manifest}"
  [[ -f "${PROFILE_OUT}" ]] || { echo "ERROR: PROFILE output missing: ${PROFILE_OUT}" >&2; exit 1; }
  echo "OK: PROFILE output: ${PROFILE_OUT}"
  echo
fi

# 2) SCOPE
if has_stage "SCOPE"; then
  echo "== 2) SCOPE (Step1 raw -> Step2 canonical) =="

  # Step1-b: extractor_v3는 --manifest만 받는다
  require_file "${EXTRACTOR_ENTRY}"
  echo "RUN: python -m pipeline.step1_summary_first.extractor_v3 --manifest ${tmp_manifest}"
  python -m pipeline.step1_summary_first.extractor_v3 --manifest "${tmp_manifest}"

  raw_scope="$(discover_step1_raw_scope)"
  if [[ -z "${raw_scope}" || ! -f "${raw_scope}" ]]; then
    echo "ERROR: step1 raw scope missing under data/scope_v3 for ${INSURER}" >&2
    ls -la data/scope_v3 | egrep -i "(${insurer_lower}|${INSURER})" >&2 || true
    exit 1
  fi
  echo "OK: step1 raw scope: ${raw_scope}"

  require_file "${SCOPE_STEP2_SANITIZE}"
  require_file "${SCOPE_STEP2_CANON}"

  echo "RUN: python ${SCOPE_STEP2_SANITIZE} --insurer ${INSURER}"
  python "${SCOPE_STEP2_SANITIZE}" --insurer "${INSURER}"

  echo "RUN: python ${SCOPE_STEP2_CANON} --insurer ${INSURER}"
  python "${SCOPE_STEP2_CANON}" --insurer "${INSURER}"

  canon_scope="$(discover_canon_scope)"
  if [[ -z "${canon_scope}" || ! -f "${canon_scope}" ]]; then
    echo "ERROR: canonical scope output missing under data/scope_v3 for ${INSURER}" >&2
    ls -la data/scope_v3 | egrep -i "(${insurer_lower}|${INSURER})" >&2 || true
    exit 1
  fi
  echo "OK: canonical scope: ${canon_scope}"

  require_file "tools/scope/export_scope_v3_to_scope_csv.py"
  echo "RUN: python tools/scope/export_scope_v3_to_scope_csv.py --insurer ${INSURER}"
  python "tools/scope/export_scope_v3_to_scope_csv.py" --insurer "${INSURER}"

  [[ -f "${SCOPE_CSV}" ]] || { echo "ERROR: scope CSV missing: ${SCOPE_CSV}" >&2; exit 1; }
  echo "OK: scope CSV: ${SCOPE_CSV}"
  echo
fi

# 3) EVIDENCE
if has_stage "EVIDENCE"; then
  echo "== 3) EVIDENCE PACK =="
  require_file "${EVIDENCE_ENTRY}"
  echo "RUN: python ${EVIDENCE_ENTRY} --insurer ${INSURER}"
  python "${EVIDENCE_ENTRY}" --insurer "${INSURER}"
  [[ -f "${EVIDENCE_PACK}" ]] || { echo "ERROR: evidence pack missing: ${EVIDENCE_PACK}" >&2; exit 1; }
  echo "OK: evidence pack: ${EVIDENCE_PACK}"
  echo
fi

# 4) CARDS
if has_stage "CARDS"; then
  echo "== 4) CARDS (full) =="
  require_file "${CARDS_ENTRY}"
  echo "RUN: python ${CARDS_ENTRY} --insurer ${INSURER}"
  python "${CARDS_ENTRY}" --insurer "${INSURER}"
  [[ -f "${CARDS_JSONL}" ]] || { echo "ERROR: cards jsonl missing: ${CARDS_JSONL}" >&2; exit 1; }
  echo "OK: cards: ${CARDS_JSONL}"
  echo
fi

# 5) SLIM
if has_stage "SLIM"; then
  echo "== 5) CARDS (slim) =="
  require_file "${SLIM_ENTRY}"
  echo "RUN: python ${SLIM_ENTRY} --insurer ${INSURER}"
  python "${SLIM_ENTRY}" --insurer "${INSURER}"
  [[ -f "${SLIM_JSONL}" ]] || { echo "ERROR: slim cards jsonl missing: ${SLIM_JSONL}" >&2; exit 1; }
  echo "OK: slim cards: ${SLIM_JSONL}"
  echo
fi

# 6) ARTIFACTS
if has_stage "ARTIFACTS"; then
  echo "== 6) SSOT Artifacts Check =="
  for f in "${SCOPE_CSV}" "${CARDS_JSONL}" "${SLIM_JSONL}"; do
    [[ -f "${f}" ]] || { echo "ERROR: missing artifact: ${f}" >&2; exit 1; }
    echo "OK: ${f}  lines=$(wc -l < "${f}" | tr -d ' ')"
  done
  echo
fi

# 7) GATE
if has_stage "GATE"; then
  echo "== 7) Gate Suite (Fail Fast) =="
  pytest -q \
    tests/test_scope_gate.py \
    tests/test_coverage_cards.py \
    tests/test_evidence_pack.py \
    tests/test_audit_amount_status_dashboard_smoke.py
  echo
fi

echo "DONE: Onboarding Gate PASS for ${INSURER}"