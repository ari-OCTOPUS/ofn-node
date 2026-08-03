#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pending_card_recovery.py — C7 Slice 1 (C7.1 repair): بازسازیِ کارت‌های approvalِ معلق بعد از restart.

قوسِ شکسته (audit A3/A4): `_pending` (کارت‌های مالی) و `_pending_rfc` (کارت‌های RFC) در RAM
بودند → restart همه‌شان را می‌کشت.

--- درسِ بازبینیِ C7.1 (چرا نسخهٔ اول false-green بود) ---
نسخهٔ اول تلاش کرد کارتِ مالی را از `chrono.gated_effect` بسازد، ولی:
  * chrono مبلغِ AUD را **ذخیره نمی‌کند** (نه ستون دارد، نه در binding). content_hash فقط
    sha256(payload_ref) است. مبلغ فقط در RAMِ کارت (زمانِ ساخت) بود → بعد از restart گم.
    → مبلغِ ساختگیِ AU$0.00 (blocker B6).
  * dedupِ durable، **بازسازیِ projection** را هم می‌بست (نه فقط ارسال) → بوتِ دوم صفر کارت
    (blocker B1 — همان فراموشیِ اصلی، این بار «سبز»).
  * ارسال بدونِ دکمه بود (send_text خام) (B2)؛ marker پیش از ارسال (B5)؛ HALT دلیوری را
    برای همیشه می‌سوزاند (B4)؛ توکنِ deterministic ولی ادعای «restart باطلش می‌کند» (B3).

--- طراحیِ درست (C7.1) ---
دو مفهومِ **جدا**:
  1. **projection reconstruction** — در هر بوتِ تازه از SoTِ durable بازسازی می‌شود؛ هرگز با
     dedupِ دلیوری بسته نمی‌شود.
  2. **delivery** — ماشینِ حالتِ durable: PENDING → LEASED → SENT. markerِ SENT فقط پس از
     موفقیتِ ارسال؛ ارسالِ شکست‌خورده retryable؛ زیرِ HALT صفر ارسال/mark؛ بوتِ همزمان با
     lease اتمیک (O_EXCL) دوبار نمی‌فرستد.

**SoTِ کارت** = storeِ durable (`state/pulse/pending-cards.json`) که پیش از ارسال نوشته
می‌شود و مبلغ واقعی + binding + owner + nonce + expiry + token hash را نگه می‌دارد.
**Bearer خام هرگز persist نمی‌شود.** callback پس از restart از HMAC(secret, nonce, binding,
owner, expiry) بازتولید و در هر کلیک با Chrono cross-check می‌شود.

**مدلِ توکن = stateless-derived + durable single-use:** دکمهٔ پیش از restart تا expiry معتبر
می‌ماند، اما authorization با approval_id هش‌شده و ماشین حالت پایدار تک‌مصرف است.
ضدِ replay در لایهٔ پول است: `chrono.release_effect` یک `approval_id` تک‌مصرفه می‌خواهد
(UPDATE با `NOT EXISTS(... WHERE approval_id=?)`) → همان توکن دوبار settle نمی‌کند. (مدلِ A —
generation-bound — را انتخاب نکردیم؛ پس هرگز ادعا نمی‌کنیم «restart توکن را باطل می‌کند».)

**مرزهای سختِ مأموریت (رعایت‌شده):** صفر تغییرِ semanticِ authorizationِ پول — آزادسازیِ
واقعی همچنان فقط از `EffectorGate.release_effect` (بایندِ دقیقِ C4). بازسازی فقط projection +
دلیوریِ کارت است. مبلغِ نامعلوم/tamper = fail-closed (هیچ کارتِ قابلِ‌کلیک). فقط
pending/releasable؛ **هرگز** terminal/EXECUTING/RECONCILE_REQUIRED.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_PROPOSAL_BUTTONS"     # همان دروازهٔ کارت‌ها (بدونِ فلگِ نو)
SECRET_ENV = "OCTOPUS_CB_SECRET"
TTL_S = 72 * 3600
_MONEY_SAFE_STATES = ("pending", "releasable")   # فقط این‌ها re-present می‌شوند (cross-check با chrono)
_RFC_SAFE_STATES = ("submitted",)                # doctor-side؛ decided/merged/denied → نه
_LEASE_TTL_S = 120                                # lease کهنه‌تر از این → قابلِ بازپس‌گیری


def _secret() -> "bytes | None":
    s = os.environ.get(SECRET_ENV, "")
    return s.encode("utf-8") if s and s.strip() else None


def _now() -> int:
    return int(time.time())


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "")) == "1"


def card_delivery_ready(owner=None) -> "tuple[bool, str]":
    """آیا لولهٔ کارتِ دکمه‌دار آمادهٔ ساخت است؟ (W7 · 2026-07-25)

    prepare_money_card/prepare_rfc_card بدونِ رازِ callback هیچ توکنی mint نمی‌کنند و
    None برمی‌گردانند — یعنی کارت اصلاً ساخته نمی‌شود، چه رسد به ارسال. این پروب فقط
    همان پیش‌شرط‌ها را می‌سنجد تا caller بتواند صادقانه بگوید «چرا نرفت».
    **هرگز مقدارِ راز را برنمی‌گرداند/چاپ/لاگ نمی‌کند** — فقط بود/نبود.
    خروجی: (ready, reason) با reason ∈ {ok, no-secret, no-owner}."""
    if _secret() is None:
        return (False, "no-secret")
    o = owner if owner is not None else os.environ.get("TELEGRAM_OWNER_CHAT_ID")
    if o in (None, ""):
        return (False, "no-owner")
    return (True, "ok")


