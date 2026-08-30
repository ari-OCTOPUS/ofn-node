"""test_execution_board.py — «تختهٔ اجرا» (Execution Board، فقط‌خواندنی).

رویدادها/حالتِ کار → شش خط: queued/running/blocked/awaiting_user/done/quarantined.
پوشش: bucketingِ درست، تقدمِ awaiting بر blocked، cap، حالتِ خالی → همه خالی،
صفِ کار از templateهای سررسیده، containment scrub، fail-soft روی خطِ خراب، و «هیچ نوشتنی».
standalone — در run_all.py ثبت نمی‌شود. اجرا با REAL_VAULT=<worktree root>.
"""
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("execboard")

import execution_board as eb   # noqa: E402
import opslib                  # noqa: E402
import events                  # noqa: E402


# ─── ابزارِ تست (نوشتن فقط در sandboxِ موقت) ───────────────────────────────────────
def _reset():
    """هر تست از یک لوحِ پاک شروع می‌شود (رویداد + نقشه/حالتِ کار)."""
    p = opslib.STATE_DIR / "events.jsonl"
    if p.exists():
        p.unlink()
    pulse = opslib.STATE_DIR / "pulse"
    for f in ("work-plan.json", "work-state.json"):
        fp = pulse / f
        if fp.exists():
            fp.unlink()


def _write_json(rel, data):
    p = opslib.STATE_DIR / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), "utf-8")


def _traces(b, lane):
    return {i["trace"] for i in b[lane]}


# ─── تست‌ها ────────────────────────────────────────────────────────────────────────
def t_a_empty_state_all_lanes_empty():
    """نبودِ هر state → همهٔ خطوط خالی، شمارشِ کل صفر، بدونِ crash."""
    _reset()
    b = eb.board()
    for lane in eb.LANES:
        assert b[lane] == [], f"{lane} باید خالی باشد، بود: {b[lane]}"
    assert b["counts"]["total"] == 0
    assert b["schema"] == "execution-board.v1"
    assert set(eb.LANES).issubset(b.keys()) and "counts" in b


def t_b_lane_bucketing():
    """هر نوع رویداد به خطِ درستش می‌رود؛ startedِ تمام‌شده در running نیست."""
    _reset()
    events.emit("task.started", "pump/health", summary="بررسیِ سلامت", trace_id="r1")
    events.emit("task.started", "pump/gap", summary="یافتنِ گپ", trace_id="d1")
    events.emit("task.completed", "pump/gap", summary="گپ انجام شد", trace_id="d1")
    events.emit("task.failed", "spawn", summary="اسپاون شکست", trace_id="q1", status="failed")
    events.emit("task.blocked", "recon", summary="منتظرِ CSV", trace_id="b1",
                approval_state="none")
    events.emit("approval.required", "doctor", summary="تأییدِ RFC", trace_id="a1",
                approval_state="required")
    b = eb.board()
    assert "r1" in _traces(b, "running"), "startedِ باز باید running باشد"
    assert "d1" not in _traces(b, "running"), "startedِ تمام‌شده نباید running بماند"
    assert "d1" in _traces(b, "done")
    assert "q1" in _traces(b, "quarantined")
    assert "b1" in _traces(b, "blocked")
    assert "a1" in _traces(b, "awaiting_user")
    # taskِ completed نباید در quarantined/blocked دوباره بیاید
    assert "d1" not in _traces(b, "quarantined") and "d1" not in _traces(b, "blocked")


def t_c_blocked_with_required_goes_to_awaiting():
    """تقدم: task.blocked با approval_state=required → awaiting_user، نه blocked."""
    _reset()
    events.emit("task.blocked", "stress-homeostat", summary="ترس — نیازِ مالک",
                trace_id="br1", approval_state="required")
    b = eb.board()
    assert "br1" in _traces(b, "awaiting_user")
    assert "br1" not in _traces(b, "blocked"), "منتظرِ مالک غالب است بر blocked"


