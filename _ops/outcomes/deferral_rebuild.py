#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deferral_rebuild.py — GAP-3 (C2-C): کارتِ «بعداً» بعد از خواب برمی‌گردد.

مشکل (ممیزی B-03 / spec GAP3): کارتِ معوق فقط به‌صورتِ entryِ تصمیم‌نگرفته در RAMِ
`_proposal_cb` زنده بود → restart = ناپدید از UI. رویدادِ deferred در outcomes.db پایدار
است (پنجرهٔ A) — پس UI فقط projection است و باید در بوت **بازسازی** شود، نه اختراع.

قواعد (spec):
  - SoT: outcomes.db — deferredهایی که هنوز accepted/rejected نشده‌اند و منقضی نیستند.
  - ≤۳ کارت: هر کدام کارتِ کامل با توکنِ تازه (stateless اگر secret باشد).
  - >۳: **یک** پیامِ دایجست — هر پیشنهاد یک ردیفِ دکمه (ok/no/later) — نه طوفانِ پیام.
  - dedupe بینِ بوت‌ها durable است: مارکرِ idempotentِ per-pid در outcomes.db با کلیدِ
    `deliv-rebuild|<pid>` → هر کارتِ معوق حداکثر یک‌بار بازسازی می‌شود (ضدِطوفانِ spec تست ۳:
    «دو بوتِ پشت‌سرهم = یک rebuild»). توکنِ stateless durable است، پس کارتِ یک‌بار
    نشان‌داده‌شده تا زمانِ تصمیم قابلِ عمل می‌ماند. (پیش‌تر کلید به n_deferrals بود؛ چون
    رویدادِ deferred idempotency-dedup می‌شود n هرگز از ۱ بالاتر نمی‌رفت → شاخهٔ مرده، رفع شد.)
  - فلگ جدید نمی‌سازیم: پشتِ PROPOSAL_BUTTONS (در caller/wiring) + VERDICT_OUTCOME
    (نویسنده/خوانندهٔ outcomes.db — منبعِ واقعیِ داده؛ ثبتِ تصمیم در DECISION-LOG C2).
  - fail-soft: هیچ خطایی بوت را نمی‌کشد؛ DB غایب → skip بی‌صدا.
  - resolved/rejected هرگز دوباره ظاهر نمی‌شوند؛ منقضی‌ها rebuild نمی‌شوند ولی
    رویدادشان در DB می‌ماند (append-only).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

DEFER_TTL_ENV = "OCTOPUS_DEFER_TTL_S"
DEFAULT_DEFER_TTL_S = 7 * 24 * 3600      # یک هفته
FULL_CARD_MAX = 3                        # spec: بیشتر از این → دایجست
REBUILD_LIMIT = 20

_HERE = Path(__file__).resolve().parent


def _ttl_s() -> int:
    try:
        v = int(os.environ.get(DEFER_TTL_ENV, "") or DEFAULT_DEFER_TTL_S)
        return v if v > 0 else DEFAULT_DEFER_TTL_S
    except ValueError:
        return DEFAULT_DEFER_TTL_S


def _iso_age_s(iso: str, now: datetime) -> float:
    try:
        t = datetime.fromisoformat(str(iso))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return (now - t).total_seconds()
    except ValueError:
        return float("inf")   # timestamp خراب = منقضی فرض کن (fail-closed برای rebuild)


def pending_deferrals(store, *, now: "datetime | None" = None,
                      limit: int = REBUILD_LIMIT) -> "list[dict]":
    """کارت‌های معوقِ زنده از outcomes.db — جدیدترین اول.
    [{proposal_id, deferred_at, n_deferrals}] — decided/منقضی حذف."""
    now = now or datetime.now(timezone.utc)
    rows = store._conn.execute(   # noqa: SLF001 — projection read
        "SELECT proposal_id, MAX(recorded_at), COUNT(*) FROM outcomes "
        "WHERE event_type='deferred' AND proposal_id IS NOT NULL "
        "GROUP BY proposal_id ORDER BY MAX(recorded_at) DESC").fetchall()
    out = []
    ttl = _ttl_s()
    for pid, last_at, n in rows:
        if not pid:
            continue
        decided = store._conn.execute(   # noqa: SLF001
            "SELECT 1 FROM outcomes WHERE proposal_id=? "
            "AND event_type IN ('accepted-measurement','rejected') LIMIT 1",
            (pid,)).fetchone()
        if decided:
            continue
        if _iso_age_s(last_at, now) > ttl:
            continue
        out.append({"proposal_id": str(pid), "deferred_at": str(last_at),
                    "n_deferrals": int(n)})
        if len(out) >= limit:
            break
    return out


