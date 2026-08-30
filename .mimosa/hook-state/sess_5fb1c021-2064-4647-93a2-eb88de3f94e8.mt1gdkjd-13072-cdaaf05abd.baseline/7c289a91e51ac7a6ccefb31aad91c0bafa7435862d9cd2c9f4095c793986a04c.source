import { InlineKeyboard } from 'grammy';
import { clearOutbound, formatResourcesFa, MEDICAL_DISCLAIMER_FA } from '@wlos/safety';
import {
  bmrMifflin,
  calorieTargetRange,
  parseMeal,
  parseWeight,
  proteinTargetGrams,
  rollingAverage,
  tdeeEstimate,
  trendSummary,
} from '@wlos/nutrition-engine';
import { assessReadiness, formatSessionFa, pickSession } from '@wlos/training-engine';
import { buildDailyReportFa, buildWeeklyReportFa, scanAssociations } from '@wlos/agents';
import { fa, localDayKey, normalizeDigits, toPersianDigits } from '@wlos/shared';
import type { WlosRepos } from '@wlos/memory';
import { replySafe, sendViaOutbox, type OutboxDeps } from './outbox.js';

/** Command handlers. Every outbound goes through the outbox. */

export interface Ctx {
  deps: OutboxDeps;
  repos: WlosRepos;
  userId: string;
  chatId: bigint;
  tz: string;
}

const reply = (c: Ctx, text: string, kb?: InlineKeyboard) =>
  replySafe(c.deps, c.userId, c.chatId, text, kb ? kb : undefined);

export async function cmdToday(c: Ctx): Promise<void> {
  const dayKey = localDayKey(new Date(), c.tz);
  const summary = await c.repos.db.nutritionDailySummary.findUnique({
    where: { userId_dayKey: { userId: c.userId, dayKey } },
  });
  const target = await c.repos.db.nutritionTarget.findFirst({
    where: { userId: c.userId },
    orderBy: { effectiveFrom: 'desc' },
  });
  const lines = [
    `📅 امروز (${dayKey})`,
    target ? `• هدف کالری: ${target.kcalLow}–${target.kcalHigh} cal | پروتئین ${target.proteinG}g` : '• هنوز هدف تنظیم نشده — /plan',
    summary ? `• تا الان: ${summary.totalCalories} cal در ${summary.mealsLogged} وعده` : '• هنوز چیزی ثبت نشده',
    '',
    'ثبت سریع: /meal • /weight • /workout',
  ];
  await reply(c, lines.join('\n'));
}

export async function cmdWeight(c: Ctx, args: string): Promise<void> {
  const w = parseWeight(args);
  if (!w) {
    await reply(c, 'وزن رو این‌طوری بفرست: «/weight 94.5» یا فقط «۹۴٫۵»');
    return;
  }
  await c.repos.logWeight(c.userId, w);
  const series = await c.repos.recentWeights(c.userId, 42);
  const roll = rollingAverage(series, 7, 3);
  const avg7 = roll.length ? roll[roll.length - 1]!.avg : null;
  const t = trendSummary(series);
  const trendLine =
    t.classification === 'insufficient_data'
      ? 'چند روز دیگه ثبت کن تا روند مشخص بشه.'
      : `روند: ${t.slopeKgPerWeek} kg/هفته`;
  await reply(c, fa.WEIGHT_SAVED(String(w), avg7 === null ? null : String(avg7), trendLine));
}

