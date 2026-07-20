import { observedTdee, trendSummary, type DayValue } from '@wlos/nutrition-engine';
import type { PlateauStatus } from '@wlos/shared';

/**
 * Plateau Investigation Agent — deterministic core (spec §6/§8 protocol).
 * Does NOT assume a true metabolic plateau. Does NOT cut calories as a first
 * step — ordered next-steps start with measurement and behavior, always.
 */

export interface PlateauInputs {
  weights: DayValue[]; // daily morning weights (sparse ok)
  dailyIntake: DayValue[]; // logged kcal totals per day
  intakeLoggingCompleteness: number; // 0..1 over the window
  weekendWeekdayIntakeGapKcal: number | null; // weekend avg − weekday avg
  stepsTrend: 'declining' | 'stable' | 'rising' | 'unknown';
  sleepAvgHours: number | null;
  recentTrainingChange: boolean; // new program / big soreness → water retention
  recentHighSodiumOrTravel: boolean;
  medicationChange: boolean;
  medicalSymptoms: boolean; // fatigue/cold intolerance/etc. reported
}

export interface PlateauReport {
  status: PlateauStatus;
  confidence: 'low' | 'medium' | 'high';
  evidence: string[];
  competingExplanations: string[];
  nextBestMeasurement: string;
  smallestSafeExperiment: string;
  reviewInDays: number;
  observedTdeeEstimate: ReturnType<typeof observedTdee>;
}

export function investigatePlateau(i: PlateauInputs): PlateauReport {
  const t = trendSummary(i.weights);
  const evidence: string[] = [];
  const competing: string[] = [];

  // 1) data sufficiency gate: 14 days minimum, 28–42 preferred
  if (t.nDays < 10 || t.spanDays < 14) {
    return {
      status: 'data_insufficient',
      confidence: 'high',
      evidence: [`only ${t.nDays} weigh-ins across ${t.spanDays} days`],
      competingExplanations: ['cannot distinguish anything yet'],
      nextBestMeasurement: 'وزن صبح ناشتا، حداقل ۵ روز در هفته، برای ۱۴ تا ۲۸ روز',
      smallestSafeExperiment: 'فقط ثبت — هیچ تغییری در رژیم لازم نیست',
      reviewInDays: 14,
      observedTdeeEstimate: null,
    };
  }

  evidence.push(
    `${t.nDays} weigh-ins over ${t.spanDays} days; slope ${t.slopeKgPerWeek ?? '?'} kg/wk (${t.classification}); σ=${t.stdDev}`,
  );

  // 2) medical-first routing
  if (i.medicalSymptoms || i.medicationChange) {
    return {
      status: 'medical_review_recommended',
      confidence: 'medium',
      evidence: [...evidence, i.medicationChange ? 'medication change reported' : 'symptoms reported'],
      competingExplanations: ['medication effect', 'endocrine condition', 'other medical factors'],
      nextBestMeasurement: 'چکاپ با GP — این بخش از حیطهٔ WLOS خارجه',
      smallestSafeExperiment: 'هیچ کسری کالری جدیدی تا بعد از بررسی پزشکی',
      reviewInDays: 21,
      observedTdeeEstimate: null,
    };
  }

  // 3) actually losing? then there is no plateau
  if (t.classification === 'losing') {
    return {
      status: 'unconfirmed',
      confidence: 'medium',
      evidence: [...evidence, 'trend is already downward'],
      competingExplanations: ['perceived plateau vs. slow real progress'],
      nextBestMeasurement: 'ادامهٔ همین ثبت؛ مقایسهٔ میانگین‌های 7 روزه، نه روز به روز',
      smallestSafeExperiment: 'هیچ تغییری — روند فعلی داره کار می‌کنه',
      reviewInDays: 14,
      observedTdeeEstimate: observedTdee(i.weights, i.dailyIntake),
    };
  }

  // 4) measurement/adherence layer BEFORE any metabolic conclusion
  if (i.intakeLoggingCompleteness < 0.7) {
    competing.push(`intake logged only ${(i.intakeLoggingCompleteness * 100).toFixed(0)}% of days`);
  }
  if (i.weekendWeekdayIntakeGapKcal !== null && i.weekendWeekdayIntakeGapKcal > 400) {
    competing.push(`weekend intake ≈ +${Math.round(i.weekendWeekdayIntakeGapKcal)} kcal vs weekdays`);
  }
  if (i.stepsTrend === 'declining') competing.push('NEAT/steps declining');
  if (i.sleepAvgHours !== null && i.sleepAvgHours < 6.5) competing.push('short sleep (hunger/adherence pressure)');

  if (competing.length > 0) {
    return {
      status: 'likely_adherence_or_measurement_issue',
      confidence: competing.length >= 2 ? 'medium' : 'low',
      evidence,
      competingExplanations: competing,
      nextBestMeasurement:
        'دو هفته ثبت کامل‌تر: نوشیدنی‌ها، روغن، سس، تست‌کردن‌ها و آخر هفته‌ها — بدون تغییر رژیم',
      smallestSafeExperiment:
        'اول دقت اندازه‌گیری، بعد ساختار وعده‌ها، بعد قدم‌ها — کاهش کالری آخرین گزینه‌ست',
      reviewInDays: 14,
      observedTdeeEstimate: observedTdee(i.weights, i.dailyIntake),
    };
  }

  // 5) water masking
  if (i.recentTrainingChange || i.recentHighSodiumOrTravel) {
    return {
      status: 'likely_water_weight_masking',
      confidence: 'medium',
      evidence: [...evidence, i.recentTrainingChange ? 'new training stimulus' : 'sodium/travel spike'],
      competingExplanations: ['inflammation/glycogen water retention masking fat loss'],
      nextBestMeasurement: 'ادامهٔ وزن روزانه ۱۰ تا ۱۴ روز دیگه؛ دور کمر هفته‌ای یک‌بار',
      smallestSafeExperiment: 'هیچ تغییری — صبر اندازه‌گیری‌شده',
      reviewInDays: 12,
      observedTdeeEstimate: observedTdee(i.weights, i.dailyIntake),
    };
  }

  // 6) true plateau — with clean data and stable trend
  const est = observedTdee(i.weights, i.dailyIntake);
  return {
    status: 'likely_true_plateau',
    confidence: t.spanDays >= 28 && i.intakeLoggingCompleteness >= 0.85 ? 'high' : 'medium',
    evidence: [
      ...evidence,
      `intake completeness ${(i.intakeLoggingCompleteness * 100).toFixed(0)}%`,
      est ? `observed TDEE ≈ ${est.low}–${est.high} kcal (${est.quality})` : 'observed TDEE not computable',
    ],
    competingExplanations: ['adaptation to lower body weight', 'true energy balance at current intake'],
    nextBestMeasurement: 'ادامهٔ ثبت فعلی؛ بازبینی پس از یک آزمایش کنترل‌شده',
    smallestSafeExperiment:
      'یک تغییر در هفته: اول +۱۵۰۰ قدم روزانه یا پروتئین صبحانه؛ کاهش کالری فقط اگر این‌ها جواب نداد (حداکثر −200)',
    reviewInDays: 14,
    observedTdeeEstimate: est,
  };
}
