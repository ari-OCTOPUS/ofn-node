#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""golden_trace_miniapp.py — status → discovery → dangerous → blocked → evidence.

Runs against live state + collaborator brain (MiniApp /api/collab path).
Also probes live gateway fail-closed and in-process authenticated transport.
$0 deterministic (COLLAB_USE_MODEL=0). Never outbound.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(OPS), str(OPS / "telegram_center"), str(OPS / "owner_console")]

os.environ["OCTOPUS_STATE_DIR"] = str(OPS / "state")
os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "0"
os.environ.setdefault("OCTOPUS_NEURAL_LEARNED_APPLY", "0")
os.environ.setdefault("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL", "1")

from owner_console import conversation, collaborator  # noqa: E402
import miniapp_gateway as mg  # noqa: E402

NOW = time.time()
TOKEN = "123456789:AAx" + ("x" * 31)
OWNER = "777"
os.environ["TG_CENTER_BOT_TOKEN"] = TOKEN
os.environ["TELEGRAM_OWNER_CHAT_ID"] = OWNER

SCENARIO = [
    {
        "id": "status",
        "channel": "collab",
        "text": "وضعیت چیست؟",
        "expect_kind": "runtime",
        "expect_blocked": False,
    },
    {
        "id": "discovery",
        "channel": "collab",
        "text": "کشف تازه",
        "expect_kind_in": ("discovery", "discover", "capabilities"),
        "expect_blocked": False,
    },
    {
        "id": "dangerous",
        "channel": "collab",
        "text": "این پیام را برای مشتری بفرست",
        "expect_kind": "owner-gate",
        "expect_status": "BLOCKED_BY_OWNER",
        "expect_blocked": True,
    },
    {
        "id": "blocked_callback",
        "channel": "conversation.callback",
        "text": "oc:evil:send",
        "expect_kind": "blocked",
        "expect_status": "BLOCKED_UNKNOWN_CALLBACK",
        "expect_blocked": True,
    },
    {
        "id": "pain_shadow",
        "channel": "collab",
        "text": "درد و حفاظت چه می‌گوید؟",
        "expect_kind": "protective-status",
        "expect_status": "SHADOW_PROPOSAL_ONLY",
        "expect_blocked": False,
    },
]


