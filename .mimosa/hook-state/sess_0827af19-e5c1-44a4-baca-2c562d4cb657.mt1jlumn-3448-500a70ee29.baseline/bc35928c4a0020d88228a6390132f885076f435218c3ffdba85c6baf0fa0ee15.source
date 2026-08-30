#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_vault_bridge — پلِ RAGِ fail-closed از ابسیدین به retrieval_router.

چهار ادعا که هرکدام سنجهٔ رفتاریِ خودش را دارد:
  ۱) فلگ خاموش = [] (no-op مطلق، byte-identical با قبلِ پل).
  ۲) فلگ روشن + ChromaDB = شواهدِ semantic با namespace=vault_rag برمی‌گردد.
  ۳) **fail-closed**: شواهد هرگز veto/magnitude باز نمی‌کنند — فقط narrowing.
  ۴) fail-soft: نبودِ chromadb یا DB خراب → [] + alert_throttled، نه crash.

mutation-gates (هر ادعا واقعاً باربر است):
  · حذفِ gate فلگ → تستِ ۱ قرمز.
  · باز کردنِ veto از مسیرِ vault_rag → تستِ ۳ قرمز.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("vault-bridge")

_OPS = Path(__file__).resolve().parent.parent
_VAULT_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "memory") not in sys.path:
    sys.path.insert(0, str(_OPS / "memory"))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
# 4d_system/memory — خانهٔ vectorstore.py (lazy-imported توسطِ vault_bridge)
_4D_MEMORY = _VAULT_ROOT / "4d_system" / "memory"
if str(_4D_MEMORY) not in sys.path:
    sys.path.insert(0, str(_4D_MEMORY))

import vault_bridge as vb  # noqa: E402
import retrieval_router as rr  # noqa: E402


class _Flag:
    """ctx manager: ست/پاک‌کردنِ یک env-flag با restore."""
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


class _FakeVectorStore:
    """ctx manager: تزریقِ ماژولِ vectorstore جعلی در sys.modules.

    لازم چون vault_bridge از `from vectorstore import search_vault` (lazy-bind
    به نام) استفاده می‌کند — patch رویِ attribute ِ ماژولِ واقعی دیده نمی‌شود
    چون bind قبلاً در import-time رخ داده. فقط جای‌گذاریِ ماژول در sys.modules
    قبل از فراخوانی کار می‌کند.

    دو مجموعه از نتایج پشتیبانی می‌شود: results (برای search_vault/4d_vault)
    و whole_results (برای search_vault_collection/vault_whole)."""

    def __init__(self, results=None, whole_results=None, fail=False):
        self.results = results or []
        self.whole_results = whole_results if whole_results is not None else results
        self.fail = fail
        self.calls = 0

    def __enter__(self):
        import types as _types
        self.calls = 0
        _fake = _types.ModuleType("vectorstore")
        _outer = self

        def _search(query, k=3):
            _outer.calls += 1
            if _outer.fail:
                raise RuntimeError("simulated chromadb failure")
            return list(_outer.results)

        def _search_collection(query, k=3, collection_name="vault_whole"):
            _outer.calls += 1
            if _outer.fail:
                raise RuntimeError("simulated chromadb failure")
            return list(_outer.whole_results)
        _fake.search_vault = _search
        _fake.search_vault_collection = _search_collection
        self._orig = sys.modules.get("vectorstore")
        sys.modules["vectorstore"] = _fake
        return self

    def __exit__(self, *exc):
        if self._orig is not None:
            sys.modules["vectorstore"] = self._orig
        else:
            sys.modules.pop("vectorstore", None)


# یک search_vault جعلی برای تستِ مسیرِ روشن (بدونِ لمسِ ChromaDB واقعی)
_FAKE_EVIDENCE = [
    {"source": "07-Knowledge/math.md", "title": "BCM Law",
     "content": "phi = y*(y-theta); dw = eta*phi - beta*w", "relevance": 0.87},
    {"source": "04-Arch/spec.md", "title": "Hebbian",
     "content": "strength += 0.1 per co-occurrence", "relevance": 0.71},
]


