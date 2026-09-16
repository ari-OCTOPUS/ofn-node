# TERRITORY-REPORT — 4d_system

findings: **16** · classes: DEBT_HIDDEN 5 · RULING_UNEXECUTED 4 · OPEN_WORK 4 · DOC_RUNTIME_DISCREPANCY 2 · ABANDONED 1

## top findings (rank order)

- **[4D-16] r10.0 RULING_UNEXECUTED** VERDICT_QUEUE: all 4 governing verdicts (30-day run, Telegram, self-code risk, budget cap) still 'open'
  - `4d_system/VERDICT_QUEUE.md` · `line 5: | 4D-V1 | اجرای ۳۰ روزه؟ | yes/no/later | open | daemon run |`
- **[4D-18] r10.0 OPEN_WORK** 24/7 self-heal supervisor promised but never installed: no supervisor_log.jsonl/logs, no CONTROL_PLANE flags, and dead d
  - `4d_system/SELF_HEAL.md` · `line 31: **autostart**: روی `scripts\install_supervisor_task.bat` دوبار کلیک کن`
- **[4D-17] r7.0 OPEN_WORK** Telegram owner channel never configured: empty token in .env, every decision packet 'queued (not-configured)', 100 diges
  - `4d_system/.env` · `line 28: TELEGRAM_BOT_TOKEN=`
- **[4D-19] r7.0 RULING_UNEXECUTED** B10 standalone git init ordered 'owner must run once on Windows' - never executed; contradicts MANIFEST 'has own .git' a
  - `4d_system/BACKLOG.md` · `line 83: **باید خودت یک‌بار روی ویندوز اجرایش کنی**`
- **[4D-20] r7.0 ABANDONED** Promised one-month autonomous run lasted 6 days (2026-08-15 to 2026-08-21) and was never concluded; month-end evaluation
  - `4d_system/outputs/daemon_state.json` · `line 6: "last_tick_at": "2026-08-21T08:07:28"`
- **[4D-22] r7.0 RULING_UNEXECUTED** Kill-switch unimplemented: KillSwitchCommand 'v1: always False remains', no live execution path despite v0-v5 ladder dec
  - `4d_system/ARCHITECTURAL_SCAN_REPORT.md` · `line 268: contracts.py defines KillSwitchCommand but notes "v1: always False remains"`
- **[4D-24] r6.8 DEBT_HIDDEN** TCB guards itself with no external validator/checksum auditor - acknowledged single point of failure never remedied
  - `4d_system/ARCHITECTURAL_SCAN_REPORT.md` · `line 262: guardrails.py guards itself. No external validator or checksum auditor was found`
- **[4D-26] r6.8 DEBT_HIDDEN** BLACK-BOX.md relocation target F:\Black Box does not exist and restore bundle _history/nbb-cp-full-history.bundle is gon
  - `4d_system/BLACK-BOX.md` · `line 3: Relocated to `F:\Black Box` on **2026-07-11**. This is now a **standalone git repo**`
- **[4D-21] r5.0 OPEN_WORK** B11 LLM-stack migration decision requires >=30 shadow records; llm_shadow.jsonl stuck at 6 records since 2026-07-11
  - `4d_system/BACKLOG.md` · `line 84: معیارِ تصمیمِ فاز ۲ (پس از ≥۳۰ رکورد)`
- **[4D-23] r5.0 DEBT_HIDDEN** Self-code approval pipeline never exercised end-to-end: proposals sandbox empty since creation, 0 proposals in final dae
  - `4d_system/ARCHITECTURAL_SCAN_REPORT.md` · `line 263: outputs/self_code_proposals/ is empty. Self-code pipeline has not been end-to-end tested in producti`
- **[4D-27] r5.0 RULING_UNEXECUTED** B6 SOG integration: steps 2-3 draft-only behind 'boss choice'; 3 owner decisions open (boss, nbb_cp install, Desktop-C f
  - `4d_system/docs/B6-SOG-INTEGRATION-STEP1.md` · `line 49: ## ۵. تصمیم‌های باز (مالک — در AGENT_QUESTIONS ثبت شد)`
- **[4D-29] r5.0 OPEN_WORK** Second-Brain Super-Governor: CLAUDE.md still stamps spec 'هنوز ساخته نشده'; Phase 2/3 blocked on owner GO (vault path, F
  - `4d_system/CLAUDE.md` · `line 10: **SPEC است، هنوز ساخته نشده.**`

## coverage

- inventory files_total (md/json/txt ≤2MB): 323
- read: ~281 pattern-grepped + 28 deep
- method: docs deep-read; code marker-grep; outputs sampled
- excluded: python internals, venv/.pytest caches, npy/bin
