#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vault_bridge — پلِ RAGِ fail-closed از ابسیدین (canonical) به retrieval_router.

شکافی که می‌بندد (سندِ ۲۰ §۲.۴ / تصمیمِ مالک ۲۰۲۶-۰۸-۰۶):
  · `_ops/memory/` (FTS5، operational، decision-time) و `4d_system/memory/`
    (ChromaDB، semantic، برداری) دو ردِ کاملاً بی‌ربط بودند — هیچ پلی.
  · ابسیدین حافظهٔ canonical/اصلی است و **می‌ماند**؛ ChromaDB و FTS5 فقط index.
  · این پل ChromaDB را به‌عنوان **شاهدِ semantic** به retrieval_router می‌رساند.

قاعدهٔ سخت (fail-closed، هم‌جهت با retrieval_router):
  · **فقط شاهد/evidence** — هرگز veto، هرگز مجوز باز نمی‌کند، هرگز magnitude.
    خروجی به `memories_used` (شواهد) ضمیمه می‌شود، دقیقاً مثلِ مسیرِ
    episodic/procedural. جهت همیشه narrowing است.
  · **فقط خواندنی** — هیچ فایلی نمی‌نویسد، هیچ index را بازسازی نمی‌کند.
    ابسیدین canonical دست‌نخورده؛ ChromaDB فقط خوانده می‌شود.
  · **پشتِ فلگِ خودش** (`OCTOPUS_WIRE_VAULT_RAG`، پیش‌فرض خاموش، خارج از
    PAPER_FULL_FLAGS): نبودش = `[]` (no-op مطلق، byte-identical با امروز).
  · **fail-soft**: اگر chromadb/langchain غایب یا DB خراب بود → `[]` +
    alert_throttled (نه crash، نه سکوت).

وابستگی‌ها (همگی ازپیش‌نصب‌شده، تأییدشده ۲۰۲۶-۰۸-۰۶): chromadb 1.5.9،
langchain_chroma، sentence_transformers. lazy-import تا نبودشان ماژول را نمی‌کشد.

$0 · آفلاین · فقط‌خواندنی روی ChromaDB · صفر نوشتن.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/memory
_OPS = _HERE.parent                               # _ops
_VAULT_ROOT = _OPS.parent                         # F:\backup (canonical)
# مسیرِ ChromaDB (4d_system/memory/vectorstore.py) — برایِ lazy-import
_4D_MEMORY = _VAULT_ROOT / "4d_system" / "memory"

FLAG = "OCTOPUS_WIRE_VAULT_RAG"                   # پیش‌فرض خاموش، خارج از profile


def flag_on() -> bool:
    """env-flag با پیش‌فرض خاموش (allowlistِ truthy، هم‌راستا با retrieval_router)."""
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def search_vault_evidence(goal_key: str, k: int = 3) -> list[dict]:
    """شواهدِ semantic از ChromaDB (vault) — فقط خواندنی، فقط شاهد.

    خروجی: list[{memory_id, source, title, relevance, snippet, namespace}].
    فلگ خاموش → []. خطا → [] + alert_throttled. هرگز exception پرت نمی‌کند.
    ابسیدین canonical است؛ این تابع فقط index را می‌خواند."""
    if not flag_on():
        return []
    gk = str(goal_key or "").strip()
    if not gk:
        return []
    try:
        # lazy-import: نبودِ chromadb/langchain ماژول را نمی‌کشد (fail-soft)
        #
        # ۲۰۲۶-۰۸-۰۷ — دستِ‌نخورده ماند (نه `from memory.vectorstore import`):
        # `_ops/memory/__init__.py` خودش یک پکیجِ واقعیِ دیگر به‌نامِ `memory`
        # است (gate.py، memory_store.py، retrieval_router.py، همین فایل). این
        # پروسه (organism) هر دو را روی sys.path دارد — `import memory` این‌جا
        # می‌توانست به‌جای `4d_system/memory`، بسته به ترتیبِ importِ
        # process-wide، به `_ops/memory` resolve شود (که `vectorstore.py`
        # ندارد) → شکستِ نامعلوم‌تر. importِ لختِ زیر امن است چون «vectorstore»
        # در کلِ vault فقط همین یک فایل است؛ فیکسِ واقعی داخلِ خودِ
        # vectorstore.py است (bootstrap ِ self-path + importِ مطلق به‌جایِ
        # relative، به‌جای وابستگی به __package__).
        for _p in (str(_4D_MEMORY), str(_4D_MEMORY.parent)):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        from vectorstore import search_vault, search_vault_collection  # noqa: E402
        # ۲۰۲۶-۰۸-۰۷ (نوتِ ۲۳): هر دو کالکشن را query کن، dedup روی source،
        # merge-sort روی relevance، truncate به k. vault_whole ابرمجموعه است.
        _kq = max(1, int(k))
        _res_default = search_vault(gk, k=_kq)
        _res_whole = search_vault_collection(gk, k=_kq, collection_name="vault_whole")
        # merge + dedup روی source (vault_whole برنده در تضاد — غنی‌تر)
        _seen: set[str] = set()
        _merged: list[dict] = []
        for r in _res_whole + _res_default:
            _src = r.get("source", "")
            if _src in _seen:
                continue
            _seen.add(_src)
            _merged.append(r)
        _merged.sort(key=lambda x: float(x.get("relevance", 0.0)), reverse=True)
        results = _merged[:_kq]
    except Exception as e:  # noqa: BLE001 — غیابِ RAG هرگز decision را نمی‌بندد
        # نویزِ تکراریِ import-failure را throttle کن (alert خام هر بار سر و صدا می‌کند)
        try:
            for _bp in (str(_OPS / "budget"), str(_OPS)):
                if _bp not in sys.path:
                    sys.path.insert(0, _bp)
            import opslib  # noqa: E402
            opslib.alert_throttled(
                [f"vault_bridge: RAG در دسترس نیست ({type(e).__name__}: {e})"],
                key="vault-bridge-rag-unavailable", window_s=3600.0)
        except Exception:  # noqa: BLE001 — حتی alert شکست بخورد، بی‌صدا [] بده
            pass
        return []
    # نرمال‌سازی به شکلِ memories_used (هم‌الگو با store.as_memories_used):
    # فقط hash/ref + metadata، نه متنِ خامِ کامل — snippet کوتاهِ کران‌دار.
    out: list[dict] = []
    for i, r in enumerate(results):
        rel = float(r.get("relevance", 0.0) or 0.0)
        if not (0.0 <= rel <= 1.0):
            rel = max(0.0, min(1.0, rel))
        snippet = str(r.get("content", ""))[:160]
        out.append({
            "memory_id": f"vault:{r.get('source', f'unk{i}')}#{i}",
            "namespace": "vault_rag",
            "source": str(r.get("source", ""))[:120],
            "title": str(r.get("title", ""))[:80],
            "relevance": round(rel, 4),
            "snippet": snippet,
        })
    return out


if __name__ == "__main__":   # pragma: no cover — نمای دستیِ اپراتور
    import json
    import sys as _sys
    gk = _sys.argv[1] if len(_sys.argv) > 1 else ""
    print(json.dumps({
        "flag": FLAG, "enabled": flag_on(),
        "evidence": search_vault_evidence(gk)}, ensure_ascii=False, indent=1))
