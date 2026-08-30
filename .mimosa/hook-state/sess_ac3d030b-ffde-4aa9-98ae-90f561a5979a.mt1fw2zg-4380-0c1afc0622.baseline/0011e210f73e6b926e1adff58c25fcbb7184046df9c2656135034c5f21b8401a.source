import type { SessionIntensity } from './readiness.js';

/** Workout templates: gym / home / travel / minimum-dose, scaled by readiness. */

export interface ExercisePrescription {
  nameEn: string;
  nameFa: string;
  sets: number;
  reps: string; // "6-8", "10-12", "30s"
  rirTarget: number; // reps in reserve
}

export interface WorkoutTemplate {
  key: string;
  titleFa: string;
  kind: 'gym' | 'home' | 'travel' | 'minimum_dose' | 'walk';
  estMinutes: number;
  exercises: ExercisePrescription[];
}

export const TEMPLATES: WorkoutTemplate[] = [
  {
    key: 'gym_full_a',
    titleFa: 'باشگاه — Full Body A',
    kind: 'gym',
    estMinutes: 55,
    exercises: [
      { nameEn: 'Goblet Squat', nameFa: 'اسکوات گابلت', sets: 3, reps: '8-10', rirTarget: 2 },
      { nameEn: 'Bench Press', nameFa: 'پرس سینه', sets: 3, reps: '6-8', rirTarget: 2 },
      { nameEn: 'Seated Row', nameFa: 'زیربغل قایقی', sets: 3, reps: '10-12', rirTarget: 2 },
      { nameEn: 'Romanian Deadlift', nameFa: 'ددلیفت رومانیایی', sets: 3, reps: '8-10', rirTarget: 2 },
      { nameEn: 'Plank', nameFa: 'پلانک', sets: 3, reps: '30-45s', rirTarget: 0 },
    ],
  },
  {
    key: 'gym_full_b',
    titleFa: 'باشگاه — Full Body B',
    kind: 'gym',
    estMinutes: 55,
    exercises: [
      { nameEn: 'Leg Press', nameFa: 'پرس پا', sets: 3, reps: '10-12', rirTarget: 2 },
      { nameEn: 'Overhead Press', nameFa: 'پرس سرشانه', sets: 3, reps: '6-8', rirTarget: 2 },
      { nameEn: 'Lat Pulldown', nameFa: 'زیربغل سیم‌کش', sets: 3, reps: '10-12', rirTarget: 2 },
      { nameEn: 'Leg Curl', nameFa: 'پشت پا خوابیده', sets: 3, reps: '10-12', rirTarget: 2 },
      { nameEn: 'Farmer Carry', nameFa: 'حمل دمبل (farmer)', sets: 3, reps: '30m', rirTarget: 1 },
    ],
  },
  {
    key: 'home_basic',
    titleFa: 'خانه — بدون وسیله',
    kind: 'home',
    estMinutes: 30,
    exercises: [
      { nameEn: 'Bodyweight Squat', nameFa: 'اسکوات با وزن بدن', sets: 3, reps: '12-15', rirTarget: 2 },
      { nameEn: 'Push-up', nameFa: 'شنا', sets: 3, reps: '8-12', rirTarget: 2 },
      { nameEn: 'Hip Hinge / Good Morning', nameFa: 'هیپ هینج', sets: 3, reps: '12-15', rirTarget: 2 },
      { nameEn: 'Backpack Row', nameFa: 'رو با کوله', sets: 3, reps: '10-12', rirTarget: 2 },
      { nameEn: 'Dead Bug', nameFa: 'ددباگ', sets: 2, reps: '10/side', rirTarget: 1 },
    ],
  },
  {
    key: 'travel_hotel',
    titleFa: 'سفر — اتاق هتل',
    kind: 'travel',
    estMinutes: 20,
    exercises: [
      { nameEn: 'Split Squat', nameFa: 'اسپلیت اسکوات', sets: 2, reps: '10/leg', rirTarget: 2 },
      { nameEn: 'Push-up', nameFa: 'شنا', sets: 2, reps: 'AMRAP-2', rirTarget: 2 },
      { nameEn: 'Glute Bridge', nameFa: 'پل باسن', sets: 2, reps: '15', rirTarget: 1 },
      { nameEn: 'Side Plank', nameFa: 'پلانک پهلو', sets: 2, reps: '20-30s', rirTarget: 0 },
    ],
  },
  {
    key: 'minimum_10',
    titleFa: 'حداقلی — ۱۰ دقیقه (فقط شروع کن)',
    kind: 'minimum_dose',
    estMinutes: 10,
    exercises: [
      { nameEn: 'Bodyweight Squat', nameFa: 'اسکوات', sets: 2, reps: '10', rirTarget: 3 },
      { nameEn: 'Push-up (knee ok)', nameFa: 'شنا (زانو اوکیه)', sets: 2, reps: '6-10', rirTarget: 3 },
      { nameEn: 'Brisk March', nameFa: 'درجا یا پیاده‌روی تند', sets: 1, reps: '3min', rirTarget: 3 },
    ],
  },
  {
    key: 'walk_20',
    titleFa: 'پیاده‌روی ۲۰ دقیقه',
    kind: 'walk',
    estMinutes: 20,
    exercises: [{ nameEn: 'Walk', nameFa: 'پیاده‌روی', sets: 1, reps: '20min', rirTarget: 5 }],
  },
];

/**
 * Pick a session for today given readiness + context.
 * Reduce volume before abandoning the whole session (spec §13).
 */
export function pickSession(
  maxIntensity: SessionIntensity,
  context: { location: 'gym' | 'home' | 'travel'; lastGymKey?: string },
): WorkoutTemplate {
  if (maxIntensity === 'rest') return TEMPLATES.find((t) => t.key === 'walk_20')!; // gentle default shown as optional
  if (maxIntensity === 'walk_or_mobility') return TEMPLATES.find((t) => t.key === 'walk_20')!;
  if (maxIntensity === 'light') return TEMPLATES.find((t) => t.key === 'minimum_10')!;

  if (context.location === 'travel') return TEMPLATES.find((t) => t.key === 'travel_hotel')!;
  if (context.location === 'home') return TEMPLATES.find((t) => t.key === 'home_basic')!;
  // alternate A/B
  return context.lastGymKey === 'gym_full_a'
    ? TEMPLATES.find((t) => t.key === 'gym_full_b')!
    : TEMPLATES.find((t) => t.key === 'gym_full_a')!;
}

export function formatSessionFa(t: WorkoutTemplate): string {
  const lines = t.exercises.map(
    (e) => `• ${e.nameFa} (${e.nameEn}) — ${e.sets}×${e.reps}, RIR ${e.rirTarget}`,
  );
  return `${t.titleFa} — حدود ${t.estMinutes} دقیقه\n${lines.join('\n')}\n\nدرد مفصلی ≠ فشار عادی تمرین؛ اگر درد تیز داشتی همون‌جا قطع کن.`;
}
