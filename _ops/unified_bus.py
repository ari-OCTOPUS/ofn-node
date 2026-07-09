#!/usr/bin/env python3
"""unified_bus.py — Phase 5 · S-3: پلِ همگراییِ additive به یک ارگانیسمِ واحد.

UnifiedArchitecture L0: «one substrate, two views» — business events + causal ledger.
genome ledger (LANGAR) = substrate ابدی (append-only، hash-chain، age_tick).
chrono.db = runtime state (پایا در طولِ اجرا، reconstructable از ledger).
این دو رقیب نیستند — دو نما از یک سابستریت‌اند (همان تصمیمِ UnifiedArchitecture).

این پل:
  publish(event_type, payload, actor, is_human) → یک رویداد هم‌زمان به:
    ۱) genome ledger (LANGAR — ماندگار، age_tick در صورتِ is_human)
    ۲) chrono checkpoint (runtime — سریع، قابلِ replay)
  برعکسِ دو نویسندهٔ مستقل، این یک نویسندهٔ یکپارچه است = همگرایی بدونِ delete.

age_tick = فلشِ مشترک: همهٔ legs/doctor/telegram از همین publish می‌گذرند. راه‌های
قدیمی (ledger.append مستقیم در ماژول‌های قدیمی) deprecated نه deleted — additive.

NON-DESTRUCTIVE (طبقِ قانون): هیچ رقیبی حذف نمی‌شود. genome/agents/doctor.py قدیمی
باقی می‌ماند. این پل فقط یک مسیرِ توصیه‌شدهٔ جدید اضافه می‌کند. مهاجرتِ تدریجی،
نه big-bang.

additive؛ stdlib-only؛ $0 آفلاین. ledger/chrono قابل‌تزریق (تست).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent              # _ops
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402


class UnifiedBus:
    """پلِ همگرایی: publish → genome ledger (LANGAR) + chrono checkpoint.
    یک نویسنده، دو نما. additive — مسیرهای قدیمی دست‌نخورده.

   genome ledger = source of truth (ابدی). chrono = runtime cache (reconstructable).
    اگر ledger نباشد → fail-closed (هیچ publish). اگر chrono نباشد → ledger-only (fail-soft)."""

    def __init__(self, ledger=None, db=None, note_fn=None):
        self._ledger = ledger                          # genome Ledger instance
        self._db = db                                  # chrono ChronoDB instance
        # note_fn قابل‌تزریق (opslib.ledger_note) برای audit log جدا
        self._note = note_fn or _default_note
        # W-2: subscribers برای advisory signals (یک bus)
        self._subscribers: list = []   # list of (event_type_filter|None, callback)

    def subscribe(self, callback, event_type: str | None = None) -> None:
        """ثبتِ مشترک. callback(event_dict). event_type=None = همه.
        مشترک‌ها فقط advisory می‌بینند — هیچ‌کدام settle/effect نمی‌کنند."""
        self._subscribers.append((event_type, callback))

    def _notify(self, event: dict) -> None:
        """اعلانِ رویداد به مشترک‌ها. fail-soft: مشترکِ خراب bus را نمی‌کشد."""
        etype = event.get("type", "")
        for filt, cb in self._subscribers:
            if filt is None or filt == etype:
                try:
                    cb(event)
                except Exception:  # noqa: BLE001 — مشترکِ خراب
                    pass

    def _lg(self):
        return self._ledger or opslib.genome_ledger()

    def publish(self, event_type: str, payload: dict, actor: str = "system",
                is_human: bool = False, beat: bool = False) -> dict:
        """یک رویداد را هم‌زمان به genome ledger + chrono checkpoint بفرست.
        is_human=True → age_tick +۱ (human-append، TINV-3).
        beat=True → heartbeat age_tick (heart-driven، v0.4.6).
        خروجی: entry از ledger (شامل hash، age_tick).
        fail-closed: اگر ledger بنویسد ولی chrono نه → باز هم entry برمی‌گردد (chrono = cache)."""
        if not isinstance(payload, dict):
            raise TypeError("payload must be dict")
        lg = self._lg()
        # ۱) genome ledger = source of truth (اولین، همیشه)
        entry = lg.append(event_type, payload, actor=actor,
                          is_human=is_human, beat=beat)
        # ۲) chrono checkpoint (runtime، fail-soft)
        if self._db is not None:
            try:
                self._checkpoint(entry)
            except Exception:  # noqa: BLE001 — chrono نباید publish را بکشد
                pass
        # ۳) audit log
        try:
            self._note("UNIFIED_PUBLISH", {"event_type": event_type, "actor": actor,
                                            "is_human": is_human,
                                            "hash": entry.get("hash", "") if isinstance(entry, dict) else ""})
        except Exception:  # noqa: BLE001
            pass
        # ۴) W-2: notify subscribers (advisory — هیچ‌کدام settle نمی‌کنند)
        if isinstance(entry, dict):
            self._notify(entry)
        return entry

    def _checkpoint(self, entry: dict) -> None:
        """checkpointِ سبک در chrono.db — delegate به checkpoint.checkpoint().
        P-S4: قراردادِ testable checkpoint.py را وصل می‌کند (نه inline DDL).
        entry باید dict با hash + type باشد. fail-soft: chrono نباشد → عبور (ledger source of truth)."""
        if not isinstance(entry, dict):
            return
        try:
            import checkpoint as _cp
            h = entry.get("hash", "")
            etype = entry.get("type", "UNKNOWN")
            # beat_id: آخرین beat_seq از chrono (اگر دسترس‌پذیر)، وگرنه hash→int
            beat_id = 0
            try:
                row = self._db.q("SELECT MAX(beat_seq) FROM heartbeat")
                if row and row[0][0] is not None:
                    beat_id = int(row[0][0])
            except Exception:  # noqa: BLE001
                pass
            if beat_id == 0:
                # fallback: hash را به int تبدیل کن (سطحِ bus، بدونِ heartbeat)
                beat_id = abs(hash(h)) % (2**31) if h else 0
            _cp.checkpoint(beat=beat_id, hlc=(0, 0), ledger_hash=h,
                           db=self._db, snapshot={"type": etype,
                                                  "is_human": entry.get("is_human", 0)})
        except Exception:  # noqa: BLE001 — chrono checkpoint fail-soft (ledger source of truth)
            pass

    def replay(self, from_hash: str = "", to_hash: str = "",
               event_type: str | None = None) -> list[dict]:
        """بازپخشِ رویدادها از ledger (source of truth). chrono.db = cache فقط.
        اگر from/to باشند، بازه؛ اگر event_type باشد، فیلتر.
        این S-4 replay است — همیشه از ledger می‌آید، نه از chrono (reconstructable)."""
        lg = self._lg()
        out = []
        in_range = (not from_hash)
        for rec in lg.filter(event_type=event_type):
            h = rec.get("hash", "")
            if from_hash and h == from_hash:
                in_range = True
            if in_range:
                out.append(rec)
            if to_hash and h == to_hash:
                break
        return out


def _default_note(subtype: str, payload: dict, actor: str = "unified-bus") -> None:
    try:
        opslib.ledger_note(subtype, payload, actor=actor)
    except Exception:  # noqa: BLE001
        pass
