#!/usr/bin/env python3
"""evolution.py — Doctor upgrades: 3 techniques from industry benchmarks.

منبع: DOCTOR-EVOLUTION-BENCHMARK-10systems.md §۳ (۵ adoption، ۳ اولِ کم‌ریسک).

۱. RFCArchive (MAP-Elites + DGM lineage): repertoireِ RFCها ایندکس‌شده بر حسبِ
   (نوعِ گلوگاه × اندام)، بهترین-در-هر-سلول. mine از آرشیو sample/mutate می‌کند.
   تکاملِ open-ended ولی کران‌دار (سقفِ اندازه، evict).
۲. measured_lift (AlphaEvolve/FunSearch): eval-harness در sandbox که lift واقعی
   را می‌سنجد؛ RFCِ زیرِ آستانه خودکار drop (به انسان نمی‌رسد).
۳. tournament_rank (Co-Scientist): چند RFC-variant → مسابقهٔ Elo/pairwise؛
   فقط بازمانده submit.

قوانین (نقض = رد): propose-only · sandbox · λ_persist منفی · human-append merge ·
بدونِ import از *_gate/chrono/money · بدونِ LLMِ گران (stub یا tier ارزان).
non-destructive: mine/propose/submit فعلی دست‌نخورده.
additive؛ stdlib-only؛ $0 آفلاین.
"""
from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent               # _ops/doctor
sys.path.insert(0, str(_HERE))
from doctor import LAMBDA_PERSIST  # noqa: E402 — §۴: تک‌منبع doctor.py، دست‌نخورده منفی


# ════════════════════════════════════════════════════════════════════════════════
# ۱. RFCArchive — MAP-Elites-style quality-diversity
# ════════════════════════════════════════════════════════════════════════════════
# سلول = (bottleneck_key × organ). بهترین-در-هر-سلول. سقفِ اندازه + evict.

@dataclass
class ArchiveCell:
    """یک سلولِ آرشیو: بهترین RFC برای این (key × organ)."""
    bottleneck_key: str
    organ: str
    rfc_id: str
    score: float               # measured lift یا heuristic
    fix: str = ""
    generation: int = 0        # DGM lineage: نسلِ mutation
    parent_id: str | None = None


@dataclass
class RFCArchive:
    """MAP-Elites: بهترین-در-هر-سلول. کران‌دار (sieve). sample/mutate برای mine.
    non-destructive: mine فعلی از این استفاده می‌کند ولی مجبور نیست."""
    cap: int = 100             # |archive|_max
    cells: dict[tuple[str, str], ArchiveCell] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.cells)

    def is_bounded(self) -> bool:
        return self.size <= self.cap

    def cell_key(self, bottleneck_key: str, organ: str) -> tuple[str, str]:
        return (bottleneck_key, organ or "_global")

    def insert(self, bottleneck_key: str, organ: str, rfc_id: str,
               score: float, fix: str = "", parent_id: str | None = None) -> bool:
        """insert اگر بهتر از موجود در سلول باشد. خروجی: inserted؟"""
        if self.size >= self.cap:
            self._evict()
        key = self.cell_key(bottleneck_key, organ)
        existing = self.cells.get(key)
        gen = (existing.generation + 1) if existing and existing.parent_id == parent_id else 0
        if existing is None or score > existing.score:
            self.cells[key] = ArchiveCell(
                bottleneck_key=bottleneck_key, organ=organ or "_global",
                rfc_id=rfc_id, score=score, fix=fix,
                generation=gen, parent_id=parent_id)
            return True
        return False

    def _evict(self) -> None:
        """evict کم‌امتیازترین سلول."""
        if not self.cells:
            return
        worst_key = min(self.cells, key=lambda k: self.cells[k].score)
        del self.cells[worst_key]

    def sample(self, rng: random.Random | None = None) -> ArchiveCell | None:
        """sample یک سلول (برای mutation). غالباً از بالا‌امتیازترین‌ها."""
        if not self.cells:
            return None
        r = rng or random.Random()
        # weighted by score (بالاتر = بیشتر)
        keys = list(self.cells.keys())
        weights = [max(0.01, self.cells[k].score) for k in keys]
        chosen_key = r.choices(keys, weights=weights, k=1)[0]
        return self.cells[chosen_key]

    def mutate(self, cell: ArchiveCell, rng: random.Random | None = None) -> dict:
        """mutate یک سلول → پیشنهادِ نو. stub: tweak fix.
        خروجی: {bottleneck_key, organ, fix, parent_id, generation}."""
        r = rng or random.Random()
        mutations = [
            f"{cell.fix} + guard اضافه",
            f"{cell.fix} + retry منطق",
            f"{cell.fix} (نسخهٔ سبک‌تر)",
        ]
        return {"bottleneck_key": cell.bottleneck_key, "organ": cell.organ,
                "fix": r.choice(mutations), "parent_id": cell.rfc_id,
                "generation": cell.generation + 1}

    def best_in_cell(self, bottleneck_key: str, organ: str) -> ArchiveCell | None:
        """بهترین RFC در یک سلول."""
        return self.cells.get(self.cell_key(bottleneck_key, organ))


