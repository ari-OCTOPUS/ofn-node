"""Wire the G30 stage-guard into the REAL worker staging path (owner mission هـ).

The staging loop in coding_worker.process_patch_task writes each patched file
and only ast-parses .py files. The G30 defect class (a JSON "\b" replacement
decoding to a literal backspace, plus EOL mixing) passed both gates. This patch
adds a byte-level guard on the STAGED file immediately after write, raising
ValueError so the existing PATCH_REJECTED disposition fires - the guard sits on
the real path patch JSON -> decode -> anchor -> staging -> guard, BEFORE any
test run or proposal. Preimage kept; artifact staged for a later quota slot."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
STAGE_DIR = pathlib.Path(
    "/home/ari/ofn/state/coding-worker/stage/G30-STAGE-GUARD-WIRING-001")
OLD = """            with (stage / rel).open("w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
"""
NEW = """            with (stage / rel).open("w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
            # G30 guard 2026-09-14: byte-scan the STAGED file (not the parsed
            # AST) - a JSON "\\b" replacement decodes to a literal backspace and
            # ast.parse accepts it silently; mixed EOLs corrupt anchors later.
            _sb = (stage / rel).read_bytes()
            _ctrl = [c for c in _sb if c < 0x20 and c not in (0x0a, 0x09)]
            _cr = _sb.count(b"\\r\\n")
            _lf = _sb.count(b"\\n") - _cr
            if _ctrl or (_cr and _lf):
                raise ValueError("STAGE_BYTES_DIRTY:ctrl=%d crlf=%d lf=%d rel=%s"
                                 % (len(_ctrl), _cr, _lf, rel[:40]))
"""

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
if old.count(OLD) != 1:
    sys.exit("ABORT: anchor count = %d" % old.count(OLD))
if "STAGE_BYTES_DIRTY" in old:
    sys.exit("ABORT: already applied")
new = old.replace(OLD, NEW)
ast.parse(new)
STAGE_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy2(P, STAGE_DIR / "coding_worker.py.pre-g30guard")
(STAGE_DIR / "coding_worker.py").write_bytes(new.encode("utf-8"))
print("live worker   :", hashlib.sha256(P.read_bytes()).hexdigest()[:16], "(UNTOUCHED)")
print("staged patched:", hashlib.sha256(
    (STAGE_DIR / "coding_worker.py").read_bytes()).hexdigest()[:16])
