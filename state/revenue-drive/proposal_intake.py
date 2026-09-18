#!/usr/bin/env python3
"""proposal_intake.py — درِ ورودیِ کارهای پیش‌بینی‌نشده (U-WORK v1)

هر حلقه/ایجنت می‌تواند یک «پیشنهاد» با یک `action` مشخص بفرستد. مسیر:
  risk=internal_green  → shadow (بی‌اثر) → اجرا با رسید/rollback  (Class A)
  risk=red_external|money|public|customer → کارت با دکمه برای مالک → تپ → اجرا
  action خارج از allowlist → ACTION_NOT_ALLOWED + کارت «کلاس جدید» پیشنهاد می‌شود

Schema (proposals.jsonl):
{"id","at","title","why","action":{"type","args"},"risk","reversible","evidence"}
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path("/home/ari/ofn")
RD = ROOT / "state/revenue-drive"
PROPOSALS = RD / "proposals.jsonl"
REVIEW = RD / "owner-review.json"
sys.path.insert(0, str(RD))
import action_executor  # noqa: E402

REQUIRED = ("title", "why", "action", "risk")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_jsonl(p: pathlib.Path, row: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def _receipt(kind, **kw):
    _append_jsonl(RD / "receipts.jsonl",
                  {"schema": "octopus.proposal-intake.v1", "at": now(), "kind": kind, **kw})


def submit(prop: dict) -> dict:
    missing = [k for k in REQUIRED if not prop.get(k)]
    if missing:
        return {"ok": False, "reason": "MISSING_FIELDS:%s" % ",".join(missing)}
    _sig = hashlib.sha256(json.dumps([prop.get("title"), prop.get("why"),
                                            prop.get("action")],
                                           sort_keys=True, ensure_ascii=False)
                               .encode("utf-8")).hexdigest()[:8]
    pid = prop.get("id") or ("PROP-%s-%s" % (time.strftime("%Y%m%d"), _sig))
    row = {"id": pid, "at": now(), "title": str(prop["title"])[:200],
           "why": str(prop["why"])[:400], "action": prop["action"],
           "risk": str(prop.get("risk")), "reversible": bool(prop.get("reversible", True)),
           "evidence": str(prop.get("evidence") or "")[:300],
           "source": str(prop.get("source") or "agent")}
    sh = action_executor.shadow(row["action"])
    row["shadow"] = sh
    _append_jsonl(PROPOSALS, row)

    if row["risk"] == "internal_green" and sh.get("valid"):
        res = action_executor.execute(row["action"], via="proposal_autogreen",
                                      card_id=pid, risk=row["risk"])
        row["outcome"] = {"mode": "auto_internal_green", "result": res}
        _append_jsonl(PROPOSALS, {"id": pid, "at": now(), "outcome": row["outcome"]})
        _receipt("PROPOSAL_AUTO_EXECUTED", id=pid, ok=res.get("ok"), shadow=sh)
        return {"ok": True, "mode": "auto_internal_green", "id": pid, "result": res}

    # red boundary or invalid → card for the owner (carries the action spec)
    rv = json.loads(REVIEW.read_text(encoding="utf-8")) if REVIEW.exists() else {"items": []}
    if not any(str(i.get("id")) == pid for i in rv.get("items", [])):
        rv["items"] = rv.get("items", []) + [{
            "id": pid, "at": now(), "priority": prop.get("priority", 2),
            "why": "%s — %s" % (row["title"], row["why"]),
            "action": row["action"], "risk": row["risk"], "shadow": sh,
            "owner_one_card": prop.get("owner_one_card") or []}]
        REVIEW.write_text(json.dumps(rv, ensure_ascii=False, indent=1), encoding="utf-8")
    _receipt("PROPOSAL_NEEDS_OWNER", id=pid, risk=row["risk"],
             shadow_valid=sh.get("valid"), reason=sh.get("reason"))
    return {"ok": True, "mode": "needs_owner_card", "id": pid, "shadow": sh}


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] == "list":
        if PROPOSALS.exists():
            for line in PROPOSALS.read_text(encoding="utf-8").splitlines()[-40:]:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("title"):
                    print(d.get("at"), d.get("id"), d.get("risk"),
                          str(d.get("title"))[:70])
        return 0
    if args[0] == "submit" and len(args) > 1:
        prop = json.loads(pathlib.Path(args[1]).read_text(encoding="utf-8"))
        print(json.dumps(submit(prop), ensure_ascii=False)[:600])
        return 0
    print("usage: proposal_intake.py [list | submit <file.json>]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
