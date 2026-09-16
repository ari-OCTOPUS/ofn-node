#!/usr/bin/env python3
"""cortex_client.py — کلاینتِ HTTP به cortexِ مرکزیِ اختاپوس.

پلِ مغزِ Project-F به مغزِ مرکزی. هر LLM call به `POST {CORTEX_URL}/ask` می‌رود
(طبقِ قراردادِ _ops/cortex/cortex.py:502-526). اگر cortex پایین/آهسته/flag-off بود،
fallback به heuristic صادقانه (نه دروغ‌گویی).

قراردادِ cortex /ask:
  REQUEST:  {"task": str, "prompt": str, "max_tokens": int=300}
  RESPONSE: {"ok": bool, "tier": str, "text": str, ...}  (model_router.ask shape)

نامتغیرِ مهم: **هیچ PII/هویت/محتوا/پلتفرم به cortex نمی‌رود** (قاعده‌ی قفل‌شده‌ی #۷).
فرستنده مسئولِ scrub کردنِ prompt است؛ این کلاینت فقط transport است.

$0 آفلاین، stdlib-only (urllib، نه requests).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

from . import config


def _post_ask(task: str, prompt: str, max_tokens: int = 300,
              timeout: Optional[float] = None) -> dict:
    """POST به cortex /ask. اگر خطا داد، exception بالا می‌رود (فراخواننده fallback می‌زند).

    هرگز محتوا را log نمی‌کند. فقط metadata (task, ok, tier, ms).
    """
    if not config.flag(config.WIRE_CORTEX):
        raise RuntimeError(f"{config.WIRE_CORTEX} off — heuristic-only by design")
    url = config.CORTEX_URL.rstrip("/") + "/ask"
    body = json.dumps({
        "task": task[:40],
        "prompt": prompt[:4000],
        "max_tokens": int(max_tokens),
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"})
    t = config.CORTEX_TIMEOUT if timeout is None else float(timeout)
    with urllib.request.urlopen(req, timeout=t) as resp:
        raw = resp.read()
    out = json.loads(raw.decode("utf-8")) if raw else {}
    if not isinstance(out, dict):
        raise RuntimeError(f"cortex returned non-dict: {type(out).__name__}")
    return out


def ask(task: str, prompt: str, max_tokens: int = 300,
        timeout: Optional[float] = None) -> dict:
    """فراخوانیِ LLM از طریقِ cortex مرکزی، با fallbackِ صادقانه.

    برمی‌گرداند:
      {"ok": bool, "tier": str, "text": str, "source": "cortex"|"fallback",
       "ms": int, "reason": str (اگر fallback)}

    رفتار:
      - flag WIRE_CORTEX خاموش → فوراً fallback ("heuristic-only by design").
      - cortex online و ok=True → text بازمی‌گردد، source="cortex".
      - cortex offline/timeout/error → fallback، reason ثبت می‌شود.
      - cortex ok=False → fallback، reason از خودِ cortex.

    هیچ exception بیرون نمی‌رود — فراخواننده همیشه یک dict سالم می‌گیرد.
    """
    import time as _t
    t0 = _t.monotonic()
    try:
        out = _post_ask(task, prompt, max_tokens=max_tokens, timeout=timeout)
        ms = int((_t.monotonic() - t0) * 1000)
        if out.get("ok"):
            return {"ok": True, "tier": out.get("tier", "?"),
                    "text": str(out.get("text", "")), "source": "cortex", "ms": ms}
        # cortex گفت ok=False → دلیلش را بازگردان
        return {"ok": False, "tier": out.get("tier", "?"), "text": "",
                "source": "fallback", "ms": ms,
                "reason": f"cortex-ok-false: {out.get('reason','?')[:200]}"}
    except Exception as e:  # noqa: BLE001 — transport نباید فراخواننده را بکشد
        ms = int((_t.monotonic() - t0) * 1000)
        return {"ok": False, "tier": "none", "text": "", "source": "fallback",
                "ms": ms, "reason": f"{type(e).__name__}: {str(e)[:200]}"}


def health() -> dict:
    """پرابِ سبکِ cortex — برای /api/health. هرگز exception بیرون نمی‌رود."""
    if not config.flag(config.WIRE_CORTEX):
        return {"wired": False, "reachable": False,
                "reason": f"{config.WIRE_CORTEX}=off (heuristic-only)"}
    # یک GET به root cortex بزنیم (وجود دارد طبقِ cortex.py:491-499)
    try:
        url = config.CORTEX_URL.rstrip("/") + "/api/cortex"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            _ = resp.read()
        return {"wired": True, "reachable": True, "url": config.CORTEX_URL}
    except Exception as e:  # noqa: BLE001
        return {"wired": True, "reachable": False, "url": config.CORTEX_URL,
                "reason": f"{type(e).__name__}: {str(e)[:120]}"}
