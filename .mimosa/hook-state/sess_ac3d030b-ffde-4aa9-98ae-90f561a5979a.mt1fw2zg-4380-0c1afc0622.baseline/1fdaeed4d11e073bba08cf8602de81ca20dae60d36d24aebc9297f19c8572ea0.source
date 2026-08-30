import { addDaysToKey, type Rng } from '@wlos/shared';
import type { Question, SelectionState } from './question-types.js';

/**
 * Question selection — spec §5 rules:
 *  - exactly ONE question per message (selection returns 0 or 1)
 *  - consent-gated domains never selected without consent
 *  - cooldowns, prerequisites, contraindications, permanent refusals honored
 *  - progressive profiling outside onboarding
 *  - burden-aware: prefers high info-gain / low burden
 */

const TOPIC_DOMAIN_BIAS: Record<string, string[]> = {
  morning_awareness: ['sleep_recovery', 'self_efficacy', 'motivation_values'],
  midday_check: ['hunger_cravings', 'environment'],
  evening_risk: ['hunger_cravings', 'emotional_context', 'environment'],
  reflection: ['dieting_beliefs', 'relapse_recovery', 'weight_history', 'social_cultural'],
  risk_window: ['hunger_cravings', 'emotional_context'],
};

export interface SelectionResult {
  question: Question;
  score: number;
}

export function eligibleQuestions(bank: Question[], state: SelectionState): Question[] {
  return bank.filter((q) => {
    // permanent refusal
    if (state.history.some((h) => h.questionId === q.id && h.refusedPermanently)) return false;
    // consent gate
    if (q.consentScope && q.consentScope !== 'core_health' && state.consents[q.consentScope] !== true) return false;
    // context gate
    if (!q.allowedContexts.includes(state.context)) return false;
    // contraindications
    if (q.contraindications.some((c) => state.activeContraindications.includes(c))) return false;
    // prerequisites
    if (!q.prerequisites.every((p) => state.answeredIds.has(p))) return false;
    // cooldown (also: an answered question is not re-asked unless cooldown passed → revalidation)
    const lastAsk = state.history
      .filter((h) => h.questionId === q.id)
      .sort((a, b) => (a.askedDayKey < b.askedDayKey ? 1 : -1))[0];
    if (lastAsk) {
      const eligibleFrom = addDaysToKey(lastAsk.askedDayKey, q.cooldownDays);
      if (state.todayKey < eligibleFrom) return false;
    }
    return true;
  });
}

export function selectQuestion(bank: Question[], state: SelectionState, rng: Rng): SelectionResult | null {
  const eligible = eligibleQuestions(bank, state);
  if (eligible.length === 0) return null;

  const bias = state.topicHint ? TOPIC_DOMAIN_BIAS[state.topicHint] ?? [] : [];
  const scored = eligible.map((q) => {
    const domainBoost = bias.includes(q.domain) ? 1.5 : 1;
    const novelty = state.answeredIds.has(q.id) ? 0.4 : 1; // revalidation is lower priority
    const base = (q.infoGain / (q.burden + 1)) * domainBoost * novelty;
    // small seeded jitter → same-day determinism, day-to-day variety
    return { question: q, score: base * (0.85 + rng() * 0.3) };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored[0] ?? null;
}

/** apply a "skip / not now / never" reply to history semantics */
export type SkipKind = 'skip' | 'not_now' | 'never';

export function skipCooldownDays(kind: SkipKind, q: Question): number {
  if (kind === 'never') return Number.MAX_SAFE_INTEGER;
  if (kind === 'not_now') return 1;
  return Math.max(2, Math.ceil(q.cooldownDays / 2));
}
