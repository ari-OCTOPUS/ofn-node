"""
ui/tab_control_plane.py — تبِ Control Plane (v1: observe-only).

«تمرکزِ کنترل، نه تمرکزِ هوش» — این تب فقط می‌بیند و گزارش می‌دهد:
registry، وضعیتِ زنده (daemon/budget/bus)، approvalهای معلق (فقط آینه)،
سلامتِ کانال‌ها (Channel Doctor)، و وضعیتِ kill-switchها (نمایشی، خاموش).

هیچ دکمه‌ای در این تب رفتارِ live را عوض نمی‌کند. تنها نوشتن‌ها:
  • گزارشِ دکتر →  outputs/control_plane/_reports/   (مسیرِ مجاز)
  • آینه‌ی registry →  outputs/control_plane/control_plane.db
apply/approve از مسیرِ امنِ موجود (داشبورد/تلگرام) می‌ماند — تصمیمِ مالک.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from control_plane import __version__
from control_plane.flags import all_flags, governance_mode
from control_plane.snapshot import collect_status, SYSTEM_ROOT
from control_plane.registry import load_registry, mirror_to_sqlite

_CP_OUT = SYSTEM_ROOT / "outputs" / "control_plane"
_MIRROR_DB = _CP_OUT / "control_plane.db"
_REPORT_MD = _CP_OUT / "_reports" / "channel_doctor.md"

_VERDICT_ICON = {"PASS": "✅", "WARN": "🟡", "FAIL": "🔴", "UNKNOWN": "⚪",
                 "CONNECTED": "✅", "PARTIAL": "🟡", "MISSING": "🔴"}


def _pill(text: str, ok: bool | None) -> str:
    color = {True: "#2d8659", False: "#c0392b", None: "#5a6b7b"}[ok]
    return (f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:999px;font-size:0.78rem;">{text}</span>')


def render_control_plane() -> None:
    st.markdown(f"### 🎛️ Control Plane <small>v{__version__} · "
                f"`{governance_mode()}`</small>", unsafe_allow_html=True)
    st.caption("تمرکزِ کنترل، نه تمرکزِ هوش — black boxها دست‌نخورده می‌مانند. "
               "این تب فقط visibility است؛ هیچ رفتارِ live این‌جا تغییر نمی‌کند.")

    if st.button("🔄 تازه‌سازی وضعیت"):
        st.rerun()

    snap = collect_status()

    # ── Overview ─────────────────────────────────────────────────────────
    d, b, ev = snap["daemon"], snap["budget"], snap["events"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Daemon", d.get("status", "?"),
              f"tick {d.get('last_tick_at', '—')[-8:] if d.get('last_tick_at') else '—'}")
    c2.metric("بودجه‌ی ابری امروز",
              f"{b.get('cloud_calls', '?')}/{b.get('cap', '?')}",
              f"باقی: {b.get('remaining', '?')}")
    c3.metric("رویدادها (کل)", ev.get("total", "?"),
              f"خطا: {ev.get('errors', '?')} · بلاک: {ev.get('blocked', '?')}")
    c4.metric("Approvals معلق", snap["approvals"].get("bus_pending_approvals", "?"),
              f"self_code: {len(snap['approvals'].get('self_code_pending', []))}")

    evo, ws = snap["evolution"], snap["workspace"]
    c5, c6, c7, c8 = st.columns(4)
    anchors = evo.get("anchors_ok", "UNKNOWN")
    c5.metric("لنگرها (0.135073)", "✓ سالم" if anchors is True else str(anchors))
    c6.metric("نسلِ تحول", evo.get("generation", "?"),
              f"frontier: {evo.get('n_cells', '?')} سلول")
    c7.metric("Ignition (GWT)", ws.get("mean_ignition", "?"),
              f"پهنا: {ws.get('broadcast_width', '?')}")
    tg = snap["notify"].get("telegram_configured")
    c8.metric("Telegram", "متصل" if tg else ("تنظیم‌نشده" if tg is False else "?"))

    sup = snap.get("supervisor", {})
    sup_st = sup.get("status", "?")
    st.markdown(
        _pill(f"pause: {'هست' if d.get('pause_file') else 'نیست'}", not d.get("pause_file"))
        + " " + _pill(f"stop: {'هست' if d.get('stop_file') else 'نیست'}", not d.get("stop_file"))
        + " " + _pill(f"halt: {d.get('halted_at') or 'نه'}", not d.get("halted_at"))
        + " " + _pill(f"self-heal: {sup_st}",
                      True if sup_st == "RUNNING" else (None if sup_st == "UNKNOWN" else False)),
        unsafe_allow_html=True)

    # ── Registry ─────────────────────────────────────────────────────────
    with st.expander("📇 Registry — subsystemها و کانال‌ها", expanded=False):
        try:
            reg = load_registry()
            problems = reg.validate()
            if problems:
                st.warning("مشکلاتِ registry:\n" + "\n".join(f"- {p}" for p in problems))
            import pandas as pd
            st.markdown(f"**Subsystems ({len(reg.subsystems)})** — "
                        f"TCB: {', '.join(reg.tcb_ids())}")
            st.dataframe(pd.DataFrame(reg.subsystems)[
                ["id", "name", "path", "tcb", "risk_tier", "live", "authority"]],
                width="stretch", height=280)
            chan_rows = [{
                "id": c["id"],
                "status": f"{_VERDICT_ICON.get(c.get('status'), '')} {c.get('status')}",
                "source": c.get("source"), "risk": c.get("risk_tier"),
                "authority": c.get("authority"), "notes": c.get("notes", ""),
            } for c in reg.channels]
            st.markdown(f"**Channels ({len(reg.channels)})**")
            st.dataframe(pd.DataFrame(chan_rows), width="stretch", height=280)
            if st.button("🪞 به‌روزرسانی آینه‌ی SQLite (outputs/control_plane)"):
                res = mirror_to_sqlite(reg, _MIRROR_DB)
                st.success(f"آینه شد: {res['subsystems']} subsystem · "
                           f"{res['channels']} channel → {res['db']}")
        except Exception as e:
            st.error(f"registry خوانده نشد: {type(e).__name__}: {e}")

    # ── Channel Doctor ───────────────────────────────────────────────────
    with st.expander("🩺 Channel Doctor — سلامتِ کانال‌ها", expanded=False):
        col_run, col_info = st.columns([1, 3])
        with col_run:
            run_it = st.button("🩺 اجرای دکتر")
        with col_info:
            st.caption("فقط می‌خوانَد و گزارش در outputs/control_plane/_reports می‌نویسد.")
        if run_it:
            from control_plane.channel_doctor import run_doctor
            with st.spinner("در حالِ معاینه‌ی کانال‌ها…"):
                rep = run_doctor()
            s = rep["summary"]
            st.markdown(f"**نتیجه:** ✅ {s['PASS']} · 🟡 {s['WARN']} · "
                        f"🔴 {s['FAIL']} · ⚪ {s['UNKNOWN']}")
            import pandas as pd
            rows = [{"کانال": r["id"],
                     "حکم": f"{_VERDICT_ICON[r['verdict']]} {r['verdict']}",
                     "bus": r["checks"]["bus_events_seen"],
                     "یادداشت": (r.get("notes") or "")[:70]} for r in rep["channels"]]
            st.dataframe(pd.DataFrame(rows), width="stretch", height=320)
        elif _REPORT_MD.exists():
            st.caption(f"آخرین گزارش: {_REPORT_MD}")

    # ── Shadow Policy (v2 — فقط گزارش، هیچ enforcement) ──────────────────
    with st.expander("🕶️ Shadow Policy — v2 (فقط گزارش)", expanded=False):
        from control_plane.shadow import run_shadow, shadow_enabled
        auto = shadow_enabled()
        st.caption("policy ladder روی رویدادهای واقعی — فقط می‌گوید «اگر live بود چه می‌شد». "
                   f"flag CONTROL_PLANE_SHADOW_POLICY = {int(auto)} "
                   "(روشن = تحلیلِ خودکار در هر رندر؛ در هر دو حالت هیچ رفتاری تغییر نمی‌کند).")
        if auto or st.button("🕶️ اجرای تحلیل shadow"):
            with st.spinner("تحلیلِ shadow روی ۵۰۰ رویدادِ آخر…"):
                rep = run_shadow(limit=500)
            if rep.get("status") != "OK":
                st.info(f"bus در دسترس نیست: {rep.get('reason', '?')}")
            else:
                s = rep["summary"]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("تحلیل‌شده", s["analyzed"])
                m2.metric("approval لازم می‌شد", s["would_require_approval"])
                m3.metric("⛔ بی‌گیت", s["ungated_high_risk"])
                m4.metric("needs_review", s["needs_review"])
                if rep["disagreements"]:
                    import pandas as pd
                    st.error("high-risk بی‌گیت دیده شد — بررسی کن:")
                    st.dataframe(pd.DataFrame(rep["disagreements"])[
                        ["event_id", "agent_id", "event_name", "action_type",
                         "level", "summary"]], width="stretch", height=200)
                else:
                    st.success("هیچ high-risk بی‌گیتی در این پنجره دیده نشد.")
                if s["failure_streaks_ge3"]:
                    st.warning(f"شکستِ پیاپی (≥۳): {s['failure_streaks_ge3']}")
                st.json(s["by_level"], expanded=False)
                st.caption(f"بودجه (shadow): {s['budget_shadow'].get('verdict')} · "
                           "گزارش کامل: outputs/control_plane/_reports/shadow_policy.md")

    # ── Approvals — v3: تصمیمِ زنده فقط برای high-risk (flag-gated) ──────
    with st.expander("⏳ Approvals", expanded=False):
        from control_plane.approvals import (approvals_live, audit_tail,
                                             decide_self_code, proposal_diff,
                                             resolve_bus_approval)
        live = approvals_live()
        ap = snap["approvals"]
        st.caption("🟢 حالتِ live (v3): approve/reject همین‌جا ممکن است — اعمال "
                   "همچنان فقط از مسیرِ امنِ خودِ self_code (sandbox test + tamper "
                   "detection) می‌گذرد." if live else
                   "⚪ فقط visibility — فعال‌سازی: CONTROL_PLANE_APPROVALS_LIVE=1 در .env")
        pend = ap.get("self_code_pending", [])
        if not pend:
            st.success("صفِ self_code خالی است.")
        for p in pend:
            pid = p.get("id", "?")
            st.warning(f"**{pid}** → `{p.get('target')}` · "
                       f"هدف: {p.get('goal') or '—'} · {p.get('created_at')}")
            # دکترین: سبزشدنِ اسکن ≠ بی‌خطر — همیشه دیف را نشان بده
            st.code(proposal_diff(pid), language="diff")
            if live:
                seen = st.checkbox("دیف را دیدم؛ مسئولیتِ این تصمیم با من است",
                                   key=f"cp_seen_{pid}")
                note = st.text_input("یادداشتِ رد (اختیاری)", key=f"cp_note_{pid}")
                c_a, c_r = st.columns(2)
                if c_a.button(f"✅ approve {pid}", key=f"cp_ap_{pid}"):
                    res = decide_self_code(pid, "approve", confirmed=seen)
                    (st.success if res["result"]["ok"] else st.error)(res["result"]["reason"])
                if c_r.button(f"❌ reject {pid}", key=f"cp_rj_{pid}"):
                    res = decide_self_code(pid, "reject", note=note, confirmed=seen)
                    (st.success if res["result"]["ok"] else st.error)(res["result"]["reason"])
        bus_pending = ap.get("bus_pending_approvals", 0)
        if isinstance(bus_pending, int) and bus_pending > 0:
            st.info(f"{bus_pending} approval معلق روی event bus")
            if live:
                seen_b = st.checkbox("این approval را بررسی کرده‌ام", key="cp_bus_seen")
                cb_a, cb_r = st.columns(2)
                if cb_a.button("✅ approve آخرین", key="cp_bus_ap"):
                    res = resolve_bus_approval("approved", confirmed=seen_b)
                    (st.success if res["result"]["ok"] else st.error)(res["result"]["reason"])
                if cb_r.button("❌ reject آخرین", key="cp_bus_rj"):
                    res = resolve_bus_approval("rejected", confirmed=seen_b)
                    (st.success if res["result"]["ok"] else st.error)(res["result"]["reason"])
        st.caption(ap.get("note", ""))
        st.json(ap.get("self_code_counts", {}), expanded=False)
        trail = audit_tail(10)
        if trail:
            st.markdown("**Evidence trail — آخرین تصمیم‌ها:**")
            import pandas as pd
            rows = [{"زمان": t.get("timestamp"), "نوع": t.get("kind"),
                     "تصمیم": t.get("decision") or t.get("new_state"),
                     "confirm": t.get("confirmed"), "flag": t.get("flag_live"),
                     "ok": t.get("result", {}).get("ok"),
                     "نتیجه": (t.get("result", {}).get("reason") or "")[:50]}
                    for t in reversed(trail)]
            st.dataframe(pd.DataFrame(rows), width="stretch", height=200)

    # ── Kill switches — v4: pause/resume/stop روی قراردادِ موجود (flag-gated) ──
    with st.expander("🔌 Kill Switches", expanded=False):
        from control_plane.killswitch import (STOP_PHRASE, cancel_stop,
                                              kill_switch_live, pause_daemon,
                                              resume_daemon, stop_daemon)
        from control_plane.killswitch import audit_tail as ks_tail
        flags = all_flags()
        for name, val in flags.items():
            st.markdown(_pill(f"{name} = {int(val)}",
                              None if name == "CONTROL_PLANE_OBSERVE_ONLY" else not val),
                        unsafe_allow_html=True)
        ks_live = kill_switch_live()
        st.markdown(f"**Daemon:** `{d.get('status', '?')}` · "
                    f"pause: {'هست' if d.get('pause_file') else 'نیست'} · "
                    f"stop: {'هست' if d.get('stop_file') else 'نیست'}")
        if not ks_live:
            st.caption("⚪ غیرفعال — فعال‌سازی: CONTROL_PLANE_KILL_SWITCH_LIVE=1 در .env. "
                       "قراردادِ موجود: daemon.pause (مکثِ نرم — همان که تلگرام می‌سازد) · "
                       "daemon.stop (توقفِ تمیز).")
        else:
            st.caption("🟢 live — همه‌ی عمل‌ها فقط ساخت/حذفِ همان فایل‌های قراردادیِ "
                       "خودِ daemon هستند؛ هیچ کدی از daemon تغییر نکرده.")
            ks_ok = st.checkbox("می‌دانم این روی اجرای خودمختار اثر می‌گذارد",
                                key="ks_ok")
            c1, c2 = st.columns(2)
            if c1.button("⏸️ Pause (مکثِ نرم)", key="ks_pause"):
                r = pause_daemon(confirmed=ks_ok)
                (st.success if r["result"]["ok"] else st.error)(r["result"]["reason"])
            if c2.button("▶️ Resume", key="ks_resume"):
                r = resume_daemon(confirmed=ks_ok)
                (st.success if r["result"]["ok"] else st.error)(r["result"]["reason"])
            stop_txt = st.text_input(f"تأییدِ سخت — برای توقف دقیقاً بنویس: {STOP_PHRASE}",
                                     key="ks_stop_txt")
            if st.button("🛑 Stop daemon (توقفِ تمیز)", key="ks_stop"):
                r = stop_daemon(confirmed=ks_ok, confirm_text=stop_txt)
                (st.success if r["result"]["ok"] else st.error)(r["result"]["reason"])
            if d.get("stop_file"):
                if st.button("↩️ لغوِ stopِ معلق", key="ks_cancel"):
                    r = cancel_stop(confirmed=ks_ok)
                    (st.success if r["result"]["ok"] else st.error)(r["result"]["reason"])
            if d.get("status") == "STOPPED":
                st.caption("ℹ️ daemon الان خاموش است؛ ساختنِ stop فقط شروعِ بعدی را می‌بندد.")
        ks_trail = ks_tail(8)
        if ks_trail:
            st.markdown("**Evidence trail — آخرین عمل‌های kill-switch:**")
            import pandas as pd
            rows = [{"زمان": t.get("timestamp"), "عمل": t.get("kind"),
                     "confirm": t.get("confirmed"), "flag": t.get("flag_live"),
                     "ok": t.get("result", {}).get("ok"),
                     "rollback": (t.get("rollback") or "")[:45]}
                    for t in reversed(ks_trail)]
            st.dataframe(pd.DataFrame(rows), width="stretch", height=180)

    st.caption("صداقت: Brain-OS یک testbed است — هیچ ادعای آگاهیِ پدیداری/qualia در کار نیست. "
               "این سطح فقط access/routing/observability را نشان می‌دهد.")
