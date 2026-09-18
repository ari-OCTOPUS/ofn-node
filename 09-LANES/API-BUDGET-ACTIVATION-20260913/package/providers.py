"""providers.py — explicit multi-provider registry for the OCTOPUS credential broker.

Contract of this module
-----------------------
* Credential values live only inside this process.  No public function returns a
  key.  `_key()` and `_spec()` are internal: `_spec()` intentionally carries the
  credential so the broker can hand it to a child over **stdin** (never argv,
  never a log, never a receipt).
* Provider -> environment-variable mapping is **explicit**.  There is no
  first-match scan over env files (that was the F-2 defect: a stale key sitting
  above a fresh one silently wins).
* Authoritative secret surface: /home/ari/.config/ofn/external-models.env (mode 600).
  The legacy file is consulted only for providers that have no explicit variable
  there, and only for the single-provider sakana path.
* `OCTOPUS_API_RAW_KEYS_VISIBLE_TO_AGENTS=false` is enforced: every public
  accessor here returns booleans, model names, URLs or counts — never a value.
"""

from __future__ import annotations

import json
import pathlib
import time
import urllib.error
import urllib.request

EXTERNAL_ENV = pathlib.Path("/home/ari/.config/ofn/external-models.env")
LEGACY_ENV = pathlib.Path("/home/ari/.config/ofn/secrets.env")
DISCOVERY = pathlib.Path("/home/ari/ofn/state/api-budget/config/discovered-models.json")

BEARER = "bearer"
ANTHROPIC = "anthropic"
GOOGLE = "google"

_PROVIDER_ORDER = ("local-llamacpp-180", "sakana-fugu", "deepseek",
                   "openai", "anthropic", "gemini")

REGISTRY: dict = {
    "local-llamacpp-180": dict(
        kind="local", paid=False,
        enabled_var="LOCAL_LLAMACPP_ENABLED", key_var=None, auth=None,
        base_var="LOCAL_LLAMACPP_BASE_URL",
        chat_url_var=None, chat_suffix="/completion",
        models_url_var=None, health_path_var="LOCAL_LLAMACPP_HEALTH_PATH",
        model_vars={"local": "LOCAL_LLAMACPP_MODEL"},
        role="local-first"),
    "sakana-fugu": dict(
        kind="paid", paid=True,
        enabled_var="SAKANA_PROVIDER_ENABLED", key_var="SAKANA_API_KEY", auth=BEARER,
        chat_url_var="SAKANA_CHAT_URL", models_url_var="SAKANA_MODELS_URL",
        model_vars={"standard": "SAKANA_MODEL_STANDARD",
                    "strong": "SAKANA_MODEL_STRONG"},
        role="standard"),
    "deepseek": dict(
        kind="paid", paid=True,
        enabled_var="DEEPSEEK_PROVIDER_ENABLED", key_var="DEEPSEEK_API_KEY", auth=BEARER,
        chat_url_var="DEEPSEEK_CHAT_URL", models_url_var="DEEPSEEK_MODELS_URL",
        model_vars={"standard": "DEEPSEEK_MODEL_STANDARD",
                    "reasoning": "DEEPSEEK_MODEL_REASONING"},
        role="economy"),
    "openai": dict(
        kind="paid", paid=True,
        enabled_var="OPENAI_PROVIDER_ENABLED", key_var="OPENAI_API_KEY", auth=BEARER,
        max_tokens_field="max_completion_tokens", omit_temperature=True,
        chat_url_var="OPENAI_CHAT_URL", models_url_var="OPENAI_MODELS_URL",
        model_vars={"economy": "OPENAI_MODEL_ECONOMY",
                    "standard": "OPENAI_MODEL_STANDARD",
                    "strong": "OPENAI_MODEL_STRONG",
                    "frontier": "OPENAI_MODEL_FRONTIER"},
        role="standard"),
    "anthropic": dict(
        kind="paid", paid=True,
        enabled_var="ANTHROPIC_PROVIDER_ENABLED", key_var="ANTHROPIC_API_KEY",
        auth=ANTHROPIC, version_var="ANTHROPIC_VERSION",
        chat_url_var="ANTHROPIC_MESSAGES_URL", models_url_var="ANTHROPIC_MODELS_URL",
        model_vars={"economy": "ANTHROPIC_MODEL_ECONOMY",
                    "standard": "ANTHROPIC_MODEL_STANDARD",
                    "strong": "ANTHROPIC_MODEL_STRONG",
                    "frontier": "ANTHROPIC_MODEL_FRONTIER"},
        role="strong-review"),
    "gemini": dict(
        kind="paid", paid=True,
        enabled_var="GEMINI_PROVIDER_ENABLED", key_var="GEMINI_API_KEY", auth=GOOGLE,
        base_var="GEMINI_BASE_URL", chat_url_var=None, chat_suffix="/models/{model}:generateContent",
        models_url_var="GEMINI_MODELS_URL",
        model_vars={"economy": "GEMINI_MODEL_ECONOMY",
                    "standard": "GEMINI_MODEL_STANDARD",
                    "strong": "GEMINI_MODEL_STRONG",
                    "frontier": "GEMINI_MODEL_FRONTIER",
                    "reasoning": "GEMINI_MODEL_STABLE_REASONING"},
        role="standard"),
}

