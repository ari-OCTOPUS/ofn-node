import test from 'node:test';
import assert from 'node:assert/strict';
import { validateAnalyzeInput, DomainError } from '../src/index.js';

test('rejects empty entity list', () => {
  assert.throws(() => validateAnalyzeInput({ entities: [] }), DomainError);
});

test('rejects invalid URL inside content', () => {
  assert.throws(() => validateAnalyzeInput({
    entities: [{
      name: 'Bad URL',
      content: [{ url: 'not-a-url', metrics: {} }],
    }],
  }), DomainError);
});

test('allows minimal valid entity', () => {
  const parsed = validateAnalyzeInput({
    settings: { top_n: 1 },
    entities: [{ name: 'Minimal Creator', evidence: [{ claim: 'Manual observation', confidence: 0.4 }] }],
  });
  assert.equal(parsed.entities[0].name, 'Minimal Creator');
});
