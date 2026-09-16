import { z } from 'zod';

const EnvSchema = z.object({
  APP_ENV: z.enum(['development', 'production', 'test']).default('development'),
  LOG_LEVEL: z.string().default('info'),

  TELEGRAM_BOT_TOKEN: z.string().default(''),
  TELEGRAM_MODE: z.enum(['polling', 'webhook']).default('polling'),
  TELEGRAM_WEBHOOK_URL: z.string().default(''),
  TELEGRAM_WEBHOOK_SECRET: z.string().default(''),
  TELEGRAM_OWNER_CHAT_ID: z.string().default(''),

  DATABASE_URL: z.string().default('postgresql://wlos:wlos@localhost:5432/wlos?schema=public'),
  REDIS_URL: z.string().default('redis://localhost:6379'),

  FUGU_ENABLED: z
    .string()
    .default('true')
    .transform((v) => v === 'true' || v === '1'),
  SAKANA_API_KEY: z.string().default(''),
  SAKANA_BASE_URL: z.string().default('https://api.sakana.ai/v1'),
  FUGU_MODEL_DEFAULT: z.string().default('fugu'),
  FUGU_MODEL_DEEP: z.string().default('fugu-ultra'),
  FUGU_MONTHLY_TOKEN_BUDGET: z.coerce.number().default(2_000_000),
  OPENAI_API_KEY: z.string().default(''),
  ANTHROPIC_API_KEY: z.string().default(''),

  TZ_DEFAULT: z.string().default('Australia/Sydney'),
  DAILY_MESSAGE_CAP: z.coerce.number().default(20),
  QUIET_HOURS_START: z.string().default('00:00'),
  QUIET_HOURS_END: z.string().default('07:00'),
  DEFAULT_CHECKINS_MIN: z.coerce.number().default(3),
  DEFAULT_CHECKINS_MAX: z.coerce.number().default(6),

  COACH_API_KEY: z.string().default(''),
  MINI_APP_URL: z.string().default(''),
});

export type AppConfig = z.infer<typeof EnvSchema>;

let cached: AppConfig | null = null;

export function loadConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  if (cached) return cached;
  cached = EnvSchema.parse(env);
  return cached;
}

/** test helper */
export function resetConfigCache(): void {
  cached = null;
}
