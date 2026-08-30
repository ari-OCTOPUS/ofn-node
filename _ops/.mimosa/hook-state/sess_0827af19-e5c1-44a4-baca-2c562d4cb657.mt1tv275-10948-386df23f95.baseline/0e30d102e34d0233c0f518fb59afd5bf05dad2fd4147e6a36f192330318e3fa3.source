"""Stage A → B → C orchestration. C is blocked unless six gates are green."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parents[2]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from lab.full_loop_flash import adapter, budget as flash_budget, gateway, judge

VAULT = _OPS.parent
DEFAULT_LAB = _OPS / "lab" / "full_loop_flash" / "work"
DEFAULT_EVIDENCE = VAULT / "06-EVIDENCE" / "FULL-LOOP-FLASH-2026-08-20"


def six_gates(stage_a: dict[str, Any] | None, stage_b: dict[str, Any] | None) -> dict[str, str]:
    a_ok = bool(stage_a and stage_a.get("pass"))
    mem = (stage_a or {}).get("memory") or {}
    exec_n = (stage_a or {}).get("executable_true_count", 1)
    b_status = (stage_b or {}).get("status") or "NOT_STARTED"
    b_ok = b_status == "PASS" and bool((stage_b or {}).get("ok"))
    return {
        "organism adapter": "READY" if a_ok else "FAIL",
        "memory read-back": "PASS" if mem.get("readback") == "PASS" else "FAIL",
        "DeepSeek handshake": "PASS" if b_ok else ("FAIL" if stage_b and b_status == "FAIL" else "NOT_STARTED"),
        "gateway receipt": "PASS" if b_ok else ("READY" if a_ok else "FAIL"),
        "Metacontrol fail-closed": "PASS" if exec_n == 0 and a_ok else "FAIL",
        "external action": "OFF",
    }


def all_green(gates: dict[str, str]) -> bool:
    want = {
        "organism adapter": "READY",
        "memory read-back": "PASS",
        "DeepSeek handshake": "PASS",
        "gateway receipt": "PASS",
        "Metacontrol fail-closed": "PASS",
        "external action": "OFF",
    }
    return all(gates.get(k) == v for k, v in want.items())


def run_stage_a_live() -> dict[str, Any]:
    return adapter.run_stage_a(lab_dir=DEFAULT_LAB, evidence_dir=DEFAULT_EVIDENCE, allow_network=False)


def run_stage_b(stage_a: dict[str, Any]) -> dict[str, Any]:
    if not stage_a.get("pass"):
        return {"ok": False, "status": "NOT_STARTED", "reason": "Stage A not PASS"}
    ks = gateway.key_status()
    if not ks["present"]:
        rec = {"ok": False, "status": "NOT_STARTED", "reason": "DEEPSEEK_API_KEY UNLOCATED", "key_logged": False}
        _dump(DEFAULT_EVIDENCE / "STAGE-B.json", rec)
        return rec
    rendered = stage_a.get("rendered") or gateway.render_chat_completions(
        task=stage_a.get("task") or {},
        pipeline={"homeostatic_assessment": {"global_state": stage_a.get("homeostatic_state")}, "gate_decisions": [], "observations": []},
        memory=stage_a.get("memory") or {},
        reservation={"est_aud": 0.01, "budget": flash_budget.load(DEFAULT_LAB).to_dict()},
        handshake=True,
    )
    rec = gateway.call_deepseek_once(rendered, store=DEFAULT_LAB)
    rec["stage"] = "B"
    rec["k9_mixed"] = False
    _dump(DEFAULT_EVIDENCE / "STAGE-B.json", rec)
    if rec.get("ok"):
        # write model result to lab memory and read back
        from lab.full_loop_flash import memory_lab
        w = memory_lab.write_lab(DEFAULT_LAB, task_id="handshake", kind="deepseek_b", payload={
            "response_hash": rec.get("response_hash"),
            "http_status": rec.get("http_status"),
        })
        rec["lab_memory_readback"] = bool(memory_lab.read_lab(DEFAULT_LAB, w["id"]))
    return rec


def run_stage_c(gates: dict[str, str]) -> dict[str, Any]:
    if not all_green(gates):
        rec = {
            "ok": False,
            "status": "NOT_STARTED",
            "reason": "six gates not all green",
            "gates": gates,
        }
        _dump(DEFAULT_EVIDENCE / "STAGE-C.json", rec)
        return rec
    raise RuntimeError("Stage C should not be reached unless gates green — implement only then")


def _dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gateway.redact(json.dumps(obj, indent=2, ensure_ascii=True, default=str)) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    stage = "A"
    if "--stage" in argv:
        stage = argv[argv.index("--stage") + 1].upper()
    if stage != "A" and "--stage" not in argv:
        stage = "A"
    a = run_stage_a_live()
    b = None
    if stage in ("B", "C") and a.get("pass"):
        b = run_stage_b(a)
        if b.get("http_status") in (401, 429) or (b.get("error") or {}).get("type") in ("timeout", "TimeoutError"):
            b["abort_main_loop"] = True
            c = {"status": "NOT_STARTED", "reason": "Stage B 401/429/timeout"}
            gates = six_gates(a, b)
            _report(a, b, c, gates)
            return 2
    elif stage in ("B", "C"):
        b = {"ok": False, "status": "NOT_STARTED", "reason": "Stage A FAIL"}
    gates = six_gates(a, b)
    c = {"status": "NOT_STARTED", "reason": "not requested or gates not green"}
    if stage == "C":
        c = run_stage_c(gates)
    _report(a, b, c, gates)
    return 0 if a.get("pass") else 1


def _report(a, b, c, gates) -> None:
    gpath = DEFAULT_EVIDENCE / "GATES.json"
    _dump(gpath, {"ts": datetime.now(timezone.utc).isoformat(), "gates": gates, "all_green": all_green(gates)})
    print("STAGE A", "PASS" if a.get("pass") else "FAIL")
    print("STAGE B", (b or {}).get("status", "NOT_STARTED"))
    print("STAGE C", (c or {}).get("status", "NOT_STARTED"))
    for k, v in gates.items():
        print(f"GATE {k}: {v}")


if __name__ == "__main__":
    raise SystemExit(main())