_CACHE: dict | None = None
_CACHE_AT: float = 0.0
_TTL_S = 30.0


def _parse(path: pathlib.Path) -> dict:
    out = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        if k and k.replace("_", "").isalnum():
            out[k] = v.strip().strip('"').strip("'")
    return out


def env(refresh: bool = False) -> dict:
    global _CACHE, _CACHE_AT
    if _CACHE is None or refresh or (time.time() - _CACHE_AT) > _TTL_S:
        merged = _parse(LEGACY_ENV)
        merged.update(_parse(EXTERNAL_ENV))  # external-models.env wins
        _CACHE, _CACHE_AT = merged, time.time()
    return _CACHE


def provider_ids() -> list:
    return [p for p in _PROVIDER_ORDER if p in REGISTRY]


def paid_ids() -> list:
    return [p for p in provider_ids() if REGISTRY[p]["paid"]]


def enabled(pid: str) -> bool:
    d = REGISTRY.get(pid)
    if not d:
        return False
    return str(env().get(d["enabled_var"], "false")).strip().lower() in ("1", "true", "yes", "on")


def key_present(pid: str) -> bool:
    """Boolean only — never the value."""
    return bool(_key(pid))


def key_var(pid: str) -> str:
    d = REGISTRY.get(pid) or {}
    return d.get("key_var") or ""


def model(pid: str, tier: str = "standard") -> str:
    d = REGISTRY.get(pid) or {}
    mv = d.get("model_vars") or {}
    resolved = _discovered(pid)
    tiers = resolved.get("tiers") or {}
    for t in (tier, "standard", "strong", "economy", "frontier", "local"):
        env_name = env().get(mv.get(t, ""), "") if mv.get(t) else ""
        if not env_name:
            continue
        if tiers.get(t):
            return tiers[t]
        return env_name
    return ""


def _discovered(pid: str) -> dict:
    """Discovery record for a provider (model ids actually offered). Model names
    are not secrets; the record contains no credential."""
    try:
        return (json.loads(DISCOVERY.read_text(encoding="utf-8")) or {}).get(pid) or {}
    except (OSError, ValueError):
        return {}


def base(pid: str) -> str:
    """Effective base URL. A reachability override (e.g. the local model is on a
    different host than the caller) wins over the declared value."""
    ov = _discovered(pid).get("base_override")
    if ov:
        return ov
    d = REGISTRY.get(pid) or {}
    return env().get(d.get("base_var") or "", "")


def models(pid: str) -> dict:
    """tier -> model name. Model names are not secrets."""
    d = REGISTRY.get(pid) or {}
    return {t: env().get(v, "") for t, v in (d.get("model_vars") or {}).items() if env().get(v)}


def chat_url(pid: str, mdl: str = "") -> str:
    d = REGISTRY.get(pid) or {}
    if d.get("chat_url_var") and env().get(d["chat_url_var"]):
        return env()[d["chat_url_var"]]
    b = base(pid)
    suffix = (d.get("chat_suffix") or "").replace("{model}", mdl)
    return (b.rstrip("/") + suffix) if b else ""


def models_url(pid: str) -> str:
    d = REGISTRY.get(pid) or {}
    return env().get(d.get("models_url_var") or "", "") if d.get("models_url_var") else ""


def health(pid: str) -> dict:
    """Credential-free health probe. Local provider only."""
    d = REGISTRY.get(pid) or {}
    if not d.get("base_var"):
        return {"ok": False, "error": "NO_HEALTH_URL"}
    b = base(pid)
    path = env().get(d.get("health_path_var") or "", "/health") or "/health"
    if not b:
        return {"ok": False, "error": "NO_BASE_URL"}
    t0 = time.time()
    try:
        with urllib.request.urlopen(b.rstrip("/") + path, timeout=5) as r:
            return {"ok": r.status == 200, "http_status": r.status,
                    "latency_s": round(time.time() - t0, 3), "credential_used": False}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__,
                "latency_s": round(time.time() - t0, 3), "credential_used": False}


