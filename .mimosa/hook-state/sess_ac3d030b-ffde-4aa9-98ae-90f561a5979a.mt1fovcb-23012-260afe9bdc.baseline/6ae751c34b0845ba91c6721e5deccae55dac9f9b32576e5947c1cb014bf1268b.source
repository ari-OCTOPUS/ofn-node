"""
daemon.py — میزبانِ کرنل به‌صورت یک process جدا.
پروتکل: هر خطِ stdin یک JSON request، هر خطِ stdout یک JSON response.
فقط verbهای زیر مجازند؛ هیچ verbـی برای تغییرِ کلید یا invariant وجود ندارد.
اجرا:  python daemon.py <state_dir>
"""
from __future__ import annotations
import sys, os, json, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel import Kernel, CANON

VERBS = {"audit", "verify", "permit", "consume", "ground", "canon", "ping", "status"}


def main():
    state_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "igk_state")
    stop_path = sys.argv[2] if len(sys.argv) > 2 else None
    k = Kernel(state_dir, stop_path=stop_path)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            verb = req.get("verb")
            if verb not in VERBS:
                resp = {"ok": False, "reason": f"verb غیرمجاز: {verb}"}
            elif verb == "ping":
                resp = {"ok": True, "pong": True}
            elif verb == "status":
                resp = {"ok": True, "stopped": k.stopped()}
            elif verb == "canon":
                resp = {"ok": True, "canon": CANON}
            elif verb == "audit":
                resp = k.audit(req["event"], req.get("actor", "?"), req.get("data", {}))
            elif verb == "verify":
                resp = k.verify()
            elif verb == "permit":
                resp = k.permit(req["action"], req.get("actor", "?"))
            elif verb == "consume":
                resp = k.consume(req["token"])
            elif verb == "ground":
                resp = k.ground(req.get("claims", []), req.get("actor", "?"))
        except Exception as e:
            resp = {"ok": False, "reason": f"خطای کرنل: {e}"}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
