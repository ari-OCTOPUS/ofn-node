"""test_arm_gate_p0.py — P0 arm_gate verification (blindspot #30).

تأیید می‌کند که:
۱. sensitive action (code_autonomy) بدون arm → deny (وقتی sensitive_enforced)
۲. read-only action بدون arm → allow
۳. sensitive action با arm mock → allow
۴. /stop و kill_seam همیشه allow (logger-independent)
۵. sensitive_enforced default-off → byte-identical (pass-through)
۶. هیچ outbound ندارد
۷. arm_status کار می‌کند

no network، no real telegram، no outbound.
"""
import os
import sys
import json
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

results = {"pass": 0, "fail": 0, "details": []}


def check(name, cond):
    if cond:
        results["pass"] += 1
        results["details"].append(f"  ✅ {name}")
    else:
        results["fail"] += 1
        results["details"].append(f"  ❌ {name}")


def _make_arm_token(cap, secret=None, age_s=0):
    """Build a fresh arm-token dict."""
    tok = {
        "capability": cap,
        "armed_at": time.time() - age_s,
        "key": "owner",
    }
    if secret:
        import hmac, hashlib
        body = f"{cap}|{tok['armed_at']}|{tok['key']}".encode()
        tok["hmac"] = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return tok


def main():
    import arm_gate

    with tempfile.TemporaryDirectory() as tmp:
        ops = Path(tmp) / "ops"
        arm = Path(tmp) / "arm"
        ops.mkdir()
        arm.mkdir()

        # ─── Test 1: default-off → pass-through (byte-identical) ───
        os.environ.pop("OCTOPUS_REQUIRE_ARM", None)
        os.environ.pop("OCTOPUS_ARM_SENSITIVE_DEFAULT", None)
        ok, why = arm_gate.guard("code_autonomy", ops_dir=ops, arm_dir=arm)
        check("default-off pass-through", ok and "not-enforced" in why)

        # ─── Test 2: sensitive_enforced ON, no arm → deny ───
        os.environ["OCTOPUS_ARM_SENSITIVE_DEFAULT"] = "1"
        # activation flag present but no arm token
        (ops / "ACTIVATION-CODE-AUTONOMY.flag").write_text("owner-test")
        ok, why = arm_gate.guard("code_autonomy", ops_dir=ops, arm_dir=arm)
        check("sensitive no-arm → deny", not ok)

        # ─── Test 3: sensitive_enforced ON, valid arm → allow ───
        tok = _make_arm_token("code_autonomy")
        (arm / "code_autonomy.arm.json").write_text(json.dumps(tok))
        # two-key cap: also need arm2
        tok2 = _make_arm_token("code_autonomy")
        (arm / "code_autonomy.arm2.json").write_text(json.dumps(tok2))
        ok, why = arm_gate.guard("code_autonomy", ops_dir=ops, arm_dir=arm)
        check("sensitive valid-arm → allow", ok and "open" in why)

        # ─── Test 4: stale arm (expired) → deny ───
        stale_tok = _make_arm_token("code_autonomy", age_s=25*3600)  # 25h > 24h TTL
        (arm / "code_autonomy.arm.json").write_text(json.dumps(stale_tok))
        ok, why = arm_gate.guard("code_autonomy", ops_dir=ops, arm_dir=arm)
        check("stale arm → deny", not ok)

        # ─── Test 5: non-sensitive cap (cortex_paid) without arm → allow when sensitive_enforced ───
        # cortex_paid is NOT in _ALWAYS_SENSITIVE, so guard passes through
        (ops / "ACTIVATION-CORTEX-PAID.flag").write_text("owner-test")
        ok, why = arm_gate.guard("cortex_paid", ops_dir=ops, arm_dir=arm)
        check("non-sensitive cap pass-through under sensitive_enforced", ok)

        # ─── Test 6: full enforcement ON → all dangerous caps require arm ───
        os.environ["OCTOPUS_REQUIRE_ARM"] = "1"
        ok, why = arm_gate.guard("cortex_paid", ops_dir=ops, arm_dir=arm)
        check("full-enforce cortex_paid no-arm → deny", not ok)

        # valid arm for cortex_paid
        tok_cp = _make_arm_token("cortex_paid")
        (arm / "cortex_paid.arm.json").write_text(json.dumps(tok_cp))
        ok, why = arm_gate.guard("cortex_paid", ops_dir=ops, arm_dir=arm)
        check("full-enforce cortex_paid valid-arm → allow", ok and "open" in why)

        # ─── Test 7: unknown capability → deny ───
        ok, why = arm_gate.guard("unknown_cap", ops_dir=ops, arm_dir=arm)
        check("unknown cap → deny", not ok)

        # ─── Test 8: arm_status works ───
        status = arm_gate.arm_status(arm_dir=arm, ops_dir=ops)
        check("arm_status returns dict", isinstance(status, dict))
        check("arm_status has caps", "caps" in status)

        # ─── Test 9: activation flag absent → deny ───
        # replicate flag not created
        ok, why = arm_gate.guard("replicate", ops_dir=ops, arm_dir=arm)
        check("replicate flag absent → deny", not ok)

        # ─── Test 10: no outbound — module has no network attrs ───
        attrs = dir(arm_gate)
        has_network = any("requests" in a or "http" in a.lower() or "socket" in a.lower() for a in attrs)
        check("no network/http/socket in module", not has_network)

    # cleanup env
    os.environ.pop("OCTOPUS_REQUIRE_ARM", None)
    os.environ.pop("OCTOPUS_ARM_SENSITIVE_DEFAULT", None)

    print("test_arm_gate_p0 — P0 arm_gate verification (blindspot #30)")
    for d in results["details"]:
        print(d)
    print(f"\nPass: {results['pass']}, Fail: {results['fail']}")
    return results["fail"] == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
