#!/usr/bin/env python3
"""
check_state_isolation.py — «آیا سوییت داخلِ ظرفِ زندهٔ ارگانیسم می‌نویسد؟»

سنجهٔ برشِ ۰. هر تست را در یک پروسهٔ جدا با `live_state_guard` ِ **مسلح** می‌دواند و
گزارش می‌دهد کدام فایلِ تست کدام مسیرِ زنده را خواست عوض کند. گارد در حالتِ `block`
است، پس نوشتن **جلویش گرفته می‌شود** و هم‌زمان ثبت هم می‌شود — بررسی خودش خسارت
نمی‌زند.

چرا خودِ `run_all.py` را صدا نمی‌زند: آن runner داخلِ درختِ زنده می‌نویسد و روی هر
شکست `revoke_capability()` مارکرِ ارگانیسم را می‌کُشد. اینجا تست‌ها تک‌به‌تک و
مستقیم اجرا می‌شوند (همان قراردادِ `run_all`: `python -X utf8 <file>` با
`cwd=<پوشهٔ تست>`).

سه سنجه گزارش می‌شود و **قاتی نمی‌شوند**:
  ۱. `armed`   — گارد واقعاً بالا آمد؟ (رسیدِ سمتِ خواننده؛ نبودش = اجرای نامعتبر،
                 نه «تمیز». غیابِ خطا سبز نیست.)
  ۲. `violations` — تلاش‌های نوشتنِ **علّی** این تست. سنجهٔ اصلی.
  ۳. `ambient` — تفاوتِ اثرانگشتِ پوشهٔ زنده. ارگانیسم **در حال اجراست** و مدام
                 می‌نویسد، پس این عدد ذاتاً نویز دارد و هرگز به تست نسبت داده
                 نمی‌شود؛ فقط برای گرفتنِ بردارهایی است که گارد نمی‌بیند.

مصرف:
    python check_state_isolation.py --group lead
    python check_state_isolation.py test_lead_pipeline.py test_cockpit_v2.py
    python check_state_isolation.py --no-harness      # ۹۳ تستِ بی‌هارنس
    python check_state_isolation.py --fingerprint     # فقط عکسِ لحظه‌ایِ ظرفِ زنده
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BOOT_DIR = TESTS_DIR / "_isolation_boot"
REAL_VAULT = Path(os.environ.get("REAL_VAULT", r"F:\backup"))
LIVE_STATE = REAL_VAULT / "_ops" / "state"

# `state/models/` کشِ وزنِ whisper است (~۴GB، ۱۰ فایل) — دادهٔ عملیاتی نیست و
# اثرانگشت‌گرفتنش فقط وقت می‌برد.
FINGERPRINT_SKIP = {"models"}

# ⚠️ خلع‌سلاحِ محیطِ فرزند. اجرای تستِ لید می‌تواند ایمیلِ **واقعی** بفرستد — همان
# اقدامِ برگشت‌ناپذیری که هنوز رأیِ مالک رویش باز است. بررسیِ ایزوله‌بودن هرگز حق
# ندارد اثرِ بیرونی بسازد، پس این فلگ‌ها صریحاً صفر می‌شوند و اعتبارنامه‌ها حذف.
DISARM_ZERO = (
    "OCTOPUS_WIRE_LEAD_OUTBOUND", "OCTOPUS_SMTP_USE_GMAIL",
    "OCTOPUS_WIRE_LEAD_VERDICT_EFFECT", "OCTOPUS_WIRE_LEAD_PIPELINE",
    "OCTOPUS_WIRE_MISSION_RUNNER", "OCTOPUS_TG_MINIAPP",
)
DISARM_DROP = (
    "SMTP_PASSWORD", "SMTP_USER", "SMTP_HOST", "GMAIL_APP_PASSWORD",
    "TELEGRAM_BOT_TOKEN", "TG_CENTER_BOT_TOKEN", "OCTOPUS_MINIAPP_URL",
)

# پیش‌فرض: خروجیِ غیرِ loopback در فرزند مسدود است. سنجشِ ایزوله‌بودن نباید خودش
# تماسِ پولیِ vendor یا ارسالِ واقعی تولید کند. با `--allow-network` برداشته می‌شود.
NET_GUARD = True

GROUPS = {
    "lead":     ("lead", "outbound", "funnel"),
    "miniapp":  ("miniapp", "gateway", "pf_"),
    "approval": ("approval", "rfc", "card", "cockpit", "callback"),
}


# ── اثرانگشت ──────────────────────────────────────────────────────────────────
def fingerprint(root: Path = LIVE_STATE) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in FINGERPRINT_SKIP]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                st = p.stat()
                if st.st_size > 8 * 1024 * 1024:
                    out[str(p.relative_to(root))] = f"big:{st.st_size}:{st.st_mtime_ns}"
                else:
                    h = hashlib.sha1(p.read_bytes()).hexdigest()[:16]
                    out[str(p.relative_to(root))] = f"{st.st_size}:{h}"
            except OSError:
                out[str(p.relative_to(root))] = "unreadable"
    return out


def diff_fp(a: dict, b: dict) -> list[str]:
    keys = set(a) | set(b)
    return sorted(k for k in keys if a.get(k) != b.get(k))


# ── اجرای یک تست ──────────────────────────────────────────────────────────────
def run_one(test: Path, workdir: Path, timeout: int = 300) -> dict:
    echo = workdir / f"echo-{test.stem}.txt"
    log = workdir / f"viol-{test.stem}.jsonl"
    for f in (echo, log):
        if f.exists():
            f.unlink()

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BOOT_DIR)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["OCTOPUS_TEST_LIVE_STATE_GUARD"] = "block"
    if NET_GUARD:
        env["OCTOPUS_TEST_NET_GUARD"] = "loopback-only"
    env["OCTOPUS_TEST_ISOLATION_ECHO"] = str(echo)
    env["OCTOPUS_TEST_ISOLATION_LOG"] = str(log)
    for k in DISARM_ZERO:
        env[k] = "0"
    for k in DISARM_DROP:
        env.pop(k, None)

    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(test)],
                           cwd=str(test.parent), timeout=timeout, env=env,
                           capture_output=True, text=True, errors="replace")
        rc, out, err = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = -9, "", f"TIMEOUT>{timeout}s"

    viol = []
    if log.exists():
        for line in log.read_text("utf-8", errors="replace").splitlines():
            try:
                viol.append(json.loads(line))
            except ValueError:
                pass

    return {
        "test": test.name,
        "rc": rc,
        "secs": round(time.time() - t0, 1),
        "armed": echo.exists(),
        "guard_error": "LIVE-STATE-GUARD" in err,
        "violations": viol,
        "stderr_tail": err.strip().splitlines()[-3:] if err.strip() else [],
    }


def select(args) -> list[Path]:
    if args.files:
        return [TESTS_DIR / f if not Path(f).is_absolute() else Path(f) for f in args.files]
    if args.all_repo:
        # کلِ ریپو، شاملِ پوشه‌های تستِ تودرتو (`agi2027_control/tests`, `owner_console/tests`, …).
        # نویسندهٔ L-WAL-1 دقیقاً یکی از همین‌ها بود و در `_ops/tests` نبود.
        # فهرست‌سازی **داخلِ** runner انجام می‌شود: پاس‌دادنِ ۵۵۸ مسیر از پوسته
        # «Argument list too long» می‌دهد و اجرا بی‌صدا انجام نمی‌شود.
        ops = TESTS_DIR.parent
        out = []
        for p in sorted(ops.rglob("test_*.py")):
            parts = set(p.parts)
            if "patch_backups" in parts or "__pycache__" in parts or "_Archive" in parts:
                continue
            out.append(p)
        return out
    allt = sorted(TESTS_DIR.glob("test_*.py"))
    if args.no_harness:
        keep = []
        for p in allt:
            txt = p.read_text("utf-8", errors="replace")
            if "import harness" not in txt and "from harness" not in txt:
                keep.append(p)
        return keep
    if args.group:
        pats = GROUPS[args.group]
        return [p for p in allt if any(s in p.name for s in pats)]
    return allt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--group", choices=sorted(GROUPS))
    ap.add_argument("--no-harness", action="store_true")
    ap.add_argument("--all-repo", action="store_true",
                    help="کلِ _ops شاملِ پوشه‌های تستِ تودرتو")
    ap.add_argument("--fingerprint", action="store_true")
    ap.add_argument("--ambient", action="store_true",
                    help="اثرانگشتِ قبل/بعد هم بگیر (کند، و ذاتاً نویزِ ارگانیسمِ زنده دارد)")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--allow-network", action="store_true",
                    help="گاردِ شبکه را بردار (تست می‌تواند تماسِ بیرونی/پولی بزند)")
    args = ap.parse_args()

    global NET_GUARD
    NET_GUARD = not args.allow_network

    print(f"ریشهٔ محافظت‌شده: {LIVE_STATE}")
    print(f"گاردِ شبکه: {'فقط loopback' if NET_GUARD else 'برداشته شده'}")
    if args.fingerprint:
        fp = fingerprint()
        print(f"فایل‌های اثرانگشت‌شده: {len(fp)}")
        return 0

    tests = select(args)
    if args.limit:
        tests = tests[: args.limit]
    if not tests:
        print("هیچ تستی انتخاب نشد.")
        return 2
    print(f"تست‌های انتخابی: {len(tests)}\n")

    workdir = Path(tempfile.mkdtemp(prefix="isolation-check-"))
    results, leakers, unarmed, pointers, networked = [], [], [], [], []
    fp_before = fingerprint() if args.ambient else None

    for i, t in enumerate(tests, 1):
        if not t.exists():
            print(f"[{i}/{len(tests)}] ⚠️  {t.name} — یافت نشد")
            continue
        res = run_one(t, workdir, args.timeout)
        results.append(res)
        # دو ردهٔ متفاوت که هرگز جمع زده نمی‌شوند:
        #   bad = جهشِ واقعی (بایت عوض می‌شد) → مسدود شد
        #   ptr = نشتیِ اشاره‌ای (مسیرِ زنده resolve شد، ولی صفر بایت) → فقط ثبت
        vio = [v for v in res["violations"] if not str(v.get("op", "")).startswith("net:")]
        net = [v for v in res["violations"] if str(v.get("op", "")).startswith("net:")]
        bad = [v for v in vio if not v.get("allowed") and not v.get("benign")]
        ptr = [v for v in vio if not v.get("allowed") and v.get("benign")]
        res["bad"], res["ptr"], res["net"] = bad, ptr, net
        if net:
            networked.append(res)
        if not res["armed"]:
            unarmed.append(res["test"])
            flag = "🚫 گارد مسلح نشد"
        elif bad:
            leakers.append(res)
            flag = f"❌ {len(bad)} جهشِ زندهٔ مسدودشده"
        elif ptr:
            pointers.append(res)
            flag = f"⚠️  {len(ptr)} نشتیِ اشاره‌ای (صفر بایت)"
        else:
            flag = "✅ ایزوله"
        print(f"[{i}/{len(tests)}] {flag}  {res['test']}  (rc={res['rc']}, {res['secs']}s)")
        for v in (bad or ptr)[:4]:
            print(f"        {v['op']:<16} {v['path']}  {v.get('detail','')}")

    print("\n" + "=" * 72)
    print(f"اجرا: {len(results)}   جهشِ زنده: {len(leakers)}   "
          f"نشتیِ اشاره‌ای: {len(pointers)}   خروجیِ بیرونی: {len(networked)}   "
          f"مسلح‌نشده: {len(unarmed)}")
    if networked:
        print("\nتست‌هایی که خواستند به بیرون وصل شوند (مسدود شد — بدونِ گارد پول/اثرِ واقعی):")
        for r in networked:
            addrs = sorted({v["path"] for v in r["net"]})[:3]
            print(f"  {r['test']}  →  {', '.join(addrs)}")
    if args.ambient and fp_before is not None:
        changed = diff_fp(fp_before, fingerprint())
        print(f"تغییرِ محیطی زیرِ state زنده: {len(changed)} فایل "
              f"(شاملِ نوشتنِ خودِ ارگانیسمِ در حالِ اجرا — به تست نسبت داده نمی‌شود)")
        for c in changed[:15]:
            print(f"        ~ {c}")
    for title, group, key in (("ظرف‌های زنده‌ای که تست‌ها می‌خواستند عوض کنند", leakers, "bad"),
                              ("نشتیِ اشاره‌ای — مسیرِ زنده resolve شد (صفر بایت، ولی نوشتنِ بعدی زنده می‌افتد)",
                               pointers, "ptr")):
        if not group:
            continue
        print(f"\n{title}:")
        agg: dict[str, set[str]] = {}
        for r in group:
            for v in r[key]:
                agg.setdefault(v["path"], set()).add(r["test"])
        for path, who in sorted(agg.items(), key=lambda kv: -len(kv[1])):
            print(f"  {len(who):>3}×  {path}")
            for w in sorted(who)[:6]:
                print(f"         ← {w}")
    print(f"\nلاگ‌های خام: {workdir}")
    # سنجهٔ پذیرش «صفر بایتِ تغییر» است ⇒ فقط جهشِ واقعی و اجرایِ نامعتبر قرمزند.
    return 1 if (leakers or unarmed) else 0


if __name__ == "__main__":
    sys.exit(main())
