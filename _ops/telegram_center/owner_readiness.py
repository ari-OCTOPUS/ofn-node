#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owner_readiness — «آیا ساعتِ اولِ واقعیِ مالک کار می‌کند؟» (پروبِ فقط‌خواندنی).

منشورِ TG-UI-CHARTER-2026-07-31 چهار موج را وعده داد. این ماژول هیچ‌کدام را
نمی‌سازد — فقط می‌پرسد: **همین الان، در همین پروسه‌های زنده، کدام وعده واقعاً
برقرار است؟** و برای هر «نه»، یک خطِ فیکسِ دقیق می‌دهد.

قواعدِ سختِ این فایل (هر سه در تست قفل‌اند):
  · **صفر نوشتن.** هیچ mkdir، هیچ open(...,"w")، هیچ os.replace. حتی
    `sys.dont_write_bytecode` هنگامِ importهای probe روشن می‌شود تا حتی
    یک `.pyc` هم جا نگذارد.
  · **صفر ارسال، صفر getUpdates.** poller ِ زنده صاحبِ توکن است؛ یک poller ِ
    دوم یعنی ۴۰۹ و دزدیدنِ پیامِ مالک. شواهد فقط از آرتیفکت‌هایی می‌آید که
    خودِ مرکز نوشته (پالس، config، send-log، store).
  · **سوکت فقط connect_ex، هرگز bind** — و فقط وقتی `live=True`.
  · **فایلِ غایب هرگز استثنا نمی‌دهد** — غیابِ صادقانه یک ردیفِ گزارش است.

منبعِ حقیقتِ فلگ: اسنپ‌شاتِ **بارگذاری‌شده** (`state/flags-loaded-<proc>.json`)،
نه فایلِ `OCTOPUS-flags.cmd`. درسِ «مسلح ولی بارگذاری‌نشده»: فایل عوض می‌شود،
پروسهٔ زنده هنوز مقدارِ قدیمی را در حافظه دارد؛ فقط اسنپ‌شات این را می‌گوید.

خروجی:
    check(live=False) -> {"ok": bool, "checks": [
        {"name": str, "ok": bool, "detail": str, "fix": str, "level": str}, …]}
    level ∈ {"ok", "warn", "blocker"} · ok == (level != "blocker")
    نتیجهٔ کل ok == هیچ blocker ای نیست (warn گیت را نمی‌بندد ولی دیده می‌شود).

اجرا برای آدم:  `python _ops/telegram_center/owner_readiness.py`
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

OK, WARN, BLOCKER = "ok", "warn", "blocker"
_MARK = {OK: "✅", WARN: "⚠️", BLOCKER: "❌"}
REDACTED = "<redacted>"      # نویسندهٔ اسنپ‌شات مقدارِ حساس را این‌طور می‌نویسد

# ── آستانه‌ها ──────────────────────────────────────────────────────────────
PULSE_MAX_S = 300.0          # پالسِ مرکز — یک ضربانِ ۵ دقیقه‌ای
ORGANISM_MAX_S = 900.0       # ORGANISM-STATE — سه ضربان
MINIAPP_MAX_S = 3600.0       # فایلِ URL ِ تونل

PORTS = (("cortex", 8772), ("live", 8773), ("miniapp-gateway", 8774))

# ── قرارداد ────────────────────────────────────────────────────────────────
# ۸ تاپیکِ پا در TELEGRAM-ACCESS-CONTRACT.v1.json → legs_forum_group.allowed_topics
CONTRACT_LEG_TOPICS = ("lead", "ziman", "mining", "crypto", "accounting",
                       "studio_pf", "knowledge", "cartographer")
# محدودهٔ شناسه‌های «جاسوسیِ» تستی — هرگز نباید در configِ زنده بنشیند
SPY_ID_RANGE = (9000, 9100)

# فلگ‌هایی که هر پروسه برای وعده‌های امروز لازم دارد (مسلح = ۱ در اسنپ‌شاتِ خودش)
REQUIRED_FLAGS = {
    "center": ("OCTOPUS_TG_CAPTURE", "OCTOPUS_TG_REMINDERS", "OCTOPUS_TG_BRIEF",
               "OCTOPUS_TG_ASK_VAULT", "OCTOPUS_TG_CHAT_LOCAL",
               "OCTOPUS_TG_MINIAPP", "OCTOPUS_TG_WEEKLY_REVIEW",
               "OCTOPUS_TG_QBUDGET", "OCTOPUS_WIRE_MEMORY_DECISION"),
    "organism": ("OCTOPUS_WIRE_LEAD_PIPELINE", "OCTOPUS_WIRE_MEMORY_DECISION"),
}
# فلگ‌هایی که امروز باید خاموش باشند. outbound ایمنی است (blocker)، بقیه warn.
MUST_BE_OFF = {
    "OCTOPUS_WIRE_LEAD_OUTBOUND": BLOCKER,
    "OCTOPUS_WIRE_LEAD_DISCOVERY": WARN,
    "OCTOPUS_TG_CAPTURE_LLM": WARN,
}
SMTP_ENV = ("OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
            "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM")

EXPECTED_SEND_CAP = 10       # رأی ۱۷ منشور — عددِ سقف در کد، نه env


# ── کمکی‌های خالص ──────────────────────────────────────────────────────────
def _row(name: str, level: str, detail: str, fix: str = "") -> dict:
    return {"name": name, "ok": level != BLOCKER, "detail": detail,
            "fix": fix, "level": level}


