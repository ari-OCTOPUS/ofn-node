#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تست‌های OCTOPUS OS v1 — هر تست یک خاصیتِ سند را *ثابت* می‌کند، نه ادعا."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from honest_metric import (Measurement, MetricRegistry, Provenance,  # noqa: E402
                           combine_quality, publish_signed, self_reference_share)
from outcome_ledger import (close_intents, dedupe_intents,  # noqa: E402
                            improvement_rate, moved_bit, movement_keys)
from efe import (BETA_EPISTEMIC_MAX, Constraint, EFEConfig, Policy,  # noqa: E402
                 evaluate, kernel_constraints, select)
from silence import Kind, Msg, SilenceGate  # noqa: E402
from leg_failure import FailureRecorder, capture  # noqa: E402
from mission_runner import MissionRunner  # noqa: E402

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}" + (f"  — {detail}" if detail else ""))


# ═══════════════════════════════════════════════ §۰ honest_metric
def t_honest_metric() -> None:
    print("\n§۰ — هفت بیماری، یک واکسن")

    # velocity: ۹۶.۴٪ متروَنومِ خودش (دادهٔ واقعیِ ۲۵ جولای)
    vel = Measurement("velocity_per_hr", 5.8583, Provenance.DERIVED,
                      receipt="pulse/velocity-stream.jsonl",
                      components={"beats_self": 1356, "consolidation_self": 5,
                                  "confirmed": 0, "effects": 0})
    check("velocity خودارجاع رد می‌شود", not vel.may_vote and vel.w_q == 0.0,
          f"share={self_reference_share(vel.components):.3f} w_q={vel.w_q}")

    # moved: شمارندهٔ کشف‌های خودش ⇒ درون‌زاد
    mv = Measurement("moved", 1.0, Provenance.ENDOGENOUS, receipt="outcomes.jsonl")
    check("سنجهٔ درون‌زاد حق رأی ندارد", not mv.may_vote)

    # innervation 100% — رسید ندارد (فقط mtime)
    inv = Measurement("innervation_pct", 100.0, Provenance.DERIVED, receipt=None)
    check("سنجهٔ بی‌رسید رد می‌شود", inv.w_q == 0.0)

    # سنجهٔ سالم: پولِ تأییدشده
    ok = Measurement("confirmed_revenue_aud", 250.0, Provenance.EXOGENOUS,
                     receipt="reconcile-job + CSV بانکی", quality=1.0)
    check("سنجهٔ برون‌زادِ رسیددار رأی می‌دهد", ok.may_vote and ok.w_q == 1.0)

    # منشأ نامعلوم = fail-closed
    unk = Measurement("x", 1.0, Provenance.UNKNOWN, receipt="r")
    check("منشأ نامعلوم fail-closed است", unk.w_q == 0.0)

    # ترکیبِ ضربی — یک صفر همه را می‌کشد (برخلافِ میانگین)
    check("combine_quality ضربی است، نه میانگین",
          combine_quality(1.0, 1.0, 0.0) == 0.0 and abs(combine_quality(0.5, 0.5) - 0.25) < 1e-9)

    # publish_signed — عددِ منفی منتشر می‌شود
    check("delta_self منفی clamp نمی‌شود",
          abs(publish_signed(-0.02573) - (-0.02573)) < 1e-12)

    reg = MetricRegistry()
    for m in (vel, mv, inv, ok):
        reg.put(m)
    r = reg.report()
    check("دفتر: ۱ رأی‌دهنده از ۴", r["n_voting"] == 1 and r["n_silenced"] == 3)
    check("مقدارِ وزن‌دارِ سنجهٔ خفه صفر است", reg.weighted("velocity_per_hr") == 0.0)


