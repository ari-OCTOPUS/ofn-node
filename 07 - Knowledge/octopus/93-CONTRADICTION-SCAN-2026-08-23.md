---
title: Contradiction Scan 2026-08-23
tags: [octopus, contradiction, sensorium]
updated: 20260822T221832Z
---

# Contradiction Scan — Orange Pi

Read-only scan. No WAVE0 arm. No secrets.

## Ranked contradictions

### C4_MQTT_SCOPE (medium)
- Claim: Some docs may still say MQTT CLOSED or imply WAN/open
- Reality: mosquitto active; listen=LISTEN 0      100        127.0.0.1:1883      0.0.0.0:*    users:(("mosquitto",pid=382176,fd=5)); loopback_only=True
- Recommended: SoT: local 127.0.0.1:1883 auth-required; not WAN

### C5_ESP32_PHASE_B_DEFERRED (medium)
- Claim: Any Phase B ESP32 PASS/connected wording
- Reality: usb_serial=NONE; Phase B deferred; inet feeds only
- Recommended: Keep Phase B SKIP until hardware present

### C8_SOFT_VS_PHYSICAL_ESTOP (medium)
- Claim: Risk: soft unlock mistaken for physical Path H PASS
- Reality: latch={'asserted': False, 'reason': 'SOFT_UNLOCK_ACTIVE_LATCH_CLEARED', 'channel': 'SOFTWARE_LATCH'}; lock={'resolved_scope': 'SOFT_UNLOCK_SOFTWARE_A0_LATCH', 'hardware': 'DEFERRED_NEED_PHYSICAL_ESTOP', 'actuator_authority': 'PERMITTED_SOFTWARE_A0', 'estop_channel_board': 'SOFTWARE_LATCH', 'gpio_pwm': 'FORBIDDEN_ZERO_THIS_RUN', 'mqtt': 'SEPARATE_ENABLE', 'unlock_path_H': 'NOT_PERFORMED_NO_INVENT'}; board=safety_state: SOFTWARE_ONLY safety_mcu: ABSENT actuator_authority: PERMITTED_SOFTWARE_A0 estop_channel: SOFTWARE_LATCH max_autonomy_level: OBSERVE_ONLY
- Recommended: Always label physical Path H DEFERRED; soft latch ≠ operator_at_estop

### C9_FEEDS_NOT_ESP32 (low)
- Claim: Internet feeds might be read as ESP32 sensors
- Reality: allowlist_n=7 last_ok=7 source=EXTERNAL_PUBLIC_FEED
- Recommended: Keep sensor_id OCT-FEED-* naming; Phase B separate

### C1_TELEGRAM_NOT_ON_PI (high)
- Claim: Laptop Board2/Studio Telegram wording may be read as live Pi OCTOPUS
- Reality: No live Telegram on sensorium Pi path; ARMED=false
- Recommended: Keep Telegram Board2-only unless Pi EXECUTE prove

