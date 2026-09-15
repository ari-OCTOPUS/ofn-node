# EVIDENCE — raw command output, 2026-09-15 session

All timestamps UTC. Collected from the laptop (192.168.0.191) and the boards.

## E1 — Live host census (TCP scan of full /24 from 138, ports 22/80/443/8081/3337/3389/5900/8080)

```
192.168.0.1      ports=[80]
192.168.0.100    ports=[22, 3337, 8081]
192.168.0.138    ports=[22]
192.168.0.160    ports=[22]
192.168.0.180    ports=[22, 8081]
192.168.0.182    ports=[22]
```

This is authoritative for "hosts with a listening service". A separate ICMP sweep additionally
saw `.113` and `.118` (ping only, no open ports — the two ESP32-S3).

## E2 — Board models (`/proc/device-tree/model`)

```
138 : Orange Pi 5 Pro
180 : Orange Pi 5 Pro
182 : Orange Pi 5 Pro
.100: Orange Pi 5 Pro
```

All reachable boards are **Orange Pi 5 Pro (RK3588S)**.

## E3 — SD card state before the owner's insertion

Every board showed only the 58.3 GB eMMC plus the non-removable WiFi host — **no `mmcblk1`**:

```
138, 180, 182, .100, .160 :  lsblk -> mmcblk0 58.3G (+ mmcblk0boot0/1) ; no mmcblk1
```

## E4 — The card that appeared in 138 at 01:15 UTC

```
[    1.982802] mmc_host mmc1: Bus speed (slot 0) = 400000Hz (slot req 400000Hz, actual 400000HZ div = 0)
[ 2190.739392] mmc_host mmc1: Bus speed (slot 0) = 148500000Hz (slot req 150000000Hz, actual 148500000HZ div = 0)
[ 2190.751344] mmc1: new ultra high speed SDR104 SDHC card at address aaaa
[ 2190.752543] mmcblk1: mmc1:aaaa SD32G 29.7 GiB
[ 2190.764320]  mmcblk1: p1
```

```
Disk /dev/mmcblk1: 29.72 GiB, 31914983424 bytes, 62333952 sectors
Disklabel type: gpt
Device         Start     End Sectors  Size Type
/dev/mmcblk1p1 32768 3235806 3203039  1.5G Linux root (ARM-64)

/dev/mmcblk1p1: LABEL="armbi_root" UUID="21f59e6d-..." TYPE="ext4" PARTLABEL="rootfs"
```

