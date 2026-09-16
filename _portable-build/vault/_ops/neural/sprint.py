#!/usr/bin/env python3
"""sprint.py — NI-7: SprintContract (Anthropic Harness).

هر sprint = scope + budget + deadline + context_reset.
Anthropic's pattern: bounded task unit with context clear.

TINV-5 (ORGANISM-SPEC §۲.۵): هیچ ماژولی wall-clock مستقیم نمی‌خواند — زمان از
beat/broadcast می‌آید (لازم برای determinism/replay). پیش از این، deadline به‌صورتِ
ساعتِ دیواری بود (`time.time() + budget_beats*60`) که نشتی بود. حالا بودجه و
deadline بر حسبِ beat_seq بیان می‌شوند. منبعِ beat از طریقِ param تزریق می‌شود
(`start_beat` / `now_beat`)، نه خواندنِ مستقیمِ ساعت. fail-soft: اگر beat تزریق
نشود، شمارشِ داخلیِ `_beats_used` (که ذاتاً beat-محور است) به‌کار می‌آید.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hooks import HookBus


@dataclass
class SprintContract:
    """یک sprintِ کران‌دار (Anthropic Harness pattern).

    زمان همگی بر حسبِ beat_seq است (نه wall-clock). `start_beat` تزریقی است؛
    اگر صفر بماند، SprintRunner از شمارشِ داخلیِ beat استفاده می‌کند (fail-soft)."""
    sprint_id: str
    scope: str              # «چه سوال/گلوگاهی»
    budget_beats: int = 10  # max beats (واحدِ زمان = beat)
    budget_tokens: int = 100
    start_beat: int = 0     # beat_seq آغازِ sprint (تزریقی؛ 0 = fallback داخلی)
    deadline_beat: int = 0  # beat_seq انقضا (تزریقی؛ 0 = start_beat + budget_beats)
    context_reset: bool = True  # بعد از sprint، context پاک

    def __post_init__(self):
        # deadline بر حسبِ beat، نه time.time() — TINV-5
        if self.deadline_beat == 0 and self.start_beat > 0:
            self.deadline_beat = self.start_beat + self.budget_beats


@dataclass
class SprintResult:
    """خروجیِ یک sprint."""
    sprint_id: str
    completed: bool
    timed_out: bool
    budget_exhausted: bool
    beats_used: int
    tokens_used: int
    insights: list[str] = field(default_factory=list)
    context_cleared: bool = False


class SprintRunner:
    """اجرای sprint با کران. context_reset بعد از هر sprint.

    زمان از beat_seq می‌آید (تزریقی در tick/finish)؛ هرگز time.time() نمی‌خواند."""

    def __init__(self):
        self._current: SprintContract | None = None
        self._beats_used = 0
        self._tokens_used = 0
        self._insights: list[str] = []
        self._hooks: "HookBus | None" = None

    def set_hooks(self, hooks: "HookBus") -> None:
        self._hooks = hooks

    def start(self, contract: SprintContract, start_beat: int = 0) -> None:
        """آغازِ sprint. start_beat اختیاری (تزریقِ منبعِ زمان، نه خواندنِ مستقیم).

        اگر start_beat تزریق شود و contract.start_beat صفر باشد، آن را ست می‌کند
        و deadline_beat را (در صورتِ صفر) محاسبه می‌کند. fail-soft: اگر هیچ beat
        تزریق نشود، انقضا فقط بر حسبِ budget_beats از طریقِ شمارشِ داخلی چک می‌شود.
        """
        if start_beat > 0 and contract.start_beat == 0:
            contract.start_beat = start_beat
            if contract.deadline_beat == 0:
                contract.deadline_beat = start_beat + contract.budget_beats
        self._current = contract
        self._beats_used = 0
        self._tokens_used = 0
        self._insights = []
        if self._hooks:
            self._hooks.fire("pre_sprint", {"sprint_id": contract.sprint_id,
                                             "scope": contract.scope})

    def tick(self, tokens: int = 0, insight: str = "", now_beat: int = 0) -> bool:
        """یک beat از sprint. خروجی: continue؟ False = sprint تمام.

        now_beat: beat_seq جاری (تزریقِ منبعِ زمان — TINV-5). اگر 0 باشد،
        انقضای wall-clock چک نمی‌شود و فقط budget شمارشی استفاده می‌شود (fail-soft)."""
        if self._current is None:
            return False
        self._beats_used += 1
        self._tokens_used += tokens
        if insight:
            self._insights.append(insight)

        # budget شمارشی (همیشه در دسترس — beat-محور، نه wall-clock)
        if self._beats_used >= self._current.budget_beats:
            return False
        if self._tokens_used >= self._current.budget_tokens:
            return False
        # انقضا بر حسبِ beat_seq (تزریقی) — فقط اگر منبعِ beat در دسترس باشد
        if now_beat > 0 and self._current.deadline_beat > 0 \
                and now_beat >= self._current.deadline_beat:
            return False
        return True

    def finish(self, now_beat: int = 0) -> SprintResult:
        """پایانِ sprint. context reset.

        now_beat: beat_seq جاری (تزریقی). اگر 0 باشد، timed_out بر اساسِ
        شمارشِ داخلی ارزیابی می‌شود (fail-soft)."""
        if self._current is None:
            return SprintResult(sprint_id="none", completed=False,
                                timed_out=False, budget_exhausted=False,
                                beats_used=0, tokens_used=0)
        c = self._current
        # انقضا: اگر beat تزریقی داریم، از deadline_beat؛ وگرنه از budget شمارشی
        if now_beat > 0 and c.deadline_beat > 0:
            timed_out = now_beat >= c.deadline_beat
        else:
            timed_out = self._beats_used >= c.budget_beats
        result = SprintResult(
            sprint_id=c.sprint_id,
            completed=(self._beats_used < c.budget_beats
                       and self._tokens_used < c.budget_tokens
                       and not timed_out),
            timed_out=timed_out,
            budget_exhausted=(self._tokens_used >= c.budget_tokens),
            beats_used=self._beats_used, tokens_used=self._tokens_used,
            insights=list(self._insights),
            context_cleared=c.context_reset)
        if self._hooks:
            self._hooks.fire("post_sprint", {"sprint_id": c.sprint_id,
                                              "result": result.completed})
        self._current = None  # context reset
        self._beats_used = 0
        self._tokens_used = 0
        self._insights = []
        return result

    @property
    def is_active(self) -> bool:
        return self._current is not None
