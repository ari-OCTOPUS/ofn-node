export type CircuitState = 'closed' | 'open' | 'half_open';

export interface CircuitOptions {
  failureThreshold: number; // consecutive failures to open
  cooldownMs: number; // how long to stay open
  now?: () => number; // injectable clock for tests
}

export class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failures = 0;
  private openedAt = 0;
  private readonly now: () => number;

  constructor(private opts: CircuitOptions) {
    this.now = opts.now ?? Date.now;
  }

  canRequest(): boolean {
    if (this.state === 'closed') return true;
    if (this.state === 'open') {
      if (this.now() - this.openedAt >= this.opts.cooldownMs) {
        this.state = 'half_open';
        return true; // one probe allowed
      }
      return false;
    }
    return true; // half_open probe
  }

  onSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
  }

  onFailure(): void {
    this.failures++;
    if (this.state === 'half_open' || this.failures >= this.opts.failureThreshold) {
      this.state = 'open';
      this.openedAt = this.now();
      this.failures = 0;
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}
