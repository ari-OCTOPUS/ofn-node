"""equation_explainer.py — فاز Q: پاسخ ساده دربارهٔ هر معادله + وضعیت واقعی.

پنج سطح برای هر معادله:
    1) تعریف ریاضی  2) معنی ساده  3) ورودی‌های runtime
    4) سطح اثر واقعی (SPEC/BUILT/TESTED/DIAGNOSTIC/SHADOW/ADVISORY/PROPOSAL_ONLY/ACTIVE/CONFLICT)
    5) شواهد فایل/تست/runtime

statusها از کشف واقعی (00-DISCOVERY-REPORT §۵) و runtime truth می‌آیند — از نام فایل حدس زده نمی‌شوند.
خروجی همیشه با برچسب advice-only؛ هیچ فرمانی.
"""
from __future__ import annotations

import json
import time
from typing import Any

EXPLAINER_SCHEMA = "equation-explainer.v1"

# وضعیت‌های مجاز (منشور)
STATUSES = ("SPEC", "BUILT", "TESTED", "DIAGNOSTIC", "SHADOW", "ADVISORY",
            "PROPOSAL_ONLY", "ACTIVE", "CONFLICT")

# کاتالوگ واقعی — از discovery (فایل‌های تأییدشده، نه حدس)
CATALOG: dict[str, dict[str, Any]] = {
    "bcm": {
        "id": "bcm",
        "name": "BCM",
        "formula": "θ=EMA(y²)؛ φ=y·(y−θ)؛ Δw=η·φ−β·w",
        "plain": "آستانه‌ای متحرک که با فعالیت بالا می‌رود تا یادگیری همیشه‌فعال اشباع نشود (ضد reward-hack).",
        "inputs": ["y (activation)", "η (learning)", "β (forgetting)"],
        "status": "TESTED",
        "evidence": ["_ops/neural/bcm.py", "tests/test_bcm_forgetting.py",
                     "signals-registry TESTED/TESTED"],
        "limitations": ["advisory — هیچ تصمیمی روی آن سوار نیست"],
    },
    "hebbian": {
        "id": "hebbian",
        "name": "هبیان",
        "formula": "s←min(1,s+0.10)؛ s←0.995·s؛ prune<0.005",
        "plain": "هم‌وقوعی تقویت می‌کند، غیاب می‌فرساید؛ نیمه‌عمر ~۲۳ روز در 60s/tick.",
        "inputs": ["co-occurrence", "tick بدون هم‌وقوعی"],
        "status": "TESTED",
        "evidence": ["_ops/neural/hebbian.py", "tests/test_hebbian_signals.py",
                     "signals-registry TESTED/TESTED"],
        "limitations": ["observe/decay — وارد learned_pressure نمی‌شود"],
    },
    "nociceptor": {
        "id": "nociceptor-pain",
        "name": "درد/نوسیپتور",
        "formula": "pain = Σ wᵢ·fᵢ (budget,error,freeze,partner,afferent,σ)",
        "plain": "ترمز محافظتی: وقتی شاخص‌های سلامت بدند، کار غیرضروری متوقف/آهسته می‌شود.",
        "inputs": ["budget_pct", "error_rate", "freeze_active", "σ"],
        "status": "ACTIVE",
        "evidence": ["_ops/neural/nociceptor.py:195-232",
                     "ADR-035 APPLY=1 (protective_skip محلی)"],
        "limitations": ["فقط beat-local؛ هیچ پول/ارسال/ledger"],
    },
    "latent-cosine": {
        "id": "latent-cosine",
        "name": "بازیابی کسینوسی latent",
        "formula": "cos(U,q) = (U·q)/(‖U‖‖q‖)",
        "plain": "بازیابی ۳۲بُعدی هش‌شده با شباهت کسینوسی.",
        "inputs": ["query vector", "latent space"],
        "status": "PROPOSAL_ONLY",
        "evidence": ["_ops/neural/latent_space.py", "Phase 2 Blueprint — بدون تست/registry/caller"],
        "limitations": ["هیچ مصرف‌کنندهٔ تصمیم ندارد"],
    },
    "identity": {
        "id": "identity",
        "name": "هویت L,E,G,K,O",
        "formula": "O = 0.25L+0.25E+0.20G+0.15K+0.15·alive (با شرط مرگ)",
        "plain": "پنج نمرهٔ خودشناسی با نرمال‌سازی اشباع‌شونده؛ فقط گزارش.",
        "inputs": ["Δ", "Ĉ", "R̂", "M̂", "σ̂", "coherence"],
        "status": "ACTIVE",
        "evidence": ["_ops/identity_equations.py", "signals-registry LOCKED",
                     "spine.py:157-181"],
        "limitations": ["read-only — هیچ gate/پول"],
    },
    "sog": {
        "id": "sog-dare",
        "name": "SOG/DARE/کالمن",
        "formula": "P بسته‌شکل DARE؛ K=Pλ/S؛ Δ_self=½ln(S_b/S)",
        "plain": "ارزش اطلاعاتیِ دسترسی اول‌شخص — گران‌بهاترین ریاضیِ سیستم.",
        "inputs": ["σ_z²", "σ_e²", "ρ", "λ"],
        "status": "LOCKED",
        "evidence": ["_ops/heart/sog_math.py", "state/sim/PULSE-EQUATIONS-LOCKED.json",
                     "MC 1.2M گام + ۱۱ anchor", "test_sog_provenance.py"],
        "limitations": ["diagnostic — خروجی OTLP فقط"],
    },
    "living-beat": {
        "id": "living-beat-control",
        "name": "قانون کنترل Living-Beat",
        "formula": "period از velocity؛ π=π_n·π_reg (inverse-variance)",
        "plain": "ضربان از سرعتِ کار ظاهر می‌شود؛ σ فقط ترمز است.",
        "inputs": ["velocity", "CV gaps", "σ", "CPI/budget"],
        "status": "ACTIVE",
        "evidence": ["_ops/heart/control_law.py", "organism.py:577 (HH-P11 arbiter)",
                     "test_heart_math.py"],
        "limitations": ["advisory period؛ wire_open گیت‌شده"],
    },
    "allometry": {
        "id": "allometry",
        "name": "آلومتری Kleiber",
        "formula": "period = BASE·(mass/REF)^(1/4)",
        "plain": "بدنِ بزرگ‌تر → ضربانِ کندتر؛ «جرم» استعارهٔ کمّی (شمارش پروژه).",
        "inputs": ["mass (count)", "REF", "baroreflex"],
        "status": "SHADOW",
        "evidence": ["_ops/cardiac.py:76-97", "test_cardiac_allometry.py",
                     "flag OCTOPUS_WIRE_HEBBIAN_CARDIAC (default OFF)"],
        "limitations": ["flag-off پیش‌فرض؛ جرم استعاری"],
    },
    "phi": {
        "id": "phi-accrual",
        "name": "Phi-Accrual",
        "formula": "φ = −log₁₀(P_later)",
        "plain": "آشکارساز شکست: گپ‌های ack → alive/suspected/failed.",
        "inputs": ["ack gaps", "mean", "std"],
        "status": "DIAGNOSTIC",
        "evidence": ["_ops/chrono.py:129-172", "test_chrono_heartbeat.py"],
        "limitations": ["فقط نظارت؛ با PHI_HONEST صادق"],
    },
    "spectral-sigma": {
        "id": "spectral-sigma-legacy",
        "name": "σ طیفی (legacy)",
        "formula": "σ = λ_max/(λ₂+ε)",
        "plain": "شاخص بحرانیت گراف رویدادها؛ نزدیکی به ۱ = گذار فاز.",
        "inputs": ["Laplacian L(G)=D−A", "eigenvalues"],
        "status": "ACTIVE",
        "evidence": ["_ops/doctor/spectral.py", "spine.py:104-120",
                     "test_spectral_definitions.py"],
        "limitations": ["heuristic؛ تعریف v2 (λ₂/λ_max) shadow است"],
    },
    "chrono-rhythm": {
        "id": "chrono-rhythm",
        "name": "ریتم چرونو CR-B0",
        "formula": "T_beat = T0·exp(+κ·readiness−λ·stress)·(1+ε·ξ_1/f)",
        "plain": "ضربان متغیر با نویز 1/f؛ readiness کندتر، stress سریع‌تر.",
        "inputs": ["readiness", "stress", "novelty", "σ"],
        "status": "TESTED",
        "evidence": ["_ops/chrono_rhythm/rhythm.py", "test_rhythm.py",
                     "signals-registry TESTED/SHADOW (معتبر طبق validator)"],
        "limitations": ["advisory؛ CR-B1 کوراموتو فقط pure helper"],
    },
    "decay": {
        "id": "decay-reinforcement",
        "name": "Decay-Reinforcement",
        "formula": "value←(1−ρ)·value+Σreinforce",
        "plain": "یک knob (ρ) برای پوسیدن/تقویت ارزش‌ها.",
        "inputs": ["ρ", "reinforce", "floor/ceil"],
        "status": "ADVISORY",
        "evidence": ["_ops/coherence.py", "cortex/consolidate.py (HALFLIFE_H=24)"],
        "limitations": ["پراکنده؛ یک knob واحد ندارد"],
    },
    "fusion": {
        "id": "fusion",
        "name": "میدان فیوژن A=−L(G)",
        "formula": "A = −L(G)",
        "plain": "میدان مشترک fusion برای spectral-sense → Box؛ معادل دیفیوژن.",
        "inputs": ["L(G)"],
        "status": "SHADOW",
        "evidence": ["_ops/doctor/box/b4_fusion.py", "signals-registry SHADOW",
                     "DOCTOR-BOX-OF-AGENTS-SPEC"],
        "limitations": ["در مسیر spine نیست"],
    },
    "doctor-z": {
        "id": "doctor-z",
        "name": "دینامیک z / ρ(J)",
        "formula": "X_{t+1}≈J·X_t+b+noise؛ ρ(J)<1",
        "plain": "پایداری با شعاع طیفی ژاکوبین؛ لبهٔ بحرانیت ρ≈0.9–0.98.",
        "inputs": ["s,v,f,c", "J"],
        "status": "DIAGNOSTIC",
        "evidence": ["_ops/doctor/box/sensors.py:44", "warden.py:60 (safety cap)",
                     "DOCTOR-BOX-OF-AGENTS-SPEC"],
        "limitations": ["spec کامل نیست؛ warden فقط سقف ایمنی"],
    },
}

