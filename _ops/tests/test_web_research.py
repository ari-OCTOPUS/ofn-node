"""test_web_research.py — لایهٔ فراشناختیِ تحقیقِ وبِ رایگان ($0، جلسه ۴۶).

با opener تزریقی (بدونِ شبکهٔ واقعی): parseِ DDG/Wikipedia/arXiv، sanitize، persist،
گیتِ پرچم، و صفر-دلاری. هیچ egressِ واقعی در تست.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("web-research")

import web_research as wr   # noqa: E402

_DDG_HTML = ('<a class="result__a" href="https://ex.com/a">Neural Nets Explained</a>'
             '<a class="result__snippet">a short snippet about nets</a>')
_WIKI_OS = json.dumps(["q", ["Neural network"], [""], ["https://en.wikipedia.org/wiki/Neural_network"]])
_WIKI_SUM = json.dumps({"title": "Neural network", "extract": "A neural network is a model.",
                        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Neural_network"}}})
_ARXIV = ("<feed><entry><title>Deep Nets</title><summary>we study deep nets</summary>"
          "<id>http://arxiv.org/abs/1234.5678</id></entry></feed>")


def _fake_opener(url: str) -> str:
    if "duckduckgo" in url:
        return _DDG_HTML
    if "opensearch" in url:
        return _WIKI_OS
    if "rest_v1/page/summary" in url:
        return _WIKI_SUM
    if "arxiv" in url:
        return _ARXIV
    return ""


def t_a_search_parses_all_three_sources():
    hits = wr.search("neural networks", k=4, opener=_fake_opener)
    srcs = {h["source"] for h in hits}
    assert {"duckduckgo", "wikipedia", "arxiv"} <= srcs, srcs
    ddg = [h for h in hits if h["source"] == "duckduckgo"][0]
    assert ddg["title"] == "Neural Nets Explained" and ddg["url"].startswith("https://")
    wk = [h for h in hits if h["source"] == "wikipedia"][0]
    assert "neural network is a model" in wk["snippet"].lower()


def t_b_each_source_failsoft():
    def boom(url):
        raise RuntimeError("network down")
    assert wr.search("x", opener=boom) == []   # همه fail → خالی، نه crash


def t_c_run_and_persist_gated_by_flag():
    os.environ.pop(wr.FLAG_ENV, None)
    r = wr.run_and_persist(["topic a"], opener=_fake_opener)
    assert r["ok"] is False and "خاموش" in r["skipped"]   # پرچم خاموش → هیچ egress
    os.environ[wr.FLAG_ENV] = "1"
    try:
        r2 = wr.run_and_persist(["neural networks", "reinforcement learning"],
                                opener=_fake_opener)
        assert r2["ok"] is True and r2["n_topics"] == 2 and r2["n_hits"] > 0
        disk = json.loads(wr.RESEARCH_PATH.read_text("utf-8"))
        assert disk["schema"] == "research-latest.v1" and disk["cost_aud"] == 0
    finally:
        os.environ.pop(wr.FLAG_ENV, None)


def t_d_zero_dollar_no_money_import():
    """web_research نباید هیچ مسیرِ پول import/فراخوانی کند (صفر دلار ساختاری).
    اشارهٔ داکِ‌استرینگ مجاز است؛ فقط importِ واقعی/فراخوانی ممنوع."""
    src = (_HERE.parent / "cortex" / "web_research.py").read_text("utf-8")
    lines = [ln for ln in src.splitlines()
             if ln.strip().startswith(("import ", "from ")) or ".reserve(" in ln
             or ".settle(" in ln or "os.environ.get(\"FUGU" in ln]
    joined = "\n".join(lines)
    for banned in ("organ_gate", "budget_gate", "money_gate", "model_router",
                   "API_KEY", "api_key", ".reserve(", ".settle("):
        assert banned not in joined, f"web_research نباید {banned} را import/فراخوانی کند"


def t_e_default_opener_rejects_non_http():
    try:
        wr._default_opener("file:///etc/passwd")
        assert False, "باید ValueError بدهد"
    except ValueError:
        pass


def t_f_work_pump_wires_web_research():
    """work_pump یک executorِ $0 برای web_research دارد (paid=False)."""
    sys.path.insert(0, str(_HERE.parent / "heart"))
    import work_pump as wp
    assert "web_research" in wp._EXECUTORS
    tpl = [t for t in wp.DEFAULT_PLAN["templates"] if t["kind"] == "web_research"]
    assert tpl and tpl[0]["paid"] is False


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_web_research: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
