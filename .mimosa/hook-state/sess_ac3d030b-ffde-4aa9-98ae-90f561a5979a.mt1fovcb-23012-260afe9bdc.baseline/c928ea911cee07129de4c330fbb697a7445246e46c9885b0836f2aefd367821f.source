import { InlineKeyboard } from 'grammy';
import { clearOutbound } from '@wlos/safety';
import { QUESTION_BANK, selectQuestion, type SelectionState } from '@wlos/behavior-engine';
import { planDay, shouldStillSend } from '@wlos/jitai-engine';
import { fa, localDayKey, mulberry32, seedFromString, type NotificationPrefs } from '@wlos/shared';
import type { WlosRepos } from '@wlos/memory';
import { sendViaOutbox, type OutboxDeps } from './outbox.js';

/**
 * Check-in pipeline: plan (daily) → dispatch (per instance, re-evaluated).
 * One question per message — always.
 */

export async function planUserDay(repos: WlosRepos, userId: string, dayKey: string): Promise<number> {
  const pref = await repos.db.notificationPreference.findUnique({ where: { userId } });
  if (!pref || pref.paused) return 0;

  // idempotency: a day is planned at most once (double-run of the planner,
  // worker restarts, manual triggers — none may duplicate check-ins)
  const existing = await repos.db.checkinInstance.count({ where: { userId, dayKey } });
  if (existing > 0) return 0;

  const prefs: NotificationPrefs = {
    timezone: pref.timezone,
    dailyCap: pref.dailyCap,
    targetCheckinsMin: pref.targetCheckinsMin,
    targetCheckinsMax: pref.targetCheckinsMax,
    minGapMinutes: pref.minGapMinutes,
    quietHours: { start: pref.quietStart, end: pref.quietEnd },
    quietHoursSuspended: pref.quietSuspended,
    paused: pref.paused,
    snoozedUntil: pref.snoozedUntil,
    backoffMultiplier: pref.backoffMultiplier,
    ignoredStreak: pref.ignoredStreak,
  };

  const rng = mulberry32(seedFromString(`${userId}:${dayKey}`));
  const plan = planDay(dayKey, prefs, {}, rng);

  for (const p of plan) {
    await repos.db.checkinInstance.create({
      data: {
        userId,
        dayKey,
        slotKey: p.slotKey,
        topic: p.topic,
        scheduledAt: p.fireAtUtc,
        status: 'scheduled',
      },
    });
  }
  return plan.length;
}

