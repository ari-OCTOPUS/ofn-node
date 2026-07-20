const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
const ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩';

/** Convert Persian/Arabic-Indic digits to ASCII; normalize separators. */
export function normalizeDigits(input: string): string {
  let out = '';
  for (const ch of input) {
    const p = PERSIAN_DIGITS.indexOf(ch);
    const a = ARABIC_DIGITS.indexOf(ch);
    if (p >= 0) out += String(p);
    else if (a >= 0) out += String(a);
    else if (ch === '٫') out += '.'; // Arabic decimal separator
    else if (ch === '،') out += ','; // Arabic comma
    else out += ch;
  }
  return out;
}

/**
 * Normalize Persian text for matching/search keys.
 * Keeps ZWNJ (U+200C — meaningful in Persian) but strips other invisibles;
 * unifies Arabic yeh/kaf variants to Persian forms.
 */
export function normalizeFa(input: string): string {
  return input
    .replace(/[​‎‏﻿]/g, '')
    .replace(/[يى]/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/ۀ/g, 'هٔ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Search key: normalized, digit-unified, lowercased, ZWNJ → space. */
export function searchKey(input: string): string {
  return normalizeDigits(normalizeFa(input)).replace(/‌/g, ' ').toLowerCase();
}

export function toPersianDigits(n: number | string): string {
  return String(n).replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)] as string);
}
