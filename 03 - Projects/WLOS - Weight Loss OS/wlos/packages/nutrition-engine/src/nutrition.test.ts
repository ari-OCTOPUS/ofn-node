import { describe, expect, it } from 'vitest';
import {
  bmi,
  bmrMifflin,
  calorieTargetRange,
  fiberTargetGrams,
  proteinTargetGrams,
  tdeeEstimate,
} from './calculations.js';
import { observedTdee, rollingAverage, slopeKgPerWeek, trendSummary, type DayValue } from './trends.js';
import { parseMeal, parseWeight } from './meal-parser.js';

describe('BMR / TDEE / targets', () => {
  const p = { sex: 'male' as const, ageYears: 35, heightCm: 178, weightKg: 95 };

  it('Mifflin-St Jeor male reference value', () => {
    // 10*95 + 6.25*178 - 5*35 + 5 = 950 + 1112.5 - 175 + 5 = 1892.5
    expect(bmrMifflin(p)).toBe(1893);
  });

  it('Mifflin-St Jeor female reference value', () => {
    expect(bmrMifflin({ sex: 'female', ageYears: 30, heightCm: 165, weightKg: 70 })).toBe(
      Math.round(10 * 70 + 6.25 * 165 - 5 * 30 - 161),
    );
  });

  it('TDEE returns an honest ±10% range', () => {
    const t = tdeeEstimate(p, 'moderate');
    expect(t.mid).toBe(Math.round(1893 * 1.55));
    expect(t.low).toBeLessThan(t.mid);
    expect(t.high).toBeGreaterThan(t.mid);
  });

  it('calorie target is a range with a bounded deficit', () => {
    const t = calorieTargetRange(p, 2900);
    expect(t.deficitPerDay).toBeLessThanOrEqual(500);
    expect(t.deficitPerDay).toBeGreaterThanOrEqual(250);
    expect(t.low).toBeLessThan(t.high);
  });

  it('ED safeguard: never below floor even with aggressive request', () => {
    const small = { sex: 'female' as const, ageYears: 40, heightCm: 155, weightKg: 52 };
    const t = calorieTargetRange(small, 1350, { desiredDeficit: 800 });
    expect(t.low).toBeGreaterThanOrEqual(1200);
    expect(t.floorApplied).toBe(true);
  });

  it('protein anchored to goal weight when provided', () => {
    expect(proteinTargetGrams(95, 85).target).toBe(Math.round(85 * 1.8));
  });

  it('fiber by sex', () => {
    expect(fiberTargetGrams('male').low).toBe(30);
  });

  it('bmi', () => {
    expect(bmi(95, 178)).toBeCloseTo(30, 0);
  });
});

function makeSeries(startDay: string, values: Array<number | null>): DayValue[] {
  const out: DayValue[] = [];
  const t0 = new Date(startDay + 'T00:00:00Z').getTime();
  values.forEach((v, i) => {
    if (v !== null) out.push({ dayKey: new Date(t0 + i * 86_400_000).toISOString().slice(0, 10), value: v });
  });
  return out;
}

describe('trends', () => {
  it('7-day rolling average handles missing days', () => {
    const s = makeSeries('2026-06-01', [95, null, 94.8, 94.6, null, 94.4, 94.2, 94.0]);
    const points = rollingAverage(s, 7, 3);
    const last = points[points.length - 1]!;
    expect(last.nPoints).toBe(5); // 94.8..94.0 within trailing 7 days
    expect(last.avg).toBeCloseTo((94.8 + 94.6 + 94.4 + 94.2 + 94.0) / 5, 2);
  });

  it('slope detects ~0.35 kg/week loss', () => {
    const vals = Array.from({ length: 28 }, (_, i) => 95 - (0.05 * i)); // 0.35/week
    const s = makeSeries('2026-06-01', vals);
    expect(slopeKgPerWeek(s)!).toBeCloseTo(-0.35, 2);
  });

  it('classifies a 3-year-plateau-like flat series as stable', () => {
    const vals = Array.from({ length: 30 }, (_, i) => 94.5 + Math.sin(i / 3) * 0.4); // noise, no trend
    const t = trendSummary(makeSeries('2026-06-01', vals));
    expect(t.classification).toBe('stable');
  });

  it('refuses classification with insufficient data', () => {
    const t = trendSummary(makeSeries('2026-06-01', [95, 94.9, 94.8]));
    expect(t.classification).toBe('insufficient_data');
  });

  it('observedTdee gates on intake completeness', () => {
    const weights = makeSeries('2026-06-01', Array.from({ length: 28 }, (_, i) => 95 - 0.05 * i));
    const fewIntake = makeSeries('2026-06-01', Array.from({ length: 10 }, () => 2200));
    expect(observedTdee(weights, fewIntake)).toBeNull();

    const fullIntake = makeSeries('2026-06-01', Array.from({ length: 26 }, () => 2200));
    const est = observedTdee(weights, fullIntake)!;
    // losing 0.05 kg/day at 2200 intake → TDEE ≈ 2200 + 385 = 2585
    expect(est.estimate).toBeGreaterThan(2450);
    expect(est.estimate).toBeLessThan(2720);
    expect(est.low).toBeLessThan(est.estimate);
    expect(est.caveat.length).toBeGreaterThan(10);
  });
});

describe('meal parser (fa/en, digits, macros)', () => {
  it('parses Persian meal with Persian digits', () => {
    const m = parseMeal('ناهار: ۸۰۰ کالری')!;
    expect(m.calories).toBe(800);
    expect(m.name).toContain('ناهار');
  });

  it('parses mixed English', () => {
    const m = parseMeal('chicken rice sabzi, 650 cal')!;
    expect(m.calories).toBe(650);
    expect(m.name).toBe('chicken rice sabzi');
  });

  it('parses bare trailing number', () => {
    const m = parseMeal('yogurt 150')!;
    expect(m.calories).toBe(150);
    expect(m.name).toBe('yogurt');
  });

  it('parses //snack prefix', () => {
    const m = parseMeal('//snack: protein bar 220')!;
    expect(m.calories).toBe(220);
    expect(m.name.toLowerCase()).toContain('protein bar');
  });

  it('parses شام with no calorie word', () => {
    const m = parseMeal('شام ماهی و سبزیجات ۵۵۰')!;
    expect(m.calories).toBe(550);
  });

  it('extracts optional macros', () => {
    const m = parseMeal('kabab koobideh 700 p45 c30 f35')!;
    expect(m.proteinG).toBe(45);
    expect(m.carbsG).toBe(30);
    expect(m.fatG).toBe(35);
    expect(m.calories).toBe(700);
  });

  it('flags suspicious calories and rejects absurd ones', () => {
    expect(parseMeal('feast 3500')!.suspiciouslyHigh).toBe(true);
    expect(parseMeal('feast 9000')).toBeNull();
  });

  it('rejects text without numbers', () => {
    expect(parseMeal('ناهار خوردم')).toBeNull();
  });

  it('parses weight incl. Persian decimal', () => {
    expect(parseWeight('۹۴٫۵')).toBe(94.5);
    expect(parseWeight('/weight 101.2')).toBe(101.2);
    expect(parseWeight('7')).toBeNull();
  });
});
