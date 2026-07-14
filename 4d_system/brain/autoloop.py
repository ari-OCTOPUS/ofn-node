"""
brain/autoloop.py — موتور پژوهشِ خودمختار

این ماژول هسته‌ی «موجودِ پژوهشی» است که:
  ۱. داده تولید می‌کنه (مصنوعی/فیزیکی/واقعی)
  ۲. تحلیل می‌کنه (با Fugu)
  ۳. نتیجه رو ارزیابی می‌کنه (خودارزیابی)
  ۴. اگه الگوی جدیدی کشف کرد → با کاربر مشورت می‌کنه
  ۵. اگه تایید شد → ذخیره و یادگیری
  ۶. hypothesis بعدی رو تولید می‌کنه
  ۷. لوپ تکرار

کاربر فقط موقع «کشف‌های مهم» دخالت می‌کنه.
"""
from __future__ import annotations

import time
import json
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Generator
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LoopResult:
    """نتیجه‌ی یک دور لوپ."""
    iteration: int
    source: str
    series_stats: dict
    scores: dict
    insight: str           # تحلیل Fugu
    novelty: float         # 0..1 — چقدر این کشف جدیده
    needs_user: bool       # آیا باید با کاربر مشورت کنیم؟
    user_question: str     # سؤال برای کاربر (اگه needs_user)
    saved: bool = False    # آیا ذخیره شد؟
    pattern_id: Optional[int] = None


@dataclass
class AutoLoopConfig:
    """تنظیمات لوپ."""
    max_iterations: int = 20
    pause_on_novelty: float = 1.01   # effectively disabled — لوپ کاملاً خودمختار
    sources: list = field(default_factory=lambda: [
        "synthetic", "physical", "synthetic", "physical"
    ])
    auto_save: bool = True          # ذخیره‌ی خودکار کشف‌ها
    use_llm: bool = True            # اگر False، فقط تحلیل محلیِ سریع (بدون تماس شبکه)
    explore_points: int = 3000      # طولِ سری در هر کاوش (قابلِ تحول و آزمون)


