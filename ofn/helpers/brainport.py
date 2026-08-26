"""BrainPort stub — provider swappable (fugu now, deepseek later)."""
from __future__ import annotations
import os, json, urllib.request

ALLOW = {"ziman", "studio", "painting", "lab"}

class BrainPort:
    def __init__(self):
        self.provider = os.environ.get("BRAIN_PROVIDER", "fugu").strip().lower()

    def _model(self, tier: str) -> str:
        if self.provider == "deepseek":
            return "deepseek-chat" if tier != "hard" else "deepseek-reasoner"
        # fugu default
        return "fugu" if tier != "hard" else "fugu-ultra"

    def ask(self, *, business: str, pipeline: str, prompt: str, tier: str = "default") -> dict:
        b = business.strip().lower()
        if b not in ALLOW:
            return {"ok": False, "error": "business_denied", "business": b}
        model = self._model(tier)
        if self.provider == "deepseek":
            return self._openai_compat(
                base=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                key=os.environ.get("DEEPSEEK_API_KEY", ""),
                model=model, prompt=prompt, business=b, pipeline=pipeline,
            )
        return self._openai_compat(
            base=os.environ.get("SAKANA_BASE_URL", "https://api.sakana.ai/v1"),
            key=os.environ.get("SAKANA_API_KEY", "") or os.environ.get("FUGU_API_KEY", ""),
            model=model, prompt=prompt, business=b, pipeline=pipeline,
        )

    def _openai_compat(self, *, base, key, model, prompt, business, pipeline) -> dict:
        if not key:
            return {"ok": False, "error": "missing_api_key", "provider": self.provider, "model": model}
        url = base.rstrip("/") + "/chat/completions"
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": f"business={business}; pipeline={pipeline}; be concrete; no secrets."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 2000,
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return {"ok": True, "text": text, "model": model, "provider": self.provider, "usage": usage}
        except Exception as e:
            return {"ok": False, "error": type(e).__name__, "model": model, "provider": self.provider}