# ═══════════════════════════════════════════════ §۳ outcome_ledger
def t_outcome_ledger() -> None:
    print("\n§۳ — تابعِ پاداش: تناقض ساختاراً ناممکن")

    # بازسازیِ دقیقِ باگ: یک id، سه baselineِ متفاوت در پنجره
    intents = [
        {"id": "up-A", "baseline": {"confirmed_revenue": 0, "total_discoveries": 1}},
        {"id": "up-A", "baseline": {"confirmed_revenue": 0, "total_discoveries": 5}},
        {"id": "up-A", "baseline": {"confirmed_revenue": 0, "total_discoveries": 9}},
        {"id": "up-B", "baseline": {"confirmed_revenue": 0, "total_discoveries": 2}},
    ]
    check("dedupe: ۴ سطر ⇒ ۲ نیتِ متمایز", len(dedupe_intents(intents)) == 2)
    check("dedupe قدیمی‌ترین baseline را نگه می‌دارد",
          dedupe_intents(intents)[0]["baseline"]["total_discoveries"] == 1)

    now = {"confirmed_revenue": 0, "total_discoveries": 42}   # فقط درون‌زاد رشد کرد
    cl = close_intents(intents, [], now, ts="2026-07-25T12:00:00")
    keys = [c.key for c in cl]
    check("هر کلید حداکثر یک بستار", len(keys) == len(set(keys)))
    check("رشدِ total_discoveries بیت را روشن **نمی‌کند**",
          all(c.moved is False for c in cl),
          "درون‌زاد رأی نمی‌دهد")

    # حالا یک متریکِ برون‌زاد واقعاً جلو می‌رود
    now2 = {"confirmed_revenue": 250, "total_discoveries": 42}
    intents2 = [{"id": "up-A", "baseline": {"confirmed_revenue": 0, "total_discoveries": 1}}]
    cl2 = close_intents(intents2, [], now2, ts="t")
    check("رشدِ confirmed_revenue بیت را روشن می‌کند",
          len(cl2) == 1 and cl2[0].moved and "confirmed_revenue" in cl2[0].movers)

    check("movement_keys شاملِ total_discoveries نیست",
          "total_discoveries" not in movement_keys(now2, intents2[0]["baseline"]))

    # مخرجِ درست: ۸۳ رکورد روی ۴ کلید ⇒ مخرج ۴، نه ۸۳
    rows = []
    for i in range(83):
        rows.append({"kind": "closure", "key": f"up-{i % 4}", "moved": (i % 2 == 0)})
    ir = improvement_rate(rows)
    check("مخرج = نیتِ متمایز (۴)، نه تعدادِ رکورد (۸۳)",
          ir.value is not None and ir.value in (0.0, 25.0, 50.0, 75.0, 100.0),
          f"rate={ir.value}")

    empty = improvement_rate([])
    check("نبودِ داده ⇒ None، نه صفرِ ساختگی",
          empty.value is None and not empty.may_vote)


# ═══════════════════════════════════════════════ §۳ EFE
def t_efe() -> None:
    print("\n§۳ — EFE: کنجکاویِ بیشینه هم قید را نمی‌شکند")

    safe = Policy("propose_fix", risk=0.20, epistemic=0.30, owner_seconds=60)
    curious_but_illegal = Policy("self_merge_now", risk=0.90, epistemic=1.00,
                                 owner_seconds=0, meta={"self_merge": True})
    touches_env = Policy("read_env", risk=0.10, epistemic=1.00, meta={"touches_tcb": True})

    cons = kernel_constraints(stop_present=False, budget_frozen=False,
                              owner_verdict_available=False)

    for beta in (0.0, 0.25, BETA_EPISTEMIC_MAX, 999.0):
        cfg = EFEConfig(beta_epistemic=beta)
        r = evaluate([safe, curious_but_illegal, touches_env], cons, cfg)
        assert r["selected"] != "self_merge_now"
        assert r["selected"] != "read_env"
    check("در هر β (حتی ۹۹۹) کنشِ قیدشکن انتخاب نمی‌شود",
          True, "قید حذف می‌کند، نه جریمه")

    check("β به سقفِ سخت کلیپ می‌شود",
          EFEConfig(beta_epistemic=999.0).beta_effective == BETA_EPISTEMIC_MAX)

    # STOP ⇒ هیچ کنشی
    acting = Policy("do_something", risk=0.1, epistemic=0.1, meta={"acts": True})
    r = evaluate([acting], kernel_constraints(stop_present=True, budget_frozen=False, owner_verdict_available=True))
    check("با STOP، مجموعهٔ شدنی خالی و fail-closed", r["selected"] is None)

    # اثرِ بیرونی بدونِ رأی
    outward = Policy("send_dm", risk=0.1, epistemic=0.5, meta={"outward": True})
    r1 = evaluate([outward], kernel_constraints(stop_present=False, budget_frozen=False, owner_verdict_available=False))
    r2 = evaluate([outward], kernel_constraints(stop_present=False, budget_frozen=False, owner_verdict_available=True))
    check("اثرِ بیرونی فقط با رأیِ مالک", r1["selected"] is None and r2["selected"] == "send_dm")

    # γ فقط قاطعیت را عوض می‌کند، نه انتخاب را
    a = Policy("a", 0.2, 0.5); b = Policy("b", 0.6, 0.5)
    lo = evaluate([a, b], [], EFEConfig(gamma=0.5))
    hi = evaluate([a, b], [], EFEConfig(gamma=8.0))
    p_lo = next(x["p"] for x in lo["feasible"] if x["policy"] == "a")
    p_hi = next(x["p"] for x in hi["feasible"] if x["policy"] == "a")
    check("γ بالا = قاطع‌تر، نه بی‌پرواتر",
          lo["selected"] == hi["selected"] == "a" and p_hi > p_lo,
          f"p(a): {p_lo:.2f} → {p_hi:.2f}")

    # هزینه به ثانیهٔ مالک است، نه دلار
    cheap = Policy("auto", 0.30, 0.20, owner_seconds=0)
    dear = Policy("ask", 0.28, 0.20, owner_seconds=600)
    check("ثانیهٔ مالک واقعاً هزینه است",
          select([cheap, dear], []).name == "auto")


