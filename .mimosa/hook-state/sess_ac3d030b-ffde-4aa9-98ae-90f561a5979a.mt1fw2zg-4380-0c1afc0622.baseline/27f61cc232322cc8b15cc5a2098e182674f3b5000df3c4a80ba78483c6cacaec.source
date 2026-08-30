"""lifecycle_fold.py — «این تصمیم کجاست؟» یک تاشدگیِ خالص روی چرخهٔ عمرِ کارت.

گامِ ۲ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C1). ستونِ فقراتِ طرح.

چرا وجود دارد — یافتهٔ سنجیده‌شدهٔ ۲۰۲۶-۰۸-۰۳:

    کارت‌ها پیشنهاد می‌شوند، تحویل می‌شوند، مالک تصمیم می‌گیرد... و **هیچ‌کدام
    اثر نمی‌کنند**. روی درختِ زنده: هر ردیفِ `rfc_decision` در وضعیتِ
    `RECONCILE_REQUIRED` با `receipt_id=''` و `operation_key=NULL` نشسته بود.
    یعنی مسئله «مالک تصمیم نمی‌گیرد» نبود — مالک بارها تصمیم گرفت و لوله در
    پلهٔ **اثر** شکسته است.

    هیچ سطحی این را نشان نمی‌داد چون هیچ‌کس دو منبع را کنارِ هم نمی‌گذاشت:
    فایلِ کارت‌ها می‌گوید «تصمیم گرفته شد»، دفترِ حکم‌ها می‌گوید «اثر نکرد»، و
    تا امروز `load_rfc_verdicts` صفر صداکنندهٔ **بیرونی** داشت.

پنج مرحله، به‌علاوهٔ دو حالتِ خارج از مسیر:

    PROPOSED → DELIVERED → DECIDED → EFFECTED → MEASURED
    STALLED   تحویل شد ولی تصمیم نگرفت
    UNKNOWN   منبع غایب یا ناخوانا — هرگز صفر

ناوردی‌ها:

    ۱. **صفر نوشتن.** تاشدگیِ خالص نمی‌تواند از منابعش واگرا شود؛ نه رونوشت
       نگه می‌دارد نه persistence.
    ۲. **هر عددی که برمی‌گرداند از `provenance.stamp()` عبور می‌کند.** یک
       شمارشِ برهنه دقیقاً همان چیزی است که این طرح آمده حذفش کند.
    ۳. **منبعِ غایب ⇒ UNKNOWN، نه ۰.** یک ذخیرهٔ خالی و یک ذخیرهٔ ناخوانا دو
       چیزِ متفاوت‌اند و نباید یک‌شکل رندر شوند.
    ۴. **EFFECTED یعنی `state=APPLIED` **و** `receipt_id` ناتهی.** فقط APPLIED
       کافی نیست: قرارِ طرح این است که یک اثر بدونِ رسید، اثر نیست.

نکتهٔ ایزوله (درسِ ثبت‌شدهٔ ۰۸-۰۳): هر مسیرِ تحتِ آزمون باید `state_dir` صریح
بگیرد. ساختنِ بی‌آرگومان به ذخیرهٔ **زنده** می‌خورد.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import provenance as _prov   # noqa: E402

__all__ = ["Stage", "fold", "stalled_cards", "SOURCES"]

#: ریتمِ اعلام‌شدهٔ این تاشدگی. کارت‌ها رویدادمحورند نه per-beat؛ سنجشِ زنده
#: می‌گوید نویسنده تقریباً هر ۶ ساعت می‌نویسد، پس ۲۱۶۰۰ ثانیه.
CADENCE_S = 6 * 3600.0

# سقفِ فهرستِ راکدها. کارت‌ها ماه‌ها انباشته می‌شوند و یک فهرستِ بی‌سقف هم
# پاسخ را باد می‌کند هم صفحهٔ مالک را غیرقابلِ استفاده. بریده‌شدن در
# `stalled_list_truncated` **اعلام** می‌شود، نه بی‌صدا.
STALLED_LIST_CAP = 40

SOURCES = (
    "_ops/state/pulse/pending-cards.json",
    "_ops/state/doctor/rfc-verdicts.db::rfc_decision",
)


class Stage:
    PROPOSED = "PROPOSED"
    DELIVERED = "DELIVERED"
    DECIDED = "DECIDED"
    EFFECTED = "EFFECTED"
    MEASURED = "MEASURED"
    STALLED = "STALLED"
    UNKNOWN = "UNKNOWN"

    ALL = (PROPOSED, DELIVERED, DECIDED, EFFECTED, MEASURED, STALLED, UNKNOWN)


def _read_verdicts(state_dir, pcr):
    """پروجکشنِ حکم‌ها — **بدونِ باز کردنِ اتصالِ نوشتنی** روی دیتابیسِ پول.

    فیکسِ ۲۰۲۶-۰۸-۰۳. ادعای C1 «صفر نوشتن» بود، ولی مسیرِ ساده
    (`pcr.load_rfc_verdicts`) به `pcr._rfc_con()` می‌رسد که
    `mkdir(parents=True)` + `PRAGMA journal_mode=WAL` + `CREATE TABLE IF NOT
    EXISTS` می‌زند. روی دیتابیسِ موجود بی‌ضرر است، ولی یک **سطحِ خواندنی** که
    ممکن است به‌ازای هر درخواست صدا زده شود (مینی‌اپ، بریف) نباید اتصالِ نوشتنی
    روی ظرفِ نزدیکِ پول باز کند و فایل‌های `-wal`/`-shm` بسازد.

    دو لِینِ مستقل این را کشف کردند؛ تستِ ایزولهٔ خودم نگرفته بود چون فقط ثابت
    می‌کرد اجرا روی **فیکسچر** به state ِ زنده دست نمی‌زند — نه اینکه fold روی
    خودِ state ِ زنده چیزی نمی‌سازد. ادعا از سنجه بزرگ‌تر بود.

    اگر دیتابیس وجود دارد: اتصالِ `mode=ro`. اگر نه: هیچ — نبودِ دیتابیس یعنی
    هیچ حکمی ثبت نشده، نه اینکه باید ساخته شود. مسیرِ سازنده فقط با
    `allow_create=True` صدا زده می‌شود که هیچ مسیرِ خواندنی‌ای استفاده‌اش نمی‌کند.
    """
    db = Path(pcr._rfc_db_path(state_dir))
    if not db.exists():
        return {}
    try:
        import sqlite3   # noqa: PLC0415
        from urllib.parse import quote   # noqa: PLC0415
        # مسیرِ ویندوزی باید به شکلِ `file:///F:/...` بیاید. نسخهٔ اولِ این خط
        # `file:F:/...` می‌داد که sqlite ردش می‌کرد، استثنا می‌خورد، و fail-soft
        # بی‌صدا به مسیرِ نوشتنی برمی‌گشت — یعنی فیکس ظاهراً اعمال شده بود و در
        # عمل هیچ کاری نمی‌کرد. تستِ «هیچ فایلی ساخته نشود» گرفتش (`-wal`/`-shm`).
        uri = "file:///" + quote(str(db).replace("\\", "/")) + "?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=5.0)
        try:
            out = {}
            for rid, verdict, rev, state, receipt, opkey, uts in con.execute(
                    "SELECT rfc_id,verdict,revision,state,receipt_id,operation_key,"
                    "updated_ts FROM rfc_decision"):
                out[rid] = {"verdict": verdict, "revision": int(rev), "state": state,
                            "consumed": state in ("APPLIED", "REJECTED"),
                            "receipt_id": receipt or "", "operation_key": opkey or "",
                            "updated_ts": uts}
            return out
        finally:
            con.close()
    except Exception:   # noqa: BLE001
        # fail-soft: اگر read-only ممکن نبود، پروجکشنِ canonical را صدا بزن.
        # این تنها مسیری است که `load_rfc_verdicts` را نگه می‌دارد — قراردادِ
        # C1 و صداکنندهٔ تولیدی‌اش که تستِ AST قفلش کرده.
        return pcr.load_rfc_verdicts(state_dir)


def _stage_of(record, verdict):
    """مرحلهٔ یک کارت. `verdict` می‌تواند None باشد (در دفتر نیست)."""
    if not isinstance(record, dict):
        return Stage.UNKNOWN
    delivery = record.get("delivery")
    decision = record.get("decision")
    if delivery is None or decision is None:
        # کلیدِ غایب یعنی نمی‌دانیم، نه اینکه نرسیده. (همان تلهٔ پروبِ کور:
        # فیلترِ فیلدِ اشتباه صفرِ تمیز می‌داد.)
        return Stage.UNKNOWN
    if str(decision).upper() != "DECIDED":
        return Stage.STALLED if str(delivery).upper() == "SENT" else Stage.PROPOSED
    # تصمیم گرفته شده — حالا دفترِ حکم‌ها می‌گوید اثر کرد یا نه.
    if not isinstance(verdict, dict):
        return Stage.DECIDED
    state = str(verdict.get("state") or "").upper()
    receipt = str(verdict.get("receipt_id") or "")
    if state == "APPLIED" and receipt:
        return Stage.MEASURED if verdict.get("measured") else Stage.EFFECTED
    return Stage.DECIDED


def fold(state_dir, now=None, _pcr=None):
    """تاشدگیِ کاملِ چرخهٔ عمر. صفر نوشتن.

    `state_dir` اجباری است — پیش‌فرضِ ضمنی یعنی خوردن به ذخیرهٔ زنده.
    """
    if state_dir is None:
        raise ValueError("state_dir is required; an implicit default hits the live store")

    pcr = _pcr
    if pcr is None:
        import pending_card_recovery as pcr   # noqa: PLC0415

    store = pcr._load_store(state_dir)
    verdicts = _read_verdicts(state_dir, pcr)

    store_path = Path(state_dir) / "pulse" / "pending-cards.json"
    readable = store_path.exists()

    counts = {s: 0 for s in Stage.ALL}
    reconcile_required = 0
    oldest_stalled = None
    stalled = []

    for key, rec in (store or {}).items():
        verdict = None
        if isinstance(rec, dict):
            verdict = verdicts.get(rec.get("rfc_id") or "")
        st = _stage_of(rec, verdict)
        counts[st] += 1
        if isinstance(verdict, dict) and str(verdict.get("state") or "").upper() == "RECONCILE_REQUIRED":
            reconcile_required += 1
        if st == Stage.STALLED:
            created = _prov.parse_ts((rec or {}).get("created_ts"))
            stalled.append({"key": key, "rfc_id": (rec or {}).get("rfc_id"),
                            "created_ts": created,
                            "summary": ""})   # عمداً بدونِ متن — قاعدهٔ #۷
            if created is not None and (oldest_stalled is None or created < oldest_stalled):
                oldest_stalled = created

    total = len(store or {})
    # کارت‌ها یک‌بار تحویل می‌شوند و برنمی‌گردند: هرچه از PROPOSED گذشته
    # DELIVERED هم هست. شمارشِ تجمعی، نه انحصاری.
    delivered = sum(counts[s] for s in (Stage.STALLED, Stage.DECIDED,
                                        Stage.EFFECTED, Stage.MEASURED))
    decided = sum(counts[s] for s in (Stage.DECIDED, Stage.EFFECTED, Stage.MEASURED))
    effected = counts[Stage.EFFECTED] + counts[Stage.MEASURED]

    def num(value, cadence=CADENCE_S):
        if not readable:
            return _prov.stamp(None, "", None, cadence, now=now)
        return _prov.stamp(value, SOURCES[0], now if now is not None else _now(),
                           cadence, now=now)

    return {
        "sources": list(SOURCES),
        "readable": readable,
        "proposed": num(total),
        "delivered": num(delivered),
        "decided": num(decided),
        "effected": num(effected),
        "stalled": num(counts[Stage.STALLED]),
        "unknown": num(counts[Stage.UNKNOWN]),
        "reconcile_required": num(reconcile_required),
        "oldest_stalled_ts": oldest_stalled,
        "by_stage": dict(counts),
        # ⚠️ ۲۰۲۶-۰۸-۰۵: این فهرست از همان اول **ساخته می‌شد و برنمی‌گشت** —
        # روی زمین ریخته می‌شد. یعنی دقیقاً هویتی که مالک برای بیرون‌آوردنِ
        # کارت از رکود لازم دارد، محاسبه شده بود و دور ریخته می‌شد. حالا
        # برمی‌گردد و همچنان **بی‌متن** است (`summary` عمداً خالی، قاعدهٔ #۷):
        # رکوردِ کارت `nonce` و `token_sha256` دارد و هیچ‌کدام هرگز از این
        # مرز رد نمی‌شوند.
        # سقف صریح است و بریدنِ آن **اعلام** می‌شود؛ سقفِ بی‌صدا از «همه را
        # دیدی» غیرقابل‌تشخیص است.
        "stalled_list": stalled[:STALLED_LIST_CAP],
        "stalled_list_truncated": max(0, len(stalled) - STALLED_LIST_CAP),
    }


def _now():
    import time
    return time.time()


def stalled_cards(state_dir, now=None, _pcr=None):
    """شمار و قدیمی‌ترینِ کارت‌های راکد — بدونِ هیچ متنی از محتوایشان (قاعدهٔ #۷).

    عمداً **فقط** فایلِ کارت‌ها را می‌خواند و به دفترِ حکم‌ها دست نمی‌زند: «راکد»
    یعنی تحویل شد و تصمیم نگرفت، و این کاملاً از `pending-cards.json` درمی‌آید.
    `pcr._rfc_con()` روی هر باز شدن `mkdir` و `CREATE TABLE IF NOT EXISTS` و WAL
    می‌زند؛ یک پروب که هر چرخه می‌دود نباید آن هزینه و آن اثرِ جانبی را بدهد.

    برمی‌گرداند `(count, oldest_ts, total_records)`. `count = -1` یعنی UNKNOWN:
    ذخیره غایب/ناخوانا بود یا کلیدِ `decision` در هیچ رکوردی نبود — که با «صفر
    کارتِ راکد» یکی نیست.
    """
    pcr = _pcr
    if pcr is None:
        import pending_card_recovery as pcr   # noqa: PLC0415

    store_path = Path(state_dir) / "pulse" / "pending-cards.json"
    if not store_path.exists():
        return -1, None, 0
    store = pcr._load_store(state_dir) or {}
    rows = [r for r in store.values() if isinstance(r, dict)]
    if not rows:
        return 0, None, 0
    if not any("decision" in r for r in rows):
        # فیلد اصلاً وجود ندارد ⇒ UNKNOWN، نه صفر. همان تلهٔ predicate مرده.
        return -1, None, len(rows)

    count, oldest = 0, None
    for rec in rows:
        if _stage_of(rec, None) != Stage.STALLED:
            continue
        count += 1
        created = _prov.parse_ts(rec.get("created_ts"))
        if created is not None and (oldest is None or created < oldest):
            oldest = created
    return count, oldest, len(rows)
