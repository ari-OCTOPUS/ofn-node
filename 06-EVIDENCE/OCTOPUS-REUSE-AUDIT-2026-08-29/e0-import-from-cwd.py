import hashlib
import importlib
import os
import pathlib

os_cwd = pathlib.Path("/home/ari/ofn")
assert os_cwd.is_dir()
os.chdir(os_cwd)

modules = [
    "ofn.run",
    "ofn.adapters.http_api",
    "ofn.adapters.cockpit_v2_read_model",
    "ofn.adapters.ledger",
    "ofn.adapters.outbox",
    "ofn.adapters.owner_decision",
    "ofn.adapters.witness_mint",
    "ofn.adapters.fake_executor",
]

print("cwd", os_cwd)
for name in modules:
    try:
        m = importlib.import_module(name)
        p = pathlib.Path(m.__file__).resolve()
        data = p.read_bytes()
        print(
            name,
            f"path={p}",
            f"bytes={len(data)}",
            f"sha256={hashlib.sha256(data).hexdigest()}",
        )
    except Exception as exc:
        print(name, f"UNAVAILABLE:{type(exc).__name__}:{exc}")

for rel in (
    "ofn/adapters/cockpit_v2_read_model.py",
    "ofn/adapters/http_api.py",
):
    p = os_cwd / rel
    text = p.read_text(encoding="utf-8", errors="replace")
    physical = len(text.splitlines())
    nonempty = sum(1 for ln in text.splitlines() if ln.strip())
    print(
        "LINECOUNT",
        rel,
        "physical",
        physical,
        "nonempty",
        nonempty,
        "bytes",
        p.stat().st_size,
        "cmd=splitlines+strip",
    )
