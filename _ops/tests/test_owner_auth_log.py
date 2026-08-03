"""test_owner_auth_log — حرفِ مجوزِ مالک می‌ماند، ولی هرگز خودش عمل نمی‌شود.

دو قیدِ متضاد که هم‌زمان باید برقرار باشند:

  ۱) **ماندگاری.** تا امروز هیچ خطی از کد `OWNER_AUTH` را نمی‌شناخت؛ مجوزِ مالک
     فرّارترین دادهٔ کلِ سیستم بود — اگر ایجنتی ناظر نبود، تبخیر می‌شد.
  ۲) **بی‌عملی.** ماژولی که روی متنِ چت فلگ را بچرخاند، یک مجریِ خودکار است که
     ورودی‌اش جعل‌شدنی، فورواردشدنی و تزریق‌پذیر است. مسلح‌کردنِ فلگ عملِ استقرار
     است نه پیام.

قیدِ سومِ کم‌دیده‌تر: ادعای مجوز از کانالِ **ناشناس** هم باید ثبت شود — چون
خودش یک رویدادِ امنیتی است. رد کردنِ بی‌صدا یعنی حمله دیده نمی‌شود.
"""
import ast
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("owner-auth")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib             # noqa: E402
import owner_auth_log as oa   # noqa: E402


def _clear():
    try:
        oa._path().unlink()
    except OSError:
        pass


def _rows():
    try:
        return [json.loads(x) for x in oa._path().read_text("utf-8").splitlines() if x.strip()]
    except OSError:
        return []


# ─── ۱: هر پنج عبارتِ قرارداد شناخته می‌شود ────────────────────────────────
def t_every_contract_phrase_is_recognised():
    cases = {
        "OWNER_AUTH: COMMIT _ops/x.py": "COMMIT",
        "OWNER_AUTH: RESTART ORGANISM": "RESTART",
        "OWNER_AUTH: DEPLOY MASTER": "DEPLOY",
        "OWNER_AUTH: ARM FLAG OCTOPUS_WIRE_X": "ARM_FLAG",
        "OWNER_AUTH: TRAIN NOW": "TRAIN",
    }
    for text, kind in cases.items():
        hit = oa.parse(text)
        assert hit and hit["kind"] == kind, (text, hit)


def t_case_and_spacing_do_not_break_it():
    """مالک روی موبایل تایپ می‌کند — سخت‌گیریِ بی‌مورد یعنی مجوزِ گم‌شده."""
    for t in ("owner_auth: restart organism",
              "OWNER_AUTH:RESTART ORGANISM",
              "OWNER_AUTH:   ARM   FLAG   ABC",
              "لطفاً بزن — OWNER_AUTH: DEPLOY MASTER"):
        assert oa.parse(t) is not None, t


def t_ordinary_conversation_is_never_an_authorisation():
    for t in ("سلام", "", None, "OWNER", "AUTH: COMMIT", "درباره OWNER_AUTH بگو",
              "OWNER_AUTH: چیزی که نیست", "OWNER_AUTH: ARM"):
        assert oa.parse(t) is None, t


def t_the_flag_name_is_captured_not_swallowed():
    hit = oa.parse("OWNER_AUTH: ARM FLAG OCTOPUS_WIRE_TRAJECTORY_LOG")
    assert hit["arg"] == "OCTOPUS_WIRE_TRAJECTORY_LOG", hit


# ─── ۲: ماندگاری ──────────────────────────────────────────────────────────
def t_an_authorisation_survives_on_disk():
    """قلبِ ماژول: حرفِ نیمه‌شبِ مالک نباید تبخیر شود."""
    _clear()
    rec = oa.record("OWNER_AUTH: RESTART ORGANISM", chat_ok=True)
    assert rec and rec["written"] is True
    rows = _rows()
    assert len(rows) == 1 and rows[0]["kind"] == "RESTART"
    assert rows[0]["executed"] is False


def t_the_ledger_is_append_only():
    _clear()
    for i in range(3):
        oa.record(f"OWNER_AUTH: COMMIT p{i}", chat_ok=True)
    assert len(_rows()) == 3