# ── tamper-evident integrity tag (ضدِ card-swap/wrong-owner/amount-tamperِ storeِ durable) ──
# این تگ **توکنِ callback نیست**. Bearer از nonce+binding مشتق می‌شود و خام persist نمی‌شود.
# این تگ فقط صحتِ ردیفِ durable را می‌بندد به (effect|binding|amount|owner|exp): اگر مهاجم store را
# دستکاری کند (مبلغ/owner/target عوض شود) تگ نمی‌خواند → fail-closed، کارت بازسازی نمی‌شود.
def mint_money_token(*, effect_id, content_hash, action_kind, target_ref, amount, owner, exp):
    """(نامِ سازگاریِ عقب‌رو) تگِ صحتِ ردیفِ کارتِ مالی. HMACِ بایندِ کامل. secret نبود → None."""
    sec = _secret()
    if sec is None or owner in (None, ""):
        return None
    canon = f"mc2|{effect_id}|{content_hash}|{action_kind}|{target_ref}|{float(amount):.6f}|{owner}|{int(exp)}"
    sig = hmac.new(sec, canon.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"mc2.{hashlib.sha256(str(effect_id).encode()).hexdigest()[:12]}.{int(exp):010d}.{sig}"


def verify_money_token(token, *, effect_id, content_hash, action_kind, target_ref,
                       amount, owner, now=None) -> "tuple[bool,str]":
    """صحتِ تگ را چک کن. هر mismatchِ effect/amount/binding/owner یا انقضا → (False, reason)."""
    sec = _secret()
    if sec is None:
        return (False, "no-secret")
    parts = str(token or "").split(".")
    if len(parts) != 4 or parts[0] != "mc2":
        return (False, "bad-format")
    if parts[1] != hashlib.sha256(str(effect_id).encode()).hexdigest()[:12]:
        return (False, "wrong-effect")
    try:
        exp = int(parts[2])
    except ValueError:
        return (False, "bad-exp")
    if (now if now is not None else _now()) >= exp:
        return (False, "expired")
    expect = mint_money_token(effect_id=effect_id, content_hash=content_hash, action_kind=action_kind,
                              target_ref=target_ref, amount=amount, owner=owner, exp=exp)
    if not expect or not hmac.compare_digest(str(token), expect):
        return (False, "bad-sig")
    return (True, "ok")


# ── durable card store (SoTِ projectionِ کارت — نوشتهٔ لحظهٔ ساخت) ────────────────
def _store_path(state_dir) -> Path:
    return Path(state_dir) / "pulse" / "pending-cards.json"


def _load_store(state_dir) -> dict:
    """بارگذاریِ store. blindspot #148 (2026-08-03): قبلاً corrupted/unreadable
    ساکت {} برمی‌گرداند → همهٔ کارت‌هایِ پولِ pending بی‌صدا محو می‌شدند. حالا
    fail-closed: در صورتِ خطا، یک marker مخصوص برمی‌گرداند که callerها باید
    تشخیص دهند (کلیدِ __corrupted__). فقط «فایلِ غایب» {} مجاز است (اولین اجرا)."""
    p = _store_path(state_dir)
    if not p.exists():
        return {}  # اولین اجرا — store هنوز ساخته نشده
    try:
        d = json.loads(p.read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception as e:  # noqa: BLE001 — blindspot #148: fail-closed
        try:
            import opslib as _ops  # noqa: PLC0415
            _ops.alert([f"pending_card_recovery _load_store CORRUPTED (#148): "
                        f"{type(e).__name__}: {e} — store ممکن است خراب باشد، "
                        "بازگرداندن marker به‌جای dict خالی برای جلوگیری از محوِ بی‌صدا"])
        except Exception:
            pass
        return {"__corrupted__": True, "__error__": f"{type(e).__name__}: {e}"}


def _save_store(state_dir, store: dict) -> bool:
    try:
        p = _store_path(state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)   # atomic
        return True
    except Exception:  # noqa: BLE001
        return False


def _key(kind, cid) -> str:
    return f"{kind}:{cid}"


def _callback_token(*, effect_id, nonce, content_hash, action_kind, target_ref,
                    amount, owner, exp) -> "str | None":
    """Bearer روی دیسک ذخیره نمی‌شود؛ از nonce+binding+secret مشتق می‌شود."""
    sec = _secret()
    if sec is None or not nonce or owner in (None, ""):
        return None
    canon = (f"app3|{effect_id}|{nonce}|{content_hash or ''}|{action_kind or ''}|"
             f"{target_ref or ''}|{float(amount):.6f}|{owner}|{int(exp)}")
    return hmac.new(sec, canon.encode("utf-8"), hashlib.sha256).hexdigest()[:24]


def _mutate_store(state_dir, mutator) -> bool:
    """load-modify-replace زیرِ lease سراسری؛ دو writer کارت‌های متفاوت را گم نمی‌کنند.

    A process crash can strand the lock file. Reclaim is allowed only after a bounded
    stale interval; a fresh lock is never broken.
    """
    lock = Path(state_dir) / "pulse" / "pending-cards.lock"
    fd = None
    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + 3.0
        while True:
            try:
                fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, json.dumps({"pid": os.getpid(), "at": _now()}).encode("utf-8"))
                break
            except FileExistsError:
                try:
                    if time.time() - lock.stat().st_mtime > 30.0:
                        lock.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.time() >= deadline:
                    return False
                time.sleep(0.02)
        store = _load_store(state_dir)
        mutator(store)
        return _save_store(state_dir, store)
    except Exception:  # noqa: BLE001
        return False
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            lock.unlink(missing_ok=True)
        except OSError:
            pass


def prepare_money_card(*, state_dir, effect_id, amount_aud, content_hash, action_kind,
                       target_ref, summary, owner, expires_at=None) -> "dict | None":
    """PERSIST-BEFORE-SEND: intent را PENDING می‌نویسد و توکن HMAC مشتق‌شده برمی‌گرداند."""
    if state_dir is None or not effect_id or float(amount_aud) <= 0:
        return None
    existing = _load_store(state_dir).get(_key("money", str(effect_id))) or {}
    if existing:
        same = (str(existing.get("owner")) == str(owner)
                and abs(float(existing.get("amount_aud") or 0) - float(amount_aud)) < 1e-9
                and str(existing.get("content_hash") or "") == str(content_hash or "")
                and str(existing.get("action_kind") or "") == str(action_kind or "")
                and str(existing.get("target_ref") or "") == str(target_ref or "")
                and existing.get("decision") in ("PENDING", "DEFERRED")
                and int(existing.get("expires_at") or 0) > _now())
        if not same:
            return None  # same effect_id with changed binding is a card-swap attempt
        token = _callback_token(effect_id=effect_id, nonce=existing.get("nonce"),
                                content_hash=content_hash, action_kind=action_kind,
                                target_ref=target_ref, amount=amount_aud, owner=owner,
                                exp=int(existing["expires_at"]))
        if token and hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),
                                         str(existing.get("token_sha256") or "")):
            return {"token": token, "record": existing,
                    "send_needed": existing.get("delivery") != "SENT", "reused": True}
        return None
    exp = int(expires_at) if expires_at else (_now() + TTL_S)
    nonce = secrets.token_hex(16)
    token = _callback_token(effect_id=effect_id, nonce=nonce, content_hash=content_hash,
                            action_kind=action_kind, target_ref=target_ref, amount=amount_aud,
                            owner=owner, exp=exp)
    if not token:
        return None
    tag = mint_money_token(effect_id=effect_id, content_hash=content_hash or "",
                           action_kind=action_kind or "", target_ref=target_ref or "",
                           amount=float(amount_aud), owner=owner, exp=exp)
    rec = {"kind": "money", "effect_id": str(effect_id), "owner": owner,
           "amount_aud": float(amount_aud), "content_hash": content_hash,
           "action_kind": action_kind, "target_ref": target_ref,
           "summary": str(summary or "")[:500], "nonce": nonce,
           "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
           "integrity": tag, "expires_at": exp, "delivery": "PENDING",
           "decision": "PENDING", "defer_count": 0,
           "created_ts": _now(), "updated_ts": _now()}
    ok = _mutate_store(state_dir, lambda s: s.__setitem__(_key("money", str(effect_id)), rec))
    return {"token": token, "record": rec, "send_needed": True, "reused": False} if ok else None


