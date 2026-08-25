
import json, hashlib, time, urllib.request, urllib.error

class PolicyGate:
    def __init__(self, allow_external=False):
        self.allow_external = allow_external

    def route(self, task):
        # 1 deterministic 2 cache 3 local 4 external 5 owner
        if task.get("task_type") == "rule":
            return "deterministic"
        if task.get("required_capability") == "external" and not self.allow_external:
            return "needs_owner"
        return "local_qwen"

class LocalCortex:
    def __init__(self, base="http://127.0.0.1:8081", timeout=20):
        self.base = base
        self.timeout = timeout

    def available(self):
        try:
            with urllib.request.urlopen(self.base + "/health", timeout=3) as r:
                return r.status == 200
        except Exception:
            return False

    def complete(self, prompt_hash_source, max_tokens=32):
        body = {
            "messages": [{"role": "user", "content": prompt_hash_source}],
            "max_tokens": max_tokens,
            "temperature": 0,
        }
        data = json.dumps(body).encode()
        req = urllib.request.Request(self.base + "/v1/chat/completions", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
                status = r.status
        except urllib.error.HTTPError as e:
            raw = e.read(); status = e.code
        except Exception as e:
            return {"status": "DEGRADED", "error": str(e), "backend_selected": "local_qwen"}
        parsed = json.loads(raw.decode("utf-8", "replace")) if raw else {}
        return {
            "status": "ok" if status == 200 else "LOW_CONFIDENCE",
            "http_status": status,
            "latency": int((time.time()-t0)*1000),
            "response_hash": hashlib.sha256(raw).hexdigest(),
            "backend_selected": "local_qwen",
            "usage": parsed.get("usage"),
        }
