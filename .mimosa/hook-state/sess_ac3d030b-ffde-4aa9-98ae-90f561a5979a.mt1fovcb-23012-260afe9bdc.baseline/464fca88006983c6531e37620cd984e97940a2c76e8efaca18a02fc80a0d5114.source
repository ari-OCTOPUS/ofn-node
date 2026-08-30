"""
brain/evaluation.py — گزارشِ ارزیابیِ اجرای ماهانه («یک ماه نتایجو بسنجیم»).

از منابعِ موجود (بدونِ محاسبه‌ی سنگین) یک تصویرِ جمع‌بندی می‌سازد: مدتِ اجرا،
پوششِ مرزِ دانش، نسلِ تحول، پیشنهادهای کد و سرنوشتشان، مصرفِ بودجه، شمارِ پیام‌ها،
و رویدادها. نوشتنِ گزارش از میانِ guardrails (فقط outputs/).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        logger.debug("evaluation: %s failed: %s", getattr(fn, "__name__", "?"), e)
        return default


def gather() -> dict:
    """جمع‌آوریِ آمارِ اجرا از همه‌ی منابع."""
    out: dict = {"generated_at": datetime.now().isoformat(timespec="seconds")}

    # مدتِ اجرا (از daemon_state)
    def _daemon():
        from brain.daemon import _load_state
        return _load_state()
    ds = _safe(_daemon, {}) or {}
    out["daemon"] = {
        "started_at": ds.get("started_at"),
        "last_tick_at": ds.get("last_tick_at"),
        "total_ticks": ds.get("total_ticks", 0),
        "generation": ds.get("generation", 0),
    }

    out["budget"] = _safe(lambda: __import__("brain.budget", fromlist=["status"]).status(), {})
    out["notify"] = _safe(lambda: __import__("brain.notify", fromlist=["digest_status"]).digest_status(), {})
    out["code_proposals"] = _safe(lambda: __import__("brain.self_code", fromlist=["status_counts"]).status_counts(), {})

    # پوششِ مرزِ دانش
    def _frontier():
        from brain import frontier
        # تلاش برای شمارشِ سلول‌های متمایز از فایلِ frontier
        f = frontier
        for name in ("coverage", "distinct_cells", "summary"):
            if hasattr(f, name):
                v = getattr(f, name)
                return v() if callable(v) else v
        return None
    out["frontier"] = _safe(_frontier)

    # نتیجه‌گیریِ ریاضی (آخرین)
    def _conclusions():
        from config.settings import OUTPUT_DIR
        p = OUTPUT_DIR / "self_evolved" / "conclusions.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return None
    out["conclusions"] = _safe(_conclusions)

    # رویدادها
    out["events"] = _safe(lambda: __import__("brain.events", fromlist=["counts"]).counts(), {})
    return out


def render_markdown(data: dict | None = None) -> str:
    d = data or gather()
    dm = d.get("daemon", {})
    b = d.get("budget", {})
    cp = d.get("code_proposals", {})
    lines = [
        "# گزارشِ ارزیابیِ اجرای خودمختار",
        f"_تولید: {d.get('generated_at','')}_", "",
        "## اجرا",
        f"- شروع: {dm.get('started_at','—')} · آخرین tick: {dm.get('last_tick_at','—')}",
        f"- کلِ tickها: {dm.get('total_ticks',0)} · نسلِ تحول: {dm.get('generation',0)}",
        "",
        "## بودجه (تماسِ ابری)",
        f"- امروز: {b.get('cloud_calls','?')}/{b.get('cap','?')} · باقی‌مانده: {b.get('remaining','?')}",
        f"- به‌تفکیک: {b.get('by_provider',{})}",
        "",
        "## پیشنهادهای کد (خودتغییری، تأیید‌محور)",
    ]
    if cp:
        for status, n in sorted(cp.items()):
            lines.append(f"- {status}: {n}")
    else:
        lines.append("- هیچ پیشنهادی ثبت نشده")
    lines += [
        "",
        "## پیام‌رسانی",
        f"- امروز فرستاده: {d.get('notify',{}).get('sent_today','?')}/"
        f"{d.get('notify',{}).get('cap','?')} · در صف: {d.get('notify',{}).get('queued','?')}",
        "",
        "## مرزِ دانش",
        f"- {d.get('frontier') if d.get('frontier') is not None else '—'}",
        "",
        "## رویدادها",
        f"- {d.get('events', {})}",
    ]
    concl = d.get("conclusions")
    if isinstance(concl, dict) and concl.get("headline"):
        lines += ["", "## نتیجه‌گیریِ ریاضی (SOG)", f"- {concl.get('headline')}"]
    return "\n".join(lines)


def save_report() -> tuple[bool, str]:
    """گزارش را در outputs/self_evolved/monthly_report.md ذخیره می‌کند (guardrail)."""
    from config.settings import OUTPUT_DIR
    from brain import guardrails
    path = OUTPUT_DIR / "self_evolved" / "monthly_report.md"
    ok, reason = guardrails.assert_safe_write(path)
    if not ok:
        return False, reason
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(), encoding="utf-8")
    return True, str(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(render_markdown())
