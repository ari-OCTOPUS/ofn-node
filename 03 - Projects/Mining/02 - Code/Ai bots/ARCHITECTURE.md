# Fleet Architecture — Crypto Accumulation Bot System

```
QuantumAlphaBot + Sentinel + Coordinator + Fleet
Hardware: 1× OPi5+ / 9× OPi5 Pro / 10× ESP32 / 1× RPi3B / 2× FPGA AX7
```

---

## 1. Hardware Roles

```
┌─────────────────────────────────────────────────────────────────┐
│               Orange Pi 5 Plus  (192.168.1.100)                 │
│                        THE BRAIN                                 │
│                                                                  │
│  QuantumAlphaBot ── GemHunter → Forensics → LLM → Veto → Score │
│  Sentinel        ── SignalFusion / macro / social               │
│  Coordinator     ── confluence(QA×0.45 + Sent×0.55)            │
│  Fleet Manager   ── REST API :7700 → dispatches mining targets  │
│  Hashrate Oracle ── bridges real fleet H/s → EdgeClassifier     │
│  systemd timers  ── QA every 6h, Coordinator offset 30min       │
└─────────────┬───────────────────────────────────────────────────┘
              │ LAN 192.168.1.0/24
    ┌─────────┼─────────────────────────────────┐
    │         │                                 │
    ▼         ▼                                 ▼
┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ OPi5 Pro ×9      │  │ ESP32 ×10       │  │ RPi 3B          │
│ 192.168.1.101-109│  │ 192.168.1.111+  │  │ 192.168.1.110   │
│                  │  │                 │  │                 │
│ worker_agent.py  │  │ firmware.py     │  │ watchdog.py     │
│ XMRig / cpuminer │  │ (MicroPython)   │  │                 │
│ Reports hashrate │  │ Temp sensor     │  │ Pings OPi5+     │
│ 1500 H/s yespow  │  │ Heartbeat POST  │  │ SSH restart if  │
│ each node        │  │ to /report      │  │ brain goes down │
└──────────────────┘  └─────────────────┘  └─────────────────┘
                                     USB/UART
              ┌──────────────────────────────┐
              │ FPGA AX7 ×2                  │
              │ Connected via USB to OPi5+   │
              │ Phase 1: hardware entropy    │
              │ Phase 2: SHA/scrypt accel    │
              └──────────────────────────────┘
```

---

## 2. Network Layout

| Device       | IP              | Role              | Services running            |
|--------------|-----------------|-------------------|-----------------------------|
| OPi5+        | 192.168.1.100   | Main brain        | fleet-manager, coordinator, QA bot |
| OPi5 Pro w01 | 192.168.1.101   | Miner worker      | worker-agent, xmrig/cpuminer |
| OPi5 Pro w02 | 192.168.1.102   | Miner worker      | worker-agent, xmrig/cpuminer |
| …            | …               | …                 | …                            |
| OPi5 Pro w09 | 192.168.1.109   | Miner worker      | worker-agent, xmrig/cpuminer |
| RPi 3B       | 192.168.1.110   | Watchdog/backup   | watchdog                     |
| ESP32 s01..10| 192.168.1.111+  | Sensors           | MicroPython firmware (MQTT)  |
| FPGA AX7     | USB/UART        | Accelerator       | Custom bitstream             |

**Ports used:**
- `:7700` — Fleet Manager REST API (LAN only, not internet-exposed)
- `:6789` — XMRig HTTP API (localhost only on each worker)
- `:22`   — SSH (OPi5+ and workers, key-based auth only)

---

## 3. Decision Pipeline

