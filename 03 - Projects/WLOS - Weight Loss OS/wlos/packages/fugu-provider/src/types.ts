/**
 * BrainProvider — the ONLY doorway from WLOS to any external LLM.
 * Long-term memory NEVER lives here; providers receive a minimal,
 * task-specific, redacted context packet and return structured output.
 */

export interface ContextPacket {
  purpose: string; // logged; e.g. "weekly_synthesis"
  dataCategories: string[]; // logged; e.g. ["weights","meals"] — no raw text logged
  content: string; // redacted, compact, task-specific
}

export interface ReasoningRequest {
  task: 'reason' | 'critique' | 'summarize';
  system: string;
  packet: ContextPacket;
  model?: 'default' | 'deep';
  effort?: 'high' | 'xhigh';
  maxTokens?: number;
  /** JSON schema description for the expected output (validated with zod by caller) */
  jsonMode?: boolean;
}

export interface ReasoningResult {
  ok: true;
  text: string;
  provider: string;
  model: string;
  tokensIn: number;
  tokensOut: number;
  latencyMs: number;
}

export interface ReasoningFailure {
  ok: false;
  provider: string;
  reason: 'disabled' | 'no_key' | 'timeout' | 'http_error' | 'circuit_open' | 'budget_exceeded' | 'invalid_response';
  detail?: string;
}

export type ReasoningOutcome = ReasoningResult | ReasoningFailure;

export interface ProviderStatus {
  name: string;
  healthy: boolean;
  circuitOpen: boolean;
  detail?: string;
}

export interface BrainProvider {
  readonly name: string;
  reason(req: ReasoningRequest): Promise<ReasoningOutcome>;
  healthCheck(): Promise<ProviderStatus>;
}

/** Token budget guard — shared across providers, persisted by caller. */
export interface TokenBudget {
  monthlyLimit: number;
  usedThisMonth(): Promise<number>;
  record(tokens: number): Promise<void>;
}

export class InMemoryTokenBudget implements TokenBudget {
  private used = 0;
  constructor(public monthlyLimit: number) {}
  async usedThisMonth(): Promise<number> {
    return this.used;
  }
  async record(tokens: number): Promise<void> {
    this.used += tokens;
  }
}
