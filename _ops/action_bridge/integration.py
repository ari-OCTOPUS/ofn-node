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

$0 · stdlib · صفر side effect. (تاریخچه: تا ۰۷-۳۰ «صفر caller» بود؛ حالا
صداکنندهٔ flag-gated دارد — بخشِ ACTUAL_CALLER.)
"""
from __future__ import annotations

# ۰۷-۳۰: صداکننده ساخته و مسلح شد (goal_action_bridge از test_cycle.beat).
# ۰۷-۳۱: دفترِ idempotency و nonceها persisted شدند (restart دیگر حفاظتِ replay
# را صفر نمی‌کند). این فایل از «پیشنهاد» به «سندِ واقعیتِ اتصال» ارتقا یافت —
# چون STATUS ِ دروغ همان چیزی است که self-model را گمراه می‌کرد.
STATUS = "INTEGRATED_FLAG_GATED"

# ── صداکنندهٔ واقعی (از ۰۷-۳۰؛ پیش‌بینیِ PROPOSED_CALLER ِ قدیمی محقق شد) ────
ACTUAL_CALLER = {
    "where": "_ops/goal_action_bridge.py::run_for_cycle — از test_cycle.beat",
    "shape": (
        "prep = unified_control.pipeline.prepare_records(  # exact prereg row\n"
        "    ..., ledger=_load_ledger(), used_nonces=_load_nonces())\n"
        "rc   = executor.execute(req, plan, sandbox_root=_OPS, ...)\n"
        "دفترِ mission: state/test_cycle/missions.jsonl (+cycle_id/prereg_id)"
    ),
    "flag": "OCTOPUS_WIRE_ACTION_BRIDGE — خارج از PAPER_FULL_FLAGS و flags.cmd؛"
            " غیاب = خاموش؛ مسلح‌سازی = رأیِ ثبت‌شدهٔ مالک (VQ-ACTION-BRIDGE-ARM-001)",
    "durability": "action-ledger.jsonl = دفترِ idempotency ِ persisted؛"
                  " used-nonces.json = ضدreplay ِ A3؛ replay ِ همان چرخه = NOOP",
    "still_closed": (
        "A2 همچنان BLOCK (VQ-SELFGOAL-002) · A4/A5 ساختاراً بی‌مسیر · A6 هرگز"
    ),
}

# سازگاری: خواننده‌های قدیمیِ summary() کلیدِ proposed_caller می‌بینند.
PROPOSED_CALLER = ACTUAL_CALLER

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
    "هیچ تغییرِ state زنده جز رسید/دفترِ خودش زیرِ state/test_cycle",
)


def summary() -> dict:
    return {"status": STATUS, "proposed_caller": PROPOSED_CALLER,
            "discovery_to_action": dict(DISCOVERY_TO_ACTION),
            "review_checklist": list(HANDOFF_REVIEW_CHECKLIST),
            "non_capabilities": list(NON_CAPABILITIES)}


if __name__ == "__main__":   # pragma: no cover
    import json
    print(json.dumps(summary(), ensure_ascii=False, indent=1))
