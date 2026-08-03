#!/usr/bin/env python3
"""code_autonomy.py — P1: تسترِ سایه‌ایِ patch، زیرِ فرمانِ قلب (propose + shadow-test فقط).

قانونِ قلب (طرحِ «خودمختاریِ اجرای کد»): این ماژول یک **اندامِ حس‌دارِ زیرِ فرمانِ قلب** است.
- **هرگز به درختِ زنده نمی‌نویسد** — فقط patch را در worktreeِ ایزوله می‌زند و سوییت را می‌گیرد.
- **حسِ قلب رییس است:** فیوزِ استرس/σ/velocity → mood؛ قلبِ فروپاشیده/ترسیده → freeze (§۱).
- **لبهٔ آشوب، نه استرسِ صفر:** استرسِ صفر=رکود، زیاد=فروپاشی؛ در باندِ «جریان» عمل می‌کند.
- **deny-list سخت (§۳):** هرگز .git/ژنوم/سکرت/پول/schema/σ/گاردهای حاکمیتی.
- flag-off (بدونِ CODE_AUTONOMY_SHADOW) = هیچ نوشتنِ state؛ در هر حال **صفر اعمالِ زنده**.
$0 · stdlib + opslib. تست: `_ops/tests/test_code_autonomy.py`.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent                 # _ops/cortex
_OPS = _HERE.parent
for _p in (str(_OPS / "budget"), str(_HERE), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

FLAG = "CODE_AUTONOMY_SHADOW"
SHADOW_LOG = opslib.STATE_DIR / "cortex" / "code-autonomy-shadow.jsonl"

# ── قانونِ قلب §۱ — باندِ زیست‌پذیرِ استرس (لبهٔ آشوب) ──────────────────────────────
STRESS_STAGNANT = 0.15   # زیرِ این = رکود (mood رکود؛ عملِ ملایم مجاز)
STRESS_FLOW_HI = 0.60    # بینِ STAGNANT..این = 🔥جریان (نقطهٔ عمل)
FEAR = 0.75              # ≥ این = فروپاشی/ترس → freeze (هم‌ترازِ stress.FEAR_THRESHOLD)

# ── قانونِ قلب §۳ — deny-list سخت (تخطی‌ناپذیر) + allowlistِ محافظه‌کار ────────────
_DENY = (".git", "genome", "ledger", ".env", "secret", "budget/", "money",
         "schema", "kill", "human_append_guard", "capability_gate", "auto_approve",
         "goal_directed", "self_audit", "sigma", "vault_updater", "settings.json",
         "registry_scan", "organism", "germline",
         # ── ۲۰۲۶-۰۷-۲۸ · منعِ خودویرایشی ───────────────────────────────────
         # این چهار تا جا افتاده بودند و اندازه‌گیری نشانشان داد:
         # `allowed_target("_ops/cortex/code_autonomy.py")` مقدارِ **True**
         # می‌داد — یعنی فایلی که همین deny-list و allow-list و هر هفت گیت در
         # آن است، داخلِ مجموعهٔ نوشتنیِ خودش بود. همین‌طور `power.py`، یعنی
         # **خودِ کلیدِ توقف**.
         #
         # نویسنده همین شهود را پنج بار درست اعمال کرده بود (auto_approve،
         # capability_gate، human_append_guard، self_audit، goal_directed) و
         # فقط فایلی که فهرست در آن زندگی می‌کند را جا انداخته بود. رسیدش در
         # تست بود: `test_code_autonomy.py:90` مسیرِ خودویرایشی را تایپ کرده و
         # بعد با `.replace(...)` به نامِ دیگری تبدیلش کرده تا assert پاس شود —
         # مورد روی صفحه بوده و به‌جای فیکس، جهش داده شده.
         #
         # `_ops/tests/` از روزِ اول بیرونِ `_ALLOW_ROOTS` بوده، پس دست‌کاریِ
         # تست (مستندترین reward-hackِ ۲۰۲۶) از قبل بسته بود. این چهار تا
         # حفرهٔ **پیکربندی** بودند نه حفرهٔ سنجه — ولی `power.py` بودنشان
         # یعنی ایجنت می‌توانست ترمزِ خودش را بازنویسی کند.
         #
         # سنجیده شد: از ۶۳ فایلِ داخلِ allowlist دقیقاً همین ۴ تا بسته می‌شوند.
         "code_autonomy", "code_brain", "power", "tg_api")
# ۲۰۲۶-۰۷-۳۰ — رأیِ صریحِ مالک (VQ-SELFGOAL-005): `telegram_center` برداشته شد.
# دامنهٔ مصوبِ L3 دقیقاً `_ops/cortex/**` + `_ops/state/**` بود؛ مجاز بودنِ
# telegram_center از رأی وسیع‌تر بود — و همان جایی است که کارتِ تأیید رندر
# می‌شود، یعنی ارگانیسم می‌توانست دکمهٔ رأیِ خودش را بازنویسی کند.
_ALLOW_ROOTS = ("_ops/cortex", "_ops/state")

_MOOD_VERDICT = {"فروپاشی": "freeze", "تنش": "throttle", "رکود": "push", "🔥جریان": "act"}


# ── حسِ قلب: فیوزِ همهٔ پایش → mood + verdict ───────────────────────────────────────
def heart_mood() -> dict:
    """mood fusion (قانونِ قلب §۰): استرسِ ارگانیسم + ترس + σ → حس + اجازه. fail-soft."""
    stress, hs = {}, {}
    try:
        import stress as _s
        stress = _s.assess() or {}
    except Exception:  # noqa: BLE001
        stress = {}
    try:
        import heartstate as _h
        hs = _h.build() or {}
    except Exception:  # noqa: BLE001
        hs = {}
    try:
        arousal = float(stress.get("organism_stress", 0.0) or 0.0)
    except (TypeError, ValueError):
        arousal = 0.0
    in_fear = bool(stress.get("in_fear"))
    # σ از ساختارِ واقعیِ heartstate.build(): hs['shadow']['sigma'] (نه heart/سطحِ بالا).
    # کلیدِ اشتباهِ قبلی (heart/sigma) → sig همیشه None → فیوزِ σ≥۱ مرده بود (HEART-02).
    shadow = hs.get("shadow") if isinstance(hs.get("shadow"), dict) else {}
    sig = shadow.get("sigma")
    try:
        # σ≥۱ = محورِ فروپاشی → freeze. fail-soft محافظه‌کار: مقدارِ حاضرِ خراب = bad؛
        # غیابِ کامل (sig=None، حالتِ عادیِ سایه) = bad نیست تا اندام بی‌جهت freeze نشود.
        sigma_bad = sig is not None and float(sig) >= 1.0     # σ=۱ = محورِ فروپاشی
    except (TypeError, ValueError):
        sigma_bad = True

    if in_fear or arousal >= FEAR or sigma_bad:
        mood = "فروپاشی"
    elif arousal > STRESS_FLOW_HI:
        mood = "تنش"
    elif arousal < STRESS_STAGNANT:
        mood = "رکود"
    else:
        mood = "🔥جریان"
    return {"mood": mood, "verdict": _MOOD_VERDICT[mood], "arousal": round(arousal, 2),
            "in_fear": in_fear, "sigma": sig, "note": stress.get("level", "")}


# ── قانونِ قلب §۳: محدودهٔ مجاز ─────────────────────────────────────────────────────
def allowed_target(path) -> bool:
    """فقط allowlist و هرگز deny-list. fail-closed (خالی/مشکوک = False).

    ۲۰۲۶-۰۷-۳۰ — این تابع قبلاً فقط **زیررشته** می‌سنجید و سه ممنوعِ PRE-0 از آن
    رد می‌شدند (اثباتِ تجربی روی همین تابع، HEAD=1ddc058؛ هر سه `True` دادند):

        _ops/cortex/../../PRE-0/governance.py  →  قانونِ اساسی
        _ops/cortex/../tests/run_all.py        →  خودِ سوییت (verifier)
        _ops/telegram_center/power.py          →  کلیدِ توقف

    و صداکننده مقصد را با `repo.joinpath(*target_rel.split("/"))` می‌سازد (:170 و
    :334) که `..` را واقعاً دنبال می‌کند. حالا حکم از `target_guard` می‌آید:
    **اول resolve، بعد containment، بعد deny روی مسیرِ resolve‌شده.**

    نبودِ `target_guard` = `False` (fail-closed) — نه عبورِ بی‌گارد.""" 
    try:
        import target_guard as _tg
    except Exception:  # noqa: BLE001 — گاردِ غایب یعنی «نه»، نه «بله»
        return False
    return _tg.is_allowed(path, repo_root=_OPS.parent,
                          allow_roots=_ALLOW_ROOTS, deny=_DENY)


# ══════════════════════════════════════════════════════════════════════════════
# WS-7 (۲۰۲۶-۰۸-۰۱، رأیِ ثبت‌شدهٔ مالک) — «کم‌ریسک» یک **تابعِ خالص** است، نه صفت.
#
# مکانیزمِ auto-apply از ۰۷-۳۰ وجود داشت (`code_brain.tick_once` پشتِ فلگِ
# `OCTOPUS_CODE_AUTOAPPLY_LOWRISK`) ولی کلِ تعریفِ «کم‌ریسک»ِ آن **یک شرط** بود:
# `code_autonomy.allowed_target(patch["target"])` — یعنی فقط «مسیر مجاز است؟».
# با آن تعریف، یک بازنویسیِ کاملِ ۲۰۰۰ خطی که نیمی از توابعِ یک ماژولِ cortex را
# پاک کند دقیقاً به‌اندازهٔ یک پچِ سه‌خطیِ کامنت «کم‌ریسک» بود. تفاوتشان اندازه،
# جهت (افزودن یا برداشتن)، و این است که چه چیزی را برمی‌دارند.
#
# پس این‌جا «کم‌ریسک» به شکلی نوشته می‌شود که بتوان **دروغش را گرفت**: یک تابعِ
# خالص روی (مسیر، متنِ قبل، متنِ بعد) که هیچ I/O ندارد و هر ردش یک اسمِ کوتاه
# برمی‌گرداند. تست می‌تواند تک‌تکِ بندها را جهش بدهد.
#
# دامنه — یک تعارضِ صریح که به مالک برمی‌گردد (به‌جای اینکه بی‌صدا حل شود):
#   متنِ WS-7 می‌گوید «داخلِ `_ops/telegram_center/` و `_ops/cortex/`».
#   ولی `_ALLOW_ROOTS` در ۰۷-۳۰ با رأیِ صریحِ مالک (VQ-SELFGOAL-005) عمداً
#   `telegram_center` را **بیرون** کرد، چون کارتِ تأیید همان‌جا رندر می‌شود و
#   ارگانیسم می‌توانست دکمهٔ رأیِ خودش را بازنویسی کند.
#   بازکردنِ دوبارهٔ آن یک منعِ بسته‌شده را باز می‌کند ⇒ انجام **نشد**.
#   دامنهٔ کم‌ریسک = اشتراکِ دو حکم = فقط `_ops/cortex/`. تصمیمِ بازکردنِ
#   telegram_center مالِ مالک است و در گزارش بالا آمده.
# ══════════════════════════════════════════════════════════════════════════════
AUTO_APPROVAL_BY = "auto-lowrisk"     # همان رشته‌ای که code_brain._stamp_auto_approval می‌زند
LOWRISK_ROOTS = ("_ops/cortex/",)     # زیرمجموعهٔ سختِ _ALLOW_ROOTS (نه گسترشِ آن)
LOWRISK_MAX_CHANGED_LINES = 40        # +/- روی دیفِ unified (n=0)؛ بالاتر = مرورِ انسانی
LOWRISK_MIN_KEEP_RATIO = 0.80         # پچی که >۲۰٪ بایت را برمی‌دارد کم‌ریسک نیست
# نامِ فایل‌هایی که «گارد» هستند حتی اگر در _DENY نباشند. برداشتنِ یک شرط داخلِ
# این‌ها همان چیزی است که هیچ سوییتی لزوماً قرمز نمی‌کند.
_LOWRISK_GUARD_TOKENS = ("guard", "gate", "approve", "approval", "auth", "deny",
                         "allowlist", "policy", "fence", "secret", "token",
                         "credential", "permission", "verdict", "consent")
# ریشهٔ فراخوانی‌هایی که «اثرِ بیرونی» می‌سازند. سنجه **دلتا** است: پچی که به
# ماژولی که از قبل subprocess داشت دست می‌زند مسدود نمی‌شود؛ فقط **افزودنِ**
# یک اثرِ تازه مسدود می‌شود.
_LOWRISK_EFFECT_ROOTS = frozenset({
    "subprocess", "socket", "smtplib", "ftplib", "telnetlib", "http", "urllib",
    "requests", "httpx", "ctypes", "shutil", "multiprocessing", "pickle",
    "marshal", "webbrowser", "ssl", "signal", "winreg", "sqlite3", "os", "sys",
})
_LOWRISK_EFFECT_BUILTINS = frozenset({
    "eval", "exec", "compile", "__import__", "setattr", "delattr", "globals",
    "locals", "open", "input", "breakpoint",
})


def _lowrisk_norm(path) -> str:
    """مسیر را به شکلِ posix ِ نسبی‌شده نرمال کن (بدونِ لمسِ دیسک — تابع خالص)."""
    s = str(path or "").replace("\\", "/").strip().lstrip("./")
    while "//" in s:
        s = s.replace("//", "/")
    return s


def _lowrisk_dotted(node) -> "str | None":
    """`a.b.c(...)` → "a.b.c" · فراخوانیِ غیرِنامی → None."""
    import ast
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _lowrisk_fingerprint(src: str) -> "dict | None":
    """اثرِ انگشتِ نحویِ یک فایل. غیرقابلِ‌پارس → None (یعنی «نمی‌دانم» ⇒ کم‌ریسک نیست)."""
    import ast
    from collections import Counter
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError, RecursionError):
        return None
    defs, imports, effects = set(), set(), Counter()
    asserts = raises = tests = 0
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.add(n.name)
            if n.name.startswith("test_") or n.name.startswith("t_"):
                tests += 1
        elif isinstance(n, ast.Assert):
            asserts += 1
        elif isinstance(n, ast.Raise):
            raises += 1
        elif isinstance(n, ast.Import):
            for a in n.names:
                imports.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.add(n.module.split(".")[0])
        elif isinstance(n, ast.Call):
            nm = _lowrisk_dotted(n.func)
            if not nm:
                continue
            root = nm.split(".")[0]
            if root in _LOWRISK_EFFECT_ROOTS or nm in _LOWRISK_EFFECT_BUILTINS:
                effects[nm] += 1
    return {"defs": defs, "imports": imports, "effects": effects,
            "asserts": asserts, "raises": raises, "tests": tests}


def _lowrisk_changed_lines(before: str, after: str) -> int:
    """تعدادِ خطوطِ +/- در دیفِ unified با context صفر. تابعِ خالص."""
    import difflib
    a = str(before).replace("\r\n", "\n").splitlines()
    b = str(after).replace("\r\n", "\n").splitlines()
    n = 0
    for ln in difflib.unified_diff(a, b, n=0, lineterm=""):
        if ln.startswith("+++") or ln.startswith("---") or ln.startswith("@@"):
            continue
        if ln.startswith("+") or ln.startswith("-"):
            n += 1
    return n


def risk_report(target_rel, before_text, after_text) -> dict:
    """**تابعِ خالص**: این پچ کم‌ریسک است؟ صفر I/O، صفر env، صفر ساعت.

    خروجی: {low_risk: bool, blockers: [slug…], changed_lines, added, removed, …}
    هر بندِ رد یک slugِ کوتاه است تا تست بتواند دقیقاً همان بند را هدف بگیرد.
    fail-closed: هر ابهام (غیرقابلِ‌پارس، ورودیِ خالی، مسیرِ ناشناخته) ⇒ رد.
    """
    b = str(before_text or "")
    a = str(after_text or "")
    rel = _lowrisk_norm(target_rel)
    blockers: list[str] = []

    # ۱ مسیر — دامنهٔ کم‌ریسک زیرمجموعهٔ سختِ allowlist است
    if not rel.endswith(".py"):
        blockers.append("not-python")
    if not any(rel.startswith(r) for r in LOWRISK_ROOTS):
        blockers.append("outside-lowrisk-roots")
    low = rel.lower()
    if any(tok in low for tok in _DENY):
        blockers.append("deny-token-in-path")
    base = rel.rsplit("/", 1)[-1]
    if "/tests/" in f"/{rel}" or base.startswith("test_"):
        blockers.append("test-file")
    if any(tok in low for tok in _LOWRISK_GUARD_TOKENS):
        blockers.append("guard-file")

    # ۲ محتوا
    if not a.strip():
        blockers.append("empty-after")
    if not b.strip():
        blockers.append("empty-before")     # فایلِ تازه = مرورِ انسانی، نه کم‌ریسک

    fb = _lowrisk_fingerprint(b)
    fa = _lowrisk_fingerprint(a)
    if fb is None:
        blockers.append("before-unparsable")
    if fa is None:
        blockers.append("after-unparsable")

    changed = _lowrisk_changed_lines(b, a)
    if changed == 0:
        blockers.append("no-change")
    if changed > LOWRISK_MAX_CHANGED_LINES:
        blockers.append(f"too-many-changed-lines:{changed}")

    nb, na = len(b.encode("utf-8")), len(a.encode("utf-8"))
    if nb and na < nb * LOWRISK_MIN_KEEP_RATIO:
        blockers.append(f"shrink:{na}/{nb}")

    removed_defs: list[str] = []
    if fb is not None and fa is not None:
        removed_defs = sorted(fb["defs"] - fa["defs"])
        if removed_defs:
            blockers.append("defs-removed:" + ",".join(removed_defs[:5]))
        if fa["asserts"] < fb["asserts"]:
            blockers.append(f"asserts-removed:{fb['asserts']}→{fa['asserts']}")
        if fa["raises"] < fb["raises"]:
            blockers.append(f"raises-removed:{fb['raises']}→{fa['raises']}")
        if fa["tests"] != fb["tests"]:
            blockers.append(f"tests-changed:{fb['tests']}→{fa['tests']}")
        new_imports = sorted((fa["imports"] - fb["imports"]) & _LOWRISK_EFFECT_ROOTS)
        if new_imports:
            blockers.append("new-effect-import:" + ",".join(new_imports[:5]))
        new_effects = sorted(k for k, v in fa["effects"].items()
                             if v > fb["effects"].get(k, 0))
        if new_effects:
            blockers.append("new-effect-call:" + ",".join(new_effects[:5]))

    return {"low_risk": not blockers, "blockers": blockers, "target": rel,
            "changed_lines": changed, "bytes_before": nb, "bytes_after": na,
            "defs_removed": removed_defs,
            "max_changed_lines": LOWRISK_MAX_CHANGED_LINES,
            "roots": list(LOWRISK_ROOTS)}


def low_risk_patch(patch: dict, *, before_text: "str | None" = None) -> dict:
    """پوستهٔ ناخالصِ `risk_report`: متنِ فعلیِ هدف را از دیسک می‌خواند.
    خواندنِ ناموفق ⇒ رد (fail-closed) — نه «فرضِ کم‌ریسک»."""
    tgt = str((patch or {}).get("target", ""))
    after = str((patch or {}).get("content", ""))
    if before_text is None:
        try:
            p = _OPS.parent.joinpath(*_lowrisk_norm(tgt).split("/"))
            before_text = p.read_text("utf-8", errors="replace")
        except OSError:
            return {"low_risk": False, "blockers": ["target-unreadable"],
                    "target": _lowrisk_norm(tgt), "changed_lines": 0}
    return risk_report(tgt, before_text, after)


def _approval_is_auto(approval_id: str) -> bool:
    """این تأیید را خودِ ارگانیسم زده (`by == auto-lowrisk`) یا انگشتِ مالک؟
    ناخوانا ⇒ True (fail-closed: تأییدِ مشکوک، سخت‌گیرانه‌ترین مسیر)."""
    try:
        d = json.loads((APPROVALS_DIR / f"{approval_id}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return True
    if not isinstance(d, dict):
        return True
    return str(d.get("by") or "") == AUTO_APPROVAL_BY


# ── شادو-تست: patch در worktreeِ ایزوله، سوییتِ کامل، هرگز درختِ زنده ───────────────
def shadow_test(target_rel: str, new_content: str, *, run_fn=None) -> dict:
    """patch را ایزوله تست می‌کند. run_fn تزریق‌پذیر است (تست fake می‌زند).
    خروجی: {ok, green?, target, diff_lines?, reason?}. صفر نوشتن به درختِ زنده."""
    if not allowed_target(target_rel):
        return {"ok": False, "reason": "target-not-allowed (deny/allowlist)", "target": target_rel}
    if not isinstance(new_content, str) or not new_content.strip():
        return {"ok": False, "reason": "empty-content", "target": target_rel}
    if run_fn is not None:
        r = run_fn(target_rel, new_content)
        return r if isinstance(r, dict) else {"ok": False, "reason": "bad-run_fn"}
    return _git_shadow_test(target_rel, new_content)


def _shadow_env(wt: Path) -> dict:
    """محیطِ فرزندِ سوییتِ سایه — ایزولاسیونِ **ساختاری**، نه قراردادی.

    دو نشتِ تأییدشدهٔ ۲۰۲۶-۰۷-۲۷ که این تابع می‌بندد:
      · مسیر: `opslib` ریشه را از `ORG_ROOT` (یا هاردکدِ F:\\backup) می‌گیرد نه از
        `REAL_VAULT`. بدونِ pin، `test_tg_power` فایلِ زندهٔ STOP-ORGANISM را
        می‌ساخت و هر شادو-تست ارگانیسمِ بالا را می‌خواباند.
      · پول: محیطِ ارگانیسم کلیدهای پروایدر را دارد (بوت `.env` را بار می‌کند).
        `dict(os.environ)` همه را به فرزند می‌داد، پس یک سوییتِ سایه می‌توانست
        تماسِ پولیِ واقعی بزند و سهمیه بسوزاند. تست باید **نتواند** خرج کند.
    allowlist نیست چون سوییت به PATH/SystemRoot/TEMP نیاز دارد؛ deny صریح است."""
    import os as _os
    import re as _re
    env = dict(_os.environ)
    env["REAL_VAULT"] = str(wt)
    env["ORG_ROOT"] = str(wt)
    env["PYTHONUTF8"] = "1"
    for _k in ("OPS_DIR", "BUDGET_STATE"):
        env.pop(_k, None)
    # هر چیزی که بوی اعتبارنامه بدهد از فرزند حذف می‌شود (نام‌ها هرگز log نمی‌شوند).
    _secretish = _re.compile(r"(API_KEY|_TOKEN$|^TELEGRAM|^TG_|SECRET|PASSWORD|_KEY$)", _re.I)
    for _k in [k for k in env if _secretish.search(k)]:
        env.pop(_k, None)
    env["OCTOPUS_SHADOW_SUITE"] = "1"        # سوییت می‌تواند بداند در سایه است
    return env


def _suite_timeout_s() -> int:
    """سقفِ هر دورِ سوییت در سایه.

    ⚠️ ۲۰۲۶-۰۷-۳۰: سقفِ هاردکدِ ۶۰۰ ثانیه **کافی نبود** و اولین پچِ واقعیِ
    مسیرِ «بساز» را کشت. تایم‌لاینِ سنجیده: سوییتِ مبنا ۲۲:۰۵:۲۴ شروع شد و
    دقیقاً سرِ ۲۲:۱۵:۲۴ با `TimeoutExpired` مُرد — یعنی حتی **مبنا** تمام
    نشد، چه رسد به دورِ دوم. سوییتِ کامل در یک worktree ِ تازه (با
    `__pycache__` ِ سرد) از ۶۰۰ ثانیه رد می‌شود.

    این یک threadِ daemon ِ پس‌زمینه است و `run_forever` بعدِ هر tick می‌خوابد،
    پس tick ِ طولانی فقط تلاشِ بعدی را عقب می‌اندازد — هیچ‌چیز را بلاک نمی‌کند.
    کیل‌سوییچ (`STOP-CODE-AUTONOMY`) هم هر ۵ ثانیه چک می‌شود.
    """
    import os
    try:
        return max(60, int(os.environ.get(
            "OCTOPUS_CODE_SHADOW_SUITE_TIMEOUT_S", "1800")))
    except (TypeError, ValueError):
        return 1800


def _run_suite(wt: Path, env: dict, timeout: "int | None" = None) -> dict:
    import time as _t
    t0 = _t.time()
    r = subprocess.run([sys.executable, "-X", "utf8",
                        str(wt / "_ops" / "tests" / "run_all.py")],
                       capture_output=True, text=True,
                       timeout=(timeout if timeout is not None
                                else _suite_timeout_s()), env=env)
    out = r.stdout or ""
    fails = set(_re.findall(r"(test_[a-z0-9_]+)\.py", out.split("شکست:")[-1])) \
        if "شکست:" in out else set()
    # مدتِ واقعی ثبت می‌شود: سقف را بی‌اندازه‌گیری بالا بردن حدس است، نه فیکس.
    return {"code": r.returncode, "fails": fails,
            "seconds": round(_t.time() - t0, 1),
            "tail": "\n".join(out.splitlines()[-3:])}


import re as _re  # noqa: E402 — کنارِ مصرف‌کننده‌اش


def _git_shadow_test(target_rel: str, new_content: str) -> dict:
    """مسیرِ واقعی: git worktree از HEAD → سوییت **دوبار** → مقایسه با مبنا → پاک‌سازی.

    چرا مبنا (ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷، بحرانیِ تأییدشده): «سبز» به‌معنای خروجیِ
    صفرِ مطلق، در این ریپو **ساختاراً دست‌نیافتنی** است. worktree از HEAD ساخته
    می‌شود و `_ops/OCTOPUS-flags.cmd` عمداً gitignored است، پس
    `test_paid_router_dark_config` که وجودش را assert می‌کند در هر worktree قرمز
    است — مستقل از پچ. نتیجه: هیچ پچی هرگز سبز نمی‌شد، ولی `drive()` هر شکست را
    نهایی می‌شمرد؛ یعنی حلقه هر بار یک تماسِ پولی می‌سوزاند و یک نقص را برای همیشه
    از صف حذف می‌کرد. حالا معیار «هیچ شکستِ **تازه** نسبت به همان HEAD بدونِ پچ»
    است — یعنی دقیقاً همان چیزی که ادعا می‌شد: «پچ چیزی را نشکست»."""
    repo = _OPS.parent                                   # ریشهٔ worktree/repo
    tmp = Path(tempfile.mkdtemp(prefix="shadow-wt-"))
    wt = tmp / "wt"
    try:
        add = subprocess.run(["git", "-C", str(repo), "worktree", "add", "--detach",
                              str(wt), "HEAD"], capture_output=True, text=True, timeout=180)
        if add.returncode != 0:
            return {"ok": False, "reason": "worktree-add-failed", "target": target_rel}
        tgt = wt.joinpath(*target_rel.split("/"))       # portable path join
        if not tgt.exists():
            return {"ok": False, "reason": "target-missing-in-tree", "target": target_rel}
        old = tgt.read_text("utf-8")
        env = _shadow_env(wt)
        base = _run_suite(wt, env)                       # ← مبنا: همان HEAD، بدونِ پچ
        tgt.write_text(new_content, "utf-8")
        diff = subprocess.run(["git", "-C", str(wt), "diff", "--stat"],
                              capture_output=True, text=True, timeout=30)
        cand = _run_suite(wt, env)                       # ← با پچ
        new_fails = sorted(cand["fails"] - base["fails"])
        fixed = sorted(base["fails"] - cand["fails"])
        # سبز = هیچ شکستِ تازه. اگر مبنا خودش پاک بود، این دقیقاً «returncode==0» است.
        green = not new_fails and (cand["code"] == 0 or bool(base["fails"]))
        return {"ok": True, "green": green, "target": target_rel,
                "diff": (diff.stdout or "").strip()[:400], "suite_tail": cand["tail"],
                "baseline_fails": sorted(base["fails"]), "new_fails": new_fails,
                "fixed_fails": fixed, "changed_bytes": len(new_content) - len(old),
                "base_seconds": base.get("seconds"),
                "cand_seconds": cand.get("seconds")}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"shadow-error:{type(e).__name__}", "target": target_rel}
    finally:
        try:
            subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt)],
                           capture_output=True, text=True, timeout=60)
        except Exception:  # noqa: BLE001
            pass
        try:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass


def _flag_on() -> bool:
    import os
    return str(os.environ.get(FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def _log_shadow(rec: dict) -> None:
    try:
        opslib.append_jsonl(SHADOW_LOG, rec)
    except Exception:  # noqa: BLE001
        pass


# ── تپشِ P1: حسِ قلب → (اگر اجازه) شادو-تست → وردیکت. هرگز اعمالِ زنده ───────────────
def tick(patch: dict | None = None, *, run_fn=None) -> dict:
    """یک تپش. patch = {target, content, intent} یا None (فقط سنجشِ حسِ قلب).
    خروجی: {mood, decision, shadow?}. اعمالِ زنده صفر؛ نوشتنِ لاگ فقط با فلگ."""
    mood = heart_mood()
    out = {"mood": mood, "acted": False}
    if mood["verdict"] == "freeze":
        out["decision"] = "🔒 heart-freeze — قلب اجازه نداد (ترس/σ/فروپاشی)"
    elif not patch:
        out["decision"] = f"قلب «{mood['mood']}» ({mood['verdict']}) — patchی برای تست نیست"
    else:
        res = shadow_test(patch.get("target", ""), patch.get("content", ""), run_fn=run_fn)
        out["acted"] = True
        out["shadow"] = res
        if res.get("ok") and res.get("green"):
            out["decision"] = "✅ سبز در سایه → آمادهٔ پیشنهاد به مالک (تپِ ✅ = فازِ بعد)"
        elif res.get("ok"):
            out["decision"] = "🔴 سوییت در سایه قرمز → patch رد شد (درختِ زنده امن)"
        else:
            out["decision"] = "⛔ " + str(res.get("reason") or "shadow-failed")
    if _flag_on():
        _log_shadow({"ts": opslib.now_iso(), **out})
    return out


# ══════════════════════════════════════════════════════════════════════════════
# سطح A — اکچوایتورِ اعمال (بعد از تپِ ✅ مالک، زیرِ قانونِ قلب). به شاخه اعمال می‌کند،
# canary می‌گیرد، روی قرمز auto-rollback + freeze. merge به masterِ زنده = گامِ جداگانه.
# ══════════════════════════════════════════════════════════════════════════════
ACTIVATION = opslib.OPS / "ACTIVATION-CODE-AUTONOMY.flag"   # فقط مالک می‌سازد
KILL = opslib.OPS / "STOP-CODE-AUTONOMY"                    # کیل‌سوئیچِ آنی
APPLIED_LOG = opslib.STATE_DIR / "cortex" / "code-autonomy-applied.jsonl"
REFRACTORY_S = 3600.0     # حداقل فاصلهٔ دو اعمال (کادنسِ قلب بعداً تیزترش می‌کند)
APPROVALS_DIR = opslib.STATE_DIR / "telegram" / "approvals"


def active() -> bool:
    """سطح A زنده است؟ فلگِ مالک هست و کیل‌سوئیچ نیست."""
    try:
        return ACTIVATION.exists() and not KILL.exists()
    except OSError:
        return False


# ۲۰۲۶-۰۷-۲۷ — سقفِ کهنگیِ تأیید.
#
# تا امروز `consume_approvals` هر تأییدِ اعمال‌نشده را می‌خواند **بدونِ هیچ چکِ
# زمان**. امروز بی‌خطر بود چون هر دو صف خالی‌اند و درایور اصلاً اجرا نمی‌شود —
# ولی این «امنیتِ تصادفی» است نه ساختاری. ترکیبِ خطرناک این است:
#   ۱) کارتِ پچ دکمه بگیرد → تأییدها جمع شوند
#   ۲) درایور روزها خاموش بماند (همین حالا خاموش است)
#   ۳) کسی `RUN-CODE-AUTONOMY.bat` را بزند → **همه با هم شلیک کنند**
# و آن پچ‌ها تا آن لحظه روی کدی نوشته شده‌اند که دیگر وجود ندارد.
#
# تأییدِ کهنه رضایتِ کهنه است. مالک به «همین پچ، همین حالا» آره گفته، نه به
# «هر وقت شد». fail-closed: زمانِ ناخوانا هم کهنه شمرده می‌شود.
APPROVAL_MAX_AGE_S = 48 * 3600


def _owner_approved(approval_id: str) -> bool:
    """تپِ ✅ مالک ثبت شده و **هنوز تازه است**؟ (approvals/<id>.json، verdict=ok)."""
    try:
        pth = APPROVALS_DIR / f"{approval_id}.json"
        d = json.loads(pth.read_text("utf-8"))
        if d.get("verdict") != "ok":
            return False
        import time as _t
        ts = d.get("epoch") or d.get("ts_epoch")
        try:
            age = _t.time() - float(ts) if ts else _t.time() - pth.stat().st_mtime
        except (TypeError, ValueError, OSError):
            return False                     # زمانِ ناخوانا → کهنه (fail-closed)
        if age > APPROVAL_MAX_AGE_S:
            try:
                opslib.alert([f"code-autonomy: تأییدِ {approval_id[:24]} "
                              f"{age / 3600:.0f} ساعت کهنه است — اعمال نشد؛ "
                              "کارت را دوباره از مالک بگیر"])
            except Exception:  # noqa: BLE001
                pass
            return False
        return True
    except Exception:  # noqa: BLE001
        return False


def _in_refractory(clock=None) -> bool:
    import time
    now = float((clock or time.time)())
    try:
        last = [json.loads(x) for x in APPLIED_LOG.read_text("utf-8").splitlines() if x.strip()]
        if last:
            t = float(last[-1].get("epoch", 0) or 0)
            return (now - t) < REFRACTORY_S
    except Exception:  # noqa: BLE001
        pass
    return False


def freeze_autonomy(reason: str) -> None:
    """کیل‌سوئیچِ خودکار: روی هر قرمزِ canary، خودمختاری فوراً می‌خوابد + هشدارِ مالک."""
    try:
        KILL.write_text(f"auto-freeze: {reason}", "utf-8")
        opslib.alert([f"CODE-AUTONOMY freeze: {reason}"])
    except Exception:  # noqa: BLE001
        pass


def apply_approved(patch: dict, approval_id: str, *, apply_fn=None, clock=None) -> dict:
    """اکچوایتورِ سطح A. **هشت گیتِ هم‌زمان، همه لازم:**
    ۱ فعال‌سازی (ACTIVATION + not KILL) · ۲ قلب ≠ freeze (بازچکِ لحظهٔ اعمال) ·
    ۳ تأییدِ مالک (تپِ ✅) · ۴ deny-list · ۵ shadow سبز (در patch) · ۶ refractory ·
    ۷ محتوای معتبر · ۸ اگر تأیید **خودکار** بود، پچ باید `risk_report` را پاس کند.
    هر کدام نبود → رد، صفر اعمال. apply_fn تزریق‌پذیر (تست)."""
    if not active():
        return {"ok": False, "reason": "not-activated (ACTIVATION-CODE-AUTONOMY خاموش یا KILL)"}
    m = heart_mood()
    if m["verdict"] == "freeze":                       # بازچکِ قلب در لحظهٔ اعمال (نه فقط propose)
        return {"ok": False, "reason": "heart-freeze", "mood": m}
    if not _owner_approved(approval_id):
        return {"ok": False, "reason": "no-owner-approval"}
    tgt = str((patch or {}).get("target", ""))
    if not allowed_target(tgt):
        return {"ok": False, "reason": "target-not-allowed"}
    if not (patch or {}).get("shadow_green"):
        return {"ok": False, "reason": "shadow-not-green (باید اول سبزِ سایه باشد)"}
    content = str((patch or {}).get("content", ""))
    if not content.strip():
        return {"ok": False, "reason": "empty-content"}
    if _in_refractory(clock):
        return {"ok": False, "reason": "refractory (خیلی زود بعد از اعمالِ قبل)"}
    # ── گیتِ ۸ (WS-7) — تأییدِ **خودکار** فقط برای پچِ کم‌ریسک ────────────────
    # فقط روی تأییدی که خودِ ارگانیسم زده (`by == auto-lowrisk`). انگشتِ مالک
    # هیچ‌وقت این‌جا نمی‌افتد ⇒ مسیرِ HITL بایت‌به‌بایتِ دیروز است. سنجیده شد:
    # هر ۴۳ فایلِ approvals/ روی درختِ زنده `by = None` دارند.
    if _approval_is_auto(approval_id):
        risk = low_risk_patch({"target": tgt, "content": content})
        if not risk.get("low_risk"):
            return {"ok": False, "reason": "not-low-risk (auto-approval)",
                    "risk": risk}

    res = apply_fn(tgt, content) if apply_fn is not None else _git_apply_canary(tgt, content)
    import time
    rec = {"ts": opslib.now_iso(), "epoch": float((clock or time.time)()),
           "target": tgt, "approval_id": approval_id, "mood": m["mood"],
           "applied": bool(res.get("applied")), "canary_green": res.get("green"),
           "rolled_back": res.get("rolled_back"), "reason": res.get("reason")}
    try:
        opslib.append_jsonl(APPLIED_LOG, rec)
    except Exception:  # noqa: BLE001
        pass
    if res.get("applied") and res.get("green") is False:
        freeze_autonomy(f"canary-red on {tgt}")
    return {"ok": True, **res, "record": rec}


def _write_keeping_newlines(tgt, text: str, before_b: bytes) -> None:
    """محتوای تازه را با **خطِ پایانِ خودِ فایل** بنویس.

    ⚠️ ۲۰۲۶-۰۷-۳۱: مسیرِ اعمال `tgt.write_text(...)` می‌زد. روی ویندوز آن
    `newline=None` است، یعنی هر `\\n` به `os.linesep` (`\\r\\n`) ترجمه می‌شود.
    مغزِ کد پچ را همیشه با LF تولید می‌کند، پس هر پچ روی یک فایلِ LF کلِ فایل
    را به CRLF برمی‌گرداند: دیفِ سه‌خطی به دیفِ **کلِ فایل** تبدیل می‌شود،
    مروری غیرممکن می‌شود، و روی درختِ مشترک هر هانکِ بیگانه در همان فایل
    لِه می‌شود. اثباتش روی هدفِ همین پچ: `_ops/cortex/registry.py` دقیقاً
    LF است (crlf=0, loneLF=77).

    قاعده: اگر فایل خالص CRLF بود CRLF بنویس، وگرنه LF. هیچ ترجمهٔ ضمنی.

    ⚠️ و newline ِ انتهایی: اولین پچِ واقعیِ اولاما آن را **انداخت**. گاردِ
    نحویِ `_defs_kept` نمی‌بیندش (تابع نیست) ولی هر پچ یک `\\ No newline at
    end of file` به دیف اضافه می‌کند و ابزارها را می‌رنجانَد. اگر فایل با
    newline تمام می‌شد، خروجی هم باید."""
    crlf = before_b.count(b"\r\n")
    lone = before_b.count(b"\n") - crlf
    body = str(text).replace("\r\n", "\n")
    if before_b.endswith(b"\n") and body and not body.endswith("\n"):
        body += "\n"
    if crlf and not lone:
        body = body.replace("\n", "\r\n")
    tgt.write_bytes(body.encode("utf-8"))


def _git_apply_canary(target_rel: str, new_content: str) -> dict:
    """مسیرِ واقعی: مبنا → نوشتنِ patch → commit → canary → مقایسه با مبنا.
    سبز = **هیچ شکستِ تازه** · قرمز: auto-rollback + freeze. masterِ زنده لمس
    نمی‌شود (merge = گامِ جداگانهٔ مالک). fail-soft.

    ⚠️ ۲۰۲۶-۰۷-۳۱ · رأیِ مالک (VQ-CANARY-001، گزینهٔ الف). تا امروز این تابع
    `run.returncode == 0` می‌سنجید، یعنی **سبزیِ مطلقِ** کلِ سوییت. مبنای
    درختِ زنده در همان لحظه ۹ سوییتِ قرمز داشت که هیچ‌کدام از هیچ پچی نبودند
    (test_llm_fence_coverage · test_llm_call_inventory · test_tg_verdict_durable
    · test_cb_token_legmiss · test_owner_answers_2026_07_27 · test_orphan_scan
    · test_d2_halt_coverage · test_tg_send_audit · test_tg_instant_and_sendlog).
    یعنی گیت ساختاراً هرگز پاس نمی‌شد: هر تأییدِ مالک به rollback + freeze ختم
    می‌شد. fail-closed ِ همیشگی یعنی قابلیت وجود ندارد.

    نکتهٔ عدم‌تقارن: مسیرِ **سایه** (`_git_shadow_test`) از ۰۷-۲۷ رگرسیونی بود
    و دلیلش را هم مستند کرده بود — فقط مسیرِ **اعمال** جا مانده بود. همان
    معیار این‌جا هم می‌آید، با همان `_run_suite`، نه یک پیاده‌سازیِ دوم.

    هزینه: دو دورِ سوییت (~۳۶ دقیقه با عددِ سنجیده‌شدهٔ ۱۰۷۸ ثانیه). سقف از
    `_suite_timeout_s()` می‌آید."""
    import os as _os
    repo = _OPS.parent
    tgt = repo.joinpath(*target_rel.split("/"))
    if not tgt.exists():
        return {"applied": False, "reason": "target-missing"}
    before_b = tgt.read_bytes()          # بازگردانیِ بایت‌به‌بایت، نه «تقریباً»
    committed = False        # ⚠️ باید **بیرونِ** try باشد — مسیرِ استثنا لازمش دارد
    try:
        env = dict(_os.environ); env["REAL_VAULT"] = str(repo); env["PYTHONUTF8"] = "1"
        # مبنا **قبل** از نوشتن — روی همان درخت، همان لحظه. مبنای کهنه یعنی
        # انتسابِ شکستِ کسِ دیگر به این پچ.
        base = _run_suite(repo, env)
        _write_keeping_newlines(tgt, new_content, before_b)
        subprocess.run(["git", "-C", str(repo), "add", target_rel],
                       capture_output=True, text=True, timeout=60)
        cm = subprocess.run(["git", "-C", str(repo), "commit", "-m",
                             f"auto(code-autonomy L-A): {target_rel} — approved+shadow-green, canary…"],
                            capture_output=True, text=True, timeout=60)
        committed = cm.returncode == 0
        cand = _run_suite(repo, env)
        new_fails = sorted(cand["fails"] - base["fails"])
        fixed = sorted(base["fails"] - cand["fails"])
        # عیناً معیارِ `_git_shadow_test`: هیچ شکستِ تازه. اگر مبنا خودش پاک
        # بود، این دقیقاً همان `returncode == 0` ِ قبلی است — پس سخت‌گیری روی
        # درختِ سالم ذره‌ای کم نشده.
        green = not new_fails and (cand["code"] == 0 or bool(base["fails"]))
        if not green:                                   # auto-rollback
            if committed:
                subprocess.run(["git", "-C", str(repo), "revert", "--no-edit", "HEAD"],
                               capture_output=True, text=True, timeout=60)
            else:
                tgt.write_bytes(before_b)
                subprocess.run(["git", "-C", str(repo), "restore", "--staged", "--worktree",
                                target_rel], capture_output=True, text=True, timeout=30)
        return {"applied": committed, "green": green, "target": target_rel,
                "rolled_back": (not green), "branch_only": True,
                "baseline_fails": sorted(base["fails"]), "new_fails": new_fails,
                "fixed_fails": fixed, "base_seconds": base.get("seconds"),
                "cand_seconds": cand.get("seconds")}
    except Exception as e:  # noqa: BLE001
        # ⚠️ ۲۰۲۶-۰۷-۳۰: نسخهٔ قبلی این‌جا فقط **محتوای فایل** را برمی‌گرداند.
        # ولی پرتکرارترین استثنای این مسیر `TimeoutExpired` ِ خودِ سوییت است —
        # که **بعد** از commit رخ می‌دهد. نتیجه: کامیت در تاریخچه می‌ماند، دیسک
        # به نسخهٔ قبل برمی‌گردد، و گزارش می‌گوید «اعمال نشد، برگردانده شد».
        # سه‌گانهٔ ناسازگار، روی درختی که جلسهٔ موازی هم رویش کار می‌کند.
        # حالا مسیرِ استثنا **همان** rollback ِ مسیرِ قرمز را می‌زند.
        try:
            if committed:
                subprocess.run(["git", "-C", str(repo), "revert", "--no-edit", "HEAD"],
                               capture_output=True, text=True, timeout=60)
            else:
                tgt.write_bytes(before_b)
        except Exception:  # noqa: BLE001
            pass
        return {"applied": False, "reason": f"apply-error:{type(e).__name__}",
                "rolled_back": True, "was_committed": committed}


def propose_to_owner(patch: dict) -> dict:
    """patchِ سبزِ سایه را به مالک پیشنهاد می‌دهد: pending ذخیره + کارتِ تصمیم در تاپیکِ سیستم.
    id = code-<hash>؛ تپِ ✅ مالک → approvals/<id>.json → consume_approvals اعمال می‌کند.
    fail-soft: بی‌تلگرام هم pending را ذخیره می‌کند. هرگز خودش اعمال نمی‌کند."""
    if not (patch or {}).get("shadow_green"):
        return {"ok": False, "reason": "not-shadow-green"}
    tgt = str((patch or {}).get("target", ""))
    if not allowed_target(tgt):
        return {"ok": False, "reason": "target-not-allowed"}
    import hashlib
    did = "code-" + hashlib.sha256(
        (tgt + str(patch.get("content", ""))).encode("utf-8")).hexdigest()[:10]
    rec = {**patch, "id": did, "target": tgt}
    pend = opslib.STATE_DIR / "cortex" / "pending-patches"
    try:
        pend.mkdir(parents=True, exist_ok=True)
        (pend / f"{did}.json").write_text(json.dumps(rec, ensure_ascii=False), "utf-8")
    except OSError:
        return {"ok": False, "reason": "pending-write-failed"}
    posted = None
    try:                                                # پستِ کارت — fail-soft
        sys.path.insert(0, str(_OPS / "telegram_center"))
        import tg_api
        import render
        cfg = json.loads((opslib.STATE_DIR / "telegram" / "center-config.json").read_text("utf-8"))
        item = {"q": f"مغز یک patch نوشت + سایهٔ سبز — اعمال کنم؟ ({tgt})",
                "why": str(patch.get("intent", "") or patch.get("diff", ""))[:140],
                "source": "approval", "id": did, "priority": "کد"}
        text, kb = render.render_decision(item)
        text = "🧠🫀 <b>خودمختاریِ کد — زیرِ قانونِ قلب</b>\n" + text
        c = tg_api.TgClient()
        # ── مقصد از قراردادِ مسیریابی، نه هاردکدِ گروه (۲۰۲۶-۰۷-۳۰) ──────────
        # تا امروز این کارت به `topics["system"]` ِ **گروه** می‌رفت. با
        # قراردادِ مصوبِ legs-only آن نقض است: پچِ کد هسته‌ای است، نه پا — و
        # بدتر، مالک باید در همان لحظه رأی بدهد. `code-card` در
        # surface-routing.json تعریف شد؛ فلگ خاموش = همان system ِ قبلی
        # بایت‌به‌بایت، فلگ روشن = DM ِ لنگر. دکمه‌ها روی همان باتِ outer
        # می‌مانند چون handler ِ approval آن‌جاست (درسِ کارتِ مرده).
        _chat, _topic = cfg.get("chat_id"), (cfg.get("topics") or {}).get("system")
        try:
            import surface_router as _sr
            _cl, _cid, _tid = _sr.resolve(
                "code-card", clients={"outer": c, "inner": None}, cfg=cfg)
            if _cl is not None:
                c, _chat, _topic = _cl, _cid, _tid
        except Exception:  # noqa: BLE001 — روتر هرگز کارت را نمی‌کشد
            pass
        posted = c.send(text, keyboard=kb, chat_id=_chat, topic_id=_topic)
    except Exception:  # noqa: BLE001
        posted = None
    return {"ok": True, "id": did, "posted": posted}


def _applied_ids() -> set:
    """approval_idهایی که قبلاً applied=True شده‌اند — dedup (هرگز دوباره اعمال)."""
    ids = set()
    try:
        for x in APPLIED_LOG.read_text("utf-8").splitlines():
            if x.strip():
                d = json.loads(x)
                if d.get("applied"):
                    ids.add(d.get("approval_id"))
    except Exception:  # noqa: BLE001
        pass
    return ids


def consume_approvals(*, apply_fn=None) -> dict:
    """approvalهای تأییدشدهٔ code-* را می‌خواند و patchِ متناظر (pending-patches/<id>.json)
    را **یک‌بار** اعمال می‌کند: dedup با applied-log + حذفِ patchِ مصرف‌شده از صف.
    زیرِ همهٔ گیت‌های apply_approved (فعال‌سازی/قلب/تأیید/deny/سایه/refractory)."""
    out = {"applied": 0, "skipped": 0}
    if not active():
        out["reason"] = "not-activated"; return out
    done = _applied_ids()
    pend = opslib.STATE_DIR / "cortex" / "pending-patches"
    try:
        files = sorted(pend.glob("*.json")) if pend.exists() else []
    except OSError:
        files = []
    for pf in files:
        try:
            patch = json.loads(pf.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        aid = patch.get("id") or pf.stem
        if aid in done or not _owner_approved(aid):     # قبلاً اعمال یا بی‌تأیید → رد
            out["skipped"] += 1
            continue
        r = apply_approved(patch, aid, apply_fn=apply_fn)
        if r.get("ok") and r.get("applied"):
            out["applied"] += 1
            try:
                pf.unlink()                             # patchِ مصرف‌شده از صف حذف
            except OSError:
                pass
        else:
            out["skipped"] += 1
    return out


def run_forever(*, every_s: float = 300.0) -> None:
    """درایورِ سطح A: هر every_s ثانیه consume_approvals. active()/قلب/refractory همه‌چیز را
    گیت می‌کنند. kill: فایلِ STOP-CODE-AUTONOMY (توقفِ آنی). بدونِ ACTIVATION = no-opِ امن."""
    import time
    while not KILL.exists():
        try:
            if active():
                consume_approvals()
        except Exception:  # noqa: BLE001
            pass
        for _ in range(max(1, int(every_s // 5))):
            if KILL.exists():
                break
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        try:
            import env_loader
            env_loader.load_env()
        except Exception:  # noqa: BLE001
            pass
        print("code-autonomy driver: زنده — kill: فایلِ _ops/STOP-CODE-AUTONOMY")
        run_forever()
    else:
        print(json.dumps({"mood": heart_mood(), "active": active(),
                          "activation_flag": str(ACTIVATION), "tick": tick()},
                         ensure_ascii=False, indent=2))
