"""OCTOPUS epistemics cabin — دو لایه:

1. off-loop epistemics metrics (SCAFFOLD، Phase 4/5): read-only، advisory، reversible.
   به یک streamِ جداگانهٔ hash-chained emit می‌کند، هرگز به money ledger. به loop
   متصل نیست (Phase 5، flag-gated). metrics فقط verdictهای functional/relative هستند
   — هیچ ادعای phenomenal.
   ماژول‌ها: contracts, emit, metrics, readers, guard_review, run_offloop (stdlib-only).

2. Epistemic Test Engine (ADR-039، TCB-grade): ادعاها را به زنجیرهٔ قابل‌ابطال تبدیل
   می‌کند: claim → prediction → bounded sandbox test → tamper-evident receipt →
   belief-update | refute. گیتِ deterministic، fail-closed، may_execute==False همیشه.
   ماژول‌ها: schemas (Pydantic v2 — دومین کابینِ Pydanticِ _ops، ADR-037 amend)،
   canonical, policy, validator (این سه stdlib-only). receipt_store/provenance/runner/
   gate/bayes در commitهای بعدی (C2–C7).

نکتهٔ import: ماژول‌های ADR-039 در __init__ eager-import نمی‌شوند تا `import epistemics`
برای مصرف‌کنندگانِ لایهٔ metrics، Pydantic را نکشد. آن‌ها را صریحًا وارد کنید:
    from epistemics.schemas import EpistemicClaim
    from epistemics.validator import validate_claim
"""
from . import contracts, emit, metrics, readers  # noqa: F401
