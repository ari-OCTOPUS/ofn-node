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
CEIL_DAY_AUD, CEIL_MONTH_AUD, DISASTER_AUD = 2.0, 30.0, 500.0   # همه AUD — verdict V1 آری 2026-07-07 (روز 2 · ماه 30 · فاجعه 500)
AUD = 1.5            # نرخِ تقریبیِ USD→AUD (قابلِ تنظیم)
STALE_LOCK_S = 30    # قفلِ رهاشده بعد از این ثانیه‌ها steal می‌شود (ضدِ deadlock)


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
        if d["halted"]:
            return {"allow": False, "reason": "halted"}
        if (d["spent_today_usd"] + est_usd) * AUD > CEIL_DAY_AUD:
            return {"allow": False, "reason": "daily"}
        if d["spent_month_aud"] + est_usd * AUD > CEIL_MONTH_AUD:
            d["halted"] = True; _save(d); return {"allow": False, "reason": "monthly-halt"}
        d["spent_today_usd"] += est_usd            # ← رزرو واقعاً persist می‌شود
        d["spent_month_aud"] += est_usd * AUD
        _save(d)
        return {"allow": True, "reserved": est_usd}
    finally:
        _unlock(fd)


def settle(agent, est_usd, actual_usd):
    """بعد از call: تخمین را با هزینهٔ واقعی جایگزین کن."""
    fd = _lock()
    try:
        d = _roll(_load()); delta = actual_usd - est_usd
        d["spent_today_usd"] = max(0.0, d["spent_today_usd"] + delta)
        d["spent_month_aud"] = max(0.0, d["spent_month_aud"] + delta * AUD)
        if d["spent_month_aud"] >= DISASTER_AUD:
            d["halted"] = True                     # خطِ فاجعه (D-22) = halt کامل
        _save(d); return d
    finally:
        _unlock(fd)


def release(agent, est_usd):
    """اگر call شکست خورد → رزرو پس داده می‌شود (بدونِ نشتِ بودجه)."""
    return settle(agent, est_usd, 0.0)


if __name__ == "__main__":
    # CLI کوچک برای بازرسی: python budget_gate.py  → وضعیتِ امروز
    try:
        print(json.dumps(_roll(_load()), ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
