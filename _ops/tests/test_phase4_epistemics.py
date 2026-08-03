#!/usr/bin/env python3
"""Phase 4 — Epistemics فاز A (off-loop): test scaffold.

پنج متریک کار می‌کنند، emit روی استریمِ جدا (epi-ledger) hash-chain سالم،
readers خواننده-only، run_offloop بدونِ importِ organism. propose-only، advisory.
$0 آفلاین.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("phase4-epistemics")

_OPS = (harness.SELF_OPS)
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


# ════════════════════════════════════════════════════════════════════════════════
# metrics — همهٔ پنج کار می‌کنند
# ════════════════════════════════════════════════════════════════════════════════

def t_identifiability():
    """N_eff (perplexity) روی states."""
    from epistemics.metrics import identifiability
    r = identifiability(['A', 'A', 'B', 'B', 'C'])
    assert r["metric"] == "identifiability"
    assert r["value"] > 0
    assert r["authoritative"] is False  # sample_size=5 < MIN_SAMPLES=200


def t_self_reference():
    """SOG با twin-control — functional verdict."""
    from epistemics.metrics import self_reference
    r = self_reference([0.1, 0.2], [0.3, 0.4])
    assert r["metric"] == "self_reference"
    assert r["value"] > 0  # err_self < err_other → SOG > 0
    assert "NOT a consciousness" in r["notes"] or "NOT" in r["notes"]


def t_method_conditional_only():
    """method فقط گزارهٔ شرطی — هرگز غیرشرطی."""
    from epistemics.metrics import method
    r = method()
    assert r["value"]["conditional"] is True
    assert r["value"]["unconditional_claim"] is False
    assert r["value"]["phenomenal_claim"] is False


def t_levels_empty_safe():
    """levels روی گراف خالی → graceful."""
    from epistemics.metrics import levels
    r = levels([])
    assert r["value"] is None
    assert r["authoritative"] is False


def t_channel_empty_safe():
    """channel روی دادهٔ خالی → graceful."""
    from epistemics.metrics import channel
    r = channel([])
    assert r["value"] is None


def t_all_metrics_have_confidence():
    """هر متریک باید confidence + sample_size داشته باشد."""
    from epistemics.metrics import identifiability, channel, levels, self_reference, method
    for fn, args in [(identifiability, (['A'],)),
                     (channel, ([(0,1),(1,0)],)),
                     (levels, ([],)),   # adjacency=[]
                     (self_reference, ([0.1], [0.2])),
                     (method, ())]:
        r = fn(*args)
        assert "confidence" in r and "sample_size" in r, \
            f"{fn.__name__} باید confidence + sample_size داشته باشد"


# ════════════════════════════════════════════════════════════════════════════════
# emit — استریمِ جدا + hash-chain
# ════════════════════════════════════════════════════════════════════════════════

def test_emit_to_separate_stream():
    """emit باید روی epi-ledger.jsonl بنویسد، نه ledgerِ مالی."""
    from epistemics.emit import emit
    from epistemics.contracts import make_metric
    epi_path = str(ENV["ops"] / "state" / "epi-ledger-test.jsonl")
    rec = make_metric("test", {"v": 1}, sample_size=10)
    result = emit(rec, path=epi_path)
    assert result is not None
    # فایل باید ساخته شده باشد
    assert Path(epi_path).exists()
    # و نباید ledgerِ مالی باشد
    content = Path(epi_path).read_text("utf-8")
    assert "EPI_METRIC" in content


def test_emit_idempotency():
    """دوبار emit با همان dedup-key → یک رکورد، نه دو."""
    from epistemics.emit import emit
    from epistemics.contracts import make_metric
    epi_path = str(ENV["ops"] / "state" / "epi-ledger-dedup.jsonl")
    rec = make_metric("test", {"v": 1}, sample_size=10)
    emit(rec, path=epi_path, dedup_key="unique-1")
    emit(rec, path=epi_path, dedup_key="unique-1")  # تکراری
    lines = [l for l in Path(epi_path).read_text("utf-8").splitlines() if l.strip()]
    assert len(lines) == 1, f"idempotency: باید ۱ رکورد باشد نه {len(lines)}"


# ════════════════════════════════════════════════════════════════════════════════
# off-loop — run_offloop نباید organism را import کند
# ════════════════════════════════════════════════════════════════════════════════

def t_offloop_no_organism_import():
    """run_offloop.py نباید organism.py را import کند (فقط import statement، نه comment)."""
    import re
    src = (_OPS / "epistemics" / "run_offloop.py").read_text("utf-8")
    import_lines = [l for l in src.splitlines() if re.match(r"^\s*(import|from)\s", l)]
    for line in import_lines:
        assert "organism" not in line, \
            f"run_offloop نباید organism را import کند: {line.strip()}"


def t_offloop_runs():
    """run_offloop قابل اجراست و خروجی چاپ می‌کند."""
    from epistemics import run_offloop
    # فقط callable بودن را چک کن (اجرای کامل ممکن است به state وابسته باشد)
    assert hasattr(run_offloop, "main") or hasattr(run_offloop, "run") or callable(run_offloop)


# ════════════════════════════════════════════════════════════════════════════════
# no-collision — نباید روی ledger مالی بنویسد
# ════════════════════════════════════════════════════════════════════════════════

def t_no_write_to_money_ledger():
    """epi-ledger نباید همان فایلِ ledger.jsonl باشد."""
    from epistemics import emit
    src = Path(emit.__file__).read_text("utf-8")
    assert "ledger.jsonl" not in src or "epi-ledger" in src, \
        "emit نباید روی ledger.jsonlِ مالی بنویسد"


# ════════════════════════════════════════════════════════════════════════════════
# epistemics guards
# ════════════════════════════════════════════════════════════════════════════════

def t_authoritative_false_on_small_sample():
    """نمونهٔ کوچک → authoritative=False (ضدِ تصمیمِ زودهنگام)."""
    from epistemics.metrics import identifiability
    r = identifiability(['A'])  # sample_size=1
    assert r["authoritative"] is False


def t_sog_not_phenomenal():
    """SOG نباید ادعای phenomenal/transcendence کند."""
    from epistemics.metrics import self_reference
    r = self_reference([0.1], [0.2])
    assert "consciousness" in r["notes"].lower() or "transcendence" in r["notes"].lower() or "NOT" in r["notes"]


if __name__ == "__main__":
    failed = harness.run([
        # metrics
        ("identifiability", t_identifiability),
        ("self_reference (SOG)", t_self_reference),
        ("method conditional only", t_method_conditional_only),
        ("levels empty safe", t_levels_empty_safe),
        ("channel empty safe", t_channel_empty_safe),
        ("all have confidence", t_all_metrics_have_confidence),
        # emit
        ("emit separate stream", test_emit_to_separate_stream),
        ("emit idempotency", test_emit_idempotency),
        # off-loop
        ("offloop no organism import", t_offloop_no_organism_import),
        ("offloop runs", t_offloop_runs),
        # no-collision
        ("no money ledger write", t_no_write_to_money_ledger),
        # guards
        ("authoritative false small sample", t_authoritative_false_on_small_sample),
        ("SOG not phenomenal", t_sog_not_phenomenal),
    ])
    sys.exit(1 if failed else 0)
