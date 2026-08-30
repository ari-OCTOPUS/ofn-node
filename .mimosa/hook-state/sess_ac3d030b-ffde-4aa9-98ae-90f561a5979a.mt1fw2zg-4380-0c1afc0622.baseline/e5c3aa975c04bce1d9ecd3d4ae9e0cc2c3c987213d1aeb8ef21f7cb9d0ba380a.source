"""test_card_spec_contract — یک پاکت، رسیدِ اجباری، و مسیری که تا امروز هرگز پیموده نشد.

گامِ ۱۴ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C5).

## یافته‌ای که این تست را شکل داد

سنجشِ ۰۸-۰۳: هر ۲۱ ردیفِ `rfc_decision` در `RECONCILE_REQUIRED` با `receipt_id=''`
و `operation_key=NULL` نشسته‌اند. برداشتِ اولیه این بود که «مکانیزمِ رسید شکسته
است». **غلط بود.** خواندنِ کد نشان داد `ack_rfc_verdict` از قبل fail-closed است:

    if terminal == "APPLIED" and (not receipt_id or not row[2]):
        con.rollback(); return False

یعنی `APPLIED` هم `receipt_id` ِ ناتهی می‌خواهد هم `operation_key`. مکانیزم درست
است — **مسیر هرگز پیموده نشد**. تنها راهِ رسیدن به پایانه، `mark_rfc_consumed` بود
که با `applied=False` و `receipt_id=""` میان‌بر می‌زد و طبق طراحی در
`RECONCILE_REQUIRED` می‌نشست، بدونِ اینکه هرگز `begin_rfc_apply` صدا زده شود.

پس این تست دو کار می‌کند: **اثبات می‌کند مسیرِ کامل کار می‌کند** (تا امروز هیچ
شاهدی نداشت)، و **میان‌بر را می‌بندد**.

## قرارداد

هر effector — تغییرِ setpoint قلب، آرشیوِ یک دایرکتوری، مسلح‌کردنِ یک فلگ — همان
پاکتِ rfc را می‌گیرد و موظف است:

    ۱. پیش از `begin_rfc_apply` یک `operation_key` بدهد
    ۲. در `ack_rfc_verdict` یک `receipt_id` **ناتهی** بدهد

نبودِ هرکدام ⇒ ردیف در `RECONCILE_REQUIRED` می‌ماند، که درست است — و از گامِ ۱۶
به بعد خودش دوباره کارت می‌شود.

ایزوله: هر فیکسچر در `tempfile` است و «صفر بایتِ تغییر در `_ops/state/`» assert می‌شود.
"""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("card-spec-contract")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pending_card_recovery as pcr   # noqa: E402

#: سه effectorِ نمونه که سند نام می‌برد — سه دامنهٔ کاملاً متفاوت، یک پاکت.
CARDS = [
    ("RFC-setpoint", "تغییرِ setpoint قلب", "op-setpoint-1", "rcpt-setpoint-1"),
    ("RFC-archive", "آرشیوِ یک دایرکتوری", "op-archive-1", "rcpt-archive-1"),
    ("RFC-armflag", "مسلح‌کردنِ یک فلگ", "op-armflag-1", "rcpt-armflag-1"),
]


def _fixture():
    root = Path(tempfile.mkdtemp(prefix="card-spec-"))
    assert str(_OPS).lower() not in str(root).lower(), f"fixture inside live tree: {root}"
    (root / "pulse").mkdir(parents=True, exist_ok=True)
    return root


def _row(root, rfc_id):
    con = sqlite3.connect(str(pcr._rfc_db_path(root)))
    try:
        return con.execute(
            "SELECT verdict,revision,state,receipt_id,operation_key FROM rfc_decision "
            "WHERE rfc_id=?", (rfc_id,)).fetchone()
    finally:
        con.close()


def _walk_full_path(root, rfc_id, summary, op_key, receipt):
    """کلِ چرخه، دقیقاً همان‌طور که یک effectorِ واقعی باید بپیماید."""
    pcr.record_rfc_card(state_dir=root, rfc_id=rfc_id, summary=summary,
                        token=None, delivery="SENT")
    assert pcr.persist_rfc_verdict(state_dir=root, rfc_id=rfc_id,
                                   verdict="merge-approved"), "ثبتِ رأی شکست خورد"
    claims = pcr.claim_rfc_verdicts(state_dir=root, worker_id="contract-test", lease_s=60)
    hit = [c for c in claims if c[0] == rfc_id]
    assert hit, f"کارت claim نشد: {claims}"
    _, _, rev = hit[0]
    if op_key is not None:
        assert pcr.begin_rfc_apply(state_dir=root, rfc_id=rfc_id, revision=rev,
                                   operation_key=op_key), "begin_rfc_apply شکست خورد"
    return pcr.ack_rfc_verdict(state_dir=root, rfc_id=rfc_id, revision=rev,
                               applied=True, receipt_id=receipt), rev


