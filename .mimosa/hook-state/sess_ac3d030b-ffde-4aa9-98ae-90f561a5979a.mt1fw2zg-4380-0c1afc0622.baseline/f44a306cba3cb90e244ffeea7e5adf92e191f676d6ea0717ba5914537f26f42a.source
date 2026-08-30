import { CircuitBreaker } from './circuit.js';
import type {
  BrainProvider,
  ProviderStatus,
  ReasoningOutcome,
  ReasoningRequest,
  TokenBudget,
} from './types.js';

/**
 * Sakana Fugu via the official OpenAI-compatible API.
 * Verified July 2026: base https://api.sakana.ai/v1, models `fugu` and
 * `fugu-ultra`, Bearer auth (console.sakana.ai/get-started).
 *
 * Never receives raw history. Never owns memory. Chain-of-thought is not
 * requested and not stored — only final structured text.
 */

export interface FuguOptions {
  apiKey: string;
  baseUrl?: string;
  modelDefault?: string; // fugu
  modelDeep?: string; // fugu-ultra
  timeoutMs?: number;
  maxRetries?: number;
  budget?: TokenBudget;
  fetchImpl?: typeof fetch; // injectable for tests
  onCall?: (log: FuguCallLog) => void; // llm_calls persistence hook
}

export interface FuguCallLog {
  provider: string;
  model: string;
  purpose: string;
  dataCategories: string[];
  ok: boolean;
  tokensIn: number;
  tokensOut: number;
  latencyMs: number;
  failureReason?: string;
}

const RETRYABLE = new Set([408, 409, 425, 429, 500, 502, 503, 504]);

export class FuguProvider implements BrainProvider {
  readonly name = 'fugu';
  private circuit = new CircuitBreaker({ failureThreshold: 3, cooldownMs: 60_000 });
  private fetchImpl: typeof fetch;

  constructor(private opts: FuguOptions) {
    this.fetchImpl = opts.fetchImpl ?? fetch;
  }

  async reason(req: ReasoningRequest): Promise<ReasoningOutcome> {
    if (!this.opts.apiKey) return { ok: false, provider: this.name, reason: 'no_key' };
    if (!this.circuit.canRequest()) return { ok: false, provider: this.name, reason: 'circuit_open' };

    if (this.opts.budget) {
      const used = await this.opts.budget.usedThisMonth();
      if (used >= this.opts.budget.monthlyLimit) {
        return { ok: false, provider: this.name, reason: 'budget_exceeded' };
      }
    }

    const model =
      req.model === 'deep' ? this.opts.modelDeep ?? 'fugu-ultra' : this.opts.modelDefault ?? 'fugu';
    const base = (this.opts.baseUrl ?? 'https://api.sakana.ai/v1').replace(/\/$/, '');
    const body: Record<string, unknown> = {
      model,
      messages: [
        { role: 'system', content: req.system },
        { role: 'user', content: req.packet.content },
      ],
      max_tokens: req.maxTokens ?? 1500,
    };
    if (req.effort) body.reasoning_effort = req.effort;
    if (req.jsonMode) body.response_format = { type: 'json_object' };

    const maxRetries = this.opts.maxRetries ?? 2;
    const started = Date.now();

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.opts.timeoutMs ?? 45_000);
      try {
        const res = await this.fetchImpl(`${base}/chat/completions`, {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            authorization: `Bearer ${this.opts.apiKey}`,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        clearTimeout(timer);

        if (!res.ok) {
          if (RETRYABLE.has(res.status) && attempt < maxRetries) {
            await sleep(backoffMs(attempt));
            continue;
          }
          this.circuit.onFailure();
          this.log(req, model, false, 0, 0, Date.now() - started, `http_${res.status}`);
          return { ok: false, provider: this.name, reason: 'http_error', detail: `HTTP ${res.status}` };
        }

        const json = (await res.json()) as {
          choices?: Array<{ message?: { content?: string } }>;
          usage?: { prompt_tokens?: number; completion_tokens?: number };
        };
        const text = json.choices?.[0]?.message?.content;
        if (typeof text !== 'string' || text.length === 0) {
          this.circuit.onFailure();
          this.log(req, model, false, 0, 0, Date.now() - started, 'invalid_response');
          return { ok: false, provider: this.name, reason: 'invalid_response' };
        }

        const tokensIn = json.usage?.prompt_tokens ?? 0;
        const tokensOut = json.usage?.completion_tokens ?? 0;
        await this.opts.budget?.record(tokensIn + tokensOut);
        this.circuit.onSuccess();
        const latencyMs = Date.now() - started;
        this.log(req, model, true, tokensIn, tokensOut, latencyMs);
        return { ok: true, text, provider: this.name, model, tokensIn, tokensOut, latencyMs };
      } catch (err) {
        clearTimeout(timer);
        if (attempt < maxRetries) {
          await sleep(backoffMs(attempt));
          continue;
        }
        this.circuit.onFailure();
        const reason = controller.signal.aborted ? 'timeout' : 'http_error';
        this.log(req, model, false, 0, 0, Date.now() - started, reason);
        return { ok: false, provider: this.name, reason, detail: String(err).slice(0, 200) };
      }
    }
    return { ok: false, provider: this.name, reason: 'http_error', detail: 'retries_exhausted' };
  }

  async healthCheck(): Promise<ProviderStatus> {
    return {
      name: this.name,
      healthy: Boolean(this.opts.apiKey) && this.circuit.getState() !== 'open',
      circuitOpen: this.circuit.getState() === 'open',
    };
  }

  private log(
    req: ReasoningRequest,
    model: string,
    ok: boolean,
    tokensIn: number,
    tokensOut: number,
    latencyMs: number,
    failureReason?: string,
  ): void {
    this.opts.onCall?.({
      provider: this.name,
      model,
      purpose: req.packet.purpose,
      dataCategories: req.packet.dataCategories,
      ok,
      tokensIn,
      tokensOut,
      latencyMs,
      failureReason,
    });
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const backoffMs = (attempt: number) => Math.min(8000, 500 * 2 ** attempt) + Math.floor(Math.random() * 250);
