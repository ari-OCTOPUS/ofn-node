import { describe, expect, it } from 'vitest';
import { CircuitBreaker } from './circuit.js';
import { redactIdentifiers } from './redact.js';
import { FailingProvider, MockProvider } from './mock.js';
import { FallbackChain } from './chain.js';
import { FuguProvider } from './fugu.js';
import { InMemoryTokenBudget, type ReasoningRequest } from './types.js';

const req: ReasoningRequest = {
  task: 'reason',
  system: 'You are the WLOS weekly synthesizer.',
  packet: { purpose: 'weekly_synthesis', dataCategories: ['weights', 'meals'], content: 'compact packet' },
};

describe('redaction', () => {
  it('strips emails, phones, ids, handles, and names', () => {
    const out = redactIdentifiers(
      'ari (master.thepainting@gmail.com, +61 412 345 678, tg 123456789, @ari_dev) weighs 94.5',
      ['ari'],
    );
    expect(out).not.toContain('gmail');
    expect(out).not.toContain('412');
    expect(out).not.toContain('123456789');
    expect(out).not.toContain('@ari_dev');
    expect(out).toContain('94.5'); // health values survive
  });
});

describe('circuit breaker', () => {
  it('opens after threshold, half-opens after cooldown, closes on success', () => {
    let t = 0;
    const cb = new CircuitBreaker({ failureThreshold: 3, cooldownMs: 1000, now: () => t });
    expect(cb.canRequest()).toBe(true);
    cb.onFailure();
    cb.onFailure();
    cb.onFailure();
    expect(cb.getState()).toBe('open');
    expect(cb.canRequest()).toBe(false);
    t = 1500;
    expect(cb.canRequest()).toBe(true); // half-open probe
    cb.onSuccess();
    expect(cb.getState()).toBe('closed');
  });
});

describe('fallback chain', () => {
  it('falls back to next provider when first fails', async () => {
    const chain = new FallbackChain([new FailingProvider(), new MockProvider(() => 'from-mock')]);
    const out = await chain.reason(req);
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.text).toBe('from-mock');
  });

  it('returns last failure when all fail — callers must use rule-based path', async () => {
    const chain = new FallbackChain([new FailingProvider()]);
    const out = await chain.reason(req);
    expect(out.ok).toBe(false);
  });
});

describe('FuguProvider (mocked fetch)', () => {
  const okFetch: typeof fetch = async () =>
    new Response(
      JSON.stringify({
        choices: [{ message: { content: '{"summary":"ok"}' } }],
        usage: { prompt_tokens: 120, completion_tokens: 80 },
      }),
      { status: 200, headers: { 'content-type': 'application/json' } },
    );

  it('returns text + records token budget', async () => {
    const budget = new InMemoryTokenBudget(1000);
    const p = new FuguProvider({ apiKey: 'k', budget, fetchImpl: okFetch });
    const out = await p.reason(req);
    expect(out.ok).toBe(true);
    expect(await budget.usedThisMonth()).toBe(200);
  });

  it('fails cleanly without an API key', async () => {
    const p = new FuguProvider({ apiKey: '' });
    const out = await p.reason(req);
    expect(out).toMatchObject({ ok: false, reason: 'no_key' });
  });

  it('stops when budget exceeded', async () => {
    const budget = new InMemoryTokenBudget(100);
    await budget.record(150);
    const p = new FuguProvider({ apiKey: 'k', budget, fetchImpl: okFetch });
    const out = await p.reason(req);
    expect(out).toMatchObject({ ok: false, reason: 'budget_exceeded' });
  });

  it('retries retryable HTTP errors then succeeds', async () => {
    let calls = 0;
    const flaky: typeof fetch = async () => {
      calls++;
      if (calls === 1) return new Response('busy', { status: 429 });
      return okFetch('', {} as RequestInit);
    };
    const p = new FuguProvider({ apiKey: 'k', fetchImpl: flaky, maxRetries: 2 });
    const out = await p.reason(req);
    expect(out.ok).toBe(true);
    expect(calls).toBe(2);
  });

  it('reports http_error on persistent 500s and logs the call', async () => {
    const logs: unknown[] = [];
    const bad: typeof fetch = async () => new Response('boom', { status: 500 });
    const p = new FuguProvider({ apiKey: 'k', fetchImpl: bad, maxRetries: 1, onCall: (l) => logs.push(l) });
    const out = await p.reason(req);
    expect(out).toMatchObject({ ok: false, reason: 'http_error' });
    expect(logs.length).toBe(1);
    expect((logs[0] as { purpose: string }).purpose).toBe('weekly_synthesis');
  });
});
