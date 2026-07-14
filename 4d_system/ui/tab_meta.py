"""
ui/tab_meta.py — پنل خودآگاهی و رشدِ سیستم

این تب «مغزِ فراشناختی» است. کاربر جهت می‌ده، سیستم:
  ۱. خودش رو می‌بینه (self-model)
  ۲. وب رو می‌گرده
  ۳. با LLM ترکیب می‌کنه
  ۴. پروپوزال ارتقا می‌سازه
  ۵. نمایش می‌ده

+ تاریخچه‌ی جلسات تحقیق
+ پروپوزال‌های ذخیره‌شده (approve / reject)
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import json


@st.cache_data(ttl=600, show_spinner="🔍 خواندن ساختار سیستم...")
def _cached_self_map():
    """اسکن AST کل پروژه سنگین است — هر ۱۰ دقیقه یکبار کافی است."""
    from brain.self_model import build_self_map
    return build_self_map()


def render_meta_tab():
    """رندر کردن تب خودآگاهی."""

    st.markdown("## 🧠 خودآگاهی و رشد")
    st.caption("سیستم خودش رو می‌بینه، تحقیق می‌کنه، و پیشنهاد ارتقا می‌ده")

    # ── بخش ۱: Self-Model زنده ──────────────────────────────────────
    st.markdown("### 🔍 مدلِ خود")

    try:
        sm = _cached_self_map()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("فایل‌ها", sm.total_files)
        c2.metric("خطوط کد", f"{sm.total_lines:,}")
        c3.metric("کلاس‌ها", sm.total_classes)
        c4.metric("توابع", sm.total_functions)

        # Capabilities
        cap_col, lim_col = st.columns(2)

        with cap_col:
            st.markdown("**✅ توانمندی‌ها:**")
            for cap in sm.capabilities:
                st.markdown(f"- {cap}")

        with lim_col:
            st.markdown("**⚠️ محدودیت‌ها:**")
            for lim in sm.limitations:
                st.markdown(f"- {lim}")

    except Exception as e:
        st.error(f"خطا در self-model: {e}")

    st.divider()

    # ── بخش ۲: جهت‌دهی و تحقیق ─────────────────────────────────────
    st.markdown("### 🎯 جهت‌دهی تحقیق")

    # اعمال پیشنهادِ انتخاب‌شده قبل از ساخت ویجت — تخصیص مستقیم به key
    # بعد از instantiate شدن ویجت StreamlitAPIException می‌دهد.
    if "meta_direction_pending" in st.session_state:
        st.session_state.meta_direction = st.session_state.pop("meta_direction_pending")

    direction = st.text_area(
        "چه چیزی رو می‌خوای سیستم کشف/بهبود بده؟ (دستورکار: Brain-OS چندایجنتی)",
        placeholder="مثلا: چطور یک فضای کاری جهانی با آزمونِ اشتعال بسازم؟ یا: خودمدلِ فراشناختِ کالیبره چطور؟",
        height=80,
        key="meta_direction",
    )

    q_col1, q_col2, q_col3 = st.columns([2, 1, 1])

    with q_col2:
        use_llm = st.checkbox("استفاده از LLM", value=False,
                              help="اگر خاموش باشه، فقط تحلیل محلی (سریع‌تر)")

    with q_col3:
        max_web = st.number_input("حداکثر منابع وب", 2, 10, 4, key="meta_maxweb")

    with q_col1:
        run_clicked = st.button("🔬 شروع تحقیق", type="primary", key="meta_run",
                                disabled=not direction.strip())

    # Quick suggestions
    st.markdown("")
    sug_col1, sug_col2, sug_col3 = st.columns(3)
    with sug_col1:
        if st.button("💡 فضای کاری جهانی", key="sug1"):
            st.session_state.meta_direction_pending = (
                "چطور یک لایه‌ی فضای کاری جهانی (Global Workspace) با آزمونِ اشتعالِ "
                "همه‌یا‌هیچ روی گذرگاهِ رویداد بسازم و اثرش را بر مقاومت به goal-drift بسنجم؟")
            st.rerun()
    with sug_col2:
        if st.button("💡 خودمدلِ کالیبره", key="sug2"):
            st.session_state.meta_direction_pending = (
                "چطور یک خودمدلِ فراشناختِ کالیبره بسازم که traceها را تحلیل کند، "
                "اعتماد را کالیبره (meta-d′/ECE) کند و به نگهبان‌ها خوراک دهد؟")
            st.rerun()
    with sug_col3:
        if st.button("💡 حافظه‌ی مغز‌الهام", key="sug3"):
            st.session_state.meta_direction_pending = (
                "چطور حافظه‌ی چندلایه‌ی مغز‌الهام‌گرفته (اپیزودیک/معنایی/salience) با "
                "consolidationِ شبه‌خواب (coarse-graining زمانی) اضافه کنم؟")
            st.rerun()

    # ── اجرای تحقیق ────────────────────────────────────────────────
    if run_clicked and direction.strip():
        st.markdown("---")
        progress = st.progress(0, text="آماده‌سازی...")

        # Phase 1: Self-model
        progress.progress(15, text="🔍 خواندن ساختار سیستم...")
        import time as _time
        _time.sleep(0.3)

        # Phase 2: Web search
        progress.progress(35, text="🌐 جستجوی وب (arXiv + Wikipedia + DuckDuckGo)...")
        _time.sleep(0.3)

        # Phase 3: Synthesis
        brain_label = "🧠 ترکیب با GLM..." if use_llm else "🧠 ترکیب محلی..."
        progress.progress(60, text=brain_label)

        try:
            from brain.meta_research import run_meta_research

            result = run_meta_research(
                direction=direction.strip(),
                use_llm=use_llm,
                max_web_results=max_web,
            )

            progress.progress(90, text="💾 ذخیره پروپوزال‌ها...")
            _time.sleep(0.3)
            progress.progress(100, text="✅ کامل شد!")

            # Store in session
            st.session_state["meta_last_result"] = result

        except Exception as e:
            progress.empty()
            st.error(f"خطا در تحقیق: {e}")
            import logging, traceback
            logging.getLogger(__name__).error("meta research failed:\n%s",
                                              traceback.format_exc())
            with st.expander("جزئیات فنی خطا"):
                st.code(traceback.format_exc())

    # ── نمایش نتیجه‌ی آخرین تحقیق ──────────────────────────────────
    if "meta_last_result" in st.session_state:
        result = st.session_state["meta_last_result"]

        st.markdown("---")
        st.markdown("### 📊 نتیجه‌ی تحقیق")

        # Phases timeline
        st.markdown("**مراحل اجرا:**")
        for step in result.steps:
            icon = {"done": "✅", "running": "⏳", "error": "❌"}.get(step.status, "❓")
            st.markdown(f"{icon} **{step.phase}** — {step.detail}")

        # Sources found
        if result.web_results:
            import html as _html
            st.markdown(f"**منابع پیدا‌شده ({len(result.web_results)}):**")
            for wr in result.web_results[:6]:
                src_icon = {"arxiv": "📄", "wikipedia": "📚", "duckduckgo": "🌐"}.get(wr.source, "🔗")
                # escape محتوای وب نامطمئن — با unsafe_allow_html رندر می‌شود
                safe_title = _html.escape(wr.title[:70])
                safe_snip = _html.escape(wr.snippet[:120])
                safe_url = wr.url if wr.url.startswith(("http://", "https://")) else "#"
                st.markdown(
                    f"{src_icon} [{safe_title}]({safe_url})\n"
                    f"&nbsp;&nbsp;&nbsp;<small>{safe_snip}</small>",
                    unsafe_allow_html=True,
                )

        # Synthesis
        if result.synthesis:
            st.markdown("---")
            st.markdown("**تحلیل سیستم:**")
            st.info(result.synthesis[:600])

        # Proposals
        if result.proposals:
            st.markdown("---")
            st.markdown(f"### 💡 پروپوزال‌های ارتقا ({len(result.proposals)})")

            for i, prop in enumerate(result.proposals, 1):
                _render_proposal(prop, i)

    st.divider()

    # ── بخش ۳: تاریخچه‌ی جلسات ─────────────────────────────────────
    st.markdown("### 📜 تاریخچه‌ی تحقیقات")

    try:
        from memory.research_store import get_research_sessions

        sessions = get_research_sessions(limit=10)

        if sessions:
            for sess in sessions[:5]:
                with st.expander(
                    f"🔬 #{sess['id']} — {sess['topic'][:50]} "
                    f"({sess.get('timestamp', '')[:10]}) — "
                    f"{sess.get('sources_found', 0)} منبع"
                ):
                    st.markdown(f"**جهت:** {sess.get('direction', '')}")
                    st.markdown(f"**تحلیل:** {sess.get('insights', '')[:300]}")
                    if sess.get("proposals"):
                        st.caption(f"پروپوزال‌ها: {', '.join(str(p) for p in sess['proposals'])}")
        else:
            st.caption("هنوز تحقیقی انجام نشده")

    except Exception as e:
        st.caption(f"(تاریخچه در دسترس نیست: {e})")

    st.divider()

    # ── بخش ۴: همه‌ی پروپوزال‌ها ────────────────────────────────────
    st.markdown("### 🗂️ همه‌ی پروپوزال‌های ارتقا")

    try:
        from memory.research_store import get_proposals, update_proposal_status

        proposals = get_proposals(limit=20)

        if proposals:
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                status_filter = st.selectbox(
                    "فیلتر وضعیت",
                    ["همه", "proposed", "approved", "implemented", "rejected"],
                    key="meta_prop_filter",
                )
            with filter_col2:
                priority_filter = st.selectbox(
                    "فیلتر اولویت",
                    ["همه", "critical", "high", "medium", "low"],
                    key="meta_pri_filter",
                )

            filtered = proposals
            if status_filter != "همه":
                filtered = [p for p in filtered if p.get("status") == status_filter]
            if priority_filter != "همه":
                filtered = [p for p in filtered if p.get("priority") == priority_filter]

            for prop in filtered:
                _render_saved_proposal(prop, update_proposal_status)
        else:
            st.caption("هنوز پروپوزالی ساخته نشده. یک تحقیق شروع کن!")

    except Exception as e:
        st.error(f"خطا در بارگذاری پروپوزال‌ها: {e}")


def _render_proposal(prop: dict, idx: int):
    """نمایش یک پروپوزال تازه‌ساخته‌شده."""

    title = prop.get("title", f"پروپوزال {idx}")
    priority = prop.get("priority", "medium")
    effort = prop.get("effort", "medium")
    module = prop.get("target_module", "")
    desc = prop.get("description", "")
    rationale = prop.get("rationale", "")
    sketch = prop.get("code_sketch", "")
    refs = prop.get("references", [])

    # Priority color
    pri_colors = {"critical": "#d32f2f", "high": "#f57c00",
                  "medium": "#fbc02d", "low": "#689f38"}
    pri_color = pri_colors.get(priority, "#999")

    with st.container():
        # escape محتوای LLM-ساخته — همان الگوی بلوکِ نتایجِ وب (بالاتر در همین فایل)؛
        # قبلاً title/module خام داخل unsafe_allow_html می‌رفت (تزریق HTML/JS ممکن بود).
        import html as _html
        st.markdown(
            f"<div style='background: linear-gradient(135deg, #f5f0ff, #f0f5ff); "
            f"color: #1f1f2e; "
            f"padding: 1rem 1.2rem; border-radius: 10px; "
            f"border-right: 4px solid {pri_color}; margin: 0.5rem 0;'>"
            f"<b>💡 {idx}. {_html.escape(str(title))}</b><br>"
            f"<small style='color:{pri_color}'>{_html.escape(str(priority).upper())}</small> · "
            f"<small>زرمت: {_html.escape(str(effort))}</small> · "
            f"<small>ماژول: <code>{_html.escape(str(module))}</code></small>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if desc:
            st.markdown(f"**توضیح:** {desc}")

        if rationale:
            st.markdown(f"**دلیل:** {rationale}")

        if sketch:
            with st.expander("اسکچ کد"):
                st.code(sketch, language="python")

        if refs:
            st.markdown("**منابع:**")
            for ref in refs[:3]:
                st.markdown(f"- [{ref[:60]}]({ref})" if ref.startswith("http") else f"- {ref}")


def _render_saved_proposal(prop: dict, update_fn):
    """نمایش یک پروپوزال ذخیره‌شده با دکمه‌های approve/reject."""

    pid = prop["id"]
    title = prop.get("title", "")
    priority = prop.get("priority", "medium")
    status = prop.get("status", "proposed")
    module = prop.get("target_module", "")

    status_icons = {
        "proposed": "📝", "approved": "✅",
        "implemented": "🚀", "rejected": "❌"
    }
    icon = status_icons.get(status, "📝")

    with st.expander(f"{icon} #{pid} — {title} [{priority}/{status}]"):
        st.markdown(f"**ماژول هدف:** `{module}`")
        if prop.get("description"):
            st.markdown(f"**توضیح:** {prop['description']}")
        if prop.get("rationale"):
            st.markdown(f"**دلیل:** {prop['rationale']}")
        if prop.get("code_sketch"):
            st.code(prop["code_sketch"], language="python")

        refs = prop.get("references", [])
        if refs:
            st.markdown("**منابع:**")
            for ref in refs[:3]:
                if isinstance(ref, str) and ref.startswith("http"):
                    st.markdown(f"- [{ref[:60]}]({ref})")
                else:
                    st.markdown(f"- {ref}")

        # Action buttons
        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1:
            if st.button("✅ تأیید", key=f"appr_{pid}"):
                update_fn(pid, "approved")
                st.rerun()
        with bc2:
            if st.button("🚀 پیاده‌سازی", key=f"impl_{pid}"):
                update_fn(pid, "implemented")
                st.rerun()
        with bc3:
            if st.button("❌ رد", key=f"rej_{pid}"):
                update_fn(pid, "rejected")
                st.rerun()
        with bc4:
            if st.button("🔄 باز‌نگری", key=f"rev_{pid}"):
                update_fn(pid, "proposed")
                st.rerun()
