#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_patch.py — پلِ گمشده: از «نقصی پیدا کردم» به «پچی نوشتم و تستش کردم».

رأیِ مالک ۲۰۲۶-۰۷-۲۶: «باید خودشو بسازه، خودشو بهتر کنه، نه الکی فقط نگاه».
مرزِ انتخاب‌شده: **الف** — اختاپوس پچ را می‌نویسد و در انزوا تست می‌کند، ولی
اعمال همیشه با یک کلیکِ مالک است. هرگز auto-merge.

═══ چرا این ماژول لازم شد ═══
دو نیمه از قبل وجود داشتند و به هم وصل نبودند:
  · `c6_trigger` نقص را پیدا می‌کند و `fix_hint` می‌دهد — ولی **کد تولید نمی‌کند**.
  · `cortex.code_autonomy.shadow_test` یک پچ را در worktreeِ ایزوله می‌زند و کلِ
    سوییت را می‌گیرد — ولی **منتظرِ محتوایی است که کسی نمی‌نوشت**.
نتیجه: چهار چرخهٔ کاملِ خودبهبودی در ۲۰۲۶-۰۷-۲۶ دویدند و هر چهار روی «کارت به
مالک» تمام شدند. هیچ‌کدام به تغییرِ کد نرسید. هر فیکسی که آن روز روی دیسک نشست
را یک ایجنت زد، نه ارگانیسم.

═══ چرا مرزِ الف و نه merge خودکار ═══
همان روز اختاپوس چهار نقص در خودش پیدا کرد و **هر چهار درست بودند**. ولی ایجنتی
که این را می‌نویسد **سه بار** چیزی را باگ خواند که باگ نبود (فیلدِ اشتباه به
lead_scorer، rate-limiter به‌جای مغزِ مرده، تکرارِ تستِ خودش). نرخِ خطای تشخیص
صفر نیست. تا وقتی لایهٔ حس شش پروب دارد، merge خودکار زود است.

═══ ناوردی‌ها ═══
· allowlist از `code_autonomy.allowed_target` قرض گرفته می‌شود، بازنویسی نمی‌شود
  (فقط `telegram_center/` و `cortex/`؛ deny روی .git/ژنوم/ledger/.env/secret/
  budget/money). این ماژول **هرگز** allowlist خودش را نمی‌سازد.
· هیچ پچی بدونِ سوییتِ سبز پیشنهاد نمی‌شود. تستِ قرمز = بایگانی، نه کارت.
· هرگز به درختِ زنده نمی‌نویسد. تنها اثرِ جانبی: یک فایلِ پیشنهاد در
  `state/self-patch/` و یک کارت.
· پیش‌فرض خاموش (`OCTOPUS_WIRE_SELF_PATCH`).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "budget", _HERE / "cortex"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_SELF_PATCH"
MAX_FILE_BYTES = 60_000       # فایلِ بزرگ‌تر از این در promptِ مغز جا نمی‌شود
DAILY_CAP = 3                 # سقفِ پیشنهادِ روزانه — توجهِ مالک کمیاب است


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _dir() -> Path:
    return opslib.STATE_DIR / "self-patch"


def _today_count() -> int:
    d = _dir()
    if not d.exists():
        return 0
    today = time.strftime("%Y-%m-%d")
    return sum(1 for p in d.glob("*.json")
               if time.strftime("%Y-%m-%d", time.localtime(p.stat().st_mtime)) == today)


_SYSTEM = (
    "You repair Python. You are given one file and one defect description.\n"
    "Return the COMPLETE corrected file and nothing else — no prose, no fences, "
    "no explanation. Preserve every unrelated line byte-for-byte, including "
    "comments and their language. Make the smallest change that fixes the "
    "described defect. If you cannot fix it with certainty, return the file "
    "completely unchanged."
)


def _ask(prompt: str, ask_fn=None) -> str:
    if ask_fn is None:
        try:
            import model_router
            ask_fn = model_router.ask
        except Exception:  # noqa: BLE001
            return ""
    try:
        # tier=primary عمداً: نوشتنِ کد کارِ سنگین است و لایهٔ محلی روی آن
        # جوابِ طوطی‌وار می‌دهد. مغزِ پولی همان روز سنجیده شد: ۲.۳ ثانیه، پلنِ فلت.
        r = ask_fn("plan", prompt, system=_SYSTEM, max_tokens=4000, tier="primary")
    except Exception:  # noqa: BLE001
        return ""
    if not isinstance(r, dict) or not r.get("ok"):
        return ""
    return str(r.get("text") or "")


def _strip_fences(text: str) -> str:
    t = str(text or "").strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t


