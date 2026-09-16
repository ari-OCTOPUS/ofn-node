# Failure model

| Failure | Slice behavior |
|---|---|
| Empty HRV after restart | WARMUP global; gate SHADOW max |
| Dual period same beat | CONFLICTING; telemetry UNKNOWN; gate BLOCK |
| Future observation | FUTURE_DATA excluded; BLOCK flags |
| latest.json as history | UNLOCATED |
| Identity missing | UNKNOWN; not 0.672 improvement |
| C-042 tokens=0 | AMBER life_currency + contradiction visible |
| Live C-044 empty reasons | Slice still emits non-empty reasons; live arbiter not patched |
| credits_to_aud | not imported; unit life_credit only |
| Policy/planner import | AST test fail |
| executable True | traverse test fail |
| Auto-delete evidence | OFF |
