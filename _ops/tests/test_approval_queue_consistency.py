#!/usr/bin/env python3
"""تستِ رفتاریِ P-L6: یکپارچه‌سازیِ ApprovalQueue (shadow ≠ واقعی).

گپِ recon: دو صفِ تأییدِ ناهمگام وجود داشت — صفِ cockpit (shadow، به EffectorGate
 وصل نبود، هیچ‌گاه به‌روز نمی‌شد) و approval_channel (مسیرِ واقعیِ settle). خطر:
کاربر در UI «تأییدشده» می‌دید که هیچ اثری settle نمی‌کرد. فیکس: صفِ cockpit حالا
نمایِ فقط‌خواندنیِ همان حالتِ EffectorGate است (از طریقِ effect_status_fn).

این تست با **EffectorGate واقعی** (chrono.py) اثبات می‌کند:
  (الف) آیتمِ «تأییدشده» در cockpit ⟺ اثر واقعاً releasable/settled در EffectorGate
      است (بدونِ واگرایی).
  (ب) صفِ shadowِ cockpit هرگز به‌تنهایی چیزی را settle نمی‌کند (cockpit متدِ
      settle ندارد).
  (واگرایی-پیشگیری) بدونِ status_fn → صف صریحاً shadow است و هرگز «approved»
      نشان نمی‌دهد.
$0 آفلاین، stdlib-only.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("approval-queue-consistency")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "brain")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono  # noqa: E402
from cockpit import BrainCockpit, ApprovalItem  # noqa: E402


def _gate():
    """یک EffectorGate واقعی روی db موقت."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-l6.db")
    return chrono.EffectorGate(db), db


# ════════════════════════════════════════════════════════════════════════════════
# (الف) همگامیِ cockpit ⟺ EffectorGate (با gate واقعی)
# ════════════════════════════════════════════════════════════════════════════════

def t_pending_in_gate_shows_pending_in_cockpit():
    """effect هنوز pending در gate → آیتمِ cockpit «pending»، نه «approved»."""
    gate, db = _gate()
    eid = gate.request("send", "msg-001", beat=1)
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Project-F", "تأییدِ publish", 0.0, effect_id=eid)
    cp._reconcile_effect_status()
    item = [a for a in cp._approval_queue if a.effect_id == eid][0]
    assert item.status == "pending", f"pending در gate باید pending نشان دهد، نه {item.status}"
    assert gate.status_of(eid) == "pending"


def t_settled_in_gate_shows_approved_in_cockpit():
    """effect در gate settled → آیتمِ cockpit «approved» منعکس می‌شود (همگامی)."""
    gate, db = _gate()
    eid = gate.request("send", "msg-002", beat=1)
    # تنها مسیرِ قانونیِ settle: human-append → release → settle
    chrono.on_human_judgment({"verdict": "approve msg-002"}, gate=gate)
    assert gate.settle(eid) is True
    assert gate.status_of(eid) == "settled"
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Lead-نقاشی", "تأییدِ quote", 50.0, effect_id=eid)
    cp._reconcile_effect_status()
    item = [a for a in cp._approval_queue if a.effect_id == eid][0]
    assert item.status == "approved", f"settled در gate باید approved نشان دهد، نه {item.status}"


def t_releasable_in_gate_shows_approved_in_cockpit():
    """effect releasable (release شد ولی هنوز settle نشد) → cockpit approved."""
    gate, db = _gate()
    eid = gate.request("publish", "post-001", beat=1)
    entry = {"hash": "release-hash-001"}   # شبیه‌سازیِ append
    gate.release_gated_effects(entry)
    assert gate.status_of(eid) == "releasable"
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Project-F", "تأییدِ درفت", 0.0, effect_id=eid)
    cp._reconcile_effect_status()
    item = [a for a in cp._approval_queue if a.effect_id == eid][0]
    assert item.status == "approved", f"releasable باید approved نشان دهد، نه {item.status}"


def t_refused_in_gate_shows_denied_in_cockpit():
    """effect refused (kill/FREEZE) → آیتمِ cockpit «denied»."""
    gate, db = _gate()
    eid = gate.request("sync", "sync-001", beat=1)
    try:
        opslib_freeze()
        gate.settle(eid)   # refused می‌شود
    finally:
        opslib_unfreeze()
    assert gate.status_of(eid) == "refused"
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Crypto", "تأییدِ trade", 100.0, effect_id=eid)
    cp._reconcile_effect_status()
    item = [a for a in cp._approval_queue if a.effect_id == eid][0]
    assert item.status == "denied", f"refused باید denied نشان دهد، نه {item.status}"


def t_html_reconciles_before_display():
    """approval_queue_html ابتدا _reconcile_effect_status را صدا می‌زند — دید تازه."""
    gate, db = _gate()
    eid = gate.request("send", "msg-003", beat=1)
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Project-F", "تأییدِ publish", 0.0, effect_id=eid)
    html = cp.approval_queue_html()
    assert "تأییدِ publish" in html   # pending → نمایش داده می‌شود
    # حالا settle کن و دوباره HTML بگیر — باید از صف بیفتد (دیگر pending نیست)
    chrono.on_human_judgment({"verdict": "approve"}, gate=gate)
    gate.settle(eid)
    html2 = cp.approval_queue_html()
    assert "تأییدِ publish" not in html2, "settled نباید در صفِ pending بماند"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) صفِ shadowِ cockpit هرگز به‌تنهایی چیزی را settle نمی‌کند
# ════════════════════════════════════════════════════════════════════════════════

