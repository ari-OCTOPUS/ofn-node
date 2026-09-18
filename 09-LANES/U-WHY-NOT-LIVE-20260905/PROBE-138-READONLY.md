---
type: handoff
status: executed
requires: none_for_138
tags: [octopus, layer-2, read-only]
created: 2026-09-05
updated: 2026-09-05
lane: U-WHY-NOT-LIVE-20260905
---

# Layer 2 — 138 read-only (executed 2026-09-05)

Owner GO: `ssh ari@192.168.0.138`. Receipt: `LAYER2-138-SSH-RECEIPT.json`. 180 still auth-failed.

Do not restart `ofn.service`. Do not enable wires. Do not send.

## Allowlisted observations (on 138)

```bash
hostname
ip -4 addr
ss -lnt | awk '$4 ~ /:(8791|8792|8793|8794|8796|8771)$/'
systemctl is-active ofn.service || true
systemctl show ofn.service -p WorkingDirectory -p MainPID -p FragmentPath --no-pager
```

Paste the output into a new receipt under this lane. Until that file exists, `node138_status` stays `unverified`.
