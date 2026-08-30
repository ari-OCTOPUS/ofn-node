import { round, stableId, topCounts, unique } from './utils.js';

const HOOK_LABELS = {
  contrarian: 'ادعای خلاف انتظار',
  question: 'سؤال مستقیم',
  demo: 'نمایش عملی',
  story: 'روایت شخصی',
  proof: 'اثبات/داده',
  curiosity: 'شکاف کنجکاوی',
  problem: 'مسئله فوری مخاطب',
  trend: 'اتصال به ترند',
  none: 'بدون هوک روشن',
  other: 'ترکیبی/نامشخص',
};

const EMOTION_LABELS = {
  curiosity: 'کنجکاوی',
  belonging: 'تعلق',
  utility: 'کاربرد فوری',
  humor: 'طنز',
  trust: 'اعتماد',
  fear: 'ترس/ریسک',
  aspiration: 'آرمان/پیشرفت',
  relief: 'آرامش از حل مسئله',
  surprise: 'غافلگیری',
  other: 'احساس ترکیبی',
};

function labelHook(hook) {
  return HOOK_LABELS[hook] || hook || 'نامشخص';
}

function labelEmotion(emotion) {
  return EMOTION_LABELS[emotion] || emotion || 'نامشخص';
}

function inferPositioning(entity, metrics) {
  if (entity.positioning_hint) return entity.positioning_hint;
  const topHook = metrics.hook_types?.[0]?.value;
  const topEmotion = metrics.emotions?.[0]?.value;
  const topic = metrics.topics?.[0]?.value || entity.niche;
  if (topHook === 'proof' || topHook === 'demo') return `متخصص قابل‌اعتماد در ${topic} با تکیه بر نمایش و اثبات`;
  if (topHook === 'story') return `روایت‌گر تجربه واقعی در ${topic} برای حل مسئله مخاطب`;
  if (topEmotion === 'humor') return `سازنده سرگرم‌کننده/آموزشی در ${topic}`;
  return `منبع کاربردی و قابل‌کشف در ${topic}`;
}

function inferContentPillars(entity, metrics) {
  const topics = (metrics.topics || []).filter((t) => t.value).map((t) => t.value).slice(0, 4);
  const fallback = unique([
    entity.niche,
    'آموزش کوتاه',
    'نمایش تجربه واقعی',
    'پاسخ به سؤال مخاطب',
  ]).slice(0, 4);
  return topics.length >= 2 ? topics : fallback;
}

function inferNarrativeStructure(entity, metrics) {
  const hook = labelHook(metrics.hook_types?.[0]?.value);
  const emotion = labelEmotion(metrics.emotions?.[0]?.value);
  const cta = metrics.ctas?.[0]?.value || 'comment';
  const proofCount = entity.content.filter((c) => c.proof_type).length;
  const proof = proofCount ? 'اثبات با نمونه/داده' : 'توضیح ساده';
  return `${hook} → مسئله مخاطب → ${proof} → نتیجه قابل‌استفاده → CTA: ${cta}؛ محرک اصلی: ${emotion}`;
}

function inferCadence(entity) {
  const dates = entity.content.map((c) => c.published_at).filter(Boolean).map((d) => new Date(d).getTime()).sort((a, b) => a - b);
  if (dates.length < 2) {
    return { suggested: '3-5 محتوای کوتاه در هفته', observed: 'نمونه زمانی کافی نیست', confidence: 0.35 };
  }
  const days = Math.max(1, (dates[dates.length - 1] - dates[0]) / 86400000);
  const perWeek = round((dates.length / days) * 7, 2);
  return {
    observed_posts_per_week: perWeek,
    suggested: perWeek >= 5 ? 'انتشار تقریباً روزانه با بازیافت قالب‌های موفق' : '3-5 انتشار در هفته با سری‌سازی موضوعات برنده',
    confidence: Math.min(0.9, 0.4 + dates.length / 20),
  };
}

function inferPlatformStrategy(entity, metrics) {
  const platforms = topCounts(entity.content.map((c) => c.platform), 5);
  const formats = metrics.formats || [];
  return {
    primary: entity.primary_platform,
    observed_platforms: platforms,
    dominant_formats: formats,
    recommendation: 'یک ایده مادر را به ویدئوی کوتاه، پست توضیحی و پاسخ به کامنت تبدیل کن؛ داده‌ها را جدا برای هر پلتفرم بسنج.',
  };
}

