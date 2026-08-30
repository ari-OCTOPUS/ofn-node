#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { analyze } from './index.js';
import { analyzeInputJsonSchema, analysisOutputJsonSchema, DomainError } from './schemas.js';
import { renderMarkdownReport } from './report.js';
import { toCsv } from './utils.js';

function parseArgs(argv) {
  const [command = 'help', ...rest] = argv;
  const opts = { _: [] };
  for (let i = 0; i < rest.length; i += 1) {
    const arg = rest[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      const next = rest[i + 1];
      if (!next || next.startsWith('--')) opts[key] = true;
      else {
        opts[key] = next;
        i += 1;
      }
    } else opts._.push(arg);
  }
  return { command, opts };
}

async function readJson(filePath) {
  const text = await fs.readFile(filePath, 'utf8');
  return JSON.parse(text);
}

async function writeJson(filePath, data) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf8');
}

async function commandAnalyze(opts) {
  if (!opts.input) throw new Error('Missing --input file');
  const outDir = opts.out || 'output';
  const input = await readJson(opts.input);
  const result = analyze(input);
  await fs.mkdir(outDir, { recursive: true });
  await writeJson(path.join(outDir, 'analysis.json'), result);
  await writeJson(path.join(outDir, 'top_creators.json'), result.top_entities);
  await writeJson(path.join(outDir, 'architecture_cards.json'), result.architecture_cards);
  await writeJson(path.join(outDir, 'content_hypotheses.json'), result.experiment_plan);
  await writeJson(path.join(outDir, '30_day_experiment_plan.json'), result.thirty_day_roadmap);
  await writeJson(path.join(outDir, 'evidence_report.json'), result.evidence_report);
  await fs.writeFile(path.join(outDir, 'evidence_report.md'), renderMarkdownReport(result), 'utf8');
  await fs.writeFile(path.join(outDir, 'top_creators.csv'), toCsv(result.top_entities.map((item) => ({
    entity_id: item.entity_id,
    name: item.name,
    platform: item.primary_platform,
    niche: item.niche,
    total_score: item.scores.total,
    growth: item.scores.growth,
    engagement: item.scores.engagement,
    replicability: item.scores.replicability,
    authenticity: item.scores.authenticity,
    conversion: item.scores.conversion,
    target_fit: item.scores.target_fit,
    evidence_count: item.metrics.evidence_count,
    warnings: item.warnings.join('; '),
  }))), 'utf8');

  console.log(JSON.stringify({
    ok: true,
    outDir,
    summary: result.summary,
    files: [
      'analysis.json',
      'top_creators.json',
      'top_creators.csv',
      'architecture_cards.json',
      'content_hypotheses.json',
      '30_day_experiment_plan.json',
      'evidence_report.json',
      'evidence_report.md',
    ],
  }, null, 2));
}

async function commandSchemas(opts) {
  const outDir = opts.out || 'contracts';
  await writeJson(path.join(outDir, 'analyze-input.v1.json'), analyzeInputJsonSchema());
  await writeJson(path.join(outDir, 'analysis-output.v1.json'), analysisOutputJsonSchema());
  console.log(JSON.stringify({ ok: true, outDir }, null, 2));
}

function printHelp() {
  console.log(`Growth Archaeologist\n\nUsage:\n  node src/cli.js analyze --input fixtures/sample_entities.json --out output\n  node src/cli.js schemas --out contracts\n\nCommands:\n  analyze   Score entities, extract architecture cards, build experiment plan.\n  schemas   Write JSON schemas for contracts.\n`);
}

async function main() {
  const { command, opts } = parseArgs(process.argv.slice(2));
  try {
    if (command === 'analyze') await commandAnalyze(opts);
    else if (command === 'schemas') await commandSchemas(opts);
    else printHelp();
  } catch (err) {
    if (err instanceof DomainError) {
      console.error(JSON.stringify({ ok: false, error: err.toJSON() }, null, 2));
      process.exitCode = 2;
    } else {
      console.error(JSON.stringify({ ok: false, error: { message: err.message, stack: process.env.DEBUG ? err.stack : undefined } }, null, 2));
      process.exitCode = 1;
    }
  }
}

main();
