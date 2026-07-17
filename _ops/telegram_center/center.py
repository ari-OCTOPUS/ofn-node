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
        return out

    # ── handle_update: فقط مالک — /now و callbackهای ok/no/later ─────────────────
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
            "/menu": lambda: self._page("menu"),
            "/start": lambda: self._page("menu"),
        }
        fn = handlers.get(cmd)
        if fn is None:
            return None                    # قراردادها: /now /budget /revenue /menu /start
        try:
            out = fn()
            txt, kb = out if isinstance(out, tuple) else (str(out or ""), None)
            mid = self._client.send(_scrub(txt), chat_id=chat_id, keyboard=kb)
        except Exception:  # noqa: BLE001
            mid = None
        return {"kind": cmd.lstrip("/"), "sent": mid is not None}

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
        """(متن، کیبورد)ِ هر صفحهٔ منو — ناوبری با editِ همان پیام."""
        r, pw = self._rmod(), self._power_mod()
        back = [[{"text": "🔙 منو", "callback_data": "mn:menu"}]]
        p_on = bool(pw and pw.power_on())
        if r is None:
            return "🐙 render در دسترس نیست.", None
        try:
            if name == "st":
                return str(r.render_status(r.collect_feeds()) or ""), back
            if name == "ap":
                return self._approvals_text(), back
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
        return r.render_menu(p_on)

    def _approvals_text(self) -> str:
        """صفِ تأییدها: شمارش + آخرین verdictها (content-free — فقط id/فعل)."""
        d = opslib.STATE_DIR / "telegram" / "approvals"
        lines = ["✅ <b>تأییدها</b>"]
        try:
            files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime,
                           reverse=True) if d.exists() else []
            lines.append(f"{len(files)} تصمیمِ ثبت‌شده تا حالا.")
            for p in files[:6]:
                try:
                    rec = json.loads(p.read_text("utf-8"))
                    emo = {"ok": "✅", "no": "❌", "later": "⏳"}.get(rec.get("verdict"), "•")
                    lines.append(f"{emo} <code>{rec.get('id', '?')}</code>")
                except (OSError, ValueError):
                    continue
        except OSError:
            lines.append("صف در دسترس نیست.")
        lines.append("کارت‌های تازه خودکار به topicِ سیستم پوش می‌شوند.")
        return "\n".join(lines)

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

    def _handle_callback(self, cbq: dict) -> dict:
        """callback data = '<verb>:<id>' با verb ∈ ok/no/later (قراردادِ render_decision)
        یا verbهای مرکزِ فرماندهی (mn/lg/pw/pwc → _handle_center_callback).
        ثبت به الگوی approval-file + رویداد + answer_callback؛ ok = mintِ اختیاریِ
        توکنِ HumanAppendGuard (فقط با رازِ env)."""
        data = str(cbq.get("data") or "")
        if data.split(":", 1)[0] in ("mn", "lg", "pw", "pwc"):
            return self._handle_center_callback(cbq, data)
        parts = data.split(":", 1)
        if len(parts) != 2 or parts[0] not in _VERDICTS:
            self._answer(cbq, "نادیده")
            return {"kind": "callback", "verdict": None}
        verb, did = parts[0], _sanitize_id(parts[1])
        rec = {"id": did, "verdict": verb, "ts": opslib.now_iso(), "source": "tg-center"}
        if verb == "ok":
            tok = _mint_ha_token(did)                # بی‌راز → None → ثبتِ بدونِ توکن
            if tok:
                rec["ha_token"] = tok
        recorded = self._record_approval(rec)
        _emit_event("task.completed",
                    summary=f"verdict {verb} ثبت شد",      # content-free (فقط کلید/فعل)
                    approval_state=_VERDICT_APPROVAL_STATE.get(verb, "unknown"),
                    trace_id=did, status="ok" if recorded else "warn")
        self._answer(cbq, _VERDICT_TOAST.get(verb, ""))
        return {"kind": "callback", "verdict": verb, "id": did, "recorded": recorded}

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
