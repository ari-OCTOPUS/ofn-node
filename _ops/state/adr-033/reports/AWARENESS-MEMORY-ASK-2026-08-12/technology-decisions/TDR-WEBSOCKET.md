# TDR: WebSocket
candidate: WebSocket
observed_problem: "none observed yet"
baseline_evidence: ["no pause/resume/cancel requirement proven"]
existing_component: "XHR + SSE (one-way sufficient)"
decision: DEFER
reason: "SSE covers streaming; bidirectional only needed if live pause/resume/cancel/approval required"
