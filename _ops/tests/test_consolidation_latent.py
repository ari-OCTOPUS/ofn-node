#!/usr/bin/env python3
"""test_consolidation_latent.py — تستِ latent integration در canonical_consolidation.

Phase 2: consolidation با latent_space → latent_vector + similar_keys.
$0 آفلاین: neural_stack mock + latent_space tmpdir.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness
ENV = harness.setup("consolidation-latent")   # ایزولاسیون — alert/state به vault موقت، نه واقعی

import numpy as np
from neural.latent_space import SharedLatentSpace
from neural.consolidation import ConsolidatedInsight


def _make_stack(latent_space=None):
    """Fake neural_stack با consolidation mock."""
    cycle = MagicMock()
    cycle.run.return_value = ConsolidatedInsight(
        cycle=1, insights=["test insight"],
        verified_sources=["acquisition"], discarded_sources=[])
    return {"consolidation": cycle, "latent_space": latent_space}


def _make_school_mock(mean_awareness=0.5, full_vector=None):
    """Mock school_bridge."""
    sb = MagicMock()
    sb.mean_awareness.return_value = mean_awareness
    sb.full_awareness_vector.return_value = full_vector
    return sb


def t_with_latent_space_has_vector():
    """consolidation با latent_space → latent_vector not None."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test.json"))
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"revenue": 42.0}, latent_space=ls)
    assert result is not None
    assert isinstance(result, ConsolidatedInsight)
    assert result.latent_vector is not None, "latent_vector باید None نباشد"
    assert len(result.latent_vector) == 32, f"expected R^32, got {len(result.latent_vector)}"


def t_without_latent_space_backward_compat():
    """consolidation بدون latent_space → latent_vector=None (backward compat)."""
    import wiring
    stack = _make_stack(latent_space=None)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"revenue": 42.0}, latent_space=None)
    assert result is not None
    assert result.latent_vector is None, "بدون latent_space → باید None"


def t_similar_keys_populated():
    """بعد از ۲ cycle → similar_keys باید history را پیدا کند."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test2.json"))
    stack = _make_stack(latent_space=ls)
    # cycle 1
    r1 = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 10.0}, latent_space=ls)
    assert r1 is not None
    # cycle 2 (باید cycle-1 را در similar_keys بیابد)
    stack["consolidation"].run.return_value = ConsolidatedInsight(
        cycle=2, insights=["test2"], verified_sources=["acquisition"],
        discarded_sources=[])
    r2 = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 20.0}, latent_space=ls)
    assert r2 is not None
    # ۲۰۲۶-۰۷-۳۰ — این assert قبلاً «ممکن None باشد یا list» بود، یعنی چه بازیابی
    # کار می‌کرد چه نمی‌کرد سبز می‌شد. باگِ واقعی همان‌جا زنده ماند: `nearest(cycle_key)`
    # قبل از embedِ همان کلید صدا زده می‌شد و برای کلیدِ غایب [] می‌داد ⇒ similar_keys
    # همیشه خالی. حالا **محتوا** سنجیده می‌شود، نه صرفاً نوع.
    assert isinstance(r2.similar_keys, list), r2.similar_keys
    assert r2.similar_keys, "بازیابی باید سیکلِ قبلی را پیدا کند (نه لیستِ خالی)"
    assert any("cycle-1" in k for k in r2.similar_keys),         f"cycle-1 باید در similar_keys باشد: {r2.similar_keys}"
    # خودارجاعی ممنوع: کلیدهای خودِ همین سیکل نباید برگردند
    assert not any(k == "cycle-2" or k.startswith("cycle-2:") for k in r2.similar_keys),         f"similar_keys نباید کلیدِ خودِ سیکل را داشته باشد: {r2.similar_keys}"


def t_school_awareness_encoded():
    """school awareness با latent_space → encoded."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test3.json"))
    stack = _make_stack(latent_space=ls)
    sb = _make_school_mock(mean_awareness=0.7, full_vector=[0.1, 0.3, 0.5, 0.7])
    result = wiring.canonical_consolidation(
        stack, school_bridge=sb, latent_space=ls)
    assert result is not None
    assert result.latent_vector is not None
    # school encoding باید در latent space ذخیره شده باشد
    school_keys = ls.keys_by_layer("school")
    assert len(school_keys) >= 1, "school encoding باید ذخیره شده باشد"