function inferCommunityLoop(entity, metrics) {
  const ctas = new Set(entity.content.map((c) => c.cta));
  if (ctas.has('comment')) return 'کامنت‌ها را به صف ایده تبدیل کن: سؤال → پاسخ کوتاه → دعوت به ارسال کیس بعدی.';
  if (ctas.has('join') || ctas.has('subscribe')) return 'محتوای رایگان → عضویت جامعه/خبرنامه → جمع‌آوری سؤال → محتوای سریالی.';
  return 'در هر محتوا یک سؤال تشخیصی بپرس و بهترین پاسخ‌ها را به محتوای بعدی تبدیل کن.';
}

function inferConversionPath(entity, metrics) {
  const ctas = new Set(entity.content.map((c) => c.cta));
  if (ctas.has('buy')) return ['محتوای آموزشی/نمایشی', 'اثبات اعتماد', 'محصول مرتبط', 'پیگیری با محتوای موردی'];
  if (ctas.has('book_call')) return ['تشخیص مسئله', 'نمایش تخصص', 'دعوت به کال/مشاوره', 'پرورش لید با نمونه‌های بیشتر'];
  if (ctas.has('download')) return ['هوک مسئله', 'ارزش فوری', 'دانلود ابزار/چک‌لیست', 'ایمیل/جامعه', 'پیشنهاد تخصصی'];
  if (ctas.has('join') || ctas.has('subscribe')) return ['محتوای رایگان', 'عضویت', 'اعتماد از تداوم', 'پیشنهاد محصول/خدمت'];
  return ['محتوای قابل‌کشف', 'ذخیره/کامنت', 'بازگشت مخاطب', 'دعوت به جامعه یا پیشنهاد سبک'];
}

function inferMonetization(entity) {
  const text = [entity.positioning_hint, entity.niche, ...entity.content.map((c) => `${c.cta} ${c.transcript}`)].join(' ').toLowerCase();
  if (/course|دوره|training|workshop/.test(text)) return 'دوره/آموزش تخصصی';
  if (/shop|store|buy|خرید|فروش|product|محصول/.test(text)) return 'محصول مستقیم یا تجارت اجتماعی';
  if (/consult|call|audit|مشاوره|کال/.test(text)) return 'مشاوره/خدمت تخصصی';
  if (/newsletter|subscribe|community|جامعه|خبرنامه/.test(text)) return 'خبرنامه/جامعه و پیشنهادهای بعدی';
  return 'نیازمند کشف: ابتدا لید یا جامعه بساز، سپس پیشنهاد کم‌ریسک تست کن';
}

function inferResources(entity, metrics) {
  const resources = ['تقویم آزمایش ۳۰ روزه', 'داشبورد ساده برای views/ER/actions', 'بانک هوک و کامنت'];
  const formats = new Set(entity.content.map((c) => c.format));
  if (formats.has('short_video')) resources.push('قالب ضبط ویدئوی کوتاه + کپشن استاندارد');
  if (entity.content.some((c) => c.proof_type)) resources.push('مخزن شواهد: اسکرین‌شات، داده، before/after');
  if (entity.content.some((c) => c.cta === 'download')) resources.push('لیدمگنت یا چک‌لیست قابل دانلود');
  return resources;
}

function buildMechanismFormula(entity, metrics) {
  const topHook = labelHook(metrics.hook_types?.[0]?.value);
  const topic = metrics.topics?.[0]?.value || entity.niche;
  const emotion = labelEmotion(metrics.emotions?.[0]?.value);
  const cta = metrics.ctas?.[0]?.value || 'comment';
  return [
    `مسئله/موضوع: ${topic}`,
    `شروع: ${topHook}`,
    `محرک: ${emotion}`,
    'بدنه: نمایش تجربه، ساده‌سازی یا اثبات',
    `حلقه بازخورد: ${cta}`,
    'بازسازی: تبدیل محتوای برنده به سری، همکاری یا پیشنهاد تجاری',
  ];
}

function extractObservedFacts(entity, metrics) {
  const facts = [
    `${metrics.content_count} محتوای نمونه تحلیل شد`,
    `${metrics.evidence_count} شاهد با میانگین اطمینان ${metrics.evidence_confidence}`,
    `میانه نرخ تعامل: ${round(metrics.median_engagement_rate * 100, 2)}٪`,
    `میانه نسبت بازدید به فالوئر: ${metrics.median_view_follower_ratio}`,
  ];
  if (metrics.follower_growth_rate != null) facts.push(`رشد فالوئر در بازه داده‌شده: ${round(metrics.follower_growth_rate * 100, 2)}٪`);
  if (metrics.breakthrough_items) facts.push(`${metrics.breakthrough_items} محتوای جهشی نسبت به میانه دیده شد`);
  return facts;
}

