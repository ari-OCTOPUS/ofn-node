# PROPOSED PATCH v2.1 — make Telegram buttons EXECUTE (twice adversarially reviewed)

Reviewed by two adversarial workflows (wf_26797077-9d3 then wf_4cb7bcf2-b15). All confirmed defects fixed below with
inline `# FIX:` notes. Owner applies to F:\backup in the WORKTREE, runs `python -X utf8 _ops/run_all.py`, then flips the
flag. Additive + behind default-OFF `OCTOPUS_TG_EXEC` → byte-identical until you opt in.

## The gap (verified twice)
Buttons `doctor:run / consolidate:run / school:learn / ingest:crypto|acct` already EXIST (approval_channel.py:1370-1374,
buttons ~:1879-1884). Pressing routes `_dispatch_act → _run_act` (:1646); OOB verbs (:1383) only `_append_request`
(:1516) → `state/cockpit-requests.jsonl` (INV-7: never inline on the poll thread). **No consumer was ever built** →
that is the "read-only" bug. Fix = the missing beat-thread consumer.

## Verified-safe design decisions
- **Patch C (kill_check) DROPPED** — it wedges the poll thread (`while not self._killed()`, :367): a halt would make
  /panic EXIT the loop so /resume can never arrive. Poll thread must stay alive under halt. (See also Patch E — a
  *separate, pre-existing* halt gap the drop exposes.)
- **v1 safe verbs = doctor + consolidate ONLY.** school deferred (SensoryBus.ingest needs an `Observation`, not a dict);
  ingest excluded (ingest_raw.run overwrites .md notes in your vault project folders).
- Consumer honors STOP + HALT-ALL + **FREEZE**; first-activation fast-forward; truncation reset; AT-MOST-ONCE cursor;
  per-beat cap; complete-line-only advance; single-consumer lock; and **acks EVERY consumed button** (no dead buttons).

