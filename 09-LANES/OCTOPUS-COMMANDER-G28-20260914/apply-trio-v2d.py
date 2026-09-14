"""TRIO v2d: for target-set-bytes actions the VERDICT IS THE MEASUREMENT -
the branch moves out of the rc==0 gate so a partial mv failure (e.g. one
unreadable dir) still reports VERIFIED with explicit freed bytes and the
failing exit codes; freed==0 stays FAILED honestly."""
import ast, hashlib, pathlib, shutil, sys
P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v2c-ae293073"
OLD = '''    verified = False
    _extra = {}
    if rc == 0:
        if vk.startswith("is-active:"):'''
NEW = '''    verified = False
    _extra = {}
    if vk.startswith("target-set-bytes:"):
        # measurement IS the verdict: command exit codes are reported but do
        # not gate the frozen-set criterion (partial access failures stay
        # explicit; freed==0 still fails honestly)
        want = int(vk.split(":", 1)[1] or 0)
        after, errs_after = _b5_measure(m.get("target_set") or [])
        _extra.update({"bytes_before": want, "bytes_after": after,
                       "bytes_freed": want - after,
                       "access_errors_after": errs_after})
        verified = want > 0 and (want - after) > 0
    elif rc == 0:
        if vk.startswith("is-active:"):'''
raw = P.read_bytes(); old = raw.decode("utf-8")
if raw != old.encode("utf-8"): sys.exit("roundtrip")
if old.count(OLD) != 1: sys.exit("anchor=%d" % old.count(OLD))
# remove the old in-gate branch (now dead)
DEAD = '''        elif vk.startswith("target-set-bytes:"):
            # B5 same-scope criterion: logical bytes of the FROZEN target set
            # (from the action record), the SAME counting rule on both sides.
            # Changes OUTSIDE the frozen set never affect the verdict; the set
            # is never re-enumerated. Explicit numbers land in the receipt.
            want = int(vk.split(":", 1)[1] or 0)
            after, errs_after = _b5_measure(m.get("target_set") or [])
            _extra.update({"bytes_before": want, "bytes_after": after,
                           "bytes_freed": want - after,
                           "access_errors_after": errs_after})
            verified = want > 0 and (want - after) > 0
'''
if old.count(DEAD) != 1: sys.exit("dead-branch anchor=%d" % old.count(DEAD))
new = old.replace(OLD, NEW).replace(DEAD, "")
ast.parse(new)
shutil.copy2(P, PRE); P.write_bytes(new.encode("utf-8"))
print("v2c preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v2d         :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
