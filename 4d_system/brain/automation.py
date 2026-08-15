"""
brain/automation.py — موتورِ اتوماسیونِ خودمختار (بدونِ گیتِ تایید).

سیستم خودش تصمیم می‌گیرد و پیش می‌رود؛ در هر «tick» یکی از حالت‌های زیر را اجرا
می‌کند و رویدادِ ساختاریافته منتشر می‌کند:

  explore   — کاوشِ داده و کشفِ الگو
  introspect— «خودخوانی»: مطالعه‌ی ساختارِ خود (self-model)
  create    — «خلاقیت»: تولید و ثبتِ فرضیه/ایده‌ی جدید
  mutate    — «خودتنظیمی»: تغییرِ استراتژیِ کاوش (از میان guardrails)
  guard     — «محافظ»: بررسیِ سلامتِ لنگرها و immutableها؛ در صورتِ نقض، توقفِ حفاظتی

«پرریسک ولی محافظت‌شده»: خودمختاریِ کامل، اما هر تغییر از لایه‌ی brain/guardrails
عبور می‌کند — بدونِ ویرایشِ کدِ منبع، بدونِ نوشتن در immutableها، پارامترها محدود.

این ماژول Streamlit-agnostic و قابل‌تست است.
"""
from __future__ import annotations

import time
import random
import logging
from datetime import datetime
from typing import Optional

from brain import events
from brain import guardrails

logger = logging.getLogger(__name__)

HEARTBEAT_SECONDS = 300

# ترتیبِ حالت‌ها — اولویت: Brain-OS (تصمیمِ کاربر ۲۰۲۶-۰۷-۱۱).
# وزنِ بیشتر به خودخوانی/خلاقیت/خودتحول/نتیجه‌گیری؛ کاوشِ داده در حدِ
# تغذیه‌ی فرضیه‌ها نگه داشته می‌شود (SOG در دفترِ هدف‌ها زنده می‌ماند).
_MODE_CYCLE = [
    "introspect", "create", "explore", "evolve",
    "real", "create", "conclude", "synthesize", "kernel_consult",
    "introspect", "evolve", "mutate", "real", "guard",
]

# موادِ خامِ خلاقیت
_CONCEPTS = [
    "حافظه‌ی اپیزودیک", "کنجکاویِ ذاتی", "خودتنظیمیِ نرخِ یادگیری",
    "تشخیصِ الگویِ نوظهور", "حافظه‌ی فشرده‌ی برداری", "پایشِ اعتماد",
    "کشفِ روابطِ سببی", "بازتابِ چندلایه", "توجهِ انتخابی به سایه",
    "خوشه‌بندیِ ریتم‌ها",
]
_TEMPLATES = [
    "اگر «{c}» را به لوپ اضافه کنیم، آیا محدودیتِ «{lim}» جبران می‌شود؟",
    "آیا «{c}» می‌تواند کشفِ بُعدِ پنهان را در سری‌های ضعیف‌تر ممکن کند؟",
    "فرضیه: ترکیبِ «{c}» با پایشِ novelty، نرخِ کشفِ واقعی را بالا می‌برد.",
    "آیا «{c}» به سیستم کمک می‌کند «{lim}» را به توانمندی تبدیل کند؟",
    "بررسی: «{c}» به‌عنوان سیگنالِ کمکی برای تفکیکِ الگو از نوفه.",
]
_FALLBACK_LIMS = ["یادگیریِ offline", "پردازشِ فقط عددی", "نبودِ حافظه‌ی بلندمدت"]

# جهانِ دادهٔ واقعی — گسترده و چرخشی (سهام، شاخص، کریپتو، کالا، ارز) × بازه‌های زمانی.
# تیکر × بازه = ده‌ها سری‌زمانیِ واقعیِ متمایز؛ قابلِ گسترش تا هر اندازه.
_REAL_TICKERS = [
    "^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^FTSE", "^N225",
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "XOM", "KO",
    "BTC-USD", "ETH-USD", "SOL-USD", "GLD", "SLV", "USO", "TLT", "EURUSD=X", "JPY=X",
]
_REAL_PERIODS = ["1y", "2y", "5y"]


