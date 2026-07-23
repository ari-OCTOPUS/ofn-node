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

**SoTِ کارت** = یک storeِ durable (`state/pulse/pending-cards.json`) که در **لحظهٔ ساختِ کارت**
توسطِ `TelegramApprovalChannel.request_approval_card`/`rfc_card` نوشته می‌شود و مبلغِ **واقعی** +
binding + توکنِ **واقعیِ callback** + generation را نگه می‌دارد. بازسازی از این store می‌خواند و
با chrono (SoTِ authorizationِ پول) **cross-check** می‌کند (فقط pending/releasable re-present).

**مدلِ توکن = B (stateless-valid + durable single-use):** توکنِ callback در لحظهٔ ساخت durable
می‌شود و در بازسازی **همان** بازگردانده می‌شود → دکمهٔ پیش از restartِ مالک همچنان کار می‌کند.
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


# ── tamper-evident integrity tag (ضدِ card-swap/wrong-owner/amount-tamperِ storeِ durable) ──
# این تگ **توکنِ callback نیست** (آن `_new_token`ِ کانال است، persist/restore می‌شود). این تگ
# فقط صحتِ ردیفِ durable را می‌بندد به (effect|binding|amount|owner|exp): اگر مهاجم store را
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
    try:
        p = _store_path(state_dir)
        if p.exists():
            d = json.loads(p.read_text("utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        pass
    return {}


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


def record_money_card(*, state_dir, effect_id, amount_aud, content_hash, action_kind,
                      target_ref, summary, owner, token, expires_at=None,
                      delivery="SENT") -> bool:
    """در لحظهٔ ساختِ کارتِ مالی صدا زده می‌شود (توسطِ کانال). ردیفِ durable با مبلغِ **واقعی**
    + binding + توکنِ **واقعیِ callback** + integrity-tag را می‌نویسد. fail-soft."""
    if state_dir is None or not effect_id:
        return False
    try:
        exp = int(expires_at) if expires_at else (_now() + TTL_S)
        store = _load_store(state_dir)
        k = _key("money", str(effect_id))
        prev = store.get(k) or {}
        tag = mint_money_token(effect_id=effect_id, content_hash=content_hash or "",
                               action_kind=action_kind or "", target_ref=target_ref or "",
                               amount=float(amount_aud), owner=owner, exp=exp)
        store[k] = {"kind": "money", "effect_id": str(effect_id), "owner": owner,
                    "amount_aud": float(amount_aud), "content_hash": content_hash,
                    "action_kind": action_kind, "target_ref": target_ref,
                    "summary": str(summary or "")[:500], "token": str(token or ""),
                    "integrity": tag, "expires_at": exp,
                    "delivery": str(delivery), "generation": int(prev.get("generation", 0)) + 1,
                    "created_ts": prev.get("created_ts", _now()), "updated_ts": _now()}
        return _save_store(state_dir, store)
    except Exception:  # noqa: BLE001
        return False


def record_rfc_card(*, state_dir, rfc_id, summary, token, delivery="SENT") -> bool:
    """در لحظهٔ ساختِ کارتِ RFC صدا زده می‌شود. ردیفِ durable (submitted-undecided). fail-soft."""
    if state_dir is None or not rfc_id:
        return False
    try:
        store = _load_store(state_dir)
        k = _key("rfc", str(rfc_id))
        prev = store.get(k) or {}
        store[k] = {"kind": "rfc", "rfc_id": str(rfc_id), "summary": str(summary or "")[:500],
                    "token": str(token or ""), "delivery": str(delivery),
                    "created_ts": prev.get("created_ts", _now()), "updated_ts": _now()}
        return _save_store(state_dir, store)
    except Exception:  # noqa: BLE001
        return False


def mark_delivery(*, state_dir, kind, cid, delivery) -> bool:
    """گذارِ ماشینِ حالتِ دلیوری (PENDING/LEASED/SENT). atomic. fail-soft."""
    try:
        store = _load_store(state_dir)
        k = _key(kind, str(cid))
        if k not in store:
            return False
        store[k]["delivery"] = str(delivery)
        store[k]["updated_ts"] = _now()
        return _save_store(state_dir, store)
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
        return True   # نبودِ دایرکتوری‌سازی → بگذار ارسال شود (fail-open برای دلیوری، نه پول)
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
        return True   # خطای FSِ نامنتظر → دلیوری را نبند (پول از lease نمی‌گذرد)


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
            token = rec.get("token") or ""
            delivery = str(rec.get("delivery") or "PENDING")
            # (1) projection **همیشه** بازسازی می‌شود (توکنِ callbackِ اصلی بازگردانده می‌شود — مدل B)
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


def persist_rfc_verdict(*, state_dir, rfc_id, verdict) -> bool:
    """رأیِ RFC را durable کن **پیش از** ackِ callback (B7). append-only + fsync."""
    try:
        p = _rfc_verdict_path(state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"rfc_id": str(rfc_id), "verdict": str(verdict),
                                "consumed": False, "ts": _now()}, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception:  # noqa: BLE001
        return False


def mark_rfc_consumed(*, state_dir, rfc_id) -> bool:
    """doctor پس از مصرفِ verdict این را می‌زند (durable consumed → بعد از restart دوبار مصرف نمی‌شود)."""
    try:
        p = _rfc_verdict_path(state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"rfc_id": str(rfc_id), "verdict": "", "consumed": True,
                                "ts": _now()}, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception:  # noqa: BLE001
        return False


def load_rfc_verdicts(state_dir) -> dict:
    """آخرین حالتِ هر rfc_id: {rfc_id: {"verdict": str, "consumed": bool}}. آخرین خط برنده."""
    out: dict = {}
    if state_dir is None:
        return out
    p = _rfc_verdict_path(state_dir)
    if p.exists():
        for ln in p.read_text("utf-8").splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            rid = r.get("rfc_id")
            if rid is None:
                continue
            cur = out.setdefault(rid, {"verdict": "", "consumed": False})
            if r.get("verdict"):
                cur["verdict"] = r.get("verdict")
            if r.get("consumed"):
                cur["consumed"] = True
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
            if v.get("consumed") or not v.get("verdict"):
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
                    channel.rfc_card(rid, summary)
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
