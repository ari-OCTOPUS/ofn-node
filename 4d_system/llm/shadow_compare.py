"""
llm/shadow_compare.py — مقایسهٔ سایه‌ای (Shadow-Run) دو پشتهٔ LLM — بک‌لاگ B11، فاز ۱.

هدف: این پروژه ۳ پشتهٔ موازی LLM دارد (router با کلاینت‌های httpx خام /
آداپتورهای langchain / فراخوانی‌های مستقیم httpx). یکی‌سازیِ آن‌ها پشتِ یک
interface ریسکِ رفتاری دارد؛ پس اول «شواهد» جمع می‌کنیم: هر دو پشته را روی
پرامپت‌های ثابتِ یکسان اجرا می‌کنیم و واگراییِ خروجی/تأخیر/خطا را در
outputs/llm_shadow.jsonl ثبت می‌کنیم تا تصمیمِ یکی‌سازی بر پایهٔ داده باشد.

قاعده: shadow-first — این ابزار هیچ سوئیچِ زنده‌ای انجام نمی‌دهد، هیچ رفتارِ
جاری‌ای را تغییر نمی‌دهد، و فقط از مسیرِ guardrails داخلِ outputs/ می‌نویسد.

پشته‌ها:
  A) llm.router.get_router().ask(prompt, task="analysis")
     (اگر هیچ مدلی در دسترس نباشد، خودِ router به MockClient برمی‌گردد)
  B) llm.langchain_models.get_default_chat(task="analysis").invoke(prompt)
     (بدون کلید → get_mock_chat؛ بدون langchain → stub داخلیِ stdlib)

نکتهٔ import: سطحِ ماژول فقط stdlib است؛ importهای سنگین (router/langchain/
guardrails) همه داخلِ run_shadow انجام می‌شوند تا importِ بخش‌های خالص
(build_record / summarize) در محیطِ تست هیچ وابستگی‌ای نخواهد.

اجرا:  python -m llm.shadow_compare [--n 3]
"""
from __future__ import annotations

import difflib
import json
import logging
import time
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = ["DEFAULT_PROMPTS", "OUT_FILENAME", "build_record", "run_shadow", "summarize"]

# نام فایلِ شواهد داخلِ outputs/ (مسیرِ کامل در زمانِ اجرا از config.settings می‌آید)
OUT_FILENAME = "llm_shadow.jsonl"

# چند کاراکترِ اولِ خروجی‌ها برای سنجشِ شباهتِ ارزان مقایسه می‌شود
_SIM_PREFIX = 300
# سقفِ متنِ ذخیره‌شده در هر رکورد (خودِ طولِ کامل جداگانه ثبت می‌شود)
_STORE_MAX = 500

# ── پرامپت‌های ثابتِ فاز ۱ (۳ تحلیلیِ فارسی + ۳ واقعی/ساختاریافتهٔ انگلیسی) ──
# ثابت نگه داشتنِ این فهرست عمدی است: مقایسهٔ بینِ اجراها فقط با پرامپتِ
# یکسان معنا دارد. (فاز بعد طبق بک‌لاگ تا ۲۰ پرامپت رشد می‌کند.)
DEFAULT_PROMPTS: tuple[str, ...] = (
    # فارسی — تحلیلی
    "نقش E_shadow را در تشخیص بُعد پنهان تحلیل کن و رابطه‌اش با λρ را گام‌به‌گام توضیح بده.",
    "چرا هم‌ارزی E_shadow > 0 با λρ ≠ 0 هم‌راستا با قضیهٔ Takens است؟ استدلالی کوتاه و دقیق بنویس.",
    "لنگرهای عددی (anchors) مدل SOG را verify کن و نتیجه را به‌صورت جدول PASS/FAIL خلاصه کن.",
    # English — factual / structured
    "List the four core anchor values of the SOG model and verify each one in a two-column table.",
    "Write a short structured report (## headings plus one table) summarizing E_shadow, Delta_self, and I_pred.",
    "Explain in exactly three bullet points how a 4D tesseract's 3D shadow relates to hidden-dimension detection.",
)


