"""shadow_rollout.py — ADR-040 Phase 6: dual-read shadow comparison.

برای ۲۴h فقط-owner: همان سؤال را هم به Hub (درگاهِ واحد) و هم به collaborator
(مسیرِ legacy) می‌فرستد و پاسخ‌ها را side-by-side ثبت می‌کند تا مالک ببیند آیا
مسیرِ جدید با قدیم هم‌خوان است. **هیچ اثرِ خارجی** — هر دو مسیر observe+propose
هستند (external_effect=False).

خروجی: یک گزارشِ مقایسه‌ای + فایلِ JSONL برای ممیزی.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class DualRead:
    """یک مقایسهٔ Hub vs collab روی یک سؤال."""
    question: str
    hub_route: str
    hub_answer: str
    hub_external_effect: bool
    collab_kind: str
    collab_answer: str
    collab_external_effect: bool
    answer_overlap: float     # 0..1 — شباهتِ سطحی
    both_safe: bool           # هر دو external_effect=False


def _overlap(a: str, b: str) -> float:
    """شباهتِ سطحیِ Jaccard روی setِ کلمات (صادقانه: metric خام)."""
    sa = set(str(a or "").split())
    sb = set(str(b or "").split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# سؤال‌های probe — متنوع روی intentهای مختلف.
DEFAULT_PROBES: Tuple[str, ...] = (
    "وضعیت چیست؟",
    "هدف چیست؟",
    "موانع چیست؟",
    "از چی تشکیل شدی؟",
    "حافظه cite-only چطور کار می‌کند؟",
    "فرضیه و شواهد چیست؟",
)


def run_shadow(probes: Tuple[str, ...] = DEFAULT_PROBES, *,
               state_dir: Optional[str] = None) -> List[DualRead]:
    """هر probe را به Hub و collab بفرست و مقایسه کن."""
    import sys
    ops = Path(__file__).resolve().parent.parent
    if str(ops) not in sys.path:
        sys.path.insert(0, str(ops))
    from conversation_hub import handle as hub_handle
    from owner_console import collaborator

    out: List[DualRead] = []
    for q in probes:
        # Hub path
        try:
            hub_reply = hub_handle({"message_id": f"shadow-{int(time.time())}",
                                    "text": q, "mode": "auto"})
            hub_route = hub_reply.route
            hub_ans = hub_reply.answer
            hub_eff = hub_reply.external_effect
        except Exception as exc:  # noqa: BLE001
            hub_route, hub_ans, hub_eff = "error", f"[hub error: {type(exc).__name__}]", False
        # collab path (legacy)
        try:
            collab_reply = collaborator.handle(q, state_dir=Path(state_dir) if state_dir else None)
            collab_kind = str(collab_reply.get("kind") or "?")
            collab_ans = str(collab_reply.get("text") or "")
            collab_eff = bool(collab_reply.get("external_effect", False))
        except Exception as exc:  # noqa: BLE001
            collab_kind, collab_ans, collab_eff = "error", f"[collab error: {type(exc).__name__}]", False
        out.append(DualRead(
            question=q, hub_route=hub_route, hub_answer=hub_ans[:400],
            hub_external_effect=hub_eff,
            collab_kind=collab_kind, collab_answer=collab_ans[:400],
            collab_external_effect=collab_eff,
            answer_overlap=round(_overlap(hub_ans, collab_ans), 3),
            both_safe=(hub_eff is False and collab_eff is False),
        ))
    return out


@dataclass(frozen=True)
class ShadowReport:
    n_probes: int
    all_safe: bool                  # هر دو مسیر همه‌جا external_effect=False
    mean_overlap: float
    reads: List[DualRead] = field(default_factory=list)


def summarize(reads: List[DualRead]) -> ShadowReport:
    n = len(reads)
    safe = all(r.both_safe for r in reads) if reads else True
    mean_ov = (sum(r.answer_overlap for r in reads) / n) if n else 0.0
    return ShadowReport(n_probes=n, all_safe=safe,
                        mean_overlap=round(mean_ov, 3), reads=reads)


def format_report(rep: ShadowReport) -> str:
    lines = [
        f"# Shadow Rollout Report (ADR-040 Phase 6)",
        f"",
        f"- probes: {rep.n_probes}",
        f"- all_safe (هر دو مسیر external_effect=False): {'✅' if rep.all_safe else '🛑'}",
        f"- mean answer overlap (Hub vs collab): {rep.mean_overlap}",
        f"",
        f"## Per-probe",
    ]
    for r in rep.reads:
        lines.append(f"")
        lines.append(f"### «{r.question}»")
        lines.append(f"  · Hub: route={r.hub_route} · overlap={r.answer_overlap} · safe={r.both_safe}")
        lines.append(f"  · Hub answer: {r.hub_answer[:120]}")
        lines.append(f"  · collab: kind={r.collab_kind}")
        lines.append(f"  · collab answer: {r.collab_answer[:120]}")
    lines.append(f"")
    lines.append(f"## Honest note")
    lines.append(f"overlap یک metric خامِ Jaccard روی کلمات است — نه معیارِ کیفیت. "
                 f"هدفِ shadow فقط این است که هر دو مسیر امن (external_effect=False) "
                 f"بمانند و جوابِ تهی/خطا ندهند. تصمیمِ cut-over با مالک.")
    return "\n".join(lines)


def write_jsonl(rep: ShadowReport, path: Path) -> None:
    """ثبتِ JSONL برای ممیزی (append-only)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rep.reads:
            f.write(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "question": r.question, "hub_route": r.hub_route,
                "hub_answer": r.hub_answer, "hub_external_effect": r.hub_external_effect,
                "collab_kind": r.collab_kind, "collab_answer": r.collab_answer,
                "collab_external_effect": r.collab_external_effect,
                "answer_overlap": r.answer_overlap, "both_safe": r.both_safe,
            }, ensure_ascii=False) + "\n")
