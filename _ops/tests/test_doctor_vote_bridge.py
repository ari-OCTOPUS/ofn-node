"""test_doctor_vote_bridge.py — پل رأی دکتر (C-008): دکمه باید رأی شود، نه «نادیده».

۲۰۲۶-۰۸-۱۵: مالک دکمه‌های کارت دکتر را تپ می‌کرد و center «نادیده» جواب
می‌داد — فرمتِ سه‌بخشیِ `ok|no:<gate>:<mission_id>` در واژگانِ جدولِ verb
نبود و گوشِ دکتر (poll) هم مالِ توکنِ مشترک نیست. پلِ امشب: intercept
قبل از جدولِ verb و ریختن به سازهٔ خودِ دکتر (ingest_external → accept).

دو پروب، هر دو صادقانه دربارهٔ ادعایشان:
  A) مسیرِ واقعیِ ثبت (رفتاری): cbq واقعی‌شکل به TelegramChannel.ingest_external
     روی state آزمایشی → tg-inbox.jsonq باید یک رأیِ approved داشته باشد؛
     هم‌callback_id دوباره → dedupe (kept=0).
  B) گاردِ مسیریابی (پروبِ سورس، هم‌فلسفهٔ test_callback_routing ولی فقط
     همین را ادعا می‌کند): center باید الگوی سه‌بخشی را قبل از جدولِ verb
     intercept کند و _doctor_ingest را صدا بزند.
"""
import json
import re
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
harness.setup("doctor-vote-bridge")

_VAULT = _HERE.parent.parent
# چرا از مسیرِ فایل؟ `_ops/doctor` پکیجِ کامل است و `OCTOPUS-DOCTOR/doctor`
# را سایه می‌زند — همان دامی که پل باید در پروسهٔ مرکز از آن بگذرد (C-008).
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location(
    "_octopus_doctor_channel_test",
    _VAULT / "OCTOPUS-DOCTOR" / "doctor" / "channel.py")
_mod = _ilu.module_from_spec(_spec)
sys.modules["_octopus_doctor_channel_test"] = _mod   # دستورِ رسمی importlib
_spec.loader.exec_module(_mod)
TelegramChannel = _mod.TelegramChannel

_CENTER = _HERE.parent / "telegram_center" / "center.py"


def _cbq(cb_id="cb-1", data="ok:intent:owner-gate-sign-d1-manifest", voter=7):
    return {"id": cb_id, "data": data, "from": {"id": voter}}


# ---------------------------------------------------------------- A) رفتاری

def test_vote_lands_in_inbox(tmp_path):
    ch = TelegramChannel(str(tmp_path))
    kept = ch.ingest_external([_cbq()])
    assert len(kept) == 1 and kept[0].approved is True
    inbox = tmp_path / "tg-inbox.jsonl"
    rec = json.loads(inbox.read_text("utf-8").splitlines()[0])
    assert rec["mission_id"] == "owner-gate-sign-d1-manifest"
    assert rec["gate"] == "intent" and rec["approved"] is True


def test_same_callback_id_deduped(tmp_path):
    ch = TelegramChannel(str(tmp_path))
    assert len(ch.ingest_external([_cbq(cb_id="cb-9")])) == 1
    assert len(ch.ingest_external([_cbq(cb_id="cb-9")])) == 0   # ضدتکرار
    assert len((tmp_path / "tg-inbox.jsonl").read_text("utf-8").splitlines()) == 1


def test_channel_accepts_any_threepart_ok_no(tmp_path):
    """قراردادِ منجمدِ دکتر: پارسرِ Vote هر سه‌بخشیِ ok|no را می‌پذیرد.
    محدودسازیِ gate به intent/diff در **هوکِ مرکز** است (پروبِ سورس بالا)،
    نه در لایهٔ کانال — این تست فقط همین واقعیت را قفل می‌کند."""
    ch = TelegramChannel(str(tmp_path))
    kept = ch.ingest_external([_cbq(cb_id="cb-2", data="ok:some-other-gate:mission")])
    assert len(kept) == 1 and kept[0].gate == "some-other-gate"


# ------------------------------------------------------- B) گاردِ مسیریابی

def test_center_intercepts_doctor_pattern_before_verb_table():
    src = _CENTER.read_text(encoding="utf-8")
    assert "_doctor_ingest(cbq)" in src, "پل صدا زده نمی‌شود"
    assert re.search(r"len\(_doc\) == 3 and _doc\[0\] in \(\"ok\", \"no\"\)", src), \
        "الگوی سه‌بخشیِ دکتر تشخیص داده نمی‌شود"
    hook_pos = src.index("پلِ رأی دکتر (C-008")
    table_pos = src.index('if verb in ("lcall", "ldraft")')
    assert hook_pos < table_pos, "intercept باید قبل از جدولِ verb باشد تا تصادم نشود"


def test_center_helper_has_testable_state_seam():
    src = _CENTER.read_text(encoding="utf-8")
    assert "def _doctor_ingest(self, cbq: dict, state_dir" in src, \
        "state_dir قابل‌تزریق — الگوی OpsRoot — برای تستِ پل"
