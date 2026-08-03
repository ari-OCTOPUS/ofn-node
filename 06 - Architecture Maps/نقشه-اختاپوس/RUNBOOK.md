# 🗺️ VaultScanner RUNBOOK — نقشه اختاپوس

> وضعیت: read-only diagnostic tool.

---

## اصول سخت

- Scanner فقط read-only است.
- هیچ move/rename/delete/write روی vault هدف.
- گزارش فعلی ممکن است مربوط به `F:\backup` باشد، نه این workspace.
- اجرای scan روی این workspace نیاز به verdict مالک دارد.

---

## اجرای پیشنهادی بعد از verdict

```bash
python vault_scanner.py "C:\Users\Armin\Desktop\پازل هشت پا"
```

خروجی مجاز:

```text
vault-report.md
vault-inventory.json
```

---

## Graph search قبل از کار

1. Load `MANIFEST.yaml`, `GUIDE-FA.md`, `SYSTEM-PROMPT.md`.
2. Follow edge `VaultScanner → RegistryAlignment SUPPORTS`.
3. If task writes new report, ensure it's tool output only.

---

## Stop conditions

- scanner attempts to modify files
- target path is ambiguous
- report includes secrets/PII
