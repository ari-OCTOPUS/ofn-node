import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, "/tmp")
import g27server

GLASS_ART = ("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/"
             "glass_runner.py")
OWNER = 6150431610
REG_X = "a03b2ecc" + "9" * 56
REG_Y = "c" * 64
REG_Z = "d" * 64


def b3txt(h):
    return "Confirming " + h


fx = pathlib.Path(tempfile.mkdtemp(prefix="dbg-s6b-"))
for d in ("lanes/b3", "lanes/money", "pulse"):
    (fx / d).mkdir(parents=True, exist_ok=True)
od = fx / "owner_dialogue"
od.mkdir(parents=True, exist_ok=True)
(od / "go_b3_pending_registry.json").write_text(json.dumps(
    {"requests": [{"id": "CARD-X", "card": "CARD-X", "payload_sha256": REG_X,
                   "status": "pending"}]}), encoding="utf-8")
srv = str(fx / "server.json")
g27server.new(srv)


def glass():
    return subprocess.run([sys.executable, "/tmp/g27runner.py", GLASS_ART,
                           str(fx), srv, "normal"], capture_output=True, text=True)


def binder(w, m="poll"):
    return subprocess.run([sys.executable, "/tmp/g27binder.py", w, str(fx), srv, m],
                          capture_output=True, text=True)


def dump(tag):
    reg = json.loads((od / "go_b3_pending_registry.json").read_text(encoding="utf-8"))
    dec = []
    if (od / "owner_decision.v1.jsonl").exists():
        dec = [json.loads(l) for l in (od / "owner_decision.v1.jsonl").read_text(
            encoding="utf-8").splitlines() if l.strip()]
    print(tag, "reg:", [(r["id"], r["status"]) for r in reg["requests"]],
          "| dec:", [(d.get("verdict"), d.get("reason", "")) for d in dec])


g27server.enqueue(srv, 4001, OWNER, b3txt(REG_X))
r = binder("old", "crash_before_spool")
print("S4 crash rc:", r.returncode)
glass()
glass()
r = binder("new", "consume")
print("S5 consume:", r.stdout.strip()[-120:], r.stderr[-120:])
dump("S5")

# S6 EXACTLY as the drill: append CARD-Z FIRST, then 5001
reg = json.loads((od / "go_b3_pending_registry.json").read_text(encoding="utf-8"))
reg["requests"].append({"id": "CARD-Z", "card": "CARD-Z",
                        "payload_sha256": REG_Z, "status": "pending"})
(od / "go_b3_pending_registry.json").write_text(json.dumps(reg), encoding="utf-8")
g27server.enqueue(srv, 5001, OWNER, b3txt(REG_Y))
r = binder("old")
print("S6 poll1:", r.stdout.strip()[-120:], "stderr:", r.stderr[-200:])
dump("S6a")
