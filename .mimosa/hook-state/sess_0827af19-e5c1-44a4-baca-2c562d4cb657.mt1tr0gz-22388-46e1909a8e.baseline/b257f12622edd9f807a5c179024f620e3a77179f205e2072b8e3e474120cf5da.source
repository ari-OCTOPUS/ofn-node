import { describe, expect, it } from 'vitest';
import { investigatePlateau, type PlateauInputs } from './plateau.js';
import { scanAssociations, type DailyRecord } from './patterns.js';
import { buildCoachReportMd, buildDailyReportFa, buildWeeklyReportFa } from './reports.js';
import { draftProposals, validateApplication } from './self-mod.js';
import type { DayValue } from '@wlos/nutrition-engine';

function flatWeights(days: number, base = 94.5): DayValue[] {
  const t0 = new Date('2026-06-01T00:00:00Z').getTime();
  return Array.from({ length: days }, (_, i) => ({
    dayKey: new Date(t0 + i * 86_400_000).toISOString().slice(0, 10),
    value: base + Math.sin(i / 3) * 0.3,
  }));
}
function intake(days: number, kcal = 2100): DayValue[] {
  const t0 = new Date('2026-06-01T00:00:00Z').getTime();
  return Array.from({ length: days }, (_, i) => ({
    dayKey: new Date(t0 + i * 86_400_000).toISOString().slice(0, 10),
    value: kcal,
  }));
}

const basePlateau: PlateauInputs = {
  weights: flatWeights(30),
  dailyIntake: intake(28),
  intakeLoggingCompleteness: 0.9,
  weekendWeekdayIntakeGapKcal: 100,
  stepsTrend: 'stable',
  sleepAvgHours: 7.2,
  recentTrainingChange: false,
  recentHighSodiumOrTravel: false,
  medicationChange: false,
  medicalSymptoms: false,
};

describe('plateau investigation protocol', () => {
  it('insufficient data short-circuits everything', () => {
    const r = investigatePlateau({ ...basePlateau, weights: flatWeights(6) });
    expect(r.status).toBe('data_insufficient');
    expect(r.smallestSafeExperiment).not.toContain('کاهش کالری');
  });

  it('medical signals route to professional review, no new deficit', () => {
    const r = investigatePlateau({ ...basePlateau, medicationChange: true });
    expect(r.status).toBe('medical_review_recommended');
    expect(r.smallestSafeExperiment).toContain('هیچ کسری کالری');
  });

  it('poor logging → adherence/measurement BEFORE metabolic conclusions', () => {
    const r = investigatePlateau({ ...basePlateau, intakeLoggingCompleteness: 0.5 });
    expect(r.status).toBe('likely_adherence_or_measurement_issue');
  });

  it('weekend drift detected as competing explanation', () => {
    const r = investigatePlateau({ ...basePlateau, weekendWeekdayIntakeGapKcal: 600 });
    expect(r.status).toBe('likely_adherence_or_measurement_issue');
    expect(r.competingExplanations.join(' ')).toContain('weekend');
  });

  it('new training block → water masking hypothesis', () => {
    const r = investigatePlateau({ ...basePlateau, recentTrainingChange: true });
    expect(r.status).toBe('likely_water_weight_masking');
  });

  it('clean data + flat trend → true plateau, and the FIRST experiment is not a calorie cut', () => {
    const r = investigatePlateau(basePlateau);
    expect(r.status).toBe('likely_true_plateau');
    // acceptance criterion: protocol does not immediately reduce calories
    expect(r.smallestSafeExperiment.indexOf('قدم')).toBeGreaterThanOrEqual(0);
    expect(r.smallestSafeExperiment.startsWith('کاهش کالری')).toBe(false);
  });

  it('already losing → no plateau declared', () => {
    const losing = flatWeights(30).map((d, i) => ({ ...d, value: 95 - i * 0.06 }));
    const r = investigatePlateau({ ...basePlateau, weights: losing });
    expect(r.status).toBe('unconfirmed');
  });
});

describe('pattern discovery', () => {
  function records(n: number, fn: (i: number) => Partial<DailyRecord>): DailyRecord[] {
    const t0 = new Date('2026-06-01T00:00:00Z').getTime();
    return Array.from({ length: n }, (_, i) => ({
      dayKey: new Date(t0 + i * 86_400_000).toISOString().slice(0, 10),
      ...fn(i),
    }));
  }

  it('finds sleep→craving association with lift over base rate', () => {
    const data = records(30, (i) => ({
      sleepHours: i % 3 === 0 ? 5 : 7.5,
      eveningCraving: i % 3 === 0 ? i !== 3 : i % 10 === 1, // 9/10 craving after short sleep vs rare otherwise
    }));
    const found = scanAssociations(data, {});
    const f = found.find((x) => x.key === 'sleep_under_6h→evening_craving')!;
    expect(f.evidenceCount).toBeGreaterThan(f.counterexampleCount);
    expect(f.notCausal).toBe(true);
    expect(['low', 'medium', 'high']).toContain(f.confidence);
  });

  it('no lift → stays hypothesis even with many observations', () => {
    const data = records(40, (i) => ({
      sleepHours: i % 2 === 0 ? 5 : 8,
      eveningCraving: i % 5 === 0, // i%5 hits both parities equally → no lift
    }));
    const f = scanAssociations(data, {}).find((x) => x.key === 'sleep_under_6h→evening_craving')!;
    expect(f.confidence).toBe('hypothesis');
  });

  it('cannabis template NEVER runs without consent', () => {
    const data = records(20, (i) => ({ cannabisUse: i % 2 === 0, highIntakeDay: i % 2 === 0 }));
    expect(scanAssociations(data, {}).some((f) => f.key === 'cannabis→high_intake')).toBe(false);
    expect(
      scanAssociations(data, { cannabis: true }).some((f) => f.key === 'cannabis→high_intake'),
    ).toBe(true);
  });
});

