#!/usr/bin/env python3
"""center.py — «مرکزِ فرماندهیِ تلگرام» (hub): حلقهٔ setup/beat/poll روی TgClient.

نقش (قراردادِ telegram_center):
  * ensure_setup() — idempotent: تاپیکِ هر ۸ پا، منوی commandها، و پیامِ statusِ
    پین‌شده «فقط یک‌بار» ساخته می‌شوند؛ حافظه = فایلِ config (state/telegram/center-config.json).
  * beat() — statusِ پین‌شده را edit می‌کند (هرگز دوباره send نمی‌کند)، دایجستِ هر پا را
    طبقِ cadence (پیش‌فرض ۲۴h، قابلِ override در config) پست می‌کند، و تصمیم‌های نوی
    جعبهٔ راهنمایی را با کیبورد می‌فرستد (dedupe با seen-ids در config).
  * handle_update(u) — فقط مالک (allowlist): /now → ارسالِ status؛ callbackهای
    ok/no/later → ثبتِ verdict به الگوی approval-file + events.emit (اگر import شود)
    + answer_callback. ok اگر رازِ HH_HUMAN_GUARD_SECRET در env باشد یک توکنِ
    HumanAppendGuard هم mint می‌کند؛ بی‌راز = ثبتِ بدونِ توکن، هرگز crash.
  * run_once() — یک دورِ poll + dispatch (offset در config، restart-safe).
  * توقف (رفعِ G-no-master-halt، 2026-07-13؛ restart-aware WP3، owner decision #25):
    حلقهٔ run با هر یک از این‌ها می‌ایستد — `HALT-ALL` یا `STOP(architect)` (مرزِ سختِ
    سراسریِ opslib.master_halted؛ هیچ‌کس نادیده نمی‌گیرد) یا `STOP-TG-CENTER` (scoped ِ خودِ
    این کانکتور). `STOP-ORGANISM` هم می‌ایستاند مگر هم‌راهش `RESTART-REQUESTED` باشد — که
    یعنی ری‌استارتِ روتینِ داشبورد و tg-center باید تا relaunch جان به‌در ببرد.

ناوردی‌ها: $0/stdlib-only · flag-off (بدونِ token/چت = هر متدِ عمومی no-opِ امن با
خروجیِ پیش‌فرض) · import-time خالص (نه شبکه، نه نوشتن) · fail-soft همه‌جا (هر خطا →
پیش‌فرضِ امن، هرگز crashِ صداکننده، یک تلاش در هر فراخوان — بدونِ retry-storm) ·
containment: کلیدهای پا content-free اند؛ نامِ نمایشی از configِ مالک می‌آید
(پیش‌فرضِ پای pf = «استودیو»)؛ لایهٔ دومِ scrub با _BANNED_ECHO (parity با
registry_scan/events). تنها میزبانِ راهِ دور = api.telegram.org و آن هم فقط داخلِ
TgClient و فقط با tokenِ پیکربندی‌شده — این ماژول خودش هیچ HTTPی نمی‌زند.

تست: `_ops/tests/test_tg_center.py` (client/render/clockِ تزریقی — صفر شبکه).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# ── bootstrap مسیر (idiomِ codebase: opslib از _ops/budget) ────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402 — import خالص (فقط مسیرها/env)
# ماژول‌های فاز C/D/E (همگی در همین پکیج، stdlib-only، import-time خالص):
import intent as intent_mod        # noqa: E402 — طبقه‌بندِ نیتِ پیامِ آزاد
import metadata_scan as ms_mod     # noqa: E402 — نقشه‌برداریِ فقط‌خواندنیِ metadata
import approval_store as aps_mod   # noqa: E402 — پلِ صفِ تأیید اختاپوس
import callback_token as cbtok      # noqa: E402 — P3: توکنِ HMACِ callback (فلگ OCTOPUS_WIRE_CB_TOKEN)
import mission as mission_mod       # noqa: E402 — Mission Genome: intent→mission→approval
try:
    import mission_runner as runner_mod   # noqa: E402 — Runner v0: اجرای ایزولهٔ allowlisted (پشتِ فلگ)
except Exception:  # noqa: BLE001 — fail-soft: نبودِ runner نباید center را بشکند
    runner_mod = None  # type: ignore
try:
    import live_commands as live_cmd_mod  # noqa: E402 — /id /box /code /live (2026-07-25)
except Exception:  # noqa: BLE001
    live_cmd_mod = None  # type: ignore

# فایلِ توقفِ حلقه (هم‌خانوادهٔ STOP-ORGANISM/STOP-CORTEX؛ فقط مالک می‌سازد)
STOP_TG_CENTER = opslib.OPS / "STOP-TG-CENTER"

# نشانگرِ ری‌استارتِ داشبورد (dashboard/server.py می‌سازدش هم‌راهِ STOP-ORGANISM؛ RUN-ORGANISM.bat
# هر دو را پاک و با env نو دوباره بوت می‌کند). حضورش یعنی «STOP-ORGANISM موقتی است»، پس این
# کانکتور نباید در یک ری‌استارتِ روتین بمیرد (owner decision #25). مرزِ سختِ سراسری استثنا ندارد.
RESTART_REQUESTED = opslib.OPS / "RESTART-REQUESTED"
RESTART_FRESH_S = 900   # carve-outِ ری‌استارت فقط وقتی markerِ RESTART-REQUESTED «تازه» است
                        # مجاز است؛ markerِ کهنه نباید STOP-ORGANISMِ «ایستِ کامل» را نامحدود ماسک کند.


def _restart_pending() -> bool:
    """آیا یک ری‌استارتِ روتینِ تازه در جریان است؟ RESTART-REQUESTED فقط اگر وجود داشته
    باشد و mtimeاش تازه‌تر از RESTART_FRESH_S باشد معتبر است. در تردید/خطا → False
    (یعنی «ری‌استارتِ معتبر نیست» → STOP-ORGANISMِ کامل غالب می‌شود؛ fail-safe به‌سمتِ توقف)."""
    try:
        if not RESTART_REQUESTED.exists():
            return False
        return (time.time() - RESTART_REQUESTED.stat().st_mtime) <= RESTART_FRESH_S
    except OSError:
        return False

DEFAULT_DIGEST_S = 86400          # cadence پیش‌فرضِ دایجستِ هر پا: ۲۴ ساعت
SEEN_CAP = 200                    # سقفِ حافظهٔ dedupeِ تصمیم‌ها در config
POLL_TIMEOUT_S = 25               # long-poll ($0-idle، هم‌راستا با approval_channel)
# 2026-07-25 (build-spec §4): دایجستِ ادغام‌شده — یک پیام در topic=system به‌جایِ
# ۹ پیامِ جدا به ۹ تاپیک. پشتِ فلگ (پیش‌فرض خاموش) تا رفتارِ فعلی حفظ شود.
# وقتی روشن است، به‌جایِ حلقهٔ per-leg، همهٔ پاهایِ due در یک پیام جمع می‌شوند.
MERGED_DIGEST_FLAG = "OCTOPUS_TG_MERGED_DIGEST"
# 2026-07-26: جواب در همان تاپیکی بیفتد که مالک پرسیده (گروهِ مرکز فوروم است).
# پیش‌فرض خاموش = رفتارِ امروز؛ روشن = پاسخ به `message_thread_id`ِ همان پیام.
TOPIC_REPLY_FLAG = "OCTOPUS_TG_TOPIC_REPLY"

# containment (parity با registry_scan.scrub / events._scrub_str) — لایهٔ دوم؛
# لایهٔ اول render.scrub است. هیچ رشتهٔ ممنوع هرگز echo نمی‌شود.
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")

# کلیدهای ۸ پا — content-free (fallback وقتی render.LEGS در دسترس نیست)
LEG_KEYS = ("lead", "ziman", "mining", "crypto", "accounting",
            "studio_pf", "system", "knowledge", "cartographer")

# نامِ نمایشیِ پیش‌فرض — configِ مالک (display_names) همیشه برنده است.
# پای pf فقط با aliasِ سازمانیِ «استودیو» دیده می‌شود (containment).
DEFAULT_DISPLAY = {
    "lead": "Lead-نقاشی",
    "ziman": "Ziman Galerry",
    "mining": "Mining",
    "crypto": "Crypto-etoro",
    "accounting": "Accounting",
    "studio_pf": "استودیو",
    "system": "سیستم",
    "knowledge": "دانش",
}

# منوی command — فقط چیزی که این مرکز واقعاً handle می‌کند (قرارداد: /now)
COMMANDS: list[tuple[str, str]] = [
    ("menu", "🎛 منوی فرماندهی — همه‌چیز از اینجا"),
    ("now", "📊 وضعیت — همین حالا"),
    ("budget", "🐙 پیشنهادِ تخصیصِ ماهِ بعد (propose-only)"),
    ("revenue", "💰 درآمدِ تأییدشده (aggregate)"),
    ("missions", "🧬 مأموریت‌ها — Mission Genome"),
    # 2026-07-25 live path — identity / blackbox / collab / summary
    ("live", "🐙 خلاصهٔ زنده‌بودن (flags + هویت + جعبه‌سیاه)"),
    ("id", "🧬 مگا-معادلاتِ هویت (read-only)"),
    ("box", "📦 نقشهٔ جعبه‌سیاه‌ها"),
    ("code", "🧩 هم‌کدنویسی propose-only با مالک"),
]

_VERDICTS = ("ok", "no", "later")
_VERDICT_TOAST = {"ok": "تأیید شد ✅", "no": "رد شد ❌", "later": "بعداً ⏳"}
_VERDICT_APPROVAL_STATE = {"ok": "approved", "no": "denied", "later": "required"}


# ─── ابزارهای ماژول‌سطح (همه fail-soft، هیچ اثرِ import-time) ─────────────────────
def _scrub(s: object) -> str:
    """رشتهٔ حاویِ echo ِ ممنوع → کاملاً redact (parity با registry_scan.scrub)."""
    v = str(s if s is not None else "")
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


def _config_path() -> Path:
    return opslib.STATE_DIR / "telegram" / "center-config.json"


def _load_config() -> dict:
    """config = حافظهٔ idempotency. نبود/خرابی فایل → {} (fail-soft)."""
    try:
        p = _config_path()
        if not p.exists():
            return {}
        data = json.loads(p.read_text("utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_config(cfg: dict) -> bool:
    """نوشتنِ اتمیک (tmp + os.replace، idiomِ opslib.LockedJson.write). شکست → False."""
    try:
        p = _config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, p)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _decision_id(item: dict) -> str:
    """شناسهٔ پایدارِ یک تصمیم برای dedupe/callback. اگر خودش id داشت همان؛ وگرنه
    هشِ محتوا (content-free در config — فقط hash ذخیره می‌شود، نه متن)."""
    did = str(item.get("id") or "").strip()
    if did:
        return re.sub(r"[^A-Za-z0-9_\-]", "-", did)[:64]
    import hashlib
    base = json.dumps([item.get("q", ""), item.get("source", "")], ensure_ascii=False)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def _sanitize_id(raw: str) -> str:
    """idِ رسیده از callback data — هرگز خام واردِ نامِ فایل نمی‌شود (ضدِ path-traversal)."""
    return re.sub(r"[^A-Za-z0-9_\-]", "-", str(raw or ""))[:64] or "unknown"


def _mint_ha_token(approval_id: str, event_type: str = "APPROVAL") -> "str | None":
    """توکنِ human-append فقط اگر رازِ HH_HUMAN_GUARD_SECRET در env باشد (قراردادِ
    مرکز). بی‌راز/هر شکست → None (ثبتِ بدونِ توکن، هرگز crash). راز هرگز لاگ/ذخیره
    نمی‌شود — فقط خروجیِ HMAC (توکن) در رکورد می‌نشیند."""
    secret = str(os.environ.get("HH_HUMAN_GUARD_SECRET", "") or "").strip()
    if not secret:
        return None
    try:
        from human_append_guard import HumanAppendGuard
        g = HumanAppendGuard(secret.encode("utf-8"))
        return g.mint(str(approval_id).replace(".", "-"), event_type)
    except Exception:  # noqa: BLE001 — mint هرگز مسیرِ ثبت را نمی‌کشد
        return None


def _emit_event(event_name: str, **kw) -> None:
    """events.emit اگر import شود (fail-soft؛ نبودِ events = سکوتِ امن)."""
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        import events
        events.emit(event_name, "tg-center", **kw)
    except Exception:  # noqa: BLE001
        pass


# ─── Center ──────────────────────────────────────────────────────────────────────
class Center:
    """حلقهٔ مرکز: client (TgClient یا fakeِ تست) + clockِ تزریقی + renderِ تزریقی.

    flag-off: اگر client نباشد یا client.wired() False باشد، هر متدِ عمومی no-opِ
    امن است (خروجیِ پیش‌فرض، صفر شبکه، صفر نوشتن)."""

    def __init__(self, client=None, clock=time.time, render_mod=None):
        self._clock = clock
        self._render = render_mod          # تزریقِ تست؛ None → importِ lazyِ render
        self._client = client if client is not None else self._default_client()

    # ── سیم‌کشیِ fail-soft ───────────────────────────────────────────────────────
    @staticmethod
    def _default_client():
        """TgClient از قرارداد (env-driven). نبودِ ماژول/خطا → None (no-opِ امن)."""
        try:
            import tg_api
            return tg_api.TgClient()
        except Exception:  # noqa: BLE001
            return None

    def _rmod(self):
        """ماژولِ render (تزریقی یا lazy). نبود → None (بخش‌های وابسته skip می‌شوند)."""
        if self._render is not None:
            return self._render
        try:
            import render as _r
            self._render = _r
        except Exception:  # noqa: BLE001
            return None
        return self._render

    def _menu2(self):
        """ماژولِ منوی v2 (lazy، fail-soft). None اگر در دسترس نباشد. سیم‌کشیِ رفتاری
        فقط وقتی enabled() (پشتِ OCTOPUS_WIRE_MENU_V2) — flag خاموش → رفتارِ امروز بایت‌به‌بایت."""
        try:
            import menu_integration as _m2
            return _m2
        except Exception:  # noqa: BLE001
            return None

    def _handle_menu2_callback(self, cbq: dict, data: str, m2) -> dict:
        """verbِ m: — منوی v2 (پشتِ OCTOPUS_WIRE_MENU_V2). dispatch → editِ درجای همان پیام؛
        fail-soft. صفر settle/effector — فقط ناوبریِ منو (render)."""
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")
        try:
            txt, kb = m2.dispatch(data)
            if isinstance(mid, int):
                self._client.edit(mid, _scrub(str(txt or "")), keyboard=kb, chat_id=chat)
        except Exception:  # noqa: BLE001
            pass
        self._answer(cbq)
        return {"kind": "menu2", "data": data}

    def wired(self) -> bool:
        """لوله وصل است؟ هر خطا/نبودِ client = False (fail-closed برای اثرگذاری)."""
        try:
            return bool(self._client is not None and self._client.wired())
        except Exception:  # noqa: BLE001
            return False

    _wired = wired  # نامِ داخلیِ هم‌معنا (خوانایی در متدها)

    def stopped(self) -> bool:
        """توقفِ حلقه.
        **مرزِ سختِ سراسری** (HALT-ALL / STOP ِ معمار via master_halted) و STOP-TG-CENTER
        همیشه می‌ایستانند — این کانکتورِ بیرونی هرگز حق ندارد مرزِ سراسری را نادیده بگیرد
        (رفعِ یافتهٔ G-no-master-halt؛ این شرط‌ها هرگز ضعیف نمی‌شوند).
        اما STOP-ORGANISM فقط وقتی یک «ایستِ کامل» است این کانکتور را می‌ایستاند؛ اگر
        هم‌راهش RESTART-REQUESTED باشد یعنی یک ری‌استارتِ روتینِ داشبورد است و tg-center باید
        از آن جان به‌در ببرد تا relaunch (owner decision #25 / WP3). خطای دیسک در چکِ توقف →
        «ایست» (امن‌ترین: fail-safe)."""
        try:
            return (STOP_TG_CENTER.exists()
                    or opslib.master_halted() is not None
                    or (opslib.STOP_ORGANISM.exists() and not _restart_pending()))
        except OSError:
            return True

    # ── کلیدها/نام‌ها/cadence ────────────────────────────────────────────────────
    def _legs(self) -> list[str]:
        """ترتیبِ پاها از render.LEGS (منبعِ قرارداد)؛ نبود → fallbackِ محلی."""
        r = self._rmod()
        try:
            keys = list(getattr(r, "LEGS", {}).keys()) if r is not None else []
        except Exception:  # noqa: BLE001
            keys = []
        return keys or list(LEG_KEYS)

    @staticmethod
    def _display_names(cfg: dict) -> dict:
        names = dict(DEFAULT_DISPLAY)
        dn = cfg.get("display_names")
        if isinstance(dn, dict):
            names.update({str(k): str(v) for k, v in dn.items()})
        return names

    @staticmethod
    def _cadence_for(cfg: dict, leg: str) -> float:
        """cadence دایجستِ یک پا: config['cadence_s'] یا dict per-leg با 'default'؛
        هر ناسازگاری → پیش‌فرضِ ۲۴h (fail-soft)."""
        cad = cfg.get("cadence_s", DEFAULT_DIGEST_S)
        try:
            if isinstance(cad, dict):
                return float(cad.get(leg, cad.get("default", DEFAULT_DIGEST_S)))
            return float(cad)
        except (TypeError, ValueError):
            return float(DEFAULT_DIGEST_S)

    def _status_text(self) -> str:
        """متنِ status از render (fail-soft → '')."""
        r = self._rmod()
        if r is None:
            return ""
        try:
            return str(r.render_status(r.collect_feeds() or {}) or "")
        except Exception:  # noqa: BLE001
            return ""

    def _live_cmd(self, text: str) -> str:
        """مسیرِ زنده‌سازی 2026-07-25: /id /box /code /live — fail-soft، read/propose-only."""
        try:
            if live_cmd_mod is None:
                return "live_commands در دسترس نیست."
            return str(live_cmd_mod.dispatch(text) or "")
        except Exception as e:  # noqa: BLE001
            return f"live_cmd fail-soft: {type(e).__name__}"

    # ── ensure_setup: idempotent — config حافظه است ─────────────────────────────
    def ensure_setup(self) -> bool:
        """تاپیک‌های ناقص را می‌سازد، منو را یک‌بار ست می‌کند، status را یک‌بار
        می‌سازد+پین می‌کند. دوبار اجرا = صفر کارِ تکراری (تستِ idempotency)."""
        if not self._wired():
            return False
        cfg = _load_config()
        dirty = False

        # chat_id: از config (رأی مالک) وگرنه از خودِ client (env TG_CENTER_CHAT_ID)
        if not cfg.get("chat_id"):
            cid = getattr(self._client, "center_chat_id", None)
            if cid:
                cfg["chat_id"] = cid
                dirty = True
        chat_id = cfg.get("chat_id")

        # نام‌های نمایشی: یک‌بار پیش‌فرض‌ها را در config بنشان تا مالک قابلِ‌ویرایش ببیند
        if not isinstance(cfg.get("display_names"), dict):
            cfg["display_names"] = dict(DEFAULT_DISPLAY)
            dirty = True
        names = self._display_names(cfg)

        # تاپیکِ هر پا — فقط پاهای بدونِ topic_id (نبودِ پاسخ = تلاشِ دوباره در setup بعدی)
        topics = cfg.setdefault("topics", {})
        if not isinstance(topics, dict):
            topics = cfg["topics"] = {}
        r = self._rmod()
        for leg in self._legs():
            if isinstance(topics.get(leg), int):
                continue                            # قبلاً ساخته شده — idempotent
            # عنوانِ تاپیک: آیکنِ برندِ پا + نامِ نمایشی (render.topic_title)؛ fallback = نامِ خالی
            try:
                title = r.topic_title(leg, cfg) if (r is not None and hasattr(r, "topic_title")) \
                    else names.get(leg, leg)
            except Exception:  # noqa: BLE001
                title = names.get(leg, leg)
            try:
                tid = self._client.create_topic(_scrub(title),
                                                chat_id=chat_id)
            except Exception:  # noqa: BLE001 — یک تلاش، بدونِ storm
                tid = None
            if isinstance(tid, int):
                topics[leg] = tid
                dirty = True

        # منوی commandها — ثبتِ مجدد وقتی فهرست عوض شود (پرچم = تعدادِ ثبت‌شده)
        if cfg.get("commands_set") != len(COMMANDS):
            try:
                ok = bool(self._client.set_commands(list(COMMANDS)))
            except Exception:  # noqa: BLE001
                ok = False
            if ok:
                cfg["commands_set"] = len(COMMANDS)
                dirty = True

        # پیامِ statusِ پین‌شده — فقط یک‌بار ساخته می‌شود؛ بعداً فقط edit (beat)
        if not isinstance(cfg.get("status_message_id"), int):
            text = self._status_text() or "🐙 مرکزِ فرماندهی — راه‌اندازی…"
            try:
                mid = self._client.send(_scrub(text), chat_id=chat_id, pin=True)
            except Exception:  # noqa: BLE001
                mid = None
            if isinstance(mid, int):
                cfg["status_message_id"] = mid
                dirty = True

        if dirty:
            _save_config(cfg)
        return True

    # ── beat: edit status + دایجستِ سررسیده + تصمیم‌های نو ─────────────────────────
    def beat(self) -> dict:
        """یک ضربان. خروجی = {edited, digests, decisions} (شمارش برای مشاهده).
        statusِ پین‌شده فقط edit می‌شود — هرگز sendِ دوباره."""
        out = {"edited": False, "digests": 0, "decisions": 0}
        if not self._wired():
            return out
        cfg = _load_config()
        r = self._rmod()
        feeds: dict = {}
        if r is not None:
            try:
                feeds = r.collect_feeds() or {}
            except Exception:  # noqa: BLE001
                feeds = {}
        chat_id = cfg.get("chat_id")
        topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
        dirty = False

        # ۱) statusِ پین‌شده: همیشه edit (ensure_setup مسئولِ ساخت است)
        mid = cfg.get("status_message_id")
        if r is not None and isinstance(mid, int):
            try:
                txt = str(r.render_status(feeds) or "")
            except Exception:  # noqa: BLE001
                txt = ""
            if txt:
                try:
                    out["edited"] = bool(self._client.edit(mid, _scrub(txt),
                                                           chat_id=chat_id))
                except Exception:  # noqa: BLE001
                    pass

        # ۲) دایجستِ هر پا — سررسید با clockِ تزریقی؛ موفقیت = جلو رفتنِ last_digest
        now = float(self._clock())
        last = cfg.setdefault("last_digest", {})
        if not isinstance(last, dict):
            last = cfg["last_digest"] = {}
        if r is not None:
            legs_map = feeds.get("legs") if isinstance(feeds.get("legs"), dict) else {}
            _merged = str(os.environ.get(MERGED_DIGEST_FLAG, "0")).strip() in ("1", "true", "yes", "on")
            if _merged:
                # 2026-07-25 (build-spec §4): یک پیامِ ادغام‌شده در topic=system.
                # همهٔ پاهایِ due را جمع می‌کنیم؛ اگر حداقل یک پا متنی داشت، یک پیام
                # در topic=system می‌فرستیم و سررسیدِ همهٔ پاهایِ due را جلو می‌بریم.
                # این جایگزینِ ۹ پیامِ جدا می‌شود — رباتِ آرام‌تر.
                due_legs = []
                merged_lines = []
                for leg in self._legs():
                    try:
                        lr = float(last.get(leg, 0.0) or 0.0)
                    except (TypeError, ValueError):
                        lr = 0.0
                    if lr > 0.0 and now - lr < self._cadence_for(cfg, leg):
                        continue
                    due_legs.append(leg)
                    leg_data = legs_map.get(leg) or feeds.get(leg) or {}
                    try:
                        txt = str(r.render_leg_digest(leg, leg_data) or "")
                    except Exception:  # noqa: BLE001
                        txt = ""
                    if txt:
                        merged_lines.append(txt)
                if due_legs and merged_lines:
                    body = "\n\n".join(merged_lines)
                    try:
                        m = self._client.send(_scrub(body),
                                              topic_id=topics.get("system"),
                                              chat_id=chat_id)
                    except Exception:  # noqa: BLE001
                        m = None
                    if m is not None:
                        for leg in due_legs:
                            last[leg] = now
                        out["digests"] += 1
                        dirty = True
                elif due_legs:
                    # پاهای due بودند ولی متنی نبودند — سررسید را جلو ببر (نویز نزن).
                    for leg in due_legs:
                        last[leg] = now
                    dirty = True
            else:
                # رفتارِ فعلی (پیش‌فرض): یک پیامِ جدا به هر پا، در تاپیکِ خودش.
                for leg in self._legs():
                    try:
                        lr = float(last.get(leg, 0.0) or 0.0)
                    except (TypeError, ValueError):
                        lr = 0.0
                    # lr==0 یعنی «هرگز پست نشده» → فوراً due (مستقل از epochِ clockِ تزریقی)
                    if lr > 0.0 and now - lr < self._cadence_for(cfg, leg):
                        continue
                    leg_data = legs_map.get(leg) or feeds.get(leg) or {}
                    try:
                        txt = str(r.render_leg_digest(leg, leg_data) or "")
                    except Exception:  # noqa: BLE001
                        continue
                    if not txt:
                        last[leg] = now                  # چیزی برای گفتن نیست — سررسید جلو
                        dirty = True
                        continue
                    try:
                        m = self._client.send(_scrub(txt), topic_id=topics.get(leg),
                                              chat_id=chat_id)
                    except Exception:  # noqa: BLE001
                        m = None
                    if m is not None:
                        last[leg] = now
                        out["digests"] += 1
                        dirty = True

        # ۳) تصمیم‌های نوی جعبهٔ راهنمایی — dedupe با seen-ids در config
        if r is not None:
            g = feeds.get("guidance") if isinstance(feeds.get("guidance"), dict) else {}
            items = g.get("items") if isinstance(g.get("items"), list) else []
            seen = [s for s in (cfg.get("seen") or []) if isinstance(s, str)]
            for it in items[:8]:
                if not isinstance(it, dict):
                    continue
                did = _decision_id(it)
                if did in seen:
                    continue
                it2 = dict(it)
                it2.setdefault("id", did)            # هم‌راستاییِ callback_data با dedupe
                try:
                    res = r.render_decision(it2)
                    txt, kb = res if isinstance(res, tuple) else (str(res), None)
                    kb = self._tok_kb(kb)        # P3 (D4): توکنِ ok/no/later وقتی فلگ روشن (وگرنه no-op)
                except Exception:  # noqa: BLE001
                    continue
                try:
                    m = self._client.send(_scrub(txt), keyboard=kb,
                                          topic_id=topics.get("system"),
                                          chat_id=chat_id)
                except Exception:  # noqa: BLE001
                    m = None
                if m is not None:
                    seen.append(did)
                    out["decisions"] += 1
                    dirty = True
            cfg["seen"] = seen[-SEEN_CAP:]

        if dirty:
            _save_config(cfg)
        # فاز A (event bridge، هماهنگ با c6_state_machine از Opus مافوق): push رویدادهای
        # بحرانی به مالک. پشتِ OCTOPUS_WIRE_EVENT_BRIDGE؛ fail-soft (§۴).
        try:
            import event_bridge as _eb
            _eb.beat(self)
        except Exception:  # noqa: BLE001 — bridge هرگز beat را نمی‌کشد
            pass
        # 2026-07-25: money-pulse — فازِ جدید. درآمدِ پاها رو می‌خونه (propose-only،
        # هرگز MONEY_ATTRIBUTION جعلی). پشتِ OCTOPUS_WIRE_MONEY_PULSE؛ fail-soft.
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heart"))
            import money_pulse as _mp
            _mp.beat(self)
        except Exception:  # noqa: BLE001 — pulse هرگز beat را نمی‌کشد
            pass
        return out

    def push_alert(self, text: str) -> bool:
        """push یک پیامِ alert به topic=system. منبعِ ارسالِ event_bridge و push-per-event.
        fail-soft، scrubشده (parity با _scrub:120). false = ارسال نشد/خطا."""
        if not self._wired() or not text:
            return False
        try:
            cfg = _load_config()
            chat_id = cfg.get("chat_id")
            topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
            m = self._client.send(_scrub(text), topic_id=topics.get("system"),
                                  chat_id=chat_id)
            return m is not None
        except Exception:  # noqa: BLE001
            return False

    def _topic_key(self, msg: dict) -> str:
        """نامِ پا برای تاپیکی که پیام در آن آمده — یا "" (General/خصوصی/ناشناخته).

        وارونهٔ نگاشتِ `topics` در center-config. کاربردش این است که سؤالِ آزادِ
        مالک در تاپیکِ 🦑lead، contextِ لید بگیرد نه contextِ عمومی — یعنی جای
        پرسیدن هم بخشی از سؤال باشد. fail-soft: هر ابهام → "" (contextِ عمومی)."""
        try:
            tid = msg.get("message_thread_id")
            if not isinstance(tid, int) or not msg.get("is_topic_message"):
                return ""
            topics = (_load_config() or {}).get("topics") or {}
            for name, num in topics.items():
                if num == tid:
                    return str(name)
        except Exception:  # noqa: BLE001
            pass
        return ""

    # ── handle_update: فقط مالک — /now و callbackهای ok/no/later ─────────────────
    @staticmethod
    def _reply_thread(msg: dict):
        """تاپیکی که باید در آن جواب داد — یا None.

        باگِ ۲۰۲۶-۰۷-۲۶: گروهِ مرکز فوروم است. جوابِ بی‌`message_thread_id` در
        تاپیکِ **General** می‌افتد، نه آن‌جا که مالک پرسیده. یعنی بات جواب می‌داد و
        مالک هرگز نمی‌دید — «فرستادم» درست بود و «رسید» غلط، بدونِ هیچ خطایی.

        فقط وقتی thread می‌فرستیم که تلگرام خودش گفته باشد این پیام در یک تاپیک
        است (`is_topic_message`). در Generalِ فوروم و در چتِ خصوصی این پرچم نیست →
        None → رفتارِ امروز بایت‌به‌بایت. ارسالِ thread_idِ نامعتبر خطای ۴۰۰ می‌دهد،
        پس این باریک‌بینی عمدی است.
        """
        if os.environ.get(TOPIC_REPLY_FLAG, "").strip().lower() not in (
                "1", "true", "yes", "on"):
            return None
        try:
            if not msg.get("is_topic_message"):
                return None
            tid = msg.get("message_thread_id")
            return int(tid) if isinstance(tid, int) else None
        except (TypeError, ValueError, AttributeError):
            return None

    def _is_owner(self, u: dict) -> bool:
        """allowlist. اول helperِ قراردادیِ client.is_owner؛ هر خطا/ابهام = False
        (fail-closed: غیرمالک هرگز فرمان نمی‌دهد — قانونِ P3 §5)."""
        try:
            fn = getattr(self._client, "is_owner", None)
            if callable(fn):
                return bool(fn(u))
        except Exception:  # noqa: BLE001
            return False
        try:
            owner = getattr(self._client, "owner_chat_id", None)
            frm = ((u.get("message") or {}).get("from")
                   or (u.get("callback_query") or {}).get("from") or {})
            return owner is not None and frm.get("id") == owner
        except Exception:  # noqa: BLE001
            return False

    def handle_update(self, u) -> "dict | None":
        """یک update. غیرمالک/ناوصل/ناسازگار → None (صفر اثر، صفر پاسخ)."""
        if not self._wired() or not isinstance(u, dict):
            return None
        if not self._is_owner(u):
            return None                              # سکوتِ کامل برای غیرمالک
        cbq = u.get("callback_query")
        if isinstance(cbq, dict):
            return self._handle_callback(cbq)
        msg = u.get("message")
        if isinstance(msg, dict):
            return self._handle_message(msg)
        return None

    def _handle_message(self, msg: dict) -> "dict | None":
        text = str(msg.get("text") or "").strip()
        if not text:
            return None
        cmd = text.split()[0].split("@")[0].lower()
        chat_id = (msg.get("chat") or {}).get("id")  # پاسخ به همان‌جا که پرسید
        handlers = {
            "/now": lambda: self._status_text() or "🐙 هنوز چیزی برای گفتن ندارم.",
            "/budget": self._budget_text,
            "/revenue": self._revenue_text,
            "/missions": lambda: self._page("ms"),
            "/menu": lambda: self._page("menu"),
            "/start": lambda: self._page("menu"),
            # 2026-07-25 live path — full text after command is passed through
            "/live": lambda: self._live_cmd(text),
            "/id": lambda: self._live_cmd(text),
            "/eq": lambda: self._live_cmd(text),
            "/box": lambda: self._live_cmd(text),
            "/code": lambda: self._live_cmd(text),
            "/doctrine": lambda: self._live_cmd(text),
            "/رفتار": lambda: self._live_cmd(text),
            "/کد": lambda: self._live_cmd(text),
        }
        # Menu v2 (پشتِ OCTOPUS_WIRE_MENU_V2): فقط با فلگِ روشن /panel اضافه می‌شود.
        # flag خاموش → /panel در handlers نیست → مسیرِ «command ناشناس» امروز (return None). parity.
        _m2 = self._menu2()
        if _m2 is not None and _m2.enabled():
            handlers["/panel"] = _m2.render_menu
        fn = handlers.get(cmd)
        if fn is None:
            # پیامِ آزادِ مالک = پرسش/دستورِ نرم. اجرای مستقیمِ مخرب هرگز؛ فقط
            # نگاشتِ intent → کارت/دکمهٔ عملگرا یا پاسخِ آرام (stdlib-only، بدون LLM).
            if not text.startswith("/"):
                return self._handle_ask(msg, text)
            return None                    # قراردادها: command ناشناس نادیده
        try:
            out = fn()
            txt, kb = out if isinstance(out, tuple) else (str(out or ""), None)
            mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb,
                                    topic_id=self._reply_thread(msg))
        except Exception:  # noqa: BLE001
            mid = None
        return {"kind": cmd.lstrip("/"), "sent": mid is not None}

    def _handle_ask(self, msg: dict, text: str) -> dict:
        """پرسش‌وپاسخِ زندهٔ مالک با اختاپوس، بدون LLM و بدون اجرای مبهم.

        این لایه از intent.classify (ماژولِ جدا) برای تشخیصِ نیت استفاده می‌کند،
        سپس intent را به کارت/دکمهٔ عملگرا نگاشت می‌کند. هرگز اجرای مستقیمِ مخرب؛
        مکث/ادامه فقط دکمهٔ lg:*؛ scan فقط کارتِ map:start؛ تأییدها فقط کارتِ ap.

        ارتقا از LLM پشتِ فلگِ OCTOPUS_TG_LLM_ASK=1 در آینده بدونِ لمسِ این لایه
        ممکن است (intent.classify را می‌توان با wrapperِ LLM عوض کرد)."""
        chat_id = (msg.get("chat") or {}).get("id")
        # متنِ شرط، بعد از دکمهٔ «✍️ شرط بگذار». اولویتش بالاتر از هر مسیرِ دیگری
        # است چون مالک دارد جوابِ یک سؤالِ مشخص را می‌دهد، نه فرمانِ تازه.
        _await = getattr(self, "_awaiting_counter", None)
        if _await:
            self._awaiting_counter = None
            try:
                import negotiate as _ng
                r = _ng.respond(_await, "counter", counter=text)
                if r.get("ok"):
                    rev = _ng.make_offer(revise_of=_await)
                    if rev.get("ok"):
                        _t, _k = _ng.card(rev["offer"])
                        mid = self._client.send(_scrub(_t), chat_id=chat_id,
                                                keyboard=_k,
                                                topic_id=self._reply_thread(msg))
                        return {"kind": "negotiate_revised", "sent": mid is not None}
                    self._client.send(
                        _scrub("✍️ شرطت ثبت شد. پیشنهادِ بازنگری‌شده الان نشد — "
                               f"({_scrub(str(rev.get('reason'))[:40])}) بعداً می‌آید."),
                        chat_id=chat_id, topic_id=self._reply_thread(msg))
                    return {"kind": "negotiate_counter", "revised": False}
            except Exception:  # noqa: BLE001
                pass
        # ── اتاقِ آینه (۲۰۲۶-۰۷-۲۷): در این تاپیک **هیچ** نگاشتِ فرمانی انجام
        # نمی‌شود. هر جمله مستقیم به لایهٔ خودشناسی می‌رود، با تاریخچهٔ گفتگو و
        # تصحیح‌های ثبت‌شدهٔ مالک. جای دیگری از بات عوض نمی‌شود؛ flag خاموش یا
        # هر شکست → مسیرِ عادیِ پایین، بایت‌به‌بایت.
        if self._topic_key(msg) == "mirror":
            try:
                import mirror_room as _mr
                if _mr.enabled():
                    _m = _mr.ask(text)
                    if _m.get("ok"):
                        _txt, _kb = _mr.card(_m["text"], _m.get("model") or "",
                                             bool(_m.get("recorded_correction")))
                        _mid = self._client.send(_scrub(_txt), chat_id=chat_id,
                                                 keyboard=_kb,
                                                 topic_id=self._reply_thread(msg))
                        return {"kind": "mirror", "sent": _mid is not None}
                    # شکست را **صادقانه** بگو — در این اتاق «متوجه نشدم» بی‌معنی است
                    _why = {"daily-cap": "سهمیهٔ امروزِ فکرِ عمیقم تمام شد",
                            "not-a-paid-brain": "مغزِ گرانم الان در دسترس نیست",
                            "no-answer": "مغزم جواب نداد",
                            }.get(str(_m.get("reason") or "").split(":")[0], "")
                    if _why:
                        _mid = self._client.send(
                            _scrub(f"🪞 {_why} — چند دقیقهٔ دیگر دوباره بپرس."),
                            chat_id=chat_id, topic_id=self._reply_thread(msg))
                        return {"kind": "mirror_busy", "sent": _mid is not None}
            except Exception:  # noqa: BLE001 — آینه هرگز مسیرِ بات را نمی‌کشد
                pass
        try:
            # Mission Genome: درخواست‌های کدنویسی/تست/یادگیری/جهش نباید به منوی ثابت
            # سقوط کنند. اول به Mission قابل‌ردیابی تبدیل می‌شوند؛ اجرا/apply همچنان
            # پشتِ action_graph/approval می‌ماند و اینجا فقط کارتِ کنترل ساخته می‌شود.
            mt = mission_mod.infer_mission_type(text)
            # Trust-Engine wiring (پشتِ OCTOPUS_TG_LLM_ASK، پیش‌فرض خاموش): اگر تشخیصِ
            # rule-based «general» شد، مغزِ خودِ بات (llm_intent.understand) free-text را می‌فهمد
            # و اگر needs_mission بود، به مأموریتِ گیت‌شده ارتقا می‌دهد — فقط پیشنهاد، اجرا همچنان
            # پشتِ همان گیت (autonomy_matrix دوباره چک می‌کند؛ مدل هرگز گیت را پایین نمی‌آورد).
            # flag خاموش → این بلوک هیچ اجرا نمی‌شود؛ مسیرِ امروز بایت‌به‌بایت.
            _brain_busy = ""
            if mt == "general":
                try:
                    import llm_intent as _li
                    if _li.enabled():
                        _u = _li.understand(text)
                        if isinstance(_u, dict) and _u.get("ok") and _u.get("needs_mission"):
                            mt = "self_coding" if _u.get("intent") == "code" else "verification"
                        elif isinstance(_u, dict) and not _u.get("ok"):
                            # ۲۰۲۶-۰۷-۲۶: مغزِ محلی بینِ دو call فاصلهٔ اجباری دارد
                            # (OLLAMA_MIN_INTERVAL_S، زندهْ ۲۰ثانیه — گاردِ انصافِ GPU).
                            # پیامِ دومِ مالک در آن پنجره بی‌صدا به «متوجه نشدم» سقوط
                            # می‌کرد: بات «احمقم» می‌گفت درحالی‌که حقیقت «مشغولم» بود.
                            # اینجا فقط *علت* نگه داشته می‌شود تا کارت راست بگوید؛
                            # هیچ گاردی دور زده نمی‌شود.
                            _brain_busy = str(_u.get("reason") or "")
                except Exception:  # noqa: BLE001 — فهمِ LLM هرگز مسیرِ بات را نمی‌کشد
                    pass
            if mt != "general":
                m = mission_mod.create_mission(text, source="telegram", mission_type=mt)
                # bridge به صفِ تأیید unified: مأموریت‌های approval-required در mn:ap هم دیده شوند.
                if m.get("approval") == "required":
                    try:
                        aps_mod.add_pending({"id": m.get("id"), "type": "mission",
                                             "title": m.get("owner_intent", "mission"),
                                             "risk": m.get("risk", "medium"),
                                             "requires_confirmation": True,
                                             "source": "telegram"})
                    except Exception:  # noqa: BLE001
                        pass
                txt, kb = mission_mod.mission_card(m.get("id"))
                kb = self._tok_kb(kb)            # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
                mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb,
                                        topic_id=self._reply_thread(msg))
                return {"kind": "ask_mission", "mission_id": m.get("id"), "sent": mid is not None}

            res = intent_mod.classify(text)
            it = res["intent"]
            leg = res.get("leg")
            # نگاشتِ intent → kind (نام‌های قدیمی برای سازگاریِ عقب حفظ شدند)
            kind_map = {"status": "ask_status", "revenue": "ask_revenue",
                        "budget": "ask_budget", "help": "ask_menu",
                        "pause_leg": "ask_pause", "resume_leg": "ask_resume",
                        "scan_metadata": "ask_scan_metadata",
                        "approvals": "ask_approvals",
                        "identity": "ask_identity", "blackbox": "ask_blackbox",
                        "collab_code": "ask_collab", "live_summary": "ask_live",
                        "unknown": "ask_unknown"}
            kind = kind_map.get(it, "ask_unknown")
            if it in ("identity", "blackbox", "collab_code", "live_summary"):
                out = self._live_cmd(text)
            elif it == "status":
                out = self._page("st")
            elif it == "revenue":
                out = self._revenue_text()
            elif it == "budget":
                out = self._page("bg")
            elif it == "help":
                out = self._page("menu")
            elif it == "pause_leg":
                out = self._ask_pause_card(text) if leg else ("کدام پا را مکث کنم؟",
                                                               self._leg_choice_keyboard("p"))
            elif it == "resume_leg":
                out = self._ask_resume_card(text) if leg else ("کدام پا را ادامه بدهم؟",
                                                               self._leg_choice_keyboard("r"))
            elif it == "scan_metadata":
                out = self._page("map")        # کارتِ شروع scan (نه اجرای مستقیم)
            elif it == "approvals":
                out = self._page("ap")
            else:
                # ۲۰۲۶-۰۷-۲۷ — قبل از «متوجه نشدم»، یک‌بار واقعاً بپرس.
                # تا امروز هر جملهٔ آزادی که به فرمان نگاشت نمی‌شد به کارتِ ثابت
                # می‌افتاد؛ `llm_intent` فقط **دسته‌بندی** می‌کرد و هرگز جواب نمی‌داد.
                # `ask_brain` فقط جواب می‌دهد و هیچ گیتی را لمس نمی‌کند — هر اقدامی
                # همچنان از mission/action_graph/approval می‌رود. flag خاموش یا هر
                # شکست → دقیقاً کارتِ امروز، بایت‌به‌بایت.
                out = None
                try:
                    import ask_brain as _ab
                    if _ab.enabled():
                        _a = _ab.ask(text, topic_key=self._topic_key(msg))
                        if _a.get("ok"):
                            out = _ab.card(_a["text"], _a.get("model") or "")
                        elif _a.get("reason") in ("not-a-paid-brain", "no-answer",
                                                  "ask-exception"):
                            _brain_busy = "llm-no-answer"
                except Exception:  # noqa: BLE001 — گفتگو هرگز مسیرِ بات را نمی‌کشد
                    out = None
                if out is None:
                    out = self._ask_unknown_card(_brain_busy)
            txt, kb = out if isinstance(out, tuple) else (str(out or ""), None)
            mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb,
                                    topic_id=self._reply_thread(msg))
        except Exception:  # noqa: BLE001
            mid, kind = None, "ask_error"
        return {"kind": kind, "sent": mid is not None}

    @staticmethod
    def _leg_from_text(text: str) -> "str | None":
        """حدسِ content-free از نامِ پا در متنِ مالک. فقط whitelist؛ ابهام → None."""
        low = str(text or "").lower()
        aliases = {
            "lead": ("lead", "لید", "نقاش", "نقاشی"),
            "ziman": ("ziman", "گالری", "gallery", "ziman"),
            "mining": ("mining", "ماینینگ", "min"),
            "crypto": ("crypto", "کریپتو", "etoro", "etoro"),
            "accounting": ("accounting", "حساب", "اکانتینگ"),
            "studio_pf": ("studio", "استودیو", "project-f", "project f"),
            "knowledge": ("knowledge", "دانش"),
            "cartographer": ("cartographer", "نقشه", "نقشه‌بردار", "نقشه بردار"),
        }
        hits = [k for k, vals in aliases.items() if any(v.lower() in low for v in vals)]
        return hits[0] if len(hits) == 1 else None

    def _ask_pause_card(self, text: str) -> tuple:
        key = self._leg_from_text(text)
        if key:
            return (f"⏸ مکثِ <code>{key}</code>؟\nیک‌تاپ بزن؛ از ضربانِ بعد اثر می‌کند.",
                    [[{"text": f"⏸ مکث {key}", "callback_data": f"lg:{key}:p"}],
                     [{"text": "🔙 منو", "callback_data": "mn:menu"}]])
        return ("کدام پا را مکث کنم؟", self._leg_choice_keyboard("p"))

    def _ask_resume_card(self, text: str) -> tuple:
        key = self._leg_from_text(text)
        if key:
            return (f"▶️ ادامهٔ <code>{key}</code>؟\nیک‌تاپ بزن؛ اگر مکث باشد برداشته می‌شود.",
                    [[{"text": f"▶️ ادامه {key}", "callback_data": f"lg:{key}:r"}],
                     [{"text": "🔙 منو", "callback_data": "mn:menu"}]])
        return ("کدام پا را ادامه بدهم؟", self._leg_choice_keyboard("r"))

    @staticmethod
    def _leg_choice_keyboard(act: str) -> list:
        rows, legs = [], ("lead", "ziman", "mining", "crypto", "accounting",
                          "studio_pf", "knowledge", "cartographer")
        for i in range(0, len(legs), 2):
            rows.append([{"text": ("⏸ " if act == "p" else "▶️ ") + k,
                          "callback_data": f"lg:{k}:{act}"} for k in legs[i:i + 2]])
        rows.append([{"text": "🔙 منو", "callback_data": "mn:menu"}])
        return rows

    @staticmethod
    def _ask_unknown_card(brain_busy: str = "") -> tuple:
        """کارتِ «نفهمیدم» — ولی وقتی *نفهمیدن* واقعاً *نرسیدن به مغز* بوده،
        همان را بگو. «متوجه نشدم» در آن حالت دروغِ کوچکی است که مالک را به این
        نتیجه می‌رساند که بات کودن است، درحالی‌که فقط پنجرهٔ ۲۰ثانیه‌ایِ مغزِ
        محلی هنوز باز نشده. (۲۰۲۶-۰۷-۲۶)"""
        if brain_busy in ("llm-no-answer", "llm-error", "router-unavailable"):
            text = ("🧠 <b>مغزم چند ثانیه دیگر آزاد می‌شود</b>\n"
                    "▸ حرفت را نفهمیدم چون نرسید به مغز، نه چون بی‌معنی بود\n"
                    "▸ نکنی: همین‌طور می‌ماند — دوباره بفرست، همان جمله کافی است\n"
                    "<i>یا از این‌ها یکی را بزن:</i>")
        else:
            text = "🐙 متوجه نشدم. منظورت یکی از این‌هاست؟"
        kb = [[{"text": "📊 وضعیت", "callback_data": "mn:st"},
               {"text": "🧭 تصمیم‌ها", "callback_data": "mn:ap"}],
              [{"text": "🦵 مکث/ادامه پاها", "callback_data": "mn:lg"},
               {"text": "💰 درآمد", "callback_data": "mn:rv"}],
              [{"text": "🐙 منو", "callback_data": "mn:menu"}]]
        return text, kb

    def _budget_text(self) -> str:
        """کارتِ پیشنهادِ تخصیصِ ماهِ بعد (propose-only). render → متن؛ اسنپ‌شاتِ
        propose-only ثبت می‌کند (هرگز budgets.yaml). fail-soft → پیام آرام."""
        r = self._rmod()
        if r is None or not hasattr(r, "render_budget_proposal"):
            return "🐙 پیشنهادِ بودجه در دسترس نیست."
        try:
            txt = str(r.render_budget_proposal() or "")
        except Exception:  # noqa: BLE001
            return "🐙 پیشنهادِ بودجه در دسترس نیست."
        self._persist_proposal(txt)
        return txt or "🐙 هنوز پیشنهادی نیست."

    @staticmethod
    def _persist_proposal(text: str) -> bool:
        """اسنپ‌شاتِ propose-only از کارتِ بودجه (state/telegram/proposals/). هرگز
        budgets.yaml/ledger — فقط رکوردِ تاریخ‌دار. fail-soft → False."""
        try:
            d = opslib.STATE_DIR / "telegram" / "proposals"
            d.mkdir(parents=True, exist_ok=True)
            opslib.append_jsonl(d / "budget-proposals.jsonl",
                                {"ts": opslib.now_iso(), "kind": "budget_proposal",
                                 "propose_only": True, "text": text})
            return True
        except Exception:  # noqa: BLE001
            return False

    def _revenue_text(self) -> str:
        """کارتِ نمایشِ درآمد (aggregate، PII-safe). attribution.confirmed_revenue() را
        می‌خواند و render می‌کند (فقط‌خواندنی). fail-soft → پیام آرام."""
        r = self._rmod()
        if r is None or not hasattr(r, "render_revenue"):
            return "🐙 نمایِ درآمد در دسترس نیست."
        try:
            import attribution
            rev = attribution.confirmed_revenue()
        except Exception:  # noqa: BLE001
            rev = {}
        try:
            return str(r.render_revenue(rev) or "") or "🐙 هنوز درآمدِ تأییدشده‌ای نیست."
        except Exception:  # noqa: BLE001
            return "🐙 نمایِ درآمد در دسترس نیست."

    # ── مرکزِ فرماندهی: صفحه‌ها + اکشن‌ها (رأی مالک 2026-07-17) ────────────────────
    @staticmethod
    def _power_mod():
        """importِ lazyِ power (fail-soft → None = دکمه‌های کنترل بی‌اثرِ امن)."""
        try:
            import power
            return power
        except Exception:  # noqa: BLE001
            return None

    def _page(self, name: str) -> tuple:
        """(متن، کیبورد)ِ هر صفحهٔ منو — ناوبری با editِ همان پیام.

        از این نقطه به بعد UI باید «زنده» باشد: هر render تا حد ممکن feeds تازه و
        paused_map تازه می‌گیرد. خطا = fallback آرام، نه crash."""
        r, pw = self._rmod(), self._power_mod()
        back = [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]
        p_on = bool(pw and pw.power_on())
        if r is None:
            return "🐙 render در دسترس نیست.", None
        try:
            feeds = r.collect_feeds() if hasattr(r, "collect_feeds") else {}
        except Exception:  # noqa: BLE001
            feeds = {}
        try:
            if name == "st":
                kb = [[{"text": "🔄 تازه‌سازی", "callback_data": "mn:st"}]]
                try:
                    n = int(((feeds.get("guidance") or {}).get("n") or 0)) if isinstance(feeds, dict) else 0
                except (TypeError, ValueError):
                    n = 0
                if n:
                    kb.append([{"text": f"🧭 {n} تصمیم‌ها", "callback_data": "mn:ap"}])
                kb += back
                return str(r.render_status(feeds) or ""), kb
            if name == "qr":
                return self._quarantine_text(feeds), [[{"text": "🔄 تازه‌سازی", "callback_data": "mn:qr"}]] + back
            if name == "ap":
                return self._approvals_queue_page()
            if name == "map":
                try:
                    scan_state = ms_mod.load_state()
                except Exception:  # noqa: BLE001
                    scan_state = {}
                return r.render_map_page(scan_state)
            if name == "ms":
                return mission_mod.mission_card()
            if name == "lg" and pw:
                return r.render_organs(pw.paused_map(), _load_config())
            if name == "bg":
                kb = ([[{"text": "💰 اعمالِ سقف‌ها (دوکلیک)", "callback_data": "pw:ba"}]]
                      if p_on else []) + back
                return self._budget_text(), kb
            if name == "rv":
                return self._revenue_text(), back
            if name == "sy":
                s = {"stop": opslib.STOP_ORGANISM.exists(),
                     "halt": opslib.HALT_ALL.exists(),
                     "restart": RESTART_REQUESTED.exists()}
                return r.render_power(p_on, s)
            if name == "fl" and pw:
                return r.render_flags({n: pw.flag_state(n) for n in pw.FLAG_MENU})
        except Exception:  # noqa: BLE001
            pass
        try:
            paused = pw.paused_map() if pw else {}
            return r.render_menu(p_on, feeds=feeds, paused=paused)
        except TypeError:
            return r.render_menu(p_on)
        except Exception:  # noqa: BLE001
            return "🐙 منو در دسترس نیست.", back

    @staticmethod
    def _quarantine_text(feeds: dict | None = None) -> str:
        """کارتِ قرنطینهٔ content-free: فقط شمارش و مسیرِ رسیدگی؛ محتوا/هویت echo نمی‌شود."""
        f = feeds if isinstance(feeds, dict) else {}
        board = f.get("board") if isinstance(f.get("board"), dict) else {}
        counts = board.get("counts") if isinstance(board.get("counts"), dict) else {}
        try:
            n = int(counts.get("quarantined") or 0)
        except (TypeError, ValueError):
            n = 0
        if n <= 0:
            return "☣️ <b>قرنطینه</b>\nفعلاً چیزی در قرنطینه گزارش نشده."
        return (f"☣️ <b>قرنطینه</b>\n"
                f"<code>{n}</code> مورد نیازمند رسیدگی است.\n"
                "محتوا اینجا نشان داده نمی‌شود؛ فقط کنترل و شمارش.")

    def _approvals_text(self) -> str:
        """صفِ تأییدها (legacy): شمارش + آخرین verdictها (content-free — فقط id/فعل).

        حفظ‌شده برای سازگاری با پاسخ‌های متنی قدیمی؛ کارتِ کامل با کیبورد از
        _approvals_queue_page می‌آید."""
        try:
            sync = aps_mod.sync_to_octopus_state()
        except Exception:  # noqa: BLE001
            sync = {"count": 0, "recent": []}
        lines = [f"✅ <b>تأییدها</b> · {sync.get('count', 0)} تصمیمِ ثبت‌شده تا حالا."]
        for v in sync.get("recent", [])[:5]:
            if isinstance(v, dict):
                emo = {"ok": "✅", "no": "❌", "later": "⏳"}.get(str(v.get("verdict")), "•")
                lines.append(f"{emo} <code>{v.get('id', '?')}</code>")
        return "\n".join(lines)

    def _approvals_queue_page(self) -> tuple:
        """صفحهٔ کاملِ صف تأیید با کیبوردِ عملگرا (فاز E).

        هم pending queue اختاپوس و هم تاریخچهٔ verdict قدیمی را نشان می‌دهد.
        هر job دکمه‌های ap:ok/no/detail دارد (اجرای واقعی در callback handler)."""
        r = self._rmod()
        if r is None or not hasattr(r, "render_approvals_queue"):
            return self._approvals_text(), [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]
        try:
            pending = aps_mod.load_pending()
            counts = aps_mod.summary()
            legacy = aps_mod.sync_to_octopus_state().get("recent", [])
        except Exception:  # noqa: BLE001
            pending, counts, legacy = [], {}, []
        # P3 (Stage-1): پشتِ OCTOPUS_WIRE_CB_TOKEN → mintِ توکنِ HMAC per-job، bind به
        # owner_id + action_hash(content_sha256 روی type/risk) + expires_epoch. فلگ خاموش
        # → mint=None → کارتِ tokenless بایت‌به‌بایتِ قبلی.
        _mint = None
        try:
            if cbtok.flag_on():
                _owner = getattr(self._client, "owner_chat_id", None)
                _by_id = {str(j.get("id")): j for j in pending if isinstance(j, dict)}
                _mint = lambda jid, act: cbtok.mint(
                    str(jid), act, _owner,
                    self._ap_action_hash(act, str(jid), _by_id.get(str(jid), {})),
                    str(_by_id.get(str(jid), {}).get("expires_epoch", "")))
        except Exception:  # noqa: BLE001 — mint اختیاری؛ خطا = کارتِ عادی
            _mint = None
        try:
            return r.render_approvals_queue(pending, counts, legacy, mint=_mint)
        except Exception:  # noqa: BLE001
            return self._approvals_text(), [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]

    def _edit_page(self, cbq: dict, page: str) -> None:
        """editِ درجای همان پیام به صفحهٔ خواسته (ناوبریِ منو)."""
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")
        if not isinstance(mid, int):
            return
        txt, kb = self._page(page)
        try:
            self._client.edit(mid, _scrub(str(txt or "")), keyboard=kb, chat_id=chat)
        except Exception:  # noqa: BLE001
            pass

    def _handle_center_callback(self, cbq: dict, data: str) -> dict:
        """verbهای مرکز: mn (ناوبری) · lg (مکث/ادامهٔ پا — ردهٔ A) ·
        pw (مسلح‌کردنِ اکشنِ حساس) · pwc (تأییدِ دوکلیک — ردهٔ B)."""
        pw = self._power_mod()
        parts = data.split(":")
        verb = parts[0]

        if verb == "mn" and len(parts) == 2:
            self._edit_page(cbq, parts[1])
            self._answer(cbq)
            return {"kind": "center", "page": parts[1]}

        # اتاقِ آینه (۲۰۲۶-۰۷-۲۷): دو دکمهٔ فقط‌خواندنی و $۰ — «چه می‌دانم» و
        # «تصحیح‌ها». هیچ‌کدام مغز صدا نمی‌زند و هیچ state ای عوض نمی‌کند؛ فقط
        # همان چیزی را نشان می‌دهد که در contextِ گفتگو هم می‌رود.
        # مذاکره (۲۰۲۶-۰۷-۲۷): سه جواب به‌جای دو — قبول / نه / **شرط بگذار**.
        # «قبول» هیچ چیز را اجرا نمی‌کند؛ فقط ثبت می‌شود. اجرا همچنان از همان
        # گیت‌هایی می‌رود که این مسیر اصلاً لمسشان نمی‌کند.
        if verb == "ng" and len(parts) == 3:
            act, oid = parts[1], parts[2]
            msg = cbq.get("message") or {}
            chat_id = (msg.get("chat") or {}).get("id")
            try:
                import negotiate as _ng
                if act == "c":
                    # شرط‌گذاری: منتظرِ متنِ بعدیِ مالک می‌مانیم (RAM؛ ری‌استارت =
                    # لغوِ امن، مثلِ _awaiting_rfc_edit).
                    self._awaiting_counter = oid
                    self._client.send(
                        _scrub("✍️ شرطت را بنویس — پیشنهادِ بعدی‌ام آن را رعایت می‌کند."),
                        chat_id=chat_id, topic_id=self._reply_thread(msg))
                    self._answer(cbq, "منتظرِ شرطتم")
                    return {"kind": "negotiate", "awaiting": oid}
                r = _ng.respond(oid, "accept" if act == "a" else "reject")
                self._answer(cbq, "ثبت شد" if r.get("ok") else str(r.get("reason"))[:60])
                if r.get("ok"):
                    self._client.send(
                        _scrub("✅ پذیرفتم — ثبت شد. اجرا هنوز نشده؛ از مسیرِ تأیید می‌آید."
                               if act == "a" else "❌ باشد، کنارش گذاشتم."),
                        chat_id=chat_id, topic_id=self._reply_thread(msg))
                return {"kind": "negotiate", "verdict": act, "ok": r.get("ok")}
            except Exception:  # noqa: BLE001
                self._answer(cbq)
                return {"kind": "negotiate", "ok": False}

        if verb == "mr" and len(parts) == 2:
            try:
                import mirror_room as _mr
                body = (_mr.know_card() if parts[1] == "know"
                        else _mr.corrections_card())
            except Exception:  # noqa: BLE001
                body = "🪞 آینه در دسترس نیست."
            msg = cbq.get("message") or {}
            try:
                self._client.send(_scrub(body),
                                  chat_id=(msg.get("chat") or {}).get("id"),
                                  topic_id=self._reply_thread(msg))
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq)
            return {"kind": "mirror", "view": parts[1]}

        if verb == "lg" and len(parts) == 3 and pw:
            key, act = _sanitize_id(parts[1]), parts[2]
            ok, msg = (pw.pause_leg(key) if act == "p" else pw.resume_leg(key))
            self._answer(cbq, msg[:180])
            self._edit_page(cbq, "lg")
            return {"kind": "center", "leg": key, "ok": ok}

        if verb == "pw" and len(parts) == 2 and pw:
            act = _sanitize_id(parts[1])
            label = (f"🚩 toggleِ فلگ {act[3:]}" if act.startswith("fg-")
                     else pw.POWER_ACTIONS.get(act, ("؟",))[0])
            cfg = _load_config()
            cfg["pw_arm"] = {"act": act, "ts": float(self._clock())}
            _save_config(cfg)
            r = self._rmod()
            msg = cbq.get("message") or {}
            mid = msg.get("message_id")
            chat = (msg.get("chat") or {}).get("id")
            if r is not None and isinstance(mid, int):
                txt, kb = r.render_confirm(label, act)
                try:
                    self._client.edit(mid, _scrub(txt), keyboard=kb, chat_id=chat)
                except Exception:  # noqa: BLE001
                    pass
            self._answer(cbq, "برای اجرا، تأییدِ دوم را بزن")
            return {"kind": "center", "armed": act}

        if verb == "pwc" and len(parts) == 2 and pw:
            act = _sanitize_id(parts[1])
            cfg = _load_config()
            arm = cfg.get("pw_arm") if isinstance(cfg.get("pw_arm"), dict) else {}
            fresh = (arm.get("act") == act and
                     float(self._clock()) - float(arm.get("ts", 0) or 0) <= pw.ARM_FRESH_S)
            cfg.pop("pw_arm", None)
            _save_config(cfg)
            if not fresh:
                self._answer(cbq, "تأیید منقضی/نامعتبر — دوباره از منو")
                self._edit_page(cbq, "sy")
                return {"kind": "center", "expired": act}
            if act.startswith("fg-"):
                ok, msg = pw.toggle_flag(act[3:])
            else:
                fn = pw.POWER_ACTIONS.get(act, (None, None))[1]
                ok, msg = fn() if fn else (False, "اکشنِ ناشناخته")
            self._answer(cbq, msg[:180])
            self._edit_page(cbq, "fl" if act.startswith("fg-") else "sy")
            return {"kind": "center", "power": act, "ok": ok}

        self._answer(cbq, "نادیده")
        return {"kind": "center", "ignored": data[:24]}

    def _handle_map_callback(self, cbq: dict, data: str) -> dict:
        """verbهای نقشه‌برداریِ metadata (فاز D — فقط‌خواندنی، propose-only).

        - map:start → یک job در صف تأیید می‌سازد (risk=read) و در همین لحظه یک scan
          محدود و sync روی ریشه اجرا می‌کند (fail-soft؛ خطر کم چون فقط metadata).
          برای scanِ کامل (بدونِ سقف) کارت تأیید جداگانه می‌سازد.
        - map:status → صفحهٔ map را refresh می‌کند (mn:map).
        - map:report → آخرین گزارش را در یک پیامِ نوی نشان می‌دهد.

        امنیت: فقط metadata؛ هیچ محتوای فایل خوانده نمی‌شود (gating در metadata_scan).
        کارت تأیید بیشتر برای UX (هشدارِ طولِ احتمالی) است تا gating واقعی."""
        parts = data.split(":")
        if len(parts) < 2:
            self._answer(cbq, "نادیده")
            return {"kind": "map", "ignored": data[:24]}
        action = parts[1]
        msg = cbq.get("message") or {}
        mid = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")

        if action == "start":
            # یک scan محدود و sync همین حالا (خطرِ کم: فقط metadata)
            try:
                result = ms_mod.scan_metadata(max_files=50_000, max_seconds=60)
                paths = ms_mod.write_manifest(result)
                summary = ms_mod.summarize_manifest(result)
                # job در صف تأیید (برای بازبینیِ انسان)
                try:
                    aps_mod.add_pending({
                        "type": "metadata_scan", "title": "نقشه‌برداری metadata",
                        "risk": "read", "requires_confirmation": False,
                        "dry_run_report": paths.get("report", "")[:500],
                        "source": "telegram"})
                except Exception:  # noqa: BLE001
                    pass
                toast = summary[:180]
            except Exception as e:  # noqa: BLE001
                toast = f"خطا: {type(e).__name__}"
                summary = "🗺️ خطا در اسکن"
            self._answer(cbq, toast)
            # refresh صفحهٔ map با stateِ نو
            self._edit_page(cbq, "map")
            return {"kind": "map", "action": "start", "summary": summary[:200]}

        if action == "report":
            try:
                st = ms_mod.load_state()
                latest_report = None
                rp_dir = ms_mod._REPORTS_DIR
                if rp_dir.exists():
                    files = sorted(rp_dir.glob("metadata_scan_*.md"),
                                   key=lambda p: p.stat().st_mtime, reverse=True)
                    latest_report = files[0] if files else None
                if latest_report and latest_report.exists():
                    txt = latest_report.read_text("utf-8")[:3500]
                    self._client.send(_scrub(txt), chat_id=chat)
                    self._answer(cbq, "گزارش ارسال شد")
                else:
                    self._answer(cbq, "هنوز گزارشی نیست — اول map:start را بزن")
            except Exception:  # noqa: BLE001
                self._answer(cbq, "گزارش در دسترس نیست")
            return {"kind": "map", "action": "report"}

        # action == "status" یا هر چیزِ دیگر → refresh
        self._edit_page(cbq, "map")
        self._answer(cbq, "تازه‌سازی شد")
        return {"kind": "map", "action": action}

    def _handle_mission_callback(self, cbq: dict, data: str) -> dict:
        """verbهای Mission Genome (ms:*).

        این handler فقط state مأموریت را عوض/ثبت می‌کند و هیچ patch/code.apply واقعی
        انجام نمی‌دهد. apply واقعی همچنان مسیر جداگانهٔ code_autonomy + approval +
        shadow-green + rollback دارد. دکمه‌های test/review فقط request/note ثبت می‌کنند
        تا UI دروغ نگوید که تست یا دکتر واقعاً اجرا شده است."""
        parts = data.split(":", 2)
        if len(parts) < 2:
            self._answer(cbq, "نادیده")
            return {"kind": "mission", "ignored": data[:24]}
        action = parts[1]
        mid = _sanitize_id(parts[2]) if len(parts) > 2 else ""
        msg = cbq.get("message") or {}
        m_id = msg.get("message_id")
        chat = (msg.get("chat") or {}).get("id")

        if action == "open" and mid:
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "Mission")
            return {"kind": "mission", "action": "open", "id": mid}

        if action == "test" and mid:
            # فلگ‌خاموش پیش‌فرض: بدونِ فلگ، دقیقاً رفتارِ قبلی (فقط request/note ثبت می‌شود،
            # UI دروغ نمی‌گوید). با OCTOPUS_WIRE_MISSION_RUNNER=1 runnerِ v0 واقعاً در worktreeِ
            # ایزوله تست‌های allowlisted را اجرا می‌کند (هرگز apply/patch؛ درختِ زنده لمس نمی‌شود).
            wired = os.environ.get("OCTOPUS_WIRE_MISSION_RUNNER") == "1" and runner_mod is not None
            if wired:
                try:
                    out = runner_mod.run_mission(mid)
                    toast = ("🧪 اجرا سبز (شواهد ثبت شد)" if out.get("ok")
                             else f"🧪 اجرا: {out.get('refused') or 'قرمز'} — شواهد ثبت شد")
                except Exception:  # noqa: BLE001 — fail-soft: هر خطا → note، هرگز crash
                    mission_mod.add_note(mid, "runner error; fell back to request-only")
                    toast = "🧪 خطای runner؛ فقط درخواست ثبت شد"
            else:
                mission_mod.add_note(mid, "owner requested tests/fitness from Telegram; runner flag off (staged)")
                mission_mod.set_state(mid, "planned", "test requested; awaiting runner")
                toast = "درخواست تست ثبت شد؛ اجرا جداست"
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, toast)
            return {"kind": "mission", "action": "test_request", "id": mid, "wired": wired}

        if action == "review" and mid:
            mission_mod.add_note(mid, "owner requested doctor/epistemics review from Telegram; reviewer not executed by center")
            mission_mod.set_state(mid, "planned", "review requested; awaiting doctor/epistemics")
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "درخواست review ثبت شد")
            return {"kind": "mission", "action": "review_request", "id": mid}

        if action in ("approve", "reject") and mid:
            # P3 (D4): فلگ روشن → این verbِ رأی‌دهنده باید توکنِ HMACِ معتبر داشته باشد
            # (ms:<action>:<mid>:<token>). tokenlessِ قدیمی/جعلی/منقضی = رد (fail-closed،
            # دقیقاً مثلِ ap:). فلگ خاموش → این بلوک اجرا نمی‌شود و mid همان مقدارِ بالا می‌ماند.
            if cbtok.flag_on():
                seg = data.split(":")                        # ms : action : mid [: token]
                mid = _sanitize_id(seg[2]) if len(seg) > 2 else ""   # midِ تمیز (token جدا)
                token = seg[3] if len(seg) > 3 else None
                _exp = self._cb_expires_for(mid)
                if not mid or not self._cb_verify(token, mid, action, _exp):
                    self._answer(cbq, "توکنِ نامعتبر — کارت را از منو دوباره باز کن")
                    return {"kind": "mission", "rejected": "bad-token", "id": mid}
                if _exp:                                     # enforceِ جداگانهٔ انقضا (مثلِ ap:)
                    try:
                        import time as _t
                        if _t.time() > float(_exp):
                            self._answer(cbq, "کارت منقضی شده — از منو دوباره باز کن")
                            return {"kind": "mission", "rejected": "expired", "id": mid}
                    except (TypeError, ValueError):
                        pass
            approved = action == "approve"
            out = mission_mod.set_owner_verdict(mid, approved)
            try:
                if approved:
                    aps_mod.approve(mid)
                    aps_mod.record_legacy_verdict(mid, "ok")
                else:
                    aps_mod.reject(mid)
                    aps_mod.record_legacy_verdict(mid, "no")
            except Exception:  # noqa: BLE001
                pass
            if out:
                # Wave1-A: رأیِ مالک روی missionِ همین کارت هم measurementِ پایدار می‌شود
                # (idempotent — اگر همان job از مسیرِ ap: هم رأی بخورد، رویدادِ تکراری نمی‌نشیند).
                self._durable_verdict_outcome("ok" if approved else "no", mid,
                                              {"type": "mission"})
            txt, kb = mission_mod.mission_card(mid)
            kb = self._tok_kb(kb)                # P3 (D4): توکنِ ms: وقتی فلگ روشن (وگرنه no-op)
            try:
                if isinstance(m_id, int):
                    self._client.edit(m_id, _scrub(txt), keyboard=kb, chat_id=chat)
            except Exception:  # noqa: BLE001
                pass
            self._answer(cbq, "تأیید شد" if approved else "رد شد")
            return {"kind": "mission", "action": action, "id": mid, "ok": bool(out)}

        self._answer(cbq, "نادیده")
        return {"kind": "mission", "ignored": data[:24]}

    def _ap_action_hash(self, action: str, jid: str, job: dict) -> str:
        """P3: hashِ محتوایی برای bindِ توکنِ callback — content_sha256(action, jid, {type,risk}).
        anti-TOCTOU: اگر type/riskِ job عوض شود توکن باطل می‌شود. fail-soft → "" (آنگاه
        verify بر jid/action/owner/expires تکیه می‌کند)."""
        try:
            import mission_contract as _mc
            return _mc.content_sha256(action, str(jid),
                                      {"type": (job or {}).get("type"),
                                       "risk": (job or {}).get("risk")})
        except Exception:  # noqa: BLE001
            return ""

    # ── P3 (D4): توکنِ HMACِ callback برای verbهای legacy (ok/no/later) و mission (ms:) ──
    # همان طرحِ ap: (jid|action|owner|action_hash|expires) از callback_token — «طرحِ دوم»
    # اختراع نمی‌شود. این verbها jobِ محتوایی مثلِ ap: ندارند → action_hash="". فقط mission
    # می‌تواند expires داشته باشد (اگر missionِ ذخیره‌شده expires_epoch داشته باشد). فلگ خاموش
    # → این مسیرها اصلاً لمس نمی‌شوند (بایت‌به‌بایتِ امروز). is_owner از handle_update اول است.
    def _cb_expires_for(self, mid: str) -> str:
        """expires_epochِ missionِ ذخیره‌شده (برای bind/enforceِ توکنِ ms:) یا "" (بی‌انقضا).
        fail-soft → "" (هرگز نمی‌شکند)."""
        try:
            m = mission_mod.get(mid)
            return str((m or {}).get("expires_epoch", "")) if isinstance(m, dict) else ""
        except Exception:  # noqa: BLE001
            return ""

    def _cb_mint(self, jid: str, action: str, expires: str = "") -> str:
        """mintِ توکنِ HMAC با همان cbtok.mint (action_hash=""). بی‌راز/خطا → "" (fail-closed:
        کارتِ tokenlessِ inert، نه یک توکنِ جعلی‌پذیر)."""
        try:
            owner = getattr(self._client, "owner_chat_id", None)
            return cbtok.mint(str(jid), action, owner, "", expires)
        except Exception:  # noqa: BLE001
            return ""

    def _cb_verify(self, token, jid: str, action: str, expires: str = "") -> bool:
        """verifyِ متقارن با _cb_mint. نبودِ token/secret یا هر عدم‌تطابق = False (fail-closed)."""
        try:
            owner = getattr(self._client, "owner_chat_id", None)
            return cbtok.verify(token, str(jid), action, owner, "", expires)
        except Exception:  # noqa: BLE001
            return False

    def _tok_btn(self, btn: dict) -> dict:
        """یک دکمه را در صورتِ لزوم توکن‌دار کن (فقط verbهای گیت‌شده). idempotent:
        اگر callback_data قبلاً توکن دارد یا verbِ گیت‌نشده است، دست‌نخورده برمی‌گردد."""
        cd = btn.get("callback_data")
        if not isinstance(cd, str):
            return btn
        seg = cd.split(":")
        new_cd = None
        if len(seg) == 2 and seg[0] in _VERDICTS:            # legacy ok/no/later:<did> (بی‌توکن)
            tok = self._cb_mint(seg[1], seg[0], "")
            if tok:
                new_cd = f"{cd}:{tok}"
        elif len(seg) == 3 and seg[0] == "ms" and seg[1] in ("approve", "reject"):  # ms:<v>:<mid>
            exp = self._cb_expires_for(seg[2])
            tok = self._cb_mint(seg[2], seg[1], exp)
            if tok:
                new_cd = f"{cd}:{tok}"
        if new_cd is None:
            return btn
        nb = dict(btn)
        nb["callback_data"] = new_cd
        return nb

    def _tok_kb(self, kb):
        """کیبورد را وقتی OCTOPUS_WIRE_CB_TOKEN روشن است توکن‌دار کن تا کارتِ legacy/mission با
        handlerِ token-gated کار کند («exactly like ap:»). فلگ خاموش → kb بایت‌به‌بایت بدونِ تغییر.
        فقط verbهای گیت‌شده لمس می‌شوند؛ ap:/mn:/lg:/ms:open|test|review دست‌نخورده."""
        try:
            if not cbtok.flag_on() or not isinstance(kb, list):
                return kb
        except Exception:  # noqa: BLE001
            return kb
        out = []
        for row in kb:
            if not isinstance(row, list):
                out.append(row)
                continue
            out.append([self._tok_btn(b) if isinstance(b, dict) else b for b in row])
        return out

    def _handle_approval_callback(self, cbq: dict, data: str) -> dict:
        """verbهای صفِ تأیید (فاز E — bridge اختاپوس).

        - ap:ok:<id>  → approval_store.approve(id) + record_legacy_verdict + refresh
        - ap:no:<id>  → approval_store.reject(id)  + record_legacy_verdict + refresh
        - ap:detail:<id> → کارتِ جزئیاتِ content-free (فقط title/type/risk؛ نه محتوا)

        توجه: این فقط state را عوض می‌کند (pending → approved/rejected). اجرای واقعیِ
        job (اگر risk=high) به handlerهای جداگانه یا power-gate واگذار می‌شود — این
        لایه فقط صف است. risk=high → هشدار در toast."""
        # P3 (Stage-1): وقتی فلگ OCTOPUS_WIRE_CB_TOKEN روشن است، ok/no باید توکنِ HMACِ
        # معتبر داشته باشند (ap:<action>:<jid>:<token>). callbackِ قدیمیِ tokenless یا
        # توکنِ نامعتبر/دستکاری‌شده = رد (fail-closed). فلگ خاموش → مسیرِ قبلی بایت‌به‌بایت.
        if cbtok.flag_on():
            seg = data.split(":")
            action = seg[1] if len(seg) > 1 else ""
            jid = _sanitize_id(seg[2]) if len(seg) > 2 else ""
            token = seg[3] if len(seg) > 3 else None
            if not action or not jid:
                self._answer(cbq, "نادیده")
                return {"kind": "approval", "ignored": data[:24]}
            if action in ("ok", "no"):
                _job = aps_mod.get(jid)
                _owner = getattr(self._client, "owner_chat_id", None)
                _ah = self._ap_action_hash(action, jid, _job or {})
                _exp = str((_job or {}).get("expires_epoch", ""))
                # (1) صحتِ HMAC (شاملِ content + expires) — دستکاری/جعل/tokenless قدیمی = رد
                if not cbtok.verify(token, jid, action, _owner, _ah, _exp):
                    self._answer(cbq, "توکنِ نامعتبر — کارت را از منو دوباره باز کن")
                    return {"kind": "approval", "rejected": "bad-token", "id": jid}
                # (2) enforcement جداگانهٔ انقضا (now <= expires) — 5.3
                try:
                    import time as _t
                    if _exp and _t.time() > float(_exp):
                        self._answer(cbq, "کارت منقضی شده — از منو دوباره باز کن")
                        return {"kind": "approval", "rejected": "expired", "id": jid}
                except (TypeError, ValueError):
                    pass
                # (3) destination binding — 5.4 (علاوه بر is_owner از from.id)
                _chat = ((cbq.get("message") or {}).get("chat") or {}).get("id")
                _allowed = {str(x) for x in (getattr(self._client, "owner_chat_id", None),
                                             getattr(self._client, "center_chat_id", None))
                            if x is not None}
                if _allowed and _chat is not None and str(_chat) not in _allowed:
                    self._answer(cbq, "مقصدِ نامعتبر")
                    return {"kind": "approval", "rejected": "bad-destination", "id": jid}
        else:
            parts = data.split(":", 2)
            if len(parts) < 3:
                self._answer(cbq, "نادیده")
                return {"kind": "approval", "ignored": data[:24]}
            action, jid = parts[1], _sanitize_id(parts[2])
        ok, msg, verdict = False, "", ""
        try:
            if action == "ok":
                job_before = aps_mod.get(jid)
                ok = aps_mod.approve(jid)
                verdict = "ok"
                msg = "✅ تأیید شد" if ok else "یافت نشد/قبلاً تصمیم گرفته شده"
                if ok:
                    aps_mod.record_legacy_verdict(jid, "ok")
                    # Wave1-A: فقط پس از transitionِ single-use ِ موفق (approve=True) —
                    # replay/تکرار به این خط نمی‌رسد؛ durable هم خودش idempotent است.
                    self._durable_verdict_outcome("ok", jid, job_before)
                    if (isinstance(job_before, dict) and job_before.get("type") == "mission") or mission_mod.get(jid):
                        mission_mod.set_owner_verdict(jid, True)
            elif action == "no":
                job_before = aps_mod.get(jid)
                ok = aps_mod.reject(jid)
                verdict = "no"
                msg = "❌ رد شد" if ok else "یافت نشد/قبلاً تصمیم گرفته شده"
                if ok:
                    aps_mod.record_legacy_verdict(jid, "no")
                    self._durable_verdict_outcome("no", jid, job_before)   # Wave1-A: ردِ پایدار
                    if (isinstance(job_before, dict) and job_before.get("type") == "mission") or mission_mod.get(jid):
                        mission_mod.set_owner_verdict(jid, False)
            elif action == "detail":
                job = aps_mod.get(jid)
                if job:
                    r = self._rmod()
                    # HTML-escape محلی (center._esc نداشت؛ html.escape کافی + scrub)
                    import html as _html
                    esc = lambda s: _html.escape(str(s if s is not None else ""))
                    risk = str(job.get("risk", "read"))
                    detail_text = (f"📝 <b>جزئیاتِ job</b>\n"
                                   f"<code>{_scrub(job.get('id', '?'))}</code>\n"
                                   f"نوع: {_scrub(job.get('type', '?'))}\n"
                                   f"ریسک: <code>{esc(risk)}</code>\n"
                                   f"وضعیت: {_scrub(job.get('status', '?'))}\n"
                                   f"عنوان: {_scrub(str(job.get('title', '?'))[:120])}")
                    if r is not None and isinstance(cbq.get("message"), dict):
                        m = cbq["message"]
                        try:
                            self._client.edit(m.get("message_id"), _scrub(detail_text),
                                              chat_id=(m.get("chat") or {}).get("id"))
                        except Exception:  # noqa: BLE001
                            pass
                    self._answer(cbq, "جزئیات (content-free)")
                    return {"kind": "approval", "action": "detail", "id": jid}
                else:
                    msg = "job یافت نشد"
        except Exception as e:  # noqa: BLE001
            msg = f"خطا: {type(e).__name__}"

        self._answer(cbq, msg[:180])
        # refresh صفحهٔ approvals برای نشان‌دادنِ تغییر
        self._edit_page(cbq, "ap")
        return {"kind": "approval", "action": action, "id": jid, "ok": ok, "verdict": verdict}

    def _handle_callback(self, cbq: dict) -> dict:
        """callback data = '<verb>:<id>' با verb ∈ ok/no/later (قراردادِ render_decision)
        یا verbهای مرکزِ فرماندهی (mn/lg/pw/pwc → _handle_center_callback) یا
        verbهای فاز D/E (map → _handle_map_callback، ap → _handle_approval_callback).
        ثبت به الگوی approval-file + رویداد + answer_callback؛ ok = mintِ اختیاریِ
        توکنِ HumanAppendGuard (فقط با رازِ env)."""
        data = str(cbq.get("data") or "")
        verb = data.split(":", 1)[0]
        if verb in ("mn", "lg", "pw", "pwc"):
            return self._handle_center_callback(cbq, data)
        if verb == "map":
            return self._handle_map_callback(cbq, data)
        if verb == "ap":
            return self._handle_approval_callback(cbq, data)
        if verb == "ms":
            return self._handle_mission_callback(cbq, data)
        if verb == "m":
            _m2 = self._menu2()
            if _m2 is not None and _m2.enabled():
                return self._handle_menu2_callback(cbq, data, _m2)
            # flag خاموش → سقوط به fallbackِ امروز (m در _VERDICTS نیست → «نادیده»). parity.
        parts = data.split(":", 1)
        if len(parts) != 2 or parts[0] not in _VERDICTS:
            self._answer(cbq, "نادیده")
            return {"kind": "callback", "verdict": None}
        verb = parts[0]
        # P3 (D4): فلگ روشن → ok/no/later هم باید توکنِ HMACِ معتبر داشته باشند
        # (<verb>:<did>:<token>). tokenlessِ قدیمی/جعلی = رد (fail-closed، مثلِ ap:). این
        # کارت‌ها jobِ محتوایی/انقضا ندارند → action_hash/expires="". فلگ خاموش → مسیرِ قدیمی
        # بایت‌به‌بایت (did = _sanitize_id(parts[1])). is_owner از handle_update از قبل اول است.
        if cbtok.flag_on():
            seg = data.split(":")
            did = _sanitize_id(seg[1]) if len(seg) > 1 else ""
            token = seg[2] if len(seg) > 2 else None
            if not did or not self._cb_verify(token, did, verb, ""):
                self._answer(cbq, "توکنِ نامعتبر — کارت را از منو دوباره باز کن")
                return {"kind": "callback", "verdict": None, "rejected": "bad-token", "id": did}
        else:
            did = _sanitize_id(parts[1])
        rec = {"id": did, "verdict": verb, "ts": opslib.now_iso(), "source": "tg-center"}
        if verb == "ok":
            tok = _mint_ha_token(did)                # بی‌راز → None → ثبتِ بدونِ توکن
            if tok:
                rec["ha_token"] = tok
        recorded = self._record_approval(rec)
        # Wave1-A: همان رأیِ احرازشدهٔ مالک (کارتِ تصمیمِ ok/no/later) به‌شکلِ measurement
        # در OutcomeStoreِ پایدار هم می‌نشیند — پشتِ فلگ، fail-soft، later=deferred.
        self._durable_verdict_outcome(verb, did)
        _emit_event("task.completed",
                    summary=f"verdict {verb} ثبت شد",      # content-free (فقط کلید/فعل)
                    approval_state=_VERDICT_APPROVAL_STATE.get(verb, "unknown"),
                    trace_id=did, status="ok" if recorded else "warn")
        self._answer(cbq, _VERDICT_TOAST.get(verb, ""))
        return {"kind": "callback", "verdict": verb, "id": did, "recorded": recorded}

    def _durable_verdict_outcome(self, verdict: str, proposal_id: str,
                                 job: "dict | None" = None) -> "bool | None":
        """Wave1-A (Part2): رأیِ احرازشدهٔ مالک از همین update-handler → OutcomeStoreِ
        پایدار (measurement-only)، پشتِ OCTOPUS_WIRE_VERDICT_OUTCOME (پیش‌فرض خاموش؛
        خاموش → None و **صفر** side-effect — parity بایت‌به‌بایت با امروز).

        فقط بعد از گیتِ is_owner صدا زده می‌شود (غیرمالک هرگز به handlerها نمی‌رسد) و
        فقط واژگانِ سنجش: ok/no/later → accepted-measurement/rejected/deferred — هرگز
        approval/delivery/settle/revenue استنتاج نمی‌شود (نگاشت+ناوردی‌ها در
        verdict_recorder ِ مشترک enforce؛ idempotent روی corr|proposal|event_type →
        دو-تپ/replay رویدادِ نو نمی‌نویسد). شناسه‌های «موجود» (mission/leg/lead) حفظ
        می‌شوند، هیچ‌کدام اختراع نمی‌شوند؛ صفِ تأیید مبلغ ندارد → value=0 (بدونِ CLAIM).
        fail-soft: هر خطا → None؛ مسیرِ callback هرگز نمی‌میرد."""
        try:
            for _p in (str(_HERE.parent / "outcomes"), str(_HERE.parent / "spine")):
                if _p not in sys.path:
                    sys.path.insert(0, _p)
            import verdict_recorder as _vr   # lazy — flag خاموش → همین‌جا خروجِ امن
            if not _vr.flag_on():
                return None
            import outcome_store as _osx
            odir = opslib.STATE_DIR / "outcomes"
            odir.mkdir(parents=True, exist_ok=True)
            o = _osx.OutcomeStore(path=odir / "outcomes.db")
            spine = None
            try:   # هم‌الگوی live_loop (Sol-T4): dual-write به spine فقط با flagِ خودش
                import event_spine as _esx
                if _esx.flag_on():
                    sdir = opslib.STATE_DIR / "spine"
                    sdir.mkdir(parents=True, exist_ok=True)
                    spine = _esx.EventSpine(path=sdir / "spine.db")
            except Exception:  # noqa: BLE001
                spine = None
            try:
                j = job if isinstance(job, dict) else {}
                res = _vr.record_owner_verdict(
                    o, proposal_id=str(proposal_id), verdict=str(verdict),
                    correlation_id=j.get("correlation_id"),
                    mission_id=(j.get("mission_id")
                                or (str(proposal_id) if j.get("type") == "mission" else None)),
                    leg_id=j.get("leg_id") or j.get("leg") or "unknown",
                    value_aud_claimed=0.0,
                    event_spine=spine,
                    lead_id=j.get("lead_id") or j.get("attribution_id"),
                    source="tg-center")
                return bool(res.get("recorded"))
            finally:
                o.close()
                if spine is not None:
                    try:
                        spine.close()
                    except Exception:  # noqa: BLE001
                        pass
        except Exception:  # noqa: BLE001 — ثبتِ رأی هرگز مسیرِ دکمه را نمی‌کشد
            return None

    @staticmethod
    def _record_approval(rec: dict) -> bool:
        """الگوی approval-file: یک فایل per-decision (آخرین verdict) + jsonl ِ تاریخچه.
        اتمیک، fail-soft (شکست → False، هرگز crash)."""
        try:
            d = opslib.STATE_DIR / "telegram" / "approvals"
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"{rec['id']}.json"
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, p)
            opslib.append_jsonl(d / "approvals.jsonl", rec)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _answer(self, cbq: dict, text: str = "") -> bool:
        """answer_callback — dismiss ِ spinner. fail-soft."""
        try:
            cid = cbq.get("id")
            if not cid:
                return False
            return bool(self._client.answer_callback(cid, text))
        except Exception:  # noqa: BLE001
            return False

    # ── run: یک دورِ poll+dispatch / حلقه با STOP ────────────────────────────────
    def run_once(self) -> int:
        """یک دورِ poll + dispatch. خروجی = تعدادِ updateهای پردازش‌شده.
        STOP/ناوصل → 0 (بدونِ هیچ فراخوانی). offset در config (restart-safe)."""
        if self.stopped() or not self._wired():
            return 0
        cfg = _load_config()
        try:
            offset = int(cfg.get("last_offset", 0) or 0)
        except (TypeError, ValueError):
            offset = 0
        try:
            ups = self._client.poll_updates(offset=offset, timeout_s=POLL_TIMEOUT_S) or []
        except Exception:  # noqa: BLE001 — خطای شبکه = دورِ خالی، حلقه زنده می‌ماند
            return 0
        n = 0
        max_id = offset - 1
        for u in ups:
            if not isinstance(u, dict):
                continue
            uid = u.get("update_id")
            if isinstance(uid, int) and uid > max_id:
                max_id = uid
            try:
                self.handle_update(u)
            except Exception:  # noqa: BLE001 — یک updateِ خراب حلقه را نمی‌کشد
                pass
            n += 1
        if max_id + 1 > offset:
            cfg["last_offset"] = max_id + 1
            _save_config(cfg)
        return n

    def run_forever(self, *, beat_every_s: float = 300.0) -> None:
        """حلقهٔ اصلی: poll پیوسته + beat دوره‌ای. ناوصل یا STOP → بازگشتِ فوری
        (حتی ensure_setup اجرا نمی‌شود — STOP مقدم بر همه‌چیز)."""
        if not self._wired() or self.stopped():
            return
        self.ensure_setup()
        # P3 (Stage-1، review-3): اگر قیدِ توکن روشن ولی OCTOPUS_CB_SECRET تنظیم نشده →
        # هشدارِ fail-soft (بدونِ echoِ مقدارِ secret). fail-closed از قبل برقرار است (توکن‌ها
        # verify نمی‌شوند → دکمه‌ها inert)؛ این فقط دیده‌شدنیِ misconfig را تأمین می‌کند.
        try:
            if cbtok.flag_on() and not cbtok.ready():
                import opslib as _ol
                _ol.alert(["⚠️ OCTOPUS_WIRE_CB_TOKEN روشن ولی OCTOPUS_CB_SECRET تنظیم نشده — "
                           "کارت‌های تأیید fail-closed/inert می‌مانند تا secret ست شود "
                           "(مقدارِ secret هرگز log نمی‌شود)."])
        except Exception:  # noqa: BLE001
            pass
        last_beat = 0.0
        while not self.stopped():
            self.run_once()
            now = float(self._clock())
            if now - last_beat >= float(beat_every_s):
                self.beat()
                last_beat = now


if __name__ == "__main__":
    # مسیرِ رسمیِ لودِ .env (مثل model_router/approval_channel): بدونِ این،
    # TELEGRAM_* در os.environ نیست و رانر «not wired»ِ کاذب می‌دهد. fail-soft.
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    c = Center()
    if not c.wired():
        print("tg-center: not wired (TELEGRAM_BOT_TOKEN/چت پیکربندی نشده) — خروجِ امنِ no-op")
        sys.exit(0)
    if c.stopped():
        print("tg-center: STOP-TG-CENTER هست — اجرا نمی‌شوم")
        sys.exit(0)
    print("tg-center: زنده — kill تمیز: فایلِ _ops/STOP-TG-CENTER را بساز")
    c.run_forever()
    print("tg-center: ایستاد (STOP)")
