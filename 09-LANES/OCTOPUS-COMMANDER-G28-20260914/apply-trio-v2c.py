"""TRIO v2c: quarantine mv with UNIQUE destination names - same-basename
targets (multiple __pycache__) collided in the quarantine dir: the first mv
won, every later one failed rc=1. mv-to-explicit-unique-name is pure rename
semantics and cannot collide."""
import ast, hashlib, pathlib, shutil, sys
P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v2b-aa867bfb"
OLD = '    action_spec = {"commands": [["mkdir", "-p", str(_qdir)]] +\n                               [["mv", str(f), str(_qdir)] for f in targets],\n'
NEW = '    action_spec = {"commands": [["mkdir", "-p", str(_qdir)]] +\n                               [["mv", str(f),\n                                  str(_qdir / ("%03d-%s" % (i, f.name)))]\n                                 for i, f in enumerate(targets)],\n'
raw = P.read_bytes(); old = raw.decode("utf-8")
if raw != old.encode("utf-8"): sys.exit("roundtrip")
if old.count(OLD) != 1: sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW); ast.parse(new)
shutil.copy2(P, PRE); P.write_bytes(new.encode("utf-8"))
print("v2b preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v2c         :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
