import type { BrainProvider, ProviderStatus, ReasoningOutcome, ReasoningRequest } from './types.js';

/** Deterministic mock for tests and LLM-free development. */
export class MockProvider implements BrainProvider {
  readonly name = 'mock';
  public calls: ReasoningRequest[] = [];

  constructor(private responder?: (req: ReasoningRequest) => string) {}

  async reason(req: ReasoningRequest): Promise<ReasoningOutcome> {
    this.calls.push(req);
    const text =
      this.responder?.(req) ??
      JSON.stringify({ mock: true, purpose: req.packet.purpose, note: 'deterministic mock output' });
    return { ok: true, text, provider: this.name, model: 'mock-1', tokensIn: 10, tokensOut: 10, latencyMs: 1 };
  }

  async healthCheck(): Promise<ProviderStatus> {
    return { name: this.name, healthy: true, circuitOpen: false };
  }
}

/** Provider that always fails — for fallback-chain tests. */
export class FailingProvider implements BrainProvider {
  readonly name = 'failing';
  async reason(): Promise<ReasoningOutcome> {
    return { ok: false, provider: this.name, reason: 'http_error', detail: 'always fails' };
  }
  async healthCheck(): Promise<ProviderStatus> {
    return { name: this.name, healthy: false, circuitOpen: false };
  }
}
