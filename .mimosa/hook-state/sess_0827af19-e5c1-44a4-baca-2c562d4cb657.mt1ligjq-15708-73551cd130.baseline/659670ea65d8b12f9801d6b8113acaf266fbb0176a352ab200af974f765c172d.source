// anz-import.js — Importer برای ANZ "PS Export" CSV → ledger (draft-only).
//
// چه می‌کند:
//   1. CSV بانک را می‌خواند (schema همان export فعلی: ...,Amount,...,Closing Balance,...,ID).
//   2. dedup روی ستون ID (idempotent — import دوباره رکورد تکراری نمی‌سازد).
//   3. GST درست: مبلغِ GST-inclusive ⟵ gst = total/11 (نه total*0.10)؛ خارجی/بهره/حقوق ⟵ 0.
//   4. دسته‌بندی draft با نگاشت فروشنده + جداسازی business/personal.
//   5. پرچم انطباق: Div7A (associate)، پرداخت بدون ABN (>$75)، تراکنش ≥ $10k.
//   6. مغایرت‌گیری با Closing Balance.
//
// خروجی = گزارش draft (JSON + متن). هیچ‌چیز به business_transactions نوشته نمی‌شود
// تا انسان verdict بدهد (ARCHITECT_CHARTER §Security Gate + §1). هیچ secret/شبکه‌ای درکار نیست.
//
// اجرا:  node anz-import.js <path-to-export.csv>
// تست:  node anz-import.test.js

'use strict';
const fs = require('fs');
const path = require('path');
const cfg = require('./config');

const round2 = (x) => Math.round((x + Number.EPSILON) * 100) / 100;

// --- CSV parser (فیلدهای کوتیشن‌دار با کاما را درست می‌خواند) ---
function parseCsv(text) {
  const rows = [];
  let field = '', row = [], inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') { inQuotes = false; }
      else { field += c; }
    } else if (c === '"') { inQuotes = true; }
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      if (field !== '' || row.length) { row.push(field); rows.push(row); row = []; field = ''; }
    } else { field += c; }
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  if (!rows.length) return [];
  const headers = rows[0].map((h) => h.trim());
  return rows.slice(1).map((r) => {
    const o = {};
    headers.forEach((h, idx) => { o[h] = (r[idx] ?? '').trim(); });
    return o;
  });
}

const isBusiness = (row) => cfg.BUSINESS_ACCOUNTS.includes(row.Account);

function matchVendor(row) {
  const m = (row.Merchant || '').toLowerCase();
  return cfg.VENDOR_MAP.find((v) => m.includes(v.match)) || null;
}

function isGstFree(row, vendorHit) {
  if ((row.Currency || 'AUD').toUpperCase() !== 'AUD') return true;       // خارجی
  if (vendorHit && vendorHit.gstFree) return true;
  const hay = `${row.Merchant} ${row.Category} ${row.Note || ''}`.toLowerCase();
  return cfg.GST_FREE_HINTS.some((h) => hay.includes(h));
}

// مبلغ ورودی GST-inclusive است → gst=total/11 ، net=total-gst (ex-GST برای schema فعلی).
function computeGst(grossInclusive, gstFree) {
  if (gstFree || !grossInclusive) return { gst: 0, net: round2(grossInclusive) };
  const gst = round2(grossInclusive / 11);
  return { gst, net: round2(grossInclusive - gst) };
}

function suggestCategory(row) {
  const hit = matchVendor(row);
  if (hit) return { category: hit.category, scope: hit.scope, confidence: 0.9 };
  // پرداخت به associate بدون نگاشت فروشنده → درآمد/برداشت، دست انسان
  return { category: 'Uncategorised', scope: isBusiness(row) ? 'business' : 'personal', confidence: 0.3 };
}

function detectFlags(row) {
  const flags = [];
  const business = isBusiness(row);
  const amount = Number(row.Amount);
  const gross = Math.abs(amount);
  const isExpense = amount < 0;
  const hay = `${row.Merchant} ${row.Note || ''}`.toLowerCase();

  // Div 7A: پرداخت از حساب بیزنس به associate (نام کوچک یا کامل)
  const assoc = cfg.ASSOCIATES.find((a) => {
    const parts = a.toLowerCase().split(' ');
    return parts.some((p) => p.length > 2 && hay.includes(p));
  });
  if (assoc && business && isExpense) flags.push(`div7a_drawing:${assoc}`);

  // پرداخت بیزنسِ هزینه‌ای بالای آستانه بدون اطلاعات ABN
  if (business && isExpense && gross > cfg.ABN_THRESHOLD) flags.push('no_abn_check');

  // آستانه AUSTRAC
  if (gross >= cfg.AUSTRAC_THRESHOLD) flags.push('austrac_10k');

  return flags;
}

