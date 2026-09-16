#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""cli.py — رابطِ دکترِ اختاپوس.

    python doctor/cli.py triage                  # آفلاین، بدونِ مغز — همیشه کار می‌کند
    python doctor/cli.py scan    F:\backup\_ops  # چشم: خواندنِ ارگانیسمِ زنده (فقط‌خواندنی)
    python doctor/cli.py round   F:\backup\_ops  # چشم ⟶ والت: حلقهٔ کامل در یک دستور
    python doctor/cli.py ask     "چرا قلب ترمز خورده؟"
    python doctor/cli.py diagnose                # تشخیصِ کامل با fugu-ultra (max)
    python doctor/cli.py propose "علتِ افتادنِ لِگ را ثبت کن"   # پچِ گیت‌خورده — اعمال نمی‌کند
    python doctor/cli.py day     F:\backup\_ops  # یک پاسِ کاملِ حلقه (dry-run)
    python doctor/cli.py day     F:\backup\_ops --live --apply   # با دست و با merge
    python doctor/cli.py request "یک پا اضافه کن که رزونانسِ شومان را رصد کند"
    python doctor/cli.py mind                    # گزارشِ ناخودآگاه: کهن‌الگوها و سایه
    python doctor/cli.py outbox                  # سلامتِ کانال — بدونِ هیچ رازی
    echo [...] | python doctor/cli.py votes      # رأی‌هایی که پروسهٔ زنده جمع کرده
    python doctor/cli.py ingest  scan.json
    python doctor/cli.py stats

سه چیزی که این CLI **هرگز** نمی‌کند: چیزی در `_ops` نمی‌نویسد · پچی اعمال نمی‌کند ·
بدونِ رأیِ صریحِ مالک merge نمی‌کند.
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent

from diagnose import Doctor                    # noqa: E402
from ingest import ingest_file, ingest_scan     # noqa: E402
from vault import Vault                        # noqa: E402
from scanner import scan                       # noqa: E402