def record_money_card(*, state_dir, effect_id, amount_aud, content_hash, action_kind,
                      target_ref, summary, owner, token=None, expires_at=None,
                      delivery="SENT") -> bool:
    """در لحظهٔ ساختِ کارتِ مالی صدا زده می‌شود (توسطِ کانال). ردیفِ durable با مبلغِ **واقعی**
    + binding + توکنِ **واقعیِ callback** + integrity-tag را می‌نویسد. fail-soft."""
    # compatibility wrapper: raw token عمداً نادیده گرفته می‌شود.
    made = prepare_money_card(state_dir=state_dir, effect_id=effect_id, amount_aud=amount_aud,
                              content_hash=content_hash, action_kind=action_kind,
                              target_ref=target_ref, summary=summary, owner=owner,
                              expires_at=expires_at)
    if not made:
        return False
    return mark_delivery(state_dir=state_dir, kind="money", cid=effect_id,
                         delivery=delivery)


def _rfc_callback_token(*, rfc_id, nonce, owner, exp) -> "str | None":
    sec = _secret()
    if sec is None or not nonce or owner in (None, ""):
        return None
    canon = f"rfc3|{rfc_id}|{nonce}|{owner}|{int(exp)}"
    return hmac.new(sec, canon.encode("utf-8"), hashlib.sha256).hexdigest()[:24]


def prepare_rfc_card(*, state_dir, rfc_id, summary, owner, expires_at=None) -> "dict | None":
    """Persist RFC intent before send. Only nonce+hash are durable, never bearer token."""
    if state_dir is None or not rfc_id:
        return None
    existing = _load_store(state_dir).get(_key("rfc", str(rfc_id))) or {}
    if existing:
        if (existing.get("decision") != "SUBMITTED" or
                str(existing.get("owner")) != str(owner) or
                int(existing.get("expires_at") or 0) <= _now()):
            return None
        token = _rfc_callback_token(rfc_id=rfc_id, nonce=existing.get("nonce"),
                                    owner=owner, exp=int(existing["expires_at"]))
        if token and hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),
                                         str(existing.get("token_sha256") or "")):
            return {"token": token, "record": existing,
                    "send_needed": existing.get("delivery") != "SENT", "reused": True}
        return None
    exp = int(expires_at) if expires_at else (_now() + TTL_S)
    nonce = secrets.token_hex(16)
    token = _rfc_callback_token(rfc_id=rfc_id, nonce=nonce, owner=owner, exp=exp)
    if not token:
        return None
    rec = {"kind": "rfc", "rfc_id": str(rfc_id), "summary": str(summary or "")[:500],
           "owner": owner, "nonce": nonce, "expires_at": exp,
           "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
           "delivery": "PENDING", "decision": "SUBMITTED",
           "created_ts": _now(), "updated_ts": _now()}
    ok = _mutate_store(state_dir, lambda s: s.__setitem__(_key("rfc", str(rfc_id)), rec))
    return {"token": token, "record": rec, "send_needed": True, "reused": False} if ok else None


def record_rfc_card(*, state_dir, rfc_id, summary, token=None, delivery="SENT",
                    owner=None) -> bool:
    """Compatibility wrapper. The supplied raw token is deliberately ignored."""
    made = prepare_rfc_card(state_dir=state_dir, rfc_id=rfc_id, summary=summary,
                            owner=owner or os.environ.get("TELEGRAM_OWNER_CHAT_ID"))
    if not made:
        return False
    return mark_delivery(state_dir=state_dir, kind="rfc", cid=rfc_id, delivery=delivery)


def verify_rfc_callback(*, state_dir, rfc_id, token, owner, now=None):
    rec = _load_store(state_dir).get(_key("rfc", str(rfc_id)))
    if not isinstance(rec, dict):
        return False, None, "unknown-card"
    if str(owner) != str(rec.get("owner")):
        return False, None, "wrong-owner"
    exp = int(rec.get("expires_at") or 0)
    if (now if now is not None else _now()) >= exp:
        return False, None, "expired"
    if rec.get("decision") != "SUBMITTED":
        return False, None, "already-decided"
    expect = _rfc_callback_token(rfc_id=rfc_id, nonce=rec.get("nonce"),
                                 owner=rec.get("owner"), exp=exp)
    if not expect or not hmac.compare_digest(str(token), expect):
        return False, None, "bad-token"
    if not hmac.compare_digest(hashlib.sha256(expect.encode()).hexdigest(),
                               str(rec.get("token_sha256") or "")):
        return False, None, "token-hash-mismatch"
    return True, rec, "ok"


def mark_delivery(*, state_dir, kind, cid, delivery) -> bool:
    """گذارِ ماشینِ حالتِ دلیوری (PENDING/LEASED/SENT). atomic. fail-soft."""
    try:
        changed = {"ok": False}
        def _do(store):
            k = _key(kind, str(cid))
            if k in store:
                store[k]["delivery"] = str(delivery)
                store[k]["updated_ts"] = _now()
                changed["ok"] = True
        return _mutate_store(state_dir, _do) and changed["ok"]
    except Exception:  # noqa: BLE001
        return False


