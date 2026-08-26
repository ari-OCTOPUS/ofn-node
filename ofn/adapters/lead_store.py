from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Mapping

from .sqlite_base import Pool, add_column_if_absent, apply_schema
from ..kernel.painting_math import b2b_account_score, lead_priority, source_quality, tender_score

MAX_TEXT = 1200
MAX_PAGE = 100

# Contact permission is evidence, not a property inferred from a phone number or
# a public email address.  Values are deliberately explicit and normalized at
# the store boundary so callers cannot mint a new legal basis or channel by
# spelling it differently.
CONTACT_LEGAL_BASES = frozenset({
    "explicit_consent",
    "inbound_request",
    "existing_customer",
    "existing_business_relationship",
    "contract",
    "legitimate_interest",
    "legal_obligation",
})
_POLICY_LEGAL_BASES = CONTACT_LEGAL_BASES | {"suppression"}
_LEGAL_BASIS_ALIASES = {
    "consent": "explicit_consent",
    "express_consent": "explicit_consent",
    "explicit_consent": "explicit_consent",
    "customer_request": "inbound_request",
    "customer_enquiry": "inbound_request",
    "inquiry": "inbound_request",
    "quote_request": "inbound_request",
    "requested_contact": "inbound_request",
    "inbound_request": "inbound_request",
    "existing_customer": "existing_customer",
    "existing_business_relationship": "existing_business_relationship",
    "contract": "contract",
    "legitimate_interest": "legitimate_interest",
    "legal_obligation": "legal_obligation",
    "suppression": "suppression",
}
CONTACT_CHANNELS = frozenset({
    "phone", "sms", "email", "whatsapp", "telegram",
    "instagram", "facebook", "messenger",
})
_CHANNEL_ALIASES = {
    "call": "phone", "voice": "phone", "telephone": "phone",
    "text": "sms", "text_message": "sms",
    "e-mail": "email", "mail": "email",
    "instagram_dm": "instagram", "facebook_dm": "facebook",
}
LEAD_STATUSES = frozenset({
    "new", "review", "contacted", "quoted", "won", "lost", "spam", "archived",
})
DELIVERY_DERIVED_STATUSES = frozenset({"contacted", "quoted", "won"})
TERMINAL_LEAD_STATUSES = frozenset({"won", "lost", "spam", "archived"})
# Generic edits may classify/close a lead, but delivery evidence owns the three
# delivery-derived states.  Reopening a terminal row has its own owner method.
_GENERIC_STATUS_TRANSITIONS = {
    "new": frozenset({"new", "review", "lost", "spam", "archived"}),
    "review": frozenset({"new", "review", "lost", "spam", "archived"}),
    "contacted": frozenset({"contacted", "review", "lost", "spam", "archived"}),
    "quoted": frozenset({"quoted", "lost", "archived"}),
    "won": frozenset({"won"}),
    "lost": frozenset({"lost"}),
    "spam": frozenset({"spam"}),
    "archived": frozenset({"archived"}),
}

_CONTACT_POLICY_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS lead_contact_policy (
        tenant_id TEXT NOT NULL,
        lead_id TEXT NOT NULL,
        contact_phone_hash TEXT NOT NULL DEFAULT '',
        contact_email_hash TEXT NOT NULL DEFAULT '',
        legal_basis TEXT NOT NULL
          CHECK (legal_basis IN (
            'explicit_consent','inbound_request','existing_customer',
            'existing_business_relationship','contract','legitimate_interest',
            'legal_obligation','suppression'
          )),
        channel_scope_json TEXT NOT NULL DEFAULT '[]',
        proof_digest TEXT NOT NULL CHECK (length(trim(proof_digest)) > 0),
        do_not_contact INTEGER NOT NULL DEFAULT 0
          CHECK (do_not_contact IN (0,1)),
        opted_out_at TEXT NOT NULL DEFAULT '',
        revoked_at TEXT NOT NULL DEFAULT '',
        reason TEXT NOT NULL DEFAULT '',
        recorded_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (tenant_id, lead_id)
    )
