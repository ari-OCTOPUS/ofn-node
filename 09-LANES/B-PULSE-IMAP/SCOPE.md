# SCOPE — B / Pulse-IMAP

Lane: B-PULSE-IMAP
Owns: `09-LANES/B-PULSE-IMAP/`
Also allowed this session: one wikilink pin in `01 - Dashboard/HANDOFF.md`; escalate-only note under `07-HANDOFF/` if `requires: owner_decision`.

## Allowed

- This-host listen / process / scheduled-task inventory
- TCP/22 reachability probes (LAN)
- Owner-authorized **read-only** SSH to `192.168.0.138` (`board138` / user `ari`) — confirm first; BatchMode only
- Remote read-only: `ss`, `systemctl is-active` / `status` / `show` / `cat` / `list-timers` / `--failed`, `ps`, `journalctl -n`, `/proc/<pid>/cmdline`

## Forbidden

- Remote mutation: `systemctl start|stop|restart|enable`, `rm`, file writes on 138, git on 138
- Merge PR #106 or any PR
- Enable `OCTOPUS_WIRE_*` / `OFN_WIRE_*` / `auto_email` / closed gates
- Send email / customer message / outbound internet API
- Bind `0.0.0.0`, open a new tunnel/broker, declare a painting winner
- Touch other-lane files (A identity, C packet)

## Identity

This body is the laptop vault. Do not claim node 180 or 138 unless `eth0`/Wi-Fi matches. Default `scope=this_host_only` unless two `node_id`s are evidenced.
