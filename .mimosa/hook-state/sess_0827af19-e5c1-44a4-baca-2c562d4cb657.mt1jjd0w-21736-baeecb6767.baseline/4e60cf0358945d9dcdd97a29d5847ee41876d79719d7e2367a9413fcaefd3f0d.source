#!/usr/bin/env python3
"""api.py — REST API برای Project-F OS (پشتِ stdlib http.server).

پشتِ flag OCTOPUS_WIRE_PROJECTF_API. بدونِ flag = چیزی bind نمی‌شود.

Endpoints (همه localhost، auth با PF_OS_API_TOKEN اگر set شده):
  GET  /                          — HTML landing (RTL، مثلِ organism.py)
  GET  /api/health                — beat، brain، cortex، saba-link، bridge، learning
  GET  /api/brain/thoughts        — آخرین thoughts از آخرین tick
  POST /api/brain/ask             — {task, prompt} → brain response
  GET  /api/store/fan|vault|kpi   — snapshot از DataSpine (read-only)
  POST /api/draft/submit          — ثبت draft از طریق API (propose-only)
  GET  /api/octopus/bridge        — وضعیتِ پل به ارگانیسم
  GET  /api/learning              — وضعیتِ learning bus
  GET  /api/saba                  — snapshot از پلِ صبا (pending/halt/capacity)
  GET  /api/capabilities          — capability registry

نامتغیر: هیچ PII در responses نمی‌رود. تمام endpoints content-free.
$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional

from . import config, brain as _brain, saba_link as _sl, bridge as _br
from . import singleton as _sgl, cortex_client as _cc


class _APIState:
    """state مشترک بین handler instanceها (thread-safe via GIL برای این کار)."""
    def __init__(self):
        self.brain = _brain.BrainCore()
        self.started_at = time.time()
        self.requests_served = 0
        self.last_thoughts: list = []

    def health(self) -> dict:
        return {
            "ok": True,
            "service": "pf_os",
            "version": "0.1.0",
            "uptime_s": int(time.time() - self.started_at),
            "requests_served": self.requests_served,
            "brain": self.brain.status(),
            "saba_link": _sl.snapshot(),
            "bridge": _br.snapshot(),
            "octopus": self.octopus_health(),
            "api_port": config.API_PORT,
        }

    def octopus_health(self) -> dict:
        """سلامتِ اندام‌های نسخهٔ به‌روز (fail-soft — اگر اندامی نبود، صادقانه می‌گوید).
        content-free: فقط شمار/وضعیت/گیت، هیچ PII/محتوا."""
        out: dict = {"organs_available": bool(getattr(__import__("pf_os"), "_OCTOPUS_ORGANS", []))}
        try:
            from . import event_bus as _eb
            out["bus"] = _eb.EventBus().health()
        except Exception:  # noqa: BLE001
            out["bus"] = {}
        try:
            from . import capabilities as _cap
            gates = _cap.GateState.load()
            out["outward_locked"] = gates.outward_locked
            out["gate_reason"] = gates.reason
            snap = _cap.default_registry(gates=gates).snapshot(write=False)
            out["red_locked"] = [c["name"] for c in snap["capabilities"]
                                 if c.get("level") == "red" and not c["executable"]]
        except Exception:  # noqa: BLE001
            out["outward_locked"] = True   # fail-closed حتی در health
            out["gate_reason"] = "capabilities unavailable → fail-closed"
        return out


_STATE: Optional[_APIState] = None


def _get_state() -> _APIState:
    global _STATE
    if _STATE is None:
        _STATE = _APIState()
    return _STATE


class _Handler(BaseHTTPRequestHandler):
    """HTTP handler. هر endpoint JSON برمی‌گرداند (به‌جز / که HTML)."""

    def log_message(self, *args, **kwargs):
        pass  # خاموش — log در state می‌رود نه stderr

    # ── auth (اختیاری) ──
    def _auth_ok(self) -> bool:
        token = config.API_TOKEN
        if not token:
            return True  # no token set = localhost-only، no auth
        h = self.headers.get("Authorization", "")
        if not h.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(h[6:]).decode("utf-8")
            return decoded.endswith(":" + token)
        except Exception:  # noqa: BLE001
            return False

    def _reject_auth(self):
        self._send_json(401, {"ok": False, "reason": "auth required"})

    # ── helpers ──
    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_html(self, code: int, html: str):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_body(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n == 0:
                return {}
            raw = self.rfile.read(n)
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:  # noqa: BLE001
            return {}

    # ── GET ──
    def do_GET(self):  # noqa: N802
        st = _get_state()
        st.requests_served += 1
        path = self.path.split("?", 1)[0]

        if path == "/":
            return self._send_html(200, self._landing())

        if not self._auth_ok():
            return self._reject_auth()

        if path == "/api/health":
            return self._send_json(200, st.health())
        if path == "/api/brain/thoughts":
            return self._send_json(200, {"thoughts": st.last_thoughts[-20:]})
        if path == "/api/octopus/bridge":
            return self._send_json(200, _br.snapshot())
        if path == "/api/octopus/health":
            return self._send_json(200, _get_state().octopus_health())
        if path == "/api/learning":
            # lazy import تا اگر learning_bus موجود نبود API نشکند
            try:
                from . import learning_bus as _lb
                return self._send_json(200, _lb.LearningBus().status())
            except Exception as e:  # noqa: BLE001
                return self._send_json(200, {"available": False, "reason": str(e)[:100]})
        if path == "/api/saba":
            return self._send_json(200, _sl.snapshot())
        if path == "/api/capabilities":
            return self._send_json(200, {"capabilities": self._capabilities()})
        if path.startswith("/api/store/"):
            return self._send_json(200, self._store_snapshot(path[len("/api/store/"):]))

        return self._send_json(404, {"ok": False, "reason": "not-found"})

    # ── POST ──
    def do_POST(self):  # noqa: N802
        st = _get_state()
        st.requests_served += 1
        path = self.path.split("?", 1)[0]

        if not self._auth_ok():
            return self._reject_auth()

        if path == "/api/brain/ask":
            body = self._read_body()
            task = str(body.get("task", "daily"))[:40]
            prompt = str(body.get("prompt", ""))[:4000]
            r = st.brain.think(task, prompt)
            return self._send_json(
                200 if r.ok else 503,
                {"ok": r.ok, "text": r.text, "source": r.source,
                 "tier": r.tier, "ms": r.ms, "reason": r.reason})

        if path == "/api/draft/submit":
            body = self._read_body()
            title = str(body.get("title", "")).strip()[:80]
            if not title:
                return self._send_json(400, {"ok": False, "reason": "title required"})
            cert = body.get("self_cert", {}) or {}
            # فقط از طریقِ saba_link به studio می‌نویسیم (propose-only)
            # برای حالا: فقط event به bridge (immediately)
            _br.notify_draft_submitted(pending_count=_sl.snapshot().get("pending_drafts", 0))
            return self._send_json(200, {"ok": True, "status": "queued",
                                         "note": "draft queued for saba/owner approval"})

        return self._send_json(404, {"ok": False, "reason": "not-found"})

    # ── صفحه‌سازها ──
    def _store_snapshot(self, kind: str) -> dict:
        """read-only snapshot از DataSpine (brain/store.py)."""
        if kind not in ("fan", "vault", "kpi"):
            return {"ok": False, "reason": "unknown store kind"}
        try:
            # lazy import
            import sys
            if str(Path(config.PF_ROOT) / "brain") not in sys.path:
                sys.path.insert(0, str(Path(config.PF_ROOT) / "brain"))
            from store import KPIRollup  # type: ignore
            kpi = KPIRollup()
            return {"ok": True, "kind": kind,
                    "data": kpi.snapshot() if hasattr(kpi, "snapshot") else {}}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"store unavailable: {type(e).__name__}"}

    def _capabilities(self) -> list:
        # API endpoints (همیشه) + registryِ واقعیِ اندام‌ها (با دلیل پویا اگر موجود)
        caps = [
            {"id": "brain.ask", "kind": "post", "status": "live"},
            {"id": "brain.thoughts", "kind": "get", "status": "live"},
            {"id": "store.fan", "kind": "get", "status": "live"},
            {"id": "store.vault", "kind": "get", "status": "live"},
            {"id": "store.kpi", "kind": "get", "status": "live"},
            {"id": "draft.submit", "kind": "post", "status": "propose-only"},
            {"id": "octopus.bridge", "kind": "get", "status": "live"},
            {"id": "learning", "kind": "get", "status": "live"},
            {"id": "saba", "kind": "get", "status": "live"},
        ]
        try:
            from . import capabilities as _cap
            snap = _cap.default_registry().snapshot(write=False)
            for c in snap["capabilities"]:
                caps.append({"id": c["name"], "kind": "action", "level": c.get("level"),
                             "status": "executable" if c["executable"]
                             else f"locked: {c['reason']}"})
        except Exception:  # noqa: BLE001
            pass
        return caps

    def _landing(self) -> str:
        st = _get_state()
        h = st.health()
        return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<title>pf_os — Project-F OS</title>
<style>body{{font-family:sans-serif;margin:2em;background:#0f1419;color:#c9d1d9}}
h1{{color:#58a6ff}} .ok{{color:#7ee787}} .bad{{color:#f85149}} .box{{background:#161b22;padding:1em;border-radius:6px;margin:1em 0}}
code{{background:#21262d;padding:2px 6px;border-radius:3px}}</style></head>
<body><h1>🐙🦶 Project-F OS</h1>
<div class="box"><b>service:</b> pf_os v0.1.0 · <b>uptime:</b> {h['uptime_s']}s ·
<b>requests:</b> {h['requests_served']}</div>
<div class="box"><b>brain:</b> heuristic={'yes' if h['brain']['heuristic_loaded'] else 'no'}
· cortex.wired={h['brain']['cortex'].get('wired')} · ticks={h['brain']['ticks']}</div>
<div class="box"><b>saba-link:</b> pending_drafts={h['saba_link']['pending_drafts']}
· halted={h['saba_link']['saba_halted']}</div>
<div class="box"><b>bridge:</b> {h['bridge']['lines_total']} events published ·
writable={h['bridge']['writable']}</div>
<p><code>GET /api/health</code> · <code>POST /api/brain/ask</code> ·
<code>GET /api/capabilities</code></p>
<p><i>flag-off by design. alive = set OCTOPUS_WIRE_PROJECTF_API=1.</i></p>
</body></html>"""


def start_server(blocking: bool = True) -> Optional[_sgl.ExclusiveHTTPServer]:
    """شروعِ API server (پشتِ flag). برمی‌گرداند server یا None.

    اگر flag off باشد یا port گرفته شده باشد، None برمی‌گرداند.
    """
    if not config.flag(config.WIRE_API):
        return None  # flag-off = silent
    # pre-flight: port taken؟
    if _sgl.check_port_taken(config.API_PORT):
        return None
    srv = _sgl.ExclusiveHTTPServer(("127.0.0.1", config.API_PORT), _Handler)
    if blocking:
        srv.serve_forever()
    else:
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
    return srv


def main() -> int:
    """اجرا از CLI: python -m pf_os.api"""
    if not config.flag(config.WIRE_API):
        print(f"🔴 {config.WIRE_API}=off. set OCTOPUS_WIRE_PROJECTF_API=1 to enable.")
        print(f"   سپس: python -m pf_os.api  (bind to 127.0.0.1:{config.API_PORT})")
        return 0
    print(f"🟢 pf_os API روی http://127.0.0.1:{config.API_PORT}")
    try:
        start_server(blocking=True)
    except KeyboardInterrupt:
        print("\nخروج.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
