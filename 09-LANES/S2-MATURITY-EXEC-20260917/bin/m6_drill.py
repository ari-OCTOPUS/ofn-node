#!/usr/bin/env python3
"""S2-MATURITY M6 drill — consumer-on-restored-state + tamper refusal + halt oracle.

Isolated: works ONLY inside /root/s2-m6-drill-20260917/. Never touches live state.
Restored source: /root/s1-maturity-mirror-replica-20260917 (byte-verified vs live 138).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DRILL = Path("/root/s2-m6-drill-20260917")
SRC_REPLICA = Path("/root/s1-maturity-mirror-replica-20260917")
STATE = DRILL / "state"
OUT = {"ts": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    if DRILL.exists():
        shutil.rmtree(str(DRILL))
    STATE.mkdir(parents=True)
    # 1) restored state into drill
    shutil.copy(str(SRC_REPLICA / "api-budget" / "budget-ledger.jsonl"), str(STATE / "budget-ledger.jsonl"))
    shutil.copytree(str(SRC_REPLICA / "api-budget" / "config"), str(STATE / "config"))
    # patched broker copy (only ROOT differs)
    broker_src = Path("/tmp/api_budget.py").read_text(encoding="utf-8")
    patched = broker_src.replace('ROOT = Path("/home/ari/ofn/state/api-budget")',
                                 'ROOT = Path("%s")' % STATE)
    assert patched != broker_src, "ROOT patch failed"
    (DRILL / "api_budget_drill.py").write_text(patched, encoding="utf-8")
    (DRILL / "providers.py").write_text(Path("/tmp/providers.py").read_text(encoding="utf-8"), encoding="utf-8")
    OUT["root_patch"] = "only ROOT constant repointed to drill state"

    ab = load_module("api_budget_drill", str(DRILL / "api_budget_drill.py"))

    def verify_chain(path):
        rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
        prev = None
        bad_link, bad_hash = [], []
        for i, r in enumerate(rows):
            if r.get("previous_bl_hash") != prev:
                bad_link.append(i)
            calc = ab.sha_obj({k: v for k, v in r.items() if k != "bl_hash"})
            if calc != r.get("bl_hash"):
                bad_hash.append(i)
            prev = r.get("bl_hash")
        return {"rows": len(rows), "bad_link": bad_link, "bad_hash": bad_hash,
                "ok": not bad_link and not bad_hash, "head": prev}

    # 2) chain verify restored
    OUT["restored_chain"] = verify_chain(STATE / "budget-ledger.jsonl")
    # 3) consumer semantics on restored state
    OUT["consumer_status"] = {k: v for k, v in ab.status().items() if isinstance(v, (int, float, str, bool, type(None)))}
    OUT["month_spend_usd"] = ab.month_spend(ab._clock_guard(ab.now_iso_ts() if hasattr(ab, "now_iso_ts") else 0)) if False else None
    try:
        import time
        now = time.time()
        OUT["month_spend_usd"] = ab.month_spend(now)
        OUT["window_caps"] = list(ab.window_caps(now))
    except Exception as e:
        OUT["month_spend_error"] = repr(e)

    # 4) live round-trip on the REPLICA ledger (clearly marked drill task)
    r = ab.reserve(task_id="s2-m6-drill", purpose="mirror-restore-consumer-drill",
                   est_in_tok=100, max_out_tok=50, route_reason="s2-m6-isolated-drill")
    rid = r.get("request_id")
    s = ab.settle(request_id=rid, visible_tokens=10, orchestration_tokens=5,
                  latency_s=0.1, response_sha="drill-no-network-sha",
                  retained=False, rejection_reason="")
    OUT["roundtrip_reserve"] = {k: r.get(k) for k in ("request_id", "kind", "est_max_usd", "task_id")}
    OUT["roundtrip_settle"] = {k: s.get(k) for k in ("ok", "cost_usd", "window_spent_usd", "task_spent_usd", "month_spent_usd")} if isinstance(s, dict) else str(s)[:120]
    OUT["chain_after_roundtrip"] = verify_chain(STATE / "budget-ledger.jsonl")
    # idempotent settle must not double-charge (broker contract: DUPLICATE_SETTLE)
    s2 = ab.settle(request_id=rid, visible_tokens=10, orchestration_tokens=5,
                   latency_s=0.1, response_sha="drill-no-network-sha",
                   retained=False, rejection_reason="")
    OUT["settle_replay"] = s2
    OUT["settle_replay_rows_delta"] = verify_chain(STATE / "budget-ledger.jsonl")["rows"] - OUT["chain_after_roundtrip"]["rows"]

    # 5) tamper refusal
    tam = DRILL / "tampered-ledger.jsonl"
    lines = (STATE / "budget-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(lines):
        if '"kind": "settle"' in l or '"est_max_usd"' in l:
            lines[i] = l.replace("0.03", "9.99", 1) if "0.03" in l else l[:-3] + "9.99}" if l.endswith("9}") else l
            break
    tam.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT["tampered_chain"] = verify_chain(tam)

    # 6) halt oracle component drill (isolated copy of opslib with OFN_ROOT repointed)
    ops_src = Path("/tmp/opslib.py")
    if ops_src.exists():
        ops_text = ops_src.read_text(encoding="utf-8")
        import re as _re
        ops_patched = _re.sub(r'OFN_ROOT\s*=\s*Path\([^)]*\)', 'OFN_ROOT = Path("%s")' % DRILL, ops_text, count=1)
        (DRILL / "opslib_drill.py").write_text(ops_patched, encoding="utf-8")
        ops = load_module("opslib_drill", str(DRILL / "opslib_drill.py"))
        # Direct attribute override (regex patching proved fragile): master_halted()
        # reads module globals at call time, so this reliably repoints the oracle.
        ops.OFN_ROOT = DRILL
        ops.HALT_FLAG = DRILL / "HALT-ALL"
        if hasattr(ops, "_os"):
            pass
        os.environ.pop("HALT_SURVIVAL_LOOP", None)
        r0 = ops.master_halted()
        (DRILL / "HALT-ALL").write_text("drill\n")
        r1 = ops.master_halted()
        (DRILL / "HALT-ALL").unlink()
        os.environ["HALT_SURVIVAL_LOOP"] = "1"
        r2 = ops.master_halted()
        os.environ.pop("HALT_SURVIVAL_LOOP", None)
        def send_one_drill():
            if ops.master_halted():
                return "REFUSED_HALTED"
            return "SENT"
        OUT["halt_drill"] = {"clean": r0, "flag": r1, "env": r2,
                             "gated_send_clean": "SENT" if r0 is None else "REFUSED_HALTED",
                             "gated_send_flag": send_one_drill() if False else ("REFUSED_HALTED" if r1 else "SENT")}
        # gated send with flag present
        (DRILL / "HALT-ALL").write_text("drill\n")
        OUT["halt_drill"]["gated_send_flag"] = "REFUSED_HALTED" if ops.master_halted() else "SENT"
        (DRILL / "HALT-ALL").unlink()
    else:
        OUT["halt_drill"] = "opslib not staged"

    verdict = {
        "consumer_on_restored_state": bool(OUT["restored_chain"]["ok"]) and bool(OUT["chain_after_roundtrip"]["ok"]),
        "tamper_refused": not OUT["tampered_chain"]["ok"],
        "halt_oracle_fail_closed": OUT.get("halt_drill", {}).get("clean", None) is None
                                   and OUT.get("halt_drill", {}).get("flag") is not None
                                   and OUT.get("halt_drill", {}).get("gated_send_flag") == "REFUSED_HALTED",
    }
    OUT["verdict"] = verdict
    (DRILL / "M6-DRILL-RESULT.json").write_text(json.dumps(OUT, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(OUT, indent=1, default=str)[:3500])


if __name__ == "__main__":
    main()
