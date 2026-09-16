import { clamp, logScale, mean, median, round, safeDivide, topCounts, unique, jaccard, keywordScore } from './utils.js';

const TRUST_PROOF_TYPES = new Set(['data', 'demo', 'case_study', 'before_after', 'testimonial', 'expertise', 'transparent_failure']);
const CONVERSION_CTAS = new Set(['buy', 'join', 'subscribe', 'download', 'book_call']);
const COMMUNITY_CTAS = new Set(['comment', 'share', 'join', 'subscribe']);
const HUMAN_HOOK_TYPES = new Set(['story', 'proof', 'demo', 'question', 'problem', 'contrarian']);

export function contentEngagementRate(item) {
  const m = item.metrics;
  return safeDivide(m.likes + m.comments + m.shares + m.saves, m.views, 0);
}

export function viewFollowerRatio(item, followers) {
  return safeDivide(item.metrics.views, (followers || 0) + 1, 0);
}

export function contentActionRate(item) {
  const m = item.metrics;
  return safeDivide(m.comments + m.shares + m.saves, m.views, 0);
}

export function computeEntityMetrics(entity, settings = {}) {
  const views = entity.content.map((c) => c.metrics.views);
  const ers = entity.content.map(contentEngagementRate);
  const actionRates = entity.content.map(contentActionRate);
  const followerGrowth = entity.followers_current != null && entity.followers_previous != null
    ? safeDivide(entity.followers_current - entity.followers_previous, Math.max(1, entity.followers_previous), 0)
    : null;
  const medianViews = median(views);
  const meanViews = mean(views);
  const breakthroughItems = entity.content.filter((c) => medianViews > 0 && c.metrics.views >= medianViews * 3).length;
  const vfrs = entity.content.map((c) => viewFollowerRatio(c, entity.followers_current));
  const evidenceConfidence = entity.evidence.length ? mean(entity.evidence.map((ev) => ev.confidence)) : 0;
  const hookTypes = topCounts(entity.content.map((c) => c.hook_type), 8);
  const topics = topCounts(entity.content.map((c) => c.topic), 8);
  const ctas = topCounts(entity.content.map((c) => c.cta), 8);
  const formats = topCounts(entity.content.map((c) => c.format), 8);
  const emotions = topCounts(entity.content.map((c) => c.emotional_trigger), 8);

  const allText = [
    entity.name,
    entity.niche,
    entity.audience_problem,
    entity.positioning_hint,
    ...entity.tags,
    ...entity.content.flatMap((c) => [c.title, c.topic, c.hook, c.transcript]),
  ].join(' ');
  const targetWords = [settings.target_niche, settings.product, settings.target_audience]
    .filter(Boolean)
    .flatMap((text) => String(text).split(/[\s,،]+/).filter((x) => x.length > 2));
  const targetFitTextScore = targetWords.length ? keywordScore(allText, targetWords.slice(0, 20)) : 0.5;

  return {
    content_count: entity.content.length,
    evidence_count: entity.evidence.length,
    evidence_confidence: round(evidenceConfidence),
    followers_current: entity.followers_current,
    followers_previous: entity.followers_previous,
    follower_growth_rate: followerGrowth == null ? null : round(followerGrowth),
    total_views: views.reduce((a, b) => a + b, 0),
    mean_views: round(meanViews),
    median_views: round(medianViews),
    mean_engagement_rate: round(mean(ers)),
    median_engagement_rate: round(median(ers)),
    mean_action_rate: round(mean(actionRates)),
    median_view_follower_ratio: round(median(vfrs)),
    breakthrough_items: breakthroughItems,
    hook_types: hookTypes,
    topics,
    ctas,
    formats,
    emotions,
    target_fit_text_score: round(targetFitTextScore),
  };
}

export function scoreGrowth(entity, metrics) {
  const followerGrowthScore = metrics.follower_growth_rate == null ? 0.35 : clamp(metrics.follower_growth_rate / 2); // 200% growth caps.
  const viewVelocityScore = logScale(metrics.mean_views, 500000);
  const breakthroughScore = clamp(metrics.breakthrough_items / Math.max(2, metrics.content_count * 0.25));
  const recentEvidenceScore = clamp(metrics.evidence_count / 5) * metrics.evidence_confidence;
  const vfrScore = logScale(metrics.median_view_follower_ratio, 20);
  return round(0.30 * followerGrowthScore + 0.25 * viewVelocityScore + 0.20 * breakthroughScore + 0.15 * recentEvidenceScore + 0.10 * vfrScore);
}

export function scoreEngagement(metrics) {
  // Organic short-form ER above 8-12% is strong, above 20% exceptional. Action rate prevents empty likes from dominating.
  const erScore = clamp(metrics.median_engagement_rate / 0.18);
  const actionScore = clamp(metrics.mean_action_rate / 0.06);
  const communityCtaScore = clamp((metrics.ctas || []).filter((c) => COMMUNITY_CTAS.has(c.value)).reduce((a, b) => a + b.count, 0) / Math.max(1, metrics.content_count));
  return round(0.55 * erScore + 0.30 * actionScore + 0.15 * communityCtaScore);
}

