#!/usr/bin/env python3
"""integration — نقشهٔ اتصالِ **پیشنهادی**. هیچ‌چیز اعمال نمی‌شود.

این فایل عمداً اجرایی نیست: فقط توصیف می‌کند که اگر روزی رأیِ مالک آمد، دقیقاً
کجا و چطور وصل می‌شود. دلیلِ وجودش این است که «قدمِ بعدی» نباید در ذهنِ کسی
بماند — و همان‌قدر مهم، نباید به‌صورتِ کدِ نیمه‌وصلِ خفته روی دیسک باشد که یک
فلگ آن را بیدار کند.

هیچ import از `organism`, `wiring`, `test_cycle`, `world_discovery` — نه امروز
نه بعداً. وابستگی یک‌طرفه است:

    artifact ِ مولد  →  لایهٔ ترجمه (خارج از این پکیج)  →  action-request.v1

`action_bridge` هرگز داخلِ هیچ مولدی را import نمی‌کند، و هیچ مولدی داخلِ
executor را.

$0 · stdlib · صفر side effect · صفر caller.
"""
from __future__ import annotations

STATUS = "IMPLEMENTED_NOT_INTEGRATED"

# ── جایی که یک روز صداکننده می‌نشیند (پیشنهاد، اعمال‌نشده) ──────────────────
PROPOSED_CALLER = {
    "where": "_ops/test_cycle.py::run — بعد از ثبتِ روش، قبل از دفتر",
    "shape": (
        "req = translate(method, prereg_row)      # لایهٔ ترجمه، بیرون از این پکیج\n"
        "pl  = planner.plan(req, sandbox_root=SANDBOX, prereg_lookup=prereg.for_id)\n"
        "rc  = executor.execute(req, pl, sandbox_root=SANDBOX, ...)\n"
        "out['action'] = {k: rc['receipt'][k] for k in ('status','classification')}"
    ),
    "flag": "OCTOPUS_WIRE_ACTION_BRIDGE (وجود ندارد — عمداً ساخته نشد)",
    "why_not_yet": (
        "۱) governance هنوز A2 را نبسته (VQ-SELFGOAL-002، چهار پیش‌شرطِ مکانیکی)\n"
        "۲) لایهٔ ترجمهٔ «متنِ روش → action_type» نوشته نشده و **نباید** با مدل\n"
        "   ساخته شود: نگاشتی که مدل انتخابش کند یعنی متن دوباره مجوز شده\n"
        "۳) sandbox ِ تولیدی و مسیرِ رسید تعیین نشده‌اند"
    ),
}

# ── نگاشتِ کلاسِ کشف (GLM) به کلاسِ عمل — قراردادِ آینده ─────────────────────
# دو سمت هرگز هم را import نمی‌کنند؛ یک لایهٔ ترجمهٔ سومی این جدول را می‌خواند.
DISCOVERY_TO_ACTION = {
    "E0": "A0",   # مشاهدهٔ عمومی
    "E1": "A1",   # artifact داخلی
    "E2": "A3",   # چیزی که مالک باید تصمیم بگیرد
    "E3": "A4",   # اثرِ بیرونی
    "E4": "A5",   # پول/تعهد
}

# ── چک‌لیستِ بازبینیِ handoff ِ GLM (فقط review، نه اتصال) ───────────────────
HANDOFF_REVIEW_CHECKLIST = (
    "خروجی pure-data و نسخه‌دار است؟",
    "external effect صفر است؟",
    "cost صفر است؟",
    "source/evidence/falsifier در هر کشف هست؟",
    "owner gate صریح است (کارت ≠ مجوز)؟",
    "prompt-injection isolation دارد — متنِ وب نمی‌تواند کلاس را پایین بیاورد؟",
    "کشف قابلِ ترجمه به action-request.v1 است؟",
    "source_component هیچ privilege نمی‌گیرد؟",
    "E0..E4 به A0/A1/A3/A4/A5 نگاشت می‌شوند؟",
    "هیچ importِ دوطرفه‌ای نیست؟",
)

# ── چیزهایی که این پکیج **نمی‌کند** — تا خواننده حدس نزند ───────────────────
NON_CAPABILITIES = (
    "هیچ ارسالِ بیرونی — تابعش نوشته نشده، نه اینکه فلگش خاموش باشد",
    "هیچ خرج — cost در هر مسیر صفر است و تست‌شده",
    "هیچ نوشتن بیرون از sandbox — scope_guard با resolve می‌بندد",
    "هیچ اجرای A2..A6 — executor مسیرشان را ندارد",
    "هیچ تغییرِ state زنده",
    "هیچ صداکنندهٔ runtime",
)


def summary() -> dict:
    return {"status": STATUS, "proposed_caller": PROPOSED_CALLER,
            "discovery_to_action": dict(DISCOVERY_TO_ACTION),
            "review_checklist": list(HANDOFF_REVIEW_CHECKLIST),
            "non_capabilities": list(NON_CAPABILITIES)}


if __name__ == "__main__":   # pragma: no cover
    import json
    print(json.dumps(summary(), ensure_ascii=False, indent=1))
