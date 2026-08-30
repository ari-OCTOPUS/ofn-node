/**
 * COM-B barrier classification + Behavior Change Technique candidates.
 * Deterministic mapping table — LLM may PROPOSE a classification, but the
 * intervention menu comes from this vetted table (BCTs are not hallucinated).
 */

export type CombLevel = 'sufficient' | 'limited' | 'unknown';

export interface CombProfile {
  capability: CombLevel; // physical/psychological capability
  opportunity: CombLevel; // physical/social opportunity
  motivation: CombLevel; // reflective/automatic motivation
}

export interface InterventionCandidate {
  bctCode: string; // BCTTv1-style reference
  labelFa: string;
  labelEn: string;
  targets: Array<keyof CombProfile>;
  burden: 'low' | 'medium' | 'high';
}

export const INTERVENTION_MENU: InterventionCandidate[] = [
  { bctCode: '12.5', labelFa: 'آماده‌سازی وسایل از قبل (کاهش friction شروع)', labelEn: 'Prepare equipment in advance', targets: ['opportunity'], burden: 'low' },
  { bctCode: '8.7', labelFa: 'تمرین حداقلی ۱۰ دقیقه‌ای', labelEn: '10-minute minimum-dose workout', targets: ['motivation', 'capability'], burden: 'low' },
  { bctCode: '1.4', labelFa: 'برنامهٔ if-then (implementation intention)', labelEn: 'If-then plan', targets: ['motivation'], burden: 'low' },
  { bctCode: '12.1', labelFa: 'جابه‌جایی تمرین به بازهٔ پرانرژی‌تر روز', labelEn: 'Move training to a higher-energy window', targets: ['motivation'], burden: 'medium' },
  { bctCode: '12.3', labelFa: 'دور کردن غذاهای trigger از دسترس', labelEn: 'Reduce trigger-food accessibility', targets: ['opportunity'], burden: 'medium' },
  { bctCode: '2.3', labelFa: 'ثبت ساده‌تر برای کاهش بار logging', labelEn: 'Simplify self-monitoring', targets: ['capability'], burden: 'low' },
  { bctCode: '3.1', labelFa: 'فعال کردن حمایت یک نفر مشخص', labelEn: 'Enlist specific social support', targets: ['opportunity'], burden: 'medium' },
  { bctCode: '1.2', labelFa: 'هدف رفتاری کوچک به جای هدف عددی وزن', labelEn: 'Behavior goal over scale goal', targets: ['motivation'], burden: 'low' },
  { bctCode: '11.3', labelFa: 'میان‌وعدهٔ برنامه‌ریزی‌شدهٔ عصر', labelEn: 'Planned evening snack', targets: ['motivation'], burden: 'low' },
  { bctCode: '8.3', labelFa: 'پیش‌پُرس کردن اسنک‌ها (pre-portioning)', labelEn: 'Pre-portion snacks', targets: ['opportunity'], burden: 'low' },
];

export function candidatesFor(profile: CombProfile): InterventionCandidate[] {
  const weak = (Object.entries(profile) as Array<[keyof CombProfile, CombLevel]>)
    .filter(([, v]) => v === 'limited')
    .map(([k]) => k);
  if (weak.length === 0) return INTERVENTION_MENU.filter((i) => i.burden === 'low');
  return INTERVENTION_MENU.filter((i) => i.targets.some((t) => weak.includes(t)));
}
