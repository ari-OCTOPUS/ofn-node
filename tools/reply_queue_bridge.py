"""reply_queue_bridge — پلِ پاسخ مغز → OWNER-QUEUE (gap: reply no reader).

وقتی مغز ۱۸۰ پاسخ semantic می‌دهد و reply-outbox آن را به ۱۳۸ می‌آورد،
این اسکریپت فایل‌های inbox را می‌خواند، proposal های مغز را استخراج و به
OWNER-QUEUE.md اضافه می‌کند — تا مالک در گلاس/تلگرام ببیندش.

فقط-خواندن از inbox · فقط-افزودن به OWNER-QUEUE · dedup با idempotency_key.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
try:
    import opslib
except ModuleNotFoundError:
    import types
    opslib = types.SimpleNamespace(STATE_DIR=Path.home() / "ofn" / "data" / "state")  # noqa: E402

SCHEMA = "octopus.reply-queue-bridge.v1"
INBOX = Path.home() / "octopus-mesh/inbox"
QUEUE = opslib.STATE_DIR / "OWNER-QUEUE.md"
SEEN_FILE = opslib.STATE_DIR / "reply-bridge-seen.json"
# Local queue append is not a send. Ready ≠ authorized.
grants_send = False
ready_is_authorized = False
promotes_ready_to_send = False


def _load_seen() -> set:
    try:
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _save_seen(seen: set) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(list(seen)[-500:]), encoding="utf-8")


def extract_proposals(inbox_dir: Path | None = None) -> list[dict]:
    """از inbox ۱۳۸، پاسخ‌های مغز با claim_type=proposal را استخراج کن."""
    inbox = inbox_dir or INBOX
    seen = _load_seen()
    proposals = []
    for f in sorted(inbox.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        idem = d.get("idempotency_key", "")
        if not idem or idem in seen:
            continue
        payload = d.get("payload", {})
        resp = payload.get("response", {}) if isinstance(payload, dict) else {}
        if resp.get("claim_type") != "proposal":
            continue
        proposals.append({
            "idempotency_key": idem,
            "businesses": payload.get("businesses", []),
            "confidence": resp.get("confidence", 0),
            "evidence": resp.get("evidence", []),
            "alternatives": resp.get("alternatives", []),
            "wake_id": next(
                (e for e in resp.get("evidence", []) if "wake_id" in e), ""),
        })
        seen.add(idem)
    _save_seen(seen)
    return proposals


def _queue_line(proposal: object) -> str | None:
    """Format one proposal or refuse it. Missing shape is skip, not write."""
    if not isinstance(proposal, dict):
        return None
    ev_raw = proposal.get("evidence")
    if not isinstance(ev_raw, list):
        return None
    try:
        conf = float(proposal.get("confidence", 0))
    except (TypeError, ValueError):
        return None
    ev = "; ".join(str(e)[:80] for e in ev_raw[:3])
    return f"- [{conf:.1f}] {ev}"


def append_to_queue(proposals: list[dict]) -> int:
    if not proposals:
        return 0
    written = [_queue_line(p) for p in proposals]
    lines = [line for line in written if line is not None]
    if not lines:
        return 0
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("a", encoding="utf-8") as f:
        f.write("\n".join(["", "## Brain Proposals (auto-appended)", *lines]) + "\n")
    return len(lines)


def run() -> dict:
    proposals = extract_proposals()
    n = append_to_queue(proposals)
    return {"schema": SCHEMA, "proposals_found": len(proposals),
            "appended": n}


def main() -> int:
    print(json.dumps(run(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
