"""
ui/tab_laboratory.py — Interactive laboratory with Save/Load.

The researcher can explore parameters live, then save interesting
configurations with notes and tags for later recall.
"""
from __future__ import annotations

import streamlit as st
import numpy as np

from core.model import solve_from_stds
from core.scores import compute_scores_from_model
from ui.visuals import (
    radial_gauge, tesseract_projection,
    shadow_decomposition_chart, lambda_grid_heatmap,
)


def render_laboratory():
    """Main laboratory view with live sliders + save/load."""
    st.header("🌌 آزمایشگاه تعاملی")
    st.markdown("پارامترها را حرکت بده، الگو را کشف کن، و ذخیره‌اش کن.")

    # ── Init session state for lab parameters ──
    if "lab_rho" not in st.session_state:
        st.session_state.lab_rho = 0.5
        st.session_state.lab_lam = 0.5
        st.session_state.lab_se = 0.1
        st.session_state.lab_sz = 0.05
        st.session_state.lab_sd = 0.1
        st.session_state.lab_tess_rot = 0

    # ── Sidebar: saved patterns ──
    _render_saved_patterns_sidebar()

    # ── Main: parameter sliders ──
    col1, col2, col3 = st.columns(3)

    with col1:
        rho = st.slider("ρ — حافظه", 0.0, 0.95, st.session_state.lab_rho, 0.05,
                        key="slider_rho",
                        help="پایداریِ حالتِ پنهان")
        lam = st.slider("λ — نشت", 0.0, 2.0, st.session_state.lab_lam, 0.05,
                        key="slider_lam",
                        help="چقدر بُعد پنهان به مشاهدات لو می‌خورد")
    with col2:
        se = st.slider("σ_ε — نوفه‌ی مشاهده", 0.01, 0.5, st.session_state.lab_se, 0.01,
                       key="slider_se")
        sz = st.slider("σ_ζ — نوفه‌ی فرآیند", 0.01, 0.3, st.session_state.lab_sz, 0.01,
                       key="slider_sz")
    with col3:
        sd = st.slider("σ_d — دیترِ خصوصی", 0.0, 0.5, st.session_state.lab_sd, 0.01,
                       key="slider_sd")
        tess_rot = st.slider("🔄 تسراکت", 0, 360, st.session_state.lab_tess_rot, 5,
                              key="slider_tess")

    # Sync session state
    st.session_state.lab_rho = rho
    st.session_state.lab_lam = lam
    st.session_state.lab_se = se
    st.session_state.lab_sz = sz
    st.session_state.lab_sd = sd
    st.session_state.lab_tess_rot = tess_rot

    # ── Compute live ──
    sol = solve_from_stds(rho=rho, lam=lam, se=se, sz=sz, sd=sd)
    scores = compute_scores_from_model(rho=rho, lam=lam, se=se, sz=sz, sd=sd)

    # ── Gauges ──
    st.divider()
    st.subheader("📊 کمیت‌های زنده")

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(radial_gauge(
            max(sol.Delta_self, 0), "Δ_self", max_val=0.5,
            color="#1f3a5f", subtitle="درون‌نگری"
        ), width='stretch')
    with g2:
        st.plotly_chart(radial_gauge(
            max(sol.E_shadow, 0), "E_shadow", max_val=0.1,
            color="#6b4e8f", subtitle="ردِ پنهان"
        ), width='stretch')
    with g3:
        st.plotly_chart(radial_gauge(
            scores.sms, "SMS", max_val=0.5,
            color="#2d8659", subtitle="سودِ private"
        ), width='stretch')
    with g4:
        st.plotly_chart(radial_gauge(
            scores.pcai, "PCAI", max_val=1.0,
            color="#b8860b", subtitle="مزیت خصوصی"
        ), width='stretch')

    # ── Decomposition + Tesseract ──
    st.divider()
    left, right = st.columns([1, 1])

    with left:
        st.subheader("🔬 تجزیه‌ی سایه")
        st.plotly_chart(shadow_decomposition_chart(
            sol.sigma_z2, sol.Sb, sol.S
        ), width='stretch')

        identity = 0.5 * np.log(sol.sigma_z2 / sol.S) if sol.sigma_z2 > 0 and sol.S > 0 else 0
        e_plus_d = sol.E_shadow + sol.Delta_self
        check = abs(identity - e_plus_d) < 1e-6
        st.success(
            f"**اتحاد:** {identity:.6f} = E_shadow + Δ_self = {e_plus_d:.6f} "
            f"{'✓' if check else '✗'}"
        )

    with right:
        st.subheader("🧊 تسراکت")
        st.plotly_chart(tesseract_projection(tess_rot))

    # ── Heatmap ──
    st.divider()
    st.subheader("🗺️ نقشه‌ی فضای پارامتر")
    metric = st.radio("کمیت؟", ["Δ_self", "E_shadow", "PCAI"], horizontal=True)
    metric_key = {"Δ_self": "delta_self", "E_shadow": "e_shadow", "PCAI": "pcai"}[metric]
    st.plotly_chart(lambda_grid_heatmap(
        rho_values=[0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9],
        lambda_values=[0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5],
        se=se, sz=sz, sd=sd, metric=metric_key,
    ), width='stretch')

    # ── Save panel ──
    st.divider()
    _render_save_panel(rho, lam, se, sz, sd, sol, scores)


