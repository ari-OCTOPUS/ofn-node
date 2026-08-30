import { describe, expect, it } from 'vitest';
import { DEFAULT_NOTIFICATION_PREFS, isInQuietHours, localMinutesOfDay, mulberry32 } from '@wlos/shared';
import { nextBackoff, planDay, shouldStillSend } from './scheduler.js';
import { shouldSend, utilityScore } from './utility.js';

const prefs = { ...DEFAULT_NOTIFICATION_PREFS };

describe('planDay invariants (1000 seeded days)', () => {
  const days = ['2026-07-20', '2026-10-04', '2026-04-05', '2026-12-25']; // incl. both DST transition days

  it('never plans inside quiet hours, never exceeds max, respects min gap', () => {
    for (const day of days) {
      for (let seed = 0; seed < 250; seed++) {
        const plan = planDay(day, prefs, {}, mulberry32(seed));
        expect(plan.length).toBeLessThanOrEqual(prefs.targetCheckinsMax);
        const minutes = plan.map((p) => p.localMinutes).sort((a, b) => a - b);
        for (let i = 1; i < minutes.length; i++) {
          expect(minutes[i]! - minutes[i - 1]!).toBeGreaterThanOrEqual(prefs.minGapMinutes);
        }
        for (const p of plan) {
          expect(
            isInQuietHours(p.fireAtUtc, prefs.timezone, prefs.quietHours.start, prefs.quietHours.end),
          ).toBe(false);
          // fireAtUtc must round-trip to the same local minutes
          expect(localMinutesOfDay(p.fireAtUtc, prefs.timezone)).toBe(p.localMinutes % 1440);
        }
      }
    }
  });

  it('times actually vary across days (not a fixed clock time)', () => {
    const a = planDay('2026-07-20', prefs, {}, mulberry32(1));
    const b = planDay('2026-07-21', prefs, {}, mulberry32(2));
    const minutesA = a.map((p) => p.localMinutes).join(',');
    const minutesB = b.map((p) => p.localMinutes).join(',');
    expect(minutesA).not.toBe(minutesB);
  });

  it('paused user gets no plan', () => {
    expect(planDay('2026-07-20', { ...prefs, paused: true })).toHaveLength(0);
  });

  it('backoff multiplier reduces planned volume on average', () => {
    let normal = 0;
    let backedOff = 0;
    for (let seed = 0; seed < 200; seed++) {
      normal += planDay('2026-07-20', prefs, {}, mulberry32(seed)).length;
      backedOff += planDay('2026-07-20', { ...prefs, backoffMultiplier: 0.5 }, {}, mulberry32(seed)).length;
    }
    expect(backedOff).toBeLessThan(normal);
  });

  it('risk windows add bounded extras', () => {
    const plan = planDay(
      '2026-07-20',
      prefs,
      { riskWindows: [{ startMin: 21 * 60, endMin: 22 * 60, weight: 0.9 }], maxExtra: 2 },
      mulberry32(7),
    );
    expect(plan.filter((p) => p.slotKey === 'extra').length).toBeLessThanOrEqual(2);
    expect(plan.length).toBeLessThanOrEqual(prefs.targetCheckinsMax);
  });
});

describe('shouldStillSend re-evaluation', () => {
  const base = {
    paused: false,
    snoozedUntil: null as Date | null,
    crisisModeActive: false,
    sentToday: 3,
    dailyCap: 20,
    now: new Date('2026-07-20T02:00:00Z'), // 12:00 Sydney (winter)
    tz: 'Australia/Sydney',
    quietStart: '00:00',
    quietEnd: '07:00',
    quietSuspended: false,
  };

  it('sends in a normal window', () => {
    expect(shouldStillSend(base)).toEqual({ send: true });
  });

  it('blocks at the daily cap — cap counts ALL messages', () => {
    expect(shouldStillSend({ ...base, sentToday: 20 })).toMatchObject({ send: false, reason: 'daily_cap' });
  });

  it('blocks during quiet hours', () => {
    // 03:00 Sydney = 17:00 UTC previous day
    const r = shouldStillSend({ ...base, now: new Date('2026-07-19T17:00:00Z') });
    expect(r).toMatchObject({ send: false, reason: 'quiet_hours' });
  });

  it('crisis mode suppresses ordinary coaching', () => {
    expect(shouldStillSend({ ...base, crisisModeActive: true })).toMatchObject({ send: false, reason: 'crisis_mode' });
  });

  it('snooze respected', () => {
    const r = shouldStillSend({ ...base, snoozedUntil: new Date('2026-07-20T03:00:00Z') });
    expect(r).toMatchObject({ send: false, reason: 'snoozed' });
  });
});

describe('backoff state machine', () => {
  it('halves after 2 consecutive ignores, recovers gradually', () => {
    let s = { multiplier: 1, ignoredStreak: 0 };
    s = nextBackoff(s, 'ignored');
    expect(s.multiplier).toBe(1);
    s = nextBackoff(s, 'ignored');
    expect(s.multiplier).toBe(0.5);
    s = nextBackoff(s, 'answered');
    expect(s.multiplier).toBe(0.75);
    expect(s.ignoredStreak).toBe(0);
    s = nextBackoff(s, 'answered');
    expect(s.multiplier).toBe(1);
  });

  it('never drops below 0.25', () => {
    let s = { multiplier: 1, ignoredStreak: 0 };
    for (let i = 0; i < 10; i++) s = nextBackoff(s, 'ignored');
    expect(s.multiplier).toBeGreaterThanOrEqual(0.25);
  });
});

describe('utility scoring', () => {
  it('high-value contextual question clears threshold', () => {
    const u = utilityScore({
      informationGain: 0.8,
      actionability: 0.9,
      contextRelevance: 0.9,
      responseLikelihood: 0.7,
      burdenScore: 0.2,
      repetitionPenalty: 0,
      privacyExposureRisk: 0.1,
      interruptionCost: 0.1,
    });
    expect(u).toBeGreaterThan(0.15);
  });

  it('sensitive question in a bad moment is suppressed', () => {
    const send = shouldSend({
      informationGain: 0.6,
      actionability: 0.4,
      contextRelevance: 0.3,
      responseLikelihood: 0.3,
      burdenScore: 0.8,
      repetitionPenalty: 0.6,
      privacyExposureRisk: 0.9,
      interruptionCost: 0.7,
    });
    expect(send).toBe(false);
  });

  it('recently-asked question is penalized below a fresh one', () => {
    const base = {
      informationGain: 0.7, actionability: 0.7, contextRelevance: 0.7,
      responseLikelihood: 0.6, burdenScore: 0.3, privacyExposureRisk: 0.1, interruptionCost: 0.1,
    };
    const fresh = utilityScore({ ...base, repetitionPenalty: 0 });
    const repeated = utilityScore({ ...base, repetitionPenalty: 0.9 });
    expect(repeated).toBeLessThan(fresh);
  });
});
