"""
CONFIG -- Single source of truth for all Brushline parameters.
Maps 1:1 to CONFIG_parameters.md and .env.
NO hard-coding anywhere else -- all values come from here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (two levels up from src/)
load_dotenv(Path(__file__).parent.parent / ".env")


def _parse_chat_ids(raw: str) -> list:
    """Parse comma-separated Telegram chat IDs; skip blanks/placeholders.

    Tolerant by design: an unfilled .env (e.g. PASTE_YOUR_CHAT_ID_HERE from
    .env.example) must NOT crash the whole app at import. validate() still
    reports an empty list as a missing required config.
    """
    import logging
    ids = []
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            ids.append(int(tok))
        except ValueError:
            logging.getLogger(__name__).warning(
                "Ignoring non-numeric ALLOWED_OPERATOR_CHAT_IDS token: %r", tok
            )
    return ids


class Config:
    # -- Section 1: Financial (KB-02) ---------------------------------------
    # 1 USD = 1.45 AUD (RBA/XE, June 2026)
    FX_AUD_USD: float = 1.45

    SPEND_CAP_PER_ACTION_AUD: float = float(
        os.getenv("SPEND_CAP_PER_ACTION_AUD", "5.00")
    )
    SPEND_CAP_PER_DAY_AUD: float = float(
        os.getenv("SPEND_CAP_PER_DAY_AUD", "20.00")
    )

    # -- Model router (KB-01 s3, cheap-first) -------------------------------
    MODEL_CHEAP: str = os.getenv("MODEL_CHEAP", "claude-haiku-4-5-20251001")
    MODEL_KEY: str = os.getenv("MODEL_KEY", "claude-sonnet-4-6")
    # Opus disabled in MVP (KB-02 s2.1)
    BATCH_ENABLED: bool = os.getenv("BATCH_ENABLED", "true").lower() == "true"
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    # -- Resilience (P8) + data layer (P9) ----------------------------------
    RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RETRY_BASE_DELAY_SEC: float = float(os.getenv("RETRY_BASE_DELAY_SEC", "0.5"))
    RETRY_MAX_DELAY_SEC: float = float(os.getenv("RETRY_MAX_DELAY_SEC", "8.0"))
    DB_POOL_ENABLED: bool = os.getenv("DB_POOL_ENABLED", "true").lower() == "true"

    # -- Section 2: SLA queue (KB-05) ----------------------------------------
    SLA_LEAD_MINUTES: int = int(os.getenv("SLA_LEAD_MINUTES", "15"))
    SLA_REVIEW_NEG_HOURS: int = int(os.getenv("SLA_REVIEW_NEG_HOURS", "2"))
    SLA_FOLLOWUP_DAYS: tuple[int, ...] = (2, 5, 10)  # KB-09

    # -- Approval Queue priority + SLA deadline (KB-05 s3) -------------------
    # Minutes-to-decide before an item is escalated (priority -> critical,
    # expired flag set, operator notified). INV-1: expiry NEVER auto-approves.
    APPROVAL_SLA_MINUTES: dict = {
        "speed_to_lead":            15,        # critical -- "win the job" window
        "review_response":          120,       # high -- reputation management
        "followup":                 24 * 60,   # medium -- same-day decision
        "caption":                  24 * 60,   # low
        "gbp_post":                 24 * 60,   # low
        "suburb_page":              48 * 60,   # low
        "blog_outline":             48 * 60,   # low
        "capital_works_assessment": 48 * 60,   # low
    }
    APPROVAL_PRIORITY: dict = {
        "speed_to_lead":            "critical",
        "review_response":          "high",
        "followup":                 "medium",
        "caption":                  "low",
        "gbp_post":                 "low",
        "suburb_page":              "low",
        "blog_outline":             "low",
        "capital_works_assessment": "low",
    }
    APPROVAL_DEFAULT_SLA_MINUTES: int = 24 * 60
    APPROVAL_DEFAULT_PRIORITY: str = "low"

    # -- Section 3: Compliance (KB-03/07/09/12) ------------------------------
    SENDER_ID_TEMPLATE: str = (
        "{business_name} . ABN {abn} . unsubscribe: {unsub_link}"
    )
    UNSUBSCRIBE_WINDOW_DAYS: int = 5          # Spam Act 2003
    GATE_MAX_ROUNDS: int = 3                  # KB-07
    # Commonwealth penalty unit: $330 AUD (eff. 7 Nov 2024)
    # NOTE: indexation scheduled 1 Jul 2026 -- verify before bulk send
    SPAM_PENALTY_UNIT_AUD: int = 330

    # -- Telegram (TG-01) ------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ALLOWED_OPERATOR_CHAT_IDS: list[int] = _parse_chat_ids(
        os.getenv("ALLOWED_OPERATOR_CHAT_IDS", "")
    )

    # -- Section 4: Memory (KB-04) --------------------------------------------
    MEMORY_SCOPE: str = "per-lead"
    MEMORY_PII_ALLOWED: bool = False  # INV-2: NEVER store PII in memory

    # -- Section 5: Audit / retention (KB-06) ---------------------------------
    HASH_ALGO: str = "sha256"
    RETENTION_CONSENT: str = "spam_act"
    PII_STORAGE: str = "hash_ref"  # hash references only, never raw PII

    # -- Database --------------------------------------------------------------
    # CRITICAL: must NEVER be the same path as LANGAR's database (Phase 0)
    DB_PATH: str = os.getenv(
        "BRUSHLINE_DB_PATH", str(Path(__file__).parent.parent / "data" / "brushline.db")
    )

    # -- Governance (INV-3) -----------------------------------------------------
    KILL_SWITCH_FILE: str = os.getenv(
        "KILL_SWITCH_FILE", str(Path(__file__).parent.parent / "data" / "KILL_SWITCH")
    )

    # -- Anthropic ----------------------------------------------------------------
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # -- Business -------------------------------------------------------------
    BUSINESS_NAME: str = os.getenv("BUSINESS_NAME", "")
    BUSINESS_ABN: str = os.getenv("BUSINESS_ABN", "")

    # -- Search API (Phase 1) --------------------------------------------------
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    # DataForSEO: async = $0.0006/query, live = $0.002/query (KB-02 s2.2)
    DATAFOR_SEO_LOGIN: str = os.getenv("DATAFOR_SEO_LOGIN", "")
    DATAFOR_SEO_PASSWORD: str = os.getenv("DATAFOR_SEO_PASSWORD", "")

    # -- Integration (Phase 5) --------------------------------------------------
    SERVICEM8_API_KEY: str = os.getenv("SERVICEM8_API_KEY", "")
    TRADIFY_API_KEY: str = os.getenv("TRADIFY_API_KEY", "")

    def usd_to_aud(self, usd: float) -> float:
        return round(usd * self.FX_AUD_USD, 6)

    def approval_sla_minutes(self, draft_type: str) -> int:
        return self.APPROVAL_SLA_MINUTES.get(draft_type, self.APPROVAL_DEFAULT_SLA_MINUTES)

    def approval_priority(self, draft_type: str) -> str:
        return self.APPROVAL_PRIORITY.get(draft_type, self.APPROVAL_DEFAULT_PRIORITY)

    def validate(self) -> list[str]:
        """Return list of missing required configs (non-empty = not ready)."""
        missing = []
        if not self.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not self.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.ALLOWED_OPERATOR_CHAT_IDS:
            missing.append("ALLOWED_OPERATOR_CHAT_IDS")
        if not self.BUSINESS_NAME:
            missing.append("BUSINESS_NAME")
        if not self.BUSINESS_ABN:
            missing.append("BUSINESS_ABN")
        return missing


# Singleton -- import and use `config` everywhere
config = Config()
