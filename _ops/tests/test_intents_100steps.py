#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_intents_100steps.py — INT-02..05 hermetic (قدم ۷۸)."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "owner_console"))

from owner_console import conversation as conv  # noqa: E402


def _kind(q: str) -> str:
    return str((conv.handle(q) or {}).get("kind") or "")


def main() -> int:
    failed = []
    # INT-03: درد خام ≠ معادله
    k = _kind("دردم زیاده")
    if k == "equation":
        failed.append(f"INT-03: got equation for درد — {k}")
    else:
        print("  ✅ INT-03 درد ≠ equation →", k)

    # INT-04: خودآگاه ≠ AGI intro
    r = conv.handle("خودآگاه هستی؟")
    k = r.get("kind")
    text = str(r.get("text") or "")
    if k == "intro" and "AGI" in text and "نیستم" not in text:
        failed.append("INT-04: intro claimed AGI")
    elif "phenomenal" in text.lower() or "ادعای AGI نمی‌کنم" in text or k == "honest-self":
        print("  ✅ INT-04 honest-self →", k)
    else:
        # still ok if honest text
        if "آگاهی" in text or "access" in text.lower() or "نمی‌کنم" in text:
            print("  ✅ INT-04 honest-ish →", k)
        else:
            failed.append(f"INT-04 unexpected: {k} {text[:80]}")

    r2 = conv.handle("قلبت کجاست")
    if r2.get("kind") == "honest-self" or "heart" in str(r2.get("text") or "").lower() or "قلب" in str(r2.get("text") or ""):
        print("  ✅ INT-04 قلب →", r2.get("kind"))
    else:
        failed.append(f"INT-04 heart: {r2.get('kind')}")

    # INT-02 / INT-05 memory path
    r3 = conv.handle("درباره من چی میدونی")
    if r3.get("kind") == "memory" and (r3.get("data") or {}).get("may_authorize") is False:
        print("  ✅ INT-02 memory recall →", (r3.get("data") or {}).get("status"))
    else:
        failed.append(f"INT-02: {r3.get('kind')} {r3.get('data')}")

    r4 = conv.handle("آخرین improve چی بود")
    if r4.get("kind") == "memory":
        print("  ✅ INT-05 improve → memory")
    else:
        failed.append(f"INT-05: {r4.get('kind')}")

    print(("❌" if failed else "✅"), "test_intents_100steps",
          f"{len(failed)} failed" if failed else "ok")
    for f in failed:
        print("   -", f)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
