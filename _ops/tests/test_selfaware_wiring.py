"""test_selfaware_wiring.py — قفلِ پنج سیمِ خودآگاهی (اسکنِ ۲۰۲۶-۰۷-۲۷).

شش اسکناترِ فقط‌خواندنی سطحِ خودآگاهی را جارو کردند و ده شکافِ تأییدشده برگشت.
پنج‌تایشان یک‌خطی بودند و همان روز بسته شدند. این فایل نمی‌گذارد باز شوند.

هر تست یک شکستِ **اندازه‌گیری‌شده** را قفل می‌کند، نه یک سناریوی فرضی:
  · `full_awareness_vector` صفتی می‌خواند که وجود نداشت → کلِ حافظهٔ برداری گرسنه.
  · لِینِ اینترنت در ویکی‌پدیا دنبالِ «A08» می‌گشت، نه «perception-bias».
  · تصحیحِ مالک ثبت می‌شد ولی تشخیصِ روزانه هرگز نمی‌خواندش.
  · متنِ خامِ وب بدونِ escape داخلِ پیامِ HTML می‌رفت.
  · هر جلسهٔ گران از صفر شروع می‌کرد و همان نتیجه را دوباره کشف می‌کرد.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "afferent"))
sys.path.insert(0, str(_HERE.parent / "heart"))
sys.path.insert(0, str(_HERE.parent / "doctor"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("selfaware-wiring")

import opslib   # noqa: E402


# ─── ۱: بردارِ آگاهی، ریشهٔ قحطیِ حافظهٔ برداری ──────────────────────────────
def t_the_awareness_vector_is_no_longer_none():
    """یک صفتِ اشتباه، سه ماژول را گرسنه نگه داشته بود: latent-vectors.json هرگز
    ساخته نشد، بازیابی هرگز رخ نداد، BCM ۶۵ قدم با keys={} برداشت."""
    from school_bridge import SchoolBridge
    sb = SchoolBridge()
    v = sb.full_awareness_vector()
    assert v is not None, "بردارِ آگاهی هنوز None است — زنجیرهٔ حافظه گرسنه می‌ماند"
    assert isinstance(v, list) and len(v) > 0, v
    assert all(isinstance(x, (int, float)) for x in v), "بردار عددی نیست"
    assert all(0.0 <= float(x) <= 1.0 for x in v), "خارج از دامنهٔ [0,1]"


def t_the_field_attribute_is_the_real_one():
    """گاردِ رگرسیون علیهِ نامِ صفت — همان چیزی که سه ماه بی‌صدا شکسته بود."""
    from school_bridge import SchoolBridge
    sb = SchoolBridge()
    assert hasattr(sb.field, "a"), "نامِ صفتِ فیلد عوض شده"
    src = (Path(sb.__module__ and SchoolBridge.__module__ or "")).name
    body = Path(sys.modules["school_bridge"].__file__).read_text("utf-8")
    fn = body[body.index("def full_awareness_vector"):]
    fn = fn[:fn.index("\n\n\n")] if "\n\n\n" in fn else fn[:600]
    assert "field.awareness" not in fn, "دوباره صفتِ ناموجود خوانده می‌شود"


# ─── ۲: موضوع، نه شناسهٔ داخلی ──────────────────────────────────────────────
def t_gap_report_returns_titles_not_internal_ids():
    """این خروجی مستقیم به موتورِ جست‌وجوی اینترنت می‌رود."""
    import work_pump
    p = opslib.STATE_DIR / "school-awareness.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "awareness": {"A08": 0.01, "A07": 0.02, "A06": 0.03},
        "titles": {"A08": "perception-bias", "A07": "motivation",
                   "A06": "self-narrative"}}, ensure_ascii=False), "utf-8")
    out = work_pump._exec_gap_report()
    topics = [g["topic"] for g in out["gaps"]]
    assert topics == ["perception-bias", "motivation", "self-narrative"], topics
    assert all(g.get("topic_id", "").startswith("A") for g in out["gaps"]), out
    for t in topics:
        assert not (len(t) == 3 and t[0] == "A" and t[1:].isdigit()), \
            f"شناسهٔ داخلی به موتورِ جست‌وجو می‌رود: {t}"


def t_gap_report_falls_back_to_the_id_when_titles_are_absent():
    """سازگارِ عقب‌رو: فایلِ کهنهٔ بدونِ titles نباید بترکاند."""
    import work_pump
    p = opslib.STATE_DIR / "school-awareness.json"
    p.write_text(json.dumps({"awareness": {"A01": 0.1}}, ensure_ascii=False), "utf-8")
    out = work_pump._exec_gap_report()
    assert out["gaps"][0]["topic"] == "A01", out
    assert out["ok"] is True


def t_school_bridge_persists_titles():
    from school_bridge import SchoolBridge
    sb = SchoolBridge()
    sb._save()
    d = json.loads(sb.state_path.read_text("utf-8"))
    assert "titles" in d and d["titles"], "عنوان‌ها ذخیره نمی‌شوند"
    k = next(iter(d["titles"]))
    assert d["titles"][k] and d["titles"][k] != k, d["titles"]


# ─── ۳: تصحیحِ مالک باید به تشخیص برسد ──────────────────────────────────────
def t_owner_corrections_reach_the_daily_diagnosis():
    """ادعای اتاقِ آینه («واردِ هر چرخهٔ خودشناسی می‌شود») تا امروز فقط برای
    contextِ خودِ اتاق درست بود — snapshot این فایل را باز نمی‌کرد."""
    import self_knowledge as sk
    p = opslib.STATE_DIR / "doctor" / "owner-corrections.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"ts": "2026-07-27T13:21:00", "text": "نه، تمرکزت اشتباه است"},
                            ensure_ascii=False) + "\n", "utf-8")
    s = sk.snapshot()
    assert "owner_corrections" in s, "تصحیح به snapshot نمی‌رسد"
    assert "تمرکزت اشتباه" in " ".join(s["owner_corrections"]), s["owner_corrections"]
    # و باید همان چرخه تشخیص را تکان بدهد، نه پشتِ cached:no-change بماند
    assert "corrections" in sk._hash_digest(s), \
        "تصحیح در hash نیست — تا تغییرِ بی‌ربطِ بعدی یخ می‌ماند"


def t_a_corrupt_correction_line_does_not_blind_the_rest():
    import self_knowledge as sk
    p = opslib.STATE_DIR / "doctor" / "owner-corrections.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)   # تستِ همسایه ممکن است پاکش کرده باشد
    p.write_text(json.dumps({"text": "اولی"}, ensure_ascii=False) + "\n"
                 + '{"text": "نصفه\n'
                 + json.dumps({"text": "دومی"}, ensure_ascii=False) + "\n", "utf-8")
    s = sk.snapshot()
    got = s.get("owner_corrections") or []
    assert "اولی" in got and "دومی" in got, got


def t_no_corrections_file_is_not_an_error():
    import self_knowledge as sk
    p = opslib.STATE_DIR / "doctor" / "owner-corrections.jsonl"
    if p.exists():
        p.unlink()
    s = sk.snapshot()
    assert "owner_corrections" not in s
    assert isinstance(sk._hash_digest(s), dict)


# ─── ۴: متنِ وب هرگز خامِ HTML نرود ─────────────────────────────────────────
def t_web_text_is_escaped_before_html_send():
    """یک عنوانِ صفحه با `<` کلِ پیام را ۴۰۰ می‌کرد — و چون رکوردها **قبل از**
    ارسال «دیده‌شده» علامت می‌خورند، یک عنوانِ مسموم صف را برای همیشه دفن می‌کرد."""
    import discoveries as dsc
    p = dsc.PATH if hasattr(dsc, "PATH") else None
    rows = [{"kind": "research", "summary": '<script>x</script> & "quoted"',
             "ts": "2026-07-27T00:00:00"}]
    real = dsc.recent
    dsc.recent = lambda n=5: rows
    try:
        out = dsc.lines(1)[0]
        assert "<script>" not in out, f"HTML خام به تلگرام می‌رود: {out}"
        assert "&lt;script&gt;" in out, out
        assert "&amp;" in out, out
    finally:
        dsc.recent = real


# ─── ۵: جلسهٔ گران باید جلسهٔ قبل را بخواند ─────────────────────────────────
def t_a_deep_session_recalls_its_own_previous_sessions():
    import deep_think as dt
    dt.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    dt.LEDGER.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
        {"ts": "2026-07-27T00:30:00", "topic": dt.TOPIC_SELF, "ok": True,
         "text": "جفتِ هبی را قرنطینه کن"},
        {"ts": "2026-07-27T06:30:00", "topic": dt.TOPIC_BUSINESS, "ok": True,
         "text": "پیش‌نویس را بفرست"},
        {"ts": "2026-07-27T12:30:00", "topic": dt.TOPIC_SELF, "ok": False,
         "text": "شکست"},
    ]) + "\n", "utf-8")
    p = dt.build_prompt(dt.TOPIC_SELF)
    assert "جفتِ هبی را قرنطینه کن" in p, "جلسهٔ قبلیِ همین موضوع را نمی‌بیند"
    assert "پیش‌نویس را بفرست" not in p, "جلسهٔ موضوعِ دیگر نشت کرد"
    assert "شکست" not in p, "جلسهٔ ناموفق به‌عنوانِ حرفِ قبلی نقل شد"
    assert "حرفِ تکراری نزن" in p, "به مدل گفته نشده تکرار نکند"


def t_an_empty_ledger_leaves_the_prompt_untouched():
    import deep_think as dt
    if dt.LEDGER.exists():
        dt.LEDGER.unlink()
    p = dt.build_prompt(dt.TOPIC_SELF)
    assert "قبلاً_در_همین_موضوع" not in p
    assert len(p) > 100


def t_a_corrupt_ledger_line_does_not_kill_recall():
    import deep_think as dt
    dt.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    dt.LEDGER.write_text(
        json.dumps({"ts": "2026-07-27T01:00:00", "topic": dt.TOPIC_SELF,
                    "ok": True, "text": "حرفِ سالم"}, ensure_ascii=False) + "\n"
        + '{"ts": "بریده\n', "utf-8")
    p = dt.build_prompt(dt.TOPIC_SELF)
    assert "حرفِ سالم" in p


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_selfaware_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
