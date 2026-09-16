import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, allow, deny, append_ledger

# Any outbound-capable command is denied. Reading the network is a separate,
# owner-approved gateway inside the repository, not a shell command.
BLOCK = re.compile(
    r"\b(curl|wget|nc|ncat|telnet|ssh|scp|rsync|sftp|ftp|http\.client|requests\.(get|post)|"
    r"urllib|aiohttp|httpx|mail|sendmail|mutt|smtplib|git\s+push|gh\s+(pr|release|issue)|"
    r"docker\s+push|npm\s+publish|pip\s+upload|twine)\b", re.I)

cmd = (read_input().get("command") or "")
if BLOCK.search(cmd):
    append_ledger({"kind": "egress_denied", "command": cmd[:400]})
    deny("Egress blocked by OCTOPUS policy. No agent-initiated outbound traffic.",
         "Outbound network and publish commands are denied. Work offline and record the need in 07-HANDOFF/.")
allow()
