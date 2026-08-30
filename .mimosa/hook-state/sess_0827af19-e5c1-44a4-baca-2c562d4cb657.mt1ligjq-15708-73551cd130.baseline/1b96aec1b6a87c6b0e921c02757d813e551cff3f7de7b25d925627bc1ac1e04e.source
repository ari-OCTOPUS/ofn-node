import {
  addDaysToKey,
  chance,
  isInQuietHours,
  mulberry32,
  parseHHMM,
  randInt,
  seedFromString,
  utcAtLocalMinutes,
  type NotificationPrefs,
  type Rng,
} from '@wlos/shared';

/**
 * Daily check-in planner. Randomized but context-aware (JITAI):
 *  - plan generated once per local day (worker at ~00:05 local)
 *  - each slot fires probabilistically with jitter → NOT a fixed clock time
 *  - quiet hours / min gap / daily target respected BY CONSTRUCTION
 *  - every planned instance is RE-EVALUATED just before sending
 *    (shouldStillSend) so stale prompts get cancelled, not delivered
 */

export interface CheckinSlot {
  key: string; // 'morning' | 'midday' | 'pre_evening' | 'evening' | 'extra'
  startHHMM: string;
  endHHMM: string;
  probability: number; // chance this slot fires at all today
  defaultTopic: string; // topic hint for question selection
}

export const DEFAULT_SLOTS: CheckinSlot[] = [
  { key: 'morning', startHHMM: '07:30', endHHMM: '09:00', probability: 0.6, defaultTopic: 'morning_awareness' },
  { key: 'midday', startHHMM: '12:00', endHHMM: '14:00', probability: 0.5, defaultTopic: 'midday_check' },
  { key: 'pre_evening', startHHMM: '17:00', endHHMM: '19:00', probability: 0.7, defaultTopic: 'evening_risk' },
  { key: 'evening', startHHMM: '20:30', endHHMM: '21:30', probability: 0.5, defaultTopic: 'reflection' },
];

export interface PlannedCheckin {
  slotKey: string;
  topic: string;
  fireAtUtc: Date;
  localMinutes: number;
}

export interface DayContext {
  /** windows (minutes-of-day) to avoid, e.g. work meetings or gym */
  exclusions?: Array<{ startMin: number; endMin: number }>;
  /** predicted high-risk eating windows boost extra prompts there */
  riskWindows?: Array<{ startMin: number; endMin: number; weight: number }>;
  maxExtra?: number; // context-driven extras, default 2
}