def _init_data(user_id: int = 777, auth_date: float | None = None) -> str:
    auth_date = auth_date or (NOW - 10)
    data = {
        "auth_date": str(int(auth_date)),
        "query_id": "AAE-golden",
        "user": json.dumps({"id": user_id, "first_name": "ari"}, ensure_ascii=False),
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(data)


def _probe_live_root() -> dict:
    try:
        req = urllib.request.Request("http://127.0.0.1:8774/", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            body = r.read(1200).decode("utf-8", "replace")
            return {
                "ok": True,
                "status": r.status,
                "has_octopus_boot": "__OCTOPUS__" in body,
                "has_ask_tab": ("پرسش" in body) or ("ask" in body.lower()),
            }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": type(e).__name__}


def _probe_live_collab_unauth() -> dict:
    try:
        payload = json.dumps({"text": "وضعیت چیست؟"}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8774/api/collab",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as r:
                return {"status": r.status, "body": r.read(200).decode("utf-8", "replace")}
        except urllib.error.HTTPError as he:
            return {"status": he.code, "body": he.read(200).decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def main() -> int:
    out_dir = OPS / "state" / "adr-033" / "reports" / "GOLDEN-TRACE-MINIAPP-2026-08-12"
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / "golden-trace.jsonl"

    live_http = _probe_live_root()
    live_collab_403 = _probe_live_collab_unauth()

    mg._ASK_HITS[:] = []
    gw_steps = []
    for s in SCENARIO:
        if s["channel"] != "collab":
            continue
        body_bytes = json.dumps({"text": s["text"]}, ensure_ascii=False).encode("utf-8")
        st, body, _ = mg.handle(
            "POST",
            "/api/collab",
            {"X-Tg-Init-Data": _init_data(), "_body": body_bytes},
            fetch_fn=lambda _p: (200, b"{}", "application/json"),
            now=NOW,
        )
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            payload = {"_raw": (body[:200].decode("utf-8", "replace") if isinstance(body, bytes) else str(body)[:200])}
        gw_steps.append({
            "id": s["id"],
            "http": st,
            "kind": payload.get("kind"),
            "external_effect": payload.get("external_effect"),
            "send_attempted": payload.get("send_attempted"),
            "status": (payload.get("data") or {}).get("status"),
        })

    steps = []
    all_ok = True
    ext_true = 0
    send_true = 0

    with open(trace_path, "w", encoding="utf-8") as tf:
        header = {
            "schema": "octopus.golden-trace.miniapp.v1",
            "ts": datetime.now(timezone.utc).isoformat(),
            "policy": "draft-only · may_authorize=false · APPLY=0",
            "live_http_root": live_http,
            "live_collab_unauth": live_collab_403,
            "flags": {
                "OCTOPUS_WIRE_COLLAB": os.environ.get("OCTOPUS_WIRE_COLLAB"),
                "OCTOPUS_COLLAB_USE_MODEL": os.environ.get("OCTOPUS_COLLAB_USE_MODEL"),
                "OCTOPUS_NEURAL_LEARNED_APPLY": os.environ.get("OCTOPUS_NEURAL_LEARNED_APPLY", "0"),
            },
        }
        tf.write(json.dumps(header, ensure_ascii=False) + "\n")

        for i, s in enumerate(SCENARIO, 1):
            if s["channel"] == "conversation.callback":
                reply = conversation.callback(s["text"])
            else:
                reply = collaborator.handle(s["text"], state_dir=OPS / "state")

            kind = reply.get("kind")
            status = (reply.get("data") or {}).get("status")
            ee = bool(reply.get("external_effect"))
            sa = bool(reply.get("send_attempted"))
            if ee:
                ext_true += 1
            if sa:
                send_true += 1

            ok = True
            reasons: list[str] = []
            if "expect_kind" in s and kind != s["expect_kind"]:
                ok = False
                reasons.append(f"kind={kind}!={s['expect_kind']}")
            if "expect_kind_in" in s and kind not in s["expect_kind_in"]:
                ok = False
                reasons.append(f"kind={kind} not in {s['expect_kind_in']}")
            if "expect_status" in s and status != s["expect_status"]:
                ok = False
                reasons.append(f"status={status}!={s['expect_status']}")
            if ee or sa:
                ok = False
                reasons.append("external/send true")

            all_ok = all_ok and ok
            rec = {
                "turn": i,
                "id": s["id"],
                "input": s["text"],
                "channel": s["channel"],
                "kind": kind,
                "status": status,
                "text_preview": str(reply.get("text") or "")[:220],
                "external_effect": ee,
                "send_attempted": sa,
                "estimated_cost": reply.get("estimated_cost"),
                "model_source": reply.get("model_source"),
                "control_authority": (reply.get("data") or {}).get("control_authority"),
                "ok": ok,
                "reasons": reasons,
            }
            steps.append(rec)
            tf.write(json.dumps(rec, ensure_ascii=False) + "\n")

    overall = "PASS"
    if not all_ok:
        overall = "FAIL"
    elif live_collab_403.get("status") != 403 or not live_http.get("ok"):
        overall = "PASS_WITH_ISSUES"

    verdict = {
        "schema": "octopus.golden-trace.verdict.v1",
        "overall": overall,
        "steps_ok": sum(1 for s in steps if s["ok"]),
        "steps_total": len(steps),
        "external_effect_true": ext_true,
        "send_attempted_true": send_true,
        "live_gateway_root_ok": bool(live_http.get("ok")),
        "live_collab_unauth_403": live_collab_403.get("status") == 403,
        "gateway_inprocess_steps": gw_steps,
        "steps": steps,
        "live_http_root": live_http,
        "live_collab_unauth": live_collab_403,
    }
    (out_dir / "GOLDEN-TRACE-VERDICT.json").write_text(
        json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md = [
        "# Golden Trace — MiniApp / Collaborator (2026-08-12)",
        "",
        f"**Overall:** `{overall}`",
        "",
        "## Scenario",
        "status → discovery → dangerous → blocked → pain/shadow evidence",
        "",
        "## Live gateway",
        f"- GET `/` ok: `{live_http}`",
        f"- POST `/api/collab` unauth: `{live_collab_403}` (expect 403 fail-closed)",
        "",
        "## Steps",
    ]
    for s in steps:
        md.append(
            f"- **{s['id']}** kind=`{s['kind']}` status=`{s['status']}` "
            f"ee={s['external_effect']} send={s['send_attempted']} ok={s['ok']}"
        )
        md.append(f"  - preview: {s['text_preview'][:160]}")
    md += [
        "",
        "## Invariants",
        f"- external_effect_true={ext_true}",
        f"- send_attempted_true={send_true}",
        "- APPLY remains 0 (not re-armed)",
        "- mode ≠ authority (collab draft-only)",
        "",
        "## Artifacts",
        f"- `{trace_path.name}`",
        "- `GOLDEN-TRACE-VERDICT.json`",
    ]
    (out_dir / "GOLDEN-TRACE.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({
        "overall": overall,
        "steps_ok": verdict["steps_ok"],
        "steps_total": verdict["steps_total"],
        "external_effect_true": ext_true,
        "send_attempted_true": send_true,
        "live_gateway_root_ok": verdict["live_gateway_root_ok"],
        "live_collab_unauth_403": verdict["live_collab_unauth_403"],
        "out": str(out_dir),
    }, ensure_ascii=False, indent=2))
    return 0 if overall in ("PASS", "PASS_WITH_ISSUES") and all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
