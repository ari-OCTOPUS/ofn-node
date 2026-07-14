"""
ui/tab_graph.py — تب گراف دانش و ریتم‌ها

محتوا:
  ۱. گراف Obsidian تعاملی (force-directed)
  ۲. آمار گراف و hub‌ها
  ۳. معادلات ریاضی کلیدی (LaTeX)
  ۴. ریتم‌های خام ذخیره‌شده (حافظه‌ی پایه)
  ۵. مقایسه‌ی راداری ریتم‌ها
  ۶. دکمه‌های مدیریت: wikilink‌گذاری، ایجاد ریتم پایه
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np


# ════════════════════════════════════════════════════════════════════════
# Cache — یکبار parse برای همه‌ی بخش‌ها + invalidation خودکار با تغییر vault
# ════════════════════════════════════════════════════════════════════════

def _vault_signature() -> tuple:
    """امضای سبک vault (تعداد فایل + آخرین تغییر) — کلید cache."""
    try:
        from brain.vault_sync import VAULT_DIR
        mtimes = [f.stat().st_mtime for f in VAULT_DIR.rglob("*.md")
                  if ".obsidian" not in str(f) and "آرشیو" not in str(f)]
        return (len(mtimes), max(mtimes, default=0.0))
    except Exception:
        return (0, 0.0)


@st.cache_data(ttl=600, show_spinner="🕸️ خواندن گراف vault...")
def _cached_vault_graph(sig: tuple):
    from brain.vault_sync import parse_vault_graph
    return parse_vault_graph()


@st.cache_data(ttl=600, show_spinner="🎨 محاسبه‌ی چیدمان گراف...")
def _cached_graph_figure(sig: tuple):
    from ui.visuals import obsidian_graph
    return obsidian_graph(_cached_vault_graph(sig))


def _clear_graph_caches():
    _cached_vault_graph.clear()
    _cached_graph_figure.clear()


def render_graph_tab():
    """رندر کردن تب گراف دانش."""

    st.markdown("## 🕸️ گراف دانش")

    # ════════════════════════════════════════════════════════════════════
    # بخش ۱: گراف Obsidian تعاملی
    # ════════════════════════════════════════════════════════════════════

    gc1, gc2, gc3 = st.columns([2, 1, 1])

    with gc1:
        if st.button("🔗 wikilink‌گذاری خودکار", help="اسکن vault و اضافه‌کردن wikilink"):
            with st.spinner("در حال wikilink‌گذاری..."):
                from brain.vault_sync import autolink_vault
                results = autolink_vault(dry_run=False)
                total = sum(r.links_added for r in results)
                st.success(f"✅ {total} wikilink جدید در {len(results)} فایل اضافه شد")
                _clear_graph_caches()
                st.rerun()

    with gc2:
        if st.button("🧬 ایجاد ریتم‌های پایه", help="تولید ۶ ریتم مرجع"):
            with st.spinner("تولید ریتم‌های پایه..."):
                from data.rhythm_store import ensure_base_rhythms
                n = ensure_base_rhythms(force=True)
                st.success(f"✅ {n} ریتم پایه ایجاد شد")
                st.rerun()

    with gc3:
        if st.button("🔄 بازخوانی گراف"):
            _clear_graph_caches()
            st.rerun()

    st.markdown("### 🔮 شبکه‌ی دانش (Obsidian Graph)")

    vault_sig = _vault_signature()

    try:
        st.plotly_chart(_cached_graph_figure(vault_sig), width='stretch')
    except Exception as e:
        st.error(f"خطا در رسم گراف: {e}")

    # آمار گراف — از همان گراف cache‌شده (بدون parse دوباره)
    try:
        graph = _cached_vault_graph(vault_sig)
        folders = {nd.get("folder", "root") for nd in graph.nodes}

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("یادداشت‌ها", graph.n_nodes)
        s2.metric("پیوندها", graph.n_edges)
        s3.metric("پوشه‌ها", len(folders))
        s4.metric("میانگین link/یادداشت", f"{graph.n_edges / max(graph.n_nodes, 1):.1f}")

        # Hub‌ها
        hubs = graph.hubs[:5]
        if hubs:
            st.markdown("**🌟 Hub‌های اصلی (بیشترین پیوند ورودی):**")
            hub_cols = st.columns(min(len(hubs), 5))
            for i, hub in enumerate(hubs):
                with hub_cols[i]:
                    st.metric(hub["name"][:20], f"{hub['incoming']} ←")

    except Exception as e:
        st.caption(f"(آمار در دسترس نیست: {e})")

    # ════════════════════════════════════════════════════════════════════
    # بخش ۲: معادلات ریاضی کلیدی
    # ════════════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("### 📐 معادلات بنیادی — ارتباط ۳D ↔ ۴D")

    with st.expander("🔍 مدل خطی-گاوسی (SOG)", expanded=True):
        st.latex(r"s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)")
        st.latex(r"Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)")
        st.caption("`s(t)` = بُعد پنهان (۴D) | `Y(t)` = سایه‌ی مشاهده‌شده (۳D) | "
                   "`ρ` = حافظه | `λ` = نشت")

    with st.expander("⚡ سه کمیت محوری"):
        st.markdown("**ارزش درون‌نگری** — فاصله‌ی «خودآگاه» و «ناظرِ باهوش»:")
        st.latex(r"\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 0.122520")

        st.markdown("**سایه‌ی اطلاعاتی** — «آیا اصلاً بُعدی پنهان هست؟»:")
        st.latex(r"E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 0.012553")

        st.markdown("**اتحاد chain-rule** (همیشه برقرار):")
        st.latex(r"\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 0.135073")

    with st.expander("🎯 قضیه‌ی شناسایی"):
        st.latex(r"E_{shadow} > 0 \iff \lambda \cdot \rho \neq 0")
        st.caption("برای دیدن بُعد پنهان، هم **نشت** (λ) لازم است هم **حافظه** (ρ).")

    with st.expander("🌀 معادله‌ی Riccati (DARE)"):
        st.latex(r"P = \frac{\rho^2 P \sigma_\varepsilon^2}{\lambda^2 P + \sigma_\varepsilon^2} + \sigma_\zeta^2")
        st.caption("حلِ بسته‌ی این معادله‌ی درجه‌۲، کف کالمن رو می‌ده.")

    with st.expander("🔷 پل ۳D → ۴D (هندسه)"):
        st.markdown("""
        مثل ساکنانِ **فلت‌لند** که فقط سایه‌ی اشیاء ۳D رو می‌بینن،
        ما هم فقط **سایه‌ی بُعد چهارم** رو در داده‌ها مشاهده می‌کنیم.

        - هر نقطه‌ی ۴D → **projection** در ۳D = سری زمانی `Y(t)`
        - بُعد پنهان `s(t)` همیشه **غیرقابل مشاهده‌ی مستقیم** است
        - ابزار ریاضی: **توموگرافی اطلاعاتی** (Diaconis-Freedman، قضیه‌ی Takens)
        """)
        st.latex(r"\text{看到} = \text{اشیاء 4D} \xrightarrow{\text{projection}} \text{سایه‌ی 3D} = Y(t)")

    # ════════════════════════════════════════════════════════════════════
    # بخش ۳: ریتم‌های خام — حافظه‌ی پایه
    # ════════════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("### 🎵 ریتم‌های خام — حافظه‌ی پایه")

    try:
        from data.rhythm_store import get_rhythms, load_rhythm, get_rhythm_count

        rhythms = get_rhythms()

        if rhythms:
            st.caption(f"{get_rhythm_count()} ریتم ذخیره‌شده")

            # جدول ریتم‌ها
            rows = []
            for r in rhythms:
                rows.append({
                    "#": r["id"],
                    "نام": r["name"],
                    "نوع": r.get("source_type", "?"),
                    "MI": f"{r.get('mi', 0):.4f}",
                    "ρ̂": f"{r.get('rho_hat', 0):.3f}",
                    "n": r.get("n_points", 0),
                    "تشخیص": "✅" if r.get("detectable") else "❌",
                    "تگ": r.get("tags", ""),
                })
            st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

            # نمودار راداری
            st.markdown("#### 📊 مقایسه‌ی ریتم‌ها")
            from ui.visuals import rhythm_radar
            st.plotly_chart(rhythm_radar(rhythms), width='stretch')

            # نمایش سری زمانی یک ریتم
            st.markdown("#### 📈 نمایش ریتم")
            selected_id = st.selectbox(
                "انتخاب ریتم:",
                options=[r["id"] for r in rhythms],
                format_func=lambda rid: next(
                    (r["name"] for r in rhythms if r["id"] == rid), str(rid)
                ),
                key="rhythm_select"
            )

            if selected_id:
                rhythm = load_rhythm(selected_id)
                if rhythm:
                    from ui.visuals import series_with_shadow
                    fig = series_with_shadow(
                        rhythm.series[:1000],
                        temporal_mi=rhythm.mi,
                        detectable=rhythm.detectable,
                    )
                    st.plotly_chart(fig, width='stretch')

                    # آمار سری
                    rs1, rs2, rs3, rs4 = st.columns(4)
                    rs1.metric("طول", f"{len(rhythm.series):,}")
                    rs2.metric("میانگین", f"{np.mean(rhythm.series):.4f}")
                    rs3.metric("انحراف معیار", f"{np.std(rhythm.series):.4f}")
                    rs4.metric("MI", f"{rhythm.mi:.4f}")

        else:
            st.info("هنوز ریتمی ذخیره نشده. دکمه‌ی «🧬 ایجاد ریتم‌های پایه» رو بزن.")

    except Exception as e:
        st.error(f"خطا در بارگذاری ریتم‌ها: {e}")

    # ════════════════════════════════════════════════════════════════════
    # بخش ۴: انتخاب node و مشاهده محتوا
    # ════════════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("### 📖 کاوش یادداشت")

    try:
        from brain.vault_sync import get_node_content

        graph = _cached_vault_graph(vault_sig)
        node_names = sorted([nd["name"] for nd in graph.nodes])

        selected_node = st.selectbox(
            "انتخاب یادداشت:",
            options=node_names,
            index=0 if node_names else None,
            key="node_select"
        )

        if selected_node:
            # ابتدا از مسیر ذخیره‌شده در گراف بخوان (بدون اسکن دوباره‌ی vault)
            content = None
            node = next((nd for nd in graph.nodes if nd["name"] == selected_node), None)
            if node and node.get("path"):
                try:
                    from brain.vault_sync import VAULT_DIR
                    content = (VAULT_DIR / node["path"]).read_text(
                        encoding="utf-8", errors="replace")
                except Exception:
                    content = None
            if content is None:
                content = get_node_content(selected_node)
            if content:
                # Find links in/out
                incoming = [e["source"] for e in graph.edges if e["target"] == selected_node]
                outgoing = graph.adjacency.get(selected_node, [])

                lc1, lc2 = st.columns(2)
                with lc1:
                    st.caption(f"**پیوندهای ورودی** ({len(incoming)}):")
                    for link in incoming[:8]:
                        st.markdown(f"- {link}")
                with lc2:
                    st.caption(f"**پیوندهای خروجی** ({len(outgoing)}):")
                    for link in outgoing[:8]:
                        st.markdown(f"- {link}")

                with st.expander("📄 محتوای کامل یادداشت", expanded=False):
                    st.markdown(content[:3000])

    except Exception as e:
        st.caption(f"(کاوش یادداشت در دسترس نیست: {e})")
