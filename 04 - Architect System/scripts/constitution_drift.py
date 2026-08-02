# -*- coding: utf-8 -*-
"""خودآزمونِ قانون‌های اساسی — «قانون هم از کدش عقب می‌افتد» را ماشین‌خوان می‌کند.

می‌سنجد که ادعاهای سه سندِ حاکمیتی هنوز با زمینِ زنده می‌خوانند:
  * _PROJECT_INSTRUCTIONS.md  — مسیرها/فایل‌هایی که نام می‌برد وجود دارند؟
  * _octopus/config/policy.yaml — فعل‌های forbidden با سطحِ ابزارِ MCP نمی‌جنگند؟
  * _ops/octopus_mcp/CONSTITUTION.md — نمادهایی که نام می‌برد در کد هستند؟ سندها tracked اند؟

dry-run است: فقط گزارش. خروج غیرصفر = حداقل یک قاعدهٔ دروغ‌شده.
شمارِ صریحِ pass/fail چاپ می‌شود — «نبودِ خطا ≠ سبز».
اجرا:  python "04 - Architect System/scripts/constitution_drift.py"
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

PASS: list[str] = []
FAIL: list[str] = []


def check(ok: bool, label: str, why: str = "") -> None:
    (PASS if ok else FAIL).append(label if ok else f"{label} — {why}")


# ── ۱) _PROJECT_INSTRUCTIONS.md: هر مسیر/فایلی که نام می‌برد باید وجود داشته باشد ──
def check_instructions() -> None:
    src = ROOT / "_PROJECT_INSTRUCTIONS.md"
    text = src.read_text(encoding="utf-8", errors="replace")
    # backtick-مسیرهایی که شبیه مسیرِ واقعی‌اند (پوشهٔ شماره‌دار، _ops، اسکریپت، .md/.py/.json)
    cand = set(re.findall(r"`([^`\n]{3,120})`", text))
    paths = set()
    for c in cand:
        c2 = c.strip().strip("/")
        if re.match(r"^(0\d - |1\d - |_ops/|04 - |\.agentignore$|\.claude/)", c2) and \
           not any(ch in c2 for ch in "<>*?|«»"):
            paths.add(c2)
    # wikilink ها: [[path|alias]] — فقط آن‌ها که مسیرِ کامل دارند.
    # داخلِ جدولِ markdown پایپ escape می‌شود ([[…/PROJECT\|PROJECT]]) — بک‌اسلشِ دنباله را بریز.
    for m in re.findall(r"\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]", text):
        m = m.strip().rstrip("\\").strip()
        if "/" not in m:
            continue
        if any(part == "X" for part in m.split("/")):   # placeholderِ الگو، نه مسیرِ واقعی
            continue
        paths.add(m if m.endswith(".md") else m + ".md")
    for p in sorted(paths):
        target = ROOT / p
        # wikilink ِ بدونِ پسوند به پوشه هم می‌تواند اشاره کند
        ok = target.exists() or target.with_suffix("").exists() or \
             (ROOT / p.replace(".md", "")).exists()
        check(ok, f"منشور نام می‌برد: {p}", "وجود ندارد — قاعدهٔ دروغ‌شده یا مسیرِ جابه‌جاشده")


# ── ۲) policy.yaml در برابر سطحِ MCP: فعلِ ممنوع نباید ابزارِ مستقیم داشته باشد ──
def check_policy_vs_mcp() -> None:
    pol = ROOT / "_octopus" / "config" / "policy.yaml"
    srv = ROOT / "_ops" / "octopus_mcp" / "server.py"
    if not pol.exists() or not srv.exists():
        check(False, "policy.yaml + server.py موجودند", "یکی غایب است")
        return
    ptxt = pol.read_text(encoding="utf-8", errors="replace")
    stxt = srv.read_text(encoding="utf-8", errors="replace")
    # فعل‌های requires_approval/forbidden از yaml (پارسِ سبک، بدون وابستگی)
    verbs = set(re.findall(r'^\s*-\s*"([a-z_]+)"\s*$', ptxt, re.M))
    # ابزارهای exposed سرور
    tools = set(re.findall(r'^\s{4}"([a-z_]+)":\s*\(t_', stxt, re.M))
    overlap = verbs & tools
    check(not overlap, "هیچ فعلِ گیت‌خورده ابزارِ مستقیمِ MCP نیست",
          f"هم‌پوشانی: {sorted(overlap)}")
    # propose_action باید delete_file را رد کند (گاردِ ساختاری، نه قول)
    m = re.search(r"allowed\s*=\s*\{([^}]*)\}", stxt)
    allowed = set(re.findall(r'"([a-z_]+)"', m.group(1))) if m else set()
    check("delete_file" not in allowed, "propose_action ساختاراً delete_file ندارد",
          "delete_file در allowed-set است")
    check("propose_action" in stxt and "QUEUE_PENDING" in stxt,
          "تنها نویسنده propose_action→queue/pending است", "نماد گم شده")
    # default_mode هنوز propose-only است؟
    check('default_mode: "propose-only"' in ptxt, "policy: default_mode=propose-only",
          "سیاستِ پایه عوض شده — CONSTITUTION باید بازنویسی شود")


# ── ۳) CONSTITUTION.md: نمادهای نام‌برده در کد موجودند؛ سندهای حاکمیتی tracked اند ──
def check_constitution() -> None:
    con = ROOT / "_ops" / "octopus_mcp" / "CONSTITUTION.md"
    srv = ROOT / "_ops" / "octopus_mcp" / "server.py"
    if not con.exists():
        check(False, "CONSTITUTION.md موجود است", "غایب")
        return
    ctxt = con.read_text(encoding="utf-8", errors="replace")
    stxt = srv.read_text(encoding="utf-8", errors="replace") if srv.exists() else ""
    for sym in ("_resolve", "_denied", "t_propose_action", "MAX_SLICE_BYTES"):
        if f"`{sym}`" in ctxt or sym in ctxt:
            check(re.search(rf"def {sym}|^{sym}\s*=", stxt, re.M) is not None,
                  f"نمادِ نام‌برده در کد هست: {sym}", "سند نمادی را نام می‌برد که در server.py نیست")
    # tracked بودنِ سندهای حاکمیتی (gitignore محافظت نیست؛ سنجه git ls-files)
    try:
        ls = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=30).stdout
    except OSError as exc:
        check(False, "git ls-files اجرا شد", str(exc))
        return
    tracked = set(ls.splitlines())
    for f in ("_ops/octopus_mcp/CONSTITUTION.md", "_ops/octopus_mcp/server.py",
              "_octopus/config/policy.yaml", "_octopus/config/octopus.yaml",
              "_octopus/config/projects.yaml", "_octopus/config/bots.yaml",
              ".mcp.json"):
        check(f in tracked, f"tracked: {f}", "untracked — تاریخچه ندارد و چک‌اوتِ تمیز نابودش می‌کند")
    # state و logs نباید tracked شوند (برشِ برعکس)
    leaked = [f for f in tracked if f.startswith(("_octopus/state/", "_octopus/logs/",
                                                  "_octopus/queue/"))]
    check(not leaked, "state/logs/queue ِ ران‌تایم بیرونِ گیت‌اند", f"نشت: {leaked[:3]}")


# ── ۴) §۸: ایندکس‌های نام‌برده زیرِ ~۲۰۰ خط ──────────────────────────────────
def check_index_caps() -> None:
    for rel in ("_PROJECT_INSTRUCTIONS.md", "01 - Dashboard/Home.md",
                "_ops/octopus_mcp/CONSTITUTION.md"):
        p = ROOT / rel
        if not p.exists():
            continue
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        check(n <= 210, f"سقفِ ۲۰۰ خط: {rel} ({n})", "سرریز — طبق §۸ به نوتِ خواهر منتقل شود")


def main() -> int:
    for fn in (check_instructions, check_policy_vs_mcp, check_constitution, check_index_caps):
        try:
            fn()
        except Exception as exc:  # خطای خودِ چک = قرمز، نه سکوت
            check(False, f"چکِ {fn.__name__} اجرا شد", f"{type(exc).__name__}: {exc}")
    print(f"PASS={len(PASS)} FAIL={len(FAIL)}")
    for f in FAIL:
        print("  ✗", f)
    if not FAIL:
        print("✓ هر سه سندِ حاکمیتی با زمین می‌خوانند")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
