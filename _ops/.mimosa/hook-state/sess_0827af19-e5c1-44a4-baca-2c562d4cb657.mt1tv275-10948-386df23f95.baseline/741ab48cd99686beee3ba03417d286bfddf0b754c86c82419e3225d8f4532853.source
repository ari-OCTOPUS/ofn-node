#!/usr/bin/env python3
"""ledger_core.py — هستهٔ دفترِ دوطرفه (فازِ صفر + سخت‌سازیِ auditِ خصمانهٔ 2026-07-16).

پاسخ به حکمِ نقدِ بیرونی («برچسب‌زنیِ بانکی حسابداری نیست») + ۴۳ یافتهٔ verifyِ ۴۸-ایجنتی:
ثبتِ متوازنِ دوطرفه، اعتبارسنجِ قطعی، دفترِ append-only با **قفلِ فایل** و **نوشتنِ ضدِ-torn
(fsync)**، اصلاح فقط با reversal (با tax_code)، قفلِ دوره، trial balanceِ صادق، auditِ
append-only. LLM هیچ نقشی ندارد — همه‌چیز قطعی و به سنتِ صحیح.

مدلِ entity (two-rails، رأی‌های مالک 2026-07-16): **دفترِ رسمی/مالیاتیِ شرکت = Xero**
(ریلِ A — ARCHITECTURE-TWO-RAILS). این ماژول = **دفترِ داخلیِ خانوادگی/عملیاتی** (ریلِ B):
تسویهٔ آرمین↔عباس (حسابِ 2200) و ثبت‌های داخلی — ردگیریِ دقیق، ولی موضوعِ ATO نیست؛
هیچ تشریفاتِ مالیاتیِ related-party/Division-7A رویش گذاشته نمی‌شود (RD-003).

ناوردارهای پول (تغییرناپذیر — نوشتن fail-CLOSED):
  * مبلغ فقط int سنت (نه bool/float/رشته) و ≤ سقفِ عقلانیت — رد، نه تبدیل.
  * sum(debits) == sum(credits) > 0 وگرنه ثبت نمی‌شود.
  * journalِ posted هرگز ویرایش/حذف نمی‌شود — فقط reversal (آینهٔ دقیقِ اصل + همان tax_code).
  * «reverse شده» = reversalِ *ایستاده* دارد (زنجیرهٔ reverse-of-reversal حساب می‌شود).
  * دورهٔ قفل‌شده → رد. تاریخ باید تقویمیِ واقعی باشد.
  * GST fail-closed: بدونِ gst_registered=True هر tax_code غیرِ N-T **و هر ثبتِ مستقیم به
    حسابِ کنترلِ GST** رد می‌شود؛ با True هم فقط whitelistِ کدها. تفسیرِ مالیاتی با agent.
  * کلیدهای ناشناخته در entry/سطر رد می‌شوند (ضدِ قاچاقِ فیلدِ مالیاتی/متادیتا).
  * idempotency: کلیدِ تکراری با payloadِ یکسان → duplicate؛ با payloadِ متفاوت → **conflict**
    (نه بلعیدنِ بی‌صدا). نامفضای `rev-` رزروِ reversal است. بدونِ کلید، دو ثبتِ مشروعِ
    یکسان (دو دستمزدِ نقدیِ هم‌مبلغِ هم‌روز) **هر دو** ثبت می‌شوند.
  * خواندنِ مسیرِ نوشتن strict است: فایلِ ناخوانا/خطِ خراب/torn-tail/idِ تکراری → ثبت رد
    («دفتر نیازِ بازبینیِ دستی») — هرگز ثبتِ کور روی دفترِ مشکوک.

منبعِ policy: personal/policy-profile.json (gitignored — ABN دارد). دفتر:
personal/ledger/{journals,audit}.jsonl (gitignored). $0 · stdlib + opslib/money.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402
import money   # noqa: E402  (fmt برای نمایش؛ محاسبه همه int)

# ─── چارتِ حساب‌های پیش‌فرض (بیزنسِ نقاشی، کمینه؛ profile می‌تواند override/اضافه کند) ───
DEFAULT_COA = {
    "1000": "بانک",
    "1100": "طلب از مشتری (AR)",
    "1500": "ابزار و تجهیزات (دارایی)",
    "2100": "GST control (فقط اگر ثبتِ GST تأیید شود)",
    "2200": "حسابِ خانوادگیِ عباس (تسویهٔ داخلی — نه موضوعِ مالیات)",
    "3000": "سرمایه/برداشتِ مالک (drawings)",
    "4000": "درآمدِ نقاشی",
    "5000": "مصالح",
    "5100": "پیمانکار/کارگر",
    "5200": "اجاره",
    "5300": "دستمزد",
    "6000": "متفرقه",
}
_ALLOWED_TAX_FREE = (None, "", "N-T")          # بدونِ تأییدِ GST فقط این‌ها
_TAX_WHITELIST = {"GST", "N-T", "GST-FREE", "INPUT-TAXED"}   # با تأیید هم فقط این‌ها
_GST_CONTROL_ACCOUNTS = {"2100"}               # ثبتِ مستقیم به این‌ها هم پشتِ گیتِ GST
_ENTRY_KEYS = {"entity_id", "date", "memo", "lines", "evidence",
               "idempotency_key", "reverses"}
_LINE_KEYS = {"account", "debit_cents", "credit_cents", "tax_code"}
_MAX_CENTS = 10 ** 13                          # سقفِ عقلانیتِ تک-ثبت (۱۰۰ میلیارد دلار)


def _profile_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "policy-profile.json"


def _ledger_dir() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger"


def load_profile(path: Path | None = None) -> dict | None:
    """policy-profile (gitignored). نبود/خرابی → None (هر ثبت با profile=None رد می‌شود)."""
    p = path or _profile_path()
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else None
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def coa(profile: dict | None) -> dict:
    out = dict(DEFAULT_COA)
    if isinstance(profile, dict) and isinstance(profile.get("chart_of_accounts"), dict):
        out.update({str(k): str(v) for k, v in profile["chart_of_accounts"].items()})
    return out


def _entity_ids(profile: dict | None) -> set:
    try:
        ents = (profile or {}).get("entities") or []      # null-safe (audit #23)
        return {str(e.get("entity_id")) for e in ents
                if isinstance(e, dict) and e.get("entity_id")}
    except Exception:  # noqa: BLE001
        return set()


def _gst_ok(profile: dict | None, entity_id: str) -> bool:
    """فقط `is True` — رشتهٔ 'true'/1/'yes' همه بسته می‌مانند (fail-closed)."""
    try:
        for e in ((profile or {}).get("entities") or []):
            if isinstance(e, dict) and str(e.get("entity_id")) == entity_id:
                return e.get("gst_registered") is True
    except Exception:  # noqa: BLE001
        return False
    return False


def _gst_control_accounts(profile: dict | None) -> set:
    extra = (profile or {}).get("gst_control_accounts")
    out = set(_GST_CONTROL_ACCOUNTS)
    if isinstance(extra, list):
        out |= {str(a) for a in extra}
    return out


def _is_int_cents(x) -> bool:
    """int خالص (نه bool/float/رشته)، ≥0 و ≤ سقف — رد، نه تبدیل (ناوردای پول)."""
    return isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= _MAX_CENTS


def _valid_date(s: str) -> bool:
    """تقویمِ واقعی، نه فقط شکل ('2026-99-99' مردود — audit #35)."""
    try:
        _dt.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


# ─── اعتبارسنجِ قطعی ─────────────────────────────────────────────────────────────
def validate_journal(entry: dict, profile: dict | None) -> dict:
    """قواعدِ سختِ ثبت. خروجی {"ok": bool, "errors": [...]}. هیچ‌چیز تغییری نمی‌کند."""
    errs: list[str] = []
    if not isinstance(entry, dict):
        return {"ok": False, "errors": ["entry باید dict باشد"]}
    unknown = set(entry.keys()) - _ENTRY_KEYS
    if unknown:
        errs.append(f"کلید(های) ناشناخته در entry: {sorted(unknown)} — قاچاقِ فیلد ممنوع")
    if profile is None:
        errs.append("policy-profile غایب — اول personal/policy-profile.json را از قالب پر کن")
    ent = str(entry.get("entity_id", "") or "")
    if not ent:
        errs.append("legal entity_id اجباری است (قاعدهٔ ۳ نقد)")
    elif profile is not None and _entity_ids(profile) and ent not in _entity_ids(profile):
        errs.append(f"entity ناشناخته: {ent}")
    date = str(entry.get("date", "") or "")
    if not _valid_date(date):
        errs.append("date باید تاریخِ تقویمیِ معتبرِ YYYY-MM-DD باشد")
    lock = str((profile or {}).get("lock_date") or "")
    if lock and date and date <= lock:
        errs.append(f"دورهٔ قفل‌شده (تا {lock}) — ثبت/تغییر در دورهٔ بسته ممنوع؛ reversal در دورهٔ باز")
    ikey = entry.get("idempotency_key")
    if ikey is not None and not isinstance(ikey, str):
        errs.append("idempotency_key باید رشته باشد")
    if isinstance(ikey, str) and ikey.startswith("rev-"):
        # نامفضای رزروِ reversal (audit #1): فقط وقتی reverses هم‌خوان باشد
        rv = str(entry.get("reverses") or "")
        base = ikey[4:].rsplit("-", 1)[0] if "-" in ikey[4:] else ikey[4:]
        if not rv or base != rv:
            errs.append("نامفضای idempotency_key `rev-` رزروِ reversal است")
    lines = entry.get("lines")
    if not isinstance(lines, list) or len(lines) < 2:
        errs.append("حداقل ۲ سطر (دوطرفه)")
        return {"ok": False, "errors": errs}
    accounts = coa(profile)
    gst_open = _gst_ok(profile, ent)
    gst_ctrl = _gst_control_accounts(profile)
    tdr = tcr = 0
    amounts_ok = True
    for i, ln in enumerate(lines):
        if not isinstance(ln, dict):
            errs.append(f"سطر {i}: dict نیست")
            amounts_ok = False
            continue
        unk = set(ln.keys()) - _LINE_KEYS
        if unk:
            errs.append(f"سطر {i}: کلید(های) ناشناخته {sorted(unk)} — قاچاقِ فیلدِ مالیاتی/متادیتا ممنوع")
        acc = str(ln.get("account", "") or "")
        if acc not in accounts:
            errs.append(f"سطر {i}: حسابِ ناشناخته {acc!r} (چارت را ببین)")
        if acc in gst_ctrl and not gst_open:
            # audit #7: ثبتِ مستقیم به حسابِ کنترلِ GST هم پشتِ گیت است، نه فقط tax_code
            errs.append(f"سطر {i}: حسابِ کنترلِ GST ({acc}) بدونِ gst_registered=True → needs-agent")
        # چکِ tax_code مستقل از سلامتِ مبلغ انجام می‌شود (audit #41)
        tax = ln.get("tax_code")
        if tax not in _ALLOWED_TAX_FREE:
            if not gst_open:
                errs.append(f"سطر {i}: tax_code={tax!r} ولی gst_registered تأیید نشده → "
                            "needs-agent (BAS/tax agentِ ثبت‌شده تصمیم بگیرد)")
            elif not isinstance(tax, str) or tax.strip().upper() not in _TAX_WHITELIST:
                errs.append(f"سطر {i}: tax_code نامعتبر {tax!r} — فقط "
                            f"{sorted(_TAX_WHITELIST)} (audit #38)")
        dr, cr = ln.get("debit_cents", 0), ln.get("credit_cents", 0)
        if not _is_int_cents(dr) or not _is_int_cents(cr):
            errs.append(f"سطر {i}: مبلغ باید intِ سنت در [0, {_MAX_CENTS}] باشد — "
                        "bool/float/رشته مردود (ناوردای پول)")
            amounts_ok = False
            continue
        if (dr > 0) == (cr > 0):
            errs.append(f"سطر {i}: دقیقاً یکی از debit/credit باید مثبت باشد")
        tdr += dr
        tcr += cr
    if amounts_ok and tdr != tcr:
        errs.append(f"نامتوازن: debits={tdr} != credits={tcr} (ناوردای ۲ نقد)")
    if amounts_ok and tdr == 0 and tcr == 0:
        errs.append("ثبتِ صفر بی‌معناست")
    return {"ok": not errs, "errors": errs}


# ─── خواندنِ دفتر: soft برای گزارش، strict برای نوشتن ─────────────────────────────
def _journals_path(ledger_dir: Path | None) -> Path:
    return (ledger_dir or _ledger_dir()) / "journals.jsonl"


def _audit_path(ledger_dir: Path | None) -> Path:
    return (ledger_dir or _ledger_dir()) / "audit.jsonl"


def _read_ledger(ledger_dir: Path | None) -> dict:
    """خواندنِ کامل با آمارِ سلامت: journals + corrupt_lines + dup_ids + torn_tail +
    read_error. مسیرِ نوشتن روی هر نشانهٔ ناسلامتی fail-closed می‌شود (audit #2,#3,#16)."""
    p = _journals_path(ledger_dir)
    st = {"journals": [], "corrupt_lines": 0, "dup_ids": [], "torn_tail": False,
          "read_error": None}
    if not p.exists():
        return st
    try:
        raw = p.read_bytes()
    except OSError as e:
        st["read_error"] = type(e).__name__
        return st
    if raw and not raw.endswith(b"\n"):
        st["torn_tail"] = True                       # tornِ بی‌newline — append روی آن ممنوع
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:                       # audit #16 — crash نه، شمارش
        text = raw.decode("utf-8", errors="replace")
        st["corrupt_lines"] += 1
    seen: set = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            st["corrupt_lines"] += 1
            continue
        if not isinstance(d, dict):
            st["corrupt_lines"] += 1
            continue
        jid = str(d.get("journal_id") or "")
        if jid and jid in seen:
            st["dup_ids"].append(jid)                # audit #3: دوبار-شماری آشکار شود
        seen.add(jid)
        st["journals"].append(d)
    return st


def _write_block_errors(st: dict) -> list[str]:
    """اگر دفتر مشکوک است، نوشتن ممنوع (بازبینیِ دستی) — هرگز ثبتِ کور (audit #2,#3)."""
    errs = []
    if st["read_error"]:
        errs.append(f"دفتر ناخوانا ({st['read_error']}) — retry؛ اگر ماند بازبینیِ دستی")
    if st["torn_tail"]:
        errs.append("انتهای دفتر ناقص است (torn write) — بازبینیِ دستی قبل از هر ثبت")
    if st["corrupt_lines"]:
        errs.append(f"{st['corrupt_lines']} خطِ خراب در دفتر — بازبینیِ دستی قبل از هر ثبت")
    if st["dup_ids"]:
        errs.append(f"journal_id تکراری در دفتر: {st['dup_ids'][:3]} — بازبینیِ دستی")
    return errs


def _payload_hash(entry: dict) -> str:
    basis = json.dumps([entry.get("entity_id"), entry.get("date"), entry.get("lines"),
                        str(entry.get("memo", "")), str(entry.get("reverses") or "")],
                       ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()


def _effectively_reversed(journals: list[dict], jid: str, _depth: int = 0) -> bool:
    """آیا jid یک reversalِ *ایستاده* دارد؟ reverse-of-reversal زنجیره را برمی‌گرداند
    (audit #30: J→R→R2 یعنی J دوباره برقرار است و می‌تواند دوباره reverse شود)."""
    if _depth > 32:                                   # گاردِ حلقهٔ داده‌ٔ خراب
        return True
    for j in journals:
        if str(j.get("reverses") or "") == str(jid):
            if not _effectively_reversed(journals, str(j.get("journal_id")), _depth + 1):
                return True
    return False


def _lines_mirror(orig_lines: list, rev_lines: list) -> bool:
    """سطرهای reversal باید آینهٔ دقیقِ اصل باشند: همان حساب/tax_code، debit↔credit
    (audit #17: هیچ fake-reverse با سطرهای دلخواه)."""
    if not isinstance(orig_lines, list) or not isinstance(rev_lines, list) \
            or len(orig_lines) != len(rev_lines):
        return False
    for o, r in zip(orig_lines, rev_lines):
        if not isinstance(o, dict) or not isinstance(r, dict):
            return False
        if str(o.get("account")) != str(r.get("account")):
            return False
        if o.get("tax_code") != r.get("tax_code"):
            return False
        try:
            if int(o.get("debit_cents", 0)) != int(r.get("credit_cents", 0)) or \
               int(o.get("credit_cents", 0)) != int(r.get("debit_cents", 0)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _append_ledger_line(p: Path, rec: dict) -> None:
    """append ضدِ-torn: خط + '\\n' در یک write، بعد flush + fsync (audit #3,#21)."""
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _audit(action: str, journal_id: str, reason: str, ledger_dir: Path | None,
           actor: str = "system") -> None:
    """audit append-only. actor صادق (audit #31)؛ حتی شکستِ alert هم بلعیده می‌شود (#32)."""
    try:
        _append_ledger_line(_audit_path(ledger_dir),
                            {"ts": opslib.now_iso(), "actor": str(actor)[:40],
                             "action": action, "journal_id": journal_id,
                             "reason": str(reason or "")[:200]})
    except Exception:  # noqa: BLE001
        try:
            opslib.alert([f"ledger audit append شکست: {action} {journal_id}"])
        except Exception:  # noqa: BLE001 — alert هم شکست → سکوت؛ ثبتِ اصلی قبلاً انجام شده
            pass


# ─── ثبت (قفل‌دار، fail-closed) ───────────────────────────────────────────────────
def post_journal(entry: dict, profile: dict | None, ledger_dir: Path | None = None,
                 reason: str = "", actor: str = "system") -> dict:
    """ثبتِ متوازن — زیرِ قفلِ فایل (ضدِ raceِ audit #2,#5): scan→check→append اتمی.
    idempotency: کلیدِ تکراری+payloadِ یکسان → duplicate؛ +payloadِ متفاوت → conflict
    (audit #11). بدونِ کلید → هرگز dedupِ بی‌صدا (دو ثبتِ مشروعِ یکسان هر دو می‌نشینند،
    audit #4). entryِ دارای reverses باید آینهٔ اصلِ reverse-نشده باشد (audit #17)."""
    v = validate_journal(entry, profile)
    if not v["ok"]:
        return {"ok": False, "errors": v["errors"]}
    jp = _journals_path(ledger_dir)
    try:
        lock = opslib.LockedJson(jp)                  # فقط قفلش را می‌خواهیم (jp.lock)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "errors": [f"قفلِ دفتر ساخته نشد: {type(e).__name__}"]}
    try:
        with lock:
            st = _read_ledger(ledger_dir)
            blk = _write_block_errors(st)
            if blk:
                return {"ok": False, "errors": blk}
            existing = st["journals"]
            phash = _payload_hash(entry)
            ikey = str(entry.get("idempotency_key") or "")
            if ikey:
                for j in existing:
                    if str(j.get("idempotency_key") or "") == ikey:
                        if str(j.get("payload_hash") or "") == phash:
                            return {"ok": True, "journal_id": j.get("journal_id"),
                                    "duplicate": True}
                        return {"ok": False, "conflict": True,
                                "errors": [f"idempotency-conflict: کلید {ikey!r} قبلاً با "
                                           "payloadِ متفاوت مصرف شده — کلیدِ نو بده "
                                           "(هیچ‌چیز بی‌صدا دور انداخته نمی‌شود)"]}
            rv = str(entry.get("reverses") or "")
            if rv:
                orig = next((j for j in existing
                             if str(j.get("journal_id")) == rv), None)
                if orig is None:
                    return {"ok": False, "errors": [f"reverses به journalِ ناشناخته: {rv}"]}
                if _effectively_reversed(existing, rv):
                    return {"ok": False, "errors": [f"{rv} قبلاً reverse شده و ایستاده است"]}
                if not _lines_mirror(orig.get("lines") or [], entry.get("lines") or []):
                    return {"ok": False, "errors":
                            ["سطرهای reversal آینهٔ دقیقِ اصل نیستند (حساب/مبلغ/tax_code)"]}
            # journal_id: با ikey قطعی از payload؛ بدونِ ikey با seq تا دو ثبتِ یکسانِ
            # مشروع هرگز بلعیده نشوند (audit #4/#13)
            uniq = "" if ikey else f"|seq:{len(existing)}"
            jid = "j-" + hashlib.sha1((phash + uniq).encode("utf-8")).hexdigest()[:12]
            n = 0
            while any(str(j.get("journal_id")) == jid for j in existing):
                n += 1
                jid = "j-" + hashlib.sha1(f"{phash}{uniq}|{n}".encode("utf-8")).hexdigest()[:12]
            rec = {"journal_id": jid, "entity_id": entry.get("entity_id"),
                   "date": entry.get("date"), "memo": str(entry.get("memo", ""))[:200],
                   "lines": entry.get("lines"), "evidence": entry.get("evidence") or [],
                   "status": "posted", "reverses": rv or None,
                   "idempotency_key": ikey or None, "payload_hash": phash,
                   "posted_at": opslib.now_iso()}
            try:
                _append_ledger_line(jp, rec)
            except Exception as e:  # noqa: BLE001 — نوشتن شکست = صادقانه رد
                return {"ok": False, "errors": [f"نوشتنِ دفتر شکست: {type(e).__name__}"]}
    except TimeoutError:
        return {"ok": False, "errors": ["قفلِ دفتر مشغول است — retry"]}
    _audit("post", jid, reason, ledger_dir, actor=actor)
    return {"ok": True, "journal_id": jid, "duplicate": False}


def reverse_journal(journal_id: str, reason: str, profile: dict | None,
                    ledger_dir: Path | None = None, date: str | None = None,
                    actor: str = "system") -> dict:
    """اصلاح = reversal: آینهٔ دقیقِ اصل (با tax_code — audit #28/#37)، لینک به اصل.
    اصلِ خراب (مبلغِ ناعدد) → ردِ تمیز، نه crash (audit #10). ikey با شمارندهٔ
    reversalهای موجود تا بعدِ reverse-of-reversal دوباره reverse ممکن باشد (audit #30)."""
    st = _read_ledger(ledger_dir)
    blk = _write_block_errors(st)
    if blk:
        return {"ok": False, "errors": blk}
    js = st["journals"]
    orig = next((j for j in js if str(j.get("journal_id")) == str(journal_id)), None)
    if orig is None:
        return {"ok": False, "errors": [f"journal ناشناخته: {journal_id}"]}
    if _effectively_reversed(js, str(journal_id)):
        return {"ok": False, "errors": [f"{journal_id} قبلاً reverse شده و ایستاده است"]}
    rev_lines = []
    for ln in (orig.get("lines") or []):
        if not isinstance(ln, dict):
            return {"ok": False, "errors": ["اصل خراب است (سطرِ غیرdict) — بازبینیِ دستی"]}
        dr, cr = ln.get("debit_cents", 0), ln.get("credit_cents", 0)
        if not _is_int_cents(dr) or not _is_int_cents(cr):
            return {"ok": False,
                    "errors": ["اصل خراب است (مبلغِ ناسالم) — بازبینیِ دستی، نه reversalِ کور"]}
        out_ln = {"account": ln.get("account"), "debit_cents": cr, "credit_cents": dr}
        if ln.get("tax_code") is not None:
            out_ln["tax_code"] = ln.get("tax_code")   # tax_code حفظ می‌شود (audit #28)
        rev_lines.append(out_ln)
    n_prev = sum(1 for j in js if str(j.get("reverses") or "") == str(journal_id))
    entry = {"entity_id": orig.get("entity_id"), "date": date or opslib.today(),
             "memo": f"reversal of {journal_id}: {str(reason or '')[:120]}",
             "lines": rev_lines, "reverses": str(journal_id),
             "evidence": [f"journal:{journal_id}"],
             "idempotency_key": f"rev-{journal_id}-{n_prev}"}
    out = post_journal(entry, profile, ledger_dir, reason=f"reverse {journal_id}",
                       actor=actor)
    if out.get("ok"):
        _audit("reverse", str(journal_id), reason, ledger_dir, actor=actor)
    return out


def trial_balance(ledger_dir: Path | None = None) -> dict:
    """ترازِ آزمایشیِ *صادق*: علاوه بر جمع‌ها، سلامتِ دفتر را هم گزارش می‌کند —
    corrupt/dup/torn/read_error + bad_amount_lines. «قابلِ‌اتکا» فقط وقتی همه صفرند
    (audit #29/#33: دیگر روی دفترِ خراب balanced:True ساکت نمی‌دهد)."""
    st = _read_ledger(ledger_dir)
    per: dict = {}
    tdr = tcr = bad = 0
    for j in st["journals"]:
        for ln in (j.get("lines") or []):
            if not isinstance(ln, dict):
                bad += 1
                continue
            dr, cr = ln.get("debit_cents", 0), ln.get("credit_cents", 0)
            if not _is_int_cents(dr) or not _is_int_cents(cr):
                bad += 1                                # bool/رشته/float شمرده می‌شود، نه تبدیل
                continue
            acc = str(ln.get("account", "?"))
            s = per.setdefault(acc, {"debit_cents": 0, "credit_cents": 0})
            s["debit_cents"] += dr
            s["credit_cents"] += cr
            tdr += dr
            tcr += cr
    for acc, s in per.items():
        s["net_cents"] = s["debit_cents"] - s["credit_cents"]
        s["display"] = money.fmt(s["net_cents"])
    trustworthy = (not st["read_error"] and not st["torn_tail"]
                   and st["corrupt_lines"] == 0 and not st["dup_ids"] and bad == 0)
    return {"accounts": per, "total_debit_cents": tdr, "total_credit_cents": tcr,
            "balanced": tdr == tcr, "trustworthy": trustworthy,
            "corrupt_lines": st["corrupt_lines"], "dup_journal_ids": st["dup_ids"][:10],
            "torn_tail": st["torn_tail"], "read_error": st["read_error"],
            "bad_amount_lines": bad}


if __name__ == "__main__":
    print(json.dumps(trial_balance(), ensure_ascii=False, indent=2))
