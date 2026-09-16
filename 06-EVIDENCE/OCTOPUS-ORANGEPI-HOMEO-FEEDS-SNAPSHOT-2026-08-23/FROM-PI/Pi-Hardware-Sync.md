---
title: Pi Hardware Sync
tags: [octopus, sensorium, hardware, sync, wave0]
updated: 2026-08-23T02:43:00+10:00
---

# Pi Hardware Sync — sensorium-opi5pro

Synced from live board (sensoriom) after HOMEO-FEEDS-SNAPSHOT install.

## Identity
- Host: `sensorium-opi5pro` / DietPi / Orange Pi 5 Pro (rk3588s)
- LAN: `192.168.0.182`
- Stack: `/opt/octopus`, state `/var/lib/octopus`

## Safety / WAVE0 (as of 2026-08-23)
- `actuator_authority`: PERMITTED_SOFTWARE_A0
- `estop_channel`: SOFTWARE_LATCH (live; assert → NONE)
- Physical Path H / safety_mcu: ABSENT / DEFERRED
- `ARMED`: false (no owner GO for arm)
- PWM/GPIO invent: forbidden this season

## Sensing
- External feeds timer: `octopus-external-feeds.timer` active (15m)
- Feeds: OPENMETEO, AQI, TIME, FX-AUD, BOM-SYD, NEWS-AU, USGS-QUAKE (7)
- Homeostasis snapshot timer: `octopus-homeo-feeds-snapshot.timer` active (READ-ONLY)
- Snapshot: `/var/lib/octopus/state/homeostasis/feeds_snapshot.json`

## Doctor
- Script: readonly; `repairs_attempted=0`
- Latest known: PASS, blocking=[]

## MQTT
- Loopback `127.0.0.1:1883` auth required; no WAN/UFW public

## Explicit non-sync / deferred
- ESP32 Phase B hardware
- Physical e-stop parts buy
- Evolver/Simulator (not implemented)

## Auth cited this sync
- OCTOPUS-HOMEO-FEEDS-SNAPSHOT-20260823
- OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-20260823
- OCTOPUS-ALL-DOORS-OPEN-20260822