def t_d_cap_enforced_per_lane():
    """بیش از CAP رویداد در یک خط → دقیقاً CAP آیتم (کران‌دار)."""
    _reset()
    n = eb.CAP + 8
    for i in range(n):
        events.emit("task.completed", f"w{i}", summary=f"کارِ {i}", trace_id=f"c{i}")
    for i in range(n):
        events.emit("task.started", f"s{i}", summary=f"شروعِ {i}", trace_id=f"s{i}")
    b = eb.board()
    assert len(b["done"]) == eb.CAP, f"done باید {eb.CAP} باشد، بود {len(b['done'])}"
    assert len(b["running"]) == eb.CAP, f"running باید {eb.CAP} باشد، بود {len(b['running'])}"
    assert b["counts"]["done"] == eb.CAP and b["counts"]["running"] == eb.CAP


def t_e_queued_from_due_templates():
    """templateِ سررسیده (never-run یا کهنه) → queued؛ تازه‌اجراشده → نه."""
    _reset()
    _write_json("pulse/work-plan.json", {
        "schema": "work-plan.v1",
        "templates": [
            {"kind": "health", "every_s": 100, "paid": False, "goal": "سلامت"},
            {"kind": "search", "every_s": 100, "paid": True, "goal": "سرچِ عمیق"},
        ],
    })
    # health همین الان اجرا شد (سررسید نیست)، search هرگز اجرا نشده (سررسید است)
    _write_json("pulse/work-state.json", {"last_run": {"health": time.time()}})
    b = eb.board()
    kinds = {i["kind"] for i in b["queued"]}
    assert "search" in kinds, "templateِ هرگز-اجرانشده باید در صف باشد"
    assert "health" not in kinds, "templateِ تازه‌اجراشده نباید در صف باشد"
    paid = {i["kind"]: i["paid"] for i in b["queued"]}
    assert paid.get("search") is True


def t_f_containment_scrub():
    """هیچ رشتهٔ هویتِ Project-F هرگز از board بیرون نمی‌رود (scrub)."""
    _reset()
    events.emit("task.completed", "صبا-bot", summary="کارِ onlyfans تمام شد",
                trace_id="cx", next_action="اونلی")
    b = eb.board()
    blob = json.dumps(b, ensure_ascii=False)
    for banned in eb._BANNED_ECHO:
        assert banned not in blob, f"رشتهٔ ممنوع «{banned}» نشت کرد"
    item = b["done"][0]
    assert item["agent"] == "(redacted:containment)"
    assert item["summary"] == "(redacted:containment)"


def t_g_fail_soft_on_broken_events():
    """خطوطِ خرابِ jsonl → board نمی‌شکند و رویدادهای سالم را می‌خواند."""
    _reset()
    p = opslib.STATE_DIR / "events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write("این json نیست\n")
        f.write("{ناقص\n")
        f.write(json.dumps({"event_name": "task.completed", "agent_id": "ok",
                            "summary": "سالم", "trace_id": "good"}) + "\n")
    b = eb.board()   # نباید crash کند
    assert "good" in _traces(b, "done")


def t_h_no_writes_side_effects():
    """board() هیچ فایلی نمی‌سازد/تغییر نمی‌دهد (خالص، read-only)."""
    _reset()
    events.emit("task.completed", "w", summary="کار", trace_id="n1")
    _write_json("pulse/work-plan.json", {"schema": "work-plan.v1",
                "templates": [{"kind": "health", "every_s": 1, "paid": False}]})

    def snap():
        out = {}
        for pp in Path(ENV["root"]).rglob("*"):
            if pp.is_file():
                try:
                    out[str(pp)] = pp.stat().st_mtime
                except OSError:
                    pass
        return out

    before = snap()
    eb.board()
    eb.board()
    after = snap()
    assert before == after, ("board() نباید چیزی بنویسد؛ تفاوت: "
                             f"{set(before) ^ set(after) or 'mtime تغییر کرد'}")


def t_i_counts_total_matches_lanes():
    """counts.total = جمعِ طولِ شش خط."""
    _reset()
    events.emit("task.started", "a", summary="s", trace_id="R")
    events.emit("task.completed", "b", summary="d", trace_id="D")
    events.emit("task.failed", "c", summary="q", trace_id="Q", status="failed")
    b = eb.board()
    lane_sum = sum(len(b[k]) for k in eb.LANES)
    assert b["counts"]["total"] == lane_sum
    for k in eb.LANES:
        assert b["counts"][k] == len(b[k])


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_execution_board: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)