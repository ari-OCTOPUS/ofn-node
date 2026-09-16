# OWNER BRIEF — OCTOPUS EDGE NEXT (2026-08-23)

## خلاصه (فارسی)
- **اعتماد فرمان (Command-Trust)** وصل شد: امضای root-v2 روی لپ‌تاپ؛ روی برد فقط public. تست E2E از UNVERIFIED به **VERIFIED**.
- **Doctor** دیگر وضعیت ISOLATED یا مشاهدهٔ یخ‌زده را «سالم» نشان نمی‌دهد (چک blocking جدید).
- **Allowlist دروازه v1** فقط `COLLECT_DIAGNOSTICS` و `REQUEST_DIAGNOSTIC`؛ ARM و `mutates=true` رد می‌شوند.
- **Soak ~14m** خواندنی: bus=CONNECTED، feeds≈7، بدون OOM؛ وضعیت کلی **DEGRADED** به‌خاطر نوسان کوتاه homeo_ok.
- **قفل‌ها:** ARMED=false؛ بدون PWM؛ بدون خرید e-stop فیزیکی؛ کلید خصوصی root هرگز روی Pi نیست.

## HOLDs
- e-stop فیزیکی هنوز ABSENT (نرم‌افزاری قبول شده).
- homeo هنوز `actuator_authority=NONE` می‌گوید در حالی که board soft-unlock = PERMITTED_SOFTWARE_A0.
- اتصال مستقیم لپ‌تاپ به NATS:4222 تایم‌اوت شد (E2E از روی Pi با فرمان امضاشده از لپ‌تاپ).

## Next pick
1. هم‌تراز کردن mirror هومئوستازی با soft-unlock (بدون ARM).
2. اختیاری: Path H فیزیکی وقتی owner دوباره GO خرید بدهد.
3. ARMED=false بماند تا GO صریح owner.

## English paths
- Pack: `F:\backup\06-EVIDENCE\OCTOPUS-EDGE-NEXT-2026-08-23\`
- Receipt: `F:\backup\06-EVIDENCE\OCTOPUS-EDGE-NEXT-2026-08-23\RECEIPT.json`
- Pi session: `/var/lib/octopus/evidence/session-edge-next-20260823/`
- M1: `...\m1-command-trust\`
- M2: `...\m2-obs-harden\`
- M3: `...\m3-allowlist\`
- M4: `...\m4-soak\`
- Trust bind: `/etc/octopus/trust/command_trust.json` + `command.pub`
- Allowlist: `/opt/octopus/current/src/octopus_sensorium/policy/command_gate.py` (freeze v1)
- BL-01: `/var/lib/octopus/evidence/session-edge-gateway-20260823/NATS_CONTRACT_BL01.json`

## Forbidden still in force
ARMED=true, PWM, parts buy, unrestricted TG, invent, force-git, secrets paste.