DEFAULT_OPS = r"F:\backup\_ops"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd, rest = sys.argv[1], sys.argv[2:]
    doc = Doctor(ROOT)

    if cmd == "triage":
        print(json.dumps(doc.triage(), ensure_ascii=False, indent=2))
    elif cmd == "stats":
        print(json.dumps(Vault(ROOT).stats(), ensure_ascii=False, indent=2))
    elif cmd == "ask":
        if not rest:
            print("پرسش لازم است"); return 2
        d = doc.ask(" ".join(rest))
        print(d.as_markdown())
        if d.reasons: print("\n[دلایل] " + " · ".join(d.reasons), file=sys.stderr)
        return 0 if d.ok else 1
    elif cmd == "diagnose":
        d = doc.full()
        out = ROOT / "70-نسخه‌ها" / "تشخیصِ-اخیر.md"
        if d.ok:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(d.as_markdown(), encoding="utf-8")
            print(f"نوشته شد: {out}")
        print(d.as_markdown())
        return 0 if d.ok else 1
    elif cmd == "day":
        # یک پاسِ کاملِ حلقه. پیش‌فرض dry-run: هیچ merge‌ای رخ نمی‌دهد.
        from daemon import Daemon                    # noqa: PLC0415
        from channel import TelegramChannel          # noqa: PLC0415
        ops = next((a for a in rest if not a.startswith("--")), DEFAULT_OPS)
        st = ROOT / "90-_meta" / "state"
        ch = TelegramChannel(st)
        runner = None
        if "--live" in rest:
            try:
                sys.path.insert(0, str(Path(ops) / "os_v1"))
                from mission_runner import MissionRunner          # noqa: PLC0415
                # مسیرِ سوئیت **نسبی** است تا در worktree همان نسخهٔ پچ‌شده اجرا شود؛
                # مسیرِ مطلق همیشه سوئیتِ درختِ زنده را می‌سنجید و گیت بی‌معنا می‌شد.
                # env_root_key سوئیت را به همان درختِ زیرِ آزمون pin می‌کند (الگوی
                # code_autonomy) — بدونِ آن، تست‌های ORG_ROOT-خوان درختِ زنده را لمس می‌کنند.
                ops_p = Path(ops).resolve()
                rel_suite = Path(ops_p.name) / "tests" / "run_all.py"
                runner = MissionRunner(
                    ops_p.parent,
                    [sys.executable, "-X", "utf8", str(rel_suite)],
                    worktrees_dir=ops_p.parent / "_worktrees", timeout_s=900,
                    env_root_key="ORG_ROOT")
            except Exception as e:                   # noqa: BLE001
                print(f"⚠️ MissionRunner بارگذاری نشد: {type(e).__name__} — بدونِ دست ادامه")
        d = Daemon(ops, ROOT, channel=ch, runner=runner,
                   dry_run=("--apply" not in rest))
        out = d.cycle()
        print("\n".join("· " + l for l in out["log"]))
        print(json.dumps({"beat": out["beat"], "یافته": out["findings"],
                          "ماموریت‌ها": [(m["mission_id"], m["state"]) for m in out["missions"]],
                          "کانال": out["vitals"]["channel"],
                          "UNKNOWN": out["unknown"]}, ensure_ascii=False, indent=2))
    elif cmd == "request":
        # ← این همان «در تلگرام می‌نویسم، اختاپوس می‌سازد» است
        from daemon import Daemon                    # noqa: PLC0415
        if not rest:
            print("چه می‌خواهی؟ مثال: request \"یک پا اضافه کن که X را رصد کند\""); return 2
        ops = os.environ.get("OCTOPUS_OPS", DEFAULT_OPS)
        r = Daemon(ops, ROOT, dry_run=True).request(" ".join(rest))
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    elif cmd == "mind":
        from mind import Mind                        # noqa: PLC0415
        m = Mind(ROOT / "90-_meta" / "state")
        print(json.dumps(m.reflect(), ensure_ascii=False, indent=2))
    elif cmd == "votes":
        # رأی‌هایی که پروسهٔ زنده جمع کرده، از stdin به‌صورت JSON list وارد می‌شوند
        from channel import TelegramChannel          # noqa: PLC0415
        ch = TelegramChannel(ROOT / "90-_meta" / "state")
        raw = json.loads(sys.stdin.read() or "[]")
        got = ch.ingest_external(raw if isinstance(raw, list) else [raw])
        print(json.dumps([v.__dict__ for v in got], ensure_ascii=False, indent=2))
    elif cmd == "outbox":
        from channel import TelegramChannel          # noqa: PLC0415
        ch = TelegramChannel(ROOT / "90-_meta" / "state")
        print(json.dumps(ch.health(), ensure_ascii=False, indent=2))
    elif cmd == "propose":
        if not rest:
            print("هدف لازم است — مثال: propose \"علتِ افتادنِ لِگ را ثبت کن\""); return 2
        ps, why, used = doc.propose(" ".join(rest))
        if ps is None:
            print("⛔ پیشنهادی ساخته نشد:\n· " + "\n· ".join(why)); return 1
        out = ROOT / "70-نسخه‌ها" / f"پیشنهاد-{ps.mission_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "mission_id": ps.mission_id, "title": ps.title, "risk": ps.risk,
            "rationale": ps.rationale, "rollback": ps.rollback,
            "patches": [p.__dict__ for p in ps.patches], "evidence": used,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(ps.card())
        print(f"\n— ذخیره شد: {out}")
        print("— هیچ چیزی اعمال نشد. اجرا کارِ MissionRunner است و merge کارِ رأیِ توست.")
    elif cmd == "scan":
        s = scan(rest[0] if rest else DEFAULT_OPS,
                 run_suite=("--suite" in rest))
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0 if s.get("metrics") else 1
    elif cmd == "round":
        # حلقهٔ کامل در یک دستور: ارگانیسم ⟶ اسکن ⟶ والت
        s = scan(rest[0] if rest else DEFAULT_OPS, run_suite=("--suite" in rest))
        if not s.get("metrics"):
            print("⛔ چشم چیزی ندید — ارگانیسم خاموش است؟")
            print(json.dumps(s.get("unknown", []), ensure_ascii=False, indent=2))
            return 1
        res = ingest_scan(Vault(ROOT), s)
        print(json.dumps({"beat": s.get("beat"),
                          "یافته‌های_خودکار": len(s.get("findings", [])),
                          "نوشته_شد": res["written"],
                          "flagشده": res["flagged_metrics"],
                          "UNKNOWN": s.get("unknown", [])},
                         ensure_ascii=False, indent=2))
    elif cmd == "ingest":
        if not rest:
            print("مسیرِ فایل لازم است"); return 2
        print(json.dumps(ingest_file(Vault(ROOT), rest[0]), ensure_ascii=False, indent=2))
    else:
        print(__doc__); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
