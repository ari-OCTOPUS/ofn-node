import test from 'node:test';
import assert from 'node:assert/strict';
import fixture from '../fixtures/sample_entities.json' with { type: 'json' };
import { analyze, validateAnalyzeInput, scoreEntity } from '../src/index.js';

const input = validateAnalyzeInput(fixture);

test('validateAnalyzeInput normalizes sample fixture', () => {
  assert.equal(input.entities.length, 3);
  assert.equal(input.entities[0].content.length, 4);
  assert.equal(input.settings.top_n, 5);
});

test('scoreEntity returns bounded weighted scores', () => {
  const scored = scoreEntity(input.entities[0], input.settings);
  for (const value of Object.values(scored.scores)) {
    assert.equal(typeof value, 'number');
    assert.ok(value >= 0 && value <= 1, `score out of bounds: ${value}`);
  }
  assert.ok(scored.scores.total > 0.55, 'strong AI debugging example should score well');
});

test('one-hit viral entity is penalized for replicability/evidence risk', () => {
  const scored = scoreEntity(input.entities[2], input.settings);
  assert.ok(scored.scores.replicability < 0.6);
  assert.ok(scored.warnings.length >= 1);
});

test('analyze creates architecture cards and experiment plan', () => {
  const output = analyze(fixture);
  assert.equal(output.top_entities.length, 3);
  assert.ok(output.architecture_cards.length >= 1);
  assert.ok(output.experiment_plan.length >= 1);
  assert.ok(output.evidence_report.totals.evidence_items >= 1);
  assert.equal(output.architecture_cards[0].schema_version, 'strategy-card.v1');
});