_ALIASES = {
    "bcm": "bcm", "هبیان": "hebbian", "hebbian": "hebbian",
    "درد": "nociceptor", "nociceptor": "nociceptor", "pain": "nociceptor",
    "latent": "latent-cosine", "هویت": "identity", "identity": "identity",
    "sog": "sog", "dare": "sog", "kalman": "sog",
    "کنترل": "living-beat", "control": "living-beat", "living": "living-beat",
    "آلومتری": "allometry", "allometry": "allometry", "kleiber": "allometry",
    "phi": "phi", "فای": "phi", "sigma": "spectral-sigma", "سیگما": "spectral-sigma",
    "طیف": "spectral-sigma", "ریتم": "chrono-rhythm", "rhythm": "chrono-rhythm",
    "کوراموتو": "chrono-rhythm", "decay": "decay", "پوسش": "decay",
    "fusion": "fusion", "میدان": "fusion", "z": "doctor-z",
    "rho": "doctor-z", "ژاکوبین": "doctor-z",
}

_QUESTION_HINTS = ("چیست", "چیه", "چیست؟", "چه کاری", "چه اثری", "چقدر اختیار",
                   "بگو", "توضیح", "شرح", "شرح بده", "معنی", "تشکیل")


def resolve_equation(query: str) -> str | None:
    """معادلهٔ موردنظر از پرسش — با alias و کلمهٔ کلیدی."""
    q = str(query or "").strip().lower()
    for key, eqid in _ALIASES.items():
        if key in q:
            return eqid
    # پیش‌فرض: هر سؤال معادله → کوتاه‌ترین تطبیق نام
    for eqid, meta in CATALOG.items():
        if meta["name"].lower() in q:
            return eqid
    return None


