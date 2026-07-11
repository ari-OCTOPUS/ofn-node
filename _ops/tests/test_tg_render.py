"""test_tg_render.py — لایهٔ نمایشِ مرکزِ تلگرام (telegram_center/render).

خالص و بدونِ شبکه: status ≤ ۵ خط + شمارشِ خطوط؛ دایجستِ پا ≤ ۳ خط؛ کیبوردِ تصمیم
دقیقاً ok/no/later:<id>؛ scrubِ containment؛ collect_feeds روی STATE_DIRِ خالیِ موقت.
هیچ فراخوانیِ شبکه و هیچ نوشتنی خارج از مینی-vaultِ harness.
"""
import io
import json
import sys
from pathlib import Path

# تلهٔ cp1252 ویندوز (ایدیمِ opslib) — این تست opslib را در import-time لود نمی‌کند
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("tg-render")

from telegram_center import render  # noqa: E402 — بعد از setup تا هر I/O ِ تنبل ایزوله باشد


# ─── status: ≤ ۵ خط، شمارشِ خطوط، ضربان، پول ────────────────────────────────────
def t_a_status_five_lines_with_lane_counts():
    feeds = {
        "board": {"counts": {"queued": 7, "running": 2, "blocked": 1,
                             "awaiting_user": 3, "done": 5, "quarantined": 0, "total": 18}},
        "guidance": {"n": 2, "items": []},
        "heart": {"period_s": 90, "production_wire": {"open": False}},
        "telemetry": {"month": {"aud": 12.5}},
        "registry": {}, "business": {},
    }
    s = render.render_status(feeds)
    lines = s.splitlines()
    assert 1 <= len(lines) <= 5, f"status must be <=5 lines, got {len(lines)}"
    for tok in ("صف 7", "▶️ 2", "⏸ 1", "🙋 3", "✅ 5", "☣️ 0"):
        assert tok in s, f"lane count missing: {tok}"
    assert s.startswith("🟡"), "awaiting_user>0 → overall must be 🟡"
    assert "90" in s and "AU$12.50" in s and "2 تصمیم" in s


def t_b_status_overall_traffic_light():
    quar = {"board": {"counts": {"quarantined": 1}}}
    calm = {"board": {"counts": {}}, "guidance": {"n": 0}}
    assert render.render_status(quar).startswith("🔴")
    assert render.render_status(calm).startswith("🟢")


def t_c_status_empty_or_broken_feeds_safe():
    for bad in ({}, None, {"board": "junk", "heart": 3, "telemetry": None}):
        s = render.render_status(bad)
        assert isinstance(s, str) and 1 <= len(s.splitlines()) <= 5


# ─── دایجستِ پا: ≤ ۳ خط + نامِ نمایشی ─────────────────────────────────────────────
def t_d_leg_digest_three_lines_max():
    d = render.render_leg_digest("lead", {"status": "🟢", "detail": "۲ لیدِ باز",
                                          "next": "پیگیریِ فردا", "extra": "x"})
    assert len(d.splitlines()) <= 3
    assert "Lead-نقاشی" in d and "۲ لیدِ باز" in d and "پیگیریِ فردا" in d
    # legِ خالی/None → یک خطِ امن، بدونِ crash
    d2 = render.render_leg_digest("ziman", None)
    assert "Ziman Galerry" in d2 and len(d2.splitlines()) <= 3


def t_e_studio_pf_default_display_name():
    d = render.render_leg_digest("studio_pf", {"status": "🟢", "detail": "فعال"})
    assert "استودیو" in d
    # config ِ مالک نامِ نمایشی را عوض می‌کند (هر دو شکل: display_names یا نگاشتِ مستقیم)
    d2 = render.render_leg_digest("studio_pf", {}, config={"display_names": {"studio_pf": "کارگاه"}})
    assert "کارگاه" in d2
    d3 = render.render_leg_digest("lead", {}, config={"lead": "نقاشیِ ساختمان"})
    assert "نقاشیِ ساختمان" in d3