function extractInterpretations(entity, metrics, scores) {
  const interpretations = [];
  if (scores.replicability >= 0.65) interpretations.push('معماری نسبتاً قابل‌انتقال است، چون چند محتوای نمونه و الگوی تکرارشونده دارد.');
  else interpretations.push('قابلیت انتقال محدود است؛ باید با آزمایش کوچک و کنترل ریسک اجرا شود.');
  if (scores.authenticity >= 0.65) interpretations.push('اعتماد از مسیر نمایش، داده یا تجربه واقعی ساخته شده است.');
  if (scores.conversion < 0.35) interpretations.push('مسیر تبدیل هنوز ضعیف یا کم‌شاهد است؛ قبل از کپی‌برداری باید offer روشن شود.');
  if (scores.engagement >= 0.65) interpretations.push('تعامل فقط view نیست؛ نشانه‌هایی از action مثل کامنت/ذخیره/اشتراک وجود دارد.');
  return interpretations;
}

function buildRecommendations(entity, metrics, scores, settings) {
  const audience = settings.target_audience || entity.audience_problem || 'مخاطب هدف';
  const product = settings.product || 'پیشنهاد آزمایشی';
  const topHook = metrics.hook_types?.[0]?.value || 'problem';
  const hookLabel = labelHook(topHook);
  return [
    `برای ${audience} یک سری ۷ قسمتی با شروع «${hookLabel}» بساز.`,
    `هر محتوا را به یک مسئله کوچک وصل کن و در پایان یک CTA قابل‌اندازه‌گیری بده.`,
    `برای ${product} فقط بعد از ۳ محتوای اثباتی CTA نرم بگذار.`,
    'اگر محتوا view گرفت ولی save/comment نگرفت، هوک را نگه دار اما بدنه را کاربردی‌تر کن.',
  ];
}

export function buildArchitectureCard(scored, settings = {}) {
  const { entity, metrics, scores, warnings } = scored;
  const architectureId = stableId('arch', entity.entity_id, entity.name, entity.niche);
  return {
    schema_version: 'strategy-card.v1',
    architecture_id: architectureId,
    entity_id: entity.entity_id,
    creator: {
      name: entity.name,
      handle: entity.handle,
      entity_type: entity.entity_type,
      primary_platform: entity.primary_platform,
      niche: entity.niche,
      country: entity.country,
    },
    scores,
    positioning: inferPositioning(entity, metrics),
    audience_problem: entity.audience_problem || settings.target_audience || 'نامشخص؛ باید در تحقیق تکمیل شود',
    content_engine: {
      pillars: inferContentPillars(entity, metrics),
      hook_patterns: (metrics.hook_types || []).map((h) => ({ type: h.value, label: labelHook(h.value), count: h.count })),
      dominant_emotions: (metrics.emotions || []).map((e) => ({ type: e.value, label: labelEmotion(e.value), count: e.count })),
      narrative_structure: inferNarrativeStructure(entity, metrics),
      publishing_cadence: inferCadence(entity),
      platform_strategy: inferPlatformStrategy(entity, metrics),
    },
    growth_loop: {
      formula: buildMechanismFormula(entity, metrics),
      community_loop: inferCommunityLoop(entity, metrics),
      conversion_path: inferConversionPath(entity, metrics),
      monetization_model: inferMonetization(entity),
    },
    required_resources: inferResources(entity, metrics),
    evidence: {
      observed_facts: extractObservedFacts(entity, metrics),
      interpretations: extractInterpretations(entity, metrics, scores),
      evidence_ids: entity.evidence.map((ev) => ev.id),
      evidence_quality: metrics.evidence_confidence,
      sample_content_ids: entity.content.map((c) => c.id),
    },
    recommendations: buildRecommendations(entity, metrics, scores, settings),
    risks: warnings,
    confidence: round((scores.total * 0.65) + (metrics.evidence_confidence * 0.35)),
  };
}

export function clusterArchitectures(cards) {
  const groups = new Map();
  for (const card of cards) {
    const hook = card.content_engine.hook_patterns[0]?.type || 'other';
    const conversion = card.growth_loop.conversion_path.at(-1) || 'unknown';
    const key = `${hook}::${conversion}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(card);
  }
  return [...groups.entries()].map(([key, items]) => {
    const [hook, conversion] = key.split('::');
    return {
      cluster_id: stableId('cluster', key),
      hook_type: hook,
      terminal_conversion_step: conversion,
      entities: items.map((i) => i.entity_id),
      avg_score: round(items.reduce((a, b) => a + b.scores.total, 0) / items.length),
      common_pillars: topCounts(items.flatMap((i) => i.content_engine.pillars), 5),
    };
  }).sort((a, b) => b.avg_score - a.avg_score);
}
