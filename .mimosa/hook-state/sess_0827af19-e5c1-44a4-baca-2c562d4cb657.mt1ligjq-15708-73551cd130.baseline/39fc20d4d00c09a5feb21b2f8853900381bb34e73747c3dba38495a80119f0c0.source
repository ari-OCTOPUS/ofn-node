"""autonomy_grant — چه کاری را اختاپوس **بدونِ پرسیدن** می‌تواند بکند.

رأیِ مالک ۲۰۲۶-۰۷-۲۷، سه دسته:
  ۱) کارهای فقط‌خواندنی — اسکن، تحلیل، ساختِ گزارش.
  ۲) تمیزکاریِ خودش — فقط داخلِ `_ops/state`.
  ۳) تنظیمِ ریتمِ خودش — درونِ کران‌هایی که از قبل تعریف شده.

چرا یک ماژولِ جدا و نه یک فلگ
─────────────────────────────
«اختیار» یک بله/خیر نیست؛ یک **مرز** است. تا امروز همه‌چیز propose-only بود،
یعنی حتی اسکنِ بی‌خطر هم یک تپِ مالک می‌خواست — و آن تپ‌ها توجهی را می‌خوردند که
باید صرفِ تصمیم‌های واقعی می‌شد. این‌جا مرز **صریح و ماشین‌خوان** می‌شود تا هر
صداکننده بتواند بپرسد «این کار داخلِ اختیارِ من است؟» و جواب یک‌جا تعریف شده باشد،
نه پخش در ده فایل.

مرزهای سختِ تخطی‌ناپذیر (هیچ‌کدام از این‌ها هرگز خودکار نیست)
─────────────────────────────────────────────────────────
پول · ارسالِ بیرونی · اعمالِ کد · حذفِ چیزی خارج از `_ops/state` · PII · secret ·
تغییرِ فلگ · هر چیزی که در `_DENY` باشد. اگر کاری در فهرستِ مجاز نباشد،
جواب **نه** است — allowlist، نه denylist.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_AUTONOMY_GRANT"
SCHEMA = "autonomy-grant.v1"

# سه دستهٔ تأییدشدهٔ مالک. کلید = نامِ دسته، مقدار = شرحِ فارسی برای کارت‌ها.
GRANTED = {
    "read_only": "اسکن، تحلیل، ساختِ گزارش — چیزی عوض نمی‌شود",
    "self_cleanup": "تمیزکاریِ فایل‌های خودش، فقط داخلِ _ops/state",
    "own_rhythm": "تنظیمِ ریتمِ خودش درونِ کران‌های تعریف‌شده",
}

# مرزِ سخت. هر رشته‌ای که این‌ها را بزند، مستقلاً از دسته، **نه** است.
_DENY = re.compile(
    r"(pay|payment|invoice|money|بانک|واریز|پرداخت|پول|فاکتور"
    r"|send|publish|post|outbound|ارسال|بفرست|منتشر"
    r"|apply|merge|deploy|commit|اعمال|کامیت|دیپلوی"
    # ⚠️ معادلِ فارسی هم لازم است — تستِ متخاصمِ همان روز «توکن را بخوان» را
    # از مرز رد کرد چون فقط `token` لاتین در الگو بود. یک الگوی امنیتی که فقط
    # نصفِ زبان‌های ورودی را بشناسد، امنیت نیست.
    r"|secret|token|api_key|credential|\.env|رمز|کلید|توکن|اعتبارنامه"
    r"|flag|فلگ|پرچم"
    r"|08 - Partner|Identity|OWNER-PROFILE|PII|هویت)", re.I)

# تمیزکاری فقط این‌جا. هر مسیرِ دیگری = نه.
_CLEANUP_ROOT = "state"

# کران‌های ریتم — مالک این‌ها را تعیین کرده، اختاپوس فقط داخلشان حرکت می‌کند.
RHYTHM_BOUNDS = {
    "daily_beat_cap": (288, 2000),
    "digest_cadence_h": (6, 48),
    "deep_think_slots": (1, 8),
}


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def may(category: str, target: str = "", value=None) -> dict:
    """آیا این کار داخلِ اختیارِ اعطاشده است؟

    خروجی: {ok: bool, why: str}. **fail-closed** — هر ابهام، هر دستهٔ ناشناخته،
    هر برخورد با مرزِ سخت، و flag خاموش → `ok=False`."""
    if not enabled():
        return {"ok": False, "why": "اختیار خاموش است — همه‌چیز تأیید می‌خواهد"}
    cat = str(category or "").strip()
    if cat not in GRANTED:
        return {"ok": False, "why": f"دستهٔ «{cat}» در اختیار نیست (allowlist)"}
    blob = f"{cat} {target}"
    if _DENY.search(blob):
        return {"ok": False, "why": "مرزِ سخت — پول/ارسال/کد/راز/PII هرگز خودکار نیست"}

    if cat == "self_cleanup":
        t = str(target or "").replace("\\", "/")
        if not t:
            return {"ok": False, "why": "تمیزکاری بدونِ مسیرِ مشخص مجاز نیست"}
        if ".." in t:
            return {"ok": False, "why": "مسیرِ بالارونده مجاز نیست"}
        try:
            rel = Path(t)
            rel = rel.relative_to(opslib.OPS) if rel.is_absolute() else rel
            parts = rel.parts
        except (ValueError, OSError):
            return {"ok": False, "why": "مسیر خارج از _ops است"}
        if not parts or parts[0] != _CLEANUP_ROOT:
            return {"ok": False, "why": f"تمیزکاری فقط داخلِ _ops/{_CLEANUP_ROOT}"}

    if cat == "own_rhythm":
        k = str(target or "")
        if k not in RHYTHM_BOUNDS:
            return {"ok": False, "why": f"«{k}» یک اهرمِ ریتمِ تعریف‌شده نیست"}
        lo, hi = RHYTHM_BOUNDS[k]
        try:
            v = float(value)
        except (TypeError, ValueError):
            return {"ok": False, "why": "مقدارِ عددی لازم است"}
        if not (lo <= v <= hi):
            return {"ok": False, "why": f"{k}={v:g} خارج از کرانِ [{lo}, {hi}]"}

    return {"ok": True, "why": GRANTED[cat]}


def card() -> str:
    """کارتِ «چه کاری را بی‌اجازه می‌کنم» — تا مالک هر وقت خواست ببیند."""
    import html
    if not enabled():
        return ("🔓 <b>اختیار: هیچ</b>\n"
                "▸ هر کاری یک تپِ توست.\n"
                "▸ نکنی: همین‌طور می‌ماند.")
    lines = ["🔓 <b>کارهایی که بی‌اجازه می‌کنم</b>"]
    for k, v in GRANTED.items():
        lines.append(f"▸ {html.escape(v)}")
    lines.append("")
    lines.append("<b>هرگز بی‌اجازه:</b> پول · ارسالِ بیرونی · اعمالِ کد · "
                 "حذف بیرونِ state · راز · PII · تغییرِ فلگ")
    lines.append("")
    lines.append("▸ نکنی: هیچ — این مرز است، نه کار. عوضش کن با یک رأی.")
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    import json
    probes = [("read_only", "اسکنِ کد", None),
              ("self_cleanup", "state/telegram/old.json", None),
              ("self_cleanup", "budget/budgets.yaml", None),
              ("own_rhythm", "daily_beat_cap", 1500),
              ("own_rhythm", "daily_beat_cap", 5000),
              ("apply_code", "x.py", None),
              ("read_only", "ارسال به مشتری", None)]
    print(json.dumps({"flag": enabled(),
                      "probes": [{"cat": c, "target": t, **may(c, t, v)}
                                 for c, t, v in probes]},
                     ensure_ascii=False, indent=1))
