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


def t_f_legs_nine_ordered_keys():
    # ۲۰۲۶-۰۷-۱۳: پای نهم «cartographer» افزوده شده بود ولی این تست روی ۸ مانده بود
    # (drift ِ تست-vs-کد؛ render.LEGS مرجع است). به ۹ کلید هم‌ترتیبِ کد اصلاح شد.
    assert list(render.LEGS) == ["lead", "ziman", "mining", "crypto",
                                 "accounting", "studio_pf", "system", "knowledge",
                                 "cartographer"]
    assert render.LEGS["studio_pf"] == "استودیو"


# ─── کارتِ تصمیم: ok/no/later:<id> ────────────────────────────────────────────────
def t_g_decision_keyboard_callback_format():
    item = {"q": "تأیید کنم؟", "why": "منتظرِ رأیِ توست", "source": "needs", "id": "abc-123"}
    text, kb = render.render_decision(item)
    assert isinstance(text, str) and "تأیید کنم؟" in text
    assert isinstance(kb, list) and len(kb) == 1 and len(kb[0]) == 3
    assert [b["callback_data"] for b in kb[0]] == ["ok:abc-123", "no:abc-123", "later:abc-123"]
    for b in kb[0]:
        assert b.get("text")


def t_h_decision_id_stable_hash_without_id():
    _, kb1 = render.render_decision({"q": "سوالِ دو", "source": "needs"})
    _, kb2 = render.render_decision({"q": "سوالِ دو", "source": "needs"})
    cds = [b["callback_data"] for b in kb1[0]]
    ids = {cd.split(":", 1)[1] for cd in cds}
    assert len(ids) == 1 and cds[0].startswith("ok:") and cds[2].startswith("later:")
    assert kb2[0][0]["callback_data"] == cds[0]              # deterministic
    did = ids.pop()
    assert did and len(f"later:{did}") <= 64                 # سقفِ callback_data تلگرام
    # ورودیِ خراب هم امن است
    t3, kb3 = render.render_decision(None)
    assert isinstance(t3, str) and len(kb3[0]) == 3


def t_i_money_card_no_fake_approve():
    # راست‌گوییِ دکمه (2026-07-17): کارتِ money/approval در center نباید ✅ِ settle-نما
    # بدهد — تأییدِ واقعی فقط در کارتِ توکنِ approval_channel است (این‌جا فقط اطلاع + «دیدم»).
    for src in ("money", "approval"):
        _, kb = render.render_decision({"q": "پرداخت؟", "source": src})
        cds = [b["callback_data"] for row in kb for b in row]
        assert not any(c.startswith("ok:") for c in cds), (src, cds)
        assert not any(c.startswith("no:") for c in cds), (src, cds)
        assert any(c.startswith("later:") for c in cds), (src, cds)


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


def t_l_visual_branding_icons_divider():
    """ارتقای بصری (رأی مالک): آیکنِ برندِ هر پا + عنوانِ تاپیکِ آیکن‌دار + دیوایدر در status."""
    assert set(render.LEG_ICONS) >= set(render.LEGS), "هر پا باید آیکن داشته باشد"
    t = render.topic_title("lead")
    assert t.startswith("🎨") and "Lead-نقاشی" in t
    # config مالک نامِ نمایشی را عوض می‌کند ولی آیکنِ برند می‌ماند
    t2 = render.topic_title("studio_pf", {"display_names": {"studio_pf": "کارگاه"}})
    assert t2.startswith("🎬") and "کارگاه" in t2
    # کلیدِ ناشناس → بدونِ آیکن، بدونِ crash
    assert render.topic_title("nope") == "nope"
    # status: دیوایدرِ برند حاضر است و سقفِ ≤۵ خط حفظ شده (t_a همین را هم چک می‌کند)
    s = render.render_status({"board": {"counts": {}}, "guidance": {"n": 1}})
    assert render.DIVIDER in s and len(s.splitlines()) <= 5
    # دایجست: آیکنِ پا در هدر
    d = render.render_leg_digest("crypto", {"status": "🟢", "detail": "x"})
    assert d.startswith("📈")


def t_m_menu_is_context_aware_and_action_first():
    """منوی فرماندهی نباید ثابت/توضیحی باشد: خطر و نیازِ مالک بالاتر از دکمه‌های عادی می‌آیند."""
    feeds = {"board": {"counts": {"queued": 5, "running": 1, "blocked": 2,
                                    "awaiting_user": 3, "quarantined": 4}},
             "guidance": {"n": 7}}
    text, kb = render.render_menu(False, feeds=feeds, paused={"lead": True, "ziman": False})
    flat = [b["callback_data"] for row in kb for b in row]
    assert "اولویت الان" in text and "قرنطینه" in text
    assert kb[0][0]["callback_data"] == "mn:qr"       # خطر بالاتر از همه
    assert any(b["callback_data"] == "mn:ap" for row in kb for b in row)
    assert any("پای متوقف" in b["text"] for row in kb for b in row)
    for must in ("mn:st", "mn:lg", "mn:bg", "mn:rv", "mn:sy", "mn:map", "mn:ms"):
        assert must in flat, f"منو باید {must} را داشته باشد"


def t_n_map_page_has_action_buttons():
    """صفحهٔ نقشه‌برداری دکمهٔ شروع scan و گزارش دارد (propose-only)."""
    text, kb = render.render_map_page({"status": "idle", "files_seen": 0})
    flat = [b["callback_data"] for row in kb for b in row]
    assert "نقشه‌برداری" in text
    assert "map:start" in flat
    assert "map:report" in flat
    assert "mn:menu" in flat
    # با stateِ done هم کار می‌کند
    text2, _ = render.render_map_page({"status": "done", "files_seen": 100,
                                       "dirs_seen": 10, "bytes_total": 5_000_000,
                                       "latest_manifest": "/path/manifest.json"})
    assert "100" in text2 and "manifest" in text2


def t_o_approvals_queue_shows_pending_with_buttons():
    """صفِ تأیید: pending jobs با دکمه‌های ap:ok/no/detail."""
    pending = [{"id": "job-1", "type": "metadata_scan", "risk": "read", "title": "نقشه"},
               {"id": "job-2", "type": "budget_apply", "risk": "high", "title": "بودجه"}]
    summary_counts = {"pending": 2, "approved": 1, "rejected": 0, "done": 0}
    text, kb = render.render_approvals_queue(pending, summary_counts, [])
    flat = [b["callback_data"] for row in kb for b in row]
    assert "2" in text and "job-1" in text
    assert "ap:ok:job-1" in flat and "ap:no:job-1" in flat and "ap:detail:job-1" in flat
    # صفِ خالی هم امن است
    text2, kb2 = render.render_approvals_queue([], {"pending": 0}, [])
    assert "منتظر" in text2 or "نیست" in text2


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_render: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
