#!/usr/bin/env python3
"""تستِ harvest_austender — keyless AusTender → lead-inbox ($0، صفر شبکه).

هاروستر سرِ لولهٔ خشک (DAM-1) است: تنها تولیدکنندهٔ lead-inbox که کلید نمی‌خواهد.
شبکه تزریق می‌شود (get_json)، پس هیچ فراخوانیِ واقعیِ AusTender رخ نمی‌دهد.

اثبات‌ها: فلگ‌خاموش=no-op · releaseِ مرتبط → JSONِ conformant (description لازم) ·
نامرتبط فیلتر می‌شود · مبلغ→cost_of_development · idempotent · fetch fail-soft ·
kill-switch · کرانِ ضدِ سیل · صفر ارسال/راز.
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("harvest-austender")
_OPS = (harness.REAL_VAULT / r"_ops")
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import harvest_austender as H  # noqa: E402

_FLAG = "OCTOPUS_WIRE_HARVEST"


def _inbox() -> Path:
    """STATE_DIR را به سندباکس ببر تا نوشتن هرگز به vault واقعی نخورد.
    STOP_ORGANISM را هم به سندباکس (بدونِ فایلِ STOP) ببر — worktree خودش یک
    فایلِ STOP-ORGANISM دارد که وگرنه هر اجرا را halt نشان می‌دهد."""
    opslib.STATE_DIR = Path(ENV["ops"]) / "state"
    opslib.STOP_ORGANISM = Path(ENV["ops"]) / "STOP-ORGANISM"
    inbox = opslib.STATE_DIR / "legs" / "lead-inbox"
    if inbox.exists():   # ایزولاسیونِ per-test — ENV ماژول‌سطح است و صندوق انباشته می‌شود
        shutil.rmtree(inbox, ignore_errors=True)
    return inbox


def _release(title, desc="", amount=None, buyer=None, uri=None, day=None):
    tender = {"title": title, "description": desc}
    if amount is not None:
        tender["value"] = {"amount": amount}
    rel = {"tender": tender}
    if buyer:
        rel["buyer"] = {"name": buyer}
    if uri:
        rel["uri"] = uri
    if day:
        rel["date"] = day
    return rel


def _fake(releases):
    return lambda url, timeout=30: {"releases": releases}


_PAINT = "Exterior repainting of Blacktown community centre"
_NOISE = "Supply of enterprise IT networking hardware and licences"


# ── (الف) فلگ ───────────────────────────────────────────────────────────────
def t_flag_off_noop():
    os.environ.pop(_FLAG, None)
    inbox = _inbox()
    r = H.harvest(get_json=_fake([_release(_PAINT, amount=50000)]))
    assert r["written"] == 0 and "no-op" in r["note"], r
    assert not inbox.exists() or not list(inbox.glob("austender-*.json"))


# ── (ب) مسیرِ اصلی ────────────────────────────────────────────────────────────
def t_relevant_written_conformant():
    os.environ[_FLAG] = "1"
    inbox = _inbox()
    r = H.harvest(get_json=_fake([_release(_PAINT, "full exterior repaint",
                                           amount=80000, buyer="Blacktown Council",
                                           uri="https://tenders.gov.au/atm/123", day="2026-07-16T00:00:00Z")]))
    assert r["relevant"] == 1 and r["written"] == 1, r
    files = list(inbox.glob("austender-*.json"))
    assert len(files) == 1, files
    d = json.loads(files[0].read_text("utf-8"))
    # قراردادِ سختِ صندوق: description غیرخالی (تنها فیلدِ لازمِ lead_sense)
    assert str(d.get("description", "")).strip(), d
    assert d["source"] == "austender"
    assert d["cost_of_development"] == 80000.0
    assert d["applicant"] == "Blacktown Council"
    assert d["day"] == "2026-07-16"


def t_irrelevant_filtered():
    os.environ[_FLAG] = "1"
    inbox = _inbox()
    r = H.harvest(get_json=_fake([_release(_NOISE, "cisco switches", amount=200000)]))
    assert r["relevant"] == 0 and r["written"] == 0, r
    assert not list(inbox.glob("austender-*.json"))


def t_malformed_release_does_not_abort_batch():
    """releaseِ بدشکل (اسکالر به‌جای dict در tender/value/buyer) نباید کلِ batch را بکشد —
    باید skip شود و releaseهای سالمِ بعدی نوشته شوند (بازبینیِ خصمانه ۲۰۲۶-۰۷-۱۷)."""
    os.environ[_FLAG] = "1"
    inbox = _inbox()
    releases = [
        {"tender": {"title": "Exterior repaint job X", "value": 5000}},    # value اسکالر
        {"tender": "just a string"},                                        # tender اسکالر
        {"tender": {"title": "repaint job Y"}, "buyer": "Council Inc"},     # buyer اسکالر
        _release("repaint job Z valid", "full repaint", amount=40000, uri="u/ok"),  # سالم
    ]
    r = H.harvest(get_json=_fake(releases))
    assert isinstance(r, dict) and "written" in r, f"batch نباید crash کند: {r}"
    names = [json.loads(f.read_text("utf-8"))["description"]
             for f in inbox.glob("austender-*.json")]
    assert any("job Z valid" in n for n in names), f"releaseِ سالم باید نوشته شود: {names}"
    assert r["written"] >= 1, r


def t_missing_description_skipped():
    os.environ[_FLAG] = "1"
    _inbox()
    # عنوان و بدنهٔ خالی → کاندید نیست حتی اگر مبلغ داشته باشد
    r = H.harvest(get_json=_fake([_release("", "", amount=90000)]))
    assert r["relevant"] == 0 and r["written"] == 0, r


# ── (ج) استواری ──────────────────────────────────────────────────────────────
def t_idempotent_same_release_once():
    os.environ[_FLAG] = "1"
    inbox = _inbox()
    rel = _release(_PAINT, "repaint", amount=50000, uri="u/1")
    H.harvest(get_json=_fake([rel]))
    r2 = H.harvest(get_json=_fake([rel]))
    assert r2["written"] == 0, "اجرای دوم نباید دوباره بنویسد"
    assert len(list(inbox.glob("austender-*.json"))) == 1


def t_fetch_failsoft():
    os.environ[_FLAG] = "1"
    _inbox()

    def _boom(url, timeout=30):
        raise ConnectionError("network down")

    r = H.harvest(get_json=_boom)
    assert r["fetched"] == 0 and r["written"] == 0, r   # صفر crash


def t_kill_switch_noop():
    os.environ[_FLAG] = "1"
    inbox = _inbox()
    stop = Path(ENV["ops"]) / "STOP-ORGANISM"
    _orig = opslib.STOP_ORGANISM
    opslib.STOP_ORGANISM = stop
    try:
        stop.write_text("stop", "utf-8")
        r = H.harvest(get_json=_fake([_release(_PAINT, amount=50000)]))
        assert r["written"] == 0 and "halt" in r["note"], r
        assert not list(inbox.glob("austender-*.json"))
    finally:
        opslib.STOP_ORGANISM = _orig
        if stop.exists():
            stop.unlink()


def t_cap_against_flood():
    os.environ[_FLAG] = "1"
    inbox = _inbox()
    many = [_release(f"{_PAINT} site {i}", "repaint", amount=10000, uri=f"u/{i}")
            for i in range(H._MAX_PER_RUN + 8)]
    r = H.harvest(get_json=_fake(many))
    assert r["relevant"] == H._MAX_PER_RUN + 8, r
    assert r["written"] == H._MAX_PER_RUN, "کرانِ ضدِ سیل باید نوشتن را ببندد"
    assert len(list(inbox.glob("austender-*.json"))) == H._MAX_PER_RUN


# ── (د) خطِ قرمز ──────────────────────────────────────────────────────────────
def t_no_send_no_secret_single_host():
    """هاروستر فقط GETِ عمومیِ keyless است: صفر ارسال، صفر راز، یک هاست."""
    src = (_OPS / "legs" / "harvest_austender.py").read_text("utf-8")
    for forbidden in ("sendMessage", "Authorization", "Bearer", "api_key", "API_KEY", "data="):
        assert forbidden not in src, f"خطِ قرمز در هاروستر: {forbidden}"
    import re
    hosts = set(re.findall(r"https?://([a-z0-9.\-]+)", src))
    assert hosts <= {"api.tenders.gov.au"}, f"هاستِ غیرمنتظره: {hosts}"
    # تنها متغیرِ env که خوانده می‌شود = فلگ (نه راز)
    assert "os.environ.get(FLAG_NAME" in src and src.count("os.environ") == 1


if __name__ == "__main__":
    failed = harness.run([
        ("[الف] فلگ خاموش → no-op", t_flag_off_noop),
        ("[ب] مرتبط → JSONِ conformant", t_relevant_written_conformant),
        ("[ب] نامرتبط فیلتر می‌شود", t_irrelevant_filtered),
        ("[ب] بی‌description رد می‌شود", t_missing_description_skipped),
        ("[ج] releaseِ بدشکل batch را نمی‌کشد", t_malformed_release_does_not_abort_batch),
        ("[ج] idempotent", t_idempotent_same_release_once),
        ("[ج] fetch fail-soft", t_fetch_failsoft),
        ("[ج] kill-switch → no-op", t_kill_switch_noop),
        ("[ج] کرانِ ضدِ سیل", t_cap_against_flood),
        ("[د] صفر ارسال/راز، تک‌هاست", t_no_send_no_secret_single_host),
    ])
    sys.exit(1 if failed else 0)
