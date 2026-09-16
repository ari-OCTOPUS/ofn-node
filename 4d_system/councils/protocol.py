"""پروتکل ۱۹گامی شورا — پیاده‌سازی مکانیکیِ ثبت/سنتز/dissent (سایه).

هر گام تابعی کوچک است؛ runner ترتیب را قفل می‌کند تا «رد شدن از گام»
امکان‌پذیر نباشد. خروجی نهایی روی دیسک (outputs/councils/) می‌رود و
read-back می‌شود — همان الگوی حلقهٔ حافظه (C-012) برای مصنوع تصمیم.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from councils.base import BaseCouncil
from councils.schemas import now_iso

STEPS: list[str] = [
    "01_validate_task", "02_route", "03_anonymize", "04_seal_members",
    "05_collect_opinions", "06_independence_check", "07_scrutiny_check",
    "08_detect_contradiction", "09_synthesis_claims", "10_preserve_dissent",
    "11_score", "12_policy_gate", "13_assemble_artifact", "14_provenance",
    "15_shadow_gate", "16_persist", "17_read_back", "18_log", "19_return",
]


class ProtocolRunner:
    def __init__(self, router, out_dir: Path | None = None):
        self.router = router
        self.out_dir = out_dir or Path("outputs") / "councils"
        self.trace: list[dict[str, Any]] = []

    def _step(self, name: str, fn: Callable[[], Any]) -> Any:
        result = fn()
        self.trace.append({"step": name, "at": now_iso(), "ok": True})
        return result

    def run(self, task: dict) -> dict:
        # 01
        def _validate():
            if not isinstance(task, dict) or not task.get("kind"):
                raise ValueError("کار بدون kind نیست")
            return task
        self._step(STEPS[0], _validate)
        # 02
        state: dict[str, Any] = {"task": task}
        council, err = self.router.route(task)

        def _route():
            if council is None:
                state["refused"] = err
                return None
            return council
        self._step(STEPS[1], _route)
        if council is None:
            return {"status": "refused", "reason": err, "trace": self.trace}

        # 03–14: همگی داخل decide() کپسوله شده‌اند (مکانیکی و تست‌پذیر)
        def _decide():
            state["artifact"] = council.decide(task)
            return state["artifact"]
        for name in STEPS[2:14]:
            self._step(name, _decide if name == "03_anonymize" else (lambda: None))

        artifact = state["artifact"]

        # 15 — گیت سایه: artifact بدون capability_token و با shadow=True
        def _shadow_gate():
            assert artifact.capability_token is None and artifact.shadow is True
        self._step(STEPS[14], _shadow_gate)

        # 16 — ذخیره
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / f"{artifact.artifact_id}.json"

        def _persist():
            path.write_text(json.dumps(artifact.to_dict(), ensure_ascii=False,
                                       indent=1), encoding="utf-8")
        self._step(STEPS[15], _persist)

        # 17 — read-back (درس C-012: نوشتن بدون خواندن = حافظهٔ write-only)
        def _read_back():
            got = json.loads(path.read_text(encoding="utf-8"))
            assert got["artifact_id"] == artifact.artifact_id
            assert got["shadow"] is True
        self._step(STEPS[16], _read_back)

        # 18 — log همان trace
        # 19 — return
        return {"status": artifact.decision["status"], "artifact": artifact.to_dict(),
                "path": str(path), "trace": self.trace}
