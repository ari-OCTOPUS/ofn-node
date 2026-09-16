---
type: knowledge
status: inbox
updated: 2026-08-18
created: 2026-08-18
created_by: agent
tags: [octopus, network, wifi, ssh, handshake]
source: "[[../06-EVIDENCE/NETWORK-PATH-5GHZ-2026-08-18]]"
sources:
  - "[[../06-EVIDENCE/NETWORK-PATH-5GHZ-2026-08-18]]"
  - "[[../06-EVIDENCE/EVIDENCE-ENVELOPE-CYCLE-01-2026-08-18]]"
---

# Laptop → boards: Wi-Fi 5 GHz + SSH .138 + envelope cycle-2

Ethernet روی این میز **Disconnected** بود (کابل نزدیم). رادیو از `Tenda_EBBAA0`
(2.4 GHz) به `Tenda_EBBAA0_5G` (5 GHz ac ch36) عوض شد. پروفایل 5G از قبل نبود؛
ساخته شد در TEMP، کلید وارد vault نشد.

Write-bench محلی 200×4KB (fsync + size-verify): **53453ms → 73387ms** (recheck 40412ms).
عدد 1080ms مالک در این نشست بازتولید نشد. پرچم GITWRITE **عمداً ماند**.

`octopus_key` وجود ندارد. دستور دقیق SSH مالک exit 0 داد چون OpenSSH به کلید
دیگری افتاد؛ `id_ed25519` جداگانه هم OK. `authorized_keys`/`sshd_config` دست نخورد.

پاکت cycle-2 (سایدکار، نه TCB): continuity / sensorium / feet — جزئیات و raw:
[[../06-EVIDENCE/NETWORK-PATH-5GHZ-2026-08-18]]

Owner-pending عوض نشد: `01a00d3d` · مراسم TCB · تگ `pre-deploy-2026-07-25` · GITWRITE.
