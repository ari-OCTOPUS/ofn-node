# TDR: SSE (Server-Sent Events)
candidate: SSE
observed_problem: "model path (DeepSeek) 20-40s blocking → client_timeout"
baseline_evidence: ["events/01-RUNTIME-BASELINE.md: p50=0.6ms deterministic, model=20-40s"]
existing_component: "ThreadingHTTPServer blocking POST"
existing_limit: "no streaming; client waits full response or timeout"
trial_scope: "GET /api/runs/{run_id}/events → text/event-stream"
success_threshold: "first event < 1s; gateway regression 49/49"
new_operational_burden: "none — endpoint additive"
security_effect: "owner-auth per run; sanitize run_id; cross-user leak=0"
rollback: "remove /api/runs/ handler"
decision: TRIAL
result: "PASS — endpoint works, regression green, TTFT improvement planned for model path"