def t_cockpit_has_no_settle_method():
    """cockpit نباید متدِ settle داشته باشد (ضمانتِ ب)."""
    assert not hasattr(BrainCockpit, "settle"), "cockpit نباید متد settle داشته باشد"
    assert not hasattr(BrainCockpit, "approve"), "cockpit نباید متد approve داشته باشد"


def t_cockpit_does_not_mutate_gate():
    """حتی دستکاریِ دستیِ صفِ cockpit، وضعیتِ effect در gate واقعی را تغییر نمی‌دهد."""
    gate, db = _gate()
    eid = gate.request("send", "msg-004", beat=1)
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Project-F", "تأییدِ hack", 0.0, effect_id=eid)
    # تلاشِ مهاجم: دستی status را به approved ست کن
    item = [a for a in cp._approval_queue if a.effect_id == eid][0]
    item.status = "approved"   # دستکاریِ مستقیم
    # ولی gate واقعی هنوز pending است (cockpit چیزی نتوانسته settle کند)
    assert gate.status_of(eid) == "pending", \
        "cockpit نباید بتواند وضعیتِ gate را تغییر دهد"
    # و بعد از reconcile، cockpit دوباره به حقیقتِ gate برمی‌گردد
    cp._reconcile_effect_status()
    assert item.status == "pending", "reconcile باید دستکاری را برگرداند به حقیقتِ gate"


def t_reconcile_readonly_does_not_settle():
    """فراخوانیِ مکررِ _reconcile_effect_status هرگز effect را settle نمی‌کند."""
    gate, db = _gate()
    eid = gate.request("publish", "post-002", beat=1)
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    cp.add_approval("Project-F", "تأیید", 0.0, effect_id=eid)
    for _ in range(10):
        cp._reconcile_effect_status()
        cp.approval_queue_html()
    assert gate.status_of(eid) == "pending", "reconcile (خواندن) نباید settle کند"


# ════════════════════════════════════════════════════════════════════════════════
# (واگرایی-پیشگیری) بدونِ status_fn → صف صریحاً shadow است
# ════════════════════════════════════════════════════════════════════════════════

def t_shadow_without_status_fn():
    """بدونِ effect_status_fn → is_shadow=True و HTML برچسبِ shadow دارد."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")  # بدونِ status_fn
    assert cp.is_shadow is True
    cp.add_approval("Project-F", "تأییدِ درفت", 0.0)
    html = cp.approval_queue_html()
    assert "shadow" in html, "صفِ shadow باید صریحاً برچسب بخورد"


def t_shadow_never_shows_approved():
    """بدونِ status_fn، حتی بعد از reconcile، آیتم هرگز «approved» نمی‌شود."""
    cp = BrainCockpit(state_dir=ENV["ops"] / "state")
    cp.add_approval("Project-F", "تأیید", 0.0, effect_id="fake-eid")
    cp._reconcile_effect_status()
    item = cp._approval_queue[0]
    assert item.status == "pending", "shadow نباید خودسرانه approved شود"


def t_with_status_fn_not_shadow():
    """با status_fn → is_shadow=False (نمایِ واقعی، نه shadow)."""
    gate, _ = _gate()
    cp = BrainCockpit(state_dir=ENV["ops"] / "state",
                      effect_status_fn=gate.status_of)
    assert cp.is_shadow is False


# ════════════════════════════════════════════════════════════════════════════════
# خطِ قرمز: cockpit همچنان import از *_gate/chrono ندارد
# ════════════════════════════════════════════════════════════════════════════════

def t_cockpit_no_production_import():
    """cockpit.py نباید import از *_gate/chrono/opslib داشته باشد."""
    src = Path(BrainCockpit.__module__).absolute()
    cp_path = _OPS / "brain" / "cockpit.py"
    code = cp_path.read_text("utf-8")
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "import opslib",
                 "from opslib"]
    for f in forbidden:
        assert f not in code, f"خطِ قرمز: {f} نباید در cockpit.py باشد"


# ─── helper برای freeze/unfreeze ──────────────────────────────────────────────
def opslib_freeze():
    import opslib
    opslib.freeze("test-l6")


def opslib_unfreeze():
    import opslib
    try:
        opslib.FREEZE_FLAG.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    failed = harness.run([
        # (الف) همگامی
        ("pending در gate → pending در cockpit", t_pending_in_gate_shows_pending_in_cockpit),
        ("settled در gate → approved در cockpit", t_settled_in_gate_shows_approved_in_cockpit),
        ("releasable در gate → approved در cockpit", t_releasable_in_gate_shows_approved_in_cockpit),
        ("refused در gate → denied در cockpit", t_refused_in_gate_shows_denied_in_cockpit),
        ("HTML قبل از نمایش reconcile می‌کند", t_html_reconciles_before_display),
        # (ب) shadow settle نمی‌کند
        ("cockpit متدِ settle ندارد", t_cockpit_has_no_settle_method),
        ("cockpit وضعیتِ gate را تغییر نمی‌دهد", t_cockpit_does_not_mutate_gate),
        ("reconcile فقط‌خواندنی است (settle نمی‌کند)", t_reconcile_readonly_does_not_settle),
        # واگرایی-پیشگیری
        ("بدونِ status_fn → shadow", t_shadow_without_status_fn),
        ("shadow هرگز approved نشان نمی‌دهد", t_shadow_never_shows_approved),
        ("با status_fn → نه shadow", t_with_status_fn_not_shadow),
        # خطِ قرمز
        ("cockpit import از *_gate ندارد", t_cockpit_no_production_import),
    ])
    sys.exit(1 if failed else 0)