# ═══════════════════════════════════════════════ §۷ silence
def t_silence() -> None:
    print("\n§۷ — سکوت: ۵۰ هشدارِ هم‌امضا ⇒ ۱ پیام")
    g = SilenceGate(daily_cap=6)
    t = 1_800_000_000.0
    sent = 0
    for i in range(50):
        ok, _ = g.allow(Msg(Kind.ALERT, f"self-heal circuit-breaker: {i} restarts in 300s"), t + i)
        sent += ok
    check("۵۰ هشدار با اعداد متفاوت ⇒ ۱ پیام", sent == 1, f"sent={sent}")

    g2 = SilenceGate(daily_cap=3)
    s2 = sum(g2.allow(Msg(Kind.ALERT, "خطای " + chr(0x0627 + i) * 3), t + i * 10)[0]
             for i in range(10))
    check("سقفِ روزانه enforce می‌شود", s2 == 3, f"sent={s2}")

    gN = SilenceGate(daily_cap=10)
    n1 = gN.allow(Msg(Kind.ALERT, "3 restarts in 300s"), t)[0]
    n2 = gN.allow(Msg(Kind.ALERT, "5 restarts in 300s"), t + 5)[0]
    check("«۳ ری‌استارت» و «۵ ری‌استارت» یک امضا دارند (عمدی)", n1 and not n2)

    g3 = SilenceGate(daily_cap=1)
    g3.allow(Msg(Kind.ALERT, "aaa"), t)
    ok, why = g3.allow(Msg(Kind.VERDICT, "این RFC را تأیید می‌کنی؟"), t + 1)
    check("پیامِ رأی از سقف مستثناست", ok, why)

    d = SilenceGate().merge_digest({"lead": "۲ لید", "ziman": "", "system": "همه سبز"})
    check("۹ تاپیک ⇒ یک پیام، خالی‌ها حذف",
          d.text.count("•") == 2 and "ziman" not in d.text)

    g4 = SilenceGate(daily_cap=6)
    g4.allow(Msg(Kind.ALERT, "x"), t)
    ok, _ = g4.allow(Msg(Kind.ALERT, "x"), t + 86400 + 10)
    check("بعد از ۲۴ ساعت دوباره مجاز", ok)


# ═══════════════════════════════════════════════ §۶ leg_failure
def t_leg_failure() -> None:
    print("\n§۶ — علتِ افتادنِ لِگ")
    with tempfile.TemporaryDirectory() as td:
        rec = FailureRecorder(Path(td))
        for i in range(10):
            try:
                raise ConnectionRefusedError("port 8791 refused")
            except ConnectionRefusedError as e:
                rec.record(capture(e, "lead-naghshi", f"t{i}", beat=1000 + i))
        d = rec.diagnose("lead-naghshi")
        check("۱۰ شکستِ هم‌امضا ⇒ «علتِ واحد و تکراری»",
              d["n"] == 10 and d["distinct"] == 1 and "قابلِ تعمیر" in d["verdict"])
        check("فایلِ علت نوشته شد",
              (Path(td) / "legs" / "lead-naghshi-last-failure.json").exists())
        j = json.loads((Path(td) / "legs" / "lead-naghshi-last-failure.json").read_text("utf-8"))
        check("رکورد نوع و فریمِ استثنا را دارد",
              j["exc_type"] == "ConnectionRefusedError" and ":" in j["last_frame"],
              j["last_frame"])
        check("بدونِ داده ⇒ [UNKNOWN]، نه حدس",
              "[UNKNOWN]" in FailureRecorder(Path(td)).diagnose("x")["verdict"])


