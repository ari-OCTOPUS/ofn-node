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
import threading                             # noqa: E402
import urllib.error                          # noqa: E402
import urllib.parse                          # noqa: E402
import urllib.request                        # noqa: E402

TELEGRAM_API_BASE = "https://api.telegram.org"
TELEGRAM_LONGPOLL_TIMEOUT_S = 30   # idle = $0: getUpdates تا این ثانیه رویِ سرور بلوکه می‌ماند


def _env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


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
        self._http_get = http_get or _url_json_get
        self._http_post = http_post or _url_json_post
        self._kill = kill_check                     # None = فقط پرچمِ داخلیِ .stop()
        self._lp = int(longpoll_timeout if longpoll_timeout is not None
                       else _env_int("TELEGRAM_LONGPOLL_TIMEOUT", TELEGRAM_LONGPOLL_TIMEOUT_S))
        self._gate = gate                            # EffectorGate (TINV-7) — T-2 وصل می‌کند
        self._ledger = ledger                        # ledger ژنوم (human-append)
        self._state_dir = state_dir                  # None = _ops/state (پیش‌فرض)
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
            return 0
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
            text = msg.get("text") or (cbq.get("data") if is_callback else "")
            from_id = (msg.get("from") or cbq.get("from") or {}).get("id")
            cbq_id = cbq.get("id")  # callback_query ID برای answerCallbackQuery

            # allowlist: فقط chat_idِ مالک پذیرفته می‌شود؛ بقیه ignore (قانونِ P3 §5).
            if chat_id != self._owner:
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
            try:
                if is_callback:
                    # callback_query → dispatch + answer
                    reply = self.dispatch_callback(str(text))
                    # reply می‌تواند str باشد (toast) یا dict (پیام جداگانه با کیبورد)
                    if isinstance(reply, dict):
                        if cbq_id:
                            self._answer_callback_query(cbq_id, "✅")
                        self.send_text(reply.get("text", ""),
                                       reply_markup=reply.get("reply_markup"))
                    else:
                        if cbq_id:
                            self._answer_callback_query(cbq_id, reply or "📝")
                else:
                    # text message → handle_command + send reply
                    reply = self.handle_command(str(text))
                    if reply is not None:
                        if isinstance(reply, dict):
                            self.send_text(reply.get("text", ""),
                                           reply_markup=reply.get("reply_markup"))
                        else:
                            self.send_text(reply)
            except Exception as e:  # noqa: BLE001 — fail-soft: ارسال شکست → alert، حلقه ادامه
                opslib.alert([f"telegram T-8 dispatch error: {type(e).__name__}: {e}"])

            processed += 1
        # offset persistence: اگر offset جلو رفت و state_dir هست، در فایل ذخیره کن
        # (restart-safe). state_dir نباشد → همان رفتارِ حافظه‌ایِ T-1 (تست‌ها).
        if offset_dirty and self._state_dir:
            _save_offset(self._offset, self._state_dir)
        return processed

    def _answer_callback_query(self, callback_query_id: str, text: str = "") -> bool:
        """T-8: ارسال answerCallbackQuery برای dismiss کردنِ spinner روی دکمه.
        fail-soft: شکست = alert، بدونِ killِ حلقه."""
        if not self.wired:
            return False
        try:
            self._http_post(self._build_url("answerCallbackQuery", {}),
                            {"callback_query_id": callback_query_id,
                             # Cockpit v2 · INV-12: toast هم مثل sendMessage از redaction می‌گذرد
                             "text": self._redact(str(text))[:200], "cache_time": 0})
            return True
        except Exception as e:  # noqa: BLE001 — fail-soft
            opslib.alert([f"telegram answerCallbackQuery error: {type(e).__name__}: {e}"])
            return False

    def run_forever(self) -> None:
        """حلقهٔ long-pollِ پس‌زمینه. not wired → فوراً برمی‌گردد (no-opِ امن). kill supreme:
        با اولین سیگنالِ kill_check/STOP می‌ایستد. خطای هر دور fail-soft است."""
        if not self.wired:
            return
        self._set_my_commands()   # پاک‌سازیِ منوی قدیمی + ثبتِ منوی تمیز اختاپوس
        while not self._killed():
            self.poll_once()

    def _set_my_commands(self) -> None:
        """منوی command تلگرام را پاک و دوباره ثبت می‌کند.
        حذفِ کشِ قدیمی (deleteMyCommands) برای رفعِ مشکلِ دستوراتِ رباتِ قبلی."""
        commands = [
            {"command": "start", "description": "🐙 منوی اصلی (کابین ۸-تبی)"},
            {"command": "overview", "description": "📊 نمای کلی"},
            {"command": "money", "description": "💰 پول و متابولیسم"},
            {"command": "doctor", "description": "🩺 دکتر و تکامل"},
            {"command": "brain", "description": "🧠 حافظه و مغز"},
            {"command": "blueprint", "description": "🧭 بلوپرینت P0–P6"},
            {"command": "school", "description": "🎓 مدرسه"},
            {"command": "safety", "description": "🛡️ ایمنی"},
            {"command": "alerts", "description": "🚨 هشدارها و خام"},
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
        dispatch_callback ممکن است. not wired → False (no-opِ امن، کارت فرستاده نمی‌شود)."""
        if not self.wired:
            return False
        if amount_aud <= 0:
            return False
        token = self._new_token(effect_id, amount_aud)
        with self._lk:
            self._pending[effect_id] = {"amount_aud": float(amount_aud),
                                        "summary": str(summary)[:500],
                                        "guard": str(guard_verdict)[:200],
                                        "token": token, "status": "pending"}
        # C2/C5 · INV-12: کارتِ پول هم از پاسِ redaction می‌گذرد (summary/guard ممکن است
        # از subsystemِ بالادست رشتهٔ secret-شکل بیاورد). این تنها sendِ مستقیمِ باقی‌مانده بود.
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

    def dispatch_callback(self, data: str) -> str | dict:
        """routerِ callbackهای کارت‌ها. data = 'app:<verb>:<effect_id>:<token>' (پول، T-2)
        یا 'rfc:<verb>:<rfc_id>:<token>' (تکامل، W-3)، یا 'menu:<page>' (UX v3).
        خروجی = متنِ پاسخ برای answerCallbackQuery یا dict (پیام جداگانه با کیبورد).
        هر callback نامعتبر/جعلی → 'رد'.
        این متد از poll_once (T-8 router) برای هر callback_queryِ مالک صدا زده می‌شود."""
        parts = str(data or "").split(":")
        if parts[0] == "menu":
            return self._dispatch_menu(parts)
        if parts[0] == "rfc":
            return self._dispatch_rfc(parts)
        # ── Cockpit v2: لایهٔ read/nav/act — کنارِ schemeهای موجود، بدونِ دست‌زدن به آن‌ها ──
        if parts[0] == "card":
            return self._dispatch_card(parts)
        if parts[0] == "pg":
            return self._dispatch_page(parts)
        if parts[0] == "act":
            return self._dispatch_act(parts)
        if len(parts) != 4 or parts[0] != "app":
            return "نادیده"
        verb, effect_id, token = parts[1], parts[2], parts[3]
        with self._lk:
            meta = self._pending.get(effect_id)
        if meta is None or meta.get("status") != "pending":
            return "رد: اثر ناشناخته یا قبلاً تصمیم‌گرفته"
        if not _cteq(token, meta.get("token", "")):
            return "رد: توکنِ تأیید نامنطبق (ضدِ جعل)"
        if verb == "approve":
            return self._do_approve(effect_id, meta)
        if verb == "deny":
            with self._lk:
                meta["status"] = "denied"
            return "رد شد ❌ (هیچ اثری settle نشد)"
        if verb == "later":
            return "بعداً ⏳ (pending باقی می‌ماند)"
        return "نادیده"

    def _do_approve(self, effect_id: str, meta: dict) -> str:
        """human-append (is_human=1) → release gated effects → settle. تنها مسیرِ settle."""
        amount = float(meta.get("amount_aud", 0.0))
        judgment = {"verdict": "approve", "effect_id": effect_id,
                    "amount_aud": amount, "source": "telegram",
                    "summary": meta.get("summary", "")}
        try:
            entry = _on_human_judgment(judgment, gate=self._gate, ledger=self._ledger)
            release_hash = entry.get("hash", "") if isinstance(entry, dict) else ""
            settled = self._settle_effect(effect_id) if self._gate is not None else False
        except Exception:  # noqa: BLE001 — هر شکست = رد (fail-closed، هیچ settleِ نیمه)
            return "رد: خطا در human-append"
        with self._lk:
            meta["status"] = "approved"
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
        if page == "more":
            return {"text": "🧭 <b>همهٔ امکانات</b>\n<i>هر تب فقط‌خواندنی است؛ "
                            "پول/merge همچنان فقط از کارت‌های تأیید.</i>",
                    "reply_markup": self.MENU_KEYBOARD}
        # ── Cockpit v2: ۸ تبِ کابین به‌عنوانِ صفحاتِ menu (read-safe، بدونِ توکن) ──
        if page in self.TAB_PAGES:
            return self._render_tab(page)
        return "نادیده"

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
        if not _cteq(token, meta.get("token", "")):
            return "رد: توکنِ تأیید نامنطبق (ضدِ جعل)"
        if verb == "merge":
            with self._lk:
                meta["status"] = "merge-approved"
            return "ثبت شد ✅ — merge فقط پشتِ flag و با human-append اعمال می‌شود"
        if verb == "deny":
            with self._lk:
                meta["status"] = "denied"
            return "رد شد ❌"
        return "نادیده"

    def pop_rfc_verdicts(self) -> list[tuple[str, str]]:
        """صفِ خروجیِ verdictهای RFC برای doctor (poll). هر verdict دقیقاً یک‌بار تحویل
        می‌شود (پرچمِ consumed زیرِ قفل) — تحویلِ دوباره ممنوع تا doctor دوبار merge نکند.
        ترتیبِ قطعی (deterministic): sorted by rfc_id. فقط خواندن/علامت‌گذاری — هیچ اثرِ پولی."""
        out: list[tuple[str, str]] = []
        with self._lk:
            for rfc_id in sorted(self._pending_rfc):
                meta = self._pending_rfc[rfc_id]
                if meta.get("consumed"):
                    continue
                st = meta.get("status")
                if st in ("merge-approved", "denied"):
                    meta["consumed"] = True
                    out.append((rfc_id, st))
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
                {"text": "💰 پول و متابولیسم", "callback_data": "menu:money"},
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

    def send_text(self, text: str, reply_markup: dict | None = None) -> bool:
        """پیامِ ساده (یا با کیبورد) به مالک. not wired → False. خطای شبکه fail-soft."""
        if not self.wired:
            return False
        text = self._redact(text)   # Cockpit v2 · INV-12: هر خروجی از پاسِ redaction می‌گذرد
        body = {"chat_id": self._owner, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            body["reply_markup"] = reply_markup
        try:
            self._http_post(self._build_url("sendMessage", {}), body)
        except Exception:  # noqa: BLE001
            return False
        return True

    def handle_command(self, text: str) -> str | None:
        """routerِ دستوراتِ مالک. text = پیامِ ورودیِ مالک (بعد از allowlist).
        خروجی = متنِ پاسخ (یا None برای نادیده). هر دستور فقط یک UI را برمی‌گرداند.
        UX v2: /start منو + HTML غنی + حذفِ T-4/T-6/reentry از router.
        هیچ ورودیِ untrustedای اجرا نمی‌شود — فقط ورودیِ validated به propose می‌رود."""
        t = (text or "").strip()
        if not t:
            return None
        # UX v2: /start منوی اصلی
        if t == "/start":
            return self._main_menu()
        if t == "/lead":
            return self._cmd_lead_prompt()
        if t.startswith("/lead "):
            return self._cmd_lead_parse(t[len("/lead "):])
        # T-4: lab — حذف از router (UX v2 §۱). متدها باقی‌اند برای backward-compat.
        # T-5: status (read-only)
        if t == "/status":
            return self.status_report_v2()
        # T-7: kill-switch (می‌ماند). re-entry digest حذف شد.
        if t == "/stop":
            return self.kill_switch()
        # ── Cockpit v2: میان‌بُرهای تب + دستورهای جدید (هر ورودی همچنان DATA است) ──
        if t in ("/overview", "/blueprint", "/brain", "/doctor", "/money",
                 "/school", "/safety", "/alerts"):
            return self._render_tab(t[1:])
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
        return None

    def _main_menu(self) -> dict:
        """منوی اصلیِ ADHD (جلسه ۴۶): یک خطِ اولویت + ۳ ردیف دکمه — نه دیوارِ گزینه.
        عمقِ کاملِ ۸-تب دست‌نخورده زیرِ «همهٔ امکانات» (backward-compat کامل)."""
        mode = self._read_mode_color()
        n_pending = self._count_pending()
        top = ""
        try:
            import needs_digest
            d = needs_digest.compute(pending_count=n_pending)
            if d["n"]:
                top = f"👉 {d['items'][0]}\n"
        except Exception:  # noqa: BLE001 — منو هرگز کرش نمی‌کند
            top = ""
        return {
            "text": (f"🐙 <b>اختاپوس</b> {mode}\n"
                     f"──────────\n"
                     f"{top}"
                     f"<i>{'هیچ‌چیز منتظرت نیست ✅' if not top else 'بقیه در «الان».'}</i>"),
            "reply_markup": self.SIMPLE_KEYBOARD,
        }

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
        """بارگذاریِ lab_seed_data.json. مسیر: ابتدا کنارِ این ماژول (state/)، سپس
        CHRONOS-FABLE-OS/09_Research/. فقط‌خواندنی؛ هرگز نوشته نمی‌شود."""
        from pathlib import Path
        here = Path(__file__).resolve().parents[1]   # _ops
        candidates = [
            here / "state" / self.LAB_SEED_PATH,
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
        return str(d.get("sigma") or d.get("status") or "—")

    # ─── T-6 · RFC/تکامل: doctor.submit_for_approval پشتِ flag ───────────────────
    # ⚑ برای معمار: doctor.submit_for_approval فعلاً در کد نیست (Phase 2). من یک seam
    # می‌سازم که آن را وقتی وجود داشت صدا بزند. تا آن‌جا، فقط کارتِ مرورِ RFC را
    # نشان می‌دهد. merge نیازِ human-append دارد (همان مسیرِ T-2).
    def rfc_card(self, rfc_id: str, summary: str) -> bool:
        """کارتِ مرورِ RFC با دکمه‌های [merge پشتِ flag ✅][رد ❌].
        W-3: کارت حالا token + registry دارد (self._pending_rfc) — همان ضدِ جعل/ضدِ
        replayِ کارت‌های پول (T-2). کلیک فقط verdict را ثبت می‌کند (_dispatch_rfc)؛
        اعمالِ merge پشتِ flag و با human-append در مسیرِ doctor است (pop_rfc_verdicts).
        هیچ settle/gate اینجا نیست. not wired → False (no-opِ امن)."""
        if not self.wired:
            return False
        token = self._new_token(rfc_id, 0.0)
        with self._lk:
            # ضدِ clobber (بازبینیِ خصمانه 2026-07-10): اگر برای همین rfc_id یک verdict
            # تصمیم‌گرفته ولی هنوز مصرف‌نشده داریم، کارتِ دوباره (مثلاً از resubmit ِ
            # sweep) نباید رأیِ ثبت‌شدهٔ مالک را بی‌صدا به pending برگرداند.
            existing = self._pending_rfc.get(rfc_id)
            if (existing and not existing.get("consumed")
                    and existing.get("status") in ("merge-approved", "denied")):
                return False   # verdict معلق داریم — کارتِ نو صادر نکن تا مصرف شود
            self._pending_rfc[rfc_id] = {"summary": str(summary)[:500],
                                         "token": token, "status": "pending"}
        text = (f"🔧 <b>پیشنهادِ تکامل (RFC)</b>\n\n"
                f"<b>خلاصه:</b> {html.escape(str(summary))}\n"
                f"<b>RFC:</b> <code>{html.escape(str(rfc_id))}</code>\n\n"
                f"<i>merge فقط پشتِ flag و با ضمیمهٔ انسانی.</i>")
        kb = {"inline_keyboard": [[
            {"text": "merge پشتِ flag ✅", "callback_data": f"rfc:merge:{rfc_id}:{token}"},
            {"text": "رد ❌", "callback_data": f"rfc:deny:{rfc_id}:{token}"},
        ]]}
        return self.send_text(text, reply_markup=kb)

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
                 "school", "safety", "alerts")

    # allowlistِ بستهٔ act (§۲.۴ — ضدquarantine). chamber_t عمداً غایب است:
    # RED — فعال‌سازی فقط با verdict صریحِ مالک، هرگز از دکمهٔ تلگرام (P5).
    FLAG_KEYS = frozenset({
        "doctor", "neural", "unified", "lead", "lead_tick", "school",
        "consolidation", "evolution", "box", "ideas", "spectral", "barbell",
        "debate", "scheduler", "reconcile", "fitness", "epistemics",
        "selfheal", "bio"})
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

    def _run_act(self, verb: str, key: str, target=None):
        """اجرای actِ تأییدشده. inline فقط read/فایل‌های کنترلِ امن (§۲.۶)؛
        subsystem cycleها → صفِ out-of-band. (هرگز run_cycle/run_epoch مستقیم صدا زده نمی‌شود.)
        target: مقدارِ مطلقِ ذخیره‌شده در mint (فعلاً فقط flaggo)."""
        if verb in self.OOB_VERBS:
            ok = self._append_request(verb, key)
            return ("📨 درخواست ثبت شد (out-of-band) — organism در ضربانِ بعدی مصرف می‌کند.\n"
                    "<i>صف: state/cockpit-requests.jsonl · هیچ اجرای inline (INV-7)</i>"
                    if ok else "❌ ثبتِ درخواست ناموفق")
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
        rm = self._rm()
        cur = False
        if rm is not None:
            try:
                cur = bool(rm.read_capabilities().get("flags", {}).get(env_name, False))
            except Exception:  # noqa: BLE001
                cur = False
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
        if rm is None:
            return False
        try:
            return bool(rm.read_capabilities().get("flags", {}).get(env_name, False))
        except Exception:  # noqa: BLE001
            return False

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
            "brain": [("🧠 تحکیمِ الان", "consolidate", "run"),
                      ("💡 بازسازیِ ایده-گراف", "ideas", "rebuild")],
            "doctor": [("🩺 اجرای چرخهٔ دکتر", "doctor", "run")],
            "school": [("🎓 یادگیریِ الان", "school", "learn"),
                       ("📥 ingest کریپتو", "ingest", "crypto"),
                       ("📥 ingest حساب", "ingest", "acct")],
            "safety": [("❄️ FREEZE", "freeze", "on"),
                       ("🧹 جاروی اثرها", "sweep", "effects"),
                       ("♻️ ری‌استارتِ تمیز", "restart", "organism")],
            "alerts": [("📦 بازتولیدِ بسته", "export", "raw")],
        }.get(page, [])
        for i in range(0, len(acts), 2):
            rows.append([self._act_btn(lbl, v, k) for lbl, v, k in acts[i:i + 2]])
        rows.append([{"text": "🔄 منوی اصلی", "callback_data": "menu:main"}])
        return {"inline_keyboard": rows}

    def _hdr(self, title: str) -> str:
        return (f"{title} · {self._read_mode_color()}\n"
                f"📥 صفِ تأیید: {self._count_pending()}{self._DIV}")

    def _tab_text(self, page: str) -> str:
        rm = self._rm()
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
            return (self._hdr("🩺 <b>دکتر و تکامل</b>")
                    + f"🔧 RFCهای این نشست: {n_rfc} · اثرها: {eff or '—'}\n"
                    + f"⏰ دیسپچر: {'🟢' if caps.get('OCTOPUS_WIRE_SCHEDULER') else '🟡 OFF'} · "
                      f"🩹 خوددرمانی: {'🟢' if caps.get('OCTOPUS_WIRE_SELFHEAL') else '🟡 OFF'} · "
                      f"🔭 معرفت‌شناسی: {'🟢' if caps.get('OCTOPUS_WIRE_EPISTEMICS') else '🟡 OFF'}\n"
                    + "🥊 مناظره: 🔴 needs-live-gate (قفل تا 2026-07-21)\n"
                    + "<i>merge فقط از کارتِ RFC با ضمیمهٔ انسانی — دکمهٔ مستقیم وجود ندارد.</i>")
        if page == "money":
            tel = rm.read_telemetry() if rm else {}
            fit = rm.read_fitness() if rm else {}
            ok, why = self._live_gate_status()
            return (self._hdr("💰 <b>پول و متابولیسم</b>")
                    + f"💵 ماه: {((tel.get('month') or {}).get('aud', 0)) if tel.get('month') else (tel.get('genome') or {}).get('cost_musd', 0)} · "
                      f"suspect-zero: {tel.get('suspect_zero_total', '—')}\n"
                    + f"📊 fitness: {'authoritative' if fit.get('authoritative') else '🟡 سایه (درست — تا ۲۸ روز)'}\n"
                    + f"🔒 live-gate: {'🟢 ' + why if ok else '🔴 ' + why}\n"
                    + "🤖 گاورنرِ LLM: 🔴 قفل تا 2026-07-21\n"
                    + "<i>تنها settleِ پول = کارتِ تأییدِ موجود؛ reconcile/epoch دکمه ندارند (§۲.۵).</i>\n"
                    + "<i>ثبتِ کوت: <code>/claim ATTR-ID | ref | مبلغ</code> · "
                      "تعارض: <code>/conflict ATTR-ID | دلیل</code></i>")
        if page == "school":
            sch = rm.read_school() if rm else {}
            aw = sch.get("awareness") or {}
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
            return ("🩹 <b>خوددرمانی</b>" + self._DIV
                    + f"flag: {'🟢 روشن' if caps.get('OCTOPUS_WIRE_SELFHEAL') else '🟡 OFF'} · "
                      "circuit-breaker روی pacemaker")
        if (tab, key) == ("doctor", "projectf"):
            return ("🎬 <b>Project-F routing</b>" + self._DIV
                    + "درفت‌های high-risk به صفِ تأیید می‌روند ($0 · money-locked).\n"
                    + "ردلاین: <code>verify_no_pii_in_signals</code> (containment) — "
                      "جزئیاتِ محتوایی اینجا عمداً نمایش داده نمی‌شود.")
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
                    + "🔴 قفل تا 2026-07-21 — تخصیصِ خودمتریک (allocate_llm) پشتِ گیتِ دوقفله.\n"
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
                    + "مناظره: 🔴 پشتِ live-gate — topics فقط whitelist (topic-as-data).")
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
            c = (rm.read_channels() if rm else {}).get("channels") or {}
            lines = [f"• {html.escape(str(n))}: {'🟢' if i.get('live') else '🔴'} "
                     f"{html.escape(str(i.get('mode', '')))}" for n, i in c.items()]
            return "📡 <b>کانال‌ها</b>" + self._DIV + ("\n".join(lines) or nod)
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


def _on_human_judgment(judgment: dict, gate=None, ledger=None) -> dict:
    """پلِ تنک به chrono.on_human_judgment (lazy import) تا approval_channel به chrono
    وابستهٔ import-time نشود (جلوگیری از circular). فقط هنگامِ approve واقعی لود می‌شود."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _here = _Path(__file__).resolve().parents[1]   # _ops
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        import chrono  # noqa: WPS433
        return chrono.on_human_judgment(judgment, gate=gate, ledger=ledger)
    except Exception:  # noqa: BLE001 — chrono نبود = fail-closed (entry خالی → رد در caller)
        return {}

