/**
 * Meta-Learning / Self-Modification Agent — weekly review → PROPOSALS ONLY.
 * Nothing applies without explicit user approval (spec §9).
 * Guardrails: may never weaken safety rules, never raise cap above 20,
 * never touch consent defaults, never execute code changes itself.
 */

export interface WeeklyOps {
  checkinsSentBySlot: Record<string, { sent: number; answered: number }>;
  avgAnswerRate: number;
  burdenComplaints: number; // "stop for today" + pause events
  patternCorrectionsRejected: number;
  llmFailures: number;
  llmTokens: number;
  capHits: number; // days the 20-cap was reached
  quietHourViolations: number; // MUST stay 0
}

export interface SelfModProposalDraft {
  category: 'message_budget' | 'quiet_hours' | 'question_bank' | 'schedule' | 'prompt' | 'parameter' | 'code';
  title: string;
  hypothesis: string;
  evidence: string;
  expectedEffect: string;
  burden: 'low' | 'medium' | 'high';
  risk: 'low' | 'medium' | 'high';
  rollbackPlan: string;
}

const CAP_MAX = 20;

export function draftProposals(ops: WeeklyOps): SelfModProposalDraft[] {
  const proposals: SelfModProposalDraft[] = [];

  // dead slots → move or drop
  for (const [slot, s] of Object.entries(ops.checkinsSentBySlot)) {
    if (s.sent >= 4 && s.answered / s.sent < 0.25) {
      proposals.push({
        category: 'schedule',
        title: `کاهش یا جابه‌جایی اسلات «${slot}»`,
        hypothesis: `پیام‌های ${slot} در زمان بدی می‌رسند`,
        evidence: `${s.answered}/${s.sent} پاسخ در ۷ روز اخیر`,
        expectedEffect: 'کاهش پیام بی‌فایده، افزایش نرخ پاسخ',
        burden: 'low',
        risk: 'low',
        rollbackPlan: 'برگرداندن اسلات به تنظیم قبلی با یک تایید',
      });
    }
  }

  if (ops.burdenComplaints >= 2) {
    proposals.push({
      category: 'message_budget',
      title: 'کاهش سقف پیشنهادی چک‌این روزانه',
      hypothesis: 'بار پیام فعلی بیشتر از حد مفید است',
      evidence: `${ops.burdenComplaints} سیگنال بار (توقف/pause) این هفته`,
      expectedEffect: 'کاهش فشار، حفظ همراهی بلندمدت',
      burden: 'low',
      risk: 'low',
      rollbackPlan: 'بازگشت به 3–6 پیش‌فرض',
    });
  }

  if (ops.patternCorrectionsRejected >= 2) {
    proposals.push({
      category: 'parameter',
      title: 'سخت‌گیرتر کردن آستانهٔ confidence الگوها',
      hypothesis: 'الگوها زودتر از حد به کاربر نشان داده می‌شوند',
      evidence: `${ops.patternCorrectionsRejected} الگو توسط کاربر رد شد`,
      expectedEffect: 'الگوهای کمتر اما دقیق‌تر',
      burden: 'low',
      risk: 'low',
      rollbackPlan: 'بازگرداندن آستانه‌های قبلی',
    });
  }

  if (ops.llmFailures >= 3) {
    proposals.push({
      category: 'code',
      title: 'بررسی خطاهای مکرر LLM provider',
      hypothesis: 'پیکربندی یا سقف توکن مشکل دارد',
      evidence: `${ops.llmFailures} خطای LLM این هفته`,
      expectedEffect: 'تحلیل هفتگی پایدارتر',
      burden: 'medium',
      risk: 'low',
      rollbackPlan: 'N/A — فقط ایجاد تسک برای توسعه‌دهنده؛ اجرای خودکار ممنوع',
    });
  }

  if (ops.quietHourViolations > 0) {
    proposals.push({
      category: 'code',
      title: '🚨 نقض ساعت سکوت — باگ بحرانی',
      hypothesis: 'مسیر ارسالی خارج از گیت مرکزی وجود دارد',
      evidence: `${ops.quietHourViolations} پیام در ساعت سکوت`,
      expectedEffect: 'بازگرداندن تضمین ساعت سکوت',
      burden: 'high',
      risk: 'high',
      rollbackPlan: 'N/A — رفع باگ توسط توسعه‌دهنده، اولویت فوری',
    });
  }

  return proposals;
}

/** Validate a config-category application against hard guardrails. */
export function validateApplication(
  category: SelfModProposalDraft['category'],
  patch: Record<string, unknown>,
): { ok: boolean; reason?: string } {
  if (category === 'code' || category === 'prompt') {
    return { ok: false, reason: 'code/prompt proposals become todo tasks — never auto-applied' };
  }
  if ('dailyCap' in patch && Number(patch.dailyCap) > CAP_MAX) {
    return { ok: false, reason: `dailyCap may never exceed ${CAP_MAX}` };
  }
  const forbidden = ['consentDefaults', 'safetyRules', 'calorieFloor'];
  for (const key of Object.keys(patch)) {
    if (forbidden.some((f) => key.toLowerCase().includes(f.toLowerCase()))) {
      return { ok: false, reason: `${key} is guardrail-protected` };
    }
  }
  return { ok: true };
}