# ── atomic send lease (O_EXCL — بوتِ همزمان دوبار نمی‌فرستد) ──────────────────────
def _lease_path(state_dir, kind, cid) -> Path:
    safe = hashlib.sha256(f"{kind}:{cid}".encode()).hexdigest()[:20]
    return Path(state_dir) / "pulse" / "card-lease" / f"{safe}.lease"


def _acquire_send_lease(state_dir, kind, cid, boot_id, now=None) -> bool:
    """با O_CREAT|O_EXCL (اتمیک روی Win/POSIX) حقِ ارسالِ این کارت را claim کن. leaseِ کهنه
    (> _LEASE_TTL_S) بازپس گرفته می‌شود. True = این بوت می‌فرستد؛ False = بوتِ دیگر دارد می‌فرستد."""
    n = now if now is not None else _now()
    p = _lease_path(state_dir, kind, cid)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False  # fail-closed: بدون lease اتمیک ارسال نکن
    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps({"boot_id": str(boot_id), "at": n}))
        return True
    except FileExistsError:
        # lease موجود — کهنه است؟
        try:
            d = json.loads(p.read_text("utf-8"))
            if n - int(d.get("at", 0)) > _LEASE_TTL_S:
                p.unlink(missing_ok=True)   # leaseِ کهنه → بازپس‌گیری
                return _acquire_send_lease(state_dir, kind, cid, boot_id, now=n)
        except Exception:  # noqa: BLE001
            pass
        return False
    except OSError:
        return False  # fail-closed: خطای FS نباید ارسالِ دوگانه بسازد


def release_send_lease(state_dir, kind, cid) -> None:
    try:
        _lease_path(state_dir, kind, cid).unlink(missing_ok=True)
    except OSError:
        pass


# ── chrono status cross-check (فقط pending/releasable re-present) ─────────────────
def _chrono_status(chrono_db_path, effect_id) -> "str | None":
    try:
        db = Path(chrono_db_path)
        if not db.exists():
            return None
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        row = con.execute("SELECT status FROM gated_effect WHERE effect_id=?",
                          (str(effect_id),)).fetchone()
        con.close()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def rebuild_money_cards(*, channel, chrono_db_path=None, owner, state_dir=None, now=None,
                        halted=False, boot_id="boot", status_fn=None) -> dict:
    """کارت‌های مالیِ معلق را از **storeِ durable** بازسازی کن، با cross-checkِ chrono.
    projection **همیشه** بازسازی می‌شود (B1)؛ دلیوری با ماشینِ حالت (B4/B5) و lease (concurrency).
    خروجی: {rebuilt, sent, skipped_terminal, skipped_unknown_amount, halted}. fail-soft."""
    out = {"rebuilt": 0, "sent": 0, "skipped_terminal": 0, "skipped_unknown_amount": 0,
           "halted": bool(halted)}
    if not _flag_on():
        out["skipped"] = "flag-off"
        return out
    if state_dir is None:
        out["skipped"] = "no-state-dir"
        return out
    n = now if now is not None else _now()
    stat = status_fn or (lambda eid: _chrono_status(chrono_db_path, eid))
    try:
        store = _load_store(state_dir)
        for k, rec in list(store.items()):
            if not isinstance(rec, dict) or rec.get("kind") != "money":
                continue
            eid = rec.get("effect_id")
            # cross-check با chrono: فقط pending/releasable re-present (هرگز terminal/EXECUTING/RECONCILE)
            st = stat(eid)
            if st not in _MONEY_SAFE_STATES:
                out["skipped_terminal"] += 1
                continue
            exp = int(rec.get("expires_at") or (n + TTL_S))
            if exp <= n:
                continue
            amount = rec.get("amount_aud")
            # fail-closed (B6): مبلغِ نامعلوم یا integrity-tamper → هیچ کارتِ قابلِ‌کلیک
            if amount is None or float(amount) <= 0:
                out["skipped_unknown_amount"] += 1
                continue
            ok_tag, _why = verify_money_token(
                rec.get("integrity"), effect_id=eid, content_hash=rec.get("content_hash") or "",
                action_kind=rec.get("action_kind") or "", target_ref=rec.get("target_ref") or "",
                amount=float(amount), owner=rec.get("owner"), now=n)
            if not ok_tag:
                out["skipped_unknown_amount"] += 1   # tamper/عدمِ‌صحت = همان مسیرِ fail-closed
                continue
            if str(rec.get("decision") or "PENDING") not in ("PENDING", "DEFERRED"):
                continue
            token = _callback_token(
                effect_id=eid, nonce=rec.get("nonce"), content_hash=rec.get("content_hash"),
                action_kind=rec.get("action_kind"), target_ref=rec.get("target_ref"),
                amount=float(amount), owner=rec.get("owner"), exp=exp)
            if not token or not hmac.compare_digest(
                    hashlib.sha256(token.encode()).hexdigest(), str(rec.get("token_sha256") or "")):
                out["skipped_unknown_amount"] += 1
                continue
            delivery = str(rec.get("delivery") or "PENDING")
            # projection در هر بوت از nonce+binding بازسازی می‌شود؛ raw token روی دیسک نیست.
            _reissue(channel, eid, float(amount), rec.get("summary") or "",
                     rec.get("content_hash"), rec.get("action_kind"), rec.get("target_ref"),
                     token, send=False)
            out["rebuilt"] += 1
            # (2) دلیوری: زیرِ HALT هرگز نفرست/mark نکن (B4). فقط اگر هنوز SENT نشده (B1 no-spam / B5 retry)
            if halted:
                continue
            if delivery == "SENT":
                continue   # قبلاً تحویل شده؛ دکمهٔ همان‌توکن هنوز معتبر (مدل B) → صفر spam
            if not _acquire_send_lease(state_dir, "money", eid, boot_id, now=n):
                continue   # بوتِ همزمان دارد می‌فرستد
            try:
                mark_delivery(state_dir=state_dir, kind="money", cid=eid, delivery="LEASED")
                sent = _reissue(channel, eid, float(amount), rec.get("summary") or "",
                                rec.get("content_hash"), rec.get("action_kind"),
                                rec.get("target_ref"), token, send=True)
                if sent:
                    mark_delivery(state_dir=state_dir, kind="money", cid=eid, delivery="SENT")
                    out["sent"] += 1
                else:
                    mark_delivery(state_dir=state_dir, kind="money", cid=eid, delivery="PENDING")
            finally:
                release_send_lease(state_dir, "money", eid)
        return out
    except Exception as e:  # noqa: BLE001 — بازسازی هرگز بوت را نمی‌کشد
        out["skipped"] = f"error:{type(e).__name__}"
        return out


