#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fugu.py — مغزِ دکتر: کلاینتِ Sakana Fugu.

Fugu یک مدلِ معمولی نیست: **یک سیستمِ چندایجنتی در قالبِ یک مدل**.
  · TRINITY  — نقش‌های Thinker/Worker/Verifier را بینِ متخصص‌ها پخش می‌کند
  · Conductor — با RL آموخته الگوهای هماهنگی را خودش کشف کند

نتیجهٔ معماریِ مهم: **لایهٔ چندایجنتی روی Fugu نمی‌سازیم — داخلِ خودش هست.**
کارِ ما فقط این است: context درست بدهیم، سهمیه را بشماریم، و verifier را جدی بگیریم.

انضباط‌ها (همه از قوانینِ والت می‌آیند):
  · fail-closed — نبودِ کلید ⇒ None، نه mock و نه ادعا
  · **دو** سقف: تعدادِ فراخوان و **دلارِ روزانه** — چون Fugu Ultra گران است
  · هر فراخوان در `paid-calls.jsonl` رسید می‌گذارد، با `cost_usd`ِ **محاسبه‌شده**
  · شکلِ پارامترها ناشناخته بود ⇒ به‌جای حدس، **کشفِ خودکار** با fallback و ثبتِ نتیجه

stdlib-only (urllib). بدونِ وابستگی به openai SDK.
"""
from __future__ import annotations

import json, os, time, urllib.error, urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

BASE = os.environ.get("SAKANA_BASE_URL", "https://api.sakana.ai/v1")
KEY_ENV = "SAKANA_API_KEY"
DAILY_CAP = int(os.environ.get("FUGU_DAILY_CALL_CAP", "60"))
DAILY_USD_CAP = float(os.environ.get("FUGU_DAILY_USD_CAP", "2.00"))
CONTEXT_WINDOW = 1_000_000          # تأییدشده: console.sakana.ai/get-started (۲۹ جولای ۲۰۲۶)

MODELS = {
    "fast":   ("fugu",              "high"),   # پرسشِ روزمرهٔ دکتر
    "deep":   ("fugu-ultra-v1.1",   "max"),    # تشخیصِ کامل — تنها مدلی که max دارد
    "cyber":  ("fugu-cyber",        "xhigh"),  # ممیزیِ امنیتی
}

# دلار به‌ازای هر ۱M توکن — از console.sakana.ai/pricing (۲۹ جولای ۲۰۲۶).
# `None` یعنی **تأیید نشده**؛ عددِ حدسی جای عددِ واقعی نمی‌نشیند.
PRICING: dict[str, dict[str, float | None]] = {
    "fugu-ultra-v1.1": {"in": 5.0, "out": 30.0, "cached_in": 0.50},
    "fugu-ultra-v1.0": {"in": 5.0, "out": 30.0, "cached_in": 0.50},
    "fugu-ultra":      {"in": 5.0, "out": 30.0, "cached_in": 0.50},
    "fugu-cyber":      {"in": 6.0, "out": 36.0, "cached_in": 0.60},
    "fugu":            {"in": None, "out": None, "cached_in": None},   # [UNKNOWN]
}
# بالای ۲۷۲K توکنِ context تعرفه بالا می‌رود (ultra: 10/45 · cyber: 12/54).
LONG_CTX_TOKENS = 272_000
LONG_CTX = {
    "fugu-ultra-v1.1": {"in": 10.0, "out": 45.0},
    "fugu-ultra-v1.0": {"in": 10.0, "out": 45.0},
    "fugu-ultra":      {"in": 10.0, "out": 45.0},
    "fugu-cyber":      {"in": 12.0, "out": 54.0},
}


def price(model: str, tok_in: int, tok_out: int) -> float | None:
    """هزینهٔ واقعی به دلار. `None` = تعرفه تأیید نشده ⇒ ادعای «صفر» ممنوع."""
    p = PRICING.get(model)
    if not p or p["in"] is None or p["out"] is None:
        return None
    rate = LONG_CTX.get(model, {}) if tok_in > LONG_CTX_TOKENS else {}
    r_in = rate.get("in", p["in"])
    r_out = rate.get("out", p["out"])
    return round(tok_in / 1e6 * float(r_in) + tok_out / 1e6 * float(r_out), 6)


@dataclass
class Reply:
    text: str | None
    model: str
    effort: str
    tokens_in: int = 0
    tokens_out: int = 0
    ms: int = 0
    ok: bool = False
    reason: str = ""
    cost_usd: float | None = None
    shape: str = ""

    @property
    def usable(self) -> bool:
        return self.ok and bool(self.text)


class Quota:
    """دو سقف: تعداد و دلار. رسیدِ روی دیسک، نه حافظه."""

    def __init__(self, state_dir: Path, cap: int = DAILY_CAP,
                 usd_cap: float = DAILY_USD_CAP):
        self.p = Path(state_dir) / "fugu-quota.json"
        self.cap = cap
        self.usd_cap = float(usd_cap)

    def _load(self) -> dict:
        try:
            d = json.loads(self.p.read_text("utf-8"))
            if d.get("day") == date.today().isoformat():
                d.setdefault("spent_usd", 0.0)
                d.setdefault("unpriced_calls", 0)
                return d
        except (OSError, ValueError):
            pass
        return {"day": date.today().isoformat(), "used_total": 0,
                "spent_usd": 0.0, "unpriced_calls": 0}

    def _save(self, d: dict) -> None:
        try:
            self.p.parent.mkdir(parents=True, exist_ok=True)
            self.p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    @property
    def used(self) -> int:
        return int(self._load().get("used_total", 0))

    @property
    def spent_usd(self) -> float:
        return float(self._load().get("spent_usd", 0.0))

    @property
    def remaining(self) -> int:
        return max(0, self.cap - self.used)

    @property
    def usd_remaining(self) -> float:
        return max(0.0, self.usd_cap - self.spent_usd)

    def take(self) -> bool:
        d = self._load()
        if int(d.get("used_total", 0)) >= self.cap:
            return False
        if float(d.get("spent_usd", 0.0)) >= self.usd_cap:
            return False
        d["used_total"] = int(d.get("used_total", 0)) + 1
        self._save(d)
        return True

    def charge(self, usd: float | None) -> None:
        """`None` یعنی تعرفه نامعلوم — شمرده می‌شود ولی صفر فرض **نمی‌شود**."""
        d = self._load()
        if usd is None:
            d["unpriced_calls"] = int(d.get("unpriced_calls", 0)) + 1
        else:
            d["spent_usd"] = round(float(d.get("spent_usd", 0.0)) + float(usd), 6)
        self._save(d)


class Fugu:
    def __init__(self, state_dir: Path | str, timeout: float = 180.0):
        self.state = Path(state_dir)
        self.quota = Quota(self.state)
        self.timeout = timeout
        self._shape_f = self.state / "fugu-api-shape.json"

    # ------------------------------------------------------------------ auth
    @property
    def key(self) -> str | None:
        k = os.environ.get(KEY_ENV, "").strip()
        return k or None

    @property
    def ready(self) -> bool:
        return self.key is not None

    # ------------------------------------------------------- شکلِ پارامترها
    # مستنداتِ Sakana `reasoning.effort` را نشان می‌دهد، ولی `/chat/completions`
    # در قراردادِ OpenAI پارامترِ تختِ `reasoning_effort` دارد. کدام درست است روی
    # این endpoint؟ **حدس نمی‌زنیم** — امتحان می‌کنیم و نتیجه را می‌نویسیم.
    SHAPES = ("flat", "nested", "bare")

    @staticmethod
    def _body(shape: str, model: str, system: str, user: str,
              effort: str, max_tokens: int) -> dict:
        b: dict = {"model": model,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                   "max_tokens": max_tokens}
        if shape == "flat":
            b["reasoning_effort"] = effort
        elif shape == "nested":
            b["reasoning"] = {"effort": effort}
        return b                       # "bare" = بدونِ پارامترِ effort

    def _known_shape(self) -> str | None:
        try:
            return json.loads(self._shape_f.read_text("utf-8")).get("shape")
        except (OSError, ValueError):
            return None

    def _remember_shape(self, shape: str) -> None:
        try:
            self.state.mkdir(parents=True, exist_ok=True)
            self._shape_f.write_text(json.dumps(
                {"shape": shape, "base": BASE, "learned": time.strftime("%Y-%m-%d")},
                ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------------ ask
    def ask(self, system: str, user: str, tier: str = "fast",
            max_tokens: int = 4000) -> Reply:
        model, effort = MODELS.get(tier, MODELS["fast"])

        if not self.ready:
            return Reply(None, model, effort, ok=False,
                         reason=f"{KEY_ENV} تنظیم نیست — fail-closed، هیچ حدسی زده نمی‌شود")
        if self.quota.remaining <= 0:
            return Reply(None, model, effort, ok=False,
                         reason=f"سهمیهٔ روزانه ({self.quota.cap} فراخوان) تمام شد")
        if self.quota.usd_remaining <= 0:
            return Reply(None, model, effort, ok=False,
                         reason=f"سقفِ دلارِ روزانه (${self.quota.usd_cap:.2f}) تمام شد")
        if not self.quota.take():
            return Reply(None, model, effort, ok=False, reason="سهمیه گرفته نشد")

        order = ([s for s in (self._known_shape(),) if s] +
                 [s for s in self.SHAPES if s != self._known_shape()])
        last = ""
        t0 = time.time()
        for shape in order:
            body = json.dumps(self._body(shape, model, system, user, effort,
                                         max_tokens)).encode("utf-8")
            req = urllib.request.Request(
                f"{BASE}/chat/completions", data=body, method="POST",
                headers={"Authorization": f"Bearer {self.key}",
                         "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.reason}"
                if e.code == 400:            # شکلِ پارامتر غلط بود ⇒ بعدی
                    continue
                return Reply(None, model, effort, ms=int((time.time()-t0)*1000),
                             ok=False, reason=last, shape=shape)
            except Exception as e:                              # noqa: BLE001
                return Reply(None, model, effort, ms=int((time.time()-t0)*1000),
                             ok=False, reason=f"{type(e).__name__}: {e}", shape=shape)

            ms = int((time.time() - t0) * 1000)
            try:
                text = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                return Reply(None, model, effort, ms=ms, ok=False,
                             reason="پاسخ شکلِ منتظره را ندارد", shape=shape)
            self._remember_shape(shape)
            u = data.get("usage") or {}
            ti, to = int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))
            rep = Reply(text, model, effort, ti, to, ms, ok=True,
                        cost_usd=price(model, ti, to), shape=shape)
            self.quota.charge(rep.cost_usd)
            self._receipt(rep)
            return rep

        return Reply(None, model, effort, ms=int((time.time()-t0)*1000), ok=False,
                     reason=f"هیچ شکلِ پارامتری پذیرفته نشد — آخرین: {last}")

    # -------------------------------------------------------------- receipt
    def _receipt(self, r: Reply) -> None:
        """رسیدِ روی دیسک با هزینهٔ **محاسبه‌شده**، نه صفرِ فرضی."""
        try:
            self.state.mkdir(parents=True, exist_ok=True)
            with (self.state / "paid-calls.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "actor": "octopus-doctor", "provider": "sakana",
                    "model": r.model, "effort": r.effort, "shape": r.shape, "ok": r.ok,
                    "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                    "cost_usd": r.cost_usd,          # None = تعرفه [UNKNOWN]
                    "ms": r.ms, "quota_used": self.quota.used,
                    "spent_usd_today": self.quota.spent_usd,
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