def explain(query: str) -> dict[str, Any]:
    """توضیح معادله با ۵ سطح + شاهد. advice-only."""
    eqid = resolve_equation(query)
    if eqid is None:
        return {
            "schema": EXPLAINER_SCHEMA,
            "matched": False,
            "text": "معادلهٔ مشخصی در پرسش پیدا نکردم. بپرس مثلاً «BCM چیست؟» یا «سیگما چه اثری دارد؟»",
            "equation": None,
            "equation_advice_only": True,
            "decision_effect": False,
            "apply_effect": False,
            "may_authorize": False,
        }
    meta = CATALOG[eqid]
    status = meta["status"]

    # Truth Layer — verify evidence_refs واقعاً وجود دارند
    try:
        import sys
        from pathlib import Path as _Pth
        _cog = str(_Pth(__file__).resolve().parent.parent / "cognitive")
        if _cog not in sys.path:
            sys.path.insert(0, _cog)
        import truth_layer as _tl  # noqa: WPS433
        claim = _tl.make_claim(
            f"{meta['name']} exists in this repo",
            evidence_refs=meta["evidence"],
        )
        _tl.verify_claim(claim)
        runtime_verified = claim["runtime_verified"]
        verification = claim["verification"]
    except Exception:  # noqa: BLE001
        runtime_verified = False
        verification = "UNVERIFIED"

    lines = [
        f"{meta['name']} به زبان ساده: {meta['plain']}",
        f"فرمول: {meta['formula']}",
        f"ورودی‌های runtime: {', '.join(meta['inputs'])}",
        f"وضعیت واقعی در این مخزن: {status}.",
        "یعنی می‌تواند سیگنال بدهد/توصیه کند، ولی خودش فرمان اجرا نمی‌کند." if
        status in ("TESTED", "DIAGNOSTIC", "SHADOW", "ADVISORY", "PROPOSAL_ONLY")
        else "یعنی در مسیر زندهٔ تصمیم/حفاظت فعال است (با گیت)." if status in ("ACTIVE", "LOCKED")
        else "",
        "محدودیت‌ها: " + "؛ ".join(meta["limitations"]),
        "شاهد: " + " · ".join(meta["evidence"]),
    ]
    return {
        "schema": EXPLAINER_SCHEMA,
        "matched": True,
        "equation_id": meta["id"],
        "name": meta["name"],
        "text": "\n".join(line for line in lines if line),
        "equation": {
            "equation_id": meta["id"],
            "plain_language": meta["plain"],
            "inputs": meta["inputs"],
            "runtime_status": status,
            "decision_effect": False,
            "apply_effect": False,
            "limitations": meta["limitations"],
            "evidence_refs": meta["evidence"],
            "runtime_verified": runtime_verified,
            "verification": verification,
        },
        "equation_advice_only": True,
        "decision_effect": False,
        "apply_effect": False,
        "may_authorize": False,
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "BCM چیست؟"
    print(json.dumps(explain(q), ensure_ascii=False, indent=2))
