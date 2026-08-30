#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_watchdog_stall.py — C-watchdog: مرگِ خاموش (استالِ نامرئی + احیای بی‌صدا).

مسئله (اسکنِ 2026-07-30): سرپرستیِ organism/cortex/live فقط پروبِ **پورت** بود.
سوکتِ باز ≠ حلقهٔ زنده؛ و هر چهار watchdog روی مرگ فقط Add-Content به لاگ می‌کردند،
پس چرخهٔ مرگ/احیا/مرگ پنهان بود مگر کسی دستی watchdog-log.txt را باز کند.

⚠️ مرزِ صداقت (چیزی که این فایل **اثبات نمی‌کند**): تسکِ ثبت‌شدهٔ `organism-watchdog`
فایلِ «04 - Architect System/scripts/organism-watchdog.ps1» را می‌دواند، نه
`_ops/organism-watchdog.ps1`. آن نسخه منطقِ inlineِ خودش را دارد و صفر ارجاع به
watchdog.py؛ پس تشخیصِ استالِ organism در **تولید اجرا نمی‌شود**. هیچ assertی در این
فایل خلافِ آن را ادعا نمی‌کند (t_j فقط سه پای واقعاً ثبت‌شده روی `_ops\\` را می‌سنجد؛
t_p هم‌خوانیِ مستند-با-واقعیت را از خودِ Get-ScheduledTask می‌خواند، **بی‌آنکه** هیچ
وضعیتِ استقرار را pin کند).

آنچه اینجا اثبات می‌شود (hermetic؛ tmp-vaultِ harness — هرگز درختِ زنده، صفر شبکه/پول):
  · پورتِ باز + ts کهنه ⇒ stall (کورماهیِ اول)
  · پورتِ باز + ts **تازه** ولی شمارندهٔ beat یخ‌زده ⇒ stall — همان ارگانیسمی که روی
    exception می‌چرخد (organism.py:1173 با merge_prev=True هر بار ts را نو می‌کند)
  · هر verdictِ غیرعادی **دقیقاً یک** alert؛ ضربانِ تازه ⇒ صفر alert
  · متنِ هر ۷ alert از فیلترِ زندهٔ event_bridge._CRITICAL_KW **می‌گذرد** (وگرنه
    file-only بود و به مالک نمی‌رسید) و **پایدار** است (وگرنه dedup بی‌اثر بود)
  · مسیرِ مسلح‌کردن واقعاً وجود دارد: فایلِ نشانهٔ مالک (نه فقط env)
  · نقطهٔ ورودِ `--alert` با **subprocessِ واقعی** اجرا می‌شود (تنها مکانیزمی که سه
    پای ثبت‌شده استفاده می‌کنند)
  · STOP/HALT-ALL مطلق برنده و ساکت؛ غیابِ شاهد هرگز stall نمی‌سازد؛ alertِ شکسته
    احیا را نمی‌کشد

