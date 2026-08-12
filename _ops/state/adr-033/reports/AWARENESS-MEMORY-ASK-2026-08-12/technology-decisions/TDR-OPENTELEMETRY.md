# TDR: OpenTelemetry
candidate: OpenTelemetry
observed_problem: "none — event_log + run_store provide trace"
baseline_evidence: ["typed events + run_id + sequence provide causal trace"]
decision: DEFER
reason: "minimal OTel spans possible later; collector/backend only if operational need proven"
