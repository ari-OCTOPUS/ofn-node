# Rollback report

- Rollback used: `false`
- Rollback restart used: `false`
- Registry rollback used: `false`
- Capabilities quarantined: `[]`
- Failure evidence deleted: `false`
- Post-deploy cognitive data deleted: `false`

No abort condition occurred. The organism restarted once for deployment and remained PID `42687`; soak, llama.cpp, and gateway were not restarted.

The prepared rollback was registry `CANARY -> TESTED` with quarantine metadata, which would immediately disable further controlled-growth calls without deleting any event, episode, receipt, or self-model. Source rollback plus one separately counted rollback restart was reserved only for a deployment failure and was not needed.

ROLLBACK_STATUS: `NOT_USED`
