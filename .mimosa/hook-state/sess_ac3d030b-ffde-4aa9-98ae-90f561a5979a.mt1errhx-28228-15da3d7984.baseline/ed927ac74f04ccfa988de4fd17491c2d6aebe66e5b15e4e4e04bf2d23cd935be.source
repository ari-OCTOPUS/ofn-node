#!/usr/bin/env python3
"""owner_gate — کارتِ رأیِ مالک، و مجوزی که فقط به **همین** عمل می‌چسبد.

درسِ ثبت‌شدهٔ ارگانیسم: «تأییدِ کهنه رضایتِ کهنه است» و «رأی روی تصمیم کلید
می‌خورد نه روی پاسخ». این‌جا هر دو ساختاری شده‌اند، به‌علاوهٔ سه بندِ دیگر که
بدونشان یک approval معتبر به یک کلیدِ عمومی تبدیل می‌شود:

  bind    مجوز به `action_id` **و** `payload_hash` **و** `scope` گره می‌خورد.
          تغییرِ مقصد، محدوده، هزینه یا فلگِ اثرِ بیرونی ⇒ hash نو ⇒ مجوزِ باطل.
  expiry  هر مجوز `expires_at` دارد. منقضی = نامعتبر، بدونِ استثنا.
  replay  هر مجوز `nonce` دارد و **یک‌بارمصرف** است؛ مصرف‌شده دوباره پذیرفته
          نمی‌شود حتی اگر هنوز منقضی نشده باشد.

و صریح: **متنِ مالک مجوز نیست.** «آره بزن» در چت یک رشته است. تنها چیزی که
مجوز است، رکوردی است که این ماژول ساخته و امضا کرده باشد.

⚠️ امضا در این دور **HMAC محلی** است، نه رمزنگاریِ قوی: کلید از env می‌آید و
اگر نباشد، ماژول fail-closed می‌شود (هیچ مجوزی صادر و هیچ مجوزی تأیید نمی‌شود).
هدفِ امضا این‌جا جلوگیری از **جعلِ درون‌سیستمی** است — که یک ماژولِ دیگر یا یک
artifact ِ آلوده نتواند فایلِ approval بسازد.

$0 · stdlib · صفر I/O (ذخیره‌سازی کارِ صداکننده است) · fail-closed.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import uuid

_HEX32 = re.compile(r"[0-9a-f]{32}")

from contracts import payload_hash  # noqa: E402

CARD_SCHEMA = "owner-action-card.v1"
APPROVAL_SCHEMA = "owner-approval.v1"

KEY_ENV = "OCTOPUS_ACTION_BRIDGE_HMAC"
DEFAULT_TTL_S = 24 * 3600.0          # «تأییدِ کهنه رضایتِ کهنه است»


def _key() -> "bytes | None":
    k = str(os.environ.get(KEY_ENV, "") or "").strip()
    return k.encode("utf-8") if len(k) >= 16 else None


def _sign(fields: dict) -> "str | None":
    k = _key()
    if k is None:
        return None
    blob = "|".join(f"{n}={fields.get(n)}" for n in sorted(fields))
    return hmac.new(k, blob.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def make_card(req: dict, plan: dict, *, now: float) -> dict:
    """کارتِ رأی — چیزی که مالک می‌بیند. **خودش مجوز نیست.**

    کارت عمداً `payload_hash` را حمل می‌کند تا اگر بینِ ساختِ کارت و تپِ مالک
    درخواست عوض شود، تأیید به عملِ عوض‌شده نچسبد."""
    return {
        "schema": CARD_SCHEMA,
        "action_id": str(req.get("action_id")),
        "payload_hash": payload_hash(req),
        "classification": plan.get("classification"),
        "intent": str(req.get("intent") or "")[:400],
        "target": str(req.get("target") or "")[:300],
        "expected_effect": str(req.get("expected_effect") or "")[:300],
        "external_effect": bool(req.get("external_effect")),
        "estimated_cost": req.get("estimated_cost"),
        "allowed_scope": list(req.get("allowed_scope") or []),
        "falsifier": str(req.get("falsifier") or "")[:300],
        "rollback": str(req.get("rollback") or "")[:300],
        "reason": plan.get("reason"),
        "created_at": float(now),
        # آنچه کارت **نیست** — تا هیچ خواننده‌ای اشتباه نکند
        "is_authorization": False,
        "note": "این کارت درخواست است. مجوز فقط رکوردِ owner-approval.v1 است.",
    }


def grant(req: dict, *, now: float, ttl_s: float = DEFAULT_TTL_S,
          approver: str = "owner") -> dict:
    """صدورِ مجوز. بدونِ کلید ⇒ هیچ مجوزی صادر نمی‌شود (fail-closed)."""
    ph = payload_hash(req)
    aid = str(req.get("action_id"))
    nonce = uuid.uuid4().hex[:16]
    expires = float(now) + max(1.0, float(ttl_s))
    fields = {"action_id": aid, "payload_hash": ph, "nonce": nonce,
              "expires_at": expires,
              "scope": ",".join(sorted(str(s) for s in (req.get("allowed_scope") or [])))}
    sig = _sign(fields)
    if sig is None:
        return {"ok": False, "reason": "no-signing-key"}
    return {"ok": True, "approval": {
        "schema": APPROVAL_SCHEMA, "action_id": aid, "payload_hash": ph,
        "nonce": nonce, "expires_at": expires, "granted_at": float(now),
        "approver": str(approver)[:60],
        "scope": fields["scope"], "sig": sig}}


def verify(approval, req: dict, *, now: float, used_nonces=None) -> dict:
    """{ok, reason}. هر ابهام = رد. ترتیبِ بندها عمدی است: ارزان‌ترین اول.

    `used_nonces` مجموعهٔ nonceهای مصرف‌شده است (صداکننده نگه می‌دارد و پایدار
    می‌کند). نبودش یعنی «حافظهٔ replay ندارم» ⇒ رد، نه عبور — وگرنه فراموشیِ
    صداکننده به درِ باز تبدیل می‌شود."""
    if not isinstance(approval, dict):
        return {"ok": False, "reason": "no-approval"}
    if approval.get("schema") != APPROVAL_SCHEMA:
        return {"ok": False, "reason": "bad-schema"}
    if used_nonces is None:
        return {"ok": False, "reason": "no-replay-store"}
    if _key() is None:
        return {"ok": False, "reason": "no-signing-key"}

    aid = str(req.get("action_id"))
    if str(approval.get("action_id")) != aid:
        return {"ok": False, "reason": "action-id-mismatch"}

    ph = payload_hash(req)
    if str(approval.get("payload_hash")) != ph:
        # همان عمل نیست — چیزی در امضا عوض شده (مقصد/محدوده/هزینه/بیرونی)
        return {"ok": False, "reason": "payload-hash-mismatch"}

    scope_now = ",".join(sorted(str(s) for s in (req.get("allowed_scope") or [])))
    if str(approval.get("scope")) != scope_now:
        return {"ok": False, "reason": "scope-mismatch"}

    try:
        exp = float(approval.get("expires_at"))
    except (TypeError, ValueError):
        return {"ok": False, "reason": "bad-expiry"}
    if float(now) > exp:
        return {"ok": False, "reason": "expired"}

    nonce = str(approval.get("nonce") or "")
    if not nonce:
        return {"ok": False, "reason": "no-nonce"}
    if nonce in used_nonces:
        return {"ok": False, "reason": "replayed"}

    # ⚠️ شکلِ امضا **قبل** از مقایسه سنجیده می‌شود. `hmac.compare_digest` روی
    # رشتهٔ غیر-ASCII `TypeError` پرتاب می‌کند — یعنی یک مجوزِ جعلی با امضای
    # فارسی («بله-بزن») گیت را می‌ترکاند به‌جای اینکه ردش کند. fail-closed از
    # راهِ استثنا شکننده است: صداکنندهٔ بعدی ممکن است `except` بگذارد و بی‌صدا
    # عبور دهد. پس شکلِ نامعتبر = ردِ صریح، نه crash.
    sig = approval.get("sig")
    if not isinstance(sig, str) or not _HEX32.fullmatch(sig):
        return {"ok": False, "reason": "bad-signature"}
    expect = _sign({"action_id": aid, "payload_hash": ph, "nonce": nonce,
                    "expires_at": exp, "scope": scope_now})
    if expect is None or not hmac.compare_digest(sig, expect):
        return {"ok": False, "reason": "bad-signature"}
    return {"ok": True, "reason": "valid", "nonce": nonce}


def consume(approval: dict, used_nonces: set) -> None:
    """nonce را بسوزان. صداکننده باید این را **پایدار** کند، وگرنه replay بازمی‌گردد."""
    n = str((approval or {}).get("nonce") or "")
    if n:
        used_nonces.add(n)
