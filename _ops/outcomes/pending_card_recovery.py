#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pending_card_recovery.py — C7 Slice 1: بازسازیِ کارت‌های approvalِ معلق بعد از restart.

قوسِ شکسته (audit A3/A4): `_pending` (کارت‌های مالی) و `_pending_rfc` (کارت‌های RFC) در RAM
بودند → restart همه‌شان را می‌کشت. حقیقتِ پایدار موجود است:
  money  → chrono.gated_effect (SoT)
  RFC    → doctor rfcs.json + verdictِ پایدار (این‌جا اضافه می‌شود)
UI فقط projection است؛ در بوت از SoT بازسازی می‌شود.

**مرزهای سختِ مأموریت (رعایت‌شده):**
  - **صفر تغییرِ semanticِ authorizationِ پول.** بازسازی فقط کارت را دوباره «نمایش» می‌دهد؛
    آزادسازیِ واقعیِ پول همچنان فقط از EffectorGate.release_effect (بایندِ دقیقِ C4) می‌گذرد.
  - فقط statesِ امنِ re-present: pending/releasable — **هرگز** terminal (settled/refused/FAILED_SAFE/
    EXPIRED) و **هرگز** EXECUTINGِ درمیان‌پرواز یا RECONCILE_REQUIRED (آن‌ها آشتیِ انسانی می‌خواهند).
  - توکنِ **stateless HMAC** بایند به (effect_id|content_hash|action_kind|target_ref|amount|owner|exp).
    توکنِ خام هرگز persist نمی‌شود؛ توکنِ قدیمی بعد از restart fail می‌شود (binding/exp تازه).
  - dedupِ durable بینِ بوت‌ها (صفر spam).
  - زیرِ STOP/HALT: بازسازیِ metadata مجاز، ولی **صفر settle/action** (EffectorGate خودش refuse می‌کند).
  - RFC: فقط submitted/unconsumed؛ denied/merged/consumed هرگز دوباره ظاهر نمی‌شوند؛ verdict
    consumption **exactly-once across restart** (verdictِ پایدار).
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
_MONEY_SAFE_STATES = ("pending", "releasable")   # فقط این‌ها re-present می‌شوند
_RFC_SAFE_STATES = ("submitted",)                # doctor-side؛ decided/merged/denied → نه


def _secret() -> "bytes | None":
    s = os.environ.get(SECRET_ENV, "")
    return s.encode("utf-8") if s and s.strip() else None


def _now() -> int:
    return int(time.time())


