"""test_owner_debt — جمله‌ای که وقتی نمی‌بیند نباید بگوید «چیزی منتظر نیست».

گامِ ۲۰ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C15).

سنجه‌های پذیرشِ سند:
  · تستِ واحد روی فیکسچرِ قطعی (عددِ زندهٔ امروز عمداً هاردکد نمی‌شود)
  · بدهیِ صفر ⇒ جمله تولید نشود
  · ذخیرهٔ ناخوانا ⇒ UNKNOWN، هرگز «۰ کارت منتظر»

و دو ناوردیِ روزِ اول که سند صریحاً می‌خواهد:
  · صفر نوشتن
  · صفر صداکنندهٔ تولیدی — «نوشتنِ جمله مهندسی است؛ فرستادنش رأی مالک است»

بارِ اصلی: `ineffective = decided - effected`. سنجشِ زندهٔ امروز ۲۱ تصمیم و
**صفر** اثر می‌دهد؛ اگر این تفریق کور شود، دقیقاً همان یافته‌ای که کلِ طرح از
آن آمده بی‌صدا می‌شود.
"""
import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("owner-debt")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import owner_debt as OD              # noqa: E402
import pending_card_recovery as pcr  # noqa: E402

NOW = 1_785_700_000.0
DAY = 86400.0

#: نشانه‌ای که اگر در جمله یا در dict ظاهر شود یعنی محتوای کارت نشت کرده.
LEAK = "MARKER-CARD-BODY-DO-NOT-RENDER"


def _fixture(records, verdicts=None):
    """یک `state_dir` کاملاً ایزوله. هرگز زیرِ درختِ زنده نیست."""
    root = Path(tempfile.mkdtemp(prefix="owner-debt-"))
    assert str(_OPS).lower() not in str(root).lower(), f"fixture inside live tree: {root}"
    assert "f:\\backup" not in str(root).lower(), f"fixture under the live vault: {root}"
    (root / "pulse").mkdir(parents=True)
    (root / "pulse" / "pending-cards.json").write_text(
        json.dumps(records, ensure_ascii=False), encoding="utf-8")
    if verdicts:
        con = pcr._rfc_con(root)   # نویسندهٔ خودشان ⇒ اسکیما تضمینی درست است
        try:
            for rid, v in verdicts.items():
                con.execute(
                    "INSERT OR REPLACE INTO rfc_decision"
                    "(rfc_id,verdict,revision,state,lease_owner,lease_until,receipt_id,"
                    "operation_key,updated_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                    (rid, v.get("verdict", "approve"), 1, v.get("state", "SUBMITTED"),
                     None, None, v.get("receipt_id", ""), v.get("operation_key"), 0))
            con.commit()
        finally:
            con.close()
    return root


def _cards(n_waiting, n_decided, waiting_age_s=DAY):
    out = {}
    for i in range(n_waiting):
        out[f"rfc:S{i}"] = {"kind": "rfc", "rfc_id": f"S{i}", "delivery": "SENT",
                            "decision": "SUBMITTED", "summary": LEAK,
                            "created_ts": str(int(NOW - waiting_age_s - i))}
    for i in range(n_decided):
        out[f"rfc:D{i}"] = {"kind": "rfc", "rfc_id": f"D{i}", "delivery": "SENT",
                            "decision": "DECIDED", "summary": LEAK,
                            "created_ts": str(int(NOW - 3600))}
    return out


def _tree_of_self():
    return ast.parse((_OPS / "owner_debt.py").read_text("utf-8"))


