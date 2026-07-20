import { localDayKey, searchKey, type ConsentScope, type MessageKind } from '@wlos/shared';
import type { PrismaClient } from './client.js';

/**
 * Repository layer — every DB access the bot/agents need for the vertical
 * slice. Keeps Prisma out of handlers so logic stays unit-testable.
 */
export class WlosRepos {
  constructor(
    private prisma: PrismaClient,
    private tz = 'Australia/Sydney',
  ) {}

  // ── users ──────────────────────────────────────────────────────────────
  async getOrCreateUserByChat(chatId: bigint, username?: string, displayName = 'دوست من') {
    const existing = await this.prisma.telegramAccount.findUnique({
      where: { chatId },
      include: { user: { include: { profile: true, notificationPref: true } } },
    });
    if (existing) return existing.user;
    const user = await this.prisma.user.create({
      data: {
        displayName,
        telegramAccounts: { create: { chatId, username: username ?? null } },
        profile: { create: {} },
        notificationPref: { create: {} },
        consents: {
          create: (['core_health', 'psychology', 'cannabis', 'coach_sharing'] as const).map((scope) => ({
            scope,
            granted: scope === 'core_health', // core on; everything sensitive OFF by default
          })),
        },
      },
      include: { profile: true, notificationPref: true },
    });
    await this.audit(user.id, 'user', 'user_created', `chat ${chatId}`);
    return user;
  }

  async getUserByChat(chatId: bigint) {
    const acc = await this.prisma.telegramAccount.findUnique({
      where: { chatId },
      include: { user: { include: { profile: true, notificationPref: true, consents: true } } },
    });
    return acc?.user ?? null;
  }

  // ── consent ────────────────────────────────────────────────────────────
  async setConsent(userId: string, scope: ConsentScope, granted: boolean, source = 'telegram') {
    await this.prisma.consent.upsert({
      where: { userId_scope: { userId, scope } },
      create: { userId, scope, granted },
      update: { granted },
    });
    await this.prisma.consentEvent.create({ data: { userId, scope, granted, source } });
  }

  async hasConsent(userId: string, scope: ConsentScope): Promise<boolean> {
    const c = await this.prisma.consent.findUnique({ where: { userId_scope: { userId, scope } } });
    return c?.granted === true;
  }

  async consentMap(userId: string): Promise<Partial<Record<ConsentScope, boolean>>> {
    const rows = await this.prisma.consent.findMany({ where: { userId } });
    return Object.fromEntries(rows.map((r) => [r.scope, r.granted]));
  }

  // ── logging ────────────────────────────────────────────────────────────
  async logWeight(userId: string, kg: number, at = new Date()) {
    const dayKey = localDayKey(at, this.tz);
    return this.prisma.weight.create({
      data: { userId, kg, occurredAt: at, dayKey },
    });
  }

  async recentWeights(userId: string, days = 42) {
    const rows = await this.prisma.weight.findMany({
      where: { userId, deletedAt: null },
      orderBy: { dayKey: 'desc' },
      take: days * 2,
    });
    // one per day (latest wins), ascending
    const byDay = new Map<string, number>();
    for (const r of rows) if (!byDay.has(r.dayKey)) byDay.set(r.dayKey, r.kg);
    return [...byDay.entries()]
      .map(([dayKey, value]) => ({ dayKey, value }))
      .sort((a, b) => (a.dayKey < b.dayKey ? -1 : 1));
  }

  async logMeal(
    userId: string,
    meal: { name: string; calories: number; proteinG?: number; carbsG?: number; fatG?: number; confirmedHigh?: boolean },
    at = new Date(),
  ) {
    const dayKey = localDayKey(at, this.tz);
    const created = await this.prisma.meal.create({
      data: {
        userId,
        occurredAt: at,
        dayKey,
        nameRaw: meal.name,
        nameKey: searchKey(meal.name),
        calories: meal.calories,
        proteinG: meal.proteinG ?? null,
        carbsG: meal.carbsG ?? null,
        fatG: meal.fatG ?? null,
        confirmedHigh: meal.confirmedHigh ?? false,
      },
    });
    await this.recomputeDay(userId, dayKey);
    return created;
  }

  async recomputeDay(userId: string, dayKey: string) {
    const meals = await this.prisma.meal.findMany({ where: { userId, dayKey, deletedAt: null } });
    const totalCalories = meals.reduce((s, m) => s + m.calories, 0);
    const totalProteinG = meals.reduce((s, m) => s + (m.proteinG ?? 0), 0);
    const target = await this.prisma.nutritionTarget.findFirst({
      where: { userId },
      orderBy: { effectiveFrom: 'desc' },
    });
    await this.prisma.nutritionDailySummary.upsert({
      where: { userId_dayKey: { userId, dayKey } },
      create: {
        userId,
        dayKey,
        totalCalories,
        totalProteinG,
        mealsLogged: meals.length,
        targetLow: target?.kcalLow ?? null,
        targetHigh: target?.kcalHigh ?? null,
        withinTarget: target ? totalCalories >= target.kcalLow && totalCalories <= target.kcalHigh : null,
      },
      update: {
        totalCalories,
        totalProteinG,
        mealsLogged: meals.length,
        withinTarget: target ? totalCalories >= target.kcalLow && totalCalories <= target.kcalHigh : null,
      },
    });
    return { totalCalories, totalProteinG, mealsLogged: meals.length };
  }

