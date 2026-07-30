"""test_latent_persist — بردار ساخته می‌شد، شلیک می‌کرد، و ثبت نمی‌شد.

اندازه‌گیریِ ۲۰۲۶-۰۷-۲۸ روی دادهٔ زنده:

    consolidation.json  ردیف ۵۳۶ → latent_vector = None · similar_keys = None
    bcm-weights.json    cycle-536 → w=2.5865  θ=0.3439   ← شلیک کرده

یعنی غنی‌سازی **اجرا شده بود**. مسئله سیم‌کشی نبود، **ترتیب** بود:

    result = consolidation.run(sources)   ← asdict + _save() همین‌جا
    _enrich_with_latent(result, …)        ← شیء را in-place غنی می‌کند، دیسک را نه

این دقیقاً همان چیزی است که «می‌تواند بهتر شود ولی نمی‌تواند به یاد بیاورد» را
می‌ساخت: از ۵۳۶ سیکل، صفر تا بردار در تاریخچه داشتند.

⚠️ این تست هرگز `_history` را دستی نمی‌سازد. اگر مرجعِ خودش را از حالتِ داخلیِ
ماژول بسازد، همان ادعای کد را تکرار می‌کند — تلهٔ `test_capability_registry` که
امروز صبح گرفتم. همه‌چیز از مسیرِ عمومیِ `run()` می‌گذرد.
"""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("latent-persist")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "neural")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json   # noqa: E402
from consolidation import ConsolidationCycle   # noqa: E402

FLAG = "OCTOPUS_WIRE_LATENT_PERSIST"


def _fresh():
    p = Path(tempfile.mkdtemp()) / "c.json"
    return ConsolidationCycle(data_path=p), p


def _rows(p: Path):
    d = json.loads(p.read_text("utf-8"))
    return d if isinstance(d, list) else (d.get("rows") or d.get("history") or [])


# ─── ۱: خودِ باگ ─────────────────────────────────────────────────────────
def t_run_alone_persists_no_vector():
    """خطِ پایه — این همان رفتاری است که ۵۳۶ ردیفِ تهی ساخت."""
    c, p = _fresh()
    c.run({"acquisition": {"x": 0.5}})
    assert _rows(p)[-1].get("latent_vector") is None


def t_sync_latent_writes_the_enrichment_to_disk():
    """قلبِ فیکس: بعد از غنی‌سازی، دیسک باید بردار را داشته باشد."""
    c, p = _fresh()
    r = c.run({"acquisition": {"x": 0.5}})
    r.latent_vector = [0.1, 0.2, 0.3]
    r.similar_keys = ["cycle-1:acquisition:x"]
    assert c.sync_latent(r) is True
    last = _rows(p)[-1]
    assert last["latent_vector"] == [0.1, 0.2, 0.3], last
    assert last["similar_keys"] == ["cycle-1:acquisition:x"], last


def t_a_repeated_cycle_still_gets_its_vector():
    """رکوردِ فشرده `cycle` قدیمی نگه می‌دارد و `last_cycle` را جلو می‌برد —
    اگر فقط `cycle` را تطبیق می‌دادیم، تکرارها برای همیشه تهی می‌ماندند."""
    c, p = _fresh()
    c.run({"acquisition": {"x": 0.5}})
    r2 = c.run({"acquisition": {"x": 0.5}})      # عیناً همان → فشرده می‌شود
    assert len(_rows(p)) == 1, "فشرده‌سازی کار نکرد؛ فرضِ تست باطل است"
    r2.latent_vector = [9.0]
    assert c.sync_latent(r2) is True
    assert _rows(p)[-1]["latent_vector"] == [9.0]


# ─── ۲: مرزها ────────────────────────────────────────────────────────────
def t_a_foreign_cycle_is_never_touched():
    """رکوردِ سیکلِ دیگر نباید بردارِ این سیکل را بگیرد."""
    c, p = _fresh()
    r = c.run({"acquisition": {"x": 0.5}})
    before = json.dumps(_rows(p), sort_keys=True)

    class _Alien:
        cycle = 99999
        latent_vector = [1.0]
        similar_keys = ["z"]
    assert c.sync_latent(_Alien()) is False
    assert json.dumps(_rows(p), sort_keys=True) == before


def t_none_never_overwrites_a_real_vector():
    """غنی‌سازیِ شکست‌خورده نباید بردارِ سالمِ قبلی را پاک کند."""
    c, p = _fresh()
    r = c.run({"acquisition": {"x": 0.5}})
    r.latent_vector = [0.4]
    c.sync_latent(r)
    r.latent_vector = None
    assert c.sync_latent(r) is False
    assert _rows(p)[-1]["latent_vector"] == [0.4]