describe('reports', () => {
  it('daily report renders Persian with mixed English units', () => {
    const s = buildDailyReportFa({
      dayKey: '2026-07-20',
      displayName: 'ari',
      totalCalories: 1950,
      targetLow: 1800,
      targetHigh: 2000,
      proteinG: 120,
      proteinTarget: 150,
      mealsLogged: 3,
      weightToday: 94.2,
      avg7: 94.4,
      workoutTitle: 'Full Body A',
      sleepHours: 7,
      steps: 8200,
      hideCalories: false,
    });
    expect(s).toContain('1950 cal');
    expect(s).toContain('میانگین 7 روزه');
  });

  it('hide-calories mode omits calorie numbers (ED safeguard)', () => {
    const s = buildDailyReportFa({
      dayKey: '2026-07-20',
      displayName: 'ari',
      totalCalories: 1950,
      targetLow: 1800,
      targetHigh: 2000,
      proteinG: null,
      proteinTarget: null,
      mealsLogged: 3,
      weightToday: null,
      avg7: null,
      workoutTitle: null,
      sleepHours: null,
      steps: null,
      hideCalories: true,
    });
    expect(s).not.toContain('1950');
  });

  it('weekly report includes pattern hypotheses with evidence counts', () => {
    const s = buildWeeklyReportFa({
      weekEndDayKey: '2026-07-19',
      weights: flatWeights(21),
      intakeDays: intake(6, 2000),
      targetLow: 1800,
      targetHigh: 2000,
      workoutsCompleted: 3,
      workoutsPlanned: 4,
      sleepAvg: 6.9,
      checkinsSent: 9,
      checkinsAnswered: 7,
      hideCalories: false,
      findings: [
        {
          key: 'k',
          antecedent: 'sleep_under_6h',
          outcome: 'evening_craving',
          evidenceCount: 9,
          counterexampleCount: 3,
          baseRate: 0.2,
          antecedentRate: 0.75,
          confidence: 'medium',
          notCausal: true,
          sensitive: false,
          requiredConsent: null,
          nextValidationQuestion: 'x',
        },
      ],
    });
    expect(s).toContain('شواهد: 9');
    expect(s).toContain('فرضیه');
  });

  it('coach report includes cannabis section ONLY when summary passed', () => {
    const base = {
      weekEndDayKey: '2026-07-19',
      weights: flatWeights(21),
      intakeDays: intake(6, 2000),
      targetLow: 1800,
      targetHigh: 2000,
      workoutsCompleted: 3,
      workoutsPlanned: 4,
      sleepAvg: 7,
      checkinsSent: 9,
      checkinsAnswered: 7,
      hideCalories: false,
      findings: [],
      displayName: 'ari',
      plateauStatus: 'likely_true_plateau',
      plateauConfidence: 'medium',
      activeExperiments: ['protein breakfast'],
      safetyFlags: [],
      coachNotes: ['keep protein ≥ 130g'],
    };
    expect(buildCoachReportMd({ ...base, cannabisSummary: null })).not.toContain('Cannabis');
    expect(buildCoachReportMd({ ...base, cannabisSummary: '3 events, no intake shift' })).toContain(
      'Cannabis-aware summary',
    );
  });
});

describe('self-modification agent', () => {
  it('drafts schedule proposal for dead slots and flags quiet-hour violations as critical code bugs', () => {
    const p = draftProposals({
      checkinsSentBySlot: { evening: { sent: 6, answered: 1 }, morning: { sent: 5, answered: 4 } },
      avgAnswerRate: 0.5,
      burdenComplaints: 0,
      patternCorrectionsRejected: 0,
      llmFailures: 0,
      llmTokens: 10_000,
      capHits: 0,
      quietHourViolations: 1,
    });
    expect(p.some((x) => x.category === 'schedule')).toBe(true);
    expect(p.some((x) => x.category === 'code' && x.risk === 'high')).toBe(true);
  });

  it('guardrails: cap can never exceed 20; code/prompt never auto-applied', () => {
    expect(validateApplication('message_budget', { dailyCap: 25 }).ok).toBe(false);
    expect(validateApplication('message_budget', { dailyCap: 15 }).ok).toBe(true);
    expect(validateApplication('code', {}).ok).toBe(false);
    expect(validateApplication('prompt', {}).ok).toBe(false);
  });
});
