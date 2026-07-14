"""
brain/guardrails.py — لایه‌ی محافظِ خودمختاری.

سیستمِ خودمختار اجازه دارد «خودش را بخواند، خلاقیت کند، و استراتژی‌اش را عوض کند»،
ولی این لایه مرزهای امن را سفت نگه می‌دارد («پرریسک ولی محافظت‌شده»):

  ۱. نوشتنِ عادیِ runtime هرگز روی *.py نمی‌رود (assert_safe_write: فقط outputs/).
  ۲. خودتغییریِ کد فقط از یک کانالِ جداگانه و گیت‌دار ممکن است (brain/self_code):
     پیشنهاد در sandbox → گیتِ کاملِ تست → تأییدِ صریحِ مالک → اعمال با بکاپ.
     هرگز خودکار اعمال نمی‌شود، و هرگز به هسته‌ی موردِاعتماد (TCB) نمی‌رسد
     (core/, tests/, خودِ گاردها، settings, run.py) — assert_code_target_allowed.
  ۳. هرگز در مسیرهای immutable ننویسد (4D/ مرجع، core/).
  ۴. پارامترهای خودتنظیمی فقط در محدوده‌ی امن و با گامِ محدود تغییر کنند.
  ۵. ثابت‌های ریاضی (لنگرها) و دست‌نخوردگیِ مرجع همیشه قابل‌بررسی باشند.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ── محدوده‌ی امنِ پارامترهای خودتنظیمی ───────────────────────────────────
SAFE_PARAM_RANGES: dict[str, tuple[float, float]] = {
    "novelty_threshold": (0.50, 0.99),   # آستانه‌ی «کشفِ قابل‌توجه»
    "rho_bias":          (0.00, 0.95),   # سوگیریِ ناحیه‌ی پارامتری
    "creativity":        (0.00, 1.00),   # شدتِ خلاقیت
    "explore_points":    (500, 8000),    # طولِ سری در هر کاوش
}

# بیشترین تغییرِ مجاز در یک گام (جلوگیری از پرش‌های ناگهانی)
MAX_STEP: dict[str, float] = {
    "novelty_threshold": 0.15,
    "rho_bias":          0.25,
    "creativity":        0.30,
    "explore_points":    2000,
}


def _protected_roots() -> list[Path]:
    """مسیرهایی که نوشتن در آن‌ها ممنوع است."""
    roots: list[Path] = []
    try:
        from config.settings import SYSTEM_ROOT, REFERENCE_DIR
        roots.append(REFERENCE_DIR)                 # 4D/ مرجعِ immutable
        roots.append(SYSTEM_ROOT / "core")          # مدلِ ریاضیِ دست‌نخوردنی
    except Exception as e:
        logger.warning("guardrails: could not resolve protected roots: %s", e)
    return [r.resolve() for r in roots if r]


def clamp_param(name: str, value: float) -> float:
    """محدودکردن یک پارامتر به بازه‌ی امن."""
    lo, hi = SAFE_PARAM_RANGES.get(name, (float("-inf"), float("inf")))
    return max(lo, min(hi, value))


# ════════════════════════════════════════════════════════════════════════
#  TCB — هسته‌ی موردِاعتماد (Trusted Computing Base)
#
#  وقتی مالک «ویرایشِ کدِ .py» را باز می‌کند، سیستم اجازه دارد فایل‌های .pyِ
#  «برگ» را (فقط با گیتِ آزمون + تأییدِ مالک) پیشنهاد و اعمال کند — اما هرگز
#  نباید بتواند فایل‌هایی را دست بزند که خودِ ایمنی را می‌سازند؛ وگرنه می‌توانست
#  گاردِ خودش را خاموش کند. این فهرست سخت است و خودتغییری هرگز به آن نمی‌رسد.
# ════════════════════════════════════════════════════════════════════════

# فایل‌های منفردِ محافظت‌شده (نسبت به SYSTEM_ROOT)
CODE_TCB_FILES: frozenset[str] = frozenset({
    "run.py",                    # نقطه‌ی ورود + خودترمیمی + encoding
    "brain/guardrails.py",       # همین لایه‌ی گارد
    "brain/self_code.py",        # خطِ لوله‌ی propose→test→approve
    "brain/self_evolve.py",      # گیتِ تحولِ استراتژی
    "brain/budget.py",           # سقفِ بودجه‌ی LLM
    "brain/automation.py",       # ارکستریتور: منطقِ halt/تریگرِ انسانی/چرخه‌ی حالت
    "brain/daemon.py",           # اجراکننده‌ی بی‌مراقبِ ماهانه
    "brain/telegram_bot.py",     # کنترل‌سطحِ تلگرام (owner-only + approve کد)
    "brain/events.py",           # باسِ رویداد/مشاهده‌پذیری (halt/heartbeat)
    "llm/router.py",             # مسیریابی + سقوطِ بودجه (مهارِ هزینه)
    "llm/glm_client.py",         # ثبت/اعمالِ بودجه‌ی ابری
    "llm/fugu_client.py",        # ثبت/اعمالِ بودجه‌ی ابری
    "llm/langchain_models.py",   # مسیرِ ابریِ گراف + سقفِ بودجه
    "config/settings.py",        # مسیرها و تنظیماتِ ایمنی
})

# ریشه‌های محافظت‌شده (کلِ درخت زیرِ این‌ها دست‌نخوردنی)
CODE_TCB_DIR_NAMES: frozenset[str] = frozenset({
    "core",     # مدلِ ریاضی + لنگرها + invariants
    "tests",    # سیستم نباید تست‌های خودش را تضعیف/حذف کند
    "config",   # کلِ config/ (شاملِ __init__.py که در import اجرا می‌شود)
})


def _system_root() -> Path | None:
    try:
        from config.settings import SYSTEM_ROOT
        return SYSTEM_ROOT.resolve()
    except Exception as e:
        logger.error("guardrails: cannot resolve SYSTEM_ROOT: %s", e)
        return None


def _is_tcb_impl(path) -> bool:
    """پیاده‌سازیِ اصلیِ TCB. fail-safe → True.

    هر شکِ محاسباتی (نبودِ ریشه، مسیرِ خارج از پروژه) را «محافظت‌شده» فرض می‌کند.
    نکته‌ی امنیتی: assert_code_target_allowed این نامِ خصوصی را در زمانِ تعریف
    می‌بندد؛ پس rebindِ درون‌فرایندیِ نامِ عمومیِ is_tcb، allow-list را باز نمی‌کند.
    """
    root = _system_root()
    if root is None:
        return True  # fail-safe: نمی‌دانیم کجاست ⇒ محافظت کن
    try:
        p = Path(path).resolve()
    except Exception:
        return True

    # هر __init__.py در زمانِ import اجرا می‌شود و می‌تواند گلوبال‌ها را rebind کند
    # (فرارِ config/__init__.py) → همیشه محافظت‌شده.
    if p.name == "__init__.py":
        return True

    try:
        rel = p.relative_to(root)
    except ValueError:
        return True  # خارج از پروژه = دست‌نخوردنی (شاملِ 4D/ مرجع)

    rel_posix = rel.as_posix()
    if rel_posix in CODE_TCB_FILES:
        return True
    if rel.parts and rel.parts[0] in CODE_TCB_DIR_NAMES:
        return True
    for pr in _protected_roots():
        try:
            p.relative_to(pr)
            return True
        except ValueError:
            continue
    return False


# نامِ عمومی (برای نمایش/تست)؛ گیتِ واقعی از _is_tcb_impl استفاده می‌کند.
def is_tcb(path) -> bool:
    return _is_tcb_impl(path)


def assert_code_target_allowed(path, _is_tcb=_is_tcb_impl) -> tuple[bool, str]:
    """آیا خودتغییریِ کد اجازه دارد این فایلِ .py را هدف بگیرد؟

    قاعده‌ی allow-list سخت‌گیرانه (fail-closed):
      ۱. باید داخلِ پروژه (SYSTEM_ROOT) باشد.
      ۲. باید پسوندِ .py داشته باشد و __init__.py نباشد.
      ۳. نباید در TCB باشد (core/tests/config/گاردها/settings/run).
    `_is_tcb` به‌عنوانِ آرگومانِ پیش‌فرض در زمانِ تعریف بسته می‌شود؛ پس rebindِ
    درون‌فرایندیِ guardrails.is_tcb توسطِ کدِ اعمال‌شده، این گیت را نمی‌شکند.
    """
    root = _system_root()
    if root is None:
        return False, "SYSTEM_ROOT قابلِ‌تعیین نیست (fail-closed)"
    try:
        p = Path(path).resolve()
    except Exception as e:
        return False, f"مسیرِ نامعتبر: {e}"
    if p.suffix != ".py":
        return False, "هدف باید یک فایلِ .py باشد"
    try:
        p.relative_to(root)
    except ValueError:
        return False, "خارج از پروژه"
    if _is_tcb(p):
        return False, "فایلِ هسته‌ی موردِاعتماد (TCB) — خودتغییری ممنوع"
    return True, "مجاز (فایلِ برگ، خارج از TCB)"


def guard_param_change(name: str, old: float, proposed: float) -> tuple[bool, float, str]:
    """
    اعتبارسنجیِ یک تغییرِ پارامتر.

    برمی‌گرداند: (مجاز؟, مقدارِ امن, دلیل)
    - پارامترِ ناشناخته رد می‌شود.
    - مقدار به بازه‌ی امن clamp می‌شود.
    - گامِ بزرگ‌تر از MAX_STEP محدود می‌شود (نه رد).
    """
    if name not in SAFE_PARAM_RANGES:
        return False, old, f"پارامترِ ناشناخته: {name}"

    clamped = clamp_param(name, float(proposed))
    step = abs(clamped - old)
    max_step = MAX_STEP.get(name, float("inf"))

    if step > max_step:
        direction = 1.0 if clamped > old else -1.0
        clamped = clamp_param(name, old + direction * max_step)
        return True, clamped, f"گام به {max_step} محدود شد"

    return True, clamped, "در محدوده‌ی امن"


def assert_safe_write(path) -> tuple[bool, str]:
    """
    آیا نوشتن در این مسیر امن است؟ — سیاستِ allow-list و fail-closed.

    قاعده: نوشتنِ خودمختار فقط داخلِ outputs/ مجاز است، و هرگز روی *.py.
    اگر ریشه‌ی مجاز قابلِ‌تعیین نباشد، fail-closed (رد).
    """
    p = Path(path).resolve()

    # هرگز کدِ منبع (خودویرایشیِ کد ممنوع)
    if p.suffix == ".py":
        return False, "ویرایشِ کدِ منبع (*.py) مجاز نیست"

    # allow-list: فقط داخلِ ناحیه‌ی sandbox (outputs/)
    try:
        from config.settings import OUTPUT_DIR
        out = OUTPUT_DIR.resolve()
    except Exception as e:
        logger.error("assert_safe_write fail-closed: cannot resolve OUTPUT_DIR: %s", e)
        return False, "ریشه‌ی مجاز قابلِ‌تعیین نیست (fail-closed)"

    try:
        p.relative_to(out)
        return True, "مجاز (داخلِ outputs)"
    except ValueError:
        return False, "خارج از ناحیه‌ی مجازِ outputs"


def safe_append(path, text: str) -> tuple[bool, str]:
    """افزودنِ متن به یک فایل، فقط اگر guardrail اجازه دهد."""
    ok, reason = assert_safe_write(path)
    if not ok:
        logger.warning("guardrails BLOCKED write to %s: %s", path, reason)
        return False, reason
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(text)
    return True, "نوشته شد"


def check_invariants() -> dict:
    """
    بررسیِ سلامتِ ثابت‌های سیستم:
      - لنگرهای ریاضیِ core هنوز بازتولید می‌شوند؟
      - دایرکتوریِ مرجعِ immutable سرِ جایش است؟
    """
    anchors_ok = False
    try:
        from core.model import run_self_test
        results = run_self_test()
        anchors_ok = all(err < 1e-4 for _, (_, _, err) in results.items())
    except Exception as e:
        logger.error("invariant check (anchors) failed: %s", e)

    ref_ok = False
    try:
        from config.settings import REFERENCE_DIR
        ref_ok = REFERENCE_DIR.exists()
    except Exception as e:
        logger.error("invariant check (reference) failed: %s", e)

    # ثابتِ سختِ سیستم = بازتولیدِ لنگرهای ریاضی. نبودِ پوشه‌ی مرجعِ اختیاری
    # یک هشدارِ نرم است، نه دلیلِ توقفِ حفاظتی.
    return {
        "anchors_ok": anchors_ok,
        "reference_intact": ref_ok,
        "ok": anchors_ok,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("safe write outputs/x.md :", assert_safe_write("outputs/x.md"))
    print("safe write core/model.py:", assert_safe_write("core/model.py"))
    print("safe write ui/app.py    :", assert_safe_write("ui/app.py"))
    print("clamp novelty 1.5       :", clamp_param("novelty_threshold", 1.5))
    print("guard rho 0.5->2.0      :", guard_param_change("rho_bias", 0.5, 2.0))
    print("invariants              :", check_invariants())
