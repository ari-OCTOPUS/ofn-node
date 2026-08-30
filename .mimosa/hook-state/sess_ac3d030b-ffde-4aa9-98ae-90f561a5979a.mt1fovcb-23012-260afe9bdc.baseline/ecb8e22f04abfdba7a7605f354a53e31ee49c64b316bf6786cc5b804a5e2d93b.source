import { describe, expect, it } from 'vitest';
import { buildContextPacket } from './packet.js';

const identity = (t: string) => t;

describe('context packet firewall', () => {
  const sections = [
    { category: 'weights' as const, content: '94.5 → 94.1 over 14d' },
    { category: 'cannabis' as const, content: 'events: 3 this week' },
    { category: 'psychology' as const, content: 'all-or-nothing pattern hypothesis' },
  ];

  it('excludes sensitive categories without consent even when task needs them', () => {
    const p = buildContextPacket({
      purpose: 'weekly_synthesis',
      sections,
      needs: ['weights', 'cannabis', 'psychology'],
      consents: { core_health: true }, // no cannabis/psychology consent
      redactor: identity,
    });
    expect(p.dataCategories).toEqual(['weights']);
    expect(p.content).not.toContain('cannabis');
    expect(p.excluded).toContainEqual({ category: 'cannabis', reason: 'no_consent' });
    expect(p.excluded).toContainEqual({ category: 'psychology', reason: 'no_consent' });
  });

  it('excludes categories the task does not need even WITH consent', () => {
    const p = buildContextPacket({
      purpose: 'meal_feedback',
      sections,
      needs: ['weights'],
      consents: { cannabis: true, psychology: true },
      redactor: identity,
    });
    expect(p.dataCategories).toEqual(['weights']);
    expect(p.excluded.filter((e) => e.reason === 'not_needed')).toHaveLength(2);
  });

  it('includes sensitive data only with consent AND need', () => {
    const p = buildContextPacket({
      purpose: 'barrier_analysis',
      sections,
      needs: ['psychology'],
      consents: { psychology: true },
      redactor: identity,
    });
    expect(p.dataCategories).toEqual(['psychology']);
  });

  it('applies the redactor to the final content', () => {
    const p = buildContextPacket({
      purpose: 'x',
      sections: [{ category: 'weights', content: 'contact me@x.com' }],
      needs: ['weights'],
      consents: {},
      redactor: (t) => t.replace(/\S+@\S+/g, '[email]'),
    });
    expect(p.content).toContain('[email]');
  });

  it('enforces size budget', () => {
    const p = buildContextPacket({
      purpose: 'x',
      sections: [
        { category: 'weights', content: 'a'.repeat(100) },
        { category: 'meals', content: 'b'.repeat(100) },
      ],
      needs: ['weights', 'meals'],
      consents: {},
      redactor: identity,
      maxChars: 150,
    });
    expect(p.dataCategories).toEqual(['weights']);
    expect(p.excluded).toContainEqual({ category: 'meals', reason: 'over_budget' });
  });
});