"""

# Lead fields `_lead_components` reads from. Changing any of these on an
# existing lead means the stored score is stale, so `update_lead` recomputes.
SCORE_RELEVANT = frozenset({"message", "job_type", "budget_text", "distance_km", "rooms", "phone", "email"})


def _add_score_json(conn) -> None:
    """Fold `score_json` into `painting_leads` files created before it shipped.

    A single source of truth shared by both `LeadStore.__init__` and the boot
    supervisor (`boot.MIGRATIONS`), so the two never disagree on whether this
    column exists — which is exactly the disagreement that would raise a
    `schema:painting(critical)` flag at boot.
    """
    add_column_if_absent(conn, "painting_leads", "score_json", "TEXT NOT NULL DEFAULT '{}'")


def _add_ops_columns(conn) -> None:
    """O5 columns: follow-up due date, last contact, outcome reason, and the
    contact hashes used only for duplicate warning (never for storage of the
    contact itself — the canonical phone/email stay as typed)."""
    for col, ddl in (
        ("next_action_at", "TEXT NOT NULL DEFAULT ''"),
        ("last_contacted_at", "TEXT NOT NULL DEFAULT ''"),
        ("outcome_reason", "TEXT NOT NULL DEFAULT ''"),
        ("contact_phone_hash", "TEXT NOT NULL DEFAULT ''"),
        ("contact_email_hash", "TEXT NOT NULL DEFAULT ''"),
    ):
        add_column_if_absent(conn, "painting_leads", col, ddl)


def _add_booked_revenue_columns(conn) -> None:
    """P1 revenue: booked amount for a won job (independent of status text)."""
    for col, ddl in (
        ("booked_amount_cents", "INTEGER"),
        ("booked_currency", "TEXT NOT NULL DEFAULT 'AUD'"),
        ("booked_at", "TEXT NOT NULL DEFAULT ''"),
        ("payment_ref_digest", "TEXT NOT NULL DEFAULT ''"),
    ):
        add_column_if_absent(conn, "painting_leads", col, ddl)


def _add_contact_integrity_schema(conn) -> None:
    """Add contact-policy evidence and the one-follow-up counters.

    Both operations are safe on old files and on every subsequent boot.  The
    policy table is intentionally separate from the lead's raw contact fields:
    it contains only one-way hashes and evidence digests, never new PII.
    """
    for col, ddl in (
        ("follow_up_count", "INTEGER NOT NULL DEFAULT 0"),
        ("last_follow_up_at", "TEXT NOT NULL DEFAULT ''"),
    ):
        add_column_if_absent(conn, "painting_leads", col, ddl)
    conn.execute(_CONTACT_POLICY_TABLE_SQL)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lead_contact_policy_phone "
        "ON lead_contact_policy (tenant_id, contact_phone_hash)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lead_contact_policy_email "
        "ON lead_contact_policy (tenant_id, contact_email_hash)"
    )


# Same contract as the other adapters' `MIGRATIONS`: idempotent callables that
# each take a connection and bring an older file forward.
MIGRATIONS = (
    _add_score_json,
    _add_ops_columns,
    _add_booked_revenue_columns,
    _add_contact_integrity_schema,
)

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS painting_leads (
        lead_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        source TEXT NOT NULL,
        source_ref TEXT NOT NULL DEFAULT '',
        customer_name TEXT NOT NULL DEFAULT '',
        phone TEXT NOT NULL DEFAULT '',
        email TEXT NOT NULL DEFAULT '',
        suburb TEXT NOT NULL DEFAULT '',
        distance_km REAL,
        job_type TEXT NOT NULL DEFAULT '',
        rooms TEXT NOT NULL DEFAULT '',
        budget_text TEXT NOT NULL DEFAULT '',
        message TEXT NOT NULL DEFAULT '',
        score INTEGER NOT NULL DEFAULT 0,
        temperature TEXT NOT NULL DEFAULT 'new'
          CHECK (temperature IN ('hot','warm','cold','new')),
        status TEXT NOT NULL DEFAULT 'new'
          CHECK (status IN ('new','review','contacted','quoted','won','lost','spam','archived')),
        next_action TEXT NOT NULL DEFAULT '',
        assigned_to TEXT NOT NULL DEFAULT '',
        tags_json TEXT NOT NULL DEFAULT '[]',
        score_json TEXT NOT NULL DEFAULT '{}',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        next_action_at TEXT NOT NULL DEFAULT '',
        last_contacted_at TEXT NOT NULL DEFAULT '',
        outcome_reason TEXT NOT NULL DEFAULT '',
        contact_phone_hash TEXT NOT NULL DEFAULT '',
        contact_email_hash TEXT NOT NULL DEFAULT '',
        follow_up_count INTEGER NOT NULL DEFAULT 0,
        last_follow_up_at TEXT NOT NULL DEFAULT '',
        booked_amount_cents INTEGER,
        booked_currency TEXT NOT NULL DEFAULT 'AUD',
        booked_at TEXT NOT NULL DEFAULT '',
        payment_ref_digest TEXT NOT NULL DEFAULT ''
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_leads_status ON painting_leads (tenant_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_painting_leads_score ON painting_leads (tenant_id, score DESC, created_at DESC)",
    _CONTACT_POLICY_TABLE_SQL,
    "CREATE INDEX IF NOT EXISTS idx_lead_contact_policy_phone ON lead_contact_policy (tenant_id, contact_phone_hash)",
    "CREATE INDEX IF NOT EXISTS idx_lead_contact_policy_email ON lead_contact_policy (tenant_id, contact_email_hash)",
    """
    CREATE TABLE IF NOT EXISTS painting_marketing_channels (
        channel_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        handle TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL DEFAULT '',
        connection TEXT NOT NULL DEFAULT 'planned'
          CHECK (connection IN ('planned','manual','connected','paused','blocked')),
        inbound_enabled INTEGER NOT NULL DEFAULT 0,
        outbound_enabled INTEGER NOT NULL DEFAULT 0,
        notes TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL,
        UNIQUE (tenant_id, kind, title)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_channels_tenant ON painting_marketing_channels (tenant_id, kind, connection)",
    """
    CREATE TABLE IF NOT EXISTS painting_campaigns (
        campaign_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        title TEXT NOT NULL,
        objective TEXT NOT NULL DEFAULT '',
        channel_ids_json TEXT NOT NULL DEFAULT '[]',
        status TEXT NOT NULL DEFAULT 'idea'
          CHECK (status IN ('idea','draft','scheduled','running','paused','done')),
        next_step TEXT NOT NULL DEFAULT '',
        due_at TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_campaigns_tenant ON painting_campaigns (tenant_id, status, due_at)",
    """
    CREATE TABLE IF NOT EXISTS painting_modules (
        module_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        area TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'planned'
          CHECK (status IN ('planned','manual','connected','paused','blocked')),
        output TEXT NOT NULL DEFAULT '',
        next_step TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL,
        UNIQUE (tenant_id, area, title)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_modules_tenant ON painting_modules (tenant_id, area, status)",
    """
    CREATE TABLE IF NOT EXISTS painting_interactions (
        interaction_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        channel TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'message',
        person TEXT NOT NULL DEFAULT '',
        subject TEXT NOT NULL DEFAULT '',
        body TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'new'
          CHECK (status IN ('new','needs_reply','converted','done','archived')),
        lead_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_interactions_tenant ON painting_interactions (tenant_id, status, created_at)",
    """
    CREATE TABLE IF NOT EXISTS painting_sources (
        source_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        official_url TEXT NOT NULL DEFAULT '',
        integration_path TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'planned'
          CHECK (status IN ('priority','planned','later','guarded','unknown','blocked')),
        automation_level TEXT NOT NULL DEFAULT 'read_only_first',
        approval_required INTEGER NOT NULL DEFAULT 1,
        intent_score REAL NOT NULL DEFAULT 0.5,
        risk_score REAL NOT NULL DEFAULT 0.5,
        score REAL NOT NULL DEFAULT 0.0,
        recommendation TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL,
        UNIQUE (tenant_id, name)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_sources_tenant ON painting_sources (tenant_id, category, status, score DESC)",
    """
    CREATE TABLE IF NOT EXISTS painting_b2b_accounts (
        account_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        segment TEXT NOT NULL,
        business_name TEXT NOT NULL,
        suburb TEXT NOT NULL DEFAULT '',
        service_area TEXT NOT NULL DEFAULT '',
        website TEXT NOT NULL DEFAULT '',
        contact_channel TEXT NOT NULL DEFAULT '',
        evidence_url TEXT NOT NULL DEFAULT '',
        stage TEXT NOT NULL DEFAULT 'discovered'
          CHECK (stage IN ('discovered','researched','qualified','meeting','vendor_onboarding','opportunity','won','lost','archived')),
        score REAL NOT NULL DEFAULT 0.0,
        recommendation TEXT NOT NULL DEFAULT '',
        score_json TEXT NOT NULL DEFAULT '{}',
        outreach_permission TEXT NOT NULL DEFAULT 'unknown'
          CHECK (outreach_permission IN ('unknown','approved_channel','relationship','suppressed')),
        next_action TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_b2b_tenant ON painting_b2b_accounts (tenant_id, segment, stage, score DESC)",
    """
    CREATE TABLE IF NOT EXISTS painting_tenders (
        tender_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        source TEXT NOT NULL,
        source_url TEXT NOT NULL DEFAULT '',
        title TEXT NOT NULL,
        buyer_name TEXT NOT NULL DEFAULT '',
        location TEXT NOT NULL DEFAULT '',
        closing_at TEXT NOT NULL DEFAULT '',
        access_mode TEXT NOT NULL DEFAULT 'manual'
          CHECK (access_mode IN ('alert_email','official_api','owner_upload','manual')),
        evidence_status TEXT NOT NULL DEFAULT 'unverified'
          CHECK (evidence_status IN ('unverified','verified','expired')),
        status TEXT NOT NULL DEFAULT 'received'
          CHECK (status IN ('received','verified_source','extracted','scored','owner_review','watching','skipped','bid_approved','documents_ready','submission_drafted','owner_submitted','submitted','lost','won','cancelled')),
        score REAL NOT NULL DEFAULT 0.0,
        recommendation TEXT NOT NULL DEFAULT '',
        score_json TEXT NOT NULL DEFAULT '{}',
        missing_facts_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_tenders_tenant ON painting_tenders (tenant_id, status, score DESC, closing_at)",
    """
    CREATE TABLE IF NOT EXISTS painting_vendor_applications (
        application_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'lead',
        account_id TEXT NOT NULL DEFAULT '',
        company_name TEXT NOT NULL,
        portal_url TEXT NOT NULL DEFAULT '',
        source_type TEXT NOT NULL DEFAULT 'supplier_portal'
          CHECK (source_type IN ('supplier_portal','EOI','referral','tender','manual')),
        status TEXT NOT NULL DEFAULT 'discovered'
          CHECK (status IN ('discovered','requirements_extracted','pack_incomplete','ready_for_owner','submitted','under_review','approved','declined','renewal_due','blocked')),
        requirements_json TEXT NOT NULL DEFAULT '[]',
        missing_json TEXT NOT NULL DEFAULT '[]',
        risk_note TEXT NOT NULL DEFAULT '',
        next_action TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_painting_vendor_tenant ON painting_vendor_applications (tenant_id, status, updated_at)",
)

_SEED_CHANNELS = (
    ("website", "وب‌سایت / فرم تماس", "planned", 1, 0, "فرم تماس و لندینگ؛ هنوز وبهوک واقعی تنظیم نشده."),
    ("telegram", "تلگرام — بات لید نقاشی", "connected", 1, 0, "ورود و مینی‌اپ از تلگرام وصل است؛ ارسال بیرونی با گیت مالک."),
    ("google", "Google Business Profile", "planned", 1, 0, "برای تماس‌های محلی و ریویوها."),
    ("instagram", "Instagram", "planned", 1, 1, "محتوای قبل/بعد، استوری، پیام‌های ورودی."),
    ("facebook", "Facebook Groups/Marketplace", "planned", 1, 1, "لید محله‌ای و ریتارگت دستی."),
    ("tiktok", "TikTok / Reels", "planned", 0, 1, "ویدئوهای کوتاه قبل/بعد."),
    ("email", "Email / quote follow-up", "planned", 0, 1, "پیگیری بعد از بازدید؛ ارسال خودکار هنوز خاموش."),
 )

_SEED_MODULES = (
    ("manual_intake", "lead_finder", "ثبت دستی لید", "connected", "لید داخل پنل", "استفاده روزمره", "برای تماس تلفنی، معرفی و لید حضوری."),
    ("telegram_intake", "lead_finder", "مینی‌اپ تلگرام لید", "manual", "لید از تلگرام", "تنظیم allowlist لید", "بات تعریف شده ولی ورود شریک لید به allowlist نیاز دارد."),
    ("website_form", "lead_finder", "فرم وب‌سایت/لندینگ", "planned", "لید فرم تماس", "ساخت فرم و وبهوک", "به محض داشتن سایت، POST به همین CRM وصل می‌شود."),
    ("google_business", "lead_finder", "Google Business Profile", "planned", "تماس/فرم محلی", "اتصال دستی یا API", "بهترین منبع محلی برای نقاشی ساختمان."),
    ("instagram_dm", "lead_finder", "Instagram DM/Comment", "planned", "پیام ورودی", "ثبت کانال و روتین پاسخ", "تا قبل از توکن رسمی، تعامل‌ها دستی ثبت می‌شوند."),
    ("facebook_groups", "lead_finder", "Facebook Groups/Marketplace", "planned", "لید محله‌ای", "تعریف گروه‌ها", "مناسب درخواست‌های فوری محله‌ای."),
    ("lead_scoring", "automation", "امتیازدهی لید", "connected", "hot/warm/cold", "تنظیم وزن‌ها بعد از داده واقعی", "امتیاز فعلاً بر متن، فاصله و اطلاعات تماس است."),
    ("duplicate_check", "automation", "تشخیص تکراری", "planned", "هشدار تکراری", "اضافه‌کردن phone/email match", "برای جلوگیری از دوبار تماس گرفتن."),
    ("quote_followup", "marketing", "پیگیری قیمت پیشنهادی", "planned", "کار بعدی برای لید", "ساخت قالب پیام", "ارسال واقعی همچنان باید از outbox و تأیید مالک رد شود."),
    ("content_calendar", "marketing", "تقویم محتوا", "manual", "کمپین و پست", "پرکردن تقویم هفتگی", "قبل/بعد، ریویو، نکته نگهداری رنگ."),
    ("review_request", "marketing", "درخواست ریویو", "planned", "درخواست پس از اتمام کار", "نوشتن متن و زمان‌بندی", "برای رشد Google Business مهم است."),
    ("social_inbox", "marketing", "این‌باکس شبکه‌های اجتماعی", "manual", "تعامل قابل پیگیری", "ثبت پیام‌ها در تب مارکتینگ", "تا اتصال API، ورودی‌ها دستی یا نیمه‌دستی ثبت می‌شوند."),
)


def _clean(value: object, limit: int = MAX_TEXT) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _contact_hash(value: object) -> str:
    """SHA-256 of a normalised contact for duplicate warning.

    Normalisation maps AU formats to one form: leading 0 becomes +61, and
    separators are stripped — so +61 412 345 678, 0412345678 and
    +61412345678 hash alike. The hash is one-way — the contact itself is
    never reconstructable from it.
    """
    import hashlib
    raw = "" if value is None else str(value)
    norm = re.sub(r"[\s\-().+]", "", raw).strip().lower()
    if norm.startswith("0") and len(norm) >= 9:
        norm = "61" + norm[1:]
    if not norm:
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def _num(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        text = str(value).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace(",", "")
        return float(text)
    except (TypeError, ValueError):
        return None


def _int(value: object, default: int = 0) -> int:
    try:
        text = str(value).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _json_list(value: object, limit: int = 12) -> str:
    if isinstance(value, str):
        items = [x.strip() for x in value.split(",") if x.strip()]
    elif isinstance(value, (list, tuple)):
        items = [_clean(x, 40) for x in value if _clean(x, 40)]
    else:
        items = []
    return json.dumps(items[:limit], ensure_ascii=False)


def _normalize_channel(value: object) -> str:
    channel = _clean(value, 40).casefold().replace("-", "_").replace(" ", "_")
    return _CHANNEL_ALIASES.get(channel, channel)


def _channel_scope(value: object) -> tuple[str, ...]:
    """Return a de-duplicated, deterministic tuple of recognized channels."""
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("["):
            try:
                raw = json.loads(stripped)
            except (TypeError, json.JSONDecodeError):
                raw = [stripped]
        else:
            raw = stripped.split(",")
    elif isinstance(value, (list, tuple, set, frozenset)):
        raw = value
    else:
        raw = []
    channels = {_normalize_channel(item) for item in raw}
    return tuple(sorted(c for c in channels if c in CONTACT_CHANNELS))


def _legal_basis(value: object) -> str:
    basis = _clean(value, 80).casefold().replace("-", "_").replace(" ", "_")
    return _LEGAL_BASIS_ALIASES.get(basis, basis)


def _policy_row(row) -> dict:
    out = dict(row)
    try:
        channels = json.loads(out.pop("channel_scope_json") or "[]")
    except (TypeError, json.JSONDecodeError):
        channels = []
    out["channel_scope"] = list(_channel_scope(channels))
    out["channels"] = list(out["channel_scope"])
    out["do_not_contact"] = bool(out.get("do_not_contact"))
    return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _row(row) -> dict:
    out = dict(row)
    for key in ("tags_json", "channel_ids_json"):
        if key in out:
            dst = key[:-5] if key.endswith("_json") else key
            try:
                out[dst] = json.loads(out[key] or "[]")
            except json.JSONDecodeError:
                out[dst] = []
            del out[key]
    return out


def _lead_score_detail(row: Mapping[str, object]) -> dict:
    """Transient explanation for the legacy lead score columns.

    The table predates score_json.  Rather than forcing a destructive rewrite,
    every read returns the explanation derived from the fields that produced
    the score.  This keeps old rows compatible and gives the owner an honest
    reason string instead of a naked number.
    """
    score = _int(row.get("score"), 0)
    reasons: list[str] = []
    text = " ".join(str(row.get(k) or "").casefold() for k in ("message", "job_type", "budget_text"))
    if row.get("phone"):
        reasons.append("شماره تماس دارد")
    if row.get("email"):
        reasons.append("ایمیل دارد")
    for word, label in (("urgent", "فوریت"), ("asap", "فوریت"), ("this week", "زمان نزدیک"), ("quote", "درخواست قیمت"), ("exterior", "کار بیرونی"), ("commercial", "تجاری"), ("فوری", "فوریت"), ("قیمت", "درخواست قیمت"), ("نما", "نما/بیرونی")):
        if word in text and label not in reasons:
            reasons.append(label)
    try:
        dist = float(row.get("distance_km")) if row.get("distance_km") is not None else None
    except (TypeError, ValueError):
        dist = None
    if dist is not None:
        reasons.append("نزدیک" if dist <= 10 else "دور" if dist > 30 else "فاصله متوسط")
    if not reasons:
        reasons.append("امتیاز با داده‌های محدود و مقدار پایه ساخته شده")
    return {
        "score": score,
        "temperature": row.get("temperature") or LeadStore._temperature(score),
        "explanation": reasons[:8],
        "recommendation": "owner_review" if score >= 72 else "follow_up" if score >= 45 else "nurture",
    }


def _lead_detail(row: Mapping[str, object]) -> dict:
    """`score_detail` for a lead read.

    Prefers the stored `score_json` (the `lead_priority` model payload, same
    shape B2B/tenders use) and falls back to `_lead_score_detail` only for rows
    written before the column existed. Either branch yields the `explanation`
    and `recommendation` the owner dashboard already consumes, so the rest of
    the system does not care which scoring path produced it.
    """
    raw = row.get("score_json") or "{}"
    try:
        detail = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, dict) else {})
    except json.JSONDecodeError:
        detail = {}
    if detail:
        return detail
    return _lead_score_detail(row)


def _json_obj(value: object) -> str:
    return json.dumps(value if isinstance(value, dict) else {}, ensure_ascii=False, sort_keys=True)


def _slug(value: str, limit: int = 56) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:limit] or hashlib.sha1((value or "x").encode()).hexdigest()[:12]


class LeadStore:
    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        # `MIGRATIONS` is shared with the boot supervisor so the two agree on
        # the file's shape — see `_add_score_json`.
        apply_schema(self._conn, SCHEMA, MIGRATIONS)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        return self._pool.conn

    def ensure_seed_channels(self, tenant: str, now_iso: str) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            for kind, title, connection, inbound, outbound, notes in _SEED_CHANNELS:
                slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:32]
                cid = f"{tenant}:{kind}:{slug}"
                self._conn.execute(
                    "INSERT OR IGNORE INTO painting_marketing_channels "
                    "(channel_id, tenant_id, kind, title, connection, inbound_enabled, outbound_enabled, notes, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (cid, tenant, kind, title, connection, inbound, outbound, notes, now_iso),
                )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def create_lead(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        source = _clean(data.get("source") or "manual", 80) or "manual"
        source_ref = _clean(data.get("source_ref") or data.get("url") or "", 300)
        base = _clean(data.get("lead_id") or data.get("id") or "", 120)
        if not base:
            safe = re.sub(r"[^a-zA-Z0-9]+", "-", f"{source}-{source_ref}-{now_iso}").strip("-")
            digest = hashlib.sha1(f"{source}|{source_ref}|{now_iso}".encode()).hexdigest()[:16]
            base = safe[:96] or digest
        lead_id = f"{tenant}:{base}" if not base.startswith(f"{tenant}:") else base
        row = {
            "lead_id": lead_id,
            "tenant_id": tenant,
            "source": source,
            "source_ref": source_ref,
            "customer_name": _clean(data.get("customer_name") or data.get("name") or "", 120),
            "phone": _clean(data.get("phone") or "", 80),
            "email": _clean(data.get("email") or "", 160),
            "suburb": _clean(data.get("suburb") or data.get("location") or "", 120),
            "distance_km": _num(data.get("distance_km")),
            "job_type": _clean(data.get("job_type") or data.get("title") or "", 160),
            "rooms": _clean(data.get("rooms") or "", 80),
            "budget_text": _clean(data.get("budget_text") or data.get("budget") or "", 120),
            "message": _clean(data.get("message") or data.get("text") or "", MAX_TEXT),
            "score": max(0, min(100, _int(data.get("score"), 0))),
            "temperature": _clean(data.get("temperature") or "new", 12),
            # Intake/upsert is not delivery evidence and cannot close a lead.
            # Only the two non-terminal pre-delivery states are accepted here;
            # contacted/quoted/won and every terminal state have dedicated paths.
            "status": _clean(data.get("status") or "new", 20).casefold(),
            "next_action": _clean(data.get("next_action") or "بررسی و تماس", 220),
            "assigned_to": _clean(data.get("assigned_to") or "", 80),
            "tags_json": _json_list(data.get("tags")),
            "score_json": "{}",
            "notes": _clean(data.get("notes") or "", MAX_TEXT),
            "created_at": now_iso,
            "updated_at": now_iso,
            # Contact hashes (O5): only for duplicate warning; the canonical
            # phone/email stay as typed above.
            "contact_phone_hash": _contact_hash(data.get("phone") or ""),
            "contact_email_hash": _contact_hash(data.get("email") or ""),
            "next_action_at": _clean(data.get("next_action_at") or "", 40),
            "last_contacted_at": _clean(data.get("last_contacted_at") or "", 40),
            "outcome_reason": _clean(data.get("outcome_reason") or "", 240),
        }
        if row["temperature"] not in {"hot", "warm", "cold", "new"}:
            row["temperature"] = "new"
        if row["status"] not in {"new", "review"}:
            row["status"] = "new"
        if not row["score"]:
            row["score"], row["temperature"], row["score_json"] = self._score_payload(row)
        cols = tuple(row.keys())
        placeholders = ",".join("?" for _ in cols)
        # Intake retries may refresh the lead details, but must never reopen,
        # rewind, close, or fabricate delivery on an existing lifecycle row.
        updates = ",".join(
            f"{c}=excluded.{c}" for c in cols
            if c not in {"lead_id", "created_at", "status"}
        )
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO painting_leads ({','.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(lead_id) DO UPDATE SET {updates}",
                tuple(row[c] for c in cols),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "lead": self.get(tenant, lead_id)}

    def _lead_components(self, row: Mapping[str, object]) -> Mapping[str, float | None]:
        """Derive `lead_priority`'s seven normalized components from a lead row.

        `lead_priority` is the tested, explainable model B2B/tenders/sources
        already use, but it speaks in V/I/G/T/Q/R/C axes that a sparse lead
        (often just a name, phone and a sentence) does not carry directly. This
        is the bridge: each axis is read from the signals that *are* present,
        and any axis with no signal is left `None` so the model flags the row
        `incomplete` rather than silently scoring it as a sure thing. Scoring
        alone never grants permission to act; missing high-risk data is the
        policy layer's job, not the score's.

        The mapping is deliberately conservative and intentionally tunable —
        these are starting heuristics to replace the opaque keyword count, not
        calibrated business truth. Armin's real intake data is what should
        eventually retune the weights and these component readings.
        """
        text = " ".join(str(row.get(k) or "").casefold() for k in ("message", "job_type", "budget_text"))
        try:
            dist = float(row.get("distance_km")) if row.get("distance_km") not in (None, "") else None
        except (TypeError, ValueError):
            dist = None
        has_contact = bool(row.get("phone") or row.get("email"))
        is_commercial = any(w in text for w in ("commercial", "retail", "office", "strata", "تجاری", "اداری", "استرا"))

        # V  value/fit      — bigger or commercial scope reads higher
        v = 0.78 if any(w in text for w in ("whole", "entire", "full house", "commercial", "کل", "تمام", "نما")) else 0.5 if any(w in text for w in ("room", "اتاق")) else None
        # I  intent        — explicit quote/urgency request reads higher
        i = 0.8 if any(w in text for w in ("quote", "قیمت", "برآورد")) else 0.6 if any(w in text for w in ("urgent", "asap", "this week", "فوری", "زود")) else None
        # G  geography     — closeness from the service radius
        g = None if dist is None else 0.85 if dist <= 10 else 0.55 if dist <= 30 else 0.3
        # T  timing       — near-term availability
        t = 0.8 if any(w in text for w in ("this week", "next week", "asap", "فوری", "این هفته")) else 0.5 if any(w in text for w in ("soon", "زود")) else None
        # Q  data quality — has contactability + a described scope
        q = (0.6 if has_contact else 0.3) + (0.25 if row.get("rooms") else 0.0) + (0.15 if row.get("budget_text") else 0.0)
        q = min(1.0, q) if (has_contact or row.get("rooms") or row.get("budget_text")) else None
        # R  risk          — commercial/strata carries more site/contract risk
        r = 0.55 if is_commercial else 0.3
        # C  cost clarity  — a stated budget means fewer hidden-cost surprises
        c = 0.5 if row.get("budget_text") else None
        return {"V": v, "I": i, "G": g, "T": t, "Q": q, "R": r, "C": c}

    def _score_payload(self, row: Mapping[str, object]) -> tuple[int, str, str]:
        """Run `lead_priority` on a lead row.

        Returns `(score_0_100, temperature, score_json)` so both create and
        update write the exact same shape. Same model, same serialization, same
        explanation contract the owner dashboard already trusts for B2B and
        tenders — no second scoring path.
        """
        res = lead_priority(self._lead_components(row))
        return (
            round(res.score * 100),
            self._temperature(round(res.score * 100)),
            json.dumps(
                {"model": "lead_priority", "score": res.score, "incomplete": res.incomplete,
                 "components": dict(res.components), "recommendation": res.recommendation,
                 "explanation": list(res.explanation)},
                ensure_ascii=False, sort_keys=True,
            ),
        )

    @staticmethod
    def _temperature(score: int) -> str:
        if score >= 72:
            return "hot"
        if score >= 45:
            return "warm"
        if score > 0:
            return "cold"
        return "new"

    def get(self, tenant: str, lead_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM painting_leads WHERE tenant_id = ? AND lead_id = ?",
            (tenant, lead_id),
        ).fetchone()
        if not row:
            return None
        out = _row(row)
        out["score_detail"] = _lead_detail(out)
        return out

    def list_leads(self, tenant: str, *, status: str = "", q: str = "", limit: int = 50) -> list[dict]:
        limit = max(1, min(MAX_PAGE, int(limit or 50)))
        where = ["tenant_id = ?"]
        args: list[object] = [tenant]
        if status:
            where.append("status = ?")
            args.append(status)
        if q:
            # Server-side ESCAPE (finding 19): `%` and `_` in the user's
            # query are literal characters, not wildcards. Without this the
            # UI's escLike is the only guard, and a client that forgets it
            # turns a search for "50%" into "everything".
            escaped = (q.replace("\\", "\\\\")
                        .replace("%", "\\%")
                        .replace("_", "\\_"))
            like = f"%{escaped}%"
            where.append("(customer_name LIKE ? ESCAPE '\\' OR suburb LIKE ? "
                         "ESCAPE '\\' OR job_type LIKE ? ESCAPE '\\' OR "
                         "message LIKE ? ESCAPE '\\')")
            args += [like, like, like, like]
        rows = self._conn.execute(
            "SELECT * FROM painting_leads WHERE " + " AND ".join(where) +
            " ORDER BY CASE status WHEN 'new' THEN 0 WHEN 'review' THEN 1 WHEN 'contacted' THEN 2 WHEN 'quoted' THEN 3 ELSE 9 END, score DESC, created_at DESC LIMIT ?",
            (*args, limit),
        ).fetchall()
        out = [_row(r) for r in rows]
        for item in out:
            item["score_detail"] = _lead_detail(item)
        return out

    def update_lead(
            self, tenant: str, lead_id: str, data: Mapping[str, object], *,
            now_iso: str, authority: str = "partner",
            actor: str | None = None) -> dict:
        """Edit mutable lead fields without bypassing lifecycle integrity.

        ``authority`` defaults to the least privilege so a direct store call is
        safe. ``actor`` is accepted as a compatibility alias; only the exact
        values ``owner``/``system`` confer their corresponding authority.  The
        delivery-derived states are never writable here, including by owner.
        Their dedicated APIs require the receipt/evidence associated with the
        transition. Terminal rows are locked until ``owner_reopen_lead``.
        """
        effective_authority = _clean(authority or "partner", 20).casefold()
        if actor is not None and effective_authority == "partner":
            actor_authority = _clean(actor, 20).casefold()
            if actor_authority in {"owner", "system"}:
                effective_authority = actor_authority
        if effective_authority not in {"partner", "owner", "system"}:
            effective_authority = "partner"

        existing = self.get(tenant, lead_id)
        if not existing:
            return {"ok": False, "error": "لید پیدا نشد", "rule": "lead:not-found"}

        requested_status: str | None = None
        if "status" in data:
            requested_status = _clean(data.get("status"), 20).casefold()
            current_status = str(existing.get("status") or "new")
            if requested_status not in LEAD_STATUSES:
                return {"ok": False, "error": "وضعیت لید نامعتبر است", "rule": "lead:invalid-status"}
            if requested_status in DELIVERY_DERIVED_STATUSES and requested_status != current_status:
                return {
                    "ok": False,
                    "error": "این وضعیت فقط با متد اختصاصی و مدرک delivery قابل ثبت است",
                    "rule": "lead:delivery-status-requires-dedicated-method",
                }
            if current_status in TERMINAL_LEAD_STATUSES and requested_status != current_status:
                return {
                    "ok": False,
                    "error": "لید نهایی قفل است؛ بازگشایی فقط با مالک و دلیل",
                    "rule": "lead:terminal-locked",
                }
            if requested_status not in _GENERIC_STATUS_TRANSITIONS.get(current_status, frozenset()):
                return {"ok": False, "error": "پرش وضعیت مجاز نیست", "rule": "lead:invalid-transition"}

        allowed = {"status", "temperature", "score", "next_action", "assigned_to", "notes", "tags", "customer_name", "phone", "email", "suburb", "distance_km", "job_type", "rooms", "budget_text", "message", "next_action_at", "outcome_reason"}
        fields = []
        args: list[object] = []
        for key in allowed:
            if key not in data:
                continue
            if key == "phone" or key == "email":
                # Contact change re-hashes the duplicate fingerprint.
                fields.append(f"{key} = ?")
                args.append(_clean(data.get(key), 220))
                fields.append(f"contact_{key}_hash = ?")
                args.append(_contact_hash(data.get(key)))
                continue
            col = "tags_json" if key == "tags" else key
            if key == "tags":
                val = _json_list(data.get(key))
            elif key == "distance_km":
                val = _num(data.get(key))
            elif key == "score":
                val = max(0, min(100, _int(data.get(key), 0)))
            elif key == "status":
                val = requested_status
            else:
                val = _clean(data.get(key), MAX_TEXT if key in {"notes", "message"} else 220)
            fields.append(f"{col} = ?")
            args.append(val)
        if not fields:
            return {"ok": False, "error": "هیچ فیلدی برای تغییر نبود"}
        # A change to any score-relevant field makes the stored score stale.
        # Recompute from the row-as-it-will-be, so the score, temperature and
        # explanation always reflect the current data — never a frozen snapshot
        # from when the lead was first created. An explicit `score` in `data`
        # overrides the model (kept for owner override), so only recompute when
        # the owner did not hand-set the score.
        if "score" not in data and any(k in data for k in SCORE_RELEVANT):
            merged = {**existing, **{k: data[k] for k in data if k in existing or k == "tags"}}
            new_score, new_temp, new_json = self._score_payload(merged)
            fields += ["score = ?", "temperature = ?", "score_json = ?"]
            args += [new_score, new_temp, new_json]
        fields.append("updated_at = ?")
        args.append(now_iso)
        args += [tenant, lead_id]
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE painting_leads SET " + ", ".join(fields) + " WHERE tenant_id = ? AND lead_id = ?",
                tuple(args),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        if cur.rowcount != 1:
            return {"ok": False, "error": "لید پیدا نشد"}
        return {"ok": True, "lead": self.get(tenant, lead_id)}

    def owner_update_lead(
            self, tenant: str, lead_id: str, data: Mapping[str, object], *,
            now_iso: str, actor: str = "owner") -> dict:
        """Explicit compatibility entry point for ordinary owner edits."""
        return self.update_lead(
            tenant, lead_id, data, now_iso=now_iso,
            authority="owner", actor=actor,
        )

    def owner_reopen_lead(
            self, tenant: str, lead_id: str, *, reason: str,
            now_iso: str, status: str = "review",
            authority: str = "owner", actor: str | None = None) -> dict:
        """Owner-only terminal unlock, requiring an auditable nonblank reason."""
        effective = _clean(authority or "partner", 20).casefold()
        if actor is not None and effective == "partner" and _clean(actor, 20).casefold() == "owner":
            effective = "owner"
        why = _clean(reason, 240)
        target = _clean(status, 20).casefold()
        if effective != "owner":
            return {"ok": False, "error": "فقط مالک می‌تواند لید را باز کند", "rule": "lead:owner-required"}
        if not why:
            return {"ok": False, "error": "دلیل بازگشایی لازم است", "rule": "lead:reopen-reason-required"}
        if target not in {"new", "review"}:
            return {"ok": False, "error": "وضعیت بازگشایی نامعتبر است", "rule": "lead:invalid-reopen-target"}
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE painting_leads SET status = ?, outcome_reason = ?, updated_at = ? "
                "WHERE tenant_id = ? AND lead_id = ? "
                "AND status IN ('won','lost','spam','archived')",
                (target, why, now_iso, tenant, lead_id),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        if cur.rowcount != 1:
            lead = self.get(tenant, lead_id)
            return {
                "ok": False,
                "error": "لید پیدا نشد" if lead is None else "لید نهایی نیست",
                "rule": "lead:not-found" if lead is None else "lead:not-terminal",
            }
        return {"ok": True, "lead": self.get(tenant, lead_id)}

    # Compatibility aliases use both word orders in older integrations.
    reopen_lead = owner_reopen_lead
    owner_reopen = owner_reopen_lead

    def channels(self, tenant: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_marketing_channels WHERE tenant_id = ? ORDER BY kind, title",
            (tenant,),
        ).fetchall()
        return [_row(r) for r in rows]

    def upsert_channel(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        title = _clean(data.get("title"), 160)
        kind = _clean(data.get("kind") or "custom", 60)
        if not title:
            return {"ok": False, "error": "نام کانال لازم است"}
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]
        cid = _clean(data.get("channel_id") or f"{tenant}:{kind}:{slug}", 140)
        connection = _clean(data.get("connection") or "planned", 20)
        if connection not in {"planned", "manual", "connected", "paused", "blocked"}:
            connection = "planned"
        row = {
            "channel_id": cid, "tenant_id": tenant, "kind": kind, "title": title,
            "handle": _clean(data.get("handle"), 120),
            "url": _clean(data.get("url"), 300),
            "connection": connection,
            "inbound_enabled": 1 if data.get("inbound_enabled") else 0,
            "outbound_enabled": 1 if data.get("outbound_enabled") else 0,
            "notes": _clean(data.get("notes"), MAX_TEXT),
            "updated_at": now_iso,
        }
        cols = tuple(row.keys())
        placeholders = ",".join("?" for _ in cols)
        updates = ",".join(f"{c}=excluded.{c}" for c in cols if c != "channel_id")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO painting_marketing_channels ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(channel_id) DO UPDATE SET {updates}",
                tuple(row[c] for c in cols),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "channel": cid}

    def campaigns(self, tenant: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_campaigns WHERE tenant_id = ? ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'scheduled' THEN 1 WHEN 'draft' THEN 2 ELSE 9 END, updated_at DESC",
            (tenant,),
        ).fetchall()
        return [_row(r) for r in rows]

    def upsert_campaign(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        title = _clean(data.get("title"), 180)
        if not title:
            return {"ok": False, "error": "نام کمپین لازم است"}
        digest = hashlib.sha1(f"{title}|{now_iso}".encode()).hexdigest()[:16]
        cid = _clean(data.get("campaign_id") or f"{tenant}:campaign:{digest}", 120)
        status = _clean(data.get("status") or "idea", 20)
        if status not in {"idea", "draft", "scheduled", "running", "paused", "done"}:
            status = "idea"
        row = {
            "campaign_id": cid, "tenant_id": tenant, "title": title,
            "objective": _clean(data.get("objective"), 500),
            "channel_ids_json": _json_list(data.get("channel_ids"), 30),
            "status": status,
            "next_step": _clean(data.get("next_step"), 300),
            "due_at": _clean(data.get("due_at"), 80),
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        cols = tuple(row.keys())
        placeholders = ",".join("?" for _ in cols)
        updates = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"campaign_id", "created_at"})
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO painting_campaigns ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(campaign_id) DO UPDATE SET {updates}",
                tuple(row[c] for c in cols),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "campaign": cid}

    def ensure_seed_modules(self, tenant: str, now_iso: str) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            for mid, area, title, status, output, next_step, notes in _SEED_MODULES:
                module_id = f"{tenant}:{mid}"
                self._conn.execute(
                    "INSERT OR IGNORE INTO painting_modules "
                    "(module_id, tenant_id, area, title, status, output, next_step, notes, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (module_id, tenant, area, title, status, output, next_step, notes, now_iso),
                )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def modules(self, tenant: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_modules WHERE tenant_id = ? ORDER BY area, status, title",
            (tenant,),
        ).fetchall()
        return [_row(r) for r in rows]

    def upsert_module(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        title = _clean(data.get("title"), 160)
        area = _clean(data.get("area") or "automation", 60)
        if not title:
            return {"ok": False, "error": "نام ماژول لازم است"}
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]
        mid = _clean(data.get("module_id") or f"{tenant}:module:{slug}", 140)
        status = _clean(data.get("status") or "planned", 20)
        if status not in {"planned", "manual", "connected", "paused", "blocked"}:
            status = "planned"
        row = {
            "module_id": mid, "tenant_id": tenant, "area": area, "title": title,
            "status": status, "output": _clean(data.get("output"), 240),
            "next_step": _clean(data.get("next_step"), 240),
            "notes": _clean(data.get("notes"), MAX_TEXT), "updated_at": now_iso,
        }
        cols = tuple(row.keys())
        ph = ",".join("?" for _ in cols)
        up = ",".join(f"{c}=excluded.{c}" for c in cols if c != "module_id")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO painting_modules ({','.join(cols)}) VALUES ({ph}) ON CONFLICT(module_id) DO UPDATE SET {up}",
                tuple(row[c] for c in cols),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "module": mid}

    def interactions(self, tenant: str, limit: int = 30) -> list[dict]:
        limit = max(1, min(MAX_PAGE, int(limit or 30)))
        rows = self._conn.execute(
            "SELECT * FROM painting_interactions WHERE tenant_id = ? "
            "ORDER BY CASE status WHEN 'new' THEN 0 WHEN 'needs_reply' THEN 1 ELSE 9 END, created_at DESC LIMIT ?",
            (tenant, limit),
        ).fetchall()
        return [_row(r) for r in rows]

    # ── follow-ups, contact policy, lifecycle and duplicates ───────────────
    def set_contact_policy(
            self, tenant: str, lead_id: str,
            policy: Mapping[str, object] | None = None, *,
            legal_basis: object = "", channel_scope: object = None,
            proof_digest: object = "", do_not_contact: bool = False,
            opted_out_at: object = "", revoked_at: object = "",
            reason: object = "", now_iso: str = "",
            recorded_at: str = "", updated_at: str = "") -> dict:
        """Create or replace the contact evidence for one tenant-scoped lead.

        The row copies only the lead's one-way contact hashes. Publicly visible
        contact details never imply permission; a recognized basis, scoped
        channel, and nonblank proof digest must all be supplied explicitly.
        Once a DNC/opt-out/revocation has been recorded this method cannot clear
        it; the suppression is permanent for this lead.
        """
        supplied = dict(policy or {})
        if legal_basis == "":
            legal_basis = supplied.get("legal_basis", "")
        if channel_scope is None:
            channel_scope = supplied.get("channel_scope", supplied.get("channels", []))
        if proof_digest == "":
            proof_digest = supplied.get("proof_digest", "")
        if not do_not_contact:
            do_not_contact = bool(supplied.get("do_not_contact", False))
        if opted_out_at == "":
            opted_out_at = supplied.get("opted_out_at", "")
        if revoked_at == "":
            revoked_at = supplied.get("revoked_at", "")
        if reason == "":
            reason = supplied.get("reason", "")
        stamp = _clean(
            now_iso or updated_at or supplied.get("updated_at")
            or recorded_at or supplied.get("recorded_at") or _now_iso(),
            80,
        )
        recorded = _clean(recorded_at or supplied.get("recorded_at") or stamp, 80)
        basis = _legal_basis(legal_basis)
        channels = _channel_scope(channel_scope)
        proof = _clean(proof_digest, 160)
        opted = _clean(opted_out_at, 80)
        revoked = _clean(revoked_at, 80)
        why = _clean(reason, 500)
        requested_dnc = bool(do_not_contact or opted or revoked)

        if basis not in _POLICY_LEGAL_BASES:
            return {"ok": False, "error": "legal basis نامعتبر است", "rule": "contact:invalid-legal-basis"}
        if not proof:
            return {"ok": False, "error": "proof_digest خالی مجاز نیست", "rule": "contact:proof-missing"}
        if not channels and not requested_dnc:
            return {"ok": False, "error": "حداقل یک کانال معتبر لازم است", "rule": "contact:channel-scope-missing"}
        lead = self.get(tenant, lead_id)
        if not lead:
            return {"ok": False, "error": "لید پیدا نشد", "rule": "contact:lead-missing"}

        existing = self.get_contact_policy(tenant, lead_id)
        if existing and (
                existing.get("do_not_contact")
                or existing.get("opted_out_at")
                or existing.get("revoked_at")):
            requested_dnc = True
            opted = opted or str(existing.get("opted_out_at") or "")
            revoked = revoked or str(existing.get("revoked_at") or "")
            why = why or str(existing.get("reason") or "")
            proof = str(existing.get("proof_digest") or proof)
        if requested_dnc:
            basis = "suppression"
            channels = ()

        row = {
            "tenant_id": tenant,
            "lead_id": lead_id,
            "contact_phone_hash": lead.get("contact_phone_hash") or "",
            "contact_email_hash": lead.get("contact_email_hash") or "",
            "legal_basis": basis,
            "channel_scope_json": json.dumps(channels, ensure_ascii=False),
            "proof_digest": proof,
            "do_not_contact": 1 if requested_dnc else 0,
            "opted_out_at": opted,
            "revoked_at": revoked,
            "reason": why,
            "recorded_at": recorded,
            "updated_at": stamp,
        }
        cols = tuple(row)
        updates = ",".join(
            f"{c}=excluded.{c}" for c in cols
            if c not in {"tenant_id", "lead_id", "recorded_at"}
        )
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO lead_contact_policy ({','.join(cols)}) "
                f"VALUES ({','.join('?' for _ in cols)}) "
                f"ON CONFLICT(tenant_id, lead_id) DO UPDATE SET {updates}",
                tuple(row[c] for c in cols),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "policy": self.get_contact_policy(tenant, lead_id)}

    def get_contact_policy(self, tenant: str, lead_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM lead_contact_policy WHERE tenant_id = ? AND lead_id = ?",
            (tenant, lead_id),
        ).fetchone()
        return _policy_row(row) if row else None

    # Short aliases make the store pleasant to use without changing the stable
    # explicit names requested by the central wiring.
    set_policy = set_contact_policy
    get_policy = get_contact_policy

    def contact_allowed(self, tenant: str, lead_id: str, channel: object) -> dict:
        """Fail-closed contact verdict with a stable ``allowed``/``rule`` shape."""
        normalized = _normalize_channel(channel)
        if normalized not in CONTACT_CHANNELS:
            return {"allowed": False, "rule": "contact:channel-invalid", "channel": normalized}
        lead = self.get(tenant, lead_id)
        if not lead:
            return {"allowed": False, "rule": "contact:lead-missing", "channel": normalized}
        # A scoped channel must have a matching canonical contact on the lead.
        if normalized in {"phone", "sms", "whatsapp"} and not lead.get("contact_phone_hash"):
            return {"allowed": False, "rule": "contact:contact-missing", "channel": normalized}
        if normalized == "email" and not lead.get("contact_email_hash"):
            return {"allowed": False, "rule": "contact:contact-missing", "channel": normalized}
        policy = self.get_contact_policy(tenant, lead_id)
        if not policy:
            return {"allowed": False, "rule": "contact:policy-missing", "channel": normalized}
        if policy.get("revoked_at"):
            return {"allowed": False, "rule": "contact:revoked", "channel": normalized}
        if policy.get("do_not_contact") or policy.get("opted_out_at"):
            return {"allowed": False, "rule": "contact:do-not-contact", "channel": normalized}
        # Fingerprint binding is channel-specific: consent for email remains
        # valid when only the phone changes, while an SMS/phone/WhatsApp policy
        # is tied to the phone hash. Social channels have no raw contact field
        # in this store, so both stored hashes are compared when present.
        if normalized in {"phone", "sms", "whatsapp"}:
            fingerprint_matches = (
                policy.get("contact_phone_hash")
                == (lead.get("contact_phone_hash") or "")
            )
        elif normalized == "email":
            fingerprint_matches = (
                policy.get("contact_email_hash")
                == (lead.get("contact_email_hash") or "")
            )
        else:
            stored_hashes = {
                key: policy.get(key) or ""
                for key in ("contact_phone_hash", "contact_email_hash")
            }
            fingerprint_matches = any(stored_hashes.values()) and all(
                stored_hashes[key] == (lead.get(key) or "")
                for key in stored_hashes
            )
        if not fingerprint_matches:
            return {"allowed": False, "rule": "contact:fingerprint-changed", "channel": normalized}
        if _legal_basis(policy.get("legal_basis")) not in CONTACT_LEGAL_BASES:
            return {"allowed": False, "rule": "contact:legal-basis-missing", "channel": normalized}
        if not _clean(policy.get("proof_digest"), 160):
            return {"allowed": False, "rule": "contact:proof-missing", "channel": normalized}
        if normalized not in set(_channel_scope(policy.get("channel_scope"))):
            return {"allowed": False, "rule": "contact:channel-not-scoped", "channel": normalized}
        return {
            "allowed": True,
            "rule": "contact:allowed",
            "channel": normalized,
            "legal_basis": policy["legal_basis"],
        }

    def record_opt_out(
            self, tenant: str, lead_id: str, *, at_iso: str = "",
            reason: str = "", proof_digest: str = "") -> dict:
        """Permanently suppress a lead; later policy writes cannot undo it."""
        stamp = _clean(at_iso or _now_iso(), 80)
        why = _clean(reason, 500)
        lead = self.get(tenant, lead_id)
        if not lead:
            return {"ok": False, "error": "لید پیدا نشد", "rule": "contact:lead-missing"}
        existing = self.get_contact_policy(tenant, lead_id)
        proof = _clean(proof_digest, 160) or _clean(
            (existing or {}).get("proof_digest"), 160
        )
        if not proof:
            proof = hashlib.sha256(
                f"opt-out|{tenant}|{lead_id}|{stamp}".encode("utf-8")
            ).hexdigest()
        recorded = _clean((existing or {}).get("recorded_at") or stamp, 80)
        opted = _clean((existing or {}).get("opted_out_at") or stamp, 80)
        prior_reason = _clean((existing or {}).get("reason"), 500)
        combined_reason = why or prior_reason or "opted out"
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO lead_contact_policy "
                "(tenant_id, lead_id, contact_phone_hash, contact_email_hash, "
                "legal_basis, channel_scope_json, proof_digest, do_not_contact, "
                "opted_out_at, revoked_at, reason, recorded_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'suppression', '[]', ?, 1, ?, ?, ?, ?, ?) "
                "ON CONFLICT(tenant_id, lead_id) DO UPDATE SET "
                "legal_basis='suppression', channel_scope_json='[]', "
                "proof_digest=CASE WHEN lead_contact_policy.proof_digest != '' "
                "THEN lead_contact_policy.proof_digest ELSE excluded.proof_digest END, "
                "do_not_contact=1, "
                "opted_out_at=CASE WHEN lead_contact_policy.opted_out_at != '' "
                "THEN lead_contact_policy.opted_out_at ELSE excluded.opted_out_at END, "
                "reason=CASE WHEN excluded.reason != '' THEN excluded.reason "
                "ELSE lead_contact_policy.reason END, updated_at=excluded.updated_at",
                (
                    tenant, lead_id,
                    lead.get("contact_phone_hash") or "",
                    lead.get("contact_email_hash") or "",
                    proof, opted,
                    _clean((existing or {}).get("revoked_at"), 80),
                    combined_reason, recorded, stamp,
                ),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "policy": self.get_contact_policy(tenant, lead_id)}

    def revoke_contact_policy(
            self, tenant: str, lead_id: str, *, at_iso: str,
            reason: str = "") -> dict:
        """Permanent policy revocation; like opt-out, it cannot be cleared."""
        stamp = _clean(at_iso, 80)
        if not stamp:
            return {"ok": False, "error": "زمان revoke لازم است", "rule": "contact:revoked-at-missing"}
        existing = self.get_contact_policy(tenant, lead_id)
        if not existing:
            return {"ok": False, "error": "contact policy پیدا نشد", "rule": "contact:policy-missing"}
        why = _clean(reason, 500) or _clean(existing.get("reason"), 500) or "revoked"
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE lead_contact_policy SET legal_basis='suppression', "
                "channel_scope_json='[]', do_not_contact=1, "
                "revoked_at=CASE WHEN revoked_at != '' THEN revoked_at ELSE ? END, "
                "reason=?, updated_at=? WHERE tenant_id=? AND lead_id=?",
                (stamp, why, stamp, tenant, lead_id),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "policy": self.get_contact_policy(tenant, lead_id)}

    revoke_contact = revoke_contact_policy

    def record_follow_up(
            self, tenant: str, lead_id: str, *, at_iso: str = "",
            now_iso: str = "") -> dict:
        """Atomically claim the lead's single permitted follow-up.

        The counter predicate is inside one UPDATE under ``BEGIN IMMEDIATE``;
        competing callers cannot both observe zero and increment it.
        """
        stamp = _clean(at_iso or now_iso or _now_iso(), 80)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE painting_leads SET follow_up_count = follow_up_count + 1, "
                "last_follow_up_at = ?, last_contacted_at = ?, updated_at = ? "
                "WHERE tenant_id = ? AND lead_id = ? AND follow_up_count < 1 "
                "AND status NOT IN ('won','lost','spam','archived')",
                (stamp, stamp, stamp, tenant, lead_id),
            )
            row = self._conn.execute(
                "SELECT status, follow_up_count FROM painting_leads "
                "WHERE tenant_id = ? AND lead_id = ?",
                (tenant, lead_id),
            ).fetchone()
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        if cur.rowcount == 1:
            return {"ok": True, "lead": self.get(tenant, lead_id)}
        if row is None:
            return {"ok": False, "error": "لید پیدا نشد", "rule": "follow-up:lead-missing"}
        if row["status"] in TERMINAL_LEAD_STATUSES:
            return {"ok": False, "error": "لید نهایی است", "rule": "follow-up:terminal"}
        return {"ok": False, "error": "حداکثر یک پیگیری مجاز است", "rule": "follow-up:hard-cap"}

    def set_follow_up(self, tenant: str, lead_id: str, *, due_at: str,
                      action: str = "", now_iso: str = "") -> bool:
        """Schedule a due time; this does not consume the delivery follow-up."""
        if not due_at:
            return False
        stamp = now_iso or _now_iso()
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            if action:
                cur = self._conn.execute(
                    "UPDATE painting_leads SET next_action_at = ?, next_action = ?, "
                    "updated_at = ? WHERE tenant_id = ? AND lead_id = ?",
                    (due_at, _clean(action, 220), stamp, tenant, lead_id),
                )
            else:
                cur = self._conn.execute(
                    "UPDATE painting_leads SET next_action_at = ?, updated_at = ? "
                    "WHERE tenant_id = ? AND lead_id = ?",
                    (due_at, stamp, tenant, lead_id),
                )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return cur.rowcount == 1

    def follow_ups_due(self, tenant: str, *, before_iso: str,
                       limit: int = 50) -> list[dict]:
        """Leads whose follow-up is due (next_action_at <= before)."""
        rows = self._conn.execute(
            "SELECT * FROM painting_leads WHERE tenant_id = ?"
            " AND next_action_at != '' AND next_action_at <= ?"
            " AND status NOT IN ('won','lost','spam','archived')"
            " ORDER BY next_action_at ASC LIMIT ?",
            (tenant, before_iso, limit)).fetchall()
        return [_row(r) for r in rows]

    def mark_delivered(
            self, tenant: str, lead_id: str, *, kind: str = "reply",
            at_iso: str) -> dict:
        """Project a real delivery receipt onto the lead lifecycle.

        ``reply`` advances new/review to contacted. ``quote`` advances
        new/review/contacted to quoted. It never reopens or rewinds a row.
        """
        delivery_kind = _clean(kind, 20).casefold()
        stamp = _clean(at_iso, 80)
        if delivery_kind not in {"reply", "quote"}:
            return {"ok": False, "error": "delivery kind نامعتبر است", "rule": "lead:invalid-delivery-kind"}
        if not stamp:
            return {"ok": False, "error": "زمان delivery لازم است", "rule": "lead:delivery-time-missing"}
        allowed_from = ("new", "review") if delivery_kind == "reply" else ("new", "review", "contacted")
        target = "contacted" if delivery_kind == "reply" else "quoted"
        placeholders = ",".join("?" for _ in allowed_from)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                f"UPDATE painting_leads SET status = ?, last_contacted_at = ?, "
                f"updated_at = ? WHERE tenant_id = ? AND lead_id = ? "
                f"AND status IN ({placeholders})",
                (target, stamp, stamp, tenant, lead_id, *allowed_from),
            )
            row = self._conn.execute(
                "SELECT status FROM painting_leads WHERE tenant_id = ? AND lead_id = ?",
                (tenant, lead_id),
            ).fetchone()
            # A reply receipt arriving after a quote is still truthful contact,
            # but it must not rewind quoted -> contacted. Preserve the stronger
            # lifecycle state and project only its timestamp. A replay of the
            # same status remains idempotent and preserves its original time.
            timestamp_only = False
            if cur.rowcount == 0 and row is not None:
                compatible_ahead = (
                    (delivery_kind == "reply" and row["status"] == "quoted")
                    or row["status"] == target
                )
                if delivery_kind == "reply" and row["status"] == "quoted":
                    touched = self._conn.execute(
                        "UPDATE painting_leads SET last_contacted_at = ?, updated_at = ? "
                        "WHERE tenant_id = ? AND lead_id = ? AND status = 'quoted'",
                        (stamp, stamp, tenant, lead_id),
                    )
                    timestamp_only = touched.rowcount == 1
                elif compatible_ahead:
                    timestamp_only = True
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        if cur.rowcount == 1:
            return {"ok": True, "lead": self.get(tenant, lead_id), "transitioned": True}
        if row is None:
            return {"ok": False, "error": "لید پیدا نشد", "rule": "lead:not-found"}
        if timestamp_only:
            return {"ok": True, "lead": self.get(tenant, lead_id), "transitioned": False}
        return {"ok": False, "error": "delivery با وضعیت فعلی سازگار نیست", "rule": "lead:invalid-transition"}

    def touch_contact(self, tenant: str, lead_id: str, *, at_iso: str) -> None:
        """Legacy timestamp-only receipt; does not invent a status transition."""
        self._conn.execute(
            "UPDATE painting_leads SET last_contacted_at = ?,"
            " updated_at = ? WHERE tenant_id = ? AND lead_id = ?",
            (at_iso, at_iso, tenant, lead_id))
        self._conn.commit()

    def record_booked_revenue(
            self, tenant: str, lead_id: str, *, amount_cents: int,
            booked_at: str, payment_ref_digest: str = "",
            currency: str = "AUD", outcome_reason: str = "",
            authority: str = "owner", actor: str | None = None) -> dict:
        """Record a real booked amount and its dedicated transition to won.

        Revenue evidence owns the ``won`` transition; generic updates cannot
        manufacture it.  Existing callers are compatible through the owner
        default, while an explicit non-owner authority is refused.
        """
        effective = _clean(authority or "partner", 20).casefold()
        if actor is not None and effective == "partner" and _clean(actor, 20).casefold() == "owner":
            effective = "owner"
        if effective != "owner":
            return {"ok": False, "error": "فقط مالک می‌تواند درآمد قطعی ثبت کند", "rule": "lead:owner-required"}
        if amount_cents is None or int(amount_cents) <= 0:
            return {"ok": False, "error": "booked amount must be positive cents"}
        cents = int(amount_cents)
        if cents > 100_000_000_00:  # $1e8 AUD hard ceiling
            return {"ok": False, "error": "booked amount too large"}
        cur = currency.strip().upper()[:8] or "AUD"
        digest = (payment_ref_digest or "").strip()[:64]
        reason = (outcome_reason or "").strip()[:220]
        lead = self.get(tenant, lead_id)
        if not lead:
            return {"ok": False, "error": "lead not found"}
        if lead.get("status") in TERMINAL_LEAD_STATUSES and lead.get("status") != "won":
            return {"ok": False, "error": "terminal lead is locked", "rule": "lead:terminal-locked"}
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            update = self._conn.execute(
                "UPDATE painting_leads SET status = 'won',"
                " booked_amount_cents = ?, booked_currency = ?,"
                " booked_at = ?, payment_ref_digest = ?,"
                " outcome_reason = CASE WHEN ? != '' THEN ? ELSE outcome_reason END,"
                " updated_at = ?"
                " WHERE tenant_id = ? AND lead_id = ? "
                "AND status NOT IN ('lost','spam','archived')",
                (cents, cur, booked_at, digest, reason, reason, booked_at,
                 tenant, lead_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        if update.rowcount != 1:
            return {"ok": False, "error": "won transition failed", "rule": "lead:invalid-transition"}
        return {"ok": True, "lead": self.get(tenant, lead_id)}

    def has_duplicate_contact(
            self, tenant: str, lead_id: str, *,
            details: bool = False) -> bool | list[dict]:
        """Stable duplicate-contact check backed only by phone/email hashes."""
        matches = self.duplicate_candidates(tenant, lead_id)
        return matches if details else bool(matches)

    def duplicate_contact_hashes(
            self, tenant: str, *, phone_hash: str = "",
            email_hash: str = "", exclude_lead_id: str = "") -> list[str]:
        """Check pre-hashed contacts without accepting or exposing raw PII."""
        phone = _clean(phone_hash, 64).casefold()
        email = _clean(email_hash, 64).casefold()
        clauses: list[str] = []
        args: list[object] = [tenant]
        if phone:
            clauses.append("contact_phone_hash = ?")
            args.append(phone)
        if email:
            clauses.append("contact_email_hash = ?")
            args.append(email)
        if not clauses:
            return []
        sql = (
            "SELECT lead_id FROM painting_leads WHERE tenant_id = ? AND ("
            + " OR ".join(clauses) + ")"
        )
        if exclude_lead_id:
            sql += " AND lead_id != ?"
            args.append(exclude_lead_id)
        sql += " ORDER BY created_at, lead_id LIMIT 10"
        return [r["lead_id"] for r in self._conn.execute(sql, args).fetchall()]

    def duplicate_candidates(self, tenant: str, lead_id: str) -> list[dict]:
        """Other leads sharing the same contact hash (phone/email).

        Warning only — never merge. The hash is computed from the canonical
        phone/email at write time; no raw contact leaves the store.
        """
        lead = self.get(tenant, lead_id)
        if not lead:
            return []
        phone_h = lead.get("contact_phone_hash") or ""
        email_h = lead.get("contact_email_hash") or ""
        if not phone_h and not email_h:
            return []
        clauses, args = [], []
        if phone_h:
            clauses.append("contact_phone_hash = ? AND contact_phone_hash != ''")
            args.append(phone_h)
        if email_h:
            clauses.append("contact_email_hash = ? AND contact_email_hash != ''")
            args.append(email_h)
        args.append(tenant)
        args.append(lead_id)
        rows = self._conn.execute(
            "SELECT * FROM painting_leads WHERE ("
            + " OR ".join(clauses) + ") AND tenant_id = ? AND lead_id != ?"
            " ORDER BY created_at, lead_id LIMIT 10", args).fetchall()
        return [_row(r) for r in rows]

    def create_interaction(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        channel = _clean(data.get("channel") or "manual", 80)
        subject = _clean(data.get("subject") or data.get("title") or "تعامل", 180)
        digest = hashlib.sha1(f"{channel}|{subject}|{now_iso}".encode()).hexdigest()[:16]
        iid = _clean(data.get("interaction_id") or f"{tenant}:interaction:{digest}", 140)
        status = _clean(data.get("status") or "new", 20)
        if status not in {"new", "needs_reply", "converted", "done", "archived"}:
            status = "new"
        row = {
            "interaction_id": iid, "tenant_id": tenant, "channel": channel,
            "kind": _clean(data.get("kind") or "message", 60),
            "person": _clean(data.get("person"), 160), "subject": subject,
            "body": _clean(data.get("body") or data.get("message"), MAX_TEXT),
            "status": status, "lead_id": _clean(data.get("lead_id"), 160),
            "created_at": now_iso, "updated_at": now_iso,
        }
        cols = tuple(row.keys())
        ph = ",".join("?" for _ in cols)
        up = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"interaction_id", "created_at"})
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO painting_interactions ({','.join(cols)}) VALUES ({ph}) ON CONFLICT(interaction_id) DO UPDATE SET {up}",
                tuple(row[c] for c in cols),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "interaction": iid}

    def update_interaction(self, tenant: str, interaction_id: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        fields = []
        args: list[object] = []
        for key in ("status", "lead_id", "person", "subject", "body", "kind", "channel"):
            if key not in data:
                continue
            val = _clean(data.get(key), MAX_TEXT if key == "body" else 220)
            if key == "status" and val not in {"new", "needs_reply", "converted", "done", "archived"}:
                val = "new"
            fields.append(f"{key} = ?")
            args.append(val)
        if not fields:
            return {"ok": False, "error": "هیچ فیلدی برای تغییر نبود"}
        fields.append("updated_at = ?")
        args.append(now_iso)
        args += [tenant, interaction_id]
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE painting_interactions SET " + ", ".join(fields) + " WHERE tenant_id = ? AND interaction_id = ?",
                tuple(args),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": cur.rowcount == 1, "interaction": interaction_id}

    def ensure_source_registry(self, tenant: str, sources: list[dict], now_iso: str) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            for src in sources:
                sid = _clean(src.get("source_id") or f"{tenant}:source:{_slug(src.get('name','source'))}", 140)
                vals = {
                    "I": src.get("intent_score"),
                    "X": 0.9 if src.get("category") in {"owned", "b2b", "tender"} else 0.45,
                    "E": 0.8 if src.get("integration_path") else 0.5,
                    "O": 0.75 if src.get("status") == "priority" else 0.5,
                    "A": 0.7 if src.get("integration_path") not in {"manual_research", "manual_monitor"} else 0.35,
                    "C": 0.35 if src.get("category") in {"owned", "b2b"} else 0.55,
                    "R": src.get("risk_score"),
                }
                q = source_quality(vals)
                self._conn.execute(
                    "INSERT INTO painting_sources "
                    "(source_id, tenant_id, name, category, official_url, integration_path, status, "
                    " automation_level, approval_required, intent_score, risk_score, score, recommendation, notes, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(source_id) DO UPDATE SET name=excluded.name, category=excluded.category, "
                    "official_url=excluded.official_url, integration_path=excluded.integration_path, "
                    "status=excluded.status, automation_level=excluded.automation_level, "
                    "approval_required=excluded.approval_required, intent_score=excluded.intent_score, "
                    "risk_score=excluded.risk_score, score=excluded.score, recommendation=excluded.recommendation, "
                    "notes=excluded.notes, updated_at=excluded.updated_at",
                    (sid, tenant, _clean(src.get("name"), 180), _clean(src.get("category"), 80),
                     _clean(src.get("official_url"), 300), _clean(src.get("integration_path"), 120),
                     _clean(src.get("status") or "planned", 20), _clean(src.get("automation_level") or "read_only_first", 80),
                     1 if src.get("approval_required", True) else 0, float(src.get("intent_score") or 0.5),
                     float(src.get("risk_score") or 0.5), q.score, q.recommendation,
                     _clean(src.get("notes"), MAX_TEXT), now_iso))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def sources(self, tenant: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_sources WHERE tenant_id = ? ORDER BY score DESC, category, name",
            (tenant,),
        ).fetchall()
        return [_row(r) for r in rows]

    def create_account(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        name = _clean(data.get("business_name") or data.get("name"), 180)
        if not name:
            return {"ok": False, "error": "نام شرکت لازم است"}
        segment = _clean(data.get("segment") or "strata", 40)
        aid = _clean(data.get("account_id") or f"{tenant}:acct:{_slug(name)}", 160)
        vals = data.get("score_inputs") if isinstance(data.get("score_inputs"), dict) else {}
        if not vals:
            if segment in {"builder", "fitout", "commercial_fitout"}:
                vals = {"V": data.get("value_fit"), "D": data.get("deadline_fit"), "F": data.get("fit"), "C": data.get("capacity_fit"), "E": data.get("evidence_quality"), "risk": data.get("risk"), "cost": data.get("cost")}
            else:
                vals = {"P": data.get("portfolio_fit"), "G": data.get("geo_fit"), "M": data.get("maintenance_fit"), "E": data.get("evidence_quality"), "R": data.get("repeat_fit"), "risk": data.get("risk"), "cost": data.get("cost")}
        score = b2b_account_score(segment, vals)
        row = {
            "account_id": aid, "tenant_id": tenant, "segment": segment, "business_name": name,
            "suburb": _clean(data.get("suburb"), 120), "service_area": _clean(data.get("service_area"), 160),
            "website": _clean(data.get("website"), 300), "contact_channel": _clean(data.get("contact_channel"), 220),
            "evidence_url": _clean(data.get("evidence_url"), 300), "stage": _clean(data.get("stage") or "discovered", 40),
            "score": score.score, "recommendation": score.recommendation,
            "score_json": json.dumps({"components": dict(score.components), "explanation": list(score.explanation), "incomplete": score.incomplete}, ensure_ascii=False, sort_keys=True),
            "outreach_permission": _clean(data.get("outreach_permission") or "unknown", 40),
            "next_action": _clean(data.get("next_action") or "research + capability pack", 240),
            "notes": _clean(data.get("notes"), MAX_TEXT), "created_at": now_iso, "updated_at": now_iso,
        }
        if row["stage"] not in {"discovered","researched","qualified","meeting","vendor_onboarding","opportunity","won","lost","archived"}:
            row["stage"] = "discovered"
        if row["outreach_permission"] not in {"unknown","approved_channel","relationship","suppressed"}:
            row["outreach_permission"] = "unknown"
        cols = tuple(row.keys()); ph = ",".join("?" for _ in cols)
        up = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"account_id", "created_at"})
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(f"INSERT INTO painting_b2b_accounts ({','.join(cols)}) VALUES ({ph}) ON CONFLICT(account_id) DO UPDATE SET {up}", tuple(row[c] for c in cols))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "account": aid, "score": score.score, "recommendation": score.recommendation, "explanation": list(score.explanation)}

    def accounts(self, tenant: str, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_b2b_accounts WHERE tenant_id = ? ORDER BY score DESC, updated_at DESC LIMIT ?",
            (tenant, max(1, min(MAX_PAGE, int(limit or 50)))),
        ).fetchall()
        out = []
        for r in rows:
            d = _row(r)
            try: d["score_detail"] = json.loads(d.pop("score_json") or "{}")
            except Exception: d["score_detail"] = {}
            out.append(d)
        return out

    def create_tender(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        title = _clean(data.get("title"), 220)
        if not title:
            return {"ok": False, "error": "عنوان مناقصه لازم است"}
        tid = _clean(data.get("tender_id") or f"{tenant}:tender:{_slug(title)}", 160)
        vals = data.get("score_inputs") if isinstance(data.get("score_inputs"), dict) else {"P": data.get("painting_relevance"), "G": data.get("geography_fit"), "E": data.get("eligibility_fit"), "D": data.get("deadline_feasibility"), "M": data.get("margin_confidence"), "Q": data.get("evidence_quality"), "R": data.get("policy_risk"), "C": data.get("bid_cost")}
        score = tender_score(vals)
        row = {
            "tender_id": tid, "tenant_id": tenant, "source": _clean(data.get("source") or "manual", 80),
            "source_url": _clean(data.get("source_url"), 300), "title": title,
            "buyer_name": _clean(data.get("buyer_name"), 160), "location": _clean(data.get("location"), 160),
            "closing_at": _clean(data.get("closing_at"), 80), "access_mode": _clean(data.get("access_mode") or "manual", 40),
            "evidence_status": _clean(data.get("evidence_status") or "unverified", 40),
            "status": _clean(data.get("status") or "scored", 40), "score": score.score,
            "recommendation": score.recommendation,
            "score_json": json.dumps({"components": dict(score.components), "explanation": list(score.explanation), "incomplete": score.incomplete}, ensure_ascii=False, sort_keys=True),
            "missing_facts_json": _json_list(data.get("missing_facts"), 20), "created_at": now_iso, "updated_at": now_iso,
        }
        if row["access_mode"] not in {"alert_email","official_api","owner_upload","manual"}: row["access_mode"] = "manual"
        if row["evidence_status"] not in {"unverified","verified","expired"}: row["evidence_status"] = "unverified"
        if row["status"] in {"owner_submitted", "submitted"}:
            return {"ok": False, "error": "ثبت مستقیم submitted مجاز نیست؛ submit فقط با OwnerRelease و رسید جداگانه ثبت می‌شود"}
        if row["status"] not in {"received","verified_source","extracted","scored","owner_review","watching","skipped","bid_approved","documents_ready","submission_drafted","lost","won","cancelled"}: row["status"] = "scored"
        cols = tuple(row.keys()); ph = ",".join("?" for _ in cols)
        up = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"tender_id", "created_at"})
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(f"INSERT INTO painting_tenders ({','.join(cols)}) VALUES ({ph}) ON CONFLICT(tender_id) DO UPDATE SET {up}", tuple(row[c] for c in cols))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "tender": tid, "score": score.score, "recommendation": score.recommendation, "explanation": list(score.explanation)}

    def tenders(self, tenant: str, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_tenders WHERE tenant_id = ? ORDER BY CASE recommendation WHEN 'BID' THEN 0 WHEN 'CONSIDER' THEN 1 ELSE 9 END, score DESC, closing_at LIMIT ?",
            (tenant, max(1, min(MAX_PAGE, int(limit or 50)))),
        ).fetchall()
        out = []
        for r in rows:
            d = _row(r)
            try: d["score_detail"] = json.loads(d.pop("score_json") or "{}")
            except Exception: d["score_detail"] = {}
            try: d["missing_facts"] = json.loads(d.pop("missing_facts_json") or "[]")
            except Exception: d["missing_facts"] = []
            out.append(d)
        return out

    def create_vendor_application(self, tenant: str, data: Mapping[str, object], *, now_iso: str) -> dict:
        company = _clean(data.get("company_name") or data.get("business_name") or data.get("name"), 180)
        if not company:
            return {"ok": False, "error": "نام شرکت لازم است"}
        app_id = _clean(data.get("application_id") or f"{tenant}:vendor:{_slug(company)}", 160)
        reqs = data.get("requirements") or ["ABN", "NSW_painting_licence", "public_liability_insurance", "capability_statement"]
        missing = data.get("missing") or []
        status = _clean(data.get("status") or ("pack_incomplete" if missing else "ready_for_owner"), 40)
        if status in {"submitted", "approved"}:
            return {"ok": False, "error": "ثبت مستقیم submitted/approved مجاز نیست؛ portal action فقط با OwnerRelease ثبت می‌شود"}
        if status not in {"discovered","requirements_extracted","pack_incomplete","ready_for_owner","under_review","declined","renewal_due","blocked"}:
            status = "discovered"
        row = {
            "application_id": app_id, "tenant_id": tenant, "account_id": _clean(data.get("account_id"), 160),
            "company_name": company, "portal_url": _clean(data.get("portal_url"), 300),
            "source_type": _clean(data.get("source_type") or "supplier_portal", 40), "status": status,
            "requirements_json": _json_list(reqs, 30), "missing_json": _json_list(missing, 30),
            "risk_note": _clean(data.get("risk_note"), MAX_TEXT),
            "next_action": _clean(data.get("next_action") or "owner review checklist", 240),
            "created_at": now_iso, "updated_at": now_iso,
        }
        if row["source_type"] not in {"supplier_portal","EOI","referral","tender","manual"}: row["source_type"] = "supplier_portal"
        cols = tuple(row.keys()); ph = ",".join("?" for _ in cols)
        up = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"application_id", "created_at"})
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(f"INSERT INTO painting_vendor_applications ({','.join(cols)}) VALUES ({ph}) ON CONFLICT(application_id) DO UPDATE SET {up}", tuple(row[c] for c in cols))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "application": app_id, "status": status}

    def vendor_applications(self, tenant: str, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM painting_vendor_applications WHERE tenant_id = ? ORDER BY CASE status WHEN 'ready_for_owner' THEN 0 WHEN 'pack_incomplete' THEN 1 ELSE 9 END, updated_at DESC LIMIT ?",
            (tenant, max(1, min(MAX_PAGE, int(limit or 50)))),
        ).fetchall()
        out = []
        for r in rows:
            d = _row(r)
            for k in ("requirements_json", "missing_json"):
                try: d[k[:-5]] = json.loads(d.pop(k) or "[]")
                except Exception: d[k[:-5]] = []
            out.append(d)
        return out

    def dashboard(self, tenant: str) -> dict:
        counts = {r["status"]: int(r["n"]) for r in self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM painting_leads WHERE tenant_id = ? GROUP BY status",
            (tenant,),
        ).fetchall()}
        hot = self._conn.execute(
            "SELECT COUNT(*) AS n FROM painting_leads WHERE tenant_id = ? AND temperature = 'hot'",
            (tenant,),
        ).fetchone()["n"]
        connected = self._conn.execute(
            "SELECT COUNT(*) AS n FROM painting_marketing_channels WHERE tenant_id = ? AND connection = 'connected'",
            (tenant,),
        ).fetchone()["n"]
        return {
            "lead_counts": counts,
            "hot_leads": int(hot),
            "open_leads": sum(int(counts.get(s, 0)) for s in ("new", "review", "contacted", "quoted")),
            "connected_channels": int(connected),
            "recent_leads": self.list_leads(tenant, limit=10),
            "channels": self.channels(tenant),
            "campaigns": self.campaigns(tenant),
            "modules": self.modules(tenant),
            "interactions": self.interactions(tenant),
            "sources": self.sources(tenant),
            "accounts": self.accounts(tenant, limit=12),
            "tenders": self.tenders(tenant, limit=12),
            "vendor_applications": self.vendor_applications(tenant, limit=12),
        }
