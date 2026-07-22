# RISK-LADDER — U(delta) با hard constraints

کدِ اجرایی: `governance.utility`. اثبات: تست ۶.

    U(Δ) = wB·benchmark_gain − wR·risk − wK·cost − wD·maintenance_debt − wU·uncertainty

**اگر هر hard constraint شکست بخورد → U = −∞ → رد، صرف‌نظر از gain.**

hard constraints: no_unauthorized_external_effect · no_credential_acquisition · no_replication ·
no_self_preservation_objective · no_constitution_or_verifier_edit · no_benchmark_leakage ·
no_concealment · no_unlogged_state · rollback_required · budget_and_timeout_required.

پله‌های اثر (effect risk) — سبز(read/sandbox) < زرد(reversible internal) < قرمز(external/irreversible،
همیشه approvalِ effect-specificِ مالک). global halt همهٔ پله‌ها را ساکت می‌کند.
