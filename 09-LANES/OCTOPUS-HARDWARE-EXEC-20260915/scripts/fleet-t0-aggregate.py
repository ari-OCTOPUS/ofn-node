#!/usr/bin/env python3
import json, sys, pathlib
outdir = pathlib.Path(sys.argv[1])
roles = {
  "138":"commander-router-ledger-owner","180":"quality-brain","182":"lab-witness",
  "100":"compute-node","160":"compute-node","193":"model-server","114":"compute-node"
}
nodes = ["138","180","182","100","160","193","114"]
rows = []
for ip in nodes:
    raw = outdir / f"raw-{ip}.txt"
    row = {"node": ip, "ip": f"192.168.0.{ip}", "role": roles[ip], "collect_status": "MISSING"}
    if not raw.exists():
        rows.append(row)
        continue
    text = raw.read_text(encoding="utf-8", errors="replace")
    row["collect_status"] = "OK"
    for line in text.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        row[k] = v
    if str(row.get("SSH_OR_LOCAL_EXIT", "0")) != "0":
        row["collect_status"] = f"EXIT_{row.get('SSH_OR_LOCAL_EXIT')}"
    rows.append(row)
out = outdir / "fleet-inventory-t0.json"
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("wrote", out, "rows", len(rows))
for r in rows:
    print(r["node"], r.get("OS_CODENAME"), "librknnrt="+str(r.get("LIBRKKNRT_COUNT")),
          str(r.get("OCTOPUS_SVC_NAMES",""))[:50], r.get("collect_status"))
