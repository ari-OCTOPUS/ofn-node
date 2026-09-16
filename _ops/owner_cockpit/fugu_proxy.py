#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fugu_proxy.py — WP1: پراکسیِ محلیِ Fugu API با usage normalizer.

قرارداد (Owner-Cockpit WP1، ۲۰۲۶-۰۸-۰۸):
  · پراکسیِ HTTP روی 127.0.0.1:8787 — OpenAI-compatible (/v1/chat/completions).
  · کلید فقط از env (FUGU_API_KEY) — هرگز hardcode، هرگز در log.
  · Usage normalizer: response.usage را به فرمتِ واحد استاندارد می‌کند:
    - input_tokens, output_tokens, cached_tokens
    - orchestration_input_tokens, orchestration_output_tokens (Fugu-specific)
    - total_cost_usd (محاسبه از fugu_pricing.json)
  ·fail-closed: بدون کلید → 503 با پیامِ صریح، نه حدس.
  · پشت فلگ OCTOPUS_WIRE_FUGU_PROXY (default OFF).

منابع:
  · Sakana official: base_url=https://api.sakana.ai/v1, model=fugu-ultra-v1.1
  · Pricing: $5/1M input, $30/1M output, $0.50/1M cached (standard)
  · Orchestration tokens: separate usage fields, same rate
  · OpenAI-compatible: /v1/chat/completions + /v1/responses

CLI:
  OCTOPUS_WIRE_FUGU_PROXY=1 python -X utf8 _ops/owner_cockpit/fugu_proxy.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))

FLAG = "OCTOPUS_WIRE_FUGU_PROXY"
PORT = int(os.environ.get("OCTOPUS_FUGU_PROXY_PORT", "8787"))
UPSTREAM = os.environ.get("FUGU_UPSTREAM", "https://api.sakana.ai/v1")
PRICING_FILE = _OPS / "state" / "fugu_pricing.json"

# قیمت‌های پیش‌فرض (verified from console.sakana.ai/pricing 2026-08-08)
DEFAULT_PRICING = {
    "fugu-ultra": {
        "input_per_1m": 5.0,
        "output_per_1m": 30.0,
        "cached_input_per_1m": 0.5,
        "context_over_272k": {
            "input_per_1m": 10.0,
            "output_per_1m": 45.0,
            "cached_input_per_1m": 1.0,
        },
    },
    "verified_at": "2026-08-08",
    "source": "console.sakana.ai/pricing",
}


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


def _load_pricing() -> dict:
    """قیمت‌ها را از فایل بخوان (اگر هست) یا default برگردان."""
    try:
        if PRICING_FILE.exists():
            return json.loads(PRICING_FILE.read_text("utf-8"))
    except (OSError, ValueError):
        pass
    return DEFAULT_PRICING


