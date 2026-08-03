"""
pro_client.py — پلِ بینِ باتِ تلگرام (langar) و بک‌اندِ پژوهش (langar-pro).

Bridge between the Telegram bot and the langar-pro research backend.
فقط کتابخانه‌ی استاندارد (urllib + json + os). هیچ وابستگیِ بیرونی.

قرارداد (contract):
  • اگر LANGAR_PRO_URL ست نشده باشد → {"fallback": True, "reason": "no_langar_pro_url"}
  • اگر سرور در دسترس نباشد/خطا → {"fallback": True, "reason": "..."} (بدونِ crash)
  • اگر موفق → پاسخِ pro + {"fallback": False, "source": "langar-pro"}
بات با دیدنِ fallback=True خودکار به researcherِ محلیِ خودش برمی‌گردد.
"""

from __future__ import annotations

import json
import os
import urllib.request

DEFAULT_TIMEOUT = 8  # ثانیه


class ProClient:
    def __init__(self, base_url: str | None = None, timeout: int = DEFAULT_TIMEOUT):
        # اگر base_url داده نشود، از محیط خوانده می‌شود
        self.base_url = (base_url or os.environ.get("LANGAR_PRO_URL") or "").rstrip("/")
        self.timeout = timeout

    def enabled(self) -> bool:
        return bool(self.base_url)

    def _request(self, path: str, payload: dict | None = None):
        url = self.base_url + path
        if payload is None:
            req = urllib.request.Request(url)  # GET
        else:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"})  # POST
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))

    def health(self) -> dict:
        if not self.base_url:
            return {"fallback": True, "reason": "no_langar_pro_url"}
        try:
            out = self._request("/health")
            out.update(fallback=False, source="langar-pro")
            return out
        except Exception as e:
            return {"fallback": True, "reason": f"error: {type(e).__name__}"}

    def research(self, query: str, target: str = "armin", user_id: int = 1) -> dict:
        if not self.base_url:
            return {"fallback": True, "reason": "no_langar_pro_url"}
        try:
            out = self._request("/research",
                                {"user_id": user_id, "question": query, "target": target})
            if not isinstance(out, dict):
                return {"fallback": True, "reason": "bad_response"}
            out["fallback"] = False
            out["source"] = "langar-pro"
            return out
        except Exception as e:
            return {"fallback": True, "reason": f"error: {type(e).__name__}"}