export async function cmdMeal(c: Ctx, args: string): Promise<void> {
  if (!args.trim()) {
    const kb = new InlineKeyboard()
      .text('صبحانه 400', 'quick:صبحانه:400')
      .text('ناهار 700', 'quick:ناهار:700')
      .row()
      .text('شام 650', 'quick:شام:650')
      .text('اسنک 200', 'quick:اسنک:200');
    await reply(c, 'غذا + کالری بفرست، مثلاً «ناهار: ۸۰۰ کالری» یا «chicken rice 650»\nیا ثبت سریع:', kb);
    return;
  }
  // ">3000 kcal" confirm flow: resending the same entry with «تایید»/confirm accepts it
  const confirmRe = /(?:^|\s)(تایید|تأیید|confirm)(?:\s|$)/i;
  const confirmed = confirmRe.test(args);
  const cleaned = confirmed ? args.replace(confirmRe, ' ').trim() : args;

  const m = parseMeal(cleaned);
  if (!m) {
    await reply(c, fa.MEAL_PARSE_FAIL);
    return;
  }
  if (m.suspiciouslyHigh && !confirmed) {
    await reply(c, fa.MEAL_TOO_HIGH(m.calories));
    return;
  }
  await c.repos.logMeal(c.userId, {
    name: m.name,
    calories: m.calories,
    proteinG: m.proteinG,
    carbsG: m.carbsG,
    fatG: m.fatG,
    confirmedHigh: m.suspiciouslyHigh && confirmed,
  });
  const dayKey = localDayKey(new Date(), c.tz);
  const summary = await c.repos.db.nutritionDailySummary.findUnique({
    where: { userId_dayKey: { userId: c.userId, dayKey } },
  });
  const profile = await c.repos.db.userProfile.findUnique({ where: { userId: c.userId } });
  if (profile?.hideCalories) {
    await reply(c, `ثبت شد: ${m.name} ✅`);
  } else {
    await reply(c, fa.MEAL_SAVED(m.name, m.calories, summary?.totalCalories ?? m.calories));
  }
}

export async function cmdWorkout(c: Ctx, args: string): Promise<void> {
  const text = args.trim();
  if (!text) {
    // offer today's session based on readiness
    const today = localDayKey(new Date(), c.tz);
    const sleep = await c.repos.db.stateLog.findFirst({
      where: { userId: c.userId, kind: 'sleep_hours', dayKey: today },
      orderBy: { occurredAt: 'desc' },
    });
    const energy = await c.repos.db.stateLog.findFirst({
      where: { userId: c.userId, kind: 'energy', dayKey: today },
      orderBy: { occurredAt: 'desc' },
    });
    const verdict = assessReadiness({
      sleepHoursLastNight: sleep?.value ?? null,
      energy0to10: energy?.value ?? null,
      soreness0to10: null,
      stress0to10: null,
      reportedImpairment: false,
      reportedDizzinessOrSymptoms: false,
      daysSinceLastDeload: null,
      consecutiveHardSessions: 0,
    });
    const lastGym = await c.repos.db.workout.findFirst({
      where: { userId: c.userId, kind: 'gym' },
      orderBy: { occurredAt: 'desc' },
    });
    const session = pickSession(verdict.maxIntensity, {
      location: 'gym',
      lastGymKey: lastGym?.title.includes('Full Body A') ? 'gym_full_a' : lastGym?.title.includes('Full Body B') ? 'gym_full_b' : undefined,
    });
    const kb = new InlineKeyboard().text('انجام شد ✅', `wk:done:${session.key}`).text('کوتاهش کن', 'wk:short');
    await reply(c, `${formatSessionFa(session)}\n\n(${verdict.reasons.join('، ')})`, kb);
    return;
  }
  await c.repos.logWorkout(c.userId, { kind: 'gym', title: text });
  await reply(c, fa.WORKOUT_SAVED(text));
}

export async function cmdReport(c: Ctx): Promise<void> {
  const dayKey = localDayKey(new Date(), c.tz);
  const [summary, weights, workout, sleep, steps, profile, target] = await Promise.all([
    c.repos.db.nutritionDailySummary.findUnique({ where: { userId_dayKey: { userId: c.userId, dayKey } } }),
    c.repos.recentWeights(c.userId, 14),
    c.repos.db.workout.findFirst({ where: { userId: c.userId, dayKey }, orderBy: { occurredAt: 'desc' } }),
    c.repos.db.stateLog.findFirst({ where: { userId: c.userId, kind: 'sleep_hours', dayKey } }),
    c.repos.db.stepsDailySummary.findUnique({ where: { userId_dayKey: { userId: c.userId, dayKey } } }),
    c.repos.db.userProfile.findUnique({ where: { userId: c.userId } }),
    c.repos.db.nutritionTarget.findFirst({ where: { userId: c.userId }, orderBy: { effectiveFrom: 'desc' } }),
  ]);
  const roll = rollingAverage(weights, 7, 3);
  const todayW = weights.find((w) => w.dayKey === dayKey)?.value ?? null;
  const text = buildDailyReportFa({
    dayKey,
    displayName: '',
    totalCalories: summary?.totalCalories ?? null,
    targetLow: target?.kcalLow ?? null,
    targetHigh: target?.kcalHigh ?? null,
    proteinG: summary?.totalProteinG ?? null,
    proteinTarget: target?.proteinG ?? null,
    mealsLogged: summary?.mealsLogged ?? 0,
    weightToday: todayW,
    avg7: roll.length ? roll[roll.length - 1]!.avg : null,
    workoutTitle: workout?.title ?? null,
    sleepHours: sleep?.value ?? null,
    steps: steps?.steps ?? null,
    hideCalories: profile?.hideCalories ?? false,
  });
  await reply(c, text);
}

