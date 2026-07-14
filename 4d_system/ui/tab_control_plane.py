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

    st.markdown(
        _pill(f"pause: {'هست' if d.get('pause_file') else 'نیست'}", not d.get("pause_file"))
        + " " + _pill(f"stop: {'هست' if d.get('stop_file') else 'نیست'}", not d.get("stop_file"))
        + " " + _pill(f"halt: {d.get('halted_at') or 'نه'}", not d.get("halted_at")),
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

    # ── Approvals (آینه‌ی فقط‌خواندنی) ───────────────────────────────────
    with st.expander("⏳ Approvals — فقط visibility", expanded=False):
        ap = snap["approvals"]
        pend = ap.get("self_code_pending", [])
        if pend:
            for p in pend:
                st.warning(f"**{p.get('id')}** → `{p.get('target')}` · "
                           f"هدف: {p.get('goal') or '—'} · {p.get('created_at')}")
        else:
            st.success("صفِ self_code خالی است.")
        st.caption(ap.get("note", ""))
        st.json(ap.get("self_code_counts", {}), expanded=False)

    # ── Kill switches (نمایشی — v4) ──────────────────────────────────────
    with st.expander("🔌 Kill Switches — غیرفعال (v4)", expanded=False):
        flags = all_flags()
        for name, val in flags.items():
            st.markdown(_pill(f"{name} = {int(val)}",
                              None if name == "CONTROL_PLANE_OBSERVE_ONLY" else not val),
                        unsafe_allow_html=True)
        st.caption("قراردادِ موجود: outputs/daemon.pause (مکث نرم) · outputs/daemon.stop "
                   "(توقف). فعال‌سازیِ این‌ها از UI فقط در v4، بعد از تست + approval مالک.")

    st.caption("صداقت: Brain-OS یک testbed است — هیچ ادعای آگاهیِ پدیداری/qualia در کار نیست. "
               "این سطح فقط access/routing/observability را نشان می‌دهد.")
