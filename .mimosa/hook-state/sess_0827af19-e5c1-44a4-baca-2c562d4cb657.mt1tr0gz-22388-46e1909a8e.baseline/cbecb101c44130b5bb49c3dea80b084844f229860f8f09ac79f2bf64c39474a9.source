"""test_guidance_box.py — «جعبهٔ راهنماییِ انسان» (guidance_box).

سیگنال‌های پُراهرمِ موجود (تأیید/مسدود/ترس/نیاز) → چند سوالِ مشخص + «چرا»،
رتبه‌بندی‌شده (پول/مسدود/تأیید اول)، سقفِ ۵، dedupe. مشاهدهٔ خالص: هیچ نوشتنی، fail-soft،
scrub containment. تست با fixtureهای مصنوعی زیرِ STATE_DIR ِ موقتِ harness.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("guidance-box")

import guidance_box   # noqa: E402
import events         # noqa: E402
import opslib         # noqa: E402


# ── ابزارهای fixture ─────────────────────────────────────────────────────────
def _reset():
    """state را به «خالی» برگردان: events.jsonl + stress-latest + needs-nudge."""
    if events.LOG.exists():
        events.LOG.unlink()
    for rel in ("cortex/stress-latest.json", "needs-nudge.json"):
        p = opslib.STATE_DIR / rel
        if p.exists():
            p.unlink()


def _write_stress(in_fear, subs):
    p = opslib.STATE_DIR / "cortex" / "stress-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": "stress.v1", "in_fear": in_fear,
                             "subsystems": subs, "organism_stress": 0.9,
                             "ts": opslib.now_iso()}, ensure_ascii=False), "utf-8")


def _write_needs(n):
    p = opslib.STATE_DIR / "needs-nudge.json"
    p.write_text(json.dumps({"last_n": n, "last_hash": "h", "last_ts": 0}), "utf-8")


def _snap(root):
    out = {}
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p)] = (st.st_mtime_ns, st.st_size)
    return out


# ── تست‌ها ───────────────────────────────────────────────────────────────────
def t_a_empty_state_n_zero():
    """هیچ سیگنالی → n=0، فهرستِ خالی (هرگز سوالِ الکی نمی‌سازد)."""
    _reset()
    g = guidance_box.guidance()
    assert g["n"] == 0 and g["items"] == [], g


def t_b_high_leverage_surface_and_ranked():
    """پول/مسدود/تأیید سطح می‌آیند و پول اول است؛ هر آیتم سوال+چرا+priority دارد."""
    _reset()
    _write_stress(["money"], {"money": {"name": "💰 جریانِ مالی", "stress": 0.97,
                                        "fear": True, "detail": "29/30 دلار"}})
    events.emit("task.blocked", "legs", summary="خودترمیم شکست خورد",
                next_action="خانه: بررسی")
    events.emit("approval.required", "approval-channel",
                summary="یه کار منتظرِ تأییدِ توست", approval_state="required",
                next_action="تلگرام: آره/نه")
    g = guidance_box.guidance()
    srcs = [it["source"] for it in g["items"]]
    assert "money" in srcs                                  # ترسِ مالی
    assert "blocked" in srcs and "approval" in srcs
    assert g["items"][0]["source"] == "money"              # پول = بالاترین اهرم، اول
    assert g["items"][0]["priority"] == "high"
    assert g["n"] == len(g["items"])
    for it in g["items"]:
        assert it["q"] and it["why"]
        assert set(it.keys()) == {"q", "why", "source", "priority"}   # دقیقاً API
        assert it["priority"] in ("high", "medium", "low")


def t_c_cap_enforced_at_five():
    """بیش از ۵ سیگنال → سقفِ ۵ رعایت می‌شود؛ اهرم‌بالاها می‌مانند."""
    _reset()
    for i in range(3):
        events.emit("task.blocked", "doctor", summary=f"مانعِ شمارهٔ {i}")
    events.emit("approval.required", "approval-channel",
                summary="یه کار منتظرِ تأییدِ توست", approval_state="required")
    _write_stress(["money", "heart", "doctor"], {
        "money":  {"name": "💰 مالی", "detail": "29/30"},
        "heart":  {"name": "❤️ قلب", "detail": "σ=0.95"},
        "doctor": {"name": "🩺 دکتر", "detail": "6 معطل"}})
    _write_needs(4)
    g = guidance_box.guidance()                            # ۸ سیگنالِ متمایز → سقف ۵
    assert len(g["items"]) == 5 and g["n"] == 5, g
    assert g["items"][0]["source"] == "money"              # ترسِ مالی اول
    assert any(it["source"] == "blocked" for it in g["items"])


def t_d_dedupe_identical():
    """چند رویدادِ تأییدِ هم‌متن → یک آیتم (dedupe)."""
    _reset()
    for _ in range(4):
        events.emit("approval.required", "approval-channel",
                    summary="یه کار منتظرِ تأییدِ توست", approval_state="required")
    g = guidance_box.guidance()
    appr = [it for it in g["items"] if it["source"] == "approval"]
    assert len(appr) == 1, g


def t_e_containment_scrub():
    """هویتِ Project-F هرگز echo نمی‌شود (scrub → redacted)."""
    _reset()
    events.emit("approval.required", "approval-channel",
                summary="پرداخت به onlyfans صبا", approval_state="required")
    g = guidance_box.guidance()
    blob = json.dumps(g, ensure_ascii=False)
    for bad in ("onlyfans", "صبا", "اونلی"):
        assert bad not in blob, blob
    assert any("redacted" in it["q"] for it in g["items"])


def t_f_pure_read_no_writes():
    """guidance() هیچ فایلی نمی‌سازد/عوض نمی‌کند (مشاهدهٔ خالص)."""
    _reset()
    _write_stress(["money"], {"money": {"name": "💰 مالی", "detail": "29/30"}})
    _write_needs(2)
    events.emit("approval.required", "approval-channel", summary="x",
                approval_state="required")
    before = _snap(opslib.STATE_DIR)
    guidance_box.guidance()
    guidance_box.guidance()
    after = _snap(opslib.STATE_DIR)
    assert before == after, "guidance() نباید چیزی بنویسد"


def t_g_stale_events_fade():
    """رویدادِ کهنه‌تر از پنجره شمرده نمی‌شود (تازگی)."""
    _reset()
    ev = events.emit("approval.required", "approval-channel",
                     summary="کهنه", approval_state="required")
    # ts را دستی به فراتر از پنجره ببر (بازنویسیِ خطِ لاگ در تست، نه در ماژول)
    old_ts = ev["ts"] - (guidance_box.WINDOW_H + 1) * 3600.0
    lines = events.LOG.read_text("utf-8").splitlines()
    rec = json.loads(lines[-1]); rec["ts"] = old_ts
    lines[-1] = json.dumps(rec, ensure_ascii=False)
    events.LOG.write_text("\n".join(lines) + "\n", "utf-8")
    g = guidance_box.guidance()
    assert g["n"] == 0, g


def t_h_structural_read_only():
    """ساختاری: ماژول هیچ الگوی نوشتن ندارد."""
    src = Path(guidance_box.__file__).read_text("utf-8")
    for bad in ("write_text", ".write(", "open(", "mkdir", "LockedJson",
                "os.replace", "append_jsonl", "ledger_note", ".emit("):
        assert bad not in src, f"guidance_box باید فقط‌خواندنی باشد: {bad}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_guidance_box: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)