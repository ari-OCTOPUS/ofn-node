"""
SENTINEL — scorer.py
منطق امتیازدهی «مساعدت ورود» (Entry Favorability Score)
مقیاس: ۰ تا ۱۰۰
دو حالت: full (سه سیگنال) و limited (دو سیگنال)
ادغام Big Scenarios Framework در وزن‌دهی نهایی
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# ثابت‌ها
# ─────────────────────────────────────────────
FEAR_GREED_FEAR_THRESHOLD = 35   # زیر این عدد = ترس = مساعد برای ورود


class EntryScorer:
    def __init__(self, config: dict):
        self.config = config
        self.weights_btc_eth = config["scoring_weights"]["BTC_ETH"]
        self.weights_xmr_zec = config["scoring_weights"]["XMR_ZEC"]
        self.scenarios = config.get("scenarios", {})
        self.thresholds = config["thresholds"]

    # ─────────────────────────────────────────────
    # ۱. امتیاز Drawdown (قله‌ی ۹۰ روزه)
    # ─────────────────────────────────────────────

    def _score_drawdown(self, drawdown: float) -> float:
        """
        drawdown: 0.0 (در قله) تا 1.0 (زیر قله)
        هر چه بیشتر افت کرده، امتیاز بیشتر
        """
        # تابع خطی: افت ۰٪ → امتیاز ۰، افت ۶۰٪+ → امتیاز ۱۰۰
        score = min(drawdown / 0.60, 1.0) * 100
        return round(score, 2)

    # ─────────────────────────────────────────────
    # ۲. امتیاز موقعیت نسبت به میانگین‌های متحرک
    # ─────────────────────────────────────────────

    def _score_ma_position(self, price: float, ma50: Optional[float],
                           ma200: Optional[float]) -> float:
        """
        قیمت زیر هر دو MA → امتیاز کامل
        قیمت بین MA50 و MA200 → امتیاز متوسط
        قیمت بالای هر دو → امتیاز صفر
        """
        if not price:
            return 50.0  # بی‌اطلاعی = خنثی

        below50  = ma50  is not None and price < ma50
        below200 = ma200 is not None and price < ma200

        if below50 and below200:
            return 100.0
        elif below200 and not below50:
            return 65.0
        elif below50 and not below200:
            return 40.0
        else:
            return 10.0   # بالای هر دو MA = گران

    # ─────────────────────────────────────────────
    # ۳. امتیاز Fear & Greed
    # ─────────────────────────────────────────────

    def _score_fear_greed(self, fg_value: Optional[int]) -> float:
        """
        ترس بالا (عدد کم) = ورود مساعدتر
        0 → ۱۰۰ امتیاز، ۵۰ → ۵۰، ۱۰۰ → ۰
        """
        if fg_value is None:
            return 50.0
        return round((100 - fg_value), 2)

    # ─────────────────────────────────────────────
    # ۴. امتیاز on-chain (BTC/ETH)
    # ─────────────────────────────────────────────

    def _score_onchain(self, onchain: Optional[dict]) -> float:
        """
        exchange_netflow منفی (پول از صرافی خارج می‌شود) = صعودی
        miner_netflow منفی = ماینرها نمی‌فروشند = صعودی
        """
        if not onchain:
            return 50.0

        score = 50.0  # پایه خنثی

        # Exchange netflow: خروج خالص بزرگ = +25
        netflow = onchain.get("exchange_netflow", 0)
        if netflow < -1000:       # بیش از ۱۰۰۰ واحد خروج (برای BTC: BTC)
            score += 25
        elif netflow < 0:
            score += 12
        elif netflow > 1000:
            score -= 20
        elif netflow > 0:
            score -= 8

        # Miner pressure
        miner_flow = onchain.get("miner_netflow", 0)
        if miner_flow < 0:
            score += 15
        elif miner_flow > 500:
            score -= 15

        # NVT بالا = بازار گران است
        nvt = onchain.get("nvt")
        if nvt is not None:
            if nvt > 150:
                score -= 10
            elif nvt < 60:
                score += 10

        return round(max(0, min(100, score)), 2)

    # ─────────────────────────────────────────────
    # ۵. امتیاز social (LunarCrush)
    # ─────────────────────────────────────────────

    def _score_social(self, social: Optional[dict]) -> float:
        """
        ترس/بی‌تفاوتی اجتماعی + بنیان قوی = مساعد
        واگرایی: قیمت افتاده ولی فعالیت توسعه-social پایدار مانده = مساعد
        """
        if not social:
            return 50.0

        score = 50.0
        sentiment = social.get("sentiment", 0.5)  # 0-1

        # ترس اجتماعی (sentiment پایین) در ورود خوب است
        # sentiment < 0.35 = ترس → +20
        # sentiment > 0.75 = طمع → -15
        if sentiment < 0.35:
            score += 20
        elif sentiment < 0.50:
            score += 8
        elif sentiment > 0.75:
            score -= 15
        elif sentiment > 0.60:
            score -= 5

        # Galaxy score (کیفیت کلی): بالاتر = بهتر
        galaxy = social.get("galaxy_score", 50)
        if galaxy > 65:
            score += 10
        elif galaxy < 35:
            score -= 10

        return round(max(0, min(100, score)), 2)

    # ─────────────────────────────────────────────
    # ۶. تعدیل سناریوها (Big Scenarios)
    # ─────────────────────────────────────────────

    def _apply_scenario_modifiers(self, symbol: str, base_score: float) -> tuple:
        """
        سناریوهای فعال را روی امتیاز پایه اعمال می‌کند.
        برمی‌گرداند: (امتیاز تعدیل‌شده, لیست سناریوهای فعال)
        """
        active_scenarios = []
        total_modifier = 0

        for scenario_name, scenario in self.scenarios.items():
            status = scenario.get("status", "inactive")
            if status in ("emerging", "active"):
                modifiers = scenario.get("score_modifier", {})
                if symbol in modifiers:
                    mod = modifiers[symbol]
                    # سناریوی emerging = نصف تأثیر
                    if status == "emerging":
                        mod = mod * 0.5
                    total_modifier += mod
                    active_scenarios.append({
                        "name": scenario_name,
                        "status": status,
                        "modifier": mod,
                        "message": scenario.get("alert_message", ""),
                    })

        adjusted = base_score + total_modifier
        adjusted = round(max(0, min(100, adjusted)), 2)
        return adjusted, active_scenarios

    # ─────────────────────────────────────────────
    # ۷. محاسبه امتیاز کامل
    # ─────────────────────────────────────────────

    # ─────────────────────────────────────────────
    # ۶.۵. تشخیص ورود دیر (Late Entry Risk)
    # ─────────────────────────────────────────────

    @staticmethod
    def _late_entry_penalty(s_drawdown: float, gain_14d: Optional[float]) -> tuple:
        """
        اگر کوین در ۱۴ روز بیش از ۴۰٪ رشد کرده، امتیاز drawdown تخفیف می‌گیرد.
        ترتیب: ابتدا drawdown طبق منطق فعلی محاسبه شود، سپس ضریب ۰.۶ اعمال شود.
        این با منطق فعلی (drawdown بیشتر = مساعدتر) هماهنگ است، نه علیه آن.

        If coin gained >40% in 14 days, apply 0.6 multiplier to drawdown score.
        Calculation order: compute drawdown normally first, then discount.
        Returns: (adjusted_s_drawdown, late_entry_risk: bool, gain_14d_fraction)
        """
        if gain_14d is None:
            return s_drawdown, False, None

        # اگر به‌صورت درصد آمده (مثلاً ۴۵.۳) → تبدیل به fraction
        g = gain_14d
        if abs(g) > 3:
            g = g / 100.0

        if g > 0.40:
            adjusted = round(s_drawdown * 0.6, 2)
            logger.debug(
                f"LATE ENTRY: gain_14d={g:.1%} → "
                f"drawdown_score {s_drawdown:.1f} → {adjusted:.1f} (×0.6)"
            )
            return adjusted, True, round(g, 4)

        return s_drawdown, False, None

    def score(self, symbol: str, market_data: dict,
              sector_signals: Optional[dict] = None) -> dict:
        """
        ورودی: symbol + خروجی data_fetcher.fetch_all()
        sector_signals: اختیاری — سیگنال‌های اضافی از sector_scanner
                        اگر None باشد، رفتار دقیقاً مثل قبل است (backward compatible)
        خروجی: دیکشنری کامل امتیاز

        Input: symbol + market_data dict
        sector_signals (optional): extra signals from SectorScanner.
            If None → identical behaviour to before (all existing tests pass).
        """
        price_data  = market_data.get("price")
        fg_data     = market_data.get("fear_greed")
        social_data = market_data.get("social")
        onchain_data = market_data.get("onchain")
        available   = market_data.get("available_signals", [])

        # ─── خواندن تنظیمات دارایی از config ───
        asset_cfg = self.config.get("assets", {}).get(symbol, {})
        pole = asset_cfg.get("pole", "privacy")

        # ─── دارایی‌های stable: بدون امتیاز ورود ───
        if pole == "stable":
            return {
                "symbol": symbol,
                "score": None,
                "label": "stable_parking",
                "details": {},
                "active_scenarios": [],
                "mode": "none",
            }

        # ─── دارایی‌های watch_only: فقط رصد ───
        if asset_cfg.get("watch_only"):
            return {
                "symbol": symbol,
                "score": None,
                "label": "watch_only",
                "details": {},
                "active_scenarios": [],
                "mode": "watch",
            }

        # ─── انتخاب وزن‌ها بر اساس pole ───
        sw = self.config.get("scoring_weights", {})
        if "onchain" in asset_cfg.get("signals", []) and "onchain" in available:
            weights = self.weights_btc_eth
            mode = "full"
        elif pole == "hedge":
            weights = sw.get("HEDGE", self.weights_btc_eth)
            mode = "limited"
        elif pole == "ai":
            weights = sw.get("AI", self.weights_xmr_zec)
            mode = "limited"
        elif pole == "quantum":
            weights = sw.get("QUANTUM", self.weights_xmr_zec)
            mode = "limited"
        elif pole == "speculative":
            weights = sw.get("SPECULATIVE", self.weights_xmr_zec)
            mode = "limited"
        else:
            # privacy و هر چیز دیگه
            weights = sw.get("PRIVACY", self.weights_xmr_zec)
            mode = "limited"

        # ─── محاسبه هر زیرامتیاز ───
        price = price_data.get("price", 0) if price_data else 0
        drawdown = price_data.get("drawdown_from_90d_high", 0) if price_data else 0
        ma50  = price_data.get("ma50")  if price_data else None
        ma200 = price_data.get("ma200") if price_data else None
        fg_val = fg_data.get("value") if fg_data else None

        # ─── gain_14d برای late entry — از price_data یا sector_signals ───
        gain_14d = None
        if price_data:
            gain_14d = price_data.get("gain_14d")
        if gain_14d is None and sector_signals:
            gain_14d = sector_signals.get("gain_14d")

        s_drawdown = self._score_drawdown(drawdown)

        # ─── Late Entry Risk: بعد از محاسبه‌ی drawdown، تخفیف اعمال می‌شود ───
        s_drawdown, late_entry_risk, late_entry_gain = self._late_entry_penalty(
            s_drawdown, gain_14d
        )
        s_ma = self._score_ma_position(price, ma50, ma200)
        s_fg = self._score_fear_greed(fg_val)
        s_social  = self._score_social(social_data)  if "social"  in available else 50.0
        s_onchain = self._score_onchain(onchain_data) if "onchain" in available else None

        # ─── ترکیب وزن‌دار ───
        if mode == "full" and s_onchain is not None:
            # BTC/ETH با on-chain کامل
            base_score = (
                s_drawdown * weights["drawdown"]
                + s_ma * weights["ma_position"]
                + s_fg * weights["fear_greed"]
                + s_onchain * weights["onchain"]
                + s_social  * weights["social"]
            )
        else:
            # حالت محدود: بدون on-chain
            if "onchain" in weights:
                # وزن onchain رو بین drawdown و social تقسیم می‌کنیم
                w_draw = weights["drawdown"] + weights["onchain"] * 0.5
                w_soc  = weights.get("social", 0) + weights["onchain"] * 0.5
                base_score = (
                    s_drawdown * w_draw
                    + s_ma * weights["ma_position"]
                    + s_fg * weights["fear_greed"]
                    + s_social * w_soc
                )
            else:
                # وزن‌های بدون onchain (HEDGE, PRIVACY, AI, QUANTUM, SPECULATIVE)
                base_score = (
                    s_drawdown * weights["drawdown"]
                    + s_ma     * weights["ma_position"]
                    + s_fg     * weights["fear_greed"]
                    + s_social * weights.get("social", 0)
                )

        base_score = round(max(0, min(100, base_score)), 2)

        # ─── اگر sector_signals داده‌ی اضافی دارد (TVL، usage) ادغام می‌شود ───
        if sector_signals:
            tvl_score   = sector_signals.get("tvl_score")
            usage_score = sector_signals.get("usage_score")
            sector_name = sector_signals.get("sector", "")
            sec_weights = self.config.get("scoring_weights", {}).get("sectors", {}).get(sector_name, {})

            if tvl_score is not None and sec_weights.get("tvl", 0) > 0:
                # وزن tvl از config، کم از base_score برداشته و با tvl جایگزین می‌شود
                w_tvl = sec_weights["tvl"]
                base_score = round(
                    max(0, min(100, base_score * (1 - w_tvl) + tvl_score * w_tvl)), 2
                )

            if usage_score is not None and sec_weights.get("usage", 0) > 0:
                w_usage = sec_weights["usage"]
                base_score = round(
                    max(0, min(100, base_score * (1 - w_usage) + usage_score * w_usage)), 2
                )

        # ─── اعمال سناریوها ───
        final_score, active_scenarios = self._apply_scenario_modifiers(symbol, base_score)

        # ─── برچسب تصمیم ───
        label = self._decision_label(final_score)

        # ─── پیام هشدار اگر on-chain موجود نبود ───
        onchain_note = None
        if "onchain" in asset_cfg.get("signals", []) and mode == "limited":
            onchain_note = "⚠️ داده‌ی on-chain موجود نیست — امتیاز با سیگنال‌های موجود محاسبه شد"

        return {
            "symbol":           symbol,
            "score":            final_score,
            "base_score":       base_score,
            "label":            label,
            "mode":             mode,
            "details": {
                "drawdown_score":   s_drawdown,
                "ma_score":         s_ma,
                "fear_greed_score": s_fg,
                "social_score":     s_social,
                "onchain_score":    s_onchain,
                "price":            price,
                "drawdown_pct":     round(drawdown * 100, 1),
                "fear_greed_value": fg_val,
                "ma50":             ma50,
                "ma200":            ma200,
            },
            "active_scenarios":  active_scenarios,
            "onchain_note":      onchain_note,
            "data_quality":      market_data.get("data_quality", "unknown"),
            # ─── Late Entry Risk (None اگر sector_signals نبود) ───
            "late_entry_risk":   late_entry_risk,
            "late_entry_pct":    late_entry_gain,
        }

    # ─────────────────────────────────────────────
    # ۸. برچسب‌گذاری
    # ─────────────────────────────────────────────

    def _decision_label(self, score: float) -> str:
        if score >= self.thresholds["strong_entry"]:
            return "strong_entry"      # پله بزرگ‌تر
        elif score >= self.thresholds["moderate_entry"]:
            return "moderate_entry"    # پله متوسط
        elif score >= self.thresholds["weak_entry"]:
            return "weak_entry"        # پله کوچک / انتظار
        else:
            return "watch_only"        # فقط رصد

    def label_to_persian(self, label: str) -> str:
        mapping = {
            "strong_entry":   "ناحیه‌ی ورود مساعد 🟢",
            "moderate_entry": "نسبتاً مساعد 🟡",
            "weak_entry":     "صبر، هنوز گران 🟠",
            "watch_only":     "دور از ناحیه‌ی ورود 🔴",
            "stable_parking": "نقدینگی خشک 💵",
            "none":           "بدون امتیاز",
        }
        return mapping.get(label, label)

    # ─────────────────────────────────────────────
    # ۹. محاسبه پله پیشنهادی
    # ─────────────────────────────────────────────

    def suggest_tranche(self, symbol: str, score_result: dict,
                        remaining_budget_aud: float,
                        total_tranches: int) -> Optional[float]:
        """
        بر اساس امتیاز، یک پله از بودجه را پیشنهاد می‌دهد.
        اگر امتیاز کافی نداشت، None برمی‌گرداند.
        """
        label = score_result.get("label", "watch_only")
        score = score_result.get("score", 0)

        if label == "watch_only" or label in ("stable_parking", "none"):
            return None

        base_tranche = remaining_budget_aud / total_tranches

        if label == "strong_entry":
            multiplier = 1.5
        elif label == "moderate_entry":
            multiplier = 1.0
        else:  # weak_entry
            multiplier = 0.5

        suggested = round(base_tranche * multiplier, 2)
        # سقف: نمی‌تواند از بودجه باقی‌مانده بیشتر باشد
        return min(suggested, remaining_budget_aud)

    # ─────────────────────────────────────────────
    # ۱۰. بروزرسانی دستی وضعیت سناریو
    # ─────────────────────────────────────────────

    def update_scenario(self, scenario_name: str, new_status: str) -> bool:
        """
        اپراتور می‌تواند وضعیت سناریو را تغییر دهد.
        new_status: inactive | emerging | active
        """
        valid_statuses = {"inactive", "emerging", "active"}
        if new_status not in valid_statuses:
            logger.error(f"Invalid scenario status: {new_status}")
            return False
        if scenario_name not in self.scenarios:
            logger.error(f"Unknown scenario: {scenario_name}")
            return False
        self.scenarios[scenario_name]["status"] = new_status
        logger.info(f"Scenario {scenario_name} updated to {new_status}")
        return True
