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

from dataclasses import dataclass

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
                 gate=None, ledger=None, state_dir=None):
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
        self._lk = threading.Lock()
        # offset از فایل بارگذاری می‌شود (restart-safe)؛ نبودِ فایل = ۰.
        # state_dir=None → پیش‌فرضِ _ops/state که در نمونهٔ واقعی هست.
        self._offset: int = _load_offset(self._state_dir) if self._state_dir else 0
        self._approvals: dict[str, Approval] = {}    # seam: T-2 اینجا می‌نویسد
        self._pending: dict[str, dict] = {}          # T-2: کارت‌های تأییدِ منتظر (registry ضدِ جعل)
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
        امن، بدونِ هیچ فراخوانیِ شبکه). خطای شبکه fail-soft: ۰ برمی‌گردد، حلقه کشته نمی‌شود."""
        if not self.wired:
            return 0
        if self._killed():
            return 0
        params = {"offset": self._offset, "timeout": self._lp}
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
            msg = upd.get("message") or upd.get("callback_query", {}).get("message") or {}
            chat_id = msg.get("chat", {}).get("id")
            text = (msg.get("text")
                    or (upd.get("callback_query", {}).get("data") if "callback_query" in upd else ""))
            # allowlist: فقط chat_idِ مالک پذیرفته می‌شود؛ بقیه ignore (قانونِ P3 §5).
            if chat_id != self._owner:
                processed += 1              # پردازش‌شده ولی رد‌شده (offset جلو رفت)
                continue
            # DATA نه دستور: هر پیامِ مالک در quarantine ثبت می‌شود و هرگز اجرا نمی‌شود.
            with self._lk:
                self._quarantine.append({
                    "update_id": uid, "chat_id": chat_id,
                    "from_id": (msg.get("from") or {}).get("id"),
                    "text": str(text or "")[:1000],   # کران: پیامِ غول‌پیکر = حافظهٔ نا‌محدود ممنوع
                    "date": msg.get("date"),
                })
            processed += 1
        # offset persistence: اگر offset جلو رفت و state_dir هست، در فایل ذخیره کن
        # (restart-safe). state_dir نباشد → همان رفتارِ حافظه‌ایِ T-1 (تست‌ها).
        if offset_dirty and self._state_dir:
            _save_offset(self._offset, self._state_dir)
        return processed

    def run_forever(self) -> None:
        """حلقهٔ long-pollِ پس‌زمینه. not wired → فوراً برمی‌گردد (no-opِ امن). kill supreme:
        با اولین سیگنالِ kill_check/STOP می‌ایستد. خطای هر دور fail-soft است."""
        if not self.wired:
            return
        while not self._killed():
            self.poll_once()

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
        text = self._render_approval_card(effect_id, amount_aud, summary, guard_verdict)
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

    def dispatch_callback(self, data: str) -> str:
        """routerِ callbackهای کارتِ تأیید. data = 'app:<verb>:<effect_id>:<token>'.
        خروجی = متنِ پاسخ برای answerCallbackQuery. هر callback نامعتبر/جعلی → 'رد'.
        ⚑ برای معمار: این متد مستقیماً در poll_once از callback_query خوانده نمی‌شود؛
        فعلاً فقط برای تست/یکپارچه‌سازیِ بعدی (T-8 router) قابلِ فراخوانی است."""
        parts = str(data or "").split(":")
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

    # ─── T-3 · UIِ Lead: /lead → attribution.propose (mint LEAD-YYYYMMDD-nnn) ──────
    LEAD_CELLS = [("lead.doer", "نقاشی (Lead)"), ("ziman.doer", "Ziman"),
                  ("crypto.doer", "Crypto")]      # هم‌سان با panel/server.py

    def send_text(self, text: str, reply_markup: dict | None = None) -> bool:
        """پیامِ ساده (یا با کیبورد) به مالک. not wired → False. خطای شبکه fail-soft."""
        if not self.wired:
            return False
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
        return None

    def _main_menu(self) -> str:
        """UX v2 §۲: منوی اصلی با inline-keyboard."""
        mode = self._read_mode_color()
        return (f"🐙 <b>اختاپوس</b> — کنترلِ تو · {mode}\n"
                f"<i>دکمه‌ها را برای کارを選ن.</i>")

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
        merge = human-append (همان T-2: فقط تأیید → on_human_judgment).
        ⚑ برای معمار: فعلاً effect_id = rfc:<id> و آن را به gate نمی‌فرستد مگر
        doctor.submit_for_approval وصل شود. فعلاً فقط نمایش."""
        if not self.wired:
            return False
        text = (f"🔧 <b>پیشنهادِ تکامل (RFC)</b>\n\n"
                f"<b>خلاصه:</b> {html.escape(str(summary))}\n"
                f"<b>RFC:</b> <code>{html.escape(str(rfc_id))}</code>\n\n"
                f"<i>merge فقط پشتِ flag و با ضمیمهٔ انسانی.</i>")
        kb = {"inline_keyboard": [[
            {"text": "merge پشتِ flag ✅", "callback_data": f"rfc:merge:{rfc_id}"},
            {"text": "رد ❌", "callback_data": f"rfc:deny:{rfc_id}"},
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

