# Second-host execution witness — node160

2026-09-17T09:09:28Z · authenticated `root@192.168.0.160` · `octopus-compute-160`.
Unique sandbox `/root/s1-t1-witness-20260917`, ext4 `/dev/mmcblk0p1`, aarch64/Python3.13.5.

The same exact candidate source and unchanged harness were executed independently on a second host. This is an independent execution witness, not an independent implementation or code review. No source or service outside that sandbox was changed.

Receipt: `node160-witness/linux-run-01/RESULT.json`. All source hashes match node100:

- app: `79a10dbd02392a381b9b262d62011f4b9c37e9f6228ac5dd951a483dfe0ba4be`
- snapshot: `48cfac2e6a0cde62b86af08a8ca7843aac12e2ff113d9d52a20877c2acdd4824`

Four SIGKILL cases reproduced exactly: mid-batch 50 replayable / 0 ACK; torn record 50 / 0 and append refused without byte change; before fsync 100 / 0; after ACK 100 / 100 with zero ACKed missing. All four journal hashes also match node100's cases.

Real unchanged 3000-event fixture: original 6.2109s / 3000 fsyncs; candidate single-event 7.4000s / 3000; candidate batch100 0.1444s / 30. Every variant has identical journal bytes and replay hash. These remain one run per variant per host, UNDERPOWERED and not measurements of node182 service throughput.

**Receipt annotation correction:** the shared harness's descriptive `benchmark.limitation` string says `node100 filesystem`; this is hardcoded prose inherited by the second-host run. The command target, sandbox, and this witness establish that this receipt ran on **node160**. Original receipt bytes are retained without rewriting that field.

Full replica boot, integrated runtime batching, witnessed genesis reader, retention implementation, T+1h RSS, and power-loss durability remain NOT_RUN/NOT_IMPLEMENTED as recorded. No deployment-readiness conclusion follows from this witness.
