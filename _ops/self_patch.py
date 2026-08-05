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
import arm_gate  # noqa: E402

FLAG = "OCTOPUS_WIRE_SELF_PATCH"
PATCH_MAX_TOKENS = 4000       # سقفِ خروجیِ نوشتنِ پچ
# قرارداد «کلِ فایلِ اصلاح‌شده را برگردان» یعنی سقفِ **ورودی** نمی‌تواند از سقفِ
# **خروجی** بزرگ‌تر باشد. ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷: ۶۰٬۰۰۰ بایت پذیرفته می‌شد در
# حالی که ۴۰۰۰ توکن حدودِ ۱۲–۱۴KB کد بیرون می‌دهد، پس هر فایلِ بزرگ‌تر ساختاراً
# نیمه‌کاره برمی‌گشت و سوییت را قرمز می‌کرد بی‌آنکه کسی بفهمد چرا.
# ~۳ بایت بر توکن، محافظه‌کار.
MAX_FILE_BYTES = PATCH_MAX_TOKENS * 3
DAILY_CAP = 3                 # سقفِ پیشنهادِ روزانه — توجهِ مالک کمیاب است


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ═══ سهمِ self_patch از سقفِ سراسریِ فوگو (۲۰۲۶-۰۸-۰۵) ══════════════════════
# رأیِ مالک (اجازهٔ کاملِ امشب): «همیشه ... سهمِ توکنش رو بگیره». الگو **عیناً**
# از cockpit_brain._brain_cap قرض گرفته می‌شود، نه از نو اختراع — آن‌جا با
# شاهدِ زنده ثابت شد: سقفِ سراسریِ FUGU_DAILY_CALL_CAP در OCTOPUS-flags.cmd ِ
# زنده امروز **۶۰** است (نه ۳۰۰ ِ پیش‌فرضِ fugu_quota._cap — عددِ کد، نه عددِ
# تولید)، و model_router هر تماسِ پولیِ self_patch را هم از همان
# fugu_quota.reserve رد می‌کند. یعنی وقتی بقیهٔ ارگانیسم آن ۶۰ تا را زودتر پر
# کند، مرورِ روزانه یا پچ‌نویسیِ self_patch **بی‌صدا رد** می‌شود — دقیقاً همان
# گرسنگی‌ای که DAILY_CAP بالا برایش طراحی نشده: DAILY_CAP فقط رکوردِ پیشنهاد
# را می‌شمارد (بعد از شادو-تست، در `_dir()`)؛ مدلی که خالی یا بی‌تغییر جواب
# بدهد (`brain-no-answer`/`no-change-proposed`) هیچ رکوردی نمی‌نویسد، پس
# می‌تواند بارها تماسِ پولیِ واقعی بزند بی‌آنکه DAILY_CAP اصلاً بفهمد.
#
# پس این‌جا یک سهمِ **مستقل و محافظت‌شده** از همان سقفِ سراسری کنار گذاشته
# می‌شود — دقیقاً همان‌طور که cockpit_brain سهمِ خودش را کنار می‌گذارد. یک
# شمارندهٔ روزانهٔ خودِ self_patch (نه sp-*.json ِ رکوردها — قصداً در زیرپوشهٔ
# جدا، چون `_today_count()` بالا با `glob("*.json")` هر فایلِ json ِ کنارش را
# هم می‌شمرد و سقفِ DAILY_CAP را کاذب زودتر می‌بست).
#
# صداقتاً چه چیزی این گارد **نیست**: fugu_quota یک شمارندهٔ FIFO ِ مشترک است،
# بدونِ صف‌بندیِ اولویت‌دار. این گارد self_patch را از گرسنه‌کردنِ بقیهٔ
# ارگانیسم باز می‌دارد (سقفِ خودش بالا نمی‌رود) ولی رزروِ واقعیِ ضدِ‌گرسنگی —
# self_patch همیشه جواب بگیرد حتی اگر ۶۰ تماسِ دیگر زودتر رسیده باشند —
# نیازمندِ اولویت‌بندی در خودِ fugu_quota است، بیرون از دامنهٔ این پَس. عیناً
# همان محدودیتی که cockpit_brain._brain_cap هم دارد.
#
# چرا سهمِ پیش‌فرض ۰.۱۲: self_patch روزی حداکثر ۱ مرور + DAILY_CAP=3 پیشنهاد
# = ۴ تماسِ پولی می‌زند — در برابرِ حلقهٔ پیوستهٔ ۵دقیقه‌ایِ cockpit_brain
# (سهمِ ۰.۲۵) این خیلی سبک‌تر است. ۰.۱۲ روی سقفِ زندهٔ ۶۰ یعنی سهمِ ۷تایی:
# بیش از کافی برای ۴ تماسِ روزانه با حاشیهٔ امن، و آن‌قدر کوچک که خودش سهمِ
# بقیهٔ ارگانیسم را نمی‌بلعد.
SELF_PATCH_SHARE_ENV = "OCTOPUS_SELF_PATCH_CALL_SHARE"
_SELF_PATCH_DEFAULT_SHARE = 0.12
#: شمارندهٔ خودِ self_patch، جدا از سهمیهٔ سراسریِ ارگانیسم و جدا از
#: رکوردهای propose() (که با `sp-*.json` در همین _dir() نشسته‌اند).
SELF_PATCH_CALLS = opslib.STATE_DIR / "self-patch" / "quota" / "calls.json"


