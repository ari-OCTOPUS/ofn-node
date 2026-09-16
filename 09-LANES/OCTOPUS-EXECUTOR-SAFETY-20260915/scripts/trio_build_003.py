#!/usr/bin/env python3
"""TRIO-003 targeted semantic merger (lane OCTOPUS-EXECUTOR-SAFETY-20260915).

Reads the post-hardening executor-safety base (sha beaee58c) and the historical
TRIO artifact (sha f6bc8d1c), and applies ONLY the net-new TRIO blocks that are
missing from the hardened base, using exact-anchor extraction from the
authoritative historical artifact (byte-exact splice, no retyping):

  B5  completeness/quarantine   (_b5_measure + quarantine + target-set-bytes)
  G3  priority ordering         (_spool_order)
  S4a in-memory byte-copy barrier (.deploy.tmp + fsync + os.replace)
  S4b precondition freeze/recheck (preconditions_verified -> PRECONDITION_DRIFT)
  decision consumer wired into tick (consume_decisions + results["decisions"])
  read_receipts torn-line fail-closed tolerance

Everything the hardened base already carries is preserved untouched:
OW-8 no-starvation, canonical category (OW-8b), CATSCOPE class match,
F-001 layer1/layer2, request+proposal receipts, success-only retire.

Safety gates: every anchor must match EXACTLY ONCE; py_compile must pass;
control-byte scan; net-new and preserved marker assertions; forbidden-pattern
assertions. On any failure the builder stops WITHOUT writing the artifact.
"""
import difflib
import hashlib
import py_compile
import sys

BASE = "/home/ari/ofn/state/coding-worker/stage/EXECUTOR-SAFETY-20260915/ops_agent.py"
TRIO = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
        "ops_agent.py")
OUT = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-003-20260915/"
       "ops_agent.py")

BASE_SHA = "beaee58cc952351001b6b34c8658cbb7ef689b00510e866ffa172a4eb390682f"
TRIO_SHA = "f6bc8d1c5759a64e597abd724f1b690e4b907b82bb4ac9e7acf5d6452a9545d9"


def die(msg):
    print("BUILD-ABORT:", msg)
    sys.exit(1)


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def once(text, anchor, where):
    n = text.count(anchor)
    if n != 1:
        die("anchor not unique (%d) in %s: %r" % (n, where, anchor[:80]))
    return text.index(anchor)


def seg(text, start, end, where):
    """Extract text[start .. end+len(end)] inclusive of both anchors."""
    i = once(text, start, where)
    j = text.find(end, i + len(start))
    if j < 0:
        die("end anchor not found after start in %s" % where)
    return text[i:j + len(end)]


def replace_seg(text, start, end, new, where):
    i = once(text, start, where)
    j = text.find(end, i + len(start))
    if j < 0:
        die("end anchor not found after start in %s" % where)
    return text[:i] + new + text[j + len(end):]


def replace_once(text, old, new, where):
    once(text, old, where)
    return text.replace(old, new, 1)


