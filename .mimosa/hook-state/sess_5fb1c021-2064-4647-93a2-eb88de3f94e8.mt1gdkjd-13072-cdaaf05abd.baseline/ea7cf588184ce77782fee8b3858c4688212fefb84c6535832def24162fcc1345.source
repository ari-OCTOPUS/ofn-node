import { createHmac, timingSafeEqual } from 'node:crypto';

/**
 * Telegram Mini App initData validation (server-side, per official docs):
 *   secret_key       = HMAC_SHA256(key="WebAppData", message=bot_token)
 *   data_check_string = sorted "key=value" lines excluding `hash`, joined by \n
 *   valid            ⇔ hex(HMAC_SHA256(secret_key, data_check_string)) == hash
 */

export interface InitDataResult {
  valid: boolean;
  reason?: 'missing_hash' | 'bad_signature' | 'expired';
  userId?: number;
  authDate?: number;
}

export function validateInitData(initData: string, botToken: string, maxAgeSeconds = 3600): InitDataResult {
  const params = new URLSearchParams(initData);
  const hash = params.get('hash');
  if (!hash) return { valid: false, reason: 'missing_hash' };
  params.delete('hash');

  const dataCheckString = [...params.entries()]
    .map(([k, v]) => `${k}=${v}`)
    .sort()
    .join('\n');

  const secretKey = createHmac('sha256', 'WebAppData').update(botToken).digest();
  const expected = createHmac('sha256', secretKey).update(dataCheckString).digest('hex');

  const a = Buffer.from(expected, 'hex');
  const b = Buffer.from(hash, 'hex');
  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    return { valid: false, reason: 'bad_signature' };
  }

  const authDate = Number(params.get('auth_date') ?? 0);
  if (maxAgeSeconds > 0 && authDate > 0) {
    const age = Math.floor(Date.now() / 1000) - authDate;
    if (age > maxAgeSeconds) return { valid: false, reason: 'expired', authDate };
  }

  let userId: number | undefined;
  try {
    const userJson = params.get('user');
    if (userJson) userId = (JSON.parse(userJson) as { id?: number }).id;
  } catch {
    /* user field optional */
  }
  return { valid: true, userId, authDate };
}

/** test helper: produce a signed initData string the way Telegram would */
export function signInitData(fields: Record<string, string>, botToken: string): string {
  const params = new URLSearchParams(fields);
  const dataCheckString = [...params.entries()]
    .map(([k, v]) => `${k}=${v}`)
    .sort()
    .join('\n');
  const secretKey = createHmac('sha256', 'WebAppData').update(botToken).digest();
  const hash = createHmac('sha256', secretKey).update(dataCheckString).digest('hex');
  params.set('hash', hash);
  return params.toString();
}
