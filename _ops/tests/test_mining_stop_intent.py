"""test_mining_stop_intent — تستِ مکانیزمِ ثبتِ نیتِ توقف (D-014).

الگو: test_epoch_guard.py — توابع t_، assertion صریح، بدون pytest.
فایل حالت در tmp نگه داشته می‌شود، هرگز داخلِ ولتِ زنده نمی‌نویسد.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402
ENV = harness.setup("mining-stop-intent")

_OPS = harness.REAL_VAULT / "_ops"
_LEGS = _OPS / "legs"
for _p in (str(_OPS), str(_LEGS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mining_stop_intent as msi  # noqa: E402

# اطمینان: تست‌ها فایل حالت را در tmp نگه دارند
_STATE_DIR = Path(ENV["OPS_DIR"]) / "state"


def _set_tmp_state():
    """مسیر فایل حالت را به tmpdir هدایت کن."""
    p = _STATE_DIR / "mining-stop-intent.json"
    os.environ["OCTOPUS_MINING_STOP_INTENT_FILE"] = str(p)
    return p


# ─── ۱: ثبت نیت ────────────────────────────────────────────────────────────

def t_register_creates_an_intent():
    """بعد از register_stop_intent، latest_intent وجود دارد."""
    p = _set_tmp_state()
    try:
        result = msi.register_stop_intent(reason="تست")
        st = msi.status()
        assert st["latest_intent"] is not None, "latest_intent نباید None باشد"
        assert st["latest_intent"]["reason"] == "تست"
        assert st["total_intents"] == 1
    finally:
        p.unlink(missing_ok=True)


# ─── ۲: صادتِ ۰ تأیید ──────────────────────────────────────────────────────

def t_zero_acks_honestly_reported():
    """stop_card_text وقتی acked_count==0 حاوی ۰ نود تأیید کرد، نه متوقف/خوابید/خاموش.

    دقت: عددِ صفر را از خط آخرِ کارت بخوان (نه از timestamp).
    """
    p = _set_tmp_state()
    try:
        msi.register_stop_intent(reason="تست صادت")
        card = msi.stop_card_text()
        assert "تأیید" in card, f"کار باید حاوی «تأیید» باشد: {card}"
        # خط آخر باید حاوی «0 نود» یا «۰ نود» باشد
        lines = card.strip().split("\n")
        ack_line = lines[-1]
        assert ("0 نود" in ack_line or "۰ نود" in ack_line), \
            f"خط آخر باید حاوی صفر باشد: {ack_line}"
        assert "1 نود" not in ack_line and "۱ نود" not in ack_line, \
            f"خط آخر نباید حاوی ۱ باشد: {ack_line}"
        # وانمود نکند که نودها خوابیدند
        for bad_word in ("متوقف شد", "خوابید", "خاموش شد", "متوقف شدند"):
            assert bad_word not in card, f"کار نباید حاوی «{bad_word}» باشد: {card}"
    finally:
        p.unlink(missing_ok=True)


# ─── ۳: بدون نیت ────────────────────────────────────────────────────────────

def t_no_intent_means_honest_empty():
    """وقتی نیت نیست، کارت می‌گوید هیچ نیت توقفی ثبت نشده."""
    p = _set_tmp_state()
    try:
        p.unlink(missing_ok=True)
        card = msi.stop_card_text()
        assert "هیچ نیتِ توقفی ثبت نشده" in card, f"منتظر: «هیچ نیتِ توقفی ثبت نشده» — گرفت: {card}"
    finally:
        p.unlink(missing_ok=True)


# ─── ۴: تأیید نود ──────────────────────────────────────────────────────────

def t_ack_increments_count():
    """بعد از acknowledge، acked_count می‌شود ۱."""
    p = _set_tmp_state()
    try:
        msi.register_stop_intent(reason="تست ack")
        st = msi.acknowledge("OPI-01")
        assert st["acked_count"] == 1, f"acked_count باید ۱ باشد: {st['acked_count']}"
        card = msi.stop_card_text()
        lines = card.strip().split("\n")
        ack_line = lines[-1]
        assert ("1 نود" in ack_line or "۱ نود" in ack_line), \
            f"خط آخر باید حاوی ۱ باشد: {ack_line}"
    finally:
        p.unlink(missing_ok=True)


# ─── ۵: نوشتن اتمیک ───────────────────────────────────────────────────────

def t_atomic_write_leaves_no_tmp():
    """بعد از register_stop_intent، هیچ فایل *.tmpای نمانده."""
    p = _set_tmp_state()
    try:
        msi.register_stop_intent(reason="تست اتمیک")
        tmps = list(p.parent.glob("*.json.tmp"))
        assert len(tmps) == 0, f"فایل tmp مانده: {[t.name for t in tmps]}"
    finally:
        p.unlink(missing_ok=True)
        for t in p.parent.glob("*.json.tmp"):
            t.unlink(missing_ok=True)


# ─── ۶: fail-soft ──────────────────────────────────────────────────────────

def t_corrupted_file_is_fail_soft():
    """اگر فایل حالت خراب باشد، status() استثنا نمی‌اندازد."""
    p = _set_tmp_state()
    try:
        p.write_text("{خراب", "utf-8")
        st = msi.status()
        # باید چیزی برگرداند، نه crash
        assert isinstance(st, dict), f"status باید dict برگرداند: {type(st)}"
        card = msi.stop_card_text()
        assert isinstance(card, str), f"card باید str برگرداند: {type(card)}"
    finally:
        p.unlink(missing_ok=True)


# ─── ۷: سقف تاریخچه ────────────────────────────────────────────────────────

def t_history_capped_at_20():
    """۲۵ نیت ثبت کن؛ فقط ۲۰ نگه داشته می‌شوند."""
    p = _set_tmp_state()
    try:
        for i in range(25):
            msi.register_stop_intent(reason=f"batch-{i}")
        st = msi.status()
        assert st["total_intents"] == 20, f"باید ۲۰ باشد: {st['total_intents']}"
        # آخرین باید batch-24 باشد
        assert st["latest_intent"]["reason"] == "batch-24", \
            f"آخرین نیت باید batch-24 باشد: {st['latest_intent']['reason']}"
    finally:
        p.unlink(missing_ok=True)


# ─── ۸: پایه مثبت ──────────────────────────────────────────────────────────

def t_acked_makes_card_show_count():
    """وقتی ۲ نود تأیید کردند، کارت «۲ نود تأیید کرد» نشان می‌دهد."""
    p = _set_tmp_state()
    try:
        msi.register_stop_intent(reason="تست ۲ ack")
        msi.acknowledge("OPI-01")
        msi.acknowledge("OPI-02")
        card = msi.stop_card_text()
        lines = card.strip().split("\n")
        ack_line = lines[-1]
        assert ("2 نود" in ack_line or "۲ نود" in ack_line), \
            f"خط آخر باید حاوی ۲ باشد: {ack_line}"
        assert "تأیید" in card, f"کار باید حاوی «تأیید» باشد: {card}"
    finally:
        p.unlink(missing_ok=True)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mining_stop_intent: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