def _delivery_meta(store, pid: str) -> dict:
    """metaی تحویلِ ثبت‌شده برای pid (payloadِ رویدادِ delivered) — غایب → حداقلی."""
    import json
    row = store._conn.execute(   # noqa: SLF001
        "SELECT payload_json FROM outcomes WHERE proposal_id=? AND event_type='delivered' "
        "ORDER BY recorded_at DESC LIMIT 1", (str(pid),)).fetchone()
    payload = {}
    if row:
        try:
            payload = json.loads(row[0] or "{}")
        except ValueError:
            payload = {}
    meta = {k: payload.get(k) for k in ("proposal_id", "amount", "kind", "leg_id",
                                        "correlation_id", "mission_id", "lead_id")}
    meta["proposal_id"] = meta.get("proposal_id") or str(pid)
    meta["leg_id"] = meta.get("leg_id") or "unknown"
    return meta


def _rebuild_card_text(meta: dict, deferred_at: str) -> str:
    return ("📨 <b>کارتِ معوق — بازیابی بعد از خواب</b>\n"
            "──────────\n"
            f"🦾 پا: <code>{str(meta.get('leg_id', 'unknown'))[:80]}</code>\n"
            f"📌 نوع: <code>{str(meta.get('kind', 'unknown'))[:80]}</code>\n"
            f"🆔 id: <code>{str(meta.get('proposal_id', ''))[:120]}</code>\n"
            f"⏳ تعویق از: <code>{str(deferred_at)[:32]}</code>\n"
            "──────────\n"
            "<i>«بعداً» گفته بودی؛ کارت بعد از restart بازسازی شد. هیچ اثری settle نشده.</i>")


def _keyboard_row(token: str, label: str = "") -> list:
    tag = (label[:12] + " ") if label else ""
    return [{"text": f"✅ {tag}آره", "callback_data": f"prop:ok:{token}"},
            {"text": "❌ نه", "callback_data": f"prop:no:{token}"},
            {"text": "⏳ بعداً", "callback_data": f"prop:later:{token}"}]


def rebuild_deferred_cards(live_loop, channel, *, state_dir=None) -> dict:
    """بازسازیِ projectionِ کارت‌های معوق در بوت. fail-soft کامل — هرگز raise.
    خروجی: {rebuilt, digest, pending, skipped?}."""
    out = {"rebuilt": 0, "digest": False, "pending": 0}
    try:
        import sys
        for _p in (str(_HERE), str(_HERE.parent)):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        import proposal_registry as _pr   # noqa: WPS433
        if not _pr.flag_on():
            out["skipped"] = "flag-off"
            return out
        store = _pr._open_store(state_dir, create=False)   # noqa: SLF001
        if store is None:
            out["skipped"] = "no-db"
            return out
        try:
            pend = pending_deferrals(store)
            out["pending"] = len(pend)
            if not pend:
                return out
            # dedupe بینِ بوت‌ها: مارکرِ durable per (pid, n_deferrals)
            fresh = []
            for p in pend:
                marker_new = bool(store.record({
                    "correlation_id": "rebuild_" + p["proposal_id"][:56],
                    "proposal_id": p["proposal_id"], "event_type": "delivered",
                    "verdict": None, "value_aud_claimed": 0.0,
                    "idempotency_key": f"deliv-rebuild|{p['proposal_id']}",   # F2: per-pid, honest
                    "payload": {"rebuild": True, "n_deferrals": p["n_deferrals"]}}))
                if marker_new:
                    fresh.append(p)
            if not fresh:
                return out   # همهٔ کارت‌ها قبلاً در بوتِ قبلی بازسازی شده‌اند
            can_send = channel is not None and hasattr(channel, "send_text")
            metas = []
            for p in fresh:
                meta = _delivery_meta(store, p["proposal_id"])
                tok = None
                try:
                    tok = live_loop._mint_proposal_token(meta["proposal_id"])   # noqa: SLF001
                except Exception:  # noqa: BLE001
                    tok = None
                if tok is None:
                    tok = live_loop._proposal_token(meta["proposal_id"])        # noqa: SLF001
                live_loop._proposal_cb[tok] = meta                              # noqa: SLF001
                metas.append((p, meta, tok))
            if len(metas) <= FULL_CARD_MAX:
                for p, meta, tok in metas:
                    if can_send:
                        try:
                            channel.send_text(_rebuild_card_text(meta, p["deferred_at"]),
                                              reply_markup={"inline_keyboard":
                                                            [_keyboard_row(tok)]})
                        except TypeError:
                            channel.send_text(_rebuild_card_text(meta, p["deferred_at"]))
                    out["rebuilt"] += 1
            else:
                lines = [f"⏳ <b>{len(metas)} تصمیمِ معوق</b> بعد از خواب منتظرِ توست:"]
                kb = []
                for p, meta, tok in metas:
                    lines.append(f"• <code>{str(meta.get('kind', '?'))[:40]}</code> — "
                                 f"{str(meta.get('leg_id', '?'))[:40]}")
                    kb.append(_keyboard_row(tok, str(meta.get("kind", ""))[:12]))
                if can_send:
                    try:
                        channel.send_text("\n".join(lines),
                                          reply_markup={"inline_keyboard": kb})
                    except TypeError:
                        channel.send_text("\n".join(lines))
                out["rebuilt"] = len(metas)
                out["digest"] = True
            return out
        finally:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001 — بازسازی هرگز بوت را نمی‌کشد
        out["skipped"] = f"error: {type(e).__name__}"
        return out