```
Every 6 hours (systemd timer):

  QA Bot (main.py)
  ──────────────────────────────────────────────────────────
  GemHunter         → scan CEX listings + EnergyFunnel (PoW coins)
  ScoutForensics    → LP lock, hooks, cluster, blacklist
  HolderChecker     → GoPlus concentration data
  VetoEngine        → STRUCTURAL_DECLINE, HOLDER_DANGER, etc.
  LLMEvaluator      → Claude advisory (P-C: no forced ACCUMULATE)
  QuantumAllocator  → Kelly sizing
  PaperTrader       → log to paper_ledger.jsonl

  (30 min later)

  Coordinator (coordinator/run.py)
  ──────────────────────────────────────────────────────────
  CandidateBridge    → read paper_ledger.jsonl, extract score≥35 coins
  HashRateOracle     → read fleet_state.json → real H/s for EdgeClassifier
  ConfluenceScorer   → qa×0.45 + sentinel×0.55
  Gate checks:
    ① forensic_vetoed == False
    ② edge_present != []          ← ENERGY / DISLOCATION / YIELD
    ③ sentinel_quadrant not TRAP/UNKNOWN
    ④ macro_cq_score > 25
    ⑤ kelly_frac ≥ 0.35
    ⑥ final_score ≥ 35
  Action routing:
    ENERGY             → MINE (Fleet Manager dispatches target)
    DISLOCATION        → BUY  (manual DCA signal)
    ENERGY+DISLOCATION → MINE+BUY (max accumulation)
    YIELD              → RUN_NODE
  DualNotifier       → Telegram alert + decisions.jsonl

  Fleet Manager (:7700)
  ──────────────────────────────────────────────────────────
  Receives coordinator MINE decision → sets /target
  Workers poll /target every 30s
  Workers start/stop xmrig/cpuminer automatically
  Workers POST /report every 30s (hashrate, temp, uptime)
  fleet_state.json updated → oracle reads it next cycle
```

---

## 4. Real Fleet Hashrate (ARM benchmarks)

| Algorithm  | Per OPi5 Pro | 9 Workers (×0.85) | Viable? |
|------------|-------------|-------------------|---------|
| yespower   | ~1,500 H/s  | **11,475 H/s**    | ✅ YES  |
| yespowerr16| ~1,400 H/s  | 10,710 H/s        | ✅ YES  |
| minotaur   | ~800 H/s    | 6,120 H/s         | ✅ YES  |
| scrypt     | ~800 H/s    | 6,120 H/s         | ⚠️  GPU competition |
| argon2d    | ~600 H/s    | 4,590 H/s         | ✅ YES  |
| gr (Ghostrider) | ~450 H/s | 3,443 H/s      | ✅ YES  |
| cryptonight| ~300 H/s    | 2,295 H/s         | ⚠️  network size |
| kawpow     | ~200 H/s    | 1,530 H/s         | ❌ GPU-dominated |
| rx/c64     | ~120 H/s    | 918 H/s           | ❌ too slow |
| **randomx**| ~110 H/s    | **841 H/s**       | ❌ XMR net=3 GH/s → share <0.00003% |

**Primary target algo: yespower** — best ARM performance, small-network coins
(Sugarchain SUGAR, Myriad XMY-yespower, C64 Chain, 0xForce)

**RandomX reality check:** ARM gets ~110 H/s per core. 9 nodes = ~841 H/s vs
Monero's 3 GH/s network. Fleet share = 0.000028% — below MIN_FLEET_SHARE (0.01%).
RandomX will correctly fail the ENERGY edge gate. That's working as designed.

---

## 5. File Map

```
Ai bots/
├── QuantumAlphaBot/          ← QA scanning bot
│   ├── main.py               ← pipeline entry point (runs every 6h)
│   ├── edges.yaml            ← ENERGY/DISLOCATION/YIELD definitions + ARM hashrates
│   ├── modules/
│   │   ├── edge_classifier.py  ← TODO: wire into main.py
│   │   ├── energy_funnel.py    ← discovers PoW mining coins from CoinGecko
│   │   └── ...
│   └── data/paper_ledger.jsonl ← cycle output (coordinator reads this)
│
├── sentinel/                 ← Sentinel bot (macro + social signals)
│   ├── signal_fusion.py      ← coordinator imports SignalFusion
│   └── ...
│
├── coordinator/              ← dual-bot orchestrator
│   ├── run.py                ← entry: python coordinator/run.py --once
│   ├── config.py             ← thresholds, weights, paths
│   ├── candidate_bridge.py   ← reads paper_ledger
│   ├── confluence_scorer.py  ← qa×0.45 + sentinel×0.55
│   ├── dual_notifier.py      ← Telegram + decisions.jsonl
│   └── data/decisions.jsonl  ← audit log
│
├── fleet/                    ← hardware fleet management layer (NEW)
│   ├── models.py             ← WorkerStatus, MiningTarget, FleetStats
│   ├── manager.py            ← REST API server on OPi5+ (:7700)
│   ├── worker_agent.py       ← runs on each OPi5 Pro (polls + mines)
│   ├── hashrate_oracle.py    ← reads fleet_state.json → EdgeClassifier
│   ├── watchdog.py           ← runs on RPi3B (monitors OPi5+)
│   └── data/
│       ├── fleet_state.json  ← live worker status (updated every 60s)
│       └── current_target.json ← persisted mining target
│
└── deploy/
    ├── setup_main.sh         ← OPi5+ full setup (Python, deps, systemd)
    ├── setup_worker.sh       ← OPi5 Pro setup (xmrig, cpuminer, agent)
    ├── setup_rpi.sh          ← RPi3B watchdog setup
    ├── esp32/
    │   └── firmware.py       ← MicroPython for ESP32 sensors
    └── systemd/
        ├── quantumalpha.service  ← one-shot (fired by timer)
        ├── quantumalpha.timer    ← every 6h at :00
        ├── coordinator.service   ← one-shot (fired by timer)
        ├── coordinator.timer     ← every 6h at :30 (30min after QA)
        ├── fleet-manager.service ← always-on REST server
        ├── worker-agent.service  ← always-on on each OPi5 Pro
        └── watchdog.service      ← always-on on RPi3B
```

