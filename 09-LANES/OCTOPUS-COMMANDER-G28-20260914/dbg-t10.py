import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, "/tmp")
import g27server

ART = "/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py"
for mode, why in (("transport_none", "transport_none"),
                  ("transport_not_ok", "transport_not_ok"),
                  ("transport_malformed", "transport_malformed:list")):
    fx = pathlib.Path(tempfile.mkdtemp(prefix="dbg10b-"))
    for d in ("lanes/b3", "lanes/money", "pulse"):
        (fx / d).mkdir(parents=True)
    (fx / "registry.json").write_text("{}")
    srv = str(fx / "server.json")
    g27server.new(srv)
    g27server.enqueue(srv, 901, 6150431610, "hello")
    r = subprocess.run([sys.executable, "/tmp/g27runner.py", ART, str(fx), srv,
                        mode], capture_output=True, text=True, timeout=60)
    out = {}
    for line in (r.stdout or "").splitlines():
        try:
            out = json.loads(line)
        except ValueError:
            pass
    s = g27server._load(srv)

    def lid(fx):
        ids = set()
        for lane in ("b3/go_b3_inbox.jsonl", "money/tg-inbox.jsonl"):
            p = fx / "lanes" / lane
            if p.exists():
                for l in p.read_text().splitlines():
                    if l.strip():
                        try:
                            ids.add(json.loads(l)["update_id"])
                        except Exception:
                            pass
        return ids

    cur = fx / "pulse/glass-offset.txt"
    conds = [r.returncode == 0, out.get("transport") == "error",
             out.get("reason") == why, out.get("offset") == 0,
             s["server_confirmed"] == [], bool(s["queue"]),
             lid(fx) == set(),
             (not cur.exists()) or cur.read_text().strip() == "0",
             len(s["requested_offsets"]) == 1]
    print(mode, conds, "out=", out, "stderr=", (r.stderr or "")[-200:])
