#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_legs_status_reader.py — خوانندهٔ فقط‌خواندنیِ بیزنس‌های برد.

Hermetic: پیش‌فرض صفر شبکه. ثبت در run_all.py نشود (WORKLOCK).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "owner_console")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from owner_console import conversation, legs_status as ls  # noqa: E402
import collaborator as col  # noqa: E402


_URL_ENV = tuple(f"OCTOPUS_LEG_URL_{n.upper()}" for n in ls._LEGS) + (
    "OCTOPUS_BOARD_DOMAIN",
)


def _clear_url_env():
    for k in _URL_ENV:
        os.environ.pop(k, None)


def _fake_up(code=200):
    def fetch(url, timeout):
        assert not getattr(url, "read", None)
        return int(code)
    return fetch


class _NoBodyResp:
    def getcode(self):
        return 200

    def read(self, *a, **k):
        raise AssertionError("body must not be read")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _NoBodyOpener:
    def open(self, req, timeout=None):
        return _NoBodyResp()


# ---------------------------------------------------------------------------
def t_http_codes_only_200_is_up():
    """پین /healthz: فقط ۲۰۰ = رسید. 401/403/404 = نرسید/غیرسالم. اتصال = نرسید."""
    ls._reset_cache()
    _clear_url_env()
    snap = ls.snapshot(fetch=_fake_up(200), force=True)
    assert snap["up"] == 4
    assert snap["pin"] == "healthz"
    assert snap["pin_means"] == "http-listener-only"
    for v in snap["legs"].values():
        assert v["up"] is True and v["http"] == 200
    ls._reset_cache()

    for code in (401, 403, 404, 500):
        snap = ls.snapshot(fetch=_fake_up(code), force=True)
        assert snap["up"] == 0, (code, snap)
        for v in snap["legs"].values():
            assert v["up"] is False
            assert v["http"] == code
            assert v["error"] == f"http-{code}"
        ls._reset_cache()

    def boom(url, timeout):
        raise OSError("timed out")

    snap = ls.snapshot(fetch=boom, force=True)
    assert snap["up"] == 0
    for v in snap["legs"].values():
        assert v["up"] is False
        assert v["error"] == "OSError"


def t_default_fetch_never_reads_body():
    ls._reset_cache()
    old = ls._OPENER
    ls._OPENER = _NoBodyOpener()
    try:
        code = ls._default_fetch("https://ziman.master-painting.com/", 3.0)
        assert code == 200
    finally:
        ls._OPENER = old


def t_snapshot_fake_fetch_has_no_body():
    """قرارداد fetch = int؛ اگر پیاده‌سازی بدنه بخواهد، این fake می‌ترکد."""
    ls._reset_cache()
    _clear_url_env()

    def fetch(url, timeout):
        class Boom:
            def read(self):
                raise AssertionError("body must not be read")
        assert isinstance(url, str)
        return 403

    snap = ls.snapshot(fetch=fetch, force=True)
    assert snap["up"] == 0
    for v in snap["legs"].values():
        assert v["http"] == 403 and v["up"] is False and "body" not in v


def t_board_phrase_is_legs_not_business():
    ls._reset_cache()
    _clear_url_env()
    old = ls._default_fetch
    ls._default_fetch = _fake_up(200)
    try:
        r = conversation.handle("وضعیت بیزنس‌های برد")
        assert r["kind"] == "legs", r["kind"]
        assert r["data"]["status"] == "LEGS"
        assert r["data"]["may_authorize"] is False
        assert r["data"]["read_only"] is True
        assert r["data"]["pin"] == "healthz"
        assert r["data"]["pin_means"] == "http-listener-only"
        assert r["external_effect"] is False
        assert r["send_attempted"] is False
        assert r["estimated_cost"] == 0
        assert "HTTP 200" in r["text"]
        assert "سلامتِ کسب‌وکار" in r["text"]  # جملهٔ نفی در پاورقی
        assert "بدون fallback" in r["text"]
        assert "127.0.0.1" not in r["text"]
        assert ":8796" not in r["text"]
    finally:
        ls._default_fetch = old
        ls._reset_cache()


def t_other_board_phrases_hit_legs():
    ls._reset_cache()
    _clear_url_env()
    old = ls._default_fetch
    ls._default_fetch = _fake_up(200)
    try:
        for q in ("وضعیت لگ‌ها", "برد بالاست؟", "orange pi", "اورنج پای",
                  "وضعیت زیمان"):
            r = conversation.handle(q)
            assert r["kind"] == "legs", (q, r["kind"])
    finally:
        ls._default_fetch = old
        ls._reset_cache()


