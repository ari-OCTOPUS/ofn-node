import type { BrainProvider, ProviderStatus, ReasoningOutcome, ReasoningRequest } from './types.js';

/**
 * Ordered fallback chain: fugu → (optional others) → deterministic null.
 * Basic coaching NEVER depends on an ok result — callers must branch on
 * outcome.ok and fall back to rule-based responses (acceptance criterion:
 * "Fugu failure does not stop basic coaching").
 */
export class FallbackChain implements BrainProvider {
  readonly name = 'chain';

  constructor(private providers: BrainProvider[]) {}

  async reason(req: ReasoningRequest): Promise<ReasoningOutcome> {
    let last: ReasoningOutcome = { ok: false, provider: this.name, reason: 'disabled', detail: 'no providers' };
    for (const p of this.providers) {
      last = await p.reason(req);
      if (last.ok) return last;
    }
    return last;
  }

  async healthCheck(): Promise<ProviderStatus> {
    const checks = await Promise.all(this.providers.map((p) => p.healthCheck()));
    return {
      name: this.name,
      healthy: checks.some((c) => c.healthy),
      circuitOpen: checks.every((c) => c.circuitOpen),
      detail: checks.map((c) => `${c.name}:${c.healthy ? 'ok' : 'down'}`).join(','),
    };
  }
}
