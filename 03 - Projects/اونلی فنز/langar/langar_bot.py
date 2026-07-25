#!/usr/bin/env python3
"""langar_bot.py — ⚓ لنگر: کاکپیت تلگرامیِ خودآگاه آری برای Project-F.

اصول (LANGAR-SPEC): propose-only · فقط chat-id آری · صفر رسانه/PII ·
OpsecGuard روی هر خروجی · نوشتن فقط داخل langar/ · kill-switch فایل‌محور ·
سقف هزینه fail-closed · λ_persist<0 (هیچ بهینه‌سازی برای بقای خود).
stdlib-only؛ مغز (DualBrainV3) و LLM اختیاری‌اند و نبودشان چیزی را نمی‌شکند.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../langar
PROJECT_ROOT = HERE.parent                       # پوشهٔ Project-F
PROPOSALS_DIR = HERE / "upgrade_proposals"
LOG_FILE = HERE / "langar_log.jsonl"
KILL_FILE = HERE / "KILL"


def _global_stop() -> bool:
    """کلیدِ خاموشیِ سراسریِ اختاپوس (_ops/STOP-ORGANISM یا master_halted). walk-up تا _ops
    بدونِ import کردنِ _ops (احترام به containment). خطا/نبود = False."""
    try:
        for _anc in Path(__file__).resolve().parents:
            _ops = _anc / "_ops"
            if _ops.is_dir():
                return (_ops / "STOP-ORGANISM").exists() or (_ops / "master_halted").exists()
    except Exception:  # noqa: BLE001
        pass
    return False
COST_FILE = HERE / "cost_meter.json"
CONFIG_FILE = HERE / "langar_config.json"
TELEGRAM_API = "https://api.telegram.org"

# مغز اختیاری (brain/ داخل پوشه) — نبودش fail-open به heuristics نیست؛ فقط لایهٔ ۰ ساده‌تر می‌شود
sys.path.insert(0, str(PROJECT_ROOT / "brain"))
try:
    from dual_brain_v3 import DualBrainV3  # type: ignore
except Exception:
    DualBrainV3 = None  # noqa: N816

# رجیستریِ قابلیت (اختیاری — fail-soft به help/dispatch استاتیک)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
try:
    from capability_registry import CapabilityRegistry  # type: ignore
except Exception:
    CapabilityRegistry = None  # noqa: N816

# دستورهایی که هرگز گیت/‏revoke نمی‌شوند (fail-safe: کاکپیت هیچ‌وقت کور یا قفل نشود)
UNGATED = ("/start", "/help", "/status", "/kill", "/revive")

LOCKED_RULES = [
    "1) فقط پا — بدون صورت/بدن/explicit",
    "2) geo-block کامل ایران در همهٔ لایه‌ها",
    "3) پرداخت فقط داخل پلتفرم — هرگز P2P/خارجی",
    "4) بدون هیچ نقض ToS هیچ پلتفرمی",
    "5) privacy دوطرفه (creator + buyer)",
    "6) بدون geo-fact حد شهر؛ سیگنال فرهنگی فقط بصری",
    "7) کد Project-F بیرون از پوشه؛ صفر echo هویت/محتوا",
    "8) 18+ و رضایت ثبت‌شده؛ محدودهٔ C حاکم بر همهٔ پلن‌ها",
]
GATES = {
    "G0": "Branch A تأیید + توافق امضا + پاسخ سؤال آخر",
    "G1": "هفتهٔ ۶: ≥200 کلیک · ≥10% click→follow · delivery ≥80%",
    "G2": "هفتهٔ ۱۲: ≥30 free-sub · ≥5% free→paid · اولین AUD 100",
    "G3": "AUD 2k/ماه ×3 + churn<30% → ABN/مشاور",
    "G4": "۱۲ ماه سودده + ابزار داخلی → Tools",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _read_text(path: Path, max_chars: int = 40000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


class OpsecGuard:
    """Egress gate for every outbound Telegram message. FAIL-CLOSED (deny-by-default):
    an empty/unloadable blocklist, an unloaded policy, or ANY scrub error BLOCKS the
    send. A send proceeds only when an explicit, non-empty scrub policy is present.
    Real identifiers are NEVER hardcoded here — the operator supplies them via
    langar_config.json (blocklist + name_map)."""

    DEFAULT = {
        "blocklist": [],                      # real identifiers — operator fills langar_config.json
        "city_terms": ["Sydney", "سیدنی", "sydney"],
        "name_map": {},                       # real first-names live in config only, never in source
        "project_code": "Project-F",
    }

    def __init__(self, config: dict | None = None):
        cfg = dict(self.DEFAULT)
        loaded_ok = False
        if config is not None:
            try:
                cfg.update(config)
                loaded_ok = True
            except Exception:
                loaded_ok = False
        else:
            loaded = _load_json(CONFIG_FILE, None)
            if isinstance(loaded, dict):
                cfg.update(loaded)
                loaded_ok = True
        self.cfg = cfg
        self.policy_loaded = loaded_ok       # False = config missing/corrupt → fail-closed

    def policy_ok(self) -> bool:
        """True only when an explicit, non-empty blocklist policy is loaded.
        Empty/unloadable policy ⇒ False ⇒ egress denied."""
        if not self.policy_loaded:
            return False
        bl = self.cfg.get("blocklist") or []
        if not isinstance(bl, (list, tuple)):
            return False
        return any(isinstance(t, str) and t.strip().strip("_") for t in bl)

    def clean(self, text: str) -> str:
        out = text or ""
        for name, code in self.cfg.get("name_map", {}).items():
            out = out.replace(name, code)
        for term in self.cfg.get("city_terms", []):
            out = re.sub(re.escape(term), "⟦geo⟧", out, flags=re.IGNORECASE)
        for term in self.cfg.get("blocklist", []):
            if term and term.strip("_"):
                out = re.sub(re.escape(term), "⟦x⟧", out, flags=re.IGNORECASE)
        out = re.sub(r"[A-Z]:\\\\?[^\s]*", "⟦path⟧", out)      # مسیر ویندوزی
        out = re.sub(r"/sessions/[^\s]*", "⟦path⟧", out)        # مسیر sandbox
        return out

    def scrub(self, text: str) -> tuple[bool, str]:
        """FAIL-CLOSED egress decision. Returns (allowed, cleaned_text).
        (False, "") when no explicit non-empty policy is loaded or on ANY scrub error."""
        try:
            if not self.policy_ok():
                return False, ""
            return True, self.clean(text)
        except Exception:
            return False, ""


class CostMeter:
    """سقف ماهانهٔ خرج LLM (AUD). fail-closed: خطا در فایل = مصرف ممنوع."""

    def __init__(self, cap_aud: float | None = None, path: Path = COST_FILE):
        self.cap = float(cap_aud if cap_aud is not None
                         else os.environ.get("LANGAR_MONTHLY_CAP_AUD", 15))
        self.path = path

    def _state(self) -> dict:
        """اگر فایل هست ولی خراب است → raise (fail-closed در can_spend)."""
        month = date.today().strftime("%Y-%m")
        if self.path.exists():
            st = json.loads(self.path.read_text(encoding="utf-8"))  # ممکن است raise کند
        else:
            st = {}
        if st.get("month") != month:
            st = {"month": month, "spent_aud": 0.0}
        return st

    def can_spend(self, est_aud: float) -> bool:
        try:
            st = self._state()
            return (st["spent_aud"] + est_aud) <= self.cap
        except Exception:
            return False  # fail-closed: state نامعتبر = مصرف ممنوع

    def add(self, aud: float) -> None:
        try:
            st = self._state()
        except Exception:
            # state خراب → قفل در سقف (fail-closed)، نه ریست به صفر
            st = {"month": date.today().strftime("%Y-%m"), "spent_aud": self.cap}
        st["spent_aud"] = round(st.get("spent_aud", 0.0) + aud, 4)
        self.path.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")

    @property
    def spent(self) -> float:
        try:
            return self._state().get("spent_aud", 0.0)
        except Exception:
            return self.cap  # نمایش fail-closed


class SelfModel:
    """مدلِ زندهٔ «خودم + پروژه». هیچ حدسی — فقط خواندنِ فایل‌های state."""

    def __init__(self, root: Path = PROJECT_ROOT, src: Path | None = None):
        self.root = root
        self.src = src or Path(__file__).resolve()

    # ── پروژه ──
    def outward_locked(self) -> bool:
        """قفل تا وقتی «پیامد: Branch A» در PROJECT.md ثبت نشده.

        fail-open رفع شد — تنها یافتهٔ CONFIRMED راستی‌آزماییِ متخاصمِ ۲۰۲۶-۰۷-۲۵.
        الگوی قبلی `پیامد:\\s*Branch\\s*A\\b` روی **قالبِ پرنشدهٔ** «پیامد: Branch A/B»
        هم match می‌کرد، چون `\\b` مرزِ بینِ `A` و `/` را می‌گیرد. نتیجه: تابع
        False (=آزاد) برمی‌گرداند در حالی که همان خطِ PROJECT.md جای‌نگهدارِ `___`
        دارد و سندش می‌گوید گیت باز است. یعنی `/gates` روی باتِ زنده گیتِ **باز** را
        «بسته» گزارش می‌کرد — دروغ در کنترل‌سرفیس، روی گیتی که کلِ اکشن‌های
        Hard-Gated به آن بسته‌اند.

        حالا پیش‌فرض **قفل** است و بازشدن دو شرطِ هم‌زمان می‌خواهد:
          ۱) `Branch A` که پشتش `/` نیاید (لُکاهدِ منفی) = انتخابِ واقعی، نه قالب
          ۲) همان خط `___` نداشته باشد — خطِ پرنشده = گیتِ باز (قاعدهٔ خودِ سند)
        سخت‌ترکردنِ یک گیت هرگز جهتِ خطرناک نیست: این تغییر فقط می‌تواند بیشتر
        قفل کند، نه کمتر.
        """
        txt = _read_text(self.root / "PROJECT.md")
        for line in txt.splitlines():
            if not re.search(r"پیامد:\s*Branch\s*A\b(?!\s*/)", line):
                continue
            if "___" in line:          # قالب هنوز پر نشده → گیت باز
                continue
            return False               # ثبتِ واقعیِ Branch A → قفل باز
        return True                    # fail-closed

    def open_questions(self) -> int:
        txt = _read_text(self.root / "OpenQuestions.md")
        return len(re.findall(r"^\d+\.\s", txt, flags=re.M))

    def last_decisions(self, n: int = 3) -> list[str]:
        txt = _read_text(self.root / "DecisionLog.md")
        rows = re.findall(r"^\*\*(2026[^*]{4,90})", txt, flags=re.M)
        return rows[:n]

    def pending_verdicts(self) -> list[str]:
        txt = _read_text(self.root / "THREAD-CLOSURE-D-2026-07-10.md")
        m = re.search(r"§۹[^\n]*\n(.+?)(\n## |\Z)", txt, flags=re.S)
        if not m:
            return ["THREAD-CLOSURE پیدا نشد — DecisionLog را دستی چک کن"]
        items = re.findall(r"^\d+\.\s\**([^\n]+)", m.group(1), flags=re.M)
        return [re.sub(r"\[\[|\]\]|\*", "", i).strip() for i in items]

    # ── پل به استودیوی Creator (handoff دوطرفه، فقط‌خواندنی) ──
    def studio_bridge(self) -> dict:
        """می‌خواند از studio/: درفت‌های pending، اعلان‌های Creator، وضعیت halt.
        صفر PII — فقط شمارش/متادیتا و متن اعلانِ خودِ Creator.
        (C1 rename 2026-07-20: نام جدید to_operator.json؛ نام قدیمی to_ari.json fallback.)"""
        studio = self.root / "studio"
        drafts = _load_json(studio / "drafts.json", [])
        pend = [d for d in drafts if isinstance(d, dict) and d.get("status") == "pending"]
        notes = _load_json(studio / "to_operator.json", None)
        if not isinstance(notes, list):
            notes = _load_json(studio / "to_ari.json", [])
        return {
            "pending_drafts": len(pend),
            "pending_titles": [str(d.get("title", ""))[:40] for d in pend[-5:]],
            "saba_halted": (studio / "HALT").exists(),
            "notes": [str(n.get("text", ""))[:120] for n in notes[-5:]] if isinstance(notes, list) else [],
            "capacity": _load_json(studio / "capacity.json", {}).get("hours"),
        }

    # سازگاری عقب‌رو — نام قدیمی متد
    saba_bridge = studio_bridge

    # ── خودم ──
    def self_state(self, cost: CostMeter) -> dict:
        src_bytes = self.src.read_bytes() if self.src.exists() else b""
        return {
            "src_sha256": hashlib.sha256(src_bytes).hexdigest()[:12],
            "src_lines": src_bytes.decode("utf-8", "ignore").count("\n") + 1,
            "killed": KILL_FILE.exists(),
            "brain_loaded": DualBrainV3 is not None,
            "llm_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "cost_spent_aud": cost.spent,
            "cost_cap_aud": cost.cap,
            "proposals_on_disk": len(list(PROPOSALS_DIR.glob("*.md"))) if PROPOSALS_DIR.exists() else 0,
        }


class UpgradeEngine:
    """مسئول ارتقا — propose-only، دوکلیده: فقط فایل proposal می‌نویسد؛
    اعمال هر تغییر = دستِ A. هرگز سورس خودش را دست نمی‌زند."""

    def __init__(self, model: SelfModel, cost: CostMeter):
        self.model, self.cost = model, cost

    def _candidates(self) -> list[str]:
        s = self.model.self_state(self.cost)
        out: list[str] = []
        cfg = _load_json(CONFIG_FILE, {})
        if not cfg.get("blocklist"):
            out.append("پرکردن blocklist واقعی OpsecGuard در langar_config.json "
                       "(الان خالی است → scrubber fail-closed: هر send بلاک می‌شود تا سیاست پر شود) "
                       "— اثر: بالا (کانال خروجی بسته)، هزینه: ۵ دقیقه.")
        if not s["llm_key"]:
            out.append("فعال‌کردن لایهٔ LLM (Haiku) زیر CostMeter برای /brief و /think "
                       "— نیازمند ANTHROPIC_API_KEY و verdict V3؛ تا آن‌موقع heuristics کافی است.")
        if not s["brain_loaded"]:
            out.append("رفع import مغز (brain/dual_brain_v3.py) تا /brief از ThinkingBrain واقعی تغذیه شود.")
        if self.model.outward_locked():
            out.append("یادآوری ساختاری: GATE 0 هنوز باز است — ارتقای بعدیِ واقعی، بستنِ همین است "
                       "(پیام آماده: THREAD-CLOSURE §۱).")
        kpi = self.model.root / "drafts-awaiting-gate" / "kpi-dashboard-spec.md"
        if kpi.exists() and not (self.model.root / "Fable5").exists():
            out.append("ساخت Fable5 حداقلی + شیت داشبورد طبق kpi-dashboard-spec (گام ۷ پلن M3).")
        out.append("افزودن تست جدید برای هر باگ runtime ثبت‌شده در langar_log.jsonl هفتهٔ گذشته (اگر بود).")
        return out[:3]

    def propose(self) -> tuple[Path, list[str]]:
        PROPOSALS_DIR.mkdir(exist_ok=True)
        items = self._candidates()
        path = PROPOSALS_DIR / f"{date.today().isoformat()}.md"
        body = [f"# Upgrade proposals — {date.today().isoformat()} (propose-only، اعمال با A)"]
        body += [f"{i+1}. {t}" for i, t in enumerate(items)]
        body.append("\n> قاعده: هیچ auto-apply؛ λ_persist<0؛ هر اعمال = دستی + ثبت DecisionLog.")
        path.write_text("\n".join(body), encoding="utf-8")
        return path, items


class LangarBot:
    """⚓ حلقهٔ تلگرام — فقط A. الگوی long-poll از studio_telegram_v3."""

    def __init__(self, token: str | None = None, ari_chat_id: int | None = None,
                 http_get=None, http_post=None, root: Path = PROJECT_ROOT):
        self.token = token or os.environ.get("TELEGRAM_LANGAR_BOT_TOKEN", "").strip()
        cid = ari_chat_id if ari_chat_id is not None else os.environ.get("TELEGRAM_ARI_CHAT_ID", "0")
        self.ari = int(cid) if str(cid).strip() else 0
        self.guard = OpsecGuard()
        self.cost = CostMeter()
        self.model = SelfModel(root)
        self.upgrader = UpgradeEngine(self.model, self.cost)
        self.brain = DualBrainV3() if DualBrainV3 else None
        self._http_get = http_get or self._default_get
        self._http_post = http_post or self._default_post
        self._offset = 0
        self._stop = False
        self._last_weekly: str | None = None
        self.registry = CapabilityRegistry() if CapabilityRegistry else None

    # ── capability advertisement (dynamic — هر فراخوانی تازه محاسبه می‌شود) ──
    def _advertise(self):
        """هر دستور = یک capability با وضعیت صادقانه. برگشتی: registry یا None."""
        if not self.registry:
            return None
        caps = [
            ("/status", "وضعیت زندهٔ پروژه/خودم", "live", "", 10),
            ("/gates", "GATEها + وضعیت قفل", "live", "", 20),
            ("/verdicts", "صف verdictهای منتظر", "live", "", 30),
            ("/studio", "پل read-only استودیوی Creator (alias: /saba)", "live", "", 40),
            ("/brief", "بریف (brain یا heuristic برچسب‌دار)", "live", "", 50),
            ("/think", "تحلیل موضوع (heuristic/LLM زیر سقف)", "live", "", 60),
            ("/upgrade", "پیشنهاد ارتقا (propose-only)", "live", "", 70),
            ("/rules", "قواعد قفل‌شده", "live", "", 80),
            ("/pf", "اکتساب /pf_* (propose-only)", "live", "", 90),
            ("/dm", "DM HITL /dm_* (AI draft، آری approve، ارسال دستی)", "live", "", 92),
            ("/fan", "Fan CRM /fan_* (segments، LTV، tags)", "live", "", 93),
            ("/vault", "Vault /vault_* (بانک محتوا)", "live", "", 94),
            ("/guards", "snapshot safety nets (warm-up + channel locks)", "live", "", 95),
            ("/report_warning", "ثبتِ warning پلتفرمی → lock کانال", "live", "", 96),
            ("/report_karma", "ثبتِ کارمای Reddit → warm-up guard", "live", "", 97),
            ("/kpi", "داشبورد KPI واقعی (از rollup)", "live", "", 98),
            ("/octopus", "bridge به orchestrator (heartbeat/tick)", "live", "", 99),
            ("/dm_inbox", "incoming DM → FAQ auto-draft (HITL)", "live", "", 100),
            ("/spine", "وضعیت ستون‌فقرات اجرا (bus/telemetry/actuator، read-only)", "live", "", 101),
            ("/kill", "توقف اضطراری", "live", "", 200),
            ("/revive", "بازگشت از KILL", "live", "", 210),
        ]
        for cid, label, st, rs, o in caps:
            self.registry.advertise(cid, "langar", label, kind="command",
                                    status=st, reason=rs, order=o)
        return self.registry

    def _help_text(self) -> str:
        """help از رجیستری: live عادی، disabled با 🔒+دلیل، revoked غایب."""
        reg = self._advertise()
        if not reg:
            return ("⚓ لنگر — کاکپیت Project-F (propose-only)\n"
                    "/status /gates /verdicts /studio /brief /think <موضوع>\n"
                    "/upgrade /rules /kill /revive\n"
                    "اکتساب: /pf_status /pf_plan [n] /pf_queue /pf_ok <id> /pf_no <id> /pf_ready <id> /pf_dryrun <id>\n"
                    "DM HITL: /dm_status /dm_queue /dm_ok <id> /dm_no <id> /dm_sent <id> /dm_inbox <text>\n"
                    "Fan CRM: /fan_add <alias> /fan_list /fan_buy <alias> <usd> /fan_stats\n"
                    "Vault: /vault_add <tag> <hook> /vault_list /vault_metric <id> <up>\n"
                    "safety: /guards /report_warning <ch> /clear_warning <ch> /report_karma <n>\n"
                    "KPI: /kpi /kpi_record <usd> <ppv> [posts] [rate] /kpi_import <csv|L-code clicks>\n"
                    "Octopus: /octopus /octopus_tick")
        rows = reg.surface("langar")
        live = [r["id"] for r in rows if r["status"] == "live" and r["id"] != "/pf"]
        locked = [f"🔒 {r['id']} — {r['reason']}" for r in rows if r["status"] == "disabled"]
        out = ["⚓ لنگر — کاکپیت Project-F (propose-only)", " ".join(live)]
        if any(r["id"] == "/pf" and r["status"] == "live" for r in rows):
            out.append("اکتساب: /pf_status /pf_plan [n] /pf_queue /pf_ok <id> /pf_no <id> /pf_ready <id>")
        out += locked
        return "\n".join(out)

    def _cap_gate(self, cmd: str) -> str | None:
        """None=مجاز؛ متن=پیام بلاکِ صادقانه. UNGATED هرگز گیت نمی‌شود (fail-safe)."""
        if cmd in UNGATED:
            return None
        reg = self._advertise()
        if not reg:
            return None
        # زیردستورها به capability والد (<code> نگاشت می‌شوند
        if cmd.startswith("/pf_"):
            cap_id = "/pf"
        elif cmd in ("/saba", "/drafts", "/studio"):
            cap_id = "/studio"
        elif cmd.startswith("/dm_"):
            cap_id = "/dm"
        elif cmd.startswith("/fan_"):
            cap_id = "/fan"
        elif cmd.startswith("/vault_"):
            cap_id = "/vault"
        elif cmd.startswith("/octopus"):
            cap_id = "/octopus"
        elif cmd in ("/dm_inbox", "/inbox"):
            cap_id = "/dm_inbox"
        elif cmd in ("/kpi_record", "/kpi_import"):
            cap_id = "/kpi"
        else:
            cap_id = cmd
        eff = reg.effective(cap_id)
        if eff["status"] == "live" or cap_id not in [r["id"] for r in reg.surface("langar")]:
            return None   # ناشناخته‌ها به مسیر «دستور ناشناخته» می‌روند، نه بلاکِ گمراه‌کننده
        if eff["status"] == "revoked":
            return f"⛔ {cmd} برداشته شده — {eff.get('reason') or 'توسط اپراتور'}"
        return f"🔒 {cmd} خاموش است — {eff.get('reason') or 'به قابلیت واقعی وصل نیست'}"

    # ── HTTP ──
    @staticmethod
    def _default_get(url: str, timeout: int = 35):
        req = urllib.request.Request(url, headers={"User-Agent": "octopus-langar"})
        with urllib.request.urlopen(req, timeout=timeout + 5) as r:
            return json.loads(r.read().decode())

    @staticmethod
    def _default_post(url: str, body: dict, timeout: int = 10):
        data = json.dumps(body, ensure_ascii=False).encode()
        req = urllib.request.Request(url, data=data, headers={
            "User-Agent": "octopus-langar", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    # ── هسته ──
    def _log(self, kind: str, payload: dict) -> None:
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"t": _now(), "kind": kind, **payload},
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass

    def authorized(self, chat_id: int) -> bool:
        return bool(self.ari) and chat_id == self.ari

    def send(self, text: str) -> None:
        """تنها کانال خروجی. متن → OpsecGuard.scrub (FAIL-CLOSED) → تلگرام.
        سیاست scrub غایب/خالی/خراب = بلاک کامل (deny-by-default). صفر متد رسانه‌ای."""
        allowed, safe = self.guard.scrub(text)
        if not allowed:
            # fail-closed: no active scrub policy → block egress, log via alert path.
            self._log("send_blocked", {"reason": "opsec_fail_closed", "chars": len(text or "")})
            if not (self.token and self.ari):
                print("⛔ [opsec fail-closed] پیام بلاک شد — سیاست scrub فعال نیست "
                      "(blocklist خالی/بارنشده). langar_config.json را پر کن تا کانال باز شود.")
            return
        safe = safe[:4000]
        if not (self.token and self.ari):
            print(safe)  # shadow-mode بدون توکن
            return
        try:
            self._http_post(f"{TELEGRAM_API}/bot{self.token}/sendMessage",
                            {"chat_id": self.ari, "text": safe})
        except Exception as e:  # pragma: no cover
            self._log("send_error", {"err": str(e)[:200]})

    # ── دستورها ──
    def handle(self, chat_id: int, text: str) -> str | None:
        """برمی‌گرداند پاسخ (قبل از guard) یا None برای سکوت."""
        if not self.authorized(chat_id):
            self._log("unauthorized", {"chat": chat_id})
            return None  # سکوت مطلق برای غریبه
        cmd, _, arg = (text or "").strip().partition(" ")
        cmd = cmd.lower()
        if _global_stop() and cmd != "/status":
            return "🔴 STOP سراسریِ اختاپوس فعال است — لنگر فقط /status می‌دهد (برداشتنِ STOP کارِ مالک است)."
        if KILL_FILE.exists() and cmd not in ("/revive", "/status"):
            return "⚓ لنگر در حالت KILL است. فقط /status و /revive."
        if cmd in ("/start", "/help"):
            # UI-truth: help از رجیستری — فقط دستورهای واقعی؛ disabled با 🔒 + دلیل.
            return self._help_text()
        blocked = self._cap_gate(cmd)
        if blocked:
            return blocked
        if cmd.startswith("/pf_"):
            # خطِ لولهٔ اکتساب (propose-only، هیچ اکشنِ بیرونی) — آداپتورِ ایزوله
            try:
                import pf_admin
            except ImportError:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import pf_admin
            return pf_admin.handle_pf(cmd, arg)
        # /dm_inbox و /inbox باید قبل از generic /dm_ چک شوند (prefix collision)
        if cmd in ("/dm_inbox", "/inbox"):
            if not arg:
                return "❌ /dm_inbox <incoming message text>\nمثال: /dm_inbox \"hi how much for custom?\""
            return self._dm_inbox(arg)
        if cmd.startswith("/dm_"):
            # صفِ DMِ HITL (safety net #1: AI draft، آری approve، ارسال دستی)
            try:
                import dm_admin
            except ImportError:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import dm_admin
            return dm_admin.handle_dm(cmd, arg)
        if cmd.startswith("/fan_"):
            # Fan CRM (لایهٔ ۲): مدیریتِ هواداران
            try:
                import fan_admin
            except ImportError:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import fan_admin
            return fan_admin.handle_fan(cmd, arg)
        if cmd.startswith("/vault_"):
            # Vault (لایهٔ ۲): بانکِ محتوا
            try:
                import vault_admin
            except ImportError:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import vault_admin
            return vault_admin.handle_vault(cmd, arg)
        if cmd == "/rules":
            return "قواعد قفل‌شده:\n" + "\n".join(LOCKED_RULES)
        if cmd == "/gates":
            lock = "🔒 باز (بلاکر)" if self.model.outward_locked() else "✅ ثبت‌شده"
            rows = [f"{g}: {desc}" for g, desc in GATES.items()]
            return f"GATE 0: {lock}\n" + "\n".join(rows)
        if cmd == "/status":
            s = self.model.self_state(self.cost)
            b = self.model.studio_bridge()
            lock = "قفل (GATE 0 باز)" if self.model.outward_locked() else "Branch A ثبت"
            saba = ("✋ توقف" if b["saba_halted"] else f"{b['pending_drafts']} درفت منتظر")
            return (f"⚓ وضعیت {_now()}\n"
                    f"پروژه: outward={lock} · سؤال باز={self.model.open_questions()}\n"
                    f"استودیو: {saba}" + (f" · {len(b['notes'])} پیام" if b['notes'] else "") + "\n"
                    f"آخرین تصمیم‌ها: " + " | ".join(self.model.last_decisions(2)) + "\n"
                    f"خودم: src={s['src_sha256']} ({s['src_lines']}L) · brain={'✓' if s['brain_loaded'] else '—'}"
                    f" · LLM={'✓' if s['llm_key'] else 'off'} · kill={'ON' if s['killed'] else 'off'}\n"
                    f"هزینهٔ ماه: {s['cost_spent_aud']:.2f}/{s['cost_cap_aud']:.0f} AUD"
                    f" · proposals={s['proposals_on_disk']}")
        if cmd == "/verdicts":
            items = self.model.pending_verdicts()
            return "منتظر verdict تو:\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(items))
        if cmd in ("/studio", "/saba", "/drafts"):
            b = self.model.studio_bridge()
            head = "✋ استودیو الان روی توقف است.\n" if b["saba_halted"] else ""
            lines = [f"{head}🎬 استودیوی Creator:",
                     f"درفت‌های منتظر تأیید: {b['pending_drafts']}"]
            for t in b["pending_titles"]:
                lines.append(f"  ⏳ {t}")
            if b.get("capacity") is not None:
                lines.append(f"ظرفیت اعلامی Creator: {b['capacity']} ساعت")
            if b["notes"]:
                lines.append("پیام‌های Creator:")
                lines += [f"  • {n}" for n in b["notes"]]
            lines.append("\n(تأیید هر درفت = دستی و درون‌پلتفرم؛ این‌جا فقط مشاهده.)")
            return "\n".join(lines)
        if cmd == "/brief":
            return self._brief()
        if cmd == "/think":
            return self._think(arg or "وضعیت کلی")
        if cmd == "/kpi":
            # لایهٔ ۲ (2026-07-16): KPI واقعی از KPIRollup — دیگر disabled نیست.
            # اگه داده نیست، صفر صادقانه نشان می‌دهد (نه fabricated template).
            return self._kpi_card()
        if cmd == "/kpi_record":
            # /kpi_record <revenue_usd> <ppv_unlocks> [posts] [delivery_rate]
            # آری هر جمعه از داشبورد عدد می‌زند.
            return self._kpi_record(arg)
        if cmd == "/kpi_import":
            # 2026-07-20 (backlog #4): import دستی CSV — صفر شبکه، صفر API پلتفرم.
            return self._kpi_import(arg)
        if cmd == "/report":
            # لایهٔ ۲: report از همون KPI واقعی — دیگر disabled نیست.
            return self._kpi_card()
        if cmd == "/spine":
            return self._spine_card()
        if cmd == "/upgrade":
            path, items = self.upgrader.propose()
            self._log("upgrade", {"file": path.name, "n": len(items)})
            return ("پیشنهادهای ارتقا (اعمال = دست تو):\n" +
                    "\n".join(f"{i+1}. {t}" for i, t in enumerate(items)) +
                    f"\n📄 ثبت شد: langar/upgrade_proposals/{path.name}")
        # ── safety-net commands (2026-07-16 launch guard) ──
        if cmd == "/report_warning":
            # /report_warning <channel> [reason...] — ثبتِ warning پلتفرمی → lock کانال
            parts = arg.split(maxsplit=1)
            if not parts:
                return "❌ /report_warning <channel> [reason]"
            try:
                sys.path.insert(0, str(PROJECT_ROOT / "brain"))
                from guards import ChannelLocks
                locks = ChannelLocks()
                ch = parts[0]
                reason = parts[1] if len(parts) > 1 else "platform warning"
                r = locks.report_warning(ch, reason)
                self._log("platform_warning", r)
                head = (f"⛔ FULL STOP فعال — {r.get('warning_count')} warning روی {ch}. "
                        f"verdict لازم: /clear_full_stop" if r.get("full_stop")
                        else f"🔒 {ch} lock شد ({r.get('warning_count')} warning). "
                             f"/clear_warning {ch} برای بازگشت.")
                return head
            except Exception as e:  # noqa: BLE001
                return f"❌ guards error: {type(e).__name__}"
        if cmd == "/clear_warning":
            if not arg:
                return "❌ /clear_warning <channel>"
            try:
                sys.path.insert(0, str(PROJECT_ROOT / "brain"))
                from guards import ChannelLocks
                r = ChannelLocks().clear_warning(arg.strip())
                return f"✅ {arg} باز شد" if r.get("ok") else f"❌ {r.get('error')}"
            except Exception as e:  # noqa: BLE001
                return f"❌ guards error: {type(e).__name__}"
        if cmd == "/clear_full_stop":
            try:
                sys.path.insert(0, str(PROJECT_ROOT / "brain"))
                from guards import ChannelLocks
                ChannelLocks().clear_full_stop()
                self._log("clear_full_stop", {"by": "operator"})
                return "✅ full_stop پاک شد. همهٔ کانال‌ها باز. قیف از سر گرفته شد."
            except Exception as e:  # noqa: BLE001
                return f"❌ guards error: {type(e).__name__}"
        if cmd in ("/report_karma", "/set_karma"):
            # /report_karma <n> — ثبتِ کارمای دستی Reddit (هر جمعه از داشبورد)
            if not arg.strip().isdigit():
                return "❌ /report_karma <number> — عدد کارما از داشبارد Reddit"
            try:
                sys.path.insert(0, str(PROJECT_ROOT / "brain"))
                from guards import WarmupGuard
                wg = WarmupGuard()
                r = wg.set_karma(int(arg.strip()), note="manual via langar")
                self._log("karma_update", r)
                flag = "✅ آستانه محقق — فروش باز شد" if r.get("threshold_met") \
                    else f"🔒 هنوز {wg.threshold() - r.get('karma', 0)} کارما لازم"
                return f" karma ثبت شد: {r['karma']}/{wg.threshold()} · {flag}"
            except Exception as e:  # noqa: BLE001
                return f"❌ guards error: {type(e).__name__}"
        if cmd == "/guards":
            # /guards — snapshot کاملِ safety nets (read-only)
            try:
                sys.path.insert(0, str(PROJECT_ROOT / "brain"))
                from guards import WarmupGuard, ChannelLocks
                wg = WarmupGuard()
                cl = ChannelLocks()
                w = {"karma": wg.get_karma(), "threshold": wg.threshold(),
                     "met": wg.threshold_met()}
                lk = cl.snapshot()
                line = f"🛡 safety nets:\n"
                flag = "✅" if w["met"] else "🔒"
                line += f"{flag} warm-up: {w['karma']}/{w['threshold']}\n"
                if lk.get("full_stop"):
                    line += f"⛔ FULL STOP: {lk.get('full_stop_reason','')}\n"
                for ch, c in lk.get("channels", {}).items():
                    s = "🔒" if c.get("locked") else "✅"
                    line += f"{s} {ch}: {c.get('warnings',0)} warning\n"
                return line or "🛡 safety nets: همه سبز"
            except Exception as e:  # noqa: BLE001
                return f"❌ guards error: {type(e).__name__}"
        # ── لایهٔ ۲: Octopus bridge + DM inbox (FAQ auto-draft) ──
        if cmd in ("/octopus", "/octopus_status"):
            return self._octopus_card()
        if cmd == "/octopus_tick":
            return self._octopus_tick()
        if cmd == "/kill":
            KILL_FILE.write_text(_now(), encoding="utf-8")
            self._log("kill", {})
            return "⚓ KILL فعال شد. همه‌چیز متوقف؛ /revive برای بازگشت."
        if cmd == "/revive":
            KILL_FILE.unlink(missing_ok=True)
            self._log("revive", {})
            return "لنگر برگشت. /status بزن."
        return "دستور ناشناخته. /help"

    # ── ستون‌فقرات اجرا (read-only truth card) ──
    def _spine_card(self) -> str:
        """وضعیت صادقانهٔ bus/telemetry/actuator/registry — فقط خواندن، صفر اکشن."""
        try:
            from event_bus import EventBus
            from telemetry import Telemetry
            from actuator import Actuator
        except Exception:
            return ("🦴 ستون‌فقرات نصب نیست (event_bus/telemetry/actuator import نشد) — "
                    "این یعنی هنوز فقط file-handoff قدیمی داریم.")
        bus_snap = EventBus().snapshot()
        tel_sum = Telemetry().summary()
        act_snap = Actuator().snapshot()
        reg = self._advertise()
        reg_line = ""
        if reg:
            s = reg.snapshot()
            reg_line = (f"رجیستری: {s['advertised']} قابلیت — live {s['live']} · "
                        f"🔒 {s['disabled']} · ⛔ {s['revoked']}\n")
        topics = bus_snap.get("topics", {})
        topics_line = (" · ".join(f"{t}:{n}" for t, n in sorted(topics.items()))
                       if topics else "خالی (هنوز رویدادی publish نشده)")
        return ("🦴 ستون‌فقرات اجرا (read-only)\n"
                + reg_line +
                f"bus: {topics_line}\n"
                f"telemetry: {tel_sum.get('jobs', 0)} job"
                + (f" · error-rate {tel_sum['error_rate']}" if tel_sum.get("jobs") else "") + "\n"
                f"actuator: mode={act_snap['mode']} · adapters={act_snap['adapters_count']} · "
                f"live={'ممکن' if act_snap['live_possible'] else 'غیرممکن (صفر adapter — fail-closed)'}")

    # ── لایهٔ ۲: KPI / Octopus / DM inbox ──────────────────────────────────
    def _kpi_card(self) -> str:
        """KPI واقعی از KPIRollup. اگه داده نیست، صفر صادقانه نشان می‌دهد."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "brain"))
            from store import KPIRollup, FanDB
            k = KPIRollup()
            cur = k.current_week()
            trend = k.trend(4)
            fans = FanDB().summary()
            if not cur:
                return ("📊 KPI (هنوز داده ثبت نشده — /kpi_record برای ثبت)\n"
                        f"fans: {fans['total']} · LTV کل: ${fans['total_ltv_usd']:.2f}\n"
                        "هفتهٔ جاری: صفر داده. /kpi_record <usd> <ppv> [posts] هر جمعه.")
            seg = " · ".join(f"{k}:{v}" for k, v in sorted(fans["segments"].items())) or "خالی"
            rev_trend = " → ".join(f"${w.get('revenue_usd', 0):.0f}" for w in trend) or "—"
            return (f"📊 KPI هفتهٔ جاری\n"
                    f"revenue: ${cur.get('revenue_usd', 0):.2f} · PPV unlocks: {cur.get('ppv_unlocks', 0)}\n"
                    f"posts: {cur.get('posts', 0)} · delivery: {cur.get('delivery_rate', 0)*100:.0f}%\n"
                    f"fans: {fans['total']} ({seg}) · LTV کل: ${fans['total_ltv_usd']:.2f}\n"
                    f"trend (۴ هفته): {rev_trend}")
        except Exception as e:  # noqa: BLE001
            return f"❌ kpi error: {type(e).__name__}"

    def _kpi_record(self, arg: str) -> str:
        """/kpi_record <revenue_usd> <ppv_unlocks> [posts] [delivery_rate]"""
        try:
            parts = (arg or "").split()
            if len(parts) < 2:
                return "❌ /kpi_record <revenue_usd> <ppv_unlocks> [posts] [delivery_rate]\nمثال: /kpi_record 15 1 3 0.9"
            rev = float(parts[0])
            ppv = int(parts[1])
            posts = int(parts[2]) if len(parts) > 2 else 0
            dr = float(parts[3]) if len(parts) > 3 else 0.0
            sys.path.insert(0, str(PROJECT_ROOT / "brain"))
            from store import KPIRollup, FanDB
            r = KPIRollup().record(revenue_usd=rev, ppv_unlocks=ppv, posts=posts,
                                   delivery_rate=dr, fan_summary=FanDB().summary())
            self._log("kpi_record", r)
            return f"✅ KPI ثبت شد: ${rev:.2f} · {ppv} PPV · {posts} posts · delivery {dr*100:.0f}%"
        except (ValueError, IndexError):
            return "❌ اعداد نامعتبر — /kpi_record <usd> <ppv> [posts] [rate]"
        except Exception as e:  # noqa: BLE001
            return f"❌ kpi error: {type(e).__name__}"

    def _kpi_import(self, arg: str) -> str:
        """/kpi_import — دو حالت (هر دو دستی، صفر شبکه):
        ۱) سطر(های) CSV هفتگی: revenue,ppv,posts,rate,new_fans,clicks,follows,free_subs,paid
        ۲) کلیک یک کد tracking: «<code> <clicks>» مثل «L-a1b2c3 42»"""
        try:
            text = (arg or "").strip()
            if not text:
                return ("❌ /kpi_import <csv>\n"
                        "فرمت CSV: revenue,ppv,posts,rate,new_fans,clicks,follows,free_subs,paid\n"
                        "یا: /kpi_import L-xxxxxx <clicks> برای کلیکِ یک کد tracking")
            sys.path.insert(0, str(PROJECT_ROOT / "brain"))
            from store import KPIRollup, LinkState, FanDB
            parts = text.split()
            # حالت ۲: کد tracking + کلیک
            if len(parts) == 2 and parts[0].upper().startswith("L-") and parts[1].isdigit():
                r = LinkState().record_clicks(parts[0], int(parts[1]))
                if not r.get("ok"):
                    return f"❌ کد ناشناخته: {parts[0]}"
                # کلیک‌ها به bucket هفتگی هم اضافه شوند تا G1 قابل‌سنجش شود
                KPIRollup().record(clicks=int(parts[1]))
                self._log("kpi_import_clicks", r)
                return f"✅ {r['code']}: جمع کلیک {r['clicks']} (به KPI هفته هم اضافه شد)"
            # حالت ۱: CSV
            r = KPIRollup().import_csv(text, fan_summary=FanDB().summary())
            self._log("kpi_import_csv", r)
            if r["imported"] == 0:
                return f"❌ هیچ سطری import نشد (خراب: {r['skipped']}) — فرمت را چک کن"
            return f"✅ {r['imported']} سطر KPI import شد" + \
                (f" · {r['skipped']} سطر خراب رد شد" if r["skipped"] else "")
        except Exception as e:  # noqa: BLE001
            return f"❌ kpi_import error: {type(e).__name__}"

    def _octopus_card(self) -> str:
        """وضعیتِ bridge به orchestrator. صادقانه: اگه _ops غایب است، isolated می‌گوید."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "brain"))
            from store import OctopusState
            snap = OctopusState().snapshot()
            neural = "✅ موجود" if snap["neural_available"] else "🔴 غایب (isolated)"
            brain = "✅" if snap["brain_loaded"] else "—"
            prot = "⛔ protective" if snap["protective"] else "✅ normal"
            last = snap.get("last_tick")
            now_ts = time.time()
            last_str = "هیچ‌وقت" if not last else f"{int((now_ts - last)/60)} دقیقه پیش"
            return (f"🪄 Octopus bridge\n"
                    f"beat: {snap['beat']} · mode: {prot} · pain: {snap['pain']:.2f}\n"
                    f"neural: {neural} · brain: {brain}\n"
                    f"last tick: {last_str}\n"
                    f"/octopus_tick برای یک tick advisory")
        except Exception as e:  # noqa: BLE001
            return f"❌ octopus error: {type(e).__name__}"

    def _octopus_tick(self) -> str:
        """یک tick از orchestrator اجرا کن (اگه موجود باشد)."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            sys.path.insert(0, str(PROJECT_ROOT / "brain"))
            # تلاش برای import orchestrator (وابسته به _ops/neural و غیره)
            try:
                import orchestrator as _orch_mod
                orch = _orch_mod.PFOrchestrator()
                result = orch.tick()
                sys.path.insert(0, str(PROJECT_ROOT / "brain"))
                from store import OctopusState
                OctopusState().record_tick(
                    beat=result.beat, protective=result.mode == "protective",
                    pain=result.pain, brain_loaded=True,
                    neural_available=getattr(_orch_mod, "NEURAL_AVAILABLE", True))
                self._log("octopus_tick", {"beat": result.beat, "mode": result.mode})
                if result.mode == "blocked_compliance":
                    return ("⛔ tick بلاک شد — compliance fail-closed: manifest غایب/خراب یا "
                            "قانونی از hard_rules تأیید نشد. هیچ advisory تولید نشد. "
                            "(PROJECT-F-CONTROL-MANIFEST.json را چک کن)")
                return (f"🪄 tick #{result.beat} اجرا شد · mode: {result.mode} · pain: {result.pain:.2f}\n"
                        f"snapshot: {len(result.snapshot)} کلید · messages: {len(result.messages)}")
            except ImportError:
                # orchestrator یا _ops غایب — isolated heartbeat
                from store import OctopusState
                r = OctopusState().mark_isolated("orchestrator/_ops modules unavailable")
                self._log("octopus_tick_isolated", r)
                return ("🪄 tick isolated (orchestrator یا _ops غایب)\n"
                        "heartbeat ثبت شد. برای tick واقعی، _ops/neural باید موجود باشد.\n"
                        "این حالت صادقانه‌ست — bridge بدون dependency دروغ نمی‌گوید.")
        except Exception as e:  # noqa: BLE001
            return f"❌ octopus error: {type(e).__name__}"

    def _dm_inbox(self, text: str) -> str:
        """incoming DM از مشتری → FAQ auto-draft (HITL — هیچ auto-send)."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "brain"))
            from faq_engine import auto_draft_to_pipeline
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from dm_pipeline import DmPipeline
            r = auto_draft_to_pipeline(text, DmPipeline(), channel="of")
            if not r.get("ok"):
                return f"❌ {r.get('error')}"
            if not r.get("matched"):
                return ("📭 HITL عادی — این پیام FAQ نیست.\n"
                        "با /dm_new <channel> <kind> <body> دستی draft کن.")
            return (f"🤖 FAQ auto-draft ساخته شد: {r['id']} [{r['kind']}]\n"
                    f"intent: {r['intent']}\n"
                    f"⚠️ placeholders را پر کن، بعد /dm_ok {r['id']} (هیچ auto-send نیست).")
        except Exception as e:  # noqa: BLE001
            return f"❌ dm_inbox error: {type(e).__name__}"

    # ── مغز ──
    def _brief(self) -> str:
        if self.model.outward_locked():
            head = "⛔ GATE 0 باز است — بریف فقط جنبهٔ آماده‌سازی دارد.\n"
        else:
            head = ""
        if self.brain:
            try:
                out = self.brain.think_and_communicate(draft_title="weekly")
                msgs = out.get("messages", []) if isinstance(out, dict) else []
                body = "\n".join(getattr(m, "text", str(m))[:300] for m in msgs[:3]) or "مغز پیامی نداشت."
                return head + "🧠 بریف مغز:\n" + body
            except Exception as e:
                self._log("brain_error", {"err": str(e)[:200]})
        return head + ("🧠 بریف heuristic: تمرکز هفته طبق M3 = گام‌های فاز جاری؛ "
                       "صف verdictها را با /verdicts ببین؛ جمعه SOP داشبورد.")

    def _think(self, topic: str) -> str:
        if os.environ.get("ANTHROPIC_API_KEY") and self.cost.can_spend(0.05):
            resp = self._llm(topic)
            if resp:
                return "🧠 " + resp
        return (f"🧠 (heuristic) دربارهٔ «{topic}»: مقابل قواعد قفل‌شده و ماتریس M2 بسنجش؛ "
                "اگر outward است → صف verdict؛ اگر داخلی است → کم‌هزینه‌ترین آزمایش ۲هفته‌ای را طراحی کن "
                "و در Experiment Log ثبت کن. جزئیات بیشتر بعد از فعال‌شدن لایهٔ LLM (V3).")

    def _llm(self, topic: str) -> str | None:
        try:
            body = {
                "model": os.environ.get("LANGAR_MODEL", "claude-haiku-4-5"),
                "max_tokens": 400,
                "system": ("Advisor for 'Project-F' (coded). Persian answers. Propose-only. "
                           "Never suggest outward actions while GATE 0 open. Never include real "
                           "names, cities, or identity details; partners are codes A and C. "
                           "Hard rules: feet-only, no ToS violation, in-platform payment, "
                           "geo-block Iran, 18+, human-in-the-loop."),
                "messages": [{"role": "user", "content": topic[:2000]}],
            }
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(body).encode(),
                headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.loads(r.read().decode())
            usage = out.get("usage", {})
            aud = (usage.get("input_tokens", 0) * 1 + usage.get("output_tokens", 0) * 5) / 1e6 * 1.55
            self.cost.add(max(aud, 0.001))
            return "".join(b.get("text", "") for b in out.get("content", []))[:1500]
        except Exception as e:
            self._log("llm_error", {"err": str(e)[:200]})
            return None

    # ── حلقه ──
    def maybe_weekly(self) -> None:
        """تیک جمعه: خودارزیابی + proposal — فقط پیام، هیچ اکشن."""
        today = date.today()
        key = today.strftime("%G-W%V")
        if today.weekday() == 4 and self._last_weekly != key and not KILL_FILE.exists() \
                and not _global_stop():
            path, items = self.upgrader.propose()
            self.send("⚓ تیک جمعه — خودارزیابی:\n" + self.handle(self.ari, "/status") +
                      "\n\nارتقاهای پیشنهادی:\n" + "\n".join(f"• {t}" for t in items) +
                      f"\n📄 {path.name}")
            self._last_weekly = key   # RESIL-4: فقط بعد از انجامِ کار مارک کن (نه قبلش)

    def poll_forever(self) -> None:  # pragma: no cover
        if not (self.token and self.ari):
            print("shadow-mode: TELEGRAM_LANGAR_BOT_TOKEN/TELEGRAM_ARI_CHAT_ID ست نیست. "
                  "دستور بده (stdin):")
            for line in sys.stdin:
                r = self.handle(self.ari or 0, line.strip())
                if r:
                    print(self.guard.clean(r))
            return
        self.send("⚓ لنگر بالا آمد. /status")
        _fail = 0
        while not self._stop:
            try:
                self.maybe_weekly()
            except Exception as e:  # RESIL-3: تیکِ جمعه نباید کلِ حلقهٔ poll را بکشد
                self._log("weekly_error", {"err": str(e)[:200]})
            try:
                url = (f"{TELEGRAM_API}/bot{self.token}/getUpdates?" +
                       urllib.parse.urlencode({"timeout": 30, "offset": self._offset}))
                data = self._http_get(url, timeout=30)
                for up in data.get("result", []):
                    self._offset = up["update_id"] + 1
                    msg = up.get("message") or {}
                    chat = (msg.get("chat") or {}).get("id", 0)
                    reply = self.handle(chat, msg.get("text", ""))
                    if reply:
                        self.send(reply)
                _fail = 0   # RESIL-5: poll تمیز → ریستِ بک‌آف
            except Exception as e:
                _fail += 1
                _err = str(e)[:200]
                self._log("poll_error", {"err": _err, "conflict": "409" in _err})  # ۴۰۹=pollerِ دوم
                time.sleep(min(5 * (2 ** min(_fail, 4)), 60))   # RESIL-5: بک‌آفِ نمایی سقف ۶۰s


if __name__ == "__main__":  # pragma: no cover
    LangarBot().poll_forever()
# end of langar_bot.py