def verify_callback(*, state_dir, effect_id, token, owner, chrono_db_path=None,
                    status_fn=None, now=None,
                    require_effect_pending: bool = True) -> "tuple[bool, dict | None, str]":
    """گیتِ کلیک: owner+expiry+HMAC+binding را در همان لحظه verify می‌کند.
    `require_effect_pending` (پیش‌فرض True): چکِ chrono status=pending. **فقط برای approve**
    (فعلِ settle) لازم است — چون تنها approve پول را آزاد می‌کند. deny/later اثرِ مالی ندارند و
    نباید به pending‌بودنِ chrono مقید شوند (backcompat + امکانِ رد کردنِ کارتِ اثرِ غیر-pending).
    توجه: مسیرِ مالی دست‌نخورده است — approve بعداً از EffectorGate.release_effect می‌گذرد که
    خودش binding+status='pending' را اتمیک دوباره چک می‌کند."""
    rec = _load_store(state_dir).get(_key("money", str(effect_id)))
    if not isinstance(rec, dict):
        return False, None, "unknown-card"
    if str(owner) != str(rec.get("owner")):
        return False, None, "wrong-owner"
    n = now if now is not None else _now()
    exp = int(rec.get("expires_at") or 0)
    if n >= exp:
        return False, None, "expired"
    if str(rec.get("decision") or "PENDING") not in ("PENDING", "DEFERRED"):
        return False, None, "already-decided"
    expect = _callback_token(effect_id=effect_id, nonce=rec.get("nonce"),
                             content_hash=rec.get("content_hash"),
                             action_kind=rec.get("action_kind"), target_ref=rec.get("target_ref"),
                             amount=rec.get("amount_aud"), owner=rec.get("owner"), exp=exp)
    if not expect or not hmac.compare_digest(str(token), expect):
        return False, None, "bad-token"
    if require_effect_pending:
        stat = status_fn or (lambda eid: _chrono_status(chrono_db_path, eid))
        if stat(effect_id) not in _MONEY_SAFE_STATES:
            return False, None, "effect-not-pending"
    return True, rec, "ok"


# ── ماشینِ حالتِ پول (نقطهٔ کورِ ۱۳۶) ────────────────────────────────────────
# تا امروز فقط **حالتِ مقصد** اعتبارسنجی می‌شد، نه **گذار**. یعنی `APPROVED →
# PENDING` مجاز بود: یک پرداختِ تمام‌شده می‌توانست به عقب برگردد و دوباره کارت
# بگیرد. هیچ صداکنندهٔ امروزی این کار را نمی‌کند، ولی «امروز هیچ‌کس نمی‌کند»
# ناوردی نیست — فقط یک مشاهده است.
#
# ناوردیِ واقعی: **تصمیمِ پولی هرگز بی‌تصمیم نمی‌شود.** APPROVED و DENIED پایانی‌اند.
MONEY_STATES = {"PENDING", "DEFERRED", "DENIED", "APPROVING", "APPROVED", "EXPIRED",
                "RECONCILE_REQUIRED"}
MONEY_TRANSITIONS = {
    "": set(MONEY_STATES),                       # رکوردِ تازه، بدونِ حالتِ قبلی
    "PENDING": {"DEFERRED", "DENIED", "APPROVING", "EXPIRED"},
    "DEFERRED": {"PENDING", "DEFERRED", "DENIED", "APPROVING", "EXPIRED"},
    "APPROVING": {"APPROVED", "RECONCILE_REQUIRED", "DENIED"},
    "RECONCILE_REQUIRED": {"APPROVED", "DENIED"},   # فقط رأیِ مالک بازش می‌کند
    "APPROVED": set(),                              # پایانی
    "DENIED": set(),                                # پایانی
    "EXPIRED": set(),                               # پایانی
}
# ⚠️ عمداً پیش‌فرض **خاموش**. این گارد روی مسیرِ زندهٔ پول می‌نشیند و فهرستِ
# گذارهای بالا از خواندنِ کد آمده، نه از مشاهدهٔ ترافیکِ واقعی. اگر همین حالا
# اجباری شود و یک گذارِ مشروعِ نادیده وجود داشته باشد، پرداختِ واقعیِ مالک
# می‌شکند. پس اول **می‌شمارد**، بعد — با شواهد — مسلح می‌شود.
TRANSITION_FLAG = "OCTOPUS_ENFORCE_MONEY_FSM"


def _illegal_transition(prev: str, nxt: str) -> bool:
    return nxt not in MONEY_TRANSITIONS.get(str(prev or ""), set(MONEY_STATES))


def _log_transition(effect_id, prev: str, nxt: str, enforced: bool,
                    *, state_dir=None) -> None:
    """۲۰۲۶-۰۷-۲۸ — `state_dir` اضافه شد چون این تابع مقصدِ خودش را حساب می‌کرد.

    `persist_money_decision` مسیرِ درست را به‌عنوان پارامتر می‌گیرد و به
    `_mutate_store` می‌دهد، ولی این لاگ آن را **نادیده می‌گرفت** و
    `_ops_state_dir()` را صدا می‌زد. نتیجه: `test_money_fsm` با harnessِ ایزوله
    اجرا می‌شد و لاگش در `_ops/state` ِ **زنده** می‌نشست.

    پیامدش تزئینی نبود: تنها شواهدی که کدِ خودِ FSM قبل از مسلح‌شدن طلب می‌کند
    همین فایل است، و آن فایل با دو ردیفِ ساختهٔ تست آلوده شده بود (`APPROVED →
    PENDING` با `enforced` هم True هم False در یک ثانیه — چیزی که کدِ زنده با
    فلگِ همیشه‌خاموش نمی‌تواند بنویسد). یعنی «صفر گذارِ واقعی» شبیهِ «دو نمونه»
    به نظر می‌رسید. خویشاوندِ `_timeout_truncated` (همان روز، صبح).

    `state_dir` نداده‌شده = رفتارِ قبلی، پس هیچ صداکنندهٔ دیگری نمی‌شکند.
    """
    try:
        base = Path(state_dir) if state_dir else Path(_ops_state_dir())
        p = base / "money-fsm-violations.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now(), "effect_id": str(effect_id)[:64],
                                "from": prev, "to": nxt, "enforced": bool(enforced)},
                               ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _ops_state_dir():
    try:
        import opslib
        return opslib.STATE_DIR
    except Exception:  # noqa: BLE001
        return Path(__file__).resolve().parent.parent / "state"


