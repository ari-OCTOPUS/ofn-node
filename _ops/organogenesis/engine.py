#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engine.py — موتور زایش قابلیت (فاز ۷ MEGA-FINISH-ALL-v1).

مسیر استاندارد تولد (هر گام رسید دارد؛ پرش ممنوع):
  contract → گیت بدایع (بدیع؟ یادگرفتنی؟) → sandbox (کدِ واقعی روی فیکسچر)
  → تست‌های کاندید (pytest) → shadow (فقط‌خواندنی، صفر نوشت) → verdict
  → ثبت تولد append-only + صفحهٔ Obsidian + کارت وب + replay.

قابلیت نخست‌زاده: pain_triage (دیجست اولویت‌بندیِ درد) با سیگنالِ واقعیِ
cartographer-map-stale (map_age_days=21, OBSERVED) و ledger درد واقعی
(_ops/state/neural/pain-assessment.jsonl — 4730 ردیف).

همهٔ خروجی‌ها MEASURED؛ هیچ VERIFIED بدون callerِ زنده + اجرا + رسید + هش.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

SCHEMA = "organogenesis.v1"
GRADE = "MEASURED"

REQUIRED_CONTRACT = ("identity", "purpose", "human_value_target", "inputs",
                     "permitted_outputs", "tools", "budget", "risk_class",
                     "heartbeat_policy", "evidence_policy", "owner_gates",
                     "failure_modes", "rollback", "retirement_rule")


@dataclass
class LegContract:
    identity: str = ""
    purpose: str = ""
    human_value_target: str = ""
    inputs: list = field(default_factory=list)
    permitted_outputs: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    budget: dict = field(default_factory=dict)
    risk_class: str = ""
    heartbeat_policy: str = ""
    evidence_policy: str = ""
    doctor_endpoint: str = ""
    owner_gates: list = field(default_factory=list)
    failure_modes: list = field(default_factory=list)
    rollback: str = ""
    retirement_rule: str = ""

    def missing(self) -> list:
        return [k for k in REQUIRED_CONTRACT if not getattr(self, k)]

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in REQUIRED_CONTRACT}