# ── توکنِ stateless HMAC برای کارتِ مالی (بایندِ کاملِ effect) ───────────────────
def mint_money_token(*, effect_id, content_hash, action_kind, target_ref, amount, owner, exp):
    sec = _secret()
    if sec is None or owner in (None, ""):
        return None
    canon = f"mc1|{effect_id}|{content_hash}|{action_kind}|{target_ref}|{float(amount):.6f}|{owner}|{int(exp)}"
    sig = hmac.new(sec, canon.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"mc1.{hashlib.sha256(str(effect_id).encode()).hexdigest()[:12]}.{int(exp):010d}.{sig}"


def verify_money_token(token, *, effect_id, content_hash, action_kind, target_ref,
                       amount, owner, now=None) -> "tuple[bool,str]":
    sec = _secret()
    if sec is None:
        return (False, "no-secret")
    parts = str(token or "").split(".")
    if len(parts) != 4 or parts[0] != "mc1":
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


def _dedup_marker(state_dir, key: str) -> bool:
    """dedupِ durable بینِ بوت‌ها. True = تازه (باید بازسازی شود)، False = قبلاً بازسازی‌شده."""
    try:
        p = Path(state_dir) / "pulse" / "pending-rebuilt.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        seen = {}
        if p.exists():
            seen = json.loads(p.read_text("utf-8"))
        if key in seen:
            return False
        seen[key] = _now()
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(seen, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except Exception:  # noqa: BLE001 — بدونِ dedup هم بازسازی امن است (idempotency در لایهٔ پایین)
        return True


def rebuild_money_cards(*, channel, chrono_db_path, owner, state_dir=None, now=None,
                        halted=False) -> dict:
    """کارت‌های مالیِ معلق را از gated_effect (SoT) بازسازی کن. projection-only.
    خروجی: {rebuilt, skipped_terminal, halted}. fail-soft."""
    out = {"rebuilt": 0, "skipped_terminal": 0, "halted": bool(halted)}
    if str(os.environ.get(FLAG, "")) != "1":
        out["skipped"] = "flag-off"
        return out
    try:
        db = Path(chrono_db_path)
        if not db.exists():
            out["skipped"] = "no-chrono"
            return out
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = con.execute(
            "SELECT effect_id, kind, content_hash, action_kind, target_ref, expires_at, status, "
            "payload_ref FROM gated_effect WHERE status IN (?,?)", _MONEY_SAFE_STATES).fetchall()
        con.close()
        n = now if now is not None else _now()
        for (eid, kind, chash, akind, tref, exp_at, status, pref) in rows:
            # هرگز terminal/EXECUTING/RECONCILE — کوئری فقط pending/releasable گرفت، این گاردِ دوم است
            if status not in _MONEY_SAFE_STATES:
                out["skipped_terminal"] += 1
                continue
            exp = int(exp_at) if exp_at else (n + TTL_S)
            if exp <= n:                      # منقضی → دوباره نمایش نده
                continue
            key = f"money|{eid}|{status}"
            if not _dedup_marker(state_dir, key):
                continue                      # قبلاً در بوتِ قبلی بازسازی شده
            amount = 0.0
            try:
                if pref:
                    amount = float(json.loads(pref).get("amount_aud", 0.0))
            except Exception:  # noqa: BLE001
                amount = 0.0
            tok = mint_money_token(effect_id=eid, content_hash=chash or "", action_kind=akind or "",
                                   target_ref=tref or "", amount=amount, owner=owner, exp=exp)
            # projection: کارت را در _pending بنویس (کانالِ نو RAM-خالی است) — بایندِ کامل
            meta = {"amount_aud": amount, "token": tok, "status": "pending",
                    "content_hash": chash, "action_kind": akind, "target_ref": tref,
                    "effect_id": eid, "expires_at": exp, "rebuilt": True}
            try:
                with getattr(channel, "_lk", _NullLock()):
                    channel._pending[str(eid)] = meta   # noqa: SLF001 — projection rebuild
            except Exception:  # noqa: BLE001
                channel._pending[str(eid)] = meta       # noqa: SLF001
            # زیرِ HALT فقط metadata؛ ارسالِ کارت اختیاری و بدونِ settle
            if not halted and hasattr(channel, "send_text"):
                try:
                    channel.send_text(f"🔁 کارتِ تأییدِ معلق بازسازی شد (effect {str(eid)[:16]}, "
                                      f"AU${amount:.2f}) — تصمیم همچنان human-gated.")
                except Exception:  # noqa: BLE001
                    pass
            out["rebuilt"] += 1
        return out
    except Exception as e:  # noqa: BLE001 — بازسازی هرگز بوت را نمی‌کشد
        out["skipped"] = f"error:{type(e).__name__}"
        return out


def rebuild_rfc_cards(*, channel, rfcs_path, state_dir=None, now=None) -> dict:
    """کارت‌های RFCِ submitted/unconsumed را از rfcs.json (SoT) بازسازی کن.
    denied/merged/consumed هرگز دوباره نمی‌آیند. verdictِ پایدار = exactly-once across restart."""
    out = {"rebuilt": 0, "skipped_decided": 0}
    if str(os.environ.get(FLAG, "")) != "1":
        out["skipped"] = "flag-off"
        return out
    try:
        p = Path(rfcs_path)
        if not p.exists():
            out["skipped"] = "no-rfcs"
            return out
        doc = json.loads(p.read_text("utf-8"))
        rfcs = doc.get("rfcs", []) if isinstance(doc, dict) else doc
        if isinstance(rfcs, dict):
            rfcs = [{"rfc_id": k, **(v if isinstance(v, dict) else {})} for k, v in rfcs.items()]
        # verdictِ پایدار (exactly-once): rfc_idهایی که قبلاً رأی خورده‌اند دوباره نمی‌آیند
        consumed = _load_durable_rfc_verdicts(state_dir)
        for r in rfcs:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("rfc_id") or r.get("id") or "")
            st = str(r.get("status") or "")
            if not rid:
                continue
            if st not in _RFC_SAFE_STATES or rid in consumed:
                out["skipped_decided"] += 1
                continue
            if not _dedup_marker(state_dir, f"rfc|{rid}"):
                continue
            summary = str(r.get("bottleneck") or r.get("fix") or r.get("summary") or "RFC")[:200]
            try:
                if hasattr(channel, "rfc_card"):
                    channel.rfc_card(rid, summary)      # همان مسیرِ کارتِ RFC (توکنِ تازه)
                    out["rebuilt"] += 1
            except Exception:  # noqa: BLE001
                pass
        return out
    except Exception as e:  # noqa: BLE001
        out["skipped"] = f"error:{type(e).__name__}"
        return out


def _rfc_verdict_path(state_dir):
    return Path(state_dir) / "doctor" / "rfc-verdicts.jsonl"


def _load_durable_rfc_verdicts(state_dir) -> set:
    """rfc_idهایی که رأیِ پایدار خورده‌اند (exactly-once across restart)."""
    if state_dir is None:
        return set()
    p = _rfc_verdict_path(state_dir)
    out = set()
    if p.exists():
        for ln in p.read_text("utf-8").splitlines():
            try:
                out.add(json.loads(ln).get("rfc_id"))
            except ValueError:
                pass
    return out


def persist_rfc_verdict(*, state_dir, rfc_id, verdict) -> bool:
    """رأیِ RFC را durable کن (append-only) تا بعد از restart دوبار مصرف/بازسازی نشود."""
    try:
        p = _rfc_verdict_path(state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"rfc_id": str(rfc_id), "verdict": str(verdict),
                                "ts": _now()}, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
