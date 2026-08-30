import { Bot, InlineKeyboard, InputFile, type Context } from 'grammy';
import { clearOutbound, formatResourcesFa, triageInbound, MEDICAL_DISCLAIMER_FA } from '@wlos/safety';
import { fa, loadConfig, localDayKey } from '@wlos/shared';
import { parseMeal } from '@wlos/nutrition-engine';
import { makePrisma, WlosRepos } from '@wlos/memory';
import { handleOnboardingCallback, handleOnboardingInput, isOnboarding, startOnboarding } from './onboarding.js';
import { replySafe, sendViaOutbox, type OutboxDeps } from './outbox.js';
import * as cmd from './commands.js';

/**
 * Bot assembly. Middleware order is a safety property:
 *   owner-filter → idempotency → inbound safety triage → routing
 * Inbound triage runs BEFORE any handler including LLM-touching ones.
 */

export function buildBot() {
  const cfg = loadConfig();
  if (!cfg.TELEGRAM_BOT_TOKEN) {
    throw new Error('TELEGRAM_BOT_TOKEN is required (see .env.example — never commit it)');
  }
  const prisma = makePrisma(cfg.DATABASE_URL);
  const repos = new WlosRepos(prisma, cfg.TZ_DEFAULT);
  const bot = new Bot(cfg.TELEGRAM_BOT_TOKEN);
  const deps: OutboxDeps = { api: bot.api, repos };

  // ── middleware 1: single-user lock ─────────────────────────────────────
  bot.use(async (ctx, next) => {
    const chatId = ctx.chat?.id;
    if (!chatId) return;
    if (cfg.TELEGRAM_OWNER_CHAT_ID && String(chatId) !== cfg.TELEGRAM_OWNER_CHAT_ID) {
      return; // silently ignore strangers — bot is personal
    }
    if (ctx.chat?.type !== 'private') return; // private chats only, by policy
    await next();
  });

  // ── middleware 2: idempotency (webhook retries / duplicate updates) ────
  bot.use(async (ctx, next) => {
    const dup = await repos.markUpdateProcessed(BigInt(ctx.update.update_id));
    if (dup) return;
    await next();
  });

  // ── middleware 3: inbound safety triage on any text ────────────────────
  bot.use(async (ctx, next) => {
    const text = ctx.message?.text;
    if (text && !text.startsWith('/')) {
      const verdict = triageInbound(text);
      if (verdict.level === 'crisis' || verdict.level === 'urgent_medical') {
        const user = await getUser(ctx);
        if (user) {
          await repos.recordSafetyEvent(user.id, 'inbound', verdict.level, verdict.categories, 'resources_sent');
          if (verdict.level === 'crisis') {
            await repos.setCrisisMode(user.id, new Date(Date.now() + 24 * 3600 * 1000));
            const msg = [fa.CRISIS_HEADER, '', formatResourcesFa(), '', fa.CRISIS_FOOTER].join('\n');
            await sendViaOutbox(deps, {
              userId: user.id,
              chatId: BigInt(ctx.chat!.id),
              kind: 'safety',
              sensitivity: 'low',
              clearance: clearOutbound(msg),
              isDirectReply: true,
            });
            return; // crisis interrupts normal coaching entirely
          }
          if (verdict.categories.includes('eating_disorder')) {
            await replyDirect(user.id, fa.ED_CONCERN);
          } else {
            await replyDirect(user.id, fa.URGENT_MEDICAL);
          }
          return;
        }
      }
    }
    await next();

    async function replyDirect(userId: string, msg: string) {
      await sendViaOutbox(deps, {
        userId,
        chatId: BigInt(ctx.chat!.id),
        kind: 'safety',
        sensitivity: 'low',
        clearance: clearOutbound(msg),
        isDirectReply: true,
      });
    }
  });

  async function getUser(ctx: Context) {
    const chatId = ctx.chat?.id;
    if (!chatId) return null;
    return repos.getUserByChat(BigInt(chatId));
  }

  async function requireUser(ctx: Context) {
    const chatId = BigInt(ctx.chat!.id);
    return repos.getOrCreateUserByChat(chatId, ctx.from?.username ?? undefined, ctx.from?.first_name ?? 'دوست من');
  }

  function mkCtx(userId: string, chatId: bigint): cmd.Ctx {
    return { deps, repos, userId, chatId, tz: cfg.TZ_DEFAULT };
  }

  // ── commands ───────────────────────────────────────────────────────────
  bot.command('start', async (ctx) => {
    const user = await requireUser(ctx);
    const r = await startOnboarding(repos, user.id);
    await replySafe(deps, user.id, BigInt(ctx.chat.id), r.text, undefined);
  });

  bot.command('setup', async (ctx) => {
    const user = await requireUser(ctx);
    const r = await startOnboarding(repos, user.id);
    await replySafe(deps, user.id, BigInt(ctx.chat.id), '🔧 تنظیم دوباره:\n\n' + r.text);
  });

  const simple = (name: string, fn: (c: cmd.Ctx, args: string) => Promise<void>) => {
    bot.command(name, async (ctx) => {
      const user = await requireUser(ctx);
      await fn(mkCtx(user.id, BigInt(ctx.chat.id)), ctx.match ?? '');
    });
  };

  simple('today', (c) => cmd.cmdToday(c));
  simple('weight', (c, a) => cmd.cmdWeight(c, a));
  simple('meal', (c, a) => cmd.cmdMeal(c, a));
  simple('workout', (c, a) => cmd.cmdWorkout(c, a));
  simple('plan', (c) => cmd.cmdPlan(c));
  simple('report', (c) => cmd.cmdReport(c));
  simple('weekly', (c) => cmd.cmdWeekly(c));
  simple('patterns', (c) => cmd.cmdPatterns(c));
  simple('privacy', (c) => cmd.cmdPrivacy(c));
  simple('consent', (c) => cmd.cmdPrivacy(c));
  simple('help', (c) => cmd.cmdHelp(c));
  simple('crisis', (c) => cmd.cmdCrisis(c));
  simple('hunger', (c, a) => cmd.cmdQuickState(c, 'hunger', a, 'گرسنگی الان از ۰ تا ۱۰؟'));
  simple('mood', (c, a) => cmd.cmdQuickState(c, 'mood', a, 'حال‌وهوات از ۰ تا ۱۰؟'));
  simple('sleep', (c, a) => cmd.cmdQuickState(c, 'sleep_hours', a, 'دیشب چند ساعت خوابیدی؟ (عدد بفرست)'));
  simple('steps', (c, a) => cmd.cmdQuickState(c, 'steps', a, 'امروز چند قدم؟ (عدد بفرست)'));

  bot.command('pause', async (ctx) => {
    const user = await requireUser(ctx);
    await repos.db.notificationPreference.update({ where: { userId: user.id }, data: { paused: true } });
    await replySafe(deps, user.id, BigInt(ctx.chat.id), fa.PAUSED);
  });

  bot.command('resume', async (ctx) => {
    const user = await requireUser(ctx);
    await repos.db.notificationPreference.update({
      where: { userId: user.id },
      data: { paused: false, snoozedUntil: null, stopForDayKey: null },
    });
    await repos.setCrisisMode(user.id, null);
    await replySafe(deps, user.id, BigInt(ctx.chat.id), fa.RESUMED);
  });

  bot.command('snooze', async (ctx) => {
    const user = await requireUser(ctx);
    const min = 90;
    await repos.db.notificationPreference.update({
      where: { userId: user.id },
      data: { snoozedUntil: new Date(Date.now() + min * 60_000) },
    });
    await replySafe(deps, user.id, BigInt(ctx.chat.id), fa.SNOOZED(min));
  });

  bot.command('nosleep', async (ctx) => {
    const user = await requireUser(ctx);
    await repos.db.notificationPreference.update({
      where: { userId: user.id },
      data: { quietSuspended: true },
    });
    await replySafe(deps, user.id, BigInt(ctx.chat.id), 'ساعت سکوت موقتاً غیرفعال شد. با /setup برمی‌گرده.');
  });

  bot.command('export', async (ctx) => {
    const user = await requireUser(ctx);
    const dump = await repos.exportAll(user.id);
    const buf = Buffer.from(JSON.stringify(dump, (_k, v) => (typeof v === 'bigint' ? String(v) : v), 2));
    await ctx.replyWithDocument(new InputFile(buf, `wlos-export-${localDayKey(new Date(), cfg.TZ_DEFAULT)}.json`), {
      caption: fa.EXPORT_READY,
    });
    await repos.db.dataExportJob.create({
      data: { userId: user.id, status: 'done', completedAt: new Date() },
    });
    await repos.audit(user.id, 'user', 'data_export');
  });

  bot.command('delete', async (ctx) => {
    const user = await requireUser(ctx);
    await repos.requestDeletion(user.id);
    await replySafe(deps, user.id, BigInt(ctx.chat.id), fa.DELETE_CONFIRM);
  });

  // ── callbacks ──────────────────────────────────────────────────────────
  bot.on('callback_query:data', async (ctx) => {
    const user = await getUser(ctx);
    if (!user) return ctx.answerCallbackQuery();
    const data = ctx.callbackQuery.data;
    const chatId = BigInt(ctx.chat!.id);
    const c = mkCtx(user.id, chatId);

    // reveal sensitive envelope
    if (data === 'reveal') {
      const msgId = ctx.callbackQuery.message?.message_id;
      const stash = msgId
        ? await repos.db.memory.findUnique({
            where: { userId_layer_key: { userId: user.id, layer: 'dynamic_state', key: `reveal:${msgId}` } },
          })
        : null;
      if (stash) {
        const payload = JSON.parse(stash.content) as { text: string; keyboard: never | null };
        await ctx.editMessageText(payload.text, payload.keyboard ? { reply_markup: payload.keyboard } : undefined);
      } else {
        await ctx.editMessageText('این پیام منقضی شده.');
      }
      return ctx.answerCallbackQuery();
    }

    // onboarding buttons
    if (data.startsWith('ob:')) {
      const r = await handleOnboardingCallback(repos, user.id, data);
      if (r) {
        await replySafe(deps, user.id, chatId, r.text, r.keyboard ? { inline_keyboard: r.keyboard } : undefined);
      }
      return ctx.answerCallbackQuery();
    }

    // consent toggles from /privacy
    if (data.startsWith('consent:toggle:')) {
      const scope = data.split(':')[2] as 'psychology' | 'cannabis' | 'coach_sharing';
      const current = await repos.hasConsent(user.id, scope);
      await repos.setConsent(user.id, scope, !current);
      await ctx.answerCallbackQuery({ text: !current ? fa.CONSENT_ON : fa.CONSENT_OFF });
      return cmd.cmdPrivacy(c);
    }
    if (data === 'privacy:togglecal') {
      const p = await repos.db.userProfile.findUnique({ where: { userId: user.id } });
      await repos.db.userProfile.update({
        where: { userId: user.id },
        data: { hideCalories: !p?.hideCalories },
      });
      await ctx.answerCallbackQuery({ text: 'اعمال شد' });
      return cmd.cmdPrivacy(c);
    }
    if (data === 'privacy:export') {
      await ctx.answerCallbackQuery();
      const dump = await repos.exportAll(user.id);
      const buf = Buffer.from(JSON.stringify(dump, (_k, v) => (typeof v === 'bigint' ? String(v) : v), 2));
      await ctx.replyWithDocument(new InputFile(buf, `wlos-export.json`), { caption: fa.EXPORT_READY });
      return;
    }
    if (data === 'privacy:delete') {
      await repos.requestDeletion(user.id);
      await ctx.answerCallbackQuery();
      return replySafe(deps, user.id, chatId, fa.DELETE_CONFIRM);
    }

    // quick meal buttons
    if (data.startsWith('quick:')) {
      const [, name, kcal] = data.split(':');
      await repos.logMeal(user.id, { name: name!, calories: Number(kcal) });
      await ctx.answerCallbackQuery({ text: 'ثبت شد ✅' });
      return;
    }

    // state scale buttons (from commands or check-ins)
    if (data.startsWith('state:')) {
      const [, kind, val] = data.split(':');
      await repos.logState(user.id, kind!, Number(val), 'button');
      await ctx.answerCallbackQuery({ text: fa.CHECKIN_THANKS });
      return;
    }

    // check-in answer buttons: ci:<instanceId>:<payload>
    if (data.startsWith('ci:')) {
      const [, instanceId, payload] = data.split(':');
      const instance = await repos.db.checkinInstance.findUnique({ where: { id: instanceId! } });
      if (!instance) return ctx.answerCallbackQuery();
      if (payload === 'snooze') {
        await repos.db.checkinInstance.update({ where: { id: instance.id }, data: { status: 'snoozed' } });
        await repos.db.notificationPreference.update({
          where: { userId: user.id },
          data: { snoozedUntil: new Date(Date.now() + 60 * 60_000) },
        });
        await ctx.answerCallbackQuery({ text: fa.SNOOZED(60) });
        return;
      }
      if (payload === 'stopday') {
        await repos.db.checkinInstance.update({ where: { id: instance.id }, data: { status: 'cancelled', cancelReason: 'stop_today' } });
        await repos.db.notificationPreference.update({
          where: { userId: user.id },
          data: { stopForDayKey: localDayKey(new Date(), cfg.TZ_DEFAULT) },
        });
        await ctx.answerCallbackQuery();
        await replySafe(deps, user.id, chatId, fa.CHECKIN_STOPPED_TODAY);
        return;
      }
      const numeric = payload === 'low' ? 2 : payload === 'mid' ? 5 : payload === 'high' ? 8 : payload === 'yes' ? 1 : payload === 'no' ? 0 : null;
      await repos.db.checkinResponse.create({
        data: { checkinId: instance.id, valueRaw: payload ?? '', valueNum: numeric },
      });
      await repos.db.checkinInstance.update({ where: { id: instance.id }, data: { status: 'answered' } });
      // map hunger/craving/etc. topics into state logs when numeric
      if (numeric !== null && ['hunger', 'craving', 'mood', 'energy', 'stress'].some((k) => instance.topic.includes(k))) {
        const kind = ['hunger', 'craving', 'mood', 'energy', 'stress'].find((k) => instance.topic.includes(k))!;
        await repos.logState(user.id, kind, numeric === 1 && payload === 'yes' ? 8 : numeric, 'checkin');
      }
      // backoff recovery on any answer
      const pref = await repos.db.notificationPreference.findUnique({ where: { userId: user.id } });
      if (pref) {
        await repos.db.notificationPreference.update({
          where: { userId: user.id },
          data: { ignoredStreak: 0, backoffMultiplier: Math.min(1, pref.backoffMultiplier + 0.25) },
        });
      }
      await ctx.answerCallbackQuery({ text: fa.CHECKIN_THANKS });
      return;
    }

    // pattern corrections
    if (data.startsWith('pat:')) {
      const [, verdict, id] = data.split(':');
      const p = await repos.db.pattern.findUnique({ where: { id: id! } });
      if (p) {
        await repos.db.pattern.update({
          where: { id: p.id },
          data: { userVerdict: verdict === 'confirm' ? 'confirmed' : 'rejected' },
        });
        await repos.db.patternUserCorrection.create({
          data: { patternId: p.id, verdict: verdict === 'confirm' ? 'confirmed' : 'rejected' },
        });
      }
      await ctx.answerCallbackQuery({ text: 'ثبت شد — نظر تو معیاره 🙏' });
      return;
    }

    // workout done
    if (data.startsWith('wk:done:')) {
      const key = data.split(':')[2]!;
      const title = key === 'gym_full_a' ? 'باشگاه — Full Body A' : key === 'gym_full_b' ? 'باشگاه — Full Body B' : key;
      await repos.logWorkout(user.id, { kind: 'gym', title });
      await ctx.answerCallbackQuery({ text: fa.WORKOUT_SAVED(title) });
      return;
    }
    if (data === 'wk:short') {
      await ctx.answerCallbackQuery();
      const { pickSession, formatSessionFa } = await import('@wlos/training-engine');
      const s = pickSession('light', { location: 'home' });
      return void (await replySafe(deps, user.id, chatId, formatSessionFa(s)));
    }

    await ctx.answerCallbackQuery();
  });

  // ── free-text routing ──────────────────────────────────────────────────
  bot.on('message:text', async (ctx) => {
    const user = await requireUser(ctx);
    const chatId = BigInt(ctx.chat.id);
    const text = ctx.message.text;

    // deletion confirmation phrase
    if (text.trim() === 'DELETE ALL') {
      const pending = await repos.db.deletionRequest.findFirst({
        where: { userId: user.id, status: 'awaiting_confirmation' },
      });
      if (pending) {
        await repos.confirmDeletion(user.id);
        await ctx.reply(fa.DELETE_DONE); // user row is gone; direct reply is the only channel left
        return;
      }
    }

    // onboarding flow
    const profile = await repos.db.userProfile.findUnique({ where: { userId: user.id } });
    if (profile && isOnboarding(profile.onboardingStep)) {
      const r = await handleOnboardingInput(repos, user.id, text);
      if (r) {
        await replySafe(deps, user.id, chatId, r.text, r.keyboard ? { inline_keyboard: r.keyboard } : undefined);
        return;
      }
    }

    // photo-free food logging: bare "name + number" is treated as a meal
    const meal = parseMeal(text);
    if (meal) {
      const c = mkCtx(user.id, chatId);
      await cmd.cmdMeal(c, text);
      return;
    }

    // gentle default — keep it useful without LLM chatter
    await replySafe(
      deps,
      user.id,
      chatId,
      'دریافت شد 👍 برای ثبت غذا: «اسم + کالری» (مثلاً «ناهار ۸۰۰»). بقیهٔ دستورها: /help',
    );
  });

  // reject photos explicitly (product decision: no photo processing)
  bot.on(['message:photo', 'message:document'], async (ctx) => {
    const user = await requireUser(ctx);
    await replySafe(
      deps,
      user.id,
      BigInt(ctx.chat.id),
      'عکس پردازش نمی‌کنم (تصمیم محصول برای سادگی و حریم خصوصی). فقط بنویس: «اسم غذا + کالری» 🙏',
    );
  });

  return { bot, repos, prisma, cfg, deps };
}

export type BotBundle = ReturnType<typeof buildBot>;
export { InlineKeyboard };
