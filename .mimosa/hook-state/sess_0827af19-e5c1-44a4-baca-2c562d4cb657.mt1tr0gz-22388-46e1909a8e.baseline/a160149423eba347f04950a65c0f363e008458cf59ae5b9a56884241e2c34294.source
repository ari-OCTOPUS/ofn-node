/**
 * Weight-trend analytics over daily series with missing days.
 * Input: sparse map of dayKey → weightKg (morning weight preferred).
 */

export interface DayValue {
  dayKey: string; // YYYY-MM-DD local
  value: number;
}

export interface RollingPoint {
  dayKey: string;
  avg: number | null; // null when not enough points in window
  nPoints: number;
}

/** Rolling average over trailing `windowDays`, requiring `minPoints` present. */
export function rollingAverage(series: DayValue[], windowDays: number, minPoints = 3): RollingPoint[] {
  const sorted = [...series].sort((a, b) => (a.dayKey < b.dayKey ? -1 : 1));
  const byDay = new Map(sorted.map((d) => [d.dayKey, d.value]));
  const days = sorted.map((d) => d.dayKey);
  const out: RollingPoint[] = [];
  for (const day of days) {
    const window: number[] = [];
    const end = new Date(day + 'T00:00:00Z').getTime();
    for (let i = 0; i < windowDays; i++) {
      const k = new Date(end - i * 86_400_000).toISOString().slice(0, 10);
      const v = byDay.get(k);
      if (v !== undefined) window.push(v);
    }
    out.push({
      dayKey: day,
      avg: window.length >= minPoints ? round2(window.reduce((s, v) => s + v, 0) / window.length) : null,
      nPoints: window.length,
    });
  }
  return out;
}

/** Least-squares slope in kg/week over the whole series (uses day index as x). */
export function slopeKgPerWeek(series: DayValue[]): number | null {
  if (series.length < 5) return null;
  const sorted = [...series].sort((a, b) => (a.dayKey < b.dayKey ? -1 : 1));
  const t0 = new Date(sorted[0]!.dayKey + 'T00:00:00Z').getTime();
  const pts = sorted.map((d) => ({
    x: (new Date(d.dayKey + 'T00:00:00Z').getTime() - t0) / 86_400_000,
    y: d.value,
  }));
  const n = pts.length;
  const sx = pts.reduce((s, p) => s + p.x, 0);
  const sy = pts.reduce((s, p) => s + p.y, 0);
  const sxx = pts.reduce((s, p) => s + p.x * p.x, 0);
  const sxy = pts.reduce((s, p) => s + p.x * p.y, 0);
  const denom = n * sxx - sx * sx;
  if (denom === 0) return null;
  const perDay = (n * sxy - sx * sy) / denom;
  return round3(perDay * 7);
}

export interface TrendSummary {
  nDays: number;
  spanDays: number;
  missingness: number; // 0..1 fraction of span without a weigh-in
  mean: number | null;
  stdDev: number | null;
  slopeKgPerWeek: number | null;
  slopePctBodyweightPerWeek: number | null;
  classification: 'insufficient_data' | 'losing' | 'gaining' | 'stable';
}

export function trendSummary(series: DayValue[]): TrendSummary {
  if (series.length === 0) {
    return {
      nDays: 0, spanDays: 0, missingness: 1, mean: null, stdDev: null,
      slopeKgPerWeek: null, slopePctBodyweightPerWeek: null, classification: 'insufficient_data',
    };
  }
  const sorted = [...series].sort((a, b) => (a.dayKey < b.dayKey ? -1 : 1));
  const span =
    Math.round(
      (new Date(sorted[sorted.length - 1]!.dayKey).getTime() - new Date(sorted[0]!.dayKey).getTime()) / 86_400_000,
    ) + 1;
  const mean = sorted.reduce((s, d) => s + d.value, 0) / sorted.length;
  const variance = sorted.reduce((s, d) => s + (d.value - mean) ** 2, 0) / sorted.length;
  const slope = slopeKgPerWeek(sorted);
  const pct = slope !== null && mean > 0 ? round3((slope / mean) * 100) : null;

  let classification: TrendSummary['classification'] = 'insufficient_data';
  if (sorted.length >= 10 && span >= 14 && slope !== null && pct !== null) {
    // ±0.15% bodyweight/week ≈ noise band
    classification = pct <= -0.15 ? 'losing' : pct >= 0.15 ? 'gaining' : 'stable';
  }

  return {
    nDays: sorted.length,
    spanDays: span,
    missingness: round3(1 - sorted.length / Math.max(span, 1)),
    mean: round2(mean),
    stdDev: round2(Math.sqrt(variance)),
    slopeKgPerWeek: slope,
    slopePctBodyweightPerWeek: pct,
    classification,
  };
}

/**
 * Observed TDEE from energy balance: intake − (Δweight × 7700)/days.
 * Gated on data quality; returns null rather than a garbage estimate.
 */
export interface ObservedTdee {
  estimate: number;
  low: number;
  high: number;
  days: number;
  intakeLoggedFraction: number;
  quality: 'low' | 'medium' | 'high';
  caveat: string;
}

export function observedTdee(
  weights: DayValue[],
  dailyIntake: DayValue[], // kcal per day, only days actually logged
): ObservedTdee | null {
  const w = trendSummary(weights);
  if (w.nDays < 10 || w.spanDays < 14 || w.slopeKgPerWeek === null) return null;
  const span = w.spanDays;
  const loggedFraction = dailyIntake.length / span;
  if (loggedFraction < 0.6) return null; // too little intake data to say anything

  const meanIntake = dailyIntake.reduce((s, d) => s + d.value, 0) / dailyIntake.length;
  const kgPerDay = w.slopeKgPerWeek / 7;
  const estimate = Math.round(meanIntake - kgPerDay * 7700);

  // Uncertainty widens with missing intake days and weight noise
  const noise = (w.stdDev ?? 0.5) * 150 + (1 - loggedFraction) * 500 + 150;
  const quality: ObservedTdee['quality'] = loggedFraction > 0.85 && span >= 28 ? 'high' : loggedFraction > 0.7 ? 'medium' : 'low';
  return {
    estimate,
    low: Math.round(estimate - noise),
    high: Math.round(estimate + noise),
    days: span,
    intakeLoggedFraction: round2(loggedFraction),
    quality,
    caveat:
      'Energy-balance estimate; assumes logged intake ≈ true intake. Under-logging inflates this number — treat as a range, not a fact.',
  };
}

const round2 = (n: number) => Math.round(n * 100) / 100;
const round3 = (n: number) => Math.round(n * 1000) / 1000;