def persist_money_decision(*, state_dir, effect_id, decision, defer_count=None) -> bool:
    allowed = MONEY_STATES
    if decision not in allowed:
        return False
    enforce = str(os.environ.get(TRANSITION_FLAG, "")).strip().lower() in (
        "1", "true", "yes", "on")
    changed = {"ok": False, "blocked": False}
    def _do(store):
        rec = store.get(_key("money", str(effect_id)))
        if isinstance(rec, dict):
            prev = str(rec.get("decision") or "")
            if _illegal_transition(prev, decision):
                _log_transition(effect_id, prev, decision, enforce,
                                state_dir=state_dir)
                if enforce:
                    changed["blocked"] = True
                    return
            rec["decision"] = decision
            if defer_count is not None:
                rec["defer_count"] = int(defer_count)
                rec["deferred_at"] = _now()
            rec["updated_ts"] = _now()
            changed["ok"] = True
    wrote = _mutate_store(state_dir, _do)
    if changed["blocked"]:
        return False        # گذارِ غیرمجاز، با فلگِ اجبار → صریحاً ناموفق
    return wrote and changed["ok"]


def _reissue(channel, effect_id, amount, summary, content_hash, action_kind, target_ref,
             token, *, send) -> bool:
    """رندرِ canonical (اشتراکی با request_approval_card). projection را با **همان توکن** بازسازی
    می‌کند؛ فقط اگر send=True کارتِ ۳-دکمه می‌فرستد. اگر کانال متدِ reissue داشت از آن (single
    source of truth) استفاده کن؛ وگرنه fallbackِ حداقلی (فقط projection)."""
    try:
        if hasattr(channel, "reissue_approval_card"):
            return bool(channel.reissue_approval_card(
                effect_id, float(amount), str(summary), token=token,
                content_hash=content_hash, action_kind=action_kind,
                target_ref=target_ref, send=bool(send)))
        # fallback: projection مستقیم (کانالِ تست/قدیمی) — همان binding و همان token
        meta = {"amount_aud": float(amount), "summary": str(summary), "token": token,
                "content_hash": content_hash, "action_kind": action_kind,
                "target_ref": target_ref, "status": "pending", "rebuilt": True}
        try:
            with getattr(channel, "_lk", _NullLock()):
                channel._pending[str(effect_id)] = meta   # noqa: SLF001
        except Exception:  # noqa: BLE001
            channel._pending[str(effect_id)] = meta       # noqa: SLF001
        if send and hasattr(channel, "send_text"):
            channel.send_text(f"card:{effect_id}", reply_markup={"inline_keyboard": [[
                {"text": "approve", "callback_data": f"app:approve:{effect_id}:{token}"},
                {"text": "deny", "callback_data": f"app:deny:{effect_id}:{token}"},
                {"text": "later", "callback_data": f"app:later:{effect_id}:{token}"}]]})
        return bool(send)
    except Exception:  # noqa: BLE001
        return False


# ── RFC durable verdict (exactly-once across restart) ────────────────────────────
def _rfc_verdict_path(state_dir):
    return Path(state_dir) / "doctor" / "rfc-verdicts.jsonl"


def _rfc_db_path(state_dir):
    return Path(state_dir) / "doctor" / "rfc-verdicts.db"


def _rfc_con(state_dir):
    p = _rfc_db_path(state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p), timeout=5.0)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE IF NOT EXISTS rfc_decision("
                "rfc_id TEXT PRIMARY KEY, verdict TEXT NOT NULL, revision INTEGER NOT NULL,"
                "state TEXT NOT NULL, lease_owner TEXT, lease_until INTEGER,"
                "receipt_id TEXT, operation_key TEXT, updated_ts INTEGER NOT NULL)")
    rfc_cols = {r[1] for r in con.execute("PRAGMA table_info(rfc_decision)")}
    if "operation_key" not in rfc_cols:
        con.execute("ALTER TABLE rfc_decision ADD COLUMN operation_key TEXT")
    # One-time compatibility migration from the C7.1 JSONL ledger. A consumed merge has
    # unknown apply outcome, so it becomes RECONCILE_REQUIRED rather than falsely APPLIED.
    if con.execute("SELECT COUNT(*) FROM rfc_decision").fetchone()[0] == 0:
        legacy = _rfc_verdict_path(state_dir)
        folded = {}
        if legacy.exists():
            for ln in legacy.read_text("utf-8").splitlines():
                try:
                    r = json.loads(ln); rid = str(r.get("rfc_id") or "")
                except Exception:
                    continue
                if not rid:
                    continue
                cur = folded.setdefault(rid, {"verdict": "", "consumed": False})
                if r.get("verdict"):
                    cur["verdict"] = str(r["verdict"])
                cur["consumed"] = cur["consumed"] or bool(r.get("consumed"))
        for rid, r in folded.items():
            if not r["verdict"]:
                continue
            state = ("REJECTED" if r["consumed"] and r["verdict"] == "denied" else
                     ("RECONCILE_REQUIRED" if r["consumed"] else "DECIDED"))
            con.execute("INSERT OR IGNORE INTO rfc_decision("
                        "rfc_id,verdict,revision,state,lease_owner,lease_until,receipt_id,"
                        "operation_key,updated_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                        (rid, r["verdict"], 1, state, None, None, "", None, _now()))
    con.commit()
    return con


def persist_rfc_verdict(*, state_dir, rfc_id, verdict) -> bool:
    """SUBMITTED→DECIDED, durably and idempotently, before Telegram ACK."""
    try:
        con = _rfc_con(state_dir)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT verdict,revision,state FROM rfc_decision WHERE rfc_id=?",
                              (str(rfc_id),)).fetchone()
            if row and row[2] in ("DECIDED", "LEASED", "APPLIED", "REJECTED",
                                  "RECONCILE_REQUIRED"):
                # Same owner verdict is an idempotent replay; a conflicting second verdict
                # is rejected rather than silently creating a new decision revision.
                con.rollback(); return row[0] == str(verdict)
            rev = int(row[1]) + 1 if row else 1
            con.execute("INSERT INTO rfc_decision(rfc_id,verdict,revision,state,updated_ts) "
                        "VALUES(?,?,?,?,?) ON CONFLICT(rfc_id) DO UPDATE SET "
                        "verdict=excluded.verdict,revision=excluded.revision,state='DECIDED',"
                        "lease_owner=NULL,lease_until=NULL,updated_ts=excluded.updated_ts",
                        (str(rfc_id), str(verdict), rev, "DECIDED", _now()))
            con.commit()
        finally:
            con.close()
        # Card projection is terminal as soon as the owner decision is durable.
        _mutate_store(state_dir, lambda s: s.get(_key("rfc", str(rfc_id)), {}).update(
            {"decision": "DECIDED", "updated_ts": _now()}))
        return True
    except Exception:
        return False


