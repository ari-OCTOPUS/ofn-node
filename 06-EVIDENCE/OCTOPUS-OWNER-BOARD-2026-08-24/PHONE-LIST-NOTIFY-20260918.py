#!/usr/bin/env python3
"""octopus-phone-list-notify — auto-send the phone-only lead list to the OWNER's Telegram.

Owner ruling 2026-09-18 (chat): DIDWW deferred ~1 week; until the call channel is live,
OCTOPUS itself pushes the phone-only lead list to owner Telegram automatically, so the
owner can call the leads personally. Owner-facing ONLY — this script never contacts a
customer and never touches the customer send path.

Design:
- dedup by sha256 of the remaining list: re-sends ONLY when the list changes
  (e.g. discovery_runner adds new phone-only leads) — no daily spam.
- DRY_RUN=1 prints instead of sending (paired test).
- state + log under state/revenue-drive/phone-list-notify/ (own dir; revenue-drive
  core files untouched).
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HOME = Path("/home/ari/ofn")
QUEUE = HOME / "state/revenue-drive/phone-only-queue.jsonl"
OUT = HOME / "state/revenue-drive/phone-list-notify"
STATE = OUT / "state.json"
LOG = OUT / "log.jsonl"
sys.path.insert(0, str(HOME))

MAX_LEN = 3500  # Telegram hard limit 4096; keep headroom for the title line


def load_rows():
    rows = []
    if QUEUE.exists():
        for line in QUEUE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            name = (d.get("business_name") or "").strip()
            phone = str(d.get("phone") or "").strip()
            if name and phone:
                rows.append((name, phone, (d.get("website") or "").strip()))
    return rows


def chunks_of(lines):
    out, cur = [], []
    n = 0
    for ln in lines:
        if n + len(ln) + 1 > MAX_LEN and cur:
            out.append("\n".join(cur))
            cur, n = [], 0
        cur.append(ln)
        n += len(ln) + 1
    if cur:
        out.append("\n".join(cur))
    return out


def main():
    dry = os.environ.get("DRY_RUN", "") in ("1", "true", "yes")
    rows = load_rows()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if not rows:
        print(json.dumps({"at": stamp, "why": "phone_only_queue_empty"}))
        return 0
    payload = "\n".join(f"{n}|{p}|{w}" for n, p, w in rows)
    sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        prev = json.loads(STATE.read_text(encoding="utf-8")).get("sha")
    except Exception:
        prev = None
    if prev == sha and not dry:
        print(json.dumps({"at": stamp, "why": "unchanged", "sha": sha[:12], "count": len(rows)}))
        return 0

    lines = [f"{name} — {phone}" + (f" ({web})" if web else "") for name, phone, web in rows]
    parts = chunks_of(lines)
    results = []
    from ofn.agents.owner_notify import send  # owner Telegram door only
    for i, part in enumerate(parts, 1):
        title = f"📞 OCTOPUS لیست تماس دستی — {len(rows)} لید فقط-تلفنی (بخش {i}/{len(parts)}) — {stamp[:10]}"
        body = f"{title}\n{part}\n(مسیر تماس DIDWW تا هفتهٔ بعد تعویق شد؛ زنگ بزن و نتیجه را بگو)"
        if dry:
            print(f"--- DRY chunk {i} chars={len(body)}")
            print(body[:400] + ("…" if len(body) > 400 else ""))
            results.append({"chunk": i, "dry": True, "chars": len(body)})
        else:
            r = send(body)
            results.append({"chunk": i, "ok": bool(r.get("ok")), "chars": len(body),
                            "errs": (r.get("errs") or [])[:2]})
            time.sleep(2)  # gentle on the Telegram API
    if not dry:
        STATE.write_text(json.dumps({"sha": sha, "at": stamp, "count": len(rows),
                                     "chunks": len(results)}, ensure_ascii=False) + "\n",
                         encoding="utf-8")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": stamp, "sha": sha[:16], "count": len(rows),
                                "results": results}, ensure_ascii=False) + "\n")
    print(json.dumps({"at": stamp, "sent_chunks": len(results), "count": len(rows),
                      "ok": all(x.get("ok", x.get("dry")) for x in results)}, ensure_ascii=False))
    return 0 if all(x.get("ok", x.get("dry")) for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
