"""
ui/tab_dashboard.py — داشبوردِ اتوماسیونِ خودمختار (بدونِ گیتِ تایید).

سیستم خودش کار می‌کند: کاوش، خودخوانی، خلاقیت، خودتنظیمی، و محافظت.
UI فقط وضعیتِ خلاصه و actionable را نشان می‌دهد — نه لاگِ خام و نه نمودارِ تزئینی.

چیدمان:
  • نوارِ بالا: وضعیت + حالتِ فعلی + محافظ فعال + استراتژی + دکمه‌های شروع/توقف
  • ۳ کارت: «الان»، «آخرین نتیجه»، «توجه»
  • KPIهای کوچک + خلاصه‌ی ۵دقیقه‌ای
  • لاگِ رویدادِ فشرده (یک ناحیه‌ی اسکرول)

به‌روزرسانیِ زنده با @st.fragment(run_every).
"""
from __future__ import annotations

import html as _html
from datetime import datetime

import streamlit as st

from brain import events


_ICONS = {
    "task.started":      "▶️",
    "task.completed":    "✅",
    "task.failed":       "❌",
    "task.blocked":      "⛔",
    "handoff.created":   "🔀",
    "system.heartbeat":  "💓",
    "approval.required": "⏳",
}
_STATUS_COLOR = {
    "ok": "#2d8659", "error": "#c0392b", "blocked": "#e67e22",
    "pending": "#e67e22", "retry": "#b8860b", "info": "#5a6b7b",
}
# نگاشتِ agent → برچسبِ حالت (برای نمایشِ «الان چه می‌کند»)
_MODE_LABEL = {
    "explore":   "🔬 کاوش",
    "real":      "🌐 دادهٔ واقعی",
    "synthesize": "🧪 ساختِ هدفمند",
    "introspect": "🪞 خودخوانی",
    "creative":  "💡 خلاقیت",
    "mutate":    "🔧 خودتنظیمی",
    "evolve":    "🧬 خودتحول",
    "conclude":  "🔬 نتیجه‌گیری",
    "guardrail": "🛡️ محافظ",
    "guard":     "🛡️ محافظ",     # نامِ حالت (مسیرِ backstop)
    "creative":  "💡 خلاقیت",
    "create":    "💡 خلاقیت",     # نامِ حالت (مسیرِ backstop)
    "vault":     "🔀 ثبت",
    "frontier":  "🗺️ مرزِ دانش",
    "system":    "💓 heartbeat",
}


# ════════════════════════════════════════════════════════════════════════
#  CSS فشرده
# ════════════════════════════════════════════════════════════════════════

