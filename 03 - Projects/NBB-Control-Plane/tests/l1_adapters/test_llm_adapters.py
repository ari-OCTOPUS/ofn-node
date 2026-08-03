import pytest

pytestmark = pytest.mark.l1

from nbb_cp.adapters.llm.cassette import (
    CassetteMissError,
    RecordingLLM,
    ReplayLLM,
    request_key,
)
from nbb_cp.adapters.llm.mock import MockLLM
from nbb_cp.kernel.ports import LLMRequest


class TestMockLLM:
    def test_deterministic_for_same_prompt(self):
        llm = MockLLM()
        request = LLMRequest(task="govern", prompt="allocate epoch 0")
        assert llm.complete(request).text == llm.complete(request).text

    def test_distinct_prompts_distinct_answers(self):
        llm = MockLLM()
        a = llm.complete(LLMRequest(task="govern", prompt="alpha"))
        b = llm.complete(LLMRequest(task="govern", prompt="beta"))
        assert a.text != b.text


class TestCassette:
    def test_record_then_replay_roundtrip(self, tmp_path):
        path = tmp_path / "tape.jsonl"
        recorder = RecordingLLM(MockLLM(), path)
        request = LLMRequest(task="govern", prompt="allocate epoch 1")
        live = recorder.complete(request)

        replay = ReplayLLM(path)
        replayed = replay.complete(request)
        assert replayed.text == live.text
        assert replayed.input_tokens == live.input_tokens

    def test_replay_miss_fails_closed(self, tmp_path):
        path = tmp_path / "tape.jsonl"
        RecordingLLM(MockLLM(), path).complete(LLMRequest(task="govern", prompt="known"))
        replay = ReplayLLM(path)
        with pytest.raises(CassetteMissError, match="drifted"):
            replay.complete(LLMRequest(task="govern", prompt="never recorded"))

    def test_missing_cassette_file_fails_closed(self, tmp_path):
        with pytest.raises(CassetteMissError, match="not found"):
            ReplayLLM(tmp_path / "ghost.jsonl")

    def test_corrupt_cassette_line_fails_closed(self, tmp_path):
        path = tmp_path / "tape.jsonl"
        path.write_text('{"key": "ok"...broken\n', encoding="utf-8")
        with pytest.raises(CassetteMissError, match="corrupt"):
            ReplayLLM(path)

    def test_key_depends_on_task_and_prompt(self):
        a = request_key(LLMRequest(task="govern", prompt="x"))
        b = request_key(LLMRequest(task="summarize", prompt="x"))
        c = request_key(LLMRequest(task="govern", prompt="y"))
        assert len({a, b, c}) == 3
