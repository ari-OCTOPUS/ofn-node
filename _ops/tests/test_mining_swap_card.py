"""test_mining_swap_card — کارتِ پیشنهادِ swapِ یک‌ضربه‌ای (D-016)."""
import os
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("swap-card")

_OPS = harness.REAL_VAULT / "_ops"
_LEGS = _OPS / "legs"
for _p in (str(_OPS), str(_LEGS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mining_swap_card as msc  # noqa: E402

# مسیرِ موقت برای فایلِ تصمیم‌ها
_TMP_JSON = Path(tempfile.mktemp(suffix=".json", prefix="test-sc-"))


def _cleanup():
    _TMP_JSON.unlink(missing_ok=True)
    _TMP_JSON.with_suffix(".tmp").unlink(missing_ok=True)


def _set_env():
    os.environ["OCTOPUS_MINING_SWAP_DECISION_FILE"] = str(_TMP_JSON)


def _clr_env():
    os.environ.pop("OCTOPUS_MINING_SWAP_DECISION_FILE", None)


# ─── ۱: propose_swap ──────────────────────────────────────────────────────
def t_propose_creates_pending_entry():
    """propose_swap یک ورودیِ pending می‌سازد."""
    try:
        _set_env()
        r = msc.propose_swap(from_coin="VRSC", to_coin="SAL",
                             reason="test", now=1700000000.0)
        assert r["from"] == "VRSC"
        assert r["to"] == "SAL"
        assert r["status"] == "pending"
        assert len(r.get("id", "")) >= 8
    finally:
        _clr_env()
        _cleanup()


def t_propose_is_idempotent_on_decision():
    """دو بار propose با همان from/to → همان id."""
    try:
        _set_env()
        r1 = msc.propose_swap(from_coin="VRSC", to_coin="SAL", now=1700000000.0)
        r2 = msc.propose_swap(from_coin="VRSC", to_coin="SAL", now=1700000100.0)
        assert r1["id"] == r2["id"], f"idempotency broken: {r1['id']} != {r2['id']}"
        assert r1["status"] == "pending"
    finally:
        _clr_env()
        _cleanup()


def t_propose_different_pair_creates_new():
    """from/to متفاوت → ورودیِ تازه."""
    try:
        _set_env()
        r1 = msc.propose_swap(from_coin="VRSC", to_coin="SAL", now=1700000000.0)
        r2 = msc.propose_swap(from_coin="BTC", to_coin="ETH", now=1700000000.0)
        assert r1["id"] != r2["id"]
    finally:
        _clr_env()
        _cleanup()


# ─── ۲: owner_approved ──────────────────────────────────────────────────
def t_owner_approved_changes_status():
    """تپِ مالک: status → owner_approved."""
    try:
        _set_env()
        r = msc.propose_swap(from_coin="VRSC", to_coin="SAL", now=1700000000.0)
        sid = r["id"]
        a = msc.owner_approved(sid, now=1700000100.0)
        assert a["status"] == "owner_approved"
        assert "approved_ts" in a
    finally:
        _clr_env()
        _cleanup()


def t_owner_approved_on_nonexistent_returns_error():
    """swap_id ناموجود → error."""
    try:
        _set_env()
        r = msc.owner_approved("nonexistent123")
        assert "error" in r
    finally:
        _clr_env()
        _cleanup()


# ─── ۳: owner_approval_text (صداقت) ──────────────────────────────────────
def t_approval_text_says_registered_not_executed():
    """متنِ تأیید صادقانه: اجرا با خودت، نه اجرا شد."""
    txt = msc.owner_approval_text("any-id")
    assert "تأییدِ مالک ثبت شد" in txt
    assert "D-11" in txt
    assert "اجرا" in txt
    # نباید بگوید «swap اجرا شد»
    assert "swap اجرا شد" not in txt


def t_approval_text_does_not_promise_execution():
    """متنِ تأیید نباید وعدهٔ اجرا بدهد."""
    txt = msc.owner_approval_text("any-id")
    assert "در حال اجرا" not in txt
    assert "انجام شد" not in txt


# ─── ۴: card_text ────────────────────────────────────────────────────────
def t_card_text_shows_pending():
    """card_text پیشنهادِ pending را نشان می‌دهد."""
    try:
        _set_env()
        msc.propose_swap(from_coin="VRSC", to_coin="SAL", now=1700000000.0)
        txt = msc.card_text()
        assert "VRSC" in txt
        assert "SAL" in txt
        assert "یک تپ" in txt
    finally:
        _clr_env()
        _cleanup()


def t_card_text_empty_when_no_pending():
    """بدونِ pending → خالی."""
    try:
        _set_env()
        txt = msc.card_text()
        assert txt == ""
    finally:
        _clr_env()
        _cleanup()


def t_card_text_shows_callback_data():
    """card_text حاوی callback_data است (برای center.py)."""
    try:
        _set_env()
        r = msc.propose_swap(from_coin="A", to_coin="B", now=1700000000.0)
        txt = msc.card_text()
        assert f"mo:swap:{r['id']}" in txt
    finally:
        _clr_env()
        _cleanup()


# ─── ۵: no network / no wallet imports ───────────────────────────────────
def t_no_network_or_wallet_imports():
    """ماژول هیچ شبکه‌ای وارد نمی‌کند."""
    import ast
    tree = ast.parse(Path(msc.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "subprocess",
                             "paramiko", "fabric", "web3", "ethers"}), imported


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mining_swap_card: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
