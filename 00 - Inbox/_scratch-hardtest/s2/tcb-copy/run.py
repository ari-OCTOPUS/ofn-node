#!/usr/bin/env python3
"""
run.py — Entry point for the 4D discovery system (upgraded with LangGraph).

Usage:
    python run.py           # full self-test including intelligent brain
    streamlit run run.py    # launch the dashboard

This file serves double duty: CLI self-test and Streamlit entry point.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# روی ویندوز، stdout هنگام redirect/pipe به cp1252 برمی‌گردد و اولین print با
# ✓/✗/▶ کل self-test را با UnicodeEncodeError می‌کشد (پیش از هر آزمونی). با
# utf-8 + errors=replace خروجی هرگز به‌خاطرِ یک نویسه کرش نمی‌کند.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def cli_self_test() -> int:
    """Run a comprehensive end-to-end self-test.

    برمی‌گرداند: exit code (۰ = همه سالم، ۱ = دست‌کم یک شکست).
    قبلاً همه‌ی شکست‌های مرحله‌های ۳-۶ بلعیده می‌شد و همیشه exit 0 بود —
    یعنی CI/اسکریپت هیچ‌وقت خرابی را نمی‌دید.
    """
    failures: list[str] = []
    print("=" * 65)
    print("  4D SYSTEM — Self-test (LangGraph Intelligent Edition)")
    print("=" * 65)

    # 1) Reference dir
    from config.settings import verify_reference_dir, REFERENCE_DIR
    ok = verify_reference_dir()
    print(f"\n{'✓' if ok else '✗'} Reference dir: {REFERENCE_DIR}")
    if not ok:
        failures.append("reference_dir")

    # 2) Core model
    print("\n▶ Core model (anchors vs 4.py):")
    from core.model import run_self_test
    results = run_self_test()
    all_pass = all(err < 1e-4 for _, (_, _, err) in results.items())
    for name, (comp, exp, err) in list(results.items())[:4]:
        p = err < 1e-4
        print(f"  {'✓' if p else '✗'} {name}: {float(comp):.8f} (err={float(err):.1e})")
    if len(results) > 4:
        rest_ok = all(err < 1e-4 for _, (_, _, err) in list(results.items())[4:])
        print(f"  {'✓' if rest_ok else '✗'} ... +{len(results)-4} more anchors")

    # 3) Memory systems
    print("\n▶ Memory (SQLite):")
    from memory.store import get_stats, _ensure_db
    _ensure_db()
    stats = get_stats()
    print(f"  experiments: {stats['experiments']}, reflections: {stats['reflections']}")

    print("\n▶ Memory (Vector store / RAG):")
    try:
        from memory.vectorstore import index_vault, search_vault
        n = index_vault()
        print(f"  ✓ Indexed {n} chunks from 4D-Vault")
        result = search_vault("E_shadow", k=1)
        if result:
            print(f"  ✓ RAG search works (top hit: {result[0]['title']})")
    except Exception as e:
        print(f"  ⚠ RAG: {e}")
        failures.append(f"rag: {type(e).__name__}")

    # 4) LLM / LangChain
    print("\n▶ LLM (LangChain adapter):")
    try:
        from llm.langchain_models import get_default_chat, get_mock_chat
        mock = get_mock_chat()
        from langchain_core.messages import HumanMessage
        resp = mock.invoke([HumanMessage(content="test")])
        print(f"  ✓ Mock chat model: {resp.content[:50]}...")
    except Exception as e:
        print(f"  ⚠ {e}")
        failures.append(f"llm: {type(e).__name__}")

    # 5) Tools
    print("\n▶ Tools (5 available):")
    try:
        from brain.tools import ALL_TOOLS
        for t in ALL_TOOLS:
            print(f"  ✓ {t.name}")
    except Exception as e:
        print(f"  ⚠ {e}")
        failures.append(f"tools: {type(e).__name__}")

    # 6) Intelligent pipeline (LangGraph)
    print("\n▶ Intelligent Pipeline (LangGraph):")
    try:
        import numpy as np
        from brain.graph import run_experiment_streaming

        rng = np.random.default_rng(42)
        series = np.zeros(2000)
        for t in range(1, 2000):
            series[t] = 0.7 * series[t-1] + rng.normal(0, 0.1)

        steps = []
        for node_name, state_update in run_experiment_streaming(
            series, label="self-test AR(1)"
        ):
            steps.append(node_name)
            print(f"  ▶ {node_name}: {list(state_update.keys())}")

        if len(steps) >= 5:
            print(f"  ✓ Pipeline completed ({len(steps)} steps)")
        else:
            print(f"  ⚠ Pipeline incomplete ({len(steps)} steps)")
            failures.append(f"pipeline_incomplete: {len(steps)} steps")

    except Exception as e:
        print(f"  ⚠ Pipeline error: {e}")
        failures.append(f"pipeline: {type(e).__name__}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 65)
    if all_pass and not failures:
        print("  ✓ ALL SYSTEMS GO")
        print("  Run: streamlit run run.py")
    else:
        print("  ⚠ Some checks failed:")
        if not all_pass:
            print("    - core anchors")
        for f in failures:
            print(f"    - {f}")
    print("=" * 65)
    return 0 if (all_pass and not failures) else 1


def _is_streamlit():
    try:
        from importlib.metadata import version
        return "streamlit" in sys.modules
    except Exception:
        return False


def _run_streamlit_app():
    """اجرای UI روی هر rerun استریملیت.

    Streamlit اسکریپت اصلی را در هر rerun دوباره اجرا می‌کند، ولی پایتون ماژول‌ها
    را cache می‌کند؛ بدون reload، بدنه‌ی ui.app از اجرای دوم به بعد اجرا نمی‌شود و
    هیچ عنصری رندر نمی‌شود (صفحه‌ی سفید). پس ui.app را در هر rerun دوباره اجرا می‌کنیم.

    اگر API یک وابستگی (مثلاً افزودن یک نام جدید به config.settings) وسط همان session
    عوض شده باشد، import با ماژولِ cache‌شده‌ی قدیمی شکست می‌خورد. در آن حالت یک‌بار
    ماژول‌های خودِ پروژه را از sys.modules پاک و rerun می‌کنیم تا session بدون restart
    ترمیم شود (rerun عناصرِ نیمه‌رندرشده را دور می‌ریزد؛ پس set_page_config دوبار صدا
    نمی‌شود).
    """
    import importlib
    try:
        if "ui.app" in sys.modules:
            importlib.reload(sys.modules["ui.app"])
        else:
            import ui.app  # noqa: F401
    except Exception:
        import streamlit as st
        if st.session_state.get("_self_heal_tried"):
            raise  # قبلاً ترمیم شده ولی هنوز خطاست ⇒ خطای واقعی است
        st.session_state["_self_heal_tried"] = True
        _project_pkgs = {"ui", "brain", "data", "memory", "llm",
                         "agents", "config", "knowledge", "core"}
        for _name in [n for n in list(sys.modules)
                      if n.split(".")[0] in _project_pkgs]:
            del sys.modules[_name]
        st.rerun()
    else:
        import streamlit as st
        st.session_state["_self_heal_tried"] = False


if __name__ == "__main__":
    if _is_streamlit():
        _run_streamlit_app()
    else:
        sys.exit(cli_self_test())