def normalize_usage(usage: dict, model: str = "fugu-ultra") -> dict:
    """WP1 Usage Normalizer: response.usage را به فرمتِ واحد استاندارد کن.

    Fugu دو نوع توکن برمی‌گرداند:
    - model tokens: prompt_tokens, completion_tokens (استانداردِ OpenAI)
    - orchestration tokens: orchestration_input_tokens, orchestration_output_tokens

    خروجیِ واحد:
    - input_tokens, output_tokens, cached_tokens
    - orchestration_input_tokens, orchestration_output_tokens
    - total_tokens (مجموعِ همه)
    - total_cost_usd (محاسبه از pricing)
    """
    if not isinstance(usage, dict):
        return {"total_tokens": 0, "total_cost_usd": 0.0}

    # استانداردِ OpenAI
    input_tok = usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
    output_tok = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
    cached_tok = 0
    # cached tokens می‌تونه در دو جا باشه
    cd = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    if isinstance(cd, dict):
        cached_tok = cd.get("cached_tokens", 0) or 0

    # orchestration tokens (Fugu-specific)
    orch_in = usage.get("orchestration_input_tokens", 0) or 0
    orch_out = usage.get("orchestration_output_tokens", 0) or 0
    orch_cached = usage.get("orchestration_input_cached_tokens", 0) or 0

    total = input_tok + output_tok + orch_in + orch_out

    # محاسبهٔ هزینه
    pricing = _load_pricing()
    rates = pricing.get(model, pricing.get("fugu-ultra", {}))
    if not isinstance(rates, dict):
        rates = DEFAULT_PRICING.get("fugu-ultra", {})
    price_in = rates.get("input_per_1m", 5.0)
    price_out = rates.get("output_per_1m", 30.0)
    price_cached = rates.get("cached_input_per_1m", 0.5)

    cost = (
        (input_tok - cached_tok) / 1e6 * price_in
        + cached_tok / 1e6 * price_cached
        + output_tok / 1e6 * price_out
        + orch_in / 1e6 * price_in
        + orch_out / 1e6 * price_out
        + orch_cached / 1e6 * price_cached
    )

    return {
        "input_tokens": input_tok,
        "output_tokens": output_tok,
        "cached_tokens": cached_tok,
        "orchestration_input_tokens": orch_in,
        "orchestration_output_tokens": orch_out,
        "orchestration_cached_tokens": orch_cached,
        "total_tokens": total,
        "total_cost_usd": round(cost, 6),
    }


# ─── HTTP proxy handler ─────────────────────────────────────────────────────

class _ProxyHandler(BaseHTTPRequestHandler):
    """پراکسیِ OpenAI-compatible: /v1/chat/completions → upstream Fugu."""

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "http://web.telegram.org")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def _json(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/v1/responses"):
            self._json(404, {"error": "not_found"})
            return

        api_key = os.environ.get("FUGU_API_KEY", "")
        if not api_key:
            self._json(503, {"error": "FUGU_API_KEY not set", "reason": "fail-closed"})
            return

        # body را بخوان
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw_body.decode("utf-8"))
        except (ValueError, OSError):
            self._json(400, {"error": "bad_json"})
            return

        # به upstream بفرست
        t0 = time.time()
        try:
            url = UPSTREAM.rstrip("/") + self.path
            req = urllib.request.Request(
                url, data=raw_body, method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_body = resp.read()
                resp_data = json.loads(resp_body.decode("utf-8"))
                ms = int((time.time() - t0) * 1000)

                # usage normalize
                usage = resp_data.get("usage", {})
                normalized = normalize_usage(usage, body.get("model", "fugu-ultra"))
                resp_data["usage"] = normalized
                resp_data["_proxy"] = {"ms": ms, "upstream": UPSTREAM}

                self._json(200, resp_data)

        except urllib.error.HTTPError as e:
            ms = int((time.time() - t0) * 1000)
            err_body = {"error": str(e), "status": e.code, "ms": ms}
            self._json(e.code, err_body)
        except Exception as e:
            ms = int((time.time() - t0) * 1000)
            self._json(502, {"error": type(e).__name__, "detail": str(e)[:200], "ms": ms})

    def log_message(self, fmt, *args):
        # لاگِ سبک — بدون کلید
        sys.stderr.write(f"[fugu_proxy] {fmt % args}\n")


def main():
    if not _flag_on():
        print(f"fugu_proxy: {FLAG} خاموش است — هیچ پورتی باز نشد (خروجِ تمیز).")
        return
    if not os.environ.get("FUGU_API_KEY"):
        print("fugu_proxy: FUGU_API_KEY تنظیم نیست — خروجِ fail-closed.")
        return

    # pricing file را تضمین کن
    if not PRICING_FILE.exists():
        PRICING_FILE.parent.mkdir(parents=True, exist_ok=True)
        PRICING_FILE.write_text(json.dumps(DEFAULT_PRICING, ensure_ascii=False, indent=2), "utf-8")

    server = HTTPServer(("127.0.0.1", PORT), _ProxyHandler)
    print(f"fugu_proxy: listening on 127.0.0.1:{PORT} → {UPSTREAM}")
    print(f"  pricing: {PRICING_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nfugu_proxy: shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
