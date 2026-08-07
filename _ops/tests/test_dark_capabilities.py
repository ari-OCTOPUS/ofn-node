"""test_dark_capabilities.py — ابزارِ سنجش هم می‌تواند دروغ بگوید.

این فایل یک درسِ خاص را قفل می‌کند، و آن درس از **خودِ همین ماژول** آمد.

`dark_capabilities` ساخته شد تا بگوید کدام قابلیت کد دارد ولی هرگز نمی‌دود.
اولین اجرایش گفت: «۲۵۷ از ۲۵۷ فلگ تاریک». یعنی ادعا کرد هیچ‌چیزِ ارگانیسم
روشن نیست — در حالی که در همان لحظه چهار پروسه بالا بودند و مالک ساعتی قبل
اتاقِ چت را زنده دیده بود.

علت: تابعِ حقیقتِ زنده `state/ORGANISM-STATE.json` را می‌خواند و دنبالِ کلیدِ
`flags` می‌گشت. آن کلید **وجود ندارد**. پس `None` می‌گرفت، مجموعهٔ تهی
برمی‌گرداند، و منبع را `live` اعلام می‌کرد. یک «نمی‌دانم» که خودش را «همه‌چیز
خاموش است» جا زد.

این بدترین شکلِ خطا برای یک ابزارِ سنجش است، چون خروجی‌اش **قابلِ‌باور** بود.
اگر عدد ۱۲۴ می‌بود کسی شک نمی‌کرد؛ ۲۵۷ از ۲۵۷ آن‌قدر مطلق بود که لو رفت. یعنی
نجاتِ ما شدتِ باگ بود، نه دقتِ ما. پس ناوردی باید ساختاری باشد:

    **نبودِ داده هرگز نباید به حکمِ قطعی تبدیل شود.**

تست‌های زیر همان را می‌سنجند، به‌علاوهٔ سه ناوردیِ دیگر که این ابزار بدونشان
بی‌ارزش است: تفکیکِ دروازه از تنظیم، دیدنِ شکافِ بینِ پروسه‌ها، و اینکه هرگز
مقدارِ هیچ کلیدی چاپ نشود.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("dark-capabilities")

import dark_capabilities as dc  # noqa: E402

_ROOT = Path(ENV["ORG_ROOT"] if isinstance(ENV, dict) else ENV)
_N = [0]


def _sandbox(flags_cmd="", snapshots=None, wiring_src=None, modules=None) -> Path:
    """یک `_ops` ِ ساختگیِ کامل — **هر فراخوانی پوشهٔ خودش**.

    ⚠️ نسخهٔ اول همیشه در یک مسیر می‌نوشت. نتیجه: ماژولِ تستِ قبلی سرِ جایش
    می‌ماند و اسکنِ بعدی فلگ‌های او را هم می‌شمرد — دقیقاً همان نشتی که در
    `test_proposal_counter_durable` یک‌بار `3` داد جایی که `2` انتظار می‌رفت.
    """
    _N[0] += 1
    root = _ROOT / f"case{_N[0]}" / "_ops"
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "OCTOPUS-flags.cmd").write_text(flags_cmd, "utf-8")
    (root / "wiring.py").write_text(
        wiring_src if wiring_src is not None else "PAPER_FULL_FLAGS = ()\n", "utf-8")
    for proc, flags in (snapshots or {}).items():
        (root / "state" / f"flags-loaded-{proc}.json").write_text(
            json.dumps({"schema": 1, "flags": flags}, ensure_ascii=False), "utf-8")
    for name, src in (modules or {}).items():
        f = root / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(src, "utf-8")
    return root


_GATE = 'import os\nFLAG = "OCTOPUS_TESTGATE"\n' \
        'def on(): return os.environ.get(FLAG) == "1"\n'


# ── ناوردیِ اصلی: نمی‌دانم ≠ خاموش ──────────────────────────────────────────
def t_a_missing_live_source_is_never_reported_as_live():
    """همان باگِ اصلی، به شکلِ ساختاری.

    بدونِ هیچ snapshotی، منبع باید `absent` باشد. اگر روزی کسی این را به
    «تهی ولی live» برگرداند، این تست قرمز می‌شود.
    """
    res = dc.scan(_sandbox(modules={"m_a.py": _GATE}))
    assert res["live_source"] == "absent", res["live_source"]


def t_b_absent_source_does_not_manufacture_darkness():
    """و مهم‌تر: در نبودِ منبعِ زنده، فلگی که در فایل مسلح است باید ON بماند.

    نسخهٔ باگ‌دار همین را DARK می‌کرد و ۲۵۷ تاریکِ کاذب می‌ساخت.
    """
    root = _sandbox(flags_cmd="set OCTOPUS_TESTGATE=1\n", modules={"m_b.py": _GATE})
    res = dc.scan(root)
    row = next(r for r in res["rows"] if r["flag"] == "OCTOPUS_TESTGATE")
    assert row["state"] == "ON", row
    assert res["n_dark"] == 0, res["dark"]


def t_c_a_corrupt_snapshot_is_not_evidence():
    """snapshotِ خراب هم «نمی‌دانم» است، نه «خاموش» — و نباید بترکد."""
    root = _sandbox(modules={"m_c.py": _GATE})
    (root / "state" / "flags-loaded-organism.json").write_text("{ نه json", "utf-8")
    res = dc.scan(root)
    assert res["live_source"] in ("absent", "unreadable"), res["live_source"]


# ── دروازه در برابر تنظیم ────────────────────────────────────────────────────
def t_d_a_default_makes_it_tuning_not_dark():
    """`os.environ.get("X", "8080")` قابلیت را خاموش نمی‌کند — پیش‌فرض دارد.

    بدونِ این تفکیک، ۳۸ پارامترِ تنظیمی در فهرستِ «تاریک» می‌نشستند و سیگنال
    را زیرِ نویز دفن می‌کردند.
    """
    root = _sandbox(modules={"m_d.py":
                             'import os\nP = os.environ.get("OCTOPUS_TESTPORT", "8080")\n'})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTPORT")
    assert row["state"] == "TUNING", row


def t_da_an_empty_string_default_is_still_a_default():
    """`get(X, "")` تنظیم است، نه دروازه.

    قاعدهٔ اولِ من پیش‌فرضِ «معنادار» می‌خواست و رشتهٔ تهی را نپذیرفت. نتیجه:
    `OCTOPUS_STATE_DIR` با ۱۴ خواننده صدرِ فهرستِ «تاریک» شد — یک مسیر، که
    اصلاً قابلیتی را دروازه نمی‌کند. یک ابزارِ سنجش که صدرِ فهرستش نویز باشد،
    خوانده نمی‌شود؛ پس این ناوردی دربارهٔ **اعتمادپذیری** است نه دقتِ تزئینی.
    """
    root = _sandbox(modules={"m_da.py":
                             'import os\nD = os.environ.get("OCTOPUS_TESTPATH", "").strip()\n'})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTPATH")
    assert row["state"] == "TUNING", row


def t_db_a_truth_comparison_beats_the_default():
    """ولی `get(X, "") == "1"` دروازه است — چون با «۱» مقایسه می‌شود.

    این جفتِ متضادِ تستِ بالاست: اگر کسی قاعده را به «هر پیش‌فرضی ⇒ تنظیم»
    ساده کند، این یکی قرمز می‌شود. یک قاعده بدونِ جفتِ متضادش نصفهٔ قاعده است.
    """
    root = _sandbox(modules={"m_db.py":
                             'import os\ndef on(): return os.environ.get("OCTOPUS_TESTBOOL", "") == "1"\n'})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTBOOL")
    assert row["state"] == "DARK", row


def t_e_one_undefaulted_read_makes_it_a_gate():
    """ولی یک خوانشِ بی‌پیش‌فرض کافی است تا دروازه شمرده شود.

    سخت‌گیرانه‌ترین حالت عمدی است: اگر جایی از کد بدونِ پیش‌فرض می‌خواندش،
    آن‌جا می‌تواند خاموش بماند و آن همان چیزی است که دنبالش هستیم.
    """
    root = _sandbox(modules={
        "m_e1.py": 'import os\nX = os.environ.get("OCTOPUS_TESTMIX", "5")\n',
        "m_e2.py": 'import os\ndef on(): return os.environ.get("OCTOPUS_TESTMIX") == "1"\n'})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTMIX")
    assert row["state"] == "DARK", row
    assert row["n_readers"] == 2, row


# ── شکافِ بینِ پروسه‌ها ──────────────────────────────────────────────────────
def t_f_on_in_some_processes_is_its_own_verdict():
    """جزئی نه ON است نه DARK.

    همین جلسه دیده شد که `surface_policy` فقط از یک cwd resolve می‌شد و از
    چهارتای دیگر نه. اگر جزئی به ON گِرد شود، آن کلاسِ باگ نامرئی می‌ماند؛
    اگر به DARK گِرد شود، نیمی از سیستم که واقعاً کار می‌کند انکار می‌شود.
    """
    root = _sandbox(
        snapshots={"center": {"OCTOPUS_TESTGATE": "1"},
                   "organism": {"OCTOPUS_TESTGATE": "0"}},
        modules={"m_f.py": _GATE})
    res = dc.scan(root)
    row = next(r for r in res["rows"] if r["flag"] == "OCTOPUS_TESTGATE")
    assert row["state"] == "PARTIAL", row
    assert row["on_in_processes"] == ["center"], row
    assert res["n_dark"] == 0, "جزئی نباید تاریک شمرده شود"


def t_g_on_in_every_process_is_on():
    root = _sandbox(
        snapshots={"center": {"OCTOPUS_TESTGATE": "1"},
                   "organism": {"OCTOPUS_TESTGATE": "1"}},
        modules={"m_g.py": _GATE})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTGATE")
    assert row["state"] == "ON", row


# ── پروفایل: غیاب یعنی روشن ─────────────────────────────────────────────────
def t_h_paper_full_membership_counts_as_on():
    """درسِ ۰۷-۲۹: `apply_profile` هر عضوِ `PAPER_FULL_FLAGS` را که در env نباشد
    روی ۱ می‌گذارد. پس غیاب از فایلِ فلگ به‌تنهایی حکمِ خاموشی نیست."""
    root = _sandbox(wiring_src='PAPER_FULL_FLAGS = ("OCTOPUS_TESTGATE",)\n',
                    modules={"m_h.py": _GATE})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTGATE")
    assert row["profile_on"] is True and row["state"] == "ON", row


# ── امنیت و دامنه ────────────────────────────────────────────────────────────
def t_ha_the_repos_own_flag_helper_counts_as_a_read():
    """`flag("X")` — ایدیمِ خانگی — باید دیده شود.

    این بزرگ‌ترین کوریِ نسخهٔ اول بود: اسکنر فقط `os.environ.get` را می‌شناخت،
    پس **۱۱۸ خوانشِ تولیدی** با `flag()` نامرئی بودند در برابرِ ۱۶۹ که دیده
    می‌شدند. نتیجه‌اش دو خطای هم‌زمان بود: فلگ‌هایی که فقط با `flag()` خوانده
    می‌شوند از گزارش غایب بودند، و ۱۴ فلگِ کاملاً سالم «یتیم» اعلام شدند.

    درس: اسکنِ صداکننده باید ایدیمِ **همین مخزن** را بشناسد، نه فقط شکلِ
    کتابیِ کتابخانهٔ استاندارد.
    """
    root = _sandbox(modules={"m_ha.py":
                             'from wiring import flag\ndef on(): return flag("OCTOPUS_TESTHOME")\n'})
    row = next(r for r in dc.scan(root)["rows"] if r["flag"] == "OCTOPUS_TESTHOME")
    assert row["state"] == "DARK", row
    assert row["n_readers"] == 1, row


def t_hb_a_bare_mention_is_not_a_read_but_is_not_an_orphan():
    """تفکیکِ دو پرسش با دو سنجهٔ متفاوت.

    `("mining", "⛏", "OCTOPUS_WIRE_MINING", "business")` در جدولِ منو خوانشِ
    env نیست — پس نباید در فهرستِ دروازه‌ها بیاید. ولی قطعاً یعنی فلگ زنده
    است — پس **نباید** یتیم اعلام شود. نسخهٔ اول هر دو را با یک سنجه جواب داد
    و همین یک آژیرِ کاذبِ ۱۵تایی ساخت.
    """
    root = _sandbox(flags_cmd="set OCTOPUS_TESTMENU=1\n",
                    modules={"m_hb.py": 'MENU = [("x", "OCTOPUS_TESTMENU", "biz")]\n'})
    res = dc.scan(root)
    assert "OCTOPUS_TESTMENU" not in res["orphan_armed"], res["orphan_armed"]
    assert not any(r["flag"] == "OCTOPUS_TESTMENU" for r in res["rows"]), res["rows"]


def t_i_no_value_is_ever_emitted():
    """گزارش فقط **نام** دارد. اگر روزی مقداری چاپ شود، این تست می‌گیردش."""
    root = _sandbox(flags_cmd="set OCTOPUS_TESTGATE=super-secret-value-42\n",
                    modules={"m_i.py": _GATE})
    res = dc.scan(root)
    blob = json.dumps(res, ensure_ascii=False) + dc.render(res)
    assert "super-secret-value-42" not in blob, "مقدار نشت کرد"


def t_j_tests_are_not_counted_as_readers():
    """یک تست که فلگی را ست می‌کند، دلیلِ زنده‌بودنِ آن فلگ نیست.

    وگرنه هر فلگی که تستِ خوبی داشت «مصرف‌کننده دارد» به‌نظر می‌رسید — همان
    «آرتیفکتِ خودساخته شاهد نیست».
    """
    root = _sandbox(modules={
        "tests/test_fake.py": 'import os\nos.environ["OCTOPUS_ONLYINTEST"] = "1"\n'})
    flags = {r["flag"] for r in dc.scan(root)["rows"]}
    assert "OCTOPUS_ONLYINTEST" not in flags, flags


def t_k_a_broken_module_does_not_stop_the_scan():
    """فایلِ نحواً خراب باید رد شود، نه اینکه کلِ اسکن را بخواباند."""
    root = _sandbox(modules={"m_ok.py": _GATE, "m_bad.py": "def ( این نحو ندارد\n"})
    res = dc.scan(root)
    assert any(r["flag"] == "OCTOPUS_TESTGATE" for r in res["rows"]), res["rows"]


def t_l_armed_but_unread_is_reported():
    """فلگی که مسلح است ولی هیچ کدی نمی‌خواندش: تایپو، یا کدی که حذف شده."""
    root = _sandbox(flags_cmd="set OCTOPUS_GHOSTFLAG=1\n", modules={"m_l.py": _GATE})
    assert "OCTOPUS_GHOSTFLAG" in dc.scan(root)["orphan_armed"]


def t_m_a_secret_shaped_flag_name_is_not_a_false_orphan():
    """باگِ اسکنِ ۲۰۲۶-۰۸-۰۷: `is_secret_name` (که برایِ پنهان‌کردنِ *مقدارِ* رازها
    ساخته شده) قبلاً رویِ `mentioned` هم اعمال می‌شد، پس هر فلگی که نامش زیررشتهٔ
    AUTH/TOKEN/KEY/... داشت — حتی وقتی واقعاً و درست خوانده می‌شد — از مجموعهٔ
    «ذکرشده» حذف و در `orphan_armed` گزارش می‌شد. دو نمونهٔ واقعی که این‌طور
    به‌غلط «تایپو/بی‌خواننده» گزارش شدند: `OCTOPUS_HTTP_AUTH` (گیتِ CSRF/Origin
    چهار سرورِ HTTP) و `OCTOPUS_WIRE_CB_TOKEN` (HMACِ callbackِ تلگرام).
    """
    root = _sandbox(
        flags_cmd="set OCTOPUS_HTTP_AUTH=1\n",
        modules={"m_m.py": 'import os\n'
                            'if os.environ.get("OCTOPUS_HTTP_AUTH") == "1":\n'
                            '    pass\n'})
    res = dc.scan(root)
    assert "OCTOPUS_HTTP_AUTH" not in res["orphan_armed"], res["orphan_armed"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_dark_capabilities: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