export async function cmdWeekly(c: Ctx): Promise<void> {
  const now = new Date();
  const dayKey = localDayKey(now, c.tz);
  const weights = await c.repos.recentWeights(c.userId, 28);
  const since = new Date(now.getTime() - 7 * 86400_000);
  const [meals, workouts, sleeps, checkins] = await Promise.all([
    c.repos.db.nutritionDailySummary.findMany({ where: { userId: c.userId, computedAt: { gte: since } } }),
    c.repos.db.workout.findMany({ where: { userId: c.userId, occurredAt: { gte: since } } }),
    c.repos.db.stateLog.findMany({ where: { userId: c.userId, kind: 'sleep_hours', occurredAt: { gte: since } } }),
    c.repos.db.checkinInstance.findMany({ where: { userId: c.userId, sentAt: { gte: since } } }),
  ]);
  const target = await c.repos.db.nutritionTarget.findFirst({
    where: { userId: c.userId },
    orderBy: { effectiveFrom: 'desc' },
  });
  const profile = await c.repos.db.userProfile.findUnique({ where: { userId: c.userId } });
  const consents = await c.repos.consentMap(c.userId);

  // daily records for pattern scan (last 28 days)
  const stateRows = await c.repos.db.stateLog.findMany({
    where: { userId: c.userId, occurredAt: { gte: new Date(now.getTime() - 28 * 86400_000) } },
  });
  const summaries28 = await c.repos.db.nutritionDailySummary.findMany({
    where: { userId: c.userId },
    orderBy: { dayKey: 'desc' },
    take: 28,
  });
  const byDay = new Map<string, { sleepHours?: number; eveningCraving?: boolean; highIntakeDay?: boolean; stress?: number }>();
  for (const s of summaries28) {
    byDay.set(s.dayKey, {
      ...byDay.get(s.dayKey),
      highIntakeDay: s.targetHigh ? s.totalCalories > s.targetHigh : undefined,
    });
  }
  for (const r of stateRows) {
    const d = byDay.get(r.dayKey) ?? {};
    if (r.kind === 'sleep_hours') d.sleepHours = r.value;
    if (r.kind === 'craving' && r.value >= 6) d.eveningCraving = true;
    if (r.kind === 'stress') d.stress = r.value;
    byDay.set(r.dayKey, d);
  }
  const findings = scanAssociations(
    [...byDay.entries()].map(([k, v]) => ({ dayKey: k, ...v })),
    { cannabis: consents.cannabis, psychology: consents.psychology },
  );

  // persist findings as patterns
  for (const f of findings) {
    await c.repos.db.pattern.upsert({
      where: { userId_antecedent_outcome: { userId: c.userId, antecedent: f.antecedent, outcome: f.outcome } },
      create: {
        userId: c.userId,
        antecedent: f.antecedent,
        outcome: f.outcome,
        direction: 'positive',
        effectSummary: `${f.antecedentRate ?? '?'} vs base ${f.baseRate ?? '?'}`,
        evidenceCount: f.evidenceCount,
        counterexampleCount: f.counterexampleCount,
        confidence: f.confidence,
        sensitive: f.sensitive,
        nextValidationQuestion: f.nextValidationQuestion,
      },
      update: {
        evidenceCount: f.evidenceCount,
        counterexampleCount: f.counterexampleCount,
        confidence: f.confidence,
        lastSeenAt: new Date(),
        effectSummary: `${f.antecedentRate ?? '?'} vs base ${f.baseRate ?? '?'}`,
      },
    });
  }

  const text = buildWeeklyReportFa({
    weekEndDayKey: dayKey,
    weights,
    intakeDays: meals.map((m) => ({ dayKey: m.dayKey, value: m.totalCalories })),
    targetLow: target?.kcalLow ?? null,
    targetHigh: target?.kcalHigh ?? null,
    workoutsCompleted: workouts.filter((w) => w.completed).length,
    workoutsPlanned: workouts.length,
    sleepAvg: sleeps.length
      ? Math.round((sleeps.reduce((s, x) => s + x.value, 0) / sleeps.length) * 10) / 10
      : null,
    checkinsSent: checkins.length,
    checkinsAnswered: checkins.filter((ch) => ch.status === 'answered').length,
    findings,
    hideCalories: profile?.hideCalories ?? false,
  });
  await reply(c, text);
  await c.repos.db.report.create({
    data: { userId: c.userId, kind: 'weekly', dayKey, content: text },
  });
}

