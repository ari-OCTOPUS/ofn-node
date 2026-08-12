# TDR: NATS JetStream
candidate: NATS JetStream
observed_problem: "none — single process sufficient"
baseline_evidence: ["event volume < 10/run; single gateway process; no cross-process consumers"]
decision: DEFER
reason: "internal JSONL sufficient; NATS only if multi-process consumers or cross-machine replay proven"
