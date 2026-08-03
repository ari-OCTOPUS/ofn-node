"""test_owner_answers_2026_07_27.py — سه رأیِ مالک، پیاده‌شده و قفل‌شده.

مالک همان روز سه تصمیم داد و این فایل نمی‌گذارد پیاده‌سازی از رأی منحرف شود:

  ۱) **`/lead` تا مرزِ ارسال** — «کامل تا مرزِ ارسال»: قیمت و پیش‌نویس آماده، دکمهٔ
     «بفرست» هم باشد، ولی **تا او نزند چیزی نرود**. سخت‌ترین قید همین است.
  ۲) **سکوتِ ۰ تا ۷** — فقط جریانِ محیطی؛ پاسخِ مستقیم و هشدارِ حیاتی هرگز.
  ۳) **«اول فقط منقضی‌ها»** — از ۴۸ رأیِ باز، آن‌هایی که واقعیت جوابشان را داده،
     با شاهدِ فیزیکی. و فایلِ مالک هرگز بازنویسی نمی‌شود (قانونِ اساسی §۷).
"""
import datetime
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("owner-answers")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                 # noqa: E402
import approval_channel as ac  # noqa: E402
import quote_cmd as qc        # noqa: E402
import verdict_probe as vp    # noqa: E402


# ─── ۱: `/lead` — تا مرزِ ارسال، نه یک قدم جلوتر ────────────────────────────
def t_the_quote_module_can_never_send_anything():
    """قیدِ اصلیِ رأیِ مالک. اگر روزی مسیرِ ارسالی در این ماژول پیدا شود، «تا مرزِ
    ارسال» شکسته است."""
    import ast
    tree = ast.parse(Path(qc.__file__).read_text("utf-8"))
    banned = {"urllib", "requests", "socket", "http", "smtplib", "subprocess"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("send", "post", "sendMessage", "mark_sent"):
        assert d not in called, f"مسیرِ ارسال در ماژولِ کوت: {d}"


def t_parse_understands_persian_digits_and_partial_input():
    r = qc.parse("/lead آشپزخانه ۳خوابه | ۱۲۰ | interior | standard | residential")
    assert r["ok"] and r["fields"]["size_m2"] == 120.0, r
    assert r["fields"]["scope"].startswith("آشپزخانه"), r
    r2 = qc.parse("/lead حمام | 25")          # فقط دو فیلدِ لازم
    assert r2["ok"] and r2["fields"]["size_m2"] == 25.0, r2
    assert "area_type" not in r2["fields"], "فیلدِ نداده نباید ساخته شود"


def t_a_quote_without_scope_or_size_asks_instead_of_guessing():
    for bad in ("/lead", "/lead   ", "/lead فقط شرح", "/lead | 100"):
        r = qc.parse(bad)
        assert not r["ok"], f"ورودیِ ناقص قبول شد: {bad!r}"


def t_flag_off_returns_a_message_not_a_quote():
    os.environ.pop(qc.FLAG, None)
    body, kb = qc.quote("/lead حمام | 25")
    assert kb is None and "خاموش" in body, body


def t_the_send_button_records_a_verdict_it_does_not_send():
    """گاردِ متنی روی مسیرِ callback: دکمه باید رأی ثبت کند، نه ارسال."""
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    i = src.index('if verb == "qt"')
    block = src[i:i + 1400]
    assert "_record_approval" in block, "دکمهٔ بفرست رأی ثبت نمی‌کند"
    assert "هنوز چیزی نرفته" in block, "به مالک نمی‌گوید که ارسال نشده"
    for d in ("mark_sent", "outbound", "transport"):
        assert d not in block, f"مسیرِ ارسالِ واقعی در callback: {d}"


def t_the_quote_verb_is_routed():
    """درسِ همان روز: دکمه‌ای که فعلش در جدولِ dispatch نباشد مرده است.

    ⚠️ ۰۷-۳۱: پنجرهٔ ثابتِ ۳۰۰۰ کاراکتری قلابی بود — با رشدِ طبیعیِ
    `_handle_callback` (شاخه‌های نو قبل از qt) تستِ سبز قرمز می‌شد بی‌آنکه
    سیمی قطع شده باشد. سنجهٔ درست: کلِ بدنهٔ همان تابع، نه N کاراکترِ اول."""
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    i = src.index("def _handle_callback")
    j = src.find("\ndef ", i + 1)
    body = src[i:j if j != -1 else len(src)]
    assert '"qt"' in body, "فعلِ qt مسیر ندارد — دکمه‌ها مرده‌اند"


# ─── ۲: سکوتِ ۰ تا ۷ ────────────────────────────────────────────────────────
def t_quiet_window_matches_the_owners_answer():
    os.environ.pop("OCTOPUS_QUIET_FROM", None)
    os.environ.pop("OCTOPUS_QUIET_TO", None)
    assert ac._quiet_hours() == (0, 7), ac._quiet_hours()
    for h in (0, 3, 6):
        assert ac._quiet_now(datetime.datetime(2026, 7, 27, h)), f"ساعت {h} باید ساکت باشد"
    for h in (7, 8, 14, 22, 23):
        assert not ac._quiet_now(datetime.datetime(2026, 7, 27, h)), f"ساعت {h} نباید ساکت باشد"


def t_a_window_crossing_midnight_still_works():
    os.environ["OCTOPUS_QUIET_FROM"] = "22"
    os.environ["OCTOPUS_QUIET_TO"] = "7"
    try:
        assert ac._quiet_now(datetime.datetime(2026, 7, 27, 23))
        assert ac._quiet_now(datetime.datetime(2026, 7, 27, 3))
        assert not ac._quiet_now(datetime.datetime(2026, 7, 27, 12))
    finally:
        os.environ.pop("OCTOPUS_QUIET_FROM", None)
        os.environ.pop("OCTOPUS_QUIET_TO", None)


def t_hostile_quiet_env_falls_back_to_the_owners_answer():
    for bad in ("abc", "-1", "99", ""):
        os.environ["OCTOPUS_QUIET_FROM"] = bad
        assert ac._quiet_hours()[0] == 0, f"{bad!r} → {ac._quiet_hours()}"
    os.environ.pop("OCTOPUS_QUIET_FROM", None)


def t_vital_streams_are_never_silenced():
    """ترس، هشدار و قلب باید نیمه‌شب هم برسند."""
    for s in ("cortisol", "alert", "heart"):
        assert s in ac._NEVER_QUIET, f"جریانِ حیاتیِ {s} می‌تواند ساکت شود"
    for s in ("brain", "discovery", "map", "summary"):
        assert s not in ac._NEVER_QUIET, f"جریانِ محیطیِ {s} از سکوت معاف شده"


def t_a_direct_reply_is_never_silenced():
    """گاردِ ساختاری: شرطِ سکوت فقط داخلِ شاخه‌ای که `chat_id is None` می‌خواهد.

    ۲۰۲۶-۰۷-۲۸ — نسخهٔ اول این گارد دنبالِ رشتهٔ **عیناً**
    `"if chat_id is None and stream:"` در پنجرهٔ ۵۰۰ کاراکتریِ قبل می‌گشت. وقتی
    فیکسِ تاپیک یک شرطِ دیگر جلویش گذاشت (`thread is None and chat_id is None
    and stream`)، تست قرمز شد در حالی که **رفتار حتی سخت‌گیرتر شده بود**.

    آن قرمز بی‌ضرر نبود: در شواهدِ markerِ capability به‌عنوان «۲ قرمزِ از قبل
    موجود» ثبت شد و مارکر با وجودش نوشته شد — یعنی یک تستِ کهنه تبدیل شد به
    مجوزِ عبور از گیتِ پول. گاردی که به **نحوِ نوشتن** حساس باشد، دیر یا زود
    یا دروغِ قرمز می‌گوید یا سبزِ دروغ می‌سازد.

    حالا **ناوردی** سنجیده می‌شود نه املا: هر `if`ی که `_quiet_now()` را صدا
    می‌زند باید جایی در زنجیرهٔ اجدادش شرطی داشته باشد که `chat_id` را با None
    مقایسه می‌کند. هر بازنویسی‌ای که این را نگه دارد، سبز می‌ماند.
    """
    import ast
    tree = ast.parse(Path(ac.__file__).read_text("utf-8"))
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node

    def _guards_chat_id(test) -> bool:
        for n in ast.walk(test):
            if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) \
                    and n.left.id == "chat_id" \
                    and any(isinstance(c, ast.Constant) and c.value is None
                            for c in n.comparators):
                return True
        return False

    found = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if "_quiet_now" not in ast.dump(node.test):
            continue
        found += 1
        cur, ok = node, False
        while cur in parent and not ok:
            cur = parent[cur]
            if isinstance(cur, ast.If) and _guards_chat_id(cur.test):
                ok = True
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                break          # از مرزِ تابع فراتر نرو
        assert ok, ("سکوت خارج از شاخه‌ای است که chat_id را چک می‌کند — "
                    "پاسخِ مستقیم را هم می‌خورد")
    assert found, "شرطِ سکوت (_quiet_now) اصلاً پیدا نشد — گارد بی‌هدف شده"


