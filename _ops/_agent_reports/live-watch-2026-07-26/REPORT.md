---
type: deliverable
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [telegram, live-observation, handoff]
created: 2026-07-26
updated: 2026-07-26
---

# Two hours of live Telegram observation — 2026-07-26, 12:43 → 14:41

Owner's instruction: *watch it live for two full hours, interact with me over
Telegram, record everything for the next agent, fix only safe bugs.*

60 samples at 2-minute intervals in `samples.jsonl`. Baseline in `baseline.json`.
Nothing here is inferred from a flag or a config file — every claim below has a
counter, a timestamp, or a file that moved.

---

## 1. What was proven to work

| Surface | Evidence |
|---|---|
| Centre bot receives | `centre_offset` **+25** across the window |
| Main bot receives | `main_offset` **+50** |
| Both bots send | **46** new rows in `tg-send-log.jsonl`, all `ok=True` |
| Group topic delivery | 5 test sends to topic 28, all accepted |
| Both DMs | 5 rounds × 2 DMs, all accepted |
| Δ_self evidence stream | `thesis/measurements.jsonl` **3 → 16** rows, steady |
| C6 card debt | stayed at **0** the whole window |

### The click fix is repeatable — this was the open question

`rfc_decision` held **zero rows for the entire history of the system** until today.

```
12:38:54   c6-32d7981f0d99   merge-approved   DECIDED
13:26:57   RFC-aa01e8ff      merge-approved   DECIDED
```

