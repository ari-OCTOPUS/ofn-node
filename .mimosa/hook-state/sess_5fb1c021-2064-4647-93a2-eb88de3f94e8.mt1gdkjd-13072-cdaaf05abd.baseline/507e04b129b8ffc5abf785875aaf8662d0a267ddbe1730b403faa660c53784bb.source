"""FuguLLM (OpenAI-compatible) — parsing, every fail-closed path, and the
no-redirect key-exfil guard. All offline (the opener is mocked)."""

import io
import json
import urllib.error

import pytest

pytestmark = pytest.mark.l1

from nbb_cp.adapters.llm import fugu
from nbb_cp.adapters.llm.fugu import FuguError, FuguLLM
from nbb_cp.app.bootstrap import build_llm
from nbb_cp.app.config import AppConfig
from nbb_cp.kernel.errors import FailClosedError
from nbb_cp.kernel.ports import LLMRequest


class _FakeResp:
    def __init__(self, body):  # body: str or raw bytes
        self._b = body.encode("utf-8") if isinstance(body, str) else body

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _openai_body(text="hi", pt=10, ct=5):
    return json.dumps(
        {
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": pt, "completion_tokens": ct},
        }
    )


def _patch_open(monkeypatch, fn):
    # The adapter calls fugu._OPENER.open (redirects disabled), not urlopen.
    monkeypatch.setattr(fugu._OPENER, "open", fn)


class TestFuguLLM:
    def test_requires_key(self):
        with pytest.raises(FuguError):
            FuguLLM(api_key="")

    def test_parses_openai_response_and_builds_request(self, monkeypatch):
        seen = {}

        def fake(req, timeout=None):
            seen["url"] = req.full_url
            seen["auth"] = req.headers.get("Authorization")
            seen["body"] = json.loads(req.data.decode("utf-8"))
            seen["method"] = req.get_method()
            return _FakeResp(_openai_body("hello fugu", 12, 7))

        _patch_open(monkeypatch, fake)
        resp = FuguLLM(api_key="fish_test", host="https://api.sakana.ai/v1", model="fugu").complete(
            LLMRequest(task="govern", prompt="plan epoch 0")
        )
        assert resp.text == "hello fugu"
        assert resp.input_tokens == 12 and resp.output_tokens == 7
        assert seen["url"] == "https://api.sakana.ai/v1/chat/completions"
        assert seen["auth"] == "Bearer fish_test"
        assert seen["method"] == "POST"
        assert seen["body"]["model"] == "fugu"
        assert seen["body"]["messages"][0]["content"] == "plan epoch 0"

    def test_http_error_fails_closed(self, monkeypatch):
        def fake(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"error":"bad key"}')
            )

        _patch_open(monkeypatch, fake)
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_unreachable_fails_closed(self, monkeypatch):
        def fake(req, timeout=None):
            raise urllib.error.URLError("no route to host")

        _patch_open(monkeypatch, fake)
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_malformed_json_fails_closed(self, monkeypatch):
        _patch_open(monkeypatch, lambda req, timeout=None: _FakeResp('{"not":"openai"}'))
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_non_text_content_fails_closed(self, monkeypatch):
        body = json.dumps({"choices": [{"message": {"content": {"obj": 1}}}]})
        _patch_open(monkeypatch, lambda req, timeout=None: _FakeResp(body))
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_non_dict_usage_fails_closed(self, monkeypatch):
        # usage as a list would previously raise a raw AttributeError outside the guard.
        body = json.dumps({"choices": [{"message": {"content": "hi"}}], "usage": [1, 2]})
        _patch_open(monkeypatch, lambda req, timeout=None: _FakeResp(body))
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_non_numeric_tokens_fail_closed(self, monkeypatch):
        body = json.dumps({"choices": [{"message": {"content": "hi"}}], "usage": {"prompt_tokens": "lots"}})
        _patch_open(monkeypatch, lambda req, timeout=None: _FakeResp(body))
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_non_utf8_body_fails_closed_not_crash(self, monkeypatch):
        # Invalid UTF-8 must decode (replace) then fail closed as FuguError, never a raw
        # UnicodeDecodeError that would bypass the incident handler.
        _patch_open(monkeypatch, lambda req, timeout=None: _FakeResp(b"\xff\xfe not json"))
        with pytest.raises(FuguError):
            FuguLLM(api_key="x").complete(LLMRequest(task="t", prompt="p"))

    def test_redirect_is_refused(self):
        # A 3xx must NOT be followed — following it would re-send Authorization: Bearer
        # <key> to the redirect host (stdlib urllib does not strip it).
        with pytest.raises(FuguError):
            fugu._NoRedirect().redirect_request(None, None, 302, "Found", {}, "http://evil.example/steal")


class TestBuildLLMFugu:
    def test_fugu_mode_needs_key(self):
        with pytest.raises(FailClosedError):
            build_llm(AppConfig(llm_mode="fugu", fugu_api_key=None))

    def test_fugu_mode_builds_adapter(self):
        llm = build_llm(AppConfig(llm_mode="fugu", fugu_api_key="fish_x", fugu_model="fugu"))
        assert isinstance(llm, FuguLLM)
        assert llm.model == "fugu" and llm.host == "https://api.sakana.ai/v1"

    def test_live_is_alias_for_fugu(self):
        assert isinstance(build_llm(AppConfig(llm_mode="live", fugu_api_key="fish_x")), FuguLLM)
