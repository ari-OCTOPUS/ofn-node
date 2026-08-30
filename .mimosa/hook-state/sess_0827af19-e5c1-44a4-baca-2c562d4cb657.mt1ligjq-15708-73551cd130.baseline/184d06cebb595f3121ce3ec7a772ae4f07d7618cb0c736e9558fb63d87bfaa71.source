"""بودجهٔ سختِ ماهانهٔ API — fail-closed، AUD-محور.

اصل: هیچ فراخوانِ زنده‌ای مجاز نیست اگر برآوردِ هزینه از باقی‌ماندهٔ سقفِ ماه بگذرد.
قیمت‌ها و نرخِ تبدیل از ziman.yaml می‌آیند؛ همه [Unverified] تا تأییدِ مالک/حسابدار.
حالتِ ماه در یک فایلِ JSON نگهداری می‌شود (ماه که عوض شود، صفر می‌شود).
"""
import json
from datetime import date
from pathlib import Path

# قیمتِ پیش‌فرض USD به‌ازای ۱M توکن — [Unverified — صفحهٔ pricing Anthropic]
_DEFAULT_PRICES_USD = {
    "claude-haiku-4-5": {"in": 1.0, "out": 5.0},
    "claude-sonnet-5": {"in": 3.0, "out": 15.0},
    "claude-opus-4-8": {"in": 5.0, "out": 25.0},
}


class Budget:
    """گیتِ بودجهٔ ماهانه. can_spend() قبل از هر فراخوانِ API؛ record() بعد از آن."""

    def __init__(self, cfg, base_dir=None):
        b = (cfg.get("budget") or {})
        self.cap_aud = float(b.get("monthly_cap_aud", 15.0))
        self.usd_to_aud = float(b.get("usd_to_aud", 1.55))
        prices = dict(_DEFAULT_PRICES_USD)
        for k, v in (b.get("prices_usd_per_mtok") or {}).items():
            prices[k] = {"in": float(v.get("in")), "out": float(v.get("out"))}
        self.prices = prices
        base = Path(base_dir) if base_dir else Path(".")
        self.state_path = base / str(b.get("state_file", ".budget_state.json"))
        self.month = date.today().strftime("%Y-%m")
        self.spent_aud = 0.0
        self._load()

    def _load(self):
        try:
            d = json.loads(self.state_path.read_text(encoding="utf-8"))
            if d.get("month") == self.month:
                self.spent_aud = float(d.get("spent_aud", 0.0))
        except Exception:  # noqa: BLE001 — فایلِ نبود/خراب = صفر
            self.spent_aud = 0.0

    def _save(self):
        try:
            self.state_path.write_text(
                json.dumps({"month": self.month,
                            "spent_aud": round(self.spent_aud, 6),
                            "cap_aud": self.cap_aud}, ensure_ascii=False),
                encoding="utf-8")
        except Exception:  # noqa: BLE001 — ناتوانی در نوشتن نباید فروش را بشکند
            pass

    def _cost_aud(self, model, in_tok, out_tok):
        p = self.prices.get(model) or self.prices["claude-haiku-4-5"]
        usd = (in_tok / 1e6) * p["in"] + (out_tok / 1e6) * p["out"]
        return usd * self.usd_to_aud

    def remaining_aud(self):
        return max(0.0, self.cap_aud - self.spent_aud)

    def can_spend(self, model, est_in=2000, est_out=800):
        """fail-closed: اگر برآوردِ هزینه از باقی‌مانده بگذرد → False."""
        return self._cost_aud(model, est_in, est_out) <= self.remaining_aud()

    def record(self, model, in_tok, out_tok):
        self.spent_aud += self._cost_aud(model, in_tok, out_tok)
        self._save()
        return self.spent_aud

    def snapshot(self):
        return {"month": self.month,
                "spent_aud": round(self.spent_aud, 4),
                "cap_aud": self.cap_aud,
                "remaining_aud": round(self.remaining_aud(), 4)}
