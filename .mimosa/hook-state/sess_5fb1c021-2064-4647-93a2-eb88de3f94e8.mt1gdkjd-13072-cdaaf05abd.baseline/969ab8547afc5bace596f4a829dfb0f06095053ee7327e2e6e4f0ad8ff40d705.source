#!/usr/bin/env python3
"""ingest_adapter.py — آداپتورِ generic ingestion برای تماس‌های بیرونی (M1).

الگو: pocketsmith_api.py (Black Box client) — flag-based، stdlib urllib، retry 429،
      dedup by id، merge به store، fail-soft، readonly GET، propose-only.

خط‌قرمزهای سخت:
  • فقط GET — هرگز POST/PUT/DELETE.
  • کلید فقط از os.environ؛ هرگز echo/log/return نمی‌شود.
  • پشتِ فلگِ OCTOPUS_WIRE_INGEST_{NAME} (پیش‌فرض خاموش → no-op).
  • circuit breaker قبل از هر تماس consult می‌شود (fail-closed).
  • DLQ برای شکست‌های غیرقابل‌بازیابی.
  • secrets در payload هرگز نمی‌مانند (strip قبل از store/DLQ).
  • stdlib-only؛ $0 offline؛ propose-only.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib       # noqa: E402
import circuit_breaker as cb  # noqa: E402
import dlq          # noqa: E402

from leg import TaskPacket, Proposal, Leg  # noqa: E402


class IngestAdapter:
    """آداپتور ingestion با circuit breaker + DLQ + propose-only output.

    usage:
        pkt = TaskPacket(leg_id="ingest-x", organ="ARCHITECT_SYS",
                         read_allowlist=("note-a",), budget_aud=0.5)
        adapter = IngestAdapter(pkt, base_url="https://api.example.com/v1",
                                flag_env="OCTOPUS_WIRE_EXAMPLE")
        proposal = adapter.fetch_and_propose("/items", map_fn=my_mapper)
    """

    _DEFAULT_TIMEOUT = 30
    _MAX_RETRIES = 3
    _MAX_PAGES = 1000

    def __init__(self, packet: TaskPacket, *, base_url: str, flag_env: str,
                 key_env: str | None = None, timeout: int = _DEFAULT_TIMEOUT,
                 max_retries: int = _MAX_RETRIES, max_pages: int = _MAX_PAGES,
                 organ_table: dict | None = None):
        self.packet = packet
        self.base_url = base_url.rstrip("/")
        self.flag_env = flag_env
        self.key_env = key_env
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_pages = max_pages
        self.leg = Leg(packet, organ_table=organ_table)
        self._last_error: str | None = None
        self._proposals: list[Proposal] = []

    # ─── فلگ + کلید (پیش‌فرض خاموش) ────────────────────────────────────────────
    def _flag_on(self) -> bool:
        return str(os.environ.get(self.flag_env, "")).strip().lower() in {"1", "true", "yes", "on"}

    def _api_key(self) -> str | None:
        if not self.key_env:
            return None
        try:
            import env_loader
            env_loader.load_env()
        except Exception:  # noqa: BLE001
            pass
        return os.environ.get(self.key_env) or None

    # ─── circuit breaker consult ───────────────────────────────────────────────
    def _circuit_ok(self) -> dict:
        target = urllib.parse.urlparse(self.base_url).netloc or self.base_url
        return cb.check(target)

    # ─── HTTP (فقط GET) ────────────────────────────────────────────────────────
    def _build_url(self, path: str, params: dict | None = None) -> str:
        url = path if path.startswith("http") else self.base_url + path
        if params:
            q = {k: v for k, v in params.items() if v is not None}
            if q:
                sep = "&" if "?" in url else "?"
                url = url + sep + urllib.parse.urlencode(q)
        return url

    def _get(self, path: str, params: dict | None = None) -> dict:
        """خروجی: {ok, status, data, link, note}."""
        key = self._api_key()
        if self.key_env and not key:
            return {"ok": False, "status": 0, "data": None, "link": None,
                    "note": f"{self.key_env} not set"}
        url = self._build_url(path, params)
        attempt = 0
        while True:
            req = urllib.request.Request(url, method="GET", headers={
                "Accept": "application/json",
                "User-Agent": "octopus-ingest-readonly/1.0",
            })
            if key:
                # کلید در هدر می‌رود؛ هرگز در خروجی/note
                req.add_header("Authorization", f"Bearer {key}")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    link = None
                    try:
                        link = resp.headers.get("Link")
                    except Exception:  # noqa: BLE001
                        pass
                    data = json.loads(body.decode("utf-8")) if body else None
                    return {"ok": True, "status": getattr(resp, "status", 200) or 200,
                            "data": data, "link": link, "note": "ok"}
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < self.max_retries:
                    attempt += 1
                    try:
                        ra = int((e.headers.get("Retry-After") if e.headers else None) or 0)
                    except (TypeError, ValueError):
                        ra = 0
                    time.sleep(min(ra if ra > 0 else 2 ** attempt, 60))
                    continue
                reason = "rate-limit (429)" if e.code == 429 else f"HTTP {e.code}"
                return {"ok": False, "status": e.code, "data": None, "link": None,
                        "note": f"{reason} (fail-soft)"}
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                return {"ok": False, "status": 0, "data": None, "link": None,
                        "note": f"network/timeout — {type(e).__name__} (fail-soft)"}

    def _parse_next_link(self, link_header: str | None) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            seg = part.strip()
            if 'rel="next"' in seg or "rel=next" in seg:
                lt, gt = seg.find("<"), seg.find(">")
                if lt != -1 and gt != -1 and gt > lt:
                    return seg[lt + 1:gt]
        return None

    # ─── public API ────────────────────────────────────────────────────────────
    def fetch(self, path: str, params: dict | None = None) -> dict:
        """fetch خام با circuit breaker + DLQ. خروجی همیشه صادق."""
        if not self._flag_on():
            return {"ok": False, "wired": False, "data": None,
                    "note": f"flag {self.flag_env} off → no-op"}
        c = self._circuit_ok()
        if not c["allow"]:
            return {"ok": False, "wired": True, "data": None,
                    "note": f"circuit {c['state']}: {c['reason']}"}
        result = self._get(path, params)
        target = urllib.parse.urlparse(self.base_url).netloc or self.base_url
        if result["ok"]:
            cb.record_success(target)
        else:
            cb.record_failure(target, result["note"])
            if result["status"] in (0, 403, 404, 500, 502, 503, 504):
                dlq.append({"path": path, "params": params, "status": result["status"]},
                           reason=result["note"], source=self.packet.leg_id,
                           record_type="ingest_fetch")
        return {**result, "wired": True, "circuit": c["state"]}

    def fetch_paginated(self, path: str, params: dict | None = None,
                        per_page: int = 100) -> dict:
        """pagination با دنبال‌کردن Link header. guard ضد حلقهٔ بی‌پایان."""
        if not self._flag_on():
            return {"ok": False, "wired": False, "items": [], "pages": 0,
                    "note": f"flag {self.flag_env} off → no-op"}
        c = self._circuit_ok()
        if not c["allow"]:
            return {"ok": False, "wired": True, "items": [], "pages": 0,
                    "note": f"circuit {c['state']}: {c['reason']}"}
        items: list = []
        url = self._build_url(path, params)
        pages = 0
        target = urllib.parse.urlparse(self.base_url).netloc or self.base_url
        while url and pages < self.max_pages:
            r = self._get(url)
            if not r["ok"]:
                cb.record_failure(target, r["note"])
                dlq.append({"path": path, "page": pages + 1, "status": r["status"]},
                           reason=r["note"], source=self.packet.leg_id,
                           record_type="ingest_fetch_paginated")
                return {"ok": False, "wired": True, "items": items, "pages": pages,
                        "note": f"page {pages + 1} failed: {r['note']}", "circuit": c["state"]}
            page = r["data"] or []
            if isinstance(page, list):
                items.extend(x for x in page if isinstance(x, dict))
            pages += 1
            url = self._parse_next_link(r["link"])
        cb.record_success(target)
        return {"ok": True, "wired": True, "items": items, "pages": pages,
                "note": "ok", "circuit": c["state"]}

    def fetch_and_propose(self, path: str, map_fn, params: dict | None = None) -> Proposal:
        """fetch + map → proposal. map_fn(item: dict) → payload dict.
        شکست = proposal با kind='ingest_failed' و payload حاوی دلیل."""
        fetched = self.fetch_paginated(path, params)
        if not fetched["ok"]:
            payload = {
                "path": path, "params": params,
                "error": fetched["note"], "circuit": fetched.get("circuit"),
            }
            prop = self.leg.emit_proposal("ingest_failed", payload)
            self._proposals.append(prop)
            return prop
        mapped = [m for m in (map_fn(x) for x in fetched["items"]) if m is not None]
        payload = {
            "path": path, "items_count": len(fetched["items"]),
            "mapped_count": len(mapped), "pages": fetched["pages"],
            "circuit": fetched.get("circuit"),
        }
        prop = self.leg.emit_proposal("ingest_draft", payload)
        self._proposals.append(prop)
        return prop

    def dedup_by_id(self, rows: list[dict], id_key: str = "id") -> list[dict]:
        """dedup ساده روی id_key (اولین بروز می‌ماند)."""
        seen: set = set()
        out: list[dict] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            k = r.get(id_key)
            if k is None:
                continue
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
        return out

    def merge_to_store(self, existing: list[dict], new_rows: list[dict],
                       id_key: str = "id") -> tuple[list[dict], int]:
        """existing + new → dedup → (merged, new_added)."""
        merged = self.dedup_by_id(existing + new_rows, id_key=id_key)
        return merged, len(merged) - len(existing)

    @property
    def proposals(self) -> list[Proposal]:
        return list(self._proposals)

    def status(self) -> dict:
        return {
            "leg_id": self.packet.leg_id,
            "flag_env": self.flag_env,
            "flag_on": self._flag_on(),
            "key_set": bool(self._api_key()),
            "circuit": self._circuit_ok(),
            "proposals_emitted": len(self._proposals),
            "last_error": self._last_error,
        }


if __name__ == "__main__":
    # اجرای مستقل: فقط status (فلگ/کلید set/not-set، هرگز مقدار کلید).
    _s = {
        "example_flag": str(os.environ.get("OCTOPUS_WIRE_INGEST_EXAMPLE", "not-set")),
        "read_only": True,
        "circuit_breaker": cb.status(),
    }
    print(json.dumps(_s, ensure_ascii=False, indent=2))