# ════════════════════════════════════════════════════════════════════════════════
# (۱) فلگ خاموش = [] (no-op مطلق)
# ════════════════════════════════════════════════════════════════════════════════
def t_flag_off_returns_empty():
    """فلگ خاموش → صفر شاهد + **صفر تماس با ChromaDB** (نه فقط خروجیِ خالی).

    سنجه‌ی باربر: یک ماژولِ جعلی در sys.modules می‌گذاریم که شمارشِ تماس‌ها
    را می‌دهد. فلگ خاموش یعنی search_vault **هرگز صدا زده نمی‌شود** — نه اینکه
    خروجیِ خالی است چون کوئری چیزی پیدا نکرده. درسِ §۱ منشور: «فلگ خاموش =
    صفر تماس با DB، نه فقط خروجیِ خالی»."""
    with _FakeVectorStore(results=_FAKE_EVIDENCE) as fvs:
        with _Flag(vb.FLAG, None):
            out = vb.search_vault_evidence("BCM equation")
    assert out == [], f"فلگ خاموش باید [] بدهد نه {out}"
    assert fvs.calls == 0, f"فلگ خاموش ولی ChromaDB لمس شد ({fvs.calls} بار)"


def t_flag_off_empty_goalkey():
    """فلگ روشن ولی goal_key خالی → [] (no query)."""
    with _Flag(vb.FLAG, "1"):
        assert vb.search_vault_evidence("") == []
        assert vb.search_vault_evidence("   ") == []


# ════════════════════════════════════════════════════════════════════════════════
# (۲) فلگ روشن + ChromaDB = شواهدِ semantic با namespace=vault_rag
# ════════════════════════════════════════════════════════════════════════════════
def t_flag_on_returns_evidence_with_namespace(monkeypatch_search=None):
    """فلگ روشن + search_vault موفق → شواهد با namespace=vault_rag، فقط‌خواندنی."""
    with _FakeVectorStore(results=_FAKE_EVIDENCE) as fvs:
        with _Flag(vb.FLAG, "1"):
            out = vb.search_vault_evidence("BCM equation", k=2)
    assert fvs.calls >= 1, f"حداقل یک بار search_vault باید صدا زده شود: {fvs.calls}"
    assert len(out) == 2, out
    assert out[0]["namespace"] == "vault_rag", out[0]
    assert out[0]["memory_id"].startswith("vault:"), out[0]
    assert 0.0 <= out[0]["relevance"] <= 1.0, out[0]
    # snippet کران‌دار است (نه متنِ خامِ کامل)
    assert len(out[0]["snippet"]) <= 160, out[0]


def t_relevance_clamped():
    """relevance خارجِ [0,1] → clamp می‌شود (هیچ مقدارِ غیرمجاز نشت نمی‌کند)."""
    with _FakeVectorStore(results=[
        {"source": "x", "title": "t", "content": "c", "relevance": 1.5},
        {"source": "y", "title": "t", "content": "c", "relevance": -0.3}]) as fvs:
        with _Flag(vb.FLAG, "1"):
            out = vb.search_vault_evidence("q")
    assert out[0]["relevance"] == 1.0, out[0]
    assert out[1]["relevance"] == 0.0, out[1]


# ════════════════════════════════════════════════════════════════════════════════
# (۲b) دو کالکشن merge + dedup روی source، مرتب‌شده بر relevance
# ════════════════════════════════════════════════════════════════════════════════
def t_two_collections_merge_dedup():
    """دو کالکشن (4d_vault + vault_whole) query می‌شوند، dedup روی source،
    merge-sort روی relevance. vault_whole ابرمجموعه است — source‌های مشترک فقط
    یک‌بار می‌آیند (vault_whole برنده در تضاد)."""
    default_only = [
        {"source": "only-4d.md", "title": "old", "content": "c1", "relevance": 0.50}]
    whole = [
        {"source": "shared.md", "title": "from whole", "content": "c2", "relevance": 0.90},
        {"source": "only-4d.md", "title": "dup of 4d", "content": "c3", "relevance": 0.60},
        {"source": "whole-only.md", "title": "new", "content": "c4", "relevance": 0.80}]
    with _FakeVectorStore(results=default_only, whole_results=whole):
        with _Flag(vb.FLAG, "1"):
            out = vb.search_vault_evidence("test", k=5)
    # 3 منبعِ یکتا (dedup: only-4d.md یک‌بار، vault_whole برنده)
    sources = [e["source"] for e in out]
    assert len(sources) == len(set(sources)), f"dedup شکست خورد: {sources}"
    assert len(out) == 3, f"باید ۳ منبعِ یکتا باشد: {sources}"
    # مرتب‌شده بر relevance نزولی
    rels = [e["relevance"] for e in out]
    assert rels == sorted(rels, reverse=True), f"merge-sort شکست خورد: {rels}"
    # فقط-4d از vault_whole آمد (ابرمجموعه)
    only_4d = [e for e in out if e["source"] == "only-4d.md"][0]
    assert only_4d["relevance"] == 0.60, f"vault_whole باید برنده باشد: {only_4d}"


