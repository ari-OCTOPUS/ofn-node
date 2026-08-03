from __future__ import annotations
import datetime as _dt
PRICES = {
    "offline": (0.0, 0.0), "haiku": (0.80, 4.00), "sonnet": (3.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.50, 10.00),
    "deepseek-reasoner": (0.55, 2.19), "deepseek": (0.27, 1.10),
}
_DEFAULT_PRICE = (1.0, 3.0)
def _price_for(model):
    m = (model or "").lower()
    for key, p in PRICES.items():
        if key in m:
            return p
    return _DEFAULT_PRICE
def estimate_tokens(t): return max(1, len(t or "") // 4)
def estimate_cost(model, i, o):
    pin, pout = _price_for(model)
    return i/1_000_000*pin + o/1_000_000*pout
class BudgetManager:
    def __init__(s, db, daily_usd=1.0, monthly_usd=20.0):
        s.db=db; s.daily=float(daily_usd); s.monthly=float(monthly_usd)
    def record(s, model, i, o, command=""):
        cost=estimate_cost(model,i,o)
        if s.db: s.db.record_ai_usage(model,i,o,round(cost,6),command)
        return cost
    def record_text(s, model, prompt, output, command=""):
        return s.record(model, estimate_tokens(prompt), estimate_tokens(output), command)
    def spent_today(s):
        return s.db.ai_usage_sum(_dt.date.today().isoformat()) if s.db else 0.0
    def spent_month(s):
        return s.db.ai_usage_sum(_dt.date.today().replace(day=1).isoformat()) if s.db else 0.0
    def can_spend(s): return s.spent_today()<s.daily and s.spent_month()<s.monthly
    def status(s):
        return {"spent_today":round(s.spent_today(),4),"daily_limit":s.daily,
                "spent_month":round(s.spent_month(),4),"monthly_limit":s.monthly,"ok":s.can_spend()}
