import { normalizeDigits } from '@wlos/shared';

/**
 * Outbound content guard — runs on EVERY coaching message before send,
 * including LLM-generated text. Deterministic, cannot be prompt-injected.
 */

export interface GuardViolation {
  code:
    | 'below_calorie_floor'
    | 'starvation_language'
    | 'compensatory_exercise'
    | 'purge_language'
    | 'rapid_loss_promise'
    | 'detox_language'
    | 'medication_advice'
    | 'diagnosis_language'
    | 'cannabis_instruction'
    | 'shame_language';
  detail: string;
}

const CHECKS: Array<{ code: GuardViolation['code']; re: RegExp }> = [
  { code: 'starvation_language', re: /(نخور(?:ی)? تا|هیچی نخور|گرسنگی بکش|skip (all )?meals|stop eating|fast for \d+ days)/i },
  { code: 'compensatory_exercise', re: /(جبرانش .{0,12}(بدو|ورزش)|burn it off|punish(ing)? (yourself|workout)|به عنوان جریمه)/i },
  { code: 'purge_language', re: /(بالا بیار|استفراغ کن|purge|laxative)/i },
  { code: 'rapid_loss_promise', re: /(\d+\s*(کیلو|kg)\s*(در|per|in)\s*(یک|1)?\s*(هفته|week))/i },
  { code: 'detox_language', re: /(دیتاکس|detox|سم ?زدایی|cleanse diet)/i },
  { code: 'medication_advice', re: /(داروت? رو (قطع|کم|زیاد) کن|stop your medication|change your dose|بدون دکتر دارو)/i },
  { code: 'diagnosis_language', re: /(تو (افسردگی|اختلال|بیماری) داری|you (clearly )?have .{0,24}(disorder|depression|adhd|bulimia|anorexia)|تشخیص من اینه)/i },
  { code: 'cannabis_instruction', re: /(چطور (گل|علف) (بکش|مصرف کن)|how to (smoke|dose|use) (weed|cannabis)|بیشتر مصرف کن)/i },
  { code: 'shame_language', re: /(خجالت بکش|تنبل(ی)? هستی|بی اراده ای|اراده نداری|شکست خورده ای|you'?re (lazy|weak|a failure)|no willpower)/i },
];

/** Calorie floor scan: any explicit daily target below floor is blocked. */
function calorieFloorViolation(text: string, floorKcal: number): GuardViolation | null {
  const t = normalizeDigits(text);
  const patterns = [
    /(?:هدف|target|بخور|فقط|روزانه|daily)[^\d]{0,20}(\d{3,4})\s*(?:کالری|k?cal)/gi,
    /(\d{3,4})\s*(?:کالری|k?cal)[^\d]{0,20}(?:در روز|روزانه|per day|a day|daily)/gi,
  ];
  for (const re of patterns) {
    for (const m of t.matchAll(re)) {
      const kcal = Number(m[1]);
      if (kcal >= 100 && kcal < floorKcal) {
        return { code: 'below_calorie_floor', detail: `mentions daily target ${kcal} < floor ${floorKcal}` };
      }
    }
  }
  return null;
}

export function guardOutbound(text: string, opts: { calorieFloor?: number } = {}): GuardViolation[] {
  const violations: GuardViolation[] = [];
  for (const c of CHECKS) {
    if (c.re.test(text)) violations.push({ code: c.code, detail: c.re.source.slice(0, 50) });
  }
  const floor = calorieFloorViolation(text, opts.calorieFloor ?? 1200);
  if (floor) violations.push(floor);
  return violations;
}
