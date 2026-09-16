# PLAN - Orange Pi MQTT 1883 ENABLE ABD (discover-first)

**Authorization tokens:** `OCTOPUS-ALL-DOORS-OPEN-20260822` + `OCTOPUS-MQTT-ENABLE-ABD-20260822`  
**Authorization ID:** `OCTOPUS-MQTT-ENABLE-ABD-20260822`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER auth only (no SSH/mutate from this writer)  
**Written (AEST):** 2026-08-22T22:40:00+10:00  
**mutate_device:** true  
**Supersedes (auth-only):** `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-MQTT-1883-2026-08-22` (mutate_device=false; RECEIPT result BLOCKED_NEED_RUNBOOK / mqtt CLOSED)

## Prior SoT (do not contradict)

- Laptop plan search verdict: **no prior enable runbook** existed under F:\backup (`LAPTOP-MQTT-PLAN-SEARCH.json`). This package **is** the missing enable ABD.
- Pi receipt: `FROM-PI/RECEIPT-MQTT-1883.json` -> `result=BLOCKED_NEED_RUNBOOK`, `mqtt=CLOSED`, `wan_open=false`, `local_only_policy=true`, `mutate_device_auth=false`.
- ALL-DOORS `POINTERS.md`: keep-closed CHG-ABD / CHG-C explicitly forbade MQTT; those packages remain keep-closed for their own scopes. This package is a **new owner enable grant** for MQTT bind+auth only.
- WAVE0: software latch `PROVE_PASS_SOFTWARE_LATCH` exists; hardware Path H still `BLOCKED_NEED_ESTOP`. **This MQTT package does NOT unlock WAVE0 hardware / PWM / legs.**
- Board docs on Pi (from receipt paths): `MQTT_DISABLED.md` present under sensorium releases/staging - discover and honor that SoT before mutate.
- Credentials: **do not invent**. Use `DISCOVER_OR_GENERATE_LOCAL_ONLY` placeholders only; never paste real passwords into laptop evidence.

## Goal

Discover-first enable **mosquitto** (or an **already-installed** broker if one exists) on Orange Pi so MQTT TCP **1883** can serve **local-only** clients with **authentication required**.

Bind policy (choose one after discover; never both WAN-open):

1. **Loopback:** `127.0.0.1:1883` (safest default), OR
2. **LAN-only:** listen reachable from `192.168.0.0/24` only (bind `192.168.0.182` or `0.0.0.0` **with** host firewall/UFW allow from `192.168.0.0/24` only).

**Hard no:** WAN / open-internet / UFW public 1883 / 0.0.0.0 without LAN ACL / anonymous allow.

## Allowed change set

### 0) Precheck / discover (REQUIRED before mutate)

Record before-state in receipt:

1. `ss -ltnp` / `ss -ltn` filtered to **1883** and **8883** - confirm CLOSED or existing listener + address.
2. Units: `systemctl list-units --all '*mosquitto*' '*mqtt*' '*emqx*' '*nats*'` - note what exists (do **not** invent a second broker if one already owns 1883).
3. Packages: `dpkg -l | grep -E 'mosquitto|emqx'` (or distro equivalent) - install mosquitto **only if** no suitable broker present.
4. Config surfaces already on board (read-only first):
   - `/etc/mosquitto/` (or existing broker conf.d)
   - any octopus `MQTT_DISABLED.md` / board.yaml mqtt fields already present
   - UFW/nft/iptables rules mentioning 1883/8883
5. Auth material: discover existing password_file / ACL path if present. If absent: **generate local-only** user+password on the Pi; store under board-local secret path; laptop evidence may only record placeholder `DISCOVER_OR_GENERATE_LOCAL_ONLY` (never real secret).
6. Doctor: locate any mqtt / 1883 / broker-closed assertion; record current expected (likely CLOSED / DISABLED).

**STOP** if an unexpected WAN-facing broker is already listening, or if discover cannot identify a safe local bind path.

### 1) Enable broker (minimal)

1. Prefer **existing** installed broker config over installing a new one.
2. If installing: `mosquitto` + `mosquitto-clients` via distro packages only (no random third-party repo).
3. Listener: `127.0.0.1:1883` **OR** LAN-scoped as above.
4. **Authentication required:** `allow_anonymous false`; password_file + ACL (topic restrict to octopus/WAVE0 path as already named on board if present; otherwise minimal local ACL allowing only intended local topics - do not invent WAVE0 PWM payloads).
5. TLS/8883: **out of scope** unless an existing board cert path is already documented - do not invent PKI this run.
6. Enable + start unit (`systemctl enable --now mosquitto` or the discovered unit). Do **not** open UFW 1883 to Anywhere.

### 2) Host firewall

- If UFW/nft active: allow TCP 1883 from `192.168.0.0/24` **only** when LAN bind chosen; for loopback-only bind, **no** UFW public allow.
- Explicitly refuse WAN / `Anywhere` / `0.0.0.0/0` allow on 1883.

### 3) Doctor expectations (do not invent new doctor features)

- After enable, any doctor check that asserts `mqtt=CLOSED` / `MQTT_DISABLED` may **FAIL** or flip to OPEN-local - **expected**; document in receipt.
- Do **not** Doctor auto-patch.
- If an existing doctor field for mqtt/1883 exists, update it to reflect local-auth-enabled + this auth token + timestamp.
- If no such field exists, receipt-only note - do not invent a new doctor subsystem.

### 4) Verify

1. On Pi: `ss` shows intended bind (loopback OR LAN IP), not unexplained WAN.
2. Auth negative test: anonymous connect **DENIED**.
3. Auth positive test: local user from `DISCOVER_OR_GENERATE_LOCAL_ONLY` can pub/sub a harmless probe topic (no actuator/PWM/leg commands).
4. Confirm WAVE0 hardware / PWM / legs / keys / CHG-C / torch / money untouched; software estop latch unchanged unless explicitly out of scope (leave alone).
5. Confirm UFW/nft has **no** public 1883.

### 5) Receipts

- Board evidence JSON + TO-LAPTOP exchange ack citing this package path.
- Include: before/after listen addresses, unit name, conf path, auth mode (`allow_anonymous=false`), firewall delta, doctor implication, credential handling note (`DISCOVER_OR_GENERATE_LOCAL_ONLY` - no secret material on laptop).

## Explicitly forbidden

- WAN / UFW public / open-internet 1883
- Anonymous MQTT
- Inventing credentials into laptop evidence files
- WAVE0 hardware unlock / Path H / invent GPIO pin map / PWM / legs / root action_executor / arm reflex
- Treating software estop latch PROVE PASS as physical estop
- Private key export/rewrite; Doctor auto-patch; torch WM; zero-fill; re-run CHG-C; LAN:9101 rebind; money/webhook/work_pump
- Invent new protocol/port beyond 1883 local enable; casual hash rewrite
- Laptop writer SSH/mutate (sensoriom executes)

## Success criteria

- Broker listening on **127.0.0.1:1883** OR LAN-scoped **192.168.0.0/24-only** path
- Auth required; anonymous denied
- No WAN/UFW public 1883
- Doctor implications documented; ROLLBACK.md (stop+disable) concrete
- No WAVE0 hardware / PWM invent; no secrets written to laptop package
- Receipts cite both auth tokens

## Rollback summary

`systemctl stop` + `disable` the enabled broker unit; restore prior conf/firewall; return doctor expectation to CLOSED if previously CLOSED. See ROLLBACK.md.
