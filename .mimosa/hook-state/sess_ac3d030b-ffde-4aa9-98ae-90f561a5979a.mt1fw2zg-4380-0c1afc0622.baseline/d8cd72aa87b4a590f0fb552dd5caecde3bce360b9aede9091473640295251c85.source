import { toPersianDigits } from '@wlos/shared';
import { rollingAverage, trendSummary, type DayValue } from '@wlos/nutrition-engine';
import type { AssociationFinding } from './patterns.js';

/** Report Agent — deterministic daily/weekly/coach-ready builders. */

export interface DailyReportInput {
  dayKey: string;
  displayName: string;
  totalCalories: number | null;
  targetLow: number | null;
  targetHigh: number | null;
  proteinG: number | null;
  proteinTarget: number | null;
  mealsLogged: number;
  weightToday: number | null;
  avg7: number | null;
  workoutTitle: string | null;
  sleepHours: number | null;
  steps: number | null;
  hideCalories: boolean;
}

export function buildDailyReportFa(d: DailyReportInput): string {
  const lines: string[] = [`📊 گزارش امروز (${d.dayKey})`];
  if (d.totalCalories !== null && !d.hideCalories) {
    const target =
      d.targetLow && d.targetHigh ? ` (هدف: ${d.targetLow}–${d.targetHigh})` : '';
    lines.push(`• کالری: ${d.totalCalories} cal${target} — ${d.mealsLogged} وعده ثبت شد`);
  } else if (d.hideCalories) {
    lines.push(`• وعده‌های ثبت‌شده: ${toPersianDigits(d.mealsLogged)} (نمایش کالری خاموشه)`);
  } else {
    lines.push('• غذایی ثبت نشده');
  }
  if (d.proteinG !== null && d.proteinG > 0) {
    lines.push(`• پروتئین: ~${d.proteinG}g${d.proteinTarget ? ` — هدف ${d.proteinTarget}g` : ''}`);
  }
  if (d.weightToday !== null) {
    lines.push(`• وزن: ${d.weightToday} kg${d.avg7 ? ` — میانگین 7 روزه: ${d.avg7} kg` : ''}`);
  }
  if (d.workoutTitle) lines.push(`• تمرین: ${d.workoutTitle} ✅`);
  if (d.sleepHours !== null) lines.push(`• خواب دیشب: ${d.sleepHours}h`);
  if (d.steps !== null) lines.push(`• قدم‌ها: ${d.steps}`);
  lines.push('', 'روند مهمه، نه یک روز. 🌱');
  return lines.join('\n');
}

export interface WeeklyReportInput {
  weekEndDayKey: string;
  weights: DayValue[];
  intakeDays: DayValue[]; // logged daily totals
  targetLow: number | null;
  targetHigh: number | null;
  workoutsCompleted: number;
  workoutsPlanned: number;
  sleepAvg: number | null;
  checkinsSent: number;
  checkinsAnswered: number;
  findings: AssociationFinding[];
  hideCalories: boolean;
}

export function buildWeeklyReportFa(w: WeeklyReportInput): string {
  const t = trendSummary(w.weights);
  const roll = rollingAverage(w.weights, 7, 3);
  const lastAvg = roll.length ? roll[roll.length - 1]!.avg : null;
  const intakeAvg =
    w.intakeDays.length > 0
      ? Math.round(w.intakeDays.reduce((s, d) => s + d.value, 0) / w.intakeDays.length)
      : null;

  const lines: string[] = [`🗓 گزارش هفتگی — تا ${w.weekEndDayKey}`, ''];

  lines.push('وزن:');
  if (t.classification === 'insufficient_data') {
    lines.push('• داده هنوز برای نتیجه‌گیری کافی نیست — ادامه بده، همین ثبت کردن خودش برده.');
  } else {
    lines.push(
      `• میانگین 7 روزه: ${lastAvg ?? '—'} kg`,
      `• شیب: ${t.slopeKgPerWeek} kg/هفته (${faClass(t.classification)})`,
    );
  }

  if (!w.hideCalories && intakeAvg !== null) {
    lines.push(
      '',
      'تغذیه:',
      `• میانگین روزانه: ~${intakeAvg} cal${w.targetLow ? ` (هدف ${w.targetLow}–${w.targetHigh})` : ''}`,
      `• روزهای ثبت‌شده: ${w.intakeDays.length}/7`,
    );
  }

  lines.push(
    '',
    'تمرین:',
    `• ${w.workoutsCompleted} از ${w.workoutsPlanned || '?'} جلسه انجام شد`,
  );
  if (w.sleepAvg !== null) lines.push('', `خواب: میانگین ${w.sleepAvg}h`);
  lines.push('', `چک‌این‌ها: ${w.checkinsAnswered}/${w.checkinsSent} پاسخ داده شد`);

  const showable = w.findings.filter((f) => f.confidence !== 'hypothesis');
  if (showable.length) {
    lines.push('', 'الگوهای احتمالی (فرضیه — نه قطعی):');
    for (const f of showable.slice(0, 3)) {
      lines.push(
        `• ${f.antecedent} → ${f.outcome} | شواهد: ${f.evidenceCount}, خلافش: ${f.counterexampleCount} (${f.confidence})`,
      );
    }
    lines.push('برای تایید/رد: /patterns');
  }

  lines.push('', 'هفتهٔ بعد فقط «یک» آزمایش کوچیک — تو /weekly پیشنهادش میاد.');
  return lines.join('\n');
}