# ═══════════ فازِ ۴ — تستِ حیاتی: پچِ خراب صفر بایت روی درختِ زنده
def t_mission_runner() -> None:
    print("\nفازِ ۴ — تستِ حیاتی: پچِ عمداً خراب")
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def git(*a):
            subprocess.run(["git", *a], cwd=repo, check=True,
                           capture_output=True, env=env)

        git("init", "-q", "-b", "main")
        # بدونِ این، `git add -A` پوشهٔ __pycache__ را track می‌کند و بعد هر اجرای
        # سوئیت اثرِ انگشتِ درختِ زنده را عوض می‌کند — آژیرِ دروغ.
        (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
        (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / "suite.py").write_text(
            "import app, sys\n"
            "n = 3\n"
            "ok = app.VALUE == 1\n"
            "print(f'{n} tests')\n"
            "sys.exit(0 if ok else 1)\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-qm", "init")

        runner = MissionRunner(repo, [sys.executable, "suite.py"],
                               worktrees_dir=Path(td) / "wt", timeout_s=60)

        live_before = (repo / "app.py").read_text("utf-8")
        # روی ویندوز write_text «\n» را CRLF می‌نویسد؛ مقایسهٔ بایتی باید با
        # اسنپ‌شاتِ خودِ دیسک باشد نه live_before.encode()
        live_bytes = (repo / "app.py").read_bytes()
        fp_before = runner.live_fingerprint()

        # ---- ماموریتِ خراب ----
        def bad(wt: Path) -> None:
            (wt / "app.py").write_text("VALUE = 999\n", encoding="utf-8")

        r_bad = runner.run("bad-001", bad)
        check("پچِ خراب ⇒ کارتِ قرمز", not r_bad.ok and not r_bad.may_merge)
        check("علتش «سوئیت قرمز شد» است",
              any("سوئیت قرمز" in x for x in r_bad.reasons), str(r_bad.reasons[:1]))
        check("⛔ درختِ زنده صفر بایت تغییر کرد",
              (repo / "app.py").read_text("utf-8") == live_before
              and runner.live_fingerprint() == fp_before
              and r_bad.live_tree_untouched)
        check("worktree پاک شد", not (Path(td) / "wt" / "mission-bad-001").exists())
        # قبلاً این تست به عارضهٔ جانبیِ «اجرای پایه روی درختِ زنده» تکیه داشت.
        # حالا پایه در worktree اندازه گرفته می‌شود (تا capability markerِ زنده را
        # نزند)، پس مصنوعِ ساخت را **صریح** می‌سازیم — تستِ بهتری هم هست.
        (repo / "__pycache__").mkdir(exist_ok=True)
        (repo / "__pycache__" / "app.cpython-99.pyc").write_bytes(b"\x00junk")
        check("__pycache__ گاردِ ایمنی را الکی شلیک نمی‌کند",
              (repo / "__pycache__").exists()
              and runner.live_fingerprint() == fp_before,
              "مصنوعِ ساخت ≠ لمسِ منبع")

        # ---- ماموریتِ سالم ----
        def good(wt: Path) -> None:
            (wt / "app.py").write_text("VALUE = 1  # توضیح\n", encoding="utf-8")

        r_ok = runner.run("good-001", good)
        check("پچِ سالم ⇒ سبز و آمادهٔ رأی",
              r_ok.ok and r_ok.may_merge and r_ok.stage == "awaiting-owner",
              f"stage={r_ok.stage}")
        check("پایه اندازه‌گیری شد، نه هاردکد",
              r_ok.baseline is not None and r_ok.baseline.count == 3)
        check("دیف واقعی گرفته شد", r_ok.files_changed == 1 and "VALUE" in r_ok.diff)
        check("درختِ زنده باز هم دست‌نخورده",
              (repo / "app.py").read_text("utf-8") == live_before)
        check("سبزِ کامل هم merge نمی‌کند — رأی لازم است",
              r_ok.stage == "awaiting-owner" and (repo / "app.py").read_text("utf-8") == live_before)

        # ---- پچی که استثنا می‌دهد ----
        def boom(wt: Path) -> None:
            raise RuntimeError("پچ منفجر شد")

        r_x = runner.run("boom-001", boom, measure_baseline=False)
        check("پچِ استثنادار ⇒ قرمز + worktree پاک",
              not r_x.ok and not (Path(td) / "wt" / "mission-boom-001").exists())
        check("درختِ زنده بعد از استثنا هم سالم", r_x.live_tree_untouched)

        # ---- خصمانه: پچی که عمداً به *درختِ زنده* می‌نویسد ----
        def malicious(wt: Path) -> None:
            (repo / "app.py").write_text("VALUE = 666\n", encoding="utf-8")   # ← نه wt
            (wt / "app.py").write_text("VALUE = 1\n", encoding="utf-8")

        r_m = runner.run("evil-001", malicious, measure_baseline=False)
        check("پچی که به درختِ زنده بنویسد ⇒ گیر می‌افتد",
              not r_m.ok and not r_m.live_tree_untouched
              and any("درختِ زنده تغییر کرد" in x for x in r_m.reasons))
        (repo / "app.py").write_text(live_before, encoding="utf-8")   # ترمیمِ fixture

        # ---- خصمانه: فایلِ نوی untracked در درختِ زنده ----
        def sneaky(wt: Path) -> None:
            (repo / "backdoor.py").write_text("x=1\n", encoding="utf-8")
            (wt / "app.py").write_text("VALUE = 1  # ok\n", encoding="utf-8")

        r_s = runner.run("evil-002", sneaky, measure_baseline=False)
        check("فایلِ نوی untracked در درختِ زنده هم گیر می‌افتد",
              not r_s.ok and not r_s.live_tree_untouched)
        (repo / "backdoor.py").unlink(missing_ok=True)

        print(f"\n  نمونهٔ کارتِ قرمز:\n    " + r_bad.card().replace("\n", "\n    "))
        print(f"\n  نمونهٔ کارتِ سبز:\n    " + r_ok.card().replace("\n", "\n    "))

        # ═══ حملهٔ DGM — ایجنتی که به‌جای حلِ مسئله، دادگاه را عوض می‌کند ═══
        # حالتِ شکستِ **مشاهده‌شده** در مقالهٔ Darwin Gödel Machine (Sakana، ۲۰۲۵):
        # ایجنت لاگِ تست را جعل کرد، و در موردی دیگر گاردِ تشخیصِ توهم را حذف کرد.
        print("\nحملهٔ DGM — پچی که سوئیت را همیشه‌سبز می‌کند")
        (repo / "_ops").mkdir(exist_ok=True)
        (repo / "_ops" / "tests").mkdir(parents=True, exist_ok=True)
        real_suite = repo / "_ops" / "tests" / "run_all.py"
        real_suite.write_text(
            "import sys, pathlib\n"
            "ok = 'VALUE = 1' in pathlib.Path('app.py').read_text(encoding='utf-8')\n"
            "print('3 tests')\n"
            "sys.exit(0 if ok else 1)\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-qm", "add suite")
        runner2 = MissionRunner(repo, [sys.executable, "_ops/tests/run_all.py"],
                                worktrees_dir=Path(td) / "wt2", timeout_s=60)

        def cheat(wt: Path) -> None:
            """کدِ خراب + سوئیتی که همیشه سبز است. کلاسیکِ objective hacking."""
            (wt / "app.py").write_text("VALUE = 999\n", encoding="utf-8")
            (wt / "_ops" / "tests" / "run_all.py").write_text(
                "print('9999 tests')\nraise SystemExit(0)\n", encoding="utf-8")

        r_cheat = runner2.run("dgm-attack", cheat)
        check("⛔ پچی که سوئیت را همیشه‌سبز می‌کند **گیر می‌افتد**",
              not r_cheat.ok and not r_cheat.may_merge,
              str(r_cheat.reasons[:1]))
        check("دست‌زدن به شاهد صریحاً گزارش می‌شود، بی‌صدا نمی‌گذرد",
              r_cheat.suite_touched and "run_all" in r_cheat.suite_touched[0])
        check("کارت هم به مالک می‌گوید پچ به سوئیت دست زده",
              "به سوئیت دست زد" in r_cheat.card())
        check("⛔ درختِ زنده باز هم صفر بایت", r_cheat.live_tree_untouched)

        # و همان پچ، بدونِ دست‌زدن به سوئیت، درست رد می‌شود
        def honest_bad(wt: Path) -> None:
            (wt / "app.py").write_text("VALUE = 999\n", encoding="utf-8")

        r_hb = runner2.run("honest-bad", honest_bad)
        check("پچِ خرابِ صادق هم رد می‌شود — ولی به دلیلِ درست (سوئیت قرمز)",
              not r_hb.ok and not r_hb.suite_touched
              and any("سوئیت قرمز" in x for x in r_hb.reasons))

        # ═══ فازِ ۵ — merge: تنها لحظه‌ای که درختِ زنده لمس می‌شود ═══
        print("\nفازِ ۵ — merge (بعد از رأی)")
        os.environ.setdefault("GIT_AUTHOR_NAME", "t")
        for k, v in env.items():
            os.environ[k] = v

        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True, env=env)
        subprocess.run(["git", "commit", "-qm", "post-dgm"], cwd=repo,
                       capture_output=True, env=env)
        fp_now = runner.live_fingerprint()
        try:
            runner.merge("x", good, files=["app.py"], fp_expected="عوض-شده")
            r = "انجام شد!"
        except RuntimeError as e:
            r = str(e)
        check("⛔ اگر درخت زیرِ پایمان تکان خورده باشد merge لغو می‌شود",
              "تغییر کرده" in r and (repo / "app.py").read_text("utf-8") == live_before)

        try:
            runner.merge("y", good, files=[], fp_expected=fp_now); r = "انجام شد!"
        except RuntimeError as e:
            r = str(e)
        check("merge بدونِ فهرستِ صریحِ فایل‌ها انجام نمی‌شود", "فهرستِ صریح" in r)

        (repo / "app.py").write_text("VALUE = 1  # کارِ نیمه‌کارهٔ یکی دیگر\n", encoding="utf-8")
        try:
            runner.merge("dirty", good, files=["app.py"]); r = "انجام شد!"
        except RuntimeError as e:
            r = str(e)
        check("⛔ merge روی درختِ کثیف ممنوع — کارِ ثبت‌نشدهٔ کسِ دیگر پاک نمی‌شود",
              "تمیز نیست" in r)
        subprocess.run(["git", "checkout", "--", "app.py"], cwd=repo,
                       capture_output=True, env=env)

        def bad_live(root: Path) -> None:
            (root / "app.py").write_text("VALUE = 999\n", encoding="utf-8")

        try:
            runner.merge("z", bad_live, files=["app.py"], fp_expected=fp_now)
            r = "انجام شد!"
        except RuntimeError as e:
            r = str(e)
        check("⛔ سوئیتِ قرمز ⇒ فایل بایت‌به‌بایت برمی‌گردد و کامیتی نمی‌شود",
              "قرمز شد" in r and (repo / "app.py").read_bytes() == live_bytes)

        def stray(root: Path) -> None:
            (root / "app.py").write_text("VALUE = 1  # merged\n", encoding="utf-8")
            (root / "suite.py").write_text(
                (root / "suite.py").read_text("utf-8") + "# اعلام‌نشده\n", encoding="utf-8")

        suite_before = (repo / "suite.py").read_bytes()
        try:
            runner.merge("w", stray, files=["app.py"], fp_expected=fp_now); r = "انجام شد!"
        except RuntimeError as e:
            r = str(e)
        check("⛔ دست‌زدن به فایلی خارج از آنچه مالک دیده ⇒ merge لغو و بازگردانی",
              "اعلام‌نشده" in r and (repo / "suite.py").read_bytes() == suite_before
              and (repo / "app.py").read_bytes() == live_bytes)

        head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                                     capture_output=True, text=True).stdout.strip()

        def good_live(root: Path) -> None:
            (root / "app.py").write_text("VALUE = 1  # تأییدشده\n", encoding="utf-8")

        res = runner.merge("m-ok", good_live, files=["app.py"], fp_expected=fp_now)
        head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                                    capture_output=True, text=True).stdout.strip()
        check("✅ merge سالم: فایل عوض شد، سوئیت سبز، کامیت خورد",
              res["ok"] and "تأییدشده" in (repo / "app.py").read_text("utf-8")
              and head_after != head_before, f"commit={res['commit']}")
        check("درختِ کاری بعد از merge تمیز است",
              subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                             cwd=repo, capture_output=True, text=True).stdout.strip() == "")


