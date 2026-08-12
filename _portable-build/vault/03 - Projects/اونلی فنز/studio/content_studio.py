#!/usr/bin/env python3
"""content_studio.py — Content Studio v2: باتِ صبا (Project-F).

TELEGRAM-CONTENT-STUDIO-v2.md §۲: استودیوی محتوا برای صبا.
همه workflow-محور، compliant، propose-only. قواعدِ قفل‌شده:
  - فقط متادیتا/پلن/آنالیزِ تجمیعی — هرگز رسانه/هویت/PII فن
  - دوکلیده (صبا ثبت → آری تأیید → انتشارِ درون‌پلتفرم)
  - پرداخت فقط درون‌پلتفرم، صفر مذاکره
  - self-cert اجباری (faceless ✅ · فقط‌پا ✅ · بدون explicit ✅ · ۱۸+/رضایت ✅)
  - محدودهٔ صبا مقدمِ مطلق (یک‌ضربه halt)
  - geo-block ایران
  - بات/توکن/allowlistِ جدا

FIXES (2026-07-09):
  - FIX 1: analytics از config.json (نه hardcoded)
  - FIX 2: PPV prices از config.json (قابل‌تنظیم)
  - FIX 3: trend feed از config.json
  - FIX 6: drafts persistence (JSON — restart-safe)
  - FIX 8: calendar از config.json (نه hardcoded)

هیچ import از *_gate/chrono/money production. $0 آفلاین، stdlib-only.
ایزوله در پوشهٔ Project-F.
"""
from __future__ import annotations

import html
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

# قواعدِ قفل‌شده (self-cert checklist)
COMPLIANCE_CHECKS = [
    "faceless",        # بدون چهره
    "feet_only",       # فقط‌پا
    "no_explicit",     # بدون explicit
    "over_18",         # ۱۸+/رضایت
]

