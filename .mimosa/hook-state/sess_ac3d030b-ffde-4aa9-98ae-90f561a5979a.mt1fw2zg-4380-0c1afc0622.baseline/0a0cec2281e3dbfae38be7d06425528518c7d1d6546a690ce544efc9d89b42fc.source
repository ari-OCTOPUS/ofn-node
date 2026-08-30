"""test_probe_predicate_rule — «صفر» و «نمی‌دانم» نباید یک‌شکل رندر شوند.

گامِ ۳ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C2). دو چیز اینجا قفل می‌شود، به
همین ترتیبِ اهمیت:

  ۱. **قاعده** — `predicate_never_matches`: هر فیلتری که روی ذخیرهٔ **ناتهی** صفر
     رکورد بگیرد، یک نقصِ گزارش‌شدنی است. این کلاسِ باگ را می‌گیرد، نه یک نمونه را.
  ۲. **نمونه** — `tg_stale_delivery`: روی `delivery=PENDING` فیلتر می‌کرد در حالی
     که هیچ رکوردی چنین نبود، پس صفرِ تمیز می‌داد و ۲۰ کارتِ راکد (قدیمی‌ترین
     هشت‌روزه) نامرئی بودند.

ترتیب مهم است و سند صریح خواسته: قاعده باید **پیش از** رفعِ نمونه روی همان
predicateِ خراب شلیک کند — این اثبات می‌کند قاعده نمونه را بی‌راهنمایی می‌گیرد.
اینجا با یک اعلانِ خرابِ ساختگی همان را بازتولید می‌کنیم.

ایزوله: `opslib.STATE_DIR` موقتاً به فیکسچر اشاره می‌کند و در `finally`
برمی‌گردد. صفر بایتِ تغییر در `_ops/state/` واقعی.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("probe-predicate-rule")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import c6_probes as C  # noqa: E402
import lifecycle_fold as LF   # noqa: E402


def _fixture(records):
    root = Path(tempfile.mkdtemp(prefix="probe-rule-"))
    assert str(_OPS).lower() not in str(root).lower(), f"fixture inside live tree: {root}"
    (root / "pulse").mkdir(parents=True)
    (root / "pulse" / "pending-cards.json").write_text(
        json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return root


def _with_state(root, fn):
    """`opslib.STATE_DIR` را موقتاً جابه‌جا می‌کند و همیشه برمی‌گرداند."""
    saved = opslib.STATE_DIR
    try:
        opslib.STATE_DIR = root
        return fn()
    finally:
        opslib.STATE_DIR = saved


def _cards(n_stalled, n_decided, field="decision"):
    out = {}
    for i in range(n_stalled):
        out[f"rfc:S{i}"] = {"kind": "rfc", "rfc_id": f"S{i}", "delivery": "SENT",
                            field: "SUBMITTED", "created_ts": "1785000000"}
    for i in range(n_decided):
        out[f"rfc:D{i}"] = {"kind": "rfc", "rfc_id": f"D{i}", "delivery": "SENT",
                            field: "DECIDED", "created_ts": "1785600000"}
    return out


# ───────────────────────── ۱. قاعده ─────────────────────────

def t_rule_fires_on_a_dead_predicate():
    """اعلانی که روی ذخیرهٔ ناتهی هیچ نمی‌گیرد باید گزارش شود."""
    root = _fixture(_cards(2, 3))
    saved = C.PROBES["tg_stale_delivery"].get("reads")
    try:
        # همان اعلانِ خرابِ تاریخی را بازتولید کن
        C.PROBES["tg_stale_delivery"]["reads"] = {
            "path": "pulse/pending-cards.json", "field": "delivery",
            "expected_values": ["PENDING"]}
        r = _with_state(root, C.PROBES["predicate_never_matches"]["measure"])
        assert r["count"] >= 1, f"قاعده روی predicate مرده شلیک نکرد: {r}"
        assert "tg_stale_delivery" in r["detail"], r["detail"]
        assert "matches 0/5" in r["detail"], r["detail"]
    finally:
        C.PROBES["tg_stale_delivery"]["reads"] = saved
        shutil.rmtree(root, ignore_errors=True)


def t_rule_is_silent_on_a_live_predicate():
    """جفتِ لازم: اعلانِ درست نباید گزارش شود، وگرنه قاعده فقط پرسروصداست."""
    root = _fixture(_cards(2, 3))
    try:
        r = _with_state(root, C.PROBES["predicate_never_matches"]["measure"])
        assert r["count"] == 0, f"قاعده روی predicate زنده شلیک کرد: {r['detail']}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_rule_ignores_an_empty_store():
    """صفر روی ذخیرهٔ تهی صادقانه است و نباید نقص شمرده شود."""
    root = _fixture({})
    try:
        r = _with_state(root, C.PROBES["predicate_never_matches"]["measure"])
        assert r["count"] == 0, f"ذخیرهٔ تهی نباید نقص شمرده شود: {r['detail']}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_rule_catches_a_field_absent_from_every_record():
    """فیلدی که در هیچ رکوردی نیست هم یک predicate مرده است."""
    root = _fixture(_cards(2, 1, field="verdict_state"))   # decision وجود ندارد
    try:
        r = _with_state(root, C.PROBES["predicate_never_matches"]["measure"])
        assert r["count"] >= 1, r
        assert "in 0/3 records" in r["detail"], r["detail"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_every_probe_with_reads_declares_all_three_keys():
    """اعلانِ ناقص یعنی قاعده بی‌صدا ردش می‌کند — گاردِ ساختاری."""
    for name, spec in C.PROBES.items():
        decl = spec.get("reads")
        if decl is None:
            continue
        for key in ("path", "field", "expected_values"):
            assert key in decl, f"{name}.reads کلیدِ {key} را ندارد: {decl}"


# ───────────────────────── ۲. نمونه ─────────────────────────

def t_instance_counts_the_real_backlog():
    """جهشِ سند، حالتِ اول: یک راکد ⇒ ۱."""
    root = _fixture(_cards(1, 2))
    try:
        r = _with_state(root, C.PROBES["tg_stale_delivery"]["measure"])
        assert r["count"] == 1, r
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_instance_returns_zero_when_all_decided():
    """جهشِ سند، حالتِ دوم: همه DECIDED ⇒ ۰ (و این صفر صادقانه است)."""
    root = _fixture(_cards(0, 3))
    try:
        r = _with_state(root, C.PROBES["tg_stale_delivery"]["measure"])
        assert r["count"] == 0, r
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_instance_returns_unknown_when_the_field_is_renamed():
    """جهشِ سند، حالتِ سوم — بارِ اصلی: کلیدِ غایب ⇒ -1، **نه ۰**."""
    root = _fixture(_cards(2, 1, field="decision_state"))
    try:
        r = _with_state(root, C.PROBES["tg_stale_delivery"]["measure"])
        assert r["count"] == -1, f"کلیدِ غایب باید UNKNOWN بدهد نه صفر: {r}"
        assert "UNKNOWN" in r["detail"], r["detail"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_instance_reports_the_oldest():
    """مالک باید بداند قدیمی‌ترین چند وقت است منتظر است."""
    root = _fixture(_cards(2, 0))
    try:
        r = _with_state(root, C.PROBES["tg_stale_delivery"]["measure"])
        assert "oldest=" in r["detail"], r["detail"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_instance_no_longer_mentions_the_dead_field():
    """سند: رشته‌های خودِ پروب هم اصلاح شوند، وگرنه مستندش دروغ می‌ماند."""
    spec = C.PROBES["tg_stale_delivery"]
    blob = " ".join(str(spec.get(k, "")) for k in
                    ("subject", "question", "hypothesis", "expected_artifact"))
    assert "PENDING" not in blob, f"هنوز از delivery=PENDING حرف می‌زند: {blob[:160]}"
    assert spec["reads"]["field"] == "decision", spec["reads"]


def t_probe_does_not_open_the_verdict_db():
    """پروبِ هر-چرخه نباید sqlite را باز کند (mkdir + CREATE TABLE + WAL)."""
    src = (_OPS / "lifecycle_fold.py").read_text("utf-8")
    body = src.split("def stalled_cards(", 1)[1]
    assert "load_rfc_verdicts" not in body, "stalled_cards نباید دفترِ حکم‌ها را باز کند"


def t_stalled_cards_is_isolated():
    """صفر بایتِ تغییر در `_ops/state/` واقعی حینِ اجرا."""
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
    root = _fixture(_cards(1, 1))
    try:
        LF.stalled_cards(root)
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
    print(f"\n{'OK' if not failed else 'FAIL'} test_probe_predicate_rule: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
