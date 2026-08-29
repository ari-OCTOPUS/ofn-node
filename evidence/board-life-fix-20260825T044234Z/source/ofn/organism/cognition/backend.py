
import hashlib
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ofn.organism.persistence.db import DB_LOCK

_CACHE_LOCK = threading.RLock()
_INFERENCE_LOCK = threading.Lock()
CACHE_NAMESPACE = b"board-life-001:qwen3-0.6b-q4_0:ask-policy-v1\0"


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        _request,
        _file_pointer,
        _code,
        _message,
        _headers,
        _new_url,
    ):
        return None


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
        parsed = urllib.parse.urlparse(base)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.port != 8081
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("local_cortex_must_use_http_numeric_loopback_8081")
        self.base = "http://127.0.0.1:8081"
        self.timeout = timeout
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            NoRedirectHandler(),
        )

    def available(self):
        try:
            with self.opener.open(self.base + "/health", timeout=3) as r:
                return r.status == 200
        except Exception:
            return False

    def complete(self, prompt_hash_source, max_tokens=96):
        body = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Reply briefly. Do not claim access to sensors or external "
                        "systems. If uncertain, say so."
                    ),
                },
                {"role": "user", "content": prompt_hash_source},
            ],
            "max_tokens": max_tokens,
            "temperature": 0,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        data = json.dumps(body).encode()
        req = urllib.request.Request(self.base + "/v1/chat/completions", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        t0 = time.monotonic()
        try:
            with self.opener.open(req, timeout=self.timeout) as r:
                raw = r.read()
                status = r.status
        except urllib.error.HTTPError as e:
            raw = e.read(); status = e.code
        except Exception as e:
            return {"status": "DEGRADED", "error": str(e), "backend_selected": "local_qwen"}
        try:
            response_body = (
                json.loads(raw.decode("utf-8", "replace")) if raw else {}
            )
        except json.JSONDecodeError:
            response_body = {}
        if not isinstance(response_body, dict):
            response_body = {}
        choices = response_body.get("choices")
        if not isinstance(choices, list):
            choices = []
        first_choice = choices[0] if choices and isinstance(choices[0], dict) else {}
        message = first_choice.get("message")
        if not isinstance(message, dict):
            message = {}
        answer = message.get("content")
        if not isinstance(answer, str) or not answer.strip():
            answer = None
        return {
            "status": "LOW_CONFIDENCE" if status == 200 and answer else "DEGRADED",
            "http_status": status,
            "latency_ms": int((time.monotonic()-t0)*1000),
            "response_hash": hashlib.sha256(raw).hexdigest(),
            "backend_selected": "local_qwen",
            "usage": response_body.get("usage"),
            "answer": answer.strip() if answer else None,
            "error": None if answer else "empty_or_invalid_model_content",
        }


def _normalise_text(text: str) -> str:
    return " ".join(text.strip().casefold().split())


def _request_hash(text: str) -> str:
    return hashlib.sha256(CACHE_NAMESPACE + text.encode("utf-8")).hexdigest()


def _deterministic_rule(
    text: str,
    status_snapshot: dict[str, Any],
) -> dict[str, Any] | None:
    normalised = _normalise_text(text)
    if normalised in {"ping", "پینگ"}:
        return {
            "route": "deterministic_rule",
            "label": "RULE_DEFINED",
            "answer": "PONG",
            "data": None,
        }
    if normalised in {"status", "health", "وضعیت", "وضعیتت چیست؟", "وضعیتت چیه"}:
        return {
            "route": "deterministic_rule",
            "label": "RULE_DEFINED",
            "answer": (
                f"health={status_snapshot.get('health_state', 'UNKNOWN')}; "
                f"cortex={status_snapshot.get('local_cortex', 'UNKNOWN')}; "
                f"identity_chain_valid={status_snapshot.get('identity_chain_valid')}"
            ),
            "data": status_snapshot,
        }
    return None


class AskCascade:
    def __init__(self, con, cortex: LocalCortex | None = None):
        self.con = con
        self.cortex = cortex or LocalCortex()

    def _cached(self, request_hash: str) -> dict[str, Any] | None:
        with _CACHE_LOCK, DB_LOCK:
            row = self.con.execute(
                """
                SELECT response_text, source_route, source_response_hash, hits
                FROM ask_cache
                WHERE request_hash=?
                """,
                (request_hash,),
            ).fetchone()
            if not row:
                return None
            self.con.execute(
                """
                UPDATE ask_cache
                SET hits=hits+1, last_used_at=?
                WHERE request_hash=?
                """,
                (time.time(), request_hash),
            )
        return {
            "route": "cache",
            "label": "LOW_CONFIDENCE",
            "answer": row[0],
            "data": {
                "original_route": row[1],
                "source_response_hash": row[2],
                "prior_hits": row[3],
            },
        }

    def _store_cache(
        self,
        request_hash: str,
        response_text: str,
        source_route: str,
        source_response_hash: str,
    ) -> None:
        now = time.time()
        with _CACHE_LOCK, DB_LOCK:
            self.con.execute(
                """
                INSERT INTO ask_cache(
                    request_hash, response_text, source_route,
                    source_response_hash, created_at, last_used_at, hits
                ) VALUES (?,?,?,?,?,?,0)
                ON CONFLICT(request_hash) DO UPDATE SET
                    response_text=excluded.response_text,
                    source_route=excluded.source_route,
                    source_response_hash=excluded.source_response_hash,
                    last_used_at=excluded.last_used_at
                """,
                (
                    request_hash,
                    response_text,
                    source_route,
                    source_response_hash,
                    now,
                    now,
                ),
            )

    def ask(
        self,
        text: str,
        status_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        request_hash = _request_hash(text)
        attempts: list[dict[str, Any]] = []

        deterministic = _deterministic_rule(text, status_snapshot)
        attempts.append({
            "route": "deterministic_rule",
            "result": "MATCH" if deterministic else "NO_MATCH",
        })
        if deterministic:
            return {
                **deterministic,
                "request_hash": request_hash,
                "attempts": attempts,
            }

        cache_error = None
        try:
            cached = self._cached(request_hash)
        except Exception as exc:
            cached = None
            cache_error = f"{type(exc).__name__}: {exc}"
        attempts.append({
            "route": "cache",
            "result": "ERROR" if cache_error else ("HIT" if cached else "MISS"),
            "error": cache_error,
        })
        if cached:
            return {
                **cached,
                "request_hash": request_hash,
                "attempts": attempts,
            }

        with _INFERENCE_LOCK:
            try:
                rechecked = self._cached(request_hash)
            except Exception as exc:
                rechecked = None
                attempts.append({
                    "route": "cache_recheck",
                    "result": "ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                })
            if rechecked:
                attempts.append({
                    "route": "cache_recheck",
                    "result": "HIT",
                    "error": None,
                })
                return {
                    **rechecked,
                    "request_hash": request_hash,
                    "attempts": attempts,
                }

            try:
                local = self.cortex.complete(text)
            except Exception as exc:
                local = {
                    "status": "DEGRADED",
                    "answer": None,
                    "error": f"{type(exc).__name__}: {exc}",
                    "http_status": None,
                }
            attempts.append({
                "route": "local_qwen",
                "result": local.get("status", "DEGRADED"),
                "http_status": local.get("http_status"),
                "error": local.get("error"),
            })
            if local.get("status") == "LOW_CONFIDENCE" and local.get("answer"):
                cache_store_error = None
                try:
                    self._store_cache(
                        request_hash,
                        local["answer"],
                        "local_qwen",
                        local["response_hash"],
                    )
                except Exception as exc:
                    cache_store_error = f"{type(exc).__name__}: {exc}"
                    attempts.append({
                        "route": "cache_store",
                        "result": "ERROR",
                        "error": cache_store_error,
                    })
                return {
                    "route": "local_qwen",
                    "label": "LOW_CONFIDENCE",
                    "answer": local["answer"],
                    "data": {
                        "latency_ms": local.get("latency_ms"),
                        "response_hash": local["response_hash"],
                        "usage": local.get("usage"),
                        "cache_store_error": cache_store_error,
                    },
                    "request_hash": request_hash,
                    "attempts": attempts,
                }

        return {
            "route": "needs_owner",
            "label": "NEEDS_OWNER",
            "answer": None,
            "data": {
                "reason": "LOCAL_CORTEX_UNAVAILABLE_OR_EMPTY",
                "local_error": local.get("error"),
            },
            "request_hash": request_hash,
            "attempts": attempts,
        }