# ═══════════ فازِ ۴ — F-08: worktree باید کدِ زندهٔ کاری را ببیند نه فقط HEAD
def t_replicate_live_source() -> None:
    print("\nفازِ ۴ — F-08: تستِ untracked ِ زنده باید در worktree هم اجرا شود")
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        (repo / "_ops" / "tests").mkdir(parents=True)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def git(*a):
            subprocess.run(["git", *a], cwd=repo, check=True,
                           capture_output=True, env=env)

        git("init", "-q", "-b", "main")
        (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n_ops/state/\n",
                                         encoding="utf-8")
        # سوئیتِ کامیت‌شده: هر دو فایلِ تست را می‌دود؛ عددِ تست = تعدادِ فایل‌های سبز
        (repo / "_ops" / "tests" / "run_all.py").write_text(
            "import subprocess, sys\n"
            "from pathlib import Path\n"
            "here = Path(__file__).resolve().parent\n"
            "tests = sorted(here.glob('test_*.py'))\n"
            "ok = 0\n"
            "for t in tests:\n"
            "    r = subprocess.run([sys.executable, str(t)], capture_output=True)\n"
            "    ok += (r.returncode == 0)\n"
            "print(f'{ok} tests')\n"
            "sys.exit(0 if ok == len(tests) else 1)\n", encoding="utf-8")
        (repo / "_ops" / "tests" / "test_committed.py").write_text(
            "import sys; sys.exit(0)\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-qm", "init")

        # ← این تستِ زنده روی دیسک هست ولی هرگز کامیت نشده (دقیقاً حالتِ F-08)
        (repo / "_ops" / "tests" / "test_untracked.py").write_text(
            "import sys; sys.exit(0)\n", encoding="utf-8")

        suite = [sys.executable, "-X", "utf8", "_ops/tests/run_all.py"]
        runner = MissionRunner(repo, suite, worktrees_dir=Path(td) / "wt",
                               timeout_s=60, env_root_key="ORG_ROOT")

        # بدونِ replicate، سوئیتِ worktree فقط ۱ فایل می‌بیند (test_untracked غایب)
        base_wt = Path(td) / "wt-bare"
        git("worktree", "add", "--detach", str(base_wt), "HEAD")
        bare = runner.run_suite(base_wt)
        check("بدونِ replicate: worktree فقط تستِ کامیت‌شده را دارد",
              bare.green and bare.count == 1, f"count={bare.count}")
        subprocess.run(["git", "worktree", "remove", "--force", str(base_wt)],
                       cwd=repo, capture_output=True, env=env)

        # با replicate: هر دو تست باید دیده شوند
        rep_wt = Path(td) / "wt-rep"
        git("worktree", "add", "--detach", str(rep_wt), "HEAD")
        n = runner._replicate_live_source(rep_wt, commit=False)
        rep = runner.run_suite(rep_wt)
        check("با replicate: تستِ untracked ِ زنده هم در worktree اجرا شد",
              rep.green and rep.count == 2 and n >= 1,
              f"copied={n} count={rep.count}")
        subprocess.run(["git", "worktree", "remove", "--force", str(rep_wt)],
                       cwd=repo, capture_output=True, env=env)

        # ماموریتِ create: فایلِ نو باید دیده شود (files_changed>0) و سوئیت سبز بماند
        def add_tool(wt: Path) -> None:
            (wt / "_ops" / "tools").mkdir(parents=True, exist_ok=True)
            (wt / "_ops" / "tools" / "pulse.py").write_text(
                "print('ok')\n", encoding="utf-8")

        r = runner.run("rep-create", add_tool)
        check("ماموریتِ create روی درختِ ناقص: پایه و کاندید هر دو ۲ تست، سبز",
              r.ok and r.stage == "awaiting-owner"
              and (r.baseline.count or 0) == 2 and (r.candidate.count or 0) == 2,
              f"stage={r.stage} base={r.baseline and r.baseline.count} "
              f"cand={r.candidate and r.candidate.count}")
        check("فایلِ نو در دیف دیده شد (create-aware)", r.files_changed >= 1,
              f"files_changed={r.files_changed}")


