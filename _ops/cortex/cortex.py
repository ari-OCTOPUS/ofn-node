#!/usr/bin/env python3
"""cortex.py — مغزِ مرکزیِ کنترل‌گر: پروسهٔ جدا روی 127.0.0.1:8772 (رأی مالک).

هر چرخه (ریتم از قلبِ سایه — «قلب به همهٔ ساختار وصل است»):
  1) sweep: آگاهیِ همهٔ اعضا از state-fileهای خودشان (read-only) → coherence
  2) alignment: مرتب‌سازیِ **کران‌دارِ** نقشهٔ کارِ $0 (رأی مالک: هرگز پول/merge/حذف)
  3) think: یک فکرِ کوتاه با مغزِ محلی ($0) → ژورنالِ append-only (حافظهٔ ماندگار —
     با خاموش/روشن از بین نمی‌رود)
  4) state ماشین‌خوان + HTTP برای کابین/پنل/هر عضو («به همه جا API»)

جدایی: crash بدن روی مغز اثر ندارد و برعکس. STOP-CORTEX = خوابِ مغز؛
STOP-ORGANISM = مغز فقط تماشا می‌کند (هیچ نوشتنِ نقشه). STOP معمار = خروجِ کامل.
bind انحصاریِ 8772 = قفلِ تک‌نمونه (الگوی organism).
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE))
import opslib        # noqa: E402
import registry      # noqa: E402
import model_router  # noqa: E402

PORT = int(os.environ.get("CORTEX_PORT", "8772"))
CORTEX_DIR = opslib.STATE_DIR / "cortex"
STATE_PATH = CORTEX_DIR / "cortex-state.json"
JOURNAL_PATH = CORTEX_DIR / "journal.jsonl"
STOP_CORTEX = opslib.OPS / "STOP-CORTEX"
THINK_EVERY_N = int(os.environ.get("CORTEX_THINK_EVERY_N", "5"))
IMPROVE_EVERY_N = int(os.environ.get("CORTEX_IMPROVE_EVERY_N", "10"))
# OCT-CORTISOL (رأی مالک 2026-07-18 «بودجه داریم، هوشمندتر»): ورود به ترس = رویدادِ
# مهم → سنتزِ فوریِ مغز با زمینهٔ هشدار، نه انتظار برای تایمرِ پمپ. cooldown ضدِ طوفان.
CORTISOL_EVENTS = os.environ.get("OCTOPUS_CORTISOL_EVENTS", "0") == "1"
CORTISOL_COOLDOWN_S = float(os.environ.get("OCTOPUS_CORTISOL_COOLDOWN_S", "14400"))
CORTISOL_PATH = CORTEX_DIR / "cortisol-state.json"
ACT_WORK_LLM = opslib.OPS / "ACTIVATION-WORK-LLM.flag"   # همان قفلِ لِینِ کاریِ پمپ
DEFAULT_PERIOD_S = float(os.environ.get("CORTEX_PERIOD_S", "120"))
# RC3 فیوزِ سکوتِ مرگ (پیش‌فرض خاموش): وقتی مغز می‌داند مریض است (coherence پایین /
# اعضای کهنهٔ زیاد)، به governor-alerts خبر بده تا مالک بشنود.
OBS_ALERT = os.environ.get("OCTOPUS_OBS_ALERT", "0") == "1"
OBS_COHERENCE_MIN = float(os.environ.get("OCTOPUS_OBS_COHERENCE_MIN", "0.5"))
OBS_STALE_MAX = int(os.environ.get("OCTOPUS_OBS_STALE_MAX", "2"))
OBS_ALERT_EVERY_S = float(os.environ.get("OCTOPUS_OBS_ALERT_EVERY_S", "3600"))


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def heart_rhythm_period() -> tuple[float, str]:
    """ریتمِ چرخهٔ مغز از قلبِ سایه: period مغز = clamp(۲×periodِ قلب، ۶۰..۶۰۰).
    قلب تند بتپد مغز هم تندتر جارو می‌کند؛ قلبِ در استراحت = مغزِ آرام."""
    shadow = _read_json(opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json")
    p = shadow.get("period_s")
    if not p:
        return DEFAULT_PERIOD_S, "بدونِ قلب — ریتمِ پیش‌فرض"
    period = max(60.0, min(600.0, 2.0 * float(p)))
    return period, f"×۲ قلبِ سایه ({p}s)"


def align_work_plan(sweep: dict) -> dict:
    """اختیارِ مصوب: مرتب‌سازیِ کران‌دارِ کارِ $0. کران‌ها (تست‌شده):
    فقط templateهای paid=False · فقط ترتیب + every_s در [۰.۵×..۲×]ِ پیش‌فرض ·
    هرگز add/remove/kind-change · نبودِ plan → هیچ. خروجی: گزارشِ diff.

    W3 (2026-07-25): دو واقعیتِ *جدا* برمی‌گرداند —
      changed = «این چرخه نقشه را عوض کردم؟»
      aligned = «نقشه *الان* هم‌راستاست؟»
    اینها یکی نیستند و `aligned = not changed` هم غلط است: STOP / plan-غایب /
    write-failed هم changed=False‌اند ولی هیچ‌کدام هم‌راستا نیستند. پس هر return
    خودش صریح اعلام می‌کند."""
    if opslib.STOP_ORGANISM.exists():
        return {"changed": False, "aligned": False,
                "reason": "بدن STOP است — مغز فقط تماشا می‌کند"}
    plan_path = opslib.STATE_DIR / "pulse" / "work-plan.json"
    plan = _read_json(plan_path)
    if plan.get("schema") != "work-plan.v1" or not plan.get("templates"):
        return {"changed": False, "aligned": False,
                "reason": "plan غایب — pump هنوز seed نکرده"}
    # ۲۰۲۶-۰۸-۰۶ — `web_research` این‌جا نبود، پس خطِ ۱۰۰ برایش
    # `t.get("every_s", 43200)` می‌خواند — یعنی خودِ مقدارِ **کنونی** (حتی
    # اگر خراب باشد) را به‌عنوانِ base به کار می‌گرفت و بازهٔ کلمپ را دورِ
    # همان مقدارِ خراب می‌ساخت (خودتقویت‌کننده، نه خودترمیم). زنده: every_s
    # به ۵ (ثانیه) رسیده بود — گزارشِ گپ باید هر ۱۲ساعت (۴۳۲۰۰s) بزند،
    # داشت هر ~۵ ثانیه می‌زد. seed ِ اصلی هم ۴۳۲۰۰ است (heart/work_pump.py:45).
    defaults = {"health": 21600, "gap_report": 43200, "web_research": 43200}
    free = [t for t in plan["templates"] if not t.get("paid")]
    paid = [t for t in plan["templates"] if t.get("paid")]
    stale = set(sweep.get("stale_members") or [])
    coherence = float(sweep.get("coherence", 1.0))
    changed = []
    # قاعدهٔ ۱: coherence پایین → health تندتر (تا کفِ ۰.۵×)؛ بالا → به پیش‌فرض برگرد
    for t in free:
        base = defaults.get(t["kind"], t.get("every_s", 43200))
        target = base * (0.5 if coherence < 0.5 else 1.0)
        target = max(base * 0.5, min(base * 2.0, target))
        if abs(t.get("every_s", base) - target) > 1:
            t["every_s"] = int(target)
            changed.append(f"{t['kind']}.every_s→{int(target)}")
    # قاعدهٔ ۲: عضوِ کهنهٔ مدرسه → gap_report جلوی صف؛ وگرنه health اول
    order = ["gap_report", "health"] if "school" in stale else ["health", "gap_report"]
    free_sorted = sorted(free, key=lambda t: order.index(t["kind"])
                         if t["kind"] in order else 99)
    if [t["kind"] for t in free_sorted] != [t["kind"] for t in free]:
        changed.append("reorder:" + ">".join(t["kind"] for t in free_sorted))
    new_templates = free_sorted + paid          # paid دست‌نخورده، تهِ صف
    if not changed:
        return {"changed": False, "aligned": True, "reason": "هم‌راستا بود"}
    plan["templates"] = new_templates
    plan["aligned_by"] = "cortex"
    plan["aligned_ts"] = opslib.now_iso()
    try:
        with opslib.LockedJson(plan_path) as lj:
            lj.write(plan)
    except Exception as e:  # noqa: BLE001
        return {"changed": False, "aligned": False, "reason": f"write-failed: {e}"}
    return {"changed": True, "aligned": True, "diff": changed}


def think(sweep: dict, cycle: int, focus: str | None = None) -> str:
    """فکرِ کوتاهِ ژورنال‌شده — مغزِ محلی اگر بالا بود؛ وگرنه خلاصهٔ قطعی.
    فقط عددها و idها به مدل می‌رود — هیچ secret/PII."""
    summary = (f"coherence={sweep['coherence']} · "
               f"stale={','.join(sweep['stale_members']) or 'هیچ'} · "
               f"اعضا={sweep['n']}")
    q = f"وضعیتِ مجموعه: {summary}."
    # P2 (۲۰۲۶-۰۸-۰۷): مغزِ محلی یک فکر را ۱۶ ساعت تکرار کرد چون ورودی ثابت بود.
    # پشتِ OCTOPUS_WIRE_CORTEX_RICH_THINK: context را با شواهدِ متغیر غنی کن تا هر
    # بار prompt متفاوت باشد (آخرینِ reflection + سیگنالِ قلب). خاموش = byte-identical.
    if os.environ.get("OCTOPUS_WIRE_CORTEX_RICH_THINK", "0") == "1":
        try:
            # آخرین reflection از semantic memory (هر چند دقیقه تغییر می‌کند)
            _sem = opslib.STATE_DIR / "semantic_memory.jsonl"
            if _sem.exists():
                _lines = _sem.read_text("utf-8").splitlines()
                for _ln in reversed(_lines[-5:]):
                    try:
                        _d = json.loads(_ln)
                        _gist = str(_d.get("gist", "")).strip()
                        if _gist:
                            q += f" آخرینِ بازتاب: {_gist[:120]}."
                            break
                    except (ValueError, KeyError):
                        continue
            # سیگنالِ زندهٔ قلب (هر تیک تغییر می‌کند). `signal` یک HeartSignal.v1
            # است (dict با beat_seq/period_s/sigma_now/baro_factor)، نه رشته —
            # پارسِ فیلدهایِ مفهومیِ انسان‌خواندن، نه dumpِ خامِ dict.
            _shadow = _read_json(opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json")
            _sig = _shadow.get("signal") if isinstance(_shadow, dict) else None
            if isinstance(_sig, dict):
                _period = _sig.get("period_s")
                _sigma = _sig.get("sigma_now")
                _baro = _sig.get("baro_factor")
                _parts = []
                if isinstance(_period, (int, float)):
                    _parts.append(f"ریتم={_period:.0f}s")
                if isinstance(_sigma, (int, float)):
                    _parts.append(f"σ={_sigma:.2f}")
                if isinstance(_baro, (int, float)):
                    _parts.append(f"baro={_baro:.1f}")
                if _parts:
                    q += f" قلب: {', '.join(_parts)}."
            elif _sig:   # backward-compat: اگر روزی رشته شد، همان خام
                q += f" قلب: {_sig}."
        except Exception:  # noqa: BLE001 — غنی‌سازی هرگز فکر را نمی‌کشد
            pass
    if focus:
        q += f" تمرکزِ خواسته‌شدهٔ مالک: {str(focus)[:200]}."
    q += " یک جملهٔ کوتاه: الان مهم‌ترین کارِ مجموعه چیست؟"
    r = model_router.ask("think", q, max_tokens=90)
    if r.get("ok"):
        return f"[{r.get('tier')}] {r['text']}"
    return f"[det] {summary}"


def self_improve(cycle: int) -> dict | None:
    """هر IMPROVE_EVERY_N چرخه: حلقهٔ خودارتقایی — ممیزیِ خود + پیشنهادهای دسته‌بندی‌شده.
    propose-only (رأی مالک/قانون)؛ $0؛ fail-soft. خروجی برای state/کابین."""
    try:
        import improve
        d = improve.run(write=True)
        return {"maturity_pct": d.get("maturity_pct"),      # ایستا — پوششِ چک‌لیست
                "checklist_static": d.get("checklist_static"),
                "improvement_rate": d.get("improvement_rate"),
                "n_proposals": d.get("n_proposals"),
                "top": [t.get("title") for t in (d.get("top") or [])[:3]]}
    except Exception as e:  # noqa: BLE001 — خودارتقا نباید مغز را بکشد
        opslib.alert([f"cortex self_improve error: {type(e).__name__}: {e}"])
        return None


def self_model_refresh(cycle: int) -> dict | None:
    """هر IMPROVE_EVERY_N چرخه (لایهٔ فراشناختی جلسه ۴۶): نقشهٔ سورسِ خود را تازه کن —
    «کدِ خودش رو بخونه و درک کنه». $0، read-only، fail-soft."""
    try:
        import self_model
        r = self_model.run_and_persist()
        # VQ-STATE-WRITE-001: ok=False قبلاً بی‌خوانده در cortex-state دفن می‌شد.
        if isinstance(r, dict) and not r.get("ok", False):
            opslib.alert([f"cortex self_model persist FAILED: {r.get('error')}"])
        return r
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex self_model error: {type(e).__name__}: {e}"])
        return None


def part_loops_run(cycle: int) -> dict | None:
    """لوپِ یادگیری+خود-تغییرِ هر بخش (جلسه ۴۶، «برای هر بخش لوپ طرح کن»).
    هر بخش observe→learn→propose؛ propose-only. $0، fail-soft."""
    try:
        import part_loops
        d = part_loops.run_all(beat=cycle)
        bad = [p["name"] for p in d.get("parts", []) if p["status"] in ("🔴", "🟡")]
        return {"n_parts": len(d.get("parts", [])),
                "n_proposals": d.get("n_proposals", 0), "attention": bad[:5]}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex part_loops error: {type(e).__name__}: {e}"])
        return None


def business_brain_run(cycle: int) -> dict | None:
    """مغزِ دومِ عملیاتِ کسب‌وکار (جلسه ۴۶): Lead-نقاشی + Project-F لوپِ درآمدیِ خودشان.
    propose-only؛ Project-F content-free. $0، fail-soft."""
    try:
        import business_brain
        d = business_brain.run_all(beat=cycle)
        return {"n_projects": len(d.get("projects", [])),
                "n_proposals": d.get("n_proposals", 0)}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex business_brain error: {type(e).__name__}: {e}"])
        return None


def _hypothesis_registry_path() -> Path:
    """مسیرِ registry فرضیه (read-only)."""
    return Path(__file__).resolve().parents[2] / "architecture" / "hypothesis-registry.yaml"


def _load_active_hypotheses() -> list:
    """فرضیه‌های فعال را فقط‌خواندن از registry بخوان (propose-only؛ هرگز نمی‌نویسد).
    هر خطا → [] (fail-soft، بدون خراب کردنِ چرخه)."""
    try:
        import yaml  # noqa: E402
        p = _hypothesis_registry_path()
        if not p.is_file():
            return []
        reg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        active = {"SPECULATIVE", "HYPOTHESIZING", "TESTING"}
        return [h for h in reg.get("hypotheses", []) if h.get("status") in active]
    except Exception:  # noqa: BLE001
        return []


def epistemic_tick(cycle: int) -> dict | None:
    """موتور آزمونِ معرفتی (ADR-039، C5): health-checkِ shadowِ کابینِ epistemics.

    پیش‌فرض خاموش (`EPISTEMIC_TESTS=0`). وقتی روشن باشد، فقط آمادگیِ کابین را
    report می‌کند (policy load، receipt-store verify، count invariants) — **هیچ
    claimی از telemetry نمی‌سازد، هیچ آزمونی اجرا نمی‌کند، may_execute همیشه False**.
    این C5 است: مسیرِ زنده‌شدنِ سیم‌کشی، نه خودِ آزمون. آزمونِ واقعی در benchmark
    آفلاین (go_no_go) و فقط بعد از Go criteria.

    fail-soft: هر خطا → alert + None؛ هرگز cycle را نمی‌کشد. الگوی hypothesis_brain_run."""
    if os.environ.get("EPISTEMIC_TESTS", "0") != "1":
        return None
    try:
        # کابینِ epistemics یک package با relative-imports interno است؛ از طریقِ
        # package prefix ایمپورت کن (نه flat) تا receipt_store/pol مماشات نشود.
        import epistemics.invariants as _inv  # noqa: WPS433
        import epistemics.policy as _pol  # noqa: WPS433
        from epistemics.receipt_store import ReceiptStore  # noqa: WPS433
        cfg = _pol.load_policy()
        store = ReceiptStore()
        chain = store.verify()
        return {
            "cycle": cycle,
            "wired": True,
            "policy_schema_version": cfg.schema_version,
            "default_off": cfg.default_off,
            "max_authority": cfg.max_authority,
            "sandbox_profile": cfg.sandbox_profile,
            "invariants_count": _inv.count(),
            "receipt_chain_ok": chain.ok,
            "receipt_chain_n": chain.n_records,
            "may_execute": False,   # hard invariant — هرگز True
            "note": "shadow health-check only; no claim/test executed (C5)",
        }
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex epistemic_tick error: {type(e).__name__}: {e}"])
        return None


def hypothesis_brain_run(cycle: int) -> dict | None:
    """مغز فرضیه (ADR-037): رتبه‌بندیِ فرضیه‌های فعال — propose-only، fail-soft،
    پیش‌فرض خاموش. فقط با CORTEX_HYPOTHESIS=1 روشن می‌شود. هرگز به ledger/Gate/
    autonomy_grant دست نمی‌زند؛ خروجی فقط یک ranking برای کارتِ advisory است.
    کابینِ Pydantic مستقل (hypothesis_engine/impl/) — الگوی ADR-034 (neural→proposal)."""
    if os.environ.get("CORTEX_HYPOTHESIS", "0") != "1":
        return None
    try:
        import asyncio  # noqa: E402
        impl = Path(__file__).resolve().parents[1] / "hypothesis_engine" / "impl"
        if str(impl) not in sys.path:
            sys.path.insert(0, str(impl))
        from hypothesis_brain import HypothesisBrain  # noqa: E402
        hyps = _load_active_hypotheses()
        out = asyncio.run(HypothesisBrain().execute(
            {"op": "prioritize", "hypotheses": hyps}))
        ranked = out.get("ranked", [])
        return {"n_ranked": len(ranked),
                "n_active": len(hyps),
                "n_overflow": out.get("overflow_count", 0),
                "top": ranked[0]["id"] if ranked else None,
                "ranked": ranked}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex hypothesis_brain error: {type(e).__name__}: {e}"])
        return None


def _should_think(cycle: int) -> bool:
    """فکرِ LLM هر THINK_EVERY_N چرخه. پیش‌فرض (۵) = رفتارِ همیشگی، بایت‌به‌بایت؛
    deployِ مالک 2026-07-18 با CORTEX_THINK_EVERY_N=1 یعنی هر چرخه — و چون 1٪1==0،
    خودِ چرخهٔ ۱ هم فکر می‌کند (مغز از لحظهٔ بوت گرم، نه ~۵۰ دقیقه بعد از restart)."""
    return cycle % max(1, THINK_EVERY_N) == 0


def cortisol_tick(cycle: int, stress_summary: dict | None) -> dict | None:
    """OCT-CORTISOL: لحظهٔ ورود به ترس (سطحِ 🔴 یا عضوِ تازه در in_fear) → همان لحظه
    سنتزِ مغز با زمینهٔ هشدار (synthesis.run_and_persist(extra=…)) — مصداقِ «Fugu =
    کورتیزول برای لحظه‌های مهم»، این‌بار واقعاً رویدادمحور نه تایمرِ ۲۴ساعته.

    حاکمیت: خودِ خرج همچنان پشتِ دوقفلهٔ روتر + متر organ_gate؛ این‌جا فقط ماشه +
    همان قفلِ ACTIVATION-WORK-LLM لِینِ پمپ + cooldown (پیش‌فرض ۴h، ماندگار روی دیسک
    تا restart دورش نزند). فقط لبهٔ ورود شلیک می‌کند — ترسِ ماندگار spam نمی‌شود.
    flag خاموش (پیش‌فرض) = دقیقاً رفتارِ امروز. fail-soft: هر خطا فقط alert."""
    if not CORTISOL_EVENTS or not stress_summary:
        return None
    try:
        prev = _read_json(CORTISOL_PATH)
        now_fear = set(stress_summary.get("in_fear") or [])
        prev_fear = set(prev.get("in_fear") or [])
        red_now = "🔴" in str(stress_summary.get("level", ""))
        red_prev = "🔴" in str(prev.get("level", ""))
        new_members = now_fear - prev_fear
        # اولین مشاهده (state تازه، مثلاً wipe یا نصبِ نو) فقط baseline ثبت می‌کند —
        # وگرنه هر بوتِ state-تازه وسطِ ترسِ مزمن = یک تماسِ پولیِ خودکار (بازبینی 07-18).
        entered = bool(prev) and ((red_now and not red_prev) or bool(new_members))
        state = {"ts": opslib.now_iso(), "level": stress_summary.get("level"),
                 "in_fear": sorted(now_fear),
                 "last_fire_ts": float(prev.get("last_fire_ts", 0.0))}
        fired: dict | None = None
        if entered:
            since = time.time() - float(prev.get("last_fire_ts", 0.0))
            gate_ok, gate_why = opslib.live_gate_open(ACT_WORK_LLM)
            if since < CORTISOL_COOLDOWN_S:
                fired = {"fired": False,
                         "reason": f"cooldown {int(since)}s<{int(CORTISOL_COOLDOWN_S)}s"}
            elif not gate_ok:
                fired = {"fired": False, "reason": f"live-locked: {gate_why}"[:120]}
            elif not model_router.paid_gate()[0]:
                # دروازهٔ پولیِ خودِ روتر بسته = شلیک بی‌فایده است (سنتز به محلی/هیچ
                # degrade می‌شد ولی cooldown می‌سوخت) — صادقانه گزارش، بدونِ سوختنِ لبه.
                fired = {"fired": False, "reason": "paid-gate-closed (router)"}
            else:
                # ضدِ رگبارِ بودجه (بازبینی 2026-07-18): اولِ کار slotِ cooldown را
                # اتمیک ثبت کن؛ اگر همین نوشتن شکست بخورد (قفل/AV)، اصلاً شلیک نکن —
                # وگرنه last_fire_ts هرگز ذخیره نمی‌شد و هر چرخه یک تماسِ پولیِ تازه
                # می‌رفت تا تهِ بودجهٔ ارگان (fail-closed برای خرج).
                state["last_fire_ts"] = time.time()
                try:
                    CORTEX_DIR.mkdir(parents=True, exist_ok=True)
                    with opslib.LockedJson(CORTISOL_PATH) as lj:
                        lj.write(state)
                except Exception as e:  # noqa: BLE001
                    opslib.alert([f"cortex cortisol state-write failed پیش از شلیک "
                                  f"(شلیک لغو شد): {type(e).__name__}: {e}"])
                    return {"fired": False, "reason": "state-write-failed (no-spend)"}
                import synthesis
                alarm = ("ورود به ترس: "
                         + (", ".join(sorted(new_members)) or "سطحِ کل")
                         + f" · سطح {stress_summary.get('level')}"
                         + f" · استرس {stress_summary.get('organism_stress')}")
                r = synthesis.run_and_persist(extra={"alarm": alarm})
                return {"fired": True, "trigger": alarm[:120], "ok": r.get("ok"),
                        **({"tier": r.get("tier")} if r.get("tier") else {}),
                        **({"n_proposals": r.get("n_proposals")}
                           if r.get("n_proposals") is not None else {})}
        CORTEX_DIR.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(CORTISOL_PATH) as lj:
            lj.write(state)
        return fired
    except Exception as e:  # noqa: BLE001 — کورتیزول هرگز مغز را نمی‌کشد
        opslib.alert([f"cortex cortisol error: {type(e).__name__}: {e}"])
        return None


def stress_tick(cycle: int) -> dict | None:
    """هومئوستاتِ استرس/ترس هر چرخه (رأی مالک): علائمِ حیاتیِ زیرسیستم‌ها.
    ترس → auto_approve.self_test مکث می‌کند (fail-closed). $0، fail-soft."""
    try:
        import stress
        a = stress.persist()
        return {"level": a["level"], "organism_stress": a["organism_stress"],
                "in_fear": a["in_fear"]}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex stress error: {type(e).__name__}: {e}"])
        return None


def innervation_tick(cycle: int) -> dict | None:
    """نقشهٔ عصب‌کشی هر چرخه (رأی مالک «قلب به تمومِ اندام‌ها وصل باشه، کم‌نقطهٔ مرده»):
    آیا هر اندام beat می‌خورد؟ نقطهٔ مرده → هشدار. $0، fail-soft."""
    try:
        import innervation
        a = innervation.persist()
        return {"coverage_pct": a["coverage_pct"], "dead_spots": a["dead_spots"],
                "heart_period_s": a["heart_period_s"]}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex innervation error: {type(e).__name__}: {e}"])
        return None


def fourd_health_tick(cycle: int) -> dict | None:
    """probe فقط‌خواندنِ 4d_system (ADR-038) — فقط وقتی OCTOPUS_OBSERVE_4D=1.
    صرفاً observability: تازگیِ daemon_state.json را در یک shadow-report می‌نویسد.
    هیچ اتصالِ اجرایی، هیچ import از 4d_system، هیچ write به آن. fail-soft، پیش‌فرض خاموش."""
    try:
        import fourd_health  # noqa: E402
        rec = fourd_health.persist()
        if rec is None:
            return None
        return {"status": rec["status"], "age_s": rec.get("age_s")}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex fourd_health error: {type(e).__name__}: {e}"])
        return None


def ignition_tick(cycle: int) -> dict | None:
    """CORTEX-01 (شعله‌ورشدنِ فضای کاری): فقط با CORTEX_IGNITION=1 برندهٔ winner-take-all
    را COMPUTE + در state-fileِ خودش (ignition-latest.json) LOG کن — SHADOW/مشاهده‌ای.
    هرگز ترتیبِ اجرای اعضا را عوض/skip نمی‌کند (بازچینشِ اجرا رأیِ جداگانهٔ مالک است).
    flag-off → کاملاً skip (byte-identical). $0، fail-soft."""
    if os.environ.get("CORTEX_IGNITION", "0") != "1":
        return None                                   # پیش‌فرض: skip → رفتار دست‌نخورده
    try:
        import ignition
        rec = ignition.persist()                      # خودش هم STOP-aware + flag-gated است
        if rec.get("enabled") is False:               # flag همین‌جا هم دوباره چک شد → no-op
            return None
        if rec.get("halted"):                         # STOP فعال بود → مغز فقط تماشا
            return {"halted": True}
        w = rec.get("winner") or {}
        return {"ignited": rec.get("ignited"), "winner": w.get("source"),
                "broadcast_width": rec.get("broadcast_width"),
                "n_candidates": rec.get("n_candidates")}
    except Exception as e:  # noqa: BLE001 — شعلهٔ سایه هرگز مغز را نمی‌کشد
        opslib.alert([f"cortex ignition error: {type(e).__name__}: {e}"])
        return None


def calibration_tick(cycle: int) -> dict | None:
    """CORTEX-03 (خود-پایشِ واسنجی): فقط با CORTEX_SELF_MONITOR روشن، ادعاهای اخیرِ خود را
    با لِجِرِ بیرونی بسنج (Brier/AURC) و snapshot را زیرِ STATE_DIR بنویس — مشاهده‌ای،
    بی‌اثرِ زنده. flag-off → skip. $0، fail-soft."""
    v = str(os.environ.get("CORTEX_SELF_MONITOR", "")).strip().lower()
    if v in ("", "0", "false", "no", "off"):
        return None
    try:
        import calibration_probe
        d = calibration_probe.probe()                 # نوشتن را خودش با همین flag گیت می‌کند
        return {"n": d.get("n"), "brier": d.get("brier"),
                "aurc": d.get("aurc"), "ungraded": d.get("ungraded")}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex calibration error: {type(e).__name__}: {e}"])
        return None


def consolidate_tick(cycle: int) -> dict | None:
    """CORTEX-04 (تثبیتِ حافظه): فقط با CORTEX_CONSOLIDATE=1 یک دورِ tail→نوتِ سِمانتیک را
    اجرا کن (idempotent با cursor؛ فقط زیرِ STATE_DIR). flag-off → no-op مطلق/skip.
    $0، fail-soft."""
    if os.environ.get("CORTEX_CONSOLIDATE", "0") != "1":
        return None
    try:
        import consolidate
        d = consolidate.consolidate_once()
        if not d.get("flag"):
            return None
        return {"n_in": d.get("n_in"), "n_semantic": d.get("n_semantic"),
                "archived": d.get("archived")}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex consolidate error: {type(e).__name__}: {e}"])
        return None


def softwta_tick(cycle: int) -> dict | None:
    """CORTEX-05 (مقایسهٔ سایهٔ soft-WTA): فقط با IGNITION_SOFT_WTA_SHADOW=1 برندهٔ منطقِ
    فعلی را در برابرِ soft-WTA بسنج و رکوردِ سایه را append کن — رفتارِ زنده در هر حالت
    همان مسیرِ فعلی می‌ماند (این تابع هیچ مسیرِ زنده‌ای را عوض نمی‌کند). flag-off → skip.
    $0، fail-soft."""
    if os.environ.get("IGNITION_SOFT_WTA_SHADOW", "0") != "1":
        return None
    try:
        import ignition_softwta
        rec = ignition_softwta.shadow_compare()
        return {"winner_current": rec.get("winner_current"),
                "winner_soft_wta_shadow": rec.get("winner_soft_wta_shadow"),
                "disagreement": rec.get("disagreement"),
                "n_candidates": rec.get("n_candidates")}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex softwta error: {type(e).__name__}: {e}"])
        return None


_obs_last_alert = 0.0


def obs_alert_check(sweep: dict) -> None:
    """RC3: مغز می‌داند مریض است ولی کسی خبردار نمی‌شود. اگر coherence افت کند یا اعضای
    کهنه از حد بگذرند، به governor-alerts.md خبر بده (تبِ /alerts). flag-gated (OBS_ALERT)،
    throttle ساعتی، fail-soft — هرگز چرخه را نمی‌شکند."""
    if not OBS_ALERT:
        return
    global _obs_last_alert
    try:
        coherence = float(sweep.get("coherence", 1.0))
        stale = list(sweep.get("stale_members") or [])
        problems = []
        if coherence < OBS_COHERENCE_MIN:
            problems.append(f"coherence={coherence} < {OBS_COHERENCE_MIN}")
        if len(stale) > OBS_STALE_MAX:
            problems.append(f"{len(stale)} stale > {OBS_STALE_MAX}: {','.join(stale)}")
        if not problems:
            return
        now = time.time()
        if now - _obs_last_alert < OBS_ALERT_EVERY_S:
            return
        _obs_last_alert = now
        opslib.alert(["cortex obs: " + p for p in problems])
    except Exception:  # noqa: BLE001
        pass


_last_truth_sync = 0.0


def truth_sync_tick(sweep: dict) -> dict | None:
    """CORTEX-06 (احیای CURRENT-TRUTH.md، ۲۰۲۶-۰۸-۰۶ — رأیِ مالک «موافقم با تمومِ
    تصمیماتت، انجامشون بده»): فقط با OCTOPUS_WIRE_TRUTH_SYNC=1، اسنپ‌شاتِ مکانیکیِ
    وضعِ ارگانیسم را در OCTOPUS/CURRENT-TRUTH.md به‌روز می‌کند.

    چرا این‌جا: نویسندهٔ فرمت (`intel_spine.obsidian_sync.sync_truth_note`) از قبل
    ساخته/تست‌شده بود ولی صفر صداکننده داشت — فایل از ۲۰۲۶-۰۸-۰۴ ۲۳:۳۲ ایستاده بود
    (جزئیات: 07 - Knowledge/شناخت-اختاپوس/15-SELF-REPORTED-ISSUES-SWEEP-2026-08-06.md).
    نوشتن marker-محور است (`safe_update_note`) و **هرگز** محتوای دستی را overwrite
    نمی‌کند؛ خودِ این فایل تماماً auto-generated است (بلوکِ `OCTOPUS-AUTO-START/END`
    کلِ بدنه را می‌گیرد)، پس این جایگزینی امن‌ترین نوعِ اثرِ نوشتاری در این فایل است.

    ریتم: هر ≥TRUTH_SYNC_MIN_S (پیش‌فرض ۱۸۰۰ = ۳۰د)، سنجیده روی زمانِ حافظه‌ایِ آخرین
    تلاش — نه mtime ِ خودِ فایل (نوشتنِ ناموفق/غایب نباید هر چرخه دوباره تلاش کند و
    نه اینکه هرگز retry نکند). دورهٔ cortex بینِ ۶۰..۶۰۰s شناور است، پس شمارشِ چرخه
    ریتمِ واقعی‌ای نمی‌داد. flag-off یا هر خطا → skip بی‌صدا (alert-شده)، هرگز چرخه
    را نمی‌کشد. $0، read-only بجز همین یک نوت — همان چهار فیلد از `sweep` که
    align_work_plan/obs_alert_check هم می‌خوانند، صفر منبعِ نو."""
    global _last_truth_sync
    if os.environ.get("OCTOPUS_WIRE_TRUTH_SYNC", "0") != "1":
        return None
    min_s = float(os.environ.get("TRUTH_SYNC_MIN_S", "1800"))
    now = time.time()
    if now - _last_truth_sync < min_s:
        return {"skipped": "cooldown", "next_in_s": round(min_s - (now - _last_truth_sync), 1)}
    _last_truth_sync = now
    try:
        data = {"coherence": round(float(sweep.get("coherence", 0.0)), 3),
                "members_present": sum(1 for m in (sweep.get("members") or [])
                                       if m.get("present")),
                "stale_members": ", ".join(sweep.get("stale_members") or []) or "هیچ"}
        try:
            org = _read_json(opslib.STATE_DIR / "ORGANISM-STATE.json")
            data["beat"] = org.get("beat", "؟")
            data["halted"] = bool(org.get("halted"))
        except Exception:  # noqa: BLE001
            pass
        try:
            # ⚠️ عمداً `_read_json` (fail-soft) استفاده نمی‌شود: آن روی هر خطا `{}`
            # برمی‌گرداند و اینجا با «صفر پیشنهادِ معطلِ واقعی» یکی می‌شد — همان دامِ
            # «نبودِ داده = حکم» که این جلسه چند بار جایِ دیگر گرفته شده. فایلِ
            # ناخوانا/غایب ⇒ کلید اصلاً در نوت ظاهر نمی‌شود؛ صفرِ واقعی هم صفر می‌ماند.
            rfcs_path = opslib.STATE_DIR / "doctor" / "rfcs.json"
            rf = json.loads(rfcs_path.read_text("utf-8")).get("rfcs") or []
            data["rfcs_pending"] = sum(1 for r in rf if r.get("status") in ("submitted", "drafted"))
        except Exception:  # noqa: BLE001
            pass
        try:
            import subprocess
            head = subprocess.run(
                ["git", "-C", str(opslib.ORG_ROOT), "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5).stdout.strip()
            if head:
                data["HEAD"] = head
        except Exception:  # noqa: BLE001
            pass
        _ops_dir = str(_HERE.parent)
        if _ops_dir not in sys.path:
            sys.path.insert(0, _ops_dir)
        from intel_spine import obsidian_sync
        wrote = obsidian_sync.sync_truth_note(opslib.ORG_ROOT, data)
        return {"wrote": bool(wrote), "keys": list(data.keys())}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex truth_sync error: {type(e).__name__}: {e}"])
        return None


def run_cycle(cycle: int) -> dict:
    # 3b (2026-07-24): steeringِ boundedِ مالک — فقط خواندنِ state-file (این پروسه هرگز
    # bot/poller نمی‌سازد؛ ضدِ 409). directiveهای بسته: focus / think_every_n / paused.
    guid = {}
    try:
        import owner_guidance as _og
        guid = _og.effective() or {}
    except Exception:  # noqa: BLE001
        guid = {}
    sweep = registry.sweep()
    alignment = align_work_plan(sweep)
    stress_summary = stress_tick(cycle)
    cortisol_summary = cortisol_tick(cycle, stress_summary)
    innervation_summary = innervation_tick(cycle)
    fourd_health_summary = fourd_health_tick(cycle)
    ignition_summary = ignition_tick(cycle)
    calibration_summary = calibration_tick(cycle)
    consolidate_summary = consolidate_tick(cycle)
    softwta_summary = softwta_tick(cycle)
    truth_sync_summary = truth_sync_tick(sweep)
    _ten = guid.get("think_every_n")
    _think_now = (cycle % max(1, int(_ten)) == 0) if _ten else _should_think(cycle)
    if guid.get("paused"):
        _think_now = False   # pause: think — فکرِ LLM خاموش؛ خلاصهٔ قطعی می‌ماند ($0)
    thought = think(sweep, cycle, focus=guid.get("focus")) if _think_now else None
    model_summary = (self_model_refresh(cycle)
                     if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    parts_summary = (part_loops_run(cycle)
                     if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    business_summary = (business_brain_run(cycle)
                        if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    hypothesis_summary = (hypothesis_brain_run(cycle)
                          if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    epistemic_summary = (epistemic_tick(cycle)
                         if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    improve_summary = (self_improve(cycle)
                       if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    period, rhythm_src = heart_rhythm_period()
    state = {
        "ts": opslib.now_iso(), "cycle": cycle,
        "coherence": sweep["coherence"],
        "stale_members": sweep["stale_members"],
        "members": sweep["members"],
        "alignment": alignment,
        "rhythm": {"period_s": period, "source": rhythm_src},
        "brains": {"keys": model_router.keys_present(),
                   "paid_gate": model_router.paid_gate()[1],
                   "local_model": os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")},
        **({"thought": thought} if thought else {}),
        **({"self_improve": improve_summary} if improve_summary else {}),
        **({"self_model": model_summary} if model_summary else {}),
        **({"part_loops": parts_summary} if parts_summary else {}),
        **({"business_brain": business_summary} if business_summary else {}),
        **({"hypothesis_brain": hypothesis_summary} if hypothesis_summary else {}),
        **({"epistemic_tick": epistemic_summary} if epistemic_summary else {}),
        **({"stress": stress_summary} if stress_summary else {}),
        **({"cortisol": cortisol_summary} if cortisol_summary else {}),
        **({"innervation": innervation_summary} if innervation_summary else {}),
        **({"fourd_health": fourd_health_summary} if fourd_health_summary else {}),
        **({"ignition": ignition_summary} if ignition_summary else {}),
        **({"calibration": calibration_summary} if calibration_summary else {}),
        **({"consolidate": consolidate_summary} if consolidate_summary else {}),
        **({"softwta": softwta_summary} if softwta_summary else {}),
        **({"truth_sync": truth_sync_summary} if truth_sync_summary else {}),
        **({"owner_guidance": guid} if guid else {}),
        "schema": "cortex-state.v1",
    }
    CORTEX_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with opslib.LockedJson(STATE_PATH) as lj:
            lj.write(state)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex state write failed: {e}"])
    # P7 (truth-map 2026-07-17): «aligned» نامِ گمراه‌کننده بود — مقدارِ changed را حمل
    # می‌کرد (false = حالتِ سالمِ «هم‌راستا بود»، ولی blocked/خطا هم همین را می‌نوشت).
    # هر دو واقعیت journal می‌شود؛ کلیدِ قدیمی برای سازگاریِ مصرف‌کننده‌ها می‌ماند.
    # W3 (2026-07-25): P7 فقط دو کلیدِ نو *اضافه* کرد و خودِ aligned را همچنان از
    # changed می‌خواند → ژورنال هر چرخه خودش را نقض می‌کرد («aligned»: false کنارِ
    # align_reason=«هم‌راستا بود»). حالا aligned واقعیتِ خودش را از align_work_plan
    # می‌گیرد: «نقشه الان هم‌راستاست؟» — نه «این چرخه عوض شد؟».
    # jschema رکوردهای پس از فیکس را از رکوردهای قدیمیِ همان فایل (معناشناسیِ کهنه)
    # جدا می‌کند؛ ژورنال append-only است و تاریخ بازنویسی نمی‌شود.
    rec = {"ts": state["ts"], "cycle": cycle,
           "jschema": "cortex-journal.v2",
           "coherence": sweep["coherence"],
           "aligned": bool(alignment.get("aligned", False)),
           "align_changed": bool(alignment.get("changed", False)),
           "align_reason": str(alignment.get("reason", ""))[:120],
           **({"diff": alignment.get("diff")} if alignment.get("changed") else {}),
           **({"thought": thought} if thought else {})}
    try:
        opslib.append_jsonl(JOURNAL_PATH, rec)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex journal failed: {e}"])
    obs_alert_check(sweep)
    return state


def _redact(text: str) -> str:
    """INV-12: پاسخِ خطای HTTP خام نباید باشد — `/ask` به providerهای پولی
    می‌رسد (FUGU/GLM/DEEPSEEK_API_KEY) و یک استثنایِ شبکه‌ای می‌تواند کلید
    را در متنِ خطا حمل کند. اگر لایهٔ اصلی در دسترس نبود، fail-closed:
    جایگزینِ امن، نه متنِ خام (هم‌الگویِ live/server.py)."""
    try:
        import cockpit_readmodel as crm
        return crm.redact(text)
    except Exception:  # noqa: BLE001
        return "⚠️ محتوا حذف شد — لایهٔ redaction در دسترس نبود"


class _Srv(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/cortex":
            self._send(200, STATE_PATH.read_bytes() if STATE_PATH.exists() else b"{}")
            return
        if self.path.startswith("/api/journal"):
            lines = []
            try:
                if JOURNAL_PATH.exists():
                    lines = JOURNAL_PATH.read_text("utf-8").splitlines()[-20:]
            except OSError:
                pass
            self._send(200, ("[" + ",".join(lines) + "]").encode("utf-8"))
            return
        if self.path == "/":
            st = _read_json(STATE_PATH)
            html = ("<!doctype html><html dir='rtl' lang='fa'><meta charset='utf-8'>"
                    "<title>Cortex</title><body style='font-family:Tahoma;padding:2em'>"
                    "<h2>🧠 مغزِ مرکزی</h2>"
                    f"<pre style='direction:ltr;text-align:left'>"
                    f"{json.dumps(st, ensure_ascii=False, indent=2)}</pre>"
                    "<p>API: /api/cortex · /api/journal · POST /ask</p></body></html>")
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        self._send(404, b"{}")

    def do_POST(self):  # noqa: N802
        import sys as _s, os as _o
        _p = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
        if _p not in _s.path:
            _s.path.insert(0, _p)
        try:
            import httpauth as _ha  # RC1: گاردِ CSRF/Origin پشتِ OCTOPUS_HTTP_AUTH
            if not _ha.guard_post(self):
                return
        except Exception:  # noqa: BLE001
            # P1 (2026-07-20 Stage-1): گارد در دسترس نبود → secure-by-default fail-closed
            # (503) مگر صریحاً خاموش (OCTOPUS_HTTP_AUTH=0/false/no/off).
            import os as _os_fc
            if str(_os_fc.environ.get("OCTOPUS_HTTP_AUTH", "1")).strip().lower() not in (
                    "0", "false", "no", "off"):
                try:
                    self._send(503, b'{"ok":false,"reason":"http guard unavailable (fail-closed)"}')
                except Exception:  # noqa: BLE001
                    pass
                return
        if self.path != "/ask":
            self._send(404, b"{}")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            task = str(body.get("task", "daily"))[:40]
            prompt = str(body.get("prompt", ""))[:4000]
            out = model_router.ask(task, prompt,
                                   max_tokens=int(body.get("max_tokens", 300)))
            self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"))
        except Exception as e:  # noqa: BLE001
            self._send(500, _redact(json.dumps({"ok": False, "reason": str(e)},
                                                ensure_ascii=False)).encode("utf-8"))

    def log_message(self, *a):
        pass


def main() -> int:
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    try:
        srv = _Srv(("127.0.0.1", PORT), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except OSError:
        print(f"cortex: نمونهٔ دیگری روی {PORT} زنده است — خروجِ تمیز.")
        return 0
    print(f"cortex: زنده روی http://127.0.0.1:{PORT} — kill تمیز: فایل _ops/STOP-CORTEX")
    opslib.heartbeat(f"cortex=START port={PORT}")
    # عکسِ envِ همین پروسه سرِ boot (رأیِ مالک ۲۰۲۶-۰۷-۲۹). append نه insert،
    # تا هیچ ماژولی سایه نیفتد. fail-soft مطلق و بدونِ اثرِ رفتاری.
    try:
        _ops_dir = str(_HERE.parent)
        if _ops_dir not in sys.path:
            sys.path.append(_ops_dir)
        import flag_drift
        flag_drift.snapshot_boot("cortex")
    except Exception:  # noqa: BLE001
        pass
    cycle = 0
    while True:
        if STOP_CORTEX.exists() or opslib.master_halted():
            opslib.heartbeat("cortex=HALT (STOP) — خروجِ تمیز")
            return 0
        cycle += 1
        try:
            run_cycle(cycle)
        except Exception as e:  # noqa: BLE001 — خطای خاموش ممنوع، مرگِ حلقه هم ممنوع
            opslib.alert([f"cortex cycle error: {type(e).__name__}: {e}"])
        # بازبینیِ خصمانه 2026-07-17: این تماس بیرونِ try بود — یک period_sِ آلودهٔ
        # غیرعددی، دیمنِ کورتکس (تنها مانیتورِ مستقلِ مرگِ ارگانیسم) را می‌کشت.
        try:
            period, _ = heart_rhythm_period()
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"cortex heart_rhythm_period error: {type(e).__name__}: {e}"])
            period = 600.0
        time.sleep(period)


if __name__ == "__main__":
    sys.exit(main())
