import hashlib, json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"F:/backup")
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-REMEMBER-CORRECT-PROVE-2026-08-23"
MEM = ROOT / "research" / "full_loop" / "state" / "memory.jsonl"
SYD = timezone(timedelta(hours=10))
now_local = datetime.now(SYD).isoformat(timespec="seconds")

def sha(p: Path):
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

lines = [ln for ln in MEM.read_text(encoding="utf-8").splitlines() if ln.strip()]
rows = [json.loads(ln) for ln in lines]
ids = [r["id"] for r in rows]
prove_ids = [i for i in ids if i.startswith("mem-") and any(t in json.dumps(r, ensure_ascii=False) for t in ("prove-canary", "OCTOPUS-REMEMBER-PROVE") for r in rows if r["id"]==i)]
# simpler prove ids from text
prove_ids = [r["id"] for r in rows if "prove-canary" in str(r.get("text")) or "OCTOPUS-REMEMBER-PROVE" in str(r.get("text"))]

iso_ob = sorted((EVID / "isolated-loop" / "telegram" / "loop" / "outbox").glob("*.json"), key=lambda p: p.stat().st_mtime)[-1]
iso_ev = sorted((EVID / "isolated-loop" / "telegram" / "loop" / "events").glob("*.json"), key=lambda p: p.stat().st_mtime)[-1]
ob = json.loads(iso_ob.read_text(encoding="utf-8"))
ev = json.loads(iso_ev.read_text(encoding="utf-8"))
live_dry_ob = ROOT / "_ops/state/telegram/loop/outbox/prove-remember-correct-6ab24aa1.json"
live_dry_ev = ROOT / "_ops/state/telegram/loop/events/prove-remember-correct-6ab24aa1.json"
lock = json.loads((ROOT / "_ops/state/locks/octopus-writer.lock").read_text(encoding="utf-8"))
rs = {}
rsp = EVID / "receipts-summary.json"
if rsp.exists():
    try:
        rs = json.loads(rsp.read_text(encoding="utf-8"))
    except Exception:
        rs = {}

result = {
  "schema": "octopus-remember-correct-prove/1",
  "status": "PARTIAL",
  "captured_at_local": now_local,
  "branch": "rescue/octopus-live-tree-20260821",
  "head": "d07c9ad",
  "center_pid": 35916,
  "center_alive": True,
  "ACTION_COMPLETED": [
    "renew_writer_lock grok-ari-single-writer",
    "handle_local /remember -> LIVE memory.jsonl",
    "handle_local /correct invalid -> local-correct-invalid",
    "isolated durable_loop.ack_local_result CONFIRMED/CLOSED",
    "live-loop dry-run prove-* markers (no sendMessage)",
    "A18 blocker note under evidence + DISCOVER",
  ],
  "COMMIT_WORKTREE": {
    "commit": None,
    "patch": None,
    "reason": "No code gap requiring patch; ACK + invalid-correct already in local_commands.py @ HEAD",
  },
  "EVIDENCE": str(EVID),
  "hashes_counts": {
    "memory_lines_after": len(lines),
    "memory_sha256_after": sha(MEM),
    "memory_bytes_after": MEM.stat().st_size,
    "prove_memory_ids": prove_ids,
  },
  "receipt_paths": {
    "memory_store": str(MEM),
    "isolated_outbox": str(iso_ob),
    "isolated_event": str(iso_ev),
    "live_dry_run_outbox": str(live_dry_ob) if live_dry_ob.exists() else None,
    "live_dry_run_event": str(live_dry_ev) if live_dry_ev.exists() else None,
    "receipts_summary": str(rsp),
    "a18_note": str(EVID / "A18-BLOCKER-NOTE.md"),
  },
  "receipts": {
    "local_remember": "local-remember",
    "local_correct_invalid": "local-correct-invalid",
    "isolated_outbox_state": ob.get("state"),
    "isolated_delivery_truth": ob.get("delivery_truth"),
    "isolated_event_state": ev.get("state"),
    "isolated_readback_verified": ev.get("readback_verified"),
    "live_dry_run_outbox_state": (json.loads(live_dry_ob.read_text(encoding="utf-8")).get("state") if live_dry_ob.exists() else None),
    "prior_receipts_summary_note": "see receipts-summary.json for first canary mem-3710e669de79",
  },
  "lock": {
    "agent_id": lock.get("agent_id"),
    "session_id": lock.get("session_id"),
    "expires_at": lock.get("expires_at"),
    "renewed_at_local": lock.get("renewed_at_local"),
    "expired_now": time.time() > float(lock.get("expires_at") or 0),
  },
  "BLOCKERS": [
    {
      "id": "A18-LIVE-TELEGRAM-OWNER-ACK",
      "severity": "partial",
      "detail": "Local persistence + isolated durable CONFIRMED/CLOSED proven. Fresh LIVE center PID 35916 outbox/events for owner Telegram /remember still needs owner-chat inbound (no TELEGRAM_OWNER_CHAT_ID in agent shell; lease forbids live sendMessage).",
    }
  ],
  "NEXT_ACTION": {
    "id": "A18-OWNER-TG-REMEMBER-CANARY",
    "reversible": True,
    "step": "Owner sends one /remember and one /correct <bad-id> in owner chat only; verify new LIVE outbox CONFIRMED + events CLOSED; then update CURRENT-TRUTH A18 if proven.",
  },
  "no_process_restart": True,
  "no_deletes": True,
  "no_secrets_in_evidence": True,
}
(EVID / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
note = """# A18 blocker note — 2026-08-23 (Australia/Sydney)

## STATUS
PARTIAL. Local /remember + /correct-invalid + isolated durable ACK proven. A18 Full Loop / LIVE-B still blocked for live Telegram owner re-verify only.

## PASSED
- handle_local /remember → local-remember + memory_id ACK in text + LIVE memory.jsonl append
- handle_local /correct invalid-id → local-correct-invalid (no bogus write)
- isolated durable_loop.ack_local_result (fake transport) → outbox CONFIRMED + event CLOSED + readback_verified
- Center PID 35916 not restarted; no deletes; no live sendMessage
- Writer lock renewed as grok-ari-single-writer

## STILL BLOCKS TRUTH-DOC UNLOCK
- No center-produced LIVE CONFIRMED row for this canary (needs owner Telegram inbound)
- Agent shell lacks TELEGRAM_OWNER_CHAT_ID; lease forbids live sendMessage

## NEXT (nearest reversible)
Owner sends /remember and /correct <bad-id> in owner chat → verify LIVE outbox/events → update CURRENT-TRUTH A18 if PASS.

## EVIDENCE
06-EVIDENCE/OCTOPUS-REMEMBER-CORRECT-PROVE-2026-08-23/RESULT.json
"""
(EVID / "A18-BLOCKER-NOTE.md").write_text(note, encoding="utf-8")
disc = ROOT / "06-EVIDENCE" / "OCTOPUS-CONTINUOUS-DISCOVER-2026-08-23"
disc.mkdir(parents=True, exist_ok=True)
(disc / "A18-BLOCKER-NOTE.md").write_text(note, encoding="utf-8")
print(json.dumps({
  "status": result["status"],
  "memory_lines": len(lines),
  "prove_ids": prove_ids,
  "iso_state": ob.get("state"),
  "ev_state": ev.get("state"),
  "lock_expired": result["lock"]["expired_now"],
}, ensure_ascii=False))