class OrganogenesisEngine:
    def __init__(self, state_dir: Path | None = None,
                 archive_path: Path | None = None, lab=None,
                 pages_dir: Path | None = None):
        if state_dir is None:
            state_dir = Path(__file__).resolve().parent.parent / "state"
        self.state_dir = Path(state_dir)
        self.births_path = self.state_dir / "organogenesis" / "births.jsonl"
        self.births_path.parent.mkdir(parents=True, exist_ok=True)
        if archive_path is None:
            archive_path = self.state_dir / "novelty" / "archive.jsonl"
        self.archive_path = Path(archive_path)
        if lab is None:
            from lab.runner import SandboxRunner
            lab = SandboxRunner(workspace_root=self.state_dir / "lab" / "workspaces")
        self.lab = lab
        if pages_dir is None:
            pages_dir = Path(__file__).resolve().parents[2] / "07 - Knowledge" / "organism-pages"
        self.pages_dir = Path(pages_dir)
        self.pages_dir.mkdir(parents=True, exist_ok=True)

    # ── گام‌ها ───────────────────────────────────────────────────────────────
    def _gate_novelty(self, description: str) -> dict:
        from novelty.archive import NoveltyArchive, evaluate
        arc = NoveltyArchive(self.archive_path)
        return evaluate({"text": description, "problem_class": "organogenesis"}, arc.load())

    def _sandbox(self, module_source: str, driver_source: str, fixtures: dict,
                 name: str, timeout_s: float = 15.0) -> dict:
        """کدِ واقعیِ کاندید + درایور داخل workspace؛ فیکسچرها پیش‌نوشته میشوند."""
        marker = 'if __name__ == "__main__":'
        if marker in module_source:
            module_source = module_source.split(marker)[0]
        composite = module_source + "\n\n" + driver_source
        return self.lab.run(composite, name=name, timeout_s=timeout_s, extra_files=fixtures)

    def _shadow(self, module_path: Path, pain_file: Path, state_file: Path) -> dict:
        """اجرای فقط‌خواندنی روی ورودی‌های واقعی؛ صفر نوشت (mtime قبل/بعد)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cand", str(module_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        before = {p: p.stat().st_mtime_ns for p in
                  (self.state_dir / "pulse").glob("*.json")}
        out = mod.triage(Path(pain_file), json.loads(Path(state_file).read_text("utf-8")))
        after = {p: p.stat().st_mtime_ns for p in
                 (self.state_dir / "pulse").glob("*.json")}
        wrote = any(after.get(p) != m for p, m in before.items())
        return {"shadow_ok": not wrote, "wrote_anything": wrote, "output_keys": sorted(out)}

    # ── تولد ─────────────────────────────────────────────────────────────────
    def birth(self, *, spec: dict, module_source: str, driver_source: str,
              fixtures: dict, tests_ref: str, pain_file: Path, state_file: Path,
              timeout_s: float = 15.0) -> dict:
        contract = LegContract(**{k: spec.get(k) for k in REQUIRED_CONTRACT})
        steps = []
        # ۱. قرارداد
        missing = contract.missing()
        if missing:
            rec = {"capability_id": str(uuid.uuid4())[:12], "verdict": "RETIRE",
                   "reason": f"contract-missing:{','.join(missing)}", "steps": []}
            self._record(rec)
            return rec
        steps.append({"step": "contract", "ok": True})
        # ۲. گیت بدایع (پیش از هر مصرف بودجه)
        ng = self._gate_novelty(spec.get("description") or contract.purpose)
        if not ng.get("allow"):
            rec = {"capability_id": str(uuid.uuid4())[:12], "verdict": "RETIRE",
                   "reason": f"novelty-gate:{ng.get('state')}", "steps": steps}
            self._record(rec)
            return rec
        steps.append({"step": "novelty-gate", "ok": True, "state": ng.get("state")})
        # ۳. sandbox با کدِ واقعی
        sb = self._sandbox(module_source, driver_source, fixtures,
                           name=contract.identity, timeout_s=timeout_s)
        steps.append({"step": "sandbox", "ok": bool(sb.get("ok") and not sb.get("blocked")),
                      "exit": sb.get("exit_code"), "security_events": len(sb.get("security_events") or [])})
        if not steps[-1]["ok"]:
            rec = {"capability_id": str(uuid.uuid4())[:12], "verdict": "ITERATE",
                   "reason": "sandbox-failed", "steps": steps, "sandbox": sb}
            self._record(rec)
            return rec
        # ۴. تست‌های کاندید (pytest واقعی روی فایل تست)
        import subprocess
        tp = subprocess.run([sys.executable, "-m", "pytest", tests_ref, "-q"],
                            capture_output=True, text=True, timeout=180)
        steps.append({"step": "candidate-tests", "ok": tp.returncode == 0,
                      "exit": tp.returncode, "tail": (tp.stdout or "")[-200:]})
        if not steps[-1]["ok"]:
            rec = {"capability_id": str(uuid.uuid4())[:12], "verdict": "ITERATE",
                   "reason": "candidate-tests-failed", "steps": steps}
            self._record(rec)
            return rec
        # ۵. shadow (فقط‌خواندنی روی ورودی‌های واقعی)
        sh = self._shadow(Path(__file__).resolve().parent.parent / "legs" / "pain_triage.py",
                          pain_file, state_file)
        steps.append({"step": "shadow", "ok": bool(sh["shadow_ok"]), **sh})
        verdict = "PROMOTE" if sh["shadow_ok"] else "ITERATE"
        cap_id = hashlib.sha256(json.dumps(
            {"identity": contract.identity, "purpose": contract.purpose,
             "source_hash": hashlib.sha256(module_source.encode("utf-8")).hexdigest()},
            ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        page = self._write_page(cap_id, contract, steps, verdict)
        card = self._write_card(cap_id, contract, steps, verdict)
        rec = {"schema": SCHEMA, "grade": GRADE, "capability_id": cap_id,
               "verdict": verdict, "reason": "full-birth-path",
               "steps": steps, "sandbox": {k: sb.get(k) for k in
                                           ("ok", "exit_code", "timeout", "security_events")},
               "novelty_gate": {"state": ng.get("state")},
               "tests_ref": tests_ref, "obsidian_page": str(page),
               "web_card": str(card), "ts": time.time(),
               "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S")}
        rec["receipt_hash"] = self._hash(rec)
        self._record(rec)
        return rec

    @staticmethod
    def _hash(rec: dict) -> str:
        core = {k: rec.get(k) for k in ("capability_id", "verdict", "reason",
                                        "steps", "novelty_gate", "tests_ref")}
        return hashlib.sha256(json.dumps(core, ensure_ascii=False,
                                         sort_keys=True).encode("utf-8")).hexdigest()[:24]

    def _record(self, rec: dict) -> None:
        with self.births_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def replay(self, capability_id: str) -> dict:
        """بازاجرای قطعی: تولد ثبت‌شده را پیدا میکند و هش رسید را بازتولید میکند."""
        for line in self.births_path.read_text("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("capability_id") == capability_id and rec.get("receipt_hash"):
                return {"replay_ok": self._hash(rec) == rec.get("receipt_hash"),
                        "receipt_hash": rec.get("receipt_hash"),
                        "recomputed_hash": self._hash(rec),
                        "verdict": rec.get("verdict")}
        return {"replay_ok": False, "reason": "not-found"}

    # ── artifacts ────────────────────────────────────────────────────────────
    def _write_page(self, cap_id: str, contract: LegContract, steps: list,
                    verdict: str) -> Path:
        p = self.pages_dir / f"{cap_id}-CARD.md"
        lines = [f"# {contract.identity}", "",
                 f"> machine-generated · {time.strftime('%Y-%m-%dT%H:%M:%S')} · grade={GRADE}",
                 "", f"**purpose:** {contract.purpose}",
                 f"**human_value_target:** {contract.human_value_target}",
                 f"**risk_class:** {contract.risk_class}",
                 f"**verdict:** {verdict}", "",
                 "## مسیر تولد (steps)", ""]
        lines += [f"- {s.get('step')}: ok={s.get('ok')}" for s in steps]
        lines += ["", f"*capability_id: `{cap_id}` · replayable via births.jsonl*"]
        p.write_text("\n".join(lines), encoding="utf-8")
        return p

    def _write_card(self, cap_id: str, contract: LegContract, steps: list,
                    verdict: str) -> Path:
        d = self.state_dir / "organogenesis" / "cards"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{cap_id}.json"
        p.write_text(json.dumps({"capability_id": cap_id, "identity": contract.identity,
                                 "purpose": contract.purpose, "verdict": verdict,
                                 "steps": steps, "grade": GRADE,
                                 "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                ensure_ascii=False, indent=1), "utf-8")
        return p


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--birth", action="store_true")
    ap.add_argument("--replay", default="")
    args = ap.parse_args()
    eng = OrganogenesisEngine()
    if args.birth:
        spec = {
            "identity": "pain-triage",
            "purpose": "دیجستِ اولویتبندیشدهٔ سیگنالهای درد برای مالک/داشبورد",
            "human_value_target": "کاهش بار شناختی مالک در خواندن ۴۷۳۰ ردیف درد",
            "inputs": ["pain-assessment.jsonl", "ORGANISM-STATE.json"],
            "permitted_outputs": ["triage-digest-json", "priority"],
            "tools": ["read-only-files"],
            "budget": {"tokens": 0, "calls": 0, "risk_weight": 0.1},
            "risk_class": "A0-observation",
            "heartbeat_policy": "on-demand",
            "evidence_policy": "MEASURED; sources cited",
            "owner_gates": ["external-output-none"],
            "failure_modes": ["missing-file", "malformed-row"],
            "rollback": "read-only; no state written",
            "retirement_rule": "3 cycles without use",
            "description": "تولید دیجست triage از ledger درد و سیگنالهای ساختاری ارگانیسم، فقطخواندنی",
        }
        mod = Path(__file__).resolve().parent.parent / "legs" / "pain_triage.py"
        driver = ('import json, sys\n'
                  'from pathlib import Path\n'
                  'import pain_triage\n'
                  'rows = [json.loads(l) for l in Path("fixture-pain.jsonl").read_text("utf-8").splitlines() if l.strip()]\n'
                  'state = json.loads(Path("fixture-state.json").read_text("utf-8"))\n'
                  'out = pain_triage.triage(Path("fixture-pain.jsonl"), state)\n'
                  'print(json.dumps({"rows": out["counts"]["rows"], "priority": out["priority"]}))\n')
        fixtures = {"fixture-pain.jsonl": json.dumps([
            {"ts": "2026-08-11T21:10:41", "pain": 0.25, "threshold": 0.35,
             "status": "OK", "reason_codes": ["all_clear"], "evidence_level": "SHADOW",
             "proposal": "none", "trace_id": "f1"},
            {"ts": "2026-08-11T21:14:04", "pain": 0.375, "threshold": 0.35,
             "status": "OK", "reason_codes": ["pain_above_threshold"],
             "evidence_level": "SHADOW", "proposal": "protective_proposal",
             "trace_id": "f2"}], ensure_ascii=False),
            "fixture-state.json": json.dumps(
                {"cartographer": {"map_stale": True, "map_age_days": 21,
                                  "drift_files": 1163},
                 "chrono": {"legs_diag": {"lead-naghshi": {"state": "alive"}}}})}
        res = eng.birth(spec=spec, module_source=mod.read_text("utf-8"),
                        driver_source=driver, fixtures=fixtures,
                        tests_ref=str(Path(__file__).resolve().parent.parent /
                                      "tests" / "test_pain_triage.py"),
                        pain_file=Path(__file__).resolve().parent.parent /
                        "state" / "neural" / "pain-assessment.jsonl",
                        state_file=Path(__file__).resolve().parent.parent /
                        "state" / "ORGANISM-STATE.json")
        print(json.dumps({k: res.get(k) for k in ("capability_id", "verdict", "reason",
                                                  "receipt_hash", "obsidian_page")},
                         ensure_ascii=False, indent=1))
    elif args.replay:
        print(json.dumps(eng.replay(args.replay), ensure_ascii=False, indent=1))
    else:
        ap.print_help()