# ═══════════ فازِ ۴ — pinِ ریشهٔ سوئیت (env_root_key، الگوی code_autonomy)
def t_env_root_pin() -> None:
    print("\nفازِ ۴ — pinِ ریشه: سوئیت باید درختِ زیرِ آزمون را ببیند، نه درختِ زنده")
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def git(*a):
            subprocess.run(["git", *a], cwd=repo, check=True,
                           capture_output=True, env=env)

        git("init", "-q", "-b", "main")
        (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        # سوئیتی که ریشه‌اش را از env می‌گیرد (مثلِ opslib.ORG_ROOT): فقط وقتی سبز است
        # که X_ROOT دقیقاً به همان درختی اشاره کند که سوئیت در آن اجرا می‌شود.
        (repo / "suite.py").write_text(
            "import os, sys\n"
            "from pathlib import Path\n"
            "root = os.environ.get('X_ROOT', '')\n"
            "here = str(Path.cwd().resolve())\n"
            "print('1 tests')\n"
            "sys.exit(0 if root == here else 1)\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-qm", "init")

        pinned = MissionRunner(repo, [sys.executable, "suite.py"],
                               worktrees_dir=Path(td) / "wt", timeout_s=60,
                               env_root_key="X_ROOT")
        check("پایه با pin سبز است (X_ROOT=repo)", pinned.run_suite(repo).green)

        unpinned = MissionRunner(repo, [sys.executable, "suite.py"],
                                 worktrees_dir=Path(td) / "wt2", timeout_s=60)
        os.environ.pop("X_ROOT", None)
        check("بدونِ pin همان سوئیت قرمز است — یعنی pin واقعاً اثر دارد",
              not unpinned.run_suite(repo).green)

        def patch(wt: Path) -> None:
            (wt / "app.py").write_text("VALUE = 2\n", encoding="utf-8")

        r = pinned.run("pin-001", patch)
        check("ماموریتِ کامل با pin: سوئیتِ worktree ریشهٔ worktree را دید",
              r.ok and r.stage == "awaiting-owner",
              f"stage={r.stage} reasons={r.reasons[:1]}")


# ═══════════ §۱۰ — ارزش بر وات، بدونِ خطای واحد (از ممیزیِ بیرونی)
def t_value_metric() -> None:
    print("\n§۱۰ — ارزش بر دلار / ارزش بر وات‌ساعت")
    from value_metric import (Quantity, UnitError, value_per_usd, value_per_wh,
                              efficiency_report, USD, WH, OUTCOME)

    try:
        Quantity(3.0, USD) + Quantity(1.0, WH)
        r = "جمع کرد!"
    except UnitError as e:
        r = str(e)
    check("⛔ جمعِ دلار با وات‌ساعت **ساختاراً** ناممکن است",
          "بی‌معناست" in r, "این همان باگی بود که ممیزی گرفت")
    check("جمعِ هم‌واحد درست کار می‌کند",
          (Quantity(3.0, USD) + Quantity(2.0, USD)).value == 5.0)

    a = value_per_usd(4, 2.0)
    b = value_per_wh(4, 800.0)
    check("دو سنجه ساخته می‌شوند و **واحدشان چسبیده به عدد است**",
          a.unit == "outcome/usd" and b.unit == "outcome/wh" and a.value == 2.0)
    try:
        a + b
        r = "جمع کرد!"
    except UnitError as e:
        r = str(e)
    check("⛔ دو نسبت هم با هم جمع نمی‌شوند", "جمع نمی‌شوند" in r)

    rep = efficiency_report(4, 2.0, None)
    check("مصرفِ برقِ اندازه‌نگرفته ⇒ [UNKNOWN]، نه صفرِ ساختگی",
          rep["value_per_wh"] is None and any("نامعلوم" in u for u in rep["unknown"]))
    check("بدونِ خرجِ دلار، نسبت None است نه بی‌نهایت",
          value_per_usd(4, 0.0) is None)
    check("گزارش صریحاً می‌گوید این دو یکی نمی‌شوند", "جمع نمی‌شوند" in rep["note"])


# ═══════════ §۱۱ — نمونه‌گیرِ سیاست: قید حذف می‌کند، جریمه نمی‌کند
def t_policy_sampler() -> None:
    print("\n§۱۱ — نمونه‌گیرِ سیاست با قیدِ اثبات‌پذیر")
    from policy_sampler import (Policy, CpuSoftmaxSampler, PolicySampler,
                                ConstraintViolation)
    import random as _r

    s = CpuSoftmaxSampler()
    pol = [Policy("خواندن", 1.0), Policy("پیشنهاد", 1.2),
           Policy("merge-بدونِ-رأی", -99.0, allowed=False, reason="قیدِ هسته")]

    res = s.distribution(pol, gamma=4.0)
    check("⛔ سیاستِ ممنوع احتمالِ **دقیقاً صفر** دارد، نه کم",
          res.p("merge-بدونِ-رأی") == 0.0 and "merge-بدونِ-رأی" not in res.names)
    check("دلیلِ حذف ثبت می‌شود، بی‌صدا نمی‌افتد",
          any("قیدِ هسته" in x for x in res.removed))
    check("جمعِ احتمال‌ها ۱ است", abs(sum(res.probs) - 1.0) < 1e-9)

    # بدترین حالت برای «جریمه به‌جای حذف»: γ=0 ⇒ توزیعِ یکنواخت.
    res0 = s.distribution(pol, gamma=0.0)
    check("حتی با γ=0 (یکنواخت) سیاستِ ممنوع صفر می‌ماند",
          res0.p("merge-بدونِ-رأی") == 0.0
          and abs(res0.p("خواندن") - 0.5) < 1e-9)

    rng = _r.Random(7)
    bad = 0
    try:
        for _ in range(50_000):
            if s.sample(pol, gamma=0.0, rng=rng) == "merge-بدونِ-رأی":
                bad += 1
    except ConstraintViolation:
        bad = -1
    check("۵۰٬۰۰۰ نمونه‌گیری، **صفر** بار سیاستِ ممنوع", bad == 0, f"bad={bad}")

    # مقایسهٔ صریح با روشِ «جریمه» — چیزی که این ماژول رد می‌کند
    pen = [Policy("خواندن", 1.0), Policy("merge-بدونِ-رأی", -99.0 + 1e9)]
    rp = s.distribution(pen, gamma=1e-12)
    check("نشان می‌دهیم چرا «جریمه» ناکافی است: با γ≈0 جریمه بی‌اثر می‌شود",
          rp.p("merge-بدونِ-رأی") > 0.4,
          f"p={rp.p('merge-بدونِ-رأی'):.3f} — به همین دلیل حذف می‌کنیم، نه جریمه")

    check("γ بزرگ سرریز نمی‌کند و به argmin می‌رسد",
          abs(s.distribution(pol, gamma=1e6).p("خواندن") - 1.0) < 1e-9)
    check("همهٔ سیاست‌ها ممنوع ⇒ مجموعهٔ خالی و fail-closed",
          s.distribution([Policy("x", 1.0, allowed=False)], 4.0).names == []
          and s.sample([Policy("x", 1.0, allowed=False)]) is None)
    check("رابط باز است — backend قابلِ تعویض بدونِ لمسِ هسته",
          issubclass(CpuSoftmaxSampler, PolicySampler)
          and CpuSoftmaxSampler.backend == "cpu-softmax")


# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 66)
    print("OCTOPUS OS v1 — سوئیتِ تست")
    print("=" * 66)
    for fn in (t_honest_metric, t_outcome_ledger, t_efe,
               t_silence, t_leg_failure, t_mission_runner,
               t_replicate_live_source, t_env_root_pin,
               t_value_metric, t_policy_sampler):
        fn()
    print("\n" + "=" * 66)
    print(f"نتیجه: {len(PASS)} سبز · {len(FAIL)} قرمز")
    if FAIL:
        for f in FAIL:
            print(f"  ❌ {f}")
    print("=" * 66)
    sys.exit(1 if FAIL else 0)