## Patch A — new consumer in `F:\backup\_ops\wiring.py` (near the other *_beat functions)
```python
# ── TG-EXEC (2026-07-15): on-demand consumer of the Telegram cockpit-requests queue. ──
_TG_EXEC_SAFE  = frozenset({"doctor", "consolidate"})                       # v1 executable set
_TG_EXEC_KNOWN = frozenset({"doctor", "consolidate", "school", "ideas", "ingest"})  # = OOB_VERBS (approval_channel.py:1383)
_TG_EXEC_MAX_PER_BEAT = 5

def _tg_ack(channel, text):
    if channel is None:
        return
    try: channel.send_text(text)
    except Exception: pass  # noqa: BLE001 — outbound fail must never abort the beat

def _tg_halt_reason():
    # FIX(freeze): honor the metabolic circuit-breaker too, not just STOP/HALT-ALL.
    if opslib.STOP_ORGANISM.exists(): return "STOP"
    h = opslib.halted()
    if h: return h
    if opslib.frozen(): return "FREEZE"
    return None

def cockpit_requests_beat(state_dir=None, doctor=None, channel=None) -> dict:
    import json as _json, os as _os, time as _time
    from pathlib import Path as _P
    if not flag("OCTOPUS_TG_EXEC"):
        return {"skipped": "flag-off"}                 # default OFF → byte-identical no-op
    if _tg_halt_reason():
        return {"skipped": "halt"}
    sd = _P(state_dir) if state_dir else (_HERE / "state")
    logp, curp, lockp = (sd / "cockpit-requests.jsonl",
                         sd / "cockpit-requests.cursor", sd / "cockpit-requests.lock")
    if not logp.exists():
        return {"skipped": "no-queue"}
    pid = _os.getpid()
    # FIX(split-brain): single-consumer advisory lock; fresh lock from another pid (<120s) → skip this beat.
    try:
        if lockp.exists():
            prev = (lockp.read_text(encoding="utf-8").strip() or ":")
            if prev.split(":")[0] not in ("", str(pid)) and (_time.time() - lockp.stat().st_mtime) < 120:
                return {"skipped": "locked-by-other"}
        lockp.write_text(f"{pid}:{opslib.now_iso()}", encoding="utf-8")
    except OSError:
        pass
    size = logp.stat().st_size
    # FIX(first-activation): no cursor → fast-forward to EOF, never replay the historical backlog.
    if not curp.exists():
        try: curp.write_text(str(size), encoding="utf-8")
        except OSError: pass
        return {"skipped": "first-activation-ffwd", "at": size}
    try:
        off = int(curp.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        off = 0
    # FIX(truncation): file shrank below cursor (full rotation) → reset + alert, else permanent blindness.
    if off > size:
        opslib.alert([f"tg-exec: cockpit-requests shrank ({off}>{size}) — cursor reset to 0"])
        off = 0
    try:
        with open(logp, "rb") as f:
            f.seek(off)
            chunk = f.read()
    except OSError:
        return {"skipped": "read-fail"}
    # FIX(partial-line): consume only up to the LAST complete newline; keep any tail for next beat.
    nl = chunk.rfind(b"\n")
    if nl < 0:
        return {"skipped": "no-complete-line"}
    # decode('replace') is safe here: reads are line-aligned (rfind \\n) and json.dumps emits valid UTF-8,
    # so no byte-length drift can occur; 'replace' keeps the queue progressing even on theoretical corruption.
    raw_lines = chunk[:nl + 1].decode("utf-8", "replace").splitlines(keepends=True)
    take = raw_lines[:_TG_EXEC_MAX_PER_BEAT]            # FIX(cap): bound blast radius per beat
    consumed = len("".join(take).encode("utf-8"))
    new_off = off + consumed
    # FIX(at-most-once): persist cursor BEFORE executing. Persist-fail → do NOT execute (a dropped command the owner
    # re-presses beats a duplicate doctor approval card / re-run). Verified byte-exact (Persian text round-trips).
    try:
        tmp = curp.with_suffix(".cursor.tmp")
        tmp.write_text(str(new_off), encoding="utf-8")
        _os.replace(tmp, curp)
    except OSError as e:
        opslib.alert([f"tg-exec: cursor persist FAILED ({type(e).__name__}) — skip beat, no exec"])
        return {"skipped": "cursor-persist-failed"}
    ran, failed, skipped = [], [], []
    for line in take:
        line = line.strip()
        if not line:
            continue
        try: req = _json.loads(line)
        except ValueError: continue
        if req.get("status") != "requested":
            continue
        verb, key = req.get("verb"), req.get("key")
        if verb not in _TG_EXEC_KNOWN:                 # non-cockpit line (defensive) → silent skip
            continue
        if _tg_halt_reason():                          # FIX(mid-loop halt/FREEZE): stop, and ACK so it's not "dead"
            _tg_ack(channel, f"⛔ «{verb}:{key}» اجرا نشد — سیستم در حالتِ توقف/انجماد. بعد از /resume دوباره بزن.")
            skipped.append(f"{verb}:{key}:halt")
            continue
        if verb not in _TG_EXEC_SAFE:                  # FIX(ack): recognized button, not enabled v1 → tell the owner
            _tg_ack(channel, f"⏸ «{verb}» در این نسخه اجرا نمی‌شود (فعّال: doctor، consolidate).")
            skipped.append(f"{verb}:{key}:not-enabled")
            continue
        try:
            res = _tg_exec_run_one(verb, key, doctor=doctor)   # "ran" | "not-wired"
            if res == "ran":
                ran.append(f"{verb}:{key}")
                _tg_ack(channel, f"✅ اجرا شد (تلگرام→بیت): {verb}:{key}")
            else:                                      # FIX(ack): recognized but subsystem not wired
                skipped.append(f"{verb}:{key}:not-wired")
                _tg_ack(channel, f"⚠️ «{verb}» وصل نیست (فلگِ زیرسیستم خاموش است).")
        except Exception as e:  # noqa: BLE001 — one bad verb must not kill the beat
            failed.append(f"{verb}:{key}:{type(e).__name__}")
            opslib.alert([f"tg-exec {verb}:{key} failed: {type(e).__name__}: {e}"])
            _tg_ack(channel, f"⚠️ اجرای {verb}:{key} خطا داد: {type(e).__name__}")
    return {"ran": ran, "failed": failed, "skipped": skipped}

def _tg_exec_run_one(verb, key, doctor=None) -> str:
    """Run ONE safe verb via its real entrypoint. OCTOPUS_TG_EXEC = the owner's explicit execute-consent, so this
    bypasses the paper-mode cadence wrappers — each verb keeps its own internal safety. Returns 'ran' | 'not-wired'."""
    import sys as _sys
    if verb == "consolidate" and key == "run":
        p = str(_HERE / "cortex")
        if p not in _sys.path: _sys.path.insert(0, p)
        import consolidate as _c
        _c.consolidate_once()      # SELF-gates on CORTEX_CONSOLIDATE → no-op (but 'ran') unless owner also set it. State-only.
        return "ran"
    if verb == "doctor" and key == "run":
        # doctor:run == what doctor_beat already runs periodically (organism.py:374) — NOT a new capability.
        # Propose-only RFC card to the OWNER (cost_usd=0). apply_merge caveat: see the doctor note below.
        d = doctor if doctor is not None else make_doctor(state_dir=str(opslib.STATE_DIR))
        if d is None:
            return "not-wired"
        d.run_cycle(beat=1_000_000)   # big beat → ignores cadence window
        return "ran"
    return "not-wired"
```