def t_pending_shows_only_authenticated_unexecuted_ones():
    _clear()
    oa.record("OWNER_AUTH: COMMIT a", chat_ok=True)
    oa.record("OWNER_AUTH: COMMIT b", chat_ok=False)      # کانالِ ناشناس
    oa.record("OWNER_AUTH: COMMIT sk-" + "a" * 25, chat_ok=True)   # رد شده
    p = oa.pending()
    assert len(p) == 1 and p[0]["arg"] == "a", p


# ─── ۳: بی‌عملی — سخت‌ترین قید ────────────────────────────────────────────
def t_the_module_cannot_flip_a_flag_or_run_anything():
    """اگر این بشکند، متنِ چت به مجریِ استقرار وصل شده است."""
    tree = ast.parse(Path(oa.__file__).read_text("utf-8"))
    banned = {"subprocess", "os.system", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not ({b.split(".")[0] for b in banned} & imported), sorted(imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("system", "run", "Popen", "putenv", "setenv", "commit", "restart",
              "apply", "arm", "execv"):
        assert d not in called, f"ماژولِ ثبت عمل می‌کند: {d}"
    src = Path(oa.__file__).read_text("utf-8")
    assert "os.environ[" not in src, "ماژول محیط را می‌نویسد — یعنی فلگ را می‌چرخاند"


def t_the_reply_says_plainly_that_nothing_happened():
    """اگر جواب مبهم باشد، مالک باور می‌کند کاری شده. این بدترین حالت است."""
    rec = oa.record("OWNER_AUTH: ARM FLAG X", chat_ok=True)
    body = oa.ack(rec)
    assert "اجرایش نمی‌کنم" in body, body
    assert "ثبت شد" in body and "نکنی:" in body


def t_the_record_carries_a_warning_for_future_readers():
    """ردیف‌های این فایل ادعای مجوزند — خواننده‌ای در آینده نباید اشتباه بگیرد."""
    _clear()
    oa.record("OWNER_AUTH: COMMIT x", chat_ok=True)
    r = _rows()[0]
    assert "ادعای مجوز" in r["_note"] and "نه اجرا" in r["_note"], r


# ─── ۴: کانالِ ناشناس ─────────────────────────────────────────────────────
def t_a_claim_from_an_unknown_channel_is_recorded_not_dropped():
    """ردِ بی‌صدا یعنی حمله دیده نمی‌شود."""
    _clear()
    rec = oa.record("OWNER_AUTH: DEPLOY MASTER", chat_ok=False)
    assert rec["written"] is True
    assert _rows()[0]["chat_ok"] is False
    assert "قبول نیست" in oa.ack(rec)
    assert not oa.pending(), "ادعای ناشناس وارد صف شد"


# ─── ۵: راز ───────────────────────────────────────────────────────────────
def t_a_secret_shaped_argument_is_refused_and_never_stored():
    _clear()
    for bad in ("sk-" + "a" * 25, "12345678:AA" + "b" * 34, "a" * 40,
                "-----BEGIN PRIVATE KEY"):
        rec = oa.record(f"OWNER_AUTH: COMMIT {bad}", chat_ok=True)
        assert rec["rejected"] == "secret-shaped", bad
        raw = oa._path().read_text("utf-8")
        assert bad not in raw, f"راز روی دیسک نشست: {bad[:12]}"


def t_the_card_never_echoes_an_argument_raw():
    _clear()
    oa.record("OWNER_AUTH: ARM FLAG <script>x</script>", chat_ok=True)
    body = oa.card()
    assert "<script>" not in body


def t_the_card_is_useful_when_empty():
    _clear()
    body = oa.card()
    assert "OWNER_AUTH" in body and "نکنی:" in body


def t_a_broken_disk_does_not_lose_the_reply():
    """اگر ثبت نشد، مالک باید همان لحظه بداند — نه اینکه فکر کند ثبت شد."""
    real = oa._path
    try:
        oa._path = lambda: Path("Z:/nope/owner-auth.jsonl")
        rec = oa.record("OWNER_AUTH: COMMIT x", chat_ok=True)
        assert rec["written"] is False, rec
    finally:
        oa._path = real


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_owner_auth_log: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
