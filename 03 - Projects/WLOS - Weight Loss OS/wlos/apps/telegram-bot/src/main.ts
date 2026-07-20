import pino from 'pino';
import { buildBot } from './bot.js';

/**
 * Bot entrypoint.
 *  - development: long polling (TELEGRAM_MODE=polling)
 *  - production: webhook via Fastify (TELEGRAM_MODE=webhook) with
 *    X-Telegram-Bot-Api-Secret-Token verification
 */

const log = pino({ name: 'wlos-bot' });

async function main() {
  const { bot, cfg } = buildBot();

  await bot.api.setMyCommands([
    { command: 'start', description: 'شروع / onboarding' },
    { command: 'today', description: 'وضعیت امروز' },
    { command: 'weight', description: 'ثبت وزن' },
    { command: 'meal', description: 'ثبت غذا (اسم + کالری)' },
    { command: 'workout', description: 'تمرین امروز / ثبت تمرین' },
    { command: 'plan', description: 'پلن تغذیه' },
    { command: 'report', description: 'گزارش امروز' },
    { command: 'weekly', description: 'گزارش هفتگی و الگوها' },
    { command: 'patterns', description: 'الگوهای کشف‌شده' },
    { command: 'privacy', description: 'حریم خصوصی و رضایت‌ها' },
    { command: 'pause', description: 'توقف چک‌این‌ها' },
    { command: 'resume', description: 'ادامهٔ چک‌این‌ها' },
    { command: 'snooze', description: 'یک ساعت بعداً' },
    { command: 'help', description: 'راهنما' },
    { command: 'crisis', description: 'منابع اضطراری (AU)' },
  ]);

  if (cfg.TELEGRAM_MODE === 'webhook') {
    if (!cfg.TELEGRAM_WEBHOOK_URL || !cfg.TELEGRAM_WEBHOOK_SECRET) {
      throw new Error('webhook mode requires TELEGRAM_WEBHOOK_URL and TELEGRAM_WEBHOOK_SECRET');
    }
    const { webhookCallback } = await import('grammy');
    const Fastify = (await import('fastify')).default;
    const app = Fastify({ logger: false });
    const handler = webhookCallback(bot, 'fastify', { secretToken: cfg.TELEGRAM_WEBHOOK_SECRET });
    app.post('/webhook/telegram', async (req, reply) => handler(req, reply));
    app.get('/health', async () => ({ ok: true, mode: 'webhook' }));
    await bot.api.setWebhook(cfg.TELEGRAM_WEBHOOK_URL, {
      secret_token: cfg.TELEGRAM_WEBHOOK_SECRET,
      drop_pending_updates: false,
    });
    await app.listen({ port: 8081, host: '0.0.0.0' });
    log.info('WLOS bot up in WEBHOOK mode on :8081/webhook/telegram');
  } else {
    await bot.api.deleteWebhook({ drop_pending_updates: false });
    log.info('WLOS bot up in POLLING mode (development)');
    await bot.start();
  }
}

main().catch((err) => {
  log.error(err, 'bot crashed');
  process.exit(1);
});
