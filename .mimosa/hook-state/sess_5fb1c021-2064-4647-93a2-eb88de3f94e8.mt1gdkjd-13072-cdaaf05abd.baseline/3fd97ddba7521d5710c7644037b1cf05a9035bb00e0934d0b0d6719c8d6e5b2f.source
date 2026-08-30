#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_scope_guard — محدوده و containment.

این فایل بعد از یک **جهشِ ناموفق** نوشته شد: جایگزینیِ `contained()` با
زیررشته هیچ تستی را قرمز نکرد، یعنی گارد بی‌دندان بود. علتش این بود که
مسیرهای فرارِ `test_flow` همگی زودتر (در طبقه‌بند یا در `resolve_within`) گرفته
می‌شدند، و تنها موردی که containment را از زیررشته جدا می‌کند — **پیشوندِ
همسایه** — اصلاً سنجیده نمی‌شد.

درس: جهش فقط وقتی معنا دارد که تست دقیقاً همان تمایزی را بسنجد که گارد
می‌سازد؛ وگرنه جهشِ سبز یعنی «این خط را کسی نمی‌بیند».
"""
import sys
from pathlib import Path

import bridge_harness

import scope_guard  # noqa: E402

ENV = bridge_harness.setup("scope")
ROOT = ENV["root"]
for _d in ("workspace", "workspace-evil", "workspace/sub", "reports"):
    (ROOT / _d).mkdir(parents=True, exist_ok=True)


def _ok(rel, scope=("workspace",)):
    return scope_guard.is_allowed(rel, sandbox_root=ROOT, allowed_scope=list(scope))


# ── تمایزی که containment می‌سازد و زیررشته نمی‌سازد ────────────────────────
def t_sibling_prefix_is_not_containment():
    """`workspace-evil` با startswith داخلِ `workspace` دیده می‌شود — نباید."""
    assert _ok("workspace/ok.md") is True
    assert _ok("workspace-evil/bad.md") is False


def t_contained_rejects_equal_paths():
    """ریشه با خودش contained نیست — `len(cp) > len(pp)`."""
    assert scope_guard.contained(ROOT, ROOT) is False
    assert scope_guard.contained(ROOT / "workspace", ROOT) is True


def t_contained_is_case_insensitive_on_this_platform():
    a = ROOT / "WORKSPACE" / "x.md"
    assert scope_guard.contained(a, ROOT / "workspace") is True


def t_contained_rejects_unrelated_trees():
    assert scope_guard.contained(Path("C:/other/x.md"), ROOT) is False


# ── فرارها ─────────────────────────────────────────────────────────────────
def t_dotdot_escape_is_rejected():
    for bad in ("workspace/../../out.md", "workspace/../../../out.md",
                "workspace/sub/../../../out.md"):
        assert _ok(bad) is False, bad


def t_absolute_drive_unc_and_nul_are_rejected():
    for bad in ("/etc/passwd", "//server/share/x", "C:/x.md", r"D:\x.md",
                "work\x00space/x.md", "", "   "):
        assert _ok(bad) is False, repr(bad)


def t_backslash_and_mixed_separators_are_normalised():
    assert _ok(r"workspace\sub\ok.md") is True
    assert _ok(r"workspace\..\..\out.md") is False


def t_scope_outside_declared_subdir_is_rejected():
    """محدودهٔ اعلام‌شده `workspace` است — `reports` مجاز نیست حتی داخلِ sandbox."""
    assert _ok("reports/x.md", scope=("workspace",)) is False
    assert _ok("reports/x.md", scope=("workspace", "reports")) is True


def t_no_scope_declared_means_rejected_not_everything():
    """خالی بودنِ محدوده = «اعلام نشده» ⇒ رد. این تفاوتِ allowlist با denylist است."""
    for empty in (None, [], [""], ["   "]):
        r = scope_guard.check("workspace/x.md", sandbox_root=ROOT,
                              allowed_scope=empty)
        assert r["ok"] is False and r["reason"] == "no-scope-declared", (empty, r)


def t_a_malformed_scope_entry_does_not_open_the_door():
    for bad_scope in (["../"], ["/abs"], [".."], ["workspace/../.."]):
        assert _ok("workspace/x.md", scope=bad_scope) is False, bad_scope


# ── deny روی مسیرِ resolve‌شده، نه روی ورودیِ خام ────────────────────────────
def t_forbidden_marker_is_checked_after_resolution():
    (ROOT / "workspace" / "tests").mkdir(parents=True, exist_ok=True)
    r = scope_guard.check("workspace/sub/../tests/run_all.py",
                          sandbox_root=ROOT, allowed_scope=["workspace"])
    assert r["ok"] is False and r["reason"].startswith("forbidden:"), r
    assert r["rel"] == "workspace/tests/run_all.py", r   # قضاوت روی resolve‌شده


def t_hits_forbidden_covers_the_core_prohibitions():
    for t in ("PRE-0/governance.py", "_ops/tests/run_all.py",
              "state/fitness-latest.json", "_ops/telegram_center/power.py",
              ".git/config", "x/.env", "held_out_evaluator.py"):
        assert scope_guard.hits_forbidden(t), t
    for ok in ("workspace/report.md", "fixtures/leads.json", "reports/out.json"):
        assert scope_guard.hits_forbidden(ok) is None, ok


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = bridge_harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_scope_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    bridge_harness.teardown(ENV)
    sys.exit(1 if failed else 0)
