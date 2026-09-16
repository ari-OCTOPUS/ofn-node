/**
 * Deterministic nutrition math. No LLM involvement — ever.
 * All outputs are RANGES with stated uncertainty, not false precision.
 */

export type Sex = 'male' | 'female';

export interface BodyProfile {
  sex: Sex;
  ageYears: number;
  heightCm: number;
  weightKg: number;
}

/** Mifflin-St Jeor. Screening estimate only (±~10%). */
export function bmrMifflin(p: BodyProfile): number {
  const base = 10 * p.weightKg + 6.25 * p.heightCm - 5 * p.ageYears;
  return Math.round(p.sex === 'male' ? base + 5 : base - 161);
}

export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';

export const ACTIVITY_FACTORS: Record<ActivityLevel, number> = {
  sedentary: 1.2,
  light: 1.375,
  moderate: 1.55,
  active: 1.725,
  very_active: 1.9,
};

export function tdeeEstimate(p: BodyProfile, activity: ActivityLevel): { mid: number; low: number; high: number } {
  const mid = Math.round(bmrMifflin(p) * ACTIVITY_FACTORS[activity]);
  // Formula TDEE is honest to ±10%
  return { mid, low: Math.round(mid * 0.9), high: Math.round(mid * 1.1) };
}

export function bmi(weightKg: number, heightCm: number): number {
  const m = heightCm / 100;
  return Math.round((weightKg / (m * m)) * 10) / 10;
}

/** kcal per kg of body-mass change (mixed tissue). An approximation, flagged as such. */
export const KCAL_PER_KG = 7700;

/**
 * Eating-disorder safeguards, non-negotiable:
 *  - absolute calorie floors (1200 F / 1500 M unsupervised)
 *  - deficit never exceeds 25% of TDEE mid
 *  - target expressed as a RANGE
 */
export interface CalorieTarget {
  low: number;
  high: number;
  deficitPerDay: number;
  floorApplied: boolean;
  rationale: string;
}

export function calorieTargetRange(
  p: BodyProfile,
  tdeeMid: number,
  opts: { desiredDeficit?: number } = {},
): CalorieTarget {
  const floor = p.sex === 'male' ? 1500 : 1200;
  const requested = opts.desiredDeficit ?? 400; // default moderate deficit
  const maxDeficit = Math.round(tdeeMid * 0.25);
  const deficit = Math.min(Math.max(requested, 250), Math.min(500, maxDeficit));
  let mid = tdeeMid - deficit;
  let floorApplied = false;
  if (mid < floor) {
    mid = floor;
    floorApplied = true;
  }
  return {
    low: Math.max(floor, mid - 100),
    high: mid + 100,
    deficitPerDay: tdeeMid - mid,
    floorApplied,
    rationale: floorApplied
      ? `Deficit capped by safety floor (${floor} kcal). Rate goal must slow down rather than eat below floor.`
      : `TDEE ~${tdeeMid} − deficit ${deficit} kcal/day ≈ 0.3–0.5 kg/week expected.`,
  };
}

/** Protein target: 1.6–2.2 g/kg of goal (or current) weight. Default anchor 1.8. */
export function proteinTargetGrams(weightKg: number, goalWeightKg?: number): { low: number; high: number; target: number } {
  const anchor = goalWeightKg && goalWeightKg > 30 ? goalWeightKg : weightKg;
  return {
    low: Math.round(anchor * 1.6),
    high: Math.round(anchor * 2.2),
    target: Math.round(anchor * 1.8),
  };
}

export function fiberTargetGrams(sex: Sex): { low: number; high: number } {
  return sex === 'male' ? { low: 30, high: 38 } : { low: 25, high: 32 };
}