def t_truncate_to_k_after_merge():
    """merge دو کالکشن بعد از dedup، truncate به k."""
    default_evs = [{"source": f"d{i}.md", "title": "t", "content": "c", "relevance": 0.3 + i*0.01}
                   for i in range(5)]
    whole_evs = [{"source": f"w{i}.md", "title": "t", "content": "c", "relevance": 0.8 + i*0.01}
                 for i in range(5)]
    with _FakeVectorStore(results=default_evs, whole_results=whole_evs):
        with _Flag(vb.FLAG, "1"):
            out = vb.search_vault_evidence("test", k=3)
    assert len(out) == 3, f"باید به k=3 truncate شود: {len(out)}"
    # ۳ تا بالاترین relevance
    assert all(e["relevance"] >= 0.80 for e in out), [e["relevance"] for e in out]


# ════════════════════════════════════════════════════════════════════════════════
# (۳) fail-closed: شواهد هرگز veto/magnitude باز نمی‌کنند
# ════════════════════════════════════════════════════════════════════════════════
def t_evidence_never_vetoes_via_router():
    """integration: route() با شواهدِ RAG → veto همچنان False (فقط شاهد، نه حکم)."""
    import memory_store as _ms
    store = _ms.MemoryStore()
    try:
        with _FakeVectorStore(results=_FAKE_EVIDENCE):
            with _Flag(rr.FLAG, "1"), _Flag(vb.FLAG, "1"):
                out = rr.route(goal_key="BCM equation", store=store, k=2)
        # شواهدِ RAG اضافه شدند ولی veto باز نشد
        assert out["veto"] is False, "شواهدِ RAG هرگز نباید veto باز کنند (fail-closed)"
        assert out["veto_ref"] is None, out
        # ولی mode و memories_used شاهد را نشان می‌دهند
        assert "vault_rag" in out["mode"], out["mode"]
        rag_items = [m for m in out["memories_used"] if m.get("namespace") == "vault_rag"]
        assert len(rag_items) == 2, f"دو شاهد باید ضمیه شوند: {rag_items}"
    finally:
        store.close()


def test_router_flag_off_no_rag():
    """integration: retrieval_router flag خاموش → حتی با فلگِ RAG روشن، خروجی off."""
    import memory_store as _ms
    store = _ms.MemoryStore()
    try:
        with _Flag(rr.FLAG, None), _Flag(vb.FLAG, "1"):
            out = rr.route(goal_key="anything", store=store)
        assert out["mode"] == "off", out
        assert "vault_rag" not in out.get("mode", ""), out
    finally:
        store.close()


# ════════════════════════════════════════════════════════════════════════════════
# (۴) fail-soft: نبودِ chromadb یا DB خراب → []، نه crash
# ════════════════════════════════════════════════════════════════════════════════
def t_chromadb_failure_returns_empty():
    """اگر search_vault استثنا پرت کند → [] (نه crash، نه سکوت — alert_throttled)."""
    with _FakeVectorStore(fail=True):
        with _Flag(vb.FLAG, "1"):
            out = vb.search_vault_evidence("test")
    assert out == [], f"failure باید [] بدهد نه {out}"


def t_does_not_write_anything():
    """پل فقط می‌خواند — هیچ فایلِ نو نباید ساخته شود در اجرایِ آن."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        # اجرا در یک dir جداگانه — خروجیِ پل نباید هیچ فایلی بسازد
        before = set(Path(td).rglob("*"))
        with _Flag(vb.FLAG, None):
            vb.search_vault_evidence("test")
        after = set(Path(td).rglob("*"))
        assert before == after, "پل نباید چیزی بنویسد (فقط‌خواندنی)"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_vault_bridge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
