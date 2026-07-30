#!/usr/bin/env python3
"""watchdog.py — Phase 5 · S-1: watchdogِ کد (revive-after-death، نه persistence-fight).

اصلِ LifeDoctrine §۴: «You fight to keep Octopus alive. Octopus never fights to stay
alive.» watchdog = ابزارِ مالک برای زنده‌کردن، نه خودِ سیستم برای مقاومت.
kill-switch مطلق: watchdog بی‌قیدوشرط تسلیمِ هر STOP می‌شود (persistence نه resistance).

تولدِ owner-launched: watchdog فقط REVIVE می‌کند — هرگز first-birth. اولین/تشریفاتی
راه‌اندازی فقط Scheduled Task/at-logonِ تأییدِ مالک (هرگز از شلِ ایجنت — INC-1).

منطق (آزمون‌پذیر، $0 آفلاین):
  should_revive(port_alive, stop_flags, state_exists, beat_stale) → bool
    True فقط اگر: port مرده ∧ هیچ stop-flag نیست ∧ state وجود دارد (شواهدِ اجرای قبلی)
    False در غیر اینصورت — به‌ویژه: هر STOP = False (yield).
  monitor(...) → dict   شاهدِ کاملِ نظارت (پورت AND تازگیِ ts AND پیشرویِ beat).
  notify([...])         صداکردنِ مالک روی opslib.alert — fail-soft مطلق.

⚠️ مرزِ صداقتِ استقرار (اندازه‌گیریِ 2026-07-30 با Get-ScheduledTask):
   تسکِ ثبت‌شدهٔ `organism-watchdog` فایلِ «04 - Architect System/scripts/
   organism-watchdog.ps1» را می‌دواند — نه `_ops/organism-watchdog.ps1`. آن نسخه
   منطقِ inlineِ خودش را دارد و **صفر** ارجاع به watchdog.py؛ پس هیچ‌چیز در تولید
   این ماژول را برای organism صدا نمی‌زند و تشخیصِ استالِ organism در تولید
   **اجرا نمی‌شود**. تنها مسیرِ تولیدیِ همین ماژول، `--alert` است که سه تسکِ
   ثبت‌شدهٔ دیگر (cortex/live/tg-center) صدا می‌زنند. re-pointکردنِ آن تسک یا
   ویرایشِ آن نسخه owner-gated است (SPLIT-BRAIN NOTE، ثبتِ دومی ممنوع).

PS1 موجود (organism-watchdog.ps1) همین منطق را دارد ولی آزمون‌پذیر نیست. این ماژول
قراردادِ testable را استخراج می‌کند؛ PS1 می‌تواند آن را صدا بزند (یا مالک مستقیم).
additive؛ stdlib-only.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent              # _ops
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402

# پرچم‌های STOP (kill-switch مطلق — هرکدام = yield). ترتیب بررسی مهم نیست چون همه yield.
# D-G (2026-07-20): HALT-ALL افزوده شد — watchdog دیگر زیرِ پنیکِ سراسری احیا نمی‌کند
# (پیش‌تر فقط architect-STOP و STOP-ORGANISM را می‌دید؛ HALT-ALL بی‌اثر بود).
STOP_FLAGS = [
    opslib.HALT_ALL,                     # 🔴 پنیکِ سراسری (HALT-ALL) — MUST yield
    opslib.STOP_ARCHITECT,               # architect-level — canonical «04 - Architect System/STOP»
    opslib.STOP_ORGANISM,                # organism-level
]
# BLOCKER-3 (split-brain STOP): پیش‌تر اینجا `_HERE.parent / "STOP"` (= ریشهٔ
# F:\backup\STOP) بود که با مسیرِ canonicalِ opslib/loopها (`04 - Architect System/
# STOP`) واگرا بود؛ STOP معمار روی مسیرِ درست، watchdog را متوقف نمی‌کرد →
# boot-and-exit churn. حالا همه به `opslib.STOP_ARCHITECT` نشانه می‌روند.
ORGANISM_PORT = 8771
STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"

# ─── C-watchdog (2026-07-30): مرگِ خاموش — پروب فقط پورت را می‌دید ───────────────
# سوکتِ باز ≠ حلقهٔ زنده. اگر حلقهٔ درون-پروسه بایستد ولی listener باز بماند،
# پروبِ پورت «سالم» می‌گوید و مرگ **نامرئی** است. پس تازگیِ ضربان با پورت AND می‌شود.
#
# چرا ORGANISM-STATE.json و نه beat_scheduler.heartbeat_health؟ آن تابع
# `state/pulse/beat-state.json` را می‌خواند که فقط زیرِ OCTOPUS_ONE_HEARTBEAT نوشته
# می‌شود و آن فلگ shadow-first/خاموش است ⇒ فایل در درختِ زنده **وجود ندارد** و
# heartbeat_health روی ارگانیسمِ کاملاً سالم stall=True می‌دهد (اندازه‌گیری‌شده
# 2026-07-30، همان لحظه که beat=18413 و ts فقط ۲۸s کهنه بود) — یعنی false-positive
# و طوفانِ revive. ORGANISM-STATE.json هر beat بازنویسی می‌شود (`ts` + `beat`) و
# تنها مصنوعِ ضربانِ واقعاً به‌روز است. `_memory/HEARTBEAT.md` هم رد شد: مصنوعِ
# تسک‌های ratified است نه حلقه (همان لحظه ~۴۹ دقیقه کهنه بود).
BEAT_STALL_AFTER_S = 900.0     # همان کفِ heartbeat_health(stall_after_s=900)
# احیا وقتی پورت **باز** است = لانچِ دومی روی سوکتِ bind-شده ⇒ رفتاریِ خطرناک،
# پس پیش‌فرض خاموش. تشخیص + alert همیشه روشن‌اند؛ فقط خودِ احیا owner-gated است.
STALL_REVIVE_FLAG = "OCTOPUS_WATCHDOG_STALL_REVIVE"
# ─── مسیرِ واقعیِ مسلح‌کردن («مسلح ولی اثبات‌ناپذیر»، 2026-07-30) ───────────────
# هر چهار watchdog، Scheduled Taskِ مستقل‌اند و **هیچ‌کدام** OCTOPUS-flags.cmd را
# source نمی‌کنند؛ پس ویرایشِ آن فایل هرگز این فلگ را در محیطِ آنها روشن نمی‌کند و
# «فلگ را مسلح کردم» اثبات‌ناپذیر می‌ماند. مسیرِ مسلح‌کردنی که واقعاً به یک
# Scheduled Task می‌رسد = فایلِ نشانه روی دیسک — همان اصطلاحی که مالک برای
# STOP-ORGANISM/HALT-ALL دارد و همین ماژول می‌خواند:
#     وجود داشتن → مسلح          نبودن → خاموش (پیش‌فرض، و پیش‌فرض درست است)
# مسلح (فقط مالک): New-Item -ItemType File "F:\backup\_ops\WATCHDOG-STALL-REVIVE"
# خلع سلاح:        Remove-Item "F:\backup\_ops\WATCHDOG-STALL-REVIVE"
STALL_REVIVE_ARM_FILE = opslib.OPS / "WATCHDOG-STALL-REVIVE"
# حافظهٔ خودِ watchdog برای «شمارندهٔ beat جلو می‌رود یا یخ زده».
# چرا لازم است: تازگیِ `ts` تنها کافی **نیست**. organism._write_state همیشه
# `ts` را نو می‌کند و handlerِ خطای حلقه (organism.py:1173) با merge_prev=True
# فقط کلیدهای غایب را از prev back-fill می‌کند ⇒ ارگانیسمی که روی exception
# می‌چرخد و پورتش باز است، `ts` تازه و `beat` **یخ‌زده** دارد؛ چکِ ts-only
# هرگز شلیک نمی‌کرد. مونوتونیکِ beat همین حالت را می‌گیرد.
BEAT_MARK_FILE = opslib.STATE_DIR / "watchdog-beat-mark.json"
# سطل‌های درشتِ سن برای متنِ alert. چرا: opslib.alert امضا را از **متنِ joined**
# هش می‌کند؛ هر عددِ متغیر در متن (age=1234s) امضا را در هر اجرا نو می‌کند ⇒
# count همیشه ۱، پنجرهٔ ۶ساعته و نشانه‌های escalation هرگز درگیر نمی‌شوند و با
# کیدنسِ ۵دقیقه‌ای تا ۲۸۸ آلارمِ throttle-نشده در روز می‌شود (همان اشتباهِ
# ثبت‌شدهٔ این repo: «شمارنده در کلیدِ dedup»). پس: جملهٔ ثابت + سطلِ درشت.
_AGE_BUCKET_EDGES = (900, 1800, 3600, 21600, 86400)


def _flag_on(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "on")


def _age_bucket(age_s: float | None) -> str:
    """سنِ درشت‌شده — دامنهٔ متنِ alert کراندار می‌شود (حداکثر ۷ مقدار)."""
    if age_s is None:
        return "age=unknown"
    try:
        a = float(age_s)
    except (TypeError, ValueError):
        return "age=unknown"
    for edge in _AGE_BUCKET_EDGES:
        if a <= edge:
            return f"age<={edge}s"
    return f"age>{_AGE_BUCKET_EDGES[-1]}s"


def _stall_revive_armed(arm_file: Path | None = None) -> bool:
    """آیا احیای روی استال مسلح است؟ env **یا** فایلِ نشانهٔ مالک. پیش‌فرض: خیر.

    env برای تست/اجرای دستی است؛ فایلِ نشانه تنها مسیری است که به یک Scheduled
    Task هم می‌رسد (رجوع به کامنتِ STALL_REVIVE_ARM_FILE)."""
    if _flag_on(STALL_REVIVE_FLAG):
        return True
    p = STALL_REVIVE_ARM_FILE if arm_file is None else Path(arm_file)
    try:
        return p.exists()
    except OSError:      # fail-safe: بی‌خبری = خاموش (هرگز مسلحِ کاذب)
        return False


def _beat_ts(state_file: Path) -> tuple[float | None, int | None, str]:
    """(epochِ آخرین ضربان، شمارندهٔ beat، منبع) — fail-soft، هرگز raise."""
    try:
        d = json.loads(state_file.read_text("utf-8"))
    except Exception:  # noqa: BLE001 — نیمه-نوشته/خراب = بی‌خبری، نه سلامت
        try:
            return state_file.stat().st_mtime, None, "mtime (state unreadable)"
        except OSError:
            return None, None, "unreadable"
    beat = d.get("beat") if isinstance(d.get("beat"), int) else None
    try:
        return datetime.fromisoformat(str(d.get("ts") or "").strip()).timestamp(), beat, "state.ts"
    except (TypeError, ValueError):
        pass
    try:
        return state_file.stat().st_mtime, beat, "mtime (ts unparsable)"
    except OSError:
        return None, beat, "no-timestamp"


def beat_health(state_file=None, now: float | None = None,
                stall_after_s: float | None = None,
                age_s: float | None = None) -> dict:
    """تازگیِ ضربان: {evidence, age_s, beat, stall, source, reason}.

    ناوردی: **غیابِ شاهد هرگز stall نمی‌سازد.** فایلِ نبودن = «شاهدی ندارم»
    (first-birth guard جداگانه آن را می‌گیرد)؛ اگر absence را stall بگیریم هر
    درختِ تازه و هر tmp-treeِ تست یک احیا/آلارمِ کاذب می‌گیرد."""
    limit = BEAT_STALL_AFTER_S if stall_after_s is None else float(stall_after_s)
    beat, source = None, "injected"
    if age_s is None:
        p = Path(state_file) if state_file else STATE_FILE
        if not p.exists():
            return {"evidence": False, "age_s": None, "beat": None, "stall": False,
                    "source": "absent", "limit_s": limit,
                    "reason": "no beat evidence (state file absent)"}
        ts, beat, source = _beat_ts(p)
        if ts is None:
            return {"evidence": False, "age_s": None, "beat": beat, "stall": False,
                    "source": source, "limit_s": limit,
                    "reason": f"no beat evidence ({source})"}
        age_s = (time.time() if now is None else float(now)) - float(ts)
    age_s = round(float(age_s), 1)
    stall = age_s > limit
    return {"evidence": True, "age_s": age_s, "beat": beat, "stall": stall,
            "source": source, "limit_s": limit,
            "reason": (f"beat stale: {age_s}s > {limit}s" if stall
                       else f"beat fresh: {age_s}s")}


def beat_progress(beat: int | None, now: float | None = None,
                  mark_file: Path | None = None,
                  stall_after_s: float | None = None,
                  persist: bool = True) -> dict:
    """آیا شمارندهٔ beat جلو می‌رود؟ {evidence, beat, prev_beat, frozen, frozen_age_s}.

    این تنها چکی است که «ارگانیسمِ چرخنده روی exception» را می‌گیرد: آن حالت
    `ts` را تازه نگه می‌دارد (organism._write_state همیشه ts می‌نویسد) و فقط
    `beat` را یخ می‌زند، پس چکِ ts-only روی آن **کور** است.

    برای «یخ‌زده بودن» حافظه لازم است، پس این تابع تنها side-effectِ ماژول را
    دارد: یک فایلِ نشانهٔ کوچک (BEAT_MARK_FILE). persist=False آن را خاموش می‌کند.
    ناوردی: **غیابِ شاهد هرگز frozen نمی‌سازد** (beat=None ⇒ evidence=False)؛ و
    هر *تغییرِ* beat (حتی کاهش، یعنی restart) ساعت را از نو صفر می‌کند."""
    limit = BEAT_STALL_AFTER_S if stall_after_s is None else float(stall_after_s)
    t = time.time() if now is None else float(now)
    if not isinstance(beat, int) or isinstance(beat, bool):
        return {"evidence": False, "beat": None, "prev_beat": None, "frozen": False,
                "frozen_age_s": None, "limit_s": limit,
                "reason": "no beat counter (absence is never a stall)"}
    p = BEAT_MARK_FILE if mark_file is None else Path(mark_file)
    prev_beat, since = None, None
    try:
        d = json.loads(p.read_text("utf-8"))
        if isinstance(d, dict):
            if isinstance(d.get("beat"), int) and not isinstance(d.get("beat"), bool):
                prev_beat = d["beat"]
            since = float(d["since"]) if d.get("since") is not None else None
    except Exception:  # noqa: BLE001 — نشانهٔ نبود/خراب = «اولین مشاهده»، نه استال
        prev_beat, since = None, None
    fresh_observation = prev_beat is None or prev_beat != beat or since is None
    if fresh_observation:
        since = t
    frozen_age = max(0.0, t - float(since))
    frozen = (not fresh_observation) and frozen_age > limit
    if persist:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"beat": beat, "since": since, "seen": t}),
                         "utf-8")
        except OSError:  # نتوانستیم به‌یاد بسپاریم؛ نظارت نباید بمیرد
            pass
    if frozen:
        reason = f"beat counter FROZEN at {beat} for {round(frozen_age, 1)}s > {limit}s"
    elif fresh_observation and prev_beat is None:
        reason = f"first observation of beat {beat}"
    elif fresh_observation:
        reason = f"beat moved {prev_beat} → {beat}"
    else:
        reason = f"beat unchanged at {beat} for {round(frozen_age, 1)}s (within {limit}s)"
    return {"evidence": True, "beat": beat, "prev_beat": prev_beat, "frozen": frozen,
            "frozen_age_s": round(frozen_age, 1), "limit_s": limit, "reason": reason}


def _stall_verdict(now: float | None = None, health: dict | None = None,
                   progress: dict | None = None) -> tuple[bool, list[str], dict, dict]:
    """(stale?, causes, health, progress) — تک‌منبعِ ترکیبِ دو سیگنالِ استال."""
    h = health if health is not None else beat_health(now=now)
    prog = progress if progress is not None else beat_progress(h.get("beat"), now=now)
    causes = []
    if h.get("stall"):
        causes.append("ts-stale")
    if prog.get("frozen"):
        causes.append("beat-frozen")
    return bool(causes), causes, h, prog


def should_revive(port_alive: bool | None = None,
                  stop_flags: list[Path] | None = None,
                  state_exists: bool | None = None,
                  beat_stale: bool | None = None) -> tuple[bool, str]:
    """آیا باید revive شود؟ (همهٔ ورودی‌ها قابل‌تزریق برای تستِ hermetic).
    خروجی: (should, reason). هر STOP = (False, yield-reason).

    LifeDoctrine §۴: revive = ابزارِ مالک، نه self-preservationِ سیستم.
    تولدِ owner-launched: اگر state_exists نباشد (اولین بار) → False (first-birth با مالک)."""
    flags = stop_flags if stop_flags is not None else STOP_FLAGS
    # 1) kill-switch مطلق — FIRST check
    for flag in flags:
        if flag.exists():
            return False, f"yield: STOP flag present ({flag.name})"
    # 2) پورتِ باز → زنده، **مگر** ضربان کهنه باشد (استالِ درون-پروسه = مرگِ خاموش)
    if port_alive is None:
        port_alive = _port_alive(ORGANISM_PORT)
    if port_alive:
        if beat_stale is None:
            beat_stale = _stall_verdict()[0]
        if beat_stale:
            if _stall_revive_armed():
                return True, ("revive: STALL — port open but beat stale "
                              "(in-process loop dead)")
            # «alive» در متن می‌ماند تا گاردهای موجود (test_d4/test_phase5) نشکنند،
            # ولی STALL صریح است و revive_action روی همین حالت alert می‌زند.
            return False, ("alive: port open but beat STALE — stall detected, "
                           f"revive disarmed ({STALL_REVIVE_FLAG}=0)")
        return False, "alive: organism running"
    # 3) first-birth guard: only revive, never first-launch
    if state_exists is None:
        state_exists = STATE_FILE.exists()
    if not state_exists:
        return False, "no-prior-run: first-birth is owner-only (INC-1)"
    # 4) revive
    return True, "revive: port dead, no STOP, prior run exists"


def _port_alive(port: int, host: str = "127.0.0.1", timeout: float = 1.5) -> bool:
    """چکِ زنده‌بودنِ پورت (bind انحصاری = lockِ liveness). fail-soft: خطا = مرده."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def monitor(port_alive: bool | None = None,
            stop_flags: list[Path] | None = None,
            state_exists: bool | None = None,
            beat_stale: bool | None = None,
            health: dict | None = None,
            progress: dict | None = None,
            now: float | None = None) -> dict:
    """گزارشِ کاملِ نظارت — تک‌منبعِ حقیقتِ «تصمیم + شاهد».
    stall = پورت باز ∧ (ts کهنه ∨ beat یخ‌زده) ∧ هیچ STOP (پورتِ مرده = مرگِ ساده).
    تنها side-effect: به‌یادسپاریِ beat در BEAT_MARK_FILE (لازمهٔ تشخیصِ یخ‌زدگی)."""
    flags = stop_flags if stop_flags is not None else STOP_FLAGS
    armed = _stall_revive_armed()
    stopped = next((f for f in flags if f.exists()), None)
    if stopped is not None:   # STOP اول — نه پروبِ پورت، نه خواندنِ state
        # port_alive به bool اجبار می‌شود تا قرارداد type-consistent بماند؛ اینکه
        # «پروب نشد» در port_probed می‌ماند، نه در Noneِ مبهمِ همان کلید.
        return {"should_revive": False, "reason": f"yield: STOP flag present ({stopped.name})",
                "stall": False, "stall_cause": [], "port_alive": bool(port_alive),
                "port_probed": port_alive is not None, "beat_age_s": None,
                "beat": None, "beat_evidence": None, "beat_reason": "not probed (STOP)",
                "beat_frozen": False, "beat_frozen_age_s": None,
                "stop_flag": stopped.name, "stall_revive_armed": armed}
    probed = port_alive is not None
    if port_alive is None:
        port_alive = _port_alive(ORGANISM_PORT)
    stale, causes, h, prog = _stall_verdict(now=now, health=health, progress=progress)
    if beat_stale is None:
        beat_stale = stale
    elif beat_stale and not causes:
        causes = ["injected"]
    should, reason = should_revive(port_alive=port_alive, stop_flags=flags,
                                  state_exists=state_exists, beat_stale=beat_stale)
    return {"should_revive": should, "reason": reason,
            "stall": bool(port_alive and beat_stale),
            "stall_cause": (causes if beat_stale else []),
            "port_alive": bool(port_alive), "port_probed": probed,
            "beat_age_s": h.get("age_s"),
            "beat": h.get("beat"), "beat_evidence": h.get("evidence"),
            "beat_reason": h.get("reason"),
            "beat_frozen": bool(prog.get("frozen")),
            "beat_frozen_age_s": prog.get("frozen_age_s"),
            "stop_flag": None, "stall_revive_armed": armed}


