#!/usr/bin/env python3
"""R2 post-window closeout scanner — READ-ONLY. Steps 3/4/5 + B5 + W3G30 state."""
import json, hashlib, os, sys
from datetime import datetime, timedelta, timezone

RX = "/home/ari/ofn/state/ops-agent/state/ops-receipts.jsonl"
EXECUTED_DIR = "/home/ari/ofn/state/ops-agent/state/executed"
REQ_DIR = "/home/ari/ofn/state/ops-agent/state/canary-requests"
LIVE = "/home/ari/ofn/state/ops-agent/ops_agent.py"
TRIO_SHA = "a255c4c0deb380cdd6d2034671968c9737461798a4db4e857ea1122d9337ea51"

rows, malformed = [], 0
with open(RX, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            malformed += 1

def parse_at(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return None

now = datetime.now(timezone.utc).replace(microsecond=0)
out = {"scanned_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
       "total_rows": len(rows), "malformed_rows": malformed}

# --- STEP 3: budget recompute (rolling 24h OPS_B_EXECUTED) ---
execd = [r for r in rows if r.get("kind") == "OPS_B_EXECUTED"]
win = []
for r in execd:
    t = parse_at(r.get("at", ""))
    if t and (now - t) <= timedelta(hours=24):
        win.append((t, r))
win.sort(key=lambda x: x[0])
out["budget"] = {
    "rolling_24h_executed": len(win),
    "oldest": win[0][0].strftime("%Y-%m-%dT%H:%M:%SZ") if win else None,
    "next_rolling_release_estimate": (win[0][0] + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ") if win else None,
    "rows": [{"at": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
              "request": r.get("request", "<MISSING>"),
              "proposal_id": r.get("proposal_id", "<MISSING>"),
              "verified": r.get("verified", "<MISSING>"),
              "exit_code": r.get("exit_code", "<MISSING>")}
             for t, r in win],
}

# --- STEP 4: TRIO receipts ---
trio_rows = [r for r in rows if any(tok in json.dumps(r, default=str)
                                    for tok in ("TRIO-003", "a255c4c0", "SUCCESSOR-TRIO"))]
out["trio_rows"] = trio_rows
exp = os.path.join(EXECUTED_DIR, "native-Z-SUCCESSOR-TRIO-003.json")
out["trio_executed_file"] = {"exists": os.path.exists(exp)}
if os.path.exists(exp):
    with open(exp, "r", encoding="utf-8", errors="replace") as f:
        d = json.load(f)
    out["trio_executed_file"].update({"at": d.get("at"), "request": d.get("request", "<MISSING>"),
                                      "proposal_id": d.get("proposal_id", "<MISSING>"),
                                      "verified": d.get("verified", "<MISSING>"),
                                      "artifact_sha256": str(d.get("artifact_sha256", d.get("sha256", "<MISSING>")))[:70]})

# --- live sha + compile sanity ---
with open(LIVE, "rb") as f:
    live_bytes = f.read()
live_sha = hashlib.sha256(live_bytes).hexdigest()
compile_ok = True
try:
    compile(live_bytes.decode("utf-8", errors="replace"), "ops_agent.py", "exec")
except Exception as e:
    compile_ok = f"FAIL: {e}"
out["live"] = {"sha256": live_sha, "size": len(live_bytes), "compile_check": compile_ok,
               "equals_trio_artifact": live_sha == TRIO_SHA,
               "content_has_request_emit": ('"request"' in live_bytes.decode("utf-8", "replace") or "'request'" in live_bytes.decode("utf-8", "replace"))}

# --- STEP 5: FIX-B live proof — ALL post-reload EXECUTED receipts ---
reload_at = "2026-09-15T10:10:29"
post = []
for r in execd:
    a = r.get("at", "")
    if a >= reload_at:
        req = r.get("request", "")
        pid = r.get("proposal_id", "")
        art = str(r.get("artifact_sha256", r.get("sha256", "")))
        post.append({"at": a, "kind": r.get("kind"),
                     "request_present": bool(req), "request": req or "<MISSING>",
                     "proposal_id_present": bool(pid), "proposal_id": pid or "<MISSING>",
                     "identity_join_trio": ("TRIO-003" in (req or "") or "SUCCESSOR-TRIO" in (req or "") or art.startswith("a255c4c0"))})
out["fixb_post_reload_executed"] = post
out["fixb_live_proof"] = {
    "any_post_reload_executed": bool(post),
    "all_carry_request_and_proposal": bool(post) and all(p["request_present"] and p["proposal_id_present"] for p in post),
    "trio_receipt_identity_join": any(p["identity_join_trio"] for p in post),
}

# --- OPS_B_BLOCKED post F-NEW-3 deploy 21:46Z (request field check) ---
blocked_post = []
for r in rows:
    if r.get("kind") == "OPS_B_BLOCKED" and r.get("at", "") >= "2026-09-15T21:46":
        blocked_post.append({"at": r.get("at"), "request": r.get("request", "<MISSING>"),
                             "reason": str(r.get("reason", r.get("detail", "")))[:120]})
out["blocked_post_fnew3"] = blocked_post
out["fnew3_live_proof"] = {"status": "PENDING_FIRST_BLOCKED_EVENT" if not blocked_post else
                           ("PASS" if all(b["request"] != "<MISSING>" for b in blocked_post) else "FAIL"),
                           "blocked_rows_seen": len(blocked_post)}

# --- W3G30 state (NO bump run — verify only) ---
w3 = os.path.join(REQ_DIR, "native-W3G30-COMBINED-001.json")
out["w3g30"] = {}
if os.path.exists(w3):
    with open(w3, "r", encoding="utf-8", errors="replace") as f:
        d = json.load(f)
    deps = d.get("dependencies", [])
    out["w3g30"] = {"file_exists": True, "dependencies": deps,
                    "has_trio_dep": "native-Z-SUCCESSOR-TRIO-003.json" in deps,
                    "consumed": d.get("status", d.get("consumed", "<MISSING>")),
                    "sha256": hashlib.sha256(open(w3, "rb").read()).hexdigest()[:16]}
else:
    out["w3g30"] = {"file_exists": False}
w3_exec = os.path.join(EXECUTED_DIR, "native-W3G30-COMBINED-001.json")
out["w3g30"]["executed_file_exists"] = os.path.exists(w3_exec)
if os.path.exists(w3_exec):
    with open(w3_exec, "r", encoding="utf-8", errors="replace") as f:
        d = json.load(f)
    out["w3g30"]["executed_at"] = d.get("at")
    out["w3g30"]["executed_verified"] = d.get("verified", "<MISSING>")

# --- W3G30 + F-NEW-3 receipts (identity) ---
w3_rows = [r for r in rows if "W3G30" in json.dumps(r, default=str)]
out["w3g30_receipts_kinds"] = [{"at": r.get("at"), "kind": r.get("kind"),
                                "verified": r.get("verified", "<MISSING>"),
                                "request": r.get("request", "<MISSING>")} for r in w3_rows]
fnew3_rows = [r for r in rows if "F-NEW-3" in json.dumps(r, default=str) or "fnew3" in json.dumps(r, default=str).lower()]
out["fnew3_receipts"] = [{"at": r.get("at"), "kind": r.get("kind"),
                          "verified": r.get("verified", "<MISSING>"),
                          "artifact_sha256": str(r.get("artifact_sha256", r.get("sha256", "")))[:70],
                          "request": r.get("request", "<MISSING>")} for r in fnew3_rows]

# --- B5 breaker recompute (ow_9) ---
b5_rows = [r for r in rows if "B5" in json.dumps(r, default=str) and r.get("at", "") >= "2026-09-15T11:00"]
out["b5_recent"] = [{"at": r.get("at"), "kind": r.get("kind"),
                     "note": str(r.get("reason", r.get("detail", r.get("category", ""))))[:140]} for r in b5_rows[-12:]]

# --- queue state now ---
try:
    q = [fn for fn in os.listdir(REQ_DIR) if fn.endswith(".json")]
    out["queue_files_now"] = q
except Exception as e:
    out["queue_files_now"] = f"ERR {e}"

print(json.dumps(out, indent=1, default=str))