class AutomationController:
    """موتورِ خودمختار — هر بار یک حالت اجرا و رویداد منتشر می‌کند."""

    def __init__(self, use_llm: bool = False, novelty_threshold: float = 0.85):
        from brain.autoloop import AutoLoopEngine, AutoLoopConfig
        self.engine = AutoLoopEngine(AutoLoopConfig(auto_save=True, use_llm=use_llm))

        # استراتژیِ تکامل‌یافته را از sandbox بارگذاری کن («کدِ رفتاریِ» خودنوشته)
        from brain import self_evolve
        self.evolved = self_evolve.load_strategy()

        # استراتژیِ خودتنظیم‌شونده (همه در بازه‌ی امنِ guardrails)
        self.strategy = {
            "novelty_threshold": guardrails.clamp_param(
                "novelty_threshold", self.evolved.get("novelty_threshold", novelty_threshold)),
            "rho_bias":   guardrails.clamp_param("rho_bias", self.evolved.get("rho_bias", 0.50)),
            "creativity": guardrails.clamp_param("creativity", self.evolved.get("creativity", 0.50)),
        }
        self._apply_evolved()         # explore_points / source_policy → موتور

        # دستورکارِ پژوهشیِ Brain-OS را (یک‌بار) در حافظه بکار (idempotent)
        try:
            from brain import research_agenda
            research_agenda.seed_hypotheses_into_store()
        except Exception as e:
            logger.warning("agenda seed failed: %s", e)

        self.iteration = 0            # شمارِ کاوش‌ها
        self._mode_i = 0
        self._intro_i = 0
        self._create_i = 0
        self._mut_i = 0
        self._evolve_seed = 0
        self._synth_i = 0
        self._real_i = 0
        self._focus_limitation = ""
        self._fail_streak = 0          # برای هشدارِ «failure تکرارشونده»
        self._last_milestone = 0       # آخرین milestoneِ پوششِ اعلام‌شده
        self._last_heartbeat: Optional[datetime] = None

    def _apply_evolved(self) -> None:
        """اعمالِ استراتژیِ تکامل‌یافته روی موتور (طولِ کاوش و سیاستِ منبع)."""
        try:
            self.engine.config.explore_points = int(self.evolved.get("explore_points", 3000))
            pol = self.evolved.get("source_policy")
            if isinstance(pol, list) and pol:
                self.engine.config.sources = list(pol)
        except Exception as e:
            logger.warning("apply_evolved failed: %s", e)

    # ── حلقه‌ی اصلی ──────────────────────────────────────────────────────
    def run_one(self) -> dict:
        """اجرای یک گام بر اساسِ حالتِ بعدی. Tier 1 خودکار؛ triggerهای انسانی فعال."""
        mode = _MODE_CYCLE[self._mode_i % len(_MODE_CYCLE)]
        self._mode_i += 1
        try:
            result = getattr(self, f"_job_{mode}")()
        except Exception as e:            # backstop — هیچ حالتی کلِ لوپ را نمی‌شکند
            logger.error("job %s crashed: %s", mode, e)
            events.emit("task.failed", f"خطای داخلی در حالتِ {mode}: {type(e).__name__}",
                        status="error", agent_id=mode, next_action="ادامه")
            result = {"ok": False, "mode": mode}

        self._human_triggers(result)
        return result

    def _human_triggers(self, result: dict) -> None:
        """triggerهای دکترینِ Hybrid: failure تکرارشونده + milestone (Tier 2 notify)."""
        try:
            from brain import notify
            # failure تکرارشونده → warning (یک‌بار به‌ازای هر رشته)
            if result.get("ok") is False:
                self._fail_streak += 1
                if self._fail_streak == 3:
                    notify.send_packet(
                        "warning",
                        f"لوپِ خودمختار — حالتِ {result.get('mode','?')}",
                        "۳ شکستِ پیاپی رخ داد (failure تکرارشونده)",
                        "لاگِ داشبورد را ببین؛ اگر ادامه داشت «توقف و صفر» بزن",
                        "لوپ ادامه می‌دهد ولی ممکن است دادهٔ کمتری جمع شود",
                    )
            else:
                self._fail_streak = 0

            # milestone: هر ۲۰ ناحیه‌ی جدیدِ مرزِ دانش → خلاصه (قالبِ پیش‌فرضِ دکترین)
            from brain import frontier
            cov = frontier.coverage()
            if cov >= self._last_milestone + 20:
                self._last_milestone = (cov // 20) * 20
                s = events.get_summary(300)
                notify.send_packet(
                    "summary",
                    "milestone مرزِ دانش",
                    f"پوشش به {cov} رفتارِ متمایز رسید",
                    f"الان: کاوشِ خودمختار · تمام شد: {cov} ناحیه · "
                    f"گیر: {s['errors']} خطا · ریسک: پایین · نیاز به تو: هیچ",
                    "ادامه‌ی خودکار — فقط برای اطلاع",
                )
        except Exception as e:
            logger.warning("human trigger failed: %s", e)

    # ── explore: کاوشِ داده ──────────────────────────────────────────────
    def _job_explore(self) -> dict:
        trace = events.new_trace_id()
        n = self.iteration + 1
        events.emit("task.started", f"کاوش #{n}: تولید و تحلیلِ سری زمانی",
                    status="info", agent_id="explore", trace_id=trace,
                    next_action="در حال اجرا", approval_state="not_required")
        t0 = time.perf_counter()
        try:
            result = self.engine.run_step(self.iteration, past_results=self.engine.history)
        except Exception as e:
            self.iteration += 1
            events.emit("task.failed", f"خطا در کاوش #{n}: {type(e).__name__}",
                        status="error", agent_id="explore", trace_id=trace,
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        next_action="retry", approval_state="not_required")
            return {"ok": False, "mode": "explore"}

        dur = int((time.perf_counter() - t0) * 1000)
        self.iteration += 1

        if result.source == "error":
            events.emit("task.failed", f"دادهٔ نامعتبر رد شد (#{n})", status="retry",
                        agent_id="explore", trace_id=trace, duration_ms=dur,
                        next_action="retry", approval_state="not_required")
            return {"ok": False, "mode": "explore"}

        mi = result.scores.get("temporal_mi", 0.0)
        rho = result.scores.get("rho_hat", 0.0)
        kurt = result.scores.get("kurtosis", 0.0)
        det = result.scores.get("detectable", False)
        src = result.source
        notable = result.novelty >= self.strategy["novelty_threshold"]
        star = "⭐ " if notable else ""

        # ثبت در مرزِ دانش — پیشرفتِ واقعیِ انباشتی (رشدِ پوشش)
        frontier_note = ""
        try:
            from brain import frontier
            rec = frontier.record(src, mi, rho, kurt, det)
            if rec["new_cell"]:
                frontier_note = " · 🗺️ ناحیه‌ی نو"
                events.emit("handoff.created",
                            f"مرزِ دانش گسترش یافت → {frontier.coverage()} ناحیه ({src})",
                            status="ok", agent_id="frontier", trace_id=trace,
                            approval_state="not_required")
            elif rec["improved"]:
                frontier_note = " · 🗺️ بهبودِ ناحیه"
        except Exception as e:
            logger.warning("frontier.record failed: %s", e)

        if result.saved:
            events.emit("handoff.created", f"یادداشتِ Obsidian ساخته شد: {src}",
                        status="ok", agent_id="vault", trace_id=trace,
                        approval_state="not_required")

        events.emit(
            "task.completed",
            f"{star}{'کشف ذخیره شد' if result.saved else 'بدون کشفِ جدید'}: "
            f"{src} · MI={mi:.4f} · {'قابل‌تشخیص ✅' if det else 'نامرئی'}{frontier_note}",
            status="ok", agent_id="explore", trace_id=trace, duration_ms=dur,
            next_action="ادامه", approval_state="not_required",
        )
        return {"ok": True, "mode": "explore", "summary": src, "notable": notable}

    # ── real: کاوشِ دادهٔ واقعیِ خارجی (تازگیِ بی‌پایان — نه خودساخته) ────────
    def _job_real(self) -> dict:
        import numpy as np
        from brain import frontier
        events.emit("task.started",
                    "کاوشِ واقعی: دریافتِ سری‌زمانیِ دنیای واقعی (بورس/آب‌وهوا)",
                    status="info", agent_id="real", approval_state="not_required")
        try:
            from data.real_api import fetch_real
            # جهانِ چندمنبعیِ رسمیِ keyless: ارز (ECB) + کریپتو + آب‌وهوا + سهام.
            # هر منبع cache روزانه + throttle دارد (استفاده‌ی اصولی از API).
            i = self._real_i
            self._real_i += 1
            res = fetch_real(i)
            name = res.get("label", "real")

            series = np.asarray(res.get("series"), dtype=float)
            src_kind = res.get("source", "real")

            if series.size < 20 or not np.all(np.isfinite(series)):
                events.emit("task.failed", f"دادهٔ واقعی نامعتبر ({name})",
                            status="retry", agent_id="real", approval_state="not_required")
                return {"ok": False, "mode": "real"}

            from core.metrics import empirical_shadow, fit_shadow_parameters
            shadow = empirical_shadow(series)
            fit = fit_shadow_parameters(series)
            mi = float(shadow["temporal_mi"])
            rho = float(fit["rho_hat"])
            det = bool(fit.get("detectable"))
            m = float(series.mean()); v = float(series.var())
            kurt = float(((series - m) ** 4).mean() / (v ** 2) - 3.0) if v > 1e-12 else 0.0

            # اگر شبکه نبود و fallback مصنوعی شد، خانواده را صادقانه synthetic بگذار
            fam = "real" if not str(src_kind).startswith("synthetic") else "synthetic"
            src = f"{fam}:{name}"
            fallback_flag = "" if fam == "real" else " ⚠️(fallback مصنوعی — شبکه در دسترس نبود)"

            rec = frontier.record(src, mi, rho, kurt, det)
            if rec["new_cell"]:
                note = " · 🗺️ ناحیه‌ی نو"
                events.emit("handoff.created",
                            f"مرزِ دانش با دادهٔ واقعی گسترش یافت → {frontier.coverage()} ناحیه ({src})",
                            status="ok", agent_id="frontier", approval_state="not_required")
            elif rec["improved"]:
                note = " · 🗺️ بهبودِ ناحیه"
            else:
                note = " · تکراری"

            events.emit("task.completed",
                        f"واقعی: {name} · MI={mi:.4f} · کشیدگی={kurt:.1f}{note}{fallback_flag}",
                        status="ok", agent_id="real", next_action="ادامه",
                        approval_state="not_required")
            return {"ok": True, "mode": "real", "new": rec["new_cell"]}
        except Exception as e:
            logger.error("real explore failed: %s", e)
            events.emit("task.failed", f"خطا در کاوشِ واقعی: {type(e).__name__}",
                        status="error", agent_id="real", approval_state="not_required")
            return {"ok": False, "mode": "real"}

    # ── synthesize: ساختِ آزمایشِ هدفمند (کنجکاوی — نواحیِ خالیِ مرز را پر کن) ──
    def _job_synthesize(self) -> dict:
        import numpy as np
        from collections import Counter
        from brain import frontier
        events.emit("task.started",
                    "ساختِ آزمایش: تولیدِ داده‌ی پارامتریکِ هدفمند برای ناحیه‌ی خالی",
                    status="info", agent_id="synthesize", approval_state="not_required")
        try:
            from data.synthetic import ar1_plus_noise, arma11
            from core.metrics import empirical_shadow, fit_shadow_parameters

            # کنجکاوی: کم‌پوشش‌ترین باندِ ρ را هدف بگیر
            archive = frontier.load_frontier()
            band_counts = Counter()
            for key in archive:
                for p in key.split("|"):
                    if p.startswith("rho") and p[3:].isdigit():
                        band_counts[int(p[3:])] += 1
            n_bands = len(frontier.RHO_EDGES) + 1
            target = min(range(n_bands), key=lambda i: band_counts.get(i, 0))

            rng = np.random.default_rng(self._synth_i * 101 + 3)
            self._synth_i += 1
            edges = [0.0] + list(frontier.RHO_EDGES) + [0.98]
            lo, hi = edges[target], edges[min(target + 1, len(edges) - 1)]
            rho = float(rng.uniform(lo, min(hi, 0.95)))
            noise = float(rng.uniform(0.05, 0.6))
            n = int(getattr(self.engine.config, "explore_points", 1500)) or 1500
            seed = int(rng.integers(0, 999999))

            if self._synth_i % 2:
                series = ar1_plus_noise(n, rho=rho, noise_sigma=noise, seed=seed)
                gen = "AR1+noise"
            else:
                series = arma11(n, rho=rho, theta=float(rng.uniform(0, 0.5)), seed=seed)
                gen = "ARMA11"

            series = np.asarray(series, dtype=float)
            if series.size < 20 or not np.all(np.isfinite(series)):
                events.emit("task.failed", "دادهٔ ساخته‌شده نامعتبر", status="retry",
                            agent_id="synthesize", approval_state="not_required")
                return {"ok": False, "mode": "synthesize"}

            shadow = empirical_shadow(series)
            fit = fit_shadow_parameters(series)
            mi = float(shadow["temporal_mi"])
            rho_hat = float(fit["rho_hat"])
            det = bool(fit.get("detectable"))
            m = float(series.mean()); v = float(series.var())
            kurt = float(((series - m) ** 4).mean() / (v ** 2) - 3.0) if v > 1e-12 else 0.0
            src = f"synthetic:{gen}(ρ={rho:.2f})"

            rec = frontier.record(src, mi, rho_hat, kurt, det)
            if rec["new_cell"]:
                note = " · 🗺️ ناحیه‌ی نو"
                events.emit("handoff.created",
                            f"مرزِ دانش گسترش یافت → {frontier.coverage()} ناحیه ({src})",
                            status="ok", agent_id="frontier", approval_state="not_required")
            elif rec["improved"]:
                note = " · 🗺️ بهبودِ ناحیه"
            else:
                note = " · تکراری"

            events.emit("task.completed", f"ساختِ هدفمند: {src} · MI={mi:.4f}{note}",
                        status="ok", agent_id="synthesize", next_action="ادامه",
                        approval_state="not_required")
            return {"ok": True, "mode": "synthesize", "summary": src, "new": rec["new_cell"]}
        except Exception as e:
            logger.error("synthesize failed: %s", e)
            events.emit("task.failed", f"خطا در ساختِ آزمایش: {type(e).__name__}",
                        status="error", agent_id="synthesize", approval_state="not_required")
            return {"ok": False, "mode": "synthesize"}

    # ── introspect: خودخوانی ─────────────────────────────────────────────
    def _job_introspect(self) -> dict:
        trace = events.new_trace_id()
        events.emit("task.started", "خودخوانی: مطالعه‌ی ساختارِ خود",
                    status="info", agent_id="introspect", trace_id=trace,
                    approval_state="not_required")
        # C-012 فاز صفر: پیش از تصمیم، حافظه خوانده می‌شود (تجربهٔ گذشته + آمار).
        mem_note = ""
        try:
            from brain import memory_read_patch as mrp
            mem = mrp.patch_introspect(self, trace_id=trace)
            stats = mem.get("stats") or {}
            mem_note = (f" · حافظه: {mem['past']} تجربهٔ گذشته · "
                        f"{stats.get('hypotheses', '?')} فرضیه")
        except Exception as e:
            logger.warning("introspect memory read failed: %s", e)
        try:
            from brain.self_model import build_self_map
            sm = build_self_map()
        except Exception as e:
            events.emit("task.failed", f"خودخوانی ناموفق: {type(e).__name__}",
                        status="error", agent_id="introspect", trace_id=trace)
            return {"ok": False, "mode": "introspect"}

        lims = sm.limitations or []
        lim = lims[self._intro_i % len(lims)] if lims else ""
        self._intro_i += 1
        self._focus_limitation = lim

        events.emit(
            "task.completed",
            f"خودخوانی: {sm.total_files} فایل · {sm.total_functions} تابع · "
            f"{len(sm.capabilities)} توان · {len(lims)} محدودیت{mem_note}",
            status="ok", agent_id="introspect", trace_id=trace,
            next_action="هدفِ خلاقیت",
            approval_state="not_required",
        )
        if lim:
            events.emit("handoff.created", f"محدودیتِ هدفِ بعدی: {lim[:60]}",
                        status="info", agent_id="introspect", approval_state="not_required")
        return {"ok": True, "mode": "introspect", "summary": "self-map"}

    # ── create: خلاقیت ───────────────────────────────────────────────────
    def _creative_idea(self) -> str:
        # ایده‌ها از دستورکارِ پژوهشیِ «Brain-OS» تغذیه می‌شوند تا روی مسیر بمانند
        from brain import research_agenda as ra
        rng = random.Random(self._create_i * 131 + 7)
        self._create_i += 1
        c = rng.choice(ra.CONCEPTS_FA)
        goal = rng.choice(ra.GOAL_PHRASES_FA)
        try:
            return rng.choice(ra.TEMPLATES_FA).format(c=c, goal=goal)
        except Exception:
            return f"آیا «{c}» می‌تواند «{goal}» را بهبود دهد؟"

    def _job_create(self) -> dict:
        trace = events.new_trace_id()
        events.emit("task.started", "خلاقیت: تولیدِ ایده‌ی پژوهشیِ جدید",
                    status="info", agent_id="creative", trace_id=trace,
                    approval_state="not_required")
        idea = self._creative_idea()

        # C-012 فاز صفر: پیش از ثبت، صفِ فرضیه‌های pending خوانده می‌شود —
        # dedup (همان بیماریِ ۱۰۶۲ فرضیهٔ ثبت‌شدهٔ هرگز-مصرف‌نشده) + شمارشِ stale.
        hid = None
        dedup_note = ""
        stale_note = ""
        try:
            from brain import memory_read_patch as mrp
            pending = mrp.read_pending_hypotheses(200, trace_id=trace)
            stale, fresh = mrp.split_stale(pending)
            if stale:
                stale_note = f" · صفِ راکد: {len(stale)} فرضیهٔ بالای {mrp.STALE_DAYS_DEFAULT} روز"
            if mrp.is_duplicate_hypothesis(idea, pending):
                dedup_note = " · تکراری — ثبت نشد (dedup)"
                events.emit(
                    "task.completed",
                    f"ایدهٔ تکراری رد شد: {idea[:60]}{stale_note}{dedup_note}",
                    status="ok", agent_id="creative", trace_id=trace,
                    next_action="ایدهٔ بعدی", approval_state="not_required",
                )
                return {"ok": True, "mode": "create", "summary": "dedup",
                        "dedup_skipped": True}
        except Exception as e:
            logger.warning("create memory read failed: %s", e)

        try:
            from memory.store import save_hypothesis
            hid = save_hypothesis(
                domain="autonomous-creative", hypothesis=idea,
                rationale=f"خودتولید · creativity={self.strategy['creativity']:.2f}",
            )
        except Exception as e:
            logger.error("save_hypothesis failed: %s", e)

        # read-back از مسیرِ مصرف‌کننده — نوشتهٔ خوانده‌نشده اعتماد ندارد.
        readback_note = ""
        if hid:
            try:
                from brain import memory_read_patch as mrp
                if not mrp.readback_hypothesis(hid, trace_id=trace):
                    logger.error("readback failed for hypothesis #%s", hid)
                    readback_note = " · ⚠️ read-back ناموفق"
            except Exception as e:
                logger.warning("readback check failed: %s", e)

        # نوشتنِ ایده در لاگِ محافظت‌شده (guardrail مسیر را تایید می‌کند)
        try:
            from config.settings import OUTPUT_DIR
            guardrails.safe_append(
                OUTPUT_DIR / "autonomous_ideas.md",
                f"- {datetime.now().isoformat(timespec='seconds')} · {idea}\n",
            )
        except Exception as e:
            logger.error("idea log write failed: %s", e)

        if hid:
            events.emit("handoff.created", f"فرضیه #{hid} ثبت شد",
                        status="ok", agent_id="creative", trace_id=trace,
                        approval_state="not_required")
        events.emit("task.completed", f"ایده‌ی جدید: {idea[:60]}{stale_note}{readback_note}",
                    status="ok", agent_id="creative", trace_id=trace,
                    next_action="آزمونِ آینده",
                    approval_state="not_required")
        return {"ok": True, "mode": "create", "summary": idea[:40]}

    # ── mutate: خودتنظیمی (از میانِ guardrails) ──────────────────────────
    def _propose_change(self) -> tuple[str, float]:
        s = events.get_summary(300)
        name = ["novelty_threshold", "rho_bias", "creativity"][self._mut_i % 3]
        self._mut_i += 1
        old = self.strategy[name]
        if name == "novelty_threshold":
            # کشفِ کم ⇒ آستانه را پایین بیاور تا بیشتر سطحی شود؛ کشفِ زیاد ⇒ سخت‌گیرتر
            proposed = old - 0.05 if s["completed"] < 2 else old + 0.05
        elif name == "rho_bias":
            proposed = old + 0.10 if (self._mut_i % 2 == 0) else old - 0.10
        else:  # creativity به سمتِ ۰.۷ میل کند
            proposed = old + 0.10 if old < 0.70 else old - 0.05
        return name, proposed

    def _apply_strategy(self) -> None:
        """اعمالِ استراتژی روی موتور — سوگیریِ منابع بر اساسِ rho_bias."""
        r = self.strategy["rho_bias"]
        if r >= 0.60:      # حافظه‌ی بالا ⇒ سیستم‌های فیزیکی
            self.engine.config.sources = ["physical", "physical", "synthetic", "physical"]
        elif r <= 0.30:
            self.engine.config.sources = ["synthetic", "synthetic", "physical", "synthetic"]
        else:
            self.engine.config.sources = ["synthetic", "physical", "synthetic", "physical"]

    def _job_mutate(self) -> dict:
        events.emit("task.started", "خودتنظیمی: بازبینیِ استراتژیِ کاوش",
                    status="info", agent_id="mutate", approval_state="not_required")
        name, proposed = self._propose_change()
        old = self.strategy[name]
        ok, safe, reason = guardrails.guard_param_change(name, old, proposed)

        if not ok:
            events.emit("task.blocked", f"تغییرِ ناامن مسدود شد: {name} ({reason})",
                        status="blocked", agent_id="guardrail", next_action="نادیده",
                        approval_state="not_required")
            return {"ok": True, "mode": "mutate", "summary": "blocked"}

        self.strategy[name] = safe
        self._apply_strategy()
        events.emit("task.completed",
                    f"استراتژی عوض شد: {name}: {old:.2f} → {safe:.2f} ({reason})",
                    status="ok", agent_id="mutate", next_action="اعمال شد",
                    approval_state="not_required")
        return {"ok": True, "mode": "mutate", "summary": f"{name}={safe:.2f}"}

    # ── evolve: خودتحولِ راستی‌آزمایی‌شده («اول تست، بعد تغییر») ──────────
    def _job_evolve(self) -> dict:
        from brain import self_evolve
        events.emit("task.started",
                    "خودتحول: پیشنهادِ تغییر و آزمونِ آن (اول تست)",
                    status="info", agent_id="evolve", approval_state="not_required")
        try:
            # B9: با EVOLVE_REQUIRE_APPROVAL=1 کاندیدای قبول‌شده اعمال نمی‌شود؛
            # فقط پیشنهاد ثبت و اطلاع داده می‌شود. پیش‌فرض: خاموش (خودمختار).
            import os as _os
            _need_ok = _os.getenv("EVOLVE_REQUIRE_APPROVAL", "0") == "1"
            r = self_evolve.evolve(seed=self._evolve_seed, n_experiments=3,
                                   apply=not _need_ok)
        except Exception as e:
            events.emit("task.failed", f"خطا در خودتحول: {type(e).__name__}: {e}",
                        status="error", agent_id="evolve", approval_state="not_required")
            return {"ok": False, "mode": "evolve"}
        self._evolve_seed += 1

        rep = r["report"]
        test_line = (f"لنگرها={'✓' if rep['anchors_ok'] else '✗'} · "
                     f"تجربه={rep['valid_fraction']:.0%} معتبر · "
                     f"تازگی={rep.get('open_score', 0):.1f} "
                     f"(+{rep.get('new_cells', 0)} ناحیه)")

        if r["applied"]:
            # استراتژیِ تاییدشده را بارگذاری و اعمال کن
            self.evolved = self_evolve.load_strategy()
            self._apply_evolved()
            self.strategy["novelty_threshold"] = self.evolved.get(
                "novelty_threshold", self.strategy["novelty_threshold"])
            events.emit("handoff.created",
                        f"استراتژی تکامل یافت → نسل {r.get('generation', '?')}",
                        status="ok", agent_id="evolve", approval_state="not_required")
            events.emit("task.completed",
                        f"✅ تغییر پس از آزمون اعمال شد: {r['desc']} · {test_line}",
                        status="ok", agent_id="evolve", next_action="اعمال شد",
                        approval_state="not_required")
            # Tier 2 — NOTIFY: تغییرِ رفتاریِ سیستم اعمال شد (برگشت‌پذیر با backup)
            try:
                from brain import notify
                notify.send_packet(
                    "notify", "خودتحولِ تست‌شده",
                    f"استراتژیِ سیستم عوض شد: {r['desc']} (نسل {r.get('generation','?')})",
                    "تغییر از گیتِ آزمون (لنگرها+تجربه) گذشته؛ نیازی به اقدام نیست",
                    "ادامه‌ی خودکار — backup برای rollback موجود است",
                )
            except Exception:
                pass
        elif r.get("proposed"):
            # B9: کاندیدا از گیتِ آزمون گذشت ولی طبقِ فلگ، منتظرِ تأییدِ مالک است
            events.emit("approval.required",
                        f"🕓 پیشنهادِ خودتحول منتظرِ تأیید: {r['desc']} · {test_line}",
                        status="warning", agent_id="evolve",
                        approval_state="required")
            try:
                from brain import notify
                notify.send_packet(
                    "approval", "خودتحول: نیازمندِ تأییدِ مالک",
                    f"کاندیدا از گیتِ آزمون گذشت: {r['desc']}",
                    "بازبینی: outputs/self_evolved/strategy_proposed.json",
                    "تا تأیید نکنی هیچ تغییری روی رفتارِ زنده اعمال نمی‌شود",
                )
            except Exception:
                pass
        else:
            events.emit("task.blocked",
                        f"⛔ تغییر رد شد ({r['reason']}) · {test_line} — استراتژی دست‌نخورده",
                        status="blocked", agent_id="evolve", next_action="بازگردانی",
                        approval_state="not_required")
        return {"ok": True, "mode": "evolve", "summary": r["desc"]}

    # ── conclude: نتیجه‌گیریِ ریاضی (اعمالِ مدلِ SOG روی داده‌ها) ──────────
    def _job_conclude(self) -> dict:
        from brain import conclusions
        trace = events.new_trace_id()
        events.emit("task.started",
                    "نتیجه‌گیریِ ریاضی: اعمالِ مدلِ SOG روی داده‌های جمع‌شده",
                    status="info", agent_id="conclude", trace_id=trace,
                    approval_state="not_required")
        # C-012 فاز صفر: پیش از نتیجه‌گیری، بافتِ مشابه از والت خوانده می‌شود.
        ctx_note = ""
        try:
            from brain import memory_read_patch as mrp
            ctx = mrp.patch_conclude(self, topic=self._focus_limitation or "SOG",
                                     trace_id=trace)
            ctx_note = f" · بافتِ والت: {ctx.get('vault', 0)} قطعه"
        except Exception as e:
            logger.warning("conclude memory read failed: %s", e)
        try:
            c = conclusions.synthesize_conclusions()
            conclusions.save_conclusions(c)
        except Exception as e:
            logger.error("conclude failed: %s", e)
            events.emit("task.failed", f"خطا در نتیجه‌گیری: {type(e).__name__}",
                        status="error", agent_id="conclude", trace_id=trace,
                        approval_state="not_required")
            return {"ok": False, "mode": "conclude"}

        lines = c.get("conclusions_fa", [])
        # سرخطِ نتیجه = قضیه‌ی شناسایی اگر بود، وگرنه اولین نتیجه‌گیری
        head = next((l for l in lines if "قضیه‌ی شناسایی" in l), lines[0] if lines else "—")
        events.emit("task.completed", f"نتیجه: {head[:130]}{ctx_note}",
                    status="ok", agent_id="conclude", trace_id=trace,
                    next_action="ادامه", approval_state="not_required")
        return {"ok": True, "mode": "conclude"}

    # ── guard: محافظ ─────────────────────────────────────────────────────
    def _job_guard(self) -> dict:
        events.emit("task.started", "محافظ: بررسیِ سلامتِ لنگرها و immutableها",
                    status="info", agent_id="guardrail", approval_state="not_required")
        inv = guardrails.check_invariants()

        # ثابتِ سخت = لنگرهای ریاضی. نقضِ آن ⇒ توقفِ حفاظتیِ فوری (Tier 3 — APPROVE).
        if not inv["anchors_ok"]:
            events.emit(
                "task.failed",
                "⚠️ نقضِ لنگرهای ریاضی — توقفِ حفاظتی",
                status="error", agent_id="guardrail", next_action="halt",
                approval_state="pending",
            )
            try:
                from brain import notify
                notify.send_packet(
                    "approve", "توقفِ حفاظتیِ Brain-OS",
                    "لنگرهای ریاضیِ مدلِ SOG بازتولید نشدند — ثابتِ سختِ سیستم نقض شده",
                    "سیستم را متوقف نگه دار؛ در داشبورد «توقف و صفر» بزن و علت را بررسی کن",
                    "سیستم در حالتِ امن متوقف می‌ماند تا تو تصمیم بگیری (safe fallback)",
                    options=["reset-and-investigate", "defer"],
                )
            except Exception:
                pass
            return {"ok": False, "mode": "guard", "halt": True}

        # خانه‌داری: سقفِ هوشمندِ نگه‌داری (archive، نه حذف — تصمیمِ کاربر)
        hk_note = ""
        try:
            from brain import housekeeping
            hk = housekeeping.run_housekeeping()
            moved = sum(hk.values())
            if moved:
                hk_note = f" · 🗃️ آرشیو: {moved} مورد ({hk['vault_notes']} یادداشت، {hk['rhythms']} ریتم)"
        except Exception as e:
            logger.warning("housekeeping failed: %s", e)

        # لنگرها سالم‌اند؛ نبودِ پوشه‌ی مرجعِ اختیاری فقط یک هشدارِ نرم است.
        ref_note = "" if inv["reference_intact"] else " · ⚠️ پوشه‌ی مرجعِ اختیاری یافت نشد"
        events.emit("task.completed",
                    f"🛡️ لنگرها سالم · بدونِ ویرایشِ کد · نوشتن فقط در نواحیِ مجاز{ref_note}{hk_note}",
                    status="ok", agent_id="guardrail", next_action="امن",
                    approval_state="not_required")
        return {"ok": True, "mode": "guard"}

    # ── kernel_consult: مشاوره با کرنلِ شناختی ────────────────────────────
    def _job_kernel_consult(self) -> dict:
        events.emit("task.started", "مشاوره با کرنل: بررسیِ verdictها و ADRهای جدید",
                    status="info", agent_id="kernel_consult", approval_state="not_required")
        try:
            from brain import kernel_consumer as kc
            consumer = kc.KernelConsumer()
            dash = consumer.read_dashboard()
            action = consumer.suggest_automation_action()
        except Exception as e:
            logger.warning("kernel consult failed: %s", e)
            events.emit("task.failed", f"خطا در مشاوره با کرنل: {type(e).__name__}",
                        status="error", agent_id="kernel_consult", approval_state="not_required")
            return {"ok": False, "mode": "kernel_consult"}

        if not dash:
            events.emit("task.completed", "کرنل در دسترس نیست — ادامهٔ خودکار",
                        status="ok", agent_id="kernel_consult", next_action="ادامه",
                        approval_state="not_required")
            return {"ok": True, "mode": "kernel_consult", "summary": "unreachable"}

        tally = dash.get("tally", {})
        high = dash.get("high_priority_adr", [])
        action_name = action.get("action", "no_op")
        priority = action.get("priority", "low")

        # اگر rejection زیاد باشد، خلاقیت را محتاط‌تر کن
        if tally.get("REJECTED", 0) >= 2:
            old = self.strategy["creativity"]
            self.strategy["creativity"] = guardrails.clamp_param("creativity", old - 0.05)
            strat_note = f" · creativity: {old:.2f} → {self.strategy['creativity']:.2f} (محتاط)"
        else:
            strat_note = ""

        # اگر INTEGRATE جدید باشد، انگیزهٔ کاوش بالا برود
        if tally.get("INTEGRATE", 0) >= 5:
            strat_note += " · کاوشِ نواحیِ جدید تشویق می‌شود"

        summary = (
            f"ADR={tally.get('INTEGRATE',0)}I/{tally.get('OPTIMIZE',0)}O/"
            f"{tally.get('REJECTED',0)}R · high={len(high)} · action={action_name}"
        )

        events.emit("task.completed",
                    f"کرنل: {summary}{strat_note}",
                    status="ok" if priority != "high" else "warning",
                    agent_id="kernel_consult", next_action=action_name,
                    approval_state="not_required")

        # اگر priority HIGH بود، handoff بساز
        if priority == "high" and high:
            adr = high[0]
            events.emit("handoff.created",
                        f"کرنل: {adr.get('title','?')} → {adr.get('verdict','?')} (نیاز به review)",
                        status="blocked", agent_id="kernel_consult",
                        approval_state="not_required")

        return {"ok": True, "mode": "kernel_consult", "summary": summary, "action": action_name}

    # ── heartbeat ────────────────────────────────────────────────────────
    def maybe_heartbeat(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        if self._last_heartbeat is None:
            self._last_heartbeat = now
            return False
        if (now - self._last_heartbeat).total_seconds() < HEARTBEAT_SECONDS:
            return False
        s = events.get_summary(HEARTBEAT_SECONDS)
        events.emit(
            "system.heartbeat",
            f"{s['total']} رویداد · {s['completed']} تکمیل · "
            f"{s['errors']} خطا · novelty={self.strategy['novelty_threshold']:.2f}",
            status="info", agent_id="system", approval_state="not_required",
        )
        self._last_heartbeat = now
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import os
    os.environ["MOCK_MODE"] = "true"
    # C-012: پاک‌کردنِ رویدادها دیگر پیش‌فرضِ دمو نیست — telemetry تاریخ را
    # نابود می‌کرد (۴۸ ردیفِ مانده از ۳۴۲۱۶ رویداد، اثرِ همین clear بود).
    # فقط با ارادهٔ صریح:  DEMO_CLEAR_EVENTS=1
    if os.getenv("DEMO_CLEAR_EVENTS", "") == "1":
        events.clear_events()
    ctrl = AutomationController(use_llm=False)
    for _ in range(len(_MODE_CYCLE) + 2):
        r = ctrl.run_one()
        print(r.get("mode"), "→", r.get("summary", ""))
    print("strategy:", ctrl.strategy)
    print("counts:", events.counts())
