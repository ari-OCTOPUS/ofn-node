#!/bin/bash
set -euo pipefail
EV=/home/ari/ofn/06-EVIDENCE/runtime-provenance-20260828T230743Z

curl -sS -o /tmp/v2-version.body -w '%{http_code}' \
  -H 'Host: panel.master-painting.com' \
  http://127.0.0.1:8794/api/v2/owner/version | tee "$EV/v2-version-http.txt"
echo
python3 - <<'PY'
import json
from pathlib import Path
raw = Path("/tmp/v2-version.body").read_text(encoding="utf-8", errors="replace")
print("version_bytes", len(raw))
d = json.loads(raw)
print("top_keys", list(d.keys())[:24])
print("status", d.get("status"))
data = d.get("data")
if isinstance(data, dict):
    safe = {k: data.get(k) for k in list(data)[:20]}
    print("data_keys", list(data.keys())[:20])
    print("data_preview", safe)
PY
cp /tmp/v2-version.body "$EV/v2-version.body.json"

curl -sS -o /tmp/v2-queue.body -w '%{http_code}' \
  -H 'Host: panel.master-painting.com' \
  http://127.0.0.1:8794/api/v2/owner/queue | tee "$EV/v2-queue-http.txt"
echo
python3 - <<'PY'
import json
from pathlib import Path
raw = Path("/tmp/v2-queue.body").read_text(encoding="utf-8", errors="replace")
print("queue_bytes", len(raw))
d = json.loads(raw)
print("top_keys", list(d.keys())[:24])
print("status", d.get("status"))
data = d.get("data")
print("data_type", type(data).__name__)
items = []
if isinstance(data, list):
    items = data
elif isinstance(data, dict):
    print("data_keys", list(data.keys())[:20])
    for k in ("items", "rows", "queue"):
        if isinstance(data.get(k), list):
            items = data[k]
            print("items_key", k)
            break
print("n_items", len(items))
for it in items[:12]:
    if not isinstance(it, dict):
        print("row_non_dict", type(it).__name__)
        continue
    print({k: it.get(k) for k in (
        "id", "queue", "state", "message_type", "run_id", "created_at", "truth"
    )})
Path("/tmp/v2-queue-ids.txt").write_text(
    "\n".join(str((it or {}).get("id")) for it in items if isinstance(it, dict)),
    encoding="utf-8",
)
PY
cp /tmp/v2-queue.body "$EV/v2-queue.body.json"

sqlite3 -readonly /home/ari/.local/share/ofn/outbox.sqlite \
  'SELECT status, count(*) FROM outbox GROUP BY status;' \
  | tee "$EV/outbox-status-counts.txt"

sqlite3 -readonly /home/ari/.local/share/ofn/outbox.sqlite \
  'SELECT idem_key, status, substr(created_at,1,19) FROM outbox ORDER BY created_at DESC LIMIT 20;' \
  | tee "$EV/outbox-recent-ids.txt"
