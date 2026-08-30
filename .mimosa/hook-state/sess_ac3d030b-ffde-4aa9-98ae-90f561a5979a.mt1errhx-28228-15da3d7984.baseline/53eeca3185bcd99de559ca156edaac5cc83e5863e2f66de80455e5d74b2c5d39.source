"""
ui/tab_research.py — Research workspace tab.

Browse saved patterns, compose architectures, write notes,
and compare discoveries.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ui.visuals import radial_gauge


def render_research():
    """Main research workspace."""
    st.header("🔬 پژوهش")
    st.markdown("الگوهای ذخیره‌شده، معماری‌های ترکیبی، و یادداشت‌ها")

    # Stats
    from memory.research_store import get_research_stats
    stats = get_research_stats()

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("الگوها", stats["patterns"])
    s2.metric("معماری‌ها", stats["architectures"])
    s3.metric("یادداشت‌ها", stats["notes"])
    s4.metric("تأییدشده", stats["validated"])

    # Sub-tabs
    sub1, sub2, sub3 = st.tabs(["⭐ الگوها", "🏗️ معماری‌ها", "📝 یادداشت‌ها"])

    with sub1:
        _render_patterns_view()
    with sub2:
        _render_architectures_view()
    with sub3:
        _render_notes_view()


def _render_patterns_view():
    """Browse, filter, load, delete, and compare saved patterns."""
    from memory.research_store import (
        get_patterns, get_all_tags, get_pattern,
        delete_pattern, update_pattern_note
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tags = get_all_tags()
        tag_filter = st.selectbox("فیلتر برچسب", ["همه"] + tags, key="pat_tag")
    with col_f2:
        name_search = st.text_input("جست‌وجو در نام", "", key="pat_search")

    patterns = get_patterns(
        tag_filter="" if tag_filter == "همه" else tag_filter,
        name_filter=name_search,
    )

    if not patterns:
        st.info("هنوز الگویی ذخیره نشده. از تب «آزمایشگاه» الگو را ذخیره کن.")
        return

    # Table view
    df = pd.DataFrame([{
        "ID": p["id"],
        "نام": p["name"],
        "ρ": p["rho"],
        "λ": p["lam"],
        "Δ_self": round(p["delta_self"], 4),
        "E_shadow": round(p["e_shadow"], 4),
        "PCAI": round(p["pcai"], 3),
        "تشخیص": "✅" if p["detectable"] else "❌",
        "برچسب‌ها": p["tags"],
        "تاریخ": p["timestamp"][:10],
    } for p in patterns])
    st.dataframe(df, width='stretch', hide_index=True)

    # Actions
    st.divider()
    st.subheader("عملیات روی الگو")

    selected_id = st.selectbox(
        "الگو را انتخاب کن",
        [p["id"] for p in patterns],
        format_func=lambda i: next((p["name"] for p in patterns if p["id"] == i), str(i)),
        key="pat_selected"
    )

    if selected_id:
        pat = get_pattern(selected_id)
        if pat:
            action_col = st.columns(5)

            with action_col[0]:
                if st.button("📋 بارگذاری در آزمایشگاه", key="pat_load"):
                    st.session_state.lab_rho = pat["rho"]
                    st.session_state.lab_lam = pat["lam"]
                    st.session_state.lab_se = pat["se"]
                    st.session_state.lab_sz = pat["sz"]
                    st.session_state.lab_sd = pat["sd"]
                    st.success("بارگذاری شد! به تب آزمایشگاه برو.")
                    st.rerun()

            with action_col[1]:
                if st.button("🗑️ حذف", key="pat_del"):
                    delete_pattern(selected_id)
                    st.warning("حذف شد.")
                    st.rerun()

            # Edit note
            st.divider()
            new_note = st.text_area("یادداشت", value=pat["note"], key="pat_note_edit")
            new_tags = st.text_input("برچسب‌ها", value=pat["tags"], key="pat_tags_edit")
            if st.button("💾 به‌روزرسانی", key="pat_save"):
                update_pattern_note(selected_id, new_note, new_tags)
                st.success("به‌روزرسانی شد.")
                st.rerun()

    # Compare two patterns
    st.divider()
    st.subheader("🔄 مقایسه‌ی دو الگو")
    cmp_col = st.columns(2)
    with cmp_col[0]:
        id_a = st.selectbox("الگوی A", [p["id"] for p in patterns],
                            format_func=lambda i: next((p["name"] for p in patterns if p["id"] == i), ""),
                            key="cmp_a")
    with cmp_col[1]:
        id_b = st.selectbox("الگوی B", [p["id"] for p in patterns],
                            format_func=lambda i: next((p["name"] for p in patterns if p["id"] == i), ""),
                            key="cmp_b")

    if id_a and id_b and id_a != id_b:
        pa = get_pattern(id_a)
        pb = get_pattern(id_b)
        if pa and pb:
            g_col = st.columns(4)
            metrics = [
                ("Δ_self", "delta_self", "#1f3a5f", 0.5),
                ("E_shadow", "e_shadow", "#6b4e8f", 0.1),
                ("SMS", "sms", "#2d8659", 0.5),
                ("PCAI", "pcai", "#b8860b", 1.0),
            ]
            for i, (label, key, color, mx) in enumerate(metrics):
                with g_col[i]:
                    ga = radial_gauge(pa[key], f"A: {label}", max_val=mx, color=color)
                    gb = radial_gauge(pb[key], f"B: {label}", max_val=mx, color=color)
                    st.plotly_chart(ga)
                    st.plotly_chart(gb)


def _render_architectures_view():
    """Compose and browse multi-pattern architectures."""
    from memory.research_store import (
        get_architectures, save_architecture, delete_architecture,
        update_architecture_status, get_patterns, SavedArchitecture
    )

    # Existing architectures
    archs = get_architectures()
    if archs:
        df = pd.DataFrame([{
            "ID": a["id"],
            "نام": a["name"],
            "توصیف": a["description"][:40],
            "الگوها": len(a["parent_ids"]),
            "وضعیت": a["status"],
            "تاریخ": a["timestamp"][:10],
        } for a in archs])
        st.dataframe(df, width='stretch', hide_index=True)

        # Status management
        st.divider()
        arch_id = st.selectbox(
            "معماری را انتخاب کن",
            [a["id"] for a in archs],
            format_func=lambda i: next((a["name"] for a in archs if a["id"] == i), ""),
            key="arch_select"
        )
        if arch_id:
            arch = next((a for a in archs if a["id"] == arch_id), None)
            if arch:
                st.markdown(f"**توضیح:** {arch['description']}")
                st.markdown(f"**یادداشت:** {arch['note']}")

                status = st.radio(
                    "وضعیت",
                    ["draft", "testing", "validated"],
                    index=["draft", "testing", "validated"].index(arch["status"]),
                    horizontal=True,
                    key="arch_status"
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("💾 به‌روزرسانی وضعیت", key="arch_upd"):
                        update_architecture_status(arch_id, status)
                        st.success("به‌روزرسانی شد.")
                        st.rerun()
                with c2:
                    if st.button("🗑️ حذف", key="arch_del"):
                        delete_architecture(arch_id)
                        st.rerun()

    # Create new architecture
    st.divider()
    st.subheader("🏗️ معماری جدید")

    patterns = get_patterns(limit=50)
    if not patterns:
        st.info("برای ساخت معماری، اول الگوها را در آزمایشگاه ذخیره کن.")
        return

    with st.form("new_arch_form"):
        name = st.text_input("نام معماری", key="arch_name")
        desc = st.text_area("توصیف", key="arch_desc",
                            placeholder="این معماری چه می‌کند؟ چرا این الگوها را ترکیب کردی؟")

        selected = st.multiselect(
            "الگوهای تشکیل‌دهنده",
            [p["id"] for p in patterns],
            format_func=lambda i: next((f"{p['name']} (Δ={p['delta_self']:.3f})" for p in patterns if p["id"] == i), ""),
            key="arch_parents"
        )

        note = st.text_area("یادداشت", key="arch_note")

        if st.form_submit_button("🏗️ بساز", type="primary"):
            if name and selected:
                aid = save_architecture(SavedArchitecture(
                    name=name, description=desc,
                    parent_ids=selected,
                    config={"layer_count": len(selected)},
                    note=note, status="draft"
                ))
                st.success(f"معماری «{name}» ساخته شد (#{aid})")
                st.rerun()
            else:
                st.error("نام و حداقل یک الگو الزامی است.")


def _render_notes_view():
    """Free-form research notes."""
    from memory.research_store import get_notes, save_note, delete_note, ResearchNote

    # Search
    search = st.text_input("🔍 جست‌وجو", "", key="note_search")
    notes = get_notes(search=search)

    # New note
    with st.expander("➕ یادداشت جدید", expanded=False):
        with st.form("new_note_form"):
            title = st.text_input("عنوان", key="note_title")
            content = st.text_area("متن", height=100, key="note_content")
            if st.form_submit_button("💾 ذخیره"):
                if content:
                    save_note(ResearchNote(title=title, content=content))
                    st.success("ذخیره شد.")
                    st.rerun()

    # List notes
    st.divider()
    if not notes:
        st.info("یادداشتی وجود ندارد.")
        return

    for n in notes:
        with st.expander(f"📝 {n['title'] or 'بدون عنوان'} — {n['timestamp'][:16]}"):
            st.text(n["content"])
            if st.button("🗑️ حذف", key=f"note_del_{n['id']}"):
                delete_note(n["id"])
                st.rerun()
