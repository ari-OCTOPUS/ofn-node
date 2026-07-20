# mining_os — ACTIVATION (رانبوکِ مالک)

> وضعیت: **وصل‌شده، flag-off، uncommitted.** تا این قدم‌ها را نزنی هیچ رفتاری تغییر نمی‌کند (flag-off = بایت‌به‌بایت).

## چه چیزی از قبل انجام شده (این جلسه، ارگانیسم owner-stopped)
- بستهٔ `mining_os/` در `03 - Projects/Mining/mining_os/` (۲۰ تستِ سبز، pure-stdlib).
- هوکِ additive/flag-off در `_ops/organism.py:712` (کنارِ Ziman/Project-F).
- راستی‌آزمایی: `py_compile` ✅ · flag-off بایت‌به‌بایت (فلگ در هیچ `.cmd` نیست) ✅ · flag-on smoke (`tick()` → skeleton، بدونِ crash) ✅.

## قدم‌های فعال‌سازی (روی ویندوز)
1. **Commit checkpoint** — git از سندباکس بلاک است ([[vault-sandbox-quirks]])، پس روی ویندوز:
   - تغییرها: `_ops/organism.py` (+۱۰ خطِ هوک)، `03 - Projects/Mining/mining_os/`، پوشهٔ `Mining-Deep-Scan-2026-07-19/`، و pointerهای `HANDOFF.md`/`PROJECT.md`.
   - پیام پیشنهادی: `agent-checkpoint: mining sub-OS wired flag-off + deep-scan`.
2. **(اختیاری) دادهٔ واقعی:** `mining_os/state/MINING-STATE.json` را با ناوگان/کوین/برقِ واقعی پر کن (اسکیما در `state.py`). تا آن‌موقع `live=False` (اسکلتِ صادق) درست است.
3. **روشن‌کردنِ فلگ‌ها:** در `OCTOPUS-flags.cmd`: `set OCTOPUS_WIRE_MINING_OS=1` (ضربانِ leg)، `set OCTOPUS_WIRE_MINING_UI=1` (منوی تلگرامِ Topic ⛏ + دستورِ `/mining`)، و (اختیاری) `set OCTOPUS_WIRE_MINING_VERDICT_SYNC=1` (سینکِ verdict به بلوکِ auto-managed در `VERDICT_QUEUE.md`). هر سه مستقل‌اند.
4. **ری‌استارت:** `_ops/STOP-ORGANISM` را بردار / ارگانیسم را ری‌استارت کن → هر beat، `mining_os.loop.tick` صدا زده می‌شود و snapshot در `mining_os/state/last-beat.json` می‌نشیند.

## خط‌قرمزها
- پول همیشه **P7** (`capability ∧ LIVE_ENABLED ∧ approval`). این فلگ فقط سنجش/گزارش است، هیچ خرجی.
- هرگز به `Ai bots/fleet` (SSH/subprocess) وصل نشو مگر پشتِ **P5+** و کارتِ تأیید.
- UI تلگرام (Topic ⛏، منوی ۶-گزینهٔ `mo:` + `/mining`) **پیاده و flag-off وصل شد** به `center.py` (۳ هوکِ additive، پشتِ `OCTOPUS_WIRE_MINING_UI`). verdictها به `mining_os/state/verdict-actions.jsonl` می‌روند. **سینکِ canonical پیاده شد** (`tg_mining.sync_verdicts_to_queue`): پشتِ فلگِ `OCTOPUS_WIRE_MINING_VERDICT_SYNC` (flag-off = دست‌نخورده)، append-only در بلوکِ `MINING-AUTO-VERDICTS` با dedup آخرین‌تصمیم — هرگز داغ‌ویرایشِ کورِ جدولِ انسانی. صفر لمسِ `center.py`؛ ۳۲ تستِ سبز.

## Rollback
- فلگ را خاموش کن (`=0`) — کافی است (flag-off = بایت‌به‌بایت).
- یا بلوکِ `_ops/organism.py:711-720` را بردار (additive و بی‌عارضه).
