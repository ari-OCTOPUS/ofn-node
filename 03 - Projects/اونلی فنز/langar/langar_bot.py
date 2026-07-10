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
COST_FILE = HERE / "cost_meter.json"
CONFIG_FILE = HERE / "langar_config.json"
TELEGRAM_API = "https://api.telegram.org"

# مغز اختیاری (brain/ داخل پوشه) — نبودش fail-open به heuristics نیست؛ فقط لایهٔ ۰ ساده‌تر می‌شود
sys.path.insert(0, str(PROJECT_ROOT / "brain"))
try:
    from dual_brain_v3 import DualBrainV3  # type: ignore
except Exception:
    DualBrainV3 = None  # noqa: N816

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
    """هر متن خروجی به تلگرام از این گیت رد می‌شود. fail-closed:
    اگر config خراب باشد، سخت‌گیرترین حالت اعمال می‌شود."""

    DEFAULT = {
        "blocklist": [],                      # نام‌های واقعی — توسط آری پر شود
        "city_terms": ["Sydney", "سیدنی", "sydney"],
        "name_map": {"صبا": "C", "آری": "A"},
        "project_code": "Project-F",
    }

    def __init__(self, config: dict | None = None):
        cfg = dict(self.DEFAULT)
        try:
            cfg.update(config or _load_json(CONFIG_FILE, {}))
        except Exception:
            pass
        self.cfg = cfg

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
        """قفل تا وقتی «پیامد: Branch A» در PROJECT.md ثبت نشده."""
        txt = _read_text(self.root / "PROJECT.md")
        recorded = re.search(r"پیامد:\s*Branch\s*A\b", txt)
        return not bool(recorded)

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

    # ── پل به استودیوی صبا (handoff دوطرفه، فقط‌خواندنی) ──
    def saba_bridge(self) -> dict:
        """می‌خواند از studio/: درفت‌های pending، اعلان‌های صبا، وضعیت halt.
        صفر PII — فقط شمارش/متادیتا و متن اعلانِ خودِ صبا."""
        studio = self.root / "studio"
        drafts = _load_json(studio / "drafts.json", [])
        pend = [d for d in drafts if isinstance(d, dict) and d.get("status") == "pending"]
        notes = _load_json(studio / "to_ari.json", [])
        return {
            "pending_drafts": len(pend),
            "pending_titles": [str(d.get("title", ""))[:40] for d in pend[-5:]],
            "saba_halted": (studio / "HALT").exists(),
            "notes": [str(n.get("text", ""))[:120] for n in notes[-5:]] if isinstance(notes, list) else [],
            "capacity": _load_json(studio / "capacity.json", {}).get("hours"),
        }

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
                       "(الان خالی است — redact نام‌ها فقط روی name_map پیش‌فرض) — اثر: بالا، هزینه: ۵ دقیقه.")
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

    # ── HTTP ──
    @staticmethod
    def _default_get(url: str, timeout: int = 35):
        req = urllib.request.Request(url, headers={"User-Agent": "langar/0.1"})
        with urllib.request.urlopen(req, timeout=timeout + 5) as r:
            return json.loads(r.read().decode())

    @staticmethod
    def _default_post(url: str, body: dict, timeout: int = 10):
        data = json.dumps(body, ensure_ascii=False).encode()
        req = urllib.request.Request(url, data=data, headers={
            "User-Agent": "langar/0.1", "Content-Type": "application/json"})
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
        """تنها کانال خروجی. متن → OpsecGuard → تلگرام. هیچ متد رسانه‌ای وجود ندارد."""
        safe = self.guard.clean(text)[:4000]
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
        if KILL_FILE.exists() and cmd not in ("/revive", "/status"):
            return "⚓ لنگر در حالت KILL است. فقط /status و /revive."
        if cmd in ("/start", "/help"):
            return ("⚓ لنگر — کاکپیت Project-F (propose-only)\n"
                    "/status /gates /verdicts /saba /brief /think <موضوع>\n"
                    "/kpi /report /upgrade /rules /kill /revive")
        if cmd == "/rules":
            return "قواعد قفل‌شده:\n" + "\n".join(LOCKED_RULES)
        if cmd == "/gates":
            lock = "🔒 باز (بلاکر)" if self.model.outward_locked() else "✅ ثبت‌شده"
            rows = [f"{g}: {desc}" for g, desc in GATES.items()]
            return f"GATE 0: {lock}\n" + "\n".join(rows)
        if cmd == "/status":
            s = self.model.self_state(self.cost)
            b = self.model.saba_bridge()
            lock = "قفل (GATE 0 باز)" if self.model.outward_locked() else "Branch A ثبت"
            saba = ("✋ توقف" if b["saba_halted"] else f"{b['pending_drafts']} درفت منتظر")
            return (f"⚓ وضعیت {_now()}\n"
                    f"پروژه: outward={lock} · سؤال باز={self.model.open_questions()}\n"
                    f"صبا: {saba}" + (f" · {len(b['notes'])} پیام" if b['notes'] else "") + "\n"
                    f"آخرین تصمیم‌ها: " + " | ".join(self.model.last_decisions(2)) + "\n"
                    f"خودم: src={s['src_sha256']} ({s['src_lines']}L) · brain={'✓' if s['brain_loaded'] else '—'}"
                    f" · LLM={'✓' if s['llm_key'] else 'off'} · kill={'ON' if s['killed'] else 'off'}\n"
                    f"هزینهٔ ماه: {s['cost_spent_aud']:.2f}/{s['cost_cap_aud']:.0f} AUD"
                    f" · proposals={s['proposals_on_disk']}")
        if cmd == "/verdicts":
            items = self.model.pending_verdicts()
            return "منتظر verdict تو:\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(items))
        if cmd in ("/saba", "/drafts"):
            b = self.model.saba_bridge()
            head = "✋ صبا الان روی توقف است.\n" if b["saba_halted"] else ""
            lines = [f"{head}🎬 استودیوی صبا:",
                     f"درفت‌های منتظر تأیید: {b['pending_drafts']}"]
            for t in b["pending_titles"]:
                lines.append(f"  ⏳ {t}")
            if b.get("capacity") is not None:
                lines.append(f"ظرفیت اعلامی صبا: {b['capacity']} ساعت")
            if b["notes"]:
                lines.append("پیام‌های صبا:")
                lines += [f"  • {n}" for n in b["notes"]]
            lines.append("\n(تأیید هر درفت = دستی و درون‌پلتفرم؛ این‌جا فقط مشاهده.)")
            return "\n".join(lines)
        if cmd == "/brief":
            return self._brief()
        if cmd == "/think":
            return self._think(arg or "وضعیت کلی")
        if cmd == "/kpi":
            p = self.model.root / "drafts-awaiting-gate" / "kpi-dashboard-spec.md"
            return ("داشبورد هنوز داده ندارد (pre-launch). اسپک آماده است: kpi-dashboard-spec"
                    if p.exists() else "اسپک داشبورد پیدا نشد.")
        if cmd == "/report":
            return ("قالب گزارش جمعه (برای C):\n"
                    "«این هفته: ⟨n⟩ نفر دیدن، ⟨n⟩ کلیک، ⟨$x⟩ اومد (حتی اگر صفر).\n"
                    "هفتهٔ بعد: ⟨تم⟩. سؤالی داری؟»\n"
                    "+ ردیف داشبورد را پر کن (SOP جمعه).")
        if cmd == "/upgrade":
            path, items = self.upgrader.propose()
            self._log("upgrade", {"file": path.name, "n": len(items)})
            return ("پیشنهادهای ارتقا (اعمال = دست تو):\n" +
                    "\n".join(f"{i+1}. {t}" for i, t in enumerate(items)) +
                    f"\n📄 ثبت شد: langar/upgrade_proposals/{path.name}")
        if cmd == "/kill":
            KILL_FILE.write_text(_now(), encoding="utf-8")
            self._log("kill", {})
            return "⚓ KILL فعال شد. همه‌چیز متوقف؛ /revive برای بازگشت."
        if cmd == "/revive":
            KILL_FILE.unlink(missing_ok=True)
            self._log("revive", {})
            return "لنگر برگشت. /status بزن."
        return "دستور ناشناخته. /help"

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
        if today.weekday() == 4 and self._last_weekly != key and not KILL_FILE.exists():
            self._last_weekly = key
            path, items = self.upgrader.propose()
            self.send("⚓ تیک جمعه — خودارزیابی:\n" + self.handle(self.ari, "/status") +
                      "\n\nارتقاهای پیشنهادی:\n" + "\n".join(f"• {t}" for t in items) +
                      f"\n📄 {path.name}")

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
        while not self._stop:
            self.maybe_weekly()
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
            except Exception as e:
                self._log("poll_error", {"err": str(e)[:200]})
                time.sleep(5)


if __name__ == "__main__":  # pragma: no cover
    LangarBot().poll_forever()
# end of langar_bot.py
