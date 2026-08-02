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

import ast
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


# ── جدولِ مسیر: ایستا (امروز) + مشتق‌شده از خودِ handler (پشتِ فلگ) ────────────
#
# چرا این بخش هست
# ───────────────
# ۲۰۲۶-۰۸-۰۱ اندازه‌گیری شد: `langar_bot.LangarBot.handle` **۴۱ فرمانِ واقعی**
# دارد و جدولِ زیر ۳۰ ردیف. با prefix-matching، ۹ فرمانِ زنده به هیچ ردیفی
# نمی‌خوردند و `dispatch` برایشان `None` برمی‌گرداند — یعنی مالک تایپ می‌کرد و
# **سکوت** می‌گرفت، در حالی که handlerش همان لحظه زنده بود:
#
#     /agreement /agreement_for_creator /agreement_signed
#     /code /code_queue /code_status /inbox /reset /studio
#
# راهِ ارزان این بود که نُه رشته append شود. آن کار **دفعهٔ بعد دوباره** خراب
# می‌شود: هر handlerِ تازه در langar یک سکوتِ تازه می‌سازد و هیچ‌چیز نمی‌پرسد.
# پس به‌جای بستنِ شکاف، قاعده بسته می‌شود: مجموعهٔ فرمان‌ها از خودِ AST ِ
# `handle` مشتق می‌شود و `route_coverage()` **هر دو جهت** را گزارش می‌دهد.
#
# مرزها
# ─────
# · فقط پارس (`ast.parse`) — هیچ import و هیچ اجرایی از langar_bot.
# · فلگ خاموش → `effective_routes() is LANGAR_CMDS` → رفتارِ امروز بایت‌به‌بایت.
# · شکستِ خواندن/پارس → مجموعهٔ خالی → سقوط به LANGAR_CMDS (fail-soft).
ROUTE_DERIVE_FLAG = "OCTOPUS_LANGAR_ROUTE_DERIVE"

# فهرستِ ایستا — **دست‌نخورده**. این همان چیزی است که تا امروز مسیر می‌داد.
LANGAR_CMDS = (
    "/pf_", "/dm_", "/fan_", "/vault_", "/saba", "/drafts", "/brief", "/think",
    "/spine", "/upgrade", "/gates", "/verdicts", "/rules", "/kpi", "/kpi_record",
    "/report", "/guards", "/report_warning", "/clear_warning", "/clear_full_stop",
    "/report_karma", "/set_karma", "/octopus", "/octopus_status", "/octopus_tick",
    "/kill", "/revive", "/status", "/start", "/help",
)

# handlerهایی که عمداً به langar نمی‌روند — هر ردیف باید **دلیل** داشته باشد.
# «بعداً» دلیل نیست. اعلامِ کهنه هم قرمز می‌شود (تستِ دوطرفه).
#
# ⚠️ `/code*`: `center.py` (باتِ بیرونی) از ۰۷-۲۵ `/code` را به `_live_cmd`
# می‌برد و در `_CENTER_SLASH` ثبتش کرده. اگر این‌جا هم به langar برود، یک نام
# روی دو باتِ مالک دو معنی می‌گیرد — دقیقاً همان بیماریِ `/lead`. کدام معنی
# برنده باشد **رأیِ مالک** است، پس تا آن رأی این‌جا مسدود می‌ماند نه بی‌صدا.
LANGAR_ROUTE_EXCLUDED: dict[str, str] = {
    "/code": "center.py:_live_cmd همین نام را روی باتِ بیرونی دارد — تصادمِ نام، رأیِ مالک لازم",
    "/code_queue": "زیرمجموعهٔ همان تصادم (/code)",
    "/code_status": "زیرمجموعهٔ همان تصادم (/code)",
}


