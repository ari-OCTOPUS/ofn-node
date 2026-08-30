"""octopus_bridge — Local Trust & Execution Boundary.

یک مرزِ zero-trust که روی همان ماشینِ بیزنس‌ها (Orange Pi / DietPi) اجرا
می‌شود و بینِ control-plane ابریِ اختاپوس (هنوز آماده نیست) و ایجنت‌های
محلی (OFN :8794، Hypno :8895) میانجی‌گری می‌کند.

قانونِ اساسی: Bridge مجوزِ *حمل* می‌دهد؛ مجوزِ اجرای domain متعلقِ target
است. `OFN admit()` هرگز bypass نمی‌شود.

طراحی: stdlib-only، صفر dependency خارجی، outbound به‌طور پیش‌فرض خاموش.
جزئیات کامل: README.md
"""
from __future__ import annotations

__version__ = "0.1.0"
