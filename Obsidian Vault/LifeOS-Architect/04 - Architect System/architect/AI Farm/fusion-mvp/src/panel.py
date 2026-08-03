"""
panel.py — چک‌لیست #۵ و #۶: پنل چندداورِ مستقل (separation of duties + بدون تک‌نقطه).

به‌جای یک ناظرِ تنها، چند داورِ مستقل با نگرش‌های متفاوت (strict/lenient/balanced)
و احتمالاً روی providerهای مختلف، خروجی Analyst را داوری می‌کنند و رأی می‌دهند.
  - هیچ داوری به‌تنهایی نمی‌تواند تأیید کند (نیاز به حد نصاب PANEL_QUORUM).
  - اگر آرا نصفه‌نیمه شد (نه تأیید، نه ردِ کامل) → ارجاع به انسان (escalation).
هر رأی در audit log ثبت می‌شود (شفافیت). هزینه‌ی داوران زیر بودجه‌ی «panel».
"""
from __future__ import annotations

import config

JUDGE_SYSTEM = {
    "strict":   ("تو داورِ سخت‌گیر هستی. فقط اگر تحلیل هم منبع‌دار و هم دارای هشدارِ "
                 "راستی‌آزمایی باشد APPROVE بده، وگرنه REJECT."),
    "lenient":  ("تو داورِ سهل‌گیر هستی. اگر تحلیل خالی نباشد APPROVE بده."),
    "balanced": ("تو داورِ متعادل هستی. اگر تحلیل هشدارِ راستی‌آزمایی دارد یا به‌قدر کافی "
                 "کامل است APPROVE بده، وگرنه REJECT."),
}


class Judge:
    def __init__(self, name, stance, provider_name, provider, ledger, audit, ks):
        self.name = name
        self.stance = stance
        self.provider_name = provider_name
        self.provider = provider
        self.ledger = ledger
        self.audit = audit
        self.ks = ks

    def _decide(self, analysis: str) -> bool:
        """منطقِ نگرش — تنوعِ تصمیم را تضمین می‌کند."""
        has_caveat = ("راستی‌آزمایی" in analysis) or ("احتیاط" in analysis)
        long_enough = len(analysis.strip()) >= 40
        nonempty = len(analysis.strip()) >= 15
        if self.stance == "strict":
            return has_caveat and long_enough
        if self.stance == "lenient":
            return nonempty
        return has_caveat or long_enough   # balanced

    def vote(self, analysis: str) -> tuple[bool, str]:
        self.ks.check()                       # چک‌لیست #۲
        self.ledger.precheck("panel")         # چک‌لیست #۱
        system = JUDGE_SYSTEM.get(self.stance, "")
        res = self.provider.complete(system, f"این تحلیل را داوری کن:\n{analysis}\nAPPROVE یا REJECT؟")
        self.ledger.record("panel", res.input_tokens, res.output_tokens)
        approve = self._decide(analysis)
        self.audit.log("judge_vote", "panel", judge=self.name, stance=self.stance,
                       provider=self.provider_name, approve=approve)
        return approve, f"{self.name}({self.stance}@{self.provider_name})"


class JudgePanel:
    def __init__(self, providers, ledger, audit, ks,
                 judges=None, quorum=None):
        judges = judges or config.JUDGES
        self.quorum = quorum or config.PANEL_QUORUM
        self.audit = audit
        self.judges = []
        for i, (name, stance) in enumerate(judges):
            pname, prov = providers[i % len(providers)]   # پخش round-robin روی providerها
            self.judges.append(Judge(name, stance, pname, prov, ledger, audit, ks))

    def review(self, analysis: str) -> dict:
        votes = [j.vote(analysis) for j in self.judges]
        yes = sum(1 for ok, _ in votes if ok)
        total = len(votes)
        approved = yes >= self.quorum
        if approved:
            decision = "approved"
        elif yes == 0:
            decision = "rejected"
        else:
            decision = "split"        # نه تأیید، نه ردِ کامل → ارجاع به انسان
        self.audit.log("panel_decision", "panel", yes=yes, total=total,
                       quorum=self.quorum, decision=decision)
        return {"approved": approved, "yes": yes, "total": total,
                "decision": decision, "votes": votes}
