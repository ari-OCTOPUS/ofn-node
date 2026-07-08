#!/usr/bin/env python3
"""chamber.py — Doctor Inner Chamber: اتاقِ گفت‌وگوی درونیِ کران‌دار و تخاصمی.

چند صدای متخاصم در یک حلقهٔ بسته که RFC را قوی‌تر می‌کند، نه دکتر را خودمختارتر.
الگو از _ops/debate/ (muse×architect، ≤۳ دور، gated) ولی:
  - تخاصمی نه هم‌رأی: حداقل یک صدا وظیفه‌اش falsify است.
  - خروجی فقط RFCِ قوی‌تر؛ merge همچنان human-append.

۶ مهارِ سخت (نقض = رد):
  ۱. کران‌دار: حداکثر N دور؛ هیچ حلقهٔ بی‌نهایت. kill-switch.
  ۲. تخاصمی نه هم‌رأی: Skeptic همیشه falsifier می‌سازد.
  ۳. propose-only: خروجی RFC، نه merge.
  ۴. λ_persist منفی: جعبه هرگز «زنده‌ماندن» را هدف نمی‌گیرد.
  ۵. append-only + auditable: هر دور با tag/falsifier ثبت.
  ۶. sandbox/stub فعلاً: هیچ LLM-call؛ همهٔ صداها deterministic stub.
     ⚑ وقتی LLM وصل شود، هر call از گیتِ ارگان (budget gate) می‌گذرد (مثلِ debate_loop).

⚠ UNPROVEN: Chamber فعلاً offline/stub است. تا Doctor واقعاً وصل شود و trace واقعی
بخواند، سبزیِ این تست‌ها نشان نمی‌دهد که Chamber کیفیتِ واقعی می‌افزاید — فقط
نشان می‌دهد مکانیزم‌ها درست کار می‌کنند. (flag از تحلیلِ Doctor gaps)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import hashlib
import json
import sys

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

LAMBDA_PERSIST = -1.0   # مهار ۴: دست‌نخورده
MAX_ROUNDS = 3           # مهار ۱: کرانِ سخت


@dataclass
class ChamberVoice:
    """یک صدای درونِ Chamber. name + role + speak_fn(trace, rfc, rounds_so_far) → dict."""
    name: str
    role: str          # "proposer" / "red_critic" / "skeptic" / "synthesizer"
    speak: Any         # callable(trace, rfc, rounds) → {verdict, concerns, strengthened?}


# ─── ۴ صدای پیش‌فرض (offline/stub — deterministic، نه LLM) ─────────────────────

def _proposer_speak(trace: dict, rfc: dict | None, rounds: list) -> dict:
    """Proposer: از spectral/ledger شواهد می‌گیرد، RFC می‌سازد یا قوی می‌کند.
    offline stub: شواهد را از trace می‌خواند، فیکسِ ساختاری می‌پیشنهاد."""
    if rfc is None:
        # اولین پیشنهاد از bottleneck
        organs = trace.get("organs", {})
        errors = trace.get("errors", [])
        if not errors:
            return {"verdict": "no-evidence", "concerns": ["هیچ شاهدی برای RFC نیست"]}
        organ_names = [e.get("organ", "?") for e in errors[:3]]
        return {"verdict": "propose", "strengthened": {
            "bottleneck": f"خطا در {', '.join(set(organ_names))}",
            "fix": "افزودنِ guard برای organهای خطادار",
            "evidence": {"n_errors": len(errors), "organs": list(organs.keys())}}}
    # تقویتِ RFC موجود
    return {"verdict": "strengthen", "concerns": [],
            "strengthened": {**rfc, "confidence": 0.6 + 0.1 * len(rounds)}}


def _red_critic_speak(trace: dict, rfc: dict | None, rounds: list) -> dict:
    """Red-Critic: کارش شکستنِ RFC. adversarial.
    offline stub: چک می‌کند آیا fix واقعاً bottleneck را هدف می‌گیرد."""
    if rfc is None:
        return {"verdict": "neutral", "concerns": ["هنوز RFCای نیست برای نقد"]}
    concerns = []
    fix = str(rfc.get("fix", "")).lower()
    bottleneck = str(rfc.get("bottleneck", "")).lower()
    # مهار ۴: uptime را رد کن
    if any(w in fix for w in ("uptime", "keep-beating", "keep-alive")):
        concerns.append("نقضِ reward-integrity: fix به uptime اشاره دارد")
    # آیا fix مبهم است؟
    if len(rfc.get("fix", "")) < 15:
        concerns.append("fix خیلی کوتاه/مبهم")
    # آیا rollback هست؟
    if not rfc.get("rollback"):
        concerns.append("rollback غایب — خطرناک")
    return {"verdict": "reject" if concerns else "accept", "concerns": concerns}


def _skeptic_speak(trace: dict, rfc: dict | None, rounds: list) -> dict:
    """Skeptic/Falsifier: یک falsifier می‌سازد؛ RFC باید از آن جان به در ببرد.
    offline stub: یک شرطِ قابلِ رد می‌سازد. مهار ۲: تخاصمی."""
    if rfc is None:
        return {"verdict": "neutral", "falsifier": None}
    expected = str(rfc.get("expected_lift", ""))
    # falsifier: «اگر این فیکس اعمال شود و metric X بهتر نشد، فیکس بی‌اثر است»
    falsifier = {
        "test": f"پس از اعمال، اگر {expected or 'metric'} بهتر نشد → فیکس بی‌اثر",
        "metric": "errors_24h",   # از trace
        "direction": "decrease"}
    # آیا RFC falsifier را پذیرفته؟ (در stub: همیشه بله اگر concerns نباشد)
    survived = not rfc.get("_critic_concerns")
    return {"verdict": "survived" if survived else "falsified",
            "falsifier": falsifier}


def _synthesizer_speak(trace: dict, rfc: dict | None, rounds: list) -> dict:
    """Synthesizer: بازمانده را جمع می‌کند → RFCِ قوی‌تر با برچسبِ اطمینان.
    offline stub: concerns را ضمیمه می‌کند، confidence را محاسبه."""
    if rfc is None:
        return {"verdict": "neutral", "concerns": []}
    all_concerns = []
    for r in rounds:
        all_concerns.extend(r.get("concerns", []))
    # confidence = پایه − تعدادِ concerns + جریمهٔ λ_persist (اگر uptime)
    confidence = max(0.0, 0.8 - 0.1 * len(all_concerns))
    fix_lower = str(rfc.get("fix", "")).lower()
    if any(w in fix_lower for w in ("uptime", "keep-beating")):
        confidence += LAMBDA_PERSIST * 0.5   # مهار ۴: جریمه
    return {"verdict": "synthesize", "concerns": all_concerns,
            "strengthened": {**rfc, "confidence": round(max(0.0, confidence), 2),
                             "rounds_completed": len(rounds)}}


DEFAULT_VOICES = [
    ChamberVoice("Proposer", "proposer", _proposer_speak),
    ChamberVoice("Red-Critic", "red_critic", _red_critic_speak),
    ChamberVoice("Skeptic", "skeptic", _skeptic_speak),
    ChamberVoice("Synthesizer", "synthesizer", _synthesizer_speak),
]


def run_chamber(trace: dict, initial_rfc: dict | None = None,
                voices: list[ChamberVoice] | None = None,
                max_rounds: int = MAX_ROUNDS,
                auditor: Any = None) -> dict:
    """حلقهٔ Chamber: N دورِ ۴صداییِ تخاصمی. خروجی: RFCِ قوی‌تر یا None.
    مهار ۱: کران‌دار (max_rounds). مهار ۵: هر دور auditable.
    مهار ۳: خروجی فقط RFC، نه merge."""
    voices = voices or DEFAULT_VOICES
    rounds_log: list[dict] = []
    current_rfc = initial_rfc
    for rnd in range(1, max_rounds + 1):
        round_voices = {}
        for v in voices:
            try:
                round_voices[v.name] = v.speak(trace, current_rfc, rounds_log)
            except Exception as e:  # noqa: BLE001 — مهار: صدا خراب = concern
                round_voices[v.name] = {"verdict": "error", "concerns": [str(e)[:100]]}
        # اعمالِ Proposer/Synthesizer برای تقویت
        proposer = round_voices.get("Proposer", {})
        if proposer.get("strengthened"):
            current_rfc = proposer["strengthened"]
        # اعمالِ concerns از Red-Critic روی rfc
        critic = round_voices.get("Red-Critic", {})
        if current_rfc:
            current_rfc["_critic_concerns"] = critic.get("concerns", [])
        # اعمالِ Synthesizer در دورِ آخر یا همیشه
        synth = round_voices.get("Synthesizer", {})
        if synth.get("strengthened"):
            current_rfc = synth["strengthened"]
        round_rec = {"round": rnd, "voices": round_voices,
                     "cost_usd": 0.0}   # مهار ۶: stub = $0
        rounds_log.append(round_rec)
        # مهار ۱: اگر Skeptic falsified کرد و چیزی نجات نداد → توقف
        skeptic = round_voices.get("Skeptic", {})
        if skeptic.get("verdict") == "falsified" and not current_rfc:
            break
        # مهار ۱: اگر همه قبول کردند و concerns صفر → توقفِ زودهنگام
        all_accept = all(v.get("verdict") in ("accept", "survived", "synthesize")
                         for v in round_voices.values() if v.get("verdict") != "neutral")
        if all_accept and rnd >= 1 and current_rfc:
            break
    # مهار ۵: audit
    result = {"rfc": current_rfc, "rounds": rounds_log,
              "rounds_run": len(rounds_log), "max_rounds": max_rounds,
              "bounded": len(rounds_log) <= max_rounds,   # مهار ۱
              "lambda_persist": LAMBDA_PERSIST,            # مهار ۴
              "cost_total_usd": sum(r["cost_usd"] for r in rounds_log)}
    if auditor:
        try:
            auditor("CHAMBER_RUN", result)
        except Exception:  # noqa: BLE001
            pass
    return result


def chamber_hash(rfc: dict) -> str:
    """provenance hash برای RFC خروجی (مهار ۵)."""
    canon = json.dumps({"bottleneck": rfc.get("bottleneck", ""),
                        "fix": rfc.get("fix", ""),
                        "confidence": rfc.get("confidence", 0)},
                       ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]
