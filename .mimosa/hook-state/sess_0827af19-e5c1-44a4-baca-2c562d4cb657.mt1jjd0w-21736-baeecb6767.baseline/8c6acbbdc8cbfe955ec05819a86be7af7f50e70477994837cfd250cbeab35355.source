#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arm_renewal.py — تجدیدِ خودکارِ اَرم‌توکن برای دو ظرفیتِ دوکلیدیِ خودمختاری
(code_autonomy، self_improve_auto)، پشتِ فلگِ خودش، additive به arm_gate.py.

مسئله (رأیِ مالکِ ۲۰۲۶-۰۸-۰۵، «همیشه، بسته به قلب، هر دو قلب هم‌گام»): arm_gate.py
عمداً tokenهای *فانی* طراحی کرده (TTL=۲۴h، arm_gate.py:۱۲-۲۶ — «ambient capability
نه»)، پس بدونِ یک نوهٔ زنده، ۲۴ ساعت بعد از هر arm-ِ دستیِ مالک، code_autonomy و
self_improve_auto **بی‌صدا** می‌میرند — نه چون مالک خواسته، فقط چون کسی توکن را
دوباره نساخته. این دقیقاً طعمِ همان الگویی است که در حافظه چند بار افتاده: قابلیتِ
تست‌شده‌ای که صداکننده/نگه‌دارنده ندارد. این ماژول آن نگه‌دارنده است — نه یک راهِ دور زدنِ
گیت، فقط یک دست ثابت که وقتی مالک از قبل «بله» گفته (فلگِ ACTIVATION هست)، آن
«بله» را هر چند دقیقه یک‌بار در قالبِ توکنِ تازه دوباره امضا می‌کند.

قرارداد (هرگز شل‌تر نمی‌شود، فقط سخت‌تر):
  ۱) تنها مسیرِ ورودی: arm_gate.DANGEROUS — این ماژول تعریفِ خودش از «کدام فلگ»
     یا «کدام capability دوکلیدی است» نمی‌سازد؛ همیشه از arm_gate می‌خواند تا
     هرگز از آن واگرا نشود.
  ۲) هرگز بدونِ ACTIVATION-*.flag یا در حضورِ کیل‌مارکرِ STOP-* چیزی نمی‌نویسد —
     حتی یک توکنِ تازه. این خطِ قرمز است؛ تستِ جهش همین خط را قفل می‌کند
     (پایینِ test_arm_renewal.py، «mutation: renders active() blind»).
  ۳) پشتِ فلگِ خودش (OCTOPUS_WIRE_ARM_RENEWAL) — نبودش یعنی این فایل هیچ اثری
     ندارد، حتی وقتی organism.py آن را در تیک صدا می‌زند.
  ۴) کیل‌سوییچِ لحظه‌ایِ code_autonomy (فایلِ STOP-CODE-AUTONOMY، از قبل در
     cortex/code_autonomy.py) بلافاصله این حلقه را هم می‌خواباند — هیچ سیمِ
     تازه‌ای لازم نیست چون منطقِ فعال‌بودن یکی است (بخشِ «مشتقِ نامِ کیل‌مارکر»
     پایین). برای self_improve_auto که در تولید کیل‌مارکرِ اختصاصی نداشت
     (فقط ACT_AUTO.exists())، همان قاعدهٔ عمومی یک STOP-SELF-IMPROVE-AUTO
     اضافه می‌کند — گیتِ کاملاً additive، نه جایگزینِ ACTIVATION-SELF-IMPROVE-AUTO.flag.

چرا code_autonomy.active() مستقیم import نشد: آن تابع مسیرهای واقعی
(opslib.OPS/opslib.STATE_DIR) را درونِ خودش hardcode می‌کند و پارامتری برای
تزریقِ ops_dir ندارد — یعنی تستِ ایزوله (بدونِ لمسِ درختِ زنده) رویش ممکن نیست.
این‌جا دقیقاً همان منطقِ دوخطی (ACTIVATION.exists() and not STOP.exists()) با
پارامترِ تزریق‌پذیرِ ops_dir بازتولید شده — الگویی که خودِ arm_gate.arm_open هم
برای همین دلیل استفاده می‌کند (ops_dir/arm_dir تزریقی، آدرسِ واقعی فقط پیش‌فرض).

خودِ فایلِ توکن دقیقاً همان قراردادِ arm_gate._read_token/_token_fresh/_hmac_ok
را برآورده می‌کند: {"capability","armed_at","key",optional"hmac"}. کلید با
secrets.token_hex (نه رشتهٔ ضعیف/قابلِ‌حدس)؛ HMAC با همان ساختِ دقیقِ
arm_gate._hmac_ok (`cap|armed_at|key`) تا verify بدونِ تغییر جمع بخورد.