def claim_rfc_verdicts(*, state_dir, worker_id, lease_s=300) -> list:
    """DECIDED→LEASED with a durable lease. Returns (rfc_id, verdict, revision)."""
    out = []
    try:
        con = _rfc_con(state_dir)
        try:
            con.execute("BEGIN IMMEDIATE")
            now = _now()
            rows = con.execute(
                "SELECT rfc_id,verdict,revision FROM rfc_decision WHERE state='DECIDED' "
                "OR (state='LEASED' AND COALESCE(lease_until,0)<?) ORDER BY rfc_id", (now,)).fetchall()
            for rid, verdict, rev in rows:
                cur = con.execute(
                    "UPDATE rfc_decision SET state='LEASED',lease_owner=?,lease_until=?,updated_ts=? "
                    "WHERE rfc_id=? AND revision=? AND (state='DECIDED' OR lease_until<?)",
                    (str(worker_id), now + int(lease_s), now, rid, rev, now))
                if cur.rowcount == 1:
                    out.append((rid, verdict, int(rev)))
            con.commit()
        finally:
            con.close()
    except Exception:
        return []
    return out


def begin_rfc_apply(*, state_dir, rfc_id, revision, operation_key) -> bool:
    """Persist the ambiguity boundary before external/stateful apply.

    LEASED→RECONCILE_REQUIRED means a crash can never auto-retry the operation. A later
    APPLIED transition requires a real receipt bound to this operation key.
    """
    if not operation_key:
        return False
    try:
        con = _rfc_con(state_dir)
        try:
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute(
                "UPDATE rfc_decision SET state='RECONCILE_REQUIRED',operation_key=?,updated_ts=? "
                "WHERE rfc_id=? AND revision=? AND state='LEASED' AND verdict='merge-approved'",
                (str(operation_key), _now(), str(rfc_id), int(revision)))
            con.commit()
            return cur.rowcount == 1
        finally:
            con.close()
    except Exception:
        return False


def ack_rfc_verdict(*, state_dir, rfc_id, revision, applied, receipt_id="") -> bool:
    """LEASED→APPLIED/REJECTED only after the idempotent doctor operation receipt."""
    try:
        con = _rfc_con(state_dir)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT verdict,state,operation_key FROM rfc_decision "
                              "WHERE rfc_id=? AND revision=?",
                              (str(rfc_id), int(revision))).fetchone()
            if not row:
                con.rollback(); return False
            terminal = "APPLIED" if applied else ("REJECTED" if row[0] == "denied" else
                                                   "RECONCILE_REQUIRED")
            if terminal == "APPLIED" and (not receipt_id or not row[2]):
                con.rollback(); return False
            allowed_state = "RECONCILE_REQUIRED" if terminal == "APPLIED" else "LEASED"
            cur = con.execute(
                "UPDATE rfc_decision SET state=?,receipt_id=?,lease_owner=NULL,lease_until=NULL,"
                "updated_ts=? WHERE rfc_id=? AND revision=? AND state=?",
                (terminal, str(receipt_id or ""), _now(), str(rfc_id), int(revision),
                 allowed_state))
            con.commit()
            return cur.rowcount == 1
        finally:
            con.close()
    except Exception:
        return False


def mark_rfc_consumed(*, state_dir, rfc_id) -> bool:
    """RETIRED 2026-08-03 (بازنشسته — گامِ ۱۴ ِ UNIFICATION-DESIGN، جزءِ C5).

    این میان‌بر همان مسیری است که هر ۲۱ پایانهٔ بی‌رسیدِ درختِ زنده را ساخت: با
    `applied=False` و `receipt_id=""` صدا می‌زد و **هرگز** `begin_rfc_apply` را
    نمی‌پیمود، پس `operation_key` هم `NULL` می‌ماند. نتیجه طبقِ طراحیِ خودِ
    `ack_rfc_verdict` وضعیتِ `RECONCILE_REQUIRED` بود — یعنی مالک تصمیم می‌گرفت و
    هیچ اثری ثبت نمی‌شد.

    نکتهٔ مهم: مکانیزمِ رسید هرگز خراب نبود. `ack_rfc_verdict` از قبل fail-closed
    است و برای `APPLIED` هم `receipt_id` ِ ناتهی می‌خواهد هم `operation_key`. مسیر
    فقط هیچ‌وقت **پیموده** نشد. پس این تابع حذف نمی‌شود (قاعدهٔ «هرگز حذف نکن») ولی
    دیگر پایانه نمی‌سازد: صریح رد می‌کند تا صداکنندهٔ احتمالی خطا را ببیند، نه یک
    ردیفِ بی‌رسیدِ دیگر.

    مسیرِ درست: `record_rfc_card` → `persist_rfc_verdict` → `claim_rfc_verdicts`
    → `begin_rfc_apply(operation_key=...)` → `ack_rfc_verdict(receipt_id=...)`.
    """
    # هشدار fail-soft: این ماژول عمداً opslib را در سطحِ ماژول import نمی‌کند (مسیرِ
    # پول، وابستگیِ سبک). نبودنش نباید ردکردن را بشکند — ردکردن خودش قرارداد است.
    try:
        sys.path.insert(0, str(_HERE.parent / "budget"))
        import opslib as _ops_lib   # noqa: PLC0415
        _ops_lib.alert("rfc-legacy-consume-refused",
                       f"mark_rfc_consumed بازنشسته است (rfc={rfc_id}); "
                       "مسیرِ رسیددار را بپیمایید — C5")
    except Exception:  # noqa: BLE001
        pass
    return False


