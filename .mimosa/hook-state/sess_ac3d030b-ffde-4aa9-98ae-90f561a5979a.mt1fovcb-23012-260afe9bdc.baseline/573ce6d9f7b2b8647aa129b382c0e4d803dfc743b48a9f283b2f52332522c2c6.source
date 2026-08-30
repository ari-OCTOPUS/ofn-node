/**
 * Training readiness gate — deterministic safety layer for workout selection.
 * Non-negotiable: never recommend heavy training under intoxication, severe
 * dizziness, impaired coordination, or unusual symptoms.
 */

export interface ReadinessInputs {
  sleepHoursLastNight: number | null;
  energy0to10: number | null;
  soreness0to10: number | null;
  stress0to10: number | null;
  /** consented cannabis state: true when user reported recent use / impairment */
  reportedImpairment: boolean;
  reportedDizzinessOrSymptoms: boolean;
  daysSinceLastDeload: number | null;
  consecutiveHardSessions: number;
}

export type SessionIntensity = 'heavy' | 'moderate' | 'light' | 'walk_or_mobility' | 'rest';

export interface ReadinessVerdict {
  maxIntensity: SessionIntensity;
  reasons: string[];
  deloadSuggested: boolean;
}

export function assessReadiness(r: ReadinessInputs): ReadinessVerdict {
  const reasons: string[] = [];

  // hard safety gates first
  if (r.reportedDizzinessOrSymptoms) {
    return {
      maxIntensity: 'rest',
      reasons: ['reported symptoms — no training until reviewed; medical check if persistent'],
      deloadSuggested: false,
    };
  }
  if (r.reportedImpairment) {
    return {
      maxIntensity: 'walk_or_mobility',
      reasons: ['impairment reported — no loaded/heavy training right now (safety rule)'],
      deloadSuggested: false,
    };
  }

  let score = 0;
  if (r.sleepHoursLastNight !== null) {
    if (r.sleepHoursLastNight < 5) {
      score -= 2;
      reasons.push('under 5h sleep');
    } else if (r.sleepHoursLastNight < 6.5) {
      score -= 1;
      reasons.push('short sleep');
    }
  }
  if (r.energy0to10 !== null && r.energy0to10 <= 3) {
    score -= 1;
    reasons.push('low energy');
  }
  if (r.soreness0to10 !== null && r.soreness0to10 >= 7) {
    score -= 1;
    reasons.push('high soreness');
  }
  if (r.stress0to10 !== null && r.stress0to10 >= 8) {
    score -= 1;
    reasons.push('very high stress');
  }

  const deloadSuggested =
    (r.daysSinceLastDeload !== null && r.daysSinceLastDeload > 42) || r.consecutiveHardSessions >= 6;
  if (deloadSuggested) reasons.push('deload window reached');

  const maxIntensity: SessionIntensity =
    score <= -3 ? 'walk_or_mobility' : score === -2 ? 'light' : score === -1 ? 'moderate' : 'heavy';
  if (reasons.length === 0) reasons.push('all clear');
  return { maxIntensity, reasons, deloadSuggested };
}
