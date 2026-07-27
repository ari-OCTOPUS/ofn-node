#!/usr/bin/env python3
"""approval_channel — منبعِ مستقلِ تأییدِ انسانی برای گیت‌های پول (A2/A3).

اصل (I7 + قاعدهٔ ضدِ گیم): تأیید هرگز از خودگزارشیِ ایجنت نمی‌آید — فقط از این کانال،
که در تولید به هستهٔ انسانی/core.db (نوشتهٔ کلیکِ انسان) وصل می‌شود.
adapterِ عملیاتی = Telegram (انتخابِ اپراتور 2026-07-07)؛ الان وصل نیست →
NotWiredStub که همیشه no-approval می‌دهد → گیت‌ها بسته (fail-closed مطلوبِ فازِ paper).

secret-guard: وصلِ Telegram یک قدمِ جدا و human-gated است؛ tokenِ botِ آن راز است
(انسان در زمانِ اجرا از env/secret-store می‌دهد، هرگز hardcode، هرگز در repo/.env کامیت‌شده).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# ── W-3 bootstrap: این ماژول در _ops/budget کنارِ opslib.py می‌نشیند. مسیرِ خودمان را
# جلو می‌گذاریم تا importِ opslib همیشه resolve شود (حتی وقتی approval_channel مستقیم و
# خارج از sys.pathِ budget بارگذاری شده). بدونِ این، opslib.alert در مسیرهای خطای
# poll_once/_answer_callback_query یک NameErrorِ نهفته بود که run_forever را می‌کشت.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
# ۲۰۲۶-۰۷-۲۶: خودِ `_ops` هم لازم شد (tg_send_log آن‌جاست). بدونِ این خط، قلابِ
# سنجشِ ارسال داخل try/except بی‌صدا رد می‌شد و «اندازه‌گیری روشن است» یک ادعای
# غیرقابلِ‌ابطال می‌ماند — همان بیماری‌ای که این ماژول‌ها برای شکارش ساخته شدند.
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
import opslib  # noqa: E402 — بعد از bootstrapِ مسیر؛ برای alertهای fail-soft لازم است

# فقط این وضعیت‌ها = «کلیکِ انسانیِ واقعی» در صف کنترل‌برین/core.db (هم‌راستا با I7 outbox status='sent')
VALID_STATUSES = frozenset({"approved", "sent"})


@dataclass(frozen=True)
class Approval:
    """یک تأییدِ per-action از منبعِ مستقل. amount_aud و action_id باید با همان اقدام match بخورند."""
    action_id: str
    amount_aud: float
    status: str
    source: str = "unknown"

    @property
    def valid(self) -> bool:
        return self.status in VALID_STATUSES


class ApprovalChannel:
    """interfaceِ pluggable. پیاده‌سازیِ واقعی (Telegram→core.db) بعداً و human-gated وصل می‌شود."""
    name = "abstract"

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        raise NotImplementedError


class NotWiredStub(ApprovalChannel):
    """حالتِ فعلیِ فازِ paper: هیچ کانالی وصل نیست → هیچ تأییدی → گیت بسته."""
    name = "not-wired"

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        return None


class MockApprovalChannel(ApprovalChannel):
    """فقط تست/shadow: مجموعه‌ای از approvalهای از پیش‌داده (شبیه‌سازیِ کلیکِ انسان).
    تطبیق فقط وقتی action_id و amount هر دو بخورند و وضعیت معتبر باشد (نه ادعای ایجنت)."""
    name = "mock"

    def __init__(self, approvals: list[Approval] | None = None):
        self._approvals = list(approvals or [])

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        for a in self._approvals:
            if a.action_id == action_id and abs(a.amount_aud - amount_aud) < 1e-9 and a.valid:
                return a
        return None


# ─── T-1 · Telegram adapter — سطحِ human-append (P3-TELEGRAM §5) ────────────────
# انتخابِ اپراتور 2026-07-07: تلگرام = کانالِ عملیاتیِ کلیکِ انسان. T-1 فقط «لوله»
# را می‌سازد: bindِ chat_idِ مالک + long-pollingِ $0-idle + allowlist + quarantine.
# در T-1 هیچ approvalی از پیامِ ورودی ساخته نمی‌شود — شیرِ human-append (T-2) هنوز
# بسته است، پس approval_for همچنان fail-closed (None) است. _record_approval یک seam
# است که T-2 (دکمهٔ تأیید) آن را وصل می‌کند. وصل کردنِ adapter به سیستمِ زنده
# human-gated است (مستندسازیِ بالای فایل)؛ لذا money_gate دست‌نخورده می‌ماند.
#
# secret-guard (I9): tokenِ bot فقط از env خوانده می‌شود — هرگز hardcode/log/commit.
# نبودِ token = no-opِ امن، نه crash. URL حاویِ token هرگز لاگ/echo نمی‌شود؛ خطاها
# masked هستند. HTTP = stdlib-only (urllib) هم‌راستا با panel/server.py؛ هیچ وابستگیِ
# خارجی (requests/python-telegram-bot) اضافه نمی‌شود.
import html                                  # noqa: E402
import json                                  # noqa: E402
import os                                    # noqa: E402
import re                                    # noqa: E402 — جلسه ۴۶: strip تگ برای toast
import threading                             # noqa: E402
import time                                  # noqa: E402 — جلسه ۴۶: throttle هشدارِ 409
import urllib.error                          # noqa: E402
import urllib.parse                          # noqa: E402
import urllib.request                        # noqa: E402

TELEGRAM_API_BASE = "https://api.telegram.org"
TELEGRAM_LONGPOLL_TIMEOUT_S = 30   # idle = $0: getUpdates تا این ثانیه رویِ سرور بلوکه می‌ماند


# ── فاز ۲: accessorِ تنبلِ langar_bridge (لا‌مزاحم — اگر نبود، None = skip) ──
# در handle_command به‌صورتِ «langar_bridge_dispatch is not None» خوانده می‌شود.
# اولین استفاده real import می‌کند و کش می‌کند. شکستِ import (نبودِ langar یا
# وابستگی‌هاش) → None → شاخهٔ delegation بی‌صدا skip می‌شود (fail-soft، مثلِ _ar/_jb).
_langar_bridge_dispatch_cache: "callable | None" = None
_langar_bridge_tried = False


# ── مسیریابیِ جریانِ محیطی به تاپیک (رأی مالک ۲۰۲۶-۰۷-۲۶) ────────────────────
# مسئله‌ای که این حل می‌کند: ۶ تابعِ beat هر تیک به **DMِ مالک** می‌نویسند (قلب،
# دکتر، مغز، نیازها) چون این ماژول اصلاً `message_thread_id` نداشت. نتیجه: DM پر و
# ۹ تاپیکِ گروه خالی — یعنی جریانِ محیطی در کانالِ کمیاب‌ترین منبع (توجهِ مالک) و
# کانالِ مرتب بی‌استفاده. اینجا فقط *مقصد* عوض می‌شود؛ محتوا و کادنس دست‌نخورده.
#
# منبعِ حقیقتِ idها = همان center-config.json که خودِ مرکز می‌نویسد. کپی نمی‌کنیم،
# چون دو نسخه از یک حقیقت دقیقاً همان بیماریِ b763adb است.
# سقفِ سختِ تلگرام برای callback_data. کارتِ RFC این را می‌سازد:
#     rfc:<verb>:<rfc_id>:<token>   →  len("rfc:merge:") + id + 1 + len(token)
# طولانی‌ترین verb «merge» است و توکن ۲۴ کاراکترِ hex.
CALLBACK_DATA_MAX = 64
_RFC_CB_OVERHEAD = len("rfc:merge:") + 1 + 24


def callback_fits(rfc_id: str, overhead: int = _RFC_CB_OVERHEAD) -> bool:
    """آیا کارتِ این شناسه در سقفِ تلگرام جا می‌شود؟ (bytes، نه characters —
    شناسهٔ غیرASCII در UTF-8 بزرگ‌تر از طولِ رشته‌اش است.)"""
    try:
        return len(str(rfc_id).encode("utf-8")) + int(overhead) <= CALLBACK_DATA_MAX
    except (TypeError, ValueError, UnicodeError):
        return False


ROUTE_FLAG = "OCTOPUS_TG_ROUTE_TOPICS"
# ── ساعتِ سکوتِ مالک (رأی ۲۰۲۶-۰۷-۲۷: «۰ تا ۷») ─────────────────────────────
# اندازه‌گیریِ همان روز: ۷ پیامِ خودکار بینِ ۲۲ شب تا ۸ صبح رفته بود. این بازه
# فقط جریانِ **محیطی** را ساکت می‌کند؛ پاسخِ مستقیم و هشدارِ حیاتی هرگز.
# ساعتِ محلیِ همین ماشین (مالک و ارگانیسم یک‌جا هستند) — env قابلِ تنظیم.
_NEVER_QUIET = frozenset({"cortisol", "alert", "heart"})


def _quiet_hours() -> tuple:
    def _h(name, default):
        try:
            v = int(str(os.environ.get(name, "")).strip())
            return v if 0 <= v <= 23 else default
        except (TypeError, ValueError):
            return default
    return _h("OCTOPUS_QUIET_FROM", 0), _h("OCTOPUS_QUIET_TO", 7)


def _quiet_now(now=None) -> bool:
    """آیا الان در بازهٔ سکوت است؟ بازهٔ گذرنده از نیمه‌شب هم پشتیبانی می‌شود."""
    import datetime as _dt
    h = (now or _dt.datetime.now()).hour
    a, b = _quiet_hours()
    if a == b:
        return False
    return (a <= h < b) if a < b else (h >= a or h < b)


_STREAM_TOPIC = {
    "heart": "system", "doctor": "system", "needs": "system", "summary": "system",
    "brain": "knowledge", "discovery": "knowledge", "map": "cartographer",
    # ۲۰۲۶-۰۷-۲۶ — مقصدِ هشدارهای فوری (instant_alert_bridge):
    # ترس در 🫀قلب (وضعیتِ حیاتی)، فرضیه در 🧠مغز (یادگیری)، لید در بازوی خودش.
    "cortisol": "system", "alert": "system", "c6": "knowledge", "lead": "lead",
}
def _center_cfg_path() -> Path:
    """مسیرِ configِ مرکز — از opslib.STATE_DIR، نه ثابتِ hardcode. دلیلش عملی است:
    مسیرِ ثابت در تست به درختِ **زنده** می‌خورد و شواهد را آلوده می‌کند."""
    return Path(opslib.STATE_DIR) / "telegram" / "center-config.json"


def _stream_route(stream: str) -> tuple:
    """(chat_id, topic_id) برای یک جریان — یا (None, None).

    (None, None) یعنی «همان DMِ همیشگی». هر شکستی — فلگ خاموش، فایلِ نبود، JSONِ
    خراب، تاپیکِ ساخته‌نشده — به DM برمی‌گردد و **هرگز به سکوت**. گم‌شدنِ پیام
    بدتر از پیامِ در جای اشتباه است."""
    if str(os.environ.get(ROUTE_FLAG, "") or "").strip().lower() not in (
            "1", "true", "yes", "on"):
        return (None, None)
    key = _STREAM_TOPIC.get(str(stream or ""))
    if not key:
        return (None, None)
    try:
        cfg = json.loads(_center_cfg_path().read_text("utf-8"))
        chat = cfg.get("chat_id")
        tid = (cfg.get("topics") or {}).get(key)
        if isinstance(chat, int) and isinstance(tid, int):
            return (chat, tid)
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return (None, None)


def langar_bridge_dispatch(text: str, chat_id=None, owner=None):
    """accessor در سطحِ ماژول: langar_bridge.dispatch را lazy بارگذاری و صدا بزن.
    شکستِ import/Dispatch → None (fail-soft). رباتِ واحد برای بقیه کار می‌کند."""
    global _langar_bridge_dispatch_cache, _langar_bridge_tried
    if not _langar_bridge_tried:
        _langar_bridge_tried = True
        try:
            import sys as _s
            legs = str(Path(__file__).resolve().parents[1] / "legs")   # _ops/legs
            if legs not in _s.path:
                _s.path.insert(0, legs)
            import langar_bridge  # noqa: WPS433
            _langar_bridge_dispatch_cache = langar_bridge.dispatch
        except Exception:  # noqa: BLE001 — لا‌مزاحم
            _langar_bridge_dispatch_cache = None
    fn = _langar_bridge_dispatch_cache
    if fn is None:
        return None
    return fn(text, chat_id=chat_id, owner=owner)


def _env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _allowed_chat_ids(owner: int | None) -> frozenset[int]:
    """allowlist از chat-idها که ربات از آن‌ها فرمان می‌پذیرد (گروه‌پذیریِ کاکپیت، رأیِ
    مالک 2026-07-17). منبعِ حقیقت = TELEGRAM_ALLOWED_CHAT_IDS (CSV در env: -100…،
    اعدادِ منفیِ تلگرام برای گروه/سوپرگروپ/کانال). owner همیشه عضو است.

    fail-closed: اگر متغیر نباشد/خالی باشد → فقط {owner} (رفتارِ قبلیِ byte-identical،
    فقط چتِ ۱:۱). هر مقدارِ غیرعددی بی‌صدا skip می‌شود (هرگز guess).
    مهم: این فقط «این پیام از کجا پذیرفته شد» را گسترش می‌دهد — مسیرِ ضدِ جعلِ
    callback (_new_token) و مسیرِ settle (_do_approve→gate.settle) chat-id-agnostic
    اند و دست‌نخورده می‌مانند (تأییدِ زیرسیستم)."""
    ids: set[int] = set()
    if owner is not None:
        ids.add(int(owner))
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "")
    for tok in raw.replace(";", ",").split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            ids.add(int(tok))
        except ValueError:
            continue   # غیرعددی → نادیده (هرگز guess)
    return frozenset(ids)


def _mask_token(tok: str) -> str:
    """برای repr/خطا: فقط ۴ نویسهٔ نخست + … (هرگز کلِ token)."""
    if not tok:
        return "∅"
    return (tok[:4] + "…") if len(tok) > 4 else "…"


def _url_json_get(url: str, timeout_s: float) -> dict:
    """getterِ پیش‌فرضِ HTTP (stdlib-only). timeout کمی بیشتر از longpoll تا پاسخِ دیررس
    هم خوانده شود. هرگز URL را لاگ نمی‌کند. خروجیِ Telegram همیشه JSON است."""
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-telegram/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s + 5) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


def _url_json_post(url: str, body: dict, timeout_s: float = 10.0) -> dict:
    """posterِ پیش‌فرضِ HTTP (stdlib-only، JSON body). body هرگز شاملِ token نیست (token در
    URL است). هرگز URL را لاگ نمی‌کند. برای send/answerCallback/editMessage."""
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"User-Agent": "octopus-telegram/0.1",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


class TelegramApprovalChannel(ApprovalChannel):
    """کانالِ تأییدِ تلگرامی (T-1: لوله). Long-polling، $0-idle، owner-allowlist،
    quarantine (پیام = DATA نه دستور). وقتی token نباشد no-opِ امن است.

    http_get قابل‌تزریق است (هم‌سان با ChronoBus clock) تا تست بدونِ شبکه/کلید برود.
    kill_check قابل‌تزریق است تا حلقهٔ پس‌زمینه فوراً تسلیمِ STOP/halted شود (kill supreme)."""

    name = "telegram"

    def __init__(self, token: str | None = None, owner_chat_id: int | None = None,
                 http_get=None, http_post=None, kill_check=None,
                 longpoll_timeout: int | None = None,
                 gate=None, ledger=None, state_dir=None, leg=None,
                 readmodel=None):
        self._token = (token if token is not None else _env_str("TELEGRAM_BOT_TOKEN"))
        self._owner = int(owner_chat_id) if owner_chat_id is not None else (
            _env_int("TELEGRAM_OWNER_CHAT_ID", 0) or None)
        # allowlistِ chat-idها (گروه‌پذیری، رأی مالک 2026-07-17). owner همیشه عضو است؛
        # TELEGRAM_ALLOWED_CHAT_IDS اضافه می‌کند. نبود = فقط owner (byte-identical).
        self._allowed = _allowed_chat_ids(self._owner)
        self._http_get = http_get or _url_json_get
        self._http_post = http_post or _url_json_post
        self._kill = kill_check                     # None = فقط پرچمِ داخلیِ .stop()
        self._lp = int(longpoll_timeout if longpoll_timeout is not None
                       else _env_int("TELEGRAM_LONGPOLL_TIMEOUT", TELEGRAM_LONGPOLL_TIMEOUT_S))
        self._gate = gate                            # EffectorGate (TINV-7) — T-2 وصل می‌کند
        self._ledger = ledger                        # ledger ژنوم (human-append)
        # C7.2: callback state may never be RAM-only.  None resolves to the canonical
        # (harness-remapped in tests) state directory rather than disabling durability.
        self._state_dir = str(state_dir or opslib.STATE_DIR)
        self._leg = leg                              # W-3: پای Lead (اختیاری) — /lead → leg.intake
        self._readmodel = readmodel                  # Cockpit v2: read-model تزریقی (تست) یا lazy
        self._pending_act: dict[str, dict] = {}      # Cockpit v2: رجیستریِ act تک‌مصرف (INV-13)
        self._dash_mod = None                        # Cockpit v2: کشِ ماژولِ dashboard (importlib، بدونِ تصادمِ نام)
        self._lk = threading.Lock()
        # offset از فایل بارگذاری می‌شود (restart-safe)؛ نبودِ فایل = ۰.
        # state_dir=None → پیش‌فرضِ _ops/state که در نمونهٔ واقعی هست.
        self._offset: int = _load_offset(self._state_dir) if self._state_dir else 0
        self._approvals: dict[str, Approval] = {}    # seam: T-2 اینجا می‌نویسد
        self._pending: dict[str, dict] = {}          # T-2: کارت‌های تأییدِ منتظر (registry ضدِ جعل)
        self._pending_rfc: dict[str, dict] = {}      # W-3: کارت‌های RFCِ منتظرِ verdict (token + ضدِ replay)
        self._quarantine: list[dict] = []            # پیام‌های ورودی = DATA (نه دستور)
        self._awaiting_rfc_edit: str | None = None   # 3a: انتظارِ متنِ ویرایشِ RFC (RAM؛ restart = لغوِ امن)
        self._last_chstat = 0.0                      # Task 2: کادنسِ writerِ زندهٔ channel-status
        self._stop = False

    @property
    def wired(self) -> bool:
        """لوله وصل است؟ token + owner هر دو لازم. نبودِ هر = no-opِ امن."""
        return bool(self._token) and self._owner is not None

    def __repr__(self) -> str:
        n_q = n_ap = -1
        with self._lk:
            n_q, n_ap = len(self._quarantine), len(self._approvals)
        return (f"<TelegramApprovalChannel wired={self.wired} "
                f"token={_mask_token(self._token)} owner={self._owner} "
                f"lp={self._lp}s offset={self._offset} quarantined={n_q} approvals={n_ap}>")

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        """قراردادِ ApprovalChannel. در T-1 همیشه None (شیر بسته) مگر آنکه T-2 از طریقِ
        _record_approval چیزی ثبت کرده باشد. تطبیق = action_id + amount (هم‌سان با Mock)."""
        with self._lk:
            a = self._approvals.get(action_id)
        if a is not None and abs(a.amount_aud - amount_aud) < 1e-9 and a.valid:
            return a
        return None

    def _record_approval(self, approval: Approval) -> None:
        """seam برای T-2: کلیکِ دکمهٔ تأیید اینجا یک Approval ثبت می‌کند. در T-1 هیچ
        مسیرِ inboundی این متد را صدا نمی‌زند — فقط تست/T-2. keyed by action_id."""
        if not isinstance(approval, Approval):
            raise TypeError("approval must be Approval")
        with self._lk:
            self._approvals[approval.action_id] = approval

    def stop(self) -> None:
        """توقفِ تمیزِ حلقهٔ long-poll (پرچمِ داخلی). kill_switchِ out-of-band (T-7)
        فایلِ STOP-ORGANISM را می‌نویسد؛ حلقه از kill_check هم می‌رسد."""
        self._stop = True

    def _killed(self) -> bool:
        if self._stop:
            return True
        if self._kill is not None:
            try:
                return bool(self._kill())
            except Exception:  # noqa: BLE001 — kill_checkِ خراب = امن بایست
                return True
        return False

    def _build_url(self, method: str, params: dict) -> str:
        """ساختِ URLِ Telegram API. هرگز کلِ URL را لاگ نکن (token داخلش است)."""
        q = urllib.parse.urlencode(params)
        return f"{TELEGRAM_API_BASE}/bot{self._token}/{method}?{q}"

    # ─── Task 2 (2026-07-24) · writerِ زندهٔ channel-status ─────────────────────
    def _write_channel_status(self) -> bool:
        """حقیقتِ زندهٔ «تلگرام وصل است؟» را در state/channel-status.json می‌نویسد.
        تاریخچه: فایل از 2026-07-08 orphan بود (صفر writerِ زنده) و خواننده‌ها
        (dashboard/page_channels · cockpit_readmodel.read_channels · export_status)
        عکسِ کهنهٔ «stub(no-creds)» می‌دیدند. حالا خودِ کانالِ زنده — تنها کسی که
        واقعاً می‌داند — در بوتِ run_forever و سپس هر ~۱۵ دقیقه از poll_once آن را
        refresh می‌کند. read-modify-write اتمیک؛ کانال‌های دیگرِ snapshot دست‌نخورده.
        fail-soft (هرگز poll/boot را نمی‌کشد)؛ هیچ token/secret در خروجی."""
        try:
            from pathlib import Path as _P
            if not self._state_dir:
                return False
            p = _P(self._state_dir) / "channel-status.json"
            try:
                cur = json.loads(p.read_text("utf-8")) if p.exists() else {}
            except (OSError, ValueError):
                cur = {}
            if not isinstance(cur, dict):
                cur = {}
            channels = cur.get("channels") if isinstance(cur.get("channels"), dict) else {}
            entry = {
                "channel": "telegram",
                "live": bool(self.wired),
                "mode": "long-poll(T-8)" if self.wired else "stub(no-creds)",
                "writer": "approval_channel(run_forever/poll_once)",
                "allowlist": len(self._allowed) > 1,
                "owner_set": self._owner is not None,
            }
            if not self.wired:
                entry["required_env"] = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID"]
            channels["telegram"] = entry
            cur["channels"] = channels
            cur["ts"] = opslib.now_iso()
            cur["writer_note"] = ("entryِ telegram توسطِ کانالِ زنده refresh می‌شود "
                                  "(2026-07-24)؛ بقیهٔ کانال‌ها snapshot")
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".json.tmp2")
            tmp.write_text(json.dumps(cur, ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, p)
            return True
        except Exception:  # noqa: BLE001 — راست‌گوییِ کابین نباید حلقه را بکشد
            return False

    def poll_once(self) -> int:
        """یک دورِ long-poll. خروجی = تعداد updateهای پردازش‌شده. وقتی not wired → 0 (no-opِ
        امن، بدونِ هیچ فراخوانیِ شبکه). خطای شبکه fail-soft: ۰ برمی‌گردد، حلقه کشته نمی‌شود.
        T-8 router: پیام‌های متنی مالک → handle_command + پاسخ. callback_query → dispatch_callback + answer."""
        if not self.wired:
            return 0
        if self._killed():
            return 0
        # Cockpit v2 fix (2026-07-10): بدونِ allowed_updates صریح، تلگرام «آخرین تنظیم» را
        # نگه می‌دارد؛ چون این همان باتِ control-brain است و ممکن است جایی به فقط ["message"]
        # قفل شده باشد، دکمه‌ها (callback_query) هرگز نمی‌رسیدند. صریح هر دو نوع را می‌خواهیم.
        params = {"offset": self._offset, "timeout": self._lp,
                  "allowed_updates": json.dumps(["message", "callback_query"])}
        try:
            data = self._http_get(self._build_url("getUpdates", params), float(self._lp))
        except Exception:  # noqa: BLE001 — خطای شبکه، بدونِ leakِ URL/token
            return 0
        if not isinstance(data, dict) or not data.get("ok"):
            # جلسه ۴۶ — تشخیصِ pollerِ دوم: 409 یعنی مصرف‌کنندهٔ دیگری روی همین بات
            # getUpdates می‌زند و دکمه‌ها را می‌بلعد (مثلاً control-brainِ قدیمی/دستگاهِ دیگر).
            if isinstance(data, dict) and data.get("error_code") == 409:
                if time.time() - getattr(self, "_last_409_alert", 0.0) > 3600:
                    self._last_409_alert = time.time()
                    opslib.alert(["telegram getUpdates 409 Conflict — pollerِ دوم روی "
                                  "همین بات! دکمه‌ها را او می‌بلعد (control-brain قدیمی؟)"])
            return 0
        # نبضِ poll برای اتاقِ زنده/کابین: thread زنده است و آپدیت می‌گیرد (fail-soft).
        try:
            p = opslib.STATE_DIR / "pulse" / "telegram-poll.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({"ts": opslib.now_iso(),
                                       "batch": len(data.get("result") or [])},
                                      ensure_ascii=False), "utf-8")
            os.replace(tmp, p)
        except OSError:
            pass
        # Task 2 (2026-07-24): writerِ زندهٔ channel-status — هر ~۱۵ دقیقه، poll-محور، ارزان
        if time.time() - self._last_chstat > 900:
            self._last_chstat = time.time()
            self._write_channel_status()
        processed = 0
        offset_dirty = False
        for upd in data.get("result") or []:
            uid = upd.get("update_id")
            if isinstance(uid, int) and uid + 1 > self._offset:
                self._offset = uid + 1
                offset_dirty = True

            # ── تشخیص نوع update: callback_query یا text message ──
            is_callback = "callback_query" in upd
            cbq = upd.get("callback_query") if is_callback else {}

            msg = upd.get("message") or cbq.get("message") or {}
            chat_id = msg.get("chat", {}).get("id") or cbq.get("message", {}).get("chat", {}).get("id")
            # 🐛 فیکسِ جلسه ۴۶ (علتِ واقعیِ «نادیده»): برای callback، پیامِ ضمیمهٔ دکمه خودش
            # `text` دارد (بدنهٔ منو). فرمِ قبلی `msg.get("text") or cbq.data` آن متن را
            # می‌خواند و callback data هرگز خوانده نمی‌شد → dispatch("متنِ منو") → «نادیده».
            # برای callback همیشه data؛ برای پیام همیشه text. (تستِ e2e این را می‌گیرد.)
            if is_callback:
                text = cbq.get("data") or ""
            else:
                text = msg.get("text") or ""
            # 🐛 ۲۰۲۶-۰۷-۲۶ — گزارشِ مالک: «کلیک می‌کنم تأیید، می‌گوید فقط مالک».
            # برای یک callback، `msg` همان `cbq["message"]` است — یعنی **کارتی که خودِ
            # بات فرستاده** — پس `msg["from"]` همیشه پر است و شناسهٔ *بات* را می‌دهد.
            # فرمِ قبلی هرگز به `cbq["from"]` (که خودِ کلیک‌کننده است) نمی‌رسید، پس هر
            # کلیک به بات نسبت داده می‌شد و `_callback_owner_ok` آن را رد می‌کرد.
            # نتیجهٔ ساختاری: گیتِ fail-closed برای callbackها **همیشه** بسته بود — و
            # همین توضیح می‌دهد چرا جدولِ rfc_decision در کلِ تاریخِ سیستم صفر ردیف
            # دارد. کنشگرِ یک callback همیشه `cbq["from"]` است، هرگز فرستندهٔ پیام.
            from_id = ((cbq.get("from") if is_callback else None)
                       or msg.get("from") or {}).get("id")
            cbq_id = cbq.get("id")  # callback_query ID برای answerCallbackQuery

            # allowlist: chat_idهای مجاز (owner + گروه‌های TELEGRAM_ALLOWED_CHAT_IDS).
            # گروه‌پذیریِ کاکپیت (رأی مالک 2026-07-17). نبود = فقط owner (byte-identical).
            if chat_id not in self._allowed:
                processed += 1              # پردازش‌شده ولی رد‌شده (offset جلو رفت)
                continue

            # ── T-8: quarantine همیشه ثبت می‌شود (DATA) ──
            with self._lk:
                self._quarantine.append({
                    "update_id": uid, "chat_id": chat_id,
                    "from_id": from_id,
                    "text": str(text or "")[:1000],   # کران: پیامِ غول‌پیکر = حافظهٔ نا‌محدود ممنوع
                    "date": msg.get("date"),
                })

            # ── T-8: پردازشِ واقعی — command یا callback ──
            # پاسخ به همان chat_id (گروه یا چتِ ۱:۱) که فرمان از آن آمد — نه همیشه owner.
            # کارت‌های تأیید (request_approval_card) همچنان به owner می‌رود (قانونِ T-2: تنها
            # مسیرِ تأیید، owner-only intent)؛ ولی پاسخِ دستور به همان‌جا برمی‌گردد که پرسیده شد.
            try:
                if is_callback:
                    # callback_query → dispatch + answer
                    # C2-B: from_id به dispatcher می‌رود تا توکنِ statelessِ کارتِ پیشنهاد
                    # به مالک bind شود (همان الگوی GOV-P1 برای handle_command).
                    reply = self.dispatch_callback(str(text), from_id=from_id, external=True)
                    # reply می‌تواند str باشد (toast) یا dict (پیام جداگانه با کیبورد)
                    if isinstance(reply, dict):
                        if cbq_id:
                            self._answer_callback_query(cbq_id, "✅")
                        self.send_text(reply.get("text", ""),
                                       reply_markup=reply.get("reply_markup"),
                                       chat_id=chat_id)
                    else:
                        if cbq_id:
                            self._answer_callback_query(cbq_id, reply or "📝")
                else:
                    # text message → handle_command + send reply
                    # from_id thread-through: مرزِ سختِ سراسری فقط owner (red-team GOV-P1)
                    reply = self.handle_command(str(text), chat_id=chat_id,
                                                from_id=from_id)
                    if reply is not None:
                        if isinstance(reply, dict):
                            self.send_text(reply.get("text", ""),
                                           reply_markup=reply.get("reply_markup"),
                                           chat_id=chat_id)
                        else:
                            self.send_text(reply, chat_id=chat_id)
            except Exception as e:  # noqa: BLE001 — fail-soft: ارسال شکست → alert، حلقه ادامه
                opslib.alert([f"telegram T-8 dispatch error: {type(e).__name__}: {e}"])

            processed += 1
        # offset persistence: اگر offset جلو رفت و state_dir هست، در فایل ذخیره کن
        # (restart-safe). state_dir نباشد → همان رفتارِ حافظه‌ایِ T-1 (تست‌ها).
        if offset_dirty and self._state_dir:
            _save_offset(self._offset, self._state_dir)
        return processed

    @staticmethod
    def _toast_plain(text: str) -> str:
        """answerCallbackQuery متنِ ساده است (HTML render نمی‌شود) — تگ‌ها را بردار و
        entityها را باز کن تا `<i>...</i>` خام دیده نشود (باگِ toastِ جلسه ۴۶)."""
        return html.unescape(re.sub(r"<[^>]+>", "", str(text))).strip()

    def _answer_callback_query(self, callback_query_id: str, text: str = "") -> bool:
        """T-8: ارسال answerCallbackQuery برای dismiss کردنِ spinner روی دکمه.
        fail-soft: شکست = alert، بدونِ killِ حلقه."""
        if not self.wired:
            return False
        try:
            self._http_post(self._build_url("answerCallbackQuery", {}),
                            {"callback_query_id": callback_query_id,
                             # Cockpit v2 · INV-12: toast هم مثل sendMessage از redaction می‌گذرد؛
                             # + strip تگ چون toast متنِ ساده است (HTML parse نمی‌شود)
                             "text": self._redact(self._toast_plain(text))[:200],
                             "cache_time": 0})
            return True
        except Exception as e:  # noqa: BLE001 — fail-soft
            opslib.alert([f"telegram answerCallbackQuery error: {type(e).__name__}: {e}"])
            return False

    def run_forever(self) -> None:
        """حلقهٔ long-pollِ پس‌زمینه. not wired → فوراً برمی‌گردد (no-opِ امن). kill supreme:
        با اولین سیگنالِ kill_check/STOP می‌ایستد. خطای هر دور fail-soft است."""
        if not self.wired:
            return
        self._diagnose_webhook()  # جلسه ۴۶: کشفِ webhookِ رقیب (علتِ ۴۰۹ ابدیِ دکمه‌ها)
        self._set_my_commands()   # پاک‌سازیِ منوی قدیمی + ثبتِ منوی تمیز اختاپوس
        self._write_channel_status()   # Task 2: حقیقتِ live-wired از لحظهٔ بوتِ poll
        while not self._killed():
            self.poll_once()

    def _diagnose_webhook(self, delete: bool | None = None) -> dict:
        """یک‌بار در شروع: getWebhookInfo. اگر webhook ست باشد، getUpdates ما همیشه
        ۴۰۹ می‌گیرد و دکمه‌ها هرگز نمی‌رسند — علتِ محتملِ «نادیده» با باتِ مشترک.
        delete=True → deleteWebhook(drop_pending_updates=False) تا getUpdatesِ ما کار کند
        (پیش‌فرض از env: TELEGRAM_TAKE_OVER_WEBHOOK=1 → مالک صریحاً بات را از control-brain
        می‌گیرد). فقط لاگ/هشدار؛ هرگز token را echo نمی‌کند."""
        if delete is None:
            delete = os.environ.get("TELEGRAM_TAKE_OVER_WEBHOOK") == "1"
        try:
            info = self._http_get(self._build_url("getWebhookInfo", {}), 8.0)
            url = ((info or {}).get("result") or {}).get("url") or ""
            pending = ((info or {}).get("result") or {}).get("pending_update_count", 0)
            if url:
                opslib.alert([
                    f"telegram: webhookِ رقیب ست است (pending={pending})! دکمه‌ها به "
                    f"getUpdatesِ ما نمی‌رسند → «نادیده». علت: باتِ مشترک با control-brain. "
                    f"چاره: باتِ اختصاصی، یا TELEGRAM_TAKE_OVER_WEBHOOK=1 برای گرفتنِ بات."])
                if delete:
                    self._http_post(self._build_url("deleteWebhook", {}),
                                    {"drop_pending_updates": False})
                    opslib.alert(["telegram: deleteWebhook زده شد — بات از control-brain "
                                  "گرفته شد (رأی مالک TELEGRAM_TAKE_OVER_WEBHOOK)."])
                return {"webhook": True, "url_set": True, "deleted": delete,
                        "pending": pending}
            return {"webhook": False}
        except Exception as e:  # noqa: BLE001 — تشخیص نباید thread را بکشد
            opslib.alert([f"telegram getWebhookInfo failed (non-fatal): "
                          f"{type(e).__name__}"])
            return {"webhook": None, "error": type(e).__name__}

    def _set_my_commands(self) -> None:
        """منوی command تلگرام را پاک و دوباره ثبت می‌کند.
        حذفِ کشِ قدیمی (deleteMyCommands) برای رفعِ مشکلِ دستوراتِ رباتِ قبلی."""
        commands = [
            {"command": "start", "description": "🐙 منوی اصلی"},
            {"command": "overview", "description": "📊 نمای کلی"},
            {"command": "money", "description": "💰 پول و متابولیسم"},
            {"command": "finance", "description": "📊 وضعِ من (خلاصهٔ پول)"},
            {"command": "review", "description": "🧮 دسته‌بندی کن (یکی‌یکی)"},
            {"command": "books", "description": "📋 ثبتِ نهایی"},
            {"command": "sync", "description": "🔄 تازه‌ها رو بگیر"},
            {"command": "doctor", "description": "🩺 دکتر و تکامل"},
            {"command": "brain", "description": "🧠 حافظه و مغز"},
            {"command": "blueprint", "description": "🧭 بلوپرینت P0–P6"},
            {"command": "school", "description": "🎓 مدرسه"},
            {"command": "safety", "description": "🛡️ ایمنی"},
            {"command": "alerts", "description": "🚨 هشدارها و خام"},
            {"command": "organs", "description": "🦾 اندام‌ها (مدیریت)"},
            {"command": "neworgan", "description": "🆕 ساختِ اندامِ نو"},
            {"command": "wiring", "description": "🔌 نقشهٔ اتصال‌ها (راست‌گو)"},
            {"command": "health", "description": "🫀 سلامتِ اختاپوس"},
            {"command": "heart", "description": "💓 قلب — ریتم و تنظیم"},
            {"command": "queue", "description": "📥 صف تأیید"},
            {"command": "status", "description": "📊 وضعیت ارگانیسم"},
            {"command": "lead", "description": "📝 ثبت لید جدید"},
            {"command": "reentry", "description": "📋 بستهٔ بازگشت از gap"},
            {"command": "stop", "description": "🛑 توقف اضطراری"},
        ]
        try:
            self._http_post(self._build_url("deleteMyCommands", {}), {})
            self._http_post(self._build_url("setMyCommands", {}),
                             {"commands": commands})
        except Exception:  # noqa: BLE001 — fail-soft: منو بیاید یا نیاید، بات کار می‌کند
            pass

    # ─── T-2 · تأییدِ irreversible/مالی → human-append → EffectorGate.settle ────
    # جریانِ ستونی (تنها مسیرِ settle طبقِ TINV-7):
    #   request_approval_card(effect_id, amount, summary, guard_verdict)
    #     → ثبتِ intent در self._pending (registry ضدِ جعل: token منطبق لازم)
    #     → POST sendMessage با reply_markup (کارت + ۳ دکمه)
    #   کاربر کلیک → callback_query data = "app:approve:<effect_id>:<token>"
    #     → dispatch_callback → _do_approve → on_human_judgment (human-append, age_tick+1)
    #     → gate.release_gated_effects(entry) → gate.settle(effect_id) → _record_approval
    # هیچ مسیرِ دیگری settle نمی‌کند. تأییدِ جعلی (token نامنطبق / effect ناشناخته) = رد.

    def _new_token(self, effect_id: str, amount_aud: float) -> str:
        """توکنِ یک‌بارمصرفِ ضدِ جعلِ برای callback: هشِ effect_id + مبلغ + رازِ پویا.
        رازِ پویا = شمارندهٔ monotonic (از epoch). این کار replay/جعلِ callback را سخت می‌کند:
        مهاجم حتی با دیدنِ data باید توکنِ منطبق با همان effect+amount را داشته باشد."""
        import hashlib, time
        with self._lk:
            n = self._pending.get(effect_id, {}).get("_n", 0)
        payload = f"{effect_id}|{amount_aud:.6f}|{n}|{time.time_ns()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def request_approval_card(self, effect_id: str, amount_aud: float,
                              summary: str, guard_verdict: str = "") -> bool:
        """کارتِ تأیید را برای یک اثرِ برگشت‌ناپذیر/مالی به مالک می‌فرستد. effect_id و
        amount را در registry ثبت می‌کند با یک توکنِ ضدِ جعل. تأیید فقط از طریقِ
        dispatch_callback ممکن است. not wired → False (no-opِ امن، کارت فرستاده نمی‌شود).

        C7.1: ساخت/ارسال از `reissue_approval_card` (رندرِ canonicalِ اشتراکی با بازسازیِ
        بعد از restart) می‌گذرد؛ سپس یک ردیفِ **durable** با مبلغِ واقعی + binding + توکن
        نوشته می‌شود تا کارت از restart جان به در ببرد (pending_card_recovery). صفر تغییرِ
        semanticِ authorizationِ پول — release همچنان فقط از EffectorGate."""
        if not self.wired:
            return False
        if amount_aud <= 0:
            return False
        # C-caller-migration (2026-07-23): snapshotِ bindingِ ردیفِ gate در لحظهٔ ساختِ
        # کارت — approve بعداً همین را ارائه می‌دهد (نه بازخوانی از DB) تا اگر ردیف بعد
        # از کارت عوض شود، release_effect دقیقِ C4 با mismatch رد کند (ضدِ card-swap).
        _bind = {}
        try:
            if self._gate is not None and hasattr(self._gate, "binding_of"):
                _bind = self._gate.binding_of(effect_id) or {}
        except Exception:  # noqa: BLE001 — snapshot اختیاری؛ نبودش = مسیرِ fail-closedِ قبلی
            _bind = {}
        # C7.2: intent باید قبل از ارسال durable شود؛ raw bearer token روی دیسک ذخیره نمی‌شود.
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            made = _pcr.prepare_money_card(
                state_dir=self._state_dir, effect_id=effect_id, amount_aud=float(amount_aud),
                content_hash=_bind.get("content_hash"), action_kind=_bind.get("action_kind"),
                target_ref=_bind.get("target_ref"), summary=summary, owner=self._owner)
        except Exception:  # noqa: BLE001
            made = None
        if not made:
            return False                 # persistence/secret failure => no actionable card
        token = made["token"]
        if not made.get("send_needed", True):
            # Already delivered in an earlier call/boot: reconstruct RAM only, no spam.
            return self.reissue_approval_card(
                effect_id, amount_aud, summary, token=token,
                content_hash=_bind.get("content_hash"), action_kind=_bind.get("action_kind"),
                target_ref=_bind.get("target_ref"), guard_verdict=guard_verdict, send=False)
        lease_id = f"initial-{os.getpid()}-{threading.get_ident()}"
        if not _pcr._acquire_send_lease(self._state_dir, "money", effect_id, lease_id):  # noqa: SLF001
            return False
        try:
            _pcr.mark_delivery(state_dir=self._state_dir, kind="money", cid=effect_id,
                               delivery="LEASED")
            ok = self.reissue_approval_card(
                effect_id, amount_aud, summary, token=token,
                content_hash=_bind.get("content_hash"), action_kind=_bind.get("action_kind"),
                target_ref=_bind.get("target_ref"), guard_verdict=guard_verdict, send=True)
            if not _pcr.mark_delivery(state_dir=self._state_dir, kind="money", cid=effect_id,
                                      delivery="SENT" if ok else "PENDING"):
                return False
            return ok
        finally:
            _pcr.release_send_lease(self._state_dir, "money", effect_id)

    def reissue_approval_card(self, effect_id: str, amount_aud: float, summary: str, *,
                              token: str, content_hash=None, action_kind=None,
                              target_ref=None, guard_verdict: str = "", send: bool = True) -> bool:
        """رندرِ canonicalِ کارتِ مالی — **تنها منبعِ حقیقتِ ساخت/بازساخت** (C7.1). projection
        (`_pending`) را با binding + **همان توکنِ داده‌شده** بازسازی می‌کند؛ فقط اگر send=True و
        wired، کارتِ ۳-دکمه POST می‌شود. توکن از بیرون داده می‌شود تا بازسازیِ بعد از restart
        (مدل B) همان توکنِ پیش از restart را بازگرداند و دکمهٔ مالک معتبر بماند. صفر settle."""
        with self._lk:
            self._pending[effect_id] = {"amount_aud": float(amount_aud),
                                        "summary": str(summary)[:500],
                                        "guard": str(guard_verdict)[:200],
                                        "content_hash": content_hash,
                                        "action_kind": action_kind,
                                        "target_ref": target_ref,
                                        "token": token, "status": "pending"}
        if not send:
            return True                       # فقط projection (بازسازیِ بی‌ارسال، یا زیرِ HALT)
        if not self.wired:
            return False
        try:
            import sys as _s
            _s.path.insert(0, str(_HERE.parent))
            import events as _ev
            _ev.emit("approval.required", "approval-channel",
                     summary="یه کار منتظرِ تأییدِ توست", approval_state="required",
                     next_action="تلگرام: آره/نه")
        except Exception:  # noqa: BLE001
            pass
        # C2/C5 · INV-12: کارتِ پول هم از پاسِ redaction می‌گذرد.
        text = self._redact(
            self._render_approval_card(effect_id, amount_aud, summary, guard_verdict))
        kb = {"inline_keyboard": [[
            {"text": "تأیید ✅", "callback_data": f"app:approve:{effect_id}:{token}"},
            {"text": "رد ❌", "callback_data": f"app:deny:{effect_id}:{token}"},
            {"text": "بعداً ⏳", "callback_data": f"app:later:{effect_id}:{token}"},
        ]]}
        try:
            self._http_post(self._build_url("sendMessage", {}),
                            {"chat_id": self._owner, "text": text,
                             "parse_mode": "HTML", "reply_markup": kb})
        except Exception:  # noqa: BLE001 — fail-soft: کارت نرفت، pending باقی می‌ماند
            return False
        return True

    @staticmethod
    def _render_approval_card(effect_id: str, amount_aud: float, summary: str,
                              guard_verdict: str) -> str:
        """UX v2 §۲: کارتِ غنی با خط‌جداکننده، آیکن، escapeِ HTML."""
        g = f"\n🛡 گارد: <code>{html.escape(str(guard_verdict))}</code>" if guard_verdict else ""
        return (f"🐙 <b>تأییدِ لازم</b> · 🔴 برگشت‌ناپذیر\n"
                f"──────────\n"
                f"📌 پیشنهاد: «{html.escape(str(summary))}»\n"
                f"💰 مبلغ: AU${amount_aud:.2f}\n"
                f"🛡 گارد: organ ✅ · money 🔒 · cap ✅\n"
                f"⚠️ ریسک: {'هیچ' if amount_aud <= 0 else 'موجود'}{g}\n"
                f"──────────\n"
                f"<i>تأیید = ضمیمهٔ انسانی؛ تنها چیزی که settle را آزاد می‌کند.</i>")

    # C7.2: سیاستِ مرکزیِ callback. هر scheme که state/ledger/effect/control را تغییر می‌دهد
    # فقط با هویتِ واقعیِ مالک مجاز است. navigation/read-only می‌تواند در گروه allowlisted خوانده شود.
    _MUTATING_CALLBACK_SCHEMES = frozenset({
        "app", "rfc", "home", "act", "rev", "jrn", "acct", "prop"
    })
    _MUTATING_MENU_PAGES = frozenset({"stop_confirm", "learned"})

    def _callback_requires_owner(self, parts: list[str]) -> bool:
        if not parts:
            return False
        if parts[0] in self._MUTATING_CALLBACK_SCHEMES:
            return True
        return parts[0] == "menu" and len(parts) > 1 and parts[1] in self._MUTATING_MENU_PAGES

    def _callback_owner_ok(self, from_id) -> bool:
        try:
            return self._owner is not None and from_id is not None and int(from_id) == int(self._owner)
        except (TypeError, ValueError):
            return False

    def dispatch_callback(self, data: str, from_id=None, *, external: bool = False,
                          trusted_internal: bool = False) -> str | dict:
        """routerِ callbackهای کارت‌ها. data = 'app:<verb>:<effect_id>:<token>' (پول، T-2)
        یا 'rfc:<verb>:<rfc_id>:<token>' (تکامل، W-3)، یا 'menu:<page>' (UX v3).
        خروجی = متنِ پاسخ برای answerCallbackQuery یا dict (پیام جداگانه با کیبورد).
        هر callback نامعتبر/جعلی → 'رد'. `from_id` (C2-B) فقط به مسیرِ prop می‌رود
        (bindِ owner در توکنِ stateless)؛ schemeهای دیگر دست‌نخورده.
        این متد از poll_once (T-8 router) برای هر callback_queryِ مالک صدا زده می‌شود."""
        parts = str(data or "").split(":")
        # C7.2/P0: callback بیرونیِ mutating بدون owner identity هرگز عبور نمی‌کند.
        # فراخوانیِ داخلی باید trusted_internal=True را صریح بدهد؛ None دیگر معادل owner نیست.
        if self._callback_requires_owner(parts) and (external or from_id is not None):
            # Every externally reachable mutation is fail-closed. Direct in-process calls
            # retain compatibility as trusted test/application seams; callers that route
            # untrusted data MUST set external=True (poll_once always does).
            if trusted_internal:
                pass
            elif not self._callback_owner_ok(from_id):
                return "⛔ فقط مالک می‌تواند این تصمیم را اجرا کند"
        if parts[0] == "menu":
            return self._dispatch_menu(parts)
        if parts[0] == "home":              # جلسه ۴۶: آره/نهِ خانهٔ ساده
            return self._dispatch_home(parts)
        if parts[0] == "rfc":
            return self._dispatch_rfc(parts)
        # ── Cockpit v2: لایهٔ read/nav/act — کنارِ schemeهای موجود، بدونِ دست‌زدن به آن‌ها ──
        if parts[0] == "card":
            return self._dispatch_card(parts)
        if parts[0] == "pg":
            return self._dispatch_page(parts)
        if parts[0] == "act":
            return self._dispatch_act(parts)
        if parts[0] == "rev":                 # حسابدارِ گفتگومحور (propose-only)
            return self._dispatch_review(parts)
        if parts[0] == "jrn":                 # صفِ ثبتِ دفتر (تأییدِ دومِ مالک → post_journal)
            return self._dispatch_books(parts)
        if parts[0] == "acct":                # میان‌بُرهای دکمه‌ایِ حسابداری (review/books/sync)
            return self._dispatch_acct(parts)
        if parts[0] == "prop":                # G3 arc: رأیِ کارتِ پیشنهاد (measurement-only، جدا از پول)
            return self._dispatch_proposal(parts, from_id=from_id)
        if len(parts) != 4 or parts[0] != "app":
            return "نادیده"
        verb, effect_id, token = parts[1], parts[2], parts[3]
        # C7.2: verify در لحظهٔ کلیک (owner+expiry+HMAC+binding+Chrono)، نه اعتماد به RAM.
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            _dbp = str(Path(self._state_dir) / "chrono.db") if self._state_dir else None
            _status_fn = None
            if self._gate is not None and hasattr(self._gate, "status_of"):
                _status_fn = self._gate.status_of
            ok_cb, durable_meta, why_cb = _pcr.verify_callback(
                state_dir=self._state_dir, effect_id=effect_id, token=token,
                owner=(from_id if from_id is not None else self._owner), chrono_db_path=_dbp,
                status_fn=_status_fn, require_effect_pending=(verb == "approve"))
        except Exception:  # noqa: BLE001
            ok_cb, durable_meta, why_cb = False, None, "verify-error"
        if not ok_cb:
            return f"رد: کارت نامعتبر/منقضی ({why_cb})"
        with self._lk:
            projection = self._pending.get(effect_id)
        if projection is None or projection.get("status") != "pending":
            return "رد: اثر ناشناخته یا قبلاً تصمیم‌گرفته"
        if not _cteq(token, projection.get("token", "")):
            return "رد: توکنِ تأیید نامنطبق (ضدِ جعل)"
        # Authorization metadata comes from the verified durable record. RAM contributes
        # presentation-only fields; it can never replace amount/binding/owner/expiry.
        meta = dict(durable_meta or {})
        meta["token"] = token
        meta["summary"] = projection.get("summary", meta.get("summary", ""))
        meta["status"] = projection.get("status")
        meta["defer_count"] = int(meta.get("defer_count", 0))
        if verb == "approve":
            return self._do_approve(effect_id, meta)
        if verb == "deny":
            if not _pcr.persist_money_decision(state_dir=self._state_dir,
                                               effect_id=effect_id, decision="DENIED"):
                return "رد: ثبت پایدار تصمیم ناموفق"
            with self._lk:
                projection["status"] = "denied"
            return "رد شد ❌ (هیچ اثری settle نشد)"
        if verb == "later":
            # 2026-07-18: دیگر no-op نیست — یک ردِ تعویق ذخیره می‌کند (شمارش + زمان)
            # تا دکمه واقعاً چیزی «عوض/ذخیره» کند، بدونِ settle. pending می‌ماند.
            count = int(meta.get("defer_count", 0)) + 1
            if not _pcr.persist_money_decision(state_dir=self._state_dir,
                                               effect_id=effect_id, decision="DEFERRED",
                                               defer_count=count):
                return "رد: ثبت پایدار تعویق ناموفق"
            with self._lk:
                projection["defer_count"] = count
                try:
                    projection["deferred_at"] = opslib.now_iso()
                except Exception:  # noqa: BLE001
                    pass
            return f"بعداً ⏳ (ثبت شد ×{count}؛ pending می‌ماند)"
        return "نادیده"

    def _dispatch_proposal(self, parts: list, from_id=None) -> str:
        """G3 arc (ported to master 2026-07-18): 'prop:<verb>:<token>' — رأیِ مالک به کارتِ
        پیشنهاد را می‌سنجد. schemeِ 'prop' جدا از 'app' (پول): این مسیر هرگز
        settle/ledger/spend نمی‌زند — فقط یک ردیفِ اندازه‌گیریِ in-memory. بدترین حالتِ یک
        callbackِ جعلی = یک متریکِ اشتباه، نه یک ریال جابه‌جایی؛ ضمناً poll_once از قبل
        allowlistِ chat_idِ مالک را اعمال کرده. قلابِ تزریق‌نشده (فلگ خاموش) → «نادیده»،
        دقیقاً مثل هر schemeِ ناشناخته. هوک از wiring.wire_proposal_buttons ست می‌شود."""
        hook = getattr(self, "_proposal_hook", None)
        if hook is None or len(parts) != 3:
            return "نادیده"
        # F1 (red-team P2): schemeِ prop هم owner-gated است مثلِ /panic (GOV-P1). اگر کارت
        # به گروهِ allowlist برود، عضوِ غیرمالک نباید رأیِ مالک را جعل کند. from_id=None
        # (فراخوانِ داخلی/غیرتلگرام) عبور می‌کند؛ ownerِ نامشخص هم عبور (لایهٔ allowlist گارد است).
        if from_id is not None and self._owner is not None and \
                str(from_id).strip() != str(self._owner).strip():
            return "رد: تنها مالک می‌تواند به کارتِ پیشنهاد رأی دهد"
        try:
            # F3 (red-team P2): arity را یک‌بار بازرسی کن و hook را دقیقاً یک‌بار صدا بزن.
            # retryِ TypeError یک foot-gun بود: TypeErrorِ داخلیِ hook (بعدِ اثرِ جزئی)
            # باعثِ دو-صداکردن می‌شد. حالا از سیگنچر تصمیم می‌گیریم، بدونِ re-invoke.
            import inspect as _insp
            try:
                _np = sum(1 for p in _insp.signature(hook).parameters.values()
                          if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY))
            except (TypeError, ValueError):
                _np = 3
            # C2-B: from_id برای bindِ ownerِ توکنِ stateless (pb1) — restart-safe
            rec = hook(parts[2], parts[1], from_id) if _np >= 3 else hook(parts[2], parts[1])
        except Exception:  # noqa: BLE001 — تپِ بد نباید threadِ poller را بکشد
            return "نادیده"
        if rec is None:
            return "قبلاً ثبت شده یا کارتِ کهنه ⏳"
        if rec.get("event") == "expired":
            return "کارت منقضی شده ⏳ (اگر هنوز معتبر است، پیشنهاد دوباره صادر می‌شود)"
        if rec.get("event") == "deferred":
            return "بعداً ⏳ (کارت زنده می‌ماند — هر وقت خواستی تصمیم بگیر)"
        return {"ok": "ثبت شد ✅ (فقط اندازه‌گیری — هیچ اثری settle نشد)",
                "no": "ثبت شد ❌"}.get(parts[1], "ثبت شد")

    # ─── خانهٔ سادهٔ آره/نه (جلسه ۴۶، رأی مالک «فقط آره یا نه بگم») ──────────────────
    def _gather_decisions(self) -> list[dict]:
        """هر چیزی که یک آره/نهِ ساده لازم دارد، به زبانِ آدمیزاد. منبع: پیشنهادهای
        بهبودِ خودِ سیستم (RFC) + کارهای منتظرِ تأیید (پول/Project-F). هر آیتم {q,yes,no}."""
        out: list[dict] = []
        with self._lk:
            rfcs = [(k, dict(v)) for k, v in self._pending_rfc.items()]
            apps = [(k, dict(v)) for k, v in self._pending.items()]
        for rid, m in rfcs:
            if m.get("status") != "pending":
                continue
            tok = m.get("token", "")
            summ = str(m.get("summary", "") or "").strip()
            q = "🔧 می‌خوام یه چیزی رو تو خودم بهتر کنم" + (f" ({summ[:50]})" if summ else "") + ". باشه؟"
            out.append({"q": q, "yes": f"home:rfcyes:{rid}:{tok}",
                        "no": f"home:rfcno:{rid}:{tok}"})
        for eid, m in apps:
            if m.get("status") != "pending":
                continue
            tok = m.get("token", "")
            amt = float(m.get("amount_aud", 0) or 0)
            summ = str(m.get("summary", "") or "").strip() or "یه کار"
            money = f" ({amt:.0f} دلار)" if amt > 0 else ""
            q = f"💰 {summ[:50]}{money} — تأیید کنم؟"
            out.append({"q": q, "yes": f"home:appyes:{eid}:{tok}",
                        "no": f"home:appno:{eid}:{tok}"})
        return out[:5]

    def _selfheal_recent(self) -> int:
        """چند بار در ۲۴ ساعتِ اخیر عضوی خراب شد و سیستم خودش درستش کرد (بی‌محتوا)."""
        try:
            import datetime as _dt
            p = opslib.STATE_DIR / "selfheal-events.jsonl"
            if not p.exists():
                return 0
            cutoff = _dt.datetime.now().timestamp() - 86400
            n = 0
            for ln in p.read_text("utf-8").splitlines()[-50:]:
                try:
                    if float(json.loads(ln).get("ts", 0)) >= cutoff:
                        n += 1
                except (ValueError, TypeError):
                    continue
            return n
        except OSError:
            return 0

    def _learn_bits(self) -> tuple[str, int]:
        """خطِ «چی یاد گرفتم» + شمارِ کشف‌های تازه (بی‌محتوا)."""
        try:
            import sys as _s
            _s.path.insert(0, str(_HERE.parent / "cortex"))
            import discoveries
            n = discoveries.unseen_count()
            return ((f"\n🧠 اخیراً {n} چیزِ جدید یاد گرفتم — «📚 چی یاد گرفتی؟»" if n else ""), n)
        except Exception:  # noqa: BLE001
            return ("", 0)

    def _simple_home(self) -> dict:
        """خانهٔ ساده: یا «همه‌چیز خوبه»، یا چند سوالِ آره/نه. صفر جارگون."""
        decs = self._gather_decisions()
        heal = self._selfheal_recent()
        heal_line = (f"\n🩹 اخیراً {heal} بار یه چیزی خراب شد و خودم درستش کردم." if heal else "")
        learn_line, n_learn = self._learn_bits()
        learn_btn = ([{"text": "📚 چی یاد گرفتی؟", "callback_data": "menu:learned"}]
                     if n_learn else [])
        if not decs:
            kb = [[{"text": "📊 حالت چطوره؟", "callback_data": "menu:status"},
                   {"text": "⚙️ بیشتر", "callback_data": "menu:more"}]]
            if learn_btn:
                kb.insert(0, learn_btn)
            return {
                "text": ("🐙 <b>همه‌چیز خوبه</b>\n"
                         "خودم دارم کار می‌کنم، یاد می‌گیرم و خودمو درست می‌کنم.\n"
                         "هر وقت کاری ازت داشتم همین‌جا می‌پرسم — فقط آره یا نه. ✅"
                         + heal_line + learn_line),
                "reply_markup": {"inline_keyboard": kb},
            }
        lines = ["🐙 <b>چند چیز ازت می‌پرسم:</b>", ""]
        rows = []
        for i, d in enumerate(decs, 1):
            lines.append(f"<b>{i}.</b> {html.escape(d['q'])}")
            rows.append([{"text": f"✅ آره ({i})", "callback_data": d["yes"]},
                         {"text": f"❌ نه ({i})", "callback_data": d["no"]}])
        if learn_btn:
            rows.append(learn_btn)
        rows.append([{"text": "⚙️ بیشتر", "callback_data": "menu:more"}])
        return {"text": "\n".join(lines) + heal_line + learn_line,
                "reply_markup": {"inline_keyboard": rows}}

    def _menu_learned(self) -> dict:
        """صفحهٔ «چی یاد گرفتم» — خطوطِ سادهٔ کشف/یادگیری (بی‌محتوا). دیدن = seen."""
        try:
            import sys as _s
            _s.path.insert(0, str(_HERE.parent / "cortex"))
            import discoveries
            ls = discoveries.lines(8)
            discoveries.mark_seen()
            body = "\n".join(ls) if ls else "هنوز چیزِ تازه‌ای یاد نگرفتم — به‌زودی!"
        except Exception:  # noqa: BLE001
            body = "الان نمی‌تونم لیست رو بیارم."
        return {"text": "📚 <b>تازه‌ها — چی یاد گرفتم/کشف کردم</b>\n──────────\n" + body,
                "reply_markup": {"inline_keyboard": [[
                    {"text": "🏠 خانه", "callback_data": "menu:main"}]]}}

    def _dispatch_home(self, parts: list[str]):
        """خانه فقط router نمایشی است؛ mutation را به همان dispatcherهای canonical می‌سپارد.

        Owner identity در ``dispatch_callback`` پیش از رسیدن به این متد enforce شده است.
        این متد دیگر `_do_approve` یا RAM را مستقیم لمس نمی‌کند، تا app/rfc همیشه همان
        HMAC/expiry/durable-decision contract را طی کنند.
        """
        if len(parts) != 4:
            return self._simple_home()
        kind, _id, tok = parts[1], parts[2], parts[3]
        if kind in ("rfcyes", "rfcno"):
            self._dispatch_rfc(["rfc", "merge" if kind == "rfcyes" else "deny", _id, tok])
        elif kind in ("appyes", "appno"):
            # Re-enter the canonical app branch as a trusted internal dispatch.  It still
            # performs durable callback verification and decision persistence.
            self.dispatch_callback(
                f"app:{'approve' if kind == 'appyes' else 'deny'}:{_id}:{tok}",
                from_id=self._owner, trusted_internal=True)
        return self._simple_home()

    def _do_approve(self, effect_id: str, meta: dict) -> str:
        """human-append (is_human=1) → release gated effects → settle. تنها مسیرِ settle."""
        # Use the just-verified durable record, not mutable RAM, as authorization metadata.
        amount = float(meta.get("amount_aud", 0.0))
        judgment = {"verdict": "approve", "effect_id": effect_id,
                    "amount_aud": amount, "source": "telegram",
                    "summary": meta.get("summary", "")}
        # C-caller-migration (2026-07-23): اگر کارت با snapshotِ binding ساخته شده،
        # approve همان bindingِ ارائه‌شده به مالک را حمل می‌کند → routing به
        # release_effectِ دقیقِ C4 می‌رود (تنها مسیرِ مجازِ پول/E4)، با approval_idِ
        # تک‌مصرفهٔ مشتق از توکنِ ضدِ جعلِ همین کارت (anti-replay در DB).
        # کارتِ بدونِ snapshot → مسیرِ id-only قبلی (release_one؛ پول را C4.1 رد می‌کند).
        if meta.get("content_hash"):
            judgment.update({
                "content_hash": meta.get("content_hash"),
                "action_kind": meta.get("action_kind"),
                "target_ref": meta.get("target_ref"),
                # Never persist the raw callback bearer in chrono/ledger. A bound token
                # hash is sufficient for idempotency and cannot replay the Telegram card.
                "approval_id": f"tg:{effect_id}:{str(meta.get('token_sha256') or '')[:24]}",
                "approved_by": "owner-telegram"})
        # C7.2: reserve the owner decision durably *before* human-append/effect release.
        # If the process dies after an effect but before final ACK, APPROVING prevents a
        # second click and routes the card to reconciliation rather than duplicate action.
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            if not _pcr.persist_money_decision(state_dir=self._state_dir,
                                               effect_id=effect_id, decision="APPROVING"):
                return "رد: رزرو پایدار approval ناموفق"
        except Exception:  # noqa: BLE001
            return "رد: رزرو پایدار approval ناموفق"
        try:
            # جلسه ۴۶: توکنِ human-append — اثباتِ اینکه این append از تلگرام (مالک) است،
            # نه کدِ جعل‌کننده. گاردِ خاموش → None → رفتارِ قبلی (downgrade در chrono، بی‌خطر).
            _ha = _mint_ha_token(effect_id, "APPROVAL")
            entry = _on_human_judgment(judgment, gate=self._gate, ledger=self._ledger,
                                       ha_token=_ha)
            release_hash = entry.get("hash", "") if isinstance(entry, dict) else ""
            # Some injected/test ledgers do not return a hash. The binding release status
            # is authoritative for money; an empty entry alone must not trigger a second settle.
            released = False
            try:
                released = bool(self._gate is not None and
                                getattr(self._gate, "status_of", lambda _x: None)(effect_id)
                                == "releasable")
            except Exception:
                released = False
            if not release_hash and not released:
                _pcr.persist_money_decision(state_dir=self._state_dir, effect_id=effect_id,
                                            decision="RECONCILE_REQUIRED")
                return "⚠️ human-append تأیید نشد — RECONCILE_REQUIRED؛ settle نشد"
            settled = self._settle_effect(effect_id) if self._gate is not None else False
        except Exception:  # noqa: BLE001 — هر شکست = رد (fail-closed، هیچ settleِ نیمه)
            try:
                _pcr.persist_money_decision(state_dir=self._state_dir, effect_id=effect_id,
                                            decision="RECONCILE_REQUIRED")
            except Exception:
                pass
            return "رد: خطا در human-append؛ RECONCILE_REQUIRED"
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            if not _pcr.persist_money_decision(state_dir=self._state_dir,
                                               effect_id=effect_id, decision="APPROVED"):
                # Effect may already have happened.  APPROVING remains durable and blocks
                # replay; report reconciliation rather than lying about a clean failure.
                return "⚠️ اثر بررسی شد؛ ثبت نهایی ناموفق — RECONCILE_REQUIRED"
        except Exception:  # noqa: BLE001
            return "⚠️ اثر بررسی شد؛ ثبت نهایی ناموفق — RECONCILE_REQUIRED"
        with self._lk:
            meta["status"] = "approved"
            if effect_id in self._pending:
                self._pending[effect_id]["status"] = "approved"
        self._record_approval(Approval(action_id=effect_id, amount_aud=amount,
                                       status="approved", source="telegram"))
        _ = release_hash  # برای audit در آینده (T-7 Re-entry)؛ فعلاً مصرف نمی‌شود
        return "تأیید شد ✅" + (" و settle شد" if settled else " (human-append ثبت، settle نیاز به gate)")

    def _settle_effect(self, effect_id: str) -> bool:
        """gate را release + settle می‌کند. اگر gate نباشد → False (ولی human-append ثبت شد)."""
        if self._gate is None:
            return False
        # release از آخرین append (on_human_judgment بالا gate را هم release کرده)
        return bool(self._gate.settle(effect_id))

    # ─── UX v3 · routerِ منوی inline: menu:<page> ──────────────────────────────────
    def _dispatch_menu(self, parts: list[str]) -> str | dict:
        """شاخهٔ منوی dispatch_callback. parts = ['menu', '<page>'].
        هیچ اثرِ پولی/settle/gate‌ای اینجا نیست — فقط نمایشِ اطلاعات و هدایتِ کاربر.
        خروجی dict = پیامِ جداگانه با کیبورد؛ str = فقط toast روی دکمه."""
        if len(parts) < 2:
            return "نادیده"
        page = parts[1]
        if page == "status":
            return {"text": self.status_report_v2(),
                    "reply_markup": self.MENU_KEYBOARD}
        if page == "lead":
            return {"text": self._cmd_lead_prompt(),
                    "reply_markup": self.MENU_KEYBOARD}
        if page == "queue":
            return {"text": self._menu_queue(),
                    "reply_markup": self.MENU_KEYBOARD}
        if page == "lab":
            return {"text": self.lab_status(),
                    "reply_markup": self.MENU_KEYBOARD}
        if page == "stop":
            # تأییدِ kill-switch با دکمه‌های بله/خیر
            kb = {"inline_keyboard": [[
                {"text": "✅ بله، متوقف کن", "callback_data": "menu:stop_confirm"},
                {"text": "❌ خیر", "callback_data": "menu:main"},
            ]]}
            return {"text": ("🛑 <b>توقفِ اضطراری</b>\n\n"
                             "آیا مطمئنی؟ این کار ارگانیسم را متوقف می‌کند.\n"
                             "<i>برای راه‌اندازیِ دوباره: <code>_ops\\RUN-ORGANISM.bat</code></i>"),
                    "reply_markup": kb}
        if page == "stop_confirm":
            return {"text": self.kill_switch(),
                    "reply_markup": None}
        if page == "main":
            return self._main_menu()
        # ── ADHD (جلسه ۴۶): «الان» = فقط چیزهایی که به مالک نیاز دارند؛ «بیشتر» = گریدِ کامل ──
        if page == "now":
            return self._menu_now()
        if page == "learned":
            return self._menu_learned()
        if page == "more":
            return {"text": "🧭 <b>همهٔ امکانات</b>\n<i>هر تب فقط‌خواندنی است؛ "
                            "پول/merge همچنان فقط از کارت‌های تأیید.</i>",
                    "reply_markup": self.MENU_KEYBOARD}
        # ── Cockpit v2: ۸ تبِ کابین به‌عنوانِ صفحاتِ menu (read-safe، بدونِ توکن) ──
        if page in self.TAB_PAGES:
            return self._render_tab(page)
        return "نادیده"

    def _upgrades_text(self) -> str:
        """🧬 خودارتقا — دایجستِ پیشنهادهای اولویت‌دار (owner-facing، فقط‌خواندنی)."""
        rm = self._rm()
        u = (rm.read_upgrades() if rm else {}) or {}
        if not u:
            return ("🧬 <b>خودارتقا</b>" + self._DIV
                    + "حلقه هنوز نچرخیده — هر ۱۰ چرخهٔ مغز یک‌بار.\n"
                    + "<i>مغز روی 8772 باید روشن باشد (RUN-CORTEX.bat).</i>")
        cats = " · ".join(f"{k}:{len(v)}" for k, v in (u.get("by_category") or {}).items())
        tops = "\n".join(
            f"{t.get('priority')} · {html.escape(str(t.get('title','')))} "
            f"<code>[{t.get('change_level')}]</code>\n  ↳ {html.escape(str(t.get('suggested_action',''))[:90])}"
            for t in (u.get("top") or [])[:5])
        _ir = u.get("improvement_rate") or {}
        return ("🧬 <b>خودارتقا — نرخِ بهبود "
                f"{_ir.get('rate_pct', '—')}%</b> "
                f"<i>({_ir.get('moved', 0)}/{_ir.get('closed', 0)} نیت متریک را جابه‌جا کرد)</i>\n"
                f"پوششِ چک‌لیست: {u.get('checklist_pct', u.get('maturity_pct', '—'))}% "
                "<i>(ایستا — سقفِ ثابت، سنجهٔ پیشرفت نیست)</i>" + self._DIV
                + f"{u.get('n_proposals','—')} پیشنهاد · auto: "
                + ("🟢 روشن" if u.get("auto_enabled") else "⚪ خاموش (propose-only)") + "\n"
                + f"دسته‌ها: {cats}\n\n{tops}\n"
                + (f"\n💭 {html.escape(str(u.get('brain_note',''))[:140])}\n"
                   if u.get("brain_note") else "")
                + "<i>هر تغییرِ جدی از کارتِ RFC می‌پرسد؛ این فقط دایجست است.</i>")

    def _menu_now(self) -> dict:
        """📌 الان — یک صفحه، فقط نیازها (ADHD-first: کم، مرتب، قابلِ‌اقدام)."""
        try:
            import needs_digest
            d = needs_digest.compute(pending_count=self._count_pending())
        except Exception:  # noqa: BLE001 — صفحه هرگز کرش نمی‌کند
            d = {"items": [], "n": 0}
        if d["n"] == 0:
            body = "هیچ‌چیز منتظرِ تو نیست ✅\n<i>سیستم خودش می‌چرخد؛ برو به زندگی‌ات.</i>"
        else:
            body = "\n".join(f"{i}. {it}" for i, it in enumerate(d["items"], 1))
        kb = {"inline_keyboard": [
            [{"text": "📮 صف تأیید", "callback_data": "menu:queue"},
             {"text": "🔄 منو", "callback_data": "menu:main"}],
        ]}
        return {"text": f"📌 <b>الان — کارای من</b>\n──────────\n{body}",
                "reply_markup": kb}

    def _menu_queue(self) -> str:
        """نمایشِ صفِ تأییدهای در انتظار (فقط‌خواندنی)."""
        n_pending = self._count_pending()
        if n_pending == 0:
            return ("📮 <b>صفِ تأیید</b>\n"
                    "──────────\n"
                    "خالی است ✅\n"
                    "<i>هیچ کارتِ تأییدی در انتظار نیست.</i>")
        items = []
        with self._lk:
            pend = [(eid, meta) for eid, meta in self._pending.items()
                    if meta.get("status") == "pending"]
        for eid, meta in pend:
            amt = meta.get("amount_aud", 0)
            summary = meta.get("summary", "")[:60]
            # Cockpit v2 (تستِ ۱۸): وضعیتِ authoritative از گیتِ تک‌گلوگاه، نه خوداظهاری.
            auth = ""
            if self._gate is not None and hasattr(self._gate, "status_of"):
                try:
                    st = self._gate.status_of(eid)
                    auth = f" · gate:<code>{html.escape(str(st))}</code>" if st else " · gate:—"
                except Exception:  # noqa: BLE001 — fail-soft
                    auth = ""
            items.append(f"• <code>{html.escape(str(eid))}</code> — AU${amt:.2f}{auth}\n"
                         f"  {html.escape(str(summary))}")
        body = "\n".join(items) if items else "خالی"
        return (f"📮 <b>صفِ تأیید</b> ({n_pending} مورد)\n"
                f"──────────\n"
                f"{body}\n"
                f"<i>تأیید از طریقِ دکمه‌های کارت‌ها انجام می‌شود.</i>")

    # ─── W-3 · routerِ RFC: rfc:<verb>:<rfc_id>:<token> — فقط ثبتِ verdict ─────────
    def _dispatch_rfc(self, parts: list[str]) -> str:
        """شاخهٔ RFCِ dispatch_callback. ثبتِ verdict یک اثرِ پولی نیست — هیچ
        settle/gate/effectorی اینجا صدا زده نمی‌شود. اعمالِ merge پشتِ flag و با
        human-append در مسیرِ doctor است (مصرفِ pop_rfc_verdicts).
        ضدِ replay: فقط status == 'pending' پذیرفته می‌شود؛ token با _cteq چک می‌شود."""
        if len(parts) == 3:
            # کارتِ قدیمیِ ۳-تکه (پیش از W-3، بدونِ token/registry) — graceful، بدونِ crash
            return "رد: کارتِ قدیمی — کارتِ نو صادر می‌شود"
        if len(parts) != 4:
            return "نادیده"
        verb, rfc_id, token = parts[1], parts[2], parts[3]
        with self._lk:
            meta = self._pending_rfc.get(rfc_id)
        if meta is None or meta.get("status") != "pending":
            return "رد: RFC ناشناخته یا قبلاً تصمیم‌گرفته"
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            ok_rfc, _durable, why_rfc = _pcr.verify_rfc_callback(
                state_dir=self._state_dir, rfc_id=rfc_id, token=token,
                owner=self._owner)
        except Exception:
            ok_rfc, why_rfc = False, "verify-error"
        if not ok_rfc or not _cteq(token, meta.get("token", "")):
            return f"رد: توکنِ RFC نامعتبر/منقضی ({why_rfc})"
        if verb == "edit":
            # 3a-afferent: [✍️ ویرایش] → حالتِ انتظارِ متنِ آزاد (الگوی acct_review).
            # هیچ verdict ثبت نمی‌شود و token مصرف نمی‌شود (decision همچنان SUBMITTED —
            # دکمه‌های merge/deny معتبر می‌مانند).
            with self._lk:
                self._awaiting_rfc_edit = rfc_id
            try:
                import acct_review as _ar_x
                _ar_x.set_awaiting_free(False)
            except Exception:  # noqa: BLE001
                pass
            return ("✍️ متنِ بازنگری/ویرایش را به‌صورتِ یک پیامِ متنی بفرست — برای "
                    f"{rfc_id}")
        if verb in ("merge", "deny"):
            new_status = "merge-approved" if verb == "merge" else "denied"
            # C7.2: callback success is conditional on fsync.  A failed durable write
            # must not be acknowledged or reflected in RAM.
            if not self._persist_rfc_verdict(rfc_id, new_status):
                return "رد: ثبت پایدار رأی RFC ناموفق"
            with self._lk:
                meta["status"] = new_status
            return ("ثبت شد ✅ — merge فقط پشتِ flag و با human-append اعمال می‌شود"
                    if verb == "merge" else "رد شد ❌")
        return "نادیده"

    def _persist_rfc_verdict(self, rfc_id: str, verdict: str) -> bool:
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            return bool(_pcr.persist_rfc_verdict(
                state_dir=self._state_dir, rfc_id=rfc_id, verdict=verdict))
        except Exception:  # noqa: BLE001
            return False

    def claim_rfc_verdicts(self, worker_id: str, lease_s: int = 300) -> list[tuple[str, str, int]]:
        """Durably lease owner decisions. Applying doctor code must acknowledge the lease
        only after its idempotent operation receipt exists."""
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            return _pcr.claim_rfc_verdicts(state_dir=self._state_dir,
                                           worker_id=worker_id, lease_s=lease_s)
        except Exception:
            return []

    def begin_rfc_apply(self, rfc_id: str, revision: int, operation_key: str) -> bool:
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            return bool(_pcr.begin_rfc_apply(
                state_dir=self._state_dir, rfc_id=rfc_id, revision=revision,
                operation_key=operation_key))
        except Exception:
            return False

    def ack_rfc_verdict(self, rfc_id: str, revision: int, *, applied: bool,
                        receipt_id: str = "") -> bool:
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            return bool(_pcr.ack_rfc_verdict(
                state_dir=self._state_dir, rfc_id=rfc_id, revision=revision,
                applied=applied, receipt_id=receipt_id))
        except Exception:
            return False

    def pop_rfc_verdicts(self) -> list[tuple[str, str]]:
        """Legacy at-least-once lease API.

        New doctor code MUST use claim_rfc_verdicts + ack_rfc_verdict so APPLIED is written
        only after an operation receipt. This method leases a batch and returns it once per
        lease window; it never lies that the operation was consumed/applied.
        """
        claims = self.claim_rfc_verdicts(f"legacy-pop-{os.getpid()}", lease_s=300)
        out = [(rid, verdict) for rid, verdict, _revision in claims]
        with self._lk:
            for rid, _ in out:
                if rid in self._pending_rfc:
                    self._pending_rfc[rid]["consumed"] = True
        return out

    # ─── T-3 · UIِ Lead: /lead → attribution.propose (mint LEAD-YYYYMMDD-nnn) ──────
    LEAD_CELLS = [("lead.doer", "نقاشی (Lead)"), ("ziman.doer", "Ziman"),
                  ("crypto.doer", "Crypto")]      # هم‌سان با panel/server.py

    # ── منوی سادهٔ ADHD (جلسه ۴۶): ۳ ردیف، یک اولویت — عمقِ کامل زیرِ «همهٔ امکانات» ──
    SIMPLE_KEYBOARD: dict = {
        "inline_keyboard": [
            [{"text": "📌 الان — کارای من", "callback_data": "menu:now"}],
            [{"text": "🫀 وضعیت سریع", "callback_data": "menu:status"}],
            [
                {"text": "🧭 همهٔ امکانات", "callback_data": "menu:more"},
                {"text": "🛑 توقف", "callback_data": "menu:stop"},
            ],
        ],
    }

    # ── منوی کاملِ inline اختاپوس (حالا زیرِ «همهٔ امکانات» — بدونِ حذفِ هیچ قابلیت) ──
    MENU_KEYBOARD: dict = {
        "inline_keyboard": [
            [
                {"text": "📊 نمای کلی", "callback_data": "menu:overview"},
                {"text": "🧠 مغز مرکزی", "callback_data": "menu:cortex"},
            ],
            [
                {"text": "🧭 بلوپرینت", "callback_data": "menu:blueprint"},
            ],
            [
                {"text": "🧠 حافظه و مغز", "callback_data": "menu:brain"},
                {"text": "🩺 دکتر و تکامل", "callback_data": "menu:doctor"},
            ],
            [
                {"text": "🦾 اندام‌ها", "callback_data": "menu:organs"},
            ],
            [
                {"text": "💰 پول و متابولیسم", "callback_data": "menu:money"},
                {"text": "📊 وضعِ من", "callback_data": "menu:finance"},
            ],
            [
                {"text": "🎓 مدرسه", "callback_data": "menu:school"},
            ],
            [
                {"text": "🛡️ ایمنی", "callback_data": "menu:safety"},
                {"text": "🚨 هشدارها و خام", "callback_data": "menu:alerts"},
            ],
            [
                {"text": "📊 وضعیت", "callback_data": "menu:status"},
                {"text": "📝 ثبت لید", "callback_data": "menu:lead"},
            ],
            [
                {"text": "📮 صف تأیید", "callback_data": "menu:queue"},
                {"text": "🧪 آزمایش‌ها", "callback_data": "menu:lab"},
            ],
            [
                {"text": "🛑 توقف اضطراری", "callback_data": "menu:stop"},
            ],
        ],
    }

    def send_text(self, text: str, reply_markup: dict | None = None,
                  chat_id: int | None = None, stream: str | None = None) -> bool:
        """پیامِ ساده (یا با کیبورد). مقصد = chat_id یا، اگر داده نشد، owner.
        گروه‌پذیری (رأی مالک 2026-07-17): پاسخ به همان chat (گروه/چت) که فرمان از آن آمد.
        `stream` (رأی مالک 2026-07-26): جریانِ محیطی به تاپیکِ خودش می‌رود نه DM —
        ولی فقط وقتی chat_id صریح داده نشده باشد (پاسخِ مستقیم همیشه برنده است).
        not wired → False. خطای شبکه fail-soft."""
        if not self.wired:
            return False
        target = int(chat_id) if chat_id is not None else self._owner
        thread = None
        if chat_id is None and stream:
            # ── ساعتِ سکوت (رأیِ مالک ۲۰۲۶-۰۷-۲۷: «۰ تا ۷») ──────────────────
            # اندازه‌گیری: ۷ پیامِ خودکار بینِ ۲۲ تا ۸ رفته بود. فقط **جریانِ
            # محیطی** ساکت می‌شود — پاسخِ مستقیمِ مالک (chat_id صریح) و هشدارِ
            # فوری هرگز. چیزی صف نمی‌شود: جریانِ محیطی دوره‌ای است و نسخهٔ بعدی
            # خودش می‌آید؛ نگه‌داشتنش فقط رگبارِ صبحگاهی می‌سازد.
            if _quiet_now() and str(stream) not in _NEVER_QUIET:
                return False
            r_chat, r_topic = _stream_route(stream)
            if r_chat is not None and r_topic is not None:
                target, thread = r_chat, r_topic
        text = self._redact(text)   # Cockpit v2 · INV-12: هر خروجی از پاسِ redaction می‌گذرد
        body = {"chat_id": target, "text": text, "parse_mode": "HTML"}
        if thread is not None:
            body["message_thread_id"] = thread
        if reply_markup:
            body["reply_markup"] = reply_markup
        ok = True
        try:
            self._http_post(self._build_url("sendMessage", {}), body)
        except Exception:  # noqa: BLE001
            ok = False
        # سنجشِ حجم و تکرار، قبل از هر تصمیمِ ضدِاسپم (رأیِ مالک ۲۰۲۶-۰۷-۲۶).
        # فقط hashِ متن ثبت می‌شود، نه خودِ متن. خطای لاگ هرگز ارسال را عوض نمی‌کند.
        try:
            import tg_send_log as _tsl  # noqa: WPS433
            _tsl.record(chat_id=target, topic_id=thread, text=text,
                        stream=stream, ok=ok)
        except Exception:  # noqa: BLE001
            pass
        return ok

    # دستوراتِ مرزِ-سختِ سراسری/kill — حتی داخلِ یک گروهِ allowlisted فقط شخصِ مالک
    # (from_id == owner) مجاز است، نه هر عضوِ گروه. (red-team GOV-P1، 2026-07-23)
    _OWNER_ONLY_COMMANDS = frozenset({"/panic", "/resume", "/stop"})
    # Commands that mutate durable state/control are owner-only in allowlisted groups too.
    # Prefix matching covers argument-bearing commands without treating read-only pages as mutation.
    _OWNER_ONLY_COMMAND_PREFIXES = (
        "/lead ", "/claim ", "/conflict ", "/neworgan ", "/organ-approve ",
        "/review", "/books", "/sync", "/start_exp", "/reveal ",
        # Task 3 (2026-07-24): دیالوگِ organ — همهٔ مسیرهای تغییردهنده owner-only
        "/heart set ", "/doctor focus ", "/doctor edit ", "/brain guide "
    )
    _GROUP_READONLY_COMMANDS = frozenset({
        "/start", "/status", "/overview", "/blueprint", "/brain", "/doctor",
        "/money", "/finance", "/school", "/safety", "/alerts", "/organs",
        "/queue", "/reentry", "/wiring", "/health", "/upgrades", "/lead",
        "/brief", "/think", "/spine", "/gates", "/verdicts", "/rules",
        "/guards", "/drafts", "/heart"
    })

    def handle_command(self, text: str, chat_id: int | None = None,
                       from_id: int | None = None) -> str | None:
        """routerِ دستوراتِ مالک. text = پیامِ ورودیِ مالک (بعد از allowlist).
        chat_id = همان chat که فرمان از آن آمد (گروه یا چتِ ۱:۱)؛ برای delegation به
        langar_bridge (فاز ۲). None = رفتارِ قبلی (owner) برای backward-compat.
        from_id = فرستندهٔ واقعیِ پیام. دستوراتِ مرزِ-سختِ سراسری/kill
        (_OWNER_ONLY_COMMANDS) حتی در یک گروهِ allowlisted فقط با from_id==owner
        اجرا می‌شوند — عضویتِ chat در allowlist برای پاک‌کردنِ HALT-ALL کافی نیست.
        from_id=None → backward-compat (فراخوانیِ برنامه‌ایِ owner-trusted؛ گارد رد نمی‌کند).
        خروجی = متنِ پاسخ (یا None برای نادیده). هر دستور فقط یک UI را برمی‌گرداند.
        UX v2: /start منو + HTML غنی + حذفِ T-4/T-6/reentry از router.
        هیچ ورودیِ untrustedای اجرا نمی‌شود — فقط ورودیِ validated به propose می‌رود."""
        t = (text or "").strip()
        if not t:
            return None
        # Non-owner members of an allowlisted group get an explicit read-only surface.
        # Unknown/delegated commands and free text are denied before any stateful handler.
        if from_id is not None and not self._callback_owner_ok(from_id):
            if t not in self._GROUP_READONLY_COMMANDS:
                return "⛔ این گروه فقط نمای فقط‌خواندنی دارد؛ تغییر فقط با مالک است."
        # owner-gate: every mutating command is only the owner's in an allowlisted group.
        owner_only = (t in self._OWNER_ONLY_COMMANDS or
                      any(t == p.rstrip() or t.startswith(p)
                          for p in self._OWNER_ONLY_COMMAND_PREFIXES))
        if owner_only and from_id is not None:
            try:
                if int(from_id) != int(self._owner):
                    return "⛔ فقط مالک می‌تواند این دستورِ تغییردهنده را اجرا کند."
            except (TypeError, ValueError):
                return "⛔ فرستندهٔ نامعتبر برای دستورِ تغییردهنده."
        # اگر مالک وسطِ حالتِ متنِ آزادِ حسابدار یک دستورِ / زد = تغییرِ زمینه → حالتِ متن را ببند
        # (تا پیامِ بعدیِ نامرتبط اشتباهاً جوابِ حسابداری تلقی نشود — رفعِ sticky-flagِ audit)
        if t.startswith("/"):
            try:
                import acct_review as _ar0
                if _ar0.is_awaiting_free():
                    _ar0.set_awaiting_free(False)
            except Exception:  # noqa: BLE001
                pass
            self._awaiting_rfc_edit = None   # 3a: تغییرِ زمینه = بستنِ حالتِ ویرایشِ RFC
        # UX v2: /start منوی اصلی
        if t == "/start":
            return self._main_menu()
        if t == "/lead":
            return self._cmd_lead_prompt()
        if t.startswith("/lead "):
            return self._cmd_lead_parse(t[len("/lead "):])
        # ── Task 3 (2026-07-24): دیالوگِ owner↔organ (Doctor/Brains/Hearts) ──
        if t == "/heart":
            return self._cmd_heart()
        if t.startswith("/heart set "):
            return self._cmd_heart_set(t[len("/heart set "):])
        if t.startswith("/doctor focus "):
            return self._cmd_doctor_focus(t[len("/doctor focus "):])
        if t.startswith("/doctor edit "):
            return self._cmd_doctor_edit(t[len("/doctor edit "):])
        if t.startswith("/brain guide "):
            return self._cmd_brain_guide(t[len("/brain guide "):])
        # T-4: lab — حذف از router (UX v2 §۱). متدها باقی‌اند برای backward-compat.
        # T-5: status (read-only)
        if t == "/status":
            return self.status_report_v2()
        # T-7: kill-switch (می‌ماند). re-entry digest حذف شد.
        if t == "/stop":
            return self.kill_switch()
        # مرزِ سختِ سراسری (پنیک): /panic HALT-ALL می‌نویسد، /resume آزاد می‌کند.
        # هم‌الگوی /stop (owner-only از allowlistِ poll_once)، ولی سراسری نه فقط ارگانیسم.
        if t == "/panic":
            return self.panic_all()
        if t == "/resume":
            return self.resume_all()
        # ── Cockpit v2: میان‌بُرهای تب + دستورهای جدید (هر ورودی همچنان DATA است) ──
        # /finance! → نسخهٔ expert (مالک/توسعه‌دهنده): Dr/Cr، ATO، دفترِ داخلی.
        # /finance  → نسخهٔ سادهٔ «وضعِ من» برای آرمین/عباس (UX-SPEC §۳.۱، 2026-07-18).
        if t == "/finance!":
            return {"text": self._finance_text_expert(),
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "📊 نسخهٔ ساده", "callback_data": "menu:finance"},
                        {"text": "🏠 منو", "callback_data": "menu:main"}]]}}
        if t in ("/overview", "/blueprint", "/brain", "/doctor", "/money",
                 "/finance", "/school", "/safety", "/alerts", "/organs"):
            return self._render_tab(t[1:])
        if t == "/upgrades":
            return self._upgrades_text()
        if t == "/queue":
            return {"text": self._menu_queue(), "reply_markup": self.MENU_KEYBOARD}
        if t == "/reentry":
            return self.reentry_packet()
        if t.startswith("/claim "):
            return self._cmd_claim(t[len("/claim "):])
        if t.startswith("/conflict "):
            return self._cmd_conflict(t[len("/conflict "):])
        if t == "/reveal" or t.startswith("/reveal "):
            arg = t[len("/reveal"):].strip()
            return self.reveal_experiment(arg) if arg else self.lab_status()
        # ── کابینِ راست‌گو (P3 2026-07-15): read-only، وضعیت از تازگیِ فایل نه پیش‌فرضِ فلگ ──
        if t == "/wiring":
            return self._cmd_wiring()
        if t == "/health":
            return self._cmd_health()
        # ── موج ۲: ساختِ اندامِ نو (data-driven، دو-مرحله‌ای، owner-only) ──
        if t.startswith("/neworgan "):
            return self._cmd_neworgan(t[len("/neworgan "):])
        if t.startswith("/organ-approve "):
            return self._cmd_organ_approve(t[len("/organ-approve "):])
        # ── حسابداریِ گفتگومحورِ دونه‌دونه (2026-07-16) ──
        if t == "/review":
            return self._cmd_review_start()
        # ── دفترِ واقعی: صفِ ثبت‌های پیشنهادی + رفرشِ امنِ شبکه (فازِ ۱، 2026-07-16) ──
        if t == "/books":
            return self._cmd_books()
        if t == "/sync":
            return self._cmd_acct_sync()
        # متنِ آزاد فقط وقتی جلسه فعال است و منتظرِ متن → تجزیه به پیشنهاد (نه دستور، نه auto-apply)
        # گیت روی is_active هم هست تا پرچمِ سرگردانِ یک جلسهٔ بسته پیامِ نامرتبط را ندزدهد.
        if not t.startswith("/"):
            # 3a: اگر مالک وسطِ ویرایشِ RFC است، این متن پاسخِ همان RFC است (قبل از حسابدار)
            if self._awaiting_rfc_edit:
                return self._consume_rfc_edit_text(t)
            try:
                import acct_review as _ar
                if _ar.is_active() and _ar.is_awaiting_free():
                    return self._cmd_review_freetext(t)
            except Exception:  # noqa: BLE001 — fail-soft: نبودِ ماژول = نادیده
                pass
        # ── فاز ۲: ادغامِ langarِ Project-F (رأی مالک 2026-07-17) ──
        # دستورهای langar (/pf_*, /saba, /drafts, /dm_*, /fan_*, /vault_*, /guards, /kpi*,
        # /octopus*, /brief, /think, /spine, /upgrade, /gates, /verdicts, /rules, /kill,
        # /revive, /report_*, /clear_*, /set_karma) از همین رباتِ واحد پاسخ می‌گیرند.
        # پلِ additive: langar لمس نمی‌شود؛ فقط .handle() صدا زده می‌شود (OpsecGuard خودکار).
        # هر شکستِ import → نادیده (fail-soft، مثلِ _ar/_jb). ثبتی در ledger فقط برای
        # کارهایِ واقعی (verdict/kpi) داخلِ langar_bridge انجام می‌شود.
        if langar_bridge_dispatch is not None:
            try:
                reply = langar_bridge_dispatch(t, chat_id=chat_id, owner=self._owner)
                if reply is not None:
                    return reply
            except Exception as e:  # noqa: BLE001 — fail-soft: langar نباید ربات را بکشد
                opslib.alert([f"telegram langar_bridge error: {type(e).__name__}: {e}"])
        return None

    # ─── حسابدارِ گفتگومحور (acct_review) — propose-only، پول‌جابه‌جا‌نمی‌کند ───────────
    def _ar(self):
        """import acct_review (lazy، fail-soft → None)."""
        import sys as _s
        legs = str(_HERE.parent / "legs")
        if legs not in _s.path:
            _s.path.insert(0, legs)
        try:
            import acct_review
            return acct_review
        except Exception:  # noqa: BLE001
            return None

    def _cmd_review_start(self):
        ar = self._ar()
        if ar is None:
            return "🧮 حسابدار در دسترس نیست."
        try:
            q = ar.start()
        except Exception as e:  # noqa: BLE001
            return f"🧮 خطا در شروعِ مرور: {type(e).__name__}"
        return self._review_card(q)

    def _review_card(self, q: dict):
        """payloadِ acct_review → (text, inline_keyboard) — نسخهٔ فارسیِ سادهٔ «بی‌اصطلاح»
        (UX-SPEC §۳.۲، 2026-07-18). header به «🟢 ورودی/🔴 خروجی»، دکمه‌های روزمره.
        فقط به مالک؛ صفر دکمهٔ پول. هویتِ txn_id در callback حفظ شده (ضدِ تپِ کارتِ کهنه)."""
        if not isinstance(q, dict):
            return "🧮 چیزی برای مرور نیست."
        kind = q.get("kind")
        if kind in ("empty", "done", "stopped"):
            return "🧮 " + str(q.get("message", "تمام."))
        if kind == "error":
            return "🧮 " + str(q.get("message", "خطا."))
        # question | stale — کارتِ سوال
        g = q.get("guess") or {}
        head = ("⚠️ سوالِ قبلی گذشته بود؛ این یکی:\n" if kind == "stale" else "")
        # sign → ورودی/خروجیِ فارسیِ روزمره (به‌جای «+/-»)
        sign = str(q.get("sign", ""))
        if sign.startswith("+") or sign.lower() in ("in", "credit", "ورودی"):
            flow = "🟢 ورودی (پول اومد)"
        elif sign.startswith("-") or sign.lower() in ("out", "debit", "خروجی"):
            flow = "🔴 خروجی (پول رفت)"
        else:
            flow = sign or "—"
        lines = [head + "🧮 <b>یکی‌دونه باهات چک می‌کنم</b> "
                 f"({q.get('n','?')}/{q.get('total','?')})",
                 f"📅 {html.escape(str(q.get('date','')))} · {flow}",
                 f"💵 <b>{html.escape(str(q.get('amount','?')))}</b> دلار",
                 f"📝 {html.escape(str(q.get('desc','')))}"]
        # حدسِ موتور — فقط اگه چیزی داره
        oc = g.get("owner"); pc = g.get("ptype")
        ofa = g.get("owner_fa"); pfa = g.get("ptype_fa")
        has_guess = bool(oc) and bool(pc) and oc != "unknown" and pc != "unknown"
        if has_guess:
            lines.append(f"🤖 حدسم: {html.escape(str(pfa))}ِ {html.escape(str(ofa))}ه — درسته؟")
        else:
            lines.append("🤖 این یکی رو نمی‌شناسم — مالِ کیه و چیه؟")
        # هویتِ پایدار: idِ همان تراکنش در callback (نه موقعیتِ idx) — ضدِ تپِ کارتِ گذشته
        tid = str(q.get("txn_id", ""))[:32]
        code_o = {"armin": "a", "abbas": "b", "business": "z", "unknown": "u"}.get(oc)
        code_p = {"income": "i", "expense": "e", "wage": "w", "transfer": "t"}.get(pc)
        rows = []
        # دکمهٔ ✅ فقط وقتی حدس هست
        if has_guess and code_o and code_p:
            rows.append([{"text": "✅ آره، درسته",
                          "callback_data": f"rev:a:{tid}:{code_o}:{code_p}"}])
        # دکمه‌های روزمرهٔ ۴ گانهٔ اصلی: خرجِ آرمین/عباس، درآمد، عبور
        rows += [
            [{"text": "💸 خرجِ آرمین", "callback_data": f"rev:a:{tid}:a:e"},
             {"text": "💸 خرجِ عباس", "callback_data": f"rev:a:{tid}:b:e"}],
            [{"text": "💰 درآمدِ آرمین", "callback_data": f"rev:a:{tid}:a:i"},
             {"text": "💰 درآمدِ عباس", "callback_data": f"rev:a:{tid}:b:i"}],
            [{"text": "👷 حقوقِ آرمین", "callback_data": f"rev:a:{tid}:a:w"},
             {"text": "🔄 فقط رد شد", "callback_data": f"rev:a:{tid}:a:t"}],
            [{"text": "✍️ خودم می‌گم", "callback_data": f"rev:f:{tid}"},
             {"text": "⏭ بعداً", "callback_data": f"rev:s:{tid}"},
             {"text": "⏹ بس کن", "callback_data": "rev:x"}],
        ]
        return {"text": "\n".join(lines), "reply_markup": {"inline_keyboard": rows}}

    def _cmd_review_freetext(self, text: str):
        """متنِ آزادِ مالک → پیشنهادِ تأییدشدنی (هرگز auto-apply). روی «نفهمیدم»/«ناقص»
        حالتِ متنِ آزاد باز می‌ماند تا مالک دوباره بنویسد (رفعِ dead-endِ audit)."""
        ar = self._ar()
        if ar is None:
            return None
        try:
            p = ar.parse_free(text)                     # awaiting را اینجا پاک نمی‌کنیم
        except Exception:  # noqa: BLE001
            return "🧮 نتونستم بخونم — دوباره بنویس یا با دکمه‌ها جواب بده."
        if p.get("kind") == "need-clarify":
            return "🧮 " + str(p.get("message", "واضح‌تر بگو.")) + " (هنوز منتظرِ متنم)"
        oc, pc = p.get("owner_code"), p.get("ptype_code")
        if not oc or not pc:                            # نیمه‌فهمیده → متن باز می‌ماند، دوباره بنویس
            return (f"🧮 فهمیدم: {p.get('owner_fa','؟')}/{p.get('ptype_fa','؟')} — "
                    "ناقصه؛ دوباره کامل بنویس (مثلاً «عباس، خرج») یا با دکمه‌ها جواب بده.")
        # پیشنهادِ کامل → حالا حالتِ متنِ آزاد را ببند و کارتِ تأیید با هویتِ تراکنشِ فعلی بده
        q = ar.question()
        if q.get("kind") != "question":
            ar.set_awaiting_free(False)
            return "🧮 چیزی برای تأیید نمانده — /review بزن."
        ar.set_awaiting_free(False)
        tid = str(q.get("txn_id", ""))[:32]
        txt = (f"🧮 پیشنهاد از متنت برای این تراکنش: <b>{html.escape(str(p.get('owner_fa')))}/"
               f"{html.escape(str(p.get('ptype_fa')))}</b> — تأیید کنم؟")
        kb = {"inline_keyboard": [[
            {"text": "✅ تأیید", "callback_data": f"rev:a:{tid}:{oc}:{pc}"},
            {"text": "✍️ دوباره", "callback_data": f"rev:f:{tid}"},
            {"text": "⏭ رد", "callback_data": f"rev:s:{tid}"}]]}
        return {"text": txt, "reply_markup": kb}

    def _dispatch_review(self, parts: list):
        """callbackهای حسابدار: rev:a:<txn_id>:oc:pc (جواب) · rev:f:<txn_id> (متنِ آزاد) ·
        rev:s:<txn_id> (رد) · rev:x (توقف). propose-only — هیچ‌کدام پول جابه‌جا نمی‌کند.
        هویتِ تراکنش (نه موقعیت) در callback است تا تپِ کارتِ گذشته سطرِ اشتباه را عوض نکند."""
        ar = self._ar()
        if ar is None:
            return "نادیده"
        verb = parts[1] if len(parts) > 1 else ""
        try:
            if verb == "a" and len(parts) == 5:
                r = ar.answer(parts[3], parts[4], tid_token=parts[2])
                kind = r.get("kind")
                if kind == "applied":
                    a = r.get("applied", {})
                    nxt = self._review_card(r.get("next", {}))
                    tag = f"ثبت شد: {a.get('owner_fa','')}/{a.get('ptype_fa','')} ✅\n"
                    if isinstance(nxt, dict):
                        nxt["text"] = tag + nxt.get("text", "")
                        return nxt
                    return tag + str(nxt)
                if kind == "vanished":
                    nxt = self._review_card(r.get("next", {}))
                    if isinstance(nxt, dict):
                        nxt["text"] = "این تراکنش دیگر در دیتا نیست — سراغِ بعدی.\n" + nxt.get("text", "")
                        return nxt
                    return "این تراکنش دیگر نیست — " + str(nxt)
                if kind == "save-failed":
                    return "🧮 " + str(r.get("message", "ثبت نشد."))
                if kind == "stale":
                    return self._review_card({**r, "kind": "stale"})
                return self._review_card(r)
            if verb == "f" and len(parts) >= 3:
                ar.set_awaiting_free(True)
                return {"text": "✍️ بنویس (مثلاً: «مالِ عباسه، خرجِ مصالح»). "
                                "مبلغ به هیچ هوشِ ابری نمی‌رود.", "reply_markup": None}
            if verb == "s" and len(parts) >= 3:
                return self._review_card(ar.skip())
            if verb == "x":
                return self._review_card(ar.stop())
        except Exception as e:  # noqa: BLE001
            return f"رد: خطا {type(e).__name__}"
        return "نادیده"

    # ─── /books — صفِ ثبت‌های پیشنهادیِ دفتر (تأییدِ دومِ مالک؛ propose-only تا تأیید) ───
    def _jb(self):
        """import journal_bridge (lazy، fail-soft → None)."""
        import sys as _s
        legs = str(_HERE.parent / "legs")
        if legs not in _s.path:
            _s.path.insert(0, legs)
        try:
            import journal_bridge
            return journal_bridge
        except Exception:  # noqa: BLE001
            return None

    def _cmd_books(self):
        jb = self._jb()
        if jb is None:
            return "📋 ثبتِ نهایی در دسترس نیست."
        try:
            rb = jb.rebuild()                       # idempotent — تصمیم‌های قبلی دست‌نخورده
            plist = jb.pending()
        except Exception as e:  # noqa: BLE001
            return f"📋 خطا در ساختِ صف: {type(e).__name__}"
        if not plist:
            st = jb.stats()
            return (self._hdr("📋 <b>ثبتِ نهایی</b>") + "\n"
                    "چیزی برای ثبتِ نهایی نیست ✅\n"
                    f"تا حالا {st.get('posted', 0)} تا ثبت شده، {st.get('rejected', 0)} تا رد شده.\n"
                    "<i>اول تازه‌ها رو در /review دسته‌بندی کن، بعد این‌جا ثبتِ نهایی می‌شن.</i>")
        head = (f"📋 <b>ثبتِ نهایی</b>: {len(plist)} مورد در انتظار"
                + (f" (+{rb.get('built', 0)} تازه)" if rb.get("built") else "") + "\n\n")
        card = self._books_card(plist[0])
        if isinstance(card, dict):
            card["text"] = head + card["text"]
        return card

    def _books_card(self, p: dict):
        """📋 «ثبتِ نهایی» — نسخهٔ فارسیِ سادهٔ بی‌اصطلاح (UX-SPEC §۳.۴، 2026-07-18).
        حذفِ «ثبتِ دوطرفه»، Dr/Cr، journal_id، tax_code از کاربر. پشتِ پرده، همون double-entry
        می‌شه ولی کاربر فقط «ثبت کن؟» رو می‌بینه. هشدارهای صادق: تکراریِ احتمالی."""
        if not isinstance(p, dict):
            return "📚 پیشنهادی نیست."
        tid = str(p.get("txn_id", ""))
        if len(tid) > 48:
            return "📚 idِ تراکنش برای دکمه بلند است — این مورد را دستی ثبت کن (گزارش به ایجنت)."
        # sign → ورودی/خروجی
        amt = p.get("amount", "?")
        try:
            av = float(amt); flow = "🟢 ورودی" if av >= 0 else "🔴 خروجی"
        except (TypeError, ValueError):
            flow = ""
        # owner/ptype → فارسیِ روزمره
        owner_fa = {"armin": "آرمین", "abbas": "عباس", "business": "بیزنس"}.get(
            str(p.get("owner", "")).lower(), str(p.get("owner", "؟")))
        ptype_fa = {"income": "درآمد", "expense": "خرج", "wage": "حقوق",
                    "transfer": "عبور"}.get(
            str(p.get("ptype", "")).lower(), str(p.get("ptype", "؟")))
        lines = [self._hdr("📋 <b>ثبتِ نهایی</b>"),
                 f"📅 {html.escape(str(p.get('date', '')))}" + (f" · {flow}" if flow else ""),
                 f"💵 <b>{html.escape(str(amt))}</b> دلار",
                 f"📝 {html.escape(str(p.get('desc', '')))}",
                 f"🏷 {ptype_fa}ِ {owner_fa}"]
        if p.get("note"):
            lines.append("⚠️ " + html.escape(str(p.get("note"))[:160]))
        if p.get("possible_dup_of"):
            lines.append("⚠️ شاید قبلاً ثبت شده — اگه جداست، ثبت کن؛ وگرنه رد.")
        # gst_pending: اطلاعِ صادقانه ولی به‌زبانِ ساده (نه «tax_code» / «RD-002»)
        if p.get("gst_pending"):
            lines.append("<i>مالیاتِ این مورد رو بعداً با حسابدار مشخص می‌کنیم.</i>")
        kb = {"inline_keyboard": [
            [{"text": "✅ ثبت کن", "callback_data": f"jrn:a:{tid}"},
             {"text": "❌ رد", "callback_data": f"jrn:r:{tid}"}],
            [{"text": "⏭ بعداً", "callback_data": f"jrn:n:{tid}"},
             {"text": "🏠 منو", "callback_data": "menu:main"}],
        ]}
        return {"text": "\n".join(lines), "reply_markup": kb}

    def _dispatch_books(self, parts: list):
        """jrn:a:<tid> ثبت · jrn:r:<tid> رد · jrn:n:<tid> بعدی. هویت با txn_id —
        تپِ کارتِ کهنه/تکراری = «قبلاً تصمیم‌گرفته» (هرگز ثبتِ دوباره؛ ikey=txn-<id>)."""
        jb = self._jb()
        if jb is None:
            return "نادیده"
        verb = parts[1] if len(parts) > 1 else ""
        tid = parts[2] if len(parts) > 2 else ""
        try:
            if verb == "a" and tid:
                r = jb.apply(tid, actor="owner")
                if not r.get("ok"):
                    msg = "📚 ثبت نشد: " + "؛ ".join(str(e) for e in r.get("errors", ["خطا"]))[:180]
                    if r.get("stale"):
                        # کارت کهنه بود — کارتِ تازه را نشان بده (اگر هنوز proposed است)
                        p = jb.get(tid)
                        if isinstance(p, dict) and p.get("status") == "proposed":
                            card = self._books_card(p)
                            if isinstance(card, dict):
                                card["text"] = msg + "\n\n" + card["text"]
                                return card
                    return msg
                tag = f"✅ ثبت شد.\n"
                if r.get("duplicate"):
                    tag = "✅ قبلاً ثبت شده بود.\n"
                if r.get("warn"):
                    tag += "⚠️ " + html.escape(str(r["warn"])) + "\n"
                nxt = jb.pending()
                if nxt:
                    card = self._books_card(nxt[0])
                    if isinstance(card, dict):
                        card["text"] = tag + "\n" + card["text"]
                        return card
                    return tag + str(card)
                return tag + "\n🎉 همه‌چیز ثبت شد! وضعیت رو در /finance ببین."
            if verb == "r" and tid:
                rr = jb.reject(tid, reason="owner-reject")
                if not rr.get("ok"):
                    return "📋 رد نشد: " + "؛ ".join(str(e) for e in rr.get("errors", ["خطا"]))[:120]
                nxt = jb.pending()
                return (self._books_card(nxt[0]) if nxt
                        else "❌ رد شد. چیزی برای ثبت نیست.")
            if verb == "n" and tid:
                # چرخشِ واقعی (audit #33): موردِ بعد از tid در ترتیب؛ آخرِ لیست → برگرد اول
                plist = jb.pending()
                if not plist:
                    return "📋 چیزی برای ثبت نیست."
                ids = [str(p.get("txn_id")) for p in plist]
                i = ids.index(tid) if tid in ids else -1
                nxt = plist[(i + 1) % len(plist)]
                return self._books_card(nxt)
        except Exception as e:  # noqa: BLE001
            return f"رد: خطا {type(e).__name__}"
        return "نادیده"

    def _cmd_acct_sync(self):
        """🔄 «تازه‌ها اومدن» — نسخهٔ فارسیِ سادهٔ بی‌اصطلاح (UX-SPEC §۳.۳، 2026-07-18).
        رفرشِ امنِ شبکه: pull خام → شواهدِ immutable → attribute با **حفظِ تأییدهای مالک**
        → بازسازیِ صفِ ثبت. read-only نسبت به بانک (GET) — تنها استثنا: write-backِ برچسبِ
        دسته‌بندی به PocketSmith پشتِ فلگِ OCTOPUS_WIRE_PS_WRITEBACK (RD-004، فقط labels).
        جزئیاتِ فنی (شواهدِ خام، تأییدهای برگردانده‌شده، صفِ ثبت) از چت حذف شده — برای لاگ، نه کاربر."""
        import sys as _s
        legs = str(_HERE.parent / "legs")
        if legs not in _s.path:
            _s.path.insert(0, legs)
        out = ["🔄 <b>تازه‌ها رو گرفتم</b>"]
        new_count = 0      # برای نمایشِ «+N تازه»
        sync_ok = False
        max_date = ""
        writeback_written = 0
        writeback_kept = 0
        writeback_403 = False
        writeback_note = ""
        total = 0
        needs_review = 0
        # ۱) **یک** fetch (اسکن #48: دو pullِ جدا = دو snapshotِ ناهم‌زمان → شواهد≠store)
        rows = None
        fetch_err = None
        try:
            import pocketsmith_api, raw_store  # noqa: WPS433
            if pocketsmith_api._flag_on() if hasattr(pocketsmith_api, "_flag_on") \
                    else os.environ.get("OCTOPUS_WIRE_POCKETSMITH") == "1":
                raw = pocketsmith_api.fetch_transactions("2025-12-08", None)
                if isinstance(raw, dict) and raw.get("ok") is False:
                    fetch_err = "partial"
                    rows = None
                else:
                    rows = raw.get("transactions", []) if isinstance(raw, dict) else raw
                    ri = raw_store.ingest("pocketsmith", "anz-main", rows or [])
                    new_count = ri.get("ingested", 0)
            else:
                fetch_err = "flag_off"
        except Exception as e:  # noqa: BLE001
            fetch_err = type(e).__name__
        # ۲) شبکه با حفظِ تأییدها — از **همان** fetch (بدونِ pullِ دوم)
        try:
            import accountant  # noqa: WPS433
            sn = accountant.sync_network(api_raw=rows)
            if sn.get("ok"):
                sync_ok = True
                c = sn.get("counts") or {}
                total = sn.get("unique", 0)
                needs_review = c.get("needs_review", 0)
                # آخرین تاریخ از store برای نمایشِ «تا YYYY-MM-DD»
                try:
                    import txn_store  # noqa: WPS433
                    txns = txn_store.load_all()
                    if txns:
                        max_date = max((t.get("date", "") for t in txns
                                        if isinstance(t, dict) and t.get("date")), default="")
                except Exception:  # noqa: BLE001
                    pass
                psw = sn.get("ps_writeback") or {}
                writeback_written = psw.get("written", 0)
                writeback_kept = psw.get("kept", 0)
                writeback_note = str(psw.get("note", "") or "")
                # تشخیصِ 403 (کلیدِ فقط‌خواندنی) از note
                if "403" in writeback_note or "read-only" in writeback_note.lower() \
                        or "full-access" in writeback_note.lower():
                    writeback_403 = True
            else:
                fetch_err = html.escape(str(sn.get("error", "?")))
        except Exception as e:  # noqa: BLE001
            fetch_err = type(e).__name__
        # ۳) صفِ ثبتِ دفتر (داده جمع می‌شه ولی در چت نشون داده نمی‌شه — جزئیات فنی)
        jb = self._jb()
        pending_books = 0
        if jb is not None:
            try:
                rb = jb.rebuild()
                pending_books = rb.get("pending", 0)
            except Exception:  # noqa: BLE001
                pass
        # ── خلاصهٔ فارسیِ سادهٔ نهایی (UX-SPEC §۳.۳) ──
        out = ["🔄 <b>تازه‌ها رو گرفتم</b>"]
        if fetch_err == "flag_off":
            out.append("⚪ PocketSmith خاموشه (فلگ روشن نیست).")
            out.append("<i>فعال‌سازی: OCTOPUS_WIRE_POCKETSMITH=1</i>")
        elif fetch_err == "partial":
            out.append("⚠️ گرفتنِ تازه‌ها ناقص بود — دوباره /sync بزن.")
        elif fetch_err:
            out.append(f"⚠️ خطا در گرفتنِ تازه‌ها: <code>{fetch_err}</code>")
        if sync_ok:
            out.append(f"✅ تا {html.escape(max_date) if max_date else 'الان'}: "
                       f"<b>{total}</b> تراکنش")
            if new_count > 0:
                out.append(f"➕ <b>{new_count}</b> تا تازه داشتی.")
            else:
                out.append("تازه‌ای نداشتی.")
            # writeback: فقط اگه واقعاً چیزی نوشته یا 403 خورده
            if writeback_written > 0:
                out.append(f"💾 {writeback_written} دسته‌بندیِ تأییدشده‌ت رو تو پاکت‌اسمیت هم ذخیره کردم.")
            elif writeback_403:
                out.append("⚠️ نتونستم تو پاکت‌اسمیت ذخیره کنم — کلیدِ دسترسیِ کامل لازمه.")
                out.append("<i>(دسته‌بندی‌ها این‌جا ذخیره شدن، فقط سینکِ دوطرفه نیازه.)</i>")
            elif writeback_kept > 0:
                out.append(f"⏳ {writeback_kept} مورد منتظرِ ذخیره‌سازی در پاکت‌اسمیت.")
        # پیشنهادِ ادامه
        if needs_review > 0 and sync_ok:
            out.append("")
            out.append(f"🧮 <b>{needs_review}</b> موردِ بدونِ دسته مانده.")
            out.append("یکی‌یکی باهات چک می‌کنم؟")
            out.append("<i>🟢 هیچ پولی جابه‌جا نمی‌شه — فقط دسته‌بندی.</i>")
            return {"text": "\n".join(out),
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "🧮 آره، شروع کن", "callback_data": "acct:review"},
                        {"text": "📊 وضعِ من", "callback_data": "menu:finance"},
                        {"text": "🏠 منو", "callback_data": "menu:main"}]]}}
        # اگه صفِ مرور خالیه
        if sync_ok:
            out.append("")
            out.append("همه‌چیز دسته‌بندی شده ✅")
        return {"text": "\n".join(out),
                "reply_markup": {"inline_keyboard": [[
                    {"text": "📊 وضعِ من", "callback_data": "menu:finance"},
                    {"text": "🏠 منو", "callback_data": "menu:main"}]]}}

    def _dispatch_acct(self, parts: list):
        """میان‌بُرهای دکمه‌ایِ حسابداری (اسکن #34/#35): acct:review/books/sync →
        همان handlerهای دستوری (owner-only از قبل در poll_once، propose-only).
        2026-07-18: acct:finance_expert → نسخهٔ expert (مالک/توسعه‌دهنده)."""
        verb = parts[1] if len(parts) > 1 else ""
        if verb == "review":
            return self._cmd_review_start()
        if verb == "books":
            return self._cmd_books()
        if verb == "sync":
            return self._cmd_acct_sync()
        if verb == "finance_expert":
            return {"text": self._finance_text_expert(),
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "📊 نسخهٔ ساده", "callback_data": "menu:finance"},
                        {"text": "🏠 منو", "callback_data": "menu:main"}]]}}
        return "نادیده"

    # ─── موج ۲: ساختِ اندامِ نو — فقط نوشتنِ رجیستریِ داده (هرگز کدِ تولید) ──────────────
    def _organ_registry_path(self):
        from pathlib import Path as _P
        sd = _P(self._state_dir) if self._state_dir else (_P(__file__).resolve().parents[1] / "state")
        return sd / "organ-registry.json"

    def _read_organ_registry(self) -> list:
        import json as _json
        p = self._organ_registry_path()
        try:
            if p.exists():
                d = _json.loads(p.read_text("utf-8"))
                return d.get("organs", []) if isinstance(d, dict) else []
        except (OSError, ValueError):
            pass
        return []

    @staticmethod
    def _organ_slug(name: str) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")
        return s[:32]

    def _cmd_neworgan(self, arg: str):
        """قدمِ ۱: پیشنهادِ اندامِ نو (فقط pending؛ هیچ نوشتنِ رجیستری). نامِ نمایشیِ آزاد، slug مشتق."""
        import json as _json
        name = str(arg or "").strip()[:60]
        if len(name) < 2:
            return "نام کوتاه است. مثال: <code>/neworgan فروشگاه ووکامرس</code>"
        slug = self._organ_slug(name)
        if not slug:
            return "نامِ نامعتبر (باید حرف/عددِ لاتین در slug بسازد؛ یک نامِ لاتین‌دار بده)."
        if slug in {o.get("key") for o in self._read_organ_registry()} or \
                slug in {k for k, *_ in self.ORGANS}:
            return f"اندامِ «{html.escape(slug)}» از قبل هست."
        try:
            pdir = self._organ_registry_path().parent / "organ-proposals"
            pdir.mkdir(parents=True, exist_ok=True)
            (pdir / f"{slug}.json").write_text(_json.dumps(
                {"key": slug, "label": name, "live": False, "kind": "custom",
                 "note": "اسکلتِ owner-ساخت (propose-only، بی‌پول)",
                 "proposed_at": _today_iso(), "status": "proposed"}, ensure_ascii=False), "utf-8")
        except OSError as e:  # noqa: BLE001
            return f"❌ ثبتِ پیشنهاد ناموفق: {type(e).__name__}"
        return (f"🆕 <b>اندامِ نو پیشنهاد شد</b>\n"
                f"نام: {html.escape(name)} · کلید: <code>{html.escape(slug)}</code>\n"
                f"{self._DIV.strip()}\n"
                f"اسکلتِ propose-only (read-only، بی‌پول، live=false). برای ساخت بنویس:\n"
                f"<code>/organ-approve {html.escape(slug)}</code>")

    def _cmd_organ_approve(self, arg: str):
        """قدمِ ۲: تأییدِ owner → افزودنِ پیشنهاد به رجیستریِ دادهٔ state/organ-registry.json.
        هیچ کدِ تولید نوشته نمی‌شود؛ فقط یک ورودیِ داده (append، بدونِ حذف)."""
        import json as _json
        import os as _os
        slug = self._organ_slug(arg)
        pp = self._organ_registry_path().parent / "organ-proposals" / f"{slug}.json"
        if not pp.exists():
            return f"پیشنهادی برای «{html.escape(slug)}» نیست. اول <code>/neworgan &lt;نام&gt;</code>."
        try:
            entry = _json.loads(pp.read_text("utf-8"))
        except (OSError, ValueError):
            return "❌ پیشنهادِ ناخوانا."
        organs = self._read_organ_registry()
        if any(o.get("key") == slug for o in organs):
            return f"«{html.escape(slug)}» از قبل در رجیستری است."
        entry["status"] = "active"
        entry["approved_at"] = _today_iso()
        organs.append(entry)
        try:
            rp = self._organ_registry_path()
            tmp = rp.with_suffix(".json.tmp")
            tmp.write_text(_json.dumps({"schema": "organ-registry.v1", "organs": organs},
                                       ensure_ascii=False, indent=1), "utf-8")
            _os.replace(tmp, rp)
            pp.unlink()
        except OSError as e:  # noqa: BLE001
            return f"❌ نوشتنِ رجیستری ناموفق: {type(e).__name__}"
        self._append_request("organ-create", slug)      # auditِ append-only
        return (f"✅ <b>اندام ساخته شد</b>: {html.escape(entry.get('label', slug))} "
                f"(<code>{html.escape(slug)}</code>)\n"
                f"در تبِ 🦾 اندام‌ها به‌عنوان اسکلت (⚪ live=false) دیده می‌شود تا دادهٔ واقعی وصل شود.\n"
                f"<i>هیچ کدِ تولید نوشته نشد — فقط یک ورودیِ رجیستریِ داده.</i>")

    # ─── کابینِ راست‌گو: /wiring + /health (read-only، هرگز stale/بی‌نویسنده را سبز نشان نمی‌دهد) ──
    def _cmd_wiring(self) -> str:
        """نقشهٔ اتصال‌ها از truth-cards: هر جزء با آیکنِ صادق (🟢 تازه · 🟠 کهنه · ⚫ غایب/فلگ-خاموش).
        قانون: 🟢 فقط برای فایلِ موجودِ تازه؛ هیچ پیش‌فرضِ کدی «زنده» جا نمی‌زند."""
        rm = self._rm()
        if rm is None:
            return "🔌 <b>اتصال‌ها</b>\n(read-model در دسترس نیست)"
        try:
            cards = rm.read_truth_cards()
        except Exception as e:  # noqa: BLE001 — fail-soft
            return f"🔌 <b>اتصال‌ها</b>\n❌ خطا: {type(e).__name__}"
        lines = ["🔌 <b>نقشهٔ اتصال‌ها</b> (راست‌گو)", self._DIV.strip()]
        for c in cards:
            flag = f" · <code>{c['flag']}</code>" if c.get("flag") else ""
            fo = ""
            if c.get("flag"):
                fo = " (فلگ روشن)" if c.get("flag_on") else " (فلگ خاموش)"
            lines.append(f"{c['icon']} <b>{html.escape(str(c['label']))}</b> — "
                         f"{html.escape(str(c['status']))}{fo}{flag}")
        n_green = sum(1 for c in cards if c["icon"] == "🟢")
        lines.append(self._DIV.strip())
        lines.append(f"🟢 تازه: {n_green} · 🟠 کهنه/⚫ غایب: {len(cards) - n_green}")
        lines.append("<i>سبز فقط برای فایلِ موجودِ تازه — snapshotِ کهنه یا بی‌نویسنده هرگز سبز نیست.</i>")
        return "\n".join(lines)

    def _cmd_health(self) -> str:
        """سلامتِ راست‌گو: قلبِ shadow (تازگیِ واقعی)، capability marker، گیتِ پول، halt."""
        rm = self._rm()
        cards = {}
        if rm is not None:
            try:
                cards = {c["id"]: c for c in rm.read_truth_cards()}
            except Exception:  # noqa: BLE001
                cards = {}
        heart = cards.get("heart_shadow", {})
        heart_line = f"{heart.get('icon', '❔')} {heart.get('status', '?')}" if heart else "❔"
        # capability marker + گیتِ پول از فایل (نه پیش‌فرض)
        from pathlib import Path as _P
        sd = _P(self._state_dir) if self._state_dir else (_P(__file__).resolve().parents[1] / "state")
        cap = "🟢 معتبر" if (sd / "CAPABILITY-OK.flag").exists() else "🔴 غایب"
        money = ("🔓 مسلح" if (sd / "LIVE-ENABLED.flag").exists()
                 else "🔒 بسته (LIVE-ENABLED نیست — paper، عمدی)")
        try:
            halt = "🔴 HALT فعال" if (opslib.STOP_ORGANISM.exists() or opslib.halted()) else "🟢 در حال اجرا"
        except Exception:  # noqa: BLE001
            halt = "❔"
        # صداقتِ GO-LIVE (2026-07-16): کدام گیت‌های ACTIVATION مسلح‌اند — از فایل، نه ادعا.
        # هیچ سطحِ کابین این را نشان نمی‌داد؛ ۹ فلگِ مسلح از 07-10 نامرئی بودند.
        try:
            gates = sorted(p.name for p in opslib.OPS.glob("ACTIVATION-*.flag"))
        except Exception:  # noqa: BLE001
            gates = []
        gate_names = "، ".join(g[len("ACTIVATION-"):-len(".flag")] for g in gates)
        gates_line = (f"گیت‌های مسلح: {len(gates)}"
                      + (f" — {html.escape(gate_names)}" if gates else " (هیچ ACTIVATION-فلگی نیست)"))
        return (f"🫀 <b>سلامتِ اختاپوس</b> · {self._read_mode_color()}\n"
                f"{self._DIV.strip()}\n"
                f"قلب (shadow): {heart_line}\n"
                f"Capability marker: {cap}\n"
                f"گیتِ پول: {money}\n"
                f"{gates_line}\n"
                f"وضعیتِ توقف: {halt}\n"
                f"{self._DIV.strip()}\n"
                f"<i>سلامتِ کاملِ تست‌ها: run_all (۱۳۷) + validators جدا اجرا می‌شوند.</i>")

    # ─── Task 3 (2026-07-24) · دیالوگِ owner↔organ (Doctor/Brains/Hearts) ─────────
    def _organ_dialogue(self):
        """ماژولِ مشترکِ رندر/persistِ دیالوگ (lazy، fail-soft → None)."""
        try:
            import sys as _sys
            from pathlib import Path as _P
            _ops = str(_P(__file__).resolve().parents[1])
            if _ops not in _sys.path:
                _sys.path.insert(0, _ops)
            import organ_dialogue as _od
            return _od
        except Exception:  # noqa: BLE001
            return None

    def _dlg_state_dir(self):
        from pathlib import Path as _P
        return _P(self._state_dir) if self._state_dir else None

    def _cmd_heart(self):
        """/heart — کارتِ فقط‌خواندنیِ قلب (همان رندرِ heart_card_beat)."""
        _od = self._organ_dialogue()
        if _od is None:
            return "🫀 ماژولِ دیالوگ در دسترس نیست."
        try:
            d = _od.heart_digest(state_dir=self._dlg_state_dir())
            return {"text": d["text"], "reply_markup": {"inline_keyboard": [[
                {"text": "📊 وضعیت", "callback_data": "menu:overview"},
                {"text": "🏠 منو", "callback_data": "menu:main"}]]}}
        except Exception as e:  # noqa: BLE001
            return f"🫀 خطا در گزارشِ قلب: {type(e).__name__}"

    def _cmd_heart_set(self, arg: str):
        """/heart set <param> <value> — قدمِ ۱: preview + کارتِ confirmِ توکن‌دار.
        نوشتنِ واقعی فقط بعد از تپِ مالک (act:heartset، INV-13 تک‌مصرف + owner-gate)
        و فقط از راهِ HeartParams.validate() — ADR-001: هرگز period/rate."""
        _od = self._organ_dialogue()
        if _od is None:
            return "🫀 ماژولِ دیالوگ در دسترس نیست."
        parts = str(arg or "").split()
        if len(parts) != 2:
            return ("🫀 فرمت: <code>/heart set &lt;param&gt; &lt;value&gt;</code>\n"
                    "پارامترها: sigma · lo · hi · cap · baro (فقط setpoint — هرگز period)")
        try:
            pv = _od.heart_set_preview(parts[0], parts[1], state_dir=self._dlg_state_dir())
        except Exception as e:  # noqa: BLE001
            return f"🫀 خطا در preview: {type(e).__name__}"
        if not pv.get("ok"):
            return "⛔ رد شد:\n" + "\n".join(
                f"• {html.escape(str(x))}" for x in pv.get("errs") or [])
        canon = pv["param"]
        # C4 (الگوی flaggo): مقدارِ مطلق در mintِ توکن ذخیره می‌شود — کارتِ کهنه مقدارِ کهنه
        tok = self._new_act_token("heartset", canon, target=pv["new"])
        btn = {"text": f"✅ اعمالِ {canon} → {pv['new']}",
               "callback_data": f"act:heartset:{canon}:{tok}"}
        return {"text": (f"🫀 <b>تنظیمِ setpointِ قلب</b>\n"
                         f"{canon}: <code>{html.escape(str(pv['old']))}</code> → "
                         f"<code>{html.escape(str(pv['new']))}</code>\n"
                         f"epoch فعلی {pv.get('epoch_now')} — با اعمال، epochِ نو "
                         "atomic/audited/برگشت‌پذیر نوشته می‌شود.\nمطمئنی؟"),
                "reply_markup": {"inline_keyboard": [[btn,
                    {"text": "❌ انصراف", "callback_data": "menu:main"}]]}}

    def _act_heartset(self, key: str, target=None) -> str:
        """قدمِ ۲ (تپِ توکن‌دارِ مالک): اعمالِ setpoint از راهِ HeartParams.validate."""
        _od = self._organ_dialogue()
        if _od is None:
            return "🫀 ماژولِ دیالوگ در دسترس نیست."
        if target is None:
            return "⛔ مقدارِ هدف گم شد — دوباره /heart set بزن."
        try:
            r = _od.heart_set_apply(key, target, state_dir=self._dlg_state_dir())
        except Exception as e:  # noqa: BLE001
            return f"🫀 اعمال شکست: {type(e).__name__}"
        if not r.get("ok"):
            return "⛔ رد شد:\n" + "\n".join(f"• {str(x)[:120]}" for x in r.get("errs") or [])
        return (f"✅ setpoint نوشته شد: {r['param']} {r['old']}→{r['new']} "
                f"(epoch {r['epoch_seq']}؛ audit: pulse/heart-setpoint-audit.jsonl)")

    def _cmd_doctor_focus(self, arg: str):
        _od = self._organ_dialogue()
        if _od is None:
            return "🩺 ماژولِ دیالوگ در دسترس نیست."
        r = _od.save_owner_focus(arg, state_dir=self._dlg_state_dir())
        if not r.get("ok"):
            return f"⛔ ثبت نشد: {r.get('error')}"
        return (f"🎯 steering ثبت شد: «{html.escape(str(r['focus']))}» — دکتر در cycleِ بعد "
                "mine/self-knowledge را با این سوگیری اجرا می‌کند (فقط اولویت، نه فرمان).")

    def _cmd_doctor_edit(self, arg: str):
        """/doctor edit <RFC-id> <متن> — بازنگریِ one-shot (دکمهٔ ✍️ کارت هم هست)."""
        _od = self._organ_dialogue()
        if _od is None:
            return "🩺 ماژولِ دیالوگ در دسترس نیست."
        parts = str(arg or "").split(None, 1)
        if len(parts) != 2:
            return "🩺 فرمت: <code>/doctor edit RFC-xxxxxxxx متنِ بازنگری</code>"
        r = _od.save_rfc_revision(parts[0], parts[1], state_dir=self._dlg_state_dir())
        if not r.get("ok"):
            return f"⛔ ثبت نشد: {r.get('error')}"
        return (f"✍️ بازنگری برای <code>{html.escape(str(r['rfc_id']))}</code> صف شد — "
                "دکتر در cycleِ بعد در متنِ RFC ادغام و اعلام می‌کند.")

    def _cmd_brain_guide(self, arg: str):
        _od = self._organ_dialogue()
        if _od is None:
            return "🧠 ماژولِ دیالوگ در دسترس نیست."
        r = _od.brain_guide(arg, state_dir=self._dlg_state_dir())
        if not r.get("ok"):
            return (f"⛔ ثبت نشد: {html.escape(str(r.get('error')))}\n"
                    "<i>bounded: focus:&lt;متن&gt; · think_every_n:N (۱..۱۰۰) · "
                    "pause: think · resume: think</i>")
        return ("🧭 راهنماییِ مغز ثبت شد: <code>"
                + html.escape(json.dumps(r.get("directive"), ensure_ascii=False))
                + "</code>\ncortex در ابتدای cycleِ بعدی (state-file خوان؛ بدونِ pollerِ نو) اعمالش می‌کند.")

    def _consume_rfc_edit_text(self, text: str):
        """متنِ آزادِ مالک بعد از [✍️ ویرایش] → صفِ بازنگریِ همان RFC."""
        rfc_id, self._awaiting_rfc_edit = self._awaiting_rfc_edit, None
        _od = self._organ_dialogue()
        if _od is None or not rfc_id:
            return "🩺 ماژولِ دیالوگ در دسترس نیست."
        r = _od.save_rfc_revision(rfc_id, text, state_dir=self._dlg_state_dir())
        if not r.get("ok"):
            return f"⛔ ثبت نشد: {r.get('error')} — دوباره دکمهٔ ✍️ را بزن."
        return (f"✍️ بازنگری برای <code>{html.escape(str(rfc_id))}</code> ثبت شد — "
                "دکتر در cycleِ بعد ادغام می‌کند.")

    def _main_menu(self) -> dict:
        """خانهٔ اصلی (جلسه ۴۶، رأی مالک «فقط آره یا نه»): خانهٔ سادهٔ تصمیم‌ها.
        عمقِ کاملِ ۸-تب دست‌نخورده زیرِ «⚙️ بیشتر» (backward-compat کامل)."""
        return self._simple_home()

    def _read_mode_color(self) -> str:
        """رنگِ حالت از Chrono-Rhythm (§۳). fallback STEADY/🟢."""
        try:
            import sys as _sys
            from pathlib import Path as _P
            _here = _P(__file__).resolve().parents[0]   # budget
            _ops = _here.parent                          # _ops
            if str(_ops / "chrono_rhythm") not in _sys.path:
                _sys.path.insert(0, str(_ops / "chrono_rhythm"))
            from rhythm import Rhythm
            rh = Rhythm()
            rh.step(readiness=0.6, stress=0.2, novelty=0.3, sigma=0.5)
            s = rh.state
            icons = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
            return f"{icons.get(s.mode_color, '🟢')} {s.mode_color} · {s.mode_focus}"
        except Exception:  # noqa: BLE001 — fallback
            return "🟢 GREEN · STEADY"

    def status_report_v2(self) -> str:
        """UX v2 §۲: وضعیتِ غنی با HTML، رنگِ mode، خط‌جداکننده."""
        from pathlib import Path
        state_dir = Path(self._state_dir) if self._state_dir else (
            Path(__file__).resolve().parents[1] / "state")
        org = _read_json_safe(state_dir / "ORGANISM-STATE.json")
        mode = self._read_mode_color()
        if not org:
            return (f"🐙 <b>اختاپوس</b> · {mode}\n"
                    f"──────────\n"
                    f"<i>هنوز روشن نشده.</i>\n"
                    f"روشن‌کردن: <code>_ops\\RUN-ORGANISM.bat</code>")
        month = org.get("month") or {}
        today = org.get("today") or {}
        conflicts = org.get("conflicts") or []
        lag = org.get("germline_lag_h", "—")
        lag_alert = org.get("germline_alert", "")
        lag_mark = "🔴" if lag_alert == "ERROR" else ("🟡" if lag_alert == "warn" else "🟢")
        sigma = self._read_sigma()
        n_pending = self._count_pending()
        return (f"🐙 <b>اختاپوس</b> · {mode}\n"
                f"──────────\n"
                f"💵 خرج: امروز US${_safe_float(today.get('usd')):.4f} · "
                f"ماه AU${_safe_float(month.get('aud')):.2f}\n"
                f"📊 σ {sigma} · تعارض {len(conflicts)}\n"
                f"💾 germline: {lag_mark} {lag}h · 📥 صفِ تأیید: {n_pending}\n"
                f"<i>فقط‌خواندنی — این دستور هیچ‌چیزی تغییر نمی‌دهد.</i>")

    def _count_pending(self) -> int:
        with self._lk:
            return sum(1 for m in self._pending.values() if m.get("status") == "pending")

    def _cmd_lead_prompt(self) -> str:
        """راهنمای /lead: فرمت + دکمه‌های انتخابِ پا. mirrorِ panel/server.py."""
        opts = " | ".join(f"{lbl} (<code>{c}</code>)" for c, lbl in self.LEAD_CELLS)
        return (f"📝 <b>ثبتِ لید جدید</b>\n\n"
                f"فرمت:\n<code>/lead نام لید | ارزشِ تخمینی AUD | پا</code>\n\n"
                f"پاها: {opts}\n\n"
                f"<i>مثال: <code>/lead بازسازی آشپزخانه | 5000 | lead.doer</code></i>\n"
                f"<i>فقط ثبتِ فرصت (PROPOSAL) — تأییدِ پول از reconcile می‌آید.</i>")

    def _cmd_lead_parse(self, raw: str) -> str:
        """پارسِ /lead و فراخوانیِ attribution.propose. ورودی نامعتبر → پیامِ خطا (fail-closed)."""
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 2:
            return "⚠ فرمت ناقص. مثال: <code>/lead نام | ارزش AUD | پا</code>"
        lead_name = parts[0]
        try:
            exp = float(parts[1])
        except ValueError:
            return "⚠ ارزشِ تخمینی باید عدد باشد (AUD)."
        if exp < 0:
            return "⚠ ارزشِ تخمینی منفی نمی‌شود."
        cell = parts[2] if len(parts) >= 3 else self.LEAD_CELLS[0][0]
        if cell not in {c for c, _ in self.LEAD_CELLS}:
            cell = self.LEAD_CELLS[0][0]
        # W-3: اگر پای Lead تزریق شده (leg=)، intake از خودِ پا (قراردادِ lead_leg.intake:
        # فقط PROPOSAL mint می‌کند — نه پول، نه ارسال). هر خطا/ناموفق → fail-soft:
        # alert + سقوط به مسیرِ موجودِ _attribution_propose. leg=None → رفتارِ قبلی byte-identical.
        if self._leg is not None:
            try:
                res = self._leg.intake(lead_name, exp, cell=cell)
            except Exception as e:  # noqa: BLE001 — پای خراب نباید UIِ مالک را بکشد
                opslib.alert([f"telegram /lead leg intake error: {type(e).__name__}: {e}"])
                res = None
            if isinstance(res, dict) and res.get("ok"):
                aid = res.get("attribution_id", "?")
                return (f"✅ <b>لید ثبت شد</b>\n\n"
                        f"کد: <code>{html.escape(str(aid))}</code>\n"
                        f"این را روی کوت/فاکتور بنویس.\n"
                        f"<i>وضعیت: PROPOSAL — پول بعداً از reconcile تأیید می‌شود.</i>")
        try:
            rec = _attribution_propose(cell, exp, lead=lead_name)
        except Exception:  # noqa: BLE001 — fail-closed، هیچ نیمه‌ثبتی
            return "❌ ثبت نشد (خطای داخلی)."
        aid = (rec.get("payload") or {}).get("attribution_id", "?") if isinstance(rec, dict) else "?"
        return (f"✅ <b>لید ثبت شد</b>\n\n"
                f"کد: <code>{html.escape(str(aid))}</code>\n"
                f"این را روی کوت/فاکتور بنویس.\n"
                f"<i>وضعیت: PROPOSAL — پول بعداً از reconcile تأیید می‌شود.</i>")

    # ─── T-4 · lab N=1: /start_exp, /reveal (seal/SHA256، no-early-decode) ────────
    LAB_SEED_PATH = "lab_seed_data.json"

    def _load_lab_seed(self) -> dict:
        """بارگذاریِ lab_seed_data.json. مسیر: ابتدا state_dirِ تزریقی (اگر ست شده)،
        بعد کنارِ این ماژول (state/)، سپس CHRONOS-FABLE-OS/09_Research/.
        فقط‌خواندنی؛ هرگز نوشته نمی‌شود. بدونِ کاندیدِ state_dir، تستِ worktree
        seed را از درختِ ماژول می‌خواند نه از mini-vaultِ harness (نشتِ state زنده)."""
        from pathlib import Path
        here = Path(__file__).resolve().parents[1]   # _ops
        candidates = [
            here / "state" / self.LAB_SEED_PATH,
        ]
        if self._state_dir:
            candidates.insert(0, Path(self._state_dir) / self.LAB_SEED_PATH)
        candidates += [
            here.parent / "CHRONOS-FABLE-OS" / "09_Research" / self.LAB_SEED_PATH,
            here.parent / "CHRONOS-FABLE-OS" / "01_SourceMap" / "_primaries" / "from-vault" / self.LAB_SEED_PATH,
        ]
        for p in candidates:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
        return {}

    def start_experiment(self, exp_id: str) -> str:
        """/start_exp<N>: تقویمِ ۱۴روزه را تولید و قفل می‌کند. exp2 از random.seed ثابت.
        prediction (b64) هرگز در این مرحله decode نمی‌شود — فقط sha256 ذخیره می‌شود."""
        seed = self._load_lab_seed()
        exps = {e["id"]: e for e in seed.get("experiments", []) if "id" in e}
        exp = exps.get(exp_id)
        if exp is None:
            return f"⚠ آزمایشِ <code>{html.escape(exp_id)}</code> یافت نشد."
        today = _today_str()
        end_date = _add_days(today, exp.get("duration_days", 14))
        # exp2: تقویمِ تناوب A/B با seed ثابت (قابلِ بازتولید)
        calendar = []
        if exp_id == "exp2":
            import random
            rng = random.Random(20260708)   # seed ثابت (حذفِ سوگیریِ انتخاب)
            gestures = ["GESTURE_A", "GESTURE_B"]
            # هفتهٔ ۱: فقط A؛ هفتهٔ ۲: تناوبِ random با حداقل ۳ روز برای هرکدام
            for d in range(1, 8):
                calendar.append({"day": d, "protocol": "GESTURE_A"})
            w2 = [rng.choice(gestures) for _ in range(8, 15)]
            # تضمینِ حداقل ۳ از هرکدام
            if w2.count("GESTURE_A") < 3:
                w2 = ["GESTURE_A"] * 3 + ["GESTURE_B"] * 3 + w2[6:]
            for i, g in enumerate(w2, start=8):
                calendar.append({"day": i, "protocol": g})
        else:
            # exp1/exp3: زوج/فرد طبقِ schedule_rule
            for d in range(1, exp.get("duration_days", 14) + 1):
                if exp_id == "exp1":
                    proto = "P_FORCE" if d % 2 == 0 else "P_IMAGE"
                else:  # exp3
                    proto = "STRAT_A" if d % 2 == 1 else "STRAT_B"
                calendar.append({"day": d, "protocol": proto})
        # قفل: فقط sha256 ذخیره می‌شود، b64 هرگز decode نمی‌شود
        sealed = exp.get("sealed_prediction", {})
        state = _load_lab_state(self._state_dir)
        state["experiments"][exp_id] = {
            "name": exp.get("name", exp_id),
            "start_date": today, "end_date": end_date,
            "duration_days": exp.get("duration_days", 14),
            "calendar": calendar,
            "sealed_sha256": sealed.get("sha256", ""),  # فقط هش؛ b64 در seed باقی می‌ماند
            "metrics": exp.get("metrics", []),
            "status": "running",
        }
        _save_lab_state(state, self._state_dir)
        first = calendar[0] if calendar else {}
        return (f"🧪 <b>{html.escape(exp.get('name', exp_id))}</b> شروع شد\n\n"
                f"از <code>{today}</code> تا <code>{end_date}</code> ({len(calendar)} روز)\n"
                f"امروز (روز ۱): <code>{html.escape(str(first.get('protocol', '?')))}</code>\n\n"
                f"<i>پیش‌بینی مهر-و-موم شد. تا پایان، ترند/تفسیری نمایش داده نمی‌شود.</i>\n"
                f"<i>پس از {end_date} با <code>/reveal {exp_id}</code> بازش کن.</i>")

    def reveal_experiment(self, exp_id: str) -> str:
        """/reveal: فقط بعد از end_date + verifyِ sha256 محتوای b64. قبل از end_date = قفل."""
        state = _load_lab_state(self._state_dir)
        run = state.get("experiments", {}).get(exp_id)
        if run is None or run.get("status") != "running":
            return f"⚠ آزمایشِ <code>{html.escape(exp_id)}</code> فعال نیست."
        today = _today_str()
        if today < run.get("end_date", ""):
            return (f"🔒 قفل است. آزمایش تا <code>{run.get('end_date')}</code> پایان نمی‌یابد "
                    f"(امروز: {today}). پیش‌بینی زودتر decode نمی‌شود.")
        # verify sha256 از seed (b64 را همین‌جا decode می‌کنیم — اولین بار)
        seed = self._load_lab_seed()
        exps = {e["id"]: e for e in seed.get("experiments", [])}
        sealed = exps.get(exp_id, {}).get("sealed_prediction", {})
        b64_text = sealed.get("b64", "")
        expected_sha = run.get("sealed_sha256") or sealed.get("sha256", "")
        import base64, hashlib
        try:
            decoded_bytes = base64.b64decode(b64_text) if b64_text else b""
            decoded = decoded_bytes.decode("utf-8")
        except Exception:  # noqa: BLE001
            return "❌ پیش‌بینی آسیب‌دیده (decode ناموفق)."
        # sha256 از محتوایِ decoded محاسبه می‌شود (نه از b64_text) — مطابقِ seed
        actual_sha = hashlib.sha256(decoded_bytes).hexdigest() if decoded_bytes else ""
        if expected_sha and actual_sha and not _cteq(actual_sha, expected_sha):
            return ("❌ شکستِ تأییدِ یکپارچگی: sha256 منطبق نیست. "
                    "فایلِ seed دست‌خورده یا پیش‌بینی جعل شده.")
        run["status"] = "revealed"
        _save_lab_state(state, self._state_dir)
        return (f"🔓 <b>پیش‌بینی آشکار شد</b> ({html.escape(exp_id)})\n\n"
                f"<i>sha256 تأیید شد ✅</i>\n\n"
                f"<pre>{html.escape(decoded)}</pre>\n\n"
                f"<i>حالا می‌توانی داده‌ها را با پیش‌بینی مقایسه کنی.</i>")

    def lab_status(self) -> str:
        """وضعیتِ کوتاهِ آزمایش‌های فعال (ضدِ نشت: فقط نام/روز، بدونِ ترند)."""
        state = _load_lab_state(self._state_dir)
        runs = state.get("experiments", {})
        if not runs:
            return "هیچ آزمایشِ فعالی نیست. شروع: <code>/start_exp1</code>، <code>/start_exp2</code>، <code>/start_exp3</code>"
        lines = []
        for eid, run in runs.items():
            today = _today_str()
            done = today >= run.get("end_date", "")
            mark = "✅" if done else "🧪"
            lines.append(f"{mark} <code>{eid}</code> ({html.escape(run.get('name', ''))}) "
                         f"— تا <code>{run.get('end_date')}</code> [{run.get('status')}]")
        return "آزمایش‌ها:\n" + "\n".join(lines)

    # ─── T-5 · /status: فقط‌خواندنی، هیچ write ───────────────────────────────────
    def status_report(self) -> str:
        """گزارشِ وضعیتِ ارگانیسم — فقط‌خواندنی از _ops/state/*.json + heartbeat.
        ⚑ برای معمار: germline_lag و σ باید به فیلدهای موجود متصل شوند؛ فعلاً از
        ORGANISM-STATE.json می‌خواند. هیچ write."""
        from pathlib import Path
        state_dir = Path(self._state_dir) if self._state_dir else (
            Path(__file__).resolve().parents[1] / "state")
        org = _read_json_safe(state_dir / "ORGANISM-STATE.json")
        if not org:
            return ("📊 <b>وضعیت</b>\n\n<i>هنوز ارگانیسم روشن نشده — state‌ای نیست.</i>\n"
                    "روشن‌کردن: <code>_ops\\RUN-ORGANISM.bat</code>")
        month = org.get("month") or {}
        today = org.get("today") or {}
        conflicts = org.get("conflicts") or []
        lag = org.get("germline_lag_h", "—")
        lag_alert = org.get("germline_alert", "")
        lag_mark = "🔴" if lag_alert == "crit" else ("🟠" if lag_alert == "warn" else "🟢")
        halted = org.get("halted") or "—"
        frozen = "بله ❄️" if org.get("frozen") else "خیر"
        ts = str(org.get("ts", "—"))[:19]
        sigma = self._read_sigma()
        return (f"📊 <b>وضعیتِ ارگانیسم</b>\n\n"
                f"<b>آخرین تیک:</b> <code>{ts}</code>\n"
                f"<b>خرج ماه:</b> AU${_safe_float(month.get('aud')):.2f}\n"
                f"<b>خرج امروز:</b> US${_safe_float(today.get('usd')):.4f}\n"
                f"<b>متر مشکوک صفر:</b> {org.get('suspect_zero_total', '—')}\n"
                f"<b>تعارضِ تلمتری:</b> {len(conflicts)}\n"
                f"<b>σ تکثیر:</b> {sigma}\n"
                f"<b>germline lag:</b> {lag_mark} {lag} ساعت\n"
                f"<b>halted:</b> {halted} · <b>frozen:</b> {frozen}\n\n"
                f"<i>فقط‌خواندنی — این دستور هیچ‌چیزی تغییر نمی‌دهد.</i>")

    def _read_sigma(self) -> str:
        """σ تکثیر از replication-latest.json (fail-soft)."""
        from pathlib import Path
        state_dir = Path(self._state_dir) if self._state_dir else (
            Path(__file__).resolve().parents[1] / "state")
        d = _read_json_safe(state_dir / "replication-latest.json")
        if not d:
            return "pre-replication"
        sg = d.get("sigma")
        if isinstance(sg, dict):  # replication-latest.json: sigma = {sigma_effective, zone, ...}
            return f"{sg.get('sigma_effective', '—')} ({sg.get('zone', '—')})"
        return str(sg or d.get("status") or "—")

    # ─── T-6 · RFC/تکامل: doctor.submit_for_approval پشتِ flag ───────────────────
    # ⚑ برای معمار: doctor.submit_for_approval حالا در کد هست و وایر شده (به‌روزرسانی
    # 2026-07-14: ادعای «Phase 2/در کد نیست» کهنه بود). این کارتِ مرورِ RFC را
    # نشان می‌دهد. merge نیازِ human-append دارد (همان مسیرِ T-2).
    def rfc_card(self, rfc_id: str, summary: str) -> bool:
        """کارتِ مرورِ RFC با دکمه‌های [merge پشتِ flag ✅][رد ❌].
        W-3: کارت حالا token + registry دارد (self._pending_rfc) — همان ضدِ جعل/ضدِ
        replayِ کارت‌های پول (T-2). کلیک فقط verdict را ثبت می‌کند (_dispatch_rfc)؛
        اعمالِ merge پشتِ flag و با human-append در مسیرِ doctor است (pop_rfc_verdicts).
        هیچ settle/gate اینجا نیست. not wired → False (no-opِ امن)."""
        if not self.wired:
            return False
        # سقفِ ۶۴ بایتِ callback_data (۲۰۲۶-۰۷-۲۶). کارت `rfc:<verb>:<rfc_id>:<token>`
        # می‌سازد؛ رد شدن از سقف یعنی تلگرام **کلِ** sendMessage را ۴۰۰ می‌کند،
        # `send_text` استثنا را می‌بلعد و False می‌دهد، و کارت بی‌هیچ ردی در هیچ لاگ
        # گم می‌شود — کارتِ C6 دقیقاً یک شبانه‌روز همین‌طور ناپدید بود (۷۵ بایت).
        # این چک عمداً **قبل از** mintِ توکن است: شناسهٔ غیرممکن نباید رکوردِ
        # ماندگار و nonce بسوزاند. شکستِ بی‌صدا → شکستِ دیده‌شدنی.
        if not callback_fits(rfc_id):
            opslib.alert([
                f"rfc_card: rfc_id طولش {len(str(rfc_id))} است و callback_data را از "
                f"سقفِ {CALLBACK_DATA_MAX} بایت رد می‌کند — تلگرام کلِ پیام را رد "
                f"می‌کند و کارت بی‌صدا گم می‌شود. کارت فرستاده نشد؛ شناسه را کوتاه کن."])
            return False
        # Refuse re-card before touching durable intent: an unconsumed owner verdict must
        # never be overwritten by a fresh SUBMITTED nonce.
        with self._lk:
            existing = self._pending_rfc.get(rfc_id)
            if (existing and not existing.get("consumed")
                    and existing.get("status") in ("merge-approved", "denied")):
                return False
        # C7.2 RFC intent follows persist-before-send too. The durable store returns a
        # derived HMAC callback token; raw bearer material is never persisted.
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            made = _pcr.prepare_rfc_card(state_dir=self._state_dir, rfc_id=rfc_id,
                                         summary=summary, owner=self._owner)
        except Exception:
            made = None
        if not made:
            return False
        token = made["token"]
        with self._lk:
            self._pending_rfc[rfc_id] = {"summary": str(summary)[:500],
                                         "token": token, "status": "pending"}
        if not made.get("send_needed", True):
            return True
        text = (f"🔧 <b>پیشنهادِ تکامل (RFC)</b>\n\n"
                f"<b>خلاصه:</b> {html.escape(str(summary))}\n"
                f"<b>RFC:</b> <code>{html.escape(str(rfc_id))}</code>\n\n"
                f"<i>merge فقط پشتِ flag و با ضمیمهٔ انسانی.</i>")
        kb = {"inline_keyboard": [[
            {"text": "merge پشتِ flag ✅", "callback_data": f"rfc:merge:{rfc_id}:{token}"},
            {"text": "رد ❌", "callback_data": f"rfc:deny:{rfc_id}:{token}"},
        ], [
            {"text": "✍️ ویرایش/بازنگری", "callback_data": f"rfc:edit:{rfc_id}:{token}"},
        ]]}
        lease_id = f"rfc-{os.getpid()}-{threading.get_ident()}"
        if not _pcr._acquire_send_lease(self._state_dir, "rfc", rfc_id, lease_id):  # noqa: SLF001
            return False
        try:
            _pcr.mark_delivery(state_dir=self._state_dir, kind="rfc", cid=rfc_id,
                               delivery="LEASED")
            ok = self.send_text(text, reply_markup=kb)
            if not _pcr.mark_delivery(state_dir=self._state_dir, kind="rfc", cid=rfc_id,
                                      delivery="SENT" if ok else "PENDING"):
                return False
            return ok
        finally:
            _pcr.release_send_lease(self._state_dir, "rfc", rfc_id)

    # ─── T-7 · kill-switch out-of-band + Re-entry Packet ─────────────────────────
    def kill_switch(self) -> str:
        """/stop → فایلِ _ops/STOP-ORGANISM را می‌نویسد. فایل authoritative است، نه بات.
        بات فقط trigger است. توقفِ واقعی توسط pacemaker/organism خوانده می‌شود."""
        from pathlib import Path
        state_dir = Path(self._state_dir) if self._state_dir else (
            Path(__file__).resolve().parents[1] / "state")
        ops_dir = state_dir.parent                      # _ops (parent of state/)
        stop_file = ops_dir / "STOP-ORGANISM"
        try:
            stop_file.write_text(f"telegram kill-switch {_today_str()}\n", encoding="utf-8")
        except OSError:
            return "❌ نوشتنِ STOP-ORGANISM ناموفق."
        self.stop()                                    # حلقهٔ long-poll هم بایستد
        return ("🛑 <b>KILL-SWITCH فعال شد</b>\n\n"
                f"فایلِ <code>_ops\\STOP-ORGANISM</code> نوشته شد.\n"
                "<i>این فایل authoritative است. ارگانیسم در تیکِ بعدی متوقف می‌شود.</i>")

    def panic_all(self) -> str:
        """/panic → مرزِ سختِ سراسری HALT-ALL را می‌نویسد (opslib.raise_halt_all).
        هم‌الگوی kill_switch ولی سراسری: هر حلقه/کانکتور/باتِ بیرونی تیکِ بعد بی‌استثنا
        می‌ایستد (opslib.master_halted honor می‌کند). حلقهٔ خودِ بات را عمداً stop نمی‌کنیم
        تا /resume همچنان قابلِ دریافت بماند. fail-soft: خطا = پیامِ خطا، بدونِ crash."""
        try:
            opslib.raise_halt_all("telegram /panic")
        except Exception:  # noqa: BLE001 — fail-soft: نوشتن نشد، حلقه نمی‌میرد
            return "❌ نوشتنِ HALT-ALL ناموفق."
        return "🔴 HALT-ALL نوشته شد — همهٔ حلقه‌ها تیکِ بعد می‌ایستند"

    def resume_all(self) -> str:
        """/resume → مرزِ سختِ سراسری را آزاد می‌کند (opslib.clear_halt_all). قرینهٔ /panic.
        fail-soft: خطا = پیامِ خطا، بدونِ crash."""
        try:
            opslib.clear_halt_all()
        except Exception:  # noqa: BLE001 — fail-soft
            return "❌ آزادسازیِ HALT-ALL ناموفق."
        return "🟢 HALT-ALL آزاد شد"

    def reentry_packet(self) -> str:
        """Re-entry Packet: پس از gapِ آفلاین، اثرهای freeze/queue‌شده را نشان می‌دهد.
        ⚑ برای معمار: فعلاً از self._pending (pending کارت‌ها) + chrono gated_effect می‌خواند.
        اگر gate وصل باشد، pending effects را هم نشان می‌دهد."""
        n_cards = 0
        with self._lk:
            n_cards = sum(1 for m in self._pending.values() if m.get("status") == "pending")
        lines = [f"📋 <b>Re-entry Packet</b> (بازگشت از gap)", ""]
        lines.append(f"• کارت‌های تأییدِ معلق: {n_cards}")
        if self._gate is not None:
            try:
                db = getattr(self._gate, "db", None)
                if db is not None:
                    n = db.q("SELECT COUNT(*) FROM gated_effect WHERE status='pending'")[0][0]
                    lines.append(f"• اثرهای گیت‌دارِ freeze‌شده: {n}")
            except Exception:  # noqa: BLE001 — fail-soft
                lines.append("• اثرهای گیت‌دار: (خواندن ناموفق)")
        else:
            lines.append("• اثرهای گیت‌دار: gate وصل نیست")
        lines.append("")
        lines.append("<i>cognition + heartbeat در طولِ gap ادامه داشت. اثرها freeze بودند.</i>")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════════
    # Cockpit v2 — کابینِ بازرسیِ ۸-تبی (مگاپرامپت TELEGRAM-BRAIN-COCKPIT-v2-FULL-BODY)
    # read آزاد (menu:/card:/pg: بدونِ توکن) · هر کنترل act:<verb>:<key>:<token>
    # (تک‌مصرف، ضدجعل، allowlistِ بسته — INV-13). هیچ settleِ جدید (INV-1)،
    # هیچ subsystem cycleِ inline (INV-7)، redaction روی هر خروجی (INV-12).
    # ═══════════════════════════════════════════════════════════════════════════

    TAB_PAGES = ("overview", "cortex", "blueprint", "brain", "doctor", "money",
                 "finance", "school", "safety", "alerts", "organs")

    # allowlistِ بستهٔ act (§۲.۴ — ضدquarantine). chamber_t عمداً غایب است:
    # RED — فعال‌سازی فقط با verdict صریحِ مالک، هرگز از دکمهٔ تلگرام (P5).
    FLAG_KEYS = frozenset({
        "doctor", "neural", "unified", "lead", "lead_tick", "school",
        "consolidation", "evolution", "box", "ideas", "spectral", "barbell",
        "debate", "scheduler", "reconcile", "fitness", "epistemics",
        "selfheal", "bio",
        # 🦾 کنسولِ اندام (2026-07-15): legهای worker/business توگل‌پذیر (propose-only، بی‌پول،
        # هیچ‌کدام RISKY نیستند). فعال‌سازی همان مسیرِ flag/flaggo — اثر در بوتِ بعدی.
        "ziman", "cartographer", "mining"})
    RISKY_FLAGS = frozenset({"barbell", "debate", "reconcile", "fitness",
                             "epistemics", "selfheal", "bio"})
    # C9 (بازبینیِ خصمانه): allowlist = دقیقاً مجموعهٔ reachable (هر key دکمه‌ای دارد که
    # tokenش را mint می‌کند). verbهای نیازمندِ آرگومان بدونِ UIِ انتخاب (latent:forget با
    # کدام key؟ idea:accept کدام یال؟ cardiac:stimulate چقدر؟) عمداً حذف شدند — کارتشان
    # «not-wired/از CLI» می‌ماند تا سطحِ حمله = قابلیتِ واقعی. reveal از /reveal command
    # می‌رود (نه act). C11: act:phase:transition/metric:prereg/restart:<leg> عمداً پیاده
    # نشدند (governance/args) — narrowingِ ثبت‌شده؛ گذارِ فاز از رجیستریِ rfc، prereg از CLI.
    ACT_ALLOWLIST: dict = {
        "export":      frozenset({"raw"}),
        "flag":        FLAG_KEYS,          # قدمِ ۱: کارتِ confirm (دکمه در safety:flags paged)
        "flaggo":      FLAG_KEYS,          # قدمِ ۲: نوشتنِ merged به OCTOPUS-flags.cmd
        "restart":     frozenset({"organism"}),
        "restartgo":   frozenset({"organism"}),
        "freeze":      frozenset({"on"}),
        "freezego":    frozenset({"on"}),
        "sweep":       frozenset({"effects"}),
        "doctor":      frozenset({"run"}),
        "consolidate": frozenset({"run"}),
        "ideas":       frozenset({"rebuild"}),
        "school":      frozenset({"learn"}),
        "ingest":      frozenset({"crypto", "acct"}),
        "lab":         frozenset({"start1", "start2", "start3"}),
        "baseline":    frozenset({"capture"}),
        "pf":          frozenset({"pause", "resume"}),   # Project-F کنترلِ content-free
        # Task 3c (2026-07-24): تنظیمِ setpointِ قلب — فقط ۵ فیلدِ HeartParams
        # (ADR-001: هیچ period/rate — حذفِ ساختاری)؛ مقدار در target (الگوی flaggo، C4)
        "heartset":    frozenset({"target_sigma", "viable_band_lo", "viable_band_hi",
                                  "daily_beat_cap", "baroreflex_gain"}),
    }
    # هیچ verbِ پول‌خوری در allowlist نیست (act:reconcile:run / act:epoch:run عمداً
    # وجود ندارند — §۲.۵). این مجموعه دفاعی است: verbِ پولیِ آینده بدونِ گیتِ باز رد می‌شود.
    MONEY_VERBS = frozenset()
    # این verbها هرگز inline اجرا نمی‌شوند (INV-7) — فقط ثبتِ درخواستِ out-of-band
    # در state/cockpit-requests.jsonl تا organism در ضربانِ بعدی مصرف کند.
    OOB_VERBS = frozenset({"doctor", "consolidate", "ideas", "school", "ingest"})
    # کارت‌هایی که خودشان دکمه‌ی act دارند (C9: هر act در allowlist باید reachable باشد).
    CARD_ACTIONS: dict = {
        ("doctor", "lab"): [("🧪 شروع exp1", "lab", "start1"),
                            ("🧪 شروع exp2", "lab", "start2"),
                            ("🧪 شروع exp3", "lab", "start3")],
        ("doctor", "projectf"): [("⏸ نگه‌دار", "pf", "pause"),
                                 ("▶️ ادامه بده", "pf", "resume")],
    }

    TAB_CARDS: dict = {
        "overview":  [("vitals", "🩺 علائم"), ("heart", "♥️ ضربان"),
                      ("legs", "🐙 ۶ پا"), ("projects", "📁 پروژه‌ها")],
        "blueprint": [("phases", "🧭 فازها"), ("baselines", "📸 baselineها"),
                      ("bcm", "🧬 BCM (P3)"), ("sparse", "🕸 Sparse (P4)"),
                      ("chamber", "🌡 Chamber-T (P5)"), ("fisher", "📐 Fisher (P6)"),
                      ("prereg", "📋 پیش‌ثبت"), ("transition", "🚪 گذارِ فاز")],
        "brain":     [("consolidation", "🧠 تحکیم"), ("latent", "🌀 Latent R³²"),
                      ("idea", "💡 ایده-گراف"), ("hebbian", "🔗 Hebbian"),
                      ("sprint", "🏃 اسپرینت")],
        "doctor":    [("rfc", "🔧 RFCها"), ("box", "📦 جعبهٔ دکتر"),
                      ("evolution", "🧬 تکامل"), ("epi", "🔭 معرفت‌شناسی"),
                      ("scheduler", "⏰ دیسپچر"), ("selfheal", "🩹 خوددرمانی"),
                      ("projectf", "🎬 Project-F"), ("lab", "🧪 آزمایشگاه")],
        "money":     [("telemetry", "💵 مصرف"), ("organs", "🫀 ارگان‌ها"),
                      ("fitness", "📊 فیتنس"), ("attribution", "🧾 درآمد/لیدها"),
                      ("cardiac", "♥️ ضربانِ بودجه"), ("reconcile", "🔁 تطبیق"),
                      ("barbell", "⚖️ باربل"), ("governor", "🤖 گاورنر LLM")],
        "school":    [("awareness", "🎓 آگاهی"), ("cells", "🧫 سلول‌ها"),
                      ("afferent", "🔌 آوران"), ("crypto", "📈 بریفِ کریپتو")],
        "safety":    [("gates", "🔒 گیت‌ها"), ("flags", "🚦 flagها"),
                      ("germline", "💾 germline"), ("conflicts", "⚔️ تعارض"),
                      ("integrity", "🔏 اثرانگشتِ پول"), ("pii", "🕵️ گاردِ PII"),
                      ("llm", "🧭 مسیرِ LLM"), ("reentry", "📋 بازگشت")],
        "alerts":    [("rules", "✅ ۲۴ قاعده"), ("governor", "🚨 هشدارها"),
                      ("genome", "🧬 زنجیرهٔ ژنوم"), ("chrono", "⏱ chrono"),
                      ("channels", "📡 کانال‌ها"), ("raw", "🗂 state خام"),
                      ("log", "📜 لاگ"), ("requests", "📨 صفِ درخواست")],
    }
    PG_KEYS = {("alerts", "rules"), ("safety", "flags")}
    # 🦾 کنسولِ اندام (2026-07-15): (key, label, env-flag یا None, kind). keyِ دارای env با
    # همان مسیرِ flag/flaggo توگل می‌شود؛ بی‌flag = اسکلتِ همیشه‌روشنِ read-only.
    ORGANS = (
        ("lead",         "🎨 Lead-نقاشی",   "OCTOPUS_WIRE_LEAD",         "worker"),
        ("ziman",        "🖼 Ziman",         "OCTOPUS_WIRE_ZIMAN",        "worker"),
        ("cartographer", "🗺 Cartographer",  "OCTOPUS_WIRE_CARTOGRAPHER", "worker"),
        ("mining",       "⛏ Mining",         "OCTOPUS_WIRE_MINING",       "business"),
        ("crypto",       "📈 Crypto",         None,                        "business"),
        ("accounting",   "🧾 Accounting",     None,                        "business"),
        ("knowledge",    "📚 Knowledge",      None,                        "business"),
    )
    _DIV = "\n➖➖➖➖➖\n"

    # ── زیرساخت: read-model ، redaction ، توکنِ act ─────────────────────────────
    def _rm(self):
        """read-modelِ کابین (lazy، قابلِ تزریق برای تست). شکست → None (کارت «بی‌داده»).
        C8: وقتی state_dir تزریق شده، ops_dir را هم از parentِ آن مشتق کن — وگرنه readerهای
        مبتنی بر ops (governor-alerts, neural/*, OCTOPUS-flags) از vaultِ واقعی می‌خوانند
        (نشتِ ایزوله‌سازیِ تست + خواندنِ ناخواستهٔ prod)."""
        if self._readmodel is not None:
            return self._readmodel
        try:
            import cockpit_readmodel as _crm
            from pathlib import Path as _P
            ops = _P(self._state_dir).parent if self._state_dir else None
            self._readmodel = _crm.CockpitReadModel(state_dir=self._state_dir, ops_dir=ops)
            return self._readmodel
        except Exception:  # noqa: BLE001 — fail-soft
            return None

    def _redact(self, text: str) -> str:
        """INV-12: پاسِ redactionِ خروجی. secretِ سخت → کلِ بدنه؛ hex64 → per-match (C7).
        C3/C6: اگر لایهٔ redaction بشکند، fail-open و ساکت نیست — یک‌بار alert می‌زند و متن
        را دست‌نخورده می‌فرستد (بهتر از سکوت). مسیرِ خوش‌کار از cockpit_readmodel.redact می‌رود."""
        try:
            import cockpit_readmodel as _crm
            return _crm.redact(text)
        except Exception as e:  # noqa: BLE001
            if not getattr(self, "_redact_warned", False):
                self._redact_warned = True
                opslib.alert([f"INV-12 redaction layer unavailable: {type(e).__name__}: {e}"])
            return text

    def _redact_pii(self, text: str) -> str:
        """لایهٔ دومِ INV-12 فقط برای mirrorهای خام (state/log/alerts/quarantine):
        PII (تشخیصِ sensory_bus._contains_pii) → کلِ بدنه حذف می‌شود."""
        try:
            import sys as _sys
            from pathlib import Path as _P
            _aff = _P(__file__).resolve().parents[1] / "afferent"
            if str(_aff) not in _sys.path:
                _sys.path.insert(0, str(_aff))
            from sensory_bus import _contains_pii
            if _contains_pii(str(text or "")):
                import cockpit_readmodel as _crm
                return _crm.REDACTED_BODY
        except Exception:  # noqa: BLE001 — گاردِ PII در دسترس نیست → لایهٔ secret کافی است
            pass
        return text

    def _new_act_token(self, verb: str, key: str, ttl_s: int = 3600, target=None) -> str:
        """توکنِ تک‌مصرفِ ضدجعلِ act (INV-13). زیرِ قفل در _pending_act ثبت می‌شود؛
        رندرِ دوباره = mintِ دوباره (آخرین رندر معتبر است).
        target: مقدارِ مطلقِ تصمیم (C4) — برای flaggo همان «not cur» در زمانِ رندرِ کارتِ confirm،
        تا کلیکِ روی کارتِ کهنه flag را به سمتِ اشتباه flip نکند."""
        import hashlib
        import time as _time
        action_id = f"{verb}:{key}"
        payload = f"{action_id}|{_time.time_ns()}|{len(self._pending_act)}"
        token = hashlib.sha256(payload.encode()).hexdigest()[:24]
        with self._lk:
            self._pending_act[action_id] = {
                "token": token, "verb": verb, "key": key, "target": target,
                "status": "pending", "expires_at": _time.time() + ttl_s}
        return token

    def _act_btn(self, label: str, verb: str, key: str) -> dict:
        """دکمهٔ act با توکنِ تازه‌mint‌شده. توکن فقط در callback_data، هرگز در متن."""
        return {"text": label,
                "callback_data": f"act:{verb}:{key}:{self._new_act_token(verb, key)}"}

    def _live_gate_status(self) -> tuple[bool, str]:
        """وضعیتِ گیتِ زندهٔ دوقفله (fail-closed). تا 2026-07-21 قفل است."""
        try:
            import capability_gate
            if capability_gate.capability_ok() and capability_gate.live_enabled():
                return True, "باز"
            return False, "قفل تا 2026-07-21 (capability/LIVE_ENABLED بسته)"
        except Exception:  # noqa: BLE001 — گیتِ ناخوانا = بسته
            return False, "قفل (گیت خوانا نیست — fail-closed)"

    def _activation_gate_line(self, flag_name: str) -> str:
        """وضعیتِ راست‌گوی یک گیتِ دوقفله از فایل، نه متنِ hardcode (صداقتِ GO-LIVE 2026-07-16):
        باز → 🟢 مسلح؛ فلگ هست ولی سپرِ تاریخ بسته → 🟡؛ فلگ غایب → 🔴 با تاریخِ واقعی.
        فقط رندر است — هیچ گیتی را باز نمی‌کند (opslib.live_gate_open همان مرجعِ اجرایی)."""
        try:
            flag = opslib.OPS / flag_name
            ok, _why = opslib.live_gate_open(flag)
            if ok:
                return "🟢 مسلح (فلگ + سپرِ تاریخ باز)"
            if flag.exists():
                return (f"🟡 فلگ مسلح ولی سپرِ تاریخ بسته "
                        f"(تا {opslib.LIVE_GATE_DATE.isoformat()}، بدونِ GO-LIVE)")
            return (f"🔴 قفل تا {opslib.LIVE_GATE_DATE.isoformat()} "
                    f"(فلگِ {flag_name} غایب)")
        except Exception:  # noqa: BLE001 — گیتِ ناخوانا = بسته (fail-closed)
            return "🔴 قفل (گیت خوانا نیست — fail-closed)"

    def _dashboard(self):
        """ماژولِ dashboard/server.py با importlib و نامِ یکتا (بدونِ تصادم با panel/server)."""
        if self._dash_mod is not None:
            return self._dash_mod
        import importlib.util
        from pathlib import Path as _P
        p = _P(__file__).resolve().parents[1] / "dashboard" / "server.py"
        spec = importlib.util.spec_from_file_location("octo_dashboard_server", str(p))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self._dash_mod = mod
        return mod

    def _append_request(self, verb: str, key: str) -> bool:
        """صفِ out-of-band (INV-7): درخواستِ کنترلی به state/cockpit-requests.jsonl.
        اجرا نمی‌کند — organism/مالک مصرف می‌کند. append-only، fail-soft."""
        from pathlib import Path as _P
        state_dir = _P(self._state_dir) if self._state_dir else (
            _P(__file__).resolve().parents[1] / "state")
        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            with open(state_dir / "cockpit-requests.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": _today_iso(), "verb": verb, "key": key,
                                    "source": "telegram-cockpit",
                                    "status": "requested"}, ensure_ascii=False) + "\n")
            return True
        except OSError:
            return False

    # ── routerهای جدید: card / pg / act ─────────────────────────────────────────
    def _dispatch_card(self, parts: list[str]):
        """card:<tab>:<key> — رندرِ یک detail-card فقط‌خواندنی. بدونِ توکن (read-safe)."""
        if len(parts) != 3:
            return "نادیده"
        tab, key = parts[1], parts[2]
        if not any(k == key for k, _ in self.TAB_CARDS.get(tab, [])):
            return "نادیده"
        try:
            text = self._render_card(tab, key)
        except Exception as e:  # noqa: BLE001 — INV-9: رندر نباید loop را بکشد
            opslib.alert([f"cockpit card error ({tab}:{key}): {type(e).__name__}: {e}"])
            text = "❌ خطای رندرِ کارت — ثبت شد."
        rows: list[list[dict]] = []
        for lbl, v, k in self.CARD_ACTIONS.get((tab, key), []):   # C9: actهای این کارت
            rows.append([self._act_btn(lbl, v, k)])
        rows.append([{"text": "⬅️ بازگشت", "callback_data": f"menu:{tab}"}])
        return {"text": text, "reply_markup": {"inline_keyboard": rows}}

    def _dispatch_page(self, parts: list[str]):
        """pg:<tab>:<key>:<n> — صفحه‌بندیِ لیست‌های بلند. فقط کلیدهای PG_KEYS."""
        if len(parts) != 4:
            return "نادیده"
        tab, key = parts[1], parts[2]
        if (tab, key) not in self.PG_KEYS:
            return "نادیده"
        try:
            n = max(1, int(parts[3]))
        except ValueError:
            return "نادیده"
        try:
            return self._render_paged(tab, key, n)
        except Exception as e:  # noqa: BLE001 — INV-9
            opslib.alert([f"cockpit pg error ({tab}:{key}): {type(e).__name__}: {e}"])
            return "❌ خطای صفحه‌بندی — ثبت شد."

    def _dispatch_act(self, parts: list[str]):
        """act:<verb>:<key>:<token> — تنها مسیرِ کنترلیِ کابین (INV-13).
        allowlistِ بسته → توکنِ ذخیره‌شده (_cteq) → مصرفِ قبل از اجرا → kill-check →
        گیتِ سختِ live برای verbهای پولی (§۲.۵) → اجرا. هیچ settleِ پول اینجا نیست."""
        import time as _time
        if len(parts) != 4:
            return "نادیده"
        verb, key, token = parts[1], parts[2], parts[3]
        allowed = self.ACT_ALLOWLIST.get(verb)
        if allowed is None or key not in allowed:
            return "نادیده"
        action_id = f"{verb}:{key}"
        # C1 (بازبینیِ خصمانه 2026-07-10): اعتبارسنجی + مصرف باید اتمیک باشند — وگرنه دو
        # dispatchِ همزمان با یک توکن هر دو 'pending' می‌بینند و act دوبار اجرا می‌شود (نقضِ
        # تک‌مصرفیِ INV-13). همه‌چیز داخلِ یک بلوکِ قفل: get → check → cteq → consume.
        with self._lk:
            entry = self._pending_act.get(action_id)
            if entry is None or entry.get("status") != "pending" \
                    or _time.time() > entry.get("expires_at", 0):
                return "رد: توکن ناموجود/منقضی — کارت را دوباره باز کن"
            if not _cteq(token, entry.get("token", "")):
                return "رد: توکنِ act نامنطبق (ضدجعل)"
            entry["status"] = "consumed"     # تک‌مصرف، اتمیک با اعتبارسنجی (anti-replay)
            target = entry.get("target")     # C4: مقدارِ مطلقِ ذخیره‌شده در mint (flaggo)
        if self._killed():
            return "🛑 STOP فعال است — اجرا نشد"
        if verb in self.MONEY_VERBS:          # دفاعی: امروز خالی است (§۲.۵)
            ok, why = self._live_gate_status()
            if not ok:
                return f"🔒 قفلِ live-gate: {why}"
        try:
            result = self._run_act(verb, key, target=target)
            if self._killed():                # C14 · §۲.۶: چک بعد از اثر هم
                note = "\n🛑 STOP اکنون فعال است."
                if isinstance(result, dict):
                    result["text"] = result.get("text", "") + note
                    return result
                return str(result) + note
            return result
        except Exception as e:  # noqa: BLE001 — INV-9
            opslib.alert([f"cockpit act error ({action_id}): {type(e).__name__}: {e}"])
            return "❌ اجرای act ناموفق — ثبت شد."

    # ─── Project-F کنترلِ content-free (جلسه ۴۶، رأی مالک «اونلی‌فنزم بیار زیرمجموعه») ──
    def _pf_pause_path(self):
        return opslib.STATE_DIR / "projectf-paused.flag"

    def _pf_paused(self) -> bool:
        return self._pf_pause_path().exists()

    def _pf_pending_count(self) -> int:
        """شمارِ آیتم‌های Project-Fِ منتظرِ تأیید — فقط effect_idهای pf- (بی‌محتوا)."""
        try:
            with self._lk:
                return sum(1 for eid, m in self._pending.items()
                           if str(eid).startswith("pf-") and m.get("status") == "pending")
        except Exception:  # noqa: BLE001
            return 0

    def _act_pf_control(self, key: str) -> str:
        """کنترلِ content-free: pause = نگه‌داشتنِ روتِ درفت‌های نو؛ resume = ادامه.
        فقط یک فلگِ خالی می‌نویسد/پاک می‌کند — صفر محتوا/هویت/پلتفرم. مسیرِ پول/تأیید
        دست‌نخورده (آیتم‌های در صف با همان human-append تأیید می‌شوند)."""
        p = self._pf_pause_path()
        try:
            if key == "pause":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("owner-paused", "utf-8")
                return ("⏸ Project-F نگه داشته شد — درفت‌های نو تا «ادامه» روت نمی‌شوند.\n"
                        "آیتم‌های در صف دست‌نخورده‌اند.")
            if key == "resume":
                if p.exists():
                    p.unlink()
                return "▶️ Project-F ادامه یافت — درفت‌های نو دوباره به صفِ تأیید می‌روند."
            return "نامعتبر"
        except OSError as e:
            return f"❌ ثبتِ کنترل ناموفق: {type(e).__name__}"

    def _run_act(self, verb: str, key: str, target=None):
        """اجرای actِ تأییدشده. inline فقط read/فایل‌های کنترلِ امن (§۲.۶)؛
        subsystem cycleها → صفِ out-of-band. (هرگز run_cycle/run_epoch مستقیم صدا زده نمی‌شود.)
        target: مقدارِ مطلقِ ذخیره‌شده در mint (فعلاً فقط flaggo)."""
        if verb in self.OOB_VERBS:
            ok = self._append_request(verb, key)
            if not ok:
                return "❌ ثبتِ درخواست ناموفق"
            # 2026-07-15 صداقت: دیگر دروغِ «اجرا می‌شود» نمی‌گوییم. فقط doctor/consolidate با
            # OCTOPUS_TG_EXEC=1 روی beat اجرا می‌شوند؛ بقیه مصرف‌کننده ندارند.
            import os as _os
            runnable = verb in ("doctor", "consolidate")
            exec_on = _os.environ.get("OCTOPUS_TG_EXEC") == "1"
            if runnable and exec_on:
                return "📨 ثبت شد — organism در ضربانِ بعدی اجرا می‌کند.\n<i>صف: cockpit-requests.jsonl</i>"
            if runnable:
                return ("📨 ثبت شد — ولی <b>اجرا خاموش است</b>. برای اجرای واقعی "
                        "<code>OCTOPUS_TG_EXEC=1</code> بگذار و restart کن.")
            return "📨 ثبت شد — ولی این verb مصرف‌کنندهٔ اجرا ندارد (فقط doctor/consolidate اجرا می‌شوند)."
        if verb == "pf":
            return self._act_pf_control(key)
        if verb == "export":
            return self._act_export()
        if verb == "flag":
            return self._act_flag_confirm(key)
        if verb == "flaggo":
            return self._act_flag_write(key, target=target)
        if verb == "restart":
            kb = {"inline_keyboard": [[
                self._act_btn("✅ بله، ری‌استارت کن", "restartgo", "organism"),
                {"text": "❌ انصراف", "callback_data": "menu:safety"}]]}
            return {"text": ("♻️ <b>ری‌استارتِ تمیزِ ارگانیسم</b>\n"
                             "STOP-ORGANISM + RESTART-REQUESTED نوشته می‌شود؛ "
                             "organism در تیکِ بعد (≤۵ دقیقه) تمیز خارج و با env جدید بوت می‌شود.\n"
                             "مطمئنی؟"), "reply_markup": kb}
        if verb == "restartgo":
            return self._act_restart()
        if verb == "freeze":
            kb = {"inline_keyboard": [[
                self._act_btn("✅ بله، FREEZE کن", "freezego", "on"),
                {"text": "❌ انصراف", "callback_data": "menu:safety"}]]}
            return {"text": ("❄️ <b>FREEZE متابولیک</b>\n"
                             "FREEZE.flag نوشته می‌شود — هر spend/effect تا رفعِ دستی یخ می‌زند.\n"
                             "(رفع: حذفِ دستیِ فایلِ <code>_ops/budget/FREEZE.flag</code> توسطِ خودت)\n"
                             "مطمئنی؟"), "reply_markup": kb}
        if verb == "freezego":
            try:
                opslib.freeze("cockpit: act:freeze توسطِ مالک (تلگرام)")
                return "❄️ FREEZE.flag نوشته شد — متابولیسم یخ زد. رفع: حذفِ دستیِ فایل."
            except Exception as e:  # noqa: BLE001
                return f"❌ FREEZE ناموفق: {type(e).__name__}"
        if verb == "sweep":
            return self._act_sweep()
        if verb == "lab":
            return self.start_experiment({"start1": "exp1", "start2": "exp2",
                                          "start3": "exp3"}[key])
        # reveal از /reveal command می‌رود (نه act) — §۸ resurface.
        if verb == "baseline":
            return self._act_baseline()
        if verb == "heartset":
            return self._act_heartset(key, target)
        return "نادیده"

    def _act_export(self) -> str:
        """بازتولیدِ بستهٔ وضعیت — read-only + secret-scanِ fail-closedِ خودِ export_status."""
        try:
            import sys as _sys
            from pathlib import Path as _P
            _ops = _P(__file__).resolve().parents[1]
            if str(_ops) not in _sys.path:
                _sys.path.insert(0, str(_ops))
            import export_status
            rc = export_status.main()
            if rc == 0:
                p = (_P(self._state_dir) if self._state_dir else _ops / "state") \
                    / "export" / "octopus-status-bundle.json"
                kb = (p.stat().st_size // 1024) if p.exists() else 0
                return f"✅ بستهٔ وضعیت بازتولید شد ({kb} KB · secret-scanned)"
            return "⛔ ABORT: اسکنِ secret جلوی export را گرفت — چیزی نوشته نشد"
        except Exception as e:  # noqa: BLE001
            return f"❌ export ناموفق: {type(e).__name__}"

    def _act_flag_confirm(self, key: str):
        """قدمِ ۱ از تغییرِ flag: کارتِ confirm با توکنِ تازه (flagهای ریسکی هشدار دارند)."""
        env_name = f"OCTOPUS_WIRE_{key.upper()}"
        cur = self._current_flag(env_name)   # 2026-07-15: منبعِ واحد (شاملِ flagهای اندام via env)
        want = not cur                       # C4: تصمیمِ مطلق در زمانِ رندر
        target_word = "روشن" if want else "خاموش"
        risk = "⚠️ <b>ریسکی</b>" if key in self.RISKY_FLAGS else "🟢 امن"
        # توکنِ flaggo با target=want ثبت می‌شود؛ کلیکِ کارتِ کهنه همان مقدارِ ثابت را می‌نویسد.
        go_tok = self._new_act_token("flaggo", key, target=want)
        kb = {"inline_keyboard": [[
            {"text": f"✅ بله، {target_word} کن",
             "callback_data": f"act:flaggo:{key}:{go_tok}"},
            {"text": "❌ انصراف", "callback_data": "menu:safety"}]]}
        return {"text": (f"🚦 <b>تغییرِ flag</b> — <code>{html.escape(env_name)}</code>\n"
                         f"وضعیتِ فعلی: {'🟢 روشن' if cur else '⚪ خاموش'} · {risk}\n"
                         f"بعد از تأیید <b>{target_word}</b> می‌شود — اثر فقط در بوتِ بعدی "
                         f"(act:restart یا RESTART-ORGANISM.bat)."), "reply_markup": kb}

    def _act_flag_write(self, key: str, target=None) -> str:
        """قدمِ ۲: نوشتنِ merged به OCTOPUS-flags.cmd از راهِ dashboard._write_env —
        همهٔ flagهای دیگر حفظ می‌شوند (نه reset). human-append: خودِ کلیک = ضمیمهٔ انسانی.
        C4: مقدار = targetِ مطلقِ زمانِ رندر (نه toggleِ زمانِ کلیک).
        C10: flagهای ریسکی فقط با capability_gate بازِ اثبات‌شده؛ + ثبتِ auditِ تاریخ‌دار."""
        env_name = f"OCTOPUS_WIRE_{key.upper()}"
        want = (not self._current_flag(env_name)) if target is None else bool(target)
        # C10: گیتِ سختِ capability برای flagهای ریسکی (سوییتِ سبزِ اثبات‌شده لازم است)
        if key in self.RISKY_FLAGS:
            try:
                import capability_gate
                if not capability_gate.capability_ok():
                    return ("🔒 نوشتنِ flagِ ریسکی رد شد: سوییتِ سبزِ اثبات‌شده نیست "
                            "(capability_gate بسته). اول تست‌ها را سبز کن.")
            except Exception:  # noqa: BLE001 — گیتِ ناخوانا = fail-closed برای ریسکی
                return "🔒 نوشتنِ flagِ ریسکی رد شد (capability_gate خوانا نیست — fail-closed)."
        try:
            dash = self._dashboard()
            eff = dash._effective_flags()
            eff[env_name] = want
            form = {"OCTOPUS_PROFILE": dash._effective_profile()}
            form.update({n: ("1" if v else "0") for n, v in eff.items()})
            form.update(dash._effective_cadences())
            msg = dash._write_env(form)
        except Exception as e:  # noqa: BLE001
            return f"❌ نوشتنِ flag ناموفق: {type(e).__name__}"
        # C10: auditِ تاریخ‌دارِ human-append (فراتر از خودِ کلیک) — صفِ append-only
        self._append_request("flagwrite", f"{env_name}={'1' if want else '0'}")
        return (f"💾 {html.escape(msg)}\n"
                f"<code>{html.escape(env_name)}</code> → "
                f"{'🟢 روشن' if want else '⚪ خاموش'} در بوتِ بعدی.\n"
                f"♻️ اعمال: دکمهٔ ری‌استارت در تبِ ایمنی.")

    def _current_flag(self, env_name: str) -> bool:
        rm = self._rm()
        if rm is not None:
            try:
                fl = rm.read_capabilities().get("flags", {}) or {}
                if env_name in fl:
                    return bool(fl.get(env_name))
            except Exception:  # noqa: BLE001
                pass
        # fallback: env زنده — flagهای اندام (ZIMAN/CARTOGRAPHER/MINING) در لیستِ ۱۹تاییِ
        # read_capabilities نیستند؛ os.environ حقیقتِ زمانِ اجراست.
        import os as _os
        return _os.environ.get(env_name) == "1"

    def _act_restart(self) -> str:
        """ری‌استارتِ تمیز از مسیرِ موجودِ dashboard._do_restart (فایل authoritative است)."""
        try:
            dash = self._dashboard()
            return "♻️ " + html.escape(dash._do_restart())
        except Exception as e:  # noqa: BLE001
            return f"❌ restart ناموفق: {type(e).__name__}"

    def _act_sweep(self) -> str:
        """جاروی اثرهای کهنه (>72h pending) — متدِ موجودِ گیتِ تک‌گلوگاه، bounded."""
        if self._gate is None:
            return "gate وصل نیست — sweep ممکن نیست"
        try:
            r = self._gate.sweep_stale_effects()
            return f"🧹 sweep انجام شد: {r.get('refused', 0)} اثرِ کهنه refuse شد"
        except Exception as e:  # noqa: BLE001
            return f"❌ sweep ناموفق: {type(e).__name__}"

    def _act_baseline(self) -> str:
        """گرفتنِ baselineِ فازِ جاری (baseline.capture_baseline — bounded، فقط state-write)."""
        try:
            import sys as _sys
            from pathlib import Path as _P
            _ops = _P(__file__).resolve().parents[1]
            if str(_ops) not in _sys.path:
                _sys.path.insert(0, str(_ops))
            import baseline as _baseline
            rm = self._rm()
            phase = (rm.read_phase() or {}).get("current_phase") if rm else None
            if not phase:
                return ("فازِ جاری از state خوانا نیست — baseline را از CLI بگیر:\n"
                        "<code>python _ops/baseline.py</code>")
            # C13 · §۲.۶ (bounded inline، فقط state-write): از state_dirِ تزریقی استفاده کن
            # تا baselineِ تست به vaultِ واقعی نشت نکند.
            from pathlib import Path as _P
            kw = {"state_dir": _P(self._state_dir)} if self._state_dir else {}
            _baseline.capture_baseline(str(phase), "cockpit", **kw)
            return f"📸 baseline گرفته شد برای فازِ <code>{html.escape(str(phase))}</code>"
        except Exception as e:  # noqa: BLE001
            return f"❌ baseline ناموفق: {type(e).__name__}"

    # ── دستورهای متنی جدید (پول: فقط human-append — هیچ settle) ────────────────
    def _cmd_claim(self, raw: str) -> str:
        """/claim ATTR-ID | شماره‌کوت | مبلغ — ثبتِ CLAIMED (attribution.claim، human-append).
        CONFIRMED فقط از reconcile-actor می‌آید؛ این دستور پول جابه‌جا نمی‌کند."""
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 3:
            return "⚠ فرمت: <code>/claim ATTR-ID | شماره‌کوت | مبلغ AUD</code>"
        try:
            amount = float(parts[2])
        except ValueError:
            return "⚠ مبلغ باید عدد باشد (AUD)."
        if amount < 0:
            return "⚠ مبلغ منفی نمی‌شود."
        try:
            import attribution
            attribution.claim(parts[0], parts[1], amount)
            return (f"✅ <b>CLAIMED</b> ثبت شد: <code>{html.escape(parts[0])}</code> · "
                    f"AU${amount:.2f}\n<i>تأییدِ نهایی (CONFIRMED) فقط از reconcile می‌آید.</i>")
        except Exception as e:  # noqa: BLE001 — fail-closed، هیچ نیمه‌ثبت
            return f"❌ ثبتِ claim ناموفق: {type(e).__name__}"

    def _cmd_conflict(self, raw: str) -> str:
        """/conflict ATTR-ID | دلیل — علامتِ تعارضِ انسانی روی یک attribution."""
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 2:
            return "⚠ فرمت: <code>/conflict ATTR-ID | دلیل</code>"
        try:
            import attribution
            attribution.conflict(parts[0], parts[1])
            return f"⚔️ تعارض ثبت شد روی <code>{html.escape(parts[0])}</code>"
        except Exception as e:  # noqa: BLE001
            return f"❌ ثبتِ conflict ناموفق: {type(e).__name__}"

    # ── رندرِ تب‌ها ──────────────────────────────────────────────────────────────
    def _render_tab(self, page: str):
        """یک تبِ کابین: سربرگِ mode-color + خلاصهٔ زنده + دکمه‌های card/act + back.
        INV-9: هر خطا → alert + کارتِ خطا؛ loop هرگز نمی‌میرد."""
        try:
            text = self._tab_text(page)
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"cockpit tab error ({page}): {type(e).__name__}: {e}"])
            text = f"❌ خطای رندرِ تبِ <code>{html.escape(page)}</code> — ثبت شد."
        try:
            kb = self._tab_keyboard(page)
        except Exception:  # noqa: BLE001
            kb = {"inline_keyboard": [[{"text": "🔄 منوی اصلی", "callback_data": "menu:main"}]]}
        return {"text": text, "reply_markup": kb}

    def _tab_keyboard(self, page: str) -> dict:
        rows: list[list[dict]] = []
        cards = self.TAB_CARDS.get(page, [])
        for i in range(0, len(cards), 2):
            rows.append([{"text": lbl, "callback_data": f"card:{page}:{k}"}
                         for k, lbl in cards[i:i + 2]])
        acts = {
            "blueprint": [("📸 گرفتنِ baseline", "baseline", "capture")],
            # 2026-07-15 حذفِ دکمه‌های مرده: مصرف‌کنندهٔ beat فقط doctor/consolidate را اجرا می‌کند
            # (_TG_EXEC_SAFE، wiring.py). دکمه‌های ideas/school/ingest صف می‌شدند و هرگز اجرا نمی‌شدند
            # (toastِ دروغینِ «اجرا می‌شود») → حذف شدند تا UI الکی نباشد. اجرای واقعیِ ingest/school
            # از مسیرِ beatِ خودشان (OCTOPUS_WIRE_INGEST/SCHOOL) می‌رود، نه از دکمهٔ تلگرام.
            "brain": [("🧠 تحکیمِ الان", "consolidate", "run")],
            "doctor": [("🩺 اجرای چرخهٔ دکتر", "doctor", "run")],
            "safety": [("❄️ FREEZE", "freeze", "on"),
                       ("🧹 جاروی اثرها", "sweep", "effects"),
                       ("♻️ ری‌استارتِ تمیز", "restart", "organism")],
            "alerts": [("📦 بازتولیدِ بسته", "export", "raw")],
            # 🦾 کنسولِ اندام: توگل‌ها از مسیرِ flag/flaggo (توکن + تأییدِ دومرحله‌ای) + دکتر
            "organs": [("🎨 Lead", "flag", "lead"), ("🖼 Ziman", "flag", "ziman"),
                       ("🗺 Cartographer", "flag", "cartographer"), ("⛏ Mining", "flag", "mining"),
                       ("🩺 اجرای چرخهٔ دکتر", "doctor", "run")],
        }.get(page, [])
        for i in range(0, len(acts), 2):
            rows.append([self._act_btn(lbl, v, k) for lbl, v, k in acts[i:i + 2]])
        if page == "finance":
            # اسکن #35: تبِ مالی می‌گفت «/review بزن» ولی دکمه نداشت — سه میان‌بُرِ مستقیم
            # (acct: → همان handlerهای دستوری؛ نه act: — این‌ها propose-only اند، نه اکشنِ پولی)
            # 2026-07-18: دکمه‌های فارسیِ ساده (UX-SPEC) + راهِ رسیدن به نسخهٔ expert.
            rows.append([{"text": "🧮 دسته‌بندی کن", "callback_data": "acct:review"},
                         {"text": "📋 ثبتِ نهایی", "callback_data": "acct:books"},
                         {"text": "🔄 تازه‌ها", "callback_data": "acct:sync"}])
            rows.append([{"text": "🔬 نسخهٔ کامل (expert)", "callback_data": "acct:finance_expert"}])
        rows.append([{"text": "🏠 منو", "callback_data": "menu:main"}])
        return {"inline_keyboard": rows}

    def _hdr(self, title: str) -> str:
        return (f"{title} · {self._read_mode_color()}\n"
                f"📥 صفِ تأیید: {self._count_pending()}{self._DIV}")

    def _organs_text(self) -> str:
        """🦾 کنسولِ اندام (Wave 1، read-only): لیستِ صادقِ همهٔ legها با وضعیتِ flag + زنده.
        قانونِ راست‌گویی: 🟢 فقط برای flagِ واقعاً روشن؛ leg بدونِ داده = ⚪ اسکلت، نه سبز."""
        rm = self._rm()
        bl = {}
        if rm is not None:
            try:
                st = rm.read_state() or {}
                bl = st.get("business_legs") or {}
                if isinstance(bl.get("business_legs"), dict):   # شکلِ دولایه (فیکسِ P0)
                    bl = bl["business_legs"]
            except Exception:  # noqa: BLE001
                bl = {}
        lines = [self._hdr("🦾 <b>اندام‌ها</b>")]
        on = 0
        for key, label, env, _kind in self.ORGANS:
            if env:
                is_on = self._current_flag(env)
                fstate = "🟢 روشن" if is_on else "⚪ خاموش"
            else:
                is_on = True
                fstate = "◽ همیشه‌روشن"
            cell = bl.get(key) if isinstance(bl, dict) else None
            if isinstance(cell, dict):
                note = str(cell.get("signal") or cell.get("note") or "")[:44]
                live_txt = ("🟢 زنده" if cell.get("live") else "⚪ اسکلت") + \
                           (f" — {html.escape(note)}" if note else "")
            elif env and is_on:
                live_txt = "روشن (منتظرِ داده)"
            elif env:
                live_txt = "خاموش"
            else:
                live_txt = "—"
            if is_on:
                on += 1
            lines.append(f"{label}: {fstate} · {live_txt}")
        # موج ۲: اندام‌های owner-ساختِ رجیستری (data-driven، اسکلت تا دادهٔ واقعی)
        customs = self._read_organ_registry()
        for o in customs:
            lbl = o.get("label") or o.get("key")
            live = bool(o.get("live"))
            lines.append(f"🆕 {html.escape(str(lbl))}: ◽ رجیستری · "
                         + ("🟢 زنده" if live else "⚪ اسکلت"))
        lines.append(self._DIV.strip())
        lines.append(f"🟢 فعالِ built-in: {on}/{len(self.ORGANS)} · 🆕 owner-ساخت: {len(customs)}")
        lines.append("<i>فعال/غیرفعال: دکمه‌ها (تأییدِ دومرحله‌ای، بوتِ بعدی) · 🩺 دکتر.\n"
                     "ساختِ اندامِ نو: <code>/neworgan &lt;نام&gt;</code> سپس <code>/organ-approve</code>.</i>")
        return "\n".join(lines)

    # ── 💰 دارایی‌ها/حساب — نظارتِ داراییِ کل + دفترِ شخصی/مشترک (فقط‌خواندنی) ────────
    def _finance_data(self):
        """(asset_map_status, personal_status) — دو ماژولِ فقط‌خواندنیِ _ops/legs. fail-soft:
        هر کدام None اگر ماژول غایب/خطا (→ کارتِ «خاموش/خالی»ِ صادق). صفر mutation، صفر settle،
        صفر جابه‌جاییِ پول. seamِ تزریق برای تست (تست این متد را override می‌کند)."""
        import sys as _s
        legs_dir = str(_HERE.parent / "legs")
        if legs_dir not in _s.path:
            _s.path.insert(0, legs_dir)
        asset = personal = None
        try:
            import asset_map as _am
            asset = _am.asset_map_status()
        except Exception:  # noqa: BLE001 — ماژول/پرچم غایب یا خطا → خاموش (هرگز عددِ ساختگی)
            asset = None
        try:
            import personal_ledger as _pl
            personal = _pl.personal_status()
        except Exception:  # noqa: BLE001
            personal = None
        return asset, personal

    def _finance_text(self) -> str:
        """📊 «وضعِ من» — نسخهٔ فارسیِ سادهٔ بی‌اصطلاح برای آرمین/عباس (UX-SPEC §۳.۱، 2026-07-18).
        جایگزینِ نسخهٔ expert که پر از Dr/Cr / خالصِ بانکی / ATO / سنتِ سازگار بود. داده‌ها از
        همون accountant.network_summary_card میاد (PII-safe، فقط تجمیع). هیچ منطقی عوض نشده —
        فقط رندر. برای نسخهٔ کاملِ expert: _finance_text_expert (یا /finance?expert=1 در آینده)."""
        net = self._network_summary()
        lines = [self._hdr("📊 <b>وضعِ من</b>")]
        if not net or not net.get("live"):
            note = str((net or {}).get("note", "")).strip()
            tail = (" — " + html.escape(note[:90])) if note else " — فعلاً داده‌ای وصل نیست."
            lines.append("⚪ چیزی برای نشان دادن نیست" + tail)
            lines.append("<i>برای به‌روزرسانی: /sync</i>")
            lines.append(self._DIV.strip())
            lines.append("<i>🟢 فقط‌خواندنی — هیچ پولی جابه‌جا نمی‌شه.</i>")
            return "\n".join(lines)
        # نمایشِ اعداد با ~ (تقریبیِ دوستانه — RD-001 مبلغِ دقیق را پذیرفت ولی برای خلاصه،
        # ~ نشانهٔ «این خلاصه‌ست نه گزارشِ نهاییِ مالیاتی» است). هیچ گردکردن؛ مقدارِ دقیق.
        def _fa_amt(x) -> str:
            try:
                return f"~${abs(float(x)):,.0f}"
            except (TypeError, ValueError):
                return html.escape(str(x))
        rev = net.get("client_revenue"); assoc = net.get("assoc_total")
        wage = net.get("wage_total"); wage_days = net.get("wage_days")
        armin = net.get("armin_net"); abbas = net.get("abbas_net")
        as_of = html.escape(str(net.get("as_of", ""))[:10])
        if as_of:
            lines.append(f"<i>تا {as_of}</i>")
        # بخشِ درآمد/خرج/حقوق (داده از network_summary_card)
        if rev is not None:
            lines.append(f"💰 اومد: {_fa_amt(rev)}  (درآمدِ مشتری‌ها)")
        if assoc is not None:
            lines.append(f"💸 رفت: {_fa_amt(assoc)}  (پیمانکارها)")
        if wage is not None:
            wd = f"  (~{wage_days} روز)" if isinstance(wage_days, (int, float)) else ""
            lines.append(f"👷 حقوقِ آرمین: {_fa_amt(wage)}{wd}")
        lines.append("─────────────────")
        # مابه‌التفاوتِ آرمین/عباس (جایگزینِ «تسویهٔ مشترک»)
        lines.append("💵 مابه‌التفاوتِ آرمین و عباس:")
        if armin is not None:
            try:
                av = float(armin)
                tag = "از جیبِ خودش رفته" if av < 0 else "بیشتر دریافت کرده"
                lines.append(f"  آرمین: {_fa_amt(armin)}  ({tag})")
            except (TypeError, ValueError):
                lines.append(f"  آرمین: {html.escape(str(armin))}")
        if abbas is not None:
            try:
                bv = float(abbas)
                tag = "تو حسابِ بیزنس مانده" if bv >= 0 else "بدهکار"
                lines.append(f"  عباس:  {_fa_amt(abbas)}  ({tag})")
            except (TypeError, ValueError):
                lines.append(f"  عباس:  {html.escape(str(abbas))}")
        lines.append("")
        # جایگزینِ «✅ سنتِ سازگار»: «عدد‌ها می‌خونن»
        rec = "✅ عدد‌ها می‌خونن" if net.get("reconciled") else "⚠️ عدد‌ها نمی‌خونن (داده ناقص)"
        lines.append(rec)
        c = net.get("counts") or {}
        confirmed = c.get("confirmed", 0); needs = c.get("needs_review", 0)
        lines.append("")
        lines.append(f"📋 {confirmed} موردِ تأییدشده · {needs} موردِ بدونِ دسته")
        if needs > 0:
            lines.append("   <i>برای دسته‌بندی: /review</i>")
        lines.append(self._DIV.strip())
        lines.append("<i>«این خلاصهٔ داخلیه؛ گزارشِ نهاییِ مالیاتی با حسابداره.»</i>")
        lines.append("<i>🟢 فقط‌خواندنی — هیچ پولی جابه‌جا نمی‌شه.</i>")
        return "\n".join(lines)

    def _finance_text_expert(self) -> str:
        """💰 دارایی‌ها/حساب (نسخهٔ expert / کامل) — نقشهٔ نظارتِ دارایی (asset_map) + دفترِ
        شخصی/مشترک (personal_ledger). برای مالک/توسعه‌دهنده. آرمین/عباس _finance_text ساده
        را می‌بینند. data-driven و فقط‌خواندنی؛ صفر settle/جابه‌جاییِ پول."""
        asset, personal = self._finance_data()
        lines = [self._hdr("💰 <b>دارایی‌ها/حساب (expert)</b>")]

        # ── ۱) نقشهٔ نظارتِ دارایی (فقط سیگنالِ whitelist شده از asset_map) ──
        assets = (asset or {}).get("assets") or []
        if not assets:
            lines.append("🗺 <b>نقشهٔ دارایی</b>: ⚪ خاموش/خالی — asset_map در دسترس نیست.")
        else:
            cats = (asset or {}).get("categories", "—")
            stale = (asset or {}).get("stale_count", 0)
            lines.append(f"🗺 <b>نقشهٔ دارایی</b>: {cats} دسته · {stale} کهنه")
            for a in assets[:8]:
                live = "🟢" if a.get("live") else "⚪"
                leg = html.escape(str(a.get("leg", "?")))
                cat = html.escape(str(a.get("category", "?")))
                sig = html.escape(str(a.get("signal", "unknown"))[:60])
                age = a.get("age_days")
                age_txt = (f" · {age:.0f}روز کهنگی"
                           if isinstance(age, (int, float)) and not isinstance(age, bool)
                           else "")
                lines.append(f"{live} {leg} ({cat}): {sig}{age_txt}")
            props = (asset or {}).get("proposals") or []
            if props:
                lines.append("💡 پیشنهادها (advisory — تأییدِ خودت، صفر اجرا):")
                for p in props[:3]:
                    lines.append(f"• {html.escape(str(p)[:130])}")

        lines.append(self._DIV.strip())

        # ── ۲) دفترِ شخصی/مشترک — فقط ترازِ تجمیعی + رشتهٔ تسویه (هرگز تراکنش/شماره‌حساب) ──
        if not personal or not personal.get("live"):
            note = str((personal or {}).get("note", "")).strip()
            tail = (" — " + html.escape(note[:90])) if note else " — ledger پر نشده."
            lines.append("🧾 <b>دفترِ شخصی/مشترک</b>: ⚪ خالی" + tail)
        else:
            bal = personal.get("balance") or {}
            cur = html.escape(str(bal.get("currency", "AUD")))
            per = bal.get("per_party") or {}
            lines.append("🧾 <b>دفترِ شخصی/مشترک</b> (فقط ترازِ تجمیعی):")
            for party, plabel in (("armin", "آرمین"), ("abbas", "عباس")):
                pd = per.get(party) or {}
                nw, cf = pd.get("net_worth"), pd.get("cashflow")
                if nw is not None or cf is not None:
                    lines.append(f"• {plabel}: ثروتِ خالص {nw} · جریانِ نقدی {cf} {cur}")
            ato = bal.get("entity_ato") or {}
            if ato.get("net_before_tax") is not None:
                lines.append(f"• واحدِ ATO-NSW: خالصِ پیش‌از‌مالیات {ato.get('net_before_tax')} {cur}")
            prop = str(personal.get("proposal", "")).strip()
            if prop:
                lines.append("⚖️ تسویهٔ مشترک: " + html.escape(prop[:220]))

        lines.append(self._DIV.strip())

        # ── ۳) شبکهٔ حسابدار (PocketSmith زنده، تجمیعِ PII-امن از accountant.network_summary_card) ──
        # هرگز نامِ مشتری/طرف‌حساب/desc/شماره‌حساب؛ فقط خالصِ تجمیعیِ آرمین/عباس + جمع‌های بی‌نام.
        net = self._network_summary()
        if not net or not net.get("live"):
            note = str((net or {}).get("note", "")).strip()
            tail = (" — " + html.escape(note[:90])) if note else ""
            lines.append("🌐 <b>شبکهٔ حساب</b>: ⚪ خاموش/خالی" + tail)
        else:
            # صادق: این علامت فقط «سازگاریِ داخلیِ سنت» را اثبات می‌کند (بی‌نشتِ گِردکردن)،
            # نه تطبیقِ چند-منبعی با صورت‌حسابِ بانک. برچسبِ 'tie-out' گمراه بود (green-lie).
            rec = "✅ سنتِ سازگار" if net.get("reconciled") else "⚠️ ناسازگار"
            as_of = html.escape(str(net.get("as_of", ""))[:10])
            lines.append(f"🌐 <b>شبکهٔ حساب</b> ({net.get('unique', '?')} تراکنش · {rec}"
                         + (f" · تا {as_of}" if as_of else "") + "):")
            # «خالصِ بانکی» = جمعِ جبریِ همه (هم‌ترازِ اپِ PocketSmith)؛ نه netِ تحلیلیِ report()
            lines.append(f"• آرمین: خالصِ بانکی {html.escape(str(net.get('armin_net', '?')))} · "
                         f"عباس: خالصِ بانکی {html.escape(str(net.get('abbas_net', '?')))} AUD")
            lines.append(f"• درآمدِ مشتری‌ها: {html.escape(str(net.get('client_revenue', '?')))} · "
                         f"به طرف‌حساب‌ها: {html.escape(str(net.get('assoc_total', '?')))} AUD")
            # حقوق بخشی از خالصِ بانکیِ آرمین است (نه اضافه بر آن) — تا دوبار خوانده نشود
            lines.append(f"• از این، حقوقِ آرمین: {html.escape(str(net.get('wage_total', '?')))} AUD "
                         f"(~{net.get('wage_days', '?')} روز)")
            c = net.get("counts") or {}
            lines.append(f"• تأیید {c.get('confirmed', 0)} · خودکار {c.get('auto', 0)} · "
                         f"در صفِ مرورِ تو {c.get('needs_review', 0)}")

        lines.append(self._DIV.strip())

        # ── ۴) ریلِ شرکت (ATO) — اپِ حسابداریِ حرفه‌ای via company_books (two-rails) ──
        lines += self._company_lines()

        # ── ۵) دفترِ داخلیِ خانوادگی (ledger_core) — تسویهٔ آرمین↔عباس، نه ATO ──
        lines += self._ledger_lines()

        lines.append(self._DIV.strip())
        lines.append("<i>🟢 read-only — این تب هیچ‌چیزی را settle/جابه‌جا نمی‌کند. "
                     "فقط سیگنال + ترازِ تجمیعی؛ هرگز تراکنشِ منفرد یا شماره‌حساب.</i>")
        return "\n".join(lines)

    def _company_lines(self) -> list:
        """ریلِ شرکت (ATO) — وضعِ اتصالِ اپِ حسابداری + اینویس‌ها. PII/secret-free، fail-soft."""
        import sys as _s
        legs = str(_HERE.parent / "legs")
        if legs not in _s.path:
            _s.path.insert(0, legs)
        try:
            import company_books as _cbk
            st = _cbk.status()
        except Exception:  # noqa: BLE001
            return ["🏢 <b>ریلِ شرکت (ATO)</b>: ⚪ در دسترس نیست."]
        if not st.get("wired"):
            note = html.escape(str(st.get("note", ""))[:90])
            return [f"🏢 <b>ریلِ شرکت (ATO)</b>: ⚪ {note}"]
        org = html.escape(str(st.get("org", "") or "وصل"))
        out = [f"🏢 <b>ریلِ شرکت (ATO)</b>: 🟢 {org} — دفترِ مالیاتی داخلِ اپ"]
        try:
            import company_books as _cbk2
            li = _cbk2.list_invoices(limit=50)
            if li.get("ok"):
                inv = li.get("invoices") or []
                drafts = sum(1 for i in inv if str(i.get("status", "")).upper() == "DRAFT")
                out.append(f"• اینویس‌ها: {len(inv)} اخیر · {drafts} پیش‌نویسِ منتظرِ تأییدِ تو (داخلِ اپ)")
        except Exception:  # noqa: BLE001
            pass
        return out

    def _ledger_lines(self) -> list:
        """خلاصهٔ دفترِ داخلیِ خانوادگی (آرمین↔عباس): جمعِ Dr/Cr + سلامت + صفِ ثبت. PII-safe."""
        import sys as _s
        legs = str(_HERE.parent / "legs")
        if legs not in _s.path:
            _s.path.insert(0, legs)
        try:
            import ledger_core as _lc
            import journal_bridge as _jb
            tb = _lc.trial_balance()
            st = _jb.stats()
        except Exception:  # noqa: BLE001
            return ["📚 <b>دفترِ رسمی</b>: ⚪ در دسترس نیست."]
        out = []
        if tb.get("total_debit_cents", 0) == 0 and not tb.get("accounts"):
            out.append("📒 <b>دفترِ داخلی (خانوادگی)</b>: خالی — تأیید در /review، ثبت در /books.")
        else:
            hb = "✅" if tb.get("balanced") else "🔴 نامتوازن!"
            tw = "" if tb.get("trustworthy") else " · ⚠️ فایلِ دفتر نیازِ بازبینی"
            from money import fmt as _fmt  # noqa: WPS433
            out.append(f"📒 <b>دفترِ داخلی (خانوادگی)</b>: Dr {_fmt(tb.get('total_debit_cents', 0))} = "
                       f"Cr {_fmt(tb.get('total_credit_cents', 0))} {hb}{tw}")
        pend = st.get("proposed", 0)
        if pend:
            out.append(f"• {pend} ثبتِ پیشنهادی منتظرِ تأییدِ توست → /books")
        elif st.get("posted", 0):
            out.append(f"• ثبت‌شده: {st.get('posted', 0)} · ردشده: {st.get('rejected', 0)}")
        gstp = st.get("posted_gst_pending", 0)
        if gstp:
            out.append(f"• ⏳ {gstp} ثبت هنوز کدِ GST ندارد — با حسابدار کدگذاری شود (RD-002)")
        if st.get("queue_error"):
            out.append("• ⚠️ صفِ ثبت ناخوانا — بازبینیِ دستی")
        return out

    def _network_summary(self):
        """accountant.network_summary_card() — تجمیعِ PII-امنِ شبکهٔ حسابدار (خالصِ تجمیعی،
        بی‌نام). fail-soft → None (→ کارتِ «خاموش/خالی»). seamِ تزریق برای تست."""
        import sys as _s
        legs_dir = str(_HERE.parent / "legs")
        if legs_dir not in _s.path:
            _s.path.insert(0, legs_dir)
        try:
            import accountant as _ac
            out = _ac.network_summary_card()
            return out if isinstance(out, dict) else None
        except Exception:  # noqa: BLE001 — ماژول/فایل غایب یا خطا → خاموش، هرگز crash
            return None

    def _tab_text(self, page: str) -> str:
        rm = self._rm()
        if page == "organs":
            return self._organs_text()
        if page == "finance":
            return self._finance_text()
        if page == "overview":
            st = rm.read_state() if rm else {}
            rep = rm.read_sigma() if rm else {}
            if not st:
                return self._hdr("📊 <b>نمای کلی</b>") + "<i>داده در دسترس نیست.</i>"
            month, today = st.get("month") or {}, st.get("today") or {}
            sig = (rep.get("sigma") or {})
            germ = st.get("germline_lag_h", "—")
            chr_ = st.get("chrono") or {}
            return (self._hdr("📊 <b>نمای کلی</b>")
                    + f"🫀 halted={st.get('halted') or '—'} · frozen={'✅' if st.get('frozen') else 'نه'}"
                      f" · stop={'✅' if st.get('stop_organism') else 'نه'}\n"
                    + f"💵 ماه AU${_safe_float(month.get('aud')):.2f} · امروز US${_safe_float(today.get('usd')):.4f}\n"
                    + f"🔍 suspect-zero: {st.get('suspect_zero_total', '—')} · ⚔️ تعارض: {len(st.get('conflicts') or [])}\n"
                    + f"🦠 σ={sig.get('sigma_effective', '—')} ({sig.get('zone', '—')}) · 💾 germline {germ}h\n"
                    + (f"⏳ سنِ متابولیک: {chr_.get('metabolic_age', '—')} · 🧬 age_tick: {chr_.get('age_tick', '—')}\n"
                       if chr_ else "")
                    + f"🛡 protective: {'فعال' if (st.get('protective_mode') or st.get('protective_skip')) else 'نه'}\n"
                    + "<i>🟢 read-now — این تب هیچ‌چیزی را تغییر نمی‌دهد.</i>")
        if page == "cortex":
            cx = rm.read_cortex() if rm else {}
            st = cx.get("state") or {}
            if not st:
                return (self._hdr("🧠 <b>مغزِ مرکزی</b>")
                        + "🟡 کورتکس هنوز روشن نشده — <code>RUN-CORTEX.bat</code>\n"
                        + "<i>پروسهٔ جدا روی 8772؛ ریتمش را از قلبِ سایه می‌گیرد.</i>")
            # صداقتِ GO-LIVE (2026-07-16): stateِ کهنه (mtime>2h) هرگز «در حالِ فکر» رندر نمی‌شود —
            # مغزی که از 07-10 مرده بود، تا امروز «الان دارد فکر می‌کند» نشان داده می‌شد.
            if cx.get("stale"):
                age_h = cx.get("age_h")
                age_txt = ("؟" if age_h is None else
                           (f"{age_h / 24.0:.1f}d" if age_h >= 24 else f"{age_h:.1f}h"))
                th_old = html.escape(str(st.get("thought", "—"))[:160])
                return (self._hdr("🧠 <b>مغزِ مرکزی</b>")
                        + f"⚫ کورتکس خاموش/کهنه (سن: {age_txt}) — stateِ قدیمی «الان» نیست.\n"
                        + f"💤 آخرین فکرِ ثبت‌شده (کهنه): <i>{th_old}</i>\n"
                        + "راه‌اندازیِ دوباره: <code>RUN-CORTEX.bat</code>\n"
                        + "<i>صداقتِ کابین: تا cortex-state.json تازه نشود، این تب مغز را "
                          "«در حالِ فکر» نشان نمی‌دهد.</i>")
            br = st.get("brains") or {}
            keys = br.get("keys") or {}
            th = html.escape(str(st.get("thought", "—"))[:220])
            align = st.get("alignment") or {}
            return (self._hdr("🧠 <b>مغزِ مرکزی</b>")
                    + f"🧩 coherence مجموعه: <b>{st.get('coherence', '—')}</b> · "
                      f"اعضای کهنه: {len(st.get('stale_members') or [])}\n"
                    + f"⏱ ریتم: هر {(st.get('rhythm') or {}).get('period_s', '—')}s "
                      f"({html.escape(str((st.get('rhythm') or {}).get('source', '')))})\n"
                    + f"🗂 مرتب‌سازی: {'🟢 ' + ' · '.join(align.get('diff', [])) if align.get('changed') else 'ℹ️ ' + html.escape(str(align.get('reason', '—')))}\n"
                    + f"🤖 مغزها: local {'🟢' if br.get('local_model') else '—'} "
                      f"(<code>{html.escape(str(br.get('local_model', '')))}</code>) · "
                      f"fugu {'🔑' if keys.get('fugu') else '⚪ بی‌کلید'} · "
                      f"glm {'🔑' if keys.get('glm') else '⚪ بی‌کلید'} · "
                      f"paid: 🔴 {html.escape(str(br.get('paid_gate', '')))}\n"
                    + f"💭 آخرین فکر: <i>{th}</i>\n"
                    + "<i>مغز جداست؛ فقط کارِ $0 را مرتب می‌کند — پول/merge هرگز (رأی مالک).</i>")
        if page == "blueprint":
            phase = rm.read_phase() if rm else {}
            bcm, sp = (rm.read_bcm() if rm else {}), (rm.read_sparse() if rm else {})
            fish, cht = (rm.read_fisher() if rm else {}), (rm.read_chamber_t() if rm else {})
            return (self._hdr("🧭 <b>بلوپرینت P0–P6</b>")
                    + f"فازِ جاری: <code>{html.escape(str(phase.get('current_phase', 'نامشخص')))}</code>\n"
                    + f"P3 BCM: {'🟢 داده دارد' if bcm else 'ℹ️ هنوز نچرخیده'} · "
                      f"P4 Sparse: {'🟢' if sp else '🟡 OFF/بی‌فایل'}\n"
                    + f"P5 Chamber-T: {'🔴 فایلِ دما هست!' if cht else '🟢 RED خاموش (طبقِ طراحی)'}\n"
                    + f"P6 Fisher: {('🟢 cond=' + str(fish.get('fisher_condition_number'))) if fish else '🟡 OFF/بی‌فایل'}\n"
                    + "<i>رأیِ فازها human-only است — از کارتِ RFC، نه دکمه (§۲.۵).</i>")
        if page == "brain":
            cons = rm.read_consolidation() if rm else {}
            lat, idea = (rm.read_latent() if rm else {}), (rm.read_idea() if rm else {})
            return (self._hdr("🧠 <b>حافظه و مغز</b>")
                    + f"تحکیم: {'🟢 ' + str(len(cons.get('cycles', cons) if isinstance(cons, dict) else [])) + ' رکورد' if cons else '🟡 بی‌داده'}\n"
                    + f"Latent R³²: {'🟢 ' + str(len(lat.get('vectors', lat))) + ' کلید' if lat else '🟡 بی‌فایل'}\n"
                    + f"ایده-گراف: {('🟢 ' + str(idea.get('nodes_count', '?')) + ' نوت · ' + str(idea.get('edges_count', '?')) + ' یال') if idea else '🟡 هنوز تحلیلی ننوشته'}\n"
                    + "🏃 اسپرینت: 🟡 stub (ساخته‌شده، tick نشده)\n"
                    + "<i>کنترل‌ها out-of-band ثبت می‌شوند — هیچ اجرای inline (INV-7).</i>")
        if page == "doctor":
            n_rfc = len(self._pending_rfc)
            ch = rm.read_chrono_ro() if rm else {}
            eff = (ch.get("effects_by_status") or {})
            caps = (rm.read_capabilities() if rm else {"flags": {}})["flags"]
            # جلسه ۴۶: RFCهای persistشده (با restart گم نمی‌شوند) + وضعیتِ apply_merge
            rfc_persist = (rm.read_doctor_rfcs() if rm else {}) or {}
            all_rfcs = rfc_persist.get("rfcs") or []
            merged = sum(1 for r in all_rfcs if r.get("status") == "merged")
            am_on = os.environ.get("OCTOPUS_WIRE_APPLY_MERGE", "1") == "1"
            hg_on = os.environ.get("OCTOPUS_WIRE_HUMAN_APPEND_GUARD") == "1"
            return (self._hdr("🩺 <b>دکتر و تکامل</b>")
                    + f"🔧 پیشنهادها: {len(all_rfcs)} ذخیره ({merged} اعمال‌شده) · اثر: {eff or '—'}\n"
                    + f"✅ تأییدِ تو اثرِ واقعی دارد: {'🟢 بله' if am_on else '🟡 نه'} · "
                      f"🔒 امضای انسانی جعل‌ناپذیر: {'🟢 بله' if hg_on else '🟡 نه'}\n"
                    + f"⏰ برنامه‌ریز: {'🟢' if caps.get('OCTOPUS_WIRE_SCHEDULER') else '🟡 خاموش'} · "
                      f"🩹 خودترمیم: {'🟢' if caps.get('OCTOPUS_WIRE_SELFHEAL') else '🟡 خاموش'} · "
                      f"🔭 خودشناسی: {'🟢' if caps.get('OCTOPUS_WIRE_EPISTEMICS') else '🟡 خاموش'}\n"
                    + "<i>سیستم خودش را بهتر می‌کند، ولی هر تغییرِ جدی اول از تو می‌پرسد.</i>")
        if page == "money":
            tel = rm.read_telemetry() if rm else {}
            fit = rm.read_fitness() if rm else {}
            ok, why = self._live_gate_status()
            return (self._hdr("💰 <b>پول و متابولیسم</b>")
                    + f"💵 ماه: {((tel.get('month') or {}).get('aud', 0)) if tel.get('month') else (tel.get('genome') or {}).get('cost_musd', 0)} · "
                      f"suspect-zero: {tel.get('suspect_zero_total', '—')}\n"
                    + f"📊 fitness: {'authoritative' if fit.get('authoritative') else '🟡 سایه (درست — تا ۲۸ روز)'}\n"
                    + f"🔒 live-gate: {'🟢 ' + why if ok else '🔴 ' + why}\n"
                    + f"🤖 گاورنرِ LLM: {self._activation_gate_line('ACTIVATION-GOVERNOR-LLM.flag')}\n"
                    + "<i>تنها settleِ پول = کارتِ تأییدِ موجود؛ reconcile/epoch دکمه ندارند (§۲.۵).</i>\n"
                    + "<i>ثبتِ کوت: <code>/claim ATTR-ID | ref | مبلغ</code> · "
                      "تعارض: <code>/conflict ATTR-ID | دلیل</code></i>")
        if page == "school":
            sch = rm.read_school() if rm else {}
            aw = sch.get("awareness") or {}
            if sch.get("_stale"):  # عددِ کهنه هرگز «فعلی» رندر نمی‌شود (هم‌قراردادِ channels/cortex)
                _age = sch.get("_age_h")
                _ad = f"{int(_age // 24)}d" if isinstance(_age, (int, float)) else "?"
                return (self._hdr("🎓 <b>مدرسه</b>")
                        + f"⚪ کهنه ({_ad}) — نویسندهٔ زنده ندارد (SLA=72h · snapshot {sch.get('_snapshot_ts', '?')})\n"
                        + f"<i>آخرین ثبت: میانگین {sch.get('mean', '—')} · {len(aw)} سلول — به‌عنوان «فعلی» قابل‌اتکا نیست.</i>")
            mean = sch.get("mean", (sum(aw.values()) / len(aw)) if aw else None)
            return (self._hdr("🎓 <b>مدرسه</b>")
                    + f"آگاهیِ میانگین: {mean if mean is not None else '—'} · سلول‌ها: {len(aw)}\n"
                    + f"🔥 روشن‌ترین: {max(aw, key=aw.get) if aw else '—'}\n"
                    + "🔌 آوران: 🟡 transient (persist نشده — شفاف)\n"
                    + "<i>یادگیری/ingest از صفِ out-of-band می‌روند ($0، propose-only).</i>")
        if page == "safety":
            st = rm.read_state() if rm else {}
            caps = rm.read_capabilities() if rm else {"profile": "?", "flags": {}}
            n_on = sum(1 for v in caps["flags"].values() if v)
            ok, why = self._live_gate_status()
            return (self._hdr("🛡️ <b>ایمنی</b>")
                    + f"🛑 halted={st.get('halted') or '—'} · ❄️ frozen={'✅' if st.get('frozen') else 'نه'} · "
                      f"STOP={'✅' if st.get('stop_organism') else 'نه'}\n"
                    + f"🔒 live-gate: {'🟢' if ok else '🔴'} {why}\n"
                    + f"🚦 flagها: {n_on}/{len(caps['flags'])} روشن · پروفایل: <code>{html.escape(str(caps.get('profile')))}</code>\n"
                    + f"📡 لوله: {'🟢 wired' if self.wired else '⚪ قطع'} (توکن masked: {_mask_token(self._token)})\n"
                    + "<i>فایل‌ها authoritativeاند؛ بات فقط trigger است (INV-4).</i>")
        if page == "alerts":
            rules = rm.rules() if rm else []
            g = sum(1 for r in rules if r["status"] == "🟢")
            y = sum(1 for r in rules if r["status"] == "🟡")
            rr = sum(1 for r in rules if r["status"] == "🔴")
            tail = rm.tail_governor_alerts(60) if rm else []
            warns = sum(1 for ln in tail if "⚠" in ln)
            return (self._hdr("🚨 <b>هشدارها و خام</b>")
                    + (f"چکِ سلامت: {g} 🟢 · {y} 🟡 · {rr} 🔴 (از {len(rules)})\n" if rules
                       else "چکِ سلامت: ℹ️ بسته/داده در دسترس نیست\n")
                    + f"هشدارهای اخیرِ گاورنر: {warns} ⚠\n"
                    + "<i>mirrorهای خام پس از redaction نمایش داده می‌شوند (INV-12).</i>")
        return "<i>تبِ ناشناخته.</i>"

    def _hybrid_heart_lines(self, hh: dict) -> str:
        """HH-P7: خطوطِ قلبِ ترکیبی برای کارتِ ضربان. fail-soft (فایلِ غایب → 🟡)؛
        دلایلِ سیم از فایلِ سایه (INV-7 — هیچ importِ heart در poll-thread)."""
        try:
            sh = hh.get("shadow") or {}
            sigs = hh.get("signals") or {}
            sp = hh.get("setpoint") or {}
            lock = (hh.get("lock") or {}).get("status") or {}
            sim = hh.get("sim") or {}
            if not (sh or sigs or lock or sim):
                return ("\n🫀 قلبِ ترکیبی: 🟡 هنوز سایه‌ای ثبت نشده "
                        "(<code>OCTOPUS_WIRE_HEART</code> خاموش — طبقِ طراحی)")
            v = (sigs.get("velocity") or {}).get("velocity_per_hr")
            cpi = (sigs.get("cpi") or {}).get("cpi_0_1")
            d = (sigs.get("delta_self") or {}).get("delta_self_live")
            band = (f"[{sp.get('viable_band_lo', '—')}..{sp.get('viable_band_hi', '—')}]"
                    if sp else "[پیش‌فرض 0.5..6.0]")
            wire = (sh.get("production_wire") or {})
            reasons = wire.get("reasons") or []
            first = html.escape(str(reasons[0])) if reasons else ""
            def _lk(name):
                s = lock.get(name)
                return "✅" if s == "locked" else ("⛔" if s else "—")
            return (
                "\n🫀 <b>قلبِ ترکیبی (سایه)</b>\n"
                + f"period سایه: {sh.get('period_s', '—')}s (tick واقعی: 300s) · "
                  f"σ={((sh.get('signal') or {}).get('sigma_now', '—'))}\n"
                + f"velocity: {v if v is not None else '—'}/hr · باندِ هدف: {band} · "
                  f"CPI: {cpi if cpi is not None else '—'} · Δ_self: {d if d is not None else '—'}\n"
                + f"قفل‌ها: Δ {_lk('delta_self')} · E_shadow {_lk('e_shadow')} · "
                  f"I_pred {_lk('i_pred')} (gates-nothing) · SIM {'✅' if sim.get('sim_pass') else '⛔'} · "
                  f"Gate-0 {'✅' if sh.get('gate0_live_producer') else '🟡 در حالِ جمعِ نمونه'}\n"
                + (f"🔌 سیمِ زنده: 🟢 باز" if wire.get("open")
                   else f"🔌 سیمِ زنده: 🔴 بسته ({len(reasons)} شرط) — {first}")
                + f"\n📈 setpoint epoch: {sp.get('epoch_seq', '—')} · "
                  f"<i>Doctor فقط باند می‌نویسد؛ نرخ ظاهر می‌شود (ADR-001)</i>")
        except Exception:  # noqa: BLE001 — کارت هرگز کرش نمی‌کند (INV-7)
            return "\n🫀 قلبِ ترکیبی: 🟡 خطای خواندنِ state (fail-soft)"

    # ── رندرِ کارت‌های جزئی ──────────────────────────────────────────────────────
    def _render_card(self, tab: str, key: str) -> str:
        rm = self._rm()
        nod = "<i>داده در دسترس نیست.</i>"

        def _j(d, *keys, default="—"):
            cur = d
            for k in keys:
                if not isinstance(cur, dict):
                    return default
                cur = cur.get(k)
            return default if cur is None else cur

        if (tab, key) == ("overview", "vitals"):
            return self.status_report()          # resurface T-5 (فقط‌خواندنی)
        if (tab, key) == ("overview", "heart"):
            st = rm.read_state() if rm else {}
            ch = rm.read_chrono_ro() if rm else {}
            cstat = st.get("chrono") or {}
            legs = cstat.get("legs") or {}
            legs_txt = (f"alive={legs.get('alive', '—')}/susp={legs.get('suspected', '—')}"
                        f"/failed={legs.get('failed', '—')}" if isinstance(legs, dict) else str(legs))
            # HH-P7: بخشِ قلبِ ترکیبی (velocity/باند/CPI/قفل‌ها/predicate) — فقط‌خواندنی
            hh = rm.read_heart() if rm else {}
            hh_txt = self._hybrid_heart_lines(hh)
            return ("♥️ <b>ضربان</b>" + self._DIV
                    + f"beat: {cstat.get('beat', '—')} · age_tick: {cstat.get('age_tick', '—')} · "
                      f"سنِ متابولیک: {cstat.get('metabolic_age', '—')}\n"
                    + f"HLC: <code>{html.escape(str(cstat.get('hlc', '—')))}</code>\n"
                    + f"پاها: {html.escape(legs_txt)} · اثرهای معلق: {cstat.get('effects_pending', '—')}\n"
                    + f"chrono.db: {('🟢 ' + str((ch.get('beats') or {}).get('count', '?')) + ' ضربان') if ch else '🟡 خوانا نیست/قفل'}"
                    + (f" · اثرها: {ch.get('effects_by_status')}" if ch.get('effects_by_status') else "")
                    + hh_txt)
        if (tab, key) == ("overview", "legs"):
            try:
                import sys as _sys
                from pathlib import Path as _P
                _ops = _P(__file__).resolve().parents[1]
                if str(_ops) not in _sys.path:
                    _sys.path.insert(0, str(_ops))
                from brain.cockpit import LEGS
                lines = [f"{lg['icon']} <b>{html.escape(lg['name'])}</b> {lg['color']} — "
                         f"{html.escape(lg['desc'])}" for lg in LEGS]
                return "🐙 <b>۶ پا</b>" + self._DIV + "\n".join(lines)
            except Exception:  # noqa: BLE001
                return "🐙 <b>۶ پا</b>" + self._DIV + nod
        if (tab, key) == ("overview", "projects"):
            return ("📁 <b>پروژه‌ها</b>" + self._DIV
                    + "mirror کاملِ پروژه‌ها در پنلِ محلی است: <code>http://127.0.0.1:8790/projects</code>\n"
                    + "<i>(اسکنِ vault در poll-thread اجرا نمی‌شود — INV-7)</i>")
        if (tab, key) == ("blueprint", "phases"):
            ph = rm.read_phase() if rm else {}
            if not ph:
                return "🧭 <b>فازها</b>" + self._DIV + nod
            return ("🧭 <b>فازها</b>" + self._DIV
                    + f"<pre>{html.escape(json.dumps(ph, ensure_ascii=False, indent=1)[:900])}</pre>")
        if (tab, key) == ("blueprint", "baselines"):
            try:
                import sys as _sys
                from pathlib import Path as _P
                _ops = _P(__file__).resolve().parents[1]
                if str(_ops) not in _sys.path:
                    _sys.path.insert(0, str(_ops))
                import baseline as _b
                items = _b.get_all_baselines()
                lines = [f"• <code>{html.escape(str(x.get('phase_id', '?')))}</code> "
                         f"{html.escape(str(x.get('label', '')))} · {str(x.get('ts', ''))[:16]}"
                         for x in items[-8:]]
                return "📸 <b>baselineها</b>" + self._DIV + ("\n".join(lines) or nod)
            except Exception:  # noqa: BLE001
                return "📸 <b>baselineها</b>" + self._DIV + nod
        if (tab, key) == ("blueprint", "bcm"):
            b = rm.read_bcm() if rm else {}
            return ("🧬 <b>BCM (P3)</b>" + self._DIV
                    + (f"کلیدها: {len(b.get('weights', b))} · θ/saturation در فایل\n"
                       f"<i>فقط ایندکسِ retrieval هرس می‌شود؛ تاریخچه append-only (I1).</i>"
                       if b else "ℹ️ BCM هنوز نچرخیده (بعد از restart با flag روشن می‌شود)"))
        if (tab, key) == ("blueprint", "sparse"):
            s = rm.read_sparse() if rm else {}
            return ("🕸 <b>Sparse (P4)</b>" + self._DIV
                    + (f"sparsity: {_j(s, 'sparsity_ratio')} · heavy-tail: {_j(s, 'heavy_tail_share')}"
                       if s else "🟡 OFF/بی‌فایل (خارج از profile — عمداً)"))
        if (tab, key) == ("blueprint", "chamber"):
            c = rm.read_chamber_t() if rm else {}
            return ("🌡 <b>Chamber-T (P5) — RED</b>" + self._DIV
                    + ("🔴 فایلِ دما وجود دارد!" if c else "🟢 خاموش — طبقِ طراحی.")
                    + "\n<i>فعال‌سازی فقط با verdict صریحِ مالک؛ دکمهٔ تلگرام عمداً وجود ندارد.</i>")
        if (tab, key) == ("blueprint", "fisher"):
            f = rm.read_fisher() if rm else {}
            return ("📐 <b>Fisher (P6)</b>" + self._DIV
                    + (f"cond: {_j(f, 'fisher_condition_number')} · advisory-only (I4/I6)"
                       if f else "🟡 not-wired — فایلِ fisher-latest.json نیست"))
        if (tab, key) == ("blueprint", "prereg"):
            return ("📋 <b>پیش‌ثبتِ متریک (R13)</b>" + self._DIV
                    + "پیش‌ثبت آرگومان می‌خواهد و از دکمه امن نیست؛ از CLI:\n"
                    + "<code>python -c \"import baseline; baseline.pre_register_metric("
                      "'phase-X','metric',0.5)\"</code>\n"
                    + "<i>ثبت قبل از پیاده‌سازی — جعل‌ناپذیر.</i>")
        if (tab, key) == ("blueprint", "transition"):
            return ("🚪 <b>گذارِ فاز</b>" + self._DIV
                    + "گذارِ فاز governance است و از رجیستریِ RFC می‌رود (نه act) — §۲.۵.\n"
                    + "<i>doctor کارتِ RFC صادر می‌کند؛ همین‌جا merge/رد کن.</i>")
        if (tab, key) == ("brain", "consolidation"):
            c = rm.read_consolidation() if rm else {}
            n = len(c.get("cycles", c) if isinstance(c, dict) else [])
            return ("🧠 <b>تحکیمِ حافظه</b>" + self._DIV
                    + (f"{n} رکورد · منبعِ کانونی neural/consolidation.json" if c else nod))
        if (tab, key) == ("brain", "latent"):
            v = rm.read_latent() if rm else {}
            return ("🌀 <b>Latent R³²</b>" + self._DIV
                    + (f"{len(v.get('vectors', v))} کلید · dim=32" if v else "🟡 بی‌فایل"))
        if (tab, key) == ("brain", "idea"):
            i = rm.read_idea() if rm else {}
            if not i:
                return "💡 <b>ایده-گراف</b>" + self._DIV + "🟡 هنوز تحلیلی ننوشته"
            return ("💡 <b>ایده-گراف</b>" + self._DIV
                    + f"نوت: {i.get('nodes_count', '?')} · یال: {i.get('edges_count', '?')} · "
                      f"شکسته: {len(i.get('broken_targets', []) or [])}\n"
                    + f"هاب‌ها: {', '.join(html.escape(str(h.get('title', h))) for h in (i.get('hubs') or [])[:4]) or '—'}")
        if (tab, key) == ("brain", "hebbian"):
            h = rm.read_hebbian() if rm else {}
            return ("🔗 <b>Hebbian</b>" + self._DIV
                    + (f"{len(h.get('pairs', h))} جفتِ fire-together" if h else "🟡 بی‌فایل"))
        if (tab, key) == ("brain", "sprint"):
            return ("🏃 <b>اسپرینت</b>" + self._DIV
                    + "🟡 stub — ساخته‌شده ولی هرگز tick نشده (شفاف، جعل نمی‌کنیم).")
        if (tab, key) == ("doctor", "rfc"):
            with self._lk:
                items = [(rid, m.get("status"), m.get("summary", "")[:60])
                         for rid, m in self._pending_rfc.items()]
            lines = [f"• <code>{html.escape(str(r))}</code> [{html.escape(str(s))}] "
                     f"{html.escape(str(t))}" for r, s, t in items[:8]]
            return ("🔧 <b>RFCها (این نشست)</b>" + self._DIV
                    + ("\n".join(lines) or "صف خالی است ✅")
                    + "\n<i>merge پشتِ flag و با ضمیمهٔ انسانی (مسیرِ موجودِ rfc:).</i>")
        if (tab, key) == ("doctor", "box"):
            b = rm.read_box() if rm else {}
            return ("📦 <b>جعبهٔ دکتر (B0–B4)</b>" + self._DIV
                    + (f"<pre>{html.escape(json.dumps(b, ensure_ascii=False, indent=1)[:800])}</pre>"
                       if b else "🟡 not-wired — نیازمندِ persist در doctor (doctor_box.json)"))
        if (tab, key) == ("doctor", "evolution"):
            return ("🧬 <b>تکاملِ RFC</b>" + self._DIV
                    + "🟡 گزارشِ evolution هنوز persist نمی‌شود (not-wired — شفاف).\n"
                    + "<i>tournament/measured_lift پشتِ flag، propose-only.</i>")
        if (tab, key) == ("doctor", "epi"):
            e = rm.read_epi() if rm else {}
            return ("🔭 <b>معرفت‌شناسی</b>" + self._DIV
                    + (f"<pre>{html.escape(json.dumps(e, ensure_ascii=False, indent=1)[:700])}</pre>"
                       if e else "🟡 OFF (flag خاموش) — advisory، non-enforcer"))
        if (tab, key) == ("doctor", "scheduler"):
            caps = (rm.read_capabilities() if rm else {"flags": {}})["flags"]
            return ("⏰ <b>دیسپچر/صفِ پیش‌بینی</b>" + self._DIV
                    + f"flag: {'🟢 روشن' if caps.get('OCTOPUS_WIRE_SCHEDULER') else '🟡 OFF'} · "
                      "propose-only (B6)")
        if (tab, key) == ("doctor", "selfheal"):
            caps = (rm.read_capabilities() if rm else {"flags": {}})["flags"]
            on = caps.get("OCTOPUS_WIRE_SELFHEAL")
            return ("🩹 <b>خودترمیم</b>" + self._DIV
                    + f"وضعیت: {'🟢 روشن' if on else '🟡 خاموش'}\n"
                    + "اگر عضوی از کار بیفتد، خودش دوباره راهش می‌اندازد — "
                      "با محدودیتِ حداکثر ۳ بار در ۵ دقیقه تا حلقه نزند.")
        if (tab, key) == ("doctor", "projectf"):
            paused = self._pf_paused()
            npf = self._pf_pending_count()
            t = rm.read_telemetry() if rm else {}
            organs = (t or {}).get("per_organ_alltime_musd") or {}
            pf_spend = next((v for k, v in organs.items()
                             if "project_f" in str(k).lower() or str(k).lower() == "pf"), None)
            status = "⏸ نگه‌داشته" if paused else "🟢 فعال"
            lines = ["🎬 <b>Project-F — کنترل</b>" + self._DIV,
                     f"وضعیت: {status} · پول: 🔒 قفل · مهلت: 2026-07-20",
                     f"در صفِ تأیید: <b>{npf}</b> کار"]
            if pf_spend is not None:
                lines.append(f"مصرفِ ارگان: {pf_spend}μ$")
            lines += ["",
                      "دکمه‌های پایین: نگه‌دار / ادامه. برای تأیید یا ردِ کارها، از منوی اصلی «📮 صف تأیید».",
                      "<i>محتوا و هویت اینجا نشان داده نمی‌شود — فقط کنترل (containment).</i>"]
            return "\n".join(lines)
        if (tab, key) == ("doctor", "lab"):
            kb_note = ("\n<i>شروع: دکمه‌های زیرِ همین کارت. آشکارسازی پس از پایان: "
                       "<code>/reveal exp1</code></i>")
            return "🧪 " + self.lab_status() + kb_note
        if (tab, key) == ("money", "telemetry"):
            t = rm.read_telemetry() if rm else {}
            if not t:
                return "💵 <b>مصرف</b>" + self._DIV + nod
            return ("💵 <b>مصرف</b>" + self._DIV
                    + f"genome: {_j(t, 'genome', 'cost_musd')}μ$ ({_j(t, 'genome', 'events')} رویداد) · "
                      f"brain: {_j(t, 'brain', 'cost_musd')}μ$\n"
                    + f"FX: {_j(t, 'fx_aud_per_usd', 'rate')} ({_j(t, 'fx_aud_per_usd', 'tag')}) · "
                      f"suspect-zero: {t.get('suspect_zero_total', '—')}")
        if (tab, key) == ("money", "organs"):
            t = rm.read_telemetry() if rm else {}
            organs = t.get("per_organ_alltime_musd") or {}
            lines = [f"• <code>{html.escape(str(k))}</code>: {v}μ$" for k, v in list(organs.items())[:10]]
            paint = any("paint" in str(k).lower() for k in organs)
            return ("🫀 <b>ارگان‌ها (R22)</b>" + self._DIV
                    + ("\n".join(lines) or nod)
                    + ("" if paint else "\n🟡 ارگانِ PAINTING غایب — منتظرِ verdict §۵"))
        if (tab, key) == ("money", "fitness"):
            f = rm.read_fitness() if rm else {}
            att = f.get("attribution") or {}
            return ("📊 <b>فیتنس (R10)</b>" + self._DIV
                    + f"authoritative: {'✅' if f.get('authoritative') else '🟡 سایه (درست — تا ۲۸ روز)'}\n"
                    + f"CLAIMED: {att.get('claimed', '—')} · CONFIRMED: {att.get('confirmed', '—')} · "
                      f"هشدارِ یکپارچگی: {len(f.get('integrity_alerts') or [])}")
        if (tab, key) == ("money", "attribution"):
            return ("🧾 <b>درآمد/لیدها</b>" + self._DIV
                    + "ثبتِ لید: <code>/lead نام | ارزش | پا</code>\n"
                    + "ثبتِ کوت (CLAIMED): <code>/claim ATTR-ID | ref | مبلغ</code>\n"
                    + "تعارض: <code>/conflict ATTR-ID | دلیل</code>\n"
                    + "<i>CONFIRMED فقط از reconcile-actor — هیچ دکمهٔ settle (§۲.۵).</i>")
        if (tab, key) == ("money", "cardiac"):
            caps = (rm.read_capabilities() if rm else {"flags": {}})["flags"]
            st = (rm.read_state() if rm else {}).get("cardiac") or {}
            return ("♥️ <b>ضربانِ بودجه (WIRE_BIO)</b>" + self._DIV
                    + f"flag: {'🟢 روشن' if caps.get('OCTOPUS_WIRE_BIO') else '🟡 OFF'}\n"
                    + (f"<pre>{html.escape(json.dumps(st, ensure_ascii=False)[:400])}</pre>" if st else ""))
        if (tab, key) == ("money", "reconcile"):
            caps = (rm.read_capabilities() if rm else {"flags": {}})["flags"]
            return ("🔁 <b>تطبیقِ Track-B (R11)</b>" + self._DIV
                    + f"flag: {'🟢 روشن' if caps.get('OCTOPUS_WIRE_RECONCILE') else '🟡 OFF'}\n"
                    + "<i>reconcile settle-driverِ پول است — دکمهٔ اجرایِ مستقیم عمداً وجود ندارد (§۲.۵).</i>")
        if (tab, key) == ("money", "barbell"):
            caps = (rm.read_capabilities() if rm else {"flags": {}})["flags"]
            return ("⚖️ <b>تخصیصِ باربل (CORE/SATELLITE)</b>" + self._DIV
                    + f"flag: {'🟢 روشن' if caps.get('OCTOPUS_WIRE_BARBELL') else '🟡 OFF'} · propose-only\n"
                    + "<i>ریسکی — فعال‌سازی از تبِ ایمنی (act:flag) با capability-gate.</i>")
        if (tab, key) == ("money", "governor"):
            return ("🤖 <b>گاورنرِ LLM</b>" + self._DIV
                    + f"{self._activation_gate_line('ACTIVATION-GOVERNOR-LLM.flag')} — "
                      "تخصیصِ خودمتریک (allocate_llm) پشتِ گیتِ دوقفله.\n"
                    + "<i>هر فعال‌سازی فقط از کارتِ تأییدِ پول (token → settle) — هیچ triggerِ زودتر.</i>")
        if (tab, key) == ("school", "awareness"):
            s = rm.read_school() if rm else {}
            aw = s.get("awareness") or {}
            mean = s.get("mean", (sum(aw.values()) / len(aw)) if aw else None)
            return ("🎓 <b>آگاهیِ مدرسه (R17)</b>" + self._DIV
                    + (f"میانگین: {mean} · {len(aw)} سلول" if aw or mean else nod))
        if (tab, key) == ("school", "cells"):
            s = rm.read_school() if rm else {}
            aw = s.get("awareness") or {}
            lines = [f"• <code>{html.escape(str(k))}</code>: {v}"
                     for k, v in sorted(aw.items(), key=lambda kv: -kv[1])[:8]]
            return "🧫 <b>سلول‌ها</b>" + self._DIV + ("\n".join(lines) or nod)
        if (tab, key) == ("school", "afferent"):
            return ("🔌 <b>آوران</b>" + self._DIV
                    + "🟡 transient — persist نشده (not-wired؛ شفاف، جعل نمی‌کنیم).")
        if (tab, key) == ("school", "crypto"):
            return ("📈 <b>بریفِ کریپتو</b>" + self._DIV
                    + "🟡 not-wired — خروجیِ summarize_crypto_file هنوز state ندارد.\n"
                    + "درخواست: دکمهٔ «ingest کریپتو» در تبِ مدرسه (out-of-band).")
        if (tab, key) == ("safety", "gates"):
            ok, why = self._live_gate_status()
            return ("🔒 <b>گیت‌ها</b>" + self._DIV
                    + f"live-gate دوقفله: {'🟢' if ok else '🔴'} {why}\n"
                    + f"لوله: {'🟢 wired' if self.wired else '⚪'} · owner-allowlist فعال\n"
                    + "زنجیره: organ → money → capability → live (fail-closed)\n"
                    + "توکن‌ها: پول (_new_token) · act (_new_act_token، تک‌مصرف) · _cteq ثابت‌زمانی")
        if (tab, key) == ("safety", "flags"):
            return self._render_paged("safety", "flags", 1)
        if (tab, key) == ("safety", "germline"):
            st = rm.read_state() if rm else {}
            lag = st.get("germline_lag_h", "—")
            return ("💾 <b>germline (R8)</b>" + self._DIV
                    + f"lag: {lag} ساعت (آستانه: &lt;2h سبز · &lt;26h زرد)")
        if (tab, key) == ("safety", "conflicts"):
            st = rm.read_state() if rm else {}
            c = st.get("conflicts") or []
            return ("⚔️ <b>تعارضِ متابولیک (I3)</b>" + self._DIV
                    + (f"{len(c)} تعارض\n<pre>{html.escape(json.dumps(c, ensure_ascii=False)[:500])}</pre>"
                       if c else "صف خالی ✅")
                    + "\n<i>رفعِ تعارض دستی است — بات auto-clear نمی‌کند.</i>")
        if (tab, key) == ("safety", "integrity"):
            try:
                import sys as _sys
                from pathlib import Path as _P
                _ops = _P(__file__).resolve().parents[1]
                if str(_ops) not in _sys.path:
                    _sys.path.insert(0, str(_ops))
                import baseline as _b
                fp = _b._fingerprint_money_sources(_ops)
                return ("🔏 <b>اثرانگشتِ کدِ پول</b>" + self._DIV
                        + f"<code>{html.escape(str(fp))}</code>")
            except Exception:  # noqa: BLE001
                return "🔏 <b>اثرانگشتِ کدِ پول</b>" + self._DIV + nod
        if (tab, key) == ("safety", "pii"):
            return ("🕵️ <b>گاردِ PII</b>" + self._DIV
                    + "sensory_bus._contains_pii + live_loop.verify_no_pii_in_signals (containment)\n"
                    + "mirrorهای خامِ همین کابین هم از پاسِ PII می‌گذرند (INV-12).")
        if (tab, key) == ("safety", "llm"):
            return ("🧭 <b>مسیرِ LLM</b>" + self._DIV
                    + "host-allowlist + کلید فقط از env + قیمتِ قفل + no-fallback (I9/I10)\n"
                    + f"مناظره: {self._activation_gate_line('ACTIVATION-DEBATE.flag')} "
                      "— topics فقط whitelist (topic-as-data).")
        if (tab, key) == ("safety", "reentry"):
            return self.reentry_packet()
        if (tab, key) == ("alerts", "rules"):
            return self._render_paged("alerts", "rules", 1)
        if (tab, key) == ("alerts", "governor"):
            tail = rm.tail_governor_alerts(30) if rm else []
            body = "\n".join(html.escape(ln) for ln in tail[-15:]) or nod
            return self._redact_pii("🚨 <b>هشدارهای گاورنر (R23)</b>" + self._DIV
                                    + f"<pre>{body[:1500]}</pre>")
        if (tab, key) == ("alerts", "genome"):
            b = (rm.read_bundle() if rm else {}).get("genome_ledger") or {}
            return ("🧬 <b>زنجیرهٔ ژنوم (R14)</b>" + self._DIV
                    + (f"<pre>{html.escape(json.dumps(b, ensure_ascii=False, indent=1)[:700])}</pre>"
                       if b else nod))
        if (tab, key) == ("alerts", "chrono"):
            ch = rm.read_chrono_ro() if rm else {}
            return ("⏱ <b>chrono (R15/R16)</b>" + self._DIV
                    + (f"<pre>{html.escape(json.dumps(ch, ensure_ascii=False, indent=1)[:700])}</pre>"
                       if ch else "🟡 chrono.db خوانا نیست (busy/نبود) — fail-soft"))
        if (tab, key) == ("alerts", "channels"):
            d = rm.read_channels() if rm else {}
            c = d.get("channels") or {}
            # 2026-07-15 راست‌گویی: این snapshot نویسندهٔ زنده ندارد — کهنه هرگز 🟢 نشان داده نمی‌شود.
            stale = bool(d.get("_stale", True))
            lines = [f"• {html.escape(str(n))}: "
                     f"{'⚪' if stale else ('🟢' if i.get('live') else '🔴')} "
                     f"{html.escape(str(i.get('mode', '')))}" for n, i in c.items()]
            hdr = "📡 <b>کانال‌ها</b>"
            if stale:
                hdr += (f"  <i>⚠️ snapshotِ کهنه ({html.escape(str(d.get('_snapshot_ts', '?')))}) "
                        f"— بی‌نویسنده، «زنده» نیست</i>")
            return hdr + self._DIV + ("\n".join(lines) or nod)
        if (tab, key) == ("alerts", "raw"):
            st = rm.read_state() if rm else {}
            raw = json.dumps(st, ensure_ascii=False, indent=1)[:1600]
            return self._redact_pii("🗂 <b>ORGANISM-STATE (خام، redacted)</b>" + self._DIV
                                    + f"<pre>{html.escape(raw)}</pre>")
        if (tab, key) == ("alerts", "log"):
            tail = rm.tail_structured_log(15) if rm else []
            body = "\n".join(html.escape(ln[:160]) for ln in tail) or \
                "🟡 فایلِ لاگِ ساختاریافته پیدا نشد (FileEmitter وصل نیست)"
            return self._redact_pii("📜 <b>لاگِ ساختاریافته</b>" + self._DIV
                                    + f"<pre>{body[:1500]}</pre>")
        if (tab, key) == ("alerts", "requests"):
            reqs = rm.read_requests(8) if rm else []
            lines = [f"• {html.escape(str(r.get('ts', ''))[:16])} "
                     f"<code>{html.escape(str(r.get('verb')))}:{html.escape(str(r.get('key')))}</code> "
                     f"[{html.escape(str(r.get('status', '')))}]" for r in reqs]
            return ("📨 <b>صفِ درخواستِ out-of-band</b>" + self._DIV
                    + ("\n".join(lines) or "صف خالی است ✅")
                    + "\n<i>state/cockpit-requests.jsonl — organism مصرف می‌کند.</i>")
        return nod

    # ── صفحه‌بندی (pg:) ─────────────────────────────────────────────────────────
    def _render_paged(self, tab: str, key: str, n: int, per_page: int = 8):
        """لیست‌های بلند: rules (۲۴ قاعده) و flags (۱۹ flag با دکمهٔ toggle)."""
        rm = self._rm()
        rows_kb: list[list[dict]] = []
        cad_line = ""
        if (tab, key) == ("alerts", "rules"):
            items = rm.rules() if rm else []
            title = "✅ <b>۲۴ قاعدهٔ سلامت</b>"
            render = lambda r: (f"{r['status']} <b>{r['id']}</b> {html.escape(r['label'])} — "  # noqa: E731
                                f"<i>{html.escape(r['evidence'])}</i>")
        else:  # ("safety", "flags")
            caps = rm.read_capabilities() if rm else {"flags": {}, "cadences": {}}
            items = sorted(caps["flags"].items())
            cad = caps.get("cadences") or {}                    # C15: cadenceها زیرِ لیست
            cad_line = (self._DIV + "⏱ <b>cadence</b>: "
                        + " · ".join(f"{html.escape(k.replace('CHRONO_', '').replace('_EVERY_N_BEATS', ''))}={v}"
                                     for k, v in cad.items())) if cad else ""
            title = "🚦 <b>flagهای wiring</b>"
            render = lambda kv: (f"{'🟢' if kv[1] else '⚪'} <code>{html.escape(kv[0])}</code>")  # noqa: E731
        total = max(1, (len(items) + per_page - 1) // per_page)
        n = min(max(1, n), total)
        page_items = items[(n - 1) * per_page: n * per_page]
        body = "\n".join(render(it) for it in page_items) or "<i>خالی</i>"
        if (tab, key) == ("safety", "flags"):
            # دکمهٔ toggle برای هر flagِ این صفحه (act دومرحله‌ای؛ chamber_t عمداً نیست)
            for env_name, on in page_items:
                short = env_name.replace("OCTOPUS_WIRE_", "").lower()
                if short in self.FLAG_KEYS:
                    rows_kb.append([self._act_btn(
                        f"{'🟢' if on else '⚪'} {short} → {'خاموش' if on else 'روشن'}",
                        "flag", short)])
        nav = []
        if n > 1:
            nav.append({"text": "◀️", "callback_data": f"pg:{tab}:{key}:{n - 1}"})
        nav.append({"text": f"{n}/{total}", "callback_data": f"pg:{tab}:{key}:{n}"})
        if n < total:
            nav.append({"text": "▶️", "callback_data": f"pg:{tab}:{key}:{n + 1}"})
        rows_kb.append(nav)
        rows_kb.append([{"text": "⬅️ بازگشت", "callback_data": f"menu:{tab}"}])
        return {"text": f"{title} · صفحهٔ {n}/{total}{self._DIV}{body}{cad_line}",
                "reply_markup": {"inline_keyboard": rows_kb}}


def _attribution_propose(cell: str, expected_aud: float, lead: str = "") -> dict:
    """پلِ lazy به attribution.propose (همان الگوی panel/server.py submit_lead)."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _here = _Path(__file__).resolve().parent   # budget/
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        import attribution  # noqa: WPS433
        return attribution.propose(cell, expected_aud, lead=lead)
    except Exception:  # noqa: BLE001
        return {}


# ─── T-4 · UIِ لاگِ آزمایش (lab N=1): seal/SHA256، no-early-decode، /reveal ───────
# قوانینِ قفل‌شده (lab_seed_data.json governance + blinding_note):
#   • predictionهای مهر-و-موم (b64) هرگز زودتر از end_date decode نشوند.
#   • /start_exp<N> تقویمِ ۱۴روزه را یک‌جا تولید و قفل می‌کند (seed ثابت برای exp2).
#   • /reveal فقط بعد از end_date + verifyِ sha256 محتوای b64.
#   • ضدِ نشتِ انتظار: هیچ ترند/نمودار/تفسیری در طولِ آزمایش نمایش داده نمی‌شود.
# state در _ops/state/lab_state.json (additive؛ بدونِ دست‌زدن به schemaِ chrono).

def _lab_state_path(state_dir=None) -> "pathlib.Path":
    from pathlib import Path
    base = Path(state_dir) if state_dir else Path(__file__).resolve().parents[1] / "state"
    return base / "lab_state.json"


def _load_lab_state(state_dir=None) -> dict:
    p = _lab_state_path(state_dir)
    if not p.exists():
        return {"experiments": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"experiments": {}}


def _save_lab_state(state: dict, state_dir=None) -> None:
    p = _lab_state_path(state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


# ─── offset persistence (restart-safe) ─────────────────────────────────────────
# بدون این، restart نمونهٔ بات → getUpdates از offset=0 → پیام‌های قدیمی دوباره در
# quarantine می‌ریزند (در T-1 خطرِ امنیتی نیست چون شیر بسته، ولی آزاردهنده/پرانرژی است).
# فایلِ کوچکِ atomic: {offset: <last_update_id+1>, saved_at: <iso>}. fail-soft.

def _offset_state_path(state_dir=None) -> "pathlib.Path":
    from pathlib import Path
    base = Path(state_dir) if state_dir else Path(__file__).resolve().parents[1] / "state"
    return base / "telegram_offset.json"


def _load_offset(state_dir=None) -> int:
    p = _offset_state_path(state_dir)
    if not p.exists():
        return 0
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return int(d.get("offset", 0))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0


def _save_offset(offset: int, state_dir=None) -> None:
    """نوشتنِ اتمیکِ offset. fail-soft: شکست به warn می‌رسد، نه crash."""
    from pathlib import Path
    p = _offset_state_path(state_dir)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"offset": int(offset),
                                   "saved_at": _today_iso()}, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(p)
    except OSError:
        pass   # fail-soft: offsetِ حافظه‌ای همچنان در همین ران کار می‌کند


def _today_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _today_str() -> str:
    """تاریخِ امروز (UTC) به‌صورت YYYY-MM-DD. جدا از opslib تا ماژول مستقل بماند."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _add_days(date_str: str, n: int) -> str:
    """تاریخ + n روز. ورودی/خروجی YYYY-MM-DD."""
    from datetime import datetime, timedelta
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=int(n))
        return d.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str


def _read_json_safe(path) -> dict:
    """خواندنِ امنِ JSON از فایل. نبود/خرابی → {}. فقط برای state‌های فقط‌خواندنی."""
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _safe_float(v) -> float:
    """تبدیلِ امن به float؛ نبود/خرابی → 0.0."""
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _cteq(a: str, b: str) -> bool:
    """مقایسهٔ ثابت‌زمانیِ توکن (ضدِ timing-attack)."""
    import hmac
    try:
        return hmac.compare_digest(str(a), str(b))
    except Exception:  # noqa: BLE001
        return False


def _on_human_judgment(judgment: dict, gate=None, ledger=None,
                       ha_token: str | None = None) -> dict:
    """پلِ تنک به chrono.on_human_judgment (lazy import) تا approval_channel به chrono
    وابستهٔ import-time نشود (جلوگیری از circular). فقط هنگامِ approve واقعی لود می‌شود.
    ha_token: توکنِ human-append (جلسه ۴۶) که فقط تلگرام mint می‌کند."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _here = _Path(__file__).resolve().parents[1]   # _ops
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        import chrono  # noqa: WPS433
        return chrono.on_human_judgment(judgment, gate=gate, ledger=ledger,
                                        ha_token=ha_token)
    except Exception:  # noqa: BLE001 — chrono نبود = fail-closed (entry خالی → رد در caller)
        return {}


def _mint_ha_token(approval_id: str, event_type: str = "APPROVAL") -> str | None:
    """توکنِ human-append برای یک approval بساز — فقط اگر گارد پیکربندی شده باشد.
    شکست/گاردِ خاموش → None (→ downgrade در chrono؛ هرگز crash، هرگز بلاکِ settle)."""
    try:
        from human_append_guard import default_guard
        g = default_guard()
        if not g.enabled:
            return None
        safe_id = str(approval_id).replace(".", "-")   # mint نقطه نمی‌پذیرد
        return g.mint(safe_id, event_type)
    except Exception:  # noqa: BLE001
        return None

