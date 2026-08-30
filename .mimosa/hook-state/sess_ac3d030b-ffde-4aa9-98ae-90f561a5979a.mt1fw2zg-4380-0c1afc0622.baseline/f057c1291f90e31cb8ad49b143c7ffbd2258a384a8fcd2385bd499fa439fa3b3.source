import { mdEscape, round } from './utils.js';

export function createEvidenceReport(scoredEntities, cards, clusters) {
  const totalEvidence = scoredEntities.reduce((sum, s) => sum + s.metrics.evidence_count, 0);
  const totalContent = scoredEntities.reduce((sum, s) => sum + s.metrics.content_count, 0);
  const weak = scoredEntities.filter((s) => s.warnings.length > 0).map((s) => ({ entity_id: s.entity.entity_id, name: s.entity.name, warnings: s.warnings }));
  return {
    schema_version: 'evidence-report.v1',
    totals: {
      entities: scoredEntities.length,
      content_items: totalContent,
      evidence_items: totalEvidence,
      average_evidence_confidence: round(scoredEntities.reduce((sum, s) => sum + s.metrics.evidence_confidence, 0) / Math.max(1, scoredEntities.length)),
    },
    source_quality_notes: [
      'داده مستقیم، ادعای منبع و تفسیر مدل باید جدا ذخیره شوند.',
      'امتیاز بالا بدون evidence کافی فقط فرضیه است، نه نتیجه قطعی.',
      'برای پلتفرم‌هایی مثل TikTok/Instagram بخشی از داده‌ها بدون API رسمی یا مجوز قابل اتکا نیست.',
    ],
    weak_spots: weak,
    architecture_clusters: clusters,
    top_evidence_ids: cards.flatMap((c) => c.evidence.evidence_ids.map((id) => ({ architecture_id: c.architecture_id, evidence_id: id }))).slice(0, 50),
  };
}

export function renderMarkdownReport(analysis) {
  const lines = [];
  lines.push('# Growth Archaeologist Report');
  lines.push('');
  lines.push(`Schema: ${analysis.schema_version}`);
  lines.push(`Job: ${analysis.job.job_id}`);
  lines.push('');
  lines.push('## Summary');
  lines.push('');
  lines.push(`- Entities analyzed: ${analysis.summary.entities_analyzed}`);
  lines.push(`- Architecture cards: ${analysis.summary.architecture_cards}`);
  lines.push(`- Experiments: ${analysis.summary.experiments}`);
  lines.push(`- Strongest entity: ${analysis.summary.strongest_entity || 'n/a'}`);
  lines.push('');
  lines.push('## Top Entities');
  lines.push('');
  lines.push('| Rank | Entity | Score | Growth | Engagement | Replicability | Evidence | Warnings |');
  lines.push('|---:|---|---:|---:|---:|---:|---:|---|');
  analysis.top_entities.forEach((item, index) => {
    lines.push(`| ${index + 1} | ${mdEscape(item.name)} | ${item.scores.total} | ${item.scores.growth} | ${item.scores.engagement} | ${item.scores.replicability} | ${item.metrics.evidence_count} | ${mdEscape(item.warnings.join('; '))} |`);
  });
  lines.push('');
  lines.push('## Architecture Cards');
  for (const card of analysis.architecture_cards) {
    lines.push('');
    lines.push(`### ${mdEscape(card.creator.name)} — ${mdEscape(card.positioning)}`);
    lines.push('');
    lines.push(`- Score: ${card.scores.total} | Confidence: ${card.confidence}`);
    lines.push(`- Audience problem: ${mdEscape(card.audience_problem)}`);
    lines.push(`- Pillars: ${card.content_engine.pillars.map(mdEscape).join(', ')}`);
    lines.push(`- Narrative: ${mdEscape(card.content_engine.narrative_structure)}`);
    lines.push(`- Community loop: ${mdEscape(card.growth_loop.community_loop)}`);
    lines.push(`- Conversion path: ${card.growth_loop.conversion_path.map(mdEscape).join(' → ')}`);
    lines.push('- Observed facts:');
    card.evidence.observed_facts.forEach((f) => lines.push(`  - ${mdEscape(f)}`));
    lines.push('- Recommendations:');
    card.recommendations.forEach((r) => lines.push(`  - ${mdEscape(r)}`));
    if (card.risks.length) {
      lines.push('- Risks:');
      card.risks.forEach((r) => lines.push(`  - ${mdEscape(r)}`));
    }
  }
  lines.push('');
  lines.push('## Experiment Plan');
  for (const exp of analysis.experiment_plan) {
    lines.push('');
    lines.push(`### ${mdEscape(exp.title)}`);
    lines.push(`- Hypothesis: ${mdEscape(exp.hypothesis)}`);
    lines.push(`- Priority: ${exp.priority}`);
    lines.push(`- Decision rule: ${mdEscape(exp.decision_rule)}`);
    lines.push('- Variants:');
    exp.variants.forEach((v) => {
      lines.push(`  - ${mdEscape(v.name)}: ${mdEscape(v.hook)}`);
    });
  }
  lines.push('');
  lines.push('## Evidence Caveats');
  analysis.evidence_report.source_quality_notes.forEach((n) => lines.push(`- ${mdEscape(n)}`));
  lines.push('');
  return lines.join('\n');
}
