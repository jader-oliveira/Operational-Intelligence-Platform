-- BOIP schema v0.1 — the seven tables that carry the whole MVP.
-- Apply:  psql "$BOIP_DB_DSN" -f schema.sql     (idempotent)

CREATE TABLE IF NOT EXISTS asset (
    id          BIGSERIAL PRIMARY KEY,
    kind        TEXT        NOT NULL,              -- vm | host | datastore | cluster | k8s_deployment | ...
    name        TEXT        NOT NULL,
    source      TEXT        NOT NULL,              -- vmware | xen | k8s
    source_ref  TEXT        NOT NULL,              -- stable id in the source (moref like 'vm-56')
    environment TEXT,
    owner       TEXT,
    labels      JSONB       NOT NULL DEFAULT '{}',
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_ref)
);
CREATE INDEX IF NOT EXISTS asset_name_idx ON asset (name);
CREATE INDEX IF NOT EXISTS asset_kind_idx ON asset (kind);

CREATE TABLE IF NOT EXISTS asset_edge (
    parent_id  BIGINT      NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    child_id   BIGINT      NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    relation   TEXT        NOT NULL,               -- runs_on | stored_on | member_of
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (parent_id, child_id, relation)
);

CREATE TABLE IF NOT EXISTS config_snapshot (
    id          BIGSERIAL PRIMARY KEY,
    asset_id    BIGINT      NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    taken_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    config      JSONB       NOT NULL,              -- canonical, volatile fields stripped
    config_hash TEXT        NOT NULL               -- sha256 of canonical JSON
);
CREATE INDEX IF NOT EXISTS snap_asset_time_idx ON config_snapshot (asset_id, taken_at DESC);

CREATE TABLE IF NOT EXISTS config_change (
    id              BIGSERIAL PRIMARY KEY,
    asset_id        BIGINT      NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    path            TEXT        NOT NULL,          -- e.g. 'memory_mb' or 'disks[disk-202-0].capacity_gb'
    old_value       JSONB,                         -- null = key added
    new_value       JSONB,                         -- null = key removed
    snapshot_before BIGINT REFERENCES config_snapshot(id),
    snapshot_after  BIGINT REFERENCES config_snapshot(id)
);
CREATE INDEX IF NOT EXISTS change_time_idx  ON config_change (detected_at DESC);
CREATE INDEX IF NOT EXISTS change_asset_idx ON config_change (asset_id, detected_at DESC);

CREATE TABLE IF NOT EXISTS incident (
    id           BIGSERIAL PRIMARY KEY,
    title        TEXT        NOT NULL,
    state        TEXT        NOT NULL DEFAULT 'new',
        -- new -> investigating -> report_ready -> recommendation_proposed
        --     -> approved -> executing -> verified | rolled_back | closed
    source_alert JSONB,
    opened_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS evidence (
    id           BIGSERIAL PRIMARY KEY,
    incident_id  BIGINT      NOT NULL REFERENCES incident(id) ON DELETE CASCADE,
    kind         TEXT        NOT NULL,             -- metric | event | config_change | log | topology
    source_tool  TEXT        NOT NULL,             -- which tool produced it
    content      JSONB       NOT NULL,
    content_hash TEXT        NOT NULL,             -- immutability: hash at write time
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation (
    id            BIGSERIAL PRIMARY KEY,
    incident_id   BIGINT      NOT NULL REFERENCES incident(id) ON DELETE CASCADE,
    summary       TEXT        NOT NULL,
    risk          TEXT        NOT NULL CHECK (risk IN ('low','medium','high','critical')),
    confidence    NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    evidence_ids  BIGINT[]    NOT NULL DEFAULT '{}',
    steps         JSONB       NOT NULL,
    rollback      JSONB       NOT NULL,
    verification  JSONB       NOT NULL,
    awx_template_id TEXT,
    gitlab_mr_url TEXT,
    state         TEXT        NOT NULL DEFAULT 'proposed',
    outcome       TEXT,                            -- accepted_correct | accepted_incorrect | rejected | expired
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
