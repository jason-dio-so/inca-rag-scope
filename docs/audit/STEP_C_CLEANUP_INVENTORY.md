# STEP C: Cleanup Inventory & Safe Commands

**Baseline**: HEAD=3a31976 (STEP B-4 완료)
**Date**: 2026-01-06
**Status**: 정리 전 inventory (실행 금지, 검토 전용)

---

## 0. Constitutional Rules (ABSOLUTE)

❌ **금지 사항** (STEP C 범위):
- apps/** 수정 금지
- core/** 수정 금지
- data/** SSOT 파일 삭제 금지
- pipeline/** 실행 로직 수정 금지
- routing/handler/db 변경 금지

✅ **허용 사항**:
- 문서/보고서 정리 (archive 이동)
- 백업/임시 파일 삭제
- 빌드 아티팩트 정리
- .gitignore 업데이트 (정리 후)

---

## 1. Root-Level Cleanup Candidates (25 files)

### 1.1 STEP_NEXT Completion Reports (25개)
**Status**: Historical completion logs (not referenced in code)
**Size**: ~100KB total
**Risk**: ZERO (문서만, 코드 미참조)

**Candidates**:
```
STEP_NEXT_10_COMPLETION_REPORT.md
STEP_NEXT_10B_1A_COMPLETION.md
STEP_NEXT_10B_2_COMPLETION.md
STEP_NEXT_10B_2C_2_COMPLETION.md
STEP_NEXT_10B_2C_2B_COMPLETION.md
STEP_NEXT_10B_2C_3_COMPLETION.md
STEP_NEXT_10B_2C_4_COMPLETION.md
STEP_NEXT_10B_2G_2_COMPLETION.md
STEP_NEXT_10B_2G_2_DB_LOAD_COMPLETION.md
STEP_NEXT_10B_2G_COMPLETION.md
STEP_NEXT_10B_2G_FIX_COMPLETION.md
STEP_NEXT_10B_FINAL_COMPLETION.md
STEP_NEXT_11_COMPLETION.md
STEP_NEXT_12_COMPLETION.md
STEP_NEXT_13_COMPLETION.md
STEP_NEXT_14_COMPLETION.md
STEP_NEXT_15_COMPLETION.md
STEP_NEXT_16_COMPLETION.md
STEP_NEXT_17_COMPLETION.md
STEP_NEXT_17A_COMPLETION.md
STEP_NEXT_17B_COMPLETION.md
STEP_NEXT_18A_COMPLETION.md
STEP_NEXT_18B_COMPLETION.md
STEP_NEXT_18D_COMPLETION.md
STEP_NEXT_18X_SSOT_LOCK_COMPLETION.md
```

**Recommendation**: `archive/step_completion_reports/`로 이동

---

### 1.2 Status Backups (1개)
**Status**: Duplicate of STATUS.md
**Size**: ~8KB
**Risk**: ZERO (백업 파일)

**Candidate**:
```
STATUS.md.backup
```

**Recommendation**: 삭제 (STATUS.md와 동일 내용 확인 후)

---

### 1.3 Ad-hoc Test/Dev Files (4개)
**Status**: Development/testing artifacts (not in production flow)
**Size**: ~20KB
**Risk**: LOW (startup scripts는 유지, HTML test files는 제거 가능)

**Candidates**:
```
simple_test.html          # Ad-hoc test (제거 후보)
test_api.html             # Ad-hoc test (제거 후보)
START_WEB_TEST.md         # Startup guide (보존 또는 docs/로 이동)
start-env-simple.sh       # Startup script (보존)
start-env.sh              # Startup script (보존)
stop-env.sh               # Startup script (보존)
```

**Recommendation**:
- *.html → 삭제 (기능 테스트는 pytest로 대체됨)
- START_WEB_TEST.md → docs/guides/ 이동 또는 삭제
- start-env*.sh, stop-env.sh → 보존 (실행 스크립트)

---

## 2. Directory Cleanup Candidates

### 2.1 _deprecated/ (164KB)
**Contents**: Deprecated pipeline steps (STEP NEXT-31-P2에서 이동됨)
**Risk**: ZERO (이미 비활성화됨)

**Structure**:
```
_deprecated/
└── pipeline/
    ├── step0_scope_filter/
    ├── step7_compare/
    ├── step8_multi_compare/
    ├── step8_single_coverage/
    └── step10_audit/
```

**Recommendation**: 보존 (이미 .gitignore에 추가됨, 참조용)

---

### 2.2 _recovery_snapshots/ (76KB)
**Status**: Recovery artifacts (STEP NEXT-31-P3-γ)
**Risk**: ZERO (복구 완료 후 잔재)

**Recommendation**: 삭제 가능 (복구 완료, 더 이상 필요 없음)

---

### 2.3 _triage_logs/ (8KB)
**Status**: Triage logs (STEP NEXT-31-P3-γ)
**Risk**: ZERO (복구 완료 후 잔재)

**Recommendation**: 삭제 가능 (복구 완료, 더 이상 필요 없음)

---

### 2.4 logs/ (28KB)
**Status**: Runtime logs (already in .gitignore)
**Risk**: ZERO (런타임 아티팩트)

**Recommendation**: 보존 (but not tracked in git, OK to delete locally)

---

### 2.5 output/ (200KB)
**Status**: Unknown output artifacts
**Risk**: MEDIUM (내용 확인 필요)

**Action Required**: 내용 확인 후 결정
```bash
ls -la output/ | head -20
```

**Recommendation**: 내용 확인 후 archive/ 또는 삭제

---

### 2.6 backups/ (588KB)
**Contents**: Database backups
**Risk**: MEDIUM (데이터베이스 백업 - 확인 후 보존/삭제)

**Files**:
```
backups/inca_rag_scope_backup_41s_20251231_150042.dump
```

**Recommendation**:
- 최신 백업 1개만 보존
- 오래된 백업은 archive/backups_legacy/ 또는 삭제

---

### 2.7 archive/ (2.8MB)
**Status**: Already archived content
**Risk**: ZERO (이미 아카이브됨)

**Recommendation**: 보존 (이미 정리된 상태)

---

## 3. Backup/Temp Files (4개)

### 3.1 Specific Backups
```
./STATUS.md.backup                                           # 8KB (삭제 후보)
./data/sources/mapping/담보명mapping자료_backup_20251227_125240.xlsx  # (삭제 후보)
./apps/api/server_v1.py.bak                                 # (삭제 후보)
./backups/inca_rag_scope_backup_41s_20251231_150042.dump    # (보존 또는 archive)
```

**Recommendation**:
- STATUS.md.backup → 삭제 (STATUS.md와 비교 후)
- 담보명mapping자료_backup → 삭제 (이미 .gitignore에 data/**/*.bak 패턴 있음)
- server_v1.py.bak → 삭제 (apps/api/에 백업 파일 불필요)
- DB dump → 최신 1개만 보존, 나머지 archive