export interface CoachReportInput extends WeeklyReportInput {
  displayName: string;
  plateauStatus: string;
  plateauConfidence: string;
  activeExperiments: string[];
  safetyFlags: string[];
  cannabisSummary: string | null; // ONLY when both coach_sharing & cannabis consents granted
  coachNotes: string[];
}

/** English-forward markdown for a human coach/clinician. */
export function buildCoachReportMd(c: CoachReportInput): string {
  const t = trendSummary(c.weights);
  const intakeAvg =
    c.intakeDays.length > 0
      ? Math.round(c.intakeDays.reduce((s, d) => s + d.value, 0) / c.intakeDays.length)
      : null;
  const md: string[] = [
    `# WLOS Coach-Ready Report — week ending ${c.weekEndDayKey}`,
    '',
    `Client: ${c.displayName} (self-tracked data via WLOS; not a medical record)`,
    '',
    '## Weight',
    `- n=${t.nDays} weigh-ins over ${t.spanDays} days, mean ${t.mean ?? '—'} kg, σ ${t.stdDev ?? '—'}`,
    `- trend ${t.slopeKgPerWeek ?? '—'} kg/week (${t.classification})`,
    '',
    '## Nutrition',
    `- avg logged intake: ${intakeAvg ?? '—'} kcal/day over ${c.intakeDays.length}/7 logged days${
      c.targetLow ? `; target ${c.targetLow}–${c.targetHigh}` : ''
    }`,
    '',
    '## Training & recovery',
    `- workouts ${c.workoutsCompleted}/${c.workoutsPlanned || '?'}; sleep avg ${c.sleepAvg ?? '—'} h`,
    '',
    '## Engagement',
    `- check-ins answered ${c.checkinsAnswered}/${c.checkinsSent}`,
    '',
    '## Behavioral patterns (hypotheses with evidence — correlation only)',
    ...(c.findings.length
      ? c.findings.map(
          (f) =>
            `- ${f.antecedent} → ${f.outcome}: evidence ${f.evidenceCount}, counterexamples ${f.counterexampleCount}, ` +
            `rate ${f.antecedentRate ?? '—'} vs base ${f.baseRate ?? '—'} (${f.confidence}; not causal)`,
        )
      : ['- none above hypothesis threshold']),
    '',
    '## Plateau investigation',
    `- status: ${c.plateauStatus} (confidence: ${c.plateauConfidence})`,
    '',
    '## Active experiments',
    ...(c.activeExperiments.length ? c.activeExperiments.map((e) => `- ${e}`) : ['- none']),
    '',
    '## Safety flags this week',
    ...(c.safetyFlags.length ? c.safetyFlags.map((s) => `- ${s}`) : ['- none']),
  ];
  if (c.cannabisSummary) {
    md.push('', '## Cannabis-aware summary (shared with explicit consent)', c.cannabisSummary);
  }
  if (c.coachNotes.length) {
    md.push('', '## Current coach constraints honored by WLOS', ...c.coachNotes.map((n) => `- ${n}`));
  }
  md.push(
    '',
    '---',
    '*Generated by WLOS. Self-reported data; verify clinically before acting. WLOS defers to your judgment — notes you add become constraints for the system.*',
  );
  return md.join('\n');
}

function faClass(c: string): string {
  switch (c) {
    case 'losing':
      return 'در حال کاهش';
    case 'gaining':
      return 'در حال افزایش';
    case 'stable':
      return 'ثابت';
    default:
      return 'نامشخص';
  }
}
