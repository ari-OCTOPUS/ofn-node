#!/usr/bin/env python3
"""sync_health.py — سلامتِ sync operations (M2): lag، drift، divergence، alert.

بازنشانه‌شده ۲۰۲۶-۰۸-۰۳ — گامِ ۹ ِ UNIFICATION-DESIGN-2026-08-03، جزءِ C16.

چرا بازنویسی شد (سنجشِ همان روز):

    این ماژول دقیقاً برای پاسخ به «آیا در sync است؟» ساخته شد و **هرگز یک
    موفقیت یا شکست ثبت نکرده**. هر دو ظرفش روی دیسک غایب‌اند:
    `_ops/state/sync/` و `_ops/state/sync-health.json`. سه هدفِ
    `_ops/sync_agent.py` (`studio_pf`, `cartographer`, `lead` — در
    `ensure_ids` و `_default_deps`) هرگز اجرا نشده‌اند.

    ولی `snapshot()` روی این غیاب یک سندِ **آرام** برمی‌گرداند:
    `sources={}` و `summary={"total":0,"ok":0,"warn":0,"err":0}`. صفرِ err و
    صفرِ warn دقیقاً همان‌طور رندر می‌شود که یک sync ِ سالم. یعنی غیاب خودش را
    به سبز لاندری می‌کرد.

قاعده‌ای که حالا اجرا می‌شود (بندِ ۱.۲ ِ طرح):

    **غیابِ ورودی ⇒ `UNKNOWN`، هرگز `0` و هرگز سبز.**

    و «نمی‌دانم» با «هیچ‌کدام» یکی نیست: هدفی که رکورد دارد و فقط شکست خورده،
    یک سیگنالِ **واقعی** است و `err` می‌ماند — وگرنه گارد به یک UNKNOWN ِ
    سراسری تبدیل می‌شود که همان‌قدر بی‌اطلاع است که سبزِ قبلی.

ناوردی‌ها:

    ۱. **تنها تعریفِ تازگی `_ops/provenance.py` است.** این‌جا مفهومِ دومی از
       «تازه/کهنه» ساخته نمی‌شود؛ هر گزارشِ وضعیت یک `provenance.stamp()`
       حمل می‌کند و lag فقط از مسیرِ `value_of()` عبور می‌کند — که روی
       UNKNOWN استثنا می‌دهد، پس غیاب ساختاراً نمی‌تواند به عدد تبدیل شود.

    ۲. **گزارش‌دادن هیچ‌چیز نمی‌سازد.** نه `SYNC_DIR`، نه `HEALTH_PATH`، نه
       فایلِ `.lock`. ساختنِ دایرکتوری یک اجرا را جعل می‌کند (بندِ ۸ ِ طرح).
       برای همین مسیرِ خواندن از `LockedJson` استفاده نمی‌کند: `__enter__` آن
       `mkdir(parents=True)` می‌زند و یک `.lock` می‌سازد. نوشتن اتمیک است
       (`os.replace`)، پس خواندنِ بی‌قفل یا نسخهٔ قبلی را می‌بیند یا بعدی را.

    ۳. **دفتر یک نویسنده دارد.** `HEALTH_PATH` فقط با `record_success`/
       `record_failure` نوشته می‌شود. تا امروز `write_snapshot()` گزارش را
       روی همان فایل می‌ریخت و رکوردهای `last_ok_epoch` را نابود می‌کرد —
       یعنی اولین گزارش، شواهدِ هر هدفِ سبز را پاک می‌کرد. گزارش حالا فایلِ
       خودش را دارد (`SNAPSHOT_PATH`).

    ۴. **ساعت کاملاً تزریق‌پذیر است.** هیچ شاخه‌ای وقتی `now` داده شده
       `time.time()` را مستقیم نمی‌خواند.

خط‌قرمزهای سخت (بدون تغییر):
  • fail-soft: هر source ناخوانا = report بدون alert سراسری.
  • alert فقط از opslib.alert (append-only governor-alerts.md).
  • FREEZE اگر divergence > threshold (I3) — و هرگز روی اندازه‌گیریِ غایب.
  • stdlib-only؛ $0 offline؛ propose-only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget"), str(_OPS / "state")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import provenance as _prov  # noqa: E402

SYNC_DIR = opslib.STATE_DIR / "sync"
HEALTH_PATH = opslib.STATE_DIR / "sync-health.json"
#: گزارش جدا از دفتر می‌نشیند — ناوردیِ ۳.
SNAPSHOT_PATH = opslib.STATE_DIR / "sync-health-snapshot.json"

#: اهدافِ اعلام‌شدهٔ `_ops/sync_agent.py` (`ensure_ids` / `_default_deps`).
#: بدونِ این فهرست، `snapshot()` روی دفترِ غایب صفر هدف می‌شمرد و «صفر مشکل»
#: می‌گفت — همان صفرِ آرامی که این گام آمده حذفش کند.
KNOWN_TARGETS = ("studio_pf", "cartographer", "lead")

#: عمداً همان رشتهٔ `provenance.Mode.UNKNOWN` (حروفِ بزرگ) — با هیچ‌کدام از
#: `ok`/`warn`/`err`/`fail` ِ حروف‌کوچک قابلِ اشتباه نیست.
UNKNOWN = _prov.Mode.UNKNOWN

LEDGER_ABSENT = "ledger absent — never executed"
LEDGER_UNREADABLE = "ledger unreadable"
TARGET_NEVER_RECORDED = "no record for target — never executed"
MECHANISM_ABSENT = "NO MECHANISM, never built"

#: ریتمِ اعلام‌شده برای تمبرِ اصالت = آستانهٔ خطای lag (پیش‌فرض ۲۴ ساعت).
_STAMP_WRITER = "sync_health.record_success"


def _cfg() -> dict:
    """پیکربندی از budgets.yaml → resilience.sync_health."""
    try:
        b = opslib.load_budgets()
    except Exception:  # noqa: BLE001
        b = {}
    r = (b.get("resilience") or {}).get("sync_health") or {}
    return {
        "warn_lag_seconds": float(r.get("warn_lag_seconds", 3600)),
        "err_lag_seconds": float(r.get("err_lag_seconds", 86400)),
        "divergence_pct": float(r.get("divergence_pct", 0.20)),
        "max_fail_streak": int(r.get("max_fail_streak", 5)),
        "tag": "FACT(budgets.yaml)" if r else "EST(default)",
    }


# ─── مسیرها ──────────────────────────────────────────────────────────────────
def _state_dir(state_dir=None) -> Path:
    return Path(state_dir) if state_dir is not None else opslib.STATE_DIR


def _sync_dir(state_dir=None) -> Path:
    return _state_dir(state_dir) / SYNC_DIR.name


def _ledger_path(state_dir=None) -> Path:
    return _state_dir(state_dir) / HEALTH_PATH.name


def _source_path(source: str, state_dir=None, create: bool = False) -> Path:
    """مسیرِ پرچمِ یک source. `create` فقط از مسیرِ **نوشتن** True است —
    ساختنِ دایرکتوری در مسیرِ گزارش یک اجرا را جعل می‌کند (ناوردیِ ۲)."""
    d = _sync_dir(state_dir)
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d / f"last-success-{source}.json"


def _health_path(state_dir=None, create: bool = False) -> Path:
    p = _ledger_path(state_dir)
    if create:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ─── خواندنِ دفتر (صفر نوشتن) ────────────────────────────────────────────────
def _read_ledger(state_dir=None):
    """دفتر را می‌خواند. برمی‌گرداند `(doc, reason)`؛ `reason=None` یعنی خوانده شد.

    سه شکستِ متمایز، سه رشتهٔ متمایز — چون «هرگز اجرا نشد» و «خراب است» دو
    خبرِ کاملاً متفاوت برای مالک‌اند.
    """
    path = _ledger_path(state_dir)
    if not path.exists():
        return {}, LEDGER_ABSENT
    try:
        doc = json.loads(path.read_text("utf-8"))
    except Exception as e:  # noqa: BLE001 — OSError و JSONDecodeError هر دو
        return {}, f"{LEDGER_UNREADABLE}: {type(e).__name__}"
    if not isinstance(doc, dict):
        return {}, f"{LEDGER_UNREADABLE}: not an object"
    return doc, None


def _unknown(source: str, reason: str, cfg: dict, stamp: dict | None = None) -> dict:
    """گزارشِ «نمی‌دانم» — هیچ کلیدی عددِ ساختگی حمل نمی‌کند.

    `lag_seconds`/`fail_count` عمداً `None` اند نه `0`: صفر یک اندازه‌گیری است
    و این‌جا اندازه‌گیری‌ای وجود ندارد.
    """
    return {
        "source": source,
        "status": UNKNOWN,
        "lag_seconds": None,
        "fail_count": None,
        "last_ok_ts": None,
        "last_fail_ts": None,
        "last_run_ts": None,
        "reason": reason,
        "config_tag": cfg["tag"],
        "provenance": stamp if stamp is not None else _prov.stamp(
            None, "", None, cfg["err_lag_seconds"], writer=_STAMP_WRITER),
    }


def record_success(source: str, meta: dict | None = None) -> dict:
    """ثبت موفقیتِ sync برای source. تنها نویسندهٔ رکوردهای موفق."""
    sp = _source_path(source, create=True)
    rec = {"ts": opslib.now_iso(), "epoch": time.time(), "meta": meta or {}}
    sp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    with opslib.LockedJson(_health_path(create=True)) as lj:
        health = lj.read() or {}
        h = health.setdefault("sources", {}).setdefault(source, {})
        h["last_ok_ts"] = rec["ts"]
        h["last_ok_epoch"] = rec["epoch"]
        h["fail_count"] = 0
        h["last_fail_ts"] = None
        h["status"] = "ok"
        lj.write(health)
    return {"source": source, "status": "ok"}


def record_failure(source: str, reason: str = "") -> dict:
    """ثبت شکستِ sync؛ اگر streak به max_fail_streak رسید → alert."""
    with opslib.LockedJson(_health_path(create=True)) as lj:
        health = lj.read() or {}
        h = health.setdefault("sources", {}).setdefault(source, {})
        h["last_fail_ts"] = opslib.now_iso()
        h["fail_count"] = int(h.get("fail_count") or 0) + 1
        h["status"] = "fail"
        lj.write(health)
        fail_count = h["fail_count"]
    cfg = _cfg()
    if fail_count >= cfg["max_fail_streak"]:
        opslib.alert([f"sync {source} failed {fail_count}× consecutive "
                      f"(max {cfg['max_fail_streak']}) — {reason}"])
    return {"source": source, "status": "fail", "fail_count": fail_count}


def check(source: str, now=None, state_dir=None) -> dict:
    """بررسی سلامتِ یک هدف: lag، streak، تازگی — یا صریحاً `UNKNOWN`.

    ترتیبِ تقدمِ حالت‌ها:
        دفتر غایب/ناخوانا            ⇒ UNKNOWN
        دفتر هست ولی هدف رکورد ندارد ⇒ UNKNOWN
        رکورد هست، موفقیت ندارد، شکست دارد ⇒ err   ← سیگنالِ واقعی، نه غیاب
        رکورد هست و موفقیت دارد      ⇒ ok/warn/err بر اساسِ lag
    """
    cfg = _cfg()
    ledger, reason = _read_ledger(state_dir)
    if reason:
        return _unknown(source, reason, cfg)

    h = (ledger.get("sources") or {}).get(source)
    if not isinstance(h, dict) or not h:
        return _unknown(source, TARGET_NEVER_RECORDED, cfg)

    now_s = float(now) if now is not None else time.time()
    last_ok = h.get("last_ok_epoch")
    st = _prov.stamp(last_ok, str(_ledger_path(state_dir)), last_ok,
                     cfg["err_lag_seconds"], writer=_STAMP_WRITER, now=now_s)

    if st.get("mode") == _prov.Mode.UNKNOWN:
        ever_failed = bool(h.get("last_fail_ts")) or int(h.get("fail_count") or 0) > 0
        if not ever_failed:
            # رکوردی که نه موفقیت دارد نه شکست، هیچ اجرایی را اثبات نمی‌کند.
            return _unknown(source, TARGET_NEVER_RECORDED, cfg, stamp=st)
        # اجرا شد و شکست خورد — این غیاب نیست، خبر است.
        return {
            "source": source,
            "status": "err",
            "lag_seconds": None,
            "fail_count": int(h.get("fail_count") or 0),
            "last_ok_ts": None,
            "last_fail_ts": h.get("last_fail_ts"),
            "last_run_ts": h.get("last_fail_ts"),
            "reason": "no successful sync recorded",
            "config_tag": cfg["tag"],
            "provenance": st,
        }

    # ناوردیِ ۱: lag فقط از مسیرِ value_of عبور می‌کند. اگر روزی شاخه‌ای یک
    # UNKNOWN را تا این‌جا بیاورد، این‌جا بلند می‌شکند — نه اینکه صفر بدهد.
    lag_s = round(now_s - float(_prov.parse_ts(_prov.value_of(st))), 1)
    level, reason = "ok", None
    if lag_s >= cfg["err_lag_seconds"]:
        level, reason = "err", f"lag {lag_s}s >= {cfg['err_lag_seconds']}s"
    elif lag_s >= cfg["warn_lag_seconds"]:
        level, reason = "warn", f"lag {lag_s}s >= {cfg['warn_lag_seconds']}s"
    return {
        "source": source,
        "status": level,
        "lag_seconds": lag_s,
        "fail_count": int(h.get("fail_count") or 0),
        "last_ok_ts": h.get("last_ok_ts"),
        "last_fail_ts": h.get("last_fail_ts"),
        "last_run_ts": h.get("last_ok_ts"),
        "reason": reason,
        "config_tag": cfg["tag"],
        "provenance": st,
    }


def divergence_check(source_a: str, source_b: str,
                     value_a: float | None, value_b: float | None) -> dict:
    """بررسی divergence بین دو source (مثلاً billed↔telemetry).

    اندازه‌گیریِ غایب ⇒ `UNKNOWN` و **هیچ** FREEZE ای. یک `None` که به صفر
    تبدیل شود، دو منبعِ نامعلوم را «کاملاً هم‌خوان» اعلام می‌کند.
    """
    cfg = _cfg()
    missing = [n for n, v in ((source_a, value_a), (source_b, value_b)) if v is None]
    if missing:
        return {"divergence": None, "status": UNKNOWN,
                "reason": f"missing measurement: {', '.join(missing)}"}
    if value_a <= 0 and value_b <= 0:
        return {"divergence": 0.0, "status": "ok", "reason": "both zero"}
    denom = max(abs(value_a), abs(value_b), 0.000001)
    div = abs(value_a - value_b) / denom
    status = "ok"
    reason = None
    if div > cfg["divergence_pct"]:
        status = "err"
        reason = f"divergence {div:.1%} > threshold {cfg['divergence_pct']:.1%}"
        opslib.alert([f"sync divergence {source_a}↔{source_b}: {reason}"])
        # I3: divergence = FREEZE
        opslib.freeze(f"sync divergence {source_a}↔{source_b}: {reason}")
    return {"divergence": round(div, 4), "status": status, "reason": reason}


def snapshot(targets=None, now=None, state_dir=None) -> dict:
    """عکسِ واحد از سلامتِ اهداف — با غیاب به‌عنوانِ یک حالتِ درجه‌یک.

    فهرستِ اهداف از `KNOWN_TARGETS` می‌آید (به‌علاوهٔ هرچه در دفتر ثبت شده)،
    نه از کلیدهای دفتر. وگرنه دفترِ غایب ⇒ صفر هدف ⇒ «صفر مشکل».
    صفر نوشتن.
    """
    cfg = _cfg()
    ledger, reason = _read_ledger(state_dir)
    recorded = sorted((ledger.get("sources") or {}).keys())
    if targets is not None:
        names = list(targets)
    else:
        names = list(KNOWN_TARGETS) + [s for s in recorded if s not in KNOWN_TARGETS]

    now_s = float(now) if now is not None else time.time()
    out = {
        "ts": opslib.now_iso(),
        "config": cfg,
        "known_targets": list(KNOWN_TARGETS),
        "sources": {},
    }
    for s in names:
        out["sources"][s] = check(s, now=now_s, state_dir=state_dir)

    def _n(level):
        return sum(1 for v in out["sources"].values() if v["status"] == level)

    unknown = _n(UNKNOWN)
    err, warn, ok = _n("err"), _n("warn"), _n("ok")
    out["summary"] = {"total": len(names), "ok": ok, "warn": warn,
                      "err": err, "unknown": unknown}
    # وضعیتِ کلی: نادانستن بر همه‌چیز مقدم است. هدفی که نمی‌دانیم می‌تواند
    # هر چیزی باشد، پس سبزِ کلی حق نداریم اعلام کنیم.
    if not names or unknown:
        out["status"] = UNKNOWN
    elif err:
        out["status"] = "err"
    elif warn:
        out["status"] = "warn"
    else:
        out["status"] = "ok"
    out["ledger"] = {
        "path": str(_ledger_path(state_dir)),
        "exists": _ledger_path(state_dir).exists(),
        "sync_dir": str(_sync_dir(state_dir)),
        "sync_dir_exists": _sync_dir(state_dir).exists(),
        "reason": reason,
        "recorded_targets": recorded,
    }
    #: رابطهٔ heart↔4D↔organism به‌عنوانِ غیابِ اعلام‌شده، نه شکست (C16).
    out["mechanism"] = MECHANISM_ABSENT if not recorded else None
    return out


def write_snapshot(now=None) -> dict:
    """ثبت snapshot روی دیسک — روی فایلِ **خودش**، نه روی دفتر (ناوردیِ ۳)."""
    s = snapshot(now=now)
    p = SNAPSHOT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with opslib.LockedJson(p) as lj:
        lj.write(s)
    return s


if __name__ == "__main__":
    if "--check" in sys.argv:
        idx = sys.argv.index("--check")
        source = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "unknown"
        print(json.dumps(check(source), ensure_ascii=False, indent=2))
    elif "--write" in sys.argv:
        print(json.dumps(write_snapshot(), ensure_ascii=False, indent=2))
    else:
        # پیش‌فرضِ CLI فقط می‌خواند: گزارش‌گرفتن نباید ظرفی بسازد.
        print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