def t_f_legs_eight_ordered_keys():
    assert list(render.LEGS) == ["lead", "ziman", "mining", "crypto",
                                 "accounting", "studio_pf", "system", "knowledge"]
    assert render.LEGS["studio_pf"] == "استودیو"


# ─── کارتِ تصمیم: ok/no/later:<id> ────────────────────────────────────────────────
def t_g_decision_keyboard_callback_format():
    item = {"q": "تأیید کنم؟", "why": "منتظرِ رأیِ توست", "source": "approval", "id": "abc-123"}
    text, kb = render.render_decision(item)
    assert isinstance(text, str) and "تأیید کنم؟" in text
    assert isinstance(kb, list) and len(kb) == 1 and len(kb[0]) == 3
    assert [b["callback_data"] for b in kb[0]] == ["ok:abc-123", "no:abc-123", "later:abc-123"]
    for b in kb[0]:
        assert b.get("text")


def t_h_decision_id_stable_hash_without_id():
    _, kb1 = render.render_decision({"q": "سوالِ دو", "source": "money"})
    _, kb2 = render.render_decision({"q": "سوالِ دو", "source": "money"})
    cds = [b["callback_data"] for b in kb1[0]]
    ids = {cd.split(":", 1)[1] for cd in cds}
    assert len(ids) == 1 and cds[0].startswith("ok:") and cds[2].startswith("later:")
    assert kb2[0][0]["callback_data"] == cds[0]              # deterministic
    did = ids.pop()
    assert did and len(f"later:{did}") <= 64                 # سقفِ callback_data تلگرام
    # ورودیِ خراب هم امن است
    t3, kb3 = render.render_decision(None)
    assert isinstance(t3, str) and len(kb3[0]) == 3


# ─── containment: scrub + هیچ echo ِ ممنوعی در هیچ خروجی ─────────────────────────
def t_i_scrub_redacts_banned_lines_only():
    for b in render._BANNED_ECHO:
        out = render.scrub(f"خطِ سالمِ اول\nپیامِ {b} وسط\nخطِ سالمِ آخر")
        assert b not in out and b not in out.lower()
        assert "خطِ سالمِ اول" in out and "خطِ سالمِ آخر" in out
        assert "(redacted:containment)" in out
    assert render.scrub(None) == "" and render.scrub("تمیز") == "تمیز"


def t_j_no_banned_string_in_any_rendered_output():
    for b in render._BANNED_ECHO:
        feeds = {"board": {"counts": {"queued": 1}}, "guidance": {"n": 1},
                 "heart": {}, "telemetry": {}, "registry": {}, "business": {}}
        assert b not in render.render_status(feeds).lower()
        d = render.render_leg_digest("studio_pf",
                                     {"status": "🟢", "detail": f"جزئیات {b}",
                                      "next": f"قدم {b}"})
        assert b not in d and b not in d.lower()
        text, kb = render.render_decision({"q": f"سوال {b}", "why": b, "id": b,
                                           "source": "approval"})
        flat = text + json.dumps(kb, ensure_ascii=False)
        assert b not in flat and b not in flat.lower()


# ─── collect_feeds: STATE_DIRِ خالیِ موقت → همهٔ کلیدها حاضر، بدونِ crash ─────────
def t_k_collect_feeds_empty_state_all_keys():
    feeds = render.collect_feeds()
    assert isinstance(feeds, dict)
    for k in ("board", "guidance", "business", "heart", "registry", "telemetry"):
        assert k in feeds, f"feed key missing: {k}"
        assert isinstance(feeds[k], dict), f"feed {k} must be dict, got {type(feeds[k])}"
    # روی stateِ خالی، state-fileهای قلب/registry باید {} باشند (فایل نیست)
    assert feeds["heart"] == {} and feeds["registry"] == {}
    # و status از همین feeds بدونِ crash رندر شود
    s = render.render_status(feeds)
    assert isinstance(s, str) and 1 <= len(s.splitlines()) <= 5


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_render: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
