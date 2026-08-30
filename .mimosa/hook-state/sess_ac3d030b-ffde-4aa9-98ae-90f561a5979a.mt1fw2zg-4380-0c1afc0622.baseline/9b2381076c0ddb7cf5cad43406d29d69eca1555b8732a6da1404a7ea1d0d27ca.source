import { describe, expect, it } from 'vitest';
import { assessReadiness } from './readiness.js';
import { pickSession, TEMPLATES } from './templates.js';
import { nextProgression } from './progression.js';

const baseInputs = {
  sleepHoursLastNight: 7.5,
  energy0to10: 7,
  soreness0to10: 3,
  stress0to10: 4,
  reportedImpairment: false,
  reportedDizzinessOrSymptoms: false,
  daysSinceLastDeload: 20,
  consecutiveHardSessions: 2,
};

describe('readiness safety gates', () => {
  it('symptoms → rest, absolute', () => {
    const v = assessReadiness({ ...baseInputs, reportedDizzinessOrSymptoms: true });
    expect(v.maxIntensity).toBe('rest');
  });

  it('impairment → never loaded training (non-negotiable)', () => {
    const v = assessReadiness({ ...baseInputs, reportedImpairment: true });
    expect(v.maxIntensity).toBe('walk_or_mobility');
  });

  it('good day → heavy allowed', () => {
    expect(assessReadiness(baseInputs).maxIntensity).toBe('heavy');
  });

  it('bad sleep + low energy degrades intensity, not cancels', () => {
    const v = assessReadiness({ ...baseInputs, sleepHoursLastNight: 4.5, energy0to10: 2 });
    expect(['light', 'walk_or_mobility']).toContain(v.maxIntensity);
  });

  it('deload suggested after long block', () => {
    expect(assessReadiness({ ...baseInputs, daysSinceLastDeload: 50 }).deloadSuggested).toBe(true);
  });
});

describe('session picker', () => {
  it('impaired day yields walk regardless of location', () => {
    const t = pickSession('walk_or_mobility', { location: 'gym' });
    expect(t.kind).toBe('walk');
  });

  it('light day yields 10-minute minimum dose (start, not skip)', () => {
    expect(pickSession('light', { location: 'home' }).key).toBe('minimum_10');
  });

  it('gym alternates A/B', () => {
    expect(pickSession('heavy', { location: 'gym', lastGymKey: 'gym_full_a' }).key).toBe('gym_full_b');
    expect(pickSession('heavy', { location: 'gym', lastGymKey: 'gym_full_b' }).key).toBe('gym_full_a');
  });

  it('all templates have exercises and sane durations', () => {
    for (const t of TEMPLATES) {
      expect(t.exercises.length).toBeGreaterThan(0);
      expect(t.estMinutes).toBeGreaterThanOrEqual(10);
    }
  });
});

describe('double progression', () => {
  const range = { min: 6, max: 8 };

  it('adds weight when all sets hit top of range', () => {
    const a = nextProgression(range, [
      { reps: 8, weightKg: 60, rir: 2 },
      { reps: 8, weightKg: 60, rir: 1 },
      { reps: 8, weightKg: 60, rir: 1 },
    ]);
    expect(a.action).toBe('add_weight');
  });

  it('adds reps mid-range', () => {
    const a = nextProgression(range, [
      { reps: 7, weightKg: 60, rir: 2 },
      { reps: 6, weightKg: 60, rir: 2 },
    ]);
    expect(a.action).toBe('add_reps');
  });

  it('reduces load when below range at RIR 0', () => {
    const a = nextProgression(range, [
      { reps: 5, weightKg: 60, rir: 0 },
      { reps: 4, weightKg: 60, rir: 0 },
    ]);
    expect(a.action).toBe('reduce_load');
  });

  it('deload trigger wins', () => {
    expect(nextProgression(range, [], { deloadTriggered: true }).action).toBe('deload');
  });
});
