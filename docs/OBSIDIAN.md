# Obsidian / قابل‌حمل‌سازی Hypno Fugu

اپ اکنون endpoint زیر دارد:

- `POST /api/obsidian/export`

این endpoint یک Vault کامل می‌سازد:

```text
/home/ari/hypno-fugu-mini/obsidian-vault/Hypno-Fugu-Vault
```

و نسخه zip قابل جابه‌جایی:

```text
/home/ari/hypno-fugu-mini/exports/hypno-fugu-obsidian-vault.zip
```

داخل Vault:

- `00-Dashboard.md`
- `Research/` برای متن‌های cleaned/raw
- `RAG-Chunks/` برای chunkهای قابل جستجو
- `Memory/` برای حافظه‌های فعال
- `Sessions/` برای لاگ تعاملات اخیر

از داخل مینی‌وب دکمه «خروجی Obsidian» همین کار را انجام می‌دهد و لینک دانلود می‌دهد.
