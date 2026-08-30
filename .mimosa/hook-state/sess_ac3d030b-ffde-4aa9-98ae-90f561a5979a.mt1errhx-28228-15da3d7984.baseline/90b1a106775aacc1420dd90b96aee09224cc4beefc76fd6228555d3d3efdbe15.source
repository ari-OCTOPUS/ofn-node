import { searchKey } from '@wlos/shared';
import type { SafetyLevel } from '@wlos/shared';

/**
 * Deterministic first-pass triage. Runs BEFORE any LLM sees user text and
 * BEFORE any coaching reply is composed. Persian + English keyword/regex.
 *
 * Design bias: sensitive-by-default. A false positive costs one caring
 * message; a false negative can cost far more. User can always /resume.
 */

export type SafetyCategory =
  | 'self_harm'
  | 'eating_disorder'
  | 'chest_pain'
  | 'breathing'
  | 'fainting'
  | 'severe_dizziness'
  | 'neurological'
  | 'pregnancy'
  | 'medication'
  | 'substance_help'
  | 'sleep_apnea'
  | 'mood_crisis';

export interface SafetyVerdict {
  level: SafetyLevel;
  categories: SafetyCategory[];
  matched: string[]; // for safety_events audit — NOT for user display
}

interface Rule {
  category: SafetyCategory;
  level: SafetyLevel;
  patterns: RegExp[];
}

// NOTE: matching runs on searchKey(text): digit-unified, fa-normalized, lowercased, ZWNJ→space.
const RULES: Rule[] = [
  {
    category: 'self_harm',
    level: 'crisis',
    patterns: [
      /خودکشی/, /به خودم اسیب|به خودم آسیب/, /نمی ?خوام زنده/, /زنده بودن خسته|از زندگی خسته/,
      /تمومش کنم|تمامش کنم/, /خودمو بکشم|خودم را بکشم/,
      /\bsuicid/i, /\bkill myself\b/i, /\bself[- ]?harm\b/i, /\bend my life\b/i, /\bwant to die\b/i,
      /\bhurt myself\b/i,
    ],
  },
  {
    category: 'mood_crisis',
    level: 'crisis',
    patterns: [/دیگه هیچ امیدی|هیچ امیدی ندارم/, /\bno reason to live\b/i, /\bhopeless and done\b/i],
  },
  {
    category: 'eating_disorder',
    level: 'urgent_medical',
    patterns: [
      /استفراغ عمدی|بالا میارم عمدا|بالا اوردم که/, /ملین (?:خوردم|می ?خورم) برای وزن/,
      /(?:دو|سه|چهار|پنج|شش|چند|\d+)\s*روزه?\s*(?:است که\s*)?هیچی نخوردم/, /قصد دارم چند روز نخورم/,
      /\bpurg(e|ing)\b/i, /\blaxative/i,
      /\bhaven'?t eaten in \d+ days\b/i, /\bstarv(e|ing) myself\b/i, /جبران با ورزش شدید/,
    ],
  },
  {
    category: 'chest_pain',
    level: 'urgent_medical',
    patterns: [/درد قفسه سینه|قفسه سینه ام درد/, /\bchest pain\b/i, /\bchest pressure\b/i, /فشار روی قفسه/],
  },
  {
    category: 'breathing',
    level: 'urgent_medical',
    patterns: [/نفسم بالا نمیاد|تنگی نفس شدید/, /\bcan'?t breathe\b/i, /\bshort(ness)? of breath\b/i],
  },
  {
    category: 'fainting',
    level: 'urgent_medical',
    patterns: [/غش کردم|از حال رفتم|بیهوش شدم/, /\bfaint(ed|ing)?\b/i, /\bpassed out\b/i, /\bblack(ed)? out\b/i],
  },
  {
    category: 'severe_dizziness',
    level: 'urgent_medical',
    patterns: [/سرگیجه شدید|سرم گیج میره شدید/, /\bsevere dizz/i, /\broom (is )?spinning\b/i],
  },
  {
    category: 'neurological',
    level: 'urgent_medical',
    patterns: [/نصف بدنم بی حس|بی حسی یک طرف/, /\bnumb(ness)? on one side\b/i, /\bslurred speech\b/i, /تار می ?بینم ناگهانی/],
  },
  {
    category: 'pregnancy',
    level: 'caution',
    patterns: [/باردارم|حامله ام|شیر می ?دم به بچه|شیردهی/, /\bpregnan/i, /\bbreastfeed/i],
  },
  {
    category: 'medication',
    level: 'caution',
    patterns: [/داروم رو (?:قطع|کم|زیاد) کنم/, /\bstop (taking )?my med/i, /\bchange my dose\b/i, /دوز دارو/],
  },
  {
    category: 'substance_help',
    level: 'caution',
    patterns: [/نمی ?تونم (?:گل|علف|ماریجوانا) رو کنار بذارم|کمکم کن ترک کنم/, /\bcan'?t stop (using|smoking)\b/i, /\bhelp me quit\b/i],
  },
  {
    category: 'sleep_apnea',
    level: 'caution',
    patterns: [/خروپف شدید و نفسم قطع|نفسم تو خواب قطع/, /\bstop breathing (in|during) (my )?sleep\b/i, /\bapnea\b/i],
  },
];

const LEVEL_ORDER: Record<SafetyLevel, number> = { none: 0, caution: 1, urgent_medical: 2, crisis: 3 };

export function triageInbound(rawText: string): SafetyVerdict {
  const text = searchKey(rawText);
  const categories = new Set<SafetyCategory>();
  const matched: string[] = [];
  let level: SafetyLevel = 'none';

  for (const rule of RULES) {
    for (const re of rule.patterns) {
      if (re.test(text)) {
        categories.add(rule.category);
        matched.push(`${rule.category}:${re.source.slice(0, 40)}`);
        if (LEVEL_ORDER[rule.level] > LEVEL_ORDER[level]) level = rule.level;
        break;
      }
    }
  }
  return { level, categories: [...categories], matched };
}