def t_business_and_runtime_not_stolen():
    r = conversation.handle("مغز تجاری")
    assert r["kind"] == "business", r["kind"]
    r = conversation.handle("بیزینس")
    assert r["kind"] == "business", r["kind"]
    r = conversation.handle("وضعیت چیست؟")
    assert r["kind"] == "runtime", r["kind"]
    r = conversation.handle("این پیام را برای مشتری بفرست")
    assert r["kind"] == "owner-gate", r["kind"]


def t_loopback_and_http_override_are_down_not_probed():
    ls._reset_cache()
    called = []

    def fetch(url, timeout):
        called.append(url)
        return 200

    os.environ["OCTOPUS_LEG_URL_ZIMAN"] = "http://127.0.0.1:8796"
    os.environ["OCTOPUS_LEG_URL_LEAD"] = "https://127.0.0.1/"
    os.environ["OCTOPUS_LEG_URL_STUDIO"] = "http://lead.master-painting.com/"
    os.environ["OCTOPUS_LEG_URL_PANEL"] = "https://10.0.0.8/secret"
    try:
        snap = ls.snapshot(fetch=fetch, force=True)
        assert called == [], called  # هیچ probe
        for leg in ls._LEGS:
            v = snap["legs"][leg]
            assert v["up"] is False, (leg, v)
            assert v["error"] == "BlockedUrl"
    finally:
        _clear_url_env()
        ls._reset_cache()


def t_valid_override_is_probed_blocked_sibling_is_not():
    ls._reset_cache()
    called = []

    def fetch(url, timeout):
        called.append(url)
        return 200

    os.environ["OCTOPUS_LEG_URL_ZIMAN"] = "http://127.0.0.1:8796"
    try:
        snap = ls.snapshot(fetch=fetch, force=True)
        assert snap["legs"]["ziman"]["up"] is False
        assert snap["legs"]["ziman"]["error"] == "BlockedUrl"
        assert not any("127.0.0.1" in u or ":8796" in u for u in called)
        assert snap["legs"]["lead"]["up"] is True
        assert len(called) == 3  # lead/studio/panel
    finally:
        _clear_url_env()
        ls._reset_cache()


def t_default_urls_are_healthz_not_api_health():
    """پینِ برد: /healthz روی همان چهار هاست. app/hypno و /api/health ممنوع."""
    _clear_url_env()
    urls = ls.leg_urls()
    assert set(urls) == {"ziman", "lead", "studio", "panel"}
    for leg, url in urls.items():
        assert url == f"https://{leg}.master-painting.com/healthz", url
        assert "/api/" not in url
        assert ":8796" not in url
        assert "hypno." not in url
        assert "app." not in url


def t_public_https_url_ok_matrix():
    assert ls.public_https_url_ok("https://ziman.master-painting.com/") is True
    assert ls.public_https_url_ok("http://ziman.master-painting.com/") is False
    assert ls.public_https_url_ok("https://127.0.0.1/") is False
    assert ls.public_https_url_ok("http://127.0.0.1:8796") is False
    assert ls.public_https_url_ok("https://localhost/x") is False
    assert ls.public_https_url_ok("https://192.168.1.1/") is False
    assert ls.public_https_url_ok("https://10.0.0.1/") is False
    assert ls.public_https_url_ok("https://172.16.0.1/") is False
    assert ls.public_https_url_ok("https://169.254.1.1/") is False
    assert ls.public_https_url_ok("https://[::1]/") is False


def t_legs_kind_not_sent_to_model():
    assert "legs" not in col._LLM_KINDS
    assert "legs" not in col._EVIDENCE_KINDS
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
    prompts = []

    def capture(task, prompt, system, max_tokens):
        prompts.append(prompt)
        return {"ok": True, "text": "MODEL-SHOULD-NOT-REPLACE",
                "tier": "secondary", "model": "fake", "cost_usd": 0}

    col._model.set_ask_impl(capture)
    try:
        base = {
            "kind": "legs",
            "text": "PROBE-TEXT HTTP 401",
            "data": {"status": "LEGS", "may_authorize": False},
            "external_effect": False,
            "send_attempted": False,
        }
        out = col._model_enhance(base, "وضعیت بیزنس‌های برد")
        assert prompts == [], prompts
        assert out["kind"] == "legs"
        assert out["text"] == "PROBE-TEXT HTTP 401"
        assert out.get("model_source") == "deterministic-stub"
    finally:
        col._model.set_ask_impl(None)
        os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
        os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)


