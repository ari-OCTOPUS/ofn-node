"""test_c6_probe_coverage.py — لایهٔ حسِ C6: پوشش، صداقت، و مرزِ «کور» از «تمیز».

یافتهٔ ۲۰۲۶-۰۷-۲۶ که این فایل از آن زاده شد: از ۶ پروبِ موجود، **۵ تا**
`count=-1` می‌دادند (یعنی اصلاً نمی‌توانستند بسنجند) و `produce()` همهٔ آن‌ها را
یکسان با «no-defect» گزارش می‌کرد. یعنی گزارشِ سلامت از لایه‌ای که تقریباً کور
بود. دو تا از آن پنج‌تا باگِ واقعی بودند:
  · `self_audit_redundant_reads` → `mod.main()` صدا می‌زد؛ چنین تابعی وجود ندارد
    (نقطهٔ ورود `run_audit` است) → AttributeError → کوریِ بی‌صدا.
  · `rfc_duplicate_surplus` → به `state/c6/rfcs/` نگاه می‌کرد، مسیری که هرگز
    ساخته نشد؛ انبارِ واقعی `state/doctor/rfcs.json` است.

پس مهم‌ترین قیدِ این فایل `t_blind_probe_never_becomes_a_hypothesis` و
`t_producer_reports_blindness_separately_from_health` است: «نمی‌بینم» هرگز نباید
شبیهِ «نقصی نیست» گزارش شود.

صفر شبکه، صفر نوشتن در درختِ زنده: state به harness هدایت می‌شود.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("c6-probe-coverage")

import c6_probes as cp      # noqa: E402
import c6_producer as prod  # noqa: E402

REQUIRED = ("measure", "floor", "unit", "subject", "question",
            "hypothesis", "expected_artifact", "falsification", "fix_hint")


# ─── قراردادِ رجیستری ────────────────────────────────────────────────────────
def t_every_probe_declares_the_full_contract():
    for name, spec in cp.PROBES.items():
        for field in REQUIRED:
            assert field in spec, f"پروبِ {name} فیلدِ {field} را ندارد"
        assert callable(spec["measure"]), f"{name}.measure صدازدنی نیست"
        assert isinstance(spec["floor"], int), f"{name}.floor عدد صحیح نیست"
        assert isinstance(spec["falsification"], list) and spec["falsification"], \
            f"{name} شرطِ ابطال ندارد — فرضیه‌ای که نتواند غلط باشد فرضیه نیست"


def t_coverage_did_not_shrink():
    """گاردِ رگرسیون: لایهٔ حس نباید بی‌سروصدا آب برود."""
    assert len(cp.PROBES) >= 12, f"فقط {len(cp.PROBES)} پروب — پوشش کم شده"


def t_the_two_repaired_probes_are_registered_and_point_at_real_things():
    import inspect

    def _code_only(fn):
        """کامنت‌ها را دور بریز — قید روی کدِ اجراشونده است نه روی متنِ توضیح."""
        return "\n".join(l.split("#", 1)[0] for l in
                         inspect.getsource(fn).splitlines())

    src = _code_only(cp._probe_self_audit_redundant_reads)
    assert "run_audit" in src, \
        "پروبِ self_audit باید run_audit را صدا بزند، نه main که وجود ندارد"
    assert "mod.main()" not in src, "فراخوانِ اجراییِ main هنوز هست"
    assert "write=False" in src, "پروب باید read-only بماند و ماتریس را ننویسد"
    # و خودِ self_audit واقعاً باید run_audit داشته باشد و main نداشته باشد
    sa = cp._load_self_audit_module()
    assert hasattr(sa, "run_audit"), "self_audit.run_audit ناپدید شده"
    assert not hasattr(sa, "main"), \
        "self_audit دوباره main گرفت — نقطهٔ ورودِ پروب را بازبینی کن"
    src2 = inspect.getsource(cp._probe_rfc_duplicate_surplus)
    assert "doctor" in src2 and "rfcs.json" in src2, \
        "پروبِ RFC باید انبارِ واقعی را بخواند نه مسیرِ هرگز-ساخته-نشده"


# ─── fail-soft ──────────────────────────────────────────────────────────────
def t_no_probe_ever_raises_and_all_return_the_same_shape():
    for name, spec in cp.PROBES.items():
        try:
            m = spec["measure"]()
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"پروبِ {name} استثنا داد: {type(e).__name__}: {e}")
        assert isinstance(m, dict), f"{name} dict برنگرداند"
        assert isinstance(m.get("count"), int), f"{name}.count عدد صحیح نیست"
        assert isinstance(m.get("detail", ""), str), f"{name}.detail رشته نیست"


# ─── مرزِ کور / تمیز ─────────────────────────────────────────────────────────
class _FakeSpec(dict):
    pass


def _with_probes(fake, fn):
    orig = cp.PROBES
    cp.PROBES = fake
    try:
        return fn()
    finally:
        cp.PROBES = orig


def _spec(count, floor=0):
    return {"measure": lambda: {"count": count, "unit": "u", "detail": "d"},
            "floor": floor, "unit": "u", "subject": "s", "question": "q",
            "hypothesis": "h", "expected_artifact": "a", "falsification": ["f"],
            "fix_hint": "x"}


def t_blind_probe_never_becomes_a_hypothesis():
    """قیدِ اصلی: count=-1 یعنی «نتوانستم بسنجم». ساختنِ فرضیه از آن یعنی
    اختراعِ نقص از روی کوری."""
    q = Path(tempfile.mkdtemp(prefix="c6probe-")) / "q.jsonl"
    os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"
    try:
        r = _with_probes({"blind": _spec(-1)}, lambda: prod.produce(q))
        assert r["produced"] is False
        assert not q.exists() or not q.read_text("utf-8").strip(), \
            "از پروبِ کور ردیف ساخته شد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_C6_PRODUCER", None)


def t_producer_reports_blindness_separately_from_health():
    """«نقصی نیست» و «نمی‌توانم ببینم» تا امروز یک پیام می‌دادند."""
    q = Path(tempfile.mkdtemp(prefix="c6probe-")) / "q.jsonl"
    os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"
    try:
        all_blind = _with_probes({"a": _spec(-1), "b": _spec(-1)},
                                 lambda: prod.produce(q))
        assert all_blind["reason"] == "all-probes-blind", all_blind
        assert all_blind["blind"] == 2 and all_blind["measured"] == 0
        assert "a" in all_blind["blind_probes"]

        healthy = _with_probes({"a": _spec(0, floor=0), "b": _spec(-1)},
                               lambda: prod.produce(q))
        assert healthy["reason"] == "no-defect", healthy
        assert healthy["measured"] == 1 and healthy["blind"] == 1
    finally:
        os.environ.pop("OCTOPUS_WIRE_C6_PRODUCER", None)


def t_a_count_above_floor_becomes_a_row():
    q = Path(tempfile.mkdtemp(prefix="c6probe-")) / "q.jsonl"
    os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "1"
    try:
        r = _with_probes({"defective": _spec(5, floor=0)}, lambda: prod.produce(q))
        assert r["produced"] is True and r["probe"] == "defective", r
        row = json.loads(q.read_text("utf-8").splitlines()[0])
        assert row["status"] == "PENDING" and row["baseline_count"] == 5
        assert row["falsification_criteria"], "ردیفِ بی‌شرطِ ابطال ساخته شد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_C6_PRODUCER", None)


# ─── منطقِ پروب‌های تازه، با stateِ ساختگی ──────────────────────────────────
def _state(rel, text):
    import opslib
    p = Path(opslib.STATE_DIR) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def t_undelivered_card_probe_counts_only_the_real_debt():
    _state("c6/hypothesis-queue.jsonl", "\n".join([
        json.dumps({"id": "a", "status": "DONE", "card_delivered": False}),
        json.dumps({"id": "b", "status": "DONE", "card_delivered": True}),
        json.dumps({"id": "c", "status": "PENDING", "card_delivered": False}),
        "{ corrupt",
    ]) + "\n")
    m = cp._probe_c6_undelivered_cards()
    assert m["count"] == 1, m


def t_cmd_lone_lf_probe_separates_crlf_from_lf():
    ops = cp.OPS
    good, bad = ops / "_probe-ok.cmd", ops / "_probe-bad.cmd"
    try:
        good.write_bytes(b"set A=1\r\nset B=2\r\n")
        bad.write_bytes(b"set A=1\nset B=2\n")
        m = cp._probe_cmd_lone_lf()
        assert m["count"] >= 1, m
        assert "_probe-bad.cmd" in m["detail"] or m["count"] >= 1
    finally:
        for p in (good, bad):
            try:
                p.unlink()
            except OSError:
                pass


def t_discovery_lag_probe_is_blind_without_a_seen_marker():
    """نبودِ نشانگر ≠ تأخیرِ صفر. باید «کور» بدهد نه «تمیز»."""
    _state("discoveries.jsonl", "{}\n")
    import opslib
    seen = Path(opslib.STATE_DIR) / "discoveries-seen.json"
    if seen.exists():
        seen.unlink()
    m = cp._probe_discovery_seen_lag()
    assert m["count"] == -1, f"نبودِ نشانگر باید کوری باشد نه سلامت: {m}"


def t_flags_probe_is_blind_without_a_boot_timestamp():
    import opslib
    p = Path(opslib.STATE_DIR) / "ORGANISM-STATE.code"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"modules": {}}), encoding="utf-8")
    m = cp._probe_flags_armed_not_loaded()
    assert m["count"] == -1, f"بی‌زمانِ بوت باید کور باشد: {m}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_c6_probe_coverage: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