# ─── ۳: فقط منقضی‌ها ────────────────────────────────────────────────────────
def t_the_probe_never_rewrites_the_owners_file():
    """قانونِ اساسی §۷: به نوتِ انسانی فقط append."""
    import ast
    tree = ast.parse(Path(vp.__file__).read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("write_text", "write_bytes", "unlink", "replace", "open"):
        assert d not in called, f"پروب فایل را می‌نویسد: {d}"


def t_a_broken_probe_stays_silent_rather_than_claiming_expiry():
    """ادعای غلطِ انقضا بدتر از ندیدن است — مالک را به بستنِ چیزِ باز ترغیب می‌کند."""
    real = dict(vp.PROBES)
    def _boom():
        raise RuntimeError("پروب خراب")
    vp.PROBES["VQ-LOOP-001"] = ("x", _boom)
    try:
        out = vp.expired()
        assert all(e["id"] != "VQ-LOOP-001" for e in out), out
    finally:
        vp.PROBES.clear()
        vp.PROBES.update(real)


def t_every_expired_row_carries_physical_evidence():
    for e in vp.expired():
        assert e.get("evidence") and len(e["evidence"]) > 5, e
        assert e["id"].startswith("VQ-"), e


def t_the_card_says_it_will_not_close_anything():
    body = vp.card()
    assert "بستن" in body, "کارت نمی‌گوید بستن دستِ مالک است"
    assert isinstance(body, str) and len(body) <= 3800


def t_a_row_that_is_not_open_is_never_reported_expired():
    """اگر مالک قبلاً بسته باشد، دوباره نشانش نده."""
    ids = {r["id"] for r in vp.open_rows()}
    for e in vp.expired():
        assert e["id"] in ids, f"{e['id']} باز نیست ولی منقضی گزارش شد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_owner_answers: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