# state/config قابل‌انحراف با PF_STUDIO_DIR (تست/harness)؛ بدونِ env = کنارِ ماژول (production)
# ۲۰۲۶-۰۸-۰۳ fix: مسیرها در زمانِ import محاسبه نمی‌شوند (تست‌ها به ترتیبِ اجرا
# حساس بودند). الگوی lazy به سبکِ pf_os/saba_link.py::_studio_dir().
def _studio_dir() -> Path:
    """مسیرِ studio. قابل‌تزریق برای تست (PF_STUDIO_DIR)؛ بدونِ env = کنارِ ماژول."""
    env = os.environ.get("PF_STUDIO_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent


def _config_path() -> Path:
    return _studio_dir() / "config.json"


def _data_path() -> Path:
    return _studio_dir() / "drafts.json"


def _load_config() -> dict:
    """FIX 1/2/3/8: بارگذاریِ config از فایل (نه hardcoded)."""
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@dataclass
class DraftSubmission:
    """یک درفتِ ثبت‌شده. فقط متادیتا — صفر رسانه.

    2026-07-20 (backlog #2 — join استودیو↔اکتساب): فیلدهای channel/hook/caption/
    vault_id اضافه شد تا درفتِ تأییدشدهٔ C بتواند بدونِ گم‌شدنِ schema به
    VaultBank (و از آن‌جا به AcquisitionPipeline) دست‌به‌دست شود. همه default
    دارند → درفت‌های قدیمیِ روی دیسک بدون migration لود می‌شوند."""
    draft_id: str
    title: str
    self_cert: dict
    status: str = "pending"    # pending → approved → published
    ppv_tier: str | None = None
    price_hint: float = 0.0
    channel: str = "reddit"    # مقصدِ پیشنهادی (reddit/x/of/fansly)
    hook: str = ""             # هوکِ کوتاه (اگر خالی: title)
    caption: str = ""          # کپشنِ پیشنهادی (اگر خالی: hook/title)
    vault_id: str | None = None   # بعد از handoff به VaultBank پر می‌شود

    def to_dict(self) -> dict:
        return asdict(self)


# ترتیبِ قانونیِ statusها — هر گذارِ دیگری غیرمجاز است (تستِ illegal-transition دارد)
_DRAFT_TRANSITIONS = {
    "pending": ("approved", "rejected"),
    "approved": ("published",),
    "published": (),
    "rejected": (),
}


class ContentStudio:
    """باتِ صبا. propose-only، ایزوله. خروجی = HTML غنی.
    دوکلیده: درفت → آری تأیید → انتشار.
    FIX 6: drafts persistence (restart-safe)."""

    def __init__(self, config_path: str | Path | None = None):
        # ۲۰۲۶-۰۸-۰۳: مسیرها در زمانِ ساختِ instance حل می‌شوند، نه در import.
        # اگر config_path صریح داده شد، data_path هم از همان شاخه می‌آید.
        cpath = Path(config_path) if config_path else _config_path()
        self._config_path = cpath
        self._data_path = cpath.parent / "drafts.json" if config_path else _data_path()
        self._config = self._load_config_safe()
        self._drafts: list[DraftSubmission] = self._load_drafts()
        self._halted = False

    def _load_config_safe(self) -> dict:
        try:
            return json.loads(self._config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    # ─── FIX 6: persistence ─────────────────────────────────────────────────────
    def _load_drafts(self) -> list[DraftSubmission]:
        """بارگذاریِ درفت‌ها از دیسک (restart-safe)."""
        try:
            data = json.loads(self._data_path.read_text(encoding="utf-8"))
            return [DraftSubmission(**d) for d in data]
        except (json.JSONDecodeError, OSError, TypeError):
            return []

    def _save_drafts(self) -> None:
        """ذخیرهٔ درفت‌ها روی دیسک (atomic)."""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._data_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(
                [d.to_dict() for d in self._drafts], ensure_ascii=False, indent=2),
                encoding="utf-8")
            tmp.replace(self._data_path)
        except OSError:
            pass   # fail-soft

    @property
    def draft_count(self) -> int:
        return len(self._drafts)

    def halt(self) -> str:
        self._halted = True
        return "✋ <b>متوقف شد</b>\nمحدودهٔ صبا مقدمِ مطلق. بات متوقف است."

    @property
    def is_halted(self) -> bool:
        return self._halted

    # ─── منوی اصلی ──────────────────────────────────────────────────────────────
    def main_menu(self) -> str:
        if self._halted:
            return self.halt()
        return ("🎬 <b>استودیوی محتوا</b> — Project-F\n"
                "<i>دکمه‌ها را برای کار انتخاب کن.</i>")

    # ─── 📤 ثبتِ درفت ────────────────────────────────────────────────────────────
    def submit_draft(self, title: str, self_cert: dict | None = None,
                     ppv_tier: str | None = None,
                     price_hint: float = 0.0,
                     channel: str = "reddit", hook: str = "",
                     caption: str = "") -> dict:
        if self._halted:
            return {"ok": False, "error": "halted"}
        cert = self_cert or {}
        missing = [c for c in COMPLIANCE_CHECKS if not cert.get(c)]
        if missing:
            return {"ok": False, "error": f"self-cert ناقص: {missing}"}
        draft_id = f"DRAFT-{len(self._drafts) + 1:04d}"
        draft = DraftSubmission(draft_id=draft_id, title=title,
                                self_cert=cert, ppv_tier=ppv_tier,
                                price_hint=price_hint,
                                channel=(channel or "reddit"),
                                hook=hook or "", caption=caption or "")
        self._drafts.append(draft)
        self._save_drafts()   # FIX 6: persist
        return {"ok": True, "draft_id": draft_id, "status": "pending"}

    # ─── گذارِ status + handoff به Vault (2026-07-20، backlog #2/#14) ───────────
    def _find_draft(self, draft_id: str) -> DraftSubmission | None:
        for d in self._drafts:
            if d.draft_id == draft_id:
                return d
        return None

    def set_status(self, draft_id: str, new_status: str,
                   actor: str = "operator") -> dict:
        """گذارِ statusِ درفت — فقط گذارهای قانونی (fail-closed).

        pending → approved|rejected · approved → published · بقیه = خطا."""
        d = self._find_draft(draft_id)
        if d is None:
            return {"ok": False, "error": "not found"}
        allowed = _DRAFT_TRANSITIONS.get(d.status, ())
        if new_status not in allowed:
            return {"ok": False,
                    "error": f"illegal transition {d.status} → {new_status} (fail-closed)"}
        d.status = new_status
        self._save_drafts()
        return {"ok": True, "draft_id": draft_id, "status": new_status,
                "actor": str(actor)[:24]}

    def handoff_to_vault(self, draft_id: str, vault) -> dict:
        """درفتِ approved + fully-certified → یک assetِ VaultBank (join استودیو↔اکتساب).

        شرط‌ها (fail-closed): status=approved · هر ۴ selfcert ‏True · vault موجود.
        بعد از موفقیت vault_id روی درفت ثبت می‌شود (idempotent — دوباره push نمی‌شود)."""
        d = self._find_draft(draft_id)
        if d is None:
            return {"ok": False, "error": "not found"}
        if d.status != "approved":
            return {"ok": False, "error": f"must be approved (current: {d.status})"}
        if any(not d.self_cert.get(c) for c in COMPLIANCE_CHECKS):
            return {"ok": False, "error": "self-cert incomplete — handoff refused (fail-closed)"}
        if d.vault_id:
            return {"ok": True, "draft_id": draft_id, "vault_id": d.vault_id,
                    "duplicate": True}
        if vault is None:
            return {"ok": False, "error": "no vault connected"}
        try:
            r = vault.add(tag=d.title[:40], hook=(d.hook or d.title)[:120],
                          caption=(d.caption or d.hook or d.title)[:280],
                          channel=d.channel, cert=dict(d.self_cert))
        except Exception:  # noqa: BLE001 — fail-soft، درفت دست‌نخورده می‌ماند
            return {"ok": False, "error": "vault add failed"}
        if not r.get("ok"):
            return {"ok": False, "error": "vault refused"}
        d.vault_id = r["id"]
        self._save_drafts()
        return {"ok": True, "draft_id": draft_id, "vault_id": d.vault_id}

    def drafts_html(self) -> str:
        if not self._drafts:
            return "📋 <b>بریف‌ها</b>\n──────────\n<i>هنوز درفتی ثبت نشده.</i>"
        lines = ["📋 <b>بریف‌ها</b>", "──────────"]
        for d in self._drafts:
            icon = {"pending": "⏳", "approved": "✅", "published": "📤"}.get(d.status, "❓")
            lines.append(f"{icon} {d.draft_id} · {d.title} · {d.status}")
        return "\n".join(lines)

    # ─── 💡 پلنِ PPV (FIX 2: از config) ──────────────────────────────────────────
    def ppv_plan_html(self) -> str:
        ppv = self._config.get("ppv", {})
        wall_pct = ppv.get("wall_pct", 0.55)
        tiers = ppv.get("tiers", {})
        lines = ["💡 <b>پلنِ PPV</b>", "──────────"]
        lines.append(f"📊 wall: ~{wall_pct*100:.0f}% · PPV: ~{(1-wall_pct)*100:.0f}%")
        for tier, cfg in tiers.items():
            lines.append(f"  {tier}: ${cfg.get('price', '?')} ({cfg.get('desc', '')})")
        lines.append("<i>پیشنهادِ قیمت — آری تأیید می‌کند.</i>")
        return "\n".join(lines)

    # ─── 📈 آنالیز (FIX 1: از config) ────────────────────────────────────────────
    def analytics_html(self) -> str:
        a = self._config.get("analytics", {})
        churn = a.get("churn_rate", 0.27)
        arpu = a.get("arpu", 60.0)
        unlock = a.get("ppv_unlock_rate", 0.28)
        ret = a.get("retention_30d", 0.65)
        seg = a.get("segments", {})
        return (f"📈 <b>آنالیز</b>\n──────────\n"
                f"churn: {churn*100:.0f}%\n"
                f"ARPU: ${arpu:.0f}\n"
                f"PPV unlock: {unlock*100:.0f}%\n"
                f"retention 30d: {ret*100:.0f}%\n"
                f"سگمنت: VIP {seg.get('vip',0)*100:.0f}% · "
                f"معمولی {seg.get('regular',0)*100:.0f}% · "
                f"lurker {seg.get('lurker',0)*100:.0f}%\n"
                f"<i>تجمیعی — صفر PII.</i>")

    # ─── 🔒 قواعد + ✋ محدوده ───────────────────────────────────────────────────
    def rules_html(self) -> str:
        return ("🔒 <b>قواعدِ قفل‌شده</b>\n──────────\n"
                "✅ faceless (بدون چهره)\n"
                "✅ فقط‌پا\n"
                "✅ بدون explicit\n"
                "✅ ۱۸+/رضایت\n"
                "✅ پرداختِ درون‌پلتفرم\n"
                "✅ geo-block ایران\n"
                "✅ دوکلیده (صبا→آری)\n"
                "<i>ردِ هر قاعده = drop.</i>")

    def scope_html(self) -> str:
        return ("✋ <b>محدودهٔ من</b>\n──────────\n"
                "محدودهٔ صبا مقدمِ مطلق.\n"
                "یک‌ضربه halt در هر زمان.\n"
                "<i>برای توقف: /halt</i>")

    # ─── 🔎 ترند (FIX 3: از config) ─────────────────────────────────────────────
    def trend_feed_html(self) -> str:
        trends = self._config.get("trends", [])
        if not trends:
            return "🔎 <b>ترند/ایده</b>\n──────────\n<i>هنوز ترندی ثبت نشده.</i>"
        lines = ["🔎 <b>ترند/ایده</b>", "──────────"]
        for t in trends:
            lines.append(f"📌 {t.get('tag', '?')}: {t.get('note', '')} "
                         f"({t.get('optimal_time', '?')})")
        lines.append("<i>human-gated — هیچ‌چیز خودکار.</i>")
        return "\n".join(lines)

    # ─── 🗓 تقویم (FIX 8: از config) ─────────────────────────────────────────────
    def calendar_html(self) -> str:
        cal = self._config.get("calendar", {})
        season = cal.get("season", "?")
        slots = cal.get("slots", [])
        lines = [f"🗓 <b>تقویم</b> · فصل: {season}", "──────────"]
        if not slots:
            lines.append("<i>هنوز اسلاتی ثبت نشده.</i>")
        for s in slots:
            lines.append(f"  هفته {s.get('week', '?')}: {s.get('theme', '')} — {s.get('task', '')}")
        lines.append("<i>هیچ‌چیز خودکار publish نمی‌شود.</i>")
        return "\n".join(lines)
