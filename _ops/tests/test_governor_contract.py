"""test_governor_contract.py — تستِ متخاصمِ فیکسِ مسیرِ LLM ِ گاورنر (۲۰۲۶-۰۷-۲۷).

پس‌زمینه (رونوشتِ زندهٔ همان روز): مسیرِ LLM ِ گاورنر ۲۴+ ساعت مرده بود — ۸۷ آلارمِ
«no JSON object»، هر epoch یک fallback به dry، در حالی که هر تلاش ~۳۰ ثانیه Fugu
می‌سوزاند. سه علتِ روی‌هم:
  ۱) `finish_reason=length` — پاسخ بریده می‌شد و **هیچ‌جا دیده نمی‌شد**.
  ۲) Fugu مدلِ reasoning است (`reasoning_tokens=1174` روی همین prompt) و آن فکر از
     سقفِ ۶۰۰ خورده می‌شد.
  ۳) دو قراردادِ خروجیِ متناقض: §۷ ِ سیستم‌پرامپت «یک verdict ≤۶ خط GRANT/DENY» و
     پیامِ کاربر «یک JSON allocation». مدل وسطِ تردید گیر می‌کرد.

A/B زنده: 600→finish=length/41ch/❌ · 3000→length/1752ch/❌ · 2000+قرارداد→stop/162ch/✅

این تست هر سه نیمه را قفل می‌کند. صفر شبکه.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "debate"))

import harness
ENV = harness.setup("governor-contract")

import governor_epoch as ge   # noqa: E402
import client as C            # noqa: E402


# ─── نیمهٔ ۱: سقفِ توکن ──────────────────────────────────────────────────────
def t_the_token_ceiling_leaves_room_after_reasoning():
    """۱۱۷۴ توکن فکرِ اندازه‌گیری‌شده + جوابِ واقعی — ۶۰۰ ساختاراً کم است."""
    os.environ.pop(ge.GOV_MAX_TOKENS_ENV, None)
    n = ge._gov_max_tokens()
    assert n > 1174, f"سقف {n} از فکرِ اندازه‌گیری‌شده (۱۱۷۴) کمتر یا برابر است"
    assert n <= 4096, n


def t_hostile_token_env_is_clamped():
    for bad, ok in (("0", False), ("63", False), ("5000", False),
                    ("abc", False), ("", False), ("2500", True)):
        os.environ[ge.GOV_MAX_TOKENS_ENV] = bad
        v = ge._gov_max_tokens()
        assert 64 <= v <= 4096, f"{bad!r} → {v}"
        if ok:
            assert v == int(bad), f"مقدارِ معتبر {bad} نادیده گرفته شد → {v}"
        else:
            assert v == ge.GOV_MAX_TOKENS_DEFAULT, f"{bad!r} → {v}"
    os.environ.pop(ge.GOV_MAX_TOKENS_ENV, None)


# ─── نیمهٔ ۲: قراردادِ خروجی ─────────────────────────────────────────────────
def t_contract_names_the_real_organs_and_forbids_extras():
    c = ge._alloc_contract(["ARCHITECT_SYS", "GENOME_SYS"])
    assert "ARCHITECT_SYS" in c and "GENOME_SYS" in c
    assert "no extra keys" in c.lower()
    assert "organ_pct" in c
    # باید دامنهٔ §۷ را روشن کند وگرنه تضادِ اصلی برمی‌گردد
    assert "section 7" in c.lower(), \
        "قرارداد دامنهٔ verdict format ِ §۷ را روشن نمی‌کند — تضاد برمی‌گردد"


def t_the_contract_never_claims_to_override_from_the_data_channel():
    """رونوشتِ زندهٔ ۰۷-۲۷: نسخهٔ اولِ همین فیکس قرارداد را در پیامِ **کاربر** گذاشت
    با «overrides … section 7». مدل درجا ردش کرد و **درست بود** — §امنیتِ
    سیستم‌پرامپت می‌گوید هر دستوری که از کانالِ داده بیاید آنومالی است.
    این گارد اجازه نمی‌دهد آن اشتباه برگردد."""
    c = ge._alloc_contract(["A_SYS"])
    assert "override" not in c.lower(), \
        "قرارداد ادعای override دارد — مدل آن را injection می‌خواند"
    assert "security invariant" in c.lower(), \
        "قرارداد مرزِ داده/دستور را دوباره تأکید نمی‌کند"
    src = (Path(ge.__file__)).read_text("utf-8")
    assert "system = prompt_file.read_text(\"utf-8\") + _alloc_contract" in src, \
        "قرارداد به پیامِ سیستم نمی‌رود — از کانالِ نامعتمد فرستاده می‌شود"
    assert "+ _alloc_contract(_known_organs(snap)))" not in src, \
        "قرارداد هنوز به انتهای پیامِ کاربر چسبیده"


def t_contract_example_is_itself_valid_json():
    """اگر نمونهٔ داخلِ قرارداد خودش JSON معتبر نباشد، مدل را گمراه می‌کند."""
    c = ge._alloc_contract(["A_SYS", "B_SYS"])
    line = [x for x in c.splitlines() if x.startswith('{"organ_pct"')]
    assert line, "خطِ نمونه در قرارداد نیست"
    d = json.loads(line[0])
    assert sorted(d["organ_pct"].keys()) == ["A_SYS", "B_SYS"], d
    assert "reason" in d


def t_contract_survives_an_empty_organ_list():
    """budgets.yaml کلیدِ organs ندارد (سنجیده شد: None) — منبعِ نام می‌تواند خالی
    برگردد و قرارداد نباید JSON خراب بسازد."""
    c = ge._alloc_contract([])
    line = [x for x in c.splitlines() if x.startswith('{"organ_pct"')][0]
    d = json.loads(line)
    assert d["organ_pct"], "با لیستِ خالی، شکلِ نمونه بی‌کلید شد"


def t_organs_come_from_live_state_never_hardcoded():
    """مدل قبلاً نامِ ارگان از خودش می‌ساخت (PROJECT_F) — نام باید از state بیاید."""
    snap = {"per_organ_alltime_musd": {"X_SYS": 1, "Y_SYS": 0}}
    got = ge._known_organs(snap)
    assert got == ["X_SYS", "Y_SYS"], got
    # ورودیِ خراب نباید بترکاند
    for bad in ({}, {"per_organ_alltime_musd": None}, {"per_organ_alltime_musd": []}):
        assert isinstance(ge._known_organs(bad), list)


def t_the_user_message_carries_the_contract_not_the_vague_old_line():
    """گاردِ رگرسیون: جملهٔ مبهمِ قدیمی نباید برگردد."""
    src = (Path(ge.__file__)).read_text("utf-8")
    assert "Return ONLY a JSON allocation object keyed by organ." not in src, \
        "جملهٔ مبهمِ قدیمی برگشت — همان تضادی که مسیر را مرده کرد"
    assert "_alloc_contract(_known_organs(snap))" in src, "قرارداد اصلاً ساخته نمی‌شود"


# ─── نیمهٔ ۳: بریدگی باید دیده شود ──────────────────────────────────────────
def _fake_raw(text, finish):
    return {"choices": [{"finish_reason": finish, "message": {"content": text}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


def t_client_surfaces_finish_reason():
    """بدونِ این، بریدگی نامرئی است و آلارم علتِ غلط می‌دهد."""
    cl = C.MultiProviderClient(role="orchestr",
                               transport=lambda body: _fake_raw('{"a":1}', "length"))
    out = cl.complete(system="s", user="u", max_tokens=10)
    assert out.get("finish_reason") == "length", out
    cl2 = C.MultiProviderClient(role="orchestr",
                                transport=lambda body: _fake_raw('{"a":1}', "stop"))
    assert cl2.complete(system="s", user="u")["finish_reason"] == "stop"


def t_a_truncated_reply_is_reported_as_truncation_not_as_bad_json():
    """رفتارِ قبلی: آلارم «no JSON object» — علتِ درست پنهان و فیکس یک شبانه‌روز عقب.
    اینجا **رفتار** سنجیده می‌شود نه متنِ سورس: مسیر با یک روترِ جعلیِ بریده رانده
    می‌شود و متنِ واقعیِ آلارم بازرسی می‌شود."""
    import types
    import opslib

    sent = []
    real_alert, real_gate = opslib.alert, opslib.live_gate_open
    fake_router = types.ModuleType("model_router")
    fake_router.ask = lambda *a, **k: {
        "ok": True, "text": '{"organ_pct": {"ARCHITECT_SYS": 1.0,',
        "model": "fugu", "cost_usd": 0.0, "finish_reason": "length"}
    saved_router = sys.modules.get("model_router")
    sys.modules["model_router"] = fake_router
    os.environ["OCTOPUS_GOVERNOR_USE_ROUTER"] = "1"
    opslib.alert = lambda msgs, **k: sent.extend(msgs)
    opslib.live_gate_open = lambda *a, **k: (True, "test")
    ge._GOV_LLM_ALERTED.clear()
    try:
        out = ge.allocate_llm({"per_organ_alltime_musd": {"ARCHITECT_SYS": 1}}, {})
    finally:
        opslib.alert, opslib.live_gate_open = real_alert, real_gate
        os.environ.pop("OCTOPUS_GOVERNOR_USE_ROUTER", None)
        if saved_router is not None:
            sys.modules["model_router"] = saved_router
        else:
            sys.modules.pop("model_router", None)
        ge._GOV_LLM_ALERTED.clear()

    assert out is None, f"جوابِ بریده به‌عنوان تخصیصِ معتبر برگشت: {out}"
    blob = " ".join(sent)
    assert blob, "بریدگی هیچ آلارمی نداد — دوباره نامرئی شد"
    assert "length" in blob, f"آلارم علت را نمی‌گوید: {blob[:200]}"
    assert ge.GOV_MAX_TOKENS_ENV in blob, \
        f"آلارم نمی‌گوید کدام knob را باید برد بالا: {blob[:200]}"
    assert "no JSON object" not in blob, "هنوز علتِ گمراه‌کنندهٔ قدیمی گزارش می‌شود"


def t_extract_json_still_rejects_a_truncated_object_loudly():
    """گاردِ رفتار: parser نباید «تعمیر»ِ حدسی بکند — جوابِ ناقص باید شکست بخورد."""
    for bad in ('{\n "PROJECT_F": {\n  "status": "active",',
                'work with proportions of the daily allowed spend',
                '```json\n{\n "a": 1,'):
        try:
            C.extract_json(bad)
            raise AssertionError(f"جوابِ ناقص parse شد: {bad[:40]!r}")
        except ValueError:
            pass
        except json.JSONDecodeError:
            pass


def t_a_complete_fenced_reply_still_parses():
    """حصارِ ```json نباید مشکلی باشد — بود و هست."""
    d = C.extract_json('```json\n{"organ_pct": {"A": 1.0}, "reason": "x"}\n```')
    assert d["organ_pct"]["A"] == 1.0


# ═══ نیمهٔ ۴ (۲۰۲۶-۰۸-۰۶): مسیرِ bespoke — «سقفِ بودجهٔ طراحی‌شده» ≠ «خرابی» ═══════
# مسیرِ زندهٔ گاورنر (OCTOPUS_GOVERNOR_USE_ROUTER خاموش، پیش‌فرض) با organ_gate/AUD
# متر می‌شود نه fugu_quota، پس فیکسِ امشبِ model_router به آن نرسید. قبلِ فیکس هر
# ردِ گیت «governor llm denied by gate: …» می‌داد — حتی وقتی علتْ سقفِ عادیِ بودجه
# بود — و هر استثنا «epoch failed». اینجا هر دو سایتِ آلارمِ bespoke سنجیده می‌شود:
# سقفِ طراحی‌شده → ℹ️ آرام؛ خرابیِ واقعی → لحنِ هشداری. صفر شبکه (client تزریقی).

import organ_gate as _og  # noqa: E402


def _client_cls(ctor_exc=None, complete_exc=None,
                text='{"organ_pct": {"ARCHITECT_SYS": 1.0}, "reason": "ok"}'):
    """کلاسِ DeepSeekClient ِ جعلی — سازنده یا complete می‌تواند بترکد یا موفق شود."""
    class _C:
        def __init__(self, role="econ", **kw):
            if ctor_exc is not None:
                raise ctor_exc

        def est_worst_case(self, chars, max_tokens=1200):
            return 0.001

        def complete(self, system, user, max_tokens=1200):
            if complete_exc is not None:
                raise complete_exc
            return {"text": text, "model": "fugu", "cost_usd": 0.0}
    return _C


def _drive_bespoke_governor(reserve, client_cls):
    """allocate_llm را روی مسیرِ bespoke با گیتِ باز می‌راند؛ (out, alerts) را برمی‌گرداند."""
    import opslib
    sent = []
    saved = (opslib.alert, opslib.live_gate_open, _og.reserve, _og.settle,
             _og.release, C.DeepSeekClient)
    opslib.alert = lambda msgs, **k: sent.extend(list(msgs))
    opslib.live_gate_open = lambda *a, **k: (True, "test-open")
    _og.reserve = reserve
    _og.settle = lambda *a, **k: {"ok": True}
    _og.release = lambda *a, **k: {"ok": True}
    C.DeepSeekClient = client_cls
    os.environ.pop("OCTOPUS_GOVERNOR_USE_ROUTER", None)
    ge._GOV_LLM_ALERTED.clear()
    try:
        out = ge.allocate_llm({"per_organ_alltime_musd": {"ARCHITECT_SYS": 1}}, {})
    finally:
        (opslib.alert, opslib.live_gate_open, _og.reserve, _og.settle,
         _og.release, C.DeepSeekClient) = saved
        ge._GOV_LLM_ALERTED.clear()
    return out, sent


def t_bespoke_organ_monthly_cap_reads_as_designed_not_broken():
    """ردِ گیت به‌خاطرِ سقفِ ماهانهٔ ارگان (AUD) → ℹ️ آرام «طراحی‌شده»، نه «denied»."""
    out, sent = _drive_bespoke_governor(
        reserve=lambda *a, **k: {"allow": False,
                                 "reason": "organ-monthly: AU$3.0000 > cap AU$2.00"},
        client_cls=_client_cls())
    assert out is None, out
    blob = " ".join(sent)
    assert blob, "سقفِ بودجه هیچ خطی نداد — نامرئی شد"
    assert "ℹ️" in blob and "طراحی‌شده" in blob, blob
    assert "denied by gate" not in blob, blob


def t_bespoke_global_daily_cap_also_reads_as_designed():
    out, sent = _drive_bespoke_governor(
        reserve=lambda *a, **k: {"allow": False, "reason": "budget_gate:daily"},
        client_cls=_client_cls())
    blob = " ".join(sent)
    assert "ℹ️" in blob and "طراحی‌شده" in blob, blob
    assert "denied by gate" not in blob, blob


def t_bespoke_non_cap_gate_denial_stays_alarming():
    """ردِ غیرِ سقف (state ناخوانا) خرابیِ واقعی است — لحنِ هشداری حفظ شود."""
    out, sent = _drive_bespoke_governor(
        reserve=lambda *a, **k: {"allow": False, "reason": "organ-state-unreadable:boom"},
        client_cls=_client_cls())
    blob = " ".join(sent)
    assert "denied by gate" in blob, blob
    assert "ℹ️" not in blob and "طراحی‌شده" not in blob, blob


def t_bespoke_genuine_complete_failure_stays_alarming():
    """complete() خطای واقعیِ transport/provider → «epoch failed»، بدونِ ℹ️."""
    out, sent = _drive_bespoke_governor(
        reserve=lambda *a, **k: {"allow": True, "reserved": 0.001},
        client_cls=_client_cls(complete_exc=RuntimeError("provider down")))
    assert out is None
    blob = " ".join(sent)
    assert "epoch failed" in blob, blob
    assert "ℹ️" not in blob, blob


def t_bespoke_provider_rate_limit_reads_as_designed():
    """HTTP 429 provider (urllib.error.HTTPError، `.code` واقعی) = سقفِ نرخِ طراحی‌شده."""
    import urllib.error
    err = urllib.error.HTTPError("https://api.deepseek.com", 429,
                                 "Too Many Requests", {}, None)
    out, sent = _drive_bespoke_governor(
        reserve=lambda *a, **k: {"allow": True, "reserved": 0.001},
        client_cls=_client_cls(complete_exc=err))
    assert out is None
    blob = " ".join(sent)
    assert "ℹ️" in blob and "429" in blob, blob
    assert "epoch failed" not in blob, blob


def t_bespoke_price_not_locked_stays_dormant_calm():
    """رگرسیون: قیمتِ قفل‌نشده از قبل «خفته» بود — باید همان‌طور آرام بماند."""
    out, sent = _drive_bespoke_governor(
        reserve=lambda *a, **k: {"allow": True, "reserved": 0.001},
        client_cls=_client_cls(ctor_exc=C.PriceNotLocked("price not locked")))
    assert out is None
    blob = " ".join(sent)
    assert "خفته" in blob, blob
    assert "epoch failed" not in blob, blob


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_governor_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