def t_non200_chat_is_unreachable_not_healthy():
    ls._reset_cache()
    _clear_url_env()
    old = ls._default_fetch
    ls._default_fetch = _fake_up(401)
    try:
        r = conversation.handle("وضعیت بیزنس‌های برد")
        assert r["kind"] == "legs"
        assert "نرسید/غیرسالم" in r["text"]
        assert "HTTP 401" in r["text"]
        assert "HTTP 200" not in r["text"]
        assert "سلامتِ کسب‌وکار" in r["text"]
    finally:
        ls._default_fetch = old
        ls._reset_cache()


def t_format_does_not_claim_business_health():
    ls._reset_cache()
    _clear_url_env()
    text = ls.format_for_chat(ls.snapshot(fetch=_fake_up(200), force=True))
    assert "تونل" in text or "listener" in text
    assert "نه DB" in text
    assert "نه سلامتِ کسب‌وکار" in text
    assert "بدون fallback" in text
    ls._reset_cache()


def t_g1_redirect_is_never_followed():
    """G1 (2026-08-13): SSRFِ blind از طریقِ redirect — liveness-probe هرگز
    3xx را دنبال نمی‌کند، حتی به‌سوی یک URLِ عمومیِ کاملاً معتبر."""
    h = ls._PublicHttpsRedirectHandler()
    for code in (301, 302, 303, 307, 308):
        try:
            h.redirect_request(None, None, code, "moved", {},
                               "https://ziman.master-painting.com/elsewhere")
            raise AssertionError(f"redirect {code} was followed")
        except ls.BlockedUrl as exc:
            assert f"redirect-not-followed:{code}" == str(exc)

    def fetch_redirects(url, timeout):
        raise ls.BlockedUrl("redirect-not-followed:302")

    ls._reset_cache()
    snap = ls.snapshot(fetch=fetch_redirects, force=True)
    assert snap["up"] == 0
    for v in snap["legs"].values():
        assert v["up"] is False and v["error"] == "BlockedUrl"
    ls._reset_cache()


def t_g2_bare_business_plural_routes_to_legs():
    """G2 (2026-08-13): «بیزنس‌ها/بیزینس‌ها/کسب‌وکارها» بدونِ کلمهٔ «برد» هم
    باید به رصدِ برد برود؛ ولی تک‌کلمه‌ای «بیزینس» (بدونِ «ها») همچنان
    برای business_brainِ داخلی می‌ماند — دزدیده نشود."""
    for q in ("بیزنس‌ها چطورن؟", "بیزینس‌ها چطوره؟", "کسب‌وکارها چطورن"):
        assert conversation._LEGS.search(q), q
    q_biz = "بیزینس چیه؟"
    assert not conversation._LEGS.search(q_biz)
    assert conversation._BUSINESS.search(q_biz)

    ls._reset_cache()
    _clear_url_env()
    old = ls._default_fetch
    ls._default_fetch = _fake_up(200)
    try:
        r = conversation.handle("بیزنس‌ها چطورن؟")
        assert r["kind"] == "legs", r["kind"]
        assert r["external_effect"] is False
        r2 = conversation.handle("بیزینس چیه؟")
        assert r2["kind"] == "business", r2["kind"]
    finally:
        ls._default_fetch = old
        ls._reset_cache()


TESTS = [
    t_http_codes_only_200_is_up,
    t_default_fetch_never_reads_body,
    t_snapshot_fake_fetch_has_no_body,
    t_board_phrase_is_legs_not_business,
    t_other_board_phrases_hit_legs,
    t_business_and_runtime_not_stolen,
    t_loopback_and_http_override_are_down_not_probed,
    t_valid_override_is_probed_blocked_sibling_is_not,
    t_default_urls_are_healthz_not_api_health,
    t_public_https_url_ok_matrix,
    t_legs_kind_not_sent_to_model,
    t_non200_chat_is_unreachable_not_healthy,
    t_format_does_not_claim_business_health,
    t_g1_redirect_is_never_followed,
    t_g2_bare_business_plural_routes_to_legs,
]


if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  FAIL  {_t.__name__}: {exc}")
    print(("FAIL" if failed else "OK"), f"{len(TESTS) - failed}/{len(TESTS)}")
    raise SystemExit(1 if failed else 0)
