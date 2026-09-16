"""test_scanner_provenance — چشمِ دکتر باید **نوع** منتشر کند، نه اسکالرِ برهنه.

گامِ ۱۲ ِ UNIFICATION-DESIGN-2026-08-03. سه چیز اینجا سنجیده می‌شود، و هر سه
با یک جهش قابلِ کشتن‌اند:

  ۱. هر ردیفِ سنجه تمبرِ `_ops/provenance.py` را حمل کند (`source/observed_ts/
     age_s/cadence_s/mode`) **بدونِ اینکه** کلیدهای قدیمیِ
     `value/provenance/receipt/status` — که `ingest.ingest_scan()` می‌خواند —
     تغییرِ نام بدهند.

  ۲. منبعِ غایب/ناخوانا `⬜ UNKNOWN` رندر شود، **نه سبز و نه صفر**. سه ردیف
     پیش از این ساختاراً سبز می‌شدند وقتی فایلشان اصلاً وجود نداشت.

  ۳. `_octopus/state/octopus_state.json` — لفظِ منجمدی که صفر نویسنده و صفر
     خواننده دارد — به‌جای «سبز» بخواند:
         CONSTANT since 2026-07-18T12:04:31…, 0 writers, 0 readers
     و از سنجهٔ هم‌نامِ `self_awareness_pct` (که پوششِ docstring است) جدا شود.

ایزوله: هر تست درختِ خودش را در tempdir می‌سازد و `scan()` هرگز مسیرِ زنده را
نمی‌بیند. `t_the_fixture_is_not_the_live_tree` این را assert می‌کند.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("scanner-provenance")
_OPS = harness.SELF_OPS

# ماژولِ تحتِ آزمون بیرونِ `_ops` زندگی می‌کند؛ بعد از harness وارد می‌شود تا
# `scanner`/`ingest`/`vault` از درختِ خودِ دکتر resolve شوند.
_DOCTOR = _OPS.parent / "OCTOPUS-DOCTOR" / "doctor"
sys.path.insert(0, str(_DOCTOR))

import scanner            # noqa: E402
from ingest import ingest_scan   # noqa: E402
from vault import Vault          # noqa: E402

LIVE_ROOT = Path(r"F:\backup").resolve()
FROZEN_TS = "2026-07-18T12:04:31+10:00"


def _iso(seconds_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat()


def _fixture(td: str, *, control_plane: bool = True, provenance: bool = True,
             signals_age_s: float = 60.0, extra_py: dict | None = None,
             created_at: str = FROZEN_TS, updated_at: str = FROZEN_TS,
             self_awareness: str = "green") -> Path:
    """درختِ ساختگیِ `<td>/_ops` + `<td>/_octopus` — عمداً کم‌ترین چیزِ لازم.

    فایل‌هایی که عمداً **نیستند** (`cardiac-budget.json`, `stress-latest.json`,
    `fugu-quota.json`, …) همان‌هایی‌اند که پیش از این سبزِ کاذب می‌ساختند.
    """
    root = Path(td)
    O = root / "_ops"
    S = O / "state"
    (S / "pulse").mkdir(parents=True, exist_ok=True)
    (S / "cortex").mkdir(parents=True, exist_ok=True)
    if provenance:
        shutil.copy2(_OPS / "provenance.py", O / "provenance.py")
    (S / "ORGANISM-STATE.json").write_text(json.dumps({
        # `ts` ِ سطحِ بالا عمداً **تازه** است — ناوردیِ ۴: این تازگیِ هیچ کلیدی
        # را اثبات نمی‌کند، چون `merge_prev` کلیدِ غایب را back-fill می‌کند.
        "ts": _iso(1),
        "beat": 11862,
        "arbiter": {"effective_period_s": 900.0, "driver": "brake:budget"},
        "cardiac": {"bio_rhythm": {"period_s": 61.0}},
    }, ensure_ascii=False), encoding="utf-8")
    (S / "pulse" / "heart-signals-latest.json").write_text(json.dumps({
        "ts": _iso(signals_age_s),
        "velocity": {"velocity_per_hr": 5.8583, "metronome_share": 0.9644},
        "delta_self": {"delta_self_raw": -0.02573, "delta_self_live": -0.02573},
    }, ensure_ascii=False), encoding="utf-8")
    (S / "cortex" / "self-model.json").write_text(json.dumps({
        "ts": _iso(30), "self_awareness_pct": 87.0}), encoding="utf-8")
    if control_plane:
        cp = root / "_octopus" / "state"
        cp.mkdir(parents=True, exist_ok=True)
        (cp / "octopus_state.json").write_text(json.dumps({
            "schema_version": 1, "created_at": created_at, "updated_at": updated_at,
            "status": {"self_awareness": self_awareness, "planner": "green"},
        }, ensure_ascii=False), encoding="utf-8")
    for rel, src in (extra_py or {}).items():
        p = O / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src, encoding="utf-8")
    return O


def _sig(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def _cp(M):
    return M["control_plane_self_awareness"]


# ── ایزوله ────────────────────────────────────────────────────────────────
def t_the_fixture_is_not_the_live_tree():
    """درسِ «ایزوله را برای مسیرِ واقعی بگذار»: مسیرِ فیکسچر باید بیرونِ vault باشد."""
    with tempfile.TemporaryDirectory() as td:
        O = _fixture(td)
        res = Path(td).resolve()
        assert LIVE_ROOT not in res.parents and res != LIVE_ROOT, \
            f"فیکسچر داخلِ درختِ زنده ساخته شد: {res}"
        before = _sig(Path(td))
        scanner.scan(O, run_suite=False)
        assert _sig(Path(td)) == before, "scan() بایتی در درختِ فیکسچر تغییر داد"


# ── ۱. تمبر روی هر ردیف ───────────────────────────────────────────────────
def t_every_metric_row_carries_a_provenance_stamp():
    """هیچ سنجه‌ای اسکالرِ برهنه نیست — منبع/زمانِ مشاهده/سن/ریتم/حالت اعلام شود."""
    with tempfile.TemporaryDirectory() as td:
        M = scanner.scan(_fixture(td), run_suite=False)["metrics"]
        assert M, "هیچ سنجه‌ای منتشر نشد"
        for name, row in M.items():
            for key in ("source", "observed_ts", "age_s", "cadence_s", "dof", "mode"):
                assert key in row, f"سنجهٔ `{name}` کلیدِ تمبرِ `{key}` را ندارد: {sorted(row)}"
            assert row["mode"] in ("LIVE", "HELD", "CONSTANT", "UNKNOWN"), \
                f"سنجهٔ `{name}` حالتِ ناشناخته دارد: {row['mode']}"


def t_the_keys_ingest_reads_are_untouched():
    """افزودن بله، تغییرِ نام نه — `ingest.ingest_scan()` این چهارتا را می‌خواند."""
    with tempfile.TemporaryDirectory() as td:
        M = scanner.scan(_fixture(td), run_suite=False)["metrics"]
        for name, row in M.items():
            for key in ("value", "provenance", "receipt", "status"):
                assert key in row, f"سنجهٔ `{name}` کلیدِ قدیمیِ `{key}` را از دست داد"


def t_ingest_still_consumes_the_new_row_shape():
    """نویسنده و خواننده با هم سنجیده می‌شوند، نه هرکدام جدا (درسِ ثبت‌شده)."""
    with tempfile.TemporaryDirectory() as td:
        s = scanner.scan(_fixture(td), run_suite=False)
        res = ingest_scan(Vault(Path(td) / "vault"), s)
        assert res["written"], "ingest از شکلِ تازه هیچ نوتی ننوشت"
        note = (Path(td) / "vault" / "50-اسکن‌ها" / f"SCAN-{s['date']}.md").read_text("utf-8")
        assert "CONSTANT since" in note, "رشتهٔ CONSTANT به نوتِ اسکن نرسید"
        assert "| `docstring_coverage_pct` |" in note, "نامِ تازه در جدولِ نوت نیست"


def t_held_is_actually_reachable():
    """اگر HELD هرگز شلیک نکند تمبر تزئینی است — با ظرفِ کهنه اثباتش کن."""
    with tempfile.TemporaryDirectory() as td:
        fresh = scanner.scan(_fixture(td, signals_age_s=60), run_suite=False)["metrics"]
        assert fresh["velocity_per_hr"]["mode"] == "LIVE", \
            f"ظرفِ تازه LIVE نیست: {fresh['velocity_per_hr']['mode']}"
    with tempfile.TemporaryDirectory() as td:
        # cadence اعلام‌شدهٔ velocity_per_hr ‏۳۶۰۰s است ⇒ سنِ ۳ ساعت > ۲×cadence
        stale = scanner.scan(_fixture(td, signals_age_s=10800), run_suite=False)["metrics"]
        assert stale["velocity_per_hr"]["mode"] == "HELD", \
            f"ظرفِ ۳ساعته HELD نشد: {stale['velocity_per_hr']['mode']}"


def t_organism_state_top_level_ts_never_certifies_a_key():
    """ناوردیِ ۴: `ts` ِ سطحِ بالا را `merge_prev` جلو می‌برد — مدرکِ تازگی نیست."""
    with tempfile.TemporaryDirectory() as td:
        M = scanner.scan(_fixture(td), run_suite=False)["metrics"]
        for name in ("beat", "period_s"):
            assert M[name]["mode"] == "UNKNOWN", \
                f"`{name}` از `ts` ِ سطحِ بالا تازگی قرض گرفت: {M[name]['mode']}"
            assert M[name]["value"] is not None, f"`{name}` مقدارش را هم گم کرد"


def t_provenance_absence_is_declared_not_simulated():
    """اگر ماژولِ تمبر نبود، هیچ نسخهٔ دومِ محلیِ قواعد اجرا نشود — صریحاً UNKNOWN.

    استثنای عمدی: `control_plane_self_awareness`. حکمِ CONSTANT آنجا از تمبر
    نمی‌آید، از شمارشِ ارجاع‌ها می‌آید (صفر نویسنده ⇒ نمی‌تواند حرکت کند)، پس
    بدونِ provenance هم معتبر است. ولی همان ردیف موظف است `stamp_mode` را
    `UNKNOWN` و علتش را اعلام کند تا غیابِ تمبر پنهان نشود.
    """
    with tempfile.TemporaryDirectory() as td:
        s = scanner.scan(_fixture(td, provenance=False), run_suite=False)
        assert any("provenance" in u for u in s["unknown"]), \
            f"غیابِ provenance اعلام نشد: {s['unknown']}"
        for name, row in s["metrics"].items():
            if name == "control_plane_self_awareness":
                continue
            assert row["mode"] == "UNKNOWN", f"`{name}` بدونِ ماژولِ تمبر حالت ادعا کرد"
            assert row.get("reason") in ("provenance-module-absent", "source-missing"), \
                f"`{name}` علتِ UNKNOWN را اعلام نکرد: {row.get('reason')}"
        cp = _cp(s["metrics"])
        assert cp["stamp_mode"] == "UNKNOWN" and cp["reason"] == "provenance-module-absent", \
            f"ردیفِ صفحهٔ کنترل غیابِ تمبر را پنهان کرد: {cp.get('stamp_mode')}/{cp.get('reason')}"


# ── ۲. UNKNOWN، رنگِ سوم ───────────────────────────────────────────────────
def t_a_missing_source_renders_unknown_never_green_never_zero():
    """این سه ردیف پیش از این وقتی فایلشان نبود **سبز** می‌شدند."""
    with tempfile.TemporaryDirectory() as td:
        M = scanner.scan(_fixture(td), run_suite=False)["metrics"]
        for name in ("beat_budget_remaining", "organism_stress", "fugu_used"):
            row = M[name]
            assert row["status"] == scanner.COLOR_UNKNOWN, \
                f"`{name}` با منبعِ غایب رنگِ `{row['status']}` گرفت نه ⬜"
            assert row["status"] != "🟢", f"`{name}` با منبعِ غایب سبز شد"
            assert row["value"] == scanner.UNKNOWN_VALUE, \
                f"`{name}` مقدارِ `{row['value']!r}` منتشر کرد نه [UNKNOWN]"
            assert row["value"] != 0 and row["value"] is not None, \
                f"`{name}` غیاب را به صفر ترجمه کرد"
            assert row.get("reason") == "source-missing", \
                f"`{name}` علتِ UNKNOWN را اعلام نکرد: {row.get('reason')}"


def t_a_present_source_keeps_its_own_colour():
    """رنگِ سوم نباید ردیف‌های سالم را هم بشوید."""
    with tempfile.TemporaryDirectory() as td:
        M = scanner.scan(_fixture(td), run_suite=False)["metrics"]
        assert M["docstring_coverage_pct"]["value"] == 87.0, \
            f"مقدارِ خوانده‌شده عوض شد: {M['docstring_coverage_pct']['value']}"
        assert M["docstring_coverage_pct"]["status"] != scanner.COLOR_UNKNOWN, \
            "سنجهٔ موجود اشتباهاً UNKNOWN شد"


# ── ۳. تصادمِ نام و لفظِ منجمد ──────────────────────────────────────────────
def t_the_two_self_awareness_quantities_no_longer_share_a_name():
    with tempfile.TemporaryDirectory() as td:
        M = scanner.scan(_fixture(td), run_suite=False)["metrics"]
        assert "self_awareness_pct" not in M, \
            "نامِ متصادم هنوز منتشر می‌شود"
        assert "docstring_coverage_pct" in M and "control_plane_self_awareness" in M, \
            f"دو کمیت جدا نشدند: {sorted(M)}"
        assert M["docstring_coverage_pct"]["value"] != _cp(M)["value"], \
            "دو کمیتِ بی‌ربط هنوز یک عدد می‌دهند"
        assert all(k in scanner.PROV for k in M), \
            f"سنجهٔ بی‌منشأ منتشر شد: {[k for k in M if k not in scanner.PROV]}"


def t_the_other_modules_key_was_not_renamed():
    """`self_model.py` هنوز `self_awareness_pct` می‌نویسد — فقط سنجهٔ دکتر عوض شد."""
    with tempfile.TemporaryDirectory() as td:
        O = _fixture(td)
        raw = json.loads((O / "state" / "cortex" / "self-model.json").read_text("utf-8"))
        assert "self_awareness_pct" in raw, "فیکسچر کلیدِ ماژولِ دیگر را عوض کرد"
        M = scanner.scan(O, run_suite=False)["metrics"]
        assert M["docstring_coverage_pct"]["value"] == raw["self_awareness_pct"], \
            "سنجهٔ تغییرِ‌نام‌داده دیگر همان کلید را نمی‌خواند"


def t_the_frozen_control_plane_renders_constant_not_green():
    """سنجهٔ پذیرشِ طرح، لفظ‌به‌لفظ."""
    with tempfile.TemporaryDirectory() as td:
        row = _cp(scanner.scan(_fixture(td), run_suite=False)["metrics"])
        assert row["mode"] == "CONSTANT", f"حالتش CONSTANT نیست: {row['mode']}"
        assert row["status"] != "🟢", f"هنوز سبز رندر می‌شود: {row['status']}"
        assert row["status"] == scanner.COLOR_CONSTANT, \
            f"رنگِ CONSTANT نگرفت: {row['status']}"
        assert str(row["value"]).startswith(f"CONSTANT since {FROZEN_TS}"), \
            f"رندرِ اشتباه: {row['value']!r}"
        assert "0 writers, 0 readers" in str(row["value"]), \
            f"شمارِ نویسنده/خواننده در رندر نیست: {row['value']!r}"
        assert row["writers"] == 0 and row["readers"] == 0, \
            f"شمارش غلط: {row['writers']}/{row['readers']}"
        assert row["raw_value"] == "green", "لفظِ خام گم شد"


def t_the_constant_verdict_is_measured_not_asserted():
    """یک نویسندهٔ واقعی ⇒ دیگر CONSTANT نیست. اگر این نشکند عدد hardcode است."""
    writer = ('import json\n'
              'def save(d):\n'
              '    open("_octopus/state/octopus_state.json", "w").write(json.dumps(d))\n')
    with tempfile.TemporaryDirectory() as td:
        row = _cp(scanner.scan(_fixture(td, extra_py={"cp_writer.py": writer}),
                               run_suite=False)["metrics"])
        assert row["writers"] == 1, f"نویسندهٔ واقعی شمرده نشد: {row['writers']}"
        assert row["mode"] != "CONSTANT", "با یک نویسنده هم CONSTANT ماند"
        assert row["value"] == "green", \
            f"با نویسندهٔ موجود هنوز رشتهٔ CONSTANT می‌سازد: {row['value']!r}"


def t_a_docstring_mention_is_not_a_reader():
    """درسِ ثبت‌شده: «grep کامنت را می‌شمارد». تحلیل باید ASTی باشد."""
    only_doc = ('"""این ماژول فقط در docstring اسمِ octopus_state.json را برده."""\n'
                'X = 1\n')
    with tempfile.TemporaryDirectory() as td:
        row = _cp(scanner.scan(_fixture(td, extra_py={"cp_docstring.py": only_doc}),
                               run_suite=False)["metrics"])
        assert row["readers"] == 0 and row["writers"] == 0, \
            f"ذکر در docstring به‌عنوان خواننده شمرده شد: {row['writers']}/{row['readers']}"
        assert row["mode"] == "CONSTANT", "docstring حکمِ CONSTANT را خراب کرد"


def t_the_doctors_own_test_fixtures_are_not_counted():
    """آرتیفکتِ خودساخته شاهد نیست — همین یک‌بار در ۰۸-۰۳ واقعاً اتفاق افتاد.

    لحظه‌ای که همین فایلِ تست زیرِ `_ops/tests/` نشست، رشتهٔ فیکسچرش به‌عنوان
    «نویسنده» شمرده شد و رندرِ درختِ زنده از `0 writers` به `1 writers` پرید.
    شمارش دنبالِ خوانندهٔ **تولیدی** است؛ اگر این استثنا برداشته شود، اسکنر با
    افزودنِ تستِ خودش عددِ خودش را عوض می‌کند.
    """
    writer = ('import json\n'
              'def save(d):\n'
              '    open("_octopus/state/octopus_state.json", "w").write(json.dumps(d))\n')
    # دو فیلترِ **مستقل**: پوشهٔ `tests/` و پیشوندِ نامِ `test_`. هرکدام جدا
    # سنجیده می‌شود، وگرنه یکی می‌تواند بی‌صدا حذف شود و دیگری پنهانش کند.
    for label, rel in (("پوشهٔ tests/", "tests/helper_writer.py"),
                       ("پیشوندِ test_", "test_fixture_writer.py")):
        with tempfile.TemporaryDirectory() as td:
            row = _cp(scanner.scan(_fixture(td, extra_py={rel: writer}),
                                   run_suite=False)["metrics"])
            assert row["writers"] == 0, \
                f"{label}: فیکسچرِ تست نویسندهٔ تولیدی شمرده شد ({row['writers']})"
            assert row["mode"] == "CONSTANT", f"{label}: حکمِ CONSTANT خراب شد"


def t_a_real_reader_is_counted():
    """جهتِ دومِ همان قاعده — وگرنه شمارنده فقط بلد است صفر بدهد."""
    reader = ('import json\n'
              'def load():\n'
              '    return json.loads(open("_octopus/state/octopus_state.json").read())\n')
    with tempfile.TemporaryDirectory() as td:
        row = _cp(scanner.scan(_fixture(td, extra_py={"cp_reader.py": reader}),
                               run_suite=False)["metrics"])
        assert (row["writers"], row["readers"]) in ((0, 1), (1, 0)), \
            f"ارجاعِ واقعی اصلاً شمرده نشد: {row['writers']}/{row['readers']}"
        assert row["writers"] + row["readers"] == 1, "ارجاع دوبار شمرده شد"


def t_the_stamp_alone_would_have_called_it_live():
    """شفافیتِ اختلاف: حالتِ خامِ تمبر پنهان نمی‌شود، کنارِ حکم می‌ماند."""
    with tempfile.TemporaryDirectory() as td:
        row = _cp(scanner.scan(_fixture(td), run_suite=False)["metrics"])
        assert row.get("mode_rule") == "zero-writers", \
            f"قاعدهٔ حکم اعلام نشد: {row.get('mode_rule')}"
        assert row.get("stamp_mode") and row["stamp_mode"] != "CONSTANT", \
            f"حکم فقط تکرارِ تمبر است، پس کارِ تازه‌ای نمی‌کند: {row.get('stamp_mode')}"


def t_a_missing_control_plane_file_is_unknown_not_green():
    with tempfile.TemporaryDirectory() as td:
        row = _cp(scanner.scan(_fixture(td, control_plane=False),
                               run_suite=False)["metrics"])
        assert row["status"] == scanner.COLOR_UNKNOWN, \
            f"فایلِ غایب رنگِ `{row['status']}` گرفت"
        assert row["value"] == scanner.UNKNOWN_VALUE, f"مقدار جعل شد: {row['value']!r}"


def t_a_capped_reference_scan_yields_unknown_not_a_number():
    """«اسکنی که به سقف خورده عدد تولید نمی‌کند» — حتی اگر عددی در دست داشته باشد."""
    old = scanner.REF_MAX_FILES
    scanner.REF_MAX_FILES = 0
    try:
        with tempfile.TemporaryDirectory() as td:
            row = _cp(scanner.scan(_fixture(td), run_suite=False)["metrics"])
            assert row["status"] == scanner.COLOR_UNKNOWN, \
                f"اسکنِ بریده‌شده رنگِ `{row['status']}` داد"
            assert row["value"] == scanner.UNKNOWN_VALUE, \
                f"اسکنِ بریده‌شده عدد منتشر کرد: {row['value']!r}"
    finally:
        scanner.REF_MAX_FILES = old


def t_the_frozen_literal_becomes_a_finding():
    """سبزی که نمی‌تواند قرمز شود یک نقص است، نه یک وضعیت."""
    with tempfile.TemporaryDirectory() as td:
        s = scanner.scan(_fixture(td), run_suite=False)
        ids = {f["id"] for f in s["findings"]}
        assert "F-AUTO-FROZEN-CONTROL-PLANE" in ids, f"یافته ثبت نشد: {sorted(ids)}"
        body = next(f for f in s["findings"]
                    if f["id"] == "F-AUTO-FROZEN-CONTROL-PLANE")["body"]
        assert FROZEN_TS in body and "0 نویسنده / 0 خواننده" in body, \
            f"بدنهٔ یافته شاهد ندارد: {body[:200]}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_scanner_provenance: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
