"""test_vault_updater.py — propose-only patch engine + gate (جلسه ۴۶، اسپکِ مالک).

سبکِ credential-panel: تستِ واحدِ متعدد، fail-closed. cognition≠effect: proposer هرگز
دیسک نمی‌نویسد؛ gate proposalِ ناامن را رد می‌کند. Ring×risk×envelope، ریل‌های سخت.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("vault-updater")

import vault_updater as vu        # noqa: E402
import vault_updater_gate as gate  # noqa: E402

ENV_OK = ["00 - Inbox/", "03 - Projects/", "07 - Knowledge/"]


def t_a_ring_map_correct():
    assert vu.ring_for("CLAUDE.md") == 0
    assert vu.ring_for("07 - Knowledge/genome-system/ledger/ledger.jsonl") == 0
    assert vu.ring_for("06 - Architecture Maps/Property Schema.md") == 1
    assert vu.ring_for("07 - Knowledge/_Index - Knowledge.md") == 1
    assert vu.ring_for("03 - Projects/Mining/PROJECT.md") == 1
    assert vu.ring_for("07 - Knowledge/cellular-systems/note.md") == 3
    assert vu.ring_for("00 - Inbox/2026-07-11 x.md") == 4


def t_b_ring0_never_written_hold():
    p = vu.propose("یه فکت", provenance="chat",
                   target_path="CLAUDE.md", candidates=[{"path": "CLAUDE.md", "summary": "x"}])
    assert p["commit_mode"] == "HOLD"   # ژنوم فقط flag
    assert gate.validate(p)[0]


def t_c_ring1_gate_never_auto():
    p = vu.propose("یه لینکِ نو به ایندکس",
                   provenance="chat", target_path="07 - Knowledge/_Index - Knowledge.md",
                   candidates=[{"path": "07 - Knowledge/_Index - Knowledge.md", "summary": "ایندکس"}],
                   autonomy_envelope=ENV_OK)
    assert p["commit_mode"] == "GATE" and "human_prompt" in p
    assert gate.validate(p)[0]


def t_d_ring4_low_auto():
    p = vu.propose("یه یادداشتِ کوتاهِ inbox", provenance="telegram",
                   target_path="00 - Inbox/2026-07-11 note.md",
                   candidates=[{"path": "00 - Inbox/old.md", "summary": "چیزِ دیگر"}],
                   autonomy_envelope=ENV_OK)
    assert p["commit_mode"] == "AUTO" and p["risk"] == "LOW"
    assert gate.validate(p)[0]


def t_e_domain_low_in_envelope_auto_else_gate():
    inside = vu.propose("نکتهٔ دانشیِ ساده", provenance="chat",
                        target_path="07 - Knowledge/note.md",
                        candidates=[{"path": "07 - Knowledge/x.md", "summary": "غیرمرتبط"}],
                        autonomy_envelope=ENV_OK)
    assert inside["commit_mode"] == "AUTO"
    outside = vu.propose("نکتهٔ دانشیِ ساده", provenance="chat",
                         target_path="09 - People/someone.md",
                         candidates=[{"path": "09 - People/y.md", "summary": "غیرمرتبط"}],
                         autonomy_envelope=ENV_OK)   # 09 خارج از envelope
    assert outside["commit_mode"] == "GATE"


def t_f_projectf_always_hold():
    for raw, path in [("چیزی دربارهٔ اونلی فنز", "00 - Inbox/x.md"),
                      ("یه فکت", "03 - Projects/اونلی فنز/note.md")]:
        p = vu.propose(raw, provenance="chat", target_path=path,
                       candidates=[{"path": path, "summary": "x"}], autonomy_envelope=ENV_OK)
        assert p["status"] == "HOLD" and p["commit_mode"] == "HOLD"
        assert gate.validate(p)[0]


def t_g_pii_and_secret_hold_critical():
    p = vu.propose("رمزم password: abc123 و کیفِ 0x1234567890abcdef1234", provenance="chat",
                   target_path="00 - Inbox/x.md", candidates=[{"path": "00 - Inbox/x.md", "summary": "x"}])
    assert p["status"] == "HOLD"
    # حتی اگر به‌جای HOLD یک OK با CRITICAL بیاید، gate آن را از AUTO بازمی‌دارد:
    c = vu.classify("secret wallet seed phrase", "07 - Knowledge/note.md")
    assert c["sensitivity"] == "high"
    assert vu.risk_flag(c, "07 - Knowledge/note.md", False) == "CRITICAL"


def t_h_no_provenance_holds():
    p = vu.propose("یه فکت", provenance="", target_path="00 - Inbox/x.md",
                   candidates=[{"path": "00 - Inbox/x.md", "summary": "x"}])
    assert p["status"] == "HOLD" and "منبع" in p["rationale"]


def t_i_dedup_merges_not_creates():
    cands = [{"path": "07 - Knowledge/rl.md",
              "summary": "reinforcement learning agents reward policy value"}]
    p = vu.propose("reinforcement learning agents reward policy value function",
                   provenance="chat", target_path="07 - Knowledge/new.md",
                   candidates=cands, autonomy_envelope=ENV_OK, tau=0.4)
    patch = json.loads(p["patch"])
    assert p["dedup"]["matched_path"] == "07 - Knowledge/rl.md"
    assert patch["op"] == "append"          # merge، نه create (ضدِ تکرار)
    assert p["ledger_entry"]["op"] == "append"


def t_j_never_writes_disk():
    """proposer هرگز به دیسک نمی‌نویسد (cognition≠effect). خروجی فقط dict است."""
    src = (Path(__file__).resolve().parents[1] / "vault_updater.py").read_text("utf-8")
    for banned in ("open(", ".write_text(", ".write(", "LockedJson", "mkdir", "os.replace"):
        # فقط در بدنهٔ اجرایی (نه داکِ‌استرینگ): چک می‌کنیم هیچ نوشتنی نیست
        assert banned not in src, f"proposer نباید بنویسد: {banned}"


def t_k_gate_rejects_unsafe_proposals():
    """gate مستقل: proposalِ دستکاری‌شدهٔ ناامن رد می‌شود (defense-in-depth)."""
    base = vu.propose("نکتهٔ ساده", provenance="chat", target_path="00 - Inbox/x.md",
                      candidates=[{"path": "00 - Inbox/x.md", "summary": "x"}],
                      autonomy_envelope=ENV_OK)
    assert gate.validate(base)[0]
    # Ring1 با AUTOِ جعلی → رد
    bad = dict(base); bad["classification"] = dict(base["classification"], target_ring=1)
    bad["commit_mode"] = "AUTO"
    assert gate.validate(bad)[0] is False
    # CRITICAL + AUTO → رد
    bad2 = dict(base, risk="CRITICAL", commit_mode="AUTO")
    assert gate.validate(bad2)[0] is False
    # opِ مخرب → رد
    bad3 = dict(base, patch=json.dumps({"op": "delete", "path": "x"}))
    assert gate.validate(bad3)[0] is False
    # provenance جعل‌شده (خالی) → رد
    bad4 = dict(base); bad4["ledger_entry"] = dict(base["ledger_entry"], provenance="")
    assert gate.validate(bad4)[0] is False


def t_l_idempotent_same_input_same_hash():
    a = vu.propose("عینِ همین متن", provenance="chat", target_path="00 - Inbox/x.md",
                   candidates=[{"path": "00 - Inbox/x.md", "summary": "x"}], existing_body="قبلی")
    b = vu.propose("عینِ همین متن", provenance="chat", target_path="00 - Inbox/x.md",
                   candidates=[{"path": "00 - Inbox/x.md", "summary": "x"}], existing_body="قبلی")
    assert a["ledger_entry"]["after_hash"] == b["ledger_entry"]["after_hash"]   # تکرارپذیر


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_vault_updater: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