Two independent votes, 48 minutes apart, different RFC ids, one of them clearing
a proposal that had been stuck since 2026-07-25. The fix in `63e7c8f`
(a callback's actor is `cbq["from"]`, never `cbq["message"]["from"]`) is stable,
not a one-off.

**Do not treat "0 rows in rfc_decision" as an open mystery any more.** It was
this bug. It is closed and confirmed by effect.

---

## 2. A prediction I registered, and it was REFUTED

Written to the transcript at 13:25, before the outcome was observable:

> beat 13152, cadence every 60 → next multiple 13200 → `state/heart-wires-latest.json`
> must exist by ~14:13. If it does not, my wiring is wrong.

**It does not exist. The wiring was wrong.**

Root cause: I wrote the cadence as `beat % 60 == 0`. The beat counter advances
roughly once a minute, but the organism tick samples it on its own rhythm, so the
value the tick *sees* skips over the exact multiple. Measured: beat went 13180 →
13207, passing 13200, and no tick landed on it.

Simulated both forms over a 6-hour window:

| tick sampling | `% == 0` | last-run marker + `>=` |
|---|---|---|
| every beat | 6 | 6 |
| every 5 beats | 6 | 6 |
| every 7 beats, offset | **1** | **6** |

Modulo-equality against a counter whose sampling you do not control is a
condition that can silently never become true.

Fixed in `organism.py` to a durable last-run marker (`state/heart-wires-last.json`)
with `>=`. **NOT LIVE** — the organism booted 12:37:22, the edit is newer.

Note for whoever inherits this: `wiring.discovery_nudge_beat` already used the
correct form (`epoch = beat // every_n` plus a stored `last_epoch`). The repo knew
the answer; my new code did not follow it. Prefer that pattern.

---

## 3. The spam question — first real measurement

The premise "spam is the root cause" appeared in three consecutive agent reports.
None of them had counted anything. Now there is a number.

**56 sends · 46 unique · 10 duplicate groups · 17.9%**

But the raw percentage is misleading, and the breakdown is the finding:

| duplicate | gap | attribution |
|---|---|---|
| 465 chars ×2 | 2s | my own test (same body to two DMs) |
| 608 chars ×2 | 3s | my own test |
| 584 chars ×2 | 3s | my own test |
| others at 2–3s, `stream=center` | 2–3s | my own tests |
| 80 chars ×2 | 6s | **real** |
| 60 chars ×2 | 18s | **real** |
| 268 chars ×2 | 228s | **real** |
| 240 chars ×2 | 62min | **real** |
| **2447 chars ×2** | **3s** | **real — a large card sent twice** |

Five of my own test rounds each sent identical text to two DMs, which the counter
correctly flags as duplicates. Strip those and roughly **5 real duplicate groups
in two hours** remain.

**Conclusion: there is no spam flood.** The 12:45–12:53 burst (16 sends in 6
minutes) was conversation — variable lengths, each a reply to an owner message,
confirmed by `main_offset` moving in the same windows. What does exist is a
modest double-send pattern, mostly short replies repeating within 6–18 seconds,
plus one 2447-char card duplicated within 3 seconds. That last one is the only
duplicate worth chasing.

A dedup module was **not** built. On this evidence it would be solving a problem
that is not there. Re-measure with `python _ops/tg_send_log.py 24` after a full
day before deciding.

### Known bias in this number
`center.py` has been running since 11:36:41, which predates the commit that added
send-logging to `tg_api.send`. Centre-bot sends other than my direct test calls
are **undercounted**. The true total is higher; the duplicate ratio is unknown for
that slice. Not a clean zero — a known gap.

---

## 4. Owner interaction pattern

Ten windows where an offset moved: 12:45–12:53 (heavy), 13:27–13:29, 13:53–13:55,
14:09. Rounds 1, 2 and 4 drew responses; rounds 3 and 5 did not.

I could **not** read the content of any reply. `getUpdates` would 409 against both
live pollers and take the bots down, so every conclusion above is drawn from
effects — offsets, row counts, file mtimes — never from message text. If the next
agent needs message content, it needs an inbound log; none exists today.

---

## 5. Still unverified after two hours

- **`/id` in the 🧠 مغز topic.** Asked in rounds 2, 3, 4 and 5; never observed.
  Topic-reply is confirmed working in 🫀 قلب only (owner screenshot, 11:40). Whether
  it generalises to other topics is **untested**.
- **The "brain is busy" honest card.** `center.py` predates that commit, so the
  fallback still says "I don't understand" when the local LLM is inside its
  20-second window.
- **`heart_wires` beat.** Never ran; fix not live.
- **Five business topics** (ziman, mining, crypto, accounting, studio_pf) have no
  stream mapped and receive only the 24h digest. Gap against the approved
  allocation table; owner's call.

---

## 6. Bugs fixed during the window (owner authorised safe fixes)

1. **My own watcher was blind.** It called `wmic`, which Windows 11 removed, so
   `procs` was always `{}` — reporting "no processes" identically to "could not
   read". Switched to PowerShell; a read failure now returns `{"_error": ...}`
   explicitly. The first ~34 samples carry the empty value.
2. **The heart_wires cadence** (section 2).

Neither is live until the next restart.

---

## 7. What the next agent should do first

1. **Restart the organism.** Three code changes from today are on disk and not in
   the running process: the heart_wires cadence, the brain-busy card (needs
   `center.py` restarted specifically), and the tg_api send-log hook.
2. **Re-register the heart_wires prediction** after that restart: with the marker
   form it should fire within `CHRONO_HEART_WIRES_EVERY_N_BEATS` beats of boot.
   If it still does not, the fault is deeper than the cadence.
3. **Ask the owner for one `/id` inside a non-قلب topic.** It is a ten-second test
   and it is the last unverified path in the surface.
4. **Do not build dedup yet.** Get a 24-hour number first.

## 8. Method note

Two of my own measurements nearly became false bug reports in this window: a
mislabelled duplicate (I tagged a 2447-char double as my own test on a
length-and-gap heuristic, and I never sent that message), and earlier the local
LLM's rate limiter read as "the brain does not answer". Both were caught by
printing the actual value instead of trusting the classifier. The registered
prediction in section 2 is the only reason the cadence bug became a finding
rather than a shrug.
