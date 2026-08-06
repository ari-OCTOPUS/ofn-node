# Rollback

1. Identify last backup in `/home/ari/ofn/backups/painting-*`.
2. Stop `ofn.service`.
3. Restore touched files: `ofn/adapters/http_api.py`, `ofn/node.py`, `ofn/run.py`, `ofn/config.py`, `ofn/adapters/boot.py`, `web/panel.html`, `web/lead.html`, and any new store files if needed.
4. Restart `ofn.service`.
5. Verify health and ports. SQLite additive migrations do not remove old data.
