#!/usr/bin/env python3
"""ایجنتِ مارکتینگِ زیمان — ورکرِ اجراشدنی که مغزِ کنترل روشن/خاموش/تستش می‌کند.

حالت‌ها:
  python worker.py              → حالتِ زنده (loop): مغزِ کنترل این را «start» می‌کند.
  python worker.py --once       → یک draftِ محتوا بساز و خارج شو.
  python worker.py --dm [N]     → N پیامِ DM بازارِ گرم بساز (پیش‌فرض ۶).
  python worker.py --posts [N]  → N کپشنِ پستِ اینستاگرام بساز (پیش‌فرض ۳).
  python worker.py --selftest   → خودآزمایی (مغزِ کنترل این را «test» می‌کند). کدِ خروجی 0/1.
  python worker.py --status     → وضعیتِ کوتاه (JSON).
  python worker.py --campaign N → گاردِ ظرفیتِ D4 را روی هدفِ N واحد امتحان کن.

ایمنی: هرگز منتشر/خرج نمی‌کند. فقط فایلِ draft محلی در drafts/ می‌نویسد (autonomy=read-only).
با کلیدِ ANTHROPIC_API_KEY خروجی «live (Claude)» می‌شود؛ بدونِ کلید «offline (قالبی)».
"""
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ziman.brief import read_vault_context                       # noqa: E402
from ziman.capacity import check_campaign                         # noqa: E402
from ziman.config import load_config                              # noqa: E402
from ziman.content import (generate_draft, generate_dms,          # noqa: E402
                           generate_posts)

CFG_PATH = ROOT / "ziman.yaml"
DRAFTS = ROOT / "drafts"
_STOP = False


def _log(msg):
    try:
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] زیمان: {msg}", flush=True)
    except (BrokenPipeError, ValueError):
        pass  # اگر لوله/خروجی بسته شد، کرش نکن


def _context(cfg):
    v = cfg.get("vault", {}) or {}
    return read_vault_context((ROOT / v.get("path", "..")).resolve(), v.get("notes", []))


def _write(kind, text, mode) -> Path:
    DRAFTS.mkdir(parents=True, exist_ok=True)
    out = DRAFTS / f"{kind}-{datetime.now():%Y%m%d-%H%M%S}-{mode}.md"
    out.write_text(text, encoding="utf-8")
    _log(f"{kind} نوشته شد ({mode}): {out.name}")
    return out


def cmd_once():
    cfg = load_config(CFG_PATH)
    text, mode = generate_draft(cfg, context=_context(cfg))
    _write("draft", text, mode)
    return 0


def cmd_dm(n):
    cfg = load_config(CFG_PATH)
    text, mode = generate_dms(cfg, n=int(n), context=_context(cfg))
    _write("dm", text, mode)
    return 0


def cmd_posts(n):
    cfg = load_config(CFG_PATH)
    text, mode = generate_posts(cfg, n=int(n), context=_context(cfg))
    _write("posts", text, mode)
    return 0


def cmd_status():
    cfg = load_config(CFG_PATH)
    drafts = sorted(DRAFTS.glob("*.md")) if DRAFTS.exists() else []
    print(json.dumps({
        "project": "ziman",
        "capacity_ceiling_per_week": cfg["capacity"]["units_per_week_ceiling"],
        "has_api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "mode": "live(Claude)" if os.environ.get("ANTHROPIC_API_KEY") else "offline(template)",
        "drafts_count": len(drafts),
        "last_draft": drafts[-1].name if drafts else None,
        "autonomy": (cfg.get("safety", {}) or {}).get("autonomy", "read-only"),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_campaign(n):
    cfg = load_config(CFG_PATH)
    v = check_campaign(n, cfg["capacity"]["units_per_week_ceiling"])
    print(json.dumps({"requested": v.requested, "ceiling": v.ceiling, "max_allowed": v.max_allowed,
                      "approved": v.approved, "reason": v.reason}, ensure_ascii=False, indent=2))
    return 0 if v.approved else 2


def cmd_selftest():
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("✅ " if cond else "❌ ") + name)
        ok = ok and bool(cond)

    cfg = load_config(CFG_PATH)
    cap = int(cfg["capacity"]["units_per_week_ceiling"])
    check("ziman.yaml بارگذاری شد", isinstance(cfg, dict) and "capacity" in cfg)
    check("سقفِ ظرفیت > 0", cap > 0)
    check("گاردِ D4: هدفِ بالای سقف رد می‌شود", check_campaign(cap * 5, cap).approved is False)
    check("گاردِ D4: هدفِ زیرِ سقف تأیید می‌شود", check_campaign(max(1, cap // 2), cap).approved is True)
    had = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        text, mode = generate_draft(cfg, context="")
        check("تولیدِ offline draft کار می‌کند", bool(text) and mode == "offline")
        check("ماهیتِ مصنوعیِ گل در draft لحاظ شده", "مصنوعی" in text)
        check("PayID در draft هست", "PayID" in text)
        dm_text, dm_mode = generate_dms(cfg, n=6, context="")
        check("تولیدِ ۶ DM (offline) کار می‌کند", dm_mode == "offline" and dm_text.count("**") >= 6)
        check("قواعدِ برند در DMها هست (PayID/مصنوعی)", "PayID" in dm_text or "مصنوعی" in dm_text)
        posts_text, posts_mode = generate_posts(cfg, n=3, context="")
        check("تولیدِ ۳ پست (offline) کار می‌کند", posts_mode == "offline" and posts_text.count("**") >= 3)
    finally:
        if had is not None:
            os.environ["ANTHROPIC_API_KEY"] = had
    print("\nنتیجه: " + ("همه سبز ✅" if ok else "قرمز ❌"))
    return 0 if ok else 1


def _install_signals():
    def handler(signum, frame):
        global _STOP
        _STOP = True
        _log("سیگنالِ توقف دریافت شد؛ در حالِ خاموش‌شدنِ تمیز…")
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, handler)
        except Exception:  # noqa: BLE001
            pass


def cmd_loop():
    cfg = load_config(CFG_PATH)
    cadence = int((cfg.get("generation", {}) or {}).get("cadence_seconds", 3600))
    _install_signals()
    _log(f"روشن شد (زنده). سقفِ ظرفیت={cfg['capacity']['units_per_week_ceiling']}/هفته · "
         f"هر {cadence}s یک draft · حالت=read-only (بدونِ انتشار).")
    context = _context(cfg)
    text, mode = generate_draft(cfg, context=context)
    _write("draft", text, mode)
    last = time.time()
    while not _STOP:
        time.sleep(1)
        if time.time() - last >= cadence:
            t, m = generate_draft(cfg, context=context)
            _write("draft", t, m)
            last = time.time()
    _log("خاموش شد.")
    return 0


def main(argv):
    if not argv:
        return cmd_loop()
    cmd = argv[0]
    arg1 = argv[1] if len(argv) > 1 else None
    if cmd == "--once":
        return cmd_once()
    if cmd == "--dm":
        return cmd_dm(arg1 or 6)
    if cmd == "--posts":
        return cmd_posts(arg1 or 3)
    if cmd == "--selftest":
        return cmd_selftest()
    if cmd == "--status":
        return cmd_status()
    if cmd == "--campaign":
        return cmd_campaign(arg1 or "0")
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
