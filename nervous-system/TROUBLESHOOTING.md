# TROUBLESHOOTING · OCTOPUS Nervous System

> Common issues and how to fix them.

---

## "Panel shows empty / داده یافت نشد"

**Symptom**: A panel in `admin-telegram/index.html` shows red offline chip or "داده یافت نشد".

**Causes & Fixes**:

1. **Extractor not run**
   - Run `refresh-live-data.bat` or the specific extractor.
   - Example: `python extract_health_score.py`

2. **Source file missing**
   - Check the extractor's source path in its docstring.
   - Example: `extract_health_score.py` needs `_ops/state/ORGANISM-STATE.json`.

3. **JS variable name mismatch (schema drift)**
   - Open browser DevTools → Console.
   - Check if `window.HEALTH_DATA` (or relevant var) is defined.
   - Compare the extractor's output prefix (`window.X = ...`) with `index.html` line 274-278.

4. **File path wrong in HTML**
   - `admin-telegram/index.html` references `../../nervous-system/xxx-data.js`.
   - Ensure the file exists at that relative path.

---

## "Extractor fails with file not found"

**Symptom**: Running an extractor raises `FileNotFoundError`.

**Fixes**:

- Check that the source directory exists:
  - `4d_system/outputs/` → for `extract_live_data.py`
  - `_ops/state/` → for `extract_ops_data.py`, `extract_health_score.py`
  - `03 - Projects/Mining/` → for `extract_mining_data.py`
- If a project directory was moved/renamed, update the `Path` constant in the extractor.

---

## "JS variable not defined"

**Symptom**: Browser console shows `X is not defined` or `Cannot read properties of undefined`.

**Fixes**:

1. Check that the `<script src>` tag is present in `index.html` and loads before the inline script.
2. Check for JS syntax errors in the data file (e.g. unescaped quotes).
   - Known bug fixed in Wave 5: `git-data.js` panel had unescaped single quotes in `onclick`.
3. Verify the variable name matches between the `.js` file and the consumer:
   ```javascript
   // In data file
   window.GIT_DATA = {...};
   // In consumer
   const G = window.GIT_DATA || {};
   ```

---

## "preview.html too large"

**Symptom**: `preview.html` is ~1 MB and slow to load.

**Cause**: `preview.html` embeds `task-data.js` inline (677KB of task items).

**Fixes**:

- For daily use, open `admin-telegram/index.html` (loads live JS files, ~30KB total).
- `preview.html` is meant for **offline screenshot/distribution**.
- To generate a slim preview, replace inline `task-data.js` with `task-summary-data.js` (~1.5KB).
- The admin dashboard now loads `task-summary-data.js` by default and lazy-loads full `task-data.js` on demand.

---

## "Queue actions don't do anything"

**Symptom**: Clicking "تأیید" or "رد" in the Queue panel only shows a message.

**Expected**: This is **by design**. The system is in **SHADOW / PROPOSE-ONLY** mode.

**How it works**:
- `actOne()` and `actAll()` log a proposal but do NOT execute.
- Real execution requires:
  1. `approval_channel.py` wired to Telegram (currently `NotWiredStub`)
  2. Owner clicks ✅ in Telegram
  3. `ApprovalChannel.settle()` runs with human-verified approval

---

## "Task panel only shows summary, not full list"

**Expected**: This is **by design** (Wave 5 performance fix).

**To see full list**:
- Click **"📂 جزئیات کامل"** button in the Task Queue panel.
- This lazy-loads `task-data.js` (~678KB) on demand.
- If the button doesn't work, check browser console for network errors loading `../../nervous-system/task-data.js`.

---

## "refresh-live-data.bat hangs or runs forever"

**Causes**:

1. `extract_obsidian_tasks.py` scanning a very large vault.
   - Normal: 15-25 seconds for 1300+ files.
   - If longer, check for symlink loops or unexpected large `.md` files.
2. `extract_git_status_data.py` waiting on a repo with many untracked files.
   - Normal: 3-8 seconds.

**Fix**: Run extractors individually to identify the slow one.

---

## "Health score is 0 or unexpected"

**Cause**: `_ops/state/ORGANISM-STATE.json`, `fitness-latest.json`, or `telemetry-latest.json` missing or stale.

**Fix**: Ensure `_ops` heartbeat is running, then re-run `extract_health_score.py`.

---

## Encoding issues (Persian text shows as ???)

**Fix**:
- `refresh-live-data.bat` sets `chcp 65001` (UTF-8).
- All extractors open files with `encoding="utf-8"`.
- Ensure your terminal/editor is set to UTF-8.