def _self_patch_cap() -> int:
    """سقفِ روزانهٔ تماسِ self_patch — مشتق از سقفِ واقعیِ مشترکِ فوگو، نه
    عددِ مستقل. عیناً الگوی cockpit_brain._brain_cap (fail-closed: نمی‌دانم
    ⇒ خرج نکن)."""
    try:
        import fugu_quota
        shared = int(fugu_quota._cap())  # noqa: SLF001 — تکِ منبعِ حقیقت
    except Exception:  # noqa: BLE001
        return 0
    try:
        share = float(os.environ.get(SELF_PATCH_SHARE_ENV, "") or 0)
    except (TypeError, ValueError):
        share = 0
    if not (0 < share <= 1):
        share = _SELF_PATCH_DEFAULT_SHARE
    return max(1, int(shared * share))


def _self_patch_used(now: "float | None" = None) -> int:
    try:
        d = json.loads(SELF_PATCH_CALLS.read_text("utf-8")) or {}
    except Exception:  # noqa: BLE001
        d = {}
    today = time.strftime("%Y-%m-%d", time.localtime(now) if now else time.localtime())
    return int(d.get("n") or 0) if str(d.get("day") or "") == today else 0


def _self_patch_count(now: "float | None" = None) -> None:
    """شمارنده **قبل از** تماس بالا می‌رود — اندپوینتِ خراب هم باید بسوزاند،
    وگرنه یک حلقهٔ شکستِ بی‌نهایت هرگز سقف را نمی‌بندد (همان اصلِ
    attempt-counted ِ fugu_quota و cockpit_brain._brain_count)."""
    try:
        SELF_PATCH_CALLS.parent.mkdir(parents=True, exist_ok=True)
        today = time.strftime("%Y-%m-%d", time.localtime(now) if now else time.localtime())
        SELF_PATCH_CALLS.write_text(json.dumps(
            {"day": today, "n": _self_patch_used(now) + 1}), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _self_patch_may_spend(now: "float | None" = None) -> "tuple[bool, str]":
    """(اجازه، دلیل). fail-closed: هر ابهامی ⇒ نه.
    قبل از **هر دو** مسیرِ تماسِ پولیِ self_patch صدا زده می‌شود: مرور
    (`review_and_queue`) و پچ‌نویسی (`propose`) — چون هر دو از همان سهمِ
    مشترکِ روزانه می‌خورند."""
    used, cap = _self_patch_used(now), _self_patch_cap()
    if used >= cap:
        return False, f"self-patch-quota:{used}/{cap}"
    return True, f"{used}/{cap}"


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
    # شمارندهٔ سهمِ self_patch — قبل از تماس، عیناً اصلِ attempt-counted
    # (خودِ گاردِ اجازه در propose() است؛ این‌جا فقط شمارشِ تلاشِ واقعی).
    _self_patch_count()
    try:
        # tier=primary عمداً: نوشتنِ کد کارِ سنگین است و لایهٔ محلی روی آن
        # جوابِ طوطی‌وار می‌دهد. مغزِ پولی همان روز سنجیده شد: ۲.۳ ثانیه، پلنِ فلت.
        r = ask_fn("plan", prompt, system=_SYSTEM, max_tokens=PATCH_MAX_TOKENS,
                   tier="primary")
    except Exception:  # noqa: BLE001
        return ""
    # همان گاردِ deep_think: پین فقط درخواست را می‌بندد. یک پچِ پایتونی که مدلِ
    # محلیِ ۱.۵B نوشته باشد نباید حتی وارد شادو-تست شود.
    if isinstance(r, dict) and (r.get("fallback_from") or
                                (r.get("tier") and r.get("tier") != "primary")):
        opslib.alert([f"self_patch: نوشتنِ پچ به مغزِ گران نرسید "
                      f"({r.get('fallback_from') or r.get('tier')}) — رها شد"])
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
    allow, why = _self_patch_may_spend()
    if not allow:
        # سهمِ self_patch از فوگو امروز تمام شده — گذرا است، نه شکستِ نقص
        # (drive._TRANSIENT پایینِ فایل همین دلیل را می‌شناسد).
        return {"ok": False, "reason": "self-patch-quota", "quota": why, "target": target_rel}

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
        # ۲۰۲۶-۰۷-۲۷ — متنِ پچ تا امروز **ذخیره نمی‌شد**، فقط diffِ ۶۰۰کاراکتری.
        # یعنی حتی اگر مالک «آره» می‌زد، چیزی برای اعمال وجود نداشت: کارت یک
        # گزارش بود نه یک پیشنهادِ اجراشدنی. بدونِ این کلید، کلِ حلقهٔ خودپچ‌زنی
        # ساختاراً به بن‌بست می‌خورد — و هیچ‌کس نمی‌فهمید چون هر تکه جدا کار
        # می‌کرد.
        "content": candidate,
        "shadow_green": green,
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
    و هیچ ادعایی نمی‌کند که پشتش اجرا نباشد.

    ⚠️ escape اجباری (ممیزیِ ۲۰۲۶-۰۷-۲۷): این کارت **متنِ مدل** (`defect`) و
    **کدِ خام** (`diff`) را داخلِ `parse_mode=HTML` می‌گذارد. یک `<` در هرکدام
    کلِ پیام را ۴۰۰ می‌کند و — چون `send_text` استثنا را می‌بلعد — کارت بی‌هیچ ردی
    گم می‌شود. برای کارتی که کلِ خروجیِ حلقهٔ خودپچ‌زنی است، یعنی سکوتِ کامل.
    و diff تقریباً همیشه `<` و `>` دارد."""
    import html as _h
    return (
        "🔧 <b>یک باگ در خودم پیدا کردم و پچش را نوشتم</b>\n"
        f"▸ فایل: <code>{_h.escape(str(rec.get('target') or ''))}</code>\n"
        f"▸ نقص: {_h.escape(str(rec.get('defect') or ''))[:180]}\n"
        f"▸ سوییتِ کامل در نسخهٔ ایزوله: <b>سبز</b>\n"
        f"▸ نکنی: پچ همان‌جا می‌ماند و باگ سرِ جایش است — چیزی خودکار اعمال نمی‌شود\n"
        f"\n<code>{_h.escape(str(rec.get('diff') or ''))[:300]}</code>"
    )


# ═══ حلقهٔ خودگردان (۲۰۲۶-۰۷-۲۷، «هردو کامل انجام بشه») ═══════════════════════
# تا امروز propose() یتیم بود: هیچ‌کس صدایش نمی‌زد و code_autonomy اصلاً روی این
# شاخه نبود. حالا حلقه کامل است و **تولیدکنندهٔ نقص، خودِ مغزِ گران است**:
#   ۱) review_and_queue: روزی یک فایل از allowlist را به Fugu می‌دهد («یک نقصِ
#      مشخص پیدا کن یا بگو تمیز است») → صفِ نقص. هیچ نقصِ دست‌ساز کاشته نمی‌شود.
#   ۲) drive: یک ردیفِ باز از صف → propose() → پچ + سوییتِ سبزِ ایزوله → کارت.
#   ۳) beat_async: هر دو را در یک threadِ جدا می‌دواند — تیکِ ارگانیسم هرگز پشتِ
#      تماسِ ۳۰ ثانیه‌ای یا سوییتِ چند دقیقه‌ای نمی‌ایستد.
# صف append-only است؛ ردیف **قبل از** تماسِ گران قفل می‌شود (درسِ deep_think).

QUEUE_PATH = opslib.STATE_DIR / "self-patch" / "defect-queue.jsonl"
REVIEW_STATE = opslib.STATE_DIR / "self-patch" / "review-state.json"
REVIEW_MAX_TOKENS = 700
_BEAT_LOCK = __import__("threading").Lock()


# یک ردیفِ `taken` که بیش از این بماند، یعنی پروسه وسطِ کار مرده — دوباره باز می‌شود.
# سقف = تماسِ مغز (~۳۰s) + دو اجرای سوییتِ سایه (۶۰۰s هرکدام) + سرریز.
TAKEN_STALE_S = 1800.0


def _queue_rows() -> list:
    """صف را **خط‌به‌خط** بخوان. یک خطِ خراب نباید کلِ صف را نامرئی کند.

    ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷: نسخهٔ قبلی همهٔ خط‌ها را در یک try می‌خواند و
    `json.JSONDecodeError` زیرمجموعهٔ `ValueError` است — پس **یک** خطِ نصفه (که
    append ِ غیراتمیک در قطعِ برق دقیقاً می‌سازد) کلِ صف را `[]` می‌کرد، بی‌صدا و
    برای همیشه: `drive` می‌گفت queue-empty و `beat_async` می‌گفت nothing-to-do."""
    rows, bad = [], 0
    try:
        if not QUEUE_PATH.exists():
            return []
        for line in QUEUE_PATH.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if isinstance(r, dict):
                rows.append(r)
    except OSError:
        return []
    if bad:
        try:
            opslib.alert([f"self_patch: {bad} خطِ خراب در defect-queue.jsonl "
                          f"رد شد ({len(rows)} ردیفِ سالم خوانده شد)"])
        except Exception:  # noqa: BLE001
            pass
    return rows


def _queue_append(row: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _defect_id(target: str, defect: str) -> str:
    return "sp-" + hashlib.sha1(f"{target}|{defect}".encode("utf-8")).hexdigest()[:12]


def review_targets() -> list:
    """فایل‌های قابلِ مرور: فقط allowlistِ code_autonomy، مرتب و قطعی."""
    try:
        import code_autonomy as ca
    except Exception:  # noqa: BLE001
        return []
    root = _HERE.parent   # ریشهٔ repo (F:\backup)
    out = []
    for sub in ("_ops/telegram_center", "_ops/cortex"):
        d = root / sub.replace("_ops/", "_ops" + os.sep)
        for p in sorted(d.glob("*.py")):
            rel = f"{sub}/{p.name}"
            # کفِ ۵۱۲ بایت: اسموکِ زندهٔ ۰۷-۲۷ اولین اسلاتِ روز را سرِ __init__.py ِ
            # خالی سوزاند — فایلِ بی‌گوشت ارزشِ یک مرورِ گرانِ روزانه را ندارد.
            # سقف = همان MAX_FILE_BYTES ِ پچ‌نویسی: مرورِ فایلی که پچش ساختاراً جا
            # نمی‌شود، یک تماسِ پولیِ تضمین‌شده-بی‌ثمر است (ممیزیِ ۰۷-۲۷؛ سقفِ مرور
            # ۴۸KB بود در حالی که پچ ~۱۲KB بیرون می‌دهد).
            if (ca.allowed_target(rel)
                    and 512 <= p.stat().st_size <= MAX_FILE_BYTES):
                out.append(rel)
    return out


_REVIEW_SYSTEM = (
    "تو بازبینِ کدِ خودِ این ارگانیسم هستی و جوابت مستقیم واردِ صفِ پچ می‌شود، پس "
    "فقط نقصی را گزارش کن که حاضری پشتش بایستی.\n"
    "خروجی دقیقاً یکی از این دو است:\n"
    "CLEAN\n"
    "یا یک خطِ JSON:\n"
    '{"defect": "<شرحِ دقیقِ نقص با ارجاع به خطِ/تابعِ مشخص>", "hint": "<جهتِ فیکس>"}\n'
    "قواعد: فقط باگِ واقعی (منطق/خطای نهفته/قراردادِ شکسته) — نه سلیقه، نه بازآرایی، "
    "نه performance ِ حدسی. اگر مطمئن نیستی: CLEAN. هیچ متنِ دیگری ننویس."
)


def review_and_queue(*, ask_fn=None, targets=None) -> dict:
    """روزی یک فایل: مرور با مغزِ گران → صفِ نقص. idempotent per-day."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    today = time.strftime("%Y-%m-%d")
    st = {}
    try:
        if REVIEW_STATE.exists():
            st = json.loads(REVIEW_STATE.read_text("utf-8")) or {}
    except (OSError, ValueError):
        st = {}
    if st.get("date") == today:
        return {"ok": False, "reason": "already-reviewed-today",
                "target": st.get("target")}
    files = targets if targets is not None else review_targets()
    if not files:
        return {"ok": False, "reason": "no-targets"}
    idx = int(st.get("idx", -1)) + 1
    target = files[idx % len(files)]
    # گاردِ سهمِ self_patch **قبل از** سوزاندنِ روز: اگر سهمِ امروز تمام شده،
    # روز نباید «مرورشده» ثبت شود — تلاشِ واقعی اصلاً نیفتاده که سوزاندنش
    # توجیه داشته باشد (برخلافِ شکستِ مغز که بعد از تلاشِ واقعی می‌آید).
    allow, why = _self_patch_may_spend()
    if not allow:
        return {"ok": False, "reason": "self-patch-quota", "quota": why, "target": target}
    # روز را **قبل از** تماس بسوزان — مغزِ خراب نباید هر تیک مرورِ گران بسوزاند.
    # fail-CLOSED: اگر سوزاندن روی دیسک ننشیند، تماسِ گران هم نباید انجام شود؛
    # وگرنه دیسکِ پر/فقط‌خواندنی یعنی یک مرورِ پولی در **هر تیک** (ممیزیِ ۰۷-۲۷).
    try:
        REVIEW_STATE.parent.mkdir(parents=True, exist_ok=True)
        REVIEW_STATE.write_text(json.dumps(
            {"date": today, "idx": idx % len(files), "target": target},
            ensure_ascii=False), "utf-8")
    except OSError as e:
        opslib.alert([f"self_patch: ثبتِ روزِ مرور شکست ({type(e).__name__}) — "
                      "مرورِ گران انجام نشد (fail-closed)"])
        return {"ok": False, "reason": "slot-persist-failed", "target": target}
    try:
        src = (_HERE.parent / target).read_text("utf-8")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"unreadable:{type(e).__name__}", "target": target}
    ans = (_review_ask(target, src, ask_fn=ask_fn) or "").strip()
    # سکوت ≠ «تمیز است». `_review_ask` روی هر استثنا/جوابِ not-ok رشتهٔ خالی می‌دهد؛
    # نسخهٔ قبلی همان را CLEAN می‌شمرد، یعنی یک مغزِ مرده هر روز یک فایل را «بازبینی‌شده
    # و سالم» اعلام می‌کرد و روزِ مرور را هم می‌سوزاند (ممیزیِ متخاصمِ ۰۷-۲۷).
    if not ans:
        # روز عمداً سوخته می‌ماند: پس‌دادنش یعنی مغزِ خراب هر تیک یک مرورِ گران
        # می‌سوزاند (گاردِ t_loop_review_burns_the_day_before_the_expensive_call).
        # ضررِ اصلی ثبتِ CLEANِ دروغ بود، نه سوختنِ اسلات — چرخشِ idx فردا فایلِ
        # بعدی را می‌گیرد و آلارم به مالک می‌گوید چه چیزی مرور **نشد**.
        opslib.alert([f"self_patch: مرورِ {target} جوابی نگرفت — «تمیز» ثبت نشد"])
        return {"ok": False, "reason": "brain-silent", "target": target}
    if ans.upper().startswith("CLEAN"):
        return {"ok": True, "target": target, "clean": True}
    try:
        d = json.loads(_strip_fences(ans).splitlines()[0])
        defect, hint = str(d["defect"])[:400], str(d.get("hint") or "")[:300]
    except Exception:  # noqa: BLE001 — جوابِ خارج از قرارداد = دور انداختن، نه حدس
        return {"ok": False, "reason": "bad-review-format", "target": target}
    did = _defect_id(target, defect)
    if any(r.get("id") == did for r in _queue_rows()):
        return {"ok": True, "target": target, "duplicate": True}
    _queue_append({"id": did, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "target": target, "defect": defect, "hint": hint, "status": "open"})
    return {"ok": True, "target": target, "queued": did}