export async function cmdPlan(c: Ctx): Promise<void> {
  const profile = await c.repos.db.userProfile.findUnique({ where: { userId: c.userId } });
  const weights = await c.repos.recentWeights(c.userId, 7);
  const lastW = weights.length ? weights[weights.length - 1]!.value : null;
  if (!profile?.sex || !profile.heightCm || !profile.birthYear || !lastW) {
    await reply(c, 'برای ساخت پلن، پروفایل کامل لازمه — /setup و بعد یک /weight ثبت کن.');
    return;
  }
  const body = {
    sex: profile.sex as 'male' | 'female',
    ageYears: new Date().getFullYear() - profile.birthYear,
    heightCm: profile.heightCm,
    weightKg: lastW,
  };
  const bmr = bmrMifflin(body);
  const tdee = tdeeEstimate(body, (profile.activityLevel as never) ?? 'light');
  const target = calorieTargetRange(body, tdee.mid);
  const protein = proteinTargetGrams(lastW, profile.goalWeightKg ?? undefined);
  await c.repos.db.nutritionTarget.create({
    data: {
      userId: c.userId,
      kcalLow: target.low,
      kcalHigh: target.high,
      proteinG: protein.target,
      fiberLow: body.sex === 'male' ? 30 : 25,
      fiberHigh: body.sex === 'male' ? 38 : 32,
      rationale: target.rationale,
      floorApplied: target.floorApplied,
    },
  });
  await reply(
    c,
    [
      '🎯 پلن تغذیه (تخمینی — نه حکم قطعی):',
      `• BMR: ~${bmr} cal`,
      `• TDEE: ~${tdee.low}–${tdee.high} cal`,
      `• هدف روزانه: ${target.low}–${target.high} cal (کسری ملایم ${target.deficitPerDay})`,
      `• پروتئین: ~${protein.target}g (بازه ${protein.low}–${protein.high})`,
      '',
      'با داده‌های واقعی وزن + کالری، این تخمین هر هفته دقیق‌تر می‌شه.',
      'تمرین امروز: /workout',
    ].join('\n'),
  );
}

export async function cmdPatterns(c: Ctx): Promise<void> {
  const patterns = await c.repos.db.pattern.findMany({
    where: { userId: c.userId, userVerdict: null },
    orderBy: { lastSeenAt: 'desc' },
    take: 5,
  });
  if (!patterns.length) {
    await reply(c, 'هنوز الگوی قابل نمایشی پیدا نشده — با ثبت بیشتر، فرضیه‌ها ساخته می‌شن.');
    return;
  }
  for (const p of patterns) {
    const kb = new InlineKeyboard()
      .text('درسته ✅', `pat:confirm:${p.id}`)
      .text('اشتباهه ❌', `pat:reject:${p.id}`);
    await reply(
      c,
      [
        `فرضیه: ${p.antecedent} → ${p.outcome}`,
        `شواهد: ${p.evidenceCount} | خلافش: ${p.counterexampleCount} | اطمینان: ${p.confidence}`,
        '(این همبستگیه، نه علیت — نظر تو معیار نهاییه)',
      ].join('\n'),
      kb,
    );
  }
}

