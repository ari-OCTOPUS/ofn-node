#!/usr/bin/env python3
"""funnel_reconcile.py — WHY-SLOW-250 F6: ONE authoritative funnel number.

Read-only. Recomputes funnel counts from the packet store (single source of
truth = quote-packets/*.json send_status + sent-log.jsonl) and prints the diff
against the three parallel counters that disagreed on 2026-09-18
(revenue-state.counts / season-meter / sent-log rows). Writes nothing.
"""
import collections
import glob
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent


def main():
    # packet store = authoritative per-packet state
    st = collections.Counter()
    for f in glob.glob(str(ROOT / "quote-packets" / "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except ValueError:
            st["UNPARSEABLE"] += 1
            continue
        st[str(d.get("send_status", "UNKNOWN"))] += 1
    packets_on_disk = sum(st.values())

    kinds = collections.Counter()
    for line in (ROOT / "sent-log.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            kinds[str(json.loads(line).get("kind", "packet"))] += 1
        except ValueError:
            kinds["UNPARSEABLE"] += 1
    sent_rows = sum(kinds.values())

    rs = json.loads((ROOT / "revenue-state.json").read_text(encoding="utf-8"))
    meter = json.loads((ROOT / "season-meter.json").read_text(encoding="utf-8"))
    rs_counts = rs.get("counts", {})

    print("AUTHORITATIVE (packet store):")
    print("  packets_on_disk   = %d" % packets_on_disk)
    for k, v in sorted(st.items(), key=lambda x: -x[1]):
        print("    send_status=%-18s %d" % (k, v))
    print("  sent_log_rows     = %d  %s" % (sent_rows, dict(kinds)))
    print("PARALLEL COUNTERS (now comparable, same unit = packet):")
    print("  revenue-state.counts        = %s" % json.dumps(rs_counts, sort_keys=True))
    print("  season-meter staged/sent    = %s / %s" % (
        meter.get("staged_packets"), meter.get("packets_in_sent_state")))
    print("DIFF NOTE:")
    print("  sent_log counts MESSAGES (packet+quote+followup_1+reply_1);")
    print("  packet store counts PACKETS by last known send_status.")
    print("  published authoritative SENT = %d packets" % st.get("sent", st.get("SENT", 0)))


if __name__ == "__main__":
    main()