def t_syncing_twice_changes_nothing_the_second_time():
    c, p = _fresh()
    r = c.run({"acquisition": {"x": 0.5}})
    r.latent_vector = [0.7]
    assert c.sync_latent(r) is True
    assert c.sync_latent(r) is False


def t_an_empty_history_is_safe():
    c, _ = _fresh()

    class _R:
        cycle = 1
        latent_vector = [1.0]
        similar_keys = []
    assert c.sync_latent(_R()) is False


# ─── ۳: فلگ و سیم ────────────────────────────────────────────────────────
def t_the_wiring_call_is_flag_gated_and_after_enrichment():
    """ترتیب مهم است: sync باید **بعد از** غنی‌سازی باشد وگرنه دوباره تهی می‌نویسد."""
    src = (_OPS / "wiring.py").read_text("utf-8")
    i = src.index("_enrich_with_latent(result, sources")
    j = src.index("sync_latent(result)", i)
    assert j > i, "sync قبل از غنی‌سازی صدا زده می‌شود"
    between = src[i:j]
    assert FLAG in between, f"فراخوانِ sync پشتِ {FLAG} نیست"


def t_flag_absent_means_off():
    """پیش‌فرضِ خاموش: رفتارِ قبلی بایت‌به‌بایت."""
    src = (_OPS / "wiring.py").read_text("utf-8")
    i = src.index(FLAG)
    assert 'flag("' + FLAG + '")' in src[max(0, i - 40):i + 60], src[i - 40:i + 60]


def t_sync_never_writes_outside_its_own_file():
    """گاردِ نشتی: تنها مسیرِ نوشتنِ این متد همان data_path است."""
    import ast
    tree = ast.parse((_OPS / "neural" / "consolidation.py").read_text("utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "sync_latent")
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(fn) if isinstance(n, ast.Call)}
    for banned in ("write_text", "open", "replace", "unlink"):
        assert banned not in called, f"sync_latent مستقیم می‌نویسد: {banned}"
    assert "_save" in called, "sync_latent اصلاً ذخیره نمی‌کند"


# ─── ۴: لوله، نه واحد ────────────────────────────────────────────────────
# یونیتِ سبز ثابت نمی‌کند مسیرِ زنده کار می‌کند. اولین نسخهٔ این فیکس ۱۰/۱۰ سبز
# بود و روی درختِ زنده **هیچ اثری نداشت** — چون به مسیری وصل بود که هر ۱۲ ساعت
# اجرا می‌شود، در حالی که ۹۸٪ رکوردها از نویسندهٔ هر-۱۰-ضربان می‌آمدند.
# این دو چک همان کشف را قفل می‌کنند: **هر دو** نویسنده باید بردار ثبت کنند.

def _pipeline(fn):
    """یک درختِ ایزولهٔ تازه + استکِ واقعی؛ برمی‌گرداند latent_vector ِ روی دیسک."""
    import importlib
    root = Path(tempfile.mkdtemp())
    ops = root / "_ops"
    (ops / "neural").mkdir(parents=True)
    old = dict(os.environ)
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    os.environ[FLAG] = "1"
    try:
        sys.path.insert(0, str(_OPS))
        wiring = importlib.import_module("wiring")
        cpath = ops / "neural" / "c.json"
        stack = wiring.make_neural_stack() or {}
        stack["consolidation"] = ConsolidationCycle(data_path=cpath)
        fn(wiring, stack)
        if not cpath.exists():
            return None, stack
        rows = json.loads(cpath.read_text("utf-8"))
        rows = rows if isinstance(rows, list) else (rows.get("rows") or [])
        return (rows[-1].get("latent_vector") if rows else None), stack
    finally:
        os.environ.clear()
        os.environ.update(old)


def t_the_frequent_writer_persists_a_vector():
    """`neural_beat` هر ۱۰ ضربان می‌نویسد — نویسندهٔ اصلیِ تاریخچه."""
    lv, stack = _pipeline(
        lambda w, s: w.neural_beat(s, 10, {"acquisition": {"asmr": 0.9, "x": 0.2}}))
    assert lv and len(lv) > 0, "مسیرِ پرتکرار هنوز رکوردِ فقیر می‌نویسد"
    assert "latent_space" in stack, "latent_space کش نشد — هر ۱۰ ضربان از نو ساخته می‌شود"


def t_the_canonical_writer_persists_a_vector():
    """`canonical_consolidation` هر ۷۲۰ ضربان — مسیرِ غنیِ اصلی."""
    from latent_space import SharedLatentSpace
    lv, _ = _pipeline(lambda w, s: w.canonical_consolidation(
        s, acquisition_data={"asmr": 0.9, "x": 0.2}, latent_space=SharedLatentSpace()))
    assert lv and len(lv) > 0, "مسیرِ canonical بردار ثبت نمی‌کند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_latent_persist: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