# ── بخشِ خالص (بدونِ I/O، بدونِ importِ پروژه) ───────────────────────────────
def _timed_call(fn: Callable[[str], str], prompt: str) -> tuple[dict, str | None]:
    """یک پشته را زمان‌گیری می‌کند؛ هرگز exception بیرون نمی‌دهد.

    برمی‌گرداند: (رکوردِ سمت, متنِ کاملِ خروجی یا None در خطا)
    """
    t0 = time.perf_counter()
    text: str | None = None
    err: str | None = None
    try:
        out = fn(prompt)
        text = out if isinstance(out, str) else str(out)
    except Exception as e:  # نوعِ خطا شاهد است؛ متنِ خطا ممکن است secret نشت دهد
        err = type(e).__name__
    latency = time.perf_counter() - t0
    side = {
        "output": None if text is None else text[:_STORE_MAX],
        "length": None if text is None else len(text),
        "latency_s": round(latency, 6),
        "error": err,
    }
    return side, text


def build_record(prompt: str,
                 run_a: Callable[[str], str],
                 run_b: Callable[[str], str]) -> dict:
    """اجرای هر دو پشته روی یک پرامپت و ساختِ رکوردِ واگرایی. تابعِ خالص.

    شکلِ رکورد:
      {"prompt": str,
       "a": {"output": str|None(≤500), "length": int|None, "latency_s": float, "error": str|None},
       "b": {...همان شکل...},
       "metrics": {"length_ratio": float|None, "similarity": float|None}}

    - error = نامِ نوعِ exception (خروجیِ آن سمت None می‌شود).
    - length_ratio = min/max طولِ کاملِ دو خروجی (هر دو تهی → 1.0).
    - similarity = difflib.SequenceMatcher روی ۳۰۰ کاراکترِ اولِ دو خروجی.
    - هرگز exception بیرون نمی‌دهد.
    """
    a, a_full = _timed_call(run_a, prompt)
    b, b_full = _timed_call(run_b, prompt)

    metrics: dict = {"length_ratio": None, "similarity": None}
    try:
        if a_full is not None and b_full is not None:
            la, lb = len(a_full), len(b_full)
            metrics["length_ratio"] = (
                1.0 if max(la, lb) == 0 else round(min(la, lb) / max(la, lb), 4))
            metrics["similarity"] = round(
                difflib.SequenceMatcher(
                    None, a_full[:_SIM_PREFIX], b_full[:_SIM_PREFIX]).ratio(), 4)
    except Exception:  # سنجه‌ها هرگز رکورد را نمی‌شکنند
        pass

    return {"prompt": prompt, "a": a, "b": b, "metrics": metrics}


def summarize(records: list[dict]) -> dict:
    """جمع‌بندیِ خالصِ رکوردها: شمارش، نرخِ خطا و میانگینِ تأخیر هر پشته، میانگینِ شباهت."""
    n = len(records)
    if n == 0:
        return {"count": 0,
                "error_rate_a": None, "error_rate_b": None,
                "mean_latency_a_s": None, "mean_latency_b_s": None,
                "mean_similarity": None}

    def _side(key: str) -> tuple[float, float | None]:
        errs = sum(1 for r in records if (r.get(key) or {}).get("error") is not None)
        lats = [(r.get(key) or {}).get("latency_s") for r in records]
        lats = [x for x in lats if isinstance(x, (int, float))]
        mean_lat = round(sum(lats) / len(lats), 6) if lats else None
        return round(errs / n, 4), mean_lat

    er_a, lat_a = _side("a")
    er_b, lat_b = _side("b")
    sims = [(r.get("metrics") or {}).get("similarity") for r in records]
    sims = [s for s in sims if isinstance(s, (int, float))]
    return {
        "count": n,
        "error_rate_a": er_a,
        "error_rate_b": er_b,
        "mean_latency_a_s": lat_a,
        "mean_latency_b_s": lat_b,
        "mean_similarity": round(sum(sims) / len(sims), 4) if sims else None,
    }


# ── بخشِ اجرایی (importهای سنگین فقط این‌جا) ────────────────────────────────
def _builtin_stub(side: str) -> Callable[[str], str]:
    """آخرین fallback (stdlib خالص) وقتی حتی ساختِ پشته ممکن نیست — ابزار همیشه اجرا شود."""
    def _stub(prompt: str) -> str:
        return f"[SHADOW-STUB {side}] len={len(prompt)} :: {prompt[:120]}"
    return _stub


def _make_run_a() -> tuple[Callable[[str], str], str]:
    """پشتهٔ A: router.ask(task='analysis'). بدونِ مدلِ زنده، خودِ router → MockClient."""
    try:
        from llm.router import get_router
        router = get_router()
        try:
            _, reason = router.route_explain("analysis")
        except Exception:
            reason = "router"
        def _run_a(prompt: str) -> str:
            return router.ask(prompt, task="analysis")
        return _run_a, f"router[{reason}]"
    except Exception as e:  # مثلاً نبودِ httpx در محیط
        logger.warning("stack A unavailable (%s) → builtin stub", type(e).__name__)
        return _builtin_stub("A"), f"stub[{type(e).__name__}]"