اجرا: python -X utf8 _ops/tests/test_watchdog_stall.py
"""
import ast
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness                       # noqa: E402
ENV = harness.setup("watchdog-stall")  # ⚠️ قبل از importِ هر ماژولِ _ops (STATE_DIR فریز می‌شود)
import opslib                        # noqa: E402
import watchdog                      # noqa: E402

ROOT = str(Path(ENV["root"]).resolve())
STATE = Path(ENV["ops"]) / "state" / "ORGANISM-STATE.json"
SIGS = opslib.STATE_DIR / "alert-signatures.json"
STALE_S = watchdog.BEAT_STALL_AFTER_S + 2700.0   # ۴۵ دقیقه بیش از سقف — بی‌ابهام
# سه پایی که Get-ScheduledTask نشان می‌دهد روی `_ops\` ثبت شده‌اند (اندازه‌گیری
# 2026-07-30): OCTOPUS-Cortex-Watchdog / OCTOPUS-Live-Watchdog / OCTOPUS-TG-Center-
# Watchdog. تسکِ چهارم (`organism-watchdog`) به twinِ «04 - Architect System» اشاره
# می‌کند و اینجا **عمداً** سنجیده نمی‌شود (وگرنه سبزِ روی تولیدِ لمس‌نشده).
REGISTERED_OPS_LEGS = (("cortex-watchdog.ps1", "RUN-CORTEX.bat"),
                       ("live-watchdog.ps1", "run-live-headless.bat"),
                       ("tg-center-watchdog.ps1", "RUN-TG-CENTER.bat"))
ALL_LEGS = ("organism-watchdog.ps1",) + tuple(n for n, _ in REGISTERED_OPS_LEGS)
BRIDGE = _OPS / "telegram_center" / "event_bridge.py"   # فقط خواندن، هرگز نوشتن


# ─── ابزار ────────────────────────────────────────────────────────────────────
_BEAT = [18413]


def _write_beat(age_s: float, beat: int | None = None) -> int:
    """مصنوعِ ضربان را با سنِ دلخواه بنویس؛ beat را برگردان (سنجهٔ محتوایی).
    پیش‌فرض: شمارنده جلو می‌رود — همان کاری که ارگانیسمِ سالم می‌کند."""
    if beat is None:
        _BEAT[0] += 1
        beat = _BEAT[0]
    ts = datetime.now() - timedelta(seconds=age_s)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"beat": beat, "ts": ts.isoformat(timespec="seconds"),
                                 "halted": None, "stop_organism": False},
                                ensure_ascii=False), "utf-8")
    return beat


def _alerts_reset() -> None:
    for p in (opslib.ALERTS_MD, SIGS):
        if p.exists():
            p.unlink()


def _mark_reset() -> None:
    if watchdog.BEAT_MARK_FILE.exists():
        watchdog.BEAT_MARK_FILE.unlink()


def _alerts() -> list[str]:
    if not opslib.ALERTS_MD.exists():
        return []
    return [ln for ln in opslib.ALERTS_MD.read_text("utf-8").splitlines()
            if ln.startswith("- ⚠️")]


def _assert_sandboxed(label: str, p) -> None:
    assert str(Path(p).resolve()).startswith(ROOT), f"{label} بیرونِ sandbox: {p}"


def _critical_kw() -> tuple:
    """`_CRITICAL_KW` را از **منبعِ زندهٔ** event_bridge بخوان (بدون import/اجرا).
    کپی‌کردنش در تست یعنی روزی که فیلتر عوض شود، تست سبزِ کهنه می‌ماند."""
    tree = ast.parse(BRIDGE.read_text("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "_CRITICAL_KW":
                    return tuple(e.value for e in node.value.elts)
    raise AssertionError("_CRITICAL_KW در event_bridge.py پیدا نشد — قرارداد عوض شده")


def _is_critical(line: str, kw: tuple) -> bool:
    low = line.lower()
    return any(k in low for k in kw)


def _ps1_alert_texts(name: str) -> list[str]:
    txt = (_OPS / name).read_text("utf-8", errors="replace")
    return re.findall(r'--alert\s+"([^"]+)"', txt)


def _registered_actions() -> list[str] | None:
    """اکشنِ همهٔ Scheduled Taskها — فقط خواندن. شکست/نبود → None (نه حکم)."""
    cmd = ("Get-ScheduledTask | ForEach-Object { $_.Actions } | "
           "ForEach-Object { \"$($_.Execute) $($_.Arguments)\" }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
    except Exception:  # noqa: BLE001 — محیطِ بی‌schtasks نباید تست را بترکاند
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


# ─── ۰) hermetic بودن: هیچ مسیری به درختِ زنده اشاره نمی‌کند ───────────────────
def t_a_paths_are_sandboxed():
    for label, p in (("STATE_FILE", watchdog.STATE_FILE),
                     ("ALERTS_MD", opslib.ALERTS_MD),
                     ("BEAT_MARK_FILE", watchdog.BEAT_MARK_FILE),
                     ("STALL_REVIVE_ARM_FILE", watchdog.STALL_REVIVE_ARM_FILE),
                     ("STOP_FLAGS[0]", watchdog.STOP_FLAGS[0])):
        _assert_sandboxed(label, p)


# ─── ۱) کورماهیِ اول: پورتِ باز + tsِ کهنه = استال ─────────────────────────────
def t_b_port_open_ts_stale_is_stall():
    _mark_reset()
    b = _write_beat(STALE_S)
    m = watchdog.monitor(port_alive=True, state_exists=True)
    assert m["stall"] is True, f"باید استال تشخیص شود: {m}"
    assert m["port_alive"] is True and m["port_probed"] is True, m
    assert m["beat_evidence"] is True and m["beat"] == b, m
    assert m["beat_age_s"] > watchdog.BEAT_STALL_AFTER_S, m
    assert m["stall_cause"] == ["ts-stale"], m
    # احیا پیش‌فرض خاموش است (رفتاری ⇒ owner-gated)، ولی verdict صریحاً STALE است
    assert m["should_revive"] is False and m["stall_revive_armed"] is False, m
    assert "STALE" in m["reason"], m["reason"]
    # گاردِ سازگاری: پین‌های موجود (test_d4/test_phase5) «alive» را در متن می‌خواهند
    assert "alive" in m["reason"], m["reason"]


# ─── ۲) استال دقیقاً یک alert می‌دهد (احیا/مرگِ بی‌صدا تمام شد) ─────────────────
def t_c_stall_emits_exactly_one_alert():
    _alerts_reset()
    _mark_reset()
    _write_beat(STALE_S)
    m = watchdog.monitor(port_alive=True, state_exists=True)
    out = watchdog.revive_action(m)
    assert out.startswith("NO-OP"), out
    lines = _alerts()
    assert len(lines) == 1, f"دقیقاً یک alert لازم است، شد {len(lines)}: {lines}"
    body = lines[0]
    assert "STALL" in body and "8771" in body, body
    assert "cause=ts-stale" in body, body


# ─── ۳) صفر false-positive: ضربانِ تازه = نه استال، نه alert ────────────────────
def t_d_fresh_beat_is_silent():
    _alerts_reset()
    _mark_reset()
    _write_beat(30)
    m = watchdog.monitor(port_alive=True, state_exists=True)
    assert m["stall"] is False and m["should_revive"] is False, m
    assert m["beat_frozen"] is False and m["stall_cause"] == [], m
    assert m["reason"] == "alive: organism running", m["reason"]
    assert watchdog.revive_action(m).startswith("NO-OP")
    assert _alerts() == [], f"ارگانیسمِ سالم نباید alert بدهد: {_alerts()}"


# ─── ۴) مرگِ ساده (پورتِ مرده) هم دقیقاً یک alert می‌دهد ───────────────────────
def t_e_plain_death_revive_emits_exactly_one_alert():
    _alerts_reset()
    _mark_reset()
    _write_beat(30)
    m = watchdog.monitor(port_alive=False, state_exists=True)
    assert m["should_revive"] is True, m
    assert m["stall"] is False, "پورتِ مرده = مرگِ ساده، نه استال"
    out = watchdog.revive_action(m)
    assert out.startswith("REVIVE"), out          # قراردادِ PS1: -like "REVIVE*"
    lines = _alerts()
    assert len(lines) == 1, f"دقیقاً یک alert لازم است، شد {len(lines)}: {lines}"
    assert "REVIVE" in lines[0] and "organism" in lines[0], lines[0]


# ─── ۵) fail-closed: STOP زیرِ استال هم مطلق برنده است و سکوت می‌کند ───────────
def t_f_stop_wins_under_stall():
    _alerts_reset()
    _mark_reset()
    _write_beat(STALE_S)
    halt = watchdog.STOP_FLAGS[0]                 # opslib.HALT_ALL داخلِ sandbox
    # ⚠️ این تست یک فایلِ HALT-ALL **می‌نویسد**. harness.run بعد از هر شکست ادامه
    # می‌دهد، پس تکیه به t_a کافی نیست: اگر تستِ زودتری بشکند و مسیرها sandbox
    # نباشند، همین‌جا HALT-ALLِ واقعی در _opsِ زنده کاشته می‌شد. پس درست قبل از
    # نوشتن، sandbox بودن **دوباره** سنجیده می‌شود.
    _assert_sandboxed("HALT_ALL (pre-write)", halt)
    halt.parent.mkdir(parents=True, exist_ok=True)
    halt.write_text("panic", "utf-8")
    try:
        m = watchdog.monitor(port_alive=True, state_exists=True)
        assert m["should_revive"] is False and m["stall"] is False, m
        assert m["stop_flag"] == "HALT-ALL" and "yield" in m["reason"], m
        # قراردادِ type: port_alive همیشه bool؛ «پروب نشد» در port_probed می‌ماند
        assert m["port_alive"] is True and m["port_probed"] is True, m
        m2 = watchdog.monitor(state_exists=True)   # بدونِ تزریق ⇒ پروب نشد
        assert m2["port_alive"] is False and m2["port_probed"] is False, m2
        assert isinstance(m2["port_alive"], bool), m2
        assert watchdog.revive_action(m).startswith("NO-OP")
        assert _alerts() == [], f"yield باید ساکت باشد (نه آلارم): {_alerts()}"
    finally:
        halt.unlink()


# ─── ۶) غیابِ شاهد هرگز استال نمی‌سازد ────────────────────────────────────────
def t_g_absence_never_manufactures_stall():
    _alerts_reset()
    _mark_reset()
    if STATE.exists():
        STATE.unlink()
    try:
        h = watchdog.beat_health()
        assert h["evidence"] is False and h["stall"] is False, h
        p = watchdog.beat_progress(None)
        assert p["evidence"] is False and p["frozen"] is False, p
        m = watchdog.monitor(port_alive=True, state_exists=True)
        assert m["stall"] is False and m["should_revive"] is False, m
        assert _alerts() == [], _alerts()
    finally:
        _write_beat(30)


# ─── ۷) فلگِ env: استال ⇒ احیا (owner-gated، پیش‌فرض خاموش) ────────────────────
def t_h_armed_env_flag_revives_on_stall():
    _alerts_reset()
    _mark_reset()
    _write_beat(STALE_S)
    os.environ[watchdog.STALL_REVIVE_FLAG] = "1"
    try:
        m = watchdog.monitor(port_alive=True, state_exists=True)
        assert m["stall"] is True and m["should_revive"] is True, m
        assert "STALL" in m["reason"] and m["stall_revive_armed"] is True, m
        out = watchdog.revive_action(m)
        assert out.startswith("REVIVE"), out
        lines = _alerts()
        assert len(lines) == 1, f"دقیقاً یک alert، شد {len(lines)}: {lines}"
    finally:
        os.environ.pop(watchdog.STALL_REVIVE_FLAG, None)


# ─── ۷ب) مسیرِ مسلح‌کردنی که واقعاً به Scheduled Task می‌رسد ────────────────────
def t_h2_marker_file_is_a_real_arming_path():
    """چهار watchdog، تسکِ مستقل‌اند و OCTOPUS-flags.cmd را source نمی‌کنند؛ پس
    envِ تنها = «مسلح ولی اثبات‌ناپذیر». فایلِ نشانه تنها کاناله‌ای است که به یک
    تسکِ standalone می‌رسد. اینجا اثبات می‌شود که واقعاً مسلح می‌کند — و پیش‌فرض
    (نبودِ فایل) خاموش است."""
    _alerts_reset()
    _mark_reset()
    _write_beat(STALE_S)
    assert watchdog.STALL_REVIVE_FLAG not in os.environ, "envِ باقی‌مانده تست را می‌آلاید"
    arm = watchdog.STALL_REVIVE_ARM_FILE
    _assert_sandboxed("STALL_REVIVE_ARM_FILE (pre-write)", arm)
    assert watchdog._stall_revive_armed() is False, "پیش‌فرض باید خاموش باشد"
    assert watchdog.monitor(port_alive=True, state_exists=True)["should_revive"] is False
    arm.parent.mkdir(parents=True, exist_ok=True)
    arm.write_text("armed by owner", "utf-8")
    try:
        assert watchdog._stall_revive_armed() is True, "فایلِ نشانه باید مسلح کند"
        m = watchdog.monitor(port_alive=True, state_exists=True)
        assert m["stall_revive_armed"] is True, m
        assert m["should_revive"] is True and "STALL" in m["reason"], m
    finally:
        arm.unlink()
    assert watchdog._stall_revive_armed() is False, "حذفِ فایل باید خلعِ سلاح کند"


# ─── ۸) fail-soft مطلق: alertِ شکسته احیا را نمی‌کشد ──────────────────────────
def t_i_broken_alert_never_blocks_revive():
    _mark_reset()
    _write_beat(30)
    orig = opslib.alert

    def _boom(items):
        raise RuntimeError("alert transport dead")

    opslib.alert = _boom
    try:
        assert watchdog.notify(["x"]) is False, "notify باید شکست را ببلعد و False بدهد"
        m = watchdog.monitor(port_alive=False, state_exists=True)
        out = watchdog.revive_action(m)
        assert out.startswith("REVIVE"), f"alertِ شکسته احیا را کشت: {out}"
    finally:
        opslib.alert = orig


# ─── ۹) سه پایِ ثبت‌شده روی `_ops\`: alert **بعد** از خودِ Start-Process ────────
def t_j_registered_ops_legs_alert_after_the_real_start_process():
    """anchor روی همان خطِ Start-Process است، نه اولین ذکرِ نامِ launcher در متن:
    در هر سه فایل نامِ launcher **اول** در یک کامنتِ هدر می‌آید (schtasks/توضیح)،
    پس `txt.index(launcher)` به کامنت می‌خورد و ترتیب‌سنجی بی‌معنا می‌شد."""
    for name, launcher in REGISTERED_OPS_LEGS:
        lines = (_OPS / name).read_text("utf-8", errors="replace").splitlines()
        sp = [i for i, ln in enumerate(lines)
              if "Start-Process" in ln and launcher in ln and not ln.lstrip().startswith("#")]
        assert len(sp) == 1, f"{name}: خطِ اجراییِ Start-Process یکتا نیست: {sp}"
        al = [i for i, ln in enumerate(lines)
              if "--alert" in ln and not ln.lstrip().startswith("#")]
        assert al, f"{name} روی احیا alert ندارد — احیای بی‌صدا برگشت"
        assert "WATCHDOG REVIVE" in "\n".join(lines[i] for i in al), f"{name} متنِ احیا را ندارد"
        assert min(al) > sp[0], (
            f"{name}: alert باید **بعد** از خودِ Start-Process (خط {sp[0] + 1}) باشد؛ "
            f"اولین alert در خط {min(al) + 1} است — fail-soft: هرگز مانعِ احیا")
        for i in al:
            assert "catch {}" in lines[i], f"{name} خط {i + 1}: alert در try/catch بلعیده نشده"
    # وکالتِ organism (بی‌ادعا نسبت به تولید — رجوع به t_p)
    org = (_OPS / "organism-watchdog.ps1").read_text("utf-8", errors="replace")
    assert "--alert" in org and "WATCHDOG BLIND" in org, "organism باید کوریِ خودش را صدا بزند"
    assert "watchdog.py" in org and "RUN-ORGANISM.bat" in org, "قراردادِ وکالت نباید بشکند"
    wd_src = (_OPS / "watchdog.py").read_text("utf-8")
    assert "notify(" in wd_src.split("def revive_action")[1], "revive_action باید notify کند"


# ─── ۱۰) پینِ انتخابِ مصنوعِ ضربان (دلیل، نه سلیقه) ───────────────────────────
def t_k_beat_artifact_is_the_live_one():
    """ORGANISM-STATE.json انتخاب شد چون هر beat بازنویسی می‌شود. عوض‌کردنش با
    beat_scheduler.heartbeat_health درختِ زنده را می‌شکند: آن تابع
    state/pulse/beat-state.json را می‌خواند که فقط زیرِ OCTOPUS_ONE_HEARTBEAT
    (shadow/خاموش) نوشته می‌شود ⇒ روی ارگانیسمِ سالم stall=True (false-positive)."""
    assert watchdog.STATE_FILE.name == "ORGANISM-STATE.json", watchdog.STATE_FILE
    tree = ast.parse((_OPS / "watchdog.py").read_text("utf-8"))
    names, literals = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
    assert "heartbeat_health" not in names, "کد نباید heartbeat_health را صدا بزند"
    assert not any("beat-state.json" in s for s in literals), \
        "watchdog نباید به beat-state.jsonِ shadow-only وابسته شود (طوفانِ احیای کاذب)"
    # سنجهٔ محتوایی: همان تابع روی ورودیِ کهنه/تازه دو حکمِ مخالف می‌دهد
    assert watchdog.beat_health(age_s=STALE_S)["stall"] is True
    assert watchdog.beat_health(age_s=10)["stall"] is False


# ─── ۱۱) هر ۷ متنِ alert از فیلترِ زندهٔ push می‌گذرد (وگرنه file-only) ─────────
def t_l_every_alert_text_passes_the_live_critical_filter():
    """تنها مسیرِ alert→تلگرام، event_bridge است و فقط خطوطی را push می‌کند که با
    `_CRITICAL_KW` جور باشند. پیش از این ۰ از ۷ متن جور بود ⇒ همه file-only.
    keyword از **منبعِ زندهٔ** event_bridge خوانده می‌شود، نه کپیِ کهنه در تست."""
    kw = _critical_kw()
    assert "incident" in kw, f"قراردادِ فیلتر عوض شده: {kw}"
    texts: list[tuple[str, str]] = []
    for name in ALL_LEGS:
        got = _ps1_alert_texts(name)
        assert got, f"{name}: هیچ متنِ --alert پیدا نشد"
        texts += [(name, t) for t in got]
    # متن‌های خودِ watchdog.py: از روی اجرا برداشته می‌شوند، نه از روی سورس
    _alerts_reset()
    _mark_reset()
    _write_beat(STALE_S)
    watchdog.revive_action(watchdog.monitor(port_alive=True, state_exists=True))
    _write_beat(30)
    watchdog.revive_action(watchdog.monitor(port_alive=False, state_exists=True))
    emitted = _alerts()
    assert len(emitted) == 2, f"باید STALL و REVIVE باشد: {emitted}"
    texts += [("watchdog.py", t) for t in emitted]
    assert len(texts) == 7, f"۷ متنِ alert انتظار می‌رفت، شد {len(texts)}: {texts}"
    dark = [(n, t) for n, t in texts if not _is_critical(t, kw)]
    assert not dark, ("این متن‌ها به مالک نمی‌رسند (file-only، فیلترِ push ردشان "
                      f"می‌کند): {dark}")
    banned = ("api_key", "token", "password", "secret", "bot_token")
    leaks = [(n, t) for n, t in texts if any(b in t.lower() for b in banned)]
    assert not leaks, f"متنِ alert باعثِ redact/لو رفتن می‌شود: {leaks}"


# ─── ۱۲) متن پایدار است ⇒ dedup و escalation واقعاً درگیر می‌شوند ──────────────
def t_m_alert_text_is_dedup_stable():
    """opslib.alert امضا را از **متن** هش می‌کند. متنِ قبلی `beat=…`/`age=…s` داشت،
    پس هر اجرا امضای نو می‌ساخت: count همیشه ۱ ⇒ نه پنجرهٔ ۶ساعته، نه نشانه‌های
    escalation — با کیدنسِ ۵دقیقه‌ای تا ۲۸۸ آلارمِ throttle-نشده در روز."""
    _alerts_reset()
    N = 10
    for i in range(N):
        _mark_reset()
        _write_beat(STALE_S + i * 137.0)   # سنِ **دقیقاً متفاوت** در هر دور
        watchdog.revive_action(watchdog.monitor(port_alive=True, state_exists=True))
    sigs = json.loads(SIGS.read_text("utf-8"))
    assert len(sigs) == 1, (f"متن پایدار نیست: {N} اجرا ⇒ {len(sigs)} امضای متفاوت "
                            f"(dedup و escalation بی‌اثر می‌شوند)")
    rec = next(iter(sigs.values()))
    assert rec["count"] == N, f"شمارش نخورد: {rec}"
    lines = _alerts()
    # سه تکرارِ اول همیشه نوشته می‌شوند + نشانهٔ escalation در ×۱۰ ⇒ ۴، نه ۱۰
    assert len(lines) == 4, f"throttle درگیر نشد: {len(lines)} خط از {N} اجرا: {lines}"
    assert "escalation" in lines[-1], lines[-1]
    base = [ln.split(" (×")[0] for ln in lines]
    assert len(set(base)) == 1, f"متنِ آلارم بین اجراها تغییر کرد: {set(base)}"
    assert re.search(r"age(<=|>)\d+s", base[0]), f"سطلِ درشتِ سن در متن نیست: {base[0]}"
    assert not re.search(r"\bbeat=\d", base[0]), f"عددِ متغیر برگشت: {base[0]}"


# ─── ۱۳) MF5: tsِ تازه ولی شمارندهٔ beat یخ‌زده = استال (ارگانیسمِ چرخنده) ──────
def t_n_frozen_beat_counter_is_a_stall_even_with_fresh_ts():
    """حالتی که چکِ ts-only **ساختاراً** کور است: organism._write_state همیشه
    ts را نو می‌کند و handlerِ خطای حلقه (organism.py:1173) با merge_prev=True
    فقط کلیدهای غایب را back-fill می‌کند ⇒ ارگانیسمی که روی exception می‌چرخد
    و پورتش باز است، ts تازه و beat یخ‌زده دارد."""
    # الف) خودِ ناوردی روی تابعِ خالص (mark فایلِ اختصاصی، بی‌تزریقِ جواب)
    mark = Path(ENV["ops"]) / "state" / "t_n-mark.json"
    if mark.exists():
        mark.unlink()
    t0 = time.time()
    p1 = watchdog.beat_progress(777, now=t0, mark_file=mark)
    assert p1["frozen"] is False and p1["prev_beat"] is None, p1
    p2 = watchdog.beat_progress(777, now=t0 + 60, mark_file=mark)
    assert p2["frozen"] is False and p2["frozen_age_s"] == 60.0, p2
    p3 = watchdog.beat_progress(777, now=t0 + watchdog.BEAT_STALL_AFTER_S + 1,
                                mark_file=mark)
    assert p3["frozen"] is True and p3["prev_beat"] == 777, p3
    p4 = watchdog.beat_progress(778, now=t0 + watchdog.BEAT_STALL_AFTER_S + 2,
                                mark_file=mark)
    assert p4["frozen"] is False, f"جلو رفتنِ beat باید ساعت را صفر کند: {p4}"

    # ب) e2e روی مسیرِ پیش‌فرض: ts **تازه**، beat یخ‌زده ⇒ stall
    _alerts_reset()
    b = _write_beat(30, beat=4242)                     # ts فقط ۳۰ ثانیه — تازه
    watchdog.BEAT_MARK_FILE.parent.mkdir(parents=True, exist_ok=True)
    watchdog.BEAT_MARK_FILE.write_text(json.dumps(
        {"beat": b, "since": time.time() - 3600, "seen": time.time() - 300}), "utf-8")
    m = watchdog.monitor(port_alive=True, state_exists=True)
    assert m["beat_evidence"] is True and m["beat"] == b, m
    assert m["beat_age_s"] < watchdog.BEAT_STALL_AFTER_S, \
        f"ts باید تازه باشد وگرنه این تست حالتِ اشتباهی را می‌سنجد: {m}"
    assert m["beat_frozen"] is True, m
    assert m["stall"] is True, f"چکِ ts-only اینجا کور است — یخ‌زدگی باید بگیردش: {m}"
    assert m["stall_cause"] == ["beat-frozen"], m
    out = watchdog.revive_action(m)
    assert out.startswith("NO-OP"), out
    lines = _alerts()
    assert len(lines) == 1 and "cause=beat-frozen" in lines[0], lines
    assert "incident" in lines[0].lower(), lines[0]
    _mark_reset()


# ─── ۱۴) MF7: نقطهٔ ورودِ --alert با subprocessِ واقعی اجرا می‌شود ─────────────
def t_o_alert_cli_writes_through_a_real_subprocess():
    """تنها مکانیزمی که سه پای ثبت‌شده استفاده می‌کنند همین CLI است و تا امروز
    هیچ‌چیز اجرایش نمی‌کرد. اینجا واقعاً spawn می‌شود (env، sys.path، importِ
    opslib، نوشتن در دفتر) — نه صدا زدنِ درون-پروسه‌ایِ notify()."""
    _alerts_reset()
    text = ("WATCHDOG SELFTEST incident (cli) — نقطهٔ ورودِ --alert اجرا شد")
    r = subprocess.run([sys.executable, "-X", "utf8", str(_OPS / "watchdog.py"),
                        "--alert", text],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180, env=dict(os.environ))
    assert r.returncode == 0, f"rc={r.returncode} out={r.stdout!r} err={r.stderr!r}"
    assert r.stdout.strip() == "ALERTED", f"out={r.stdout!r} err={r.stderr!r}"
    lines = _alerts()
    assert len(lines) == 1, f"CLI باید دقیقاً یک خط بنویسد: {lines}"
    assert text in lines[0], lines[0]
    _assert_sandboxed("ALERTS_MD (post-subprocess)", opslib.ALERTS_MD)
    # متنِ خالی هم باید بی‌خطا و صریح باشد (نه crash، نه سکوت)
    r2 = subprocess.run([sys.executable, "-X", "utf8", str(_OPS / "watchdog.py"), "--alert"],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=180, env=dict(os.environ))
    assert r2.returncode == 0 and r2.stdout.strip() == "ALERTED", (r2.stdout, r2.stderr)


# ─── ۱۵) هم‌خوانیِ مستند با واقعیتِ ثبت‌شده — بی‌آنکه استقرار pin شود ──────────
def t_p_docs_match_registered_reality():
    """Get-ScheduledTask (فقط خواندن) را می‌خواند و برای هر پا می‌پرسد: آیا
    تسکی به `_ops\\<نام>` اشاره می‌کند؟
      · اشاره می‌کند ⇒ آن فایل **باید** روی مسیرِ احیا alert داشته باشد (پوششِ واقعی)
      · اشاره نمی‌کند ⇒ آن فایل **باید** همین شکاف را مستند کرده باشد، وگرنه
        روزی کسی «سبز» را با «در تولید کار می‌کند» اشتباه می‌گیرد
    هیچ assertی نمی‌گوید کدام مسیر *باید* ثبت شده باشد — آن رأیِ مالک است و هر دو
    حالتِ استقرار از این تست سبز می‌گذرند."""
    actions = _registered_actions()
    if actions is None:
        print("      ℹ️ Get-ScheduledTask در دسترس نبود — پوششِ تولید UNKNOWN "
              "(t_j قرارداد را ساکن می‌سنجد)")
        return
    for name in ALL_LEGS:
        needle = ("_ops\\" + name).lower()
        hit = [a for a in actions if needle in a.lower()]
        txt = (_OPS / name).read_text("utf-8", errors="replace")
        if hit:
            assert "--alert" in txt, (f"{name} تسکِ ثبت‌شده دارد ولی روی احیا alert "
                                      f"ندارد — احیای بی‌صدا در تولید")
            print(f"      ✔ {name}: در تولید از `_ops\\` اجرا می‌شود (پوششِ واقعی)")
        else:
            assert "NOT THE FILE PRODUCTION RUNS" in txt, (
                f"{name}: هیچ Scheduled Taskی به `_ops\\{name}` اشاره نمی‌کند، پس این "
                f"فایل در تولید اجرا نمی‌شود — و خودش این را مستند نکرده است. "
                f"گاردِ سبزِ روی تولیدِ لمس‌نشده همین‌جا زاده می‌شود.")
            print(f"      ⚠️ {name}: هیچ تسکی به `_ops\\` اشاره نمی‌کند ⇒ در تولید "
                  f"اجرا نمی‌شود (مستند شده؛ رفعش owner-gated)")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_watchdog_stall: "
          f"{len(checks) - failed}/{len(checks)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
