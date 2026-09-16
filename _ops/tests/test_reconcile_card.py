"""test_reconcile_card — یک کارت برای ۲۱ ردیف، نه ۲۱ کارت؛ و هرگز خودش را نفرستد.

گامِ ۱۵ ِ UNIFICATION-DESIGN-2026-08-03 (نیمهٔ ساختِ C4).

سنجه‌های سند:
  · دقیقاً **یک** کارتِ تجمیعی که N ردیف را خلاصه می‌کند — نه N کارت
  · ذخیرهٔ ناخوانا/غایب ⇒ UNKNOWN، هرگز «۰ بدهی»
  · content-free: شمار، سن، شناسه — هیچ متنی از خلاصهٔ کارت‌های اصلی
  · صفر نوشتن، صفر ارسال — شرطِ فعال‌سازیِ C4 غیرقابلِ چشم‌پوشی است

نکتهٔ حاکم که در تست قفل می‌شود: **این ماژول حق ندارد خودش کارت بسازد.** ساختنِ
محتوا امن است؛ نوشتن در ظرف و فرستادن، رأیِ مالک است.
"""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("reconcile-card")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pending_card_recovery as pcr   # noqa: E402
import reconcile_card as rc           # noqa: E402

NOW = 1_785_800_000.0
DAY = 86400.0