def _key(pid: str) -> str:
    """INTERNAL. Returns the credential value. Never log, never return upward."""
    d = REGISTRY.get(pid) or {}
    var = d.get("key_var")
    if not var:
        return ""
    e = env()
    v = (e.get(var) or "").strip()
    if not v or "PASTE" in v.upper() or v in ("...", "CHANGEME"):
        return ""
    return v


def _spec(pid: str, mdl: str, prompt: str, max_tokens: int, timeout_s: int) -> dict:
    """INTERNAL. Contains the credential. Handed to the child over stdin only."""
    d = REGISTRY[pid]
    e = env()
    key = _key(pid)
    url = chat_url(pid, mdl)
    headers = {"Content-Type": "application/json"}
    if d["kind"] == "local":
        # llama.cpp native surface: {} prompt / n_predict / stop, no credential
        body = {"prompt": prompt, "n_predict": max_tokens,
                "temperature": 0.2, "cache_prompt": False, "stop": ["\n"]}
    elif d["auth"] == ANTHROPIC:
        headers["x-api-key"] = key
        headers["anthropic-version"] = e.get("ANTHROPIC_VERSION", "2023-06-01")
        if e.get("ANTHROPIC_WORKSPACE_ID"):
            headers["anthropic-workspace-id"] = e["ANTHROPIC_WORKSPACE_ID"]
        body = {"model": mdl, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
    elif d["auth"] == GOOGLE:
        headers["x-goog-api-key"] = key
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens}}
    else:  # BEARER (also covers the local llama.cpp native path when paid=False)
        if key:
            headers["Authorization"] = "Bearer " + key
        body = {"model": mdl, d.get("max_tokens_field", "max_tokens"): max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        if not d.get("omit_temperature"):
            body["temperature"] = 0.2
    return {"url": url, "headers": headers, "body": body, "timeout_s": timeout_s,
            "auth": d["auth"]}


RUNNER = r'''
import json, sys, time, urllib.request, urllib.error, hashlib
spec = json.load(sys.stdin)
t0 = time.time()
data = json.dumps(spec["body"]).encode()
req = urllib.request.Request(spec["url"], data=data, headers=spec["headers"], method="POST")
out = {"http_status": None, "text": "", "usage": {}, "served": None, "error": None}
try:
    with urllib.request.urlopen(req, timeout=spec["timeout_s"]) as r:
        out["http_status"] = r.status
        payload = json.loads(r.read().decode())
        if "choices" in payload:
            out["text"] = payload["choices"][0].get("message", {}).get("content", "")
            u = payload.get("usage") or {}
            out["usage"] = {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}
            out["served"] = payload.get("model")
        elif "candidates" in payload:
            c = payload["candidates"][0]
            parts = (c.get("content") or {}).get("parts") or []
            out["text"] = "".join(p.get("text", "") for p in parts)
            u = payload.get("usageMetadata") or {}
            out["usage"] = {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0)}
            out["served"] = payload.get("modelVersion") or None
        elif isinstance(payload.get("content"), list):
            blocks = payload.get("content") or []
            out["text"] = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
            u = payload.get("usage") or {}
            out["usage"] = {"in": u.get("input_tokens", 0), "out": u.get("output_tokens", 0)}
            out["served"] = payload.get("model")
        elif "content" in payload or "tokens_predicted" in payload:
            out["text"] = payload.get("content", "")
            out["usage"] = {"in": payload.get("tokens_evaluated", 0), "out": payload.get("tokens_predicted", 0)}
            out["served"] = spec["body"].get("model")
except urllib.error.HTTPError as e:
    out["http_status"] = e.code
    try:
        msg = json.loads(e.read().decode())
        err = (msg.get("error") or {})
        out["error"] = str(err.get("type") or err.get("code") or err.get("message") or "")[:120] or "HTTP_" + str(e.code)
    except Exception:
        out["error"] = "HTTP_" + str(e.code)
except Exception as e:
    out["error"] = type(e).__name__
out["latency_s"] = round(time.time() - t0, 3)
out["response_sha256"] = hashlib.sha256(out["text"].encode()).hexdigest()
sys.stdout.write(json.dumps(out))
'''


def call(pid: str, mdl: str, prompt: str, max_tokens: int = 256,
         timeout_s: int = 60) -> dict:
    """Run one completion. The credential goes to the child over stdin, never argv.

    Returns text + usage + status. The returned dict never contains the key.
    """
    import subprocess
    import sys as _sys
    spec = _spec(pid, mdl, prompt, max_tokens, timeout_s)
    try:
        p = subprocess.run([_sys.executable, "-c", RUNNER], input=json.dumps(spec).encode(),
                           capture_output=True, timeout=timeout_s + 20)
        out = json.loads(p.stdout.decode("utf-8") or "{}")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": "TRANSPORT_" + type(exc).__name__, "text": ""}
    out["ok"] = bool(out.get("http_status") == 200 and not out.get("error"))
    out.setdefault("text", "")
    return out


def list_models(pid: str, timeout_s: int = 20) -> dict:
    """Official models endpoint. Metadata only — no tokens billed."""
    d = REGISTRY[pid]
    url = models_url(pid)
    if not url:
        return {"ok": False, "error": "NO_MODELS_URL", "ids": []}
    key = _key(pid)
    headers = {}
    if d["auth"] == ANTHROPIC:
        headers = {"x-api-key": key, "anthropic-version": env().get("ANTHROPIC_VERSION", "2023-06-01")}
        if env().get("ANTHROPIC_WORKSPACE_ID"):
            headers["anthropic-workspace-id"] = env()["ANTHROPIC_WORKSPACE_ID"]
    elif d["auth"] == GOOGLE:
        headers = {"x-goog-api-key": key}
    elif d["auth"] == BEARER and key:
        headers = {"Authorization": "Bearer " + key}
    req = urllib.request.Request(url, headers=headers, method="GET")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            payload = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode())
            err = msg.get("error") or {}
            detail = str(err.get("type") or err.get("code") or err.get("message") or "")[:120]
        except Exception:
            detail = ""
        return {"ok": False, "http_status": e.code, "error": detail or ("HTTP_" + str(e.code)),
                "latency_s": round(time.time() - t0, 3), "ids": []}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__,
                "latency_s": round(time.time() - t0, 3), "ids": []}
    ids = []
    for row in (payload.get("data") or payload.get("models") or []):
        if isinstance(row, dict):
            name = row.get("id") or row.get("name") or row.get("model")
            if name:
                ids.append(str(name).split("/")[-1] if str(name).startswith("models/") else str(name))
    return {"ok": True, "http_status": 200, "count": len(ids), "ids": sorted(set(ids)),
            "latency_s": round(time.time() - t0, 3)}


