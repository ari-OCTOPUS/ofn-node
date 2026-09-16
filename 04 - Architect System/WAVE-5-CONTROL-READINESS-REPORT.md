---
title: "Wave 5 · Control-Readiness Assessment Report"
date: 2026-07-12
agent: D · Control-Readiness Agent
status: completed
scope: admin-telegram/index.html mode labels, system banner, action placeholders, control wiring documentation
---

# Wave 5 · Control-Readiness Assessment Report

## 1. Executive Summary

The OCTOPUS admin dashboard (`OCTOPUS/admin-telegram/index.html`) has been hardened with explicit **mode labels**, a **system-mode banner**, **safe action placeholders**, and **HTML comments** documenting what each action would do if wired to the live Telegram approval channel. No existing functionality was broken. All changes are additive and reversible.

**Overall System Mode:** `SHADOW / PROPOSE-ONLY` — all advisory, no execution.

---

## 2. Files Inspected

| File | What Was Inspected | Change? |
|------|-------------------|---------|
| `OCTOPUS/admin-telegram/index.html` | 13 panels, action buttons, data loading, rendering logic | **Modified** |
| `_ops/budget/approval_channel.py` | TelegramApprovalChannel, dispatch_callback, _do_approve, request_approval_card, NotWiredStub | No change (inspected only) |
| `_ops/state/pulse/telegram-poll.json` | Poll heartbeat timestamp | No change |
| `_ops/state/telegram_offset.json` | Offset persistence | No change |
| `nervous-system/queue-data.js` | Schema: `window.QUEUE_DATA` with `queue.items`, `queue.counts` | No change |
| `nervous-system/telegram-data.js` | Schema: `window.TELEGRAM_DATA` with `channel.live=false`, `channel.mode="stub(no-creds)"` | No change |
| `nervous-system/health-data.js` | Schema: `window.HEALTH_DATA` with `overall`, `subscores` | No change |

---

## 3. Changes Made

### 3.1 Mode Labels Added to All 13 Panels

Each panel now displays a colored mode badge in its header (`h2`).

| Panel | Mode Label | Rationale |
|-------|-----------|-----------|
| Vitals | `READ-ONLY` | Displays live organism data; no actions |
| Queue | `OWNER VERDICT REQUIRED` | Action buttons are propose-only; real execution requires owner approval via Telegram |
| Health | `READ-ONLY` | Composite score display; no actions |
| Neural | `READ-ONLY` | Rhythm/readiness display; no actions |
| Wallet | `SHADOW MODE` | Advisory governance display; no trades executed |
| Mining | `SHADOW MODE` | Advisory fleet monitor; no mining commands sent |
| Crypto | `SHADOW MODE` | Advisory market signals; ZERO live trades (EdgeClassifier unwired) |
| Research | `READ-ONLY` | Pipeline digest; no actions |
| Git Status | `READ-ONLY` | Branch/commit display; no actions |
| Task Queue | `READ-ONLY` | Counts/rates display; no actions |
| Ideas Backlog | `READ-ONLY` | Tier/strategy display; no actions |
| Project Index | `READ-ONLY` | Cards/health display; no actions |
| Telegram Control | `NOT YET WIRED` | Bot is stub (`live=false`, `mode="stub(no-creds)"`); approval channel = `NotWiredStub` |

### 3.2 System Mode Banner

Added a banner at the top of the page (`#sys-banner`) showing:
- **System mode:** `SHADOW / PROPOSE-ONLY` (computed from hardcoded state — can be made dynamic in Wave 6)
- **Last refresh:** computed from the freshest `generated` timestamp across all 15 loaded JS data sources, with age coloring (green < 45 min, gold < 2 h, red > 2 h)
- **Owner approval flag:** Always shows "نیاز به رأی" (red) because the system is in propose-only
- **Active channels:** count of successfully loaded data sources / 16 total channels

### 3.3 Safe Action Placeholders

The queue action buttons (`actOne`, `actAll`) now:
1. Log a clear Persian message to the log box explaining that no effect is executed
2. Inject a **visual red placeholder** (`action-placeholder`) below the queue with:
   - The action name and item ID
   - "نیاز به تأیید صاحب" in bold
   - A `why` sub-line explaining the T-2 wiring requirement
3. Auto-clear the placeholder after 5–8 seconds

**`actAll('approve')`** explicitly warns that batch-approve is **not implemented** (too risky) and each item must be approved individually.

### 3.4 Wired-Behavior Documentation (HTML Comments)

Before each panel and inside the action handler code, HTML/JavaScript comments document:
- What the panel displays and its data source
- What mode it operates in and why
- What the wired behavior would be if `TelegramApprovalChannel` were connected
- The exact callback flow: `app:approve:<id>:<token>` → `dispatch_callback` → `_do_approve` → `_on_human_judgment` → `gate.settle`

---

## 4. Control Wiring Assessment

### 4.1 Approval Channel (`approval_channel.py`)

**Current state:** `NotWiredStub` is active.