$0 · stdlib‑only · fail‑soft: هر خطا در یک ظرفیت تمدیدِ ظرفیتِ دیگر را نمی‌کشد؛
خطای کلی هرگز تیکِ ارگانیسم را نمی‌کشد (سیم‌کشی در organism.py با try/except
جدا شده است، هم‌الگو با self_patch.beat_async / deep_think.run).
تست: `_ops/tests/test_arm_renewal.py`.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent  # _ops
for _p in (str(_HERE / "budget"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib     # noqa: E402
import arm_gate   # noqa: E402

FLAG = "OCTOPUS_WIRE_ARM_RENEWAL"

# فقط این دو — بخشِ ۳ (نامهٔ کار): «replicate عمداً سیم‌کشی نشد چون تابعِ spawn
# واقعی وجود ندارد»؛ cortex_paid/governor_llm دوکلیدی نیستند و در محدودهٔ Lane 1
# مالک صراحتاً «دو ظرفیتِ دوکلیدی» را نام برده، نه هر پنج DANGEROUS.
RENEWAL_CAPS = ("code_autonomy", "self_improve_auto")

# کادنسِ چک: هر ~۱۰ دقیقه، نه هر تیک — کمینهٔ تیکِ ارگانیسم TICK_SECONDS=300 است
# (OCTOPUS-flags.cmd)، پس این تقریباً یک‌بار در میانِ تیک است، نه هر تیک.
CHECK_COOLDOWN_S = 600.0

# اگر کمتر از این مانده به انقضا (TTL پیش‌فرض ۲۴h)، تمدید کن — پیش از آنکه
# arm_gate واقعاً رد کند، نه بعدش (بدونِ این حاشیه، یک چرخهٔ کوتاهِ رد ممکن بود).
RENEW_BEFORE_EXPIRY_S = 2 * 3600.0

# state/arm/renewal-log.jsonl — append-only، رسیدِ «کِی و چرا» برای مالک.
RENEWAL_LOG_NAME = "renewal-log.jsonl"

# کوکیِ کولداونِ درون‌پروسه‌ای؛ فقط برای پرهیز از I/O روی هر تیک — با ری‌استارتِ
# پروسه صفر می‌شود (بی‌خطر: بدترین حالت یک چکِ اضافی بلافاصله بعدِ بوت).
_last_check_ts = 0.0


def enabled() -> bool:
    """قفلِ سیم‌کشی — نبودش یعنی این ماژول در organism.py هم که صدا شود بی‌اثر است."""
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _stop_marker_name(activation_flag: str) -> str:
    """مشتقِ نامِ کیل‌مارکر از نامِ فلگِ ACTIVATION — قاعدهٔ عمومی، نه حدس:
    پیشوند «ACTIVATION-» و پسوند «.flag» حذف، «STOP-» اضافه می‌شود.
    برای code_autonomy این دقیقاً با ثابتِ دستیِ خودِ ماژول یکی درمی‌آید:
    ACTIVATION-CODE-AUTONOMY.flag -> STOP-CODE-AUTONOMY (code_autonomy.py:533)."""
    name = activation_flag
    if name.startswith("ACTIVATION-"):
        name = name[len("ACTIVATION-"):]
    if name.endswith(".flag"):
        name = name[: -len(".flag")]
    return f"STOP-{name}"


def capability_active(capability: str, *, ops_dir: Path) -> bool:
    """آیا مالک از قبل این ظرفیت را روشن کرده و نخوابانده؟ همان دو-شرطیِ
    code_autonomy.active() (ACTIVATION موجود و کیل‌مارکر غایب)، فقط با ops_dir
    تزریق‌پذیر تا تست هرگز مسیرِ زنده را لمس نکند. fail-closed: هر OSError یعنی
    «فعال نیست» — یک ظرفیتِ نامعلوم هرگز تمدید نمی‌شود."""
    if capability not in arm_gate.DANGEROUS:
        return False
    flag_name, _two_key = arm_gate.DANGEROUS[capability]
    try:
        activation = Path(ops_dir) / flag_name
        stop = Path(ops_dir) / _stop_marker_name(flag_name)
        return activation.exists() and not stop.exists()
    except OSError:
        return False


def _renewal_reason(token_path: Path, *, now: float, ttl_s: int,
                     renew_before_s: float) -> "str | None":
    """None = تازه است، کاری لازم نیست. وگرنه یک دلیلِ کوتاه (برای لاگ هم مصرف می‌شود)."""
    if not token_path.exists():
        return "missing"
    try:
        tok = json.loads(token_path.read_text("utf-8"))
    except Exception:  # noqa: BLE001 — فایلِ خراب/نیمه‌نوشته = تمدید کن
        return "unreadable"
    if not isinstance(tok, dict):
        return "malformed"
    try:
        armed_at = float(tok.get("armed_at"))
    except Exception:  # noqa: BLE001
        return "malformed-armed_at"
    age = now - armed_at
    if age < 0:
        return "future-timestamp"  # ساعت‌ناهمسو یا جعل؛ امن‌ترین کار یک توکنِ تازهٔ سالم است
    if age >= (ttl_s - renew_before_s):
        return "near-expiry"
    return None


def _mint_token(capability: str, which: str, arm_dir: Path, *, now: float,
                 secret: "str | None") -> dict:
    """توکنِ تازه می‌سازد و اتمیک می‌نویسد (opslib.LockedJson — همان نوشتنِ
    fsync+retryِ ایمن‌به‌ویندوز که بقیهٔ state ارگانیسم استفاده می‌کند).
    کلید: secrets.token_hex (CSPRNG، نه uuid4/random). HMAC وقتی secret هست،
    دقیقاً با ساختِ arm_gate._hmac_ok — تغییرِ این رشته یعنی verify شکست بخورد."""
    key = secrets.token_hex(32)
    tok: dict = {"capability": capability, "armed_at": now, "key": key}
    if secret:
        body = f"{capability}|{now}|{key}".encode("utf-8")
        tok["hmac"] = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    arm_dir.mkdir(parents=True, exist_ok=True)
    path = arm_dir / f"{capability}.{which}.json"
    with opslib.LockedJson(path) as lj:
        lj.write(tok)
    return tok


def beat(*, ops_dir=None, arm_dir=None, now: "float | None" = None,
          ttl_s: int = arm_gate.DEFAULT_TTL_S,
          renew_before_s: float = RENEW_BEFORE_EXPIRY_S,
          cooldown_s: float = CHECK_COOLDOWN_S,
          secret: "str | None" = None, log_path: "Path | None" = None) -> dict:
    """صدازدنی از تیکِ ارگانیسم. غیرمسدودکننده (فقط I/O سبکِ محلی، بدونِ شبکه/LLM
    — برخلافِ self_patch.beat_async نیازی به threadِ جدا نیست). fail-soft: خطای
    یک ظرفیت باعثِ توقفِ کل نمی‌شود؛ خطای کلی به تماس‌گیرنده (organism.py) که
    خودش try/except دارد بازمی‌گردد نه اینکه بی‌صدا بلعیده شود این‌جا — تا در
    حالتِ خرابیِ ساختاری (نه یک ظرفیتِ تکی) مالک alert ببیند."""
    global _last_check_ts
    if not enabled():
        return {"ran": False, "reason": "flag-off"}

    now = time.time() if now is None else now
    if (now - _last_check_ts) < cooldown_s:
        return {"ran": False, "reason": "cooldown"}
    _last_check_ts = now

    ops_dir = Path(ops_dir) if ops_dir is not None else Path(opslib.OPS)
    arm_dir = Path(arm_dir) if arm_dir is not None else (Path(opslib.STATE_DIR) / "arm")
    if secret is None:
        secret = os.environ.get("OCTOPUS_ARM_SECRET") or None
    log_path = Path(log_path) if log_path is not None else (arm_dir / RENEWAL_LOG_NAME)

    minted: list[dict] = []
    skipped: list[dict] = []
    for cap in RENEWAL_CAPS:
        try:
            if cap not in arm_gate.DANGEROUS:
                skipped.append({"capability": cap, "reason": "unknown-capability"})
                continue
            _flag_name, two_key = arm_gate.DANGEROUS[cap]
            # ── خطِ قرمز (بخشِ ۱-ج، تستِ جهش قفلش می‌کند) ──────────────────────
            if not capability_active(cap, ops_dir=ops_dir):
                skipped.append({"capability": cap, "reason": "not-active"})
                continue
            whichs = ("arm", "arm2") if two_key else ("arm",)
            for which in whichs:
                token_path = arm_dir / f"{cap}.{which}.json"
                reason = _renewal_reason(token_path, now=now, ttl_s=ttl_s,
                                          renew_before_s=renew_before_s)
                if reason is None:
                    continue
                _mint_token(cap, which, arm_dir, now=now, secret=secret)
                rec = {"ts": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(
                           timespec="seconds"),
                       "capability": cap, "which": which, "reason": reason,
                       "armed_at": now}
                try:
                    opslib.append_jsonl(log_path, rec)
                except Exception:  # noqa: BLE001 — لاگِ ممیزی هرگز خودِ arm را نمی‌کشد
                    pass
                minted.append({"capability": cap, "which": which, "reason": reason})
        except Exception as e:  # noqa: BLE001 — یک ظرفیتِ خراب بقیه را نمی‌کشد
            skipped.append({"capability": cap, "reason": f"error:{type(e).__name__}"})
    return {"ran": True, "minted": minted, "skipped": skipped}


if __name__ == "__main__":  # pragma: no cover — پیش‌نمایشِ بی‌اثر (فلگ را خودش می‌خواند)
    print(json.dumps({"flag": FLAG, "enabled": enabled(), "caps": RENEWAL_CAPS},
                      ensure_ascii=False, indent=2))
