/** Australian support resources — product config for Sydney, Australia. */

export interface CrisisResource {
  name: string;
  phone: string;
  note?: string;
}

export const AU_RESOURCES: CrisisResource[] = [
  { name: 'Emergency (اورژانس)', phone: '000' },
  { name: 'Lifeline', phone: '13 11 14', note: '24/7' },
  { name: 'Suicide Call Back Service', phone: '1300 659 467', note: '24/7' },
  { name: 'Beyond Blue', phone: '1300 22 4636', note: '24/7' },
  { name: 'MensLine Australia', phone: '1300 78 99 78' },
  { name: 'Kids Helpline', phone: '1800 55 1800', note: 'زیر ۲۵ سال' },
  { name: 'Butterfly Foundation (اختلالات خوردن)', phone: '1800 33 4673', note: '8am–midnight AEST' },
];

export const MEDICAL_DISCLAIMER_FA =
  'این اپ جایگزین مشاورهٔ پزشکی، روان‌شناسی یا تغذیهٔ تخصصی نیست. اگر نگرانی سلامتی داری، لطفاً با متخصص واجد شرایط تماس بگیر.';

export function formatResourcesFa(): string {
  return AU_RESOURCES.map((r) => `• ${r.name}: ${r.phone}${r.note ? ` (${r.note})` : ''}`).join('\n');
}
