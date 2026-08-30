#!/usr/bin/env python3
"""leg_cultivate.py — متابولیسمِ دادهٔ $0 برای همهٔ پاها (تعمیمِ الگوی lead_sense، 2026-07-16).

الگوی SENSE→DIGEST که برای لید ساخته شد (lead_sense.py) اینجا برای هر پای بیزنسی
عمومی می‌شود: هر پا یک صندوقِ فایل دارد — `state/legs/<leg>-inbox/*.json` — هر فایل
یک dict (خوراکِ producer: ایمیل، هاروستر، دستِ مالک، cron). cultivate(leg) صندوق را
هضم می‌کند و یک digestِ فشرده به وضعیت/آگاهیِ همان پا برمی‌گرداند.

قواعد (قانونِ اساسی — عینِ lead_sense):
  - هرگز حذف نمی‌کنیم؛ فقط انتقال: پردازش‌شده → `processed/` + سایدکارِ نتیجه؛
    JSONِ خراب → `rejected/` + سایدکارِ دلیل.
  - idempotent: هَشِ محتواییِ کاندید در `processed/_seen.json` — آیتمِ تکراری
    دوباره هضم نمی‌شود (الگوی dedupِ message_id تلگرام).
  - مسیرها در زمانِ فراخوانی از opslib خوانده می‌شوند (ایزولاسیونِ تستِ env-first).
  - بدونِ PII-echo: از محتوای آیتم فقط فیلدهای اعلانیِ producer (label/kind/summary)
    کوتاه‌شده گزارش می‌شوند، هرگز مقدار/نام/عددِ مالی.

پل‌های خاصِ پا (فقط ADD، read-only):
  - mining: سن/اندازهٔ منبعِ ماشینیِ واقعی (coordinator/data/decisions.jsonl — فقط stat،
    شمارشِ خط فقط برای فایلِ کوچک؛ هرگز محتوای تصمیم echo نمی‌شود).
  - ziman: پلِ کاتالوگ (همان ziman-catalog.jsonِ برنامهٔ ۸ — شمارشِ محصول/خانواده + سن).

خروجیِ دکتر: cultivate_all یک گزارشِ فشرده در `state/legs/cultivation-report.json`
می‌نویسد (اتمیک) — doctor.mine آن را (اگر تازه باشد) به‌عنوانِ کاندیدِ گلوگاهِ
«پای گرسنه/منبعِ راکد» می‌خواند. propose-only؛ هیچ اتونومیِ نو.

stdlib-فقط؛ صفر شبکه؛ صفر effector؛ fail-soft همه‌جا.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

try:
    from leg_freshness import age_days
except ImportError:                                       # fail-soft: سنِ نامعلوم → null
    def age_days(_p):  # type: ignore[misc]
        return None

# پاهایی که متابولیسمِ داده دارند (lead صندوقِ خودش را در lead_sense دارد — تکرار نمی‌کنیم)
CULTIVATED_LEGS = ("mining", "crypto", "accounting", "knowledge", "ziman")

# آستانه‌ها (env-قابل‌تنظیم؛ پیش‌فرض‌های محافظه‌کار)
STARVED_AFTER_H_DEFAULT = 72.0      # پا «گرسنه» = این‌قدر ساعت هیچ خوراکی هضم نشده
SOURCE_STALE_DAYS_DEFAULT = 30.0    # منبعِ پل‌شده (mining/ziman) «راکد» = این‌قدر روز کهنه


# ─── مسیرها (call-time تا OPS_DIR تستی اثر کند — عینِ lead_sense) ────────────────
def _legs_state() -> Path:
    return opslib.STATE_DIR / "legs"


def _inbox(leg: str) -> Path:
    return _legs_state() / f"{leg}-inbox"


def _processed(leg: str) -> Path:
    return _inbox(leg) / "processed"


def _rejected(leg: str) -> Path:
    return _inbox(leg) / "rejected"


def _seen_index(leg: str) -> Path:
    return _processed(leg) / "_seen.json"


def _last_fed_path() -> Path:
    return _legs_state() / "cultivation-last.json"


def report_path() -> Path:
    """مسیرِ گزارشِ فشرده برای دکتر — یک منبعِ حقیقتِ واحد (wiring/doctor/تست)."""
    return _legs_state() / "cultivation-report.json"


# ─── هویت و dedup ────────────────────────────────────────────────────────────────
def content_hash(item: dict) -> str:
    """هویتِ محتواییِ آیتم — JSONِ کانونیکالِ کلِ dict (کلیدمرتب). پایهٔ dedupِ عمومی."""
    try:
        canon = json.dumps(item, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        canon = repr(sorted(str(k) for k in item))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]


def _load_seen(leg: str) -> set:
    try:
        return set(json.loads(_seen_index(leg).read_text("utf-8")))
    except (OSError, ValueError):
        return set()


def _save_seen(leg: str, seen: set) -> None:
    try:
        _processed(leg).mkdir(parents=True, exist_ok=True)
        tmp = _seen_index(leg).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=0), "utf-8")
        os.replace(tmp, _seen_index(leg))
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: نبودِ ایندکس فقط dedup را ضعیف می‌کند، نه beat را


def seen_before(leg: str, item: dict) -> bool:
    return content_hash(item) in _load_seen(leg)


# ─── SENSE: خواندنِ صندوق ────────────────────────────────────────────────────────
def read_inbox(leg: str, limit: int | None = None) -> list:
    """آیتم‌های معتبرِ صندوقِ یک پا، مرتب به نام (قطعی). JSONِ خراب/غیرdict →
    rejected/ + سایدکارِ دلیل. فقط فایل‌های سطحِ اولِ inbox (نه processed/rejected)."""
    box = _inbox(leg)
    if not box.is_dir():
        return []
    out: list = []
    for p in sorted(box.glob("*.json")):
        try:
            d = json.loads(p.read_text("utf-8"))
            if not isinstance(d, dict) or not d:
                raise ValueError("item must be a non-empty dict")
            out.append((p, d))
        except (OSError, ValueError) as e:
            _move_with_sidecar(p, _rejected(leg), {"error": f"{type(e).__name__}: {e}"})
        if limit is not None and len(out) >= limit:
            break
    return out


def mark_processed(leg: str, path: Path, item: dict, result: dict) -> None:
    """آیتم را به processed/ منتقل کن + سایدکارِ نتیجه + ثبتِ هش در dedup."""
    seen = _load_seen(leg)
    seen.add(content_hash(item))
    _save_seen(leg, seen)
    _move_with_sidecar(path, _processed(leg), result)


def _move_with_sidecar(path: Path, dest_dir: Path, result: dict) -> None:
    """انتقالِ اتمیک (نه حذف) + سایدکارِ `<name>.result.json` (fail-soft) — عینِ lead_sense."""
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


# ─── DIGEST: خلاصهٔ بی‌PII ───────────────────────────────────────────────────────
def _summarize(item: dict) -> dict:
    """خلاصهٔ فشردهٔ یک آیتم — فقط فیلدهای اعلانیِ producer (label/kind/summary،
    کوتاه‌شده) + تعدادِ کلیدها. هرگز مقدار/نام/عددِ مالی echo نمی‌شود (خطِ قرمزِ
    accounting و ingest_raw)."""
    label = str(item.get("label") or item.get("kind") or item.get("summary") or "")[:80]
    return {"label": label, "n_keys": len(item)}


# ─── پل‌های خاصِ پا (فقط ADD، read-only، fail-soft) ─────────────────────────────
def _source_pulse_age(leg: str) -> float | None:
    """سنِ سایدکارِ تازگی (leg_feed) — additive؛ نبود → None."""
    try:
        p = _legs_state() / f"{leg}-source-pulse.json"
        return age_days(p)
    except Exception:  # noqa: BLE001
        return None


def _enrich_mining() -> dict:
    """پلِ منبعِ ماشینیِ واقعیِ Mining: coordinator/data/decisions.jsonl — read-only.
    فقط stat (سن/اندازه) + شمارشِ خط برای فایلِ کوچک (<2MB). صفر echo از محتوا.
    اگر leg_feed pulse تازه نوشته باشد، سنِ مؤثر = min(منبع، pulse)."""
    out: dict = {"source": "coordinator/data/decisions.jsonl"}
    try:
        import mining_leg  # noqa: WPS433 — lazy؛ مسیرِ تأییدشده همان‌جا نگه‌داری می‌شود
        p = Path(mining_leg.DECISIONS_PATH)
        out["source_exists"] = p.exists()
        if p.exists():
            a = age_days(p)
            out["source_age_days_raw"] = round(a, 1) if a is not None else None
            out["source_age_days"] = out["source_age_days_raw"]
            size = p.stat().st_size
            out["source_bytes"] = size
            if size <= 2_000_000:   # شمارشِ خط فقط برای فایلِ کوچک (سقفِ هزینهٔ IO)
                with p.open("rb") as f:
                    out["source_lines"] = sum(1 for _ in f)
        pa = _source_pulse_age("mining")
        if pa is not None:
            out["source_pulse_age_days"] = round(pa, 1)
            if out.get("source_age_days") is None:
                out["source_age_days"] = round(pa, 1)
            else:
                out["source_age_days"] = round(min(float(out["source_age_days"]), pa), 1)
    except Exception as e:  # noqa: BLE001 — پل هرگز cultivate را نمی‌کشد
        out["source_error"] = type(e).__name__
    return out


def _enrich_ziman() -> dict:
    """پلِ کاتالوگِ زیمان (برنامهٔ ۸ — همان منبعِ حقیقتِ ziman_leg): شمارشِ محصول/
    خانواده + سنِ فایل. read-only، utf-8-sig (فایلِ واقعی BOM دارد)، fail-soft.
    pulse تازگی (leg_feed) سنِ مؤثر را پایین می‌آورد بدون mutate کاتالوگ."""
    out: dict = {}
    try:
        import ziman_leg  # noqa: WPS433 — lazy؛ مسیرِ کاتالوگ همان ثابتِ پلِ برنامهٔ ۸
        p = Path(opslib.ORG_ROOT) / ziman_leg.ZIMAN_CATALOG_NOTE
        out["catalog"] = str(ziman_leg.ZIMAN_CATALOG_NOTE)
        if not p.exists():
            out["catalog_exists"] = False
            return out
        out["catalog_exists"] = True
        a = age_days(p)
        out["catalog_age_days_raw"] = round(a, 1) if a is not None else None
        out["catalog_age_days"] = out["catalog_age_days_raw"]
        data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        prods = data.get("products") if isinstance(data, dict) else None
        if isinstance(prods, list):
            out["catalog_products"] = len(prods)
            fams = {str(pr.get("family") or "UNKNOWN")
                    for pr in prods if isinstance(pr, dict)}
            out["catalog_families"] = len(fams)
        pa = _source_pulse_age("ziman")
        if pa is not None:
            out["catalog_pulse_age_days"] = round(pa, 1)
            if out.get("catalog_age_days") is None:
                out["catalog_age_days"] = round(pa, 1)
            else:
                out["catalog_age_days"] = round(min(float(out["catalog_age_days"]), pa), 1)
    except Exception as e:  # noqa: BLE001 — پل هرگز cultivate را نمی‌کشد
        out["catalog_error"] = type(e).__name__
    return out


_ENRICHERS = {"mining": _enrich_mining, "ziman": _enrich_ziman}


# ─── حافظهٔ «آخرین خوراک» (starvation tracking، اتمیک) ──────────────────────────
def _load_last_fed() -> dict:
    try:
        d = json.loads(_last_fed_path().read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_last_fed(d: dict) -> None:
    try:
        _last_fed_path().parent.mkdir(parents=True, exist_ok=True)
        tmp = _last_fed_path().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, _last_fed_path())
    except (OSError, TypeError, ValueError):
        pass   # fail-soft


# ─── cultivate — هضمِ صندوقِ یک پا ──────────────────────────────────────────────
def cultivate(leg: str, limit: int | None = None) -> dict:
    """یک دورِ SENSE→DIGEST برای یک پا. هرگز crash نمی‌کند (fail-soft).
    خروجی: {leg, sensed, digested, duplicates, pending, starved, last_fed_at, notes}
    + کلیدهای پلِ خاصِ پا (mining/ziman) — فقط ADD، هیچ کلیدِ موجودی عوض نمی‌شود."""
    items = read_inbox(leg, limit=limit)
    digested = dups = 0
    notes: list = []
    for path, item in items:
        if seen_before(leg, item):
            mark_processed(leg, path, item, {"duplicate": True})
            dups += 1
            continue
        summary = _summarize(item)
        mark_processed(leg, path, item, {"digested": True, "summary": summary})
        digested += 1
        if len(notes) < 5:
            notes.append(summary)
    # pending = آنچه بعد از سقف در صندوق ماند (خوراکِ beatِ بعدی)
    try:
        pending = len([p for p in _inbox(leg).glob("*.json")]) if _inbox(leg).is_dir() else 0
    except OSError:
        pending = 0
    # starvation: آخرین باری که این پا واقعاً خوراک هضم کرد
    last_fed = _load_last_fed()
    now = time.time()
    if digested > 0:
        last_fed[leg] = {"ts": now, "at": opslib.now_iso()}
        _save_last_fed(last_fed)
    rec = last_fed.get(leg) or {}
    last_ts = rec.get("ts") if isinstance(rec, dict) else None
    starved_after_h = float(os.environ.get("LEG_STARVED_AFTER_H",
                                           str(STARVED_AFTER_H_DEFAULT)))
    starved = (digested == 0 and pending == 0
               and (not isinstance(last_ts, (int, float))
                    or (now - last_ts) > starved_after_h * 3600.0))
    out = {"leg": leg, "sensed": len(items), "digested": digested,
           "duplicates": dups, "pending": pending, "starved": starved,
           "last_fed_at": rec.get("at") if isinstance(rec, dict) else None,
           "notes": notes}
    enrich = _ENRICHERS.get(leg)
    if enrich is not None:
        try:
            out.update(enrich())
        except Exception as e:  # noqa: BLE001 — پل هرگز digest را نمی‌کشد
            out["enrich_error"] = type(e).__name__
    # stale-source: منبعِ پل‌شده کهنه است (فقط وقتی پل سن گزارش کرد)
    stale_days = float(os.environ.get("LEG_SOURCE_STALE_DAYS",
                                      str(SOURCE_STALE_DAYS_DEFAULT)))
    src_age = out.get("source_age_days")
    cat_age = out.get("catalog_age_days")
    ages = [a for a in (src_age, cat_age) if isinstance(a, (int, float))]
    out["stale_source"] = bool(ages and max(ages) > stale_days)
    return out


def cultivate_all(limit_per_leg: int | None = 10, write_report: bool = True) -> dict:
    """همهٔ پاهای CULTIVATED_LEGS را هضم کن + گزارشِ فشردهٔ دکتر را اتمیک بنویس.
    خروجی: {"legs": {name: digest}, "starved_legs": [...], "stale_legs": [...]}.
    fail-soft: خطای یک پا بقیه را نمی‌کشد."""
    legs: dict = {}
    for name in CULTIVATED_LEGS:
        try:
            legs[name] = cultivate(name, limit=limit_per_leg)
        except Exception as e:  # noqa: BLE001 — یک پا نباید بقیه را بکشد
            legs[name] = {"leg": name, "error": f"{type(e).__name__}: {e}"}
    starved = sorted(n for n, d in legs.items() if d.get("starved"))
    stale = sorted(n for n, d in legs.items() if d.get("stale_source"))
    report = {"schema": "cultivation-report.v1", "ts": opslib.now_iso(),
              "legs": legs, "starved_legs": starved, "stale_legs": stale}
    if write_report:
        try:
            rp = report_path()
            rp.parent.mkdir(parents=True, exist_ok=True)
            tmp = rp.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, rp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: گزارشِ دکتر اختیاری است، beat را نمی‌کشد
    return report


if __name__ == "__main__":
    print(json.dumps(cultivate_all(write_report=False), ensure_ascii=False, indent=2))