def _route_derive_enabled() -> bool:
    return str(os.environ.get(ROUTE_DERIVE_FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def langar_bot_source(path=None) -> str:
    """متنِ langar_bot.py. نبود/خطا → رشتهٔ خالی (fail-soft، هرگز raise)."""
    p = Path(path) if path else None
    if p is None:
        d = _langar_dir()
        p = (d / "langar_bot.py") if d is not None else None
    if p is None or not p.is_file():
        return ""
    try:
        return p.read_text("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def derive_langar_commands(source: str = "", func: str = "handle",
                           var: str = "cmd") -> frozenset:
    """فرمان‌های واقعیِ `handle` را از AST دربیاور.

    سه شکلِ شرط در آن متد استفاده می‌شود و هر سه شمرده می‌شوند:
      · `cmd == "/x"`            → تطابقِ دقیق
      · `cmd in ("/x", "/y")`    → تطابقِ دقیق
      · `cmd.startswith("/x_")`  → پیشوند

    خروجی = مجموعهٔ رشته‌ها (پیشوندها با همان دُمِ `_` خودشان). پارس‌نشدن →
    مجموعهٔ خالی، چون «نمی‌دانم» باید از «هیچ فرمانی نیست» جدا بماند و
    صداکننده روی خالی به فهرستِ ایستا سقوط می‌کند."""
    src = source or langar_bot_source()
    if not src.strip():
        return frozenset()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return frozenset()
    target = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func:
            target = n
            break
    if target is None:
        return frozenset()

    def _slash(node) -> str:
        return (node.value if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.startswith("/") else "")

    def _is_var(x) -> bool:
        return isinstance(x, ast.Name) and x.id == var

    found: set = set()
    for n in ast.walk(target):
        if isinstance(n, ast.Compare) and _is_var(n.left):
            for op, cmp_ in zip(n.ops, n.comparators):
                if isinstance(op, ast.Eq):
                    if _slash(cmp_):
                        found.add(cmp_.value)
                elif isinstance(op, ast.In) and isinstance(
                        cmp_, (ast.Tuple, ast.List, ast.Set)):
                    found.update(_slash(e) for e in cmp_.elts if _slash(e))
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "startswith" and _is_var(n.func.value)):
            for a in n.args:
                if _slash(a):
                    found.add(a.value)
                elif isinstance(a, ast.Tuple):
                    found.update(_slash(e) for e in a.elts if _slash(e))
    return frozenset(found)


def _routed(cmd: str, routes) -> bool:
    """همان قاعدهٔ تطابقِ `dispatch` — یک‌جا، تا دو نسخه از هم دور نیفتند."""
    return any(cmd == c or cmd.startswith(c) for c in routes)


def route_coverage(routes=None, source: str = "") -> dict:
    """گزارشِ **دوطرفهٔ** درزِ مسیر↔handler.

    {handlers: n, routes: n, handler_without_route: [...],
     route_without_handler: [...], excluded_not_a_handler: [...]}

    · `handler_without_route` — فرمانِ زنده که تایپش سکوت می‌دهد (بیماریِ امروز).
    · `route_without_handler` — ردیفی که هیچ handlerی ندارد؛ یعنی `dispatch`
      فرمان را از مسیرهای دیگرِ رباتِ واحد **می‌دزدد** و بعد langar «دستور
      ناشناخته» می‌گوید. سکوت نیست، ولی بدترش است: جوابِ غلطِ مطمئن.
    · `excluded_not_a_handler` — اعلامِ کهنه در LANGAR_ROUTE_EXCLUDED.
    """
    rts = tuple(routes if routes is not None else LANGAR_CMDS)
    hands = derive_langar_commands(source)
    hand_no_route = sorted(
        c for c in hands
        if c not in LANGAR_ROUTE_EXCLUDED and not _routed(c, rts))
    route_no_hand = sorted(
        r for r in rts
        if not any(h == r or h.startswith(r) or r.startswith(h) for h in hands))
    stale = sorted(c for c in LANGAR_ROUTE_EXCLUDED if c not in hands)
    return {"handlers": len(hands), "routes": len(rts),
            "handler_without_route": hand_no_route,
            "route_without_handler": route_no_hand,
            "excluded_not_a_handler": stale}


_effective_routes_cache = None


def effective_routes(source: str = "") -> tuple:
    """جدولی که `dispatch` واقعاً استفاده می‌کند.

    فلگ خاموش → **همان شیءِ** LANGAR_CMDS (parity بایت‌به‌بایت).
    فلگ روشن → LANGAR_CMDS ∪ (مشتق − excluded). مشتقِ خالی → LANGAR_CMDS."""
    global _effective_routes_cache
    if not _route_derive_enabled():
        return LANGAR_CMDS
    if source:
        d = derive_langar_commands(source)
        # مشتقِ خالی = «نتوانستم بخوانم»، نه «هیچ فرمانی نیست» → سقوط به ایستا.
        return (tuple(sorted(set(LANGAR_CMDS) | (d - set(LANGAR_ROUTE_EXCLUDED))))
                if d else LANGAR_CMDS)
    if _effective_routes_cache is None:
        d = derive_langar_commands()
        _effective_routes_cache = (
            tuple(sorted(set(LANGAR_CMDS) | (d - set(LANGAR_ROUTE_EXCLUDED))))
            if d else LANGAR_CMDS)
    return _effective_routes_cache


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
    # فقط دستورهای langar را delegate کن (نه هر / چیزی). فهرست از langar_bot.handle:
    # فلگ خاموش = همان تاپلِ ایستای بالا (parity)، روشن = مشتق‌شده از AST.
    if not _routed(cmd0, effective_routes()):
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
