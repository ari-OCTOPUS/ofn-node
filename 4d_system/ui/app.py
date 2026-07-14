"""
ui/app.py — «ایده‌یاب شخصی» v4 — سیستم پژوهشِ خودمختارِ خودآگاه

دو تب:
  🔄 لوپ پژوهش — کشف خودکار الگوها در داده‌های سری‌زمانی
  🧠 خودآگاهی — سیستم خودش رو می‌بینه، تحقیق می‌کنه، ارتقا پیشنهاد می‌ده

Run: streamlit run run.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import numpy as np
import pandas as pd
import time

# ════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="ایده‌یاب", page_icon="🌌", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { max-width: 1000px; margin: 0 auto; }
    .pulse-dot {
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; margin-left: 8px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .insight-box {
        background: linear-gradient(135deg, #f5f0ff, #f0f5ff);
        color: #1f1f2e;  /* متن تیره — در تم تیره‌ی Streamlit هم خوانا */
        padding: 0.8rem 1.2rem; border-radius: 10px;
        border-right: 3px solid #6b4e8f;
        margin: 0.3rem 0; font-size: 0.9rem;
    }
    .discovery-box {
        background: #fff8e1; padding: 0.8rem 1.2rem;
        color: #4e342e;  /* متن تیره روی زمینه‌ی روشن */
        border-radius: 10px; border-right: 3px solid #f57c00;
        margin: 0.3rem 0;
    }
    .metric-row {
        display: flex; gap: 1rem; justify-content: center;
    }
    /* راست‌چینی متن فارسی — جدول‌ها و نمودارها LTR می‌مانند */
    div[data-testid="stMarkdownContainer"] {
        direction: rtl; text-align: right;
    }
    div[data-testid="stMarkdownContainer"] pre,
    div[data-testid="stMarkdownContainer"] code {
        direction: ltr; text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# Session state
# ════════════════════════════════════════════════════════════════════════
if "loop_active" not in st.session_state:
    st.session_state.loop_active = False
    st.session_state.results = []
    st.session_state.chat = []
    st.session_state.pending_question = None

# ════════════════════════════════════════════════════════════════════════
# Header
# ════════════════════════════════════════════════════════════════════════
from dotenv import load_dotenv
load_dotenv(override=True)
from config.settings import setup_logging
setup_logging()
from llm.router import get_router
_router = get_router()
_s = _router.status

head_l, head_r = st.columns([4, 1])
with head_l:
    st.markdown(f"### 🌌 ایده‌یاب شخصی")
    status_badge = "🟢 زنده" if _s["mode"] == "live" else "🟡 Mock"
    st.caption(f"{status_badge} · Fugu: {_s['fugu']} · GLM: {_s['glm']} · "
               f"🖥️ Local: {_s.get('ollama', 'offline')}")
with head_r:
    if st.button("🔄 ریست", help="پاک‌کردن وضعیت جلسه و cache و شروع تازه — "
                                 "داده‌های ذخیره‌شده (الگوها، ریتم‌ها، یادداشت‌ها) حفظ می‌شوند"):
        # فقط state گذرای UI و cacheهای داده‌ای پاک می‌شوند؛ DB/vault دست‌نخورده می‌مانند.
        _bg_runner = st.session_state.get("bg_loop_runner")   # B8: threadِ پس‌زمینه یتیم نماند
        if _bg_runner is not None:
            _bg_runner.stop(timeout=0.5)
        for _k in list(st.session_state.keys()):
            del st.session_state[_k]
        try:
            st.cache_data.clear()   # گراف vault، self-map و … دوباره تازه خوانده می‌شوند
        except Exception:
            pass
        st.toast("♻️ ریست شد — شروع تازه", icon="✅")
        st.rerun()

st.divider()


# ════════════════════════════════════════════════════════════════════════
#  Tabs
# ════════════════════════════════════════════════════════════════════════

tab_dash, tab_loop, tab_graph, tab_meta, tab_lab, tab_research, tab_cp = st.tabs(
    ["🛰️ داشبورد", "🔄 لوپ پژوهش", "🕸️ گراف دانش", "🧠 خودآگاهی", "🔬 آزمایشگاه", "📚 پژوهش",
     "🎛️ Control Plane"])


# ════════════════════════════════════════════════════════════════════════
#  Tab 0: Automation Dashboard — پنلِ کنترلِ اتوماسیون (پیش‌فرض)
# ════════════════════════════════════════════════════════════════════════

with tab_dash:
    from ui.tab_dashboard import render_dashboard
    render_dashboard()


# ════════════════════════════════════════════════════════════════════════
#  Tab 1: AutoLoop — کشف خودکار الگوها
# ════════════════════════════════════════════════════════════════════════

with tab_loop:

    col_run, col_count = st.columns([3, 1])

    with col_count:
        max_loops = st.number_input("تعداد لوپ", 1, 50, 5)

    with col_run:
        if not st.session_state.loop_active:
            if st.button("🚀 شروع لوپ خودکار", type="primary"):
                st.session_state.loop_active = True
                st.session_state.results = []
                st.rerun()
        else:
            running_col, stop_col = st.columns([2, 1])
            with running_col:
                st.markdown("#### 🔄 در حال پژوهش...<span class='pulse-dot' style='background:#4caf50'></span>",
                            unsafe_allow_html=True)
            with stop_col:
                if st.button("⏹️ توقف"):
                    st.session_state.loop_active = False
                    st.rerun()

    # ── Run the loop ────────────────────────────────────────────────
    # B8 (فلگ خاموش به‌طورِ پیش‌فرض): با LOOP_BG_THREAD=1 گام‌ها به‌جای مسیرِ
    # render در threadِ پس‌زمینه اجرا می‌شوند (brain/bg_loop.py) و اینجا فقط
    # poll می‌کنیم. قانونِ ایمنی: threadِ پس‌زمینه هرگز به st.session_state یا
    # هیچ APIِ Streamlit دست نمی‌زند — همهٔ تغییرهای session در همین render است.
    _bg_mode = os.getenv("LOOP_BG_THREAD", "0") == "1"

    if _bg_mode and st.session_state.loop_active:
        from brain.bg_loop import BackgroundLoopRunner

        runner = st.session_state.get("bg_loop_runner")
        if runner is None:
            from brain.autoloop import AutoLoopEngine, AutoLoopConfig
            _cfg = AutoLoopConfig(max_iterations=max_loops,
                                  pause_on_novelty=1.01, auto_save=True)
            _engine = AutoLoopEngine(_cfg)  # history داخلِ خودِ engine می‌ماند
            runner = BackgroundLoopRunner(_engine.run_step,
                                          max_iterations=max_loops)
            st.session_state.bg_loop_runner = runner
            st.session_state.bg_loop_error = None
            runner.start()

        _finished = not runner.is_running  # پیش از poll — تا آیتمِ لحظهٔ پایان گم نشود
        for result in runner.poll(max_items=max_loops):
            st.session_state.results.append(result)
            if result.needs_user:
                st.session_state.pending_question = result
                st.session_state.loop_active = False
                break

        if runner.error is not None:
            st.session_state.bg_loop_error = (
                f"لوپ پس‌زمینه با خطا متوقف شد — "
                f"{type(runner.error).__name__}: {runner.error}")

        if (_finished or runner.error is not None
                or not st.session_state.loop_active
                or len(st.session_state.results) >= max_loops):
            runner.stop(timeout=0.5)
            st.session_state.bg_loop_runner = None
            st.session_state.loop_active = False
            st.rerun()
        else:
            with st.spinner(f"🔄 پس‌زمینه: {len(st.session_state.results)}/{max_loops} "
                            f"گام آماده — UI آزاد می‌ماند"):
                time.sleep(1.0)
            st.rerun()

    elif _bg_mode and st.session_state.get("bg_loop_runner") is not None:
        # لوپ خاموش شد (⏹️ توقف) ولی runner هنوز هست — توقفِ همیارانه و پاک‌سازی
        st.session_state.bg_loop_runner.stop(timeout=0.5)
        st.session_state.bg_loop_runner = None

    if st.session_state.get("bg_loop_error"):
        st.error("⛔ " + st.session_state.bg_loop_error)

    if (not _bg_mode) and st.session_state.loop_active and len(st.session_state.results) < max_loops:
        from brain.autoloop import AutoLoopEngine, AutoLoopConfig

        config = AutoLoopConfig(max_iterations=max_loops, pause_on_novelty=1.01, auto_save=True)
        engine = AutoLoopEngine(config)

        current_iter = len(st.session_state.results)
        with st.spinner(f"🔄 لوپ {current_iter + 1}/{max_loops} — تولید داده، تحلیل و ثبت کشف..."):
            result = engine.run_step(current_iter, past_results=st.session_state.results)
        st.session_state.results.append(result)

        if result.needs_user:
            st.session_state.pending_question = result
            st.session_state.loop_active = False

        if len(st.session_state.results) >= max_loops:
            st.session_state.loop_active = False

        st.rerun()

    # ── Pending user question ───────────────────────────────────────
    if st.session_state.pending_question:
        r = st.session_state.pending_question
        st.divider()
        st.markdown(f'<div class="discovery-box">{r.user_question}</div>',
                    unsafe_allow_html=True)
        st.markdown(f"**تحلیل:** {r.insight[:300]}")

        uc1, uc2 = st.columns(2)
        with uc1:
            if st.button("✅ تایید و ذخیره", type="primary"):
                # B2: مسیرِ واحدِ ذخیره — همان مسیرِ موتور (dedup + tags +
                # temporal_mi یک‌جا). قبلاً یک کپیِ واگرا اینجا بود: تگِ متفاوت،
                # بدونِ dedup، بدونِ ریتم/یادداشت. (سری‌ی خام در LoopResult
                # نگه‌داری نمی‌شود، پس ریتم/یادداشتِ vault اینجا ساخته نمی‌شود.)
                from brain.autoloop import AutoLoopEngine
                pid = AutoLoopEngine()._save_pattern(
                    r.scores, "تأییدِ دستی: " + r.insight[:280])
                if pid is not None:
                    st.success(f"ذخیره شد! (#{pid})")
                else:
                    st.info("تکراری بود — الگوی مشابه قبلاً ذخیره شده.")
                st.session_state.pending_question = None
                st.rerun()
        with uc2:
            if st.button("❌ رد"):
                st.session_state.pending_question = None
                st.rerun()

    # ── Show past results ───────────────────────────────────────────
    if st.session_state.results and not st.session_state.loop_active:
        st.divider()
        st.markdown("### 📋 نتایج")

        total = len(st.session_state.results)
        discoveries = sum(1 for r in st.session_state.results if r.saved)
        avg_mi = np.mean([r.scores.get("temporal_mi", 0) for r in st.session_state.results])

        m1, m2, m3 = st.columns(3)
        m1.metric("لوپ‌ها", total)
        m2.metric("کشف‌ها", discoveries)
        m3.metric("میانگین MI", f"{avg_mi:.4f}")

        rows = []
        for r in st.session_state.results:
            rows.append({
                "#": r.iteration,
                "منبع": r.source[:25],
                "MI": f"{r.scores.get('temporal_mi', 0):.4f}",
                "ρ": f"{r.scores.get('rho_hat', 0):.3f}",
                "تشخیص": "✅" if r.scores.get("detectable") else "❌",
                "novelty": f"{r.novelty:.2f}",
                "ذخیره": "💾" if r.saved else "",
            })
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    # ── Interactive Lab (compact) ───────────────────────────────────
    st.divider()
    with st.expander("🔬 آزمایش دستی + گفت‌وگو", expanded=False):

        lc1, lc2 = st.columns([1, 1])

        with lc1:
            st.markdown("**پارامترها:**")
            # key نباید lab_* باشد — تب آزمایشگاه از آن نام‌ها به‌عنوان state داخلی استفاده می‌کند
            rho = st.slider("ρ", 0.0, 0.95, 0.5, 0.05, key="quick_rho")
            lam = st.slider("λ", 0.0, 2.0, 0.5, 0.05, key="quick_lam")

            from core.model import solve_from_stds
            from core.scores import compute_scores_from_model
            sol = solve_from_stds(rho=rho, lam=lam)
            scores = compute_scores_from_model(rho=rho, lam=lam)

            st.metric("Δ_self", f"{sol.Delta_self:.4f}")
            st.metric("E_shadow", f"{max(sol.E_shadow, 0):.4f}")
            st.metric("PCAI", f"{scores.pcai:.3f}")

            if st.button("🧠 تحلیل", key="lab_analyze"):
                with st.spinner("Fugu..."):
                    resp = _router.ask(
                        f"ρ={rho}, λ={lam}, Δ={sol.Delta_self:.4f}, E={sol.E_shadow:.4f}. تحلیل کوتاه.",
                        task="analysis"
                    )
                    st.info(resp)

        with lc2:
            st.markdown("**گفت‌وگو:**")
            for msg in st.session_state.chat[-4:]:
                st.markdown(f"**{msg['role']}:** {msg['content'][:100]}")

            q = st.text_input("سؤال...", key="chat_q")
            # مقدار text_input بین rerunها باقی می‌ماند — بدون این گارد،
            # هر rerun همان سؤال را دوباره به LLM می‌فرستد (لوپ بی‌نهایت).
            if q and q != st.session_state.get("chat_last_q", ""):
                st.session_state.chat_last_q = q
                from brain.graph import chat_with_memory
                with st.spinner("🧠 در حال پاسخ..."):
                    resp = chat_with_memory(q, history=st.session_state.chat)
                st.session_state.chat.append({"role": "user", "content": q})
                st.session_state.chat.append({"role": "assistant", "content": resp})
                # جلوگیری از رشد بی‌نهایت حافظه‌ی session
                st.session_state.chat = st.session_state.chat[-100:]
                st.rerun()


# ════════════════════════════════════════════════════════════════════════
#  Tab 2: Knowledge Graph — گراف Obsidian + معادلات + ریتم‌ها
# ════════════════════════════════════════════════════════════════════════

with tab_graph:
    if st.session_state.loop_active:
        # حین لوپ، هر iteration یک rerun کامل است — رندر سنگین گراف را نگه می‌داریم
        st.info("⏸️ لوپ پژوهش در حال اجراست — گراف بعد از پایان لوپ به‌روز نمایش داده می‌شود.")
    else:
        from ui.tab_graph import render_graph_tab
        render_graph_tab()


# ════════════════════════════════════════════════════════════════════════
#  Tab 3: Self-Awareness — تحقیق و رشدِ سیستم
# ════════════════════════════════════════════════════════════════════════

with tab_meta:
    if st.session_state.loop_active:
        st.info("⏸️ لوپ پژوهش در حال اجراست — این تب بعد از پایان لوپ فعال می‌شود.")
    else:
        from ui.tab_meta import render_meta_tab
        render_meta_tab()


# ════════════════════════════════════════════════════════════════════════
#  Tab 4: Laboratory — آزمایشگاه تعاملی SOG
# ════════════════════════════════════════════════════════════════════════

with tab_lab:
    if st.session_state.loop_active:
        st.info("⏸️ لوپ پژوهش در حال اجراست — این تب بعد از پایان لوپ فعال می‌شود.")
    else:
        from ui.tab_laboratory import render_laboratory
        render_laboratory()


# ════════════════════════════════════════════════════════════════════════
#  Tab 5: Research — الگوها، معماری‌ها و یادداشت‌های ذخیره‌شده
# ════════════════════════════════════════════════════════════════════════

with tab_research:
    if st.session_state.loop_active:
        st.info("⏸️ لوپ پژوهش در حال اجراست — این تب بعد از پایان لوپ فعال می‌شود.")
    else:
        from ui.tab_research import render_research
        render_research()


# ════════════════════════════════════════════════════════════════════════
#  Tab 6: Control Plane — سطحِ واحدِ حاکمیت (v1: observe-only، additive)
# ════════════════════════════════════════════════════════════════════════

with tab_cp:
    try:
        from ui.tab_control_plane import render_control_plane
        render_control_plane()
    except Exception as e:
        st.error(f"⚠️ تبِ Control Plane بالا نیامد: {type(e).__name__}: {e}")
        st.caption("این تب additive است — خطای آن روی بقیه‌ی سیستم اثری ندارد.")
