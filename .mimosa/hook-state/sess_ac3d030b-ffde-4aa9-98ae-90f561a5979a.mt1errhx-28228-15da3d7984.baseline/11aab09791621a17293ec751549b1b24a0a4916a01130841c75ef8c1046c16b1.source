"""shadow_run.py — harnessِ shadow runِ ADR-039 (C7).

یک runِ bounded از epistemic_tick را برای مدتِ مشخص می‌چرخاند و یک گزارشِ امضاشده
می‌سازد. **هیچ اثرِ خارجی** — may_execute همیشه False؛ فقط health-checkهای متوالی
+ جمع‌آوریِ آمارِ زنجیرهٔ receipt.

owner-timed: runِ واقعیِ ۱۰h با organismِ زنده نیاز است؛ این ماژول harness است.
`run_shadow(seconds=...)` یک runِ کوتاه‌تر برای demo/CI می‌سازد.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import invariants as _inv
from .policy import load_policy
from .receipt_store import ReceiptStore


@dataclass(frozen=True)
class ShadowTick:
    """یک نمونهٔ health-check در طولِ shadow run."""
    t: float                       # epoch seconds
    cycle_label: int
    chain_ok: bool
    chain_n: int
    invariants_count: int
    may_execute: bool              # همیشه False انتظار می‌رود


@dataclass(frozen=True)
class ShadowReport:
    """گزارشِ امضاشدهٔ یک shadow run."""
    started_at: float
    ended_at: float
    duration_s: float
    n_ticks: int
    ticks: List[ShadowTick] = field(default_factory=list)
    invariants_count: int = 0
    chain_ok_at_end: bool = False
    may_execute_ever_true: bool = False   # باید همیشه False
    digest: str = ""

    def sign(self, key: bytes = b"octopus-epistemic-shadow") -> "ShadowReport":
        material = "|".join([
            f"{self.started_at:.3f}", f"{self.ended_at:.3f}",
            str(self.n_ticks),
            ",".join(f"{tk.t:.3f}:{tk.chain_ok}:{tk.chain_n}" for tk in self.ticks),
            str(self.may_execute_ever_true),
        ])
        digest = hashlib.sha256(material.encode("utf-8") + key).hexdigest()
        return ShadowReport(self.started_at, self.ended_at, self.duration_s,
                            self.n_ticks, self.ticks, self.invariants_count,
                            self.chain_ok_at_end, self.may_execute_ever_true, digest)


def _one_tick(cycle_label: int) -> ShadowTick:
    chain = ReceiptStore().verify()
    return ShadowTick(
        t=time.time(), cycle_label=cycle_label,
        chain_ok=chain.ok, chain_n=chain.n_records,
        invariants_count=_inv.count(),
        may_execute=False,   # invariantِ سخت — هرگز True
    )


def run_shadow(*, seconds: float = 60.0, tick_interval: float = 5.0,
               clock=time.monotonic, sleep=time.sleep) -> ShadowReport:
    """یک shadow runِ bounded. هر tick_interval ثانیه یک health-check.

    پیش‌فرض ۶۰ ثانیه (demo/CI)؛ runِ واقعیِ C7 با seconds=36000 (۱۰h) و organismِ
    زنده. هرگز claim/آزمون اجرا نمی‌کند — فقط health-check + آمارِ زنجیره.
    """
    cfg = load_policy()
    t0 = clock()
    deadline = t0 + max(1.0, seconds)
    ticks: List[ShadowTick] = []
    cycle = 0
    may_ever = False
    while clock() < deadline:
        cycle += 1
        tk = _one_tick(cycle)
        ticks.append(tk)
        if tk.may_execute:
            may_ever = True   # نباید رخ دهد — invariant
        if clock() + tick_interval > deadline:
            break
        sleep(tick_interval)
    ended = clock()
    rep = ShadowReport(
        started_at=t0, ended_at=ended, duration_s=ended - t0,
        n_ticks=len(ticks), ticks=ticks,
        invariants_count=_inv.count(),
        chain_ok_at_end=ticks[-1].chain_ok if ticks else False,
        may_execute_ever_true=may_ever,
    )
    return rep.sign()


def format_report(rep: ShadowReport) -> str:
    lines = [
        "# Epistemic Shadow Run Report (ADR-039 C7)",
        f"",
        f"- duration: {rep.duration_s:.1f}s · ticks: {rep.n_ticks}",
        f"- invariants: {rep.invariants_count}",
        f"- receipt-chain ok at end: {rep.chain_ok_at_end}",
        f"- may_execute ever True: {rep.may_execute_ever_true}  (must be False)",
        f"- digest: {rep.digest[:24]}…",
        f"",
        f"## Honest note",
        f"این یک shadow run است — may_execute همیشه False، هیچ اثرِ خارجی. shadow runِ",
        f"واقعیِ ۱۰h نیازِ organismِ زنده دارد (owner-timed). digest برای tamper-evidence.",
    ]
    if rep.may_execute_ever_true:
        lines.append("\n🛑 INVARIANT VIOLATION: may_execute در طولِ run True شد!")
    return "\n".join(lines)
