#!/usr/bin/env python3
"""test_lead_processed_fallback.py — برشِ ۱-ب: قفلِ دوتایی روی `lead-inbox/<id>.json`.

کشفِ ۲۰۲۶-۰۸-۰۳: `lead_pipeline.run()` همان beat ی که کارت صادر می‌شود
`lead_sense.mark_processed` را صدا می‌زند (lead_pipeline.py:395) — یعنی فایلِ
`lead-inbox/<id>.json` بلافاصله به `processed/` منتقل می‌شود. دو مصرف‌کننده که
بعداً — وقتی مالک approve می‌کند — همان داده را می‌خواهند
(`lead_effect_gate.bridge_from_inbox`، `outbound_worker._candidate_from_inbox`)
مستقیماً مسیرِ `lead-inbox/` را می‌ساختند: چون فایل قبلاً منتقل شده بود، هر دو
fail می‌شدند (`no_inbox_file` / `no-candidate`) — درست همان لحظه‌ای که مالک
دکمهٔ approve را زده بود.

این فایل از **مسیرِ تولیدی** عبور می‌کند (نه دستکاریِ دستیِ فایل): یک لید را
seed می‌کند، `lead_sense.mark_processed` واقعی را (همان تابعی که pipeline صدا
می‌زند) صدا می‌زند تا فایل واقعاً منتقل شود، و بعد اثبات می‌کند هر دو مصرف‌کننده
هنوز کاندید را پیدا می‌کنند.
"""
import json
import os
import sys
import uuid as _uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("lead-processed-fallback")

import importlib                        # noqa: E402
import opslib                           # noqa: E402
importlib.reload(opslib)
import chrono                           # noqa: E402
importlib.reload(chrono)
import lead_candidate_inbox as lci      # noqa: E402
importlib.reload(lci)
import lead_sense                       # noqa: E402
importlib.reload(lead_sense)
import lead_effect_gate as leg          # noqa: E402
importlib.reload(leg)
import outbound_worker as ow            # noqa: E402
importlib.reload(ow)


def _uniq_eid(tag: str) -> str:
    return f"{tag}-{_uuid.uuid4().hex[:8]}"


def _real_gate():
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"chrono-pf-{_uuid.uuid4().hex[:8]}.db"))
    return chrono.EffectorGate(db), db


def _inbox_path(lead_id: str) -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox" / f"{lead_id}.json"


def _seed_lead(tag: str) -> str:
    """سیدینگ از مسیرِ تولیدیِ واقعی (lci.submit_candidate) — فایلِ inbox با
    schema ِ واقعی ساخته می‌شود، دقیقاً همانی که هر دو مصرف‌کننده انتظار دارند."""
    _prev = os.environ.get("OCTOPUS_WIRE_LEAD_CANDIDATES")
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    try:
        r = lci.submit_candidate({
            "schema_version": "1.1",
            "source": {"channel": "telegram_manual", "source_id": "owner",
                       "external_id": _uniq_eid(tag)},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "owner_test"},
            "request": {"scope_text": "processed-fallback test — repaint kitchen"},
        }, source_id="owner")
    finally:
        if _prev is None:
            os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)
        else:
            os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = _prev
    assert r.get("ok"), f"seed failed: {r}"
    return str(r["lead_id"])


def _move_to_processed_like_pipeline(lead_id: str) -> None:
    """همان کاری که lead_pipeline.run() (خط ۳۹۵) بلافاصله بعدِ صدورِ کارت می‌کند:
    lead_sense.mark_processed ِ **واقعی** — نه شبیه‌سازیِ دستیِ os.replace."""
    path = _inbox_path(lead_id)
    assert path.exists(), f"seed ناموفق بود — فایلِ inbox نیست: {path}"
    lead = json.loads(path.read_text("utf-8"))
    lead_sense.mark_processed(path, lead, {"pipeline": "test-issued-card"})
    assert not path.exists(), "mark_processed فایل را جابه‌جا نکرد"


def t_a_resolver_finds_inbox_file_before_processing():
    lead_id = _seed_lead("a")
    found = lead_sense.resolve_lead_path(lead_id)
    assert found == _inbox_path(lead_id)


def t_b_resolver_falls_back_to_processed_after_move():
    lead_id = _seed_lead("b")
    _move_to_processed_like_pipeline(lead_id)
    found = lead_sense.resolve_lead_path(lead_id)
    assert found is not None, "resolve_lead_path باید processed/ را هم بگردد"
    assert found.parent == lead_sense._processed()
    assert found.name == f"{lead_id}.json"


def t_c_resolver_returns_none_for_unknown_lead():
    assert lead_sense.resolve_lead_path("no-such-lead-ever") is None
    assert lead_sense.resolve_lead_path("") is None


def t_d_resolver_prefers_freshest_among_name_collisions():
    """دو نسخهٔ processed/<id>.json و processed/<id>.1.json — تازه‌ترین باید برگردد،
    نه صرفاً اولین‌الفبایی (وعدهٔ docstring، نه فقط نسخهٔ ساده)."""
    lead_id = _seed_lead("d")
    _move_to_processed_like_pipeline(lead_id)
    older = lead_sense._processed() / f"{lead_id}.json"
    newer = lead_sense._processed() / f"{lead_id}.1.json"
    newer.write_text(json.dumps({"marker": "newer"}, ensure_ascii=False), "utf-8")
    # mtime تضمین‌شده متفاوت (بعضی فایل‌سیستم‌ها granularityِ ثانیه‌ای دارند)
    now = os.path.getmtime(newer)
    os.utime(older, (now - 5, now - 5))
    os.utime(newer, (now + 5, now + 5))
    found = lead_sense.resolve_lead_path(lead_id)
    assert found == newer, f"باید تازه‌ترین را برگرداند، برگرداند: {found}"


def t_e_bridge_from_inbox_still_authorizes_after_card_issued():
    """قلبِ رگرسیون برای lead_effect_gate: قبلِ فیکس این‌جا no_inbox_file بود."""
    gate, db = _real_gate()
    lead_id = _seed_lead("e")
    _move_to_processed_like_pipeline(lead_id)
    res = leg.bridge_from_inbox(lead_id, gate=gate)
    assert res.get("authorized") is True, (
        f"bridge_from_inbox بعدِ انتقالِ فایل به processed/ باید authorize کند — got {res}")
    assert res.get("reason") != "no_inbox_file"


def t_f_candidate_from_inbox_still_finds_it_after_card_issued():
    """قلبِ رگرسیون برای outbound_worker: قبلِ فیکس این‌جا (None, "") بود."""
    lead_id = _seed_lead("f")
    _move_to_processed_like_pipeline(lead_id)
    cand, aid = ow._candidate_from_inbox(lead_id)
    assert cand is not None, "outbound_worker._candidate_from_inbox بعدِ processed/ باید کاندید را پیدا کند"
    assert cand["lead_id"] == lead_id


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  ❌ {t.__name__}: {e!r}")
    print(f"\ntest_lead_processed_fallback: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
