#!/usr/bin/env python3
"""langar_bridge — پلِ additive از رباتِ واحد اختاپوس به langarِ Project-F.

نقش (رأی مالک 2026-07-17 «یک ربات واحد، langar ادغام‌شده»):
  دستورهای langar (/pf_*, /saba, /drafts, /dm_*, /fan_*, /vault_*, /guards, /kpi*,
  /octopus*, /brief, /think, /spine, /upgrade, /gates, /verdicts, /rules, /kill,
  /revive, ...) از همین رباتِ واحد پاسخ می‌گیرند — بدونِ توکنِ جدا.

لا‌مزاحم (قانونِ بزرگِ پروژه):
  * langar_bot.py **لمس نمی‌شود**. این ماژول فقط LangarBot را instantiate می‌کند و
    متدِ موجودِ .handle(chat_id, text) را صدا می‌زند — دوباره‌نویسی نمی‌کند.
  * OpsecGuardِ langar (scrub روی هر خروجی، fail-closed) همچنان فعال است چون از
    متدِ خودِ langar استفاده می‌کنیم. قوانینِ قفل‌شدهٔ ۵/۷ (privacy دوطرفه) پابرجا.
  * شکستِ هر import → None (fail-soft)؛ رباتِ واحد برای بقیهٔ دستورها کار می‌کند.

ثبت در ledger اختاپوس (پلِ برگشتی):
  برای کارهایی که فعلیتِ واقعی دارند (/pf_ok, /pf_no, /pf_ready, /kpi_record,
  /clear_full_stop, /set_karma, /kill, /revive) یک NOTE در ledger ژنوم (LANGAR)
  زده می‌شود — content-free (صرفاً kind=verdict/result/ts، بدونِ هویت/محتوا).
  این الگوی unified_bus.publish است. قرنطینه: هرگز محتوای Project-F در ledger نمی‌رود.

امنیت:
  توکن/owner از همان env رباتِ واحد (TELEGRAM_BOT_TOKEN / TELEGRAM_OWNER_CHAT_ID)
  تغذیه می‌شوند — نه توکنِ جدا. allowlist در approval_channel.py قبل از رسیدن به
  اینجا چک شده (فقط chat_idهای مجاز اینجا می‌رسند).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# bootstrap مسیرِ budget برای opslib (idiomِ codebase: legs→budget از طریقِ parent).
_HERE = Path(__file__).resolve().parent                   # _ops/legs
_OPS = _HERE.parent                                       # _ops
_BUDGET = _OPS / "budget"
for _p in (str(_HERE), str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# langar در vaultِ Project-F است؛ مسیرش را از env یا fallbackِ کانونیکال بیاب.
def _langar_dir() -> Path | None:
    """مسیرِ پوشهٔ langar. اول env (OCTOPUS_LANGAR_DIR)، بعد fallbackِ کانونیکال.
    نبود/خطا → None (fail-soft). هرگز hardcode هویت."""
    env_p = os.environ.get("OCTOPUS_LANGAR_DIR", "").strip()
    if env_p:
        p = Path(env_p)
        if p.is_dir():
            return p
    # fallback: F:\backup\03 - Projects\اونلی فنز\langar — ولی فقط اگر parent وجود دارد.
    try:
        # ORG_ROOT از opslib اگر موجود باشد (محلِ کانونیکال vault).
        import opslib  # noqa: WPS433
        root = getattr(opslib, "ORG_ROOT", None) or getattr(opslib, "VAULT_ROOT", None)
        if root is not None:
            cand = Path(root) / "03 - Projects" / "اونلی فنز" / "langar"
            if cand.is_dir():
                return cand
    except Exception:  # noqa: BLE001
        pass
    return None


# ── نگاشتِ کارهایی که فعلیتِ واقعی دارند → ثبتِ content-free در ledger ──
# فقط این پیشوندها/دستورها NOTE می‌خورند. بقیه (read-only مثل /status, /drafts
# مشاهده‌ای) در ledger نمی‌روند — چون تغییری ایجاد نکردند.
_EFFECTING_PREFIXES = ("/pf_ok", "/pf_no", "/pf_ready", "/pf_pause",
                       "/pf_resume", "/kpi_record", "/clear_full_stop",
                       "/set_karma", "/clear_warning", "/report_warning",
                       "/kill", "/revive")


def _is_effecting(cmd: str) -> bool:
    """آیا این دستور تغییری واقعی ایجاد می‌کند (نه read-only)؟"""
    c = (cmd or "").strip().lower().split()[0] if (cmd or "").strip() else ""
    return any(c == p or c.startswith(p) for p in _EFFECTING_PREFIXES)


def _ledger_note_verdict(cmd: str, reply: str | None, chat_id) -> None:
    """ثبتِ content-free در ledger ژنوم برای کارهایِ واقعی.
    فقط kind + نتیجه (ok/fail از نوعِ پاسخ) + chat_id-scope-flag. هیچ هویت/محتوا."""
    try:
        import opslib  # noqa: WPS433
        # قرنطینه: هرگز محتوایِ پاسخ را در ledger ننویس. فقط متادیتایِ بی‌خطر.
        result = "ok" if (reply is not None and not str(reply).startswith("❌")) else "fail"
        scope = "group" if (chat_id is not None and int(chat_id) < 0) else "private"
        opslib.ledger_note(  # الگوی unified_bus.publish / opslib.ledger_note موجود
            "LANGAR_VERDICT",
            payload={"kind": "pf-verdict", "cmd_prefix": str(cmd).split()[0][:20] if cmd else "",
                     "result": result, "scope": scope, "source": "telegram-unified-bot"},
            actor="telegram-unified-bot",
        )
    except Exception:  # noqa: BLE001 — لا‌مزاحم: ثبتِ ledger نباید مسیر را بکشد
        pass


# ── کشِ نمونهٔ LangarBot (یک‌بار ساخته شود) ──
_langar_bot_instance = None
_langar_tried = False


def _get_langar_bot(owner: int | None):
    """LangarBot را بساز (یک‌بار). توکن/owner از env رباتِ واحد. شکست → None."""
    global _langar_bot_instance, _langar_tried
    if _langar_tried:
        return _langar_bot_instance
    _langar_tried = True
    ldir = _langar_dir()
    if ldir is None:
        return None
    try:
        if str(ldir) not in sys.path:
            sys.path.insert(0, str(ldir))
        if str(ldir.parent / "brain") not in sys.path:   # langar brain را import می‌کند
            sys.path.insert(0, str(ldir.parent / "brain"))
        import langar_bot  # noqa: WPS433 — لمس‌نشدنی: فقط import
        # توکن از env رباتِ واحد (نه توکنِ جدا). owner همان owner اختاپوس.
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None
        # LangarBot.__init__(token, ari_chat_id) — قراردادِ langar_bot.py:311-314
        _langar_bot_instance = langar_bot.LangarBot(
            token=token, ari_chat_id=owner)
        return _langar_bot_instance
    except Exception:  # noqa: BLE001 — لا‌مزاحم
        return None


# ── API عمومی که approval_channel.py صدا می‌زند ──
def dispatch(text: str, chat_id=None, owner=None) -> str | None:
    """دستور را به langar بسپار. خروجیِ langar (از OpsecGuard گذشته) را برگردان.

    اگر دستور متعلق به langar نباشد → None (تا handle_command به مسیرهای دیگر برود).
    اگر langار import/ساخت نشد → None (fail-soft).
    اگر effecting بود → NOTE در ledger (content-free)."""
    t = (text or "").strip()
    if not t.startswith("/"):
        return None
    cmd0 = t.lower().split()[0] if t.lower().split() else ""
    # فقط دستورهای langar را delegate کن (نه هر / چیزی). فهرست از langar_bot.handle.
    LANGAR_CMDS = (
        "/pf_", "/dm_", "/fan_", "/vault_", "/saba", "/drafts", "/brief", "/think",
        "/spine", "/upgrade", "/gates", "/verdicts", "/rules", "/kpi", "/kpi_record",
        "/report", "/guards", "/report_warning", "/clear_warning", "/clear_full_stop",
        "/report_karma", "/set_karma", "/octopus", "/octopus_status", "/octopus_tick",
        "/kill", "/revive", "/status", "/start", "/help",
    )
    if not any(cmd0 == c or cmd0.startswith(c) for c in LANGAR_CMDS):
        return None   # متعلق به langar نیست → handle_command مسیرِ خودش را دارد
    bot = _get_langar_bot(owner=owner)
    if bot is None:
        return None   # langar در دسترس نیست → fail-soft silent
    #authorized توسطِ langar_bot.py:440 چک می‌شود: chat_id == self.ari. چون رباتِ
    # واحد از گروه هم فرمان می‌گیرد و allowlistِ اختاپوس از قبل چک شده، ما owner را
    # به‌عنوانِ chat_id به langar پاس می‌دهیم (یعنی «فرستندهٔ مجاز = مالک»)؛ اینگونه
    # langar فکر می‌کند مالک درخواست داده و پاسخ می‌دهد، و approval_channel پاسخ را
    # به همان chat (گروه/چت) که فرمان از آن آمد برمی‌گرداند (poll_once::send_text(chat_id=...)).
    # این دقیقاً رفتارِ «همهٔ دستورها در گروه قابل‌مشاهده» است که مالک خواست (رأی 2026-07-17).
    cid_for_langar = int(owner) if owner is not None else None
    try:
        reply = bot.handle(cid_for_langar, t)
    except Exception:  # noqa: BLE001 — fail-soft
        return None
    if _is_effecting(t):
        _ledger_note_verdict(t, reply, chat_id)
    return reply
