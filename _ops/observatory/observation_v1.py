"""observation_v1 — آداپتور L3 رصدخانه (ADR-041).

فقط پارس قطعی روی بدنهٔ از قبل fetchشده. هیچ شبکه، هیچ تصمیم ارگانیسم،
هیچ LLM. پارس خراب → PARSE_DRIFT، هرگز حدس.
"""
from __future__ import annotations

import json
from typing import Any

SCHEMA = "observation.v1"
PARSE_DRIFT = "PARSE_DRIFT"


def parse_body(*, url: str, fetched_at: str, body: bytes) -> dict:
    """بدنه → رویدادهای observation.v1 یا PARSE_DRIFT.

    USGS geojson (features) و آرایهٔ HN (id/title) شناخته می‌شوند.
    هر شکل دیگر بدون حدس → drift.
    """
    url_s = str(url or "").strip()
    ts = str(fetched_at or "").strip()
    if not url_s or not ts:
        return {"ok": False, "error": PARSE_DRIFT, "reason": "url-or-fetched_at-missing",
                "schema": SCHEMA, "events": []}
    if not isinstance(body, (bytes, bytearray)):
        return {"ok": False, "error": PARSE_DRIFT, "reason": "body-not-bytes",
                "schema": SCHEMA, "events": []}
    try:
        payload: Any = json.loads(bytes(body).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"ok": False, "error": PARSE_DRIFT, "reason": "json-invalid",
                "schema": SCHEMA, "events": []}

    events: list[dict] = []
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        for feat in payload["features"]:
            if not isinstance(feat, dict):
                return {"ok": False, "error": PARSE_DRIFT, "reason": "feature-not-object",
                        "schema": SCHEMA, "events": []}
            props = feat.get("properties") if isinstance(feat.get("properties"), dict) else {}
            mag = props.get("mag")
            place = props.get("place")
            when = props.get("time")
            if mag is None or place is None or when is None:
                return {"ok": False, "error": PARSE_DRIFT, "reason": "usgs-fields-missing",
                        "schema": SCHEMA, "events": []}
            try:
                mag_f = float(mag)
            except (TypeError, ValueError):
                return {"ok": False, "error": PARSE_DRIFT, "reason": "usgs-mag-not-float",
                        "schema": SCHEMA, "events": []}
            events.append({
                "kind": "earthquake",
                "magnitude": mag_f,
                "place": str(place)[:200],
                "source_time": when,
            })
    elif isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict) or "id" not in item or "title" not in item:
                return {"ok": False, "error": PARSE_DRIFT, "reason": "hn-item-shape",
                        "schema": SCHEMA, "events": []}
            events.append({
                "kind": "hn-item",
                "id": item["id"],
                "title": str(item["title"])[:200],
            })
    else:
        return {"ok": False, "error": PARSE_DRIFT, "reason": "unknown-payload-shape",
                "schema": SCHEMA, "events": []}

    return {
        "ok": True,
        "schema": SCHEMA,
        "url": url_s,
        "fetched_at": ts,
        "n_events": len(events),
        "events": events,
        "may_gate": False,
        "may_trigger_tool": False,
        "feeds_organism_decision": False,
    }