def _read_json(path: Path):
    """(داده, خطا) — فایلِ غایب/خراب هرگز استثنا نمی‌دهد. BOM-امن."""
    try:
        raw = path.read_text("utf-8-sig")
    except FileNotFoundError:
        return None, "absent"
    except OSError as e:                                    # noqa: BLE001
        return None, f"unreadable:{type(e).__name__}"
    try:
        return json.loads(raw), None
    except (ValueError, TypeError) as e:                    # noqa: BLE001
        return None, f"bad-json:{type(e).__name__}"


def _mtime(path: Path):
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _age(ts, now: float) -> float:
    return float(now) - float(ts)


def _fa_age(seconds: float) -> str:
    s = int(max(0, seconds))
    if s < 90:
        return f"{s} ثانیه"
    if s < 5400:
        return f"{s // 60} دقیقه"
    return f"{s // 3600} ساعت"


def _armed(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _paths() -> dict:
    """مسیرها در call-time از opslib (env-اول) — harness ِ تست ایزوله‌شان می‌کند."""
    try:
        import opslib
        ops = Path(opslib.OPS)
        state = Path(opslib.STATE_DIR)
        org = Path(opslib.ORG_ROOT)
    except Exception:                                       # noqa: BLE001
        ops = _OPS
        state = _OPS / "state"
        org = _OPS.parent
    env_root = str(os.environ.get("ORG_ROOT", "") or "").strip()
    return {"ops": ops, "state": state, "org": Path(env_root) if env_root else org,
            "org_env": env_root}


def parse_flags_cmd(path: Path) -> dict:
    """`set NAME=VALUE` را از OCTOPUS-flags.cmd می‌خواند. آخرین مقدار برنده است
    (همان معناییِ خودِ cmd). خطِ rem نادیده. فایلِ غایب ⇒ {}."""
    out: dict = {}
    try:
        text = path.read_text("utf-8", errors="ignore")
    except OSError:
        return out
    for line in text.splitlines():
        s = line.strip()
        if not s or s.lower().startswith(("rem ", "::", "@rem")):
            continue
        if not s.lower().startswith("set "):
            continue
        body = s[4:].strip()
        if "=" not in body:
            continue
        k, _, v = body.partition("=")
        k = k.strip()
        if k:
            out[k] = v.strip().strip('"')
    return out


def _port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.8) -> bool:
    """connect_ex — هرگز bind. تنها مصرف‌کننده: چکِ live."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(timeout)
        return s.connect_ex((host, int(port))) == 0
    except OSError:
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def _importable(module: str, extra_path: "Path | None" = None):
    """(ok, detail) — import ِ واقعی ولی **بدونِ نوشتنِ .pyc**."""
    if extra_path is not None and str(extra_path) not in sys.path:
        sys.path.insert(0, str(extra_path))
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        mod = __import__(module)
        for part in module.split(".")[1:]:
            mod = getattr(mod, part)
        return True, mod
    except Exception as e:                                  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        sys.dont_write_bytecode = prev


# ── چک‌ها ──────────────────────────────────────────────────────────────────
def _check_processes(P: dict, now: float, live: bool) -> list:
    rows = []

    # پالسِ مرکز — «مرکز زنده است؟»
    pulse, err = _read_json(P["state"] / "pulse" / "tg-center.json")
    if pulse is None:
        rows.append(_row(
            "processes.center_pulse", BLOCKER,
            f"پالسِ مرکز خوانده نشد ({err}) — state/pulse/tg-center.json",
            "مرکز را با _ops/telegram_center/RUN-TG-CENTER.bat بالا بیاور"))
    else:
        ts = pulse.get("mono")
        if not isinstance(ts, (int, float)):
            ts = _mtime(P["state"] / "pulse" / "tg-center.json") or 0
        age = _age(ts, now)
        pid = pulse.get("pid")
        if age <= PULSE_MAX_S:
            rows.append(_row("processes.center_pulse", OK,
                             f"مرکز زنده — PID {pid} · آخرین ضربان {_fa_age(age)} پیش",
                             ""))
        else:
            rows.append(_row(
                "processes.center_pulse", BLOCKER,
                f"مرکز {_fa_age(age)} است که ضربان نزده (آستانه "
                f"{int(PULSE_MAX_S)}s) — PID ثبت‌شده {pid}",
                "RUN-TG-CENTER.bat را دوباره اجرا کن و پالس را دوباره بسنج"))

    # ORGANISM-STATE — «بدن زنده است؟»
    st_path = P["state"] / "ORGANISM-STATE.json"
    st, err = _read_json(st_path)
    if st is None:
        rows.append(_row("processes.organism_state", BLOCKER,
                         f"ORGANISM-STATE خوانده نشد ({err})",
                         "ارگانیسم را با _ops/RUN-ORGANISM.bat بالا بیاور"))
    else:
        ts = None
        raw_ts = st.get("ts")
        if isinstance(raw_ts, str):
            try:
                ts = datetime.fromisoformat(raw_ts).timestamp()
            except ValueError:
                ts = None
        elif isinstance(raw_ts, (int, float)):
            ts = float(raw_ts)
        if ts is None:
            ts = _mtime(st_path) or 0
        age = _age(ts, now)
        beat = st.get("beat")
        halted = bool(st.get("halted")) or bool(st.get("stop_organism"))
        # مارکرِ روی دیسک حجت است، نه snapshot: الگوی ری‌استارتِ sentinel باعث
        # می‌شود پروسهٔ در حالِ خروج **آخرین** state را با stop_organism=True
        # بنویسد و بعد مارکرها پاک و پروسهٔ نو بالا بیاید. بدونِ این تفکیک،
        # هر ری‌استارتِ سالم یک «HALT» ِ کاذب گزارش می‌شد (۰۷-۳۱).
        markers_live = any((P["ops"] / m).exists() for m in
                           ("STOP-ORGANISM", "HALT-ALL"))
        if halted and markers_live:
            rows.append(_row("processes.organism_state", BLOCKER,
                             f"ارگانیسم halted/stop است (ضربان {beat})",
                             "علتِ HALT را در _ops/state/watchdog-log.txt ببین "
                             "— برداشتنِ HALT رأیِ مالک است"))
        elif halted and age <= ORGANISM_MAX_S:
            rows.append(_row("processes.organism_state", WARN,
                             f"snapshot ِ خداحافظیِ ری‌استارت (ضربان {beat}، "
                             f"{_fa_age(age)} پیش) — هیچ مارکرِ STOP/HALT روی "
                             "دیسک نیست؛ ضربانِ بعدی پاکش می‌کند",
                             "اگر بعد از یک ضربانِ کامل باقی ماند، جدی است"))
        elif halted:
            rows.append(_row("processes.organism_state", BLOCKER,
                             f"ارگانیسم halted/stop و state کهنه است (ضربان {beat})",
                             "علتِ HALT را در _ops/state/watchdog-log.txt ببین"))
        elif age <= ORGANISM_MAX_S:
            rows.append(_row("processes.organism_state", OK,
                             f"ارگانیسم زنده — ضربان {beat} · {_fa_age(age)} پیش",
                             ""))
        else:
            rows.append(_row("processes.organism_state", BLOCKER,
                             f"ORGANISM-STATE {_fa_age(age)} کهنه است "
                             f"(آستانه {int(ORGANISM_MAX_S)}s)",
                             "_ops/RUN-ORGANISM.bat را دوباره اجرا کن"))

    # پورت‌ها — فقط در حالتِ live
    if not live:
        rows.append(_row("processes.ports", WARN,
                         "پورت‌ها بررسی نشد (live=False — پروبِ آفلاین)",
                         "با check(live=True) یا اجرای مستقیمِ همین فایل بسنج"))
    else:
        down = [n for n, p in PORTS if not _port_open(p)]
        up = [f"{n}:{p}" for n, p in PORTS if _port_open(p)]
        if not down:
            rows.append(_row("processes.ports", OK,
                             "همهٔ پورت‌ها گوش می‌دهند — " + " · ".join(up), ""))
        else:
            rows.append(_row(
                "processes.ports", BLOCKER,
                "پورتِ خاموش: " + " · ".join(down) + " | بالا: "
                + (" · ".join(up) or "هیچ"),
                "cortex→_ops/RUN-CORTEX.bat · live→_ops/RUN-LIVE.bat · "
                "miniapp→_ops/telegram_center/run-miniapp-tunnel.ps1"))
    return rows


def _check_flags(P: dict, now: float) -> list:
    rows = []
    cmd_path = P["ops"] / "OCTOPUS-flags.cmd"
    file_flags = parse_flags_cmd(cmd_path)
    cmd_mtime = _mtime(cmd_path)

    snaps = {}
    for proc in ("center", "organism"):
        snap, err = _read_json(P["state"] / f"flags-loaded-{proc}.json")
        snaps[proc] = (snap, err)

    # ۱) هر فلگِ لازم در پروسه‌ای که لازمش دارد
    for proc, needed in REQUIRED_FLAGS.items():
        snap, err = snaps.get(proc, (None, "absent"))
        if not isinstance(snap, dict):
            rows.append(_row(
                f"flags.{proc}", BLOCKER,
                f"اسنپ‌شاتِ فلگِ {proc} خوانده نشد ({err}) — "
                f"state/flags-loaded-{proc}.json",
                f"پروسهٔ {proc} را ری‌استارت کن تا اسنپ‌شات را دوباره بنویسد"))
            continue
        loaded = snap.get("flags") if isinstance(snap.get("flags"), dict) else {}
        pid = snap.get("pid")
        off = [f for f in needed if not _armed(loaded.get(f))]
        # تلهٔ کلاسیک: در فایل مسلح، در اسنپ‌شات غایب
        ghost = [f for f in needed
                 if f not in loaded and _armed(file_flags.get(f))]
        if not off:
            rows.append(_row(f"flags.{proc}", OK,
                             f"هر {len(needed)} فلگِ لازمِ {proc} در PID {pid} "
                             f"بارگذاری و مسلح است", ""))
        else:
            ghosts = f" (در فایل مسلح ولی در پروسه غایب: {', '.join(ghost)})" if ghost else ""
            rows.append(_row(
                f"flags.{proc}", BLOCKER,
                f"فلگِ خاموش/غایب در PID {pid}: {', '.join(off)}{ghosts}",
                f"مقدار را در {cmd_path.name} به ۱ ببر و پروسهٔ {proc} را "
                f"ری‌استارت کن (بارگذاری فقط در بوت است)"))

    # ۲) فلگ‌هایی که باید خاموش باشند
    for flag, level in MUST_BE_OFF.items():
        on_in = []
        for proc, (snap, _e) in snaps.items():
            if not isinstance(snap, dict):
                continue
            loaded = snap.get("flags") if isinstance(snap.get("flags"), dict) else {}
            if _armed(loaded.get(flag)):
                on_in.append(f"{proc}(PID {snap.get('pid')})")
        if not on_in:
            rows.append(_row(f"flags.off.{flag}", OK,
                             f"{flag} در هیچ پروسه‌ای مسلح نیست", ""))
        else:
            in_file = file_flags.get(flag)
            already_off = in_file is not None and not _armed(in_file)
            rows.append(_row(
                f"flags.off.{flag}", level,
                f"{flag} در حافظهٔ {', '.join(on_in)} مسلح است "
                f"(مقدارِ فایل: {in_file if in_file is not None else '<غایب>'})"
                + (" — فایل درست است، پروسه کهنه" if already_off else ""),
                (f"فقط {', '.join(p.split('(')[0] for p in on_in)} را ری‌استارت "
                 f"کن — {cmd_path.name} از قبل صفر است")
                if already_off else
                f"در {cmd_path.name} صفر کن و آن پروسه را ری‌استارت کن"))

    # ۳) کهنگیِ اسنپ‌شات نسبت به فایل — «پروسه فلگِ دیروز را دارد»
    for proc, (snap, _e) in snaps.items():
        if not isinstance(snap, dict) or cmd_mtime is None:
            continue
        src_m = snap.get("source_mtime")
        if not isinstance(src_m, (int, float)):
            continue
        if src_m + 1 < cmd_mtime:
            loaded = snap.get("flags") if isinstance(snap.get("flags"), dict) else {}
            # مقدارِ redact-شده اصلاً قابلِ مقایسه نیست — drift ِ کاذب نسازیم.
            drift = sorted(k for k, v in file_flags.items()
                           if k in loaded
                           and str(loaded[k]).strip() != REDACTED
                           and str(loaded[k]).strip() != str(v).strip())
            rows.append(_row(
                f"flags.fresh.{proc}", WARN,
                f"{proc} (PID {snap.get('pid')}) فلگ‌ها را از نسخهٔ "
                f"{_fa_age(cmd_mtime - src_m)} قدیمی‌ترِ فایل خوانده"
                + (f" — اختلافِ واقعی: {', '.join(drift)}" if drift else
                   " — ولی هیچ مقداری عوض نشده"),
                f"پروسهٔ {proc} را ری‌استارت کن تا فلگِ امروز را بخواند"))
        else:
            rows.append(_row(f"flags.fresh.{proc}", OK,
                             f"{proc} فلگ‌ها را از نسخهٔ جاریِ فایل خوانده", ""))
    return rows


def _check_telegram(P: dict) -> list:
    rows = []
    cfg_path = P["state"] / "telegram" / "center-config.json"
    cfg, err = _read_json(cfg_path)
    if not isinstance(cfg, dict):
        return [_row("telegram.config", BLOCKER,
                     f"center-config.json خوانده نشد ({err})",
                     "مرکز را یک بار بالا بیاور تا config را بسازد")]

    chat_id = cfg.get("chat_id")
    if isinstance(chat_id, int) and chat_id != 0:
        rows.append(_row("telegram.chat_id", OK,
                         "chat_id ِ گروه ثبت است", ""))
    else:
        rows.append(_row("telegram.chat_id", BLOCKER,
                         f"chat_id نامعتبر است: {chat_id!r}",
                         "TG_CENTER_CHAT_ID را در env ست کن و مرکز را ری‌استارت"))

    topics = cfg.get("topics") if isinstance(cfg.get("topics"), dict) else {}
    missing = [t for t in CONTRACT_LEG_TOPICS
               if not isinstance(topics.get(t), int) or int(topics.get(t)) <= 0]
    if not missing:
        rows.append(_row("telegram.topics", OK,
                         f"هر ۸ تاپیکِ قرارداد ثبت است "
                         f"(+{len(topics) - len(CONTRACT_LEG_TOPICS)} تاپیکِ غیرِقرارداد)",
                         ""))
    else:
        rows.append(_row("telegram.topics", BLOCKER,
                         "تاپیکِ غایب/نامعتبر: " + "، ".join(missing),
                         "تاپیکِ فوروم را در گروه بساز و شناسه‌اش را در "
                         "center-config.json → topics ثبت کن"))

    guide_gaps = [k for k in ("guide_message_id", "guide_hash",
                              "dm_guide_message_id", "dm_guide_hash")
                  if not cfg.get(k)]
    if not guide_gaps:
        rows.append(_row("telegram.guide", OK,
                         f"راهنمای گروه (msg {cfg.get('guide_message_id')}) و "
                         f"راهنمای DM (msg {cfg.get('dm_guide_message_id')}) پین‌اند "
                         f"و hash دارند", ""))
    else:
        rows.append(_row("telegram.guide", BLOCKER,
                         "کلیدِ راهنما غایب: " + "، ".join(guide_gaps),
                         "مرکز راهنما را در بوت پین می‌کند — ری‌استارت کن و "
                         "دوباره بسنج (guide.py را دستی نفرست)"))

    home = cfg.get("home_message_id")
    if home:
        rows.append(_row("telegram.home", OK,
                         f"کارتِ خانهٔ DM پین است (msg {home})", ""))
    else:
        rows.append(_row("telegram.home", BLOCKER,
                         "home_message_id ست نشده — DM کارتِ خانه ندارد",
                         "مرکز را ری‌استارت کن تا خانه را دوباره پین کند"))

    ids = cfg.get("leg_card_ids") if isinstance(cfg.get("leg_card_ids"), dict) else {}
    lo, hi = SPY_ID_RANGE
    spies = sorted(f"{k}={v}" for k, v in ids.items()
                   if isinstance(v, int) and lo <= v <= hi)
    if not ids:
        rows.append(_row("telegram.leg_cards", WARN,
                         "هیچ کارتِ پایی ثبت نشده — اتاق‌ها هنوز کارتِ زنده ندارند",
                         "منتظرِ اولین چرخهٔ کارتِ مرکز بمان، بعد دوباره بسنج"))
    elif spies:
        rows.append(_row("telegram.leg_cards", BLOCKER,
                         "شناسهٔ کارتِ تستی در محدودهٔ "
                         f"{lo}–{hi} در configِ زنده: " + "، ".join(spies),
                         "این کلیدها را از center-config.json → leg_card_ids "
                         "بردار تا مرکز کارتِ واقعی بسازد"))
    else:
        rows.append(_row("telegram.leg_cards", OK,
                         f"{len(ids)} کارتِ پا ثبت است، هیچ‌کدام در محدودهٔ "
                         f"تستیِ {lo}–{hi} نیست", ""))

    kpi = cfg.get("kpi_daily")
    if kpi is None:
        rows.append(_row("telegram.kpi_daily", OK,
                         "هدفِ روزانه‌ای ست نشده (طبیعی — با «هدف روزانه ۵» "
                         "در تاپیکِ پا ست می‌شود)", ""))
    elif not isinstance(kpi, dict):
        rows.append(_row("telegram.kpi_daily", BLOCKER,
                         f"kpi_daily باید نگاشت باشد، هست: {type(kpi).__name__}",
                         "کلیدِ kpi_daily را از center-config.json بردار"))
    else:
        bad = sorted(f"{k}={v!r}" for k, v in kpi.items()
                     if not isinstance(v, int) or isinstance(v, bool)
                     or not (0 < v < 1000))
        if bad:
            rows.append(_row("telegram.kpi_daily", BLOCKER,
                             "مقدارِ نامعتبرِ KPI: " + "، ".join(bad),
                             "همان ردیف را از kpi_daily بردار و دوباره "
                             "«هدف روزانه N» بنویس"))
        else:
            rows.append(_row("telegram.kpi_daily", OK,
                             f"KPI ِ {len(kpi)} پا معتبر است", ""))
    return rows


def _store_row(name: str, path: Path, *, want_keys=(), optional=True) -> dict:
    data, err = _read_json(path)
    if data is None and err == "absent":
        if optional:
            # پوشهٔ store ممکن است هنوز ساخته نشده باشد؛ سؤالِ درست این است:
            # آیا نزدیک‌ترین جدِ موجود نوشتنی است؟ (خودِ ماژول نمی‌سازدش)
            anc = path.parent
            while not anc.exists() and anc.parent != anc:
                anc = anc.parent
            if anc.is_dir() and os.access(str(anc), os.W_OK):
                return _row(name, OK,
                            f"هنوز ساخته نشده (طبیعی) و مسیرش نوشتنی است — "
                            f"{path.name}", "")
            return _row(name, BLOCKER,
                        f"{path.name} نیست و مسیرِ {anc} هم نوشتنی/موجود نیست",
                        f"پوشهٔ {path.parent} را بساز/آزاد کن")
        return _row(name, BLOCKER, f"{path.name} غایب است",
                    f"{path} را از مسیرِ تولیدی‌اش بساز")
    if data is None:
        return _row(name, BLOCKER, f"{path.name} خوانده نشد ({err})",
                    f"محتوای {path} را بررسی کن — JSON ِ سالم لازم است")
    if not isinstance(data, dict):
        return _row(name, BLOCKER,
                    f"{path.name} باید شیء باشد، هست: {type(data).__name__}",
                    f"{path} را به شکلِ قراردادی برگردان")
    missing = [k for k in want_keys if k not in data]
    if missing:
        return _row(name, BLOCKER,
                    f"{path.name} کلیدِ لازم ندارد: {', '.join(missing)}",
                    f"{path} را با شکلِ قراردادی جایگزین کن")
    return _row(name, OK, f"{path.name} سالم است ({len(data)} کلید)", "")


def _check_stores(P: dict) -> list:
    st = P["state"]
    rows = [
        _store_row("stores.reminders", st / "reminders" / "reminders.json",
                   want_keys=("items",)),
        _store_row("stores.question_budget",
                   st / "telegram" / "question-budget.json",
                   want_keys=("week", "used", "queue")),
        _store_row("stores.lead_pipeline", st / "legs" / "lead-pipeline.json",
                   want_keys=("stuck", "followups")),
    ]
    legs_dir = st / "telegram" / "legs"
    try:
        files = sorted(p for p in legs_dir.glob("*-tasks.json"))
    except OSError:
        files = []
    if not legs_dir.is_dir():
        rows.append(_row("stores.leg_tasks", OK,
                         "هنوز هیچ پایی کار ندارد (پوشهٔ legs ساخته نشده)", ""))
    elif not files:
        rows.append(_row("stores.leg_tasks", OK,
                         "پوشهٔ کارِ پاها هست و خالی است — هنوز کاری صف نشده", ""))
    else:
        bad = []
        total = 0
        for p in files:
            data, err = _read_json(p)
            if not isinstance(data, dict):
                bad.append(f"{p.name}({err or 'not-dict'})")
            else:
                total += len(data.get("tasks") or data.get("items") or [])
        if bad:
            rows.append(_row("stores.leg_tasks", BLOCKER,
                             "فایلِ کارِ خراب: " + "، ".join(bad),
                             "همان فایل را از .bak کنارش برگردان"))
        else:
            rows.append(_row("stores.leg_tasks", OK,
                             f"{len(files)} فایلِ کارِ پا سالم است "
                             f"({total} کار)", ""))
    return rows


def _check_miniapp(P: dict, now: float, live: bool) -> list:
    rows = []
    path = P["state"] / "telegram" / "miniapp-url.json"
    data, err = _read_json(path)
    if not isinstance(data, dict):
        rows.append(_row("miniapp.url", BLOCKER,
                         f"miniapp-url.json خوانده نشد ({err})",
                         "_ops/telegram_center/run-miniapp-tunnel.ps1 را اجرا کن"))
    else:
        url = str(data.get("url") or "")
        age = _age(_mtime(path) or 0, now)
        if not url.startswith("https://"):
            rows.append(_row("miniapp.url", BLOCKER,
                             f"آدرسِ Mini App https نیست: {url[:40]!r}",
                             "تونل را دوباره بالا بیاور — تلگرام فقط https "
                             "را به‌عنوان Web App می‌پذیرد"))
        elif age > MINIAPP_MAX_S:
            rows.append(_row("miniapp.url", WARN,
                             f"فایلِ آدرسِ تونل {_fa_age(age)} است که تازه نشده "
                             f"(شروع: {data.get('started')})",
                             "run-miniapp-tunnel.ps1 را دوباره اجرا کن و "
                             "آدرسِ تازه را بسنج"))
        else:
            rows.append(_row("miniapp.url", OK,
                             f"آدرسِ https ِ تازه ({_fa_age(age)} پیش) — "
                             f"PID تونل {data.get('pid')}", ""))
    # ── ثبت، نه فقط دسترس‌پذیری (فاز ۲، ۲۰۲۶-۰۸-۰۴) ───────────────────────
    # هر ردیفِ بالا **دسترس‌پذیری** را می‌سنجد: آدرس https است، پورت جواب
    # می‌دهد. هیچ‌کدام نمی‌پرسد «تلگرام اصلاً این اپ را می‌شناسد؟» — و جوابِ
    # زندهٔ امروز `has_main_web_app=False` و منویِ `commands` بود، یعنی این
    # گزارش سبز می‌داد در حالی که هیچ مینی‌اپی ثبت نشده بود. شاهدِ رفتاری هم
    # همین را گفت: در ۸۸ ساعت لاگِ ضربه، **یک** نشستِ احرازشده.
    if not live:
        rows.append(_row("miniapp.registration", WARN,
                         "ثبتِ مینی‌اپ بررسی نشد (live=False)",
                         "با check(live=True) بسنج"))
    else:
        _mreg = None
        try:
            import miniapp_registration as _mreg  # noqa: PLC0415
            _st = _mreg.status()
        except Exception as e:  # noqa: BLE001
            _st = {"state": "unknown", "ok": False,
                   "why": f"ماژولِ ثبت در دسترس نیست ({type(e).__name__})"}
        # ⚠️ `unknown` عمداً WARN است نه OK: نبودِ داده حکم نیست، و همین
        # ترجمهٔ غلط اجازه داد چهار روز سبز ببینیم.
        _lvl = OK if _st.get("ok") else (
            WARN if _st.get("state") == "unknown" else BLOCKER)
        _msg = (_mreg.summary_line(_st) if _mreg is not None
                else f"ثبتِ مینی‌اپ: {_st.get('state')} — {_st.get('why')}")
        rows.append(_row(
            "miniapp.registration", _lvl, _msg,
            "" if _st.get("ok") else
            "اول آدرسِ پایدار (تونلِ نام‌دار)، بعد BotFather ‏/newapp یا "
            "setChatMenuButton — ثبت روی میزبانِ گذرا بی‌معنی است"))

    if not live:
        rows.append(_row("miniapp.gateway", WARN,
                         "پورتِ ۸۷۷۴ بررسی نشد (live=False)",
                         "با check(live=True) بسنج"))
    elif _port_open(8774):
        rows.append(_row("miniapp.gateway", OK,
                         "دروازهٔ ۸۷۷۴ گوش می‌دهد (تونل فقط به همین می‌خورد)", ""))
    else:
        rows.append(_row("miniapp.gateway", BLOCKER,
                         "دروازهٔ ۸۷۷۴ خاموش است — تونل به جایی نمی‌رسد",
                         "python _ops/telegram_center/miniapp_gateway.py را "
                         "با OCTOPUS_TG_MINIAPP=1 بالا بیاور"))
    return rows


def _check_vault(P: dict) -> list:
    """vault ِ نوشتنی + **مهم‌ترین چک**: آیا پروسه‌ها ORG_ROOT دارند؟

    capture (`capture._vault_root`) بدونِ ORG_ROOT استثنا می‌دهد و مرکز آن را
    می‌بلعد ⇒ بایگانی و یادآوریِ زبانِ طبیعی بی‌صدا از کار می‌افتند.
    ask_vault بدونِ ORG_ROOT روی cwd (یعنی درختِ کد) جست‌وجو می‌کند.
    """
    rows = []
    root = P["org"]

    launchers = (P["ops"] / "OCTOPUS-flags.cmd",
                 P["ops"] / "telegram_center" / "RUN-TG-CENTER.bat")
    setters = []
    for lp in launchers:
        try:
            text = lp.read_text("utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("set ") and s[4:].strip().lower().startswith("org_root="):
                setters.append(lp.name)
                break
    if setters:
        rows.append(_row("vault.org_root", OK,
                         "ORG_ROOT در " + "، ".join(setters) + " ست می‌شود",
                         ""))
    else:
        rows.append(_row(
            "vault.org_root", BLOCKER,
            "هیچ لانچری ORG_ROOT را ست نمی‌کند "
            f"(بررسی‌شده: {'، '.join(p.name for p in launchers)}؛ "
            f"env ِ همین پروسه: {P['org_env'] or '<غایب>'}) — "
            "capture بدونِ آن ValueError می‌دهد و مرکز آن را می‌بلعد "
            "(بایگانی و یادآوریِ زبانِ طبیعی بی‌صدا می‌میرند)، "
            "و ask_vault روی cwd ِ درختِ کد جست‌وجو می‌کند",
            "خطِ `set ORG_ROOT=F:\\backup` را به OCTOPUS-flags.cmd اضافه کن "
            "و هر چهار پروسه را ری‌استارت کن"))

    tg_dir = root / "10 - Telegram processing"
    raw = tg_dir / "Raw"
    if raw.is_dir():
        ok_w = os.access(str(raw), os.W_OK)
        rows.append(_row("vault.raw", OK if ok_w else BLOCKER,
                         f"پوشهٔ Raw هست و {'نوشتنی' if ok_w else '**فقط‌خواندنی**'} است",
                         "" if ok_w else f"دسترسیِ نوشتن روی {raw} را باز کن"))
    elif tg_dir.is_dir():
        ok_w = os.access(str(tg_dir), os.W_OK)
        rows.append(_row(
            "vault.raw", OK if ok_w else BLOCKER,
            "پوشهٔ Raw هنوز ساخته نشده ولی «10 - Telegram processing» "
            f"{'نوشتنی است (capture خودش می‌سازد)' if ok_w else 'نوشتنی نیست'}"
            " — یعنی تا امروز هیچ capture ای بایگانی نشده",
            "" if ok_w else f"دسترسیِ نوشتن روی {tg_dir} را باز کن"))
    else:
        rows.append(_row("vault.raw", BLOCKER,
                         f"پوشهٔ «10 - Telegram processing» زیرِ {root} نیست",
                         "ریشهٔ vault را درست کن (ORG_ROOT) یا پوشه را بساز"))

    tpl = root / "_Templates"
    if tpl.is_dir():
        n = len(list(tpl.glob("*.md")))
        rows.append(_row("vault.templates", OK,
                         f"_Templates هست ({n} قالب)", ""))
    else:
        rows.append(_row("vault.templates", BLOCKER,
                         f"_Templates زیرِ {root} نیست — نوتِ نو قالب ندارد",
                         "ریشهٔ vault را درست کن (ORG_ROOT)"))
    return rows


def _check_lead(P: dict) -> list:
    # ⚠️ کد از درختِ **خودِ ماژول** import می‌شود (`_OPS`)، نه از `P["ops"]`.
    # داده env-اول است (harness ایزوله‌اش می‌کند) ولی کد همان کدی است که این
    # فایل داخلش زندگی می‌کند — وگرنه پروب کدِ درختِ دیگری را می‌سنجد.
    rows = []
    legs = _OPS / "legs"

    ok_cf, cf = _importable("consent_firewall", legs)
    rows.append(_row("lead.consent_firewall", OK if ok_cf else BLOCKER,
                     "فایروالِ رضایت import می‌شود (دروازهٔ ساختاریِ ارسال)"
                     if ok_cf else f"فایروالِ رضایت import نشد — {cf}",
                     "" if ok_cf else "تا وقتی این import نشود، هیچ مسیرِ "
                                      "لیدی نباید مسلح شود"))

    ok_ow, ow = _importable("outbound_worker", legs)
    if not ok_ow:
        rows.append(_row("lead.cap", BLOCKER,
                         f"outbound_worker import نشد — {ow}",
                         "بدونِ این ماژول سقفِ روزانه قابلِ اثبات نیست"))
    else:
        cap = getattr(ow, "LEAD_DAILY_SEND_CAP", None)
        if cap == EXPECTED_SEND_CAP:
            rows.append(_row("lead.cap", OK,
                             f"سقفِ روزانهٔ ارسال در کد = {cap} (رأی ۱۷ منشور)",
                             ""))
        else:
            rows.append(_row("lead.cap", BLOCKER,
                             f"سقفِ روزانه {cap!r} است، نه {EXPECTED_SEND_CAP} — "
                             "عددِ سقف رأیِ مالک است",
                             "LEAD_DAILY_SEND_CAP را در _ops/legs/"
                             "outbound_worker.py به ۱۰ برگردان"))

    # ارسالِ بیرونی باید خاموش باشد؛ روشن + بی‌SMTP = دروغِ خطرناک
    outbound_on = []
    for proc in ("center", "organism"):
        snap, _e = _read_json(P["state"] / f"flags-loaded-{proc}.json")
        if isinstance(snap, dict):
            fl = snap.get("flags") if isinstance(snap.get("flags"), dict) else {}
            if _armed(fl.get("OCTOPUS_WIRE_LEAD_OUTBOUND")):
                outbound_on.append(f"{proc}(PID {snap.get('pid')})")
    smtp_present = [k for k in SMTP_ENV if str(os.environ.get(k, "")).strip()]
    if outbound_on:
        rows.append(_row(
            "lead.outbound", BLOCKER,
            "ارسالِ بیرونیِ لید در " + "، ".join(outbound_on) + " مسلح است"
            + (f" با {len(smtp_present)}/{len(SMTP_ENV)} envِ SMTP"
               if smtp_present else " **بدونِ هیچ envِ SMTP**")
            + " — امروز باید خاموش باشد",
            "OCTOPUS_WIRE_LEAD_OUTBOUND را صفر کن و پروسه را ری‌استارت کن؛ "
            "مسلح‌سازی رأیِ جداگانهٔ مالک است"))
    else:
        rows.append(_row("lead.outbound", OK,
                         "ارسالِ بیرونیِ لید خاموش است (طبقِ برنامهٔ امروز)", ""))
    if smtp_present:
        rows.append(_row("lead.smtp", WARN,
                         f"{len(smtp_present)}/{len(SMTP_ENV)} envِ SMTP ست است "
                         "در حالی که ارسال قرار نیست مسلح شود",
                         "اگر امروز ارسال نمی‌خواهی، envهای SMTP را بردار"))
    else:
        rows.append(_row("lead.smtp", OK,
                         "SMTP پیکربندی نشده (انتظارِ امروز) — ارسالِ ایمیل "
                         "ساختاراً NOT_ARMED است", ""))
    return rows


def _check_memory(P: dict) -> list:
    rows = []
    on = []
    off = []
    for proc in ("center", "organism"):
        snap, _e = _read_json(P["state"] / f"flags-loaded-{proc}.json")
        if not isinstance(snap, dict):
            off.append(f"{proc}(اسنپ‌شات غایب)")
            continue
        fl = snap.get("flags") if isinstance(snap.get("flags"), dict) else {}
        (on if _armed(fl.get("OCTOPUS_WIRE_MEMORY_DECISION")) else off).append(
            f"{proc}(PID {snap.get('pid')})")
    if off:
        rows.append(_row("memory.flag", BLOCKER,
                         "OCTOPUS_WIRE_MEMORY_DECISION در " + "، ".join(off)
                         + " بارگذاری/مسلح نیست"
                         + (" (مسلح در: " + "، ".join(on) + ")" if on else ""),
                         "در OCTOPUS-flags.cmd یک کن و آن پروسه را ری‌استارت"))
    else:
        rows.append(_row("memory.flag", OK,
                         "حافظهٔ تصمیم در " + "، ".join(on) + " مسلح است", ""))

    ok_m, m = _importable("memory.retrieval_router", _OPS)   # کد، نه داده
    rows.append(_row("memory.router", OK if ok_m else BLOCKER,
                     "روترِ بازیابیِ حافظه import می‌شود"
                     if ok_m else f"روترِ حافظه import نشد — {m}",
                     "" if ok_m else "بدونِ روتر، فلگِ حافظه بی‌مصرف است"))
    return rows


# ── API ────────────────────────────────────────────────────────────────────
def check(*, live: bool = False, now: "float | None" = None) -> dict:
    """پروبِ آمادگیِ مالک. فقط‌خواندنی: صفر نوشتن، صفر ارسال، صفر getUpdates.

    live=True فقط یک کارِ اضافه می‌کند: `connect_ex` روی ۸۷۷۲/۸۷۷۳/۸۷۷۴.
    """
    now = float(now if now is not None else time.time())
    # حتی یک `.pyc` هم ننویس — importهای probe زیرِ همین پرچم می‌افتند.
    _prev_bc = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        P = _paths()
        checks: list = []
        for fn, args in ((_check_processes, (P, now, live)),
                         (_check_flags, (P, now)),
                         (_check_telegram, (P,)),
                         (_check_stores, (P,)),
                         (_check_miniapp, (P, now, live)),
                         (_check_vault, (P,)),
                         (_check_lead, (P,)),
                         (_check_memory, (P,))):
            try:
                checks.extend(fn(*args))
            except Exception as e:                          # noqa: BLE001
                # خانوادهٔ چکِ منفجرشده خودش یک یافته است، نه یک crash.
                checks.append(_row(f"{fn.__name__.lstrip('_')}.crashed", BLOCKER,
                                   f"خودِ چک شکست: {type(e).__name__}: {e}",
                                   "این تابع را در owner_readiness.py درست کن"))
    finally:
        sys.dont_write_bytecode = _prev_bc
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def render(result: dict) -> str:
    """چک‌لیستِ فارسیِ خواندنی — همان چیزی که آدم اجرا می‌کند و می‌بیند."""
    checks = result.get("checks") or []
    n_block = sum(1 for c in checks if c.get("level") == BLOCKER)
    n_warn = sum(1 for c in checks if c.get("level") == WARN)
    n_ok = len(checks) - n_block - n_warn
    head = ("✅ آماده — هیچ مانعی نیست" if result.get("ok")
            else f"❌ آماده نیست — {n_block} مانع")
    lines = [f"آمادگیِ ساعتِ اولِ مالک — {head}",
             f"({n_ok} سبز · {n_warn} زرد · {n_block} قرمز از {len(checks)})",
             ""]
    for c in checks:
        lines.append(f"{_MARK.get(c.get('level'), '⚠️')} {c.get('name')} — "
                     f"{c.get('detail')}")
        if c.get("level") != OK and c.get("fix"):
            lines.append(f"      ↳ فیکس: {c['fix']}")
    if n_block:
        lines += ["", "موانع به ترتیب:"]
        for i, c in enumerate((x for x in checks if x.get("level") == BLOCKER), 1):
            lines.append(f"  {i}. {c['name']} — {c['fix'] or c['detail']}")
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover — بازرسیِ دستیِ آدم
    _live = "--offline" not in sys.argv
    _res = check(live=_live)
    if "--json" in sys.argv:
        print(json.dumps(_res, ensure_ascii=False, indent=1))
    else:
        print(render(_res))
    sys.exit(0 if _res["ok"] else 1)
