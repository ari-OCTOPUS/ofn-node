# Board2 YELLOW fix 2026-08-22

## ofn-backup
- Root cause: `/home/ari/.local/share/fugu_core/memory.sqlite` owned `root:root` (dir too). Backup `connect()` applies WAL pragmas and needs write → `attempt to write a readonly database`.
- Fix: `chown -R ari:ari /home/ari/.local/share/fugu_core` (`hypno-fugu-mini` already `User=ari`).
- Prove: `systemctl start ofn-backup` → Result=success, memory verified, legs still 200.

## hypno
- False yellow: no `hypno.service` unit. Intended = `hypno-fugu-mini.service` active on `127.0.0.1:8895`.
- Action: document/reconcile only.
