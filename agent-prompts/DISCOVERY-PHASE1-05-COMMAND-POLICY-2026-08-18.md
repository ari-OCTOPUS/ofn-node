# DISCOVERY-PHASE1-05 — Command Policy: Read-Only Whitelist & Prohibited Blacklist (all nodes)
Bundle: OCTOPUS World-Discovery Phase 1 · 2026-08-18 · Status: BINDING for D0
Scope: LAPTOP-191 (DESKTOP-KA9RFN5), BOARD-138 (Feet), BOARD-182 (Sensorium), BOARD-180 (A2 lab)

---

## 1. TAXONOMY

- **P0 PASSIVE (allowed by default)** — reads of state the OS already holds. Inject zero packets, open zero connections, write zero files. Note: `arp -a` / `Get-NetNeighbor` / `ip neigh show` display only what the kernel already learned — passive. *Sending* ARP/ICMP/TCP/DNS is active.
- **P1 CAPTURE (owner-gated, default forbidden)** — packet capture (tcpdump, pktmon, Wireshark). Not truly passive: privilege, promiscuous mode, payload exposure, unbounded volume. Requires an explicit owner decision recorded per capture.
- **A1 ACTIVE PROBE (forbidden everywhere in D0)** — anything injecting packets or opening connections.
- **D0-REMOTE-READ (separate owner-authorized phase)** — SSH read-only sessions to .138/.182. Never mixed into D0-PASSIVE; never to .180.

**Universal command discipline:** no shell redirection or file creation inside any command; the operator captures output separately. All timestamps normalized to UTC ISO-8601 at capture. Every captured output gets SHA-256 + saved artifact (`PACKAGE.sha256` per evidence bundle).

## 2. WHITELIST — LAPTOP-191 (Windows PowerShell; Git Bash where noted)

| field_id target | Command (P0) |
|---|---|
| identity.hostname / platform | `hostname` · `$PSVersionTable.PSVersion` |
| network.interface_list / ip_addresses | `Get-NetIPAddress` · `Get-NetIPConfiguration` · `ipconfig /all` |
| network.route_table | `Get-NetRoute` · `route print` |
| network.neighbor_cache | `Get-NetNeighbor` · `arp -a` *(display of existing cache only — never `arp -d`, never solicitation)* |
| network.listening_tcp / udp | `Get-NetTCPConnection` · `Get-NetUDPEndpoint` |
| network.dns_config | `Get-DnsClientServerAddress` |
| network.firewall_ruleset | `Get-NetFirewallProfile` |
| git.* (inside F:\backup) | `git status --porcelain=v1` · `git log -1 --pretty='%H %cI %s'` · `git remote get-url origin \| sed -E 's#(//)[^@]+@#\1REDACTED@#'` (redaction mandatory) |
| config.inventory_metadata | `Get-Item <known-path> \| Select-Object FullName,Length,LastWriteTime` + `Get-FileHash <known-path>` (known paths only — never unknown config `cat`) |
| board180.proven_edges | `Get-NetNeighbor` / `arp -a` *(existing entries only)* + repo-record grep: `git grep -n "192.168.0.180"` |

## 3. WHITELIST — BOARD-138 (busybox/dropbear suspected; every command is a cascade)

| field_id target | Command (P0, on-board — runs only in D0-REMOTE-READ after owner authorization) |
|---|---|
| identity.platform | `cat /etc/os-release \|\| cat /etc/issue \|\| echo TOOL_MISSING` |
| identity.hostname | `hostname \|\| cat /etc/hostname \|\| echo TOOL_MISSING` |
| memory/platform probe | `free -m \|\| head -5 /proc/meminfo \|\| echo TOOL_MISSING` |
| network.interface_list / ip_addresses | `ip addr show \|\| ifconfig \|\| echo TOOL_MISSING` |
| network.route_table | `ip route show \|\| route -n \|\| echo TOOL_MISSING` |
| network.neighbor_cache | `ip neigh show \|\| cat /proc/net/arp \|\| echo TOOL_MISSING` |
| network.listening_tcp/udp | `ss -lntu \|\| netstat -tlnu \|\| echo TOOL_MISSING` |
| ssh.server_type | `ps w \| grep -E "dropbear\|sshd" \| grep -v grep` *(process detection — ports/configs are mutable)* |
| reflex.llm_references | `grep -rn -E "openai\|anthropic\|llm\|gpt\|glm\|kimi" <VERIFIED_source_path> \|\| echo TOOL_MISSING` — **only after reflex.source_path is VERIFIED to exist**; else field stays BLOCKED_SOURCE_PATH_UNKNOWN |

**.138 transfer pattern (D0-REMOTE-READ):** `ssh <host> '<command above>' > local_capture_file` — assume **no scp/sftp** until `ssh.server_type` proves otherwise. Empty grep + `EXIT=1` on a VERIFIED path ⇒ `VERIFIED_CLEAN`. Missing path ⇒ `UNKNOWN`, never clean.

## 4. WHITELIST — BOARD-182 (Armbian/systemd; busybox cascade armed until disproven)

All BOARD-138 cascades above, plus:

