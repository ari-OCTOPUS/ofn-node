/**
 * Redaction before ANY text leaves WLOS toward an LLM.
 * Strips direct identifiers; category exclusion happens earlier in
 * @wlos/memory packet building (consent-aware).
 */

const REPLACERS: Array<[RegExp, string]> = [
  [/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[email]'],
  [/\+?\d[\d\s-]{7,14}\d/g, '[phone]'],
  [/\b\d{6,12}\b/g, '[id]'], // telegram ids, account numbers
  [/@[A-Za-z0-9_]{4,32}/g, '[handle]'],
  [/(?:\d{1,3}\.){3}\d{1,3}/g, '[ip]'],
];

export function redactIdentifiers(text: string, extraNames: string[] = []): string {
  let out = text;
  for (const [re, sub] of REPLACERS) out = out.replace(re, sub);
  for (const name of extraNames) {
    if (name.trim().length < 2) continue;
    out = out.replaceAll(name, '[name]');
  }
  return out;
}