class AutoLoopEngine:
    """
    موتور پژوهشِ خودمختار.

    usage:
        engine = AutoLoopEngine()
        for result in engine.run():
            if result.needs_user:
                # show to user, get approval
                pass
    """

    def __init__(self, config: AutoLoopConfig = None):
        self.config = config or AutoLoopConfig()
        self.iteration = 0
        self.history: list[LoopResult] = []
        self.discovered_patterns: list[dict] = []
        self._router = None

    @property
    def router(self):
        if self._router is None:
            from llm.router import get_router
            self._router = get_router()
        return self._router

    def _generate_data(self, source_type: str, n: int = 3000) -> tuple[np.ndarray, str]:
        """تولید داده بر اساس نوع منبع."""
        rng = np.random.default_rng(self.iteration * 7 + 42)

        if source_type == "synthetic":
            # Choose a random synthetic type
            from data.synthetic import CATALOG
            names = list(CATALOG.keys())
            name = names[self.iteration % len(names)]
            fn = CATALOG[name]["fn"]
            try:
                series = fn(n, rng.integers(0, 999))
            except TypeError:
                series = fn(n)
            return series, f"synthetic:{name}"

        elif source_type == "physical":
            from data.physical import CATALOG
            names = list(CATALOG.keys())
            name = names[self.iteration % len(names)]
            fn = CATALOG[name]["fn"]
            try:
                series = fn(n, rng.integers(0, 999))
            except TypeError:
                series = fn(n)
            return series, f"physical:{name}"

        elif source_type == "real":
            from data.real_api import CATALOG
            names = list(CATALOG.keys())
            name = names[self.iteration % len(names)]
            try:
                result = CATALOG[name]()
                return result["series"], result["label"]
            except Exception:
                # fallback to synthetic
                from data.synthetic import ar1
                return ar1(n, 0.7, seed=42), "fallback:AR(1)"

        # default
        from data.synthetic import ar1
        return ar1(n, 0.5, seed=42), "default:AR(1)"

    def _analyze(self, series: np.ndarray, source: str) -> dict:
        """تحلیل سری زمانی."""
        from core.metrics import empirical_shadow, fit_shadow_parameters

        shadow = empirical_shadow(series)
        fit = fit_shadow_parameters(series)

        # کشیدگیِ اضافی (غیرگوسی‌بودن) — محورِ رفتاریِ مستقل از خودهمبستگی
        x = np.asarray(series, dtype=float)
        m = float(x.mean())
        v = float(x.var())
        kurtosis = float(((x - m) ** 4).mean() / (v ** 2) - 3.0) if v > 1e-12 else 0.0

        # همه‌ی فیلدها با .get — سریِ ثابت/بی‌واریانس باعثِ dictِ خطا می‌شود که
        # کلیدِ rho_hat ندارد؛ دسترسیِ مستقیم KeyError می‌داد.
        return {
            "temporal_mi": float(shadow.get("temporal_mi", 0.0)),
            "rho_hat": float(fit.get("rho_hat", 0.0)),
            "E_shadow_proxy": float(fit.get("E_shadow_proxy", 0.0)),
            "detectable": bool(fit.get("detectable", False)),
            "verdict": fit.get("classification", fit.get("error", "unknown")),
            "n_points": len(series),
            "kurtosis": kurtosis,
            "source": source,
        }

    def _get_insight(self, analysis: dict) -> str:
        """بینشِ کوتاه — دکترینِ Local-First: اول Ollama (رایگان)، بعد GLM، بعد heuristic."""
        # First try a quick local analysis (always works)
        local = self._local_insight(analysis)

        # حالتِ سریع (داشبورد): بدون تماس شبکه
        if not getattr(self.config, "use_llm", True):
            return local

        # LOCAL-first: مدلِ محلیِ Ollama برای بینشِ کوتاه (کیفیتِ «خوبِ کافی»، رایگان)
        try:
            from llm.ollama_client import OllamaClient
            oll = OllamaClient()
            if oll.available:
                resp = oll.quick(
                    f"تحلیل کوتاه (حداکثر ۲ جمله، فارسی): منبع={analysis['source']}, "
                    f"MI={analysis['temporal_mi']:.4f}, ρ={analysis['rho_hat']:.3f}, "
                    f"قابل‌تشخیص={analysis['detectable']}. چه الگویی است؟",
                    temperature=0.3,
                )
                if resp and not resp.startswith("[Ollama"):
                    return resp
        except Exception as e:
            logger.warning("local insight (ollama) failed: %s", e)

        # CLOUD fallback: GLM از میانِ router (sanitize + timeoutِ مرکزی)
        try:
            if self.router.glm.available:
                prompt = f"""تحلیل کوتاه (۲ جمله):
منبع: {analysis['source']}, MI: {analysis['temporal_mi']:.4f},
ρ: {analysis['rho_hat']:.3f}, قابل‌تشخیص: {analysis['detectable']}
چه الگویی است؟"""
                resp = self.router.glm.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.3, max_tokens=200,
                )
                if resp and not resp.startswith("["):
                    return resp
        except Exception as e:
            logger.warning("GLM insight failed, falling back to local: %s: %s",
                           type(e).__name__, e)

        return local

    def _local_insight(self, a: dict) -> str:
        """تحلیل محلی بدون LLM — همیشه کار می‌کنه."""
        mi = a["temporal_mi"]
        rho = a["rho_hat"]
        det = a["detectable"]

        if not det:
            return f"❌ نامرئی — ρ={rho:.3f} یا نشت ضعیف. بُعد پنهان وجود دارد ولی ردی نمی‌اندازد."
        elif mi > 0.1:
            return f"🔥 ساختار قوی — MI={mi:.4f}, ρ={rho:.3f}. بُعد پنهان واضح است. حافظه‌ی بلندمدت محتمل."
        elif mi > 0.01:
            return f"📊 ساختار متوسط — MI={mi:.4f}. ردِ بُعد پنهان قابل‌تشخیص است ولی ضعیف."
        else:
            return f"🌫️ ساختار ضعیف — MI={mi:.4f}. تقریباً iid. بُعد پنهان اگر هست، کم‌اثر است."

    def _compute_novelty(self, analysis: dict) -> float:
        """
        چقدر این کشف جدیده؟
        مقایسه با history با z-score.

        کالیبراسیون:
          - اولین کشف: 0.5
          - کشف‌های روتین: < 0.5
          - outlierهای واقعی (z>3): > 0.9
        """
        if len(self.history) < 3:
            # با کمتر از ۳ نمونه، z-score آماری بی‌معناست — مقدار خنثی
            return 0.5

        past_mis = [h.scores.get("temporal_mi", 0) for h in self.history]
        past_rhos = [h.scores.get("rho_hat", 0) for h in self.history]

        current_mi = analysis["temporal_mi"]
        current_rho = analysis["rho_hat"]

        # Z-score of current MI relative to distribution of past MIs
        import numpy as np
        mi_arr = np.array(past_mis)
        mi_mean, mi_std = mi_arr.mean(), mi_arr.std()
        if mi_std < 1e-9:
            mi_z = abs(current_mi - mi_mean)
        else:
            mi_z = abs(current_mi - mi_mean) / mi_std

        rho_arr = np.array(past_rhos)
        rho_mean, rho_std = rho_arr.mean(), rho_arr.std()
        if rho_std < 1e-9:
            rho_z = abs(current_rho - rho_mean)
        else:
            rho_z = abs(current_rho - rho_mean) / rho_std

        # Combine: only truly extreme outliers (z>3) get > 0.9
        max_z = max(mi_z, rho_z)
        # Sigmoid-like mapping: z=0→0, z=1→0.31, z=2→0.58, z=3→0.78, z=4→0.90
        novelty = max_z / (1 + max_z) * 1.3
        return min(1.0, novelty)

    def _should_ask_user(self, novelty: float, analysis: dict) -> tuple[bool, str]:
        """آیا باید با کاربر مشورت کنیم؟"""
        if novelty < self.config.pause_on_novelty:
            return False, ""

        # Generate a question for the user
        question = (
            f"🔍 **کشف جدید** (novelty={novelty:.2f})\n\n"
            f"منبع: {analysis['source']}\n"
            f"MI: {analysis['temporal_mi']:.6f}\n"
            f"ρ: {analysis['rho_hat']:.4f}\n"
            f"تشخیص: {'✅' if analysis['detectable'] else '❌'}\n\n"
            f"این الگو با قبلی‌ها فرق داره. ذخیره کنم؟"
        )
        return True, question

    def _save_pattern(self, analysis: dict, insight: str) -> Optional[int]:
        """ذخیره‌ی الگو — فقط اگر قبلاً ذخیره نشده (جلوگیری از تکرار)."""
        try:
            from memory.research_store import save_pattern, get_patterns, SavedPattern

            # Check for duplicates: same source + similar stored metric (within 10%)
            # نکته‌ی مهم: در جدولِ patterns مقدارِ E_shadow_proxy در ستونِ delta_self
            # ذخیره می‌شود (MI اصلاً persist نمی‌شود). پس مقایسه باید هم‌جنس باشد:
            # E_shadow_proxy فعلی ↔ delta_self ذخیره‌شده. (قبلاً temporal_mi با
            # delta_self مقایسه می‌شد — دو کمیتِ بی‌ربط → dedup تصادفی: گاهی کشفِ
            # واقعی حذف می‌شد، گاهی تکراری رد نمی‌شد.)
            existing = get_patterns(limit=100)
            source = analysis["source"]
            cur_metric = analysis.get("E_shadow_proxy", 0.0)
            cur_mi = analysis.get("temporal_mi", 0.0)
            for p in existing:
                if source in p.get("tags", ""):
                    # B6: ردیف‌های جدید MI واقعی دارند → مقایسه‌ی دقیقِ MI↔MI؛
                    # ردیف‌های قدیمی (temporal_mi=0) → همان مقایسه‌ی E_shadow.
                    past_mi = p.get("temporal_mi", 0) or 0
                    if past_mi > 0:
                        if abs(cur_mi - past_mi) / max(past_mi, 1e-6) < 0.10:
                            return None  # Already have this pattern
                        continue
                    past = p.get("delta_self", 0) or 0
                    if past > 0 and abs(cur_metric - past) / max(past, 0.001) < 0.10:
                        return None  # Already have this pattern

            p = SavedPattern(
                name=f"auto-{source}-{datetime.now().strftime('%H%M%S')}",
                rho=analysis["rho_hat"],
                lam=0.5,  # proxy
                se=0.1, sz=0.05, sd=0.1,
                delta_self=analysis["E_shadow_proxy"],
                e_shadow=analysis["E_shadow_proxy"],
                temporal_mi=analysis.get("temporal_mi", 0.0),  # B6: بالاخره persist می‌شود
                pcai=0, sms=0,
                detectable=analysis["detectable"],
                note=insight[:300],
                tags=f"auto,{source}",
            )
            return save_pattern(p)
        except Exception as e:
            logger.error("save_pattern failed: %s: %s", type(e).__name__, e)
            return None

    def _save_rhythm_and_note(self, source_label, series, analysis, insight, pattern_id):
        """ذخیره‌ی ریتم خام + یادداشت Obsidian."""
        # Save rhythm
        try:
            from data.rhythm_store import save_rhythm
            save_rhythm(
                name=f"auto-{source_label}",
                series=series,
                source_type="auto",
                mi=analysis.get("temporal_mi", 0),
                rho_hat=analysis.get("rho_hat", 0),
                detectable=analysis.get("detectable", False),
                tags=f"auto,{source_label}",
            )
        except Exception as e:
            logger.error("save_rhythm failed: %s: %s", type(e).__name__, e)

        # Create Obsidian note
        try:
            from brain.vault_sync import create_discovery_note
            pattern_data = {
                "id": pattern_id,
                "name": f"auto-{source_label}",
                "rho": analysis.get("rho_hat", 0.5),
                "lam": 0.5,
                "delta_self": analysis.get("E_shadow_proxy", 0),
                "e_shadow": analysis.get("E_shadow_proxy", 0),
                "pcai": 0,
                "detectable": analysis.get("detectable", False),
                "tags": source_label,
            }
            create_discovery_note(pattern_data, insight)
        except Exception as e:
            logger.error("create_discovery_note failed: %s: %s", type(e).__name__, e)

    def run_step(self, iteration: int, past_results: list = None) -> LoopResult:
        """
        اجرای یک گامِ لوپ (نه کل لوپ).
        مناسب Streamlit — هر بار یک گام.
        """
        self.iteration = iteration
        if past_results:
            self.history = past_results

        # ۱. انتخاب منبع
        source_type = self.config.sources[iteration % len(self.config.sources)]

        # ۲. تولید داده + اعتبارسنجی (NaN/inf باعث false positive در امتیازدهی می‌شود)
        series, source_label = self._generate_data(
            source_type, n=getattr(self.config, "explore_points", 3000))
        n_bad = 0
        if series is not None:
            series = np.asarray(series, dtype=float)
            n_bad = int(series.size - np.isfinite(series).sum())
        if series is None or len(series) < 20 or n_bad > 0:
            reason = "داده نامعتبر" if n_bad == 0 else f"داده نامعتبر ({n_bad} مقدار NaN/inf)"
            logger.warning("run_step %d: invalid series from %s (%s)",
                           iteration, source_type, reason)
            return LoopResult(
                iteration=iteration, source="error",
                series_stats={}, scores={"detectable": False, "temporal_mi": 0},
                insight=reason, novelty=0, needs_user=False, user_question=""
            )

        # ۳. تحلیل
        analysis = self._analyze(series, source_label)

        # ۴. insight
        insight = self._get_insight(analysis)

        # ۵. novelty
        novelty = self._compute_novelty(analysis)

        # ۶. user consultation
        needs_user, question = self._should_ask_user(novelty, analysis)

        # ۷. save — auto-save all detectable results, not just high novelty
        pattern_id = None
        saved = False
        if self.config.auto_save:
            # Only save if detectable AND not a duplicate of last result
            last = self.history[-1] if self.history else None
            is_dup = (last and last.source == source_label
                      and abs(last.scores.get("temporal_mi", 0) - analysis["temporal_mi"]) < 0.001)
            if analysis.get("detectable", False) and not is_dup:
                pattern_id = self._save_pattern(analysis, insight)
                saved = pattern_id is not None

                # Save raw rhythm + create Obsidian note
                self._save_rhythm_and_note(source_label, series, analysis, insight, pattern_id)

                # D1 fix: ثبتِ کشف در مرزِ دانش — autoloop مستقل هم حالا frontier
                # را پر می‌کند، نه فقط automation.py. این conclusions را به داده
                # می‌رساند حتی اگر automation نباشد. (kurtosis از analysis می‌آید.)
                try:
                    from brain import frontier
                    frontier.record(
                        source_label,
                        mi=float(analysis.get("temporal_mi", 0.0)),
                        rho=float(analysis.get("rho_hat", 0.0)),
                        kurt=float(analysis.get("kurtosis", 0.0)),
                        detectable=bool(analysis.get("detectable", False)),
                    )
                except Exception as e:
                    logger.warning("autoloop frontier.record failed: %s", e)

        result = LoopResult(
            iteration=iteration, source=source_label,
            series_stats={"n": len(series)},
            scores=analysis, insight=insight,
            novelty=novelty, needs_user=needs_user,
            user_question=question, saved=saved, pattern_id=pattern_id,
        )
        self.history.append(result)
        return result

    def run(self) -> Generator[LoopResult, None, None]:
        """
        اجرای لوپِ پژوهش.
        هر iteration یک LoopResult برمی‌گردونه.
        """
        for i in range(self.config.max_iterations):
            self.iteration = i

            # ۱. انتخاب منبع
            source_type = self.config.sources[i % len(self.config.sources)]

            # ۲. تولید داده
            try:
                series, source_label = self._generate_data(
                    source_type, n=getattr(self.config, "explore_points", 3000))
            except Exception as e:
                logger.warning("run(): data generation failed for %s: %s",
                               source_type, e)
                continue

            if series is not None:
                series = np.asarray(series, dtype=float)
            if series is None or len(series) < 20 or not np.all(np.isfinite(series)):
                continue

            # ۳. تحلیل
            analysis = self._analyze(series, source_label)

            # ۴. insight از Fugu
            insight = self._get_insight(analysis)

            # ۵. novelty detection
            novelty = self._compute_novelty(analysis)

            # ۶. تصمیم: با کاربر مشورت کنیم؟
            needs_user, question = self._should_ask_user(novelty, analysis)

            # ۷. ذخیره — D4 fix: معیار هماهنگ با run_step (detectable && !dup)
            # قبلاً `novelty > 0.3` بود که با run_step (`detectable && !dup`) متفاوت
            # بود → همان موتور، رفتارِ متفاوت بسته به نقطهٔ ورود.
            pattern_id = None
            saved = False
            if self.config.auto_save:
                last = self.history[-1] if self.history else None
                is_dup = (last and last.source == source_label
                          and abs(last.scores.get("temporal_mi", 0) - analysis["temporal_mi"]) < 0.001)
                if analysis.get("detectable", False) and not is_dup:
                    pattern_id = self._save_pattern(analysis, insight)
                    saved = pattern_id is not None
                    self._save_rhythm_and_note(source_label, series, analysis, insight, pattern_id)
                    # D1 fix: ثبت در مرزِ دانش (مثل run_step)
                    try:
                        from brain import frontier
                        frontier.record(
                            source_label,
                            mi=float(analysis.get("temporal_mi", 0.0)),
                            rho=float(analysis.get("rho_hat", 0.0)),
                            kurt=float(analysis.get("kurtosis", 0.0)),
                            detectable=bool(analysis.get("detectable", False)),
                        )
                    except Exception as e:
                        logger.warning("run() frontier.record failed: %s", e)

            result = LoopResult(
                iteration=i,
                source=source_label,
                series_stats={
                    "n": len(series),
                    "mean": float(np.mean(series)),
                    "var": float(np.var(series)),
                },
                scores=analysis,
                insight=insight,
                novelty=novelty,
                needs_user=needs_user,
                user_question=question,
                saved=saved,
                pattern_id=pattern_id,
            )
            self.history.append(result)

            yield result

    def status(self) -> dict:
        """وضعیت موتور."""
        return {
            "iteration": self.iteration,
            "total_discoveries": len([r for r in self.history if r.saved]),
            "high_novelty": len([r for r in self.history if r.novelty > 0.6]),
            "sources_explored": list(set(r.source for r in self.history)),
        }


if __name__ == "__main__":
    engine = AutoLoopEngine(AutoLoopConfig(max_iterations=3))
    print("=== AutoLoop Engine Test ===\n")
    for result in engine.run():
        print(f"#{result.iteration} {result.source}")
        print(f"  MI={result.scores['temporal_mi']:.4f}  "
              f"detectable={result.scores['detectable']}  "
              f"novelty={result.novelty:.2f}")
        print(f"  insight: {result.insight[:80]}...")
        if result.needs_user:
            print(f"  ⚠️ USER: {result.user_question[:80]}")
        if result.saved:
            print(f"  💾 saved as #{result.pattern_id}")
        print()