def _render_saved_patterns_sidebar():
    """Sidebar showing saved patterns that can be loaded."""
    with st.sidebar:
        st.divider()
        st.markdown("### ⭐ الگوهای ذخیره‌شده")

        try:
            from memory.research_store import get_patterns, get_all_tags
            patterns = get_patterns(limit=20)
            tags = get_all_tags()
        except Exception:
            patterns = []
            tags = []

        if patterns:
            tag_filter = st.selectbox(
                "فیلتر برچسب",
                ["همه"] + tags,
                key="lab_tag_filter"
            )

            for p in patterns:
                if tag_filter != "همه" and tag_filter not in (p.get("tags") or ""):
                    continue

                col_load, col_name = st.columns([1, 4])
                detect_mark = "✅" if p["detectable"] else "❌"
                with col_load:
                    if st.button("📋", key=f"load_{p['id']}", help=f"بارگذاری {p['name']}"):
                        st.session_state.lab_rho = p["rho"]
                        st.session_state.lab_lam = p["lam"]
                        st.session_state.lab_se = p["se"]
                        st.session_state.lab_sz = p["sz"]
                        st.session_state.lab_sd = p["sd"]
                        st.rerun()
                with col_name:
                    st.caption(f"{detect_mark} **{p['name']}** (Δ={p['delta_self']:.3f})")
        else:
            st.caption("_هنوز الگویی ذخیره نشده_")


def _render_save_panel(rho, lam, se, sz, sd, sol, scores):
    """Panel for saving the current configuration."""
    st.subheader("💾 ذخیره‌ی الگوی فعلی")

    with st.form("save_pattern_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("نام الگو", value=f"config-ρ{rho:.1f}-λ{lam:.1f}",
                                 key="save_name")
        with col2:
            tags = st.text_input("برچسب‌ها (کاما جدا)", value="",
                                 key="save_tags",
                                 placeholder="مثال: memory,strong,high-shadow")

        note = st.text_area("یادداشت / تفسیر", value="", height=80,
                            key="save_note",
                            placeholder="چه الگویی کشف کردی؟ چرا جالب است؟")

        if st.form_submit_button("💾 ذخیره", type="primary", width='stretch'):
            from memory.research_store import save_pattern, SavedPattern

            p = SavedPattern(
                name=name,
                rho=rho, lam=lam, se=se, sz=sz, sd=sd,
                delta_self=sol.Delta_self,
                e_shadow=max(sol.E_shadow, 0),
                pcai=scores.pcai,
                sms=scores.sms,
                detectable=sol.detectable,
                note=note,
                tags=tags,
            )
            pid = save_pattern(p)
            st.success(f"✓ الگوی «{name}» ذخیره شد (#{pid})")
            st.rerun()

    # Quick interpretation
    st.info(scores.interpret())
