/**
 * Question/prompt utility scoring — spec section 5 formula, transparent rules.
 * Contextual-bandit-ready: swap `score()` behind the same interface later.
 * NO uncontrolled RL in production — weights are static config.
 */

export interface UtilityInputs {
  informationGain: number; // 0..1 — how much this reduces state uncertainty
  actionability: number; // 0..1 — can we DO something with the answer today
  contextRelevance: number; // 0..1 — matches current window (e.g. pre-evening risk)
  responseLikelihood: number; // 0..1 — historical response rate for this slot/type
  burdenScore: number; // 0..1 — cognitive/emotional cost of answering
  repetitionPenalty: number; // 0..1 — recently asked or similar asked
  privacyExposureRisk: number; // 0..1 — sensitivity in current channel/context
  interruptionCost: number; // 0..1 — work block, driving, gym set, etc.
}

export interface UtilityConfig {
  threshold: number; // send only above this
}

export const DEFAULT_UTILITY_CONFIG: UtilityConfig = { threshold: 0.15 };

export function utilityScore(u: UtilityInputs): number {
  const positive =
    clamp01(u.informationGain) *
    clamp01(u.actionability) *
    clamp01(u.contextRelevance) *
    clamp01(u.responseLikelihood);
  const cost =
    clamp01(u.burdenScore) * 0.5 +
    clamp01(u.repetitionPenalty) * 0.3 +
    clamp01(u.privacyExposureRisk) * 0.4 +
    clamp01(u.interruptionCost) * 0.4;
  return round3(positive - cost * 0.3);
}

export function shouldSend(u: UtilityInputs, cfg: UtilityConfig = DEFAULT_UTILITY_CONFIG): boolean {
  return utilityScore(u) >= cfg.threshold;
}

const clamp01 = (n: number) => Math.min(1, Math.max(0, n));
const round3 = (n: number) => Math.round(n * 1000) / 1000;
