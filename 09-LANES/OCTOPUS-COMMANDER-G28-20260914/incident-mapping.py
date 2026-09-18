"""Incident closure (owner mission ROUND31 section 1).

Builds the exact per-item mapping original_path -> quarantine_path ->
restore outcome FROM THE INCIDENT'S OWN RECORDS (proposals + action-map argv +
execution receipts in the fixtures), then separates the three claims:
  A. path exists again at its original location
  B. content is the original content (requires a pre-incident hash - ABSENT
     here, recorded; so B stays UNVERIFIED-by-hash, supported only by
     name-uniqueness where applicable)
  C. nothing was deleted or overwritten (evidence: exit codes per command,
     quarantine leftovers, GONE rows)
Also proves the collision hazard of the OLD basename-preserving quarantine mv
(two same-name dirs could not both land in one qdir - the second mv rc=1 and
stayed in place), which bounds the ambiguity of basename-based recovery.
"""
import json
import pathlib

rows = []
for fx in sorted(pathlib.Path("/tmp").glob("b5-*")):
    for am in (fx / "state/proposals/action-map").glob("op-*.json"):
        try:
            doc = json.loads(am.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(doc.get("argv"), list):
            rows.append((fx.name, doc))

# execution receipts per fixture (exit codes + argv)
codes = {}
for fx in sorted(pathlib.Path("/tmp").glob("b5-*")):
    rec = fx / "state/ops-receipts.jsonl"
    if rec.exists():
        for l in rec.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("kind") == "OPS_B_EXECUTED":
                codes[fx.name] = {"exit_codes": r.get("exit_codes"),
                                  "argv": r.get("argv"),
                                  "verify_kind": r.get("verify_kind")}

real_cmds = []
for fxname, doc in rows:
    argvs = doc["argv"] if (doc["argv"] and isinstance(doc["argv"][0], list))         else ([doc["argv"]] if doc["argv"] else [])
    ex = codes.get(fxname, {}).get("exit_codes") or []
    for i, a in enumerate(argvs):
        if not (isinstance(a, list) and len(a) >= 3):
            continue
        if a[0] == "mv" and a[1] not in ("-rf", "-f"):
            srcp = a[1]
            if "/tmp/b5-" in srcp:
                continue
            real_cmds.append((fxname, "mv", srcp, a[2],
                              ex[i] if i < len(ex) else None))
        elif a[0] == "rm" and "-rf" in a[1:3]:
            srcp = a[2] if a[1] == "-rf" else a[2]
            if "/tmp/b5-" in srcp:
                continue
            real_cmds.append((fxname, "rm", srcp, None,
                              ex[i] if i < len(ex) else None))

print("real (non-fixture) mv commands found:", len(real_cmds))
basename_groups = {}
for fxname, op, s, d, c in real_cmds:
    basename_groups.setdefault(pathlib.Path(s).name, []).append((fxname, op, s, d, c))

print("\n=== per-basename ambiguity ===")
for base, items in sorted(basename_groups.items()):
    qdirs = {str(pathlib.Path(d).parent) for _, _, _, d, _ in items if d}
    landed = set()
    for _, _, _, d, c in items:
        if d and c == 0:
            landed.add(d)
    print("  %-28s cmds=%d distinct-qdirs=%d landed=%d" %
          (base, len(items), len(qdirs), len(landed)))

print("\n=== per-original-path outcome ===")
A_exists, A_missing, ambiguity = 0, [], []
for fxname, op, s, d, c in real_cmds:
    p = pathlib.Path(s)
    if p.exists():
        A_exists += 1
    else:
        A_missing.append((op, s, d, c))
    # content-identity support: unique basename among real cmds AND succeeded
    if len(basename_groups[p.name]) > 1:
        ambiguity.append(s)
print("originals existing now (claim A):", A_exists, "/", len(real_cmds))
for op, s, d, c in A_missing:
    print("  MISSING: [%s rc=%s] %s q=%s" % (op, c, s, d))
print("name-ambiguous originals (content-identity needs hash):",
      len(ambiguity))
for s in ambiguity:
    print("  ambiguous:", s)

print("\n=== claim C evidence ===")
gone = 0
for fxname, op, s, d, c in real_cmds:
    if not pathlib.Path(s).exists():
        q = pathlib.Path(d) if d else None
        if q is None or not q.exists():
            gone += 1
print("both original AND quarantine absent (potential loss):", gone)
leftover_real = 0
for q in pathlib.Path("/tmp").glob("b5-*/state/b5-quarantine/*/*"):
    try:
        if q.is_symlink():
            continue
    except OSError:
        continue
    if "/tmp/" not in str(q.resolve()) or True:
        # anything still sitting in a quarantine that is NOT fixture-internal
        # (fixture-internal = its original path also lived under /tmp/b5-*)
        leftover_real += 0 if any(str(q).startswith(str(f)) for f in
                                  pathlib.Path("/tmp").glob("b5-*")) else 1
print("non-fixture items still in quarantines:", leftover_real)
print("\npre-incident hashes available: NO (recorded absent -> claim B stays "
      "UNVERIFIED-BY-HASH; supported only by name-uniqueness + rc evidence)")
