export const SCHEMA_VERSION = 'growth-archaeologist.v1';

export const ERROR_CODES = Object.freeze({
  INVALID_INPUT: 'INVALID_INPUT',
  SCHEMA_MISMATCH: 'SCHEMA_MISMATCH',
  INSUFFICIENT_EVIDENCE: 'INSUFFICIENT_EVIDENCE',
  POLICY_BLOCKED: 'POLICY_BLOCKED',
});

export class DomainError extends Error {
  constructor(errorCode, message, details = {}) {
    super(message);
    this.name = 'DomainError';
    this.errorCode = errorCode;
    this.details = details;
    this.retryable = false;
  }

  toJSON() {
    return {
      error_code: this.errorCode,
      message: this.message,
      retryable: this.retryable,
      details: this.details,
      trace_id: this.details.trace_id || null,
    };
  }
}

const PLATFORM_SET = new Set(['tiktok', 'youtube', 'instagram', 'linkedin', 'x', 'reddit', 'web', 'newsletter', 'podcast', 'other']);
const ENTITY_TYPE_SET = new Set(['creator', 'company', 'brand', 'founder']);
const CONTENT_FORMAT_SET = new Set(['short_video', 'long_video', 'carousel', 'thread', 'live', 'article', 'newsletter', 'podcast', 'post', 'other']);
const HOOK_TYPE_SET = new Set(['contrarian', 'question', 'demo', 'story', 'proof', 'curiosity', 'problem', 'trend', 'none', 'other']);
const CTA_SET = new Set(['follow', 'comment', 'save', 'share', 'buy', 'join', 'subscribe', 'download', 'book_call', 'none', 'other']);
const EMOTION_SET = new Set(['curiosity', 'belonging', 'utility', 'humor', 'trust', 'fear', 'aspiration', 'relief', 'surprise', 'other']);

export function assertObject(value, path = 'value') {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be an object`, { path });
  }
}

export function assertArray(value, path = 'value') {
  if (!Array.isArray(value)) {
    throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be an array`, { path });
  }
}

export function optionalString(value, path, { max = 1000, min = 0 } = {}) {
  if (value == null) return undefined;
  if (typeof value !== 'string') throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be a string`, { path });
  const trimmed = value.trim();
  if (trimmed.length < min) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} is too short`, { path, min });
  if (trimmed.length > max) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} is too long`, { path, max });
  return trimmed;
}

export function requiredString(value, path, opts = {}) {
  const out = optionalString(value, path, { ...opts, min: opts.min ?? 1 });
  if (!out) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} is required`, { path });
  return out;
}

export function optionalNumber(value, path, { min = -Infinity, max = Infinity, integer = false } = {}) {
  if (value == null || value === '') return undefined;
  if (typeof value !== 'number' || Number.isNaN(value) || !Number.isFinite(value)) {
    throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be a finite number`, { path });
  }
  if (integer && !Number.isInteger(value)) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be an integer`, { path });
  if (value < min || value > max) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} out of range`, { path, min, max });
  return value;
}

export function numberOr(value, fallback, path, opts = {}) {
  return optionalNumber(value, path, opts) ?? fallback;
}

export function optionalEnum(value, path, allowed, fallback = 'other') {
  if (value == null || value === '') return fallback;
  const normalized = String(value).trim().toLowerCase();
  if (!allowed.has(normalized)) return fallback;
  return normalized;
}

export function optionalStringArray(value, path, { maxItems = 50, maxLength = 200 } = {}) {
  if (value == null) return [];
  if (!Array.isArray(value)) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be an array`, { path });
  if (value.length > maxItems) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} has too many items`, { path, maxItems });
  return value.map((v, i) => requiredString(String(v), `${path}[${i}]`, { max: maxLength }));
}

export function normalizeUrl(value, path) {
  const text = optionalString(value, path, { max: 2048 });
  if (!text) return undefined;
  try {
    return new URL(text).toString();
  } catch {
    // Allow private/internal handles such as research://report_123 in future adapters.
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(text)) return text;
    throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be a valid URL`, { path });
  }
}

export function normalizeDate(value, path) {
  const text = optionalString(value, path, { max: 100 });
  if (!text) return undefined;
  const d = new Date(text);
  if (Number.isNaN(d.getTime())) throw new DomainError(ERROR_CODES.INVALID_INPUT, `${path} must be a valid date`, { path });
  return d.toISOString();
}