def notify(items: list[str]) -> bool:
    """صداکردنِ مالک روی مسیرِ داخلیِ **موجود** (opslib.alert → governor-alerts.md).
    transportِ نهایی (تلگرام یا فقط دفتر) رأیِ مالک است — اینجا فقط همان یک مسیر.

    fail-soft مطلق: شکستِ مسیرِ alert **هرگز** نباید احیا را متوقف کند."""
    try:
        opslib.alert([str(i) for i in items])
        return True
    except Exception:  # noqa: BLE001 — عمدی و کامل: آلارمِ شکسته ≠ احیای شکسته
        return False


def _governing_age(m: dict) -> float | None:
    """سنی که حکم را ساخته: یخ‌زدگیِ خالص ⇒ سنِ یخ‌زدگی، وگرنه سنِ ts."""
    causes = m.get("stall_cause") or []
    if "beat-frozen" in causes and "ts-stale" not in causes:
        return m.get("beat_frozen_age_s")
    if m.get("beat_age_s") is None:
        return m.get("beat_frozen_age_s")
    return m.get("beat_age_s")


def revive_action(report: dict | None = None) -> str:
    """اقدامِ revive + **صداکردنِ مالک**. تا امروز احیا فقط در state/watchdog-log.txt
    می‌نشست، پس چرخهٔ مرگ/احیا/مرگ کاملاً پنهان بود تا کسی دستی لاگ را باز کند.
    حالا هر verdictِ غیرعادی (REVIVE یا STALL) یک alert می‌دهد — دقیقاً یکی.

    قاعدهٔ متن (دو قیدِ سختِ اندازه‌گیری‌شده، هر دو لازم):
      ۱) واژهٔ «incident» داخلِ متن است، وگرنه event_bridge._is_critical رد می‌کند
         و alert فقط در دفتر می‌ماند (صفر پیامِ تلگرام — سنجیده: ۰/۷ می‌گذشت).
      ۲) هیچ عددِ متغیری در متن نیست — فقط جملهٔ ثابت + سطلِ درشت — وگرنه امضای
         dedupِ opslib.alert هر بار نو می‌شود و throttle/escalation بی‌اثر است."""
    m = report if report is not None else monitor()
    bucket = _age_bucket(_governing_age(m))
    if m["should_revive"]:
        notify([f"WATCHDOG REVIVE incident (organism :{ORGANISM_PORT}) — "
                f"{m['reason']} · {bucket}"])
        return (f"REVIVE: would launch RUN-ORGANISM.bat ({m['reason']}). "
                f"⚡ اجرای واقعی = مالک/PS1 (twin of organism-watchdog.ps1)")
    if m["stall"]:
        cause = "+".join(m.get("stall_cause") or ["unknown"])
        notify([f"WATCHDOG STALL incident (organism :{ORGANISM_PORT}) — سوکت باز است "
                f"ولی حلقهٔ درون-پروسه مرده (cause={cause}) · {bucket} · احیا خاموش "
                f"({STALL_REVIVE_FLAG}) — رأیِ مالک لازم است."])
    return f"NO-OP: {m['reason']}"


if __name__ == "__main__":
    _argv = sys.argv[1:]
    if _argv and _argv[0] == "--alert":
        # نقطهٔ ورودِ alert برای watchdogهای PS1 (cortex/live/tg-center) که پایتون
        # نمی‌دانند: `python watchdog.py --alert "<متن>"`. هرگز با REVIVE شروع نمی‌شود،
        # پس هیچ PS1ی این خروجی را با verdictِ احیا اشتباه نمی‌گیرد.
        _text = " ".join(_argv[1:]).strip() or "WATCHDOG: (پیامِ خالی)"
        print("ALERTED" if notify([_text]) else "ALERT-FAILED")
    else:
        print(revive_action())
