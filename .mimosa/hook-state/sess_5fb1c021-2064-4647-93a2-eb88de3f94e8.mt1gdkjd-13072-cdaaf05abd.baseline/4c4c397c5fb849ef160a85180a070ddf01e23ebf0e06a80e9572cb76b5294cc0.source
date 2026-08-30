import { DateTime, Interval } from 'luxon';

export const DEFAULT_TZ = 'Australia/Sydney';

/** Local calendar day key (YYYY-MM-DD) for a UTC instant in the user's timezone. */
export function localDayKey(utc: Date, tz: string = DEFAULT_TZ): string {
  return DateTime.fromJSDate(utc, { zone: 'utc' }).setZone(tz).toISODate() ?? '';
}

/**
 * UTC bounds of a local calendar day. DST-safe: on transition days the
 * interval is 23h or 25h long — daily boundaries are ALWAYS local midnight.
 */
export function localDayBoundsUtc(dayKey: string, tz: string = DEFAULT_TZ): { start: Date; end: Date } {
  const start = DateTime.fromISO(dayKey, { zone: tz }).startOf('day');
  const end = start.plus({ days: 1 });
  return { start: start.toUTC().toJSDate(), end: end.toUTC().toJSDate() };
}

/** Minutes since local midnight for a UTC instant. */
export function localMinutesOfDay(utc: Date, tz: string = DEFAULT_TZ): number {
  const dt = DateTime.fromJSDate(utc, { zone: 'utc' }).setZone(tz);
  return dt.hour * 60 + dt.minute;
}

/** Parse "HH:MM" to minutes-of-day. Accepts Persian digits. */
export function parseHHMM(s: string): number {
  const m = /^(\d{1,2}):(\d{2})$/.exec(s.trim());
  if (!m) throw new Error(`Invalid HH:MM: ${s}`);
  const h = Number(m[1]);
  const min = Number(m[2]);
  if (h > 23 || min > 59) throw new Error(`Invalid HH:MM: ${s}`);
  return h * 60 + min;
}

/**
 * Quiet-hours check. Window may cross midnight (e.g. 22:00→06:00).
 * WLOS default is 00:00→07:00 Sydney.
 */
export function isInQuietHours(
  utc: Date,
  tz: string = DEFAULT_TZ,
  startHHMM = '00:00',
  endHHMM = '07:00',
): boolean {
  const t = localMinutesOfDay(utc, tz);
  const start = parseHHMM(startHHMM);
  const end = parseHHMM(endHHMM);
  if (start === end) return false; // zero-length window disables quiet hours
  if (start < end) return t >= start && t < end;
  return t >= start || t < end; // crosses midnight
}

/**
 * UTC instant for a given local day + CLOCK minutes-of-day (not elapsed time).
 * DST-safe: "07:30 local" means 07:30 on the wall clock even on 23h/25h days.
 * Nonexistent times (inside a spring-forward gap) shift to the next valid
 * instant; ambiguous times resolve to the first occurrence — both fine for
 * check-in scheduling.
 */
export function utcAtLocalMinutes(dayKey: string, minutesOfDay: number, tz: string = DEFAULT_TZ): Date {
  const dt = DateTime.fromISO(dayKey, { zone: tz }).set({
    hour: Math.floor(minutesOfDay / 60) % 24,
    minute: minutesOfDay % 60,
    second: 0,
    millisecond: 0,
  });
  return dt.toUTC().toJSDate();
}

/** Length of a local day in minutes (1380/1440/1500 around DST transitions). */
export function localDayLengthMinutes(dayKey: string, tz: string = DEFAULT_TZ): number {
  const { start, end } = localDayBoundsUtc(dayKey, tz);
  return Interval.fromDateTimes(DateTime.fromJSDate(start), DateTime.fromJSDate(end)).length('minutes');
}

export function addDaysToKey(dayKey: string, days: number, tz: string = DEFAULT_TZ): string {
  return DateTime.fromISO(dayKey, { zone: tz }).plus({ days }).toISODate() ?? dayKey;
}

export function formatSydney(utc: Date, tz: string = DEFAULT_TZ): string {
  return DateTime.fromJSDate(utc, { zone: 'utc' }).setZone(tz).toFormat('yyyy-LL-dd HH:mm');
}
