import { normalizeDigits, normalizeFa } from '@wlos/shared';

/**
 * Simple meal parser — name + total calories ONLY (product decision: no photos,
 * no computer vision, no food database requirement).
 *
 * Accepts:
 *   "ناهار: ۸۰۰ کالری"
 *   "chicken rice sabzi, 650 cal"
 *   "شام ماهی و سبزیجات ۵۵۰"
 *   "yogurt 150"
 *   "//snack: protein bar 220"
 *   "kabab 700 p45 c30 f35"        (optional user-provided macros)
 */

export interface ParsedMeal {
  name: string;
  calories: number;
  proteinG?: number;
  carbsG?: number;
  fatG?: number;
  suspiciouslyHigh: boolean; // > 3000 kcal single entry → confirm
}

const CAL_WORDS = /(?:k?cal(?:ories?)?|کالری|کیلوکالری|کالر)/i;
const MACRO_RE = /\b([pcf])\s?(\d{1,3})\b/gi;
const MACRO_FA: Array<[RegExp, keyof Pick<ParsedMeal, 'proteinG' | 'carbsG' | 'fatG'>]> = [
  [/(?:پروتئین|protein)\s*[:=]?\s*(\d{1,3})/i, 'proteinG'],
  [/(?:کربوهیدرات|کربو|carbs?)\s*[:=]?\s*(\d{1,3})/i, 'carbsG'],
  [/(?:چربی|fat)\s*[:=]?\s*(\d{1,3})/i, 'fatG'],
];

export function parseMeal(raw: string): ParsedMeal | null {
  let text = normalizeDigits(normalizeFa(raw))
    .replace(/^\/{1,2}\s*/, '') // "//snack: ..." or "/meal ..."
    .replace(/^(meal|snack|breakfast|lunch|dinner)\s*[:،,-]?\s*/i, (m) => m) // keep meal words as part of name
    .trim();
  if (!text) return null;

  // Extract optional macros first so their numbers don't collide with calories
  const macros: Partial<ParsedMeal> = {};
  text = text.replace(MACRO_RE, (_, letter: string, num: string) => {
    const n = Number(num);
    if (letter.toLowerCase() === 'p') macros.proteinG = n;
    if (letter.toLowerCase() === 'c') macros.carbsG = n;
    if (letter.toLowerCase() === 'f') macros.fatG = n;
    return ' ';
  });
  for (const [re, key] of MACRO_FA) {
    const m = re.exec(text);
    if (m) {
      macros[key] = Number(m[1]);
      text = text.replace(re, ' ');
    }
  }

  // Calories: prefer a number adjacent to a calorie word; else the last standalone number 20..5000
  let calories: number | null = null;
  const withWord =
    new RegExp(`(\\d{2,4})\\s*${CAL_WORDS.source}`, 'i').exec(text) ??
    new RegExp(`${CAL_WORDS.source}\\s*[:=]?\\s*(\\d{2,4})`, 'i').exec(text);
  if (withWord) {
    calories = Number(withWord[1]);
    text = text.replace(withWord[0], ' ');
  } else {
    const nums = [...text.matchAll(/(?<![\d.])(\d{2,4})(?![\d.])/g)];
    const last = nums[nums.length - 1];
    if (last) {
      calories = Number(last[1]);
      text = text.slice(0, last.index) + text.slice(last.index! + last[0].length);
    }
  }
  if (calories === null || !Number.isFinite(calories)) return null;
  if (calories < 10 || calories > 5000) return null;

  const name = text
    .replace(CAL_WORDS, ' ')
    .replace(/[:،,;=-]+\s*$/g, '')
    .replace(/^[:،,;=-]+/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (!name) return null;

  return {
    name,
    calories,
    ...macros,
    suspiciouslyHigh: calories > 3000,
  };
}

/** Parse a weight message: "94.5", "۹۴٫۵", "وزن 94.5 kg". Range-guarded 30–350 kg. */
export function parseWeight(raw: string): number | null {
  const text = normalizeDigits(normalizeFa(raw)).replace(/^\/weight\s*/i, '');
  const m = /(\d{2,3}(?:\.\d{1,2})?)/.exec(text);
  if (!m) return null;
  const v = Number(m[1]);
  if (v < 30 || v > 350) return null;
  return v;
}
