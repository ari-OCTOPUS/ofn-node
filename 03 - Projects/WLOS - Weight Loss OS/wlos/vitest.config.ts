import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['packages/**/*.test.ts', 'apps/**/*.test.ts'],
    environment: 'node',
    // Deterministic tests only: no network, no DB, fixed seeds, fake timers where needed.
    testTimeout: 15_000,
  },
});