# ─── ۱: ناخوانا ⇒ UNKNOWN، هرگز صفر ────────────────────────────────────────
def t_absent_store_is_unknown_not_zero_waiting():
    """بریفی که وقتی نمی‌بیند می‌گوید «چیزی منتظر نیست» از سکوت بدتر است."""
    root = Path(tempfile.mkdtemp(prefix="owner-debt-absent-"))
    try:
        debt = OD.owner_debt(root, now=NOW)
        assert debt["known"] is False, f"ذخیرهٔ غایب known شمرده شد: {debt}"
        assert debt["reason"] == "store-absent", debt["reason"]
        assert "waiting" not in debt, f"UNKNOWN کلیدِ شمارشی دارد: {debt}"
        assert "نامعلوم" in debt["text"], debt["text"]
        assert "منتظر" not in debt["text"], f"UNKNOWN ادعای صف کرد: {debt['text']}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_corrupt_store_is_unknown_not_zero_waiting():
    """سنجهٔ پذیرشِ سند — و جایی که C1 به‌تنهایی کافی نیست.

    `pending_card_recovery._load_store()` استثنا را می‌بلعد و `{}` می‌دهد، و
    `fold()` خوانایی را فقط با `exists()` تعریف می‌کند. پس یک فایلِ **موجودِ
    خراب** از C1 «۰ کارت» بیرون می‌آید؛ این ماژول باید خودش جلویش را بگیرد.
    """
    root = Path(tempfile.mkdtemp(prefix="owner-debt-corrupt-"))
    try:
        (root / "pulse").mkdir(parents=True)
        (root / "pulse" / "pending-cards.json").write_text("{ NOT json ", encoding="utf-8")
        # اول اثبات کن که تلهٔ واقعی است: C1 روی همین فایل صفرِ تمیز می‌دهد.
        import lifecycle_fold as LF
        folded = LF.fold(root, now=NOW)
        assert folded["stalled"].get("value") == 0 and folded["readable"] is True, \
            f"پیش‌فرضِ این تست عوض شده — C1 دیگر روی فایلِ خراب صفر نمی‌دهد: {folded['stalled']}"

        debt = OD.owner_debt(root, now=NOW)
        assert debt["known"] is False, f"فایلِ خراب known شمرده شد: {debt}"
        assert debt["reason"] == "store-corrupt", debt["reason"]
        assert "waiting" not in debt, f"UNKNOWN کلیدِ شمارشی دارد: {debt}"
        assert "۰" not in debt["text"], f"UNKNOWN عددِ صفر رندر کرد: {debt['text']}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_fold_failure_is_unknown_not_zero():
    """اگر تاشدگی بمیرد، بریف باید «نمی‌دانم» بگوید نه «صفر»."""
    root = _fixture(_cards(2, 0))
    try:
        def _boom(state_dir, now=None):
            raise RuntimeError("ledger exploded")
        debt = OD.owner_debt(root, now=NOW, _fold=_boom)
        assert debt["known"] is False, debt
        assert debt["reason"] == "fold-error", debt["reason"]
        assert "waiting" not in debt, f"UNKNOWN کلیدِ شمارشی دارد: {debt}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_unknown_never_carries_a_count_key():
    """ناوردیِ ۳ (ارثِ `provenance`): ورودیِ غایب نباید به صفرِ بی‌صدا بدل شود."""
    for reason, unknown in ((r, OD._unknown(r)) for r in
                            ("store-absent", "store-corrupt", "fold-unknown", "fold-error")):
        for key in ("waiting", "decided", "effected", "ineffective", "level",
                    "oldest_waiting_days"):
            assert key not in unknown, f"{reason} کلیدِ {key} دارد: {unknown}"
        assert unknown["text"], f"{reason} جمله ندارد"


