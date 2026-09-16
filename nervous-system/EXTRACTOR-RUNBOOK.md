# EXTRACTOR RUNBOOK · OCTOPUS Nervous System

> How the 17 extractors work, how to add one, and how to debug them.

## Quick Reference

| # | Extractor | Output | Size | Source | Panel |
|---|-----------|--------|------|--------|-------|
| 1 | `extract_live_data.py` | `live-data.js` | ~140KB | `4d_system/outputs` | Vitals |
| 2 | `extract_ops_data.py` | `ops-data.js` | ~1KB | `_ops/state` | Vitals (wires) |
| 3 | `extract_graph.py` | `graph-data.js` | ~108KB | Vault markdown | Ontology |
| 4 | `extract_audit_data.py` | `audit-data.js` | ~11KB | `_ops/audit` | Audit |
| 5 | `extract_health_score.py` | `health-data.js` | ~1KB | `_ops/state` | Health |
| 6 | `extract_neural_data.py` | `neural-data.js` | ~2KB | `_ops/neural` | Neural |
| 7 | `extract_watchdog_data.py` | `watchdog-data.js` | ~15KB | `_ops/governor` | Watchdog |
| 8 | `extract_queue_data.py` | `queue-data.js` | ~0.3KB | `_ops/state` | Queue |
| 9 | `extract_research_data.py` | `research-data.js` | ~4KB | `00 - Inbox/scout-digests` | Research |
| 10 | `extract_git_status_data.py` | `git-data.js` | ~5KB | `.git/` repos | Git |
| 11 | `extract_wallet_data.py` | `wallet-data.js` | ~2KB | `03 - Projects/Crypto - etoro` | Wallet |
| 12 | `extract_mining_data.py` | `mining-data.js` | ~7KB | `03 - Projects/Mining` | Mining |
| 13 | `extract_crypto_data.py` | `crypto-data.js` | ~4KB | `03 - Projects/Crypto - etoro` | Crypto |
| 14 | `extract_project_index.py` | `project-data.js` | ~4KB | `03 - Projects/` | Projects |
| 15 | `extract_ideas_backlog.py` | `ideas-data.js` | ~84KB | `00 - Inbox/` | Ideas |
| 16 | `extract_telegram_control.py` | `telegram-data.js` | ~2KB | `_ops/state/telegram` | Telegram |
| 17 | `extract_obsidian_tasks.py` | `task-data.js` | ~678KB | Vault `.md` files | Tasks |
| 18 | `extract_task_summary.py` | `task-summary-data.js` | ~1.5KB | `task-data.js` (derived) | Tasks (light) |

## How to Run Extractors

### All at once
```batch
refresh-live-data.bat
```

### Individual extractor
```batch
cd F:\backup\nervous-system
python extract_health_score.py
```

> **Note:** On Windows Git Bash, use `py` or full path to Python if `python` is not in PATH.

## Schema Convention

Every extractor emits a single JS variable assignment:

```javascript
window.VAR_NAME = {"generated": "2026-07-12T...Z", ...};
```

- `generated` is ISO-8601 UTC timestamp.
- Variable names are `SCREAMING_SNAKE_CASE`.
- Consumers use `window.VAR_NAME || {}` for fail-soft.

## How to Add a New Extractor

1. **Name it**: `extract_<domain>_<thing>.py`
2. **Read-only**: Only read source files; never mutate.
3. **Fail-soft**: If source missing, emit empty/minimal payload, not crash.
4. **Output**: Write to `F:/backup/nervous-system/<thing>-data.js`
5. **Register**: Add to `refresh-live-data.bat` in dependency order.
6. **Wire UI**: Add `<script src="...">` to `admin-telegram/index.html` and destructure in the IIFE.
7. **Document**: Add a row to the table above and to the panel map.

### Minimal extractor template

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os
from datetime import datetime, timezone

NS_DIR = "F:/backup/nervous-system"

def main():
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {"generated": generated, "my_field": 42}
    js = "window.MY_DATA = " + json.dumps(data, ensure_ascii=False, default=str) + ";\n"
    with open(os.path.join(NS_DIR, "my-data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print("my-data.js refreshed", len(js), "chars")

if __name__ == "__main__":
    main()
```

## Dependencies Between Extractors

```
Group A (core):     live, ops, graph, audit, health, neural, watchdog
Group B (channels): queue, research, git, wallet, mining, crypto, project, ideas, telegram
Group C (derived):  obsidian_tasks → task_summary
```

`extract_task_summary.py` **must** run after `extract_obsidian_tasks.py` because it reads `task-data.js`.

## Approximate Runtime

- `extract_obsidian_tasks.py`: ~15-25s (scans 1300+ markdown files)
- `extract_graph.py`: ~5-10s (parses vault graph)
- `extract_git_status_data.py`: ~3-8s (runs git in multiple repos)
- All others: <2s each
- **Total**: ~20-40s

## Debugging a Failing Extractor

1. **Run it individually** and read stderr.
2. **Check source file exists**: Most extractors fail softly, but some expect specific paths.
3. **Validate output JSON**: Load the `.js` file in a browser console or run:
   ```python
   import json
   text = open("live-data.js").read().split("= ", 1)[1].rstrip(";\n")
   json.loads(text)
   ```
4. **Check schema drift**: Ensure `window.VAR_NAME` matches what `index.html` destructures.
5. **Check encoding**: All extractors use UTF-8; batch file sets `chcp 65001`.