export function planDay(
  dayKey: string,
  prefs: NotificationPrefs,
  ctx: DayContext = {},
  rngIn?: Rng,
): PlannedCheckin[] {
  if (prefs.paused) return [];
  const rng = rngIn ?? mulberry32(seedFromString(`${dayKey}:${prefs.timezone}`));
  const tz = prefs.timezone;

  const planned: PlannedCheckin[] = [];
  const effectiveMultiplier = Math.max(0.25, Math.min(1, prefs.backoffMultiplier));

  const push = (slotKey: string, topic: string, minute: number): boolean => {
    if (minute < 0 || minute >= 1440) return false; // clock-time semantics
    const fireAtUtc = utcAtLocalMinutes(dayKey, minute, tz);
    if (!prefs.quietHoursSuspended && isInQuietHours(fireAtUtc, tz, prefs.quietHours.start, prefs.quietHours.end)) {
      return false;
    }
    for (const ex of ctx.exclusions ?? []) {
      if (minute >= ex.startMin && minute < ex.endMin) return false;
    }
    for (const p of planned) {
      if (Math.abs(p.localMinutes - minute) < prefs.minGapMinutes) return false;
    }
    planned.push({ slotKey, topic, fireAtUtc, localMinutes: minute });
    return true;
  };

  // 1) base slots, probabilistic, jittered inside their window
  for (const slot of DEFAULT_SLOTS) {
    if (!chance(rng, slot.probability * effectiveMultiplier)) continue;
    const s = parseHHMM(slot.startHHMM);
    const e = parseHHMM(slot.endHHMM);
    // up to 3 attempts to find a legal jittered minute
    for (let attempt = 0; attempt < 3; attempt++) {
      const minute = randInt(rng, s, Math.max(s, e - 1));
      if (push(slot.key, slot.defaultTopic, minute)) break;
    }
  }

  // 2) ensure minimum daily target (fill from unused slots deterministically)
  const min = Math.max(0, Math.round(prefs.targetCheckinsMin * effectiveMultiplier));
  const unused = DEFAULT_SLOTS.filter((s) => !planned.some((p) => p.slotKey === s.key));
  for (const slot of unused) {
    if (planned.length >= min) break;
    const s = parseHHMM(slot.startHHMM);
    const e = parseHHMM(slot.endHHMM);
    for (let attempt = 0; attempt < 4; attempt++) {
      if (push(slot.key, slot.defaultTopic, randInt(rng, s, Math.max(s, e - 1)))) break;
    }
  }

  // 3) context-driven extras in risk windows (bounded)
  const maxExtra = ctx.maxExtra ?? 2;
  let extras = 0;
  for (const rw of [...(ctx.riskWindows ?? [])].sort((a, b) => b.weight - a.weight)) {
    if (extras >= maxExtra) break;
    if (planned.length >= prefs.targetCheckinsMax) break;
    if (!chance(rng, Math.min(0.9, rw.weight) * effectiveMultiplier)) continue;
    for (let attempt = 0; attempt < 3; attempt++) {
      if (push('extra', 'risk_window', randInt(rng, rw.startMin, Math.max(rw.startMin, rw.endMin - 1)))) {
        extras++;
        break;
      }
    }
  }

  // 4) hard invariants: target max, then global sort
  const trimmed = planned
    .sort((a, b) => a.localMinutes - b.localMinutes)
    .slice(0, prefs.targetCheckinsMax);

  // sanity: never plan inside quiet hours even if config is weird
  return trimmed.filter((p) => {
    const q = !prefs.quietHoursSuspended &&
      isInQuietHours(p.fireAtUtc, tz, prefs.quietHours.start, prefs.quietHours.end);
    return !q;
  });
}

export interface ReevaluationContext {
  paused: boolean;
  snoozedUntil: Date | null;
  crisisModeActive: boolean;
  sentToday: number; // ALL bot messages today (cap covers every kind)
  dailyCap: number;
  alreadyAnsweredTopicToday?: boolean;
  now: Date;
  tz: string;
  quietStart: string;
  quietEnd: string;
  quietSuspended: boolean;
}

export type ReevalDecision = { send: true } | { send: false; reason: string };

/** Final gate immediately before sending a planned check-in. */
export function shouldStillSend(ctx: ReevaluationContext): ReevalDecision {
  if (ctx.crisisModeActive) return { send: false, reason: 'crisis_mode' };
  if (ctx.paused) return { send: false, reason: 'paused' };
  if (ctx.snoozedUntil && ctx.now < ctx.snoozedUntil) return { send: false, reason: 'snoozed' };
  if (ctx.sentToday >= ctx.dailyCap) return { send: false, reason: 'daily_cap' };
  if (!ctx.quietSuspended && isInQuietHours(ctx.now, ctx.tz, ctx.quietStart, ctx.quietEnd)) {
    return { send: false, reason: 'quiet_hours' };
  }
  if (ctx.alreadyAnsweredTopicToday) return { send: false, reason: 'topic_already_answered' };
  return { send: true };
}

/** Ignored-prompt backoff: 2 ignored → halve frequency; recovery is gradual. */
export function nextBackoff(current: { multiplier: number; ignoredStreak: number }, event: 'ignored' | 'answered'): {
  multiplier: number;
  ignoredStreak: number;
} {
  if (event === 'answered') {
    return {
      ignoredStreak: 0,
      multiplier: Math.min(1, Math.round((current.multiplier + 0.25) * 100) / 100),
    };
  }
  const streak = current.ignoredStreak + 1;
  return {
    ignoredStreak: streak,
    multiplier: streak >= 2 ? Math.max(0.25, current.multiplier * 0.5) : current.multiplier,
  };
}

export function planNextDayKey(dayKey: string, tz: string): string {
  return addDaysToKey(dayKey, 1, tz);
}
