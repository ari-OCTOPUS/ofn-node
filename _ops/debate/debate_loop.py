#!/usr/bin/env python3
"""
debate_loop.py — STAGE 2 پک: limit cycle دو-قطبی «خلاق × معمار».

هندسه (FitzHugh–Nagumo): خلاق = متغیر تحریک v (ایدهٔ جسور)، معمار = بازدارنده w
(red-team/kill-criteria). خروجی سالم نه توافق کامل (rigidity) است نه بحث بی‌پایان
(chaos)، بلکه چرخهٔ بسته‌ای که در ≤۳ دور به verdict می‌رسد؛ دور چهارم وجود ندارد —
بی‌نتیجه = QUEUE برای انسان.

جعبه‌سیاه بودن: دو نقش همدیگر را نمی‌بینند مگر از طریق artifact ثبت‌شده (JSON دور قبل
که در ledger هم append شده است).

ناوردی‌ها:
  - هر call از organ_gate (ارگان DEBATE_LOOP) می‌گذرد؛ deny گیت = توقف امن، نه mock.
  - هر دور یک NOTE(subtype=EXPERIENCE) به ledger زنجیرهٔ‌هش ژنوم؛ هیچ delete.
  - «بازمانده» فقط یعنی واردِ صف تأیید انسان شد (SURVIVORS-QUEUE.md + PROPOSAL در ledger
    با قرارداد ۷فیلدی humility تا دکترِ ژنوم هم داوری‌اش کند) — هرگز امتیاز خودثبت‌شده.
  - live دوقفله: تاریخ ≥ 2026-07-21 + ACTIVATION-DEBATE.flag مالک. پیش‌فرض: stub آفلاین $0.
  - escalation به tier بالاتر در این حلقه ممنوع (هر escalation = WASTE؛ فقط لاگ).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib      # noqa: E402
import organ_gate  # noqa: E402
import topics      # noqa: E402
from client import DeepSeekClient, extract_json  # noqa: E402

MAX_ROUNDS = 3
ORGAN = "DEBATE_LOOP"
QUEUE_MD = opslib.DEBATE_DIR / "SURVIVORS-QUEUE.md"   # env-پذیر (تست‌ها ایزوله می‌مانند)

MUSE_KEYS = {"idea", "why_genius", "why_insane", "est_tokens", "quality_bar", "epistemic_tag"}
ARCHITECT_KEYS = {"verdict", "kill_condition", "cheapest_test", "epistemic_tag"}


def _role_prompt(name: str) -> str:
    p = opslib.PROMPTS / name
    return p.read_text("utf-8") + "\n\n" + topics.GUARD_SENTENCE


def _stub_transport(body: dict) -> dict:
    """transport قطعی آفلاین ($0): مستقل از محتوای topic — همین، خودش تستِ تزریق است."""
    system = body["messages"][0]["content"]
    is_muse = "You are ARCHITECT" not in system   # پرامپت معمار هم واژهٔ MUSE را دارد
    if is_muse:
        payload = {"idea": "پروکسی ارزش per-organ از APPROVALهای sent ساخته شود",
                   "why_genius": "fitness را از حدس به دادهٔ انسانی-تأییدشده می‌برد",
                   "why_insane": "حجم دادهٔ اولیه کم است؛ نویز نرخ پذیرش",
                   "est_tokens": 800, "quality_bar": "normal", "epistemic_tag": "SPEC"}
    else:
        payload = {"verdict": "pass",
                   "kill_condition": "اگر ۱۴ روز بگذرد و هیچ APPROVAL ثبت نشود",
                   "cheapest_test": "شمارش رویدادهای sent هفتهٔ جاری از logs/outbox.jsonl",
                   "epistemic_tag": "SPEC"}
    return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}}


def _gated_call(client: DeepSeekClient, system: str, user: str,
                max_tokens: int, task: str) -> dict:
    """reserve → call → settle/release. deny = RuntimeError (fail-closed، بدون mock)."""
    est = client.est_worst_case(len(system) + len(user), max_tokens)
    r = organ_gate.reserve(ORGAN, est, task=task)
    if not r.get("allow"):
        raise RuntimeError(f"organ_gate deny: {r.get('reason')}")
    try:
        out = client.complete(system, user, max_tokens=max_tokens)
    except Exception:
        organ_gate.release(ORGAN, est, task=task)
        raise
    organ_gate.settle(ORGAN, est, out["cost_usd"], task=task)
    return out


def _queue_survivor(topic: dict, muse: dict, architect: dict, status: str) -> bool:
    QUEUE_MD.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_MD.exists():
        QUEUE_MD.write_text(
            "# صف تأیید انسان — بازمانده‌های مناظره (append-only)\n\n"
            "> «بازمانده» فقط یعنی وارد این صف شد؛ تأیید = verdict آری.\n\n", "utf-8")
    # idempotent (§۹): تا وقتی این topic در صف است، append تکراری ممنوع —
    # وگرنه debateِ هر epoch (~۲۰ دقیقه) صف انسان و ledger را غرق می‌کند.
    if f"— {topic['id']} ·" in QUEUE_MD.read_text("utf-8"):
        return False
    with QUEUE_MD.open("a", encoding="utf-8") as f:
        f.write(f"## {opslib.now_iso()} — {topic['id']} · status: {status}\n\n"
                f"- **topic** ({topic['source']}): {topic['text']}\n"
                f"- **idea:** {muse.get('idea', '—')}\n"
                f"- **why_genius:** {muse.get('why_genius', '—')}\n"
                f"- **why_insane:** {muse.get('why_insane', '—')}\n"
                f"- **kill_condition:** {architect.get('kill_condition', '—')}\n"
                f"- **cheapest_test:** {architect.get('cheapest_test', '—')}\n\n")
    return True


def run_debate(topic: dict, live: bool = False, rounds: int = MAX_ROUNDS,
               transport=None) -> dict:
    # قرارداد topic (fail-soft): فقط شکل whitelist — id/source/text (خروجی topics.get_topic).
    # dict آزاد (مثل {"topic": ...} که governor قبلاً می‌فرستاد) نباید KeyError عمیق بدهد.
    if not isinstance(topic, dict) or not {"id", "source", "text"} <= topic.keys():
        return {"status": "invalid-topic",
                "reason": "topic باید از topics.get_topic بیاید (کلیدهای id/source/text)",
                "got": sorted(topic) if isinstance(topic, dict) else type(topic).__name__}
    stop = opslib.halted(for_debate=True)
    if stop:
        return {"status": "halted", "reason": stop}
    if live:
        ok, why = opslib.live_gate_open(opslib.ACT_DEBATE)
        if not ok:
            return {"status": "blocked", "reason": why}
    if not live and transport is None:
        transport = _stub_transport
    muse_client = DeepSeekClient(role="econ", transport=transport)
    architect_client = DeepSeekClient(role="reason", transport=transport)
    muse_sys = _role_prompt("debate-muse-role.txt")
    architect_sys = _role_prompt("debate-architect-role.txt")
    wrapped = topics.wrap(topic["text"])
    topic_hash = hashlib.sha256(topic["text"].encode("utf-8")).hexdigest()[:16]

    try:
        return _rounds(topic, wrapped, topic_hash, rounds,
                       muse_client, architect_client, muse_sys, architect_sys)
    except RuntimeError as e:
        if "organ_gate deny" in str(e):
            return {"status": "gated", "reason": str(e),
                    "note": "fail-closed: بدون permit گیت، هیچ call و هیچ mock"}
        raise


def _rounds(topic: dict, wrapped: str, topic_hash: str, rounds: int,
            muse_client: DeepSeekClient, architect_client: DeepSeekClient,
            muse_sys: str, architect_sys: str) -> dict:
    history: list[dict] = []
    muse_out: dict = {}
    arch_out: dict = {}
    final = "queue-human"
    for rnd in range(1, rounds + 1):
        constraint = ""
        if arch_out.get("verdict") == "needs-fix":
            constraint = ("\nقید معمار از دور قبل (باید رفع شود): "
                          + json.dumps(arch_out, ensure_ascii=False))
        muse_raw = _gated_call(muse_client, muse_sys,
                               f"topic: {wrapped}{constraint}\nخروجی فقط JSON.",
                               700, f"debate-muse-r{rnd}")
        muse_out = extract_json(muse_raw["text"])
        if not MUSE_KEYS.issubset(muse_out):
            raise ValueError(f"muse JSON contract broken (r{rnd}): {sorted(muse_out)}")
        arch_raw = _gated_call(architect_client, architect_sys,
                               f"topic: {wrapped}\nidea (artifact ثبت‌شده): "
                               + json.dumps(muse_out, ensure_ascii=False)
                               + "\nخروجی فقط JSON.",
                               500, f"debate-architect-r{rnd}")
        arch_out = extract_json(arch_raw["text"])
        if not ARCHITECT_KEYS.issubset(arch_out):
            raise ValueError(f"architect JSON contract broken (r{rnd}): {sorted(arch_out)}")
        round_rec = {"round": rnd, "muse": muse_out, "architect": arch_out,
                     "cost_usd": muse_raw["cost_usd"] + arch_raw["cost_usd"],
                     "stub": muse_raw.get("stub", False)}
        history.append(round_rec)
        opslib.ledger_note("EXPERIENCE", {
            "loop": "debate", "topic_id": topic["id"], "topic_hash": topic_hash,
            "round": rnd, "verdict": arch_out.get("verdict"),
            "cost_usd": round_rec["cost_usd"], "stub": round_rec["stub"]}, actor="debate")
        if arch_out.get("verdict") == "kill" and arch_out.get("kill_condition"):
            final = "killed"        # نیم‌سیکل میرا — چرخه بسته شد
            break
        if arch_out.get("verdict") == "pass":
            final = "survived"      # بلیت صف انسان، نه تأیید
            break
        # needs-fix → دور بعد با قید (بازخورد منفی؛ همان که چرخه را پایدار می‌کند)

    queued = False
    if final in ("survived", "queue-human"):
        queued = _queue_survivor(topic, muse_out, arch_out,
                                 "pending-human" if final == "survived"
                                 else "undecided-after-3-rounds")
        if final == "survived" and queued:
            # قرارداد ۷فیلدی humility → دکترِ ژنوم هم در run بعدی داوری‌اش می‌کند
            # (فقط بار اول — PROPOSAL تکراری برای topicِ هنوز-در-صف ممنوع)
            register_survivor_proposal(muse_out, arch_out, topic)
    return {"status": final, "topic_id": topic["id"], "rounds": len(history),
            "queued": queued,
            "cost_usd": round(sum(h["cost_usd"] for h in history), 6), "history": history}


# ثبت PROPOSAL واقعی (نه NOTE) برای بازمانده — جدا تا قرارداد دکتر دقیق رعایت شود
def register_survivor_proposal(muse_out: dict, architect_out: dict, topic: dict) -> None:
    try:
        opslib.genome_ledger().append("PROPOSAL", {
            "idea": muse_out.get("idea", ""),
            "why_it_might_be_genius": muse_out.get("why_genius", ""),
            "why_it_might_be_insane": muse_out.get("why_insane", ""),
            "confidence": 0.5,
            "kill_criteria": architect_out.get("kill_condition", ""),
            "smallest_test": architect_out.get("cheapest_test", ""),
            "reversible": True,
            "origin": {"loop": "debate", "topic_id": topic["id"]},
        }, actor="debate", to="doctor")
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"debate PROPOSAL append failed: {e}"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic-id", default="seed-0")
    ap.add_argument("--live", action="store_true",
                    help="نیازمند گیت دوقفله (تاریخ + ACTIVATION-DEBATE.flag مالک)")
    args = ap.parse_args()
    t = topics.get_topic(args.topic_id)
    if not t:
        print(json.dumps({"error": f"topic {args.topic_id} در whitelist نیست"}, ensure_ascii=False))
        sys.exit(1)
    r = run_debate(t, live=args.live)
    print(json.dumps(r, ensure_ascii=False, indent=2))
