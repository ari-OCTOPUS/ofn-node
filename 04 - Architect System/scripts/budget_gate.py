#!/usr/bin/env python3
"""
budget_gate.py — شمارندهٔ بودجهٔ مشترک (تک‌منبع) برای همهٔ مصرف‌کننده‌های LLM.
قرارداد: قبل از هر call → reserve(agent, est). اگر allow: بعد از call → settle(agent, est, actual)؛
اگر call شکست خورد → release(agent, est). رزرو زیرِ قفل persist می‌شود (ضدِ race).
تست‌شده در سندباکس: race/concurrency (۲۰ موازی → دقیقاً ۱۰ مجاز، سقف $2.00)، fail-closed، rollover.
مبنا: ARCHITECT_CHARTER §۵ + LEARNING-STATE (budget). status: propose (ساخته‌شده به verdict «همه‌چیو درست کن»).
"""
import json, pathlib, datetime, os, time

STATE = pathlib.Path(os.environ.get("BUDGET_STATE", r"F:\backup\_ops\budget\budget-state.json"))
LOCK  = pathlib.Path(str(STATE) + ".lock")
# ─── v2 (A1 · SoT-read): سقف‌ها از budgets.yaml خوانده می‌شوند؛ این ثابت‌ها فقط «کفِ fail-closed»اند.
# هرگز از این‌ها شل‌تر نمی‌شویم (strictest = min(yaml, hardcode))؛ yaml ناخوانا = همین‌ها.
# اعداد: verdict آری 2026-07-09 (روز 2 · ماه 200 · فاجعه 500 AUD). قبلاً ماه=30 (verdict 2026-07-07)؛
# با routingِ GLM+Fugu و سابسکرایبِ فلت، ۲۰۰ شد (disaster/kill دست‌نخورده).
CEIL_DAY_AUD_HARD, CEIL_MONTH_AUD_HARD, DISASTER_AUD_HARD = 2.0, 200.0, 500.0
AUD_DEFAULT = 1.5    # نرخِ USD→AUD پیش‌فرض (هم‌ارزِ opslib.fx_aud_per_usd؛ yaml.global.aud_per_usd override می‌کند)
BUDGETS_YAML = pathlib.Path(os.environ.get("BUDGETS_YAML", str(STATE.parent / "budgets.yaml")))
STALE_LOCK_S = 30    # قفلِ رهاشده بعد از این ثانیه‌ها steal می‌شود (ضدِ deadlock)


def _caps():
    """v2/A1: سقف‌ها را از budgets.yaml (تک‌منبع حقیقت) می‌خواند. fail-closed:
      • yaml ناخوانا/غایب/بی‌PyYAML → کفِ هاردکد (هرگز نامحدود، هرگز crash).
      • cap شل‌تر از هاردکد در yaml → هاردکد می‌ماند (strictest = min).
    فقط سقف‌ها SoT-read‌اند؛ نرخ ارز آینهٔ opslib است (yaml.aud_per_usd یا 1.5) تا دو لایه واگرا نشوند.
    بی‌کش — هر بار تازه می‌خواند تا ویرایش مالک روی yaml بدون ری‌استارت اعمال شود."""
    day, month, disaster, aud, src = (
        CEIL_DAY_AUD_HARD, CEIL_MONTH_AUD_HARD, DISASTER_AUD_HARD, AUD_DEFAULT, "hardcode-floor")
    try:
        import yaml
        g = (yaml.safe_load(BUDGETS_YAML.read_text("utf-8")) or {}).get("global", {})
        if isinstance(g, dict):
            if g.get("cap_monthly")  is not None: month    = min(month,    float(g["cap_monthly"]))
            if g.get("cap_daily")    is not None: day      = min(day,      float(g["cap_daily"]))
            if g.get("cap_disaster") is not None: disaster = min(disaster, float(g["cap_disaster"]))
            if g.get("aud_per_usd")  is not None: aud      = float(g["aud_per_usd"])
            src = "budgets.yaml ∧ hardcode-floor"
    except Exception:
        pass  # fail-closed → کفِ هاردکد
    return {"day_aud": day, "month_aud": month, "disaster_aud": disaster, "aud": aud, "src": src}


def _load():
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text("utf-8"))


def _save(d):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")


def _lock():
    for _ in range(50):
        try:
            return os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            try:  # steal a stale lock left by a crashed holder
                if time.time() - os.path.getmtime(LOCK) > STALE_LOCK_S:
                    os.unlink(LOCK); continue
            except OSError:
                pass
            time.sleep(0.1)
    raise TimeoutError("budget busy")


def _unlock(fd):
    os.close(fd)
    try:
        os.unlink(LOCK)
    except OSError:
        pass


def _roll(d):
    t = datetime.date.today().isoformat(); m = t[:7]
    if d.get("date") != t:
        d["date"] = t; d["spent_today_usd"] = 0.0
    if d.get("month") != m:
        d["month"] = m; d["spent_month_aud"] = 0.0
    for k, v in (("spent_today_usd", 0.0), ("spent_month_aud", 0.0), ("halted", False)):
        d.setdefault(k, v)
    return d


def reserve(agent, est_usd):
    fd = _lock()
    try:
        try:
            d = _roll(_load())
        except Exception:
            return {"allow": False, "reason": "state-unreadable"}   # fail-closed (نه crash)
        c = _caps()                                # v2: سقف‌ها از SoT (با کفِ fail-closed)
        if d["halted"]:
            return {"allow": False, "reason": "halted"}
        if (d["spent_today_usd"] + est_usd) * c["aud"] > c["day_aud"]:
            return {"allow": False, "reason": "daily"}
        if d["spent_month_aud"] + est_usd * c["aud"] > c["month_aud"]:
            d["halted"] = True; _save(d); return {"allow": False, "reason": "monthly-halt"}
        d["spent_today_usd"] += est_usd            # ← رزرو واقعاً persist می‌شود
        d["spent_month_aud"] += est_usd * c["aud"]
        _save(d)
        return {"allow": True, "reserved": est_usd}
    finally:
        _unlock(fd)


def settle(agent, est_usd, actual_usd):
    """بعد از call: تخمین را با هزینهٔ واقعی جایگزین کن."""
    fd = _lock()
    try:
        c = _caps()                                # v2: نرخ/خطِ فاجعه از SoT (با کفِ fail-closed)
        d = _roll(_load()); delta = actual_usd - est_usd
        d["spent_today_usd"] = max(0.0, d["spent_today_usd"] + delta)
        d["spent_month_aud"] = max(0.0, d["spent_month_aud"] + delta * c["aud"])
        if d["spent_month_aud"] >= c["disaster_aud"]:
            d["halted"] = True                     # خطِ فاجعه (D-22) = halt کامل
        _save(d); return d
    finally:
        _unlock(fd)


def release(agent, est_usd):
    """اگر call شکست خورد → رزرو پس داده می‌شود (بدونِ نشتِ بودجه)."""
    return settle(agent, est_usd, 0.0)


if __name__ == "__main__":
    # CLI کوچک برای بازرسی: python -X utf8 budget_gate.py  → سقف‌های مؤثر (SoT) + وضعیتِ امروز
    try:
        print(json.dumps({"caps_effective": _caps(), "state": _roll(_load())},
                         ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
