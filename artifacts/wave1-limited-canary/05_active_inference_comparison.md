# Active Inference comparison

Status: `NOT_ACTIVATED`

The real source is `ofn/organism/cognition/active_inference.py`:

- `expected_free_energy()` computes risk plus ambiguity.
- `plan_shadow()` ranks caller-supplied transition matrices.
- State dimension is bounded to four.
- `EXECUTABLE=False`.
- The module performs no HTTP, shell, systemd, file, or actuator operation.

The source does not define an existing policy enum. It accepts caller-provided policy matrices, so the Wave 1 requirement to rank only existing enum policies cannot be claimed as already implemented.

Because provider/cost preflight blocked the canary:

- Active Inference remained `SHADOW`.
- `CANARY_POLICY_SELECTION` was not entered.
- Posterior computations: `0`
- Policy proposals: `0`
- Actions executed: `0`
- Preferences changed: `0`
- Safety/identity/owner policy changed: `0`
- Executable total: `0`

Any future Wave 1 execution requires a closed existing-policy enum and tests proving that arbitrary policies and action dispatch are rejected.
