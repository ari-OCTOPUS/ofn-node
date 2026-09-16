# Lab enrich propose (Pi) 2026-08-24

## Complete-ish
- command-trust bound + E2E VERIFIED (EDGE-NEXT M1)
- doctor blocking ISOLATED/frozen-obs (M2) + soft-unlock accepted in doctor
- gateway allowlist freeze v1 diagnostics-only (M3)
- homeo/metacontrol authority mirror PERMITTED_SOFTWARE_A0+SOFTWARE_LATCH
- MQTT loopback 127.0.0.1:1883 WAN closed
- feeds live ok=6/7 fail=[{'name': 'timeapi_io_sydney', 'error': '<urlopen error [Errno 104] Connection reset by peer>'}]
- bus=CONNECTED ARMED=False soft_auth=PERMITTED_SOFTWARE_A0
- doctor_status=PASS blocking=[]

## Thin
- observation_age metric MISSING on :9101 (count=0)
- THERMAL quarantine still present: ['OCT-SENSE-053.THERMAL-RANGE_CHECK.json', 'wave01-range.json']
- physical estop/safety_mcu ABSENT (HOLD ? do not buy this enrich)
- homeo_ok intermittent / prediction_calibration unknown
- boot_report.json not live SoT (ancient)
- non-diag gateway cmds dark by freeze design; laptop NATS direct timeout
- NATS octopus-core E2E creds lifecycle / broader Core ACL

## Next 3 (safe)
1. **E1_OBS_AGE_METRIC** ? Expose observation_age on stability :9101 (reversible_code)
   - why: doctor informational gap; closes yellow driver without ARM
   - how: derive ages from existing evidence/snapshot stamps in stability_monitor; publish octopus_sensor_observation_age_seconds; prove curl; keep ARMED=false
2. **E2_THERMAL_QUARANTINE_TRIAGE** ? Readonly triage THERMAL quarantine then optional reversible clear (readonly_then_reversible)
   - why: yellow quarantine_present; may be stale residue
   - how: diff quarantine JSON vs live thermal reading; if false-positive/stale, move to quarantine/.cleared-YYYYMMDD (not delete) + evidence receipt; no PWM
3. **E3_FEEDS_QUALITY_SOAK** ? Readonly feeds quality pack (per-feed latency/fail taxonomy) (readonly)
   - why: feeds 7/7 count-complete but quality/soak still soft in undiscovered
   - how: 15?30m sample readings[] + last_run_ts; write FEEDS-QUALITY.json; no mutates