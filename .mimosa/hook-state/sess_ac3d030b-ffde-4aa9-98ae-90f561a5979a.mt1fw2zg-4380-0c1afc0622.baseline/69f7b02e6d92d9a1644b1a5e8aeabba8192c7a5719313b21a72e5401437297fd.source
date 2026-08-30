/** Shared domain types. DB is source of truth; these mirror prisma enums. */

export type ConsentScope =
  | 'core_health' // weight/meals/workouts/sleep — required for the product to function
  | 'psychology' // behavioral/emotional pattern questions & storage
  | 'cannabis' // cannabis-aware personalization
  | 'coach_sharing'; // include data in coach-ready report

export type MessageKind =
  | 'safety' // bypasses cap & quiet hours
  | 'checkin'
  | 'coach' // plans, feedback, reports
  | 'reply' // direct response to a user-initiated message
  | 'system'; // consent/privacy/etc.

export type Sensitivity = 'low' | 'medium' | 'high';

export type CheckinStatus = 'scheduled' | 'sent' | 'answered' | 'ignored' | 'cancelled' | 'snoozed';

export type PatternConfidence = 'hypothesis' | 'low' | 'medium' | 'high';

export type PlateauStatus =
  | 'unconfirmed'
  | 'data_insufficient'
  | 'likely_true_plateau'
  | 'likely_adherence_or_measurement_issue'
  | 'likely_water_weight_masking'
  | 'medical_review_recommended';

export type SafetyLevel = 'none' | 'caution' | 'urgent_medical' | 'crisis';

export interface QuietHours {
  start: string; // "HH:MM" local
  end: string; // "HH:MM" local
}

export interface NotificationPrefs {
  timezone: string;
  dailyCap: number; // hard cap (default 20)
  targetCheckinsMin: number; // default 3
  targetCheckinsMax: number; // default 6
  minGapMinutes: number; // default 120
  quietHours: QuietHours; // default 00:00–07:00
  quietHoursSuspended: boolean; // /nosleep
  paused: boolean;
  snoozedUntil: Date | null;
  backoffMultiplier: number; // 1.0 normal; 0.5 after 2 ignored
  ignoredStreak: number;
}

export const DEFAULT_NOTIFICATION_PREFS: NotificationPrefs = {
  timezone: 'Australia/Sydney',
  dailyCap: 20,
  targetCheckinsMin: 3,
  targetCheckinsMax: 6,
  minGapMinutes: 120,
  quietHours: { start: '00:00', end: '07:00' },
  quietHoursSuspended: false,
  paused: false,
  snoozedUntil: null,
  backoffMultiplier: 1.0,
  ignoredStreak: 0,
};

export interface EvidenceBacked {
  evidenceCount: number;
  counterexampleCount: number;
  confidence: PatternConfidence;
  notCausal: true;
  firstSeenAt: Date;
  lastSeenAt: Date;
}
