#!/usr/bin/env python3
"""txn_categorize.py — دستیارِ هوشمندِ دسته‌بندیِ پس‌ماندِ صفِ بازبینی (2026-07-16، propose-only).

پس از attributor، هر txnِ needs_review (owner=unknown, ptype=unknown) در صفِ بازبینیِ مالک
می‌ماند. این ماژول با مغزِ محلی-اول ($0، خصوصی) یک *پیشنهادِ* برچسب برای این پس‌ماند می‌سازد —
هرگز قطعی نمی‌کند. روش ۵ (تحقیقِ ۲۰۲۷): «LLM برچسب پیشنهاد می‌دهد، هرگز پول حساب نمی‌کند».

نردبانِ مغز (محلی-اول → ابری فقط برای سخت‌ها):
  ۱) tier='local' (ollama 7B) — پیش‌فرض. روی دستگاهِ مالک، $۰، descِ خام مجاز است.
  ۲) اگر use_cloud=True و پرچمِ OCTOPUS_WIRE_ACCT_CLOUD روشن باشد و محلی «کم‌سیگنال»
     برگرداند → tier='primary' (Fugu، پشتِ گیتِ پولی) — ولی *فقط* بعد از scrub_pii(desc).

مرزهای سختِ پول/PII (این ماژول):
  - هیچ مبلغی هرگز به هیچ LLM نمی‌رود. prompt *فقط* از متنِ desc ساخته می‌شود؛ amount_cents
    هرگز در prompt نمی‌آید — همهٔ اعداد در موتورِ قطعی (money.py/attributor) می‌مانند.
  - قبل از هر ارسال به Fugu (ابریِ شخصِ‌ثالث): scrub_pii نامِ همکار/شماره‌حساب/رشتهٔ رقمیِ بلند
    را حذف می‌کند. نامِ واقعی فقط از configِ gitignore می‌آید، هرگز در سورس hardcode نیست.
  - PROPOSE-ONLY: suggestion ست می‌شود ولی review همان needs_review می‌ماند — مالک تأیید،
    نه ایجنت (روش ۸). apply_corrections (مسیرِ مالک) تنها راهِ confirmed است.
  - fail-soft: مدل خاموش / JSONِ خراب → txn دست‌نخورده (بدونِ کرش) + شمارشِ صادق.

$0 (محلی) · stdlib · fail-soft.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent / "budget"), str(_HERE.parent / "cortex"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

# ── واژگانِ برچسب (مرجع: مدلِ واقعیِ حسابدار) ────────────────────────────────
OWNERS = ("armin", "abbas", "business")
PTYPES = ("income", "expense", "wage", "transfer")
# نامِ مدل برای citationِ basis (نه کلید، نه endpoint)
def _basis_model(by: str) -> str:
    """نامِ صادقِ مدل در provenance (اسکن #55): محلی از env (پیش‌فرضِ واقعیِ مغز)."""
    if by == "local":
        return "ollama:" + str(os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b"))
    return "fugu"


def _config_path() -> Path:
    """configِ gitignore که name_blocklistِ واقعیِ همکار را نگه می‌دارد (هرگز در سورس)."""
    return (opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal"
            / "categorize-config.json")


def _load_blocklist() -> list[str]:
    """blocklistِ نام (برای scrub قبل از ابری). منبع: env (تست/override) + configِ gitignore.
    نامِ واقعی هرگز این‌جا نیست — الگوی OpsecGuardِ langar (اپراتور فایل را پر می‌کند)."""
    names: list[str] = []
    env = os.environ.get("ACCT_NAME_BLOCKLIST", "")
    if env:
        names += [n.strip() for n in env.split(",") if n.strip()]
    try:
        p = _config_path()
        if p.exists():
            cfg = json.loads(p.read_text("utf-8"))
            bl = cfg.get("name_blocklist") or cfg.get("blocklist") or []
            if isinstance(bl, list):
                names += [str(n).strip() for n in bl if str(n).strip()]
    except (OSError, ValueError):
        pass
    seen: set = set()
    out: list[str] = []
    for n in names:                       # یکتا، بی‌حساس به حروف، حفظِ ترتیب
        k = n.lower()
        if k and k not in seen:
            seen.add(k)
            out.append(n)
    return out


def scrub_pii(text: str, blocklist: list[str] | None = None) -> str:
    """PII را قبل از هر ارسال به ابری (Fugu) پاک کن — الگوی scrubِ OpsecGuard:
      · هر نامِ blocklist → ⟦name⟧ (بی‌حساس به حروف).
      · **هر توکنِ عددی** (شماره‌حساب/مبلغ با کاما یا اعشار مثل '5,000'/'$1,234.56'/'99.99'/'250')
        → ⟦num⟧. قبلاً فقط `\\d{4,}` بود که مبالغِ جداشده با کاما/نقطه از تور فرار می‌کردند و
        مبلغ به LLMِ ابری می‌رسید — نقضِ «هیچ مبلغی هرگز به هیچ LLM». حالا هر رشتهٔ رقمی حذف می‌شود.
    محلی (ollama) هرگز از این عبور نمی‌کند (روی دستگاه، خصوصی). fail-soft: امن‌ترین‌کار =
    حذفِ همهٔ ارقام حتی اگر blocklist بارنشد."""
    out = text or ""
    bl = blocklist if blocklist is not None else _load_blocklist()
    for name in bl:
        if name and name.strip():
            out = re.sub(re.escape(name), "⟦name⟧", out, flags=re.IGNORECASE)
    # هر توکنِ عددی (شاملِ کاما/نقطهٔ داخلی) و نیز رقمِ منفرد → ⟦num⟧ (هیچ مبلغی نشت نکند)
    out = re.sub(r"\d[\d,\.]*\d|\d", "⟦num⟧", out)
    return out


# ── ساختِ prompt (فقط از desc — هرگز مبلغ) ───────────────────────────────────
def _categories_hint() -> str:
    """فهرستِ فشردهٔ دسته‌ها از personal_ledger.CATEGORIES (grounding). fail-soft → ''."""
    try:
        import personal_ledger  # noqa: WPS433 — هم‌پوشه
        cats: list[str] = []
        for group in personal_ledger.CATEGORIES.values():
            cats += list(group)
        return ", ".join(cats[:40])
    except Exception:  # noqa: BLE001
        return ""


def _system_prompt() -> str:
    cats = _categories_hint()
    cat_line = f"دسته‌های مجاز: {cats}.\n" if cats else ""
    return (
        "تو دسته‌بندِ تراکنشِ حسابداری هستی. فقط از «متنِ توضیحِ» تراکنش (بدونِ هیچ مبلغی) "
        "برچسب بزن. مدلِ واقعی: آرمین برای عباس روزمزد کار می‌کند (حقوق=wage)؛ پولِ کسب‌وکار "
        "که از حسابِ آرمین به عباس رد می‌شود transfer است.\n"
        + cat_line +
        'خروجی فقط یک JSONِ کوچک: {"owner":"armin|abbas|business",'
        '"ptype":"income|expense|wage|transfer","category":"..."}. '
        'اگر نامطمئنی owner یا ptype را "unknown" بگذار. هیچ توضیحِ اضافه نده — فقط JSON.'
    )


def _user_prompt(desc: str) -> str:
    """prompt فقط از desc ساخته می‌شود — هیچ amount/مبلغ اینجا راه ندارد."""
    return f'توضیحِ تراکنش: "{desc}"\nبرچسب را فقط به‌صورتِ JSON بده.'


# ── پارسِ دفاعیِ خروجیِ مدل ───────────────────────────────────────────────────
def _parse_labels(text) -> dict | None:
    """اولین بلوکِ {...} را از خروجیِ مدل بردار و امن پارس کن. بدترین‌حالت → None
    (→ تراکنش دست‌نخورده). owner/ptypeِ نامعتبر → 'unknown' (هرگز حدسِ بی‌پایه)."""
    if not text:
        return None
    m = re.search(r"\{.*\}", str(text), re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except (ValueError, TypeError):
        return None
    if not isinstance(d, dict):
        return None
    owner = str(d.get("owner", "unknown")).strip().lower()
    ptype = str(d.get("ptype", "unknown")).strip().lower()
    category = str(d.get("category", "")).strip().lower()
    return {
        "owner": owner if owner in OWNERS else "unknown",
        "ptype": ptype if ptype in PTYPES else "unknown",
        "category": category,
    }


def _low_signal(labels) -> bool:
    """پس‌ماندِ «کم‌سیگنال» که ارزشِ رفتن به ابری دارد: مدل خاموش/JSONِ خراب (None)،
    یا owner/ptypeِ unknown، یا دسته‌ی خالی."""
    if not labels:
        return True
    return (labels.get("owner") == "unknown" or labels.get("ptype") == "unknown"
            or not labels.get("category"))


def _classify(desc: str, tier: str, blocklist: list[str]) -> dict | None:
    """یک فراخوانِ مدل با tierِ داده‌شده. برای ابری (primary/Fugu) descِ خام *اول* scrub
    می‌شود — هیچ نام/شماره از مرزِ ابری عبور نمی‌کند. fail-soft: هر خطا/خروجیِ بد → None."""
    prompt_desc = scrub_pii(desc, blocklist) if tier == "primary" else desc
    try:
        import model_router  # noqa: WPS433 — lazy، مونکی‌پچ‌پذیرِ تست
        out = model_router.ask("classify", _user_prompt(prompt_desc),
                               system=_system_prompt(), max_tokens=120, tier=tier)
    except Exception:  # noqa: BLE001 — مغز هرگز دسته‌بندی را نکشد
        return None
    if not isinstance(out, dict) or not out.get("ok"):
        return None
    return _parse_labels(out.get("text", ""))


# ── API عمومی ────────────────────────────────────────────────────────────────
def suggest(txns: list, use_cloud: bool = False) -> dict:
    """برای هر txnِ review=='needs_review' یک *پیشنهادِ* برچسب بساز (روش ۵).

    - tier='local' (ollama، $۰، خصوصی) پیش‌فرض. prompt فقط از desc — هرگز مبلغ.
    - ابری فقط وقتی: use_cloud=True *و* پرچمِ OCTOPUS_WIRE_ACCT_CLOUD روشن *و* محلی
      کم‌سیگنال بود؛ آن‌هم بعد از scrub_pii(desc).
    - txn['suggestion'] = {owner, ptype, category, by, basis}؛ review همان needs_review
      می‌ماند (LLM هرگز auto-confirm نمی‌کند — مالک تأیید).
    - fail-soft: مدل خاموش/JSONِ خراب → txn دست‌نخورده، شمارشِ صادق.

    خروجی: {ok, suggested_local, suggested_cloud, skipped}."""
    if not isinstance(txns, list):
        return {"ok": False, "suggested_local": 0, "suggested_cloud": 0, "skipped": 0}
    cloud_on = bool(use_cloud) and bool(os.environ.get("OCTOPUS_WIRE_ACCT_CLOUD"))
    blocklist = _load_blocklist()
    n_local = n_cloud = n_skip = 0
    for t in txns:
        if not isinstance(t, dict) or t.get("review") != "needs_review":
            continue
        desc = str(t.get("desc") or "").strip()
        if not desc:
            n_skip += 1
            continue
        labels = _classify(desc, "local", blocklist)
        by = "local"
        # اسکن #30: labels=None یعنی محلی «در دسترس نبود» (مثلاً فاصلهٔ ۱۰ثانیه‌ایِ
        # rate-limit در batch) — این skip است، نه سیگنالِ ضعیف؛ هرگز بهانهٔ پولی‌شدن نیست.
        if labels is None:
            n_skip += 1
            continue
        if cloud_on and _low_signal(labels):
            cloud_labels = _classify(desc, "primary", blocklist)
            if cloud_labels is not None:
                labels, by = cloud_labels, "cloud"
        if not labels:                     # محلی+ابری هر دو ناموفق → دست‌نخورده
            n_skip += 1
            continue
        t["suggestion"] = {
            "owner": labels["owner"], "ptype": labels["ptype"],
            "category": labels["category"], "by": by,
            "basis": f"llm-suggest:{_basis_model(by)}",
        }
        t["review"] = "needs_review"       # صریح: پیشنهاد ≠ تأیید (روش ۸)
        if by == "cloud":
            n_cloud += 1
        else:
            n_local += 1
    return {"ok": True, "suggested_local": n_local,
            "suggested_cloud": n_cloud, "skipped": n_skip}


if __name__ == "__main__":
    # دودِ سریع — بدونِ echo مبلغِ خام؛ مدل mock (بدونِ ollama)
    import model_router as _mr
    _mr.ask = lambda *a, **k: {"ok": True, "tier": k.get("tier"),
                               "text": '{"owner":"armin","ptype":"expense","category":"materials"}'}
    _t = [{"id": "1", "desc": "BUNNINGS Warehouse", "amount_cents": -8990,
           "review": "needs_review", "owner": "unknown", "ptype": "unknown"}]
    print(json.dumps({"result": suggest(_t), "suggestion": _t[0].get("suggestion"),
                      "review": _t[0]["review"],
                      "scrub": scrub_pii("pay to Abbas acct 123456 desc")},
                     ensure_ascii=False, indent=2))