def t_multiple_sources_integrated():
    """چند source → latent_vector ترکیبی."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test4.json"))
    cycle = MagicMock()
    cycle.run.return_value = ConsolidatedInsight(
        cycle=1, insights=["multi"], verified_sources=["acquisition", "doctor_archive"],
        discarded_sources=[])
    stack = {"consolidation": cycle, "latent_space": ls}
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 50.0},
        doctor_archive=[{"outcome": "approved"}],
        latent_space=ls)
    assert result is not None
    assert result.latent_vector is not None
    # هر دو source باید encoded شده باشند
    assert ls.keys_by_layer("acquisition") != []
    assert ls.keys_by_layer("doctor") != []


def t_retrieval_finds_previous():
    """embedding ذخیره‌شده قابل retrieval است."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test5.json"))
    stack = _make_stack(latent_space=ls)
    # cycle 1 — ذخیره
    r1 = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 10.0}, latent_space=ls)
    assert r1 is not None
    # cycle key باید در space باشد
    cycle_key = "cycle-1"
    assert ls.get(cycle_key) is not None, "cycle embedding باید ذخیره شده باشد"
    # retrieval
    nn = ls.nearest(cycle_key, top_k=3)
    assert len(nn) >= 1


def t_latent_fail_soft():
    """اگر latent encoding crash کند → latent_vector=None ولی result هنوز valid."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    # latent space با dim=1 (بسیار کوچک) — ممکن باعث مشکل شود ولی نباید crash کند
    ls = SharedLatentSpace(dim=1, persist_path=str(Path(td) / "test6.json"))
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 42.0}, latent_space=ls)
    # حتی اگر latent encoding fail شود، result باید valid باشد
    assert result is not None
    assert isinstance(result, ConsolidatedInsight)
    # insights باید هنوز تولید شده باشند
    assert len(result.verified_sources) >= 1 or result.latent_vector is not None


def t_fold_never_clobbers_a_latent_row():
    """۲۰۲۶-۰۷-۳۰ — مسیرِ زندهٔ fold (compress خاموش) نباید ردیفِ دارای latent_vector
    را لِه کند. ۲۰۲۶-۰۸-۱۵ — شرطِ «هرگز مقصد نشو» به «fold کن ولی بردار را حفظ کن»
    تعدیل شد (از سیکلِ ۵۳۷ همهٔ ردیف‌ها بردار دارند و شرطِ قدیمی dedup را فریز
    کرده بود — C-012/T1b). هستهٔ حفاظت همان است: بردارِ دادهٔ کمیاب دست‌نخورده."""
    import json as _json
    import tempfile as _tf
    from neural.consolidation import ConsolidationCycle
    td = _tf.mkdtemp()
    hist = Path(td) / "consolidation.json"
    src = {"school_awareness": {"mean_awareness": 0.42}}

    # سیکلِ ۱: ردیفِ اول ساخته می‌شود
    c1 = ConsolidationCycle(data_path=str(hist))
    c1.run(src)
    rows = _json.loads(hist.read_text("utf-8"))
    assert len(rows) == 1, rows

    # همان محتوا دوباره و بدونِ بردار → باید fold شود (رفتارِ موجود، حفظ می‌شود)
    ConsolidationCycle(data_path=str(hist)).run(src)
    rows = _json.loads(hist.read_text("utf-8"))
    assert len(rows) == 1, f"بدونِ بردار باید fold شود: {len(rows)}"
    assert int(rows[-1].get("repeats", 1)) >= 2, rows[-1]

    # حالا ردیفِ آخر بردار می‌گیرد (شبیه‌سازیِ sync_latent)
    rows[-1]["latent_vector"] = [0.1, 0.2, 0.3]
    hist.write_text(_json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    # ۲۰۲۶-۰۸-۱۵ (جاروی تست T1b) — قرارداد وارونه شد: این بار هم **باید** fold شود.
    # اندازه‌گیریِ زنده: از سیکلِ ۵۳۷ (2026-07-28، روشن‌شدنِ OCTOPUS_WIRE_LATENT_PERSIST)
    # هر ردیفی بردار دارد (۸۹/۸۹) — قانونِ قدیمیِ «مقصدِ fold نباید بردار داشته باشد»
    # یعنی «هیچ‌وقت تا نشو»، و نتیجه‌اش ۲۰ ردیفِ عیناً یکسانِ پیاپی در فایلِ زنده بود
    # (C-012 / consolidation راکد). fold بردار را حذف نمی‌کند (فقط repeats/last_cycle
    # می‌افزاید) و sync_latent از طریقِ تطبیقِ last_cycle بردارِ تازه را همان‌جا
    # می‌نویسد — پوششِ خودِ کد برای ردیفِ تا-شده. تستِ کاملِ این قرارداد:
    # test_consolidation_fold_rich.py
    ConsolidationCycle(data_path=str(hist)).run(src)
    rows2 = _json.loads(hist.read_text("utf-8"))
    assert len(rows2) == 1, f"fold باید داخلِ ردیفِ غنی ادامه یابد: {len(rows2)} ردیف"
    assert rows2[0].get("latent_vector") == [0.1, 0.2, 0.3], \
        f"بردارِ ردیفِ مقصد باید دست‌نخورده بماند: {rows2[0].get('latent_vector')}"
    assert int(rows2[0].get("repeats", 1)) >= 3, rows2[0]


def t_cycle_ordinal_survives_restart():
    """۲۰۲۶-۰۷-۳۰ — شمارهٔ سیکل نباید به **شمارِ ردیف‌ها** pin شود.

    `__init__` شمارنده را از `len(self._history)` می‌گرفت. چون دورِ هم‌محتوا داخلِ
    ردیفِ قبلی تا می‌شود، شمارِ ردیف‌ها رشد نمی‌کند، پس هر ری‌استارتِ پروسه همان
    شماره را دوباره می‌ساخت. اثرِ روی فایلِ زنده: (cycle=537, last_cycle=538,
    repeats=13) — سیزده شلیکِ جدا، همه با مُهرِ «۵۳۸». و چون کلیدِ بازیابی
    `f"cycle-{result.cycle}"` است، `latent_space.embed` همان کلید را بازنویسی
    می‌کرد و ایندکس هرگز از تعدادِ ordinalهای متمایز بالاتر نمی‌رفت.

    این تست عمداً **پنج** instance می‌سازد نه دو: با یک ردیف روی دیسک،
    `len(history)` تصادفاً ۱ است و اولین بازخوانی هم ۲ می‌دهد. pin از instanceِ
    سوم به بعد خودش را نشان می‌دهد — دقیقاً همان شکلی که در فایلِ زنده دیده شد.
    """
    import json as _json
    import tempfile as _tf
    from neural.consolidation import ConsolidationCycle
    hist = Path(_tf.mkdtemp()) / "consolidation.json"
    src = {"school_awareness": {"mean_awareness": 0.42}}

    ordinals = [ConsolidationCycle(data_path=str(hist)).run(src).cycle]
    for _ in range(4):                        # چهار «ری‌استارتِ پروسه»
        ordinals.append(ConsolidationCycle(data_path=str(hist)).run(src).cycle)

    rows = _json.loads(hist.read_text("utf-8"))
    assert len(rows) == 1, f"فرضِ تست باطل شد — محتوای یکسان باید تا شود: {len(rows)} ردیف"
    assert int(rows[0]["repeats"]) == 5, rows[0]

    # هستهٔ گارد: هر instanceِ بعدی باید **اکیداً** جلوتر از قبلی باشد
    for prev, cur in zip(ordinals, ordinals[1:]):
        assert cur > prev, f"شمارهٔ سیکل جلو نرفت (pin به شمارِ ردیف): {ordinals}"
    assert len(set(ordinals)) == 5, f"۵ شلیک باید ۵ ordinalِ متمایز بدهد: {ordinals}"
    assert ordinals == [1, 2, 3, 4, 5], ordinals
    assert int(rows[0]["last_cycle"]) == 5, rows[0]


def t_seed_never_regresses_below_row_count():
    """۲۰۲۶-۰۷-۳۰ — گاردِ خودِ فیکسِ بالا. seedِ نو (`max(last_cycle)`) روی ردیفی که
    `last_cycle`/`cycle` **ندارد یا None است** صفر می‌دهد و هیچ خطایی هم نمی‌دهد، پس
    `except (TypeError, ValueError)` نمی‌گیردش. بدونِ کف، شمارنده از ۱ از نو شروع
    می‌شد — همان بازاستفادهٔ ordinal که فیکس قرار بود ببندد. اندازه‌گیری‌شده: ۵ ردیفِ
    بی‌کلید → seed=۰ در برابرِ ۵ ِ رفتارِ قبلی."""
    import json as _json
    import tempfile as _tf
    from neural.consolidation import ConsolidationCycle

    def _seed(rows):
        p = Path(_tf.mkdtemp()) / "consolidation.json"
        p.write_text(_json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        return ConsolidationCycle(data_path=p).cycle_count

    # سه شکلِ ردیفِ خراب که هیچ‌کدام استثنا نمی‌دهند
    for label, rows in (
        ("کلیدها غایب", [{"insights": []} for _ in range(5)]),
        ("کلیدها None", [{"cycle": None, "last_cycle": None} for _ in range(5)]),
        ("کلیدها غیرعددی", [{"cycle": "abc", "last_cycle": "abc"} for _ in range(5)]),
    ):
        got = _seed(rows)
        assert got >= len(rows), \
            f"seed زیرِ شمارِ ردیف افتاد ({label}) → بازاستفادهٔ ordinal: {got} < {len(rows)}"

    # و کفِ جدید نباید seedِ درست را خفه کند: تاشدگی باید همچنان جلو بزند
    folded = [{"cycle": i, "last_cycle": i} for i in range(1, 5)] + \
             [{"cycle": 5, "last_cycle": 9}]
    assert _seed(folded) == 9, f"کف نباید last_cycleِ جلوتر را پایین بکشد: {_seed(folded)}"
    assert _seed([]) == 0, "تاریخچهٔ خالی باید صفر بماند"


if __name__ == "__main__":
    failed = harness.run([
        ("latent_space → latent_vector", t_with_latent_space_has_vector),
        ("بدون latent_space → backward compat", t_without_latent_space_backward_compat),
        ("similar_keys از history", t_similar_keys_populated),
        ("school awareness encoded", t_school_awareness_encoded),
        ("multiple sources integrated", t_multiple_sources_integrated),
        ("retrieval finds previous", t_retrieval_finds_previous),
        ("latent fail-soft", t_latent_fail_soft),
        ("fold ردیفِ داری بردار را لِه نمی‌کند", t_fold_never_clobbers_a_latent_row),
        ("شمارهٔ سیکل ری‌استارت را دوام می‌آورد", t_cycle_ordinal_survives_restart),
        ("seed زیرِ شمارِ ردیف نمی‌افتد", t_seed_never_regresses_below_row_count),
    ])
    sys.exit(1 if failed else 0)