---

## 4. Safe Cleanup Commands (실행 전 승인 필요)

### Phase 1: Root-Level Completion Reports
```bash
# 1) Create archive directory
mkdir -p archive/step_completion_reports

# 2) Move completion reports
git mv STEP_NEXT_*_COMPLETION*.md archive/step_completion_reports/

# 3) Verify
ls archive/step_completion_reports/ | wc -l  # Should be 25
```

---

### Phase 2: Root-Level Backups & Ad-hoc Files
```bash
# 1) Compare STATUS.md with backup
diff STATUS.md STATUS.md.backup

# 2) Delete backup (if identical)
rm STATUS.md.backup

# 3) Delete ad-hoc HTML test files
rm simple_test.html test_api.html

# 4) Optional: Move START_WEB_TEST.md to docs
mkdir -p docs/guides
git mv START_WEB_TEST.md docs/guides/
```

---

### Phase 3: Recovery Artifacts
```bash
# Delete recovery snapshots and triage logs (복구 완료)
rm -rf _recovery_snapshots _triage_logs

# Note: Already in .gitignore, so no git operation needed
```

---

### Phase 4: Backup Files
```bash
# Delete backup files (already matched by .gitignore patterns)
rm apps/api/server_v1.py.bak
rm data/sources/mapping/담보명mapping자료_backup_20251227_125240.xlsx

# Optional: Archive old DB dumps
mkdir -p archive/backups_legacy
mv backups/*.dump archive/backups_legacy/
```

---

