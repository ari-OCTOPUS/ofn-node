# Fresh 15-minute homogeneous soak

`FRESH_SOAK_DURATION=15_MINUTES`  
`LONG_SOAK_REQUIRED=false`  
`LONG_TERM_STABILITY_PROVEN` must not be used.  
Success phrase: `SHORT_HOMOGENEOUS_SOAK_PASS`

Configuration:

- NEW_SKIN=true
- MEMORY_GATE=true
- GET_PURE=true
- LAN_TOKEN_REQUIRED=true
- EXTERNAL_LEARNING=false
- WAVE0_OBSERVE_ONLY=true
- PROPOSE_ONLY=true
- EXECUTABLE=false

Heartbeat interval is not changed to inflate sample count. Live interval is whatever `heartbeat_interval_s` already is (about 240–270s). Expected 3–4 heartbeats; minimum 3.

Previous soak is mixed-version and is closed, not overwritten.
