import type { PatternConfidence } from '@wlos/shared';

/**
 * Pattern Discovery Agent — deterministic association scanning over daily
 * records. Hypotheses with evidence counts, NEVER causal claims.
 * User corrections (rejected) permanently veto a pattern.
 */

export interface DailyRecord {
  dayKey: string;
  sleepHours?: number;
  eveningCraving?: boolean; // any craving log ≥6 after 17:00
  highIntakeDay?: boolean; // > target high
  trainedToday?: boolean;
  stress?: number; // 0..10
  cannabisUse?: boolean; // only present when consented
  mood?: number;
}

export interface AssociationTemplate {
  key: string;
  antecedent: string;
  outcome: string;
  antecedentFn: (d: DailyRecord) => boolean | undefined;
  outcomeFn: (next: DailyRecord, same: DailyRecord) => boolean | undefined;
  lag: 0 | 1; // same-day or next-day
  sensitive: boolean;
  requiredConsent: 'cannabis' | 'psychology' | null;
}

export const ASSOCIATION_TEMPLATES: AssociationTemplate[] = [
  {
    key: 'sleep_under_6h→evening_craving',
    antecedent: 'sleep_under_6h',
    outcome: 'evening_craving',
    antecedentFn: (d) => (d.sleepHours === undefined ? undefined : d.sleepHours < 6),
    outcomeFn: (_n, s) => s.eveningCraving,
    lag: 0,
    sensitive: false,
    requiredConsent: null,
  },
  {
    key: 'high_stress→high_intake',
    antecedent: 'stress_ge_7',
    outcome: 'high_intake_day',
    antecedentFn: (d) => (d.stress === undefined ? undefined : d.stress >= 7),
    outcomeFn: (_n, s) => s.highIntakeDay,
    lag: 0,
    sensitive: true,
    requiredConsent: 'psychology',
  },
  {
    key: 'training→next_day_adherence',
    antecedent: 'trained_today',
    outcome: 'next_day_within_target',
    antecedentFn: (d) => d.trainedToday,
    outcomeFn: (n) => (n.highIntakeDay === undefined ? undefined : !n.highIntakeDay),
    lag: 1,
    sensitive: false,
    requiredConsent: null,
  },
  {
    key: 'cannabis→high_intake',
    antecedent: 'cannabis_use_day',
    outcome: 'high_intake_day',
    antecedentFn: (d) => d.cannabisUse,
    outcomeFn: (_n, s) => s.highIntakeDay,
    lag: 0,
    sensitive: true,
    requiredConsent: 'cannabis',
  },
];

export interface AssociationFinding {
  key: string;
  antecedent: string;
  outcome: string;
  evidenceCount: number; // antecedent & outcome both true
  counterexampleCount: number; // antecedent true, outcome false
  baseRate: number | null; // outcome rate on non-antecedent days
  antecedentRate: number | null; // outcome rate on antecedent days
  confidence: PatternConfidence;
  notCausal: true;
  sensitive: boolean;
  requiredConsent: 'cannabis' | 'psychology' | null;
  nextValidationQuestion: string;
}

export function scanAssociations(
  records: DailyRecord[],
  consents: { cannabis?: boolean; psychology?: boolean },
): AssociationFinding[] {
  const sorted = [...records].sort((a, b) => (a.dayKey < b.dayKey ? -1 : 1));
  const findings: AssociationFinding[] = [];

  for (const tpl of ASSOCIATION_TEMPLATES) {
    if (tpl.requiredConsent && consents[tpl.requiredConsent] !== true) continue;

    let evidence = 0;
    let counter = 0;
    let nonAntecedentOutcome = 0;
    let nonAntecedentTotal = 0;

    for (let idx = 0; idx < sorted.length; idx++) {
      const day = sorted[idx]!;
      const target = tpl.lag === 1 ? sorted[idx + 1] : day;
      if (!target) continue;
      const a = tpl.antecedentFn(day);
      const o = tpl.outcomeFn(target, day);
      if (a === undefined || o === undefined) continue;
      if (a) {
        if (o) evidence++;
        else counter++;
      } else {
        nonAntecedentTotal++;
        if (o) nonAntecedentOutcome++;
      }
    }

    const n = evidence + counter;
    if (n === 0) continue;

    const antecedentRate = n > 0 ? evidence / n : null;
    const baseRate = nonAntecedentTotal > 0 ? nonAntecedentOutcome / nonAntecedentTotal : null;

    // confidence requires volume AND a real lift over base rate
    const lift = antecedentRate !== null && baseRate !== null ? antecedentRate - baseRate : null;
    let confidence: PatternConfidence = 'hypothesis';
    if (n >= 5 && lift !== null && lift > 0.15) confidence = 'low';
    if (n >= 8 && lift !== null && lift > 0.25 && evidence >= 2 * counter) confidence = 'medium';
    if (n >= 14 && lift !== null && lift > 0.3 && evidence >= 3 * counter) confidence = 'high';

    findings.push({
      key: tpl.key,
      antecedent: tpl.antecedent,
      outcome: tpl.outcome,
      evidenceCount: evidence,
      counterexampleCount: counter,
      baseRate: baseRate === null ? null : Math.round(baseRate * 100) / 100,
      antecedentRate: antecedentRate === null ? null : Math.round(antecedentRate * 100) / 100,
      confidence,
      notCausal: true,
      sensitive: tpl.sensitive,
      requiredConsent: tpl.requiredConsent,
      nextValidationQuestion: `آیا این برات آشناست: «${tpl.antecedent} → ${tpl.outcome}»؟ (تایید/رد تو /patterns)`,
    });
  }
  return findings;
}