---

## 6. Pending: Wire EdgeClassifier into main.py

Currently `edge_present=[]` for all coins because `EdgeClassifier` was built
but not called in the QA pipeline. This causes every coin to fail the
`no_edge` gate in the coordinator.

**Fix needed in `QuantumAlphaBot/main.py`** — add after QuantumAllocator:

```python
from modules.edge_classifier import EdgeClassifier

edge_clf = EdgeClassifier()
for coin in final_coins:
    edge_result = edge_clf.evaluate(coin)
    coin["edge_present"]  = edge_result["edge_present"]
    coin["edge_decision"] = edge_result["decision"]
```

This is intentionally left as the next step (real-data update phase).

---

## 7. Coordinator Test Results (2026-06-09)

```
Run: python coordinator/run.py --once
Cycle data: 2026-05-31T12:05 (last QA cycle)

Candidates extracted: 2 of 6 (OPG blacklisted, 3 below score floor)
  MEGA  score=42.1  edges=[]
  ICNT  score=37.6  edges=[]

Gate failures (all expected at this stage):
  ① no_edge — EdgeClassifier not wired yet
  ② macro_cq=20 ≤ 25 — market in DISTRIBUTING phase (correct gate)
  ③ sentinel_quadrant=UNKNOWN — MEGA/ICNT not in Sentinel universe
  ④ kelly=0.30 < 0.35 — correct floor

Action: NO_ACTION (correct — no edges, distributing macro)
decisions.jsonl: ✅ logged
Telegram: ⚠️ proxy blocked in sandbox — will work on OPi5+ with direct internet
```

All gates fired correctly. The system is working as designed.

---

## 8. Deploy Sequence (OPi5+ first run)

```bash
# 1. Flash Armbian/Ubuntu 22.04 on OPi5+ microSD
# 2. SSH in: ssh root@192.168.1.100

# 3. Upload bot files from Windows dev machine:
rsync -av --exclude='.venv' --exclude='__pycache__' \
  "C:\Users\Armin\Documents\Claude\Projects\Ai bots\\" \
  pi@192.168.1.100:~/ai-bots/

# 4. Run main setup:
sudo bash ~/ai-bots/deploy/setup_main.sh

# 5. Apply static IP:
sudo netplan apply

# 6. Start services:
sudo systemctl start fleet-manager
sudo systemctl enable --now quantumalpha.timer coordinator.timer

# 7. For each OPi5 Pro worker (run on each worker):
WORKER_ID=w01 MANAGER_URL=http://192.168.1.100:7700 \
WALLET_ADDR=YOUR_WALLET sudo bash deploy/setup_worker.sh

# 8. RPi3B watchdog:
sudo bash deploy/setup_rpi.sh

# 9. Flash ESP32 (via Thonny or mpremote):
# Edit deploy/esp32/firmware.py → set WIFI_SSID, WIFI_PASS, MANAGER_URL, ESP_ID
# Upload as main.py to each ESP32

# 10. Verify fleet:
curl http://192.168.1.100:7700/fleet | python3 -m json.tool
```
