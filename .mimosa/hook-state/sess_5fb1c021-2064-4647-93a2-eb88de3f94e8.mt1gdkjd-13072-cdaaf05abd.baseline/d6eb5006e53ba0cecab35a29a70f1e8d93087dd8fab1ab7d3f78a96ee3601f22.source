"""
agents/reporter.py — W3: Reporter.

Compiles the final experiment report card from all agent outputs:
Rosetta table (project↔math↔literature), verdict, confidence level.
"""
from __future__ import annotations
from .base import BaseAgent, AgentResult


class ReporterAgent(BaseAgent):
    name = "W3-Reporter"
    role = "report compiler (final synthesis)"
    task_type = "report"

    def run(self, inputs: dict) -> AgentResult:
        """
        Inputs:
            verifier:    AgentResult from W0
            detector:    AgentResult from W1
            analyst:     AgentResult from W2
            series:      numpy array
            label:       str
        """
        ver = inputs.get("verifier")
        det = inputs.get("detector")
        ana = inputs.get("analyst")
        label = inputs.get("label", "unknown")

        det_f = det.findings if det else {}
        ana_f = ana.findings if ana else {}

        detectable = det_f.get("detectable", False)
        ver_pass = ver.findings.get("all_pass", False) if ver else False

        # Build the quantitative summary table
        rosetta = self._build_rosetta(det_f)

        # Ask the LLM for the final synthesis
        prompt = self._build_prompt(label, det_f, ana_f, ver_pass)
        narrative = self.llm(prompt, temperature=0.5)

        # Determine overall verdict
        # گاردِ دفاعی: اگر detector اصلاً اجرا نشده/شکست خورده، «نبودِ داده» را
        # نباید به «نتیجه‌ی منفیِ مطمئن» تبدیل کرد.
        det_failed = (det is None) or (getattr(det, "status", "") == "fail")
        if det_failed:
            verdict = "INCOMPLETE — detector failed (no analyzable data)"
            confidence = "none"
        elif detectable and ver_pass:
            verdict = "HYPOTHESIS SUPPORTED — hidden dimension detected"
            confidence = "high" if det_f.get("temporal_mi", 0) > 0.01 else "medium"
        elif detectable:
            verdict = "PROVISIONAL — structure detected but model unverified"
            confidence = "low"
        else:
            verdict = "NULL RESULT — no detectable hidden dimension"
            confidence = "high"

        findings = {
            "label": label,
            "verdict": verdict,
            "confidence": confidence,
            "model_verified": ver_pass,
            "structure_detected": detectable,
            "rosetta_table": rosetta,
            "report_card": narrative,
        }

        return self._make_result(
            findings=findings,
            narrative=narrative,
            status="warning" if det_failed else "ok",
        )

    def _build_rosetta(self, det_f: dict) -> list[dict]:
        """Build the Rosetta table: project ↔ math ↔ human experience."""
        return [
            {"project": "E_shadow", "math": "½log(σ_z²/S_b)",
             "empirical": f"{det_f.get('temporal_mi', 0):.6f}",
             "human": "آیا چیزی پشت پرده هست؟"},
            {"project": "Δ_self", "math": "½log(S_b/S)",
             "empirical": "0.122520 (anchor)",
             "human": "ارزش درون‌نگری"},
            {"project": "I_pred", "math": "½Σlog(S_L/S_b)",
             "empirical": "0.0144179 (anchor)",
             "human": "کل پیش‌بینی‌پذیری"},
            {"project": "λρ≠0", "math": "identifiability",
             "empirical": str(det_f.get('detectable', False)),
             "human": "آیا سایه لو می‌دهد؟"},
        ]

    def _build_prompt(self, label, det_f, ana_f, ver_pass) -> str:
        return f"""گزارش نهاییِ آزمایش را کامپایل کن.

داده: {label}
مدل راستی‌آزمایی شد: {'بله' if ver_pass else 'خیر'}

یافته‌های تشخیص:
- اطلاعات متقابل زمانی: {det_f.get('temporal_mi', 0):.6f}
- ρ تخمینی: {det_f.get('rho_hat', 0):.4f}
- قابل‌تشخیص: {'بله' if det_f.get('detectable') else 'خیر'}

تفسیر هندسی (خلاصه):
{ana_f.get('geometric_interpretation', 'ناموجود')[:500]}

یک report card بساز با این ساختار:
۱. فرضیه: آیا نشانه‌ی بُعد پنهان در داده هست؟
۲. داده و روش (یک خط)
۳. کمیت‌های اندازه‌گیری‌شده (جدول)
۴. تأیید/رد فرضیه با درجه‌ی اطمینان
۵. محدودیت‌ها (چه چیزی را نمی‌توانیم از این نتیجه بگوییم؟)
۶. پیشنهاد گام بعد

صادق باش: اگر نتیجه منفی است، آن را ثبت کن — نتایج منفی هم ارزشمندند."""
