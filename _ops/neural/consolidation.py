#!/usr/bin/env python3
"""consolidation.py — NI-4: ConsolidationCycle (خوابِ عمیق / یادگیری).

+ Verification Gate (AlphaEvolve): فقط از نتایجِ verifyشده یاد می‌گیرد.
هر N beat همهٔ منابعِ یادگیری را synthesize می‌کند.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


def _now() -> float:
    """تنها منبعِ زمانِ این ماژول.

    چرا یک تابعِ جدا و نه `time.time` مستقیم: `field(default_factory=time.time)`
    ارجاع را **در زمانِ تعریفِ کلاس** می‌بندد، پس patch کردنِ `time.time` بعداً روی
    آن اثر ندارد و مسیرِ فرعی همچنان ساعتِ واقعی می‌خوانَد — ساعتِ نیمه‌تزریقی،
    یعنی تستی که روزها سبز و شب‌ها قرمز است. با این تابع هر دو مسیر یکی می‌شوند.
    """
    return time.time()


def _flag(name: str) -> bool:
    """env-flag با پیش‌فرض خاموش — همان قرارداد `wiring.flag`/`cardiac.flag`."""
    return os.environ.get(name, "0") == "1"


def _compress_on() -> bool:
    return _flag("OCTOPUS_CONSOLIDATION_COMPRESS")


def _floor_seconds() -> float:
    """کفِ زمانیِ فشرده‌سازی. کمتر از این فاصله = «همان یافته»؛ بیشتر = رویدادِ نو.

    چرا کف لازم است: بدونِ آن، یافته‌ای که بعد از ۱۹ روز دوباره ظاهر می‌شود در
    ردیفِ روزِ اول تا می‌شود و **ساختارِ زمانی نابود می‌شود** — همان‌قدر بی‌معنا که
    ۵۳۸ ردیفِ تکراری. با کفِ ۶ ساعته، بازگشتِ یک یافته در روزِ بعد ردیفِ خودش را
    می‌گیرد. اندازه‌گیریِ replay روی تاریخچهٔ واقعی (۵۳۸ ردیف، ۱۹.۳ روز):
        کف=۱h → ۶۷ ردیف · کف=۶h → ۳۷ ردیف · کف=۲۴h → ۲۵ · کف=∞ → ۲۴ (بی‌زمان)
    """
    try:
        return float(os.environ.get("OCTOPUS_CONSOLIDATION_FLOOR_SEC", "21600"))
    except ValueError:
        return 21600.0


# ── dedup فازی (افزودنی، پشتِ فلگِ جدا، fail-soft) — ۲۰۲۶-۰۸-۰۷ ───────────────
# چرا جدا از `_compress_on`: آن مسیر فقط **امضای دقیق** (sha256 محتوایی) را می‌بندد
# و باز هم خاموش است روی درختِ زنده. اندازه‌گیریِ زنده: ۵۸۳ ردیف، **۲۸ امضای
# یکتا (۴.۸٪)** — یعنی ۹۵.۲٪ تکرار. علت اصلی: مقدارِ «آگاهیِ میانگین» بین چند
# سطح نوسان می‌کند (0.73 → 0.72 → 0.73) و هیچ‌کدام امضای عینِ هم ندارند، پس
# گاردِ دقیق روی همه‌شان صفر اثر دارد. این مسیر **شباهتِ زیررشته‌ای** ساده (نه
# LLM) را روی آخرین N ردیف می‌سنجد: بالایِ آستانه → فولد، نه append نو.
# افزودنی: فلگ خاموش = بایت‌به‌بایت با امروز (مسیرِ exact-dedup دست‌نخورده).
def _dedup_fuzzy_on() -> bool:
    return _flag("OCTOPUS_CONSOLIDATION_DEDUP_FUZZY")


def _dedup_window() -> int:
    """تعدادِ ردیفِ اخیری که شباهت باشان سنجیده می‌شود. پیش‌فرضِ ۸ = ~یک روزِ کاری."""
    try:
        return max(1, int(os.environ.get("OCTOPUS_CONSOLIDATION_DEDUP_N", "8")))
    except ValueError:
        return 8


def _dedup_threshold() -> float:
    """کفِ شباهتِ جاکاردیِ توکنی برای «همان یافته». پیش‌فرض ۰.۷ (محافظه‌کارانه)."""
    try:
        v = float(os.environ.get("OCTOPUS_CONSOLIDATION_DEDUP_SIM", "0.7"))
        return v if 0.0 <= v <= 1.0 else 0.7
    except ValueError:
        return 0.7


def _tokenize(s: str) -> set[str]:
    """توکن‌سازیِ سبک برای شباهتِ زیررشته‌ای: کلماتِ ≥۲ حرف، normalised.
    اعداد (مثل 0.73) را نگه می‌دارد چون تکرارِ آن‌ها خودش سیگنالِ نویز است."""
    out: set[str] = set()
    for tok in str(s or "").replace(",", " ").split():
        t = tok.strip(".,؛:()«»\"'")
        if len(t) >= 2:
            out.add(t)
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    """شباهتِ جاکاردی روی دو مجموعهٔ توکن. خالی/خالی = ۰ (نه ۱)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _fuzzy_duplicate(rec: dict, history: list[dict], window: int,
                     threshold: float) -> tuple[int | None, dict | None]:
    """آیا `rec` شبیهِ ردیفِ اخیری است؟ خروجی: (موقعیتِ مقصد | None, ردیفِ مقصد | None).

    شباهت = جاکاردِ توکنیِ رشتهٔ insights (به‌هم‌چسبیده با ' | '). بالایِ آستانه روی
    آخرین `window` ردیف → اولین تطبیق برنده. ردیفِ مقصد نباید بردارِ latent داشته
    باشد (همان قراردادِ `_foldable` — تا کردن داخلِ ردیفِ غنی، دادهٔ کمیاب را له می‌کند).
    fail-soft: هر خطا → (None, None) یعنی «اجازهٔ append بده».
    """
    try:
        rec_tokens = _tokenize(" | ".join(str(x) for x in (rec.get("insights") or [])))
        if not rec_tokens:
            return None, None
        recent = [r for r in history[-max(1, window):] if isinstance(r, dict)]
        for i in range(len(recent) - 1, -1, -1):       # از تازه‌ترین به قدیمی
            cand = recent[i]
            if cand.get("latent_vector") is not None:
                continue
            cand_tokens = _tokenize(" | ".join(str(x) for x in (cand.get("insights") or [])))
            if _jaccard(rec_tokens, cand_tokens) >= threshold:
                # موقعیتِ مطلق در history (نه در recent) برای fold
                abs_pos = len(history) - len(recent) + i
                return abs_pos, cand
    except Exception:  # noqa: BLE001 — dedup هرگز consolidation را نمی‌کشد
        pass
    return None, None


