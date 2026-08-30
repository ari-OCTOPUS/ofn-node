#!/usr/bin/env python3
"""تستِ ایمنیِ ژنوم (تری‌اسکن 2026-07-17): C1 pinِ مسیرِ لجر + B1 verifyِ درون‌حلقه.

C1: مسیرِ نوشتنِ لجر به absolute canonical پین شد — worktreeی با ORG_ROOTِ متفاوت
    دیگر لجرِ زنده را fork نمی‌کند، ولی override صریحِ GENOME_DIR (تست) هنوز برنده است.
B1: حلقهٔ روزانه زنجیرهٔ هشِ لجر را verify می‌کند — فقط‌خواندنی، هرگز تغییر نمی‌دهد.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("genome-safety")
_OPS = (harness.SELF_OPS)
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402


# ── C1: pinِ مسیرِ لجر ──────────────────────────────────────────────────────────
def t_c1_env_override_still_wins():
    """harness → GENOME_DIR=sandbox؛ pin نباید override را بشکند (وگرنه تست‌ها به لجرِ واقعی می‌نویسند)."""
    assert str(opslib.GENOME_DIR) == ENV["GENOME_DIR"], (str(opslib.GENOME_DIR), ENV["GENOME_DIR"])


def t_c1_pin_ignores_org_root():
    """بدونِ GENOME_DIR env و با ORG_ROOTِ جعلی → GENOME_DIR باید canonical باشد، نه worktree."""
    env = dict(os.environ)
    env["ORG_ROOT"] = r"C:\fake\worktree"
    env.pop("GENOME_DIR", None)
    env.pop("OPS_DIR", None)
    code = ("import sys; sys.path.insert(0, r'%s'); import opslib; print(opslib.GENOME_DIR)"
            % str(_OPS / "budget"))
    out = subprocess.run([sys.executable, "-X", "utf8", "-c", code],
                         capture_output=True, text=True, env=env, timeout=30)
    res = (out.stdout or "").strip().splitlines()[-1] if out.stdout.strip() else ""
    assert res, f"subprocess چیزی چاپ نکرد: {out.stderr[-200:]}"
    assert "fake" not in res.lower(), f"ORG_ROOTِ جعلی نباید لجر را fork کند: {res}"
    assert res.replace("/", "\\").endswith(r"07 - Knowledge\genome-system"), res
    assert "F:\\backup" in res.replace("/", "\\"), res


# ── B1: verifyِ درون‌حلقه (فقط‌خواندنی) ──────────────────────────────────────────
def t_b1_verify_is_readonly():
    """genome_ledger().verify() = (bool, str)، بدونِ تغییرِ لجر (تعدادِ ردیف ثابت)."""
    lg = opslib.genome_ledger()
    before = sum(1 for _ in lg.iter_events())
    ok, reason = lg.verify()
    assert isinstance(ok, bool) and isinstance(reason, str), (ok, reason)
    after = sum(1 for _ in lg.iter_events())
    assert after == before, f"verify نباید ردیف اضافه کند: {before} → {after}"


def t_b1_organism_daily_calls_verify():
    """ساختاری: بلوکِ روزانهٔ organism.py verify را صدا می‌زند و ledger_ok را ثبت می‌کند."""
    src = (_OPS / "organism.py").read_text("utf-8")
    assert "genome_ledger().verify()" in src, "بلوکِ روزانه باید لجر را verify کند"
    assert "ledger_ok" in src
    # خطِ قرمز: فقط بلوکِ verifyِ من (پنجرهٔ ~۳۰۰ کاراکتری) نباید بنویسد — نه بلوکِ روزانهٔ
    # مجاورِ ledger_note که ردیفِ خلاصهٔ روزانه را می‌نویسد (پیش‌موجود، جدا از verify).
    i = src.index("genome_ledger().verify()")
    seg = src[i:i + 300]
    for forbidden in (".append(", "ledger_note", ".write("):
        assert forbidden not in seg, f"بلوکِ verify نباید بنویسد: {forbidden}"


# ── C2: بازنشستگیِ سیستم‌های مردهٔ ژنوم ──────────────────────────────────────────
def t_c2_status_retired_but_ledger_scoped():
    """STATUS.json ژنوم-لوپ retired است، ولی retired_note صراحتاً لجر را زنده نگه می‌دارد."""
    import json
    st = json.loads((harness.REAL_VAULT / "07 - Knowledge" / "genome-system"
                     / "STATUS.json").read_text("utf-8"))
    assert st["status"] == "retired" and st["epistemic_status"] == "retired", st
    assert "retired_note" in st and "ledger" in st["retired_note"].lower(), \
        "note باید صراحتاً بگوید لجر زنده می‌ماند (نه کلِ دایرکتوری)"


def t_c2_genome_ledger_still_resolves():
    """قلبِ ژنوم — لجر — همچنان resolve/verify می‌شود (retire فقط loop-app را بست، نه دایرکتوری)."""
    ok, _ = opslib.genome_ledger().verify()
    assert isinstance(ok, bool)


def t_c2_genome_guard_archived_no_live_caller():
    """genome_guard در _Archive است و هیچ فایلِ زنده‌ای subprocess صدایش نمی‌زند."""
    root = harness.REAL_VAULT
    gs = (root / "04 - Architect System" / "scripts" / "governor_shadow.py").read_text("utf-8")
    assert "genome_guard.py\")" not in gs and "SCRIPTS / \"genome_guard" not in gs, \
        "فراخوانیِ زندهٔ genome_guard باید حذف شده باشد"
    assert not (root / "04 - Architect System" / "scripts" / "genome_guard.py").exists(), \
        "genome_guard باید از scripts رفته باشد"
    assert (root / "_Archive" / "scripts" / "genome_guard.py").exists(), \
        "genome_guard باید در _Archive باشد (حذف نشده)"


if __name__ == "__main__":
    failed = harness.run([
        ("[C1] override env برنده می‌ماند", t_c1_env_override_still_wins),
        ("[C1] pin ORG_ROOT را نادیده می‌گیرد", t_c1_pin_ignores_org_root),
        ("[B1] verify فقط‌خواندنی است", t_b1_verify_is_readonly),
        ("[B1] بلوکِ روزانه verify می‌کند", t_b1_organism_daily_calls_verify),
        ("[C2] STATUS retired، لجر scoped", t_c2_status_retired_but_ledger_scoped),
        ("[C2] لجر همچنان resolve می‌شود", t_c2_genome_ledger_still_resolves),
        ("[C2] genome_guard آرشیو شد بی‌caller", t_c2_genome_guard_archived_no_live_caller),
    ])
    sys.exit(1 if failed else 0)
