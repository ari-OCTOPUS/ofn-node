#!/usr/bin/env python3
"""scope_guard — «این مقصد داخلِ محدوده است؟» با resolve، نه با زیررشته.

این ماژول همان درسی را حمل می‌کند که ۲۰۲۶-۰۷-۳۰ روی `code_autonomy.allowed_target`
به‌صورت تجربی اثبات شد: گاردی که روی **رشتهٔ ورودی** قضاوت کند با یک `..` دور
می‌خورد. آن‌جا `_ops/cortex/../../PRE-0/governance.py` مجاز شمرده می‌شد و
صداکننده واقعاً به قانونِ اساسی resolve می‌کرد.

اینجا همان قاعده، ولی مستقل نوشته شده و **عمداً بدونِ import از `target_guard`**:
پلِ اقدام نباید به هیچ ماژولِ اجراییِ دیگری وابسته باشد (اصلِ «هیچ importِ
دوطرفه»). دو گارد باید بتوانند جدا از هم بمیرند.

سه لایه:
  ۱) resolve → containment (جزءبه‌جزء، نه startswith)
  ۲) deny روی مسیرِ **resolve‌شدهٔ** نسبت‌به‌ریشه
  ۳) ردِ صریحِ مطلق/درایو/UNC/NUL/خالی

$0 · stdlib · تابعِ خالص جز `resolve` · fail-closed در هر ابهام.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

# مسیرهایی که هیچ عملی — با هیچ کلاسی، در هیچ محدوده‌ای — نباید لمس کند.
# روی مسیرِ resolve‌شده سنجیده می‌شوند، نه روی ورودیِ خام.
FORBIDDEN_MARKERS = (
    # قانونِ اساسی و حاکمیت
    "pre-0/", "constitution", "governance", "risk-ladder",
    # verifier و شاهد — تغییرشان یعنی جابه‌جاییِ معیارِ پذیرش
    "tests/", "run_all", "held_out_evaluator", "cycle_evaluator", "prereg",
    "conftest", "_baselines",
    # کلیدهای توقف و ترمزها
    "kill", "power.py", "tg_api", "stop-", "halt", "panic",
    "code_autonomy", "code_brain", "capability_gate", "auto_approve",
    "human_append_guard", "arm_gate", "decision_gate", "autonomy_grant",
    # راز و هویت
    ".env", "secret", "credential", "token", "wallet", "seed",
    # ژنوم و دفترهای تخطی‌ناپذیر
    ".git", "genome", "ledger", "germline",
    # پول و شاهدِ پول — جعلشان همان چیزی است که کلِ آزمون علیه آن است
    "fitness-latest", "attribution", "revenue", "money", "budget/",
    "paid-calls", "outcomes.jsonl",
    # خودِ پل
    "action_bridge/classifier", "action_bridge/scope_guard",
    "action_bridge/owner_gate", "action_bridge/contracts",
)


class Reject(str):
    """علتِ ماشین‌خوانِ رد — تا کارتِ رأی بتواند بگوید *چرا*، نه فقط «نه»."""


def _norm(p) -> str:
    return os.path.normcase(str(p))


def contained(child: Path, parent: Path) -> bool:
    """`child` واقعاً داخلِ `parent`؟ مقایسهٔ جزءبه‌جزء.

    `startswith` روی رشته `sandbox-evil` را داخلِ `sandbox` می‌بیند — همان
    اشتباهی که یک بار روی `_ops/cortex-evil` سنجیده و بسته شد."""
    try:
        cp = Path(_norm(child)).parts
        pp = Path(_norm(parent)).parts
    except (OSError, ValueError):
        return False
    return len(cp) > len(pp) and cp[:len(pp)] == pp


def resolve_within(rel: str, root) -> "Path | Reject":
    """مسیرِ نسبی → مطلقِ resolve‌شده، یا علتِ رد.

    `strict=False` عمدی است: مقصدِ نوساخته هنوز روی دیسک نیست، ولی `..`،
    junction و symlink همچنان resolve می‌شوند — پس فرار دیده می‌شود."""
    s = str(rel or "").strip()
    if not s:
        return Reject("empty")
    if "\x00" in s:
        return Reject("nul-byte")
    s = s.replace("\\", "/")
    if s.startswith("/"):
        return Reject("absolute-or-unc")
    if len(s) >= 2 and s[1] == ":":
        return Reject("drive-letter")
    try:
        root_r = Path(root).resolve()
        cand = (root_r / PurePosixPath(s)).resolve()
    except (OSError, ValueError, RuntimeError):
        return Reject("unresolvable")
    if not contained(cand, root_r):
        return Reject("escapes-root")
    return cand


def hits_forbidden(rel_or_abs: str, root=None) -> "str | None":
    """کدام markerِ ممنوع خورد؟ روی مسیرِ resolve‌شده اگر ریشه داده شود.

    بدونِ ریشه (حالتِ طبقه‌بندیِ خالص) روی رشتهٔ نرمال‌شده می‌سنجد — که برای
    **بالا بردنِ** کلاس کافی است. پایین آوردنِ کلاس از این مسیر ممکن نیست، پس
    ضعفِ رشته این‌جا فقط محافظه‌کارتر عمل می‌کند نه بازتر."""
    p = str(rel_or_abs or "").replace("\\", "/").lower()
    if root is not None:
        r = resolve_within(rel_or_abs, root)
        if isinstance(r, Reject):
            return f"unresolvable:{r}"
        try:
            p = r.relative_to(Path(root).resolve()).as_posix().lower()
        except ValueError:
            return "outside-root"
    return next((m for m in FORBIDDEN_MARKERS if m in p), None)


def check(rel: str, *, sandbox_root, allowed_scope=None) -> dict:
    """حکمِ کاملِ محدوده: {ok, reason, resolved, rel, scope}.

    `allowed_scope` فهرستِ زیرمسیرهای مجاز **داخلِ** sandbox است. خالی بودنش
    یعنی «هیچ محدوده‌ای اعلام نشده» ⇒ رد؛ نه «همه‌جا مجاز». این تفاوت همان
    چیزی است که allowlist را از denylist جدا می‌کند."""
    scopes = [s for s in (allowed_scope or []) if str(s).strip()]
    if not scopes:
        return {"ok": False, "reason": "no-scope-declared",
                "resolved": None, "rel": None}
    cand = resolve_within(rel, sandbox_root)
    if isinstance(cand, Reject):
        return {"ok": False, "reason": str(cand), "resolved": None, "rel": None}
    root_r = Path(sandbox_root).resolve()
    inside = None
    for s in scopes:
        s_clean = str(s).replace("\\", "/").rstrip("/*")
        if not s_clean or s_clean.startswith("/") or ".." in s_clean.split("/"):
            continue                       # محدودهٔ بدشکل = محدودهٔ نامعتبر
        try:
            sp = (root_r / PurePosixPath(s_clean)).resolve()
        except (OSError, ValueError, RuntimeError):
            continue
        if contained(cand, sp):
            inside = s
            break
    if inside is None:
        return {"ok": False, "reason": "outside-allowed-scope",
                "resolved": str(cand), "rel": None}
    rel_posix = cand.relative_to(root_r).as_posix().lower()
    hit = next((m for m in FORBIDDEN_MARKERS if m in rel_posix), None)
    if hit:
        return {"ok": False, "reason": f"forbidden:{hit}",
                "resolved": str(cand), "rel": rel_posix}
    return {"ok": True, "reason": "in-scope", "resolved": str(cand),
            "rel": rel_posix, "scope": inside}


def is_allowed(rel: str, *, sandbox_root, allowed_scope=None) -> bool:
    return bool(check(rel, sandbox_root=sandbox_root,
                      allowed_scope=allowed_scope)["ok"])
