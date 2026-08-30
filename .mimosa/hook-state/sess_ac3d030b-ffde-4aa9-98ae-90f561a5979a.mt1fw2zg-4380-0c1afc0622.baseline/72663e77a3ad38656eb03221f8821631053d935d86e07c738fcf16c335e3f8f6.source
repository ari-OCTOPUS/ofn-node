from __future__ import annotations
import json, os, urllib.request
DEFAULT_TIMEOUT = 8
class ProClient:
    def __init__(self, base_url=None, timeout=DEFAULT_TIMEOUT):
        self.base_url = (base_url or os.environ.get("LANGAR_PRO_URL") or "").rstrip("/")
        self.timeout = timeout
    def enabled(self): return bool(self.base_url)
    def _request(self, path, payload=None):
        url = self.base_url + path
        if payload is None:
            req = urllib.request.Request(url)
        else:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    def health(self):
        if not self.base_url: return {"fallback": True, "reason": "no_langar_pro_url"}
        try:
            out = self._request("/health"); out.update(fallback=False, source="langar-pro"); return out
        except Exception as e:
            return {"fallback": True, "reason": f"error: {type(e).__name__}"}
    def research(self, query, target="armin", user_id=1):
        if not self.base_url: return {"fallback": True, "reason": "no_langar_pro_url"}
        try:
            out = self._request("/research", {"user_id": user_id, "question": query, "target": target})
            if not isinstance(out, dict): return {"fallback": True, "reason": "bad_response"}
            out["fallback"] = False; out["source"] = "langar-pro"; return out
        except Exception as e:
            return {"fallback": True, "reason": f"error: {type(e).__name__}"}