## Patch B — call it from the organism beat loop
`F:\backup\_ops\organism.py`, in `while True:`, right AFTER the consolidation_beat block (~line 384):
```python
            # ── TG-EXEC (2026-07-15): consume Telegram-queued on-demand verbs (flag-off default). ──
            if not _protective_skip:
                try:
                    _tgx = _w.cockpit_requests_beat(state_dir=str(opslib.STATE_DIR),
                                                    doctor=_doctor_inst, channel=_chan)
                    if _tgx.get("ran"):
                        opslib.heartbeat(f"tg-exec ran: {_tgx['ran']}")
                except Exception as _qe:  # noqa: BLE001 — §۴ non-fatal
                    opslib.alert([f"cockpit_requests_beat error (non-fatal): {type(_qe).__name__}"])
```

## Patch C — DROPPED. Do NOT inject kill_check (it kills /resume).

## Patch D — key-name ALIAS only (optional; never rename — would orphan the owner's existing SAKANA/ZAI keys)
`F:\backup\_ops\debate\client.py`: keep `env_key`, ADD `env_key_alias`, OR them at the read site (:253):
```python
#   'sakana': {... 'env_key':'SAKANA_API_KEY', 'env_key_alias':'FUGU_API_KEY' ...}
#   'glm':    {... 'env_key':'ZAI_API_KEY',    'env_key_alias':'GLM_API_KEY'  ...}
self.api_key = (os.environ.get(reg['env_key'])
                or os.environ.get(reg.get('env_key_alias', ''), '') or '')
```
Backward-compatible; only matters when the LiteLLM gateway (localhost:4000) is down. Never print a value.

## ⚠️ doctor + APPLY_MERGE (read before flipping the flag)
`OCTOPUS_WIRE_APPLY_MERGE` **defaults to "1" (ON)** in code (doctor.py:600). So doctor:run CAN apply an
already-**owner-approved** RFC merge. That apply is **state-only** (ledger NOTE + `knowledge/<rfc>-lesson.md`) — no
production mutation, no spend, no 3rd-party outbound — and it fires ONLY when a prior owner "merge-approved" verdict is
pending. It is also **identical to what doctor_beat already does periodically**, so the button adds no new capability.
If you want doctor strictly propose-only, **explicitly set `OCTOPUS_WIRE_APPLY_MERGE=0`** in `.env` (it is NOT off by
default).

## Patch E — SEPARATE, PRE-EXISTING halt gap (owner-gated; not introduced by this patch, but flagged honestly)
Dropping Patch C exposes a real pre-existing issue the review found: the poll thread's INLINE act verbs
(`flaggo`/`sweep`/`baseline`/`pf`/`export` in `_run_act`, approval_channel.py:1661-1694) gate only on `self._killed()`
(= `self._stop`), NOT on `opslib.halted()`. So under `/panic` (HALT-ALL) the still-alive poll thread could still run a
`flaggo` (config self-mod) or `baseline` (money-integrity) callback. `freezego`/`restartgo` are the safety controls and
should REMAIN allowed under halt; the mutating/config/money ones should be blocked. Proposed (owner sign-off — this is
halt-semantics): add to `_run_act`, for verbs in `{flaggo, sweep, baseline, pf, export}` only:
```python
        if verb in ("flaggo", "sweep", "baseline", "pf", "export") and (opslib.STOP_ORGANISM.exists() or opslib.halted()):
            return "⛔ زیرِ halt این عملیات اجرا نمی‌شود — اول /resume."
```
This is independent of the execute-buttons work; do it as its own reviewed change.

## The 409 (operational — no code)
Unified 4d bot already disabled (`…telegram_bot_unified.py.DISABLED-409-FIX`, 2026-07-12). Live 409 = **center.py via
RUN-TG-CENTER.bat** on the SAME token as the organism's approval_channel (verified organism/wiring/run_all don't import
center). → **Do not run RUN-TG-CENTER.bat** (nor the older `4d_system/brain/telegram_bot.py`, same token). One surface:
the organism's own poller.

## Apply order (owner)
1. WORKTREE (not live F:\backup): apply Patch A + B (optionally D; Patch E separately). `python -X utf8 _ops/run_all.py` → green.
2. Stop RUN-TG-CENTER.bat (kills the 409). Restart the organism (RUN-ORGANISM.bat).
3. `OCTOPUS_TG_EXEC` unset → nothing changes. When ready: set `OCTOPUS_TG_EXEC=1` in `.env`
   (+ `CORTEX_CONSOLIDATE=1` for /consolidate to do real work; set `OCTOPUS_WIRE_APPLY_MERGE=0` if you want doctor
   strictly propose-only). First beat after activation fast-forwards the queue (no backlog replay); press a button AFTER
   that → it runs next beat and you get a ✅/⚠️/⏸ reply.
