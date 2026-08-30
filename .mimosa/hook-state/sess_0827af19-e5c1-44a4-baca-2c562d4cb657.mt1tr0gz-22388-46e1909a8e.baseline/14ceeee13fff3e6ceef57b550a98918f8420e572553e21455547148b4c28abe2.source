import { describe, expect, it } from 'vitest';
import { triageInbound } from './triage.js';
import { guardOutbound } from './content-guard.js';
import { clearOutbound, isClearance } from './clearance.js';
import { AU_RESOURCES, formatResourcesFa } from './resources.js';

describe('inbound triage (fa/en)', () => {
  it('detects Persian self-harm language as crisis', () => {
    const v = triageInbound('دیگه نمی‌خوام زنده باشم');
    expect(v.level).toBe('crisis');
    expect(v.categories).toContain('self_harm');
  });

  it('detects English suicidal language as crisis', () => {
    expect(triageInbound('I want to kill myself').level).toBe('crisis');
  });

  it('detects chest pain as urgent_medical', () => {
    const v = triageInbound('بعد تمرین درد قفسه سینه داشتم');
    expect(v.level).toBe('urgent_medical');
    expect(v.categories).toContain('chest_pain');
  });

  it('detects purging as eating_disorder / urgent_medical', () => {
    const v = triageInbound("after big meals I've been purging");
    expect(v.categories).toContain('eating_disorder');
    expect(v.level).toBe('urgent_medical');
  });

  it('detects multi-day starvation in Persian', () => {
    const v = triageInbound('سه روزه هیچی نخوردم که وزنم بیاد پایین');
    expect(v.categories).toContain('eating_disorder');
  });

  it('pregnancy is caution, not crisis', () => {
    expect(triageInbound('راستی من باردارم').level).toBe('caution');
  });

  it('normal food talk is none', () => {
    expect(triageInbound('ناهار: قرمه سبزی ۷۰۰ کالری').level).toBe('none');
    expect(triageInbound('امروز خیلی گشنمه و کباب می‌خوام').level).toBe('none');
  });

  it('crisis outranks caution when both present', () => {
    const v = triageInbound('باردارم و دیگه نمی‌خوام زنده باشم');
    expect(v.level).toBe('crisis');
  });
});

describe('outbound content guard', () => {
  it('blocks sub-floor calorie targets', () => {
    const v = guardOutbound('هدف امروزت فقط ۸۰۰ کالری باشه');
    expect(v.some((x) => x.code === 'below_calorie_floor')).toBe(true);
  });

  it('allows sane targets', () => {
    expect(guardOutbound('هدف امروز: 1900 کالری، پروتئین 140 گرم')).toHaveLength(0);
  });

  it('blocks compensatory-exercise framing', () => {
    const v = guardOutbound("you should burn it off with an extra session as punishment");
    expect(v.some((x) => x.code === 'compensatory_exercise')).toBe(true);
  });

  it('blocks shame language in Persian', () => {
    const v = guardOutbound('مشکل تو اینه که اراده نداری');
    expect(v.some((x) => x.code === 'shame_language')).toBe(true);
  });

  it('blocks medication advice', () => {
    const v = guardOutbound('به نظرم داروت رو قطع کن تا وزن کم کنی');
    expect(v.some((x) => x.code === 'medication_advice')).toBe(true);
  });

  it('blocks diagnosis language', () => {
    const v = guardOutbound('You have an eating disorder, clearly.');
    expect(v.some((x) => x.code === 'diagnosis_language')).toBe(true);
  });
});

describe('clearance gate', () => {
  it('replaces blocked text with safe fallback', () => {
    const c = clearOutbound('فقط ۷۰۰ کالری بخور در روز');
    expect(c.blocked).toBe(true);
    expect(c.text).not.toContain('۷۰۰');
    expect(c.text).not.toContain('700');
  });

  it('passes clean text through untouched', () => {
    const msg = 'امروز 1950 cal ثبت شد. عالی پیش میری 👏';
    const c = clearOutbound(msg);
    expect(c.blocked).toBe(false);
    expect(c.text).toBe(msg);
  });

  it('clearance objects are recognizable; plain objects are not', () => {
    expect(isClearance(clearOutbound('سلام'))).toBe(true);
    expect(isClearance({ text: 'سلام', blocked: false })).toBe(false);
  });
});

describe('AU resources', () => {
  it('includes 000 and Lifeline', () => {
    const s = formatResourcesFa();
    expect(s).toContain('000');
    expect(s).toContain('13 11 14');
    expect(AU_RESOURCES.length).toBeGreaterThanOrEqual(6);
  });
});
