"""تستِ گاردِ پارامترهای منحط در core.scores (log(0) دیگر نمی‌ترکد)."""
from tests import _bootstrap  # noqa: F401

import math
import unittest

from core.scores import compute_scores_from_model


class TestDegenerateParams(unittest.TestCase):
    def test_zero_variance_params_do_not_raise(self):
        """se=0, lam=0 → واریانسِ صفر؛ قبلاً ValueError: math domain error."""
        s = compute_scores_from_model(rho=0.5, lam=0.0, se=0.0, sz=0.05, sd=0.1)
        for name in ("sms", "sls", "pcai"):
            v = getattr(s, name)
            self.assertTrue(math.isfinite(v), f"{name} باید متناهی باشد، شد {v}")

    def test_normal_params_unchanged(self):
        """پارامترهای عادی نباید تحتِ‌تأثیرِ کفِ واریانس قرار بگیرند."""
        s = compute_scores_from_model(rho=0.5, lam=0.5, se=0.1, sz=0.05, sd=0.1)
        for name in ("sms", "sls", "pcai"):
            self.assertTrue(math.isfinite(getattr(s, name)))
        # sms = Δ_self باید مثبتِ معنادار باشد (خودمدل‌سازی ارزش دارد)
        self.assertGreater(s.sms, 0.0)


if __name__ == "__main__":
    unittest.main()
