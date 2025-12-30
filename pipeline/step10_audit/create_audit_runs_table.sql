-- ======================================
-- Audit Runs Metadata Table
-- ======================================
-- Purpose: Track Step7 amount pipeline audit runs for compliance and lineage
-- Lock: Ensures each production load is tied to a frozen, audited snapshot

CREATE TABLE IF NOT EXISTS audit_runs (
    audit_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Audit metadata
    audit_name TEXT NOT NULL,  -- e.g., 'step7_amount_gt_audit'
    git_commit TEXT NOT NULL,  -- e.g., 'c6fad903c4782c9b78c44563f0f47bf13f9f3417'
    freeze_tag TEXT,           -- e.g., 'freeze/pre-10b2g2-20251229-024400'

    -- Report paths (frozen snapshots)
    report_json_path TEXT NOT NULL,  -- e.g., 'reports/step7_gt_audit_all_20251229-025007.json'
    report_md_path TEXT NOT NULL,    -- e.g., 'reports/step7_gt_audit_all_20251229-025007.md'

    -- Audit results summary
    total_insurers INT NOT NULL DEFAULT 8,
    total_rows_audited INT,
    mismatch_value_count INT,
    mismatch_type_count INT,
    audit_status TEXT CHECK (audit_status IN ('PASS', 'FAIL', 'PENDING')),

    -- Coverage scope
    insurers TEXT[],  -- e.g., '{samsung,hyundai,lotte,db,kb,meritz,hanwha,heungkuk}'

    -- Timestamps
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE (git_commit, audit_name),
    CHECK (mismatch_value_count >= 0),
    CHECK (mismatch_type_count >= 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_audit_runs_freeze_tag ON audit_runs(freeze_tag);
CREATE INDEX IF NOT EXISTS idx_audit_runs_git_commit ON audit_runs(git_commit);
CREATE INDEX IF NOT EXISTS idx_audit_runs_generated_at ON audit_runs(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_runs_status ON audit_runs(audit_status);

-- Comment
COMMENT ON TABLE audit_runs IS 'Frozen audit run metadata for Step7 amount pipeline (lock + lineage)';
COMMENT ON COLUMN audit_runs.freeze_tag IS 'Git tag marking the frozen snapshot for this audit run';
COMMENT ON COLUMN audit_runs.mismatch_value_count IS 'Number of MISMATCH_VALUE errors (must be 0 for PASS)';
COMMENT ON COLUMN audit_runs.audit_status IS 'PASS if mismatch_value_count=0 and mismatch_type_count=0';