# ─── ۲: شمارش روی فیکسچرِ قطعی ─────────────────────────────────────────────
def t_counts_come_from_the_fold():
    root = _fixture(_cards(2, 3), {
        "D0": {"state": "APPLIED", "receipt_id": "rcpt-1"},
        "D1": {"state": "RECONCILE_REQUIRED", "receipt_id": ""},
        "D2": {"state": "RECONCILE_REQUIRED", "receipt_id": ""},
    })
    try:
        debt = OD.owner_debt(root, now=NOW)
        assert debt["known"] is True, f"فیکسچرِ سالم UNKNOWN شد: {debt}"
        assert debt["waiting"] == 2, f"منتظر باید ۲ باشد: {debt}"
        assert debt["decided"] == 3, f"تصمیم‌گرفته باید ۳ باشد: {debt}"
        assert debt["effected"] == 1, f"اثرکرده باید ۱ باشد (فقط APPLIED با رسید): {debt}"
        assert debt["ineffective"] == 2, f"بی‌اثر باید ۳−۱=۲ باشد: {debt}"
        assert debt["reconcile_required"] == 2, f"RECONCILE_REQUIRED باید ۲ باشد: {debt}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_decided_but_never_effected_is_the_load_bearing_number():
    """شکلِ زندهٔ امروز: تصمیم‌ها ثبت شده‌اند و **هیچ‌کدام** اثر نکرده‌اند.

    عددِ زنده (۲۱/۰) عمداً پین نمی‌شود — شکلش پین می‌شود.
    """
    root = _fixture(_cards(0, 4), {f"D{i}": {"state": "RECONCILE_REQUIRED",
                                             "receipt_id": ""} for i in range(4)})
    try:
        text, debt = OD.owner_debt_line(root, now=NOW)
        assert debt["decided"] == 4 and debt["effected"] == 0, debt
        assert debt["ineffective"] == 4, f"تصمیمِ بی‌اثر شمرده نشد: {debt}"
        assert "۴ تصمیم بی‌اثر" in text, f"جمله بی‌اثرها را نمی‌گوید: {text}"
        assert debt["level"] >= 2, f"تصمیمِ بی‌اثر باید بلند باشد: {debt['level']}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_applied_without_receipt_is_still_ineffective():
    """ناوردیِ C1 که این جمله بر آن سوار است: اثر بدونِ رسید، اثر نیست."""
    root = _fixture(_cards(0, 1), {"D0": {"state": "APPLIED", "receipt_id": ""}})
    try:
        debt = OD.owner_debt(root, now=NOW)
        assert debt["effected"] == 0, "APPLIED با رسیدِ تهی اثر شمرده شد"
        assert debt["ineffective"] == 1, debt
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ─── ۳: بدهیِ صفر ⇒ سکوت ───────────────────────────────────────────────────
def t_zero_debt_produces_no_sentence():
    """سنجهٔ پذیرشِ سند. ذخیرهٔ **خالی** با ذخیرهٔ **ناخوانا** یکی نیست."""
    root = _fixture({})
    try:
        text, debt = OD.owner_debt_line(root, now=NOW)
        assert debt["known"] is True, "ذخیرهٔ خالی نباید UNKNOWN شود"
        assert debt["waiting"] == 0 and debt["ineffective"] == 0, debt
        assert debt["level"] == 0, debt["level"]
        assert text == "", f"بدهیِ صفر جمله تولید کرد: {text!r}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ─── ۴: تشدید — چیزی که نمی‌آید باید بلندتر شود ────────────────────────────
