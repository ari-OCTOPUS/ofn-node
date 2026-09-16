#!/usr/bin/env python3
"""paid_path_probe.py — run INSIDE the coding-worker sandbox.

Proves, without spending, that the service can:
  1. read the credential file (mode 600, owner ari) under ProtectHome=read-only,
  2. import the broker registry and resolve live providers,
  3. reach a provider's models endpoint (metadata only — not billed).
Prints booleans / model names / counts. Never a credential value.
"""
import os
import pathlib
import sys

sys.path.insert(0, "/home/ari/ofn/state/api-budget")

F = pathlib.Path("/home/ari/.config/ofn/external-models.env")
print("uid=%s user=%s" % (os.getuid(), os.environ.get("USER", "?")))
try:
    data = F.read_bytes()
    print("credential_file_readable: True (%d bytes)" % len(data))
except OSError as exc:
    print("credential_file_readable: False (%s)" % type(exc).__name__)

try:
    import providers  # noqa: E402
    print("registry_import: True")
    print("candidates: %s" % providers.candidates())
    print("health: %s" % {p: providers.health_status(p) for p in providers.provider_ids()})
    for pid in ("deepseek", "gemini"):
        r = providers.list_models(pid)
        print("  %s models endpoint: ok=%s http=%s count=%s err=%s"
              % (pid, r.get("ok"), r.get("http_status"), r.get("count"), r.get("error")))
except Exception as exc:  # noqa: BLE001
    print("registry_import: False (%s: %s)" % (type(exc).__name__, str(exc)[:80]))

try:
    import api_budget  # noqa: E402
    print("broker_import: True")
    s = api_budget.status()
    print("budget: window=%s cap=%s spent=%s" % (s.get("window"), s.get("window_cap_usd"),
                                                 s.get("window_spent_usd")))
except Exception as exc:  # noqa: BLE001
    print("broker_import: False (%s)" % type(exc).__name__)

# can the worker WRITE only where it is allowed?
import tempfile  # noqa: E402
for p in ("/home/ari/ofn/state/coding-worker/state", "/tmp"):
    try:
        with tempfile.NamedTemporaryFile(dir=p, delete=True) as fh:
            fh.write(b"x")
        print("writable: %s True" % p)
    except Exception as exc:  # noqa: BLE001
        print("writable: %s False (%s)" % (p, type(exc).__name__))
try:
    pathlib.Path("/home/ari/.config/ofn/__probe_should_fail").write_text("x")
    print("credential_dir_writable: True  <-- TOO PERMISSIVE")
    pathlib.Path("/home/ari/.config/ofn/__probe_should_fail").unlink()
except Exception as exc:  # noqa: BLE001
    print("credential_dir_writable: False (%s)  <-- correct" % type(exc).__name__)
