"""test_tg_exec_consumer.py — TG-EXEC (2026-07-15): مصرف‌کنندهٔ صفِ cockpit-requests.
پوشش: فلگ‌خاموش=no-op · first-activation ffwd (بدونِ replay) · halt-gate ·
verbِ ناامن → ack ولی اجرا نه · at-most-once (cursor پیش از exec) · verbِ امن اجرا می‌شود."""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg_exec_consumer")

import wiring as w  # noqa: E402


def _seed(sd: Path, rows):
    sd.mkdir(parents=True, exist_ok=True)
    with open(sd / "cockpit-requests.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def t_a_flag_off_noop():
    os.environ.pop("OCTOPUS_TG_EXEC", None)
    with tempfile.TemporaryDirectory() as td:
        r = w.cockpit_requests_beat(state_dir=td)
        assert r.get("skipped") == "flag-off", r


def t_b_first_activation_ffwd_no_replay():
    """اولین beat بعدِ فعال‌سازی نباید backlogِ تاریخی را اجرا کند."""
    os.environ["OCTOPUS_TG_EXEC"] = "1"
    try:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td)
            _seed(sd, [{"verb": "consolidate", "key": "run", "status": "requested"}])
            r1 = w.cockpit_requests_beat(state_dir=str(sd))
            assert r1.get("skipped") == "first-activation-ffwd", r1
            assert (sd / "cockpit-requests.cursor").exists()
    finally:
        os.environ.pop("OCTOPUS_TG_EXEC", None)


def t_c_halt_blocks():
    os.environ["OCTOPUS_TG_EXEC"] = "1"
    stop = w.opslib.STOP_ORGANISM
    stop.write_text("halt", "utf-8")
    try:
        with tempfile.TemporaryDirectory() as td:
            r = w.cockpit_requests_beat(state_dir=td)
            assert r.get("skipped") == "halt", r
    finally:
        try:
            stop.unlink()
        except OSError:
            pass
        os.environ.pop("OCTOPUS_TG_EXEC", None)


def t_d_safe_verb_runs_after_activation():
    """بعد از ffwd، یک درخواستِ نوِ consolidate واقعاً مصرف می‌شود (consolidate_once no-op ولی 'ran')."""
    os.environ["OCTOPUS_TG_EXEC"] = "1"
    try:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td)
            _seed(sd, [])                          # خالی → ffwd روی 0
            w.cockpit_requests_beat(state_dir=str(sd))   # cursor=0
            with open(sd / "cockpit-requests.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"verb": "consolidate", "key": "run", "status": "requested"}) + "\n")
            r = w.cockpit_requests_beat(state_dir=str(sd))
            assert "consolidate:run" in (r.get("ran") or []), r
    finally:
        os.environ.pop("OCTOPUS_TG_EXEC", None)


def t_e_unsafe_verb_acked_not_run():
    """school در _TG_EXEC_KNOWN هست ولی در SAFE نیست → ack، اجرا نه (بدونِ دکمهٔ مرده)."""
    os.environ["OCTOPUS_TG_EXEC"] = "1"
    acks = []

    class _Ch:
        def send_text(self, t, reply_markup=None):
            acks.append(t)

    try:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td)
            _seed(sd, [])
            w.cockpit_requests_beat(state_dir=str(sd))
            with open(sd / "cockpit-requests.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"verb": "school", "key": "learn", "status": "requested"}) + "\n")
            r = w.cockpit_requests_beat(state_dir=str(sd), channel=_Ch())
            assert any("school" in a for a in acks), acks
            assert "school:learn:not-enabled" in (r.get("skipped") or []), r
    finally:
        os.environ.pop("OCTOPUS_TG_EXEC", None)


if __name__ == "__main__":
    for f in (t_a_flag_off_noop, t_b_first_activation_ffwd_no_replay, t_c_halt_blocks,
              t_d_safe_verb_runs_after_activation, t_e_unsafe_verb_acked_not_run):
        f()
        print("ok", f.__name__)
    print("PASS test_tg_exec_consumer")
