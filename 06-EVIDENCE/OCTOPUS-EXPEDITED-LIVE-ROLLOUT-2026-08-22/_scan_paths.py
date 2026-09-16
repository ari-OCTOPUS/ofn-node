from pathlib import Path
# inspect pass3_live, instant_alert, and how writer lock / allow_live_write used in prior scripts
for rel in [
  "_ops/loops/pass3_live.py",
  "_ops/instant_alert_bridge.py",
  "_ops/tests/live_state_guard.py",
]:
  p = Path(r"F:/backup") / rel
  print("====", rel)
  t = p.read_text(encoding="utf-8", errors="replace")
  for i,l in enumerate(t.splitlines(),1):
    if any(k in l.lower() for k in ["def ", "canary", "owner", "send", "outbox", "allow_live", "enqueue", "main"]):
      if l.strip().startswith(("def ","class ","#","\"\"\"","'''")) or any(x in l for x in ["canary","allow_live","OWNER","outbox","SenderBridge","send("]):
        print(f"{i}: {l[:160]}")
  print()
