#!/usr/bin/env python3
"""
self_update.py — حلقه‌ی خوداپدیتیِ پرامپت (اعمال خودکار + rollback خودکار).

فلسفه‌ی ایمنِ فیوژن با وجود «اعمال خودکار»:
  ۱) هر تغییر فقط اگر نمره‌ی eval را بهتر کند نگه داشته می‌شود؛ وگرنه خودکار rollback.
  ۲) گاردریلِ امنیتی: پرامپت پیشنهادی نباید نقشِ خود را حذف کند یا injection باشد
     (سیستم نباید گول بخورد و محافظ‌های خودش را بردارد).
  ۳) kill-switch و سقفِ تعداد دور، و تاریخچه‌ی کاملِ نسخه‌ها برای بازگشت.

اجرا:
  python self_update.py                 # روی researcher
  python self_update.py analyst         # روی یک ایجنت دیگر
  python self_update.py --show researcher    # تاریخچه‌ی نسخه‌ها
  python self_update.py --rollback researcher  # یک نسخه به عقب (دستی)
"""
from __future__ import annotations
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# بارگذاری .env (برای حالت LIVE)
def _load_env():
    p = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

import config
from src.prompt_store import PromptStore
from src.evals import score_prompt
from src.optimizer import Optimizer
from src.killswitch import KillSwitch, KillSwitchError
from src.tracing import AuditLog
from src.agents import Researcher, Analyst, Supervisor

BASELINE = {c.name: c.system for c in (Researcher, Analyst, Supervisor)}
ROLE_MARKER = {"researcher": "Researcher", "analyst": "Analyst", "supervisor": "Supervisor"}


def validate_prompt(agent: str, text: str) -> tuple[bool, str]:
    """گاردریلِ امنیتیِ خوداپدیتی."""
    if not text or not (20 <= len(text) <= 2000):
        return False, "طول نامعتبر"
    if ROLE_MARKER.get(agent, "") not in text:
        return False, "نشانه‌ی نقش حذف شده"
    low = text.lower()
    for bad in config.FORBIDDEN_IN_PROMPT:
        if bad.lower() in low:
            return False, f"عبارت ممنوع: «{bad}»"
    return True, "ok"


def run(agent: str):
    store = PromptStore(seed=BASELINE)
    ks = KillSwitch(stop_file="logs/STOP")
    audit = AuditLog()
    opt = Optimizer()

    active = store.get_active(agent)
    score, missing = score_prompt(agent, active)
    store.set_score(agent, score)
    print(f"\n🔧 خوداپدیتیِ «{agent}» | نمره‌ی اولیه: {score} | نسخه: v{store.active_version(agent)}")
    print(f"   معیارهای جاافتاده: {missing or '—'}")
    audit.log("selfupdate_start", "optimizer", agent=agent, score=score,
              version=store.active_version(agent))

    explored = False
    try:
        for rnd in range(1, config.MAX_UPDATE_ROUNDS + 1):
            ks.check()  # کلید قطع
            if missing:
                cand = opt.propose_fix(agent, active, missing); kind = "fix"
            elif not explored:
                cand = opt.propose_explore(agent, active); kind = "explore"; explored = True
            else:
                break

            ok, why = validate_prompt(agent, cand)
            if not ok:
                audit.log("selfupdate_rejected", "guardrail", agent=agent, kind=kind, reason=why)
                print(f"  ⛔ دور {rnd}: پیشنهاد رد شد (گاردریل: {why})")
                if kind == "explore":
                    break
                continue

            v = store.new_version(agent, cand, note=f"{kind} round{rnd}", score=None)
            new_score, new_missing = score_prompt(agent, cand)
            store.set_score(agent, new_score)

            if new_score > score:
                audit.log("selfupdate_kept", "optimizer", agent=agent, kind=kind,
                          version=v, old=score, new=new_score)
                print(f"  ✅ دور {rnd} ({kind}): نمره {score} → {new_score} | نگه داشته شد (v{v})")
                active, score, missing = cand, new_score, new_missing
            else:
                store.rollback(agent)
                back = store.active_version(agent)
                audit.log("selfupdate_rolledback", "optimizer", agent=agent, kind=kind,
                          version=v, old=score, new=new_score, reverted_to=back)
                print(f"  ↩️  دور {rnd} ({kind}): نمره {score} → {new_score} | بدتر شد، rollback به v{back}")
                if kind == "explore":
                    break
    except KillSwitchError as e:
        audit.log("selfupdate_halted", "optimizer", agent=agent, reason=str(e))
        print(f"\n🛑 {e}")

    audit.log("selfupdate_done", "optimizer", agent=agent,
              final_score=score, final_version=store.active_version(agent))
    print(f"\n🏁 پایان | نمره‌ی نهایی: {score} | نسخه‌ی فعال: v{store.active_version(agent)}")
    print(f"🔐 صحت audit log: {'سالم' if audit.verify_chain() else 'دستکاری‌شده!'}")
    show(agent, store)


def show(agent: str, store: PromptStore | None = None):
    store = store or PromptStore(seed=BASELINE)
    print(f"\n── تاریخچه‌ی نسخه‌های «{agent}» (فعال: v{store.active_version(agent)}) ──")
    for h in store.history(agent):
        mark = "→" if h["v"] == store.active_version(agent) else " "
        print(f"  {mark} v{h['v']} score={h['score']} · {h['note']}")
        print(f"      {h['prompt'][:90]}{'…' if len(h['prompt']) > 90 else ''}")


def rollback(agent: str):
    store = PromptStore(seed=BASELINE)
    before = store.active_version(agent)
    after = store.rollback(agent)
    AuditLog().log("selfupdate_manual_rollback", "human", agent=agent, frm=before, to=after)
    print(f"↩️  «{agent}»: از v{before} به v{after} برگشت.")
    show(agent, store)


def main():
    args = sys.argv[1:]
    if "--show" in args:
        i = args.index("--show"); show(args[i + 1] if i + 1 < len(args) else "researcher"); return
    if "--rollback" in args:
        i = args.index("--rollback"); rollback(args[i + 1] if i + 1 < len(args) else "researcher"); return
    agent = args[0] if args else "researcher"
    run(agent)


if __name__ == "__main__":
    main()
