#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_semantic_gist_dedup — گیتِ محتوایی نوت‌های سِمانتیک (2026-08-16).

شواهد: semantic_memory.jsonl = ۲۳۸ ردیف، ۲۰۸ تکرارِ دقیق (۸۷٪) — «مغزِ دوم:
2 کسب‌وکار…» ×۶۴. فیکس: gistِ نرمال‌شدهٔ تکراری در پنجرهٔ اخیر نوشته نمی‌شود
(سطحِ بدونِ تغییر = دانشِ نو نیست). حذف صفر — فقط گیتِ ورود.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("semantic-gist-dedup")
sys.path.insert(0, str(ENV["ops"] / "cortex"))
sys.path.insert(0, str(ENV["ops"]))

from cortex import consolidate as cc  # noqa: E402

TMP = Path(tempfile.mkdtemp())
SEM = TMP / "semantic_memory.jsonl"
cc.SEMANTIC = SEM


def _note(gist, sal=0.5):
    return {"ts": "2026-08-16T00:00:00", "schema": "semantic-memory.v1",
            "gist": gist, "salience": sal}


def t_norm_gist_collapses_whitespace_and_case():
    assert cc._norm_gist("  مغزِ دوم:  X ") == cc._norm_gist("مغزِ دوم: x")


def t_exact_repeat_not_rewritten():
    cc.SEMANTIC = SEM
    cc._recent_gists.cache_clear() if hasattr(cc._recent_gists, "cache_clear") else None
    SEM.write_text(json.dumps(_note("مغزِ دوم: 2 کسب‌وکار بررسی شد"),
                              ensure_ascii=False) + "\n", encoding="utf-8")
    seen = cc._recent_gists()
    key = cc._norm_gist("مغزِ دوم: 2 کسب‌وکار بررسی شد")
    assert key in seen
    assert cc._norm_gist("یادداشتِ کاملاً نو") not in seen


def t_recent_gists_missing_file_safe():
    cc.SEMANTIC = TMP / "nonexistent.jsonl"
    assert cc._recent_gists() == set()


def t_gate_in_consolidate_path_present():
    """بلوکِ گیت در سورس هست و n_dedup گزارش می‌شود (خواندنِ سورسِ زنده)."""
    live = Path(r"F:\backup\_ops\cortex\consolidate.py")
    src = live.read_text(encoding="utf-8")
    assert "_recent_gists()" in src and "n_dedup" in src
    assert "seen_gists.add(key)" in src


CHECKS = [
    ("نرمال‌سازی gist (فاصله/حالت)", t_norm_gist_collapses_whitespace_and_case),
    ("تکرارِ دقیق در پنجره دیده می‌شود", t_exact_repeat_not_rewritten),
    ("فایل غایب = ایمن", t_recent_gists_missing_file_safe),
    ("گیت در مسیر consolidate نصب است", t_gate_in_consolidate_path_present),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
