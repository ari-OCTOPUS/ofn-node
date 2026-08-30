import type { ConsentScope, Sensitivity } from '@wlos/shared';

/** Question-bank schema — versioned in code, synced to DB as needed. */

export type QuestionDomain =
  | 'weight_history' // A
  | 'motivation_values' // B
  | 'self_efficacy' // C
  | 'dieting_beliefs' // D
  | 'hunger_cravings' // E
  | 'emotional_context' // F (psychology consent)
  | 'environment' // G
  | 'exercise_psychology' // H
  | 'sleep_recovery' // I
  | 'social_cultural' // J
  | 'cannabis' // K (cannabis consent)
  | 'relapse_recovery' // L
  | 'interaction_prefs'; // M

export type ResponseType = 'scale_0_10' | 'yes_no' | 'choice' | 'free_text' | 'number' | 'done_notyet';

export type QuestionContext = 'onboarding' | 'checkin' | 'weekly_review' | 'chat';

export type Contraindication =
  | 'crisis_mode'
  | 'recent_lapse' // don't probe beliefs right after a hard day
  | 'low_mood_today'
  | 'user_overwhelmed'
  | 'late_evening'; // no heavy questions near sleep

export interface Question {
  id: string; // e.g. "E-012"
  domain: QuestionDomain;
  fa: string; // Persian text (may embed English terms naturally)
  en: string; // English reference translation
  responseType: ResponseType;
  choicesFa?: string[];
  sensitivity: Sensitivity;
  burden: 1 | 2 | 3 | 4 | 5;
  infoGain: 1 | 2 | 3 | 4 | 5;
  consentScope: ConsentScope | null; // null = core; psychology/cannabis gated
  cooldownDays: number; // min days before re-asking
  prerequisites: string[]; // question ids answered first
  allowedContexts: QuestionContext[];
  contraindications: Contraindication[];
  followupIds: string[];
  neverInNotificationPreview: boolean; // envelope+reveal flow required
}

export interface AskHistoryEntry {
  questionId: string;
  askedDayKey: string; // local day
  answered: boolean;
  refusedPermanently?: boolean; // "don't ask this again"
}

export interface SelectionState {
  todayKey: string;
  context: QuestionContext;
  consents: Partial<Record<ConsentScope, boolean>>;
  history: AskHistoryEntry[];
  activeContraindications: Contraindication[];
  answeredIds: Set<string>; // ever answered (for prerequisites & dedupe)
  /** topic hint from the scheduler slot, biases domain choice */
  topicHint?: string;
}
