"""TRIO v3d: the tick's original results-binding dropped the decisions key;
merge instead of rebind."""
import ast, hashlib, pathlib, shutil, sys
P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v3c-db03333d"
OLD = '''    results = {"goal_engine": ge, "progress": r1 or r2}'''
NEW = '''    results["goal_engine"] = ge
    results["progress"] = r1 or r2'''
raw = P.read_bytes(); old = raw.decode("utf-8")
if raw != old.encode("utf-8"): sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "db03333d": sys.exit("not v3c")
if old.count(OLD) != 1: sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW); ast.parse(new)
shutil.copy2(P, PRE); P.write_bytes(new.encode("utf-8"))
print("v3c preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v3d         :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
