import { describe, expect, it } from 'vitest';
import {
  addDaysToKey,
  isInQuietHours,
  localDayBoundsUtc,
  localDayKey,
  localDayLengthMinutes,
  utcAtLocalMinutes,
} from './time.js';
import { normalizeDigits, normalizeFa, searchKey, toPersianDigits } from './persian.js';
import { mulberry32, randInt, seedFromString } from './rng.js';

describe('time (Australia/Sydney, DST-safe)', () => {
  it('computes local day key across UTC boundary', () => {
    // 2026-07-19 23:30 UTC = 2026-07-20 09:30 AEST (winter, UTC+10)
    expect(localDayKey(new Date('2026-07-19T23:30:00Z'))).toBe('2026-07-20');
  });

  it('DST start day (2026-10-04) is 23h long', () => {
    expect(localDayLengthMinutes('2026-10-04')).toBe(23 * 60);
  });

  it('DST end day (2026-04-05) is 25h long', () => {
    expect(localDayLengthMinutes('2026-04-05')).toBe(25 * 60);
  });

  it('day bounds are exactly local midnight to midnight', () => {
    const { start, end } = localDayBoundsUtc('2026-07-20');
    expect(localDayKey(start)).toBe('2026-07-20');
    expect(localDayKey(new Date(end.getTime() - 1))).toBe('2026-07-20');
    expect(localDayKey(end)).toBe('2026-07-21');
  });

  it('quiet hours 00:00–07:00 detected in local time', () => {
    // 2026-07-20 03:00 Sydney = 2026-07-19 17:00 UTC
    expect(isInQuietHours(new Date('2026-07-19T17:00:00Z'))).toBe(true);
    // 08:00 Sydney
    expect(isInQuietHours(new Date('2026-07-19T22:00:00Z'))).toBe(false);
    // boundary: 07:00 exactly is allowed
    expect(isInQuietHours(new Date('2026-07-19T21:00:00Z'))).toBe(false);
  });

  it('quiet hours crossing midnight (22:00→06:00)', () => {
    const at = (h: string) => utcAtLocalMinutes('2026-07-20', Number(h.split(':')[0]) * 60);
    expect(isInQuietHours(at('23:00'), 'Australia/Sydney', '22:00', '06:00')).toBe(true);
    expect(isInQuietHours(at('05:00'), 'Australia/Sydney', '22:00', '06:00')).toBe(true);
    expect(isInQuietHours(at('12:00'), 'Australia/Sydney', '22:00', '06:00')).toBe(false);
  });

  it('utcAtLocalMinutes inverts localDayKey', () => {
    const utc = utcAtLocalMinutes('2026-10-04', 8 * 60); // DST start day, 08:00 local
    expect(localDayKey(utc)).toBe('2026-10-04');
  });

  it('addDaysToKey', () => {
    expect(addDaysToKey('2026-12-31', 1)).toBe('2027-01-01');
  });
});

describe('persian utils', () => {
  it('normalizes Persian and Arabic digits', () => {
    expect(normalizeDigits('۹۴٫۵ کیلو')).toBe('94.5 کیلو');
    expect(normalizeDigits('٨٠٠ کالری')).toBe('800 کالری');
  });

  it('normalizes Arabic yeh/kaf to Persian', () => {
    expect(normalizeFa('كيلو')).toBe('کیلو');
  });

  it('search key unifies everything', () => {
    expect(searchKey('  ناهار  ۸۰۰ ')).toBe('ناهار 800');
  });

  it('renders Persian digits', () => {
    expect(toPersianDigits(1950)).toBe('۱۹۵۰');
  });
});

describe('seeded rng', () => {
  it('is deterministic for the same seed', () => {
    const a = mulberry32(seedFromString('user1:2026-07-20'));
    const b = mulberry32(seedFromString('user1:2026-07-20'));
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });

  it('randInt stays in range', () => {
    const rng = mulberry32(42);
    for (let i = 0; i < 1000; i++) {
      const v = randInt(rng, 5, 9);
      expect(v).toBeGreaterThanOrEqual(5);
      expect(v).toBeLessThanOrEqual(9);
    }
  });
});