export function validateEvidence(raw, index = 0) {
  assertObject(raw, `evidence[${index}]`);
  const id = optionalString(raw.id, `evidence[${index}].id`, { max: 120 }) || `ev_${index + 1}`;
  const source_url = normalizeUrl(raw.source_url || raw.url, `evidence[${index}].source_url`);
  const source_type = optionalString(raw.source_type, `evidence[${index}].source_type`, { max: 80 }) || 'unknown';
  const claim = requiredString(raw.claim, `evidence[${index}].claim`, { max: 1200 });
  const metric_name = optionalString(raw.metric_name, `evidence[${index}].metric_name`, { max: 100 });
  const metric_value = optionalNumber(raw.metric_value, `evidence[${index}].metric_value`);
  const confidence = numberOr(raw.confidence, 0.5, `evidence[${index}].confidence`, { min: 0, max: 1 });
  return {
    id,
    source_url,
    source_type,
    published_at: normalizeDate(raw.published_at || raw.observed_at, `evidence[${index}].published_at`),
    claim,
    metric_name,
    metric_value,
    confidence,
  };
}

export function validateContentItem(raw, index = 0) {
  assertObject(raw, `content[${index}]`);
  const metrics = raw.metrics || {};
  assertObject(metrics, `content[${index}].metrics`);
  return {
    id: optionalString(raw.id, `content[${index}].id`, { max: 120 }) || `content_${index + 1}`,
    url: normalizeUrl(raw.url, `content[${index}].url`),
    platform: optionalEnum(raw.platform, `content[${index}].platform`, PLATFORM_SET, 'other'),
    published_at: normalizeDate(raw.published_at, `content[${index}].published_at`),
    title: optionalString(raw.title, `content[${index}].title`, { max: 500 }) || '',
    transcript: optionalString(raw.transcript, `content[${index}].transcript`, { max: 10000 }) || '',
    hook: optionalString(raw.hook, `content[${index}].hook`, { max: 500 }) || '',
    hook_type: optionalEnum(raw.hook_type, `content[${index}].hook_type`, HOOK_TYPE_SET, 'other'),
    format: optionalEnum(raw.format, `content[${index}].format`, CONTENT_FORMAT_SET, 'other'),
    topic: optionalString(raw.topic, `content[${index}].topic`, { max: 200 }) || '',
    emotional_trigger: optionalEnum(raw.emotional_trigger, `content[${index}].emotional_trigger`, EMOTION_SET, 'other'),
    proof_type: optionalString(raw.proof_type, `content[${index}].proof_type`, { max: 120 }) || null,
    cta: optionalEnum(raw.cta, `content[${index}].cta`, CTA_SET, 'none'),
    narrative_steps: optionalStringArray(raw.narrative_steps, `content[${index}].narrative_steps`, { maxItems: 20, maxLength: 160 }),
    metrics: {
      views: numberOr(metrics.views, 0, `content[${index}].metrics.views`, { min: 0, integer: true }),
      likes: numberOr(metrics.likes, 0, `content[${index}].metrics.likes`, { min: 0, integer: true }),
      comments: numberOr(metrics.comments, 0, `content[${index}].metrics.comments`, { min: 0, integer: true }),
      shares: numberOr(metrics.shares, 0, `content[${index}].metrics.shares`, { min: 0, integer: true }),
      saves: numberOr(metrics.saves, 0, `content[${index}].metrics.saves`, { min: 0, integer: true }),
    },
    evidence_ids: optionalStringArray(raw.evidence_ids, `content[${index}].evidence_ids`, { maxItems: 20, maxLength: 120 }),
  };
}

export function validateEntity(raw, index = 0) {
  assertObject(raw, `entities[${index}]`);
  const profile = raw.profile || raw;
  assertObject(profile, `entities[${index}].profile`);
  const evidence = (raw.evidence || []).map((ev, i) => validateEvidence(ev, i));
  const content = (raw.content || raw.contents || []).map((item, i) => validateContentItem(item, i));
  return {
    entity_id: optionalString(profile.entity_id || raw.entity_id || profile.id, `entities[${index}].entity_id`, { max: 120 }) || `ent_${index + 1}`,
    name: requiredString(profile.name || raw.name, `entities[${index}].name`, { max: 180 }),
    handle: optionalString(profile.handle || raw.handle, `entities[${index}].handle`, { max: 120 }) || null,
    entity_type: optionalEnum(profile.entity_type || raw.entity_type, `entities[${index}].entity_type`, ENTITY_TYPE_SET, 'creator'),
    primary_platform: optionalEnum(profile.primary_platform || raw.primary_platform || profile.platform, `entities[${index}].primary_platform`, PLATFORM_SET, 'other'),
    country: optionalString(profile.country || raw.country, `entities[${index}].country`, { max: 80 }) || null,
    niche: optionalString(profile.niche || raw.niche, `entities[${index}].niche`, { max: 180 }) || 'unknown',
    audience_problem: optionalString(profile.audience_problem || raw.audience_problem, `entities[${index}].audience_problem`, { max: 500 }) || '',
    positioning_hint: optionalString(profile.positioning || raw.positioning, `entities[${index}].positioning`, { max: 500 }) || '',
    discovered_at: normalizeDate(profile.discovered_at || raw.discovered_at, `entities[${index}].discovered_at`),
    first_growth_evidence_at: normalizeDate(profile.first_growth_evidence_at || raw.first_growth_evidence_at, `entities[${index}].first_growth_evidence_at`),
    followers_current: optionalNumber(profile.followers_current ?? raw.followers_current, `entities[${index}].followers_current`, { min: 0, integer: true }) ?? null,
    followers_previous: optionalNumber(profile.followers_previous ?? raw.followers_previous, `entities[${index}].followers_previous`, { min: 0, integer: true }) ?? null,
    content,
    evidence,
    tags: optionalStringArray(raw.tags || profile.tags, `entities[${index}].tags`, { maxItems: 30, maxLength: 80 }),
  };
}