def t_three_different_effectors_share_one_envelope_and_all_reach_applied():
    """سنجهٔ اصلیِ سند: سه کارتِ نامرتبط، یک پاکت، سه رسیدِ **متمایز و ناتهی**."""
    root = _fixture()
    try:
        receipts = set()
        for rfc_id, summary, op_key, receipt in CARDS:
            ok, _ = _walk_full_path(root, rfc_id, summary, op_key, receipt)
            assert ok, f"{rfc_id} به APPLIED نرسید"
            row = _row(root, rfc_id)
            assert row is not None, rfc_id
            assert row[2] == "APPLIED", f"{rfc_id} وضعیتش {row[2]} است نه APPLIED"
            assert row[3] == receipt, f"{rfc_id} رسیدش {row[3]!r} است"
            assert row[4] == op_key, f"{rfc_id} operation_key اش {row[4]!r} است"
            receipts.add(row[3])
        assert len(receipts) == 3, f"رسیدها متمایز نیستند: {receipts}"
        assert "" not in receipts, "رسیدِ تهی به پایانه رسید"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_without_an_operation_key_it_cannot_reach_applied():
    """فیکسچرِ چهارمِ سند: بدونِ `operation_key` باید RECONCILE_REQUIRED بماند."""
    root = _fixture()
    try:
        ok, _ = _walk_full_path(root, "RFC-nokey", "بدونِ کلیدِ عملیات",
                                None, "rcpt-should-not-land")
        assert not ok, "بدونِ operation_key به APPLIED رسید — قرارداد شکست"
        row = _row(root, "RFC-nokey")
        assert row[2] != "APPLIED", f"وضعیت {row[2]} است"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_without_a_receipt_it_cannot_reach_applied():
    """نیمهٔ دومِ قرارداد: رسیدِ تهی هم پایانه نمی‌سازد."""
    root = _fixture()
    try:
        pcr.record_rfc_card(state_dir=root, rfc_id="RFC-norcpt", summary="بی‌رسید",
                            token=None, delivery="SENT")
        pcr.persist_rfc_verdict(state_dir=root, rfc_id="RFC-norcpt", verdict="merge-approved")
        claims = pcr.claim_rfc_verdicts(state_dir=root, worker_id="t", lease_s=60)
        rev = [c for c in claims if c[0] == "RFC-norcpt"][0][2]
        pcr.begin_rfc_apply(state_dir=root, rfc_id="RFC-norcpt", revision=rev,
                            operation_key="op-x")
        ok = pcr.ack_rfc_verdict(state_dir=root, rfc_id="RFC-norcpt", revision=rev,
                                 applied=True, receipt_id="")
        assert not ok, "رسیدِ تهی به APPLIED رسید — قرارداد شکست"
        assert _row(root, "RFC-norcpt")[2] == "RECONCILE_REQUIRED"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_the_legacy_shortcut_is_retired():
    """`mark_rfc_consumed` همان مسیری است که ۲۱ پایانهٔ بی‌رسید را ساخت."""
    src = (_OPS / "outcomes" / "pending_card_recovery.py").read_text("utf-8")
    body = src.split("def mark_rfc_consumed(", 1)[1].split("\ndef ", 1)[0]
    assert "RETIRED" in body or "بازنشسته" in body, \
        "mark_rfc_consumed هنوز به‌عنوان مسیرِ زنده مستند است"


def t_the_legacy_shortcut_has_no_callers():
    """گاردِ قاعده: اگر کسی دوباره میان‌بر را باز کند، اینجا قرمز می‌شود."""
    import ast
    callers = []
    for path in list(_OPS.rglob("*.py")):
        parts = {p.lower() for p in path.parts}
        if parts & {"__pycache__", "tests", "patch_backups"}:
            continue
        try:
            tree = ast.parse(path.read_text("utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                nm = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if nm == "mark_rfc_consumed":
                    callers.append(path.name)
    assert not callers, f"میان‌برِ بازنشسته دوباره صداکننده گرفت: {callers}"


def t_the_shortcut_refuses_instead_of_producing_a_receiptless_terminal():
    """بازنشستگی باید **اثر** داشته باشد، نه فقط یک کامنت."""
    root = _fixture()
    try:
        pcr.record_rfc_card(state_dir=root, rfc_id="RFC-legacy", summary="x",
                            token=None, delivery="SENT")
        pcr.persist_rfc_verdict(state_dir=root, rfc_id="RFC-legacy", verdict="merge-approved")
        got = pcr.mark_rfc_consumed(state_dir=root, rfc_id="RFC-legacy")
        assert got is False, "میان‌برِ بازنشسته هنوز موفق برمی‌گردد"
        row = _row(root, "RFC-legacy")
        assert row[2] != "APPLIED", row
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_contract_run_touches_zero_bytes_of_live_state():
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
    root = _fixture()
    try:
        _walk_full_path(root, "RFC-iso", "ایزوله", "op-iso", "rcpt-iso")
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
    print(f"\n{'OK' if not failed else 'FAIL'} test_card_spec_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
