/**
 * Double-progression overload: fill the rep range, then add load.
 * Gradual by design; deload = volume cut, not abandonment.
 */

export interface SetResult {
  reps: number;
  weightKg: number;
  rir: number | null;
}

export interface ProgressionAdvice {
  action: 'add_weight' | 'add_reps' | 'hold' | 'reduce_load' | 'deload';
  detailFa: string;
}

export function nextProgression(
  repRange: { min: number; max: number },
  lastSets: SetResult[],
  opts: { incrementKg?: number; deloadTriggered?: boolean } = {},
): ProgressionAdvice {
  if (opts.deloadTriggered) {
    return { action: 'deload', detailFa: 'این هفته deload: همون وزن، ۶۰٪ ست‌ها. ریکاوری هم بخشی از برنامه‌ست.' };
  }
  if (lastSets.length === 0) {
    return { action: 'hold', detailFa: 'اولین جلسه با وزنی که ۲ تکرار توش ذخیره داری شروع کن (RIR 2).' };
  }
  const inc = opts.incrementKg ?? 2.5;
  const allAtTop = lastSets.every((s) => s.reps >= repRange.max);
  const anyBelowMin = lastSets.some((s) => s.reps < repRange.min);
  const groundToZero = lastSets.some((s) => s.rir !== null && s.rir <= 0);

  if (anyBelowMin && groundToZero) {
    return { action: 'reduce_load', detailFa: `وزن رو کمی کم کن (~${inc}kg) تا دوباره تو رنج تکرار بیفتی.` };
  }
  if (allAtTop) {
    return { action: 'add_weight', detailFa: `همهٔ ست‌ها سقف رنج بودن — جلسهٔ بعد +${inc}kg.` };
  }
  return { action: 'add_reps', detailFa: 'وزن ثابت؛ سعی کن مجموع تکرارها رو ۱–۲ تا بیشتر کنی.' };
}
