#!/usr/bin/env python3
"""lead_sense.py — آداپترِ SENSE صندوقِ لید (مرحلهٔ ۲ نقشهٔ لید، 2026-07-15).

منبعِ کاندیدای لید = فایل‌های JSON در `state/legs/lead-inbox/` — هر فایل یک dict
(همان شکلِ lead_scorer: حداقل `description`؛ اختیاری address/cost_of_development/
lat/lng/applicant/url/source/expected_aud/day). هر تولیدکننده‌ای (ایمیلِ مرحلهٔ ۳،
هاروسترِ بیرونی، حتی دستِ مالک) می‌تواند فایل بیندازد — جداسازیِ کشف از تیک.

قواعد (قانونِ اساسی):
  - هرگز حذف نمی‌کنیم؛ فقط انتقال: پردازش‌شده → `processed/` + سایدکارِ نتیجه؛
    JSONِ خراب → `rejected/` + سایدکارِ دلیل.
  - idempotent: هَشِ محتواییِ (description+address) در `processed/_seen.json` —
    کاندیدِ تکراری دوباره propose نمی‌شود (الگوی dedupِ message_id تلگرام).
  - مسیرها در زمانِ فراخوانی از opslib خوانده می‌شوند (ایزولاسیونِ تستِ env-first).

stdlib-فقط؛ صفر شبکه؛ صفر effector.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402


def _inbox() -> Path:
    """مسیرِ صندوق — در call-time تا OPS_DIR تستی اثر کند."""
    return opslib.STATE_DIR / "legs" / "lead-inbox"


def _processed() -> Path:
    return _inbox() / "processed"


def _rejected() -> Path:
    return _inbox() / "rejected"


def _seen_index() -> Path:
    return _processed() / "_seen.json"


def content_hash(lead: dict) -> str:
    """هویتِ محتواییِ کاندید — description+address (lowercase). پایهٔ dedup."""
    key = (str(lead.get("description", "")).strip().lower() + "\0"
           + str(lead.get("address", "")).strip().lower())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _load_seen() -> set[str]:
    try:
        return set(json.loads(_seen_index().read_text("utf-8")))
    except (OSError, ValueError):
        return set()


def _save_seen(seen: set[str]) -> None:
    try:
        _processed().mkdir(parents=True, exist_ok=True)
        tmp = _seen_index().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=0), "utf-8")
        os.replace(tmp, _seen_index())
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: نبودِ ایندکس فقط dedup را ضعیف می‌کند، نه beat را


def seen_before(lead: dict) -> bool:
    return content_hash(lead) in _load_seen()


def _flag_frozen_inbox_lead(p) -> None:
    """یک لیدِ گیرافتاده در inboxِ FROZEN را **دیدنی** کن (throttle‌شده، یک‌بار per فایل).

    نه reject می‌کند نه move — فقط سکوت را می‌شکند. throttle لازم است چون این تابع در هر
    beat صدا زده می‌شود و آلارم به تلگرامِ مالک می‌رود؛ کلید per-filename است تا لیدِ
    **نو** هرگز خفه نشود. fail-soft کامل: هر خطا → سکوتِ قبلی، هرگز beat را نمی‌کشد."""
    try:
        import opslib as _ol   # noqa: WPS433 — lazy، صفر وابستگیِ سخت
        _thr = getattr(_ol, "alert_throttled", None)
        _msg = (f"لیدِ گیرافتاده در inboxِ FROZEN: {p.name} — "
                "lead_sense آن را نمی‌خواند (schemaِ قدیمیِ LD-*). "
                "برای ورود به لولهٔ امتیازدهی، به‌شکلِ canonical دوباره ثبتش کن.")
        if callable(_thr):
            _thr([_msg], key=f"frozen-inbox:{p.name}", window_s=86400.0)
        else:
            _ol.alert([_msg])
    except Exception:  # noqa: BLE001
        pass


def read_inbox(limit: int | None = None) -> list[tuple[Path, dict]]:
    """کاندیدهای معتبرِ صندوق، مرتب به نام (قطعی). JSONِ خراب → rejected/ + دلیل.
    فقط فایل‌های سطحِ اولِ inbox (نه processed/rejected)."""
    box = _inbox()
    if not box.is_dir():
        return []
    out: list[tuple[Path, dict]] = []
    for p in sorted(box.glob("*.json")):
        # گاردِ همگراییِ دو inbox (2026-07-21): فایل‌های inboxِ قدیمیِ FROZEN (`LD-*`، schemaِ
        # raw_text بدونِ description) و فایل‌های داخلی (`_*`) را نه بخوان و نه reject-move کن —
        # فقط رد شو. وگرنه چون هر دو inbox روی یک دایرکتوری‌اند، این‌جا آن‌ها را (به‌خاطرِ نبودِ
        # description) به rejected/ منتقل می‌کرد و lead_leg_inbox.get_lead دیگر پیدایشان نمی‌کرد.
        if p.name.startswith("_"):
            continue        # قالب/فایلِ داخلی — عمداً و بی‌صدا نادیده
        if p.name.startswith("LD-"):
            # 2026-07-25: این‌جا قبلاً یک `continue`ِ خالص بود و نتیجه‌اش این: لیدی که مالک
            # در تلگرام تایپ می‌کرد به inboxِ FROZEN می‌رفت (`LD-*.json` با schemaِ raw_text)
            # و این خواننده **بی‌صدا** ردش می‌کرد — نه خطا، نه امتیاز، نه کارت. برای
            # کسب‌وکاری که اولویتش «گرفتنِ لید» است، گم‌شدنِ بی‌صدای لید بدترین باگ است.
            # گاردِ اصلی حفظ می‌شود (هرگز به rejected/ منتقل نمی‌شود، چون
            # lead_leg_inbox.get_lead باید همان‌جا پیدایش کند) ولی سکوت شکسته می‌شود.
            _flag_frozen_inbox_lead(p)
            continue
        try:
            d = json.loads(p.read_text("utf-8"))
            if not isinstance(d, dict) or not str(d.get("description", "")).strip():
                raise ValueError("lead must be a dict with a non-empty description")
            out.append((p, d))
        except (OSError, ValueError) as e:
            _move_with_sidecar(p, _rejected(), {"error": f"{type(e).__name__}: {e}"})
        if limit is not None and len(out) >= limit:
            break
    return out


def mark_processed(path: Path, lead: dict, result: dict) -> None:
    """کاندید را به processed/ منتقل کن + سایدکارِ نتیجه + ثبتِ هش در dedup."""
    seen = _load_seen()
    seen.add(content_hash(lead))
    _save_seen(seen)
    _move_with_sidecar(path, _processed(), result)


def resolve_lead_path(lead_id: str) -> Path | None:
    """مسیرِ فایلِ دادهٔ یک lead_id — **تازه‌ترین** نسخهٔ موجود، یا None.

    قفلِ دوتایی (کشفِ ۲۰۲۶-۰۸-۰۳): `lead_pipeline.run()` همان beat ی که کارت
    صادر می‌شود `mark_processed` را صدا می‌زند — یعنی فایلِ `lead-inbox/<id>.json`
    به `processed/` منتقل می‌شود. دو مصرف‌کننده (`lead_effect_gate.bridge_from_inbox`،
    `outbound_worker._candidate_from_inbox`) که بعداً — وقتی مالک approve می‌کند —
    همان داده را می‌خواهند، مستقیماً مسیرِ `lead-inbox/` را می‌ساختند: چون فایل
    قبلاً منتقل شده بود، هر دو با `no_inbox_file`/`no-candidate` fail می‌شدند.

    اول `lead-inbox/<id>.json` (هنوز پردازش‌نشده). اگر نبود، بینِ نسخه‌های
    `processed/<id>.json` و `processed/<id>.N.json` (تصادمِ نامِ `_move_with_sidecar`)
    تازه‌ترین (mtime) برمی‌گردد — سایدکارهای `*.result.json` هرگز کاندید نیستند."""
    lid = str(lead_id or "").strip()
    if not lid:
        return None
    direct = _inbox() / f"{lid}.json"
    if direct.exists():
        return direct
    box = _processed()
    if not box.is_dir():
        return None
    hits = []
    for p in box.glob(f"{lid}*.json"):
        if p.name.endswith(".result.json"):
            continue
        stem = p.stem
        if stem == lid or (stem.startswith(lid + ".") and stem[len(lid) + 1:].isdigit()):
            hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0]


def _move_with_sidecar(path: Path, dest_dir: Path, result: dict) -> None:
    """انتقالِ اتمیک (نه حذف) + سایدکارِ `<name>.result.json` (fail-soft)."""
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if dest.exists():                       # تصادمِ نام → suffix عددی، نه بازنویسی
            i = 1
            while (dest_dir / f"{path.stem}.{i}{path.suffix}").exists():
                i += 1
            dest = dest_dir / f"{path.stem}.{i}{path.suffix}"
        os.replace(path, dest)
        side = dest.with_name(dest.name + ".result.json")
        side.write_text(json.dumps({**result, "processed_at": opslib.now_iso()},
                                   ensure_ascii=False, indent=2), "utf-8")
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: انتقالِ ناموفق فقط باعثِ retry در beatِ بعدی می‌شود