def _inject_css():
    st.markdown("""
    <style>
      .dash-wrap { font-size: 0.86rem; }
      .dash-pill {
        display:inline-block; padding:2px 12px; border-radius:999px;
        color:#fff; font-weight:600; font-size:0.8rem;
      }
      .dash-chip {
        display:inline-block; padding:2px 10px; border-radius:999px;
        border:1px solid rgba(128,128,128,0.35); font-size:0.76rem;
        margin-right:6px;
      }
      .dash-cards { display:flex; gap:0.6rem; margin:0.5rem 0; flex-wrap:wrap; }
      .dash-card {
        flex:1; min-width:180px; border:1px solid rgba(128,128,128,0.28);
        border-radius:10px; padding:0.55rem 0.8rem; background:rgba(128,128,128,0.06);
      }
      .dash-card .lbl { font-size:0.72rem; opacity:0.7; margin-bottom:2px; }
      .dash-card .val { font-size:0.9rem; font-weight:600; line-height:1.35; }
      .dash-card.attn { border-color:#e67e22; background:rgba(230,126,34,0.12); }
      .dash-card.safe { border-color:#2d8659; background:rgba(45,134,89,0.10); }
      .dash-kpis { display:flex; gap:0.6rem; margin:0.4rem 0; flex-wrap:wrap; }
      .dash-kpi {
        flex:1; min-width:90px; text-align:center; padding:0.4rem;
        border:1px solid rgba(128,128,128,0.22); border-radius:8px;
        background:rgba(128,128,128,0.05);
      }
      .dash-kpi .n { font-size:1.4rem; font-weight:700; line-height:1; }
      .dash-kpi .k { font-size:0.68rem; opacity:0.7; margin-top:2px; }
      .dash-log {
        max-height:240px; overflow-y:auto; border:1px solid rgba(128,128,128,0.22);
        border-radius:8px; padding:0.35rem 0.5rem; direction:rtl;
        font-size:0.8rem; line-height:1.7;
      }
      .dash-log .row { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .dash-log .t { direction:ltr; display:inline-block; opacity:0.55;
                     font-family:monospace; font-size:0.72rem; margin-left:6px; }
      .dash-log .ag { opacity:0.6; font-size:0.72rem; }
    </style>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
#  ورودی اصلی
# ════════════════════════════════════════════════════════════════════════

def render_dashboard():
    """رندرِ داشبوردِ اتوماسیونِ خودمختار."""
    if "auto_ctrl" not in st.session_state:
        from brain.automation import AutomationController
        st.session_state.auto_ctrl = AutomationController(use_llm=False)
        st.session_state.auto_running = False
        st.session_state.auto_halted = False

    _inject_css()
    st.markdown("### 🛰️ داشبورد اتوماسیونِ خودمختار — Brain-OS")
    try:
        from brain import research_agenda as ra
        st.caption(f"🧠 مأموریت: {ra.MISSION_FA[:150]}…")
    except Exception:
        st.caption("سیستم خودش کاوش می‌کند، خودش را می‌خواند، ایده می‌سازد و استراتژی‌اش را عوض می‌کند.")

    _live_panel()


# ════════════════════════════════════════════════════════════════════════
#  پنلِ زنده — هر ۲ ثانیه خودبه‌روز
# ════════════════════════════════════════════════════════════════════════

@st.fragment(run_every="2s")
def _live_panel():
    ctrl = st.session_state.auto_ctrl

    # ── tick: یک گامِ خودمختار اگر در حال اجرا ──
    if st.session_state.get("auto_running") and not st.session_state.get("auto_halted"):
        res = ctrl.run_one()
        if res.get("halt"):                       # نقضِ ثابت ⇒ توقفِ حفاظتی
            st.session_state.auto_running = False
            st.session_state.auto_halted = True
    ctrl.maybe_heartbeat()

    _render_controls(ctrl)      # Top Status Strip
    _render_mission(ctrl)       # Central Mission Card
    _render_cards()             # Now / Last / Attention
    _render_orchestra()         # Agent Orchestra Panel
    _render_lanes(ctrl)         # Execution Board
    _render_kpis(ctrl)          # Evidence KPIs
    _render_conclusions()       # Audit: نتیجه‌گیری + دفترِ هدف‌ها
    _render_code_proposals()    # خودتغییریِ کد — تأیید/رد (تصمیمِ مالک)
    _render_packets()           # پیام‌رسانی + Decision Packets
    _render_log()               # Audit: لاگِ رویداد
    _render_guidance(ctrl)      # Human Guidance Box


# ════════════════════════════════════════════════════════════════════════
#  نوارِ کنترل
# ════════════════════════════════════════════════════════════════════════

def _render_controls(ctrl):
    running = st.session_state.get("auto_running", False)
    halted = st.session_state.get("auto_halted", False)

    if halted:
        pill = '<span class="dash-pill" style="background:#c0392b">🛑 توقفِ حفاظتی</span>'
    elif running:
        pill = '<span class="dash-pill" style="background:#2d8659">🟢 در حال اجرا</span>'
    else:
        pill = '<span class="dash-pill" style="background:#5a6b7b">⚪ متوقف</span>'

    started = events.latest_of("task.started")
    mode = _MODE_LABEL.get(started["agent_id"], "—") if started else "—"
    now = datetime.now().strftime("%H:%M:%S")

    st.markdown(
        f'<div class="dash-wrap">{pill}'
        f'<span class="dash-chip" style="margin-right:0;margin-left:6px">حالت: {mode}</span>'
        f'&nbsp;<span style="opacity:0.7;font-size:0.78rem">'
        f'آخرین به‌روزرسانی: <span dir="ltr">{now}</span> · '
        f'کاوش‌ها: {ctrl.iteration}</span></div>',
        unsafe_allow_html=True,
    )

    # خطِ محافظ + استراتژی + نسلِ تحول
    s = ctrl.strategy
    gen = getattr(ctrl, "evolved", {}).get("_generation", 0)
    ep = getattr(ctrl, "evolved", {}).get("explore_points", 3000)
    st.caption(
        "🛡️ محافظ فعال: بدونِ ویرایشِ کد · نوشتن فقط در نواحیِ مجاز · خودتنظیمی کران‌دار و خودتحول اول تست"
        f"  |  ⚙️ آستانه‌ی توجه={s['novelty_threshold']:.2f} · "
        f"سوگیریِ حافظه={s['rho_bias']:.2f} · خلاقیت={s['creativity']:.2f} · "
        f"🧬 نسلِ تحول={gen} · طولِ کاوش={ep}"
    )

    if halted:
        st.error("🛑 لایه‌ی محافظ یک نقضِ ثابت را شناسایی کرد و اتوماسیون را متوقف کرد. "
                 "برای بررسیِ دوباره «توقف و صفر» را بزن.")

    c1, c2, c3 = st.columns(3)
    with c1:
        if running:
            if st.button("⏸️ توقف موقت", key="dash_pause", width='stretch'):
                st.session_state.auto_running = False
                st.rerun()
        else:
            label = "▶️ ادامه" if ctrl.iteration else "▶️ شروع خودکار"
            if st.button(label, key="dash_start", type="primary",
                         width='stretch', disabled=halted):
                st.session_state.auto_running = True
                st.rerun()
    with c2:
        if st.button("⏹️ توقف و صفر", key="dash_stop", width='stretch'):
            from brain.automation import AutomationController
            st.session_state.auto_ctrl = AutomationController(use_llm=False)
            st.session_state.auto_running = False
            st.session_state.auto_halted = False
            st.rerun()
    with c3:
        if st.button("🧹 پاک‌کردن لاگ", key="dash_clear", width='stretch'):
            events.clear_events()
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
#  Central Mission Card — هدفِ فعلی، معیارِ موفقیت، شرایطِ توقف
# ════════════════════════════════════════════════════════════════════════

def _render_mission(ctrl):
    try:
        from brain import research_agenda as ra
        goals = ra.goals_now()
        gi = ctrl.iteration // 20 % max(len(goals), 1) if goals else 0
        goal = goals[gi] if goals else None
    except Exception:
        goal = None
    with st.expander("🎯 کارتِ مأموریت — هدفِ فعلی، معیارِ موفقیت، شرایطِ توقف", expanded=False):
        if goal:
            st.markdown(f"**هدفِ فعال:** {goal.get('title_fa','—')}")
            st.caption(goal.get("description_fa", "")[:220])
            st.caption(f"مبنا: {goal.get('grounded_in','—')[:120]}")
        st.markdown(
            "- **معیارِ موفقیت:** رشدِ پوششِ مرزِ دانش + فرضیه‌ی تاییدشده با متریک\n"
            "- **شرایطِ توقف:** نقضِ لنگرهای ریاضی (halt خودکار) یا دکمه‌ی توقف\n"
            "- **سقفِ لوپ:** بدونِ عمقِ delegation > ۲ · خودتنظیمی کران‌دار، خودتحول اول تست"
        )


# ════════════════════════════════════════════════════════════════════════
#  Agent Orchestra Panel — وضعیتِ همه‌ی عامل‌ها از روی رویدادها
# ════════════════════════════════════════════════════════════════════════

_ORCHESTRA = ["explore", "real", "synthesize", "introspect", "creative",
              "mutate", "evolve", "conclude", "guardrail"]


def _render_orchestra():
    rows = events.get_recent(60)
    last: dict[str, dict] = {}
    for r in rows:                      # جدیدترین اول — اولین دیدار = آخرین رویداد
        a = r.get("agent_id")
        if a and a not in last:
            last[a] = r

    chips = []
    for a in _ORCHESTRA:
        label = _MODE_LABEL.get(a, a)
        ev = last.get(a)
        if ev is None:
            dot, tip = "⚪", "بی‌کار"
        elif ev["event_name"] == "task.started":
            dot, tip = "🟢", "در حال اجرا"
        elif ev["event_name"] == "task.failed":
            dot, tip = "🔴", "خطا"
        elif ev["event_name"] == "task.blocked":
            dot, tip = "🟠", "مسدود/ردشده"
        else:
            dot, tip = "🟢", "سالم"
        t = ev["timestamp"][11:19] if ev else "—"
        chips.append(
            f'<span class="dash-chip" title="{tip} · آخرین: {t}">{dot} {label}</span>'
        )
    st.markdown('<div class="dash-wrap">🎼 ارکسترِ عامل‌ها: ' + " ".join(chips) + "</div>",
                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
#  Execution Board — صفِ کار در ۵ لاین
# ════════════════════════════════════════════════════════════════════════

def _render_lanes(ctrl):
    c = events.counts()
    running = 1 if (st.session_state.get("auto_running")
                    and not st.session_state.get("auto_halted")) else 0
    awaiting = 1 if st.session_state.get("auto_halted") else 0

    def lane(n, k, color):
        return (f'<div class="dash-kpi" style="border-color:{color}">'
                f'<div class="n" style="font-size:1.1rem">{n}</div>'
                f'<div class="k">{k}</div></div>')

    st.markdown(
        '<div class="dash-kpis">'
        + lane(running, "در حال اجرا", "#2d8659")
        + lane(c["done"], "تکمیل‌شده", "#5a6b7b")
        + lane(c.get("blocked", 0), "مسدود/ردشده", "#e67e22")
        + lane(awaiting, "منتظرِ کاربر", "#c0392b")
        + lane(c["errors"], "قرنطینه (خطا)", "#b8860b")
        + '</div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════
#  Human Guidance Box — کوچک‌ترین سؤالِ تعیین‌کننده
# ════════════════════════════════════════════════════════════════════════

def _render_guidance(ctrl):
    running = st.session_state.get("auto_running", False)
    halted = st.session_state.get("auto_halted", False)
    s5 = events.get_summary(300)

    if halted:
        msg, icon = ("نقضِ لنگرِ ریاضی شناسایی شد — «توقف و صفر» را بزن و علت را بررسی کن.", "🛑")
    elif not running:
        msg, icon = ("سیستم متوقف است — اگر می‌خواهی خودش ادامه دهد «شروع خودکار» را بزن.", "▶️")
    elif s5["total"] > 10 and s5["completed"] == 0:
        msg, icon = ("در ۵ دقیقه‌ی اخیر هیچ تکمیلی نبوده — احتمالِ گیر؛ لاگ را ببین یا ریست کن.", "⚠️")
    else:
        msg, icon = ("نیازی به تصمیمِ تو نیست — سیستم در مسیر است و محافظ فعال.", "✅")

    st.markdown(
        f'<div class="dash-card {"attn" if icon in ("🛑","⚠️") else "safe"}" '
        f'style="margin-top:0.5rem"><div class="lbl">🧭 راهنماییِ انسانی — الان کجا هدایتم کن</div>'
        f'<div class="val">{icon} {_html.escape(msg)}</div></div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════
#  ۳ کارتِ وضعیت
# ════════════════════════════════════════════════════════════════════════

def _card(label: str, value: str, cls_extra: str = "") -> str:
    cls = ("dash-card " + cls_extra).strip()
    return (f'<div class="{cls}"><div class="lbl">{label}</div>'
            f'<div class="val">{_html.escape(value)}</div></div>')


def _render_cards():
    now_ev = events.latest_of("task.started")
    last_ev = events.latest_of(["task.completed", "handoff.created"])
    fail_ev = events.latest_of(["task.failed", "task.blocked"])

    now_txt = now_ev["summary"] if now_ev else "بی‌کار — چیزی در حال اجرا نیست"
    last_txt = last_ev["summary"] if last_ev else "هنوز نتیجه‌ای نیست"

    # کارتِ «توجه»: فقط اگر آخرین رویدادِ خطا/بلاک تازه‌تر از آخرین تکمیل باشد
    attn_recent = bool(fail_ev and (not last_ev or fail_ev["timestamp"] >= last_ev["timestamp"]))
    if attn_recent:
        attn_txt, cls = fail_ev["summary"], "attn"
    else:
        attn_txt, cls = "همه‌چیز در محدوده‌ی امن ✓", "safe"

    st.markdown(
        '<div class="dash-cards">'
        + _card("الان چه می‌کند", now_txt)
        + _card("آخرین نتیجه", last_txt)
        + _card("توجه", attn_txt, cls)
        + '</div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════
#  KPIها + خلاصه‌ی ۵دقیقه‌ای
# ════════════════════════════════════════════════════════════════════════

def _render_kpis(ctrl):
    c = events.counts()
    s = events.get_summary(300)
    try:
        from brain import frontier
        fr = frontier.stats()
    except Exception:
        fr = {"coverage": 0, "total_cells": 560, "coverage_pct": 0.0, "best_mi": 0.0}

    def tile(n, k, hl=False):
        style = ' style="border-color:#2d8659;background:rgba(45,134,89,0.10)"' if hl else ""
        return f'<div class="dash-kpi"{style}><div class="n">{n}</div><div class="k">{k}</div></div>'

    st.markdown(
        '<div class="dash-kpis">'
        + tile(f'{fr["coverage"]}', "🗺️ رفتارهای متمایز", hl=True)
        + tile(ctrl.iteration, "کاوش")
        + tile(c["done"], "تکمیل‌شده")
        + tile(c["errors"], "خطا")
        + '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"🗺️ مرزِ دانش: {fr['coverage']} رفتارِ متمایز کشف شده (بالاترین MI={fr['best_mi']:.3f}). "
        "این تنوعِ واقعیِ کشف‌شده است، نه نمره‌ی سقف‌دار؛ ولی چون مولدهای داده محدودند، "
        "وقتی تنوعشان تمام شود این عدد هم به سقفِ طبیعیِ خودش می‌رسد — پیشرفتِ بی‌نهایت نیست."
    )
    st.caption(
        f"📊 خلاصه‌ی ۵ دقیقه‌ی اخیر: {s['total']} رویداد · {s['completed']} تکمیل · "
        f"{s['retries']} retry · {s['errors']} خطا · {s['heartbeats']} heartbeat"
    )
    # دینامیکِ «فضای کاری جهانی» — عملیاتی‌سازیِ نظریه‌ی GWT از روی traceها
    try:
        from brain.workspace import workspace_metrics
        w = workspace_metrics(80)
        st.caption(
            f"🧠 دینامیکِ فضای کاری (GWT): اشتعالِ میانگین={w['mean_ignition']} "
            f"(بیشینه {w['max_ignition']}) · پهنای انتشار={w['broadcast_width']} ماژول · "
            f"نرخِ اشتعال={w['ignition_rate']} · انسجام={w['coherence']} — "
            f"سنجه‌ی رفتاری، نه ادعای آگاهی"
        )
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════
#  نتیجه‌گیریِ ریاضی + دفترِ هدف‌ها (تا هدف‌های قبلی گم نشوند)
# ════════════════════════════════════════════════════════════════════════

def _render_conclusions():
    try:
        from brain.conclusions import load_conclusions
        c = load_conclusions()
    except Exception:
        c = None
    with st.expander("🔬 نتیجه‌گیریِ ریاضی (مدلِ SOG روی داده) + دفترِ هدف‌ها",
                     expanded=bool(c)):
        if not c:
            st.caption("_هنوز نتیجه‌گیری‌ای ثبت نشده — «شروع خودکار» را بزن تا حالتِ 🔬 نتیجه‌گیری اجرا شود._")
            return
        for line in c.get("conclusions_fa", []):
            st.markdown(f"- {_html.escape(line)}")
        st.markdown("**🎯 دفترِ هدف‌ها (هر دو حفظ می‌شوند):**")
        for g in c.get("goals_status", []):
            st.markdown(f"- **{_html.escape(g.get('area',''))}** — {_html.escape(g.get('progress_fa',''))}")


# ════════════════════════════════════════════════════════════════════════
#  پیام‌رسانی (Telegram) + Decision Packets
# ════════════════════════════════════════════════════════════════════════

_PACKET_ICON = {"approve": "🔴", "notify": "🔵", "blocked": "⛔",
                "warning": "🟠", "summary": "💬"}


def _render_packets():
    try:
        from brain import notify
        configured = notify.is_configured()
        packets = notify.recent_packets(6)
    except Exception:
        configured, packets = False, []

    label = "🔔 پیام‌رسانی و Decision Packets" + ("" if configured else " (تلگرام تنظیم نشده)")
    with st.expander(label, expanded=False):
        if configured:
            st.caption("✅ تلگرام فعال — packetهای مهم به گوشی‌ات ارسال می‌شوند.")
        else:
            st.caption(
                "⚪ تلگرام تنظیم نشده — packetها فقط اینجا صف می‌شوند. برای فعال‌سازی: "
                "۱) با @BotFather یک بات بساز، ۲) توکن را بگیر، ۳) در .env بگذار:\n"
                "`TELEGRAM_BOT_TOKEN=...` و `TELEGRAM_CHAT_ID=...` "
                "(chat id را از @userinfobot بگیر)، ۴) اپ را ری‌استارت کن."
            )
        if not packets:
            st.caption("_هنوز packetی ساخته نشده._")
            return
        for p in packets:
            icon = _PACKET_ICON.get(p.get("alert_type"), "•")
            t = p.get("timestamp", "")[11:19]
            st.markdown(
                f"- <span dir='ltr' style='opacity:0.6;font-family:monospace;font-size:0.75rem'>{t}</span> "
                f"{icon} **{_html.escape(p.get('context',''))}** — "
                f"{_html.escape(p.get('why_now',''))} "
                f"<span style='opacity:0.6;font-size:0.75rem'>({_html.escape(p.get('delivered',''))})</span>",
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════════════
#  خودتغییریِ کد — تأیید/ردِ مالک (propose→test→approve)
# ════════════════════════════════════════════════════════════════════════

def _render_code_proposals():
    try:
        from brain import self_code, budget
        enabled = self_code.enabled()
        pending = self_code.list_pending()
        counts = self_code.status_counts()
        bud = budget.status()
    except Exception:
        return

    n = len(pending)
    label = f"🧩 خودتغییریِ کد — {n} پیشنهادِ منتظرِ تأیید" if n else "🧩 خودتغییریِ کد"
    with st.expander(label, expanded=bool(n)):
        st.caption(
            f"وضعیت: {'🟢 فعال' if enabled else '⚪ خاموش (SELF_CODE_ENABLED=1 برای فعال‌سازی)'} · "
            f"بودجه‌ی ابری: {bud.get('cloud_calls','?')}/{bud.get('cap','?')} امروز · "
            f"وضعیت‌ها: {counts or '—'}"
        )
        st.caption(
            "🛡️ هیچ تغییری به کدِ زنده نمی‌رسد مگر پس از سبزشدنِ کلِ سوییت و **تأییدِ تو**. "
            "هسته‌ی ایمنی (core/tests/گاردها) هرگز هدف نمی‌شود."
        )

        # خودنگاره + قابلیت‌های آموخته (رشدِ هدف‌محورِ خودآگاه)
        try:
            from brain import self_growth
            focus = self_growth.current_focus(0)
            learned = self_growth.learned_capabilities(6)
            st.markdown(f"🪞 **خودنگاره** · کانون: _{_html.escape(focus.get('goal',''))[:70]}_")
            if learned:
                st.caption("📚 قابلیت‌های آموخته (با تأییدِ تو): " +
                           " · ".join(f"`{_html.escape(c.get('target',''))}`" for c in learned[:5]))
            else:
                st.caption("📚 هنوز قابلیتی با تأییدِ تو آموخته نشده — اولین تأیید، اولین یادگیری.")
        except Exception:
            pass
        if not pending:
            st.caption("_پیشنهادی برای تأیید نیست._")
            return

        for meta in pending:
            pid = meta["id"]
            st.markdown(
                f"**`{_html.escape(meta['target'])}`** — "
                f"{_html.escape(meta.get('rationale',''))[:120]}  \n"
                f"<span style='opacity:0.6;font-size:0.8rem'>pid {pid} · "
                f"خطوط {meta.get('lines_original','?')}→{meta.get('lines_new','?')} · "
                f"تست: {'✅ سبز' if meta.get('test',{}).get('passed') else '—'}</span>",
                unsafe_allow_html=True,
            )
            with st.expander(f"دیدنِ کدِ پیشنهادی · {pid}", expanded=False):
                try:
                    from brain.self_code import _proposals_dir
                    code = (_proposals_dir() / pid / "new.py").read_text(encoding="utf-8")
                    st.code(code[:6000], language="python")
                except Exception as e:
                    st.caption(f"خطا در خواندن: {e}")
            c1, c2 = st.columns(2)
            if c1.button("✅ تأیید و اعمال", key=f"approve_{pid}"):
                res = self_code.approve(pid)
                (st.success if res.get("ok") else st.error)(res.get("reason", ""))
                st.rerun()
            if c2.button("❌ رد", key=f"reject_{pid}"):
                self_code.reject(pid)
                st.rerun()


# ════════════════════════════════════════════════════════════════════════
#  لاگِ رویدادِ فشرده
# ════════════════════════════════════════════════════════════════════════

def _render_log():
    rows = events.get_recent(20)
    if not rows:
        st.caption("_هنوز رویدادی ثبت نشده. «شروع خودکار» را بزن._")
        return

    html_rows = []
    for r in rows:
        icon = _ICONS.get(r["event_name"], "•")
        color = _STATUS_COLOR.get(r["status"], "#5a6b7b")
        t = r["timestamp"][11:19] if len(r["timestamp"]) >= 19 else r["timestamp"]
        summary = _html.escape(r["summary"] or "")
        agent = _html.escape(r["agent_id"] or "")
        html_rows.append(
            f'<div class="row"><span class="t">{t}</span>{icon} '
            f'<span style="color:{color}">{summary}</span> '
            f'<span class="ag">· {agent}</span></div>'
        )

    st.markdown(
        '<div class="dash-log">' + "".join(html_rows) + '</div>',
        unsafe_allow_html=True,
    )