CONFIG_DIR = pathlib.Path("/home/ari/ofn/state/api-budget/config")
HEALTH_FILE = CONFIG_DIR / "provider-health.json"
ROUTES_FILE = CONFIG_DIR / "provider-routes.json"

# Deterministic route rank: free local first, then measured-cheapest live paid,
# then stronger, then the independent reviewer. Never a silent failover: every
# skipped provider has a recorded status reason.
# OWNER DECISION 2026-09-13: deepseek is the PREFERRED default for ordinary work
# (was "cheapest healthy" = gemini). Budget caps unchanged by the same ruling.
ROUTE_RANK = ("local-llamacpp-180", "deepseek", "gemini", "openai",
              "sakana-fugu", "anthropic")

LIVE = "LIVE"


def health_status(pid: str) -> str:
    """Last recorded health verdict for a provider (no credential inside)."""
    try:
        rec = json.loads(HEALTH_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return "UNKNOWN"
    return ((rec.get(pid) or {}).get("status")) or "UNKNOWN"


def health_record() -> dict:
    try:
        return json.loads(HEALTH_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def candidates() -> list:
    """Paid providers that are enabled, keyed, and measured LIVE, in route rank."""
    out = []
    for pid in ROUTE_RANK:
        d = REGISTRY.get(pid)
        if not d or not d["paid"]:
            continue
        if enabled(pid) and key_present(pid) and health_status(pid) == LIVE:
            out.append(pid)
    return out


def route(primary: str | None = None) -> list:
    """Full deterministic chain. Ordered, explicit, receipt-friendly."""
    chain = ["deterministic", "local-llamacpp-180"]
    chain += [p for p in candidates() if p != primary]
    if primary and primary in candidates():
        chain.insert(2, primary)
    chain += ["WAITING_COGNITION"]
    return chain


def redacted_status() -> dict:
    out = {}
    for pid in provider_ids():
        d = REGISTRY[pid]
        out[pid] = {"enabled": enabled(pid), "paid": d["paid"],
                    "kind": d["kind"], "role": d.get("role"),
                    "key_var": d.get("key_var"), "key_present": key_present(pid),
                    "auth": d["auth"], "models": models(pid),
                    "chat_url": chat_url(pid, model(pid)), "models_url": models_url(pid)}
    return out


def write_health(record: dict) -> str:
    """Persist measured health. Statuses and reasons only — never a value."""
    import os as _os
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_FILE.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8")
    try:
        _os.chmod(HEALTH_FILE, 0o640)
    except OSError:
        pass
    return str(HEALTH_FILE)
