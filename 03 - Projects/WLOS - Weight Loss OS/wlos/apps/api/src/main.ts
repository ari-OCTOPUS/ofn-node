import Fastify from 'fastify';
import pino from 'pino';
import { timingSafeEqual } from 'node:crypto';
import { loadConfig, localDayKey } from '@wlos/shared';
import { makePrisma, WlosRepos } from '@wlos/memory';
import { buildCoachReportMd } from '@wlos/agents';
import { validateInitData } from './initdata.js';

/**
 * WLOS API (Fastify, :8080)
 *  GET  /health
 *  GET  /coach/report?format=md|json   (x-api-key: COACH_API_KEY; needs coach_sharing consent)
 *  POST /coach/notes {author, content} (x-api-key)
 *  GET  /coach/notes                   (x-api-key)
 *  POST /miniapp/verify {initData}     (server-side initData validation)
 */

const log = pino({ name: 'wlos-api' });

async function main() {
  const cfg = loadConfig();
  const prisma = makePrisma(cfg.DATABASE_URL);
  const repos = new WlosRepos(prisma, cfg.TZ_DEFAULT);
  const app = Fastify({ logger: false });

  const coachAuth = (headerKey: unknown): boolean => {
    if (!cfg.COACH_API_KEY || typeof headerKey !== 'string') return false;
    const a = Buffer.from(headerKey);
    const b = Buffer.from(cfg.COACH_API_KEY);
    return a.length === b.length && timingSafeEqual(a, b);
  };

  app.get('/health', async () => ({ ok: true, service: 'wlos-api', tz: cfg.TZ_DEFAULT }));

  app.get('/coach/report', async (req, reply) => {
    if (!coachAuth(req.headers['x-api-key'])) return reply.code(401).send({ error: 'unauthorized' });
    const user = await prisma.user.findFirst({ where: { deletedAt: null }, include: { profile: true } });
    if (!user) return reply.code(404).send({ error: 'no_user' });

    const consents = await repos.consentMap(user.id);
    if (consents.coach_sharing !== true) {
      return reply.code(403).send({ error: 'coach_sharing_consent_not_granted' });
    }

    const now = new Date();
    const since = new Date(now.getTime() - 7 * 86_400_000);
    const [weights, summaries, workouts, sleeps, checkins, patterns, safety, notes, targets] = await Promise.all([
      repos.recentWeights(user.id, 42),
      prisma.nutritionDailySummary.findMany({ where: { userId: user.id }, orderBy: { dayKey: 'desc' }, take: 7 }),
      prisma.workout.findMany({ where: { userId: user.id, occurredAt: { gte: since } } }),
      prisma.stateLog.findMany({ where: { userId: user.id, kind: 'sleep_hours', occurredAt: { gte: since } } }),
      prisma.checkinInstance.findMany({ where: { userId: user.id, sentAt: { gte: since } } }),
      prisma.pattern.findMany({ where: { userId: user.id, userVerdict: { not: 'rejected' } } }),
      prisma.safetyEvent.findMany({ where: { userId: user.id, occurredAt: { gte: since } } }),
      prisma.coachNote.findMany({ where: { userId: user.id, active: true } }),
      prisma.nutritionTarget.findFirst({ where: { userId: user.id }, orderBy: { effectiveFrom: 'desc' } }),
    ]);

    const cannabisAllowed = consents.cannabis === true;
    const cannabisEvents = cannabisAllowed
      ? await prisma.cannabisEvent.count({ where: { userId: user.id, occurredAt: { gte: since }, deletedAt: null } })
      : null;

    const md = buildCoachReportMd({
      weekEndDayKey: localDayKey(now, cfg.TZ_DEFAULT),
      weights,
      intakeDays: summaries.map((s) => ({ dayKey: s.dayKey, value: s.totalCalories })),
      targetLow: targets?.kcalLow ?? null,
      targetHigh: targets?.kcalHigh ?? null,
      workoutsCompleted: workouts.filter((w) => w.completed).length,
      workoutsPlanned: workouts.length,
      sleepAvg: sleeps.length ? Math.round((sleeps.reduce((s, x) => s + x.value, 0) / sleeps.length) * 10) / 10 : null,
      checkinsSent: checkins.length,
      checkinsAnswered: checkins.filter((c) => c.status === 'answered').length,
      findings: patterns.map((p) => ({
        key: `${p.antecedent}→${p.outcome}`,
        antecedent: p.antecedent,
        outcome: p.outcome,
        evidenceCount: p.evidenceCount,
        counterexampleCount: p.counterexampleCount,
        baseRate: null,
        antecedentRate: null,
        confidence: p.confidence as never,
        notCausal: true,
        sensitive: p.sensitive,
        requiredConsent: null,
        nextValidationQuestion: '',
      })),
      hideCalories: false,
      displayName: user.displayName,
      plateauStatus: 'see /weekly analysis',
      plateauConfidence: '—',
      activeExperiments: [],
      safetyFlags: safety.map((s) => `${s.level}: ${s.categories} (${s.action})`),
      cannabisSummary: cannabisAllowed ? `${cannabisEvents} consented events this week (details in app only)` : null,
      coachNotes: notes.map((n) => n.content),
    });

    const format = (req.query as { format?: string }).format ?? 'md';
    if (format === 'json') {
      return { generatedAt: now.toISOString(), markdown: md };
    }
    reply.type('text/markdown; charset=utf-8');
    return md;
  });

  app.post('/coach/notes', async (req, reply) => {
    if (!coachAuth(req.headers['x-api-key'])) return reply.code(401).send({ error: 'unauthorized' });
    const body = req.body as { author?: string; content?: string };
    if (!body?.content || body.content.length < 3 || body.content.length > 2000) {
      return reply.code(400).send({ error: 'content_required' });
    }
    const user = await prisma.user.findFirst({ where: { deletedAt: null } });
    if (!user) return reply.code(404).send({ error: 'no_user' });
    const note = await prisma.coachNote.create({
      data: { userId: user.id, author: body.author ?? 'coach', content: body.content },
    });
    await repos.audit(user.id, 'coach', 'coach_note_added', note.id);
    return { ok: true, id: note.id, treatment: 'constraint_not_command' };
  });

  app.get('/coach/notes', async (req, reply) => {
    if (!coachAuth(req.headers['x-api-key'])) return reply.code(401).send({ error: 'unauthorized' });
    const user = await prisma.user.findFirst({ where: { deletedAt: null } });
    if (!user) return reply.code(404).send({ error: 'no_user' });
    return prisma.coachNote.findMany({ where: { userId: user.id }, orderBy: { createdAt: 'desc' } });
  });

  app.post('/miniapp/verify', async (req, reply) => {
    const body = req.body as { initData?: string };
    if (!body?.initData) return reply.code(400).send({ valid: false, reason: 'missing' });
    const result = validateInitData(body.initData, cfg.TELEGRAM_BOT_TOKEN);
    if (!result.valid) return reply.code(401).send(result);
    return result;
  });

  await app.listen({ port: 8080, host: '0.0.0.0' });
  log.info('WLOS api up on :8080');
}

main().catch((err) => {
  log.error(err, 'api crashed');
  process.exit(1);
});
