import { triageInbound, type SafetyVerdict } from './triage.js';
import { guardOutbound, type GuardViolation } from './content-guard.js';

/**
 * Type-enforced safety gate — the acceptance criterion "no agent can bypass
 * the Safety Agent" is enforced structurally: the ONLY way to construct a
 * SafetyClearance is through clearOutbound(), and the outbox refuses to send
 * without one. The brand symbol is not exported.
 */

const BRAND: unique symbol = Symbol('SafetyClearance');

export interface SafetyClearance {
  readonly [BRAND]: true;
  readonly text: string; // possibly rewritten (blocked → replaced)
  readonly violations: GuardViolation[];
  readonly blocked: boolean;
  readonly issuedAt: Date;
}

export interface ClearanceOptions {
  calorieFloor?: number;
  /** When blocked, replace with this fallback instead of refusing entirely. */
  fallbackText?: string;
}

const BLOCKING: ReadonlySet<GuardViolation['code']> = new Set([
  'below_calorie_floor',
  'starvation_language',
  'purge_language',
  'medication_advice',
  'cannabis_instruction',
]);

export function clearOutbound(text: string, opts: ClearanceOptions = {}): SafetyClearance {
  const violations = guardOutbound(text, { calorieFloor: opts.calorieFloor });
  const hasBlocking = violations.some((v) => BLOCKING.has(v.code));
  const finalText = hasBlocking
    ? opts.fallbackText ??
      'این پیشنهاد از فیلتر ایمنی WLOS رد نشد و ارسال نشد. (جزئیات در safety log ثبت شد.)'
    : text;
  return {
    [BRAND]: true,
    text: finalText,
    violations,
    blocked: hasBlocking,
    issuedAt: new Date(),
  } as SafetyClearance;
}

export function isClearance(x: unknown): x is SafetyClearance {
  return typeof x === 'object' && x !== null && (x as Record<symbol, unknown>)[BRAND] === true;
}

export { triageInbound };
export type { SafetyVerdict };
