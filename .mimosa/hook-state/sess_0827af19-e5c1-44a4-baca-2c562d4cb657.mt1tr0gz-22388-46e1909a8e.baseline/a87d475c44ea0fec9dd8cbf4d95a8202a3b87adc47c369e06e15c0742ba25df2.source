# -*- coding: utf-8 -*-
"""تستِ فیکسِ جستجوی MCP ِ octopus-vault (2026-08-06 · فیکسِ rg: 2026-08-16).

باگ: `search_hybrid` برای ایجنت‌های دیگر همیشه خالی برمی‌گرداند —
(۱) rg در runtimeِ ویندوزیِ سرور پیدا نمی‌شد → fallback ِ پایتونی،
(۲) fallback کلِ رشتهٔ کوئری را substring می‌کرد (نه term-based)،
(۳) سقفِ ۳۰۰۰ فایل روی ریپوی ~۶.۴k، match های بعدی را با خروجیِ خالی می‌بلعید.

فیکسِ 2026-08-16 (فاز ۵-الف): rg از طریقِ winget روی PATH آمد ⇒ موتور عملاً
از fallback به rg سوئیچ کرد و دو رفتارِ ناسازگار پدید آمد:
(۴) کوئریِ فقط‌فاصله به‌عنوانِ الگوی خام به rg می‌رفت ⇒ hit های جعلی از
خطوطِ تورفتگی،
(۵) کوئریِ چندواژه‌ای به‌عنوانِ عبارتِ پیوسته (یک regex) جستجو می‌شد ⇒ «search rg»
خطِ `def _rg_search(` را نمی‌یافت — خلافِ قراردادِ AND-روی-واژه‌های `_match_terms`.

اجرا: PYTHONIOENCODING=utf-8 python _ops/tests/test_octopus_mcp_search.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[1] / "octopus_mcp"))
import server  # noqa: E402


_FAILS: list[str] = []


def _ok(cond: bool, msg: str) -> None:
    if not cond:
        _FAILS.append(msg)


def t_match_terms_is_and_over_words_not_full_substring() -> None:
    """قلبِ فیکس: AND روی واژه‌ها، مستقلِ ترتیب — نه substringِ کلِ رشته."""
    hay = "the alpha and the beta and gamma"
    _ok(server._match_terms(hay, ["alpha", "beta", "gamma"]), "همهٔ واژه‌ها حاضر → match")
    _ok(server._match_terms(hay, ["gamma", "alpha"]), "ترتیبِ معکوس هم باید match کند")
    _ok(not server._match_terms(hay, ["alpha", "delta"]), "واژهٔ غایب → عدمِ match")
    # همان چیزی که جهش (بازگشت به substringِ کلِ رشته) را قرمز می‌کند:
    # "gamma alpha" به‌عنوان یک رشته در hay نیست، ولی term-based باید بیابد.
    _ok(("gamma alpha" not in hay) and server._match_terms(hay, "gamma alpha".split()),
        "term-based جایی که substringِ کل شکست می‌خورد باید موفق شود")


def t_find_rg_honours_env_override() -> None:
    """`_find_rg` باید OCTOPUS_RG_PATH را قبل از هر چیز بخواند (مسیرِ موجود)."""
    prev = os.environ.get("OCTOPUS_RG_PATH")
    try:
        os.environ["OCTOPUS_RG_PATH"] = str(_HERE)  # یک فایلِ موجود (خودِ این تست)
        _ok(server._find_rg() == str(_HERE), "env override باید مسیرِ موجود را برگرداند")
        os.environ["OCTOPUS_RG_PATH"] = str(_HERE.parent / "does-not-exist-xyz.bin")
        # مسیرِ ناموجود → نباید env را برگرداند (می‌افتد رویِ which/known-paths → None اینجا)
        _ok(server._find_rg() != str(_HERE.parent / "does-not-exist-xyz.bin"),
            "مسیرِ ناموجودِ env نباید برگردانده شود")
    finally:
        if prev is None:
            os.environ.pop("OCTOPUS_RG_PATH", None)
        else:
            os.environ["OCTOPUS_RG_PATH"] = prev


def t_multiword_query_finds_a_real_file_not_empty() -> None:
    """رگرسیونِ زنده: کوئریِ چندواژه‌ایِ واقعی باید نتیجهٔ ناخالی بدهد
    (پیش از فیکس: خالی). مسیر/گلابِ باریک تا سریع بماند."""
    r = server.t_search_hybrid("agent instruction", path="_ops", glob="*.py", max_results=5)
    _ok(isinstance(r.get("content"), list), "content باید list باشد")
    # حداقل باید بدونِ خطا برگردد و ساختار درست باشد؛ ناخالی‌بودن را روی یک
    # کوئریِ قطعی (نامِ همین ماژول) می‌سنجیم:
    r2 = server.t_search_hybrid("def t_search_hybrid", path="_ops/octopus_mcp",
                                glob="*.py", max_results=5)
    _ok(len(r2["content"]) >= 1, f"باید تعریفِ خودش را بیابد؛ گرفت: {len(r2['content'])}")


def t_empty_query_is_handled() -> None:
    r = server.t_search_hybrid("   ", path=".", glob="*.md", max_results=5)
    _ok(r["content"] == [], "کوئریِ خالی → صفر hit، نه استثنا")


def t_rg_engine_empty_query_is_empty_not_spurious() -> None:
    """رگرسیونِ rg (2026-08-16): «   » دیگر الگوی خام به rg نیست — نه hit تورفتگی."""
    if server._find_rg() is None:
        print("  (skip: rg در دسترس نیست — این تست رفتارِ موتورِ rg را می‌سنجد)")
        return
    r = server.t_search_hybrid("   ", path=".", glob="*.md", max_results=5)
    _ok(r["engine"] == "rg", f"با وجودِ rg باید engine=rg باشد؛ گرفت {r['engine']}")
    _ok(r["content"] == [], "کوئریِ فقط‌فاصله با rg → صفر hit (نه خطوطِ تورفتگی)")
    _ok(r["search_error"] == "empty-query", "علامتِ empty-query مثلِ fallback")


def t_rg_engine_multiword_is_term_and_unordered() -> None:
    """رگرسیونِ rg (2026-08-16): «search rg» با ترتیبِ معکوس باید `def _rg_search(`
    را بیابد (AND روی واژه‌ها) — پیش از فیکس: صفر hit چون عبارتِ پیوسته می‌گشت."""
    if server._find_rg() is None:
        print("  (skip: rg در دسترس نیست — این تست رفتارِ موتورِ rg را می‌سنجد)")
        return
    r = server.t_search_hybrid("search rg", path="_ops/octopus_mcp", glob="*.py",
                               max_results=10)
    _ok(r["engine"] == "rg", f"با وجودِ rg باید engine=rg باشد؛ گرفت {r['engine']}")
    _ok(len(r["content"]) >= 1,
        f"ترتیبِ معکوس باید تعریفِ _rg_search را بیابد؛ گرفت {len(r['content'])}")
    for h in r["content"]:
        low = h["text"].lower()
        _ok("rg" in low and "search" in low,
            f"هر hit باید هر دو واژه را داشته باشد: {h['path']}:{h['line']}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        try:
            t()
        except Exception as exc:  # noqa: BLE001
            _FAILS.append(f"{t.__name__} raised {type(exc).__name__}: {exc}")
    if _FAILS:
        print(f"FAIL test_octopus_mcp_search: {len(_FAILS)} problem(s)")
        for f in _FAILS:
            print("  ❌", f)
        return 1
    print(f"OK test_octopus_mcp_search: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