def _make_run_b() -> tuple[Callable[[str], str], str]:
    """پشتهٔ B: آداپتورِ langchain. بدونِ کلید → mock chat؛ بدونِ langchain → stub."""
    chat = None
    label = ""
    try:
        from llm.langchain_models import get_default_chat
        chat = get_default_chat(task="analysis")
        label = f"langchain[{type(chat).__name__}]"
    except Exception as e1:
        try:
            from llm.langchain_models import get_mock_chat
            chat = get_mock_chat()
            label = "langchain[mock]"
        except Exception as e2:
            logger.warning("stack B unavailable (%s/%s) → builtin stub",
                           type(e1).__name__, type(e2).__name__)
            return _builtin_stub("B"), f"stub[{type(e2).__name__}]"

    def _run_b(prompt: str) -> str:
        resp = chat.invoke(prompt)
        content = getattr(resp, "content", resp)
        return content if isinstance(content, str) else str(content)

    return _run_b, label


def _append_jsonl(record: dict) -> bool:
    """ثبتِ پایدارِ یک رکورد — فقط از مسیرِ guardrails (allow-list: outputs/)."""
    try:
        from config.settings import OUTPUT_DIR
        from brain import guardrails
        line = json.dumps(record, ensure_ascii=False) + "\n"
        ok, reason = guardrails.safe_append(OUTPUT_DIR / OUT_FILENAME, line)
        if not ok:
            logger.warning("shadow record blocked: %s", reason)
        return ok
    except Exception as e:  # ثبت‌نشدن هرگز اجرای مقایسه را نمی‌شکند
        logger.error("shadow record persist failed: %s", type(e).__name__)
        return False


def run_shadow(prompts: list[str] | None = None, n: int | None = None) -> list[dict]:
    """اجرای سایه‌ایِ هر دو پشته روی پرامپت‌های ثابت و ثبتِ شواهد.

    - prompts=None → DEFAULT_PROMPTS (۶ پرامپتِ ثابت).
    - n → محدودکردنِ تعدادِ پرامپت‌ها (برای تستِ سریع/ارزان).
    - هر رکورد یک خطِ JSON در outputs/llm_shadow.jsonl (utf-8، ensure_ascii=False).
    - اگر پشته‌ای در دسترس نباشد به mock/stub برمی‌گردد — ابزار همیشه اجرا می‌شود.
    """
    plist = list(prompts) if prompts is not None else list(DEFAULT_PROMPTS)
    if n is not None:
        plist = plist[:max(0, int(n))]

    run_a, label_a = _make_run_a()
    run_b, label_b = _make_run_b()
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    logger.info("shadow-run %s: %d prompt(s) | A=%s | B=%s",
                run_id, len(plist), label_a, label_b)

    records: list[dict] = []
    for i, prompt in enumerate(plist):
        rec = build_record(prompt, run_a, run_b)
        # متادادهٔ اجرا (افزودنی؛ build_record خالص می‌ماند)
        rec["run_id"] = run_id
        rec["idx"] = i
        rec["ts"] = datetime.now().isoformat(timespec="seconds")
        rec["stack_a"] = label_a
        rec["stack_b"] = label_b
        _append_jsonl(rec)
        records.append(rec)
        logger.info("  [%d/%d] err_a=%s err_b=%s sim=%s",
                    i + 1, len(plist), rec["a"]["error"], rec["b"]["error"],
                    rec["metrics"]["similarity"])
    return records


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="B11 فاز ۱ — shadow-run: مقایسهٔ دو پشتهٔ LLM روی پرامپت‌های ثابت (بدونِ سوئیچِ زنده)")
    parser.add_argument("--n", type=int, default=None,
                        help="محدودکردنِ تعدادِ پرامپت‌ها (پیش‌فرض: هر ۶)")
    args = parser.parse_args()

    recs = run_shadow(n=args.n)
    print(json.dumps(summarize(recs), ensure_ascii=False, indent=2))
    try:
        from config.settings import OUTPUT_DIR
        print(f"records → {OUTPUT_DIR / OUT_FILENAME}")
    except Exception:
        pass
