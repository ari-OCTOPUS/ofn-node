import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, allow, deny, append_ledger

SENSITIVE = re.compile(r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa|id_ed25519|secrets?\.(ya?ml|json|toml)|"
                       r".*credentials.*|.*token.*\.txt)$", re.I)

fp = (read_input().get("file_path") or "")
if SENSITIVE.search(fp.replace("\\", "/")):
    append_ledger({"kind": "secret_read_denied", "file_path": fp})
    deny(f"Read denied: {fp} may contain secret values.",
         "Secret files are not readable. Reference the key name only, never the value.")
allow()
