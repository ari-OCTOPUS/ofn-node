#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_owner_readiness — پروبِ آمادگیِ ساعتِ اولِ مالک.

    شکلِ خروجی · فایلِ غایب هرگز استثنا نمی‌دهد · کارتِ جاسوسِ ۹۰۱۰ گیر می‌افتد ·
    پالسِ کهنه گیر می‌افتد · outbound ِ مسلحِ بی‌SMTP مانع می‌شود ·
    و مهم‌تر از همه: **check هیچ‌چیز نمی‌نویسد** (اسنپ‌شاتِ قبل/بعدِ درختِ موقت).
"""
import json
import os
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("tg-owner-readiness")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import owner_readiness as orr  # noqa: E402

STATE = Path(ENV["ops"]) / "state"
ROOT = Path(ENV["root"])
NOW = 1785480000.0            # ۲۰۲۶-۰۷-۳۱ حوالیِ عصر — ساعتِ تزریقی، نه دیوار


# ── سازندهٔ صحنه ────────────────────────────────────────────────────────────
def _w(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), "utf-8")


def _flags_snapshot(proc: str, pid: int, *, overrides=None, src_mtime=None):
    flags = {f: 1 for f in orr.REQUIRED_FLAGS["center"]}
    flags.update({f: 1 for f in orr.REQUIRED_FLAGS["organism"]})
    flags.update(overrides or {})
    return {"schema": "flags-loaded.v1", "proc": proc, "pid": pid,
            "source": str(Path(ENV["ops"]) / "OCTOPUS-flags.cmd"),
            "source_mtime": float(src_mtime if src_mtime is not None else NOW),
            "boot_ts": NOW, "file_flags": sorted(flags), "flags": flags,
            "secret_names": []}


def _healthy_scene(*, pulse_ts=None, leg_card_ids=None, outbound=False) -> None:
    """صحنهٔ «همه‌چیز خوب» در vault ِ موقتِ harness."""
    _w(STATE / "pulse" / "tg-center.json",
       {"ts": "2026-07-31T16:00:00", "pid": 4242,
        "mono": float(pulse_ts if pulse_ts is not None else NOW - 10)})
    _w(STATE / "ORGANISM-STATE.json",
       {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(NOW - 20)),
        "beat": 19990, "halted": False, "stop_organism": False})
    ov = {"OCTOPUS_WIRE_LEAD_OUTBOUND": 1} if outbound else {}
    _w(STATE / "flags-loaded-center.json",
       _flags_snapshot("center", 4242, overrides=ov))
    _w(STATE / "flags-loaded-organism.json",
       _flags_snapshot("organism", 4243, overrides=ov))
    _w(STATE / "telegram" / "center-config.json",
       {"chat_id": -1004475788460,
        "topics": {t: 20 + i for i, t in enumerate(orr.CONTRACT_LEG_TOPICS)},
        "guide_message_id": 358, "guide_hash": "a" * 16,
        "dm_guide_message_id": 177, "dm_guide_hash": "b" * 16,
        "home_message_id": 149,
        "leg_card_ids": leg_card_ids if leg_card_ids is not None
        else {"lead": 354, "ziman": 356}})
    _w(STATE / "telegram" / "miniapp-url.json",
       {"url": "https://example-tunnel.invalid", "started": "2026-07-31T05:35:04Z",
        "pid": 24636})
    _w(STATE / "legs" / "lead-pipeline.json", {"stuck": {}, "followups": {}})
    (STATE / "telegram" / "legs").mkdir(parents=True, exist_ok=True)
    (ROOT / "10 - Telegram processing" / "Raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "_Templates").mkdir(parents=True, exist_ok=True)
    # لانچرِ ساختگی که ORG_ROOT را ست می‌کند (وگرنه چکِ vault قرمز است)
    cmd = Path(ENV["ops"]) / "OCTOPUS-flags.cmd"
    cmd.parent.mkdir(parents=True, exist_ok=True)
    cmd.write_text("rem flags\nset ORG_ROOT=" + str(ROOT) + "\n"
                   + "\n".join(f"set {f}=1" for f in orr.REQUIRED_FLAGS["center"])
                   + "\nset OCTOPUS_WIRE_LEAD_PIPELINE=1\n"
                     "set OCTOPUS_WIRE_LEAD_OUTBOUND=0\n"
                     "set OCTOPUS_WIRE_LEAD_DISCOVERY=0\n", "utf-8")
    os.utime(cmd, (NOW - 60, NOW - 60))


def _wipe() -> None:
    import shutil
    for p in (STATE / "pulse", STATE / "telegram", STATE / "legs",
              STATE / "reminders"):
        shutil.rmtree(p, ignore_errors=True)
    for p in (STATE / "flags-loaded-center.json",
              STATE / "flags-loaded-organism.json",
              STATE / "ORGANISM-STATE.json",
              Path(ENV["ops"]) / "OCTOPUS-flags.cmd"):
        try:
            p.unlink()
        except OSError:
            pass


def _by_name(res: dict) -> dict:
    return {c["name"]: c for c in res["checks"]}


def _snapshot_tree(root: Path) -> dict:
    """مسیر → (اندازه, mtime) برای هر فایلِ درخت. مبنایِ اثباتِ «صفر نوشتن»."""
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            try:
                st = p.stat()
            except OSError:
                continue
            out[str(p)] = (st.st_size, round(st.st_mtime, 3))
    return out


# ── شکلِ قرارداد ───────────────────────────────────────────────────────────
def t_every_check_returns_the_documented_shape():
    _wipe()
    _healthy_scene()
    res = orr.check(live=False, now=NOW)
    assert set(res) == {"ok", "checks"}, res.keys()
    assert isinstance(res["ok"], bool)
    assert isinstance(res["checks"], list) and res["checks"], "چک‌لیستِ خالی"
    for c in res["checks"]:
        assert {"name", "ok", "detail", "fix"} <= set(c), c
        assert isinstance(c["name"], str) and c["name"], c
        assert isinstance(c["ok"], bool), c
        assert isinstance(c["detail"], str) and c["detail"].strip(), c
        assert isinstance(c["fix"], str), c
        assert c["level"] in (orr.OK, orr.WARN, orr.BLOCKER), c
        assert c["ok"] == (c["level"] != orr.BLOCKER), c


def t_every_failing_check_carries_a_fix_line():
    _wipe()                      # همه‌چیز غایب ⇒ بیشترین شمارِ قرمز
    res = orr.check(live=False, now=NOW)
    bad = [c for c in res["checks"] if c["level"] == orr.BLOCKER and not c["fix"]]
    assert not bad, f"مانعِ بی‌فیکس: {[c['name'] for c in bad]}"


def t_overall_ok_is_exactly_no_blockers():
    _wipe()
    _healthy_scene()
    res = orr.check(live=False, now=NOW)
    assert res["ok"] == all(c["level"] != orr.BLOCKER for c in res["checks"])


# ── غیاب هرگز استثنا نیست ──────────────────────────────────────────────────
def t_missing_files_never_raise():
    _wipe()
    res = orr.check(live=False, now=NOW)     # هیچ فایلی نیست
    assert isinstance(res["checks"], list) and len(res["checks"]) >= 10
    assert res["ok"] is False, "درختِ خالی نباید سبز باشد"
    crashed = [c["name"] for c in res["checks"] if c["name"].endswith(".crashed")]
    assert not crashed, f"خانوادهٔ چک منفجر شد: {crashed}"


def t_corrupt_json_is_reported_not_raised():
    _wipe()
    _healthy_scene()
    (STATE / "telegram" / "center-config.json").write_text("{ نه JSON", "utf-8")
    res = orr.check(live=False, now=NOW)
    row = _by_name(res)["telegram.config"]
    assert row["level"] == orr.BLOCKER and "bad-json" in row["detail"], row


# ── دام‌های واقعی ──────────────────────────────────────────────────────────
def t_a_planted_spy_leg_card_id_is_flagged():
    _wipe()
    _healthy_scene(leg_card_ids={"lead": 354, "ziman": 9010})
    row = _by_name(orr.check(live=False, now=NOW))["telegram.leg_cards"]
    assert row["level"] == orr.BLOCKER, row
    assert "9010" in row["detail"] and "ziman" in row["detail"], row


def t_a_leg_card_id_just_outside_the_spy_range_is_clean():
    _wipe()
    _healthy_scene(leg_card_ids={"lead": 8999, "ziman": 9101})
    row = _by_name(orr.check(live=False, now=NOW))["telegram.leg_cards"]
    assert row["level"] == orr.OK, row


def t_a_stale_center_pulse_is_flagged():
    _wipe()
    _healthy_scene(pulse_ts=NOW - (orr.PULSE_MAX_S + 60))
    row = _by_name(orr.check(live=False, now=NOW))["processes.center_pulse"]
    assert row["level"] == orr.BLOCKER, row
    assert row["fix"], "پالسِ کهنه باید فیکس داشته باشد"


def t_a_fresh_pulse_is_green():
    _wipe()
    _healthy_scene(pulse_ts=NOW - 5)
    row = _by_name(orr.check(live=False, now=NOW))["processes.center_pulse"]
    assert row["level"] == orr.OK, row


def t_outbound_armed_without_smtp_creds_is_a_blocker():
    _wipe()
    _healthy_scene(outbound=True)
    for k in orr.SMTP_ENV:
        os.environ.pop(k, None)
    res = orr.check(live=False, now=NOW)
    row = _by_name(res)["lead.outbound"]
    assert row["level"] == orr.BLOCKER and row["ok"] is False, row
    assert "SMTP" in row["detail"], row
    assert res["ok"] is False, "outbound ِ مسلح باید کلِ گیت را ببندد"
    # همان فلگ در خانوادهٔ flags هم مانع است — دو ناظرِ مستقل
    assert _by_name(res)["flags.off.OCTOPUS_WIRE_LEAD_OUTBOUND"]["level"] == \
        orr.BLOCKER


def t_the_send_cap_is_pinned_to_the_owners_vote():
    _wipe()
    _healthy_scene()
    row = _by_name(orr.check(live=False, now=NOW))["lead.cap"]
    assert row["level"] == orr.OK and "10" in row["detail"], row


def t_a_required_flag_that_is_off_in_the_snapshot_is_a_blocker():
    _wipe()
    _healthy_scene()
    _w(STATE / "flags-loaded-center.json",
       _flags_snapshot("center", 4242, overrides={"OCTOPUS_TG_CAPTURE": 0}))
    row = _by_name(orr.check(live=False, now=NOW))["flags.center"]
    assert row["level"] == orr.BLOCKER and "OCTOPUS_TG_CAPTURE" in row["detail"]


def t_armed_in_the_file_but_absent_from_the_snapshot_is_caught():
    """تلهٔ کلاسیک — فایل مسلح است، پروسهٔ زنده اصلاً این کلید را ندارد."""
    _wipe()
    _healthy_scene()
    snap = _flags_snapshot("center", 4242)
    snap["flags"].pop("OCTOPUS_TG_QBUDGET")
    _w(STATE / "flags-loaded-center.json", snap)
    row = _by_name(orr.check(live=False, now=NOW))["flags.center"]
    assert row["level"] == orr.BLOCKER, row
    assert "OCTOPUS_TG_QBUDGET" in row["detail"], row
    assert "در پروسه غایب" in row["detail"], row


def t_a_process_running_older_flags_than_the_file_is_flagged():
    _wipe()
    _healthy_scene()
    _w(STATE / "flags-loaded-center.json",
       _flags_snapshot("center", 4242, src_mtime=NOW - 3600,
                       overrides={"OCTOPUS_WIRE_LEAD_DISCOVERY": 1}))
    res = orr.check(live=False, now=NOW)
    fresh = _by_name(res)["flags.fresh.center"]
    assert fresh["level"] == orr.WARN, fresh
    assert "OCTOPUS_WIRE_LEAD_DISCOVERY" in fresh["detail"], fresh
    off = _by_name(res)["flags.off.OCTOPUS_WIRE_LEAD_DISCOVERY"]
    assert off["level"] == orr.WARN and off["ok"] is True, off


def t_a_redacted_snapshot_value_never_fakes_a_drift():
    _wipe()
    _healthy_scene()
    snap = _flags_snapshot("center", 4242, src_mtime=NOW - 3600)
    snap["flags"]["OCTOPUS_TG_CAPTURE"] = orr.REDACTED
    _w(STATE / "flags-loaded-center.json", snap)
    row = _by_name(orr.check(live=False, now=NOW))["flags.fresh.center"]
    assert "OCTOPUS_TG_CAPTURE" not in row["detail"], row


def t_a_launcher_without_org_root_is_a_blocker():
    _wipe()
    _healthy_scene()
    cmd = Path(ENV["ops"]) / "OCTOPUS-flags.cmd"
    cmd.write_text("rem set ORG_ROOT=F:\\backup\nset OCTOPUS_TG_CAPTURE=1\n",
                   "utf-8")          # فقط داخلِ کامنت — یعنی ست نمی‌شود
    row = _by_name(orr.check(live=False, now=NOW))["vault.org_root"]
    assert row["level"] == orr.BLOCKER, row
    assert "ORG_ROOT" in row["fix"], row


def t_a_launcher_with_org_root_is_green():
    _wipe()
    _healthy_scene()
    row = _by_name(orr.check(live=False, now=NOW))["vault.org_root"]
    assert row["level"] == orr.OK, row


def t_all_eight_contract_leg_topics_are_required():
    _wipe()
    _healthy_scene()
    cfg_p = STATE / "telegram" / "center-config.json"
    cfg = json.loads(cfg_p.read_text("utf-8"))
    cfg["topics"].pop("cartographer")
    _w(cfg_p, cfg)
    row = _by_name(orr.check(live=False, now=NOW))["telegram.topics"]
    assert row["level"] == orr.BLOCKER and "cartographer" in row["detail"], row


def t_a_bad_kpi_daily_shape_is_flagged_and_absence_is_fine():
    _wipe()
    _healthy_scene()
    assert _by_name(orr.check(live=False, now=NOW))["telegram.kpi_daily"]["level"] \
        == orr.OK, "غیابِ KPI طبیعی است"
    cfg_p = STATE / "telegram" / "center-config.json"
    cfg = json.loads(cfg_p.read_text("utf-8"))
    cfg["kpi_daily"] = {"lead": "پنج"}
    _w(cfg_p, cfg)
    row = _by_name(orr.check(live=False, now=NOW))["telegram.kpi_daily"]
    assert row["level"] == orr.BLOCKER, row


def t_an_absent_optional_store_is_honest_not_red():
    _wipe()
    _healthy_scene()
    names = _by_name(orr.check(live=False, now=NOW))
    for n in ("stores.reminders", "stores.question_budget"):
        assert names[n]["level"] == orr.OK, names[n]
        assert "ساخته نشده" in names[n]["detail"], names[n]


def t_a_broken_leg_task_file_is_flagged():
    _wipe()
    _healthy_scene()
    (STATE / "telegram" / "legs" / "lead-tasks.json").write_text("[[", "utf-8")
    row = _by_name(orr.check(live=False, now=NOW))["stores.leg_tasks"]
    assert row["level"] == orr.BLOCKER and "lead-tasks.json" in row["detail"]


def t_a_non_https_miniapp_url_is_a_blocker():
    _wipe()
    _healthy_scene()
    _w(STATE / "telegram" / "miniapp-url.json",
       {"url": "http://insecure.invalid", "pid": 1})
    row = _by_name(orr.check(live=False, now=NOW))["miniapp.url"]
    assert row["level"] == orr.BLOCKER and "https" in row["detail"], row


# ── ناوردای بزرگ: صفر نوشتن ────────────────────────────────────────────────
def t_check_never_writes_anything():
    _wipe()
    _healthy_scene()
    before = _snapshot_tree(ROOT)
    orr.check(live=False, now=NOW)
    after = _snapshot_tree(ROOT)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    assert not added, f"check فایلِ نو ساخت: {added}"
    assert not removed, f"check فایل پاک کرد: {removed}"
    assert not changed, f"check فایل را عوض کرد: {changed}"


def t_check_writes_nothing_even_when_the_tree_is_empty():
    _wipe()
    before = _snapshot_tree(ROOT)
    orr.check(live=False, now=NOW)
    after = _snapshot_tree(ROOT)
    assert before == after, sorted(set(after) ^ set(before))


def _code_without_prose(path: Path) -> str:
    """سورس بدونِ docstring و بدونِ کامنت — وگرنه واژهٔ ممنوع در **توضیح**
    خودش تست را قرمز می‌کند، و نویسنده توضیح را پاک می‌کند نه کد را."""
    import ast
    import io
    import tokenize
    src = path.read_text("utf-8")
    lines = src.splitlines()
    drop = set()
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None) or []
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            drop.update(range(body[0].lineno,
                              (body[0].end_lineno or body[0].lineno) + 1))
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            drop.add(tok.start[0])
    return "\n".join("" if i + 1 in drop else ln for i, ln in enumerate(lines))


def t_the_module_holds_no_send_and_no_poller():
    """صفر ارسال، صفر getUpdates — مرزِ سختِ این لِین، به‌جای اعتماد."""
    import ast
    src = Path(orr.__file__).read_text("utf-8")
    code = _code_without_prose(Path(orr.__file__))
    assert "getUpdates" in src and "getUpdates" not in code, \
        "قرارداد باید در توضیح بماند و در کد نباشد"
    for banned in ("getUpdates", "poll_updates", "sendMessage", "send_text",
                   "urlopen", "import requests"):
        assert banned not in code, f"مرزِ شکسته: {banned}"
    tree = ast.parse(src)
    calls = {getattr(n.func, "attr", None) for n in ast.walk(tree)
             if isinstance(n, ast.Call)}
    for banned in ("bind", "listen", "sendall", "mkdir", "write_text",
                   "write_bytes", "replace", "unlink", "rmtree", "makedirs"):
        assert banned not in calls, f"فراخوانیِ ممنوع در پروب: {banned}"
    assert "connect_ex" in calls, "پروبِ پورت باید فقط connect_ex باشد"


def t_live_false_never_touches_a_socket():
    """live=False = صفر سوکت — با جایگزینیِ موقتِ خودِ سازندهٔ سوکت اثبات می‌شود."""
    import socket as _s
    calls = []
    real = _s.socket

    def spy(*a, **k):
        calls.append(a)
        return real(*a, **k)

    _s.socket = spy
    try:
        _wipe()
        _healthy_scene()
        orr.check(live=False, now=NOW)
    finally:
        _s.socket = real
    assert not calls, f"live=False سوکت ساخت: {calls}"


def t_render_marks_every_line_and_lists_the_blockers():
    _wipe()
    _healthy_scene(outbound=True)
    res = orr.check(live=False, now=NOW)
    txt = orr.render(res)
    assert "❌" in txt and "موانع به ترتیب" in txt, txt[:200]
    for c in res["checks"]:
        assert c["name"] in txt, c["name"]
    assert txt.count("\n") >= len(res["checks"]), "هر چک باید یک خط داشته باشد"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    P = orr._paths()
    assert not str(P["state"]).lower().startswith(live), P["state"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_owner_readiness: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
