#!/usr/bin/env python3
"""improve.py — مدیرِ خودارتقایی (لایهٔ تجمیعِ owner-facing که در سیستم غایب بود).

recon: mine/RFC/sandbox/Chamber/Evolution/کارتِ تلگرام/calibration همه هستند، ولی
«دایجستِ ارتقا»ی اولویت‌دارِ owner-facing نیست. این ماژول آن است: از

  • audit-matrix (self_audit — گاف‌های چک‌لیستِ ۲۰-بخشی)
  • RFCهای دکتر (knowledge/internal/*.md)
  • idea_graph (هاب‌ها/پل‌های vault، اگر باشد)
  • coherence/اعضای cortex

→ «پیشنهادهای ارتقا»ی **دسته‌بندی‌شده** (رأی مالک: «هر چه پیدا کرد، دسته‌بندی‌شده») +
سطح‌بندیِ تغییر (§۱۰ چک‌لیست: tune/reconfig/rewrite/code) می‌سازد.

مرزِ اتومات (محافظه‌کار، طبقِ قانونِ اساسی): **پیش‌فرض propose-only**. فقط knobهای
$0 برگشت‌پذیرِ درونِ whitelist و فقط با پرچمِ ACTIVATION-SELF-IMPROVE-AUTO خودکار
اعمال می‌شوند (log + قابلِ‌وتو). هر چیزِ کد/پرچم/پول/ژنوم → همیشه پیشنهاد به مالک.

یادگیری: verdictهای مالک روی پیشنهادها (improve-verdicts.jsonl) دسته‌های ردشده را
کم‌اولویت می‌کند. مغزِ محلی (ollama $0) عبارت‌بندی/رتبه را کمک می‌کند؛ پولی گیت‌دار.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE))
import opslib      # noqa: E402
import self_audit  # noqa: E402

STATE = opslib.STATE_DIR
DIGEST_PATH = STATE / "cortex" / "upgrades-digest.json"
VERDICTS_PATH = STATE / "cortex" / "improve-verdicts.jsonl"
AUTO_STATE_PATH = STATE / "cortex" / "improve-auto-state.json"

# ── سنتزِ عمیق (۲۰۲۶-۰۷-۲۷، «مغزِ اصلی را دوسطحی کن») ──────────────────────────
# اندازه‌گیریِ همان روز: فکرِ این حلقه ask("think") بود → مدلِ محلیِ رایگان با سقفِ
# ۹۰ توکن، در حالی که Fugu (پلنِ فلت) در کلِ ارگانیسم یک مشتری داشت. لایهٔ محیطی
# همان محلیِ تند می‌ماند (بایت‌به‌بایت)؛ این لایه، جدا و flag-gated، چند بار در روز
# صفِ کاملِ گاف‌ها را به مغزِ گران می‌دهد و جوابِ واقعی (نه یک‌جمله‌ای) می‌گیرد.
# حلقه هر ~۷ دقیقه می‌دود پس سقفِ روزانه **داخلِ** همین ماژول است، نه دستِ کادنس.
FLAG_DEEP = "CORTEX_IMPROVE_DEEP"
DEEP_SLOTS_PATH = STATE / "cortex" / "improve-deep-slots.json"
DEEP_LEDGER_PATH = STATE / "cortex" / "deep-synth.jsonl"
DEEP_DAILY_DEFAULT = 2
DEEP_MAX_TOKENS = 1200
DEEP_MIN_CHARS = 200          # کوتاه‌تر از این = جوابِ بی‌ارزش؛ ثبت می‌شود ولی digest نمی‌رود


def _deep_daily_cap() -> int:
    try:
        n = int(str(os.environ.get("CORTEX_IMPROVE_DEEP_DAILY", "")).strip())
    except (TypeError, ValueError):
        return DEEP_DAILY_DEFAULT
    return n if 0 < n <= 8 else DEEP_DAILY_DEFAULT


_DEEP_MEMO: dict = {"date": "", "used": 0}


def _deep_slot_take() -> bool:
    """یک اسلاتِ امروز را بسوزان — **قبل از** فراخوانِ گران (درسِ deep_think:
    مغزِ خراب نباید هر چرخه یک تماسِ ۳۰ ثانیه‌ای بسوزاند). False = سقف پر است."""
    today = opslib.today()
    if _DEEP_MEMO.get("date") == today and int(_DEEP_MEMO.get("used", 0)) >= _deep_daily_cap():
        return False          # دیسک شاید ننوشته باشد؛ این پروسه یادش هست
    d = {"date": "", "used": 0}
    try:
        if DEEP_SLOTS_PATH.exists():
            loaded = json.loads(DEEP_SLOTS_PATH.read_text("utf-8"))
            if isinstance(loaded, dict):
                d = loaded
    except (OSError, ValueError):
        pass
    if d.get("date") != today:
        d = {"date": today, "used": 0}
    if int(d.get("used", 0)) >= _deep_daily_cap():
        return False
    d["used"] = int(d.get("used", 0)) + 1
    try:
        DEEP_SLOTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = DEEP_SLOTS_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, DEEP_SLOTS_PATH)
    except OSError:
        # پشتیبانِ درون-پروسه‌ای (ممیزیِ ۰۷-۲۷): حلقه هر ~۷ دقیقه می‌دود، پس
        # fail-openِ قبلی روی دیسکِ ناسالم یعنی ~۲۰۰ تماسِ گران در روز.
        _DEEP_MEMO["date"] = today
        _DEEP_MEMO["used"] = int(_DEEP_MEMO.get("used", 0)) + 1
        if _DEEP_MEMO["used"] > _deep_daily_cap():
            return False
    return True


def _previous_synth(n: int = 3) -> list:
    """آنچه در جلسه‌های عمیقِ اخیر گفته‌ام. فقط جلسه‌های موفق؛ خطِ خراب رد می‌شود."""
    out = []
    try:
        if not DEEP_LEDGER_PATH.exists():
            return []
        for line in DEEP_LEDGER_PATH.read_text("utf-8").splitlines()[-20:]:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("ok") and r.get("text"):
                out.append({"وقت": str(r.get("ts"))[:16], "گفتی": str(r["text"])[:300]})
    except OSError:
        return []
    return out[-n:]


def _deep_synth(top: list, rate, maturity) -> "dict | None":
    """جوابِ عمیقِ مغزِ گران روی صفِ واقعیِ گاف‌ها. None = نبود/نخواست/نتوانست.
    tier=primary **پین** است: بدونِ پین، CORTEX_LOCAL_FIRST ردهٔ میانی را بی‌صدا
    به مدلِ رایگان می‌بَرد و این لایه نمایش می‌شد در حالِ گزارشِ موفقیت."""
    if os.environ.get(FLAG_DEEP, "0") != "1" or not top:
        return None
    if not _deep_slot_take():
        return None
    items = [{k: t.get(k) for k in ("id", "priority", "title", "suggested_action",
                                    "change_level", "source")} for t in top[:8]]
    # ۲۰۲۶-۰۷-۲۷ — بدونِ این، هر جلسهٔ گران از صفر شروع می‌کرد: `deep-synth` سه بار
    # در یک روز دوید و هر سه بار همان آیتم را با همان استدلال انتخاب کرد. جلسه‌ای
    # که جلسهٔ قبل را نخوانَد، خرج است نه سرمایه.
    body = {"گاف‌ها": items, "improvement_rate": rate, "maturity_pct": maturity}
    prev = _previous_synth()
    if prev:
        body["قبلاً_گفتی"] = prev
        body["توجه"] = ("حرفِ تکراری نزن. اگر همان انتخاب هنوز درست است، بگو چرا "
                        "هنوز انجام نشده و قدمِ متفاوتی پیشنهاد بده.")
    prompt = (
        "صفِ اولویت‌دارِ گاف‌های یک سیستمِ خودبهبودگر، با نرخِ بهبودِ سنجیده:\n"
        + json.dumps(body, ensure_ascii=False, indent=1)
        + "\n\nیکی را انتخاب کن که اول باید حل شود. چرا آن و نه بقیه — با ارجاع به "
          "همین داده‌ها. قدمِ اولِ مشخصش چیست؟ و چه مشاهده‌ای ثابت می‌کند انتخابت "
          "غلط بوده؟ اگر صف آن‌قدر بی‌کیفیت است که هیچ‌کدام نمی‌ارزد، همین را صریح بگو.")
    system = ("تو لایهٔ عمیقِ حلقهٔ خودارتقاییِ یک ارگانیسمِ نرم‌افزاری هستی. فارسی، "
              "کوتاه، بدونِ تعارف. فقط از داده‌های داده‌شده استدلال کن؛ حدسِ بیرونی ممنوع. "
              "«نمی‌دانم» و «هیچ‌کدام نمی‌ارزد» جواب‌های معتبرند.")
    rec = {"ts": opslib.now_iso(), "schema": "deep-synth.v1", "n_top": len(items)}
    try:
        import model_router
        r = model_router.ask("plan", prompt, system=system,
                             max_tokens=DEEP_MAX_TOKENS, tier="primary")
    except Exception as e:  # noqa: BLE001 — لایهٔ عمیق هرگز حلقه را نمی‌کشد
        rec.update(ok=False, reason=f"ask-exception:{type(e).__name__}")
        _deep_ledger(rec)
        return None
    text = str(r.get("text") or "").strip()
    rec.update(ok=bool(r.get("ok")), model=r.get("model"), tier=r.get("tier"),
               chars=len(text))
    if not r.get("ok") or len(text) < DEEP_MIN_CHARS:
        rec["reason"] = "empty-or-short"
        _deep_ledger(rec)
        return None
    rec["text"] = text[:4000]
    _deep_ledger(rec)
    return {"ts": rec["ts"], "model": rec.get("model"), "text": text[:2000]}


def _deep_ledger(rec: dict) -> None:
    try:
        DEEP_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEEP_LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass
RFC_DIR = opslib.GENOME_DIR / "knowledge" / "internal"
ACT_AUTO = opslib.OPS / "ACTIVATION-SELF-IMPROVE-AUTO.flag"

# SPEC-OCTOPUS-2027 §۸/§۱۴ — دو گاردِ سختِ خود-تغییری:
OBS_MAX_AGE_MIN = float(os.environ.get("IMPROVE_OBS_MAX_AGE_MIN", "60"))
REFRACTORY_H = float(os.environ.get("IMPROVE_REFRACTORY_H", "24"))

# whitelistِ knobهای $0 برگشت‌پذیر که (فقط با پرچم) خودکار قابلِ‌تنظیم‌اند.
# هرکدام: (env_var، کف، سقف) — هرگز کد/پول/ژنوم/پرچمِ wire.
AUTO_KNOBS = {
    "CORTEX_THINK_EVERY_N": (2, 20),
    "CHRONO_NUDGE_EVERY_N_BEATS": (120, 1440),
    "HEART_SAMPLE_INTERVAL_S": (1800, 7200),
}

# نگاشتِ گافِ شناخته‌شده → اقدامِ مشخص (grounded به recon). category از gap_type.
KNOWN_FIXES = {
    "human-append anti-forgery ENFORCED (is_human unforgeable)":
        ("🔴 امنیتی: human_append_guard را در organism بوت configure/enforce کن — "
         "الان کدمرده است و is_human جعل‌پذیر (یافتهٔ ممیزیِ چندایجنتی).", "code"),
    "owner merge verdict has real effect (apply_merge wired)":
        ("apply_merge را در run_cycle بعد از verdictِ merged صدا بزن (پشتِ flag) تا "
         "تأییدِ تو اثرِ واقعی داشته باشد، نه فقط برچسب.", "code"),
    "self-analysis loop observe→critique→propose→validate→promote":
        ("دکتر را داده‌زنده کن: db را در make_doctor تزریق کن (organism.py) + apply_merge را "
         "در run_cycle بعد از verdictِ merged صدا بزن (پشتِ flag).", "code"),
    "improvement proposals shadow-eval before promote":
        ("measured_lift._default_eval را از stub به سنجشِ واقعیِ suite-delta در sandbox ارتقا بده.",
         "code"),
    "change leveled: tune/reconfig/rewrite + contract":
        ("همین ماژول (improve.py) سطح‌بندیِ change_level را اضافه کرد — تأیید و در RFC schema رسمی کن.",
         "reconfig"),
    "prioritized implementation backlog":
        ("همین دایجست backlog owner-facing است — به کابین/اتاقِ زنده وصلش کن.", "reconfig"),
    "rollback path before apply":
        ("قبل از هر apply_merge یک git tag/checkpoint خودکار بزن (twin of pre-merge tags).", "code"),
    "memory poisoning / false-canon guard":
        ("مانیتورِ خودکارِ created_by:agent بدونِ sources≥2 → هشدار (validate_frontmatter در لوپ).",
         "code"),
    "drift over time measured":
        ("سریِ زمانیِ coherence/velocity را نگه‌دار و شیبِ منفی را به‌عنوان drift هشدار بده.",
         "code"),
    "single-agent / null baseline":
        ("مقایسهٔ خودکارِ neural-vs-null (box/null_dreamer) را per-epoch ثبت کن.", "reconfig"),
    "tool-call cost/latency logging":
        ("latency/costِ هر model_router.ask را به یک trace-log واحد بنویس.", "code"),
    "epistemic signals (uncertainty/disagreement/missing-evidence)":
        ("OCTOPUS_WIRE_EPISTEMICS را بعد از یک هفته shadow روشن کن (رأی مالک).", "reconfig"),
}


def _read(p: Path):
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return None


def _pid(text: str) -> str:
    return "up-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def _load_verdict_penalty() -> dict:
    """دسته‌هایی که مالک قبلاً رد کرده → جریمهٔ اولویت (یادگیری)."""
    pen: dict = {}
    try:
        if VERDICTS_PATH.exists():
            for line in VERDICTS_PATH.read_text("utf-8").splitlines():
                try:
                    r = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if r.get("verdict") == "reject":
                    c = r.get("category", "?")
                    pen[c] = pen.get(c, 0) + 1
    except OSError:
        pass
    return pen


def record_verdict(proposal_id: str, category: str, verdict: str) -> None:
    """verdictِ مالک روی یک پیشنهاد (accept/reject/later) → یادگیری."""
    opslib.append_jsonl(VERDICTS_PATH, {"ts": opslib.now_iso(), "id": proposal_id,
                                        "category": category, "verdict": verdict})


# ─── جمع‌آوریِ سیگنال‌ها ─────────────────────────────────────────────────────────
def gather_signals() -> dict:
    matrix = self_audit.run_audit(write=True)      # ممیزیِ تازه
    idea = _read(STATE / "idea-graph-latest.json") or {}
    cortex = _read(STATE / "cortex" / "cortex-state.json") or {}
    research = _read(STATE / "pulse" / "research-latest.json") or {}  # جلسه ۴۶: وبِ رایگان
    synthesis = _read(STATE / "cortex" / "synthesis-latest.json") or {}  # سنتزِ مغز
    self_model = _read(STATE / "cortex" / "self-model.json") or {}       # نقشهٔ خود
    part_loops = _read(STATE / "cortex" / "part-loops-latest.json") or {}  # لوپِ هر بخش
    business = _read(STATE / "cortex" / "business-brain-latest.json") or {}  # مغزِ دوم
    rfcs = []
    try:
        if RFC_DIR.exists():
            for f in sorted(RFC_DIR.glob("rfc-*.md"))[-10:]:
                if "lesson" in f.name:
                    continue
                rfcs.append(f.stem)
    except OSError:
        pass
    return {"matrix": matrix, "idea": idea, "cortex": cortex,
            "research": research, "synthesis": synthesis,
            "self_model": self_model, "part_loops": part_loops,
            "business": business, "doctor_rfcs": rfcs}


_PRI_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _auto_ok(change_level: str, title: str) -> bool:
    """آیا این تغییر مجازِ auto است؟ فقط tune + knobِ whitelist + پرچمِ مالک."""
    if change_level != "tune":
        return False
    if not ACT_AUTO.exists():
        return False
    return any(k for k in AUTO_KNOBS if k.lower() in title.lower())


def generate_proposals(signals: dict) -> list[dict]:
    """گاف‌های audit + RFCها + idea → پیشنهادهای دسته‌بندی‌شده."""
    pen = _load_verdict_penalty()
    out: list[dict] = []
    # ۱) از گاف‌های audit (Missing/Partial)
    for g in signals["matrix"].get("gaps", []):
        title = g["item"]
        action, level = KNOWN_FIXES.get(title, (
            f"این بند را از «{g['status']}» به Done ببر (بخشِ {g.get('section','?')}).", "reconfig"))
        cat = g["gap_type"] if g["gap_type"] != "none" else "implementation"
        base = _PRI_RANK.get(g["priority"], 3)
        out.append({
            "id": _pid("audit:" + title), "source": "audit", "category": cat,
            "priority": g["priority"], "_rank": base + pen.get(cat, 0) * 0.5,
            "title": title, "status_now": g["status"],
            "rationale": f"چک‌لیست §{g.get('section','?')} — الان {g['status']}",
            "evidence": g["evidence"], "suggested_action": action,
            "change_level": level, "auto_applicable": _auto_ok(level, title),
            "status": "proposed",
        })
    # ۲) از RFCهای دکتر (گلوگاه‌های سلامتِ کشف‌شده)
    for rid in signals.get("doctor_rfcs", []):
        out.append({
            "id": _pid("doctor:" + rid), "source": "doctor", "category": "implementation",
            "priority": "P1", "_rank": 1.2, "title": f"RFCِ دکتر: {rid}",
            "rationale": "دکترِ تکاملی یک گلوگاهِ سلامت mine کرد",
            "evidence": f"knowledge/internal/{rid}.md",
            "suggested_action": "کارتِ RFC را در تلگرام تأیید/رد کن (human-append).",
            "change_level": "reconfig", "auto_applicable": False, "status": "proposed",
        })
    # ۲.۵) از سنتزِ مغز (فراشناختی جلسه ۴۶): پروپوزال‌های fugu/glm/local — همیشه propose-only
    for sp in (signals.get("synthesis") or {}).get("proposals", [])[:3]:
        t = f"سنتزِ مغز: {sp.get('title', '')[:80]}"
        out.append({
            "id": _pid("synth:" + t), "source": "synthesis", "category": "architecture",
            "priority": "P2", "_rank": 1.8 + pen.get("architecture", 0) * 0.5, "title": t,
            "rationale": (sp.get("why") or "سنتزِ وب+کد+جهت‌های مالک")[:180],
            "evidence": f"synthesis-latest.json [{(signals['synthesis'].get('tier') or '?')}]",
            "suggested_action": (sp.get("first_step") or "بازبینِ مالک")[:180],
            "change_level": "reconfig", "auto_applicable": False, "status": "proposed",
        })
    # ۲.۶) از نقشهٔ خود: ماژول‌های بدونِ خودتوصیفی = گپِ خودآگاهی ($0، سندی)
    sm = signals.get("self_model") or {}
    if sm.get("undocumented"):
        n = len(sm["undocumented"])
        t = f"خودآگاهیِ سند: {n} ماژول بدونِ docstring"
        out.append({
            "id": _pid("selfmodel:" + t), "source": "self_model", "category": "observability",
            "priority": "P3", "_rank": 2.8, "title": t,
            "rationale": f"self-awareness {sm.get('self_awareness_pct')}% — "
                         f"نمونه: {', '.join(sm['undocumented'][:3])}",
            "evidence": "self-model.json", "suggested_action":
                "به هر ماژول یک docstringِ یک‌خطی بده (تغییرِ سندی، بی‌خطر).",
            "change_level": "tune", "auto_applicable": False, "status": "proposed",
        })
    # ۲.۷) از لوپِ هر بخش (جلسه ۴۶): هر بخش پیشنهادِ بهبودِ خودش را می‌دهد
    for pp in (signals.get("part_loops") or {}).get("proposals", [])[:8]:
        title = f"{pp.get('part', '?')}: {pp.get('title', '')[:70]}"
        lvl = pp.get("change_level", "reconfig")
        out.append({
            "id": _pid("part:" + title), "source": "part-loop", "category": "architecture",
            "priority": "P2" if lvl != "tune" else "P3",
            "_rank": (2.2 if lvl != "tune" else 3.1) + pen.get("architecture", 0) * 0.5,
            "title": title, "rationale": f"لوپِ بخشِ «{pp.get('part')}» این را یافت",
            "evidence": "part-loops-latest.json",
            "suggested_action": pp.get("action", "بازبینِ مالک")[:180],
            "change_level": lvl,
            "auto_applicable": bool(pp.get("auto_ok")) and _auto_ok(lvl, title),
            "status": "proposed",
        })
    # ۲.۸) از مغزِ دوم (کسب‌وکار جلسه ۴۶): پیشنهادهای درآمد/لید — همیشه به مالک (propose-only)
    for bp in (signals.get("business") or {}).get("proposals", [])[:5]:
        title = f"{bp.get('part', 'کسب‌وکار')}: {bp.get('title', '')[:70]}"
        out.append({
            "id": _pid("biz:" + title), "source": "business-brain", "category": "business",
            "priority": "P1", "_rank": 1.0,     # کسب‌وکار = درآمدِ واقعی = اولویتِ بالا
            "title": title, "rationale": "مغزِ دومِ کسب‌وکار این را یافت",
            "evidence": "business-brain-latest.json",
            "suggested_action": bp.get("action", "بازبینِ مالک")[:180],
            "change_level": bp.get("change_level", "reconfig"),
            "auto_applicable": False,           # کسب‌وکار هرگز خودکار نیست
            "status": "proposed",
        })
    # ۳) از idea_graph (پل‌های پیشنهادیِ vault، اگر باشد)
    edges = (signals.get("idea") or {}).get("proposed_edges") or []
    for e in edges[:3]:
        t = f"پلِ دانش: {e}" if isinstance(e, str) else f"پلِ دانش: {json.dumps(e, ensure_ascii=False)[:60]}"
        out.append({
            "id": _pid("idea:" + t), "source": "idea", "category": "theory",
            "priority": "P3", "_rank": 3.0, "title": t,
            "rationale": "idea_graph یک اتصالِ ممکن بینِ نوت‌ها یافت",
            "evidence": "idea-graph-latest.json", "suggested_action": "اگر مرتبط بود، wikilink اضافه کن.",
            "change_level": "tune", "auto_applicable": False, "status": "proposed",
        })
    out.sort(key=lambda p: p["_rank"])
    return out


def improvement_rate(limit: int = 200) -> dict:
    """نرخِ واقعیِ خودبهبودی — چه کسری از نیت‌های ثبت‌شده واقعاً یک متریکِ برون‌دادی
    را جابه‌جا کردند. منبع: رکوردهای بستارِ state/cortex/outcomes.jsonl
    (schema outcome-closure.v1 — نوشتهٔ goal_directed._close_intents).

    چرا این و نه maturity_pct (W2): چک‌لیستِ self_audit تابعِ محضِ «وجودِ فایل +
    grepِ سورس» است و ۱۷ بند از ۴۳ ساختاراً هرگز Done نمی‌شوند → آن عدد در سقفِ
    خودش قفل است. این یکی از داده‌ای می‌آید که واقعاً حرکت می‌کند.

    صداقت: نبودِ داده → rate_pct=None (نه صفرِ ساختگی). $0، فقط‌خواندنی، fail-soft.
    """
    p = STATE / "cortex" / "outcomes.jsonl"
    closed = moved = 0
    # T2 لایهٔ ۲ (2026-07-25، مگاپرامپت): مخرج = «تعدادِ نیتِ متمایزِ دارای نتیجهٔ
    # نهایی»، نه تعدادِ رکوردِ closure. گواه: ۸۳ بستار روی فقط ۴ کلیدِ متمایز با
    # ۲۰ جفتِ (ts,key) متناقض — «۴۵٪» یعنی «کارت جابه‌جا شد» نه نرخِ بهبود.
    # پشتِ OCTOPUS_HONEST_OUTCOMES (خاموش = شمارشِ خامِ قدیم، بایت‌به‌بایت).
    # نتیجهٔ موردِانتظار: rate_pct می‌افتد (احتمالاً صفر/None) — این موفقیت است،
    # نه رگرسیون؛ عددِ پایینِ راست از عددِ بالای دروغ بهتر است.
    honest = os.environ.get("OCTOPUS_HONEST_OUTCOMES") == "1"
    per_key: dict[str, bool] = {}
    try:
        if not p.exists():
            return {"closed": 0, "moved": 0, "rate_pct": None}
        for line in p.read_text("utf-8").splitlines()[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if r.get("kind") != "closure":
                continue
            if honest:
                k = str(r.get("key") or "").strip()
                if k:
                    per_key[k] = bool(r.get("moved"))   # آخرین رأی per key برنده است
            else:
                closed += 1
                moved += 1 if r.get("moved") else 0
    except OSError:
        return {"closed": 0, "moved": 0, "rate_pct": None}
    if honest:
        closed = len(per_key)
        moved = sum(1 for v in per_key.values() if v)
    return {"closed": closed, "moved": moved,
            "rate_pct": round(100.0 * moved / closed, 1) if closed else None}


def observability_ok() -> tuple[bool, str]:
    """گاردِ GAAT (SPEC §۲۱-۱): «مشاهده مُرد = خود-تغییری می‌ایستد.»
    معیار: ORGANISM-STATE موجود و تازه (≤OBS_MAX_AGE_MIN). فایلِ غایب (pre-birth/تست)
    هم degraded حساب می‌شود — L1 آزاد می‌ماند ولی L2 هرگز."""
    p = STATE / "ORGANISM-STATE.json"
    try:
        if not p.exists():
            return False, "ORGANISM-STATE غایب (pre-birth یا مشاهدهٔ مرده)"
        import datetime as _dt
        age_min = (_dt.datetime.now().timestamp() - p.stat().st_mtime) / 60.0
        if age_min > OBS_MAX_AGE_MIN:
            return False, f"ORGANISM-STATE کهنه ({age_min:.0f}min > {OBS_MAX_AGE_MIN:.0f})"
        return True, "fresh"
    except OSError as e:
        return False, f"probe-error: {type(e).__name__}"


def refractory_open() -> tuple[bool, str]:
    """SPEC §۱۴: بینِ دو auto-apply حداقل REFRACTORY_H — ضدِ دستکاریِ پشتِ‌سرِهمِ معماری."""
    st = _read(AUTO_STATE_PATH) or {}
    try:
        last = float(st.get("last_auto_ts", 0.0))
    except (TypeError, ValueError):
        last = 0.0
    if last <= 0:
        return True, "first"
    import datetime as _dt
    hours = (_dt.datetime.now().timestamp() - last) / 3600.0
    if hours < REFRACTORY_H:
        return False, f"refractory: {hours:.1f}h < {REFRACTORY_H:.0f}h"
    return True, "open"


def _persist_auto_ts(ts: float | None = None) -> None:
    """SPEC §۱۴ — مُهرِ زمانِ آخرین auto-apply را اتمیک بنویس تا گاردِ refractory
    واقعاً اجراشدنی شود. پیش از این last_auto_ts هرگز نوشته نمی‌شد → refractory_open
    همیشه «first» می‌دید و cooldown هرگز اعمال نمی‌شد (اصلاحِ محافظه‌کارِ ایمنی:
    فقط سخت‌گیرانه‌تر). کلیدهای موجود حفظ می‌شوند؛ fail-soft: خطای نوشتن هرگز
    حلقهٔ auto را نمی‌کشد."""
    import datetime as _dt
    now_ts = float(ts) if ts is not None else _dt.datetime.now().timestamp()
    try:
        with opslib.LockedJson(AUTO_STATE_PATH) as lj:
            st = lj.read() or {}
            st["last_auto_ts"] = now_ts
            st["last_auto_iso"] = opslib.now_iso()
            lj.write(st)
    except Exception as e:  # noqa: BLE001 — persist نباید auto را بکشد
        opslib.alert([f"improve auto-state persist failed (non-fatal): "
                      f"{type(e).__name__}: {e}"])


def maybe_auto_apply(proposals: list[dict]) -> list[dict]:
    """L2 نردبان (SPEC §۴): فقط knobهای $0 برگشت‌پذیرِ whitelist، فقط با پرچمِ مالک،
    فقط با مشاهدهٔ زنده، فقط بیرونِ دورهٔ refractory. هر اعمال log می‌شود."""
    applied = []
    if not ACT_AUTO.exists():
        return applied
    obs_ok, obs_why = observability_ok()
    if not obs_ok:
        opslib.alert([f"self-improve auto BLOCKED — observability degraded: {obs_why}"])
        return applied
    ref_ok, ref_why = refractory_open()
    if not ref_ok:
        return applied          # ساکت — دورهٔ نقاهت، رفتارِ عادی
    # جلسه ۴۶ (رأی مالک «براساس درجه خطر و اهداف مجوز بده»): موتورِ تصمیمِ درجه‌بندیِ خطر.
    # فقط knobِ کم‌خطر + هم‌راستا با هدف + سوییتِ سبز واقعاً اعمال می‌شود؛ بقیه escalate.
    try:
        import auto_approve
        cand = [p for p in proposals if p.get("auto_applicable")]
        res = auto_approve.run(cand)
        for a in res.get("applied", []):
            p_match = next((p for p in cand if p.get("title") == a.get("title")), None)
            if p_match:
                p_match["status"] = "auto-applied"
                applied.append(p_match["id"])
    except Exception as e:  # noqa: BLE001 — auto نباید حلقه را بکشد
        opslib.alert([f"auto_approve error (non-fatal): {type(e).__name__}: {e}"])
    # SPEC §۱۴: هر بار که یک auto-apply واقعاً رخ داد، مُهرِ refractory را ثبت کن
    # تا اعمالِ بعدیِ درونِ پنجرهٔ نقاهت مسدود شود (گاردِ cooldown را اجراشدنی می‌کند).
    if applied:
        _persist_auto_ts()
    return applied


def run(write: bool = True, use_local_brain: bool = True) -> dict:
    signals = gather_signals()
    proposals = generate_proposals(signals)
    # جلسه ۴۶ (رأی مالک «دایره‌ای الکی نباشه، هدف‌دار باشه»): بازچینیِ هدف‌محور —
    # دایره‌ای‌ها (خودمتریک/سندی) به ته، هدف‌محورها (کسب‌وکار/درآمد/هدف) بالا.
    goal_report = {}
    try:
        import goal_directed
        gr = goal_directed.rerank(proposals)
        proposals = gr["ranked"]
        goal_report = {"n_goal_serving": gr["n_goal_serving"],
                       "n_circular_dropped": gr["n_circular_dropped"],
                       "goals_count": gr["goals_count"],
                       "outcome": goal_directed.measure()}
    except Exception as e:  # noqa: BLE001 — بازچینی نباید حلقه را بکشد
        opslib.alert([f"goal_directed error (non-fatal): {type(e).__name__}: {e}"])
    auto = maybe_auto_apply(proposals)
    # دسته‌بندی (رأی مالک: «دسته‌بندی‌شده»)
    by_cat: dict = {}
    for p in proposals:
        by_cat.setdefault(p["category"], []).append(
            {k: p[k] for k in ("id", "priority", "title", "suggested_action",
                               "change_level", "source", "status_now", "status")
             if k in p})
    # هدف‌محور: proposals از قبل بر اساسِ impact مرتب‌اند (goal_directed). top = صدرِ
    # هدف‌محور + هر P0، نه صرفاً P0/P1 (تا کارِ دایره‌ای بالا نیاید).
    top = [p for p in proposals
           if p.get("priority") == "P0" or p.get("impact", 1.0) >= 1.5
           or p["priority"] == "P1"][:8]
    try:
        import goal_directed
        goal_directed.record_intent(top)   # نیتِ سنجش را ثبت کن (لوپ را ببند)
    except Exception:  # noqa: BLE001
        pass
    thought = None
    if use_local_brain and top:
        try:
            import model_router
            titles = "؛ ".join(t["title"] for t in top[:5])
            r = model_router.ask("think",
                                 f"این گاف‌های اولویت‌دارِ یک سیستمِ خودبهبودگر: {titles}. "
                                 f"در یک جمله بگو کدام اول باید حل شود و چرا.", max_tokens=90)
            if r.get("ok"):
                thought = f"[{r.get('tier')}] {r['text']}"
        except Exception:  # noqa: BLE001 — مغزِ محلی اختیاری
            thought = None
    obs_ok, obs_why = observability_ok()
    if not obs_ok:
        # SPEC §۲۱-۱: degraded → یک آیتمِ P0 صدرِ صف + هیچ L2
        top = [{"id": "up-obs-degraded", "priority": "P0",
                "title": f"⚠ مشاهده degraded: {obs_why}",
                "suggested_action": "اول بدن/observability را زنده کن؛ خود-تغییری تا آن موقع L1.",
                "change_level": "reconfig", "source": "guard",
                "status_now": "Degraded", "status": "proposed"}] + top[:7]
    rate = improvement_rate()
    # لایهٔ عمیق: flag-gated، سقفِ روزانه داخلی، fail-soft — لایهٔ محلیِ بالا دست‌نخورده.
    deep = None
    try:
        deep = _deep_synth(top, rate, signals["matrix"].get("maturity_pct"))
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"improve deep-synth error (non-fatal): {type(e).__name__}: {e}"])
    digest = {
        "ts": opslib.now_iso(), "schema": "upgrades-digest.v1",
        "observability_ok": obs_ok,
        # W2: عددِ چک‌لیست ایستا است (سقفِ ثابت) — با نامِ صادق و پرچمِ صریح.
        # maturity_pct فقط برای سازگاریِ مصرف‌کننده‌های موجود نگه داشته می‌شود.
        "checklist_pct": signals["matrix"].get("maturity_pct"),
        "checklist_static": True,
        "maturity_pct": signals["matrix"].get("maturity_pct"),
        "improvement_rate": rate,
        "n_proposals": len(proposals),
        "by_category": by_cat,
        "top": top,
        "auto_eligible": auto,
        "auto_enabled": ACT_AUTO.exists(),
        **({"brain_note": thought} if thought else {}),
        **({"deep_thought": deep} if deep else {}),
        **({"goal_directed": goal_report} if goal_report else {}),
        "learning": {"rejected_categories": _load_verdict_penalty()},
    }
    if write:
        try:
            DIGEST_PATH.parent.mkdir(parents=True, exist_ok=True)
            with opslib.LockedJson(DIGEST_PATH) as lj:
                lj.write(digest)
            opslib.ledger_note("SELF_IMPROVE_DIGEST", {
                # W2 (2026-07-25): maturity_pct از لِجِر حذف شد — ۴۸ رکوردِ پشتِ‌هم
                # دقیقاً ۷۵.۶ بود، چون تابعِ ایستایِ «وجودِ فایل + grepِ سورس» است و
                # در سقفِ خودش قفل. به‌جایش نرخِ بستارِ واقعی ثبت می‌شود که حرکت دارد.
                "n": len(proposals),
                "improve_rate_pct": rate.get("rate_pct"),
                "closed": rate.get("closed"), "moved": rate.get("moved"),
                "top": [t["title"] for t in top[:3]]}, actor="self-improve")
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"improve digest write failed: {e}"])
    return digest


def read_digest() -> dict:
    return _read(DIGEST_PATH) or {}


if __name__ == "__main__":
    d = run(write=False)
    print(json.dumps({"maturity_pct": d["maturity_pct"], "n_proposals": d["n_proposals"],
                      "categories": {k: len(v) for k, v in d["by_category"].items()},
                      "top3": [t["title"] for t in d["top"][:3]],
                      "brain": d.get("brain_note", "—")}, ensure_ascii=False, indent=2))