| Component | Status | Risk |
|-----------|--------|------|
| `TelegramApprovalChannel.wired` | `false` (no token / no owner_chat_id) | **None** — fail-closed by design |
| `poll_once()` | No-op safe return `0` | **None** |
| `request_approval_card()` | Returns `False` immediately | **None** |
| `_do_approve()` | Not reachable without wired channel | **None** |
| Token masking | `_mask_token()` limits to 4 chars | **None** |
| Redaction | `_redact()` strips secrets from messages | **None** |
| Offset persistence | Saved to `_ops/state/telegram_offset.json` | Low — file is local, no secrets |

### 4.2 Action Button → Execution Path Gap

The HTML action buttons (`actOne`, `actAll`) **do not** call any API. They are purely client-side JavaScript that:
1. Log text to a DOM element
2. Show a visual placeholder

There is **zero network path** from the dashboard to `approval_channel.py`. The dashboard is a static HTML file loading JSONP-style `.js` data files.

**To wire actions in a future wave, the following would be needed:**
- A lightweight HTTP endpoint (e.g., `panel/server.py` or a new `admin-api.py`) that accepts `{action, id, token}`
- The endpoint must validate the request (CSRF token, session, origin)
- The endpoint calls `approval_channel.request_approval_card()` — **not** `_do_approve()` directly
- The owner then receives a Telegram card and clicks ✅/❌
- Only then does `_do_approve` → `gate.settle` run

** NEVER wire `actOne` or `actAll` to call `_do_approve` directly. That would bypass the human-append layer and violate I7 + TINV-7.**

### 4.3 Data Integrity / Trust Boundary

The dashboard is **downstream read-only** of the extractors. All data files in `nervous-system/*.js` are:
- Generated by Python extractors running on the local machine
- Loaded as `<script>` tags (no fetch/XHR CORS issues)
- Not cryptographically signed, but the threat model assumes local filesystem access = owner access

**Risk:** If an attacker can write to `nervous-system/*.js`, they can spoof data. Mitigation: filesystem permissions + git monitoring.

---

## 5. Risk Register

| Risk | Level | Description | Mitigation |
|------|-------|-------------|------------|
| Silent action failure (user thinks approve worked) | **Low** (was Medium) | User clicks approve, nothing happens, no feedback | **Resolved:** placeholder now screams "نیاز به تأیید صاحب" |
| Batch-approve accidentally wired | **Low** | `actAll` could be connected to a real endpoint | **Resolved:** comment explicitly says NOT IMPLEMENTED; placeholder warns |
| Mode label drift (panel changes but label doesn't) | **Low** | Future dev adds actions but forgets to update label | HTML comment documents intended mode; grep-able |
| System banner shows stale data as fresh | **Low** | `generated` timestamp comes from extractor, not actual file mtime | Acceptable; extractor should update timestamp on each run |
| Telegram stub upgraded without updating label | **Low** | If creds added, `NOT YET WIRED` becomes wrong | Dashboard should read `TELEGRAM_DATA.channel.live` dynamically (future wave) |
| No CSRF protection on future API endpoint | **High** (future) | If an API is added later without tokens | Documented in 4.2; must be addressed before wiring |

---

## 6. Recommendations for Wave 6

1. **Dynamic mode detection:** Instead of hardcoded `SHADOW / PROPOSE-ONLY`, read `TELEGRAM_DATA.channel.live` and `TELEGRAM_DATA.channel.mode` to set the banner mode dynamically.
2. **API endpoint scaffolding:** Create `admin-api.py` (Flask/stdlib) with a single `/propose` endpoint that accepts `{panel, action, payload}` and returns `{proposed: true, approval_card_sent: false}` — still propose-only, but structured.
3. **Audit log panel:** Add a new panel showing the last 10 approval attempts (proposed vs approved vs denied) from a JSONL file written by `approval_channel.py`.
4. **Heartbeat wiring:** Wire the banner's "last refresh" to the actual `telegram-poll.json` pulse timestamp when Telegram goes live.
5. **Task summary lazy load:** Coordinate with Agent E to ensure `task-summary-data.js` loads correctly and the "جزئیات کامل" toggle works.

---

## 7. Verification Checklist

- [x] All 13 panels have mode labels
- [x] System banner renders with mode, freshness, owner flag, channel count
- [x] `actOne` shows visual placeholder + Persian explanation
- [x] `actAll` shows visual placeholder + warns batch is not implemented
- [x] `refresh` remains functional (page reload)
- [x] HTML comments document wired behavior for each panel
- [x] No existing rendering logic modified (only additions)
- [x] No network requests added
- [x] File validates as HTML5

---

## 8. Unknowns / Questions for Parent Agent

1. Should the system banner also show a "STOP file detected" warning if `_deploy/STOP.released-*` exists?
2. Should the queue panel hide action buttons entirely when `QUEUE_DATA.queue.items` is empty, or is the current empty-state message sufficient?
3. Is there a desire to add a "Propose to Telegram" button that actually calls a local API (still propose-only, but structured)?

---

*Report generated by D · Control-Readiness Agent · Wave 5 · 2026-07-12*
