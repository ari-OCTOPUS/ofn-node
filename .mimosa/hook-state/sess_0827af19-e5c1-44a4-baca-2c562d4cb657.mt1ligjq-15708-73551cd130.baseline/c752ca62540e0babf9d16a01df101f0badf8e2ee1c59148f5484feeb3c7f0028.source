#!/usr/bin/env python3
"""power.py — اکشن‌های «مرکزِ فرماندهیِ تلگرام» (رأیِ مالک 2026-07-17: مرکزِ کنترلِ همه‌چیز).

دو رده (هر دو فقط برای مالک — گیتِ from.id در center):
- ردهٔ A (برگشت‌پذیر، runtime): مکث/ادامهٔ تک‌پا — فایلِ سبکِ state/leg-<key>-paused.flag
  (قالبِ اثبات‌شدهٔ projectf-paused.flag) که wiring هر ضربان بازمی‌خواند؛ بدونِ restart.
- ردهٔ B (حساس): restart/stop/panic/فلگ/اعمالِ بودجه — پشتِ فلگِ OCTOPUS_TG_POWER
  (پیش‌فرض خاموش) + تأییدِ دوکلیک در center. تا مالک فلگ را روشن نکند، هیچ‌کدام اجرا
  نمی‌شود (fail-closed).

ناوردی‌ها:
- هیچ secret/PII هرگز echo یا لاگ نمی‌شود؛ audit فقط کلید/فعل/نتیجه (content-free).
- set_flag فقط نام‌های whitelist و فقط مقدارِ 0/1 — تزریق ساختاراً غیرممکن (F-3 آموخته).
- apply_budget فقط projects.<ORGAN>.cap_monthly را می‌نویسد (organ_gate:83 همین را
  enforce می‌کند)؛ global/floor/routing دست‌نخورده. گاردهای واقعیِ پول مستقل‌اند و
  فقط سفت‌تر می‌شوند: budget_gate کف‌سخت min(yaml,AU$2/30/500)، money_gate min(20,yaml).
- هر write اتمیک (tmp + os.replace) + backupِ تاریخ‌دار + اعتبارسنجی قبل از جایگزینی
  (yaml خراب = FREEZE کلِ متابولیسم — پس هرگز فایلِ نامعتبر جایگزین نمی‌شود).
$0 · stdlib+PyYAML (موجود) · مصرف‌کننده: center.py.
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent / "budget"), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

POWER_FLAG = "OCTOPUS_TG_POWER"          # ردهٔ B فقط وقتی "1"
ARM_FRESH_S = 180.0                       # تازگیِ تأییدِ دوکلیک (بعدش باطل)

# پاهای قابلِ مکث (system عمداً نیست — کنترلِ سیستم ردهٔ B است)
PAUSABLE_LEGS = ("lead", "ziman", "mining", "crypto", "accounting",
                 "studio_pf", "knowledge", "cartographer")

# whitelistِ فلگ‌های قابلِ toggle از تلگرام — فقط همین‌ها، هرگز free-form.
# (فلگ‌ها env هستند: اثر فقط در بوتِ بعدی — قراردادِ RUN-ORGANISM.bat:21.)
FLAG_MENU = ("OCTOPUS_OBS_ALERT", "OCTOPUS_SYNTH_EVENT_DRIVEN", "OCTOPUS_HTTP_AUTH",
             "CORTEX_IGNITION", "CORTEX_SELF_MONITOR", "CORTEX_CONSOLIDATE",
             "OCTOPUS_AUTONOMY_FREE", "EVOLVE_REQUIRE_APPROVAL")

_AUDIT = None   # تزریقِ تست؛ None → مسیرِ پیش‌فرض


def _audit_path() -> Path:
    return _AUDIT or (opslib.STATE_DIR / "telegram" / "power-audit.jsonl")


def _audit(action: str, ok: bool, detail: str = "") -> None:
    """ردِ ممیزیِ content-free — هرگز مسیرِ اکشن را نمی‌کشد."""
    try:
        p = _audit_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        opslib.append_jsonl(p, {"ts": opslib.now_iso(), "action": action,
                                "ok": bool(ok), "detail": str(detail)[:200],
                                "source": "tg-center"})
    except Exception:  # noqa: BLE001
        pass


def power_on() -> bool:
    return os.environ.get(POWER_FLAG, "0") == "1"


# ─── ردهٔ A: مکث/ادامهٔ تک‌پا (runtime، برگشت‌پذیر) ─────────────────────────────────
def _pause_path(key: str) -> Path:
    # studio_pf به فایلِ موجودش نگاشت می‌شود (business_brain.py:68 / live_loop.py:82
    # همین را هر ضربان می‌خوانند) — یک حقیقت، دو نام ممنوع.
    name = "projectf-paused.flag" if key == "studio_pf" else f"leg-{key}-paused.flag"
    return opslib.STATE_DIR / name


def leg_paused(key: str) -> bool:
    try:
        return _pause_path(key).exists()
    except OSError:
        return False


def paused_map() -> dict:
    return {k: leg_paused(k) for k in PAUSABLE_LEGS}


def pause_leg(key: str) -> tuple[bool, str]:
    """فایلِ مکث را بساز — wiring هر ضربان می‌بیند (بدونِ restart)."""
    if key not in PAUSABLE_LEGS:
        return False, f"پای ناشناخته: {key}"
    try:
        p = _pause_path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"paused via tg-center {opslib.now_iso()}\n", "utf-8")
        _audit(f"pause:{key}", True)
        return True, f"⏸ {key} مکث شد (از ضربانِ بعد)"
    except OSError as e:
        _audit(f"pause:{key}", False, type(e).__name__)
        return False, "خطای نوشتنِ فایلِ مکث"


def resume_leg(key: str) -> tuple[bool, str]:
    if key not in PAUSABLE_LEGS:
        return False, f"پای ناشناخته: {key}"
    try:
        _pause_path(key).unlink(missing_ok=True)
        _audit(f"resume:{key}", True)
        return True, f"▶️ {key} ادامه یافت"
    except OSError as e:
        _audit(f"resume:{key}", False, type(e).__name__)
        return False, "خطای حذفِ فایلِ مکث"


# ─── ردهٔ B: کنترلِ سیستم (فلگ‌گیت + دوکلیک در center) ──────────────────────────────
# استثنای اضطراری (رأی مالک 2026-07-17 «ترکیب دو بات»): پنیک/توقف/ادامه-از-پنیک بدونِ
# فلگِ قدرت هم کار می‌کنند (فقط-مالک + دوکلیک سرِ جایش). چرا: بعد از HALT/STOP خودِ
# organism می‌میرد و باتِ قدیم (threadِ داخلش) هم با آن — تنها کانالِ بازمانده همین مرکز
# است؛ ترمزِ اضطراری نباید پشتِ قفل باشد (توقف = جهتِ امنِ fail-safe). ادامه-از-پنیک هم
# اضطراری است چون RUN-ORGANISM.bat در نبودِ STOP-ORGANISM حلقه می‌زند و با پاک‌شدنِ
# HALT-ALL خودکار احیا می‌شود. restart/فلگ/بودجه (تغییرِ حالتِ ریسک‌دار) قفل می‌مانند.
EMERGENCY_ACTIONS = frozenset({"panic", "stop", "resume-all"})


def _isolation_mismatch() -> str:
    """آیا این پروسه *ادعای* ایزوله‌بودن دارد ولی نشانگر در درختِ **زنده** می‌افتد؟

    حادثهٔ ۲۰۲۶-۰۷-۲۸: یک پروب `power` را بعد از ماژولِ دیگری import کرد، وقتی
    `opslib` از قبل با مسیرهای زنده لود شده بود. پنج تابعِ قدرت در یک ثانیه صدا
    زده شدند و `stop_organism()` یک `STOP-ORGANISM` واقعی نوشت. ارگانیسم و مرکز
    ۳۰ دقیقه خوابیدند و مالک باید دستی فایل را پاک می‌کرد.

    `harness.setup` درست کار می‌کند وقتی **اول** صدا زده شود؛ شکست وقتی است که
    `opslib` زودتر بایند شده باشد. آن ناسازگاری دقیقاً همین‌جا قابلِ دیدن است:
    `ORG_ROOT` به temp اشاره می‌کند و نشانگر جای دیگری می‌افتد.

    ⚠️ در هر ابهامی رشتهٔ خالی برمی‌گرداند، یعنی **اجازه**. این عمدی است: بستنِ
    ترمزِ اضطراریِ واقعی بدتر از یک نشانگرِ سرگردان است. گارد فقط حالتی را رد
    می‌کند که خودش قابلِ اثبات باشد.
    """
    try:
        import os as _os
        from pathlib import Path as _P
        root = str(_os.environ.get("ORG_ROOT", "") or "").strip()
        if not root:
            return ""                      # ادعای ایزوله‌بودن نیست → تولید
        claimed = _P(root).resolve()
        target = _P(opslib.STOP_ORGANISM).resolve()
        if claimed == target or claimed in target.parents:
            return ""                      # سازگار
        return f"ORG_ROOT={claimed} ولی نشانگر در {target} می‌افتد"
    except Exception:  # noqa: BLE001 — گاردِ خراب هرگز ترمز را نمی‌بندد
        return ""


def _deny_if_off(action: str) -> "tuple[bool, str] | None":
    # ناسازگاریِ ایزوله‌سازی قبل از هر چیز — حتی قبل از ترمزِ اضطراری. اگر پروسه
    # فکر می‌کند در sandbox است، هیچ عملی نباید به درختِ زنده برسد؛ «اضطراری»
    # بودنِ عمل این را عوض نمی‌کند، چون آن اضطرار هم ساختگی است.
    _mm = _isolation_mismatch()
    if _mm:
        _audit(action, False, "isolation-mismatch")
        return False, ("🧪 ایزوله‌سازیِ ناسازگار — این پروسه ادعای sandbox دارد "
                       f"ولی نشانگر به درختِ زنده می‌رفت. ({_mm})")
    if action in EMERGENCY_ACTIONS:
        return None   # ترمزِ اضطراری هرگز قفل نیست (فقط-مالک + دوکلیک در center)
    if not power_on():
        _audit(action, False, "power-flag-off")
        return False, f"🔒 {POWER_FLAG} خاموش است — اول در OCTOPUS-flags.cmd روشنش کن"
    return None


def restart_organism() -> tuple[bool, str]:
    """restartِ روتین: STOP-ORGANISM + RESTART-REQUESTED → ارگانیسم تمیز خارج می‌شود و
    RUN-ORGANISM.bat:25-33 هر دو را پاک کرده با envِ تازه دوباره بالا می‌آورد (≤۵ دقیقه)."""
    d = _deny_if_off("restart")
    if d:
        return d
    try:
        opslib.STOP_ORGANISM.write_text("tg-center routine restart\n", "utf-8")
        (opslib.OPS / "RESTART-REQUESTED").write_text(opslib.now_iso() + "\n", "utf-8")
        _audit("restart", True)
        return True, "♻️ درخواستِ ری‌استارت ثبت شد — ارگانیسم تا ~۵ دقیقه با فلگ‌های تازه برمی‌گردد"
    except OSError as e:
        _audit("restart", False, type(e).__name__)
        return False, "خطای نوشتنِ سنتینل"


def stop_organism() -> tuple[bool, str]:
    """توقفِ کامل (بدونِ RESTART-REQUESTED → bat در حالتِ stopped می‌ماند)."""
    d = _deny_if_off("stop")
    if d:
        return d
    try:
        opslib.STOP_ORGANISM.write_text("tg-center stop\n", "utf-8")
        _audit("stop", True)
        return True, "⛔ STOP-ORGANISM نوشته شد — تا حذفش نکنی بالا نمی‌آید"
    except OSError as e:
        _audit("stop", False, type(e).__name__)
        return False, "خطای نوشتنِ سنتینل"


def panic() -> tuple[bool, str]:
    """HALT-ALL — مرزِ سختِ سراسری؛ هر حلقه/کانکتور بی‌استثنا می‌ایستد."""
    d = _deny_if_off("panic")
    if d:
        return d
    try:
        opslib.raise_halt_all("tg-center panic button")
        _audit("panic", True)
        return True, "🚨 HALT-ALL — همه‌چیز ایستاد. ادامه: دکمهٔ ▶️ یا حذفِ _ops/HALT-ALL"
    except Exception as e:  # noqa: BLE001
        _audit("panic", False, type(e).__name__)
        return False, "خطا در raise_halt_all"


def resume_all() -> tuple[bool, str]:
    """پاک‌کردنِ HALT-ALL (فقط پنیک را برمی‌دارد؛ STOP-ORGANISM جدا است)."""
    d = _deny_if_off("resume-all")
    if d:
        return d
    try:
        opslib.clear_halt_all()
        _audit("resume-all", True)
        return True, "▶️ HALT-ALL برداشته شد"
    except Exception as e:  # noqa: BLE001
        _audit("resume-all", False, type(e).__name__)
        return False, "خطا در clear_halt_all"


# ─── فلگ‌ها (env — اثر در بوتِ بعدی؛ صداقتِ کامل در پیام) ───────────────────────────
def _flags_cmd_path() -> Path:
    return opslib.OPS / "OCTOPUS-flags.cmd"


def flag_state(name: str) -> str:
    """وضعیتِ فعلی: envِ همین پروسه (زنده) + خطِ فایل (بوتِ بعد). فقط نمایش."""
    env_v = os.environ.get(name)
    file_v = None
    try:
        txt = _flags_cmd_path().read_text("utf-8", errors="replace")
        m = re.search(rf"^set {re.escape(name)}=(\S+)", txt, re.MULTILINE)
        if m:
            file_v = m.group(1)
    except OSError:
        pass
    return f"env={env_v if env_v is not None else '—'} · file={file_v if file_v is not None else '—'}"


def set_flag(name: str, on: bool) -> tuple[bool, str]:
    """ویرایشِ جراحیِ OCTOPUS-flags.cmd: فقط whitelist، فقط 0/1، اتمیک، ASCII-only.
    صادق: اثر فقط در بوتِ بعدی (فلگ‌ها env هستند — wiring.py:30)."""
    d = _deny_if_off(f"flag:{name}")
    if d:
        return d
    if name not in FLAG_MENU:
        _audit(f"flag:{name}", False, "not-whitelisted")
        return False, "این فلگ در whitelist نیست"
    val = "1" if on else "0"
    p = _flags_cmd_path()
    try:
        txt = p.read_text("utf-8", errors="replace") if p.exists() else "@echo off\n"
        line = f"set {name}={val}"
        pat = rf"^set {re.escape(name)}=\S*$"
        if re.search(pat, txt, re.MULTILINE):
            new = re.sub(pat, line, txt, count=1, flags=re.MULTILINE)
        else:
            sep = "" if txt.endswith("\n") else "\n"
            new = txt + f"{sep}rem tg-center toggle\n{line}\n"
        tmp = p.with_suffix(".cmd.tmp")
        tmp.write_text(new, "utf-8")
        os.replace(tmp, p)
        _audit(f"flag:{name}={val}", True)
        return True, f"🚩 {name}={val} نوشته شد — اثر در بوتِ بعدی (دکمهٔ ♻️ ری‌استارت)"
    except OSError as e:
        _audit(f"flag:{name}", False, type(e).__name__)
        return False, "خطای نوشتنِ OCTOPUS-flags.cmd"


def _flag_file_on(name: str) -> bool:
    """وضعِ فلگ در فایل (بوتِ بعد)؛ اگر خطی نبود، envِ فعلی مبنا."""
    try:
        txt = _flags_cmd_path().read_text("utf-8", errors="replace")
        m = re.search(rf"^set {re.escape(name)}=(\S+)", txt, re.MULTILINE)
        if m:
            return m.group(1) == "1"
    except OSError:
        pass
    return os.environ.get(name, "0") == "1"


def toggle_flag(name: str) -> tuple[bool, str]:
    """flipِ وضعِ فایل (نه env) — set_flag همهٔ گاردها را دارد."""
    return set_flag(name, not _flag_file_on(name))


# ─── اعمالِ بودجه (حکمِ مالک — ایجنت فقط قلم است) ──────────────────────────────────
def _latest_epoch() -> dict:
    try:
        d = opslib.BUDGET_DIR / "epochs"
        files = sorted(d.glob("epoch-*.json"), key=lambda x: x.name, reverse=True) \
            if d.exists() else []
        if not files:
            return {}
        import json
        return json.loads(files[0].read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def apply_budget() -> tuple[bool, str]:
    """گرنت‌های آخرین epoch (allocation_dry) را به‌عنوانِ سقفِ ماهانهٔ هر ارگان
    (projects.<ORGAN>.cap_monthly) در budgets.yaml می‌نویسد — همان کلیدی که
    organ_gate:83 enforce می‌کند. ویرایشِ جراحیِ متنی (کامنت‌ها سالم)، backup،
    اعتبارسنجیِ کامل قبل از جایگزینی. گاردهای سراسریِ پول مستقل و دست‌نخورده‌اند."""
    d = _deny_if_off("budget-apply")
    if d:
        return d
    ep = _latest_epoch()
    ad = ep.get("allocation_dry") if isinstance(ep.get("allocation_dry"), dict) else {}
    grants = ad.get("grants") if isinstance(ad.get("grants"), dict) else {}
    if not grants:
        _audit("budget-apply", False, "no-epoch-grants")
        return False, "هیچ epochِ تخصیصی نیست — اول governor باید بتپد"
    yp = opslib.BUDGETS_YAML
    try:
        import yaml
        txt = yp.read_text("utf-8")
        base = yaml.safe_load(txt) or {}
        projects = base.get("projects") or {}
        applied, skipped = [], []
        new_txt = txt
        for organ, g in grants.items():
            if not isinstance(g, dict) or organ not in projects:
                skipped.append(organ)
                continue
            try:
                cap = round(float(g.get("total_month_aud") or 0), 2)
            except (TypeError, ValueError):
                skipped.append(organ)
                continue
            # خطِ inline-dictِ همان ارگان: `  ORGAN: {…}` — cap_monthly را set/insert کن
            m = re.search(rf"^(\s*{re.escape(organ)}:\s*\{{)([^}}]*)(\}})",
                          new_txt, re.MULTILINE)
            if not m:
                skipped.append(organ)
                continue
            inner = m.group(2)
            if re.search(r"\bcap_monthly\s*:", inner):
                inner2 = re.sub(r"\bcap_monthly\s*:\s*[0-9.]+",
                                f"cap_monthly: {cap}", inner, count=1)
            else:
                inner2 = f"cap_monthly: {cap}, " + inner.lstrip()
            new_txt = new_txt[:m.start(2)] + inner2 + new_txt[m.end(2):]
            applied.append(f"{organ}=AU${cap}")
        if not applied:
            _audit("budget-apply", False, "nothing-applicable")
            return False, "هیچ ارگانِ قابلِ‌اعمالی نبود"
        # اعتبارسنجی قبل از جایگزینی — فایلِ خراب = FREEZE متابولیسم؛ پس هرگز.
        parsed = yaml.safe_load(new_txt)
        if not isinstance(parsed, dict) or "global" not in parsed or "projects" not in parsed:
            _audit("budget-apply", False, "validation-failed")
            return False, "اعتبارسنجیِ yaml شکست — هیچ‌چیز نوشته نشد"
        bak = yp.with_name(f"budgets.yaml.bak-{time.strftime('%Y%m%dT%H%M%S')}")
        bak.write_text(txt, "utf-8")
        tmp = yp.with_suffix(".yaml.tmp")
        tmp.write_text(new_txt, "utf-8")
        os.replace(tmp, yp)
        try:
            opslib.load_budgets(force=True)   # کشِ همین پروسه؛ ارگانیسم در بوت/چرخهٔ بعد
        except Exception:  # noqa: BLE001
            pass
        _audit("budget-apply", True, ";".join(applied))
        note = f" · ردشده: {len(skipped)}" if skipped else ""
        return True, ("💰 اعمال شد: " + " · ".join(applied) + note
                      + "\n(سقف‌های سختِ سراسری دست‌نخورده — فقط سفت‌تر)")
    except Exception as e:  # noqa: BLE001
        _audit("budget-apply", False, type(e).__name__)
        return False, f"خطای اعمال ({type(e).__name__}) — هیچ‌چیز نوشته نشد"


# دیسپچِ اکشن‌های دوکلیکِ ردهٔ B — centre فقط با کلیدِ کوتاه صدا می‌زند
POWER_ACTIONS = {
    "rs": ("♻️ ری‌استارتِ ارگانیسم (با فلگ‌های تازه)", restart_organism),
    "st": ("⛔ توقفِ کاملِ ارگانیسم", stop_organism),
    "pn": ("🚨 پنیک — HALT-ALL همه‌چیز", panic),
    "re": ("▶️ برداشتنِ پنیک (HALT-ALL)", resume_all),
    "ba": ("💰 اعمالِ سقف‌های epoch به budgets.yaml", apply_budget),
}
