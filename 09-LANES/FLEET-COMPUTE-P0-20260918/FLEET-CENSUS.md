# FLEET CENSUS — Phase 0 read-only discovery

Generated: 2026-09-18T00:00:44Z  
Samples in ledger: 7 (OK: 7)  
Source: `fleet_probe.py` over SSH. Read-only: `/proc`, `/sys`, `df`, `systemctl` queries.

## Capacity and current load

| Node | Hostname | Model | Cores | Load1 | CPU% | Hottest C | Mem used% | Disk used% | Governor | OFN | leaf | Failed units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 100 | octopus-compute-100 | Orange Pi 5 Pro | 8 | 0.0 | 0.5 | 27.8 | 7.2 | 13% | schedutil | inactive | active | 0 |
| 114 | octopus-pro-114 | Orange Pi 5 Pro | 8 | 0.05 | 0.2 | 23.1 | 6.4 | 2% | schedutil | inactive | active | 0 |
| 138 | DietPi | Orange Pi 5 Pro | 8 | 1.11 | 14.9 | 37.9 | 37.2 | 35% | schedutil | active | active | 1 |
| 160 | octopus-compute-160 | Orange Pi 5 Pro | 8 | 0.0 | 0.2 | 23.1 | 6.6 | 5% | schedutil | inactive | active | 0 |
| 180 | octopus-continuity-180 | Orange Pi 5 Pro | 8 | 0.08 | 0.5 | 27.8 | 57.0 | 22% | schedutil | inactive | active | 0 |
| 182 | sensorium-opi5pro | Orange Pi 5 Pro | 8 | 1.65 | 14.1 | 34.2 | 69.9 | 46% | schedutil | inactive | active | 0 |
| 193 | octopus-model-plus-193 | Orange Pi 5 Plus | 8 | 0.0 | 0.5 | 24.1 | 6.6 | 3% | schedutil | inactive | active | 0 |

## Identity and liveness (anti-copy check)

`liveness_proven` requires a correct sha256(nonce) echo from this round AND a clock skew within 20 s.
A stale or copied record fails it.

| Node | machine-id | boot-id (head) | uptime s | ssh rtt s | clock skew s | liveness proven |
|---|---|---|---|---|---|---|
| 100 | 9a13f5e68e71 | 1d9d56a9 | 256892 | 2.222 | -2 | True |
| 114 | 1685bcb584ad | b7a638d4 | 249099 | 3.668 | -1 | True |
| 138 | 2d9582e0eea9 | f95a1893 | 1674 | 2.932 | -1 | True |
| 160 | dba100ceead0 | bacb05a6 | 254750 | 2.023 | -2 | True |
| 180 | 7fc9a117d08f | 94c9f38e | 256873 | 12.211 | -1 | True |
| 182 | 3da939da38d1 | 7a4e237a | 254338 | 3.096 | -1 | True |
| 193 | 576b7dadd71d | 92a8e9fd | 250536 | 4.419 | -2 | True |

## Thermal zones (C)

- **100**: bigcore0-thermal=27.8, bigcore1-thermal=27.8, center-thermal=26.8, gpu-thermal=27.8, littlecore-thermal=27.8, npu-thermal=27.8, soc-thermal=27.8
- **114**: bigcore0-thermal=22.2, bigcore1-thermal=22.2, center-thermal=22.2, gpu-thermal=22.2, littlecore-thermal=23.1, npu-thermal=23.1, soc-thermal=22.2
- **138**: bigcore0-thermal=37.0, bigcore1-thermal=37.9, center-thermal=35.2, gpu-thermal=34.2, littlecore-thermal=37.0, npu-thermal=35.2, soc-thermal=36.1
- **160**: bigcore0-thermal=23.1, bigcore1-thermal=23.1, center-thermal=23.1, gpu-thermal=22.2, littlecore-thermal=23.1, npu-thermal=23.1, soc-thermal=23.1
- **180**: bigcore0-thermal=27.8, bigcore1-thermal=27.8, center-thermal=27.8, gpu-thermal=27.8, littlecore-thermal=27.8, npu-thermal=27.8, soc-thermal=27.8
- **182**: bigcore0-thermal=33.3, bigcore1-thermal=34.2, center-thermal=32.4, gpu-thermal=32.4, littlecore-thermal=34.2, npu-thermal=33.3, soc-thermal=33.3
- **193**: bigcore0-thermal=23.1, bigcore1-thermal=23.1, center-thermal=23.1, gpu-thermal=23.1, littlecore-thermal=24.1, npu-thermal=23.1, soc-thermal=24.1

## CPU frequency by policy (cur/max kHz)

- **100**: policy0=1200000/1800000, policy4=1608000/2304000, policy6=1200000/2304000
- **114**: policy0=1008000/1800000, policy4=1200000/2352000, policy6=1608000/2256000
- **138**: policy0=1800000/1800000, policy4=2352000/2352000, policy6=1608000/2352000
- **160**: policy0=1416000/1800000, policy4=1608000/2304000, policy6=1608000/2304000
- **180**: policy0=1200000/1800000, policy4=408000/2256000, policy6=408000/2256000
- **182**: policy0=1800000/1800000, policy4=2352000/2352000, policy6=2352000/2352000
- **193**: policy0=1200000/1800000, policy4=1608000/2352000, policy6=1608000/2400000