# ════════════════════════════════════════════════════════════════════════════════
# ۲. measured_lift — AlphaEvolve/FunSearch eval-harness
# ════════════════════════════════════════════════════════════════════════════════

LIFT_DROP_THRESHOLD = 0.05    # RFC با lift<این → drop خودکار (به انسان نمی‌رسد)


def measured_lift(rfc: dict, eval_fn=None, baseline: dict | None = None) -> dict:
    """lift واقعی را در sandbox می‌سنجد. eval_fn قابل‌تزریق.
    خروجی: {lift, passed, dropped, detail}.
    زیرِ LIFT_DROP_THRESHOLD → drop خودکار (propose-only، به submit نمی‌رسد).
    stub پیش‌فرض: lift از evidence تخمین (در B2 با eval واقعی جایگزین)."""
    if eval_fn is None:
        eval_fn = _default_eval
    try:
        result = eval_fn(rfc, baseline or {})
    except Exception as e:  # noqa: BLE001 — eval fail = drop (fail-closed)
        return {"lift": 0.0, "passed": False, "dropped": True,
                "detail": f"eval error: {e}"}
    lift = float(result.get("lift", 0.0))
    passed = lift >= LIFT_DROP_THRESHOLD
    return {"lift": lift, "passed": passed,
            "dropped": not passed, "detail": result.get("detail", "")}


def _default_eval(rfc: dict, baseline: dict) -> dict:
    """stub: lift از evidence/severity تخمین. در B2: eval واقعی روی held-out.
    این stub ساده است ولی ساختارِ درست دارد."""
    severity = (rfc.get("evidence") or {}).get("severity", "high")
    # severity بالا = پتانسیلِ lift بیشتر (ولی stub، نه اندازه‌گیریِ واقعی)
    sev_score = {"critical": 0.5, "high": 0.3, "medium": 0.15, "low": 0.04}.get(severity, 0.1)
    # λ_persist جریمه اگر fix به uptime اشاره کند
    fix_lower = str(rfc.get("fix", "")).lower()
    if any(w in fix_lower for w in ("uptime", "keep-beating")):
        sev_score = max(0.0, sev_score + LAMBDA_PERSIST * 0.3)
    return {"lift": sev_score, "detail": f"stub: severity={severity}"}


# ════════════════════════════════════════════════════════════════════════════════
# ۳. tournament_rank — Co-Scientist Elo/pairwise
# ════════════════════════════════════════════════════════════════════════════════

INITIAL_ELO = 1000.0
K_FACTOR = 32.0


def tournament_rank(rfcs: list[dict], judge_fn=None,
                    rng: random.Random | None = None) -> list[dict]:
    """چند RFC-variant → مسابقهٔ Elo/pairwise.
    judge_fn(a, b) → 'a'|'b'|'draw'. stub پیش‌فرض: مقایسهٔ score.
    خروجی: rfcs با elo رتبه‌بندی‌شده (desc). فقط بازمانده submit می‌شود."""
    if len(rfcs) <= 1:
        for r in rfcs:
            r["elo"] = INITIAL_ELO
        return list(rfcs)
    j_fn = judge_fn or _default_judge
    r = rng or random.Random(42)
    elos = {id(rfc): INITIAL_ELO for rfc in rfcs}
    # round-robin pairwise
    for i in range(len(rfcs)):
        for j in range(i + 1, len(rfcs)):
            a, b = rfcs[i], rfcs[j]
            winner = j_fn(a, b)
            ea = 1.0 / (1.0 + 10 ** ((elos[id(b)] - elos[id(a)]) / 400.0))
            sa = 1.0 if winner == "a" else (0.0 if winner == "b" else 0.5)
            elos[id(a)] += K_FACTOR * (sa - ea)
            elos[id(b)] += K_FACTOR * ((1 - sa) - (1 - ea))
    for rfc in rfcs:
        rfc["elo"] = round(elos[id(rfc)], 1)
    rfcs.sort(key=lambda x: x["elo"], reverse=True)
    return rfcs


def _default_judge(a: dict, b: dict) -> str:
    """stub: مقایسهٔ score/lift. در B2: LLM judge یا eval واقعی."""
    sa = float(a.get("score", a.get("lift", 0.5)))
    sb = float(b.get("score", b.get("lift", 0.5)))
    if sa > sb:
        return "a"
    if sb > sa:
        return "b"
    return "draw"


def survivor(rfcs: list[dict], judge_fn=None,
             top_k: int = 1) -> list[dict]:
    """فقط top-k بازمانده از tournament را برگردان (برای submit).
    پیش‌فرض: فقط برنده (top_k=1)."""
    ranked = tournament_rank(rfcs, judge_fn=judge_fn)
    return ranked[:max(1, top_k)]
