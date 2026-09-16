import { validateAnalyzeInput, SCHEMA_VERSION } from './schemas.js';
import { scoreEntity } from './scoring.js';
import { buildArchitectureCard, clusterArchitectures } from './patterns.js';
import { createExperimentPlan, createThirtyDayRoadmap } from './experiments.js';
import { createEvidenceReport } from './report.js';

export { validateAnalyzeInput, analyzeInputJsonSchema, analysisOutputJsonSchema, DomainError } from './schemas.js';
export { scoreEntity } from './scoring.js';
export { buildArchitectureCard, clusterArchitectures } from './patterns.js';
export { createExperimentPlan, createThirtyDayRoadmap } from './experiments.js';
export { createEvidenceReport, renderMarkdownReport } from './report.js';

export function analyze(rawInput) {
  const input = validateAnalyzeInput(rawInput);
  const scoredEntities = input.entities
    .map((entity) => scoreEntity(entity, input.settings))
    .sort((a, b) => b.scores.total - a.scores.total || b.metrics.evidence_confidence - a.metrics.evidence_confidence);

  const topScored = scoredEntities.slice(0, input.settings.top_n);
  const architectureCards = topScored.map((s) => buildArchitectureCard(s, input.settings));
  const clusters = clusterArchitectures(architectureCards);
  const experimentPlan = createExperimentPlan(architectureCards, input.settings);
  const roadmap = createThirtyDayRoadmap(experimentPlan);
  const evidenceReport = createEvidenceReport(scoredEntities, architectureCards, clusters);
  const warnings = scoredEntities.flatMap((s) => s.warnings.map((w) => `${s.entity.name}: ${w}`));

  return {
    schema_version: SCHEMA_VERSION,
    job: input.job,
    settings: input.settings,
    summary: {
      entities_analyzed: scoredEntities.length,
      architecture_cards: architectureCards.length,
      experiments: experimentPlan.length,
      strongest_entity: scoredEntities[0]?.entity.name || null,
      strongest_score: scoredEntities[0]?.scores.total ?? null,
    },
    top_entities: topScored.map((s) => ({
      entity_id: s.entity.entity_id,
      name: s.entity.name,
      handle: s.entity.handle,
      entity_type: s.entity.entity_type,
      primary_platform: s.entity.primary_platform,
      niche: s.entity.niche,
      scores: s.scores,
      metrics: s.metrics,
      warnings: s.warnings,
    })),
    architecture_cards: architectureCards,
    architecture_clusters: clusters,
    experiment_plan: experimentPlan,
    thirty_day_roadmap: roadmap,
    evidence_report: evidenceReport,
    warnings,
  };
}