def _fixture(rows):
    """rows: [(rfc_id, state, receipt_id, updated_ts)]"""
    root = Path(tempfile.mkdtemp(prefix="reconcile-card-"))
    assert str(_OPS).lower() not in str(root).lower(), f"fixture inside live tree: {root}"
    con = pcr._rfc_con(root)
    try:
        for rid, state, receipt, ts in rows:
            con.execute(
                "INSERT OR REPLACE INTO rfc_decision"
                "(rfc_id,verdict,revision,state,lease_owner,lease_until,receipt_id,"
                "operation_key,updated_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                (rid, "merge-approved", 1, state, None, None, receipt, None, int(ts)))
        con.commit()
    finally:
        con.close()
    return root


def _stuck(n, base_ts=NOW - 8 * DAY):
    return [(f"RFC-{i:03d}", "RECONCILE_REQUIRED", "", base_ts + i * 3600)
            for i in range(n)]


def t_twentyone_rows_produce_exactly_one_card():
    """سنجهٔ اصلیِ سند: یک کارت، نه ۲۱ تا."""
    root = _fixture(_stuck(21))
    try:
        card = rc.build_aggregate_card(root, now=NOW)
        assert card is not None and not card.get("unknown"), card
        assert card["count"] == 21, card["count"]
        assert card["rfc_id"] == rc.CARD_ID, card["rfc_id"]
        # یک dict، نه یک لیست از کارت‌ها
        assert isinstance(card, dict), type(card)
        assert len(card["rfc_ids"]) <= rc.MAX_IDS, card["rfc_ids"]
        assert card["more"] == 21 - len(card["rfc_ids"]), card
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_the_card_is_idempotent_by_id():
    """دو بار ساختن باید همان شناسه بدهد، وگرنه تجمیع خودش سیل می‌سازد."""
    root = _fixture(_stuck(5))
    try:
        a = rc.build_aggregate_card(root, now=NOW)
        b = rc.build_aggregate_card(root, now=NOW)
        assert a["rfc_id"] == b["rfc_id"] == rc.CARD_ID
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_rows_with_a_receipt_are_not_debt():
    """ردیفی که رسید دارد بدهی نیست — وگرنه کارت دروغ می‌گوید."""
    rows = _stuck(3) + [("RFC-paid", "RECONCILE_REQUIRED", "rcpt-real", NOW - DAY)]
    root = _fixture(rows)
    try:
        card = rc.build_aggregate_card(root, now=NOW)
        assert card["count"] == 3, f"ردیفِ رسیددار شمرده شد: {card['count']}"
        assert "RFC-paid" not in card["rfc_ids"], card["rfc_ids"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_applied_rows_are_not_debt():
    rows = _stuck(2) + [("RFC-done", "APPLIED", "rcpt-1", NOW - DAY)]
    root = _fixture(rows)
    try:
        assert rc.build_aggregate_card(root, now=NOW)["count"] == 2
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_no_debt_returns_none_not_a_card():
    """صفرِ صادقانه: بدهی‌ای نیست ⇒ هیچ کارتی، نه کارتی که می‌گوید صفر."""
    root = _fixture([("RFC-ok", "APPLIED", "rcpt-1", NOW)])
    try:
        assert rc.build_aggregate_card(root, now=NOW) is None
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_absent_store_is_unknown_never_zero_debt():
    """بارِ اصلی: نبودِ داده حکم نیست."""
    root = Path(tempfile.mkdtemp(prefix="reconcile-empty-"))
    try:
        got = rc.build_aggregate_card(root, now=NOW)
        assert isinstance(got, dict) and got.get("unknown") is True, got
        assert got.get("count") is None, "UNKNOWN نباید عددِ بدهی بدهد"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_oldest_is_reported_with_its_age():
    root = _fixture(_stuck(4, base_ts=NOW - 8 * DAY))
    try:
        card = rc.build_aggregate_card(root, now=NOW)
        assert card["oldest_rfc_id"] == "RFC-000", card["oldest_rfc_id"]
        assert 7.5 < card["oldest_age_days"] < 8.5, card["oldest_age_days"]
        assert "روز" in card["summary"], card["summary"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_min_age_threshold_holds_fresh_debt_back():
    root = _fixture(_stuck(3, base_ts=NOW - 600))
    try:
        assert rc.build_aggregate_card(root, now=NOW, min_age_s=3600) is None
        assert rc.build_aggregate_card(root, now=NOW, min_age_s=60) is not None
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_the_card_is_content_free():
    """قاعدهٔ #۷: شمار و سن و شناسه — هیچ متنی از خلاصهٔ کارت‌های اصلی."""
    root = _fixture(_stuck(3))
    try:
        card = rc.build_aggregate_card(root, now=NOW)
        blob = repr(card)
        for forbidden in ("token", "nonce", "owner", "secret", "chat_id"):
            assert forbidden not in blob.lower(), f"«{forbidden}» در کارت نشت کرد"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_the_module_neither_writes_nor_sends():
    """شرطِ فعال‌سازیِ C4: ساختن امن است، فرستادن رأیِ مالک.

    با AST سنجیده می‌شود نه با grepِ متن. نسخهٔ اولِ همین تست متنِ فایل را می‌گرفت
    و روی **docstring** قرمز شد — همان‌جایی که توضیح می‌دهد خروجی «آمادهٔ
    پاس‌دادن به prepare_rfc_card» است. یک نامِ ذکرشده در مستندات، فراخوانی نیست؛
    این دقیقاً همان تلهٔ ثبت‌شدهٔ «گرپِ متن ≠ تحلیلِ کد» است.
    """
    import ast
    src = (_OPS / "outcomes" / "reconcile_card.py").read_text("utf-8")
    tree = ast.parse(src)
    forbidden = {"prepare_rfc_card", "record_rfc_card", "_mutate_store", "send_text",
                 "urlopen", "write_text", "write_bytes", "dump", "dumps_to_file"}
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            nm = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if nm:
                called.add(nm)
    bad = called & forbidden
    assert not bad, f"reconcile_card این‌ها را **صدا می‌زند**: {sorted(bad)} — ساخت، نه ارسال"
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for net in ("requests", "urllib", "http", "socket"):
        assert net not in imported, f"ماژولِ شبکه import شد: {net}"


def t_state_dir_is_mandatory():
    try:
        rc.build_aggregate_card(None)
    except ValueError:
        pass
    else:
        raise AssertionError("پیش‌فرضِ ضمنی به ذخیرهٔ زنده می‌خورد")


def t_building_touches_zero_bytes_of_live_state():
    live = _OPS / "state"
    def snap():
        out = {}
        for p in live.rglob("*"):
            if p.is_file():
                try:
                    st = p.stat(); out[str(p)] = (st.st_size, st.st_mtime_ns)
                except OSError:
                    pass
        return out
    before = snap()
    root = _fixture(_stuck(2))
    try:
        rc.build_aggregate_card(root, now=NOW)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    after = snap()
    changed = [k for k in before if k in after and before[k] != after[k]]
    added = [k for k in after if k not in before]
    assert not changed, f"فایلِ زنده تغییر کرد: {changed[:5]}"
    assert not added, f"فایلِ تازه ساخته شد: {added[:5]}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_reconcile_card: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
