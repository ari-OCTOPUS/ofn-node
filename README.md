# Hypno Fugu Mini

مینی‌وب تلگرامی مستقل برای خودهیپنوتیزمی آری، جدا از `/home/ari/ofn`.

- Root: `/home/ari/hypno-fugu-mini`
- Port: `127.0.0.1:8895`
- State: `~/.local/share/hypno-fugu-mini/hypno.sqlite`
- Python stdlib + SQLite FTS5، بدون npm/docker
- UI: `web/index.html` با Telegram SDK defer و فونت لوکال
- API: `/health`, `/api/session`, `/api/chat`, `/api/memory`, `/api/research/ingest`, `/api/research/search?q=`
- Brain: fallback `rules+rAG`; با `HFM_REMOTE_API_KEY`, `HFM_REMOTE_BASE_URL`, `HFM_REMOTE_MODEL=fugu` به مغز ریموت وصل می‌شود.

## اجرا
```bash
cd /home/ari/hypno-fugu-mini
python3 -m hypno.run --check
python3 -m hypno.run
```

## تلگرام
اگر `HFM_BOT_TOKEN` ست شود، `initData` تلگرام اعتبارسنجی می‌شود. `HFM_OWNER_USER_IDS` را برای محدود کردن به خودت ست کن.
