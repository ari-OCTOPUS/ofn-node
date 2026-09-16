import { round, stableId } from './utils.js';

function hookTemplate(hookType, topic, audience) {
  switch (hookType) {
    case 'contrarian':
      return `برخلاف چیزی که درباره ${topic} شنیده‌ای، مشکل اصلی برای ${audience} این نیست...`;
    case 'question':
      return `اگر ${audience} هستی، چرا ${topic} هنوز نتیجه نمی‌دهد؟`;
    case 'demo':
      return `در ۳۰ ثانیه نشان می‌دهم ${topic} واقعاً چطور کار می‌کند.`;
    case 'story':
      return `این اشتباه واقعی من در ${topic} بود و این‌طور اصلاحش کردم.`;
    case 'proof':
      return `با داده/نمونه نشان می‌دهم کدام بخش ${topic} جواب داده است.`;
    case 'curiosity':
      return `یک جزئیات کوچک در ${topic} باعث شد نتیجه عوض شود...`;
    case 'problem':
    default:
      return `اگر در ${topic} گیر کردی، این سه نشانه را بررسی کن.`;
  }
}

function metricDecisionRule(goal) {
  if (goal === 'conversion') return 'اگر CTR یا ثبت‌نام نسبت به baseline حداقل ۲۰٪ بهتر شد و نرخ کامنت افت شدید نداشت، ادامه بده.';
  if (goal === 'trust') return 'اگر save/share/comment معنادار حداقل ۱۵٪ بهتر شد، قالب را به سری تبدیل کن.';
  return 'اگر retention proxy یعنی save+comment/view حداقل ۱۵٪ بهتر شد، نسخه برنده را گسترش بده.';
}

export function createExperimentPlan(cards, settings = {}) {
  const audience = settings.target_audience || 'مخاطب هدف';
  const product = settings.product || 'پیشنهاد/محصول';
  const market = settings.target_market || 'بازار هدف';
  const topCards = cards.slice(0, Math.min(5, cards.length));
  return topCards.map((card, idx) => {
    const hookType = card.content_engine.hook_patterns[0]?.type || 'problem';
    const topic = card.content_engine.pillars[0] || settings.target_niche || card.creator.niche;
    const goal = card.scores.conversion >= 0.45 ? 'conversion' : (card.scores.authenticity >= 0.55 ? 'trust' : 'discovery');
    const experimentId = stableId('exp', card.architecture_id, hookType, topic, idx);
    return {
      schema_version: 'experiment-plan.v1',
      experiment_id: experimentId,
      based_on_architecture_id: card.architecture_id,
      title: `آزمایش ${idx + 1}: ${topic} با هوک ${hookType}`,
      market,
      hypothesis: `اگر معماری «${card.positioning}» را برای ${audience} بازنویسی کنیم، نرخ اقدام برای ${product} بهتر از baseline می‌شود.`,
      variants: [
        {
          name: 'A_control_problem_solution',
          hook: hookTemplate('problem', topic, audience),
          structure: ['مسئله', 'توضیح کوتاه', 'یک مثال', 'CTA کامنت/ذخیره'],
          cta: 'comment/save',
        },
        {
          name: `B_architecture_${hookType}`,
          hook: hookTemplate(hookType, topic, audience),
          structure: card.growth_loop.formula,
          cta: card.growth_loop.conversion_path.includes('دانلود ابزار/چک‌لیست') ? 'download' : 'join/comment',
        },
      ],
      schedule: {
        duration_days: 7,
        minimum_posts: 4,
        cadence: 'یک روز در میان؛ نسخه برنده در روزهای ۶ و ۷ تکرار شود',
      },
      success_metrics: [
        'views_from_non_followers',
        'engagement_rate',
        'save_share_comment_rate',
        goal === 'conversion' ? 'click_or_signup_rate' : 'qualified_comment_count',
      ],
      guardrails: [
        'کپی متن، تصویر، ادعا یا شخصیت سازنده ممنوع است؛ فقط مکانیزم بازسازی شود.',
        'هر ادعای عددی باید evidence_id یا منبع داخلی داشته باشد.',
        'انتشار نهایی و پاسخ عمومی به کامنت‌ها نیازمند تأیید انسانی است.',
      ],
      decision_rule: metricDecisionRule(goal),
      priority: round(card.scores.total * 0.7 + card.confidence * 0.3),
    };
  }).sort((a, b) => b.priority - a.priority);
}

export function createThirtyDayRoadmap(experiments) {
  const weeks = [
    { week: 1, focus: 'baseline و تست هوک', experiments: [] },
    { week: 2, focus: 'تکرار قالب برنده و سری‌سازی', experiments: [] },
    { week: 3, focus: 'اعتماد و اثبات با نمونه/داده', experiments: [] },
    { week: 4, focus: 'CTA نرم و مسیر تبدیل', experiments: [] },
  ];
  experiments.forEach((exp, idx) => {
    weeks[idx % weeks.length].experiments.push(exp.experiment_id);
  });
  return {
    schema_version: '30-day-roadmap.v1',
    weeks,
    operating_loop: [
      'هر روز: ثبت views، ER، saves/shares/comments و هزینه تولید',
      'هر ۳ روز: انتخاب یک کامنت/سؤال برای محتوای پاسخ',
      'هر هفته: توقف ۳۰٪ ضعیف، تکرار ۲۰٪ قوی، ساخت یک offer سبک',
      'روز ۳۰: تصمیم scale / pivot / stop بر اساس تبدیل و اعتماد، نه فقط بازدید',
    ],
  };
}
