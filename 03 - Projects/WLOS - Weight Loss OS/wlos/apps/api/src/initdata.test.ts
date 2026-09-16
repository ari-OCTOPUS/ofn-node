import { describe, expect, it } from 'vitest';
import { signInitData, validateInitData } from './initdata.js';

const TOKEN = '1234567:TEST_TOKEN_NOT_REAL';

describe('Telegram Mini App initData validation', () => {
  it('accepts a correctly signed payload', () => {
    const initData = signInitData(
      {
        auth_date: String(Math.floor(Date.now() / 1000)),
        query_id: 'AAA',
        user: JSON.stringify({ id: 42, first_name: 'ari' }),
      },
      TOKEN,
    );
    const r = validateInitData(initData, TOKEN);
    expect(r.valid).toBe(true);
    expect(r.userId).toBe(42);
  });

  it('rejects a tampered payload', () => {
    const initData = signInitData(
      { auth_date: String(Math.floor(Date.now() / 1000)), user: JSON.stringify({ id: 42 }) },
      TOKEN,
    );
    const tampered = initData.replace('%22id%22%3A42', '%22id%22%3A43');
    expect(validateInitData(tampered, TOKEN).valid).toBe(false);
  });

  it('rejects a payload signed with a different bot token', () => {
    const initData = signInitData({ auth_date: String(Math.floor(Date.now() / 1000)) }, 'other:token');
    expect(validateInitData(initData, TOKEN)).toMatchObject({ valid: false, reason: 'bad_signature' });
  });

  it('rejects stale auth_date', () => {
    const initData = signInitData({ auth_date: String(Math.floor(Date.now() / 1000) - 7200) }, TOKEN);
    expect(validateInitData(initData, TOKEN, 3600)).toMatchObject({ valid: false, reason: 'expired' });
  });

  it('rejects missing hash', () => {
    expect(validateInitData('auth_date=1', TOKEN)).toMatchObject({ valid: false, reason: 'missing_hash' });
  });
});