export function scoreReplicability(entity, metrics) {
  const hookDiversity = clamp(unique(entity.content.map((c) => c.hook_type)).filter((x) => x !== 'none' && x !== 'other').length / 5);
  const topicConsistency = metrics.topics?.[0] ? clamp(metrics.topics[0].count / Math.max(1, metrics.content_count)) : 0;
  const formatConsistency = metrics.formats?.[0] ? clamp(metrics.formats[0].count / Math.max(1, metrics.content_count)) : 0;
  const serialSignals = entity.content.filter((c) => /part\s*\d+|episode|series|day\s*\d+|قسمت|سری|روز\s*\d+/i.test([c.title, c.hook, c.transcript].join(' '))).length;
  const serialScore = clamp(serialSignals / Math.max(1, Math.ceil(metrics.content_count / 3)));
  const evidenceBacked = clamp(metrics.evidence_count / 3) * metrics.evidence_confidence;
  const mechanismScore = clamp((hookDiversity * 0.25) + (topicConsistency * 0.25) + (formatConsistency * 0.2) + (serialScore * 0.15) + (evidenceBacked * 0.15));

  // Penalize patterns that appear to depend mostly on celebrity/one-off virality.
  const oneHitRatio = metrics.breakthrough_items === 1 && metrics.content_count >= 5 ? 0.15 : 0;
  const lowContentPenalty = metrics.content_count < 3 ? 0.20 : 0;
  return round(clamp(mechanismScore - oneHitRatio - lowContentPenalty));
}

export function scoreAuthenticity(entity, metrics) {
  const proofScore = clamp(entity.content.filter((c) => c.proof_type && (TRUST_PROOF_TYPES.has(c.proof_type) || c.proof_type.length > 0)).length / Math.max(1, metrics.content_count));
  const humanHookScore = clamp(entity.content.filter((c) => HUMAN_HOOK_TYPES.has(c.hook_type)).length / Math.max(1, metrics.content_count));
  const evidenceScore = clamp(metrics.evidence_count / 4) * metrics.evidence_confidence;
  const meaningfulCommentSignals = clamp(entity.content.filter((c) => ['comment', 'join', 'share', 'save'].includes(c.cta)).length / Math.max(1, metrics.content_count));
  return round(0.35 * proofScore + 0.25 * humanHookScore + 0.25 * evidenceScore + 0.15 * meaningfulCommentSignals);
}

export function scoreConversion(entity, metrics) {
  const ctaScore = clamp(entity.content.filter((c) => CONVERSION_CTAS.has(c.cta)).length / Math.max(1, metrics.content_count));
  const pathText = [entity.positioning_hint, entity.audience_problem, entity.niche, ...entity.content.map((c) => `${c.cta} ${c.transcript}`)].join(' ');
  const conversionWords = ['offer', 'shop', 'store', 'newsletter', 'community', 'course', 'audit', 'demo', 'trial', 'download', 'buy', 'join', 'subscribe', 'call', 'فروش', 'خرید', 'جامعه', 'خبرنامه', 'مشاوره', 'دانلود'];
  const pathScore = keywordScore(pathText, conversionWords);
  const actionScore = clamp(metrics.mean_action_rate / 0.05);
  return round(0.45 * ctaScore + 0.35 * pathScore + 0.20 * actionScore);
}

export function scoreTargetFit(entity, metrics, settings = {}) {
  const nicheSimilarity = jaccard(entity.niche, settings.target_niche || '') || 0;
  const audienceSimilarity = jaccard(entity.audience_problem, settings.target_audience || '') || 0;
  const productSimilarity = jaccard(`${entity.niche} ${entity.positioning_hint} ${entity.content.map((c) => c.topic).join(' ')}`, settings.product || '') || 0;
  const textScore = metrics.target_fit_text_score ?? 0.5;
  if (!settings.target_niche && !settings.product && !settings.target_audience) return 0.6;
  return round(clamp(0.35 * nicheSimilarity + 0.25 * audienceSimilarity + 0.20 * productSimilarity + 0.20 * textScore));
}

export function compositeScore(scores) {
  // S = 0.25G + 0.20E + 0.20R + 0.15A + 0.10C + 0.10T
  return round(
    0.25 * scores.growth +
    0.20 * scores.engagement +
    0.20 * scores.replicability +
    0.15 * scores.authenticity +
    0.10 * scores.conversion +
    0.10 * scores.target_fit
  );
}

export function scoreEntity(entity, settings = {}) {
  const metrics = computeEntityMetrics(entity, settings);
  const scores = {
    growth: scoreGrowth(entity, metrics),
    engagement: scoreEngagement(metrics),
    replicability: scoreReplicability(entity, metrics),
    authenticity: scoreAuthenticity(entity, metrics),
    conversion: scoreConversion(entity, metrics),
    target_fit: scoreTargetFit(entity, metrics, settings),
  };
  scores.total = compositeScore(scores);
  const warnings = [];
  if (metrics.evidence_count < (settings.min_evidence ?? 2)) warnings.push(`Low evidence count: ${metrics.evidence_count}`);
  if (metrics.content_count < 3) warnings.push(`Low content sample: ${metrics.content_count}`);
  if (scores.replicability < 0.35) warnings.push('Pattern may be hard to transfer');
  if (scores.growth > 0.75 && metrics.evidence_confidence < 0.55) warnings.push('High growth score with weak evidence confidence');
  return { entity, metrics, scores, warnings };
}
