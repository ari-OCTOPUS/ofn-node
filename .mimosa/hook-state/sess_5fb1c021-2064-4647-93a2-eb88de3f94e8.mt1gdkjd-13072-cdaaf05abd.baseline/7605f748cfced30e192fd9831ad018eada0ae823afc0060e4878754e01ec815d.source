#!/usr/bin/env python3
"""تست ۲۰۲۷ backlog #3 — kill-switchِ drawdown زنده روی budget_gate.py.
اثبات: shadow-count پیش‌فرض (بدونِ HH_DRAWDOWN_ENFORCE، هرگز halt واقعی) ·
enforce واقعاً halted می‌زند (همان مسیرِ fail-closed ِ reserve()) ·
پنجرهٔ ۱ساعته درست prune می‌شود · spike_pct از yaml فقط سخت‌تر می‌شود (کفِ ۲۵) ·
drawdown_status() فقط‌خواندنی است (صفر side-effect) · لاگِ append-only."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("drawdown-enforcer")
sys.path.insert(0, os.environ["SCRIPTS_DIR"])
import budget_gate  # noqa: E402 — تنها enforcer، از scripts/ واقعی


def _default_yaml() -> None:
    budget_gate.BUDGETS_YAML.write_text(harness.TEST_BUDGETS, "utf-8")


def _reset_all() -> None:
    for p in (budget_gate.STATE, budget_gate.LOCK, budget_gate.DRAWDOWN_LOG):
        try:
            Path(p).unlink()
        except OSError:
            pass
    os.environ.pop(budget_gate._ENV_DRAWDOWN_ENFORCE, None)


def _spike_amount_usd(c: dict) -> float:
    """کوچک‌ترین USD ِ تک‌reserve که به‌تنهایی از spike_pct عبور می‌کند."""
    aud_needed = c["day_aud"] * (c["spike_pct"] / 100.0) * 1.05   # ۵٪ حاشیه‌ی اطمینان
    return aud_needed / c["aud"]


def t_shadow_default_no_halt_on_spike():
    """پیش‌فرض (بدونِ فلگ): spike شناسایی می‌شود (شادو-لاگ) ولی halted هرگز True نمی‌شود."""
    _default_yaml(); _reset_all()
    c = budget_gate._caps()
    r = budget_gate.reserve("ZIMAN", _spike_amount_usd(c))
    assert r["allow"] is True, r
    st = budget_gate.drawdown_status()
    assert st["spike_now"] is True, st
    assert st["enforced"] is False, st
    assert st["halted"] is False, st
    # reserve بعدی هم باید مجاز بماند (shadow اثرِ واقعی ندارد)
    r2 = budget_gate.reserve("ZIMAN", 0.01)
    assert r2["allow"] is True, r2


def t_enforce_flag_actually_halts():
    """با HH_DRAWDOWN_ENFORCE=1: عبور از spike_pct → halted=True → reserveِ بعدی رد می‌شود."""
    _default_yaml(); _reset_all()
    os.environ[budget_gate._ENV_DRAWDOWN_ENFORCE] = "1"
    c = budget_gate._caps()
    r = budget_gate.reserve("ZIMAN", _spike_amount_usd(c))
    assert r["allow"] is True, r          # همین reserve که spike را رد کرد خودش مجاز بود
    st = budget_gate.drawdown_status()
    assert st["spike_now"] is True and st["enforced"] is True and st["halted"] is True, st
    r2 = budget_gate.reserve("ZIMAN", 0.01)
    assert r2["allow"] is False and r2["reason"] == "halted", r2   # مسیرِ fail-closed ِ موجود
    os.environ.pop(budget_gate._ENV_DRAWDOWN_ENFORCE, None)


def t_no_spike_under_threshold():
    """رزروِ کوچک، زیرِ spike_pct → هرگز spike/halt."""
    _default_yaml(); _reset_all()
    c = budget_gate._caps()
    tiny = (c["day_aud"] * 0.05) / c["aud"]      # ۵٪ سقف، خیلی زیرِ ۲۵٪
    r = budget_gate.reserve("ZIMAN", tiny)
    assert r["allow"] is True, r
    st = budget_gate.drawdown_status()
    assert st["spike_now"] is False and st["halted"] is False, st


def t_old_spend_pruned_from_window():
    """ورودیِ قدیمی (خارج از پنجرهٔ ۱ساعته) نباید در pct شمرده شود."""
    _default_yaml(); _reset_all()
    d = budget_gate._roll(budget_gate._load())
    old_ts = __import__("time").time() - (budget_gate.DRAWDOWN_WINDOW_S + 600)  # ۱۰ دقیقه خارج از پنجره
    c = budget_gate._caps()
    huge_aud = c["day_aud"] * 5.0   # اگر شمرده می‌شد، قطعاً spike می‌شد
    d["recent_spend"] = [[old_ts, huge_aud]]
    budget_gate._save(d)
    st = budget_gate.drawdown_status()
    assert st["spike_now"] is False, ("ورودیِ قدیمی نباید شمرده شود: " + str(st))


def t_status_is_read_only():
    """drawdown_status() نباید recent_spend را تغییر بدهد (صفر side-effect)."""
    _default_yaml(); _reset_all()
    c = budget_gate._caps()
    budget_gate.reserve("ZIMAN", 0.01)
    before = budget_gate._load().get("recent_spend", [])
    budget_gate.drawdown_status()
    budget_gate.drawdown_status()
    after = budget_gate._load().get("recent_spend", [])
    assert before == after, (before, after)


def t_spike_pct_yaml_tighten_honored():
    """yaml سخت‌تر (spike_pct=5) از کفِ ۲۵ → همان ۵ اعمال می‌شود (SoT واقعاً می‌راند)."""
    budget_gate.BUDGETS_YAML.write_text(
        "global:\n  cap_monthly: 30\n  spike_pct: 5\nprojects: {}\n", "utf-8")
    _reset_all()
    c = budget_gate._caps()
    assert c["spike_pct"] == 5.0, c


def t_spike_pct_yaml_loosen_ignored():
    """yaml شل‌تر (spike_pct=90) از کفِ ۲۵ → کفِ هاردکد می‌ماند (هرگز looser)."""
    budget_gate.BUDGETS_YAML.write_text(
        "global:\n  cap_monthly: 30\n  spike_pct: 90\nprojects: {}\n", "utf-8")
    _reset_all()
    c = budget_gate._caps()
    assert c["spike_pct"] == 25.0, c


def t_drawdown_log_append_only():
    """هر spike یک خط به drawdown-events.jsonl اضافه می‌کند؛ فایل هرگز rewrite نمی‌شود."""
    _default_yaml(); _reset_all()
    c = budget_gate._caps()
    budget_gate.reserve("ZIMAN", _spike_amount_usd(c))
    n1 = len(budget_gate.DRAWDOWN_LOG.read_text("utf-8").splitlines())
    budget_gate.reserve("ZIMAN", _spike_amount_usd(c))
    n2 = len(budget_gate.DRAWDOWN_LOG.read_text("utf-8").splitlines())
    assert n1 >= 1 and n2 > n1, (n1, n2)


def t_legacy_behavior_unchanged_without_any_spike():
    """۰۲ reserve/release ِ معمولی، بدونِ رسیدن به spike — رفتارِ amount/allow دقیقاً قبلی."""
    _default_yaml(); _reset_all()
    r = budget_gate.reserve("ZIMAN", 0.01)
    assert r == {"allow": True, "reserved": 0.01}, r
    budget_gate.release("ZIMAN", 0.01)
    d = budget_gate._roll(budget_gate._load())
    assert d["spent_today_usd"] == 0.0, d


if __name__ == "__main__":
    failed = harness.run([
        ("پیش‌فرض: spike شناسایی می‌شود ولی halt نمی‌زند (shadow-only)",
         t_shadow_default_no_halt_on_spike),
        ("HH_DRAWDOWN_ENFORCE=1: spike واقعاً halted می‌زند", t_enforce_flag_actually_halts),
        ("زیرِ spike_pct → هرگز spike/halt", t_no_spike_under_threshold),
        ("ورودیِ خارج از پنجرهٔ ۱ساعته prune/نادیده گرفته می‌شود", t_old_spend_pruned_from_window),
        ("drawdown_status() فقط‌خواندنی است", t_status_is_read_only),
        ("spike_pct: yaml سخت‌تر از کف اعمال می‌شود", t_spike_pct_yaml_tighten_honored),
        ("spike_pct: yaml شل‌تر از کف نادیده گرفته می‌شود", t_spike_pct_yaml_loosen_ignored),
        ("لاگِ drawdown-events.jsonl append-only است", t_drawdown_log_append_only),
        ("رفتارِ legacy بدونِ spike دست‌نخورده", t_legacy_behavior_unchanged_without_any_spike),
    ])
    sys.exit(1 if failed else 0)