def reconstruct_rfc_from_card(*, state_dir, rfc_id) -> "dict | None":
    """وقتی self._rfcs (RAM/rfcs.json ِ دکتر) دیگر بدنهٔ اصلیِ RFC را ندارد ولی
    کارتِ durable (pending-cards.json) دارد — summary را به‌عنوان تنها منبعِ
    بازمانده برمی‌گرداند تا doctor.run_cycle بتواند یک RFC نمادین بسازد و
    apply_merge را صدا بزند. هرگز فیلدهایی (fix/rollback/expected_lift) را که
    اصلاً ذخیره نشده‌اند حدس نمی‌زند — فقط summary ِ واقعاً persist-شده.
    خروجی: {"summary": str} یا None اگر کارت هم نبود/summary خالی بود."""
    rec = _load_store(state_dir).get(_key("rfc", str(rfc_id)))
    if not isinstance(rec, dict):
        return None
    summary = str(rec.get("summary") or "").strip()
    if not summary:
        return None
    return {"summary": summary}


def load_rfc_verdicts(state_dir) -> dict:
    """Projection of the durable RFC state machine for recovery/UI."""
    out = {}
    if state_dir is None:
        return out
    try:
        con = _rfc_con(state_dir)
        try:
            # 2026-08-03 (گامِ ۲ ِ UNIFICATION-DESIGN، افزودنی): receipt_id و
            # operation_key هم پروجکت می‌شوند. بدونشان نمی‌شود «تصمیم اثر کرد» را
            # از «تصمیم ثبت شد» جدا کرد — و همین تفاوت کلِ یافتهٔ ۰۸-۰۳ است:
            # هر ۲۱ ردیف در RECONCILE_REQUIRED با receipt_id='' نشسته‌اند، یعنی
            # مالک ۲۱ بار تصمیم گرفت و صفر اثر ثبت شد. کلیدهای قبلی دست‌نخورده‌اند.
            for rid, verdict, rev, state, receipt, opkey, uts in con.execute(
                    "SELECT rfc_id,verdict,revision,state,receipt_id,operation_key,"
                    "updated_ts FROM rfc_decision"):
                out[rid] = {"verdict": verdict, "revision": int(rev), "state": state,
                            "consumed": state in ("APPLIED", "REJECTED"),
                            "receipt_id": receipt or "",
                            "operation_key": opkey or "",
                            # `updated_ts` لازم است تا «چند وقت است اینجا مانده»
                            # محاسبه شود. بدونش سنِ بدهی None می‌شود و کارتِ
                            # تجمیعی نمی‌تواند بگوید قدیمی‌ترین چند روزه است.
                            "updated_ts": uts}
        finally:
            con.close()
    except Exception:
        pass
    return out


def rebuild_rfc_cards(*, channel, rfcs_path, state_dir=None, now=None) -> dict:
    """کارت‌های RFC را بازسازی کن. رأیِ durable = exactly-once:
      * submitted + بدونِ رأیِ durable → کارتِ pending بازسازی می‌شود.
      * رأیِ durable + مصرف‌نشده → به‌صورتِ **decided** به _pending_rfc تزریق می‌شود تا
        pop_rfc_verdicts دقیقاً یک‌بار به doctor تحویل دهد (کلیک قبل از restart گم نمی‌شود).
      * رأیِ durable + مصرف‌شده → کاملاً skip."""
    out = {"rebuilt": 0, "reinjected_verdicts": 0, "skipped_decided": 0}
    if not _flag_on():
        out["skipped"] = "flag-off"
        return out
    try:
        verdicts = load_rfc_verdicts(state_dir)
        # (الف) رأی‌های durableِ مصرف‌نشده را به کانال تزریق کن تا doctor تحویل بگیرد (exactly-once)
        for rid, v in verdicts.items():
            if v.get("state") != "DECIDED" or not v.get("verdict"):
                continue
            try:
                with getattr(channel, "_lk", _NullLock()):
                    channel._pending_rfc[str(rid)] = {   # noqa: SLF001
                        "summary": "(recovered verdict)", "token": "recovered",
                        "status": v.get("verdict"), "consumed": False, "recovered": True}
                out["reinjected_verdicts"] += 1
            except Exception:  # noqa: BLE001
                pass
        # (ب) submittedِ بی‌رأی را دوباره کارت کن
        p = Path(rfcs_path)
        if not p.exists():
            out["skipped"] = "no-rfcs"
            return out
        doc = json.loads(p.read_text("utf-8"))
        rfcs = doc.get("rfcs", []) if isinstance(doc, dict) else doc
        if isinstance(rfcs, dict):
            rfcs = [{"rfc_id": k, **(v if isinstance(v, dict) else {})} for k, v in rfcs.items()]
        for r in rfcs:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("rfc_id") or r.get("id") or "")
            st = str(r.get("status") or "")
            if not rid:
                continue
            vd = verdicts.get(rid) or {}
            if st not in _RFC_SAFE_STATES or vd.get("verdict") or vd.get("consumed"):
                out["skipped_decided"] += 1
                continue
            summary = str(r.get("bottleneck") or r.get("fix") or r.get("summary") or "RFC")[:200]
            try:
                if hasattr(channel, "rfc_card"):
                    # Existing durable intent must be re-derived, not overwritten with a
                    # fresh nonce before an old Telegram button can be verified.
                    rec = _load_store(state_dir).get(_key("rfc", rid)) or {}
                    token = _rfc_callback_token(rfc_id=rid, nonce=rec.get("nonce"),
                                                owner=rec.get("owner"),
                                                exp=int(rec.get("expires_at") or 0))
                    if token and rec.get("decision") == "SUBMITTED":
                        with getattr(channel, "_lk", _NullLock()):
                            channel._pending_rfc[rid] = {"summary": summary, "token": token,
                                                         "status": "pending"}
                        out["rebuilt"] += 1
                    elif channel.rfc_card(rid, summary):
                        out["rebuilt"] += 1
            except Exception:  # noqa: BLE001
                pass
        return out
    except Exception as e:  # noqa: BLE001
        out["skipped"] = f"error:{type(e).__name__}"
        return out


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
