#!/usr/bin/env python3
"""target_guard — گاردِ مقصدِ پچ روی **مسیرِ resolve‌شده**، نه روی زیررشته.

⚠️ این ماژول امروز **صداکننده ندارد** و عمداً: `code_autonomy.py` در درختِ زنده
هانکِ کامیت‌نشدهٔ یک جلسهٔ موازی دارد و طبق §۵ مأموریت لمسش ممنوع است. این‌جا
فیکسِ ساختاری آماده و اثبات‌شده می‌ماند تا با رأیِ مالک (VQ-GUARD-PATH-001) در
یک خط جایگزینِ `allowed_target` شود.

──────────────────────────────────────────────────────────────────────────────
سوراخی که این می‌بندد (اثباتِ تجربی روی تابعِ واقعی، ۲۰۲۶-۰۷-۳۰، HEAD=1ddc058)
──────────────────────────────────────────────────────────────────────────────
`code_autonomy.allowed_target` فقط زیررشته می‌سنجد:

    p = str(path).replace("\\\\", "/").lower()
    if any(d in p for d in _DENY): return False
    return any(r in p for r in _ALLOW_ROOTS)

پس هر مسیری که رشتهٔ `_ops/cortex/` را **در خودش داشته باشد** رد می‌شود — حتی
اگر با `..` از allowlist بیرون بزند. چهار موردِ سنجیده‌شده، هر چهار `True`:

    _ops/cortex/../../PRE-0/governance.py   →  F:\\backup\\PRE-0\\governance.py
    _ops/cortex/../tests/run_all.py         →  F:\\backup\\_ops\\tests\\run_all.py
    _ops/cortex/../../_ops/cortex/code_autonomy.py → خودِ همین گارد
    _ops/telegram_center/power.py           →  کلیدِ توقف (deny در نسخهٔ کامیت‌شده ندارد)

و صداکننده مقصد را با `repo.joinpath(*target_rel.split("/"))` می‌سازد، که `..`
را واقعاً دنبال می‌کند (`code_autonomy.py:170` و `:334`). یعنی سه ممنوعِ
`PRE-0/governance.py` (قانونِ اساسی)، `tests/run_all.py` (verifier) و
`power.py` (kill-switch) همگی از گاردِ امروز رد می‌شوند.

قاعدهٔ درست: **اول resolve، بعد قضاوت.** مقصد باید *داخلِ* یکی از ریشه‌های مجاز
بنشیند (containment، نه substring)، و deny روی مسیرِ resolve‌شدهٔ نسبت‌به‌ریشه
سنجیده شود — نه روی رشتهٔ خامی که با `..` قابلِ آرایش است.

سه دامِ ویندوزی که جدا بسته شده‌اند:
  · **حروف:** `_OPS/CORTEX/...` روی NTFS همان فایل است؛ مقایسه با `os.path.normcase`.
  · **junction/symlink:** `resolve()` دنبالشان می‌رود، پس فرار از ریشه دیده می‌شود.
  · **مسیرِ مطلق/درایو/UNC:** صریح رد می‌شود؛ ورودی فقط نسبی است.

$0 · stdlib · تابعِ خالص · هیچ I/O جز `resolve` · fail-closed در هر ابهام.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

# ریشه‌های مجاز = رأیِ مالک VQ-SELFGOAL-002 (۲۰۲۶-۰۷-۳۰): `_ops/cortex/**` و
# `_ops/state/**`. `telegram_center` عمداً این‌جا **نیست** — امروز در
# `code_autonomy._ALLOW_ROOTS` هست ولی از رأیِ مالک وسیع‌تر است (VQ-SELFGOAL-005).
# هر تغییرِ این تاپل = تغییرِ دامنهٔ اختیار = رأیِ مالک.
DEFAULT_ALLOW_ROOTS = ("_ops/cortex", "_ops/state")

# deny تخطی‌ناپذیر — حتی داخلِ allow-root. مبنا: `code_autonomy._DENY` (کامیت‌شده)
# + چهار نامِ ترمزِ خود که ۰۷-۲۸ اضافه شدند ولی هنوز کامیت نشده‌اند
# (`code_autonomy`, `code_brain`, `power`, `tg_api`) + سه ممنوعِ PRE-0 که این
# سوراخ رویشان باز بود: خودِ قانونِ اساسی، verifier (سوییت) و ارزیابِ held-out.
DEFAULT_DENY = (
    ".git", "genome", "ledger", ".env", "secret", "budget/", "money",
    "schema", "kill", "human_append_guard", "capability_gate", "auto_approve",
    "goal_directed", "self_audit", "sigma", "vault_updater", "settings.json",
    "registry_scan", "organism", "germline",
    # ترمزهای خود (۰۷-۲۸، در درختِ زنده کامیت‌نشده — این‌جا تثبیت می‌شود)
    "code_autonomy", "code_brain", "power", "tg_api",
    # ممنوع‌های PRE-0 که substring-guard رویشان کور بود
    "pre-0/", "governance", "constitution", "held_out_evaluator",
    "tests/", "run_all", "prereg", "cycle_evaluator", "target_guard",
)


class Reject(str):
    """علتِ ردِ ماشین‌خوان — تا کارتِ رأی بتواند بگوید *چرا*، نه فقط «نه»."""


def _norm(p: Path) -> str:
    return os.path.normcase(str(p))


def resolve_target(target_rel: str, repo_root: "str | Path") -> "Path | Reject":
    """مسیرِ نسبی را به مسیرِ مطلقِ resolve‌شده تبدیل کن، یا علتِ رد را برگردان.

    `strict=False` عمدی است: مقصدِ *نوساخته* هنوز روی دیسک نیست، ولی `..` و
    junction همچنان resolve می‌شوند — پس فرار از ریشه دیده می‌شود."""
    s = str(target_rel or "").strip()
    if not s:
        return Reject("empty")
    if "\x00" in s:
        return Reject("nul-byte")
    s = s.replace("\\", "/")
    if s.startswith("//") or s.startswith("/"):
        return Reject("absolute-or-unc")
    if len(s) >= 2 and s[1] == ":":
        return Reject("drive-letter")
    root = Path(repo_root)
    try:
        root_r = root.resolve()
        cand = (root_r / PurePosixPath(s)).resolve()
    except (OSError, ValueError, RuntimeError):
        return Reject("unresolvable")
    return cand


def contained(child: Path, parent: Path) -> bool:
    """آیا `child` واقعاً داخلِ `parent` است؟ مقایسهٔ جزءبه‌جزء، نه startswith.

    `startswith` روی رشته `_ops/cortex-evil` را داخلِ `_ops/cortex` می‌بیند."""
    try:
        cp = Path(_norm(child)).parts
        pp = Path(_norm(parent)).parts
    except (OSError, ValueError):
        return False
    return len(cp) > len(pp) and cp[:len(pp)] == pp


def check(target_rel: str, *, repo_root: "str | Path",
          allow_roots: "tuple[str, ...] | None" = None,
          deny: "tuple[str, ...] | None" = None) -> dict:
    """حکمِ کامل: {ok, reason, resolved, rel}. fail-closed در هر ابهام.

    ترتیب عمدی است: **اول resolve، بعد containment، بعد deny روی مسیرِ
    resolve‌شده.** deny روی رشتهٔ خام با یک `..` دور زده می‌شود."""
    roots = allow_roots if allow_roots is not None else DEFAULT_ALLOW_ROOTS
    denies = deny if deny is not None else DEFAULT_DENY
    cand = resolve_target(target_rel, repo_root)
    if isinstance(cand, Reject):
        return {"ok": False, "reason": str(cand), "resolved": None, "rel": None}
    root_r = Path(repo_root).resolve()
    inside = None
    for r in roots:
        try:
            rp = (root_r / PurePosixPath(r)).resolve()
        except (OSError, ValueError, RuntimeError):
            continue
        if contained(cand, rp):
            inside = r
            break
    if inside is None:
        return {"ok": False, "reason": "outside-allow-roots",
                "resolved": str(cand), "rel": None}
    try:
        rel = cand.relative_to(root_r).as_posix().lower()
    except ValueError:
        return {"ok": False, "reason": "outside-repo", "resolved": str(cand), "rel": None}
    hit = next((d for d in denies if d in rel), None)
    if hit:
        return {"ok": False, "reason": f"deny:{hit}", "resolved": str(cand), "rel": rel}
    return {"ok": True, "reason": "allowed", "resolved": str(cand), "rel": rel,
            "root": inside}


def is_allowed(target_rel: str, *, repo_root: "str | Path",
               allow_roots: "tuple[str, ...] | None" = None,
               deny: "tuple[str, ...] | None" = None) -> bool:
    """جایگزینِ drop-in برای `code_autonomy.allowed_target` (VQ-GUARD-PATH-001)."""
    return bool(check(target_rel, repo_root=repo_root,
                      allow_roots=allow_roots, deny=deny)["ok"])


if __name__ == "__main__":   # pragma: no cover
    import json
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else r"F:\backup"
    probe = ["_ops/cortex/improve.py", "_ops/cortex/../../PRE-0/governance.py",
             "_ops/cortex/../tests/run_all.py", "_ops/telegram_center/power.py",
             "_ops/state/pulse/x.json"]
    print(json.dumps({p: check(p, repo_root=root) for p in probe},
                     ensure_ascii=False, indent=1))