def main():
    # ---------- inputs + identity gates ----------
    if sha256_file(BASE) != BASE_SHA:
        die("post-hardening base sha mismatch")
    if sha256_file(TRIO) != TRIO_SHA:
        die("historical TRIO artifact sha mismatch")
    base = open(BASE, encoding="utf-8").read()
    trio = open(TRIO, encoding="utf-8").read()
    orig_base = base

    # ---------- E0: _cat_key helper + class-scoped OUTCOME_REJECTED filter ----------
    # The hardened base kept the weak category[-2:] substring match for the
    # outcome-rejection breaker line (overlap #1). TRIO's _cat_key fix is
    # class-scoped and conflicts with nothing hardened; the hardened `fails`
    # startswith form and legacy fixed_at handling stay untouched.
    ck = seg(trio, "def _cat_key(category: str) -> str:",
             "    return category.split('_')[0]",
             "trio/_cat_key") + "\n\n\n"
    base = replace_once(base, "def budget_allows(category: str, component: str, now: float | None = None) -> tuple:",
                        ck + "def budget_allows(category: str, component: str, now: float | None = None) -> tuple:",
                        "base/budget_allows-def")
    base = replace_once(
        base,
        '    orej = [r for r in rows if r.get("kind") == "OPS_B_OUTCOME_REJECTED"\n'
        '            and category[-2:] in str(r.get("category", ""))]\n',
        '    orej = [r for r in rows if r.get("kind") == "OPS_B_OUTCOME_REJECTED"\n'
        '            and _cat_key(r.get("category", "")) == _cat_key(category)]\n',
        "base/orej-filter")
    # overlap resolution: the execution-failure breaker keeps the hardened
    # equality/prefix clauses AND gains the TRIO class-key clause (superset:
    # B8_ROLLBACK failure now blocks B8_CANARY too).
    base = replace_once(
        base,
        '    fails = [r for r in ex\n'
        '             if (r.get("category") == category\n'
        '                 or str(r.get("category", "")).startswith(category + "_"))\n'
        '             and r.get("verified") is False]\n',
        '    fails = [r for r in ex\n'
        '             if (r.get("category") == category\n'
        '                 or str(r.get("category", "")).startswith(category + "_")\n'
        '                 or _cat_key(r.get("category", "")) == _cat_key(category))\n'
        '             and r.get("verified") is False]\n',
        "base/fails-class-match")

    # ---------- E1: read_receipts torn-line fail-closed ----------
    new = seg(trio, "    out = []\n", "    return out\n", "trio/read_receipts")
    base = replace_once(
        base,
        '    return [json.loads(l) for l in RECEIPTS.read_text(encoding="utf-8")'
        ".splitlines() if l.strip()]\n",
        new, "base/read_receipts")

    # ---------- E2: _b5_measure inserted before handle_b5_storage ----------
    m_seg = seg(trio, "def _b5_measure(paths) -> tuple:",
                "\n\ndef handle_b5_storage", "trio/_b5_measure")
    m_seg = m_seg[:-len("\n\ndef handle_b5_storage")] + "\n\n"
    base = replace_once(base, "def handle_b5_storage(cat: dict, pins: dict) -> str:",
                        m_seg + "def handle_b5_storage(cat: dict, pins: dict) -> str:",
                        "base/handle_b5_storage-def")

    # ---------- E3: B5 body -> measurement + quarantine proposal ----------
    b_start = "        str(f).startswith(str(hp)) for hp in roots)]\n"
    b_old = seg(base, b_start, '"timeout_s": 30})',
                "base/handle_b5_storage-body")
    b_new = seg(trio, b_start, '"quarantine_dir": str(_qdir)})',
                "trio/handle_b5_storage-body")
    # the base segment must be the B5 one (it contains the rm -rf action spec)
    if '["rm", "-rf", str(f)]' not in b_old:
        die("base B5 body segment sanity failed")
    if "_b5_measure(targets)" not in b_new:
        die("trio B5 body segment sanity failed")
    base = replace_seg(base, b_start, '"timeout_s": 30})',
                       b_new, "base/handle_b5_storage-body")

    # ---------- E4: _spool_order inserted before handle_spool_category ----------
    s_seg = seg(trio, "def _spool_order(_spool):",
                "    return sorted(os.listdir(_spool), key=_key)",
                "trio/_spool_order") + "\n\n\n"
    base = replace_once(
        base, "def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:",
        s_seg + "def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:",
        "base/handle_spool_category-def")

    # ---------- E5: G3 priority loop order ----------
    base = replace_once(base, "    for name in sorted(os.listdir(spool)):\n",
                        "    for name in _spool_order(spool):\n",
                        "base/spool-loop")

    # ---------- E6: S4b freeze preconditions at proposal time ----------
    anchor = ("                    unmet=_unmet_pc[:3])\n"
              "            continue\n"
              "        if not backup or not Path(backup).exists():\n")
    pv = seg(trio, "        _preconds_verified = [",
             "                              for _pc in _preconds]",
             "trio/preconds_verified") + "\n"
    base = replace_once(base, anchor,
                        "                    unmet=_unmet_pc[:3])\n"
                        "            continue\n"
                        + pv +
                        "        if not backup or not Path(backup).exists():\n",
                        "base/precond-freeze")

    # ---------- E7: freeze extends the action map ----------
    base = replace_once(base, '"deps_verified": _deps_verified})',
                        '"deps_verified": _deps_verified,\n'
                        '                                  '
                        '"preconditions_verified": _preconds_verified})',
                        "base/action-map-freeze")

    # ---------- E8: S4b recheck + S4a barrier + B5 verify in _execute_pending ----------
    e_old = seg(base, '    raw = m.get("argv", [])',
                '                   proposal_id=exp["proposal_id"])',
                "base/_execute_pending-exec")
    e_new = seg(trio, '    for _pv in (m.get("preconditions_verified") or []):',
                "                   verify_kind=vk, **_extra)",
                "trio/_execute_pending-exec")
    # preserve the hardened provenance fields in the final receipt
    tail = ('                   verify_kind=vk, **_extra)')
    if e_new.count(tail) != 1:
        die("trio _execute_pending final receipt anchor not unique in segment")
    e_new = e_new.replace(
        tail,
        "                   verify_kind=vk, request=m.get(\"request\"),\n"
        "                   proposal_id=exp[\"proposal_id\"], **_extra)", 1)
    if 'for a in argvs:' not in e_old or 'SOURCE_UNREADABLE' not in e_new:
        die("E8 segment sanity failed")
    base = replace_seg(base, '    raw = m.get("argv", [])',
                       '                   proposal_id=exp["proposal_id"])',
                       e_new, "base/_execute_pending-exec")

    # ---------- E9: decision consumer inserted before goal engine ----------
    d_seg = seg(trio, "# ------------------------------------------------- decision consumer (Class A)",
                '    return "consumed" if n else "idle"',
                "trio/consume_decisions") + "\n\n\n"
    base = replace_once(
        base, "# ---------------------------------------------------------------- goal engine (Class A)",
        d_seg + "# ---------------------------------------------------------------- goal engine (Class A)",
        "base/goal-engine-comment")

    # ---------- E10: tick wiring ----------
    base = replace_once(
        base,
        "    # Class A goal engine every tick\n"
        "    ge = goal_engine(contracts)\n"
        "    # category handlers (skip if a witness cycle is mid-flight: one at a time)\n"
        '    results = {"goal_engine": ge, "progress": r1 or r2}\n',
        "    # Class A goal engine every tick\n"
        "    ge = goal_engine(contracts)\n"
        "    # owner chain final edge: decisions -> task resume (ACK clears a flag only)\n"
        '    results = {"decisions": consume_decisions()}\n'
        "    # category handlers (skip if a witness cycle is mid-flight: one at a time)\n"
        '    results["goal_engine"] = ge\n'
        '    results["progress"] = r1 or r2\n',
        "base/tick-wiring")

    # ---------- post-build gates ----------
    if "\r" in base:
        die("CR bytes in output")
    for ch in set(base):
        if ord(ch) < 0x20 and ch not in "\n\t":
            die("control byte 0x%02x in output" % ord(ch))

    net_new = ["_b5_measure", "B5_MEASUREMENT_INCOMPLETE", "B5_NOTHING_MEASURABLE",
               "b5-quarantine", "target-set-bytes:", "_spool_order",
               "preconditions_verified", "PRECONDITION_DRIFT",
               "SOURCE_UNREADABLE", ".deploy.tmp", "os.fsync",
               "def consume_decisions", "DECISION_CONSUMED",
               'results = {"decisions": consume_decisions()}',
               "torn/partial line", "measurement-incomplete", "_cat_key"]
    preserved = ["CANONICAL_CATEGORY", "_verified_by_receipt", "_retire_executed",
                 "F001_SELF_RETIRE", "EXECUTE_DEFERRED_NOT_RETIRED",
                 'startswith(("ok", "executed", "proposal-sent"))',
                 "_any_blocked", 'return "budget-blocked" if _any_blocked',
                 '{"B8": "RY"}', "F-001 LAYER-1", "F-001 LAYER-2",
                 "OPS_B_REQUEST_ALREADY_EXECUTED", "witness-unavailable"]
    forbidden = ['for name in sorted(os.listdir(spool))',
                 '            and category[-2:] in str(r.get("category", ""))]',
                 '["rm", "-rf", str(f)] for f in findings',
                 '"verify_kind": "paths-absent:"']
    for m in net_new:
        if m not in base:
            die("net-new marker missing: %r" % m)
    for m in preserved:
        if m not in base:
            die("preserved marker missing: %r" % m)
    for m in forbidden:
        if m in base:
            die("forbidden pattern present: %r" % m)

    tmp = OUT + ".build-tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(base)
    py_compile.compile(tmp, doraise=True)
    import os
    os.replace(tmp, OUT)

    diff = list(difflib.unified_diff(
        orig_base.splitlines(), base.splitlines(), lineterm=""))
    adds = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    dels = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    print("BUILD-OK", OUT)
    print("sha256:", hashlib.sha256(base.encode("utf-8")).hexdigest())
    print("diff vs hardened base: +%d -%d lines" % (adds, dels))
    print("all gates passed: anchors unique, py_compile OK, control-byte scan OK, "
          "%d net-new markers, %d preserved markers, %d forbidden absent"
          % (len(net_new), len(preserved), len(forbidden)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
