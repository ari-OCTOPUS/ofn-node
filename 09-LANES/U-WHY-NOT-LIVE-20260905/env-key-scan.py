from pathlib import Path
p = Path(r"F:\backup\.env")
keys = []
if p.exists():
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k = s.split("=", 1)[0].strip()
        u = k.upper()
        if any(t in u for t in ("WIRE", "SMTP", "HYPOTHESIS", "AUTO_EMAIL", "OUTBOUND", "UNIFIED_CHAT")):
            keys.append(k)
print("env_exists", p.exists())
print("sensitive_key_names", keys)