  async logState(userId: string, kind: string, value: number, source = 'checkin', at = new Date()) {
    return this.prisma.stateLog.create({
      data: { userId, kind, value, occurredAt: at, dayKey: localDayKey(at, this.tz), source },
    });
  }

  async logWorkout(
    userId: string,
    w: { kind: string; title: string; durationMin?: number; rpe?: number; note?: string },
    at = new Date(),
  ) {
    return this.prisma.workout.create({
      data: {
        userId,
        occurredAt: at,
        dayKey: localDayKey(at, this.tz),
        kind: w.kind,
        title: w.title,
        durationMin: w.durationMin ?? null,
        rpe: w.rpe ?? null,
        note: w.note ?? null,
      },
    });
  }

  // ── outbound ledger (cap enforcement) ─────────────────────────────────
  async countOutboundToday(userId: string, now = new Date()): Promise<number> {
    return this.prisma.outboundMessage.count({
      where: { userId, dayKey: localDayKey(now, this.tz) },
    });
  }

  async recordOutbound(userId: string, kind: MessageKind, sensitivity: string, preview: string, bypassedCap: boolean) {
    return this.prisma.outboundMessage.create({
      data: {
        userId,
        dayKey: localDayKey(new Date(), this.tz),
        kind,
        sensitivity,
        preview: preview.slice(0, 120),
        bypassedCap,
      },
    });
  }

  // ── telegram idempotency ───────────────────────────────────────────────
  /** Returns true when this update was already processed. */
  async markUpdateProcessed(updateId: bigint): Promise<boolean> {
    try {
      await this.prisma.processedUpdate.create({ data: { updateId } });
      return false;
    } catch {
      return true; // unique violation → duplicate
    }
  }

  // ── safety ─────────────────────────────────────────────────────────────
  async recordSafetyEvent(
    userId: string,
    direction: 'inbound' | 'outbound',
    level: string,
    categories: string[],
    action: string,
  ) {
    return this.prisma.safetyEvent.create({
      data: { userId, direction, level, categories: categories.join(','), action },
    });
  }

  async setCrisisMode(userId: string, until: Date | null) {
    await this.prisma.user.update({ where: { id: userId }, data: { crisisModeUntil: until } });
  }

  // ── export / deletion ──────────────────────────────────────────────────
  async exportAll(userId: string): Promise<Record<string, unknown>> {
    const [user, weights, meals, workouts, states, checkins, patterns, consents, cannabis, reports] =
      await Promise.all([
        this.prisma.user.findUnique({ where: { id: userId }, include: { profile: true, notificationPref: true } }),
        this.prisma.weight.findMany({ where: { userId } }),
        this.prisma.meal.findMany({ where: { userId } }),
        this.prisma.workout.findMany({ where: { userId }, include: { sets: true } }),
        this.prisma.stateLog.findMany({ where: { userId } }),
        this.prisma.checkinInstance.findMany({ where: { userId }, include: { responses: true } }),
        this.prisma.pattern.findMany({ where: { userId }, include: { evidence: true, corrections: true } }),
        this.prisma.consentEvent.findMany({ where: { userId } }),
        this.prisma.cannabisEvent.findMany({ where: { userId } }),
        this.prisma.report.findMany({ where: { userId } }),
      ]);
    return {
      exportedAt: new Date().toISOString(),
      format: 'wlos-export-v1',
      user,
      weights,
      meals,
      workouts,
      states,
      checkins,
      patterns,
      consents,
      cannabis,
      reports,
    };
  }

  async requestDeletion(userId: string) {
    return this.prisma.deletionRequest.create({ data: { userId } });
  }

  async confirmDeletion(userId: string) {
    const req = await this.prisma.deletionRequest.findFirst({
      where: { userId, status: 'awaiting_confirmation' },
      orderBy: { requestedAt: 'desc' },
    });
    if (!req) return null;
    await this.prisma.deletionRequest.update({
      where: { id: req.id },
      data: { status: 'confirmed', confirmedAt: new Date() },
    });
    // hard purge — user owns their data; cascade wipes children
    await this.prisma.user.delete({ where: { id: userId } });
    return req.id;
  }

  // ── misc ───────────────────────────────────────────────────────────────
  async audit(userId: string | null, actor: string, action: string, detail?: string) {
    await this.prisma.auditLog.create({ data: { userId, actor, action, detail: detail ?? null } });
  }

  get db(): PrismaClient {
    return this.prisma;
  }
}