def _default_data_path() -> Path:
    """env-اول (OPS_DIR) تا تستِ harness-ایزوله state واقعی/repo را آلوده نکند
    (همان درسِ bcm 2026-07-10)؛ بدونِ env = کنارِ ماژول (production)."""
    ops = os.environ.get("OPS_DIR")
    base = Path(ops) / "neural" if ops else Path(__file__).resolve().parent
    return base / "consolidation.json"


_DATA_PATH = _default_data_path()


@dataclass
class VerifiedSource:
    """یک منبعِ یادگیری با verification status."""
    name: str
    data: dict
    verified: bool       # AlphaEvolve: فقط verified → یادگیری


@dataclass
class ConsolidatedInsight:
    """خروجیِ یک دورِ consolidation."""
    cycle: int
    insights: list[str]
    verified_sources: list[str]
    discarded_sources: list[str]
    timestamp: float = field(default_factory=lambda: _now())
    # Phase 2: latent representation (backward compatible — None when no latent space)
    latent_vector: list[float] | None = None
    similar_keys: list[str] | None = None
    # Phase 3 (Blueprint): گزارش BCM forgetting (backward compatible — None وقتی BCM خاموش)
    bcm_pruned: list[str] | None = None
    bcm_theta: float | None = None
    bcm_saturation: float | None = None
    # Phase 4 (Blueprint): گزارش فیلتر sparse (backward compatible — None وقتی خاموش)
    sparse_ratio: float | None = None
    sparse_filtered: list[str] | None = None
    # Phase 5 (۲۰۲۶-۰۸-۰۷): گزارشِ dedup فازی — چند ردیفِ شبیه دفع شد (None = فلگ خاموش).
    # اضافه‌شدنی: فلگ خاموش → None، بایت‌به‌بایتِ امروز.
    dedup_skipped: int | None = None