export function validateAnalyzeInput(raw) {
  assertObject(raw, 'input');
  const settings = raw.settings || {};
  assertObject(settings, 'settings');
  const entitiesRaw = raw.entities || raw.items || [];
  assertArray(entitiesRaw, 'entities');
  if (entitiesRaw.length === 0) {
    throw new DomainError(ERROR_CODES.INVALID_INPUT, 'entities must contain at least one entity', { path: 'entities' });
  }
  if (entitiesRaw.length > 500) {
    throw new DomainError(ERROR_CODES.INVALID_INPUT, 'too many entities for a single job', { max: 500 });
  }
  return {
    schema_version: raw.schema_version || SCHEMA_VERSION,
    job: {
      job_id: optionalString(raw.job?.job_id, 'job.job_id', { max: 120 }) || `job_${Date.now()}`,
      tenant: optionalString(raw.job?.tenant, 'job.tenant', { max: 120 }) || 'default',
      created_at: normalizeDate(raw.job?.created_at, 'job.created_at') || new Date().toISOString(),
    },
    settings: {
      target_niche: optionalString(settings.target_niche, 'settings.target_niche', { max: 180 }) || '',
      target_market: optionalString(settings.target_market, 'settings.target_market', { max: 80 }) || '',
      language: optionalString(settings.language, 'settings.language', { max: 80 }) || 'fa',
      product: optionalString(settings.product, 'settings.product', { max: 240 }) || '',
      target_audience: optionalString(settings.target_audience, 'settings.target_audience', { max: 500 }) || '',
      min_evidence: numberOr(settings.min_evidence, 2, 'settings.min_evidence', { min: 0, max: 20, integer: true }),
      top_n: numberOr(settings.top_n, 10, 'settings.top_n', { min: 1, max: 100, integer: true }),
    },
    entities: entitiesRaw.map((entity, i) => validateEntity(entity, i)),
  };
}

export function analyzeInputJsonSchema() {
  return {
    $schema: 'https://json-schema.org/draft/2020-12/schema',
    $id: 'https://example.local/growth-archaeologist/analyze-input.v1.json',
    title: 'Growth Archaeologist Analyze Input',
    type: 'object',
    required: ['entities'],
    additionalProperties: false,
    properties: {
      schema_version: { type: 'string' },
      job: {
        type: 'object',
        additionalProperties: true,
        properties: {
          job_id: { type: 'string' },
          tenant: { type: 'string' },
          created_at: { type: 'string', format: 'date-time' },
        },
      },
      settings: {
        type: 'object',
        additionalProperties: false,
        properties: {
          target_niche: { type: 'string' },
          target_market: { type: 'string' },
          language: { type: 'string' },
          product: { type: 'string' },
          target_audience: { type: 'string' },
          min_evidence: { type: 'integer', minimum: 0, maximum: 20 },
          top_n: { type: 'integer', minimum: 1, maximum: 100 },
        },
      },
      entities: {
        type: 'array',
        minItems: 1,
        maxItems: 500,
        items: {
          type: 'object',
          required: ['name'],
          additionalProperties: true,
          properties: {
            entity_id: { type: 'string' },
            name: { type: 'string', minLength: 1 },
            entity_type: { enum: [...ENTITY_TYPE_SET] },
            primary_platform: { enum: [...PLATFORM_SET] },
            niche: { type: 'string' },
            followers_current: { type: 'integer', minimum: 0 },
            followers_previous: { type: 'integer', minimum: 0 },
            evidence: { type: 'array' },
            content: { type: 'array' },
          },
        },
      },
    },
  };
}

export function analysisOutputJsonSchema() {
  return {
    $schema: 'https://json-schema.org/draft/2020-12/schema',
    $id: 'https://example.local/growth-archaeologist/analysis-output.v1.json',
    title: 'Growth Archaeologist Analysis Output',
    type: 'object',
    required: ['schema_version', 'job', 'summary', 'top_entities', 'architecture_cards', 'experiment_plan', 'evidence_report'],
    additionalProperties: false,
    properties: {
      schema_version: { type: 'string' },
      job: { type: 'object' },
      summary: { type: 'object' },
      top_entities: { type: 'array' },
      architecture_cards: { type: 'array' },
      experiment_plan: { type: 'array' },
      evidence_report: { type: 'object' },
      warnings: { type: 'array', items: { type: 'string' } },
    },
  };
}
