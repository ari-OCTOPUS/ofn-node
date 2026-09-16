# SERVICE LIVENESS vs READINESS — A02 Runtime Investigator

Liveness = process up / port listening (T0). Readiness = evidence the service is actually doing its job (fresh state writes, fresh receipts). Observation time ≈ 23:44–23:59 +10:00.

| Service | Liveness (T0) | Readiness evidence | Readiness verdict | Gap |
|---------|---------------|--------------------|-------------------|-----|
| organism (8771/8777, PID 29028) | LISTENING; beat advancing | `ORGANISM-STATE.json` rewritten every beat (beat 38511→38516 observed); `chrono.db-wal` fresh to the minute; hourly `HEARTBEAT.md` line 23:06:44 "organism=ok" | **READY** | none — healthiest component |
| cortex (8772, PID 11144) | LISTENING | `state/cortex-watchdog.json` `{"status":"alive","last_check":1786888444}` (23:54:04); `deep-synth.jsonl` 02:30 | READY (watchdog-attested) | last deep-synth 21 h old — thinking cadence not independently confirmed this window |
| live cockpit (8773, PID 7852) | LISTENING | live-watchdog last ran 23:53:01 (revives if dead) | READY (watchdog-attested) | readiness is watchdog-liveness, not a cockpit-native heartbeat |
| tg-center (8776, PID 11724) | LISTENING | `pulse/tg-center.json` 23:54:49 (pid matches); `pulse/telegram-poll.json` 23:54:56 batch=0; `channel-status.json` telegram live=true 23:51:09 | **READY** (poll loop alive) | `telegram_offset.json` mtime 08-15 18:19 (older artifact — offset may live elsewhere; minor) |
| miniapp gateway (8774, PID 19076) | LISTENING | tunnel URL file alive (kind=named, started 2026-08-15T20:58:11Z, keepalive touches it); cloudflared PID matches | READY | public exposure is part of design (F-03); registration on Telegram side unverifiable from here (A03) |
| board_cp (8801, PID 23464) | LISTENING (0.0.0.0, TLS) | `board_cp/commands.sqlite` last write 19:05; `board-status.txt` (source=ofn/heartbeat) 23:00:52, beat 601, `svc_octopus_bridge=active` | PARTIAL | board-status **53 min stale** at snapshot; no evidence of board pulls in hours — bridge may be idle or wedged (F-29) |
| event bus (no process) | n/a (in-process) | `events.jsonl` last event 23:11:07 (memory-consolidate task.completed) | **DEGRADED observability** | 45+ min silent while organism healthy — no "bus last-event age" readiness signal exists (F-21) |
| 4d consolidation / poisoning watch | schtask-driven | last runs 23:49:01 / 22:08:10 | READY | non-resident by design |
| NBB observatory | schtask-driven | last runs 23:36:28 / 23:06:01 | READY | runs from Desktop copy outside repo (F-02) |
| `_octopus` legacy control-plane | no process | `approvals.json`/`audit.log` latest 12:35:57 (approvals still landing); `octopus_state.json` status block frozen at 2026-07-18 | STALE-but-partly-active | status fields contradict actual activity; two approval systems coexist (F-28, A03 question) |

## Liveness-vs-readiness gaps worth owner attention

1. **board bridge staleness**: board-status.txt 53 min old while `svc_octopus_bridge` claims "active" — the bridge reports its own state, not its freshness.
2. **events.jsonl silence**: healthy organism, quiet bus — readiness signals conflate process liveness with pipeline activity.
3. **Watchdog-attested readiness**: for cortex/live, "ready" really means "watchdog says alive"; the watchdogs themselves are the single source (they both detect and revive — self-healing, but also the reason drift/liveness issues can be masked by auto-restart loops).
4. **identities-latest.json** last write 12:33 (11 h) while `math-control-latest.json` carries fresh identity values each beat — two writers, one cadence much slower; dashboards reading the wrong file would look stale.