def _verify_source(name: str, data: dict) -> bool:
    """Verification Gate (AlphaEvolve). آیا داده قابلِ اعتماد است؟
    - acquisition: فقط اگر upvotes/comments عددی واقعی باشند
    - doctor archive: فقط اگر outcome = approved/rejected
    - school: فقط اگر awareness data عددی باشد
    - calibration: فقط اگر verdict ثبت‌شده باشد"""
    if name == "acquisition" and isinstance(data, dict):
        return any(isinstance(v, (int, float)) and v > 0
                   for v in data.values() if isinstance(v, (int, float)))
    if name == "doctor_archive" and isinstance(data, list):
        return all(d.get("outcome") in ("approved", "rejected", "published")
                   for d in data if isinstance(d, dict))
    if name == "school_awareness" and isinstance(data, dict):
        return isinstance(data.get("mean_awareness"), (int, float))
    if name == "calibration" and isinstance(data, list):
        return all(isinstance(d, dict) and "verdict" in d for d in data)
    return False


class ConsolidationCycle:
    """خوابِ عمیق. synthesize همهٔ منابع. فقط verified."""

    def __init__(self, data_path: str | Path | None = None):
        self._path = Path(data_path) if data_path else _DATA_PATH
        self._history: list[dict] = self._load()
        # ۲۰۲۶-۰۷-۳۰ — شمارنده از **بیشترین سیکلِ ثبت‌شده** seed می‌شود، نه از شمارِ
        # ردیف‌ها (`len(self._history)`). چون دورِ هم‌محتوا داخلِ ردیفِ قبلی **تا**
        # می‌شود، شمارِ ردیف‌ها رشد نمی‌کند، پس هر ری‌استارتِ پروسه دقیقاً همان شماره
        # را از نو می‌ساخت. اثرِ روی فایلِ زنده: ردیفِ (cycle=537, last_cycle=538,
        # repeats=13) یعنی سیزده شلیکِ جدا که همه خودشان را «۵۳۸» مُهر کردند.
        # و چون کلیدِ بازیابی `cycle_key = f"cycle-{result.cycle}"` است
        # (`wiring._enrich_with_latent`)، `latent_space.embed` همان کلید را بازنویسی
        # می‌کرد: ایندکسِ بازیابی هرگز از تعدادِ ordinalهای **متمایز** بالاتر نمی‌رفت
        # (۱۰ بردار). این هم‌برخوردِ کلید بود، نه هرس — کمینهٔ وزنِ BCM ۱.۷۹۹ مقابلِ
        # کفِ ۰.۰۵ و ۱۰ کلید مقابلِ سقفِ ۵۱۲، یعنی هرگز چیزی prune نشده بود.
        try:
            recorded = max(
                (int(r.get("last_cycle") or r.get("cycle") or 0)
                 for r in self._history if isinstance(r, dict)), default=0)
        except (TypeError, ValueError):
            recorded = 0
        # کفِ `len(self._history)` تزئینی نیست. ردیفی که `last_cycle`/`cycle` ندارد یا
        # None است **هیچ خطایی نمی‌دهد** — `int(None or None or 0)` می‌شود صفر — پس
        # `except` نمی‌گیردش و شمارنده از ۱ از نو شروع می‌شد: دقیقاً همان بازاستفادهٔ
        # ordinal که این فیکس قرار بود ببندد، در لباسی دیگر. اندازه‌گیری‌شده روی ۵ ردیفِ
        # بی‌کلید: seed=۰ در برابرِ ۵ ِ امروز. با این max نه از امروز عقب‌تر می‌رویم و نه
        # یکنواییِ شماره را از دست می‌دهیم.
        self._cycle_count = max(recorded, len(self._history))
        # sig → ایندکسِ آخرین ردیفِ هم‌محتوا. lazy: فقط وقتی فشرده‌سازی روشن است
        # ساخته می‌شود، پس مسیرِ flag-off حتی یک sha256 هم نمی‌دهد.
        self._sig_index: dict[str, int] | None = None

    def _load(self) -> list[dict]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._history, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    # ─── فشرده‌سازی: امضای محتوایی + کفِ زمانی ─────────────────────────────────

    @staticmethod
    def _signature(rec: dict) -> str:
        """امضای **فقط محتوایی** یک رکورد.

        هیچ شمارندهٔ یکنوا (`cycle`، `last_cycle`، `repeats`) و هیچ timestampی
        داخلِ کلید نمی‌رود. درسِ ۲۰۲۶-۰۷-۲۸ (سه بار در یک روز): وقتی شمارنده در
        کلیدِ dedup باشد، «تغییرِ محتوا» و «گذشتِ زمان» یک چیز خوانده می‌شوند و
        گاردِ درست روی مکانیزمِ غلط دقیقاً صفر اثر دارد.
        """
        payload = json.dumps([rec.get("insights"),
                              rec.get("verified_sources"),
                              rec.get("discarded_sources")],
                             ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _build_sig_index(self) -> dict[str, int]:
        idx: dict[str, int] = {}
        for i, row in enumerate(self._history):
            if isinstance(row, dict):
                idx[self._signature(row)] = i     # آخرینِ هر امضا برنده است
        return idx

    @staticmethod
    def _row_last_ts(row: dict) -> float:
        for k in ("last_ts", "timestamp"):
            v = row.get(k)
            if isinstance(v, (int, float)):
                return float(v)
        return 0.0

    def _foldable(self, rec: dict) -> dict | None:
        """ردیفی که `rec` باید داخلش تا شود — یا None اگر باید ردیفِ نو بسازد.

        سه شرط: (۱) امضای محتوایی یکی، (۲) فاصلهٔ زمانی زیرِ کف، (۳) ردیفِ مقصد
        بردارِ latent نداشته باشد. شرطِ سوم عمدی است: از ۵۳۸ ردیف فقط ۲ تا بردار
        دارند (رویدادِ واقعیِ بازیابی). تا کردنِ یک ردیفِ غنی داخلِ ردیفِ فقیر —
        یا برعکس — تنها دادهٔ کمیابِ این فایل را از بین می‌برد.
        """
        if self._sig_index is None:
            self._sig_index = self._build_sig_index()
        pos = self._sig_index.get(self._signature(rec))
        if pos is None or pos >= len(self._history):
            return None
        target = self._history[pos]
        if not isinstance(target, dict) or target.get("latent_vector") is not None:
            return None
        now = rec.get("timestamp")
        now = float(now) if isinstance(now, (int, float)) else _now()
        if (now - self._row_last_ts(target)) >= _floor_seconds():
            return None                      # فراتر از کف = رویدادِ نو، نه تکرار
        return target

    def run(self, sources: dict[str, dict]) -> ConsolidatedInsight:
        """یک دورِ consolidation. sources = {name: data}.
        فقط verified → ConsolidatedInsight. unverified → discard."""
        self._cycle_count += 1
        insights = []
        verified_names = []
        discarded_names = []

        for name, data in sources.items():
            if _verify_source(name, data):
                verified_names.append(name)
                if name == "acquisition":
                    best = max(data.items(), key=lambda x: x[1]) if data else None
                    if best:
                        insights.append(f"بهترین محتوا: {best[0]} (score={best[1]:.2f})")
                elif name == "doctor_archive":
                    approved = [d for d in data if isinstance(d, dict)
                                and d.get("outcome") in ("approved", "published")]
                    insights.append(f"فیکس‌های تأییدشده: {len(approved)}")
                elif name == "school_awareness":
                    ma = data.get("mean_awareness", 0)
                    insights.append(f"آگاهیِ میانگین: {ma:.2f}")
                elif name == "calibration":
                    insights.append(f"verdictها: {len(data)} رکورد")
            else:
                discarded_names.append(name)

        result = ConsolidatedInsight(
            cycle=self._cycle_count, insights=insights,
            verified_sources=verified_names, discarded_sources=discarded_names)
        # فشرده‌سازیِ تکرار (۲۰۲۶-۰۷-۲۷). قبلاً هر چرخه append می‌شد حتی وقتی
        # insight عیناً همان قبلی بود: ۵۳۵ ردیف در فایل، و در ۴۰ چرخهٔ اخیر فقط
        # ۱۶ چیزِ متمایز — «آگاهیِ میانگین: 0.61» ده بار پشتِ سرِ هم. سیگنالِ واقعی
        # زیرِ نویزِ خودش دفن می‌شد و فایل بی‌کران رشد می‌کرد.
        # اطلاعات از دست نمی‌رود: `repeats` و `last_cycle` می‌گویند همان یافته چند
        # چرخه پایدار مانده — که خودش دادهٔ باارزشی است، نه صرفاً حذفِ تکرار.
        rec = asdict(result)
        # ۲۰۲۶-۰۷-۲۸ — چرا فشرده‌سازیِ **غیرِ متوالی** لازم شد. نسخهٔ ۰۷-۲۷ فقط با
        # `self._history[-1]` مقایسه می‌کرد، پس تکرارِ متوالی را می‌گرفت و تکرارِ
        # متناوب را نه. اندازه‌گیریِ فایلِ زنده همان روز: **۵۳۸ ردیف، ۲۴ امضای
        # یکتا** (۴.۵٪) — و ۱۸۱ ردیف عیناً «آگاهیِ میانگین: 0.02». چون مقدارِ
        # آگاهی بین چند سطح نوسان می‌کند (0.02 → 0.04 → 0.02 → …) هیچ‌کدام از آن
        # ۱۸۱ تا متوالی نبودند، پس گاردِ متوالی روی همه‌شان صفر اثر داشت.
        # حالا کلید = امضای محتوایی (بدونِ شمارنده) + کفِ زمانی.
        if _compress_on():
            target = self._foldable(rec)
        else:
            prev = self._history[-1] if self._history else None
            same = (isinstance(prev, dict)
                    and prev.get("insights") == rec["insights"]
                    and prev.get("verified_sources") == rec["verified_sources"]
                    and prev.get("discarded_sources") == rec["discarded_sources"])
            # ۲۰۲۶-۰۸-۱۵ — شرطِ «مقصدِ بدونِ بردار» از مسیرِ زنده برداشته شد.
            # چرا: OCTOPUS_WIRE_LATENT_PERSIST از سیکلِ ۵۳۷ (۲۰۲۶-۰۷-۲۸) به هر
            # ردیفی بردار می‌دهد — اندازه‌گیریِ زنده: ۸۹/۸۹ ردیفِ پس از آن غنی‌اند،
            # پس این شرط یعنی «هیچ‌وقت تا نشو» و نتیجه‌اش ۲۰ ردیفِ عیناً یکسانِ
            # پیاپی («فیکس‌های تأییدشده: 3 · آگاهیِ میانگین: 0.73») بود — همان
            # «consolidation راکد» C-012. ترسِ اصلیِ ۲۰۲۶-۰۷-۳۰ (له‌کردنِ دادهٔ
            # کمیاب) دیگر موضوعیت ندارد: fold هیچ فیلدی را حذف نمی‌کند، بردارِ
            # مقصد دست‌نخورده می‌ماند، و sync_latent از طریقِ تطبیقِ last_cycle
            # (پوششِ خودِ کد برای ردیفِ تا‌شده) بردارِ تازه را همان‌جا می‌نویسد.
            # مسیرِ compress (فلگ‌دار) با قراردادِ `_foldable` دست‌نخورده است.
            target = prev if same else None
        # Phase 5 (۲۰۲۶-۰۸-۰۷) — dedup فازیِ افزودنی: اگر مسیرِ exact برنگرداند،
        # شباهتِ زیررشته‌ای روی آخرین N ردیف را امتحان کن. چرا جدا از exact:
        # اندازه‌گیریِ زنده نشان داد exact روی ۹۵.۲٪ تکرار صفر اثر دارد (نوسانِ
        # عددِ آگاهی امضای عینِ هم نمی‌سازد). فازی این شکاف را می‌بندد. فلگِ جدا،
        # fail-soft، و ردیفِ دارای بردار را هرگز مقصد نمی‌کند (همان قرارداد).
        # فلگ خاموش → dedup_skipped می‌ماند None (بایت‌به‌بایتِ امروز).
        if _dedup_fuzzy_on():
            result.dedup_skipped = 0
            if target is None and self._history:
                _fpos, _ftarget = _fuzzy_duplicate(rec, self._history,
                                                    _dedup_window(), _dedup_threshold())
                if _ftarget is not None and _fpos is not None:
                    target = _ftarget
                    result.dedup_skipped = 1
        if target is not None:
            target["repeats"] = int(target.get("repeats", 1)) + 1
            target["last_cycle"] = self._cycle_count
            if _compress_on():
                # کف روی **آخرین** مشاهده می‌سنجد نه اولین، وگرنه یک ردیف بعد از
                # ۶ ساعت برای همیشه بسته می‌شد و تکرار دوباره ردیف می‌ساخت.
                ts = rec.get("timestamp")
                target["last_ts"] = float(ts) if isinstance(ts, (int, float)) else _now()
        else:
            rec["repeats"] = 1
            rec["last_cycle"] = self._cycle_count
            if _compress_on():
                ts = rec.get("timestamp")
                rec["last_ts"] = float(ts) if isinstance(ts, (int, float)) else _now()
                if self._sig_index is None:
                    self._sig_index = self._build_sig_index()
                self._sig_index[self._signature(rec)] = len(self._history)
            self._history.append(rec)
        self._save()
        return result

    def sync_latent(self, result) -> bool:
        """فیلدهای latent ِ `result` را به رکوردِ ماندگارِ همان سیکل برگردان.

        ۲۰۲۶-۰۷-۲۸ — چرا این وجود دارد. `run()` رکورد را با `asdict(result)`
        اسنپ‌شات می‌گیرد و **همان‌جا** `_save()` می‌کند. صداکنندهٔ canonical بعد از
        برگشتن `_enrich_with_latent(result, …)` را صدا می‌زند که شیء را in-place
        غنی می‌کند — ولی آن اسنپ‌شات از قبل روی دیسک رفته. نتیجه: بردار **ساخته
        می‌شد، در ایندکسِ بازیابی می‌نشست، و واقعاً شلیک می‌کرد**، در حالی که
        تاریخچه برای همان سیکل `None` ثبت می‌کرد.

        اندازه‌گیریِ همان روز: از ۵۳۶ ردیفِ تثبیت، **صفر** تا بردار داشتند — ولی
        `bcm-weights.json` برای `cycle-536` وزنِ w=2.5865 θ=0.3439 داشت که یعنی
        غنی‌سازی اجرا شده بود. یک باگِ **ترتیب**، نه سیم‌کشی.

        اثرش دقیقاً همان چیزی است که «نمی‌تواند به یاد بیاورد» را می‌ساخت: بردار
        بدونِ ثبت یعنی حافظه‌ای که هر بار از صفر شروع می‌کند.

        رکوردِ فشرده‌شده (repeat) هم پوشش دارد: آن‌جا `cycle` قدیمی می‌ماند و
        `last_cycle` به‌روز می‌شود، پس هر دو تطبیق داده می‌شوند.
        بازگشت: True اگر چیزی واقعاً عوض شد.
        """
        if not self._history:
            return False
        rc = getattr(result, "cycle", None)
        if rc is None:
            return False
        # با فشرده‌سازی، رکوردِ این سیکل دیگر لزوماً `[-1]` نیست: ممکن است داخل
        # ردیفی **قدیمی‌تر** تا شده باشد و فقط `last_cycle`ش به‌روز شده باشد.
        # پس عقب‌گرد جست‌وجو می‌شود. با flag خاموش دامنه دقیقاً یک ردیف است، یعنی
        # همان `self._history[-1]`ِ نسخهٔ قبلی — رفتار بایت‌به‌بایت یکسان.
        scan = len(self._history) if _compress_on() else 1
        last = None
        for row in reversed(self._history[-scan:]):
            if not isinstance(row, dict):
                continue
            if int(row.get("cycle", -1)) == int(rc) or int(row.get("last_cycle", -1)) == int(rc):
                last = row
                break
        if last is None:
            return False                      # رکوردِ سیکلِ دیگر — هرگز دست نزن
        changed = False
        for field_name in ("latent_vector", "similar_keys"):
            val = getattr(result, field_name, None)
            if val is not None and last.get(field_name) != val:
                last[field_name] = val
                changed = True
        if changed:
            self._save()
        return changed

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def history(self) -> list[dict]:
        return list(self._history)


# ════════════════════════════════════════════════════════════════════════════════
# متریکِ «آیا این سیستم در طولِ زمان بهتر *به یاد می‌آورد*؟»
# ════════════════════════════════════════════════════════════════════════════════

_CYCLE_RE_PREFIX = "cycle-"


def _key_cycle(key: str) -> int | None:
    """شمارهٔ سیکل از کلیدِ latent مثلِ `cycle-539:school_awareness`."""
    s = str(key or "")
    if not s.startswith(_CYCLE_RE_PREFIX):
        return None
    head = s[len(_CYCLE_RE_PREFIX):].split(":", 1)[0]
    try:
        return int(head)
    except ValueError:
        return None


def recall_reach(history: list[dict]) -> dict:
    """**بردِ بازیابی** — تنها متریکی که در این زیرسیستم می‌تواند «بهتر شدن» را ثابت کند.

    تعریف: برای هر ردیفی که واقعاً چیزی بازیابی کرده (`similar_keys` دارد)، فاصلهٔ
    |cycle(کلیدِ بازیابی‌شده) − cycle(خودِ ردیف)| را بگیر. `reach_median` میانهٔ همهٔ
    این فاصله‌هاست.

    چرا این یکی و نه بقیه:
      · `proposal_accept_rate` رفتارِ **مالک** را می‌سنجد نه سیستم را — ۵۶۱ اسنپ‌شات
        در ۱۷ روز روی 0.0 ثابت، چون هیچ‌کس رأی نداده؛ سیستم می‌تواند عالی شود و این
        عدد صفر بماند.
      · نسبتِ یکتا/کل (فشرده‌سازی) کیفیتِ **نوشتن** را می‌سنجد نه یادآوری را.
      · تعدادِ ردیف‌ها یا گام‌های BCM با گذشتِ زمان خودبه‌خود بالا می‌رود — سنجهٔ
        عمر است نه یادگیری.
    این یکی با «بیشتر نوشتن» بالا نمی‌رود. فقط وقتی بالا می‌رود که بازیابی چیزی از
    **گذشتهٔ دور** بیاورد. سقفِ بی‌معنا هم ندارد: reach بزرگ = حافظهٔ بلندمدتِ زنده.

    خطِ پایهٔ امروز (۲۰۲۶-۰۷-۲۸، فایلِ زنده، ۵۳۸ ردیف / ۵۳۹ سیکل / ۱۹.۳ روز):
        events=2  keys=8  reach_median=1.0  reach_max=2  self_ratio=0.375
        coverage=0.0037
    یعنی: در تمامِ عمرِ سیستم دو بار بازیابی شلیک کرده، و هر هشت کلیدی که آورد از
    سیکل‌های ۵۳۷–۵۳۹ بودند — بردِ حداکثر ۲ سیکل (~۲۰ دقیقه)، و ۳ تا از ۸ کلید
    خودِ همان سیکل. این «به یاد آوردن» نیست؛ بازتابِ همین لحظه است.

    خروجی: dict — عمداً همه‌چیز شمارشی است، هیچ صفتی.
    """
    rows = [r for r in (history or []) if isinstance(r, dict) and r.get("similar_keys")]
    deltas: list[int] = []
    selfhits = 0
    for r in rows:
        own = r.get("cycle")
        if not isinstance(own, int):
            continue
        for k in r.get("similar_keys") or []:
            kc = _key_cycle(k)
            if kc is None:
                continue
            d = abs(kc - own)
            deltas.append(d)
            if d == 0:
                selfhits += 1
    total_rows = len([r for r in (history or []) if isinstance(r, dict)])
    deltas.sort()
    n = len(deltas)
    if n == 0:
        median = 0.0
    elif n % 2:
        median = float(deltas[n // 2])
    else:
        median = (deltas[n // 2 - 1] + deltas[n // 2]) / 2.0
    return {"events": len(rows), "keys": n,
            "reach_median": median,
            "reach_max": (deltas[-1] if deltas else 0),
            "self_ratio": (selfhits / n) if n else 0.0,
            "coverage": (len(rows) / total_rows) if total_rows else 0.0}
