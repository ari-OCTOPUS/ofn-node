from pathlib import Path
# writer_lease renew + tg attach_defer + wired/token resolution
print("=== writer_lease renew ===")
lines = Path(r"F:/backup/_ops/writer_lease.py").read_text(encoding="utf-8").splitlines()
print("\n".join(f"{i+1}: {l}" for i,l in enumerate(lines[90:160])))
print("=== tg_api attach/wired ===")
lines2 = Path(r"F:/backup/_ops/telegram_center/tg_api.py").read_text(encoding="utf-8").splitlines()
for i,l in enumerate(lines2,1):
    if any(k in l for k in ["attach_defer", "def wired", "token_source", "_env", "TG_CENTER", "TELEGRAM_BOT"]):
        print(f"{i}: {l[:150]}")
# stop files
root = Path(r"F:/backup/_ops")
for name in ["STOP-TG-HEARTBEAT","STOP-ORGANISM","HALT-ALL","STOP-ALL"]:
    p = root/name
    print(name, "exists", p.exists())
ks = Path(r"F:/backup/_ops/state/telegram/loop/kill-switch.json")
print("kill-switch", ks.exists(), ks.read_text(encoding='utf-8')[:200] if ks.exists() else "")
