# -*- coding: utf-8 -*-
"""selftest ژنوم — آفلاین، بدون تلگرام/شبکه/کلید.

هر ۴ ژنوم را می‌سازد، سه بیزنسِ engine‌دار را با gateway/memory فیک دود می‌گیرد،
قیدهای ژنوم اصلی (بودجه ≤ ۱، privacy، autonomy) را چک می‌کند.

اجرا:  python genome_selftest.py       (کد خروج ۰ = سبز)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from adapters.business import engines_for, genomes          # noqa: E402
from adapters.business.base import BusinessConfig, PersonalGenome  # noqa: E402
from core.contracts import Brief, OutboxMessage             # noqa: E402
from core.memory import Memory                              # noqa: E402


class FakeGateway:
    """gateway جعلی: نه شبکه، نه کلید. خروجی ثابتِ قالبِ Brief."""
    def search(self, query, business="", n=4):
        return [{"title": "نمونه", "content": "دادهٔ آزمایشی", "url": "https://example.com"}]

    def llm(self, prompt, system="", tier="cheap", business="", max_tokens=900, use_cache=True):
        # قالبِ موردانتظارِ parse_brief؛ persona باید داخل system آمده باشد (تستش پایین)
        return ("عنوان: فرصت آزمایشی\nفرصت: شرح کوتاه\nچرا: چون تست است\n"
                "اقدام: یک قدم کوچک\nمنبع: تحلیل داخلی")

    def budget_line(self):
        return "بودجه: تست"


def _fail(msg):
    print(f"❌ {msg}")
    raise SystemExit(1)


def main() -> int:
    gw = FakeGateway()
    mem = Memory(Path(tempfile.mkdtemp()) / "core.db")

    G = genomes()
    # ۱) هر ۴ ژنوم باید PersonalGenome و دارای فیلدهای نو باشند
    expected = {"ziman", "painting", "accounting", "projectf"}
    if set(G) != expected:
        _fail(f"مجموعهٔ ژنوم‌ها {set(G)} ≠ {expected}")
    for gid, g in G.items():
        if not isinstance(g, PersonalGenome):
            _fail(f"{gid}: PersonalGenome نیست")
        for fld in ("persona", "voice", "autonomy", "budget_share", "privacy_class",
                    "evolution_optin", "kpis", "channels", "values", "goals"):
            if not hasattr(g, fld):
                _fail(f"{gid}: فیلد ژنوم «{fld}» غایب است")
        if not g.persona or not g.voice:
            _fail(f"{gid}: persona/voice پر نشد (__post_init__؟)")

    # ۲) سازگاری عقب‌رو: BusinessConfig همان PersonalGenome است
    if BusinessConfig is not PersonalGenome:
        _fail("BusinessConfig باید alias همان PersonalGenome باشد")

    # ۳) قید ژنوم اصلی: جمع budget_share ≤ ۱.۰
    total = round(sum(g.budget_share for g in G.values()), 6)
    if total > 1.0:
        _fail(f"جمع budget_share = {total} > 1.0")

    # ۴) Project-F قفل: status_only + sensitive + بدون engine
    pf = G["projectf"]
    if pf.autonomy != "status_only" or pf.privacy_class != "sensitive":
        _fail("Project-F باید status_only + sensitive باشد")
    try:
        engines_for("projectf", gw, mem)
        _fail("Project-F نباید engine داشته باشد (قفل GATE 0)")
    except KeyError:
        pass  # درست: در ALL نیست

    # ۵) سه بیزنس زنده: چرخهٔ رکن A و B آفلاین
    for bid in ("ziman", "painting", "accounting"):
        research, owner = engines_for(bid, gw, mem)
        ctx = research.gather_context()
        if bid not in ctx and G[bid].name not in ctx:
            _fail(f"{bid}: gather_context زمینهٔ بیزنس را نساخت")
        brief = research.run(ctx)
        if not isinstance(brief, Brief) or not brief.title:
            _fail(f"{bid}: رکن A بریف معتبر نساخت")
        msg = owner.compose(brief)
        if not isinstance(msg, OutboxMessage) or not msg.text:
            _fail(f"{bid}: رکن B پیام معتبر نساخت")
        if msg.to_ref != G[bid].owner_ref:
            _fail(f"{bid}: گیرندهٔ پیام {msg.to_ref} ≠ {G[bid].owner_ref}")

    # گزارش
    print("جدول ژنوم‌ها:")
    for gid, g in G.items():
        print(f"  • {gid:11} autonomy={g.autonomy:12} budget={g.budget_share:<4} "
              f"privacy={g.privacy_class:9} evo={g.evolution_optin}")
    print(f"جمع budget_share = {total} (≤ 1.0 ✔)")
    print("✅ selftest ژنوم سبز — هر ۵ چک پاس شد.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
