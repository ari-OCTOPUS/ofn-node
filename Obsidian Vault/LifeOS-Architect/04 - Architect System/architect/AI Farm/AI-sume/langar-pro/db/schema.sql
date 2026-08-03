-- LANGAR Pro — schema فاز ۱ (Postgres + pgvector)
-- جدول‌های اصلیِ یک سیستمِ تصمیم‌یار با شواهد، حافظه، و audit.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    telegram_id TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
-- کاربرِ پیش‌فرض (id=1) تا اولین /research بدونِ خطای FK کار کند
INSERT INTO users(id, telegram_id) VALUES (1, 'owner') ON CONFLICT DO NOTHING;
SELECT setval(pg_get_serial_sequence('users','id'), GREATEST((SELECT MAX(id) FROM users), 1));

CREATE TABLE IF NOT EXISTS goals (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT REFERENCES users(id),
    text       TEXT NOT NULL,
    status     TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- قرارداد انسان-AI (یک سطر در هر کاربر، JSON)
CREATE TABLE IF NOT EXISTS contracts (
    user_id    BIGINT PRIMARY KEY REFERENCES users(id),
    data       JSONB NOT NULL,
    version    TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources (
    id           BIGSERIAL PRIMARY KEY,
    url          TEXT,
    title        TEXT,
    published_at DATE,
    quality      JSONB,          -- authority/recency/independence/evidence/bias
    score        REAL,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claims (
    id           BIGSERIAL PRIMARY KEY,
    text         TEXT NOT NULL,
    tag          TEXT,           -- E / S / P
    confidence   REAL,
    embedding    vector(1536),   -- برای جست‌وجوی معنایی (اختیاری)
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claim_sources (
    claim_id  BIGINT REFERENCES claims(id),
    source_id BIGINT REFERENCES sources(id),
    PRIMARY KEY (claim_id, source_id)
);

-- Graph Memory سبک: یال بینِ claimها (به‌جای Neo4j در فاز اول)
CREATE TABLE IF NOT EXISTS claim_edges (
    src_claim BIGINT REFERENCES claims(id),
    dst_claim BIGINT REFERENCES claims(id),
    relation  TEXT,             -- supports / contradicts / depends_on
    PRIMARY KEY (src_claim, dst_claim, relation)
);

CREATE TABLE IF NOT EXISTS decisions (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT REFERENCES users(id),
    question   TEXT,
    summary    TEXT,
    confidence REAL,
    risk_level TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- verdictِ نسخه‌بندی‌شده: append-only (audit)
CREATE TABLE IF NOT EXISTS verdicts (
    id          BIGSERIAL PRIMARY KEY,
    decision_id BIGINT REFERENCES decisions(id),
    version     INT NOT NULL,
    verdict     TEXT,
    note        TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memories (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT REFERENCES users(id),
    kind       TEXT,            -- raw/verified/preference/decision/rejected/contradiction
    content    TEXT,
    embedding  vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedback (
    id          BIGSERIAL PRIMARY KEY,
    decision_id BIGINT REFERENCES decisions(id),
    kind        TEXT,           -- accept/reject/edit
    note        TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- audit ledger
CREATE TABLE IF NOT EXISTS agent_runs (
    id         BIGSERIAL PRIMARY KEY,
    agent      TEXT, status TEXT, info JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS tool_calls (
    id         BIGSERIAL PRIMARY KEY,
    tool       TEXT, args JSONB, ok BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS constitutional_checks (
    id         BIGSERIAL PRIMARY KEY,
    text       TEXT, compliant BOOLEAN, violations JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