function processRow(row) {
  const amount = Number(row.Amount);
  const gross = Math.abs(amount);
  const vendorHit = matchVendor(row);
  const gstFree = isGstFree(row, vendorHit);
  const { gst, net } = computeGst(gross, gstFree);
  const cat = suggestCategory(row);
  return {
    bank_id: row.ID,
    date: row.Date,
    account: row.Account,
    merchant: row.Merchant,
    type: amount < 0 ? 'Expense' : 'Income',
    gross_inclusive: round2(gross),
    amount_ex_gst: net,
    gst_amount: gst,
    gst_free: gstFree,
    suggested_category: cat.category,
    scope: cat.scope,
    confidence: cat.confidence,
    flags: detectFlags(row),
    closing_balance: row['Closing Balance'] !== '' ? Number(row['Closing Balance']) : null,
  };
}

// مغایرت‌گیری: برای هر حساب، به‌ترتیب زمان، Δ Closing Balance باید == مبلغ تراکنش باشد.
function reconcile(rows) {
  const byAcc = {};
  rows.forEach((r) => { (byAcc[r.Account] ||= []).push(r); });
  const report = [];
  for (const [acc, list] of Object.entries(byAcc)) {
    const ordered = list
      .filter((r) => r['Closing Balance'] !== '')
      .sort((a, b) => (a.Date < b.Date ? -1 : a.Date > b.Date ? 1 : Number(a.ID) - Number(b.ID)));
    for (let i = 1; i < ordered.length; i++) {
      const prev = Number(ordered[i - 1]['Closing Balance']);
      const cur = Number(ordered[i]['Closing Balance']);
      const expected = round2(cur - prev);
      const actual = round2(Number(ordered[i].Amount));
      if (Math.abs(expected - actual) > 0.01) {
        report.push({ account: acc, date: ordered[i].Date, id: ordered[i].ID,
                      expected_delta: expected, txn_amount: actual, mismatch: round2(expected - actual) });
      }
    }
  }
  return report;
}

function buildDraft(rows) {
  const drafts = rows.map(processRow);
  const flagged = drafts.filter((d) => d.flags.length);
  return {
    generated_at: new Date().toISOString(),
    note: 'DRAFT — needs human verdict. Nothing written to the ledger.',
    total_rows: drafts.length,
    business_rows: drafts.filter((d) => d.scope === 'business').length,
    review_queue: drafts.filter((d) => d.confidence < 0.85),
    flags: flagged,
    reconciliation: reconcile(rows),
    drafts,
  };
}

// --- main (فقط هنگام اجرای مستقیم؛ better-sqlite3 lazy تا تست بدون DB اجرا شود) ---
function main() {
  const csvPath = process.argv[2];
  if (!csvPath) { console.error('استفاده: node anz-import.js <export.csv>'); process.exit(1); }
  const text = fs.readFileSync(csvPath, 'utf8');
  const rows = parseCsv(text);

  // dedup + ذخیره خام (idempotent) در جدول مجزا؛ business_transactions دست‌نخورده می‌ماند.
  let newCount = rows.length, dbInfo = 'DB skipped';
  try {
    const Database = require('better-sqlite3');
    const db = new Database(path.join(__dirname, '..', 'app', 'financial_tracker.db'));
    db.exec(`CREATE TABLE IF NOT EXISTS bank_import (
      bank_id TEXT PRIMARY KEY, date TEXT, account TEXT, merchant TEXT,
      amount REAL, closing_balance REAL, raw_json TEXT, imported_at DATETIME DEFAULT CURRENT_TIMESTAMP)`);
    const ins = db.prepare(`INSERT OR IGNORE INTO bank_import
      (bank_id,date,account,merchant,amount,closing_balance,raw_json) VALUES (?,?,?,?,?,?,?)`);
    newCount = 0;
    const tx = db.transaction((rs) => rs.forEach((r) => {
      const info = ins.run(r.ID, r.Date, r.Account, r.Merchant, Number(r.Amount),
        r['Closing Balance'] === '' ? null : Number(r['Closing Balance']), JSON.stringify(r));
      newCount += info.changes;
    }));
    tx(rows);
    dbInfo = `bank_import: ${newCount} new / ${rows.length - newCount} duplicate skipped`;
  } catch (e) { dbInfo = `DB layer skipped (${e.code || e.message}) — draft still produced`; }

  const draft = buildDraft(rows);
  const outDir = path.join(__dirname, 'out');
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, `draft-${new Date().toISOString().slice(0, 10)}.json`);
  fs.writeFileSync(outFile, JSON.stringify(draft, null, 2));

  console.log('ANZ import (DRAFT-only) ─────────────');
  console.log(dbInfo);
  console.log(`rows: ${draft.total_rows} | business: ${draft.business_rows} | need review: ${draft.review_queue.length}`);
  console.log(`compliance flags: ${draft.flags.length} | reconciliation mismatches: ${draft.reconciliation.length}`);
  console.log(`draft written: ${outFile}`);
  console.log('⚠️ همه draft است — هیچ‌چیز بدون verdict انسانی به دفتر نمی‌رود.');
}

module.exports = { parseCsv, isBusiness, matchVendor, isGstFree, computeGst,
  suggestCategory, detectFlags, processRow, reconcile, buildDraft, round2 };

if (require.main === module) main();
