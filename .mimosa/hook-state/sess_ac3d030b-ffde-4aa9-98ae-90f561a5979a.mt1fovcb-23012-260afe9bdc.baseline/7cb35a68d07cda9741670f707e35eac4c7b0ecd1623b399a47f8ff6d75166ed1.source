import { describe, expect, it } from 'vitest';
import { mulberry32 } from '@wlos/shared';
import { QUESTION_BANK } from './data/question-bank.js';
import { eligibleQuestions, selectQuestion, skipCooldownDays } from './selection.js';
import { candidatesFor } from './comb.js';
import type { SelectionState } from './question-types.js';

const baseState: SelectionState = {
  todayKey: '2026-07-20',
  context: 'checkin',
  consents: { core_health: true },
  history: [],
  activeContraindications: [],
  answeredIds: new Set(),
};

describe('question bank integrity', () => {
  it('has at least 250 questions (spec acceptance)', () => {
    expect(QUESTION_BANK.length).toBeGreaterThanOrEqual(250);
  });

  it('ids are unique and match DOMAIN-### format', () => {
    const ids = QUESTION_BANK.map((q) => q.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) expect(id).toMatch(/^[A-M]-\d{3}$/);
  });

  it('covers all 13 domains with reasonable depth', () => {
    const byDomain = new Map<string, number>();
    for (const q of QUESTION_BANK) byDomain.set(q.domain, (byDomain.get(q.domain) ?? 0) + 1);
    expect(byDomain.size).toBe(13);
    for (const [domain, count] of byDomain) {
      expect(count, `domain ${domain}`).toBeGreaterThanOrEqual(10);
    }
  });

  it('cannabis questions are ALL consent-gated and preview-safe', () => {
    for (const q of QUESTION_BANK.filter((x) => x.domain === 'cannabis')) {
      expect(q.consentScope).toBe('cannabis');
      expect(q.neverInNotificationPreview).toBe(true);
      expect(q.sensitivity).toBe('high');
    }
  });

  it('emotional_context questions require psychology consent', () => {
    for (const q of QUESTION_BANK.filter((x) => x.domain === 'emotional_context')) {
      expect(q.consentScope).toBe('psychology');
    }
  });

  it('every question has Persian text, English reference, and valid tags', () => {
    for (const q of QUESTION_BANK) {
      expect(q.fa.length, q.id).toBeGreaterThan(5);
      expect(q.en.length, q.id).toBeGreaterThan(5);
      expect(q.burden).toBeGreaterThanOrEqual(1);
      expect(q.burden).toBeLessThanOrEqual(5);
      expect(q.infoGain).toBeGreaterThanOrEqual(1);
      expect(q.infoGain).toBeLessThanOrEqual(5);
      expect(q.allowedContexts.length).toBeGreaterThan(0);
      if (q.responseType === 'choice') expect(q.choicesFa?.length ?? 0).toBeGreaterThanOrEqual(2);
    }
  });

  it('prerequisites reference existing ids', () => {
    const ids = new Set(QUESTION_BANK.map((q) => q.id));
    for (const q of QUESTION_BANK) {
      for (const p of q.prerequisites) expect(ids.has(p), `${q.id} → ${p}`).toBe(true);
    }
  });
});

describe('selection rules', () => {
  it('never selects consent-gated questions without consent', () => {
    const eligible = eligibleQuestions(QUESTION_BANK, baseState);
    expect(eligible.every((q) => q.consentScope === null || q.consentScope === 'core_health')).toBe(true);
  });

  it('selects cannabis questions only with consent', () => {
    const withConsent = eligibleQuestions(QUESTION_BANK, {
      ...baseState,
      consents: { core_health: true, cannabis: true },
    });
    expect(withConsent.some((q) => q.domain === 'cannabis')).toBe(true);
  });

  it('returns exactly one question (or none)', () => {
    const r = selectQuestion(QUESTION_BANK, baseState, mulberry32(1));
    expect(r === null || typeof r.question.id === 'string').toBe(true);
  });

  it('honors cooldown', () => {
    const q = QUESTION_BANK.find((x) => x.id === 'C-001')!;
    const state: SelectionState = {
      ...baseState,
      history: [{ questionId: q.id, askedDayKey: '2026-07-20', answered: true }],
    };
    expect(eligibleQuestions([q], state)).toHaveLength(0); // cooldown 1 day, asked today
    const tomorrow = { ...state, todayKey: '2026-07-21' };
    expect(eligibleQuestions([q], tomorrow)).toHaveLength(1);
  });

  it('honors prerequisites', () => {
    const q = QUESTION_BANK.find((x) => x.id === 'C-002')!;
    expect(eligibleQuestions([q], { ...baseState, context: 'chat' })).toHaveLength(0);
    expect(
      eligibleQuestions([q], { ...baseState, context: 'chat', answeredIds: new Set(['C-001']) }),
    ).toHaveLength(1);
  });

  it('honors permanent refusal ("don\'t ask again")', () => {
    const state: SelectionState = {
      ...baseState,
      history: [{ questionId: 'E-001', askedDayKey: '2026-01-01', answered: false, refusedPermanently: true }],
    };
    expect(eligibleQuestions(QUESTION_BANK, state).some((q) => q.id === 'E-001')).toBe(false);
  });

  it('honors contraindications (crisis mode blocks nearly everything)', () => {
    const state: SelectionState = { ...baseState, activeContraindications: ['crisis_mode'] };
    const eligible = eligibleQuestions(QUESTION_BANK, state);
    expect(eligible.every((q) => !q.contraindications.includes('crisis_mode'))).toBe(true);
  });

  it('topic hint biases domain choice', () => {
    const r = selectQuestion(
      QUESTION_BANK,
      { ...baseState, topicHint: 'morning_awareness' },
      mulberry32(3),
    );
    expect(r).not.toBeNull();
  });

  it('skip semantics', () => {
    const q = QUESTION_BANK.find((x) => x.id === 'B-001')!;
    expect(skipCooldownDays('never', q)).toBe(Number.MAX_SAFE_INTEGER);
    expect(skipCooldownDays('not_now', q)).toBe(1);
    expect(skipCooldownDays('skip', q)).toBeGreaterThanOrEqual(2);
  });
});

describe('COM-B intervention mapping', () => {
  it('opportunity-limited barrier gets friction-reduction candidates', () => {
    const c = candidatesFor({ capability: 'sufficient', opportunity: 'limited', motivation: 'sufficient' });
    expect(c.some((i) => i.bctCode === '12.5')).toBe(true);
    expect(c.every((i) => i.targets.includes('opportunity'))).toBe(true);
  });

  it('unknown-profile falls back to low-burden menu', () => {
    const c = candidatesFor({ capability: 'unknown', opportunity: 'unknown', motivation: 'unknown' });
    expect(c.every((i) => i.burden === 'low')).toBe(true);
  });
});
