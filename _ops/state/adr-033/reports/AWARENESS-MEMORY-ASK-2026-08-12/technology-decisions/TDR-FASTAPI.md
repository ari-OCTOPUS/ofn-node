# TDR: FastAPI
candidate: FastAPI
observed_problem: "none — ThreadingHTTPServer works"
baseline_evidence: ["p50=0.6ms deterministic; 26 suite green; concurrent load not measured failing"]
existing_component: "ThreadingHTTPServer + _run_with_timeout"
decision: DEFER
reason: "no measured saturation; migration risk > benefit; adapter layer possible later"
