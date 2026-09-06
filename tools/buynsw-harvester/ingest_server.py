#!/usr/bin/env python3
"""Standalone buy.nsw ingest sidecar.

The Chrome extension POSTs harvested records here (opt-in: endpoint+token in
the popup's advanced settings); this admits them into the painting_tenders /
painting_leads store via ofn.agents.h1_buysw_dom.ingest_batch — the SAME gate
the CLI file path uses (one truth: h1_buysw filter/score, award→lead, PII
audit, idempotent by tender_id, fail-closed on malformed envelopes).

Why a sidecar and not a route in ofn/adapters/http_api.py: that file is the
governed, HMAC-authenticated tenant router (CODEOWNERS). This lets you run
the ingest path today without touching it. Folding this into the http_api
webhook path (/api/v1/webhooks/<tenant>/buysw) is the production step — do
that under review once the extension's data proves out.

Auth: shared Bearer token in env INGEST_TOKEN (fail-closed — refuses to
start without one, unless --allow-no-auth is passed for localhost testing).

Run (on board138, from the repo root or anywhere):
    OFN_PAINTING_DB=/home/ari/.local/share/ofn/painting.sqlite INGEST_TOKEN=secret \
        python3 tools/buynsw-harvester/ingest_server.py --port 8787

Then in the extension popup set endpoint = http://<node-host>:8787/api/leads/ingest
and token = the same secret. Default remains OFF in the extension.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# make the ofn package importable when run from anywhere
REPO_ROOT = Path(__file__).resolve().parents[2]   # .../ofn-node
sys.path.insert(0, str(REPO_ROOT))

from ofn.adapters.lead_store import LeadStore       # noqa: E402
from ofn.agents.h1_buysw_dom import ingest_batch    # noqa: E402

MAX_BODY = 4 * 1024 * 1024   # 4 MB cap
PATH = "/api/leads/ingest"


def _db_path() -> str:
    p = os.environ.get("OFN_PAINTING_DB")
    if p:
        return p
    state = os.environ.get("OFN_STATE_DIR") or os.path.join(
        os.path.expanduser("~"), ".local", "share", "ofn")
    return os.path.join(state, "painting.sqlite")


class Handler(BaseHTTPRequestHandler):
    server_version = "buysw-ingest/0.3"
    token = ""           # set on the class before serving
    relevance = "painting"

    # ---- helpers ----
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "authorization, content-type")
        self.send_header("Access-Control-Max-Age", "600")

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _authed(self) -> bool:
        if not type(self).token:
            return True   # --allow-no-auth mode
        got = self.headers.get("Authorization", "")
        want = f"Bearer {type(self).token}"
        return hmac.compare_digest(got, want)

    # ---- verbs ----
    def do_OPTIONS(self):  # CORS preflight from the extension
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path.split("?")[0] != PATH:
            return self._json(404, {"status": "REJECTED",
                                    "reason": "not found"})
        if not self._authed():
            return self._json(401, {"status": "REJECTED",
                                    "reason": "unauthorised"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BODY:
            return self._json(413, {"status": "REJECTED",
                                    "reason": "bad body size"})
        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return self._json(400, {"status": "REJECTED",
                                    "reason": "invalid json"})

        store = LeadStore(_db_path())
        try:
            # The gate validates the {source:"buysw_web", records} envelope
            # itself (and the versioned batch shape) — fail-closed on drift.
            result = ingest_batch(
                payload, store, relevance=type(self).relevance)
        finally:
            store.close()
        code = 200 if result.get("status") == "DONE" else 400
        return self._json(code, result)

    def log_message(self, fmt, *args):   # quieter default logging
        sys.stderr.write("[ingest] " + (fmt % args) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="buy.nsw ingest sidecar")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--relevance", choices=["painting", "all"], default="painting",
                    help="painting = filter to painting+Sydney; all = keep everything")
    ap.add_argument("--allow-no-auth", action="store_true",
                    help="localhost testing only — skip the Bearer check")
    args = ap.parse_args(argv)

    token = os.environ.get("INGEST_TOKEN", "").strip()
    if not token and not args.allow_no_auth:
        sys.exit("refusing to start without INGEST_TOKEN (or pass --allow-no-auth "
                 "for localhost testing)")
    Handler.token = token
    Handler.relevance = args.relevance

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"buy.nsw ingest listening on http://{args.host}:{args.port}{PATH} "
          f"(db={_db_path()}, relevance={args.relevance}, "
          f"auth={'on' if token else 'OFF'})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
