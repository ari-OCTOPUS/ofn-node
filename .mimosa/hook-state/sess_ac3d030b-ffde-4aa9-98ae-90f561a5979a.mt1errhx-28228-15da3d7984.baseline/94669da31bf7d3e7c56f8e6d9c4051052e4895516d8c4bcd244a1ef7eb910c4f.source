import { Queue, Worker } from 'bullmq';
import IORedis from 'ioredis';
import { Api } from 'grammy';
import { clearOutbound } from '@wlos/safety';
import { loadConfig, localDayKey } from '@wlos/shared';
import { makePrisma, WlosRepos } from '@wlos/memory';
import { dispatchCheckin, planUserDay, sweepIgnored } from './checkins.js';
import { sendViaOutbox, type OutboxDeps } from './outbox.js';
import pino from 'pino';

/**
 * Scheduler worker (BullMQ):
 *  - job "plan" (00:05 Sydney): sweep ignored → plan today's randomized
 *    check-ins (idempotent) → enqueue delayed dispatch jobs
 *  - job "dispatch": fires at the planned instant, re-evaluates, sends/cancels
 *  - job "weekly-nudge" (Sun 18:00 Sydney): a single coach message suggesting
 *    /weekly — goes through the outbox like everything else (cap/quiet apply)
 *
 * Run: npm run worker (alongside npm run bot)
 */

const log = pino({ name: 'wlos-worker' });

async function main() {
  const cfg = loadConfig();
  const connection = new IORedis(cfg.REDIS_URL, { maxRetriesPerRequest: null });
  const prisma = makePrisma(cfg.DATABASE_URL);
  const repos = new WlosRepos(prisma, cfg.TZ_DEFAULT);
  const api = new Api(cfg.TELEGRAM_BOT_TOKEN);
  const deps: OutboxDeps = { api, repos };

  const planQueue = new Queue('wlos-plan', { connection });
  const dispatchQueue = new Queue('wlos-dispatch', { connection });

  await planQueue.upsertJobScheduler(
    'daily-planner',
    { pattern: '5 0 * * *', tz: cfg.TZ_DEFAULT },
    { name: 'plan', data: {} },
  );
  await planQueue.upsertJobScheduler(
    'weekly-nudge',
    { pattern: '0 18 * * 0', tz: cfg.TZ_DEFAULT },
    { name: 'weekly-nudge', data: {} },
  );

  async function planAndEnqueue(userId: string, dayKey: string): Promise<number> {
    await sweepIgnored(repos, userId, dayKey);
    await planUserDay(repos, userId, dayKey); // idempotent: no-op if day already planned
    const instances = await prisma.checkinInstance.findMany({
      where: { userId, dayKey, status: 'scheduled', scheduledAt: { gt: new Date() } },
    });
    for (const inst of instances) {
      await dispatchQueue.add(
        'dispatch',
        { instanceId: inst.id },
        // jobId dedupe: re-enqueueing the same instance is a no-op
        { delay: Math.max(0, inst.scheduledAt.getTime() - Date.now()), jobId: `ci-${inst.id}`, removeOnComplete: true, removeOnFail: 50 },
      );
    }
    return instances.length;
  }

  new Worker(
    'wlos-plan',
    async (job) => {
      const users = await prisma.user.findMany({ where: { deletedAt: null } });
      const todayKey = localDayKey(new Date(), cfg.TZ_DEFAULT);

      if (job.name === 'weekly-nudge') {
        for (const user of users) {
          const chat = await prisma.telegramAccount.findFirst({ where: { userId: user.id } });
          if (!chat) continue;
          const result = await sendViaOutbox(deps, {
            userId: user.id,
            chatId: chat.chatId,
            kind: 'coach',
            sensitivity: 'low',
            clearance: clearOutbound('🗓 وقت مرور هفتگیه — هر وقت آماده بودی /weekly رو بزن.'),
          });
          log.info({ userId: user.id, sent: result.sent }, 'weekly nudge');
        }
        return;
      }

      // job.name === 'plan'
      for (const user of users) {
        const enqueued = await planAndEnqueue(user.id, todayKey);
        log.info({ userId: user.id, enqueued }, 'day planned');
      }
    },
    { connection },
  );

  new Worker(
    'wlos-dispatch',
    async (job) => {
      const { instanceId } = job.data as { instanceId: string };
      const outcome = await dispatchCheckin(deps, repos, instanceId);
      log.info({ instanceId, outcome }, 'checkin dispatched');
    },
    { connection },
  );

  // catch-up on boot: if today has no plan yet (worker started mid-day), plan now.
  // planUserDay's idempotency guard makes this safe against races with the cron.
  const todayKey = localDayKey(new Date(), cfg.TZ_DEFAULT);
  const users = await prisma.user.findMany({ where: { deletedAt: null } });
  for (const user of users) {
    const enqueued = await planAndEnqueue(user.id, todayKey);
    if (enqueued > 0) log.info({ userId: user.id, enqueued }, 'boot catch-up plan');
  }

  log.info('WLOS worker up — planner 00:05, dispatcher live, weekly nudge Sun 18:00 (Australia/Sydney)');

  const shutdown = async () => {
    await Promise.allSettled([planQueue.close(), dispatchQueue.close(), connection.quit(), prisma.$disconnect()]);
    process.exit(0);
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main().catch((err) => {
  log.error(err, 'worker crashed');
  process.exit(1);
});