### Phase 5: Output Directory (AFTER inspection)
```bash
# 1) Inspect output/ contents
ls -laR output/

# 2) If safe to delete:
rm -rf output/

# 3) If contains valuable artifacts:
mkdir -p archive/output_legacy
mv output/* archive/output_legacy/
rmdir output
```

---

## 5. Verification Commands (사전 실행 권장)

### Pre-cleanup Verification
```bash
# 1) Check current HEAD
git log -1 --oneline

# 2) Check clean working tree
git status -sb

# 3) Run tests before cleanup
PYTHONPATH=. pytest -q tests/test_intent_routing_lock.py

# 4) Verify server running
curl -s http://localhost:8000/health || echo "Server check needed"
```

---

### Post-cleanup Verification
```bash
# 1) Check what was deleted/moved
git status -sb

# 2) Run smoke tests
bash tools/smoke/smoke_chat.sh

# 3) Run routing tests
PYTHONPATH=. pytest -q tests/test_intent_routing_lock.py

# 4) Verify frontend build (if web files touched)
cd apps/web && npm run build
```

---

## 6. Estimated Impact

### Disk Space Savings
- STEP_NEXT reports → archive: ~100KB (git tracked)
- Backup files: ~20KB
- Recovery artifacts: ~84KB (_recovery_snapshots + _triage_logs)
- **Total**: ~204KB (minimal savings, but cleaner repo)

### Risk Assessment
- **ZERO Risk**: Completion reports, status backups, recovery artifacts
- **LOW Risk**: Ad-hoc HTML test files
- **MEDIUM Risk**: output/ directory (requires inspection)
- **HIGH Risk**: NONE (no SSOT or runtime files targeted)

---

## 7. Rollback Plan

If cleanup causes issues:

### Immediate Rollback
```bash
# 1) Undo all git operations
git reset --hard 3a31976

# 2) Restore deleted files (if backed up)
git checkout HEAD -- <file_path>

# 3) Verify tests
PYTHONPATH=. pytest -q tests/test_intent_routing_lock.py
bash tools/smoke/smoke_chat.sh
```

---

## 8. Execution Checklist

- [ ] **Pre-cleanup**: Run verification commands (Section 5)
- [ ] **Phase 1**: Move STEP_NEXT completion reports (25 files)
- [ ] **Phase 2**: Delete STATUS.md.backup, ad-hoc HTML files
- [ ] **Phase 3**: Delete _recovery_snapshots, _triage_logs
- [ ] **Phase 4**: Delete .bak files
- [ ] **Phase 5**: Inspect output/ → archive or delete
- [ ] **Post-cleanup**: Run verification commands (Section 5)
- [ ] **Commit**: Single commit with detailed message

---

## 9. Recommended Commit Message

```
chore(cleanup): archive completion reports and remove recovery artifacts

Phase 1: Archive STEP_NEXT completion reports
- Moved 25 STEP_NEXT_*_COMPLETION*.md to archive/step_completion_reports/
- Historical logs, not referenced in code (ZERO risk)

Phase 2: Remove root-level backups and ad-hoc test files
- Deleted STATUS.md.backup (identical to STATUS.md)
- Deleted simple_test.html, test_api.html (ad-hoc tests)

Phase 3: Remove recovery artifacts
- Deleted _recovery_snapshots/ (76KB, recovery complete)
- Deleted _triage_logs/ (8KB, recovery complete)

Phase 4: Remove backup files
- Deleted apps/api/server_v1.py.bak
- Deleted data/sources/mapping/담보명mapping자료_backup_20251227_125240.xlsx

STEP C: Cleanup (NO functional changes, documentation/artifacts only)

Verification:
- PYTHONPATH=. pytest -q tests/test_intent_routing_lock.py → 10/10 PASS
- bash tools/smoke/smoke_chat.sh → 3/3 verified
- git diff apps/ core/ pipeline/ → 0 lines changed
```

---

## 10. Next Steps (After Review)

1. **User Review**: Review this inventory report
2. **Approval**: Get explicit approval for each phase
3. **Execute**: Run phases 1-5 sequentially (with verification between)
4. **Commit**: Single atomic commit with all cleanup changes
5. **Verify**: Full test suite + smoke tests

---

**END OF INVENTORY REPORT**
**Status**: Ready for review (실행 대기 중)