Bootloader chain present (the thing the earlier session's `dd` copy lost):

```
sector 64    :  52 4b 4e 53 ...      <- "RKNS" Rockchip IDB (idbloader) at 32 KB
sector 16384 :  d0 0d fe ed ...      <- FIT image magic = u-boot at 8 MB
```

Image identity (read-only mount):

```
PRETTY_NAME="Armbian 25.11.1 trixie"
/etc/hostname  -> orangepi5-plus
/etc/armbian-release: BOARD=orangepi5-plus ; BOARDFAMILY=rockchip-rk3588 ; ARCH=arm64
/boot/armbianEnv.txt: fdtfile=rockchip/rk3588-orangepi-5-plus.dtb
/boot/dtb/rockchip/ contains rk3588s-orangepi-5-pro.dtb  (Pro DTB ships on the card)
```

`e2fsck -fn /dev/mmcblk1p1` -> clean:
`armbi_root: 28509/100256 files (0.1% non-contiguous), 345495/400379 blocks`

## E5 — What was written to the card

```
/root/.ssh/authorized_keys   600 root:root   (4 public keys)
/root/.ssh                   700 root:root
grep -c $'\r'  -> 0           (LF-clean; CRLF would corrupt key parsing)
/etc/ssh/sshd_config          PermitRootLogin yes ; PubkeyAuthentication yes
```

Armbian firstrun does **not** touch this file (checked `/usr/lib/armbian/armbian-firstrun`; it only
does `rm -f /etc/ssh/ssh_host*`, `dpkg-reconfigure openssh-server`, and comments out `AcceptEnv LANG`).

## E6 — SSH auth structure on .100 / .160 (why passwords can never work)

```
debug1: Remote protocol version 2.0, remote software version OpenSSH_10.0p2 Debian-7+deb13u2
debug1: Authentications that can continue: publickey,keyboard-interactive
debug1: Next authentication method: keyboard-interactive
debug2: we sent a keyboard-interactive packet, wait for reply
debug1: Authentications that can continue: publickey,keyboard-interactive
```

The server answers the keyboard-interactive request with an **empty challenge** — no prompt is ever
emitted, so `sshpass` is never handed a password. Password auth is not offered at all.
Access was obtained instead with the pre-existing `piggybank_id_ed25519` key as `root`.

## E7 — The two "new" boards are the Hacash mining rig

```
192.168.0.100  hostname DietPi  | Debian 13 (trixie)
  hacash-fullnode.service  active running   (LISTEN 3337 P2P, 8081 RPC console)
  tdc_miner.service        active running   (Tidecoin)
192.168.0.160  hostname DietPi  | Debian 13 (trixie)
  hacash-miner.service     active running   (load average 7.00)
```

Both boot from eMMC (`mmcblk0`), no SD, no USB storage.

## E8 — 182 is not boot-looping

```
uptime t0 : up 2 min   (/proc/uptime 173.84)
uptime t0+60s :          /proc/uptime 234.21     <- monotonic, no reboot
```
It was mid-reboot when first probed at ~01:12; it came back ~01:20:30 and has been stable since.

Root cause of its instability:

```
free -m            : Mem: 3910 total, 2351 used, 0 swap
systemctl show octopus-sensorium.service : MemoryMax=2147483648  MemoryCurrent=2147405824  NRestarts=14
octopus-gap001-boot-probe.service : Active: failed (Result: oom-kill) ; Mem peak: 2G
dmesg: oom-kill:constraint=CONSTRAINT_MEMCG ... oom_memcg=/system.slice/octopus-sensorium.service
       Killed process 1588 (python) total-vm:2286912kB, anon-rss:2091700kB
```

## E9 — Boot image download (the previously-reported 0-byte blocker is gone)

```
HTTP/1.1 200 OK ; Content-Type: application/x-xz ; Content-Length: 182563948
138:~/bootmedia/dietpi-opi5pro.img.xz  182563948 bytes  (exact match)
python3 lzma full-decompress OK -> uncompressed bytes: 817701376
```

## E10 — Router

`http://192.168.0.1/goform/getLoginInfo` returns JSON unauthenticated:
`{"isLocked":"0","time":"-1","leftTimes":5}`

Every other endpoint tested (`stokCfg`, `main.html`, `getOnlineList`, `getClientList`, `getDhcpList`,
`getSysStatus`, `getWanStatus`, `getLanCfg`, `getDeviceList`) returns `302 -> /login.html`, with or
without a browser User-Agent / XHR headers / cookies. `GOAHEAD_AES_CRYPT="y"` means the login POST to
`/login/Auth` must carry `AES-CBC(md5(password))` keyed by the server `sign` from `stokCfg` — and
`stokCfg` is itself behind the redirect. **Device list not obtainable this way.**
Login attempts were deliberately not spent (only 5 remain before lockout).

## E11 — Stale unit on .100 (pre-existing, not caused by this session)

```
● tdc_miner.service - Tidecoin Miner
     Active: activating (auto-restart) (Result: exit-code)
     Process: 1779 ExecStart=/root/xmrig/build/xmrig --config=/root/config.json (code=exited, status=203/EXEC)
     NRestarts=300          is-enabled: enabled
journalctl: tdc_miner.service: Unable to locate executable '/root/xmrig/build/xmrig': No such file or directory

ls /root/xmrig/build/xmrig  -> No such file or directory
ls /root/config.json        -> No such file or directory
```

xmrig was deliberately removed by the owner in an earlier project; the unit was left enabled and
has been restart-looping since. Not touched by this session.