def _review_ask(target: str, src: str, ask_fn=None) -> str:
    """مرور با tier=primary ِ پین‌شده (کارِ سنگین؛ محلی رویش طوطی‌وار جواب می‌دهد).
    ask_fn تزریق‌پذیر با امضای model_router.ask — مسیرِ تست هم از **همین** قراردادِ
    مرور رد می‌شود، نه از قراردادِ پچ‌نویسی."""
    try:
        if ask_fn is None:
            import model_router
            ask_fn = model_router.ask
        _self_patch_count()   # قبل از تماس — همان اصلِ attempt-counted
        r = ask_fn("deep", f"FILE: {target}\n--- BEGIN FILE ---\n{src}\n--- END FILE ---",
                   system=_REVIEW_SYSTEM, max_tokens=REVIEW_MAX_TOKENS,
                   tier="primary")
        return str(r.get("text") or "") if isinstance(r, dict) and r.get("ok") else ""
    except Exception:  # noqa: BLE001
        return ""


def drive(*, channel=None, ask_fn=None, shadow_fn=None) -> dict:
    """قدیمی‌ترین ردیفِ باز از صف → propose() → کارت. ردیف قبل از تماس قفل می‌شود."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    # صف append-only است — وضعِ مؤثرِ هر id آخرین ردیفش است. خواندنِ خام، ردیفِ
    # done/taken را دوباره «باز» می‌شمرد و همان نقص هر روز دوباره پچ می‌خورد.
    open_rows = [r for r in _queue_effective().values() if r.get("status") == "open"]
    if not open_rows:
        return {"ok": False, "reason": "queue-empty"}
    row = min(open_rows, key=lambda r: str(r.get("ts", "")))
    _queue_append({**row, "status": "taken",
                   "taken_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    res = propose(target_rel=row["target"], defect=row["defect"],
                  fix_hint=row.get("hint", ""), ask_fn=ask_fn, shadow_fn=shadow_fn)
    # شکستِ **گذرا** نباید نقص را برای همیشه بسوزاند. ممیزیِ ۰۷-۲۷: هر non-ok
    # ردیف را نهایی می‌کرد، از جمله «سقفِ روزانه پر شد» و «مغز جواب نداد» — که هیچ‌کدام
    # حرفی دربارهٔ خودِ نقص نمی‌زنند. فقط قضاوتِ واقعی (سوییت قرمز شد، یا مدل گفت
    # تغییری لازم نیست) نهایی است. `attempts` جلوی حلقهٔ بی‌پایان را می‌گیرد.
    _TRANSIENT = {"daily-cap", "brain-no-answer", "unreadable", "shadow-error",
                  "worktree-add-failed", "code_autonomy-unavailable", "self-patch-quota"}
    reason = str(res.get("reason") or "")
    transient = any(reason.startswith(t) for t in _TRANSIENT)
    attempts = int(row.get("attempts", 0)) + 1
    if res.get("ok"):
        status = "done"
    elif transient and attempts < 3:
        status = "open"          # دوباره برداشته می‌شود، بدونِ مرورِ گرانِ تازه
    else:
        status = "failed"
    _queue_append({**row, "status": status, "attempts": attempts,
                   "result_reason": res.get("reason"), "green": res.get("green"),
                   "new_fails": res.get("new_fails"),
                   "done_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    if status == "failed" and not res.get("ok"):
        # شکستِ نهایی باید **دیده** شود؛ وگرنه یافتهٔ یک مرورِ پولی بی‌صدا گم می‌شود.
        try:
            opslib.alert([f"self_patch: نقص {row.get('id')} روی "
                          f"{row.get('target')} بسته شد بدونِ پچ — "
                          f"{reason or 'unknown'}"
                          + (f" · شکستِ تازه: {', '.join(res.get('new_fails') or [])}"
                             if res.get("new_fails") else "")])
        except Exception:  # noqa: BLE001
            pass
    if res.get("ok") and channel is not None and hasattr(channel, "send_text"):
        try:
            channel.send_text(card_text(res), stream="c6")
        except Exception:  # noqa: BLE001 — کارت هرگز حلقه را نمی‌کشد
            pass
    _offer_patch_to_owner(res)
    return res


def _authorization_shadow(res: dict) -> dict:
    """سایه: پچ را به قراردادِ typed ترجمه کن و اثرانگشتِ **دقیقِ اکشن** را ثبت کن.

    ۲۰۲۶-۰۷-۲۸ — قدمِ ۴ از فهرستِ «vertical slice». چرا `self_patch` اولین
    مشتری شد: این تنها مسیری است که به نوشتنِ کد روی درختِ **زنده** می‌رسد، پس
    بیشترین سود را از گاردِ TOCTOU می‌برد؛ و کارتِ تأییدِ خودش را از قبل دارد،
    پس اینجا فقط یک لایه اضافه می‌شود نه یک جریانِ تازه.

    مسئله‌ای که این لایه برای حلش هست: امروز تأیید به **پیشنهاد** گره می‌خورد،
    نه به **محتوای دقیقِ پچ**. یعنی بینِ «آره»ی مالک و لحظهٔ اعمال، اگر متنِ
    پچ عوض شود، همان تأیید هنوز معتبر شمرده می‌شود. `action_sha256` این شکاف
    را می‌بندد: مجوز به هشِ دقیقِ (هدف + عملیات + محتوا) بسته می‌شود.

    ⚠️ این تابع **هیچ‌چیز را گیت نمی‌کند** — فقط می‌سنجد و می‌نویسد. تبدیلش به
    گاردِ واقعی قدمِ بعد و تصمیمِ مالک است. سایه‌بودن عمدی است: قبل از اینکه
    یک گارد بتواند چیزی را رد کند، باید ثابت شود روی ترافیکِ واقعی درست
    قضاوت می‌کند. (درسِ همین روز: گاردِ درست روی مکانیزمِ غلط.)
    """
    import os as _os
    if str(_os.environ.get("OCTOPUS_WIRE_AUTHZ_SHADOW", "")).strip().lower() \
            not in ("1", "true", "yes", "on"):
        return {"ok": False, "reason": "flag-off"}
    try:
        import hashlib as _hl
        import sys as _s
        from pathlib import Path as _P
        _r = str(_P(__file__).resolve().parent)
        if _r not in _s.path:
            _s.path.insert(0, _r)
        import control_contracts as _cc
        import opslib as _ops

        content = str((res or {}).get("content") or "")
        target = str((res or {}).get("target") or "")
        csha = _hl.sha256(content.encode("utf-8")).hexdigest()
        spec = _cc.ActionSpec(
            action_type="code_patch", target=target, operation="apply_patch",
            args={"content_sha256": csha, "bytes": len(content)},
            reversible=True, sandbox_required=True)
        prop = _cc.ActionProposal.create(
            mission_id=str(res.get("id") or "self-patch"),
            task_id=str(res.get("id") or "self-patch"),
            trace_id=str(res.get("id") or "self-patch"),
            tenant_id="personal", project_id="octopus-core",
            agent_id="self_patch", title="self-patch",
            summary=str(res.get("defect") or "")[:200],
            risk="high", confidence=1.0 if res.get("shadow_green") else 0.0,
            action=spec, expected_impact="one file on the live tree",
            rollback_plan="git revert of the applied patch")
        verdict = _cc.authorization(prop, None)
        rec = {"ts": _ops.now_iso(), "target": target,
               "action_sha256": prop.action_sha256,
               "content_sha256": csha,
               "allow": verdict.get("allow"), "reason": verdict.get("reason")}
        _ops.append_jsonl(_ops.STATE_DIR / "authz-shadow.jsonl", rec)
        return {"ok": True, **rec}
    except Exception as e:  # noqa: BLE001 — سایه هرگز مسیرِ پیشنهاد را نمی‌کشد
        return {"ok": False, "reason": type(e).__name__}


def _offer_patch_to_owner(res: dict) -> dict:
    """پچِ سبزِ سایه → کارتِ **دکمه‌دار** در صفِ تصمیم. پشتِ فلگ، پیش‌فرض خاموش.

    چرا این حلقه تا امروز باز بود: `card_text()` فقط رشته می‌سازد و `send_text`
    هیچ `reply_markup` نمی‌گیرد. پس مالک می‌دید «باگی در خودم یافتم و پچش سبز
    است» و **هیچ راهی برای جواب نداشت**. کارتِ دکمه‌دارِ کامل از قبل در
    `code_autonomy.propose_to_owner` نوشته شده بود و هیچ‌کس صدایش نمی‌زد.

    چرا فلگ‌دار و خاموش: این تنها مسیری است که به نوشتنِ **کد روی درختِ زنده**
    ختم می‌شود. هشت گیت پایین‌دستش هست (فعال‌سازی، قلب، refractory، سایه، deny،
    dedup، سقفِ کهنگیِ ۴۸ ساعته، و از ۲۰۲۶-۰۸-۰۴ arm_gate) — ولی مسلح‌کردنِ
    ورودیِ آن زنجیره تصمیمِ استقرار است، نه تصمیمِ من.

    گیتِ هشتم (DR-001، ۲۰۲۶-۰۸-۰۴): arm_gate.guard('code_autonomy') — defense-
    in-depth اضافی، فقط سخت‌تر می‌کند، هرگز شل‌تر (arm_gate.py:12-16). پیش‌فرض
    بدونِ اثر (هر دو knobِ arm_gate خاموش‌اند)؛ وقتی مالک
    OCTOPUS_ARM_SENSITIVE_DEFAULT=1 کرد (که already روشن است)، این نقطه یک
    arm-token تازهٔ دوکلیدی برای code_autonomy می‌خواهد وگرنه همین‌جا، قبل از
    authorization_shadow و پیشنهاد به مالک، متوقف می‌شود."""
    import os as _os
    if str(_os.environ.get("OCTOPUS_WIRE_PATCH_CARD", "")).strip().lower()             not in ("1", "true", "yes", "on"):
        return {"ok": False, "reason": "flag-off"}
    if not (res or {}).get("shadow_green") or not (res or {}).get("content"):
        return {"ok": False, "reason": "not-offerable"}
    # گیتِ هشتم — بالا را ببین. arm_gate هرگز نمی‌تواند چیزی را که هفت گیتِ
    # بالا رد کرده‌اند اجازه بدهد؛ فقط می‌تواند یک عبورِ موفق را رد کند.
    _arm_ok, _arm_why = arm_gate.guard("code_autonomy")
    if not _arm_ok:
        # ۲۰۲۶-۰۸-۰۴ — drive() قبلِ اینجا یک کارتِ متنِ‌سادهٔ قدیمی می‌فرستد
        # (channel.send_text(card_text(res)))، ولی آن کارت دکمه ندارد و
        # نمی‌گوید چرا رد شد. بدونِ این آلارم، مالک فقط «چیزی خودکار اعمال
        # نمی‌شود» می‌بیند و نمی‌فهمد یک arm-token لازم است. opslib.alert خودش
        # dedupِ ۶ساعته دارد، پس تکرار spam نمی‌شود.
        try:
            opslib.alert([
                f"self_patch: پچِ سبز برای «{(res or {}).get('target')}» آماده بود "
                f"ولی arm_gate رد کرد ({_arm_why}) — یک arm-token تازهٔ دوکلیدی "
                f"برای code_autonomy لازم است."])
        except Exception:  # noqa: BLE001 — آلارم هرگز پیشنهاد را نمی‌کشد
            pass
        return {"ok": False, "reason": f"arm-gate-denied:{_arm_why}"}
    # سایهٔ مجوز (قدمِ ۴): می‌سنجد و ثبت می‌کند، هیچ‌چیز را گیت نمی‌کند.
    # عمداً **بعد از** گاردهای موجود است تا ترتیبِ تصمیم‌ها عوض نشود.
    _authorization_shadow(res)
    try:
        import sys as _s
        from pathlib import Path as _P
        _c = str(_P(__file__).resolve().parent / "cortex")
        if _c not in _s.path:
            _s.path.insert(0, _c)
        import code_autonomy as _ca
        return _ca.propose_to_owner(res)
    except Exception as e:  # noqa: BLE001 — پیشنهاد هرگز حلقه را نمی‌کشد
        return {"ok": False, "reason": type(e).__name__}


def _queue_effective() -> dict:
    """آخرین وضعِ هر id (صف append-only است — آخرین ردیف برنده).

    یک ردیفِ `taken` ِ کهنه دوباره `open` دیده می‌شود. بدونِ این، thread ِ daemon که
    وسطِ کار با ری‌استارتِ ارگانیسم می‌میرد (بینِ appendِ «taken» و appendِ نتیجه)
    آن نقص را برای همیشه دفن می‌کرد: هیچ‌کس `taken` را نمی‌خواند، و
    `review_and_queue` هم به‌خاطرِ dedupِ id هرگز دوباره صفش نمی‌کرد."""
    eff = {}
    for r in _queue_rows():
        eff[r.get("id")] = r
    now = time.time()
    for rid, r in eff.items():
        if r.get("status") != "taken":
            continue
        try:
            t = time.mktime(time.strptime(str(r.get("taken_ts") or ""),
                                          "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
        except (TypeError, ValueError):
            t = 0.0
        if not t or (now - t) > TAKEN_STALE_S:
            eff[rid] = {**r, "status": "open", "reopened_from": "taken-stale"}
    return eff


def beat_async(channel=None) -> dict:
    """صدازدنی از تیکِ ارگانیسم: اگر کاری هست، در threadِ جدا انجام بده.
    غیرمسدودکننده؛ همیشه فوری برمی‌گردد. یکی بیشتر هم‌زمان نمی‌دود."""
    if not enabled():
        return {"spawned": False, "reason": "flag-off"}
    has_open = any(r.get("status") == "open" for r in _queue_effective().values())
    today = time.strftime("%Y-%m-%d")
    reviewed = False
    try:
        reviewed = (json.loads(REVIEW_STATE.read_text("utf-8")) or {}).get("date") == today
    except (OSError, ValueError):
        reviewed = False
    if reviewed and not has_open:
        return {"spawned": False, "reason": "nothing-to-do"}
    if not _BEAT_LOCK.acquire(blocking=False):
        return {"spawned": False, "reason": "busy"}

    def _work():
        try:
            if not reviewed:
                review_and_queue()
            if any(r.get("status") == "open" for r in _queue_effective().values()):
                drive(channel=channel)
        except Exception as e:  # noqa: BLE001 — thread هرگز استثنای بی‌صدا ندهد
            try:
                opslib.alert([f"self_patch beat error: {type(e).__name__}: {e}"])
            except Exception:  # noqa: BLE001
                pass
        finally:
            _BEAT_LOCK.release()

    t = __import__("threading").Thread(target=_work, name="self-patch-beat", daemon=True)
    t.start()
    return {"spawned": True, "review_pending": not reviewed, "queue_open": has_open}


if __name__ == "__main__":  # pragma: no cover — پیش‌نمایشِ بی‌ارسال
    print(f"flag {FLAG} = {'on' if enabled() else 'off'} · "
          f"today {_today_count()}/{DAILY_CAP}")
    d = _dir()
    if d.exists():
        for p in sorted(d.glob("*.json")):
            r = json.loads(p.read_text("utf-8"))
            print(f"  {r.get('id')}  {r.get('target'):40s} green={r.get('green')}")
    print(f"queue: {sum(1 for r in _queue_effective().values() if r.get('status') == 'open')} باز "
          f"از {len(_queue_effective())}")
