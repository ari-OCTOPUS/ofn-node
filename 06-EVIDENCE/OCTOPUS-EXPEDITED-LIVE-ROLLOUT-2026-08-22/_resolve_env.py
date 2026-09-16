from pathlib import Path
import os, json, hashlib
root = Path(r"F:/backup")
report = {}
report["env_has_owner"] = bool(os.environ.get("TELEGRAM_OWNER_CHAT_ID", "").strip())
report["env_has_bot"] = bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip())
report["env_has_center"] = bool(os.environ.get("TG_CENTER_BOT_TOKEN", "").strip())
report["env_owner_len"] = len(os.environ.get("TELEGRAM_OWNER_CHAT_ID", "").strip())
report["env_tg_keys_present"] = sorted([k for k in os.environ if ("TELEGRAM" in k or k.startswith("TG_"))])
keys = []
envp = root / ".env"
if envp.exists():
    for line in envp.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if any(x in k for x in ["TELEGRAM", "TG_", "OWNER", "TOKEN"]):
            keys.append({
                "key": k,
                "has_value": bool(v),
                "len": len(v),
                "sha12": hashlib.sha256(v.encode()).hexdigest()[:12] if v else None,
            })
report["dotenv_relevant"] = keys
cfg = root / "_ops/state/telegram/center-config.json"
if cfg.exists():
    d = json.loads(cfg.read_text(encoding="utf-8"))
    report["center_config_keys"] = sorted(d.keys())
    for k, v in d.items():
        if v is None:
            continue
        if any(x in k.lower() for x in ["owner", "chat", "token"]):
            s = str(v)
            report["cfg_" + k] = {"len": len(s), "sha12": hashlib.sha256(s.encode()).hexdigest()[:12]}
print(json.dumps(report, indent=2))