| field_id target | Command (P0) |
|---|---|
| identity.platform | `cat /etc/os-release \|\| cat /etc/issue \|\| echo TOOL_MISSING` · `cat /etc/armbian-release \|\| echo NO_ARMBIAN_RELEASE` *(absence is data, not failure)* |
| network.dns_config | `cat /etc/resolv.conf \|\| echo TOOL_MISSING` |
| network.firewall_ruleset | `nft list ruleset \|\| iptables -S \|\| ufw status \|\| echo TOOL_MISSING` |
| svc.service_inventory | `systemctl list-units --type=service --all --no-pager --plain` (**never** `--type=timer`) |
| checkpoint.last_signed_ref / exchange state | read-only listing of the exchange channel export the board already produced (e.g. `ls -l /var/lib/octopus/inbound/TO-LAPTOP/exchange/` + `sha256sum` on listed files) — only paths already sanctioned by owner decisions D8/D12 |

## 5. BOARD-180 — TOTAL PROHIBITION

- **Zero commands target the board.** No ping, no ARP solicitation, no SSH, no WOL, no nmap, no MQTT, nothing — regardless of how "quiet" it seems (`nmap -PR`, `arp-scan --localnet` send ARP requests = active).
- Only laptop-side reads allowed: existing `arp -a`/`Get-NetNeighbor` cache entries, repo records, prior evidence files.
- Canonical output is exactly two rows: `board180.power_target = OFF` (OWNER_DECISION) and `board180.power_state = UNKNOWN` (runtime — "OFF" is a runtime claim requiring evidence we forbade collecting).
- Any observed reachability ⇒ `CONTRADICTED` + `BLOCKED` + `OWNER_DECISION_REQUIRED`. Drift-normalization is the named failure mode.

## 6. D0-REMOTE-READ GATE (SSH to .138/.182 only)

Requires, per session, one explicit owner authorization plus: `BatchMode=yes`, `StrictHostKeyChecking=yes`, pinned known_hosts entry, and the identity pre-check (expected hostname/IP/host-key from repo evidence). Hostname/IP/host-key mismatch or a new host key ⇒ **STOP + CONTRADICTED + ESCALATE_OWNER** — auto-accept is the single fastest way discovery becomes the intrusion. Read-only commands from §3/§4 only.

## 7. BLACKLIST — A1 ACTIVE PROBES (all nodes, all of D0)

`ping` · `Test-Connection` · `Test-NetConnection` · `traceroute`/`tracert` · `mtr` · `nc`/`netcat` · `telnet` · `curl` · `wget` · `Invoke-WebRequest` · `Invoke-RestMethod` · `dig` · `host` · `nslookup` · `nmap` · `masscan` · `arp-scan` · `fping` · `hping3` · Wake-on-LAN magic packets · all MQTT operations (`mosquitto_pub/sub`, port 1883/8883 anything) · localhost HTTP health-endpoint GETs (a GET is a connection).

## 8. BLACKLIST — DESTRUCTIVE / SYSTEM-STATE (until explicit owner authorization in a later phase)

Package/state: `apt`/`apt-get`/`pip`/`npm install` · `systemctl start/stop/restart/enable/disable/mask` · `docker run/pull/stop/rm/exec` · `schtasks /create /delete /run` · `reg add/delete` · `Set-*` service/registry/network cmdlets · `New-*/Remove-*/Restart-*` service cmdlets.
Files/git: `rm` · `mv` · `chmod`/`chown` · `del`/`Remove-Item` · `rd` · `git checkout/pull/push/reset/clean/commit --amend` · `git add -A`.
Power/host: `reboot` · `shutdown` · `Restart-Computer` · `Stop-Computer` · `dd` · `mkfs.*` · `kill`/`taskkill` (except documented self-test harness) · any GPIO/PWM/actuator/leg path · clearing flags (incl. `GITWRITE-FAILED.flag` — no agent lifts it, per D14).
Ledgers: **never hand-edit hash-chained ledgers** (`ledger.jsonl`, checkpoint chains). Broken chain ⇒ quarantine proposal only, escalate.

## 9. BLACKLIST — SCHEDULER READS (standing zero-interaction order)

`crontab -l` (and `-e`, obviously) · `systemctl list-timers` · `--type=timer` in any form · `Get-ScheduledTask` · `Get-ScheduledJob` · `schtasks /query` · reading `/etc/cron*`, `/var/spool/cron`, systemd timer units. Field `svc.scheduler` = `UNKNOWN_BY_POLICY`, `verification_command: NONE`, permanently.

## 10. BLACKLIST — SECRET EXPOSURE

`env` · `printenv` · `/proc/*/environ` · `ps e`/`ps auxww` full-cmdline dumps · `docker inspect` · `cat`/`Get-Content` on unknown or credential-bearing configs (`.env`, `*token*`, `*secret*`, `*key*`, `id_rsa*`, `id_ed25519`, `/etc/octopus/secrets`, `/root/octopus-ca`) · `git remote -v` (use the redacted `get-url` form) · `klist`/credential caches · `net use` with credentials visible. Any accidental secret capture ⇒ quarantine the capture, do not commit, note in `security.secrets_in_outputs`.

## 11. REJECTION HANDLING

Every proposed/encountered command violating §7–§10 is logged to `REJECTED-COMMANDS.md`: command, source, violated section, risk label (`MUTATION`, `ACTIVE_NETWORK_PROBE`, `SECRET_EXPOSURE`, `SCHEDULER_ACCESS`, `PLATFORM_ASSUMPTION`, `PATH_ASSUMPTION`, `IDENTITY_RISK`, `DEVICE_POLICY_VIOLATION`, `UNBOUNDED_OUTPUT`, `UNKNOWN_SIDE_EFFECT`), reason, safer alternative or the evidence that would unblock it. The log is an audit artifact, not a shame list — an empty log with non-trivial inputs is itself suspicious (see Phase-3 checklist).
