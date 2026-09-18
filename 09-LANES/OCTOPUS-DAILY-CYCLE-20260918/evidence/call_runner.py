#!/usr/bin/env python3
"""Call runner — the SYSTEM places the calls (owner 2026-09-18).
Armed now, inert until call-channel.json carries a number. Honours SEND-PAUSED,
one receipt per attempt, never calls the same business twice."""
import json
import pathlib
import subprocess
import time

RD = pathlib.Path(__file__).resolve().parent
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rcp(kind, **kw):
    row = {"schema": "octopus.call-runner.v1", "at": NOW, "kind": kind, **kw}
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + chr(10))


def main():
    ch = json.loads((RD / "call-channel.json").read_text(encoding="utf-8"))
    if not ch.get("number"):
        rcp("CALL_SKIPPED", why="no_number_yet", provider=ch.get("provider"))
        print(json.dumps({"at": NOW, "placed": 0, "why": "no_number_yet"}))
        return
    if (RD / "SEND-PAUSED").exists():
        rcp("CALL_SKIPPED", why="paused")
        return
    st_path = RD / "call-state.json"
    st = json.loads(st_path.read_text()) if st_path.exists() else {}
    q = [json.loads(l) for l in (RD / "phone-only-queue.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    done = 0
    for row in q[:20]:
        name = str(row.get("business_name"))
        phone = str(row.get("phone") or row.get("number") or "")
        if not phone or name in st:
            continue
        payload = {"from": ch["number"], "to": phone, "script": "painting-quote-intro"}
        args = ["curl", "-s", "-X", "POST", ch.get("api_url") or "https://api.didww.com/v3/calls",
                "-H", "Content-Type: application/json", "-d", json.dumps(payload)]
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=60)
            ok = r.returncode == 0 and "error" not in (r.stdout or "").lower()
            st[name] = {"at": NOW, "ok": ok, "detail": (r.stdout or r.stderr or "")[:200]}
            rcp("CALL_PLACED" if ok else "CALL_FAILED", business=name, ok=ok)
            done += 1
        except Exception as exc:  # noqa: BLE001
            rcp("CALL_FAILED", business=name, why=type(exc).__name__)
    st_path.write_text(json.dumps(st, indent=1), encoding="utf-8")
    print(json.dumps({"at": NOW, "placed": done}))


if __name__ == "__main__":
    main()