def t_older_debt_is_strictly_louder():
    """تنها مکانیزمِ تشدیدِ طرح. اگر با سن بلندتر نشود، فقط محو می‌شود."""
    root = _fixture(_cards(1, 0, waiting_age_s=8 * DAY))
    try:
        fresh = OD.owner_debt(root, now=NOW - 8 * DAY + 3600.0)
        mid = OD.owner_debt(root, now=NOW - 4 * DAY)
        old = OD.owner_debt(root, now=NOW)
        assert fresh["level"] < mid["level"] < old["level"], \
            f"سطح با سن بالا نرفت: {fresh['level']}/{mid['level']}/{old['level']}"
        assert old["level"] == 3, f"۸ روز باید به بلندترین سطح برسد: {old['level']}"
        assert old["oldest_waiting_days"] == 8, \
            f"سن باید کف‌شده به روز باشد: {old['oldest_waiting_days']}"
        texts = {fresh["text"], mid["text"], old["text"]}
        assert len(texts) == 3, f"سه سنِ متفاوت یک جمله دادند: {texts}"
        for t in texts:
            assert "کارت منتظر" in t, t
        assert "۸ روز" in old["text"], old["text"]
        assert "کمتر از یک روز" in fresh["text"], fresh["text"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_level_is_monotone_in_age():
    """ناوردی روی تابعِ خالص — بدونِ دیسک، پس بی‌لرزش."""
    prev = -1
    for days in (0, 1, 2.9, 3, 6.9, 7, 30):
        lvl = OD._level(1, 0, days * DAY)
        assert lvl >= prev, f"سطح در {days} روز پایین آمد: {lvl} < {prev}"
        prev = lvl
    assert OD._level(0, 0, None) == 0, "بدونِ بدهی نباید سطحی باشد"
    assert OD._level(0, 1, None) >= 2, "تصمیمِ بی‌اثر باید کفِ بلند داشته باشد"


# ─── ۵: بی‌محتوا بودن ──────────────────────────────────────────────────────
def t_sentence_and_dict_are_content_free():
    """قاعدهٔ #۷: فقط شمارش، سن و نامِ مرحله — نه متنِ کارت، نه شناسه."""
    root = _fixture(_cards(2, 1), {"D0": {"state": "RECONCILE_REQUIRED"}})
    try:
        text, debt = OD.owner_debt_line(root, now=NOW)
        blob = json.dumps(debt, ensure_ascii=False)
        assert LEAK not in text and LEAK not in blob, "متنِ کارت نشت کرد"
        for ident in ("S0", "S1", "D0", "rfc:"):
            assert ident not in text, f"شناسه در جمله نشت کرد: {ident} / {text}"
            assert ident not in blob, f"شناسه در dict نشت کرد: {ident} / {blob}"
        assert len(text) <= 120, f"جمله کوتاه نیست ({len(text)}): {text}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ─── ۶: مرزهای روزِ اول ────────────────────────────────────────────────────
def t_state_dir_is_mandatory():
    """پیش‌فرضِ ضمنی یعنی خوردن به ذخیرهٔ زنده — درسِ ثبت‌شدهٔ ۰۸-۰۳."""
    try:
        OD.owner_debt(None)
    except ValueError:
        pass
    else:
        raise AssertionError("owner_debt(None) باید استثنا بدهد، نه ذخیرهٔ زنده را بخواند")


def t_module_writes_nothing():
    """AST نه زیررشته — `replace` روی رشته بی‌گناه است، روی `os` نه."""
    tree = _tree_of_self()
    names = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
             for n in ast.walk(tree) if isinstance(n, ast.Call)}
    bad = names & {"write_text", "write_bytes", "mkdir", "unlink", "rmtree",
                   "touch", "rename", "makedirs", "remove", "open"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "replace" and isinstance(n.func.value, ast.Name) \
                and n.func.value.id == "os":
            bad.add("os.replace")
    assert not bad, f"owner_debt می‌نویسد: {sorted(bad)}"


def t_module_imports_no_telegram_or_network():
    """جمله را می‌نویسد؛ نمی‌فرستد. فرستادن رأیِ مالک است."""
    imported = set()
    for n in ast.walk(_tree_of_self()):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    bad = imported & {"socket", "urllib", "requests", "http", "httpx", "subprocess",
                      "smtplib", "telegram", "telegram_center", "tg", "telebot"}
    assert not bad, f"ماژولِ خالص شبکه/تلگرام import می‌کند: {sorted(bad)}"


def t_zero_production_callers_on_day_one():
    """«نوشتنِ جمله مهندسی است؛ فرستادنش رأی مالک است» — امروز صفر صداکننده.

    AST نه grep: grep کامنت را می‌شمارد و `from pkg import mod` را از دست می‌دهد.
    """
    callers = []
    for path in _OPS.rglob("*.py"):
        parts = set(path.parts)
        if path.name.startswith("test_") or "tests" in parts or path.name == "owner_debt.py":
            continue
        try:
            tree = ast.parse(path.read_text("utf-8"))
        except (SyntaxError, ValueError, OSError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                if any(a.name.split(".")[-1] == "owner_debt" for a in n.names):
                    callers.append(str(path))
            elif isinstance(n, ast.ImportFrom):
                if n.module and n.module.split(".")[-1] == "owner_debt":
                    callers.append(str(path))
            elif isinstance(n, ast.Call):
                name = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                if name in ("owner_debt", "owner_debt_line"):
                    callers.append(str(path))
    assert not callers, ("C15 باید روزِ اول بی‌سیم باشد؛ صداکننده پیدا شد: "
                         f"{sorted(set(callers))[:5]}")


def t_writes_nothing_under_the_live_vault():
    """سنجهٔ ایزوله — **علّی**، نه اسنپ‌شاتِ mtime.

    نسخهٔ اول کلِ `_ops/state/` را قبل/بعد mtime می‌گرفت و قرمزِ لرزان داد:
    `_ops/state/pulse/telegram-poll.json` را پروسهٔ زندهٔ تلگرام هر ثانیه
    بازمی‌نویسد. آن اسنپ‌شات **ارگانیسم** را می‌سنجید نه این ماژول را — و
    قرمزِ لرزان بدتر از سبزِ دروغین است. اینجا مستقیم علت سنجیده می‌شود:
    هر باز-کردنِ نوشتنی در طولِ فراخوانی ثبت می‌شود و هیچ‌کدام نباید زیرِ
    درختِ زنده باشد.

    گاردِ کور نباشد: یک نوشتنِ **کنترلِ مثبت** در scratchpad هم انجام می‌شود؛
    اگر هوک اصلاً کار نکند، همان کنترل تست را قرمز می‌کند.
    """
    import os
    import sysconfig

    live_root = str(_OPS.parent).lower()
    recorded = []
    armed = {"on": False}

    def _hook(event, args):
        if not armed["on"]:
            return
        try:
            if event == "open":
                path, mode, flags = args[0], args[1], args[2]
                writing = (any(c in mode for c in "wxa+") if isinstance(mode, str)
                           else bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT
                                              | os.O_APPEND | os.O_TRUNC)))
                if writing and path:
                    recorded.append(("open", str(path)))
            elif event in ("os.mkdir", "os.rename", "os.remove", "os.rmdir",
                           "os.replace", "shutil.rmtree", "sqlite3.connect"):
                if args and args[0]:
                    recorded.append((event, str(args[0])))
        except Exception:   # noqa: BLE001 — هوک هرگز نباید تست را بترکاند
            pass

    sys.addaudithook(_hook)

    # گرم‌کردن: importِ تنبلِ `pending_card_recovery` و ساختِ .pyc نباید داخلِ
    # پنجرهٔ سنجش بیفتد؛ آن نوشتنِ مفسر است، نه نوشتنِ این ماژول.
    warm = _fixture(_cards(1, 1), {"D0": {"state": "RECONCILE_REQUIRED"}})
    try:
        OD.owner_debt_line(warm, now=NOW)
    finally:
        shutil.rmtree(warm, ignore_errors=True)

    root = _fixture(_cards(1, 1), {"D0": {"state": "RECONCILE_REQUIRED"}})
    control = Path(tempfile.gettempdir()) / "owner-debt-audit-control.txt"
    try:
        armed["on"] = True
        OD.owner_debt_line(root, now=NOW)
        control.write_text("positive control", encoding="utf-8")
        armed["on"] = False
    finally:
        armed["on"] = False
        shutil.rmtree(root, ignore_errors=True)
        control.unlink(missing_ok=True)

    assert any(str(control).lower() in p.lower() for _, p in recorded), \
        f"هوکِ ممیزی کار نکرد — این گارد کور است: {recorded[:5]}"
    stdlib = (sysconfig.get_paths().get("stdlib") or "").lower()
    hits = [(e, p) for e, p in recorded
            if p.lower().startswith(live_root) and not (stdlib and p.lower().startswith(stdlib))]
    assert not hits, f"زیرِ درختِ زنده نوشت: {hits[:5]}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_owner_debt: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
