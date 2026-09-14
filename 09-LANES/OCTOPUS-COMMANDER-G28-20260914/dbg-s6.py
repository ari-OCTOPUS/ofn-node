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


fx = pathlib.Path(tempfile.mkdtemp(prefix="dbg-s6-"))
for d in ("lanes/b3", "lanes/money", "pulse"):
    (fx / d).mkdir(parents=True, exist_ok=True)
od = fx / "owner_dialogue"
od.mkdir(parents=True, exist_ok=True)
(od / "go_b3_pending_registry.json").write_text(json.dumps(
    {"requests": [{"id": "CARD-X", "card": "CARD-X", "payload_sha256": REG_X,
                   "status": "pending"},
                  {"id": "CARD-Y", "card": "CARD-Y", "payload_sha256": REG_Y,
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
    dec = [json.loads(l) for l in (od / "owner_decision.v1.jsonl").read_text(
        encoding="utf-8").splitlines()] if (od / "owner_decision.v1.jsonl").exists() else []
    reg = json.loads((od / "go_b3_pending_registry.json").read_text(encoding="utf-8"))
    print(tag, "decisions:", [(d.get("verdict"), d.get("reason", ""),
                               str(d.get("bound_request_payload_sha256"))[:8])
                              for d in dec])
    print(tag, "registry:", [(r["id"], r["status"]) for r in reg["requests"]])


g27server.enqueue(srv, 4001, OWNER, b3txt(REG_X))
r = binder("old", "crash_before_spool")
print("crash rc:", r.returncode)
glass(); glass()
r = binder("new", "consume")
print("S5 consume:", r.stdout.strip()[-160:])
dump("S5")

g27server.enqueue(srv, 5001, OWNER, b3txt(REG_Y))
r = binder("old"); print("S6 bind5001 poll1:", r.stdout.strip()[-120:], r.stderr[-120:])
dump("S6a")
r = binder("old"); print("S6 poll2:", r.stdout.strip()[-120:])
g27server.enqueue(srv, 5002, OWNER, b3txt("e" * 64))
# re-add a fresh card for 5002 like the drill does
reg = json.loads((od / "go_b3_pending_registry.json").read_text(encoding="utf-8"))
reg["requests"].append({"id": "CARD-Z", "card": "CARD-Z",
                        "payload_sha256": "e" * 64, "status": "pending"})
(od / "go_b3_pending_registry.json").write_text(json.dumps(reg), encoding="utf-8")
glass(); glass()
r = binder("old"); print("S6 poll3:", r.stdout.strip()[-120:])
r = binder("new", "consume")
print("S6 consume5002:", r.stdout.strip()[-200:])
dump("S6b")
