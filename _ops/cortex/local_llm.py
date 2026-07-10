#!/usr/bin/env python3
"""local_llm.py — مغزِ محلی (ollama، $0، فقط localhost).

مدلِ سبک برای کارهای ساده و روزمره (خلاصه، دسته‌بندی، فکرِ کوتاه). روی سخت‌افزارِ
مالک (Legion 5: i5 + GTX 1660Ti) — هیچ هزینه، هیچ خروجِ داده از دستگاه.

انضباط: kill-switch اول · rate-limit (پیش‌فرض ≥۱۰s بین دو call) · timeout سخت ·
fail-soft (ollama خاموش → None، هرگز کرش) · هیچ secret در prompt (فراخوان مسئول است).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_S", "90"))   # cold-load مدل تا ~۶۰s
MIN_INTERVAL_S = float(os.environ.get("OLLAMA_MIN_INTERVAL_S", "10"))
_LAST_CALL = {"ts": 0.0}


def _post(path: str, payload: dict, timeout: float,
          opener=None) -> dict | None:
    """POST سادهٔ stdlib به ollama — فقط localhost. opener تزریق‌پذیر برای تست."""
    try:
        req = urllib.request.Request(
            BASE_URL + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        open_fn = opener or urllib.request.urlopen
        with open_fn(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — مغزِ محلی اختیاری است
        return None


def available(opener=None) -> bool:
    """آیا ollama بالا و مدل حاضر است؟ (بدونِ تولید — فقط پینگِ تگ‌ها)"""
    try:
        open_fn = opener or urllib.request.urlopen
        with open_fn(BASE_URL + "/api/tags", timeout=4) as r:
            tags = json.loads(r.read().decode("utf-8"))
        names = [m.get("name", "") for m in tags.get("models", [])]
        return any(n.startswith(MODEL.split(":")[0]) for n in names)
    except Exception:  # noqa: BLE001
        return False


def ask(prompt: str, system: str = "", max_tokens: int = 256,
        opener=None, force: bool = False) -> dict | None:
    """یک پرسشِ کوتاه از مغزِ محلی. خروجی: {text, ms, model} یا None (fail-soft).
    rate-limit: پشتِ‌سرِهم صدا نزن (force فقط تست)."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    now = time.time()
    if not force and now - _LAST_CALL["ts"] < MIN_INTERVAL_S:
        return None
    _LAST_CALL["ts"] = now
    body = {
        "model": MODEL,
        "prompt": prompt,
        "system": system or "پاسخِ کوتاه، دقیق، فارسی. حداکثر سه جمله.",
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.4},
    }
    t0 = time.time()
    out = _post("/api/generate", body, TIMEOUT_S, opener=opener)
    if not out or not out.get("response"):
        return None
    return {"text": str(out["response"]).strip(),
            "ms": int((time.time() - t0) * 1000),
            "model": MODEL, "tier": "local", "cost_usd": 0.0}


if __name__ == "__main__":
    print(json.dumps({"available": available(),
                      "sample": ask("سلام! یک جمله دربارهٔ خودت بگو.", force=True)},
                     ensure_ascii=False, indent=2))