export async function cmdCrisis(c: Ctx): Promise<void> {
  const text = [fa.CRISIS_HEADER, '', formatResourcesFa(), '', MEDICAL_DISCLAIMER_FA].join('\n');
  await sendViaOutbox(c.deps, {
    userId: c.userId,
    chatId: c.chatId,
    kind: 'safety',
    sensitivity: 'low',
    clearance: clearOutbound(text),
    isDirectReply: true,
  });
}

export async function cmdPrivacy(c: Ctx): Promise<void> {
  const consents = await c.repos.consentMap(c.userId);
  const profile = await c.repos.db.userProfile.findUnique({ where: { userId: c.userId } });
  const onOff = (v?: boolean) => (v ? 'روشن ✅' : 'خاموش ⛔️');
  const kb = new InlineKeyboard()
    .text(`🧠 روان‌شناسی: ${onOff(consents.psychology)}`, 'consent:toggle:psychology')
    .row()
    .text(`🌿 cannabis: ${onOff(consents.cannabis)}`, 'consent:toggle:cannabis')
    .row()
    .text(`👥 اشتراک با مربی: ${onOff(consents.coach_sharing)}`, 'consent:toggle:coach_sharing')
    .row()
    .text(`🔢 نمایش کالری: ${profile?.hideCalories ? 'خاموش' : 'روشن'}`, 'privacy:togglecal')
    .row()
    .text('📦 خروجی داده‌ها', 'privacy:export')
    .text('🗑 حذف کامل', 'privacy:delete');
  await reply(
    c,
    [
      '🔐 حریم خصوصی و رضایت‌ها:',
      '• داده‌ها فقط در سرور خودت (Sydney) نگهداری می‌شن؛ فروخته یا share نمی‌شن.',
      '• چت تلگرام end-to-end encrypted نیست — جزئیات حساس تو اعلان‌ها نمیاد.',
      '• هر رضایتی رو هر لحظه می‌تونی خاموش کنی:',
    ].join('\n'),
    kb,
  );
}

export async function cmdHelp(c: Ctx): Promise<void> {
  await reply(
    c,
    [
      '🤖 WLOS — دستورها:',
      '/today برنامه و وضعیت امروز',
      '/weight ثبت وزن • /meal ثبت غذا (اسم + کالری)',
      '/workout تمرین امروز یا ثبت تمرین',
      '/hunger /mood /sleep /steps ثبت سریع',
      '/plan پلن تغذیه • /report گزارش روز • /weekly گزارش هفته',
      '/patterns الگوهای کشف‌شده (با تایید/رد تو)',
      '/privacy رضایت‌ها، خروجی، حذف • /consent همون',
      '/pause توقف چک‌این‌ها • /resume ادامه • /snooze بعداً',
      '/setup تنظیمات • /help همین • /crisis منابع اضطراری استرالیا',
      '',
      MEDICAL_DISCLAIMER_FA,
    ].join('\n'),
  );
}

export async function cmdQuickState(c: Ctx, kind: string, args: string, promptText: string): Promise<void> {
  const n = Number(normalizeDigits(args).replace(/[^\d.]/g, ''));

  // steps is a count, not a 0–10 scale — handle FIRST so "/steps 8" never
  // lands in the scale branch below
  if (kind === 'steps') {
    const steps = Math.round(n);
    if (args.trim() && steps > 0 && steps < 100_000) {
      const dayKey = localDayKey(new Date(), c.tz);
      await c.repos.db.stepsDailySummary.upsert({
        where: { userId_dayKey: { userId: c.userId, dayKey } },
        create: { userId: c.userId, dayKey, steps },
        update: { steps },
      });
      await reply(c, `ثبت شد: ${toPersianDigits(steps)} قدم 👟`);
      return;
    }
    await reply(c, promptText);
    return;
  }

  if (args.trim() && Number.isFinite(n) && n >= 0 && n <= (kind === 'sleep_hours' ? 16 : 10)) {
    await c.repos.logState(c.userId, kind, n, 'command');
    await reply(c, fa.CHECKIN_THANKS);
    return;
  }
  const kb =
    kind === 'sleep_hours'
      ? undefined
      : new InlineKeyboard()
          .text('0-3', `state:${kind}:2`)
          .text('4-6', `state:${kind}:5`)
          .text('7-10', `state:${kind}:8`);
  await reply(c, promptText, kb);
}