def propose(*, target_rel: str, defect: str, fix_hint: str = "",
            ask_fn=None, shadow_fn=None) -> dict:
    """یک پچ برای یک نقصِ مشخص بنویس، ایزوله تست کن، و نتیجه را برگردان.

    خروجی همیشه dict با `ok`. `ok=True` **فقط** وقتی سوییت در worktreeِ ایزوله
    سبز شد — یعنی هر کارتی که از این می‌آید، پشتش یک اجرای واقعی است نه یک ادعا.
    هیچ‌جا اعمال نمی‌کند؛ آن یک کلیکِ جداست."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    try:
        import code_autonomy as ca
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"code_autonomy-unavailable:{type(e).__name__}"}
    if not ca.allowed_target(target_rel):
        # allowlist قرض گرفته می‌شود، هرگز این‌جا بازتعریف نمی‌شود.
        return {"ok": False, "reason": "target-not-allowed", "target": target_rel}
    if _today_count() >= DAILY_CAP:
        return {"ok": False, "reason": "daily-cap", "cap": DAILY_CAP}

    root = _HERE.parent
    src = root / target_rel
    try:
        original = src.read_text("utf-8")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"unreadable:{type(e).__name__}", "target": target_rel}
    if len(original.encode("utf-8")) > MAX_FILE_BYTES:
        return {"ok": False, "reason": "file-too-large", "bytes": len(original.encode())}

    prompt = (f"FILE: {target_rel}\nDEFECT: {defect}\n"
              f"HINT: {fix_hint or '(none)'}\n\n--- BEGIN FILE ---\n{original}\n--- END FILE ---")
    candidate = _strip_fences(_ask(prompt, ask_fn=ask_fn))
    if not candidate.strip():
        return {"ok": False, "reason": "brain-no-answer", "target": target_rel}
    if candidate.strip() == original.strip():
        # مدل صریحاً گفت مطمئن نیستم — این شکست نیست، صداقت است.
        return {"ok": False, "reason": "no-change-proposed", "target": target_rel}

    shadow = (shadow_fn or ca.shadow_test)(target_rel, candidate)
    green = bool(isinstance(shadow, dict) and shadow.get("green"))
    rec = {
        "id": "sp-" + hashlib.sha1(
            f"{target_rel}|{defect}".encode("utf-8")).hexdigest()[:12],
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target": target_rel, "defect": str(defect)[:400],
        "fix_hint": str(fix_hint)[:300],
        "green": green,
        "shadow_reason": (shadow or {}).get("reason"),
        "diff": str((shadow or {}).get("diff") or "")[:600],
        "suite_tail": str((shadow or {}).get("suite_tail") or "")[:400],
        "bytes_before": len(original.encode("utf-8")),
        "bytes_after": len(candidate.encode("utf-8")),
    }
    try:
        _dir().mkdir(parents=True, exist_ok=True)
        (_dir() / f"{rec['id']}.json").write_text(
            json.dumps({**rec, "candidate": candidate}, ensure_ascii=False, indent=1),
            encoding="utf-8")
    except OSError:
        pass
    if not green:
        # قرمز = بایگانی، نه کارت. توجهِ مالک برای پچی که تست را نمی‌گذراند
        # خرج نمی‌شود — و همان رکورد می‌ماند تا بعداً بشود فهمید چرا شکست.
        return {"ok": False, "reason": "shadow-red", **rec}
    return {"ok": True, **rec}


def card_text(rec: dict) -> str:
    """کارتی که مالک می‌بیند. طبق دکترین: می‌گوید اگر کاری نکنی چه می‌شود،
    و هیچ ادعایی نمی‌کند که پشتش اجرا نباشد."""
    return (
        "🔧 <b>یک باگ در خودم پیدا کردم و پچش را نوشتم</b>\n"
        f"▸ فایل: <code>{rec.get('target')}</code>\n"
        f"▸ نقص: {str(rec.get('defect'))[:180]}\n"
        f"▸ سوییتِ کامل در نسخهٔ ایزوله: <b>سبز</b>\n"
        f"▸ نکنی: پچ همان‌جا می‌ماند و باگ سرِ جایش است — چیزی خودکار اعمال نمی‌شود\n"
        f"\n<code>{str(rec.get('diff'))[:300]}</code>"
    )


if __name__ == "__main__":  # pragma: no cover — پیش‌نمایشِ بی‌ارسال
    print(f"flag {FLAG} = {'on' if enabled() else 'off'} · "
          f"today {_today_count()}/{DAILY_CAP}")
    d = _dir()
    if d.exists():
        for p in sorted(d.glob("*.json")):
            r = json.loads(p.read_text("utf-8"))
            print(f"  {r.get('id')}  {r.get('target'):40s} green={r.get('green')}")
