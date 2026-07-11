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
         "registry_scan", "organism", "germline")
_ALLOW_ROOTS = ("_ops/telegram_center/", "_ops/cortex/")

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
    heart = hs.get("heart") if isinstance(hs.get("heart"), dict) else {}
    sig = heart.get("sigma", hs.get("sigma"))
    try:
        sigma_bad = sig is not None and float(sig) >= 1.0     # σ=۱ = محورِ فروپاشی
    except (TypeError, ValueError):
        sigma_bad = False

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
    """فقط allowlist و هرگز deny-list. fail-closed (خالی/مشکوک = False)."""
    p = str(path or "").replace("\\", "/").lower()
    if not p or any(d in p for d in _DENY):
        return False
    return any(r in p for r in _ALLOW_ROOTS)


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


def _git_shadow_test(target_rel: str, new_content: str) -> dict:
    """مسیرِ واقعی: git worktree از HEAD → نوشتنِ patch در نسخهٔ ایزوله → سوییتِ کامل → پاک‌سازی.
    fail-soft: هر خطای git/اجرا → ok:False. درختِ زنده هرگز لمس نمی‌شود."""
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
        tgt.write_text(new_content, "utf-8")
        diff = subprocess.run(["git", "-C", str(wt), "diff", "--stat"],
                              capture_output=True, text=True, timeout=30)
        import os as _os
        env = dict(_os.environ)
        env["REAL_VAULT"] = str(wt)
        env["PYTHONUTF8"] = "1"
        run = subprocess.run([sys.executable, "-X", "utf8",
                              str(wt / "_ops" / "tests" / "run_all.py")],
                             capture_output=True, text=True, timeout=600, env=env)
        green = run.returncode == 0
        tail = "\n".join((run.stdout or "").splitlines()[-3:])
        return {"ok": True, "green": green, "target": target_rel,
                "diff": (diff.stdout or "").strip()[:400], "suite_tail": tail,
                "changed_bytes": len(new_content) - len(old)}
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


if __name__ == "__main__":
    print(json.dumps(tick(), ensure_ascii=False, indent=2))