/** Dispatch one scheduled instance if it still makes sense. */
export async function dispatchCheckin(deps: OutboxDeps, repos: WlosRepos, instanceId: string): Promise<'sent' | 'cancelled'> {
  const instance = await repos.db.checkinInstance.findUnique({ where: { id: instanceId } });
  if (!instance || instance.status !== 'scheduled') return 'cancelled';

  const user = await repos.db.user.findUnique({
    where: { id: instance.userId },
    include: { notificationPref: true, telegramAccounts: true },
  });
  const pref = user?.notificationPref;
  const chat = user?.telegramAccounts[0];
  if (!user || !pref || !chat) return cancel('no_user');

  const now = new Date();
  const sentToday = await repos.countOutboundToday(user.id, now);

  if (pref.stopForDayKey === instance.dayKey) return cancel('stop_today');

  const decision = shouldStillSend({
    paused: pref.paused,
    snoozedUntil: pref.snoozedUntil,
    crisisModeActive: Boolean(user.crisisModeUntil && now < user.crisisModeUntil),
    sentToday,
    dailyCap: pref.dailyCap,
    now,
    tz: pref.timezone,
    quietStart: pref.quietStart,
    quietEnd: pref.quietEnd,
    quietSuspended: pref.quietSuspended,
  });
  if (!decision.send) return cancel(decision.reason);

  // pick ONE question, consent- and history-aware
  const consents = await repos.consentMap(user.id);
  const history = await repos.db.checkinInstance.findMany({
    where: { userId: user.id, questionId: { not: null } },
    orderBy: { scheduledAt: 'desc' },
    take: 200,
  });
  const answered = new Set(
    history.filter((h) => h.status === 'answered' && h.questionId).map((h) => h.questionId!) ,
  );
  const state: SelectionState = {
    todayKey: instance.dayKey,
    context: 'checkin',
    consents,
    history: history.map((h) => ({
      questionId: h.questionId!,
      askedDayKey: h.dayKey,
      answered: h.status === 'answered',
    })),
    activeContraindications: user.crisisModeUntil && now < user.crisisModeUntil ? ['crisis_mode'] : [],
    answeredIds: answered,
    topicHint: instance.topic,
  };
  const rng = mulberry32(seedFromString(`${user.id}:${instance.id}`));
  const selected = selectQuestion(QUESTION_BANK, state, rng);
  if (!selected) return cancel('no_eligible_question');

  const q = selected.question;
  const kb = new InlineKeyboard();
  if (q.responseType === 'scale_0_10') {
    kb.text(fa.BTN_SCALE_LOW, `ci:${instance.id}:low`)
      .text(fa.BTN_SCALE_MID, `ci:${instance.id}:mid`)
      .text(fa.BTN_SCALE_HIGH, `ci:${instance.id}:high`);
  } else if (q.responseType === 'yes_no') {
    kb.text(fa.BTN_YES, `ci:${instance.id}:yes`).text(fa.BTN_NO, `ci:${instance.id}:no`);
  } else if (q.responseType === 'done_notyet') {
    kb.text(fa.BTN_DONE, `ci:${instance.id}:yes`).text(fa.BTN_NOT_YET, `ci:${instance.id}:no`);
  } else if (q.responseType === 'choice' && q.choicesFa) {
    q.choicesFa.slice(0, 3).forEach((choice, i) => kb.text(choice, `ci:${instance.id}:c${i}`));
  }
  kb.row()
    .text(fa.BTN_SKIP, `ci:${instance.id}:skip`)
    .text(fa.BTN_SNOOZE, `ci:${instance.id}:snooze`)
    .text(fa.BTN_STOP_TODAY, `ci:${instance.id}:stopday`);

  const sensitivity = q.neverInNotificationPreview ? 'high' : q.sensitivity === 'high' ? 'high' : 'low';
  const result = await sendViaOutbox(deps, {
    userId: user.id,
    chatId: chat.chatId,
    kind: 'checkin',
    sensitivity,
    clearance: clearOutbound(q.fa),
    keyboard: { inline_keyboard: kb.inline_keyboard },
  });

  if (!result.sent) return cancel(result.reason);

  await repos.db.checkinInstance.update({
    where: { id: instance.id },
    data: { status: 'sent', sentAt: now, questionId: q.id },
  });
  return 'sent';

  async function cancel(reason: string): Promise<'cancelled'> {
    await repos.db.checkinInstance.update({
      where: { id: instanceId },
      data: { status: 'cancelled', cancelReason: reason },
    });
    return 'cancelled';
  }
}

/** Mark yesterday's unanswered sent check-ins as ignored + apply backoff. */
export async function sweepIgnored(repos: WlosRepos, userId: string, todayKey: string): Promise<void> {
  const stale = await repos.db.checkinInstance.findMany({
    where: { userId, status: 'sent', dayKey: { lt: todayKey } },
  });
  if (!stale.length) return;
  await repos.db.checkinInstance.updateMany({
    where: { id: { in: stale.map((s) => s.id) } },
    data: { status: 'ignored' },
  });
  const pref = await repos.db.notificationPreference.findUnique({ where: { userId } });
  if (!pref) return;
  let streak = pref.ignoredStreak;
  let multiplier = pref.backoffMultiplier;
  for (let i = 0; i < stale.length; i++) {
    streak += 1;
    if (streak >= 2) multiplier = Math.max(0.25, multiplier * 0.5);
  }
  await repos.db.notificationPreference.update({
    where: { userId },
    data: { ignoredStreak: streak, backoffMultiplier: multiplier },
  });
}

export function todayKeyFor(tz: string): string {
  return localDayKey(new Date(), tz);
}
