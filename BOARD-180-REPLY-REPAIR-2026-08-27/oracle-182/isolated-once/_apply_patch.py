from pathlib import Path
iso = Path(r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\oracle-182\isolated-once")
prod = (iso / "octopus_witness_worker.py.prodcopy").read_text(encoding="utf-8")
lines = prod.splitlines()

hit = 0
for i, l in enumerate(lines):
    if l == "    def cycle(self) -> dict:":
        lines[i] = "    def cycle(self, max_n=None) -> dict:"
        hit += 1
        break
assert hit == 1, "cycle sig"

hit = 0
for i, l in enumerate(lines):
    if l == "        results = []":
        lines.insert(i + 1, "        claimed = 0")
        hit += 1
        break
assert hit == 1, "results"

claim_line = "            if not self.claim(item[\"path\"], msg):"
hit = 0
for i, l in enumerate(lines):
    if l == claim_line:
        cap = [
            "            if max_n is not None and claimed >= max_n:",
            "                results.append({\"mid\": mid, \"action\": \"skipped_cap\"})",
            "                continue",
        ]
        lines[i:i] = cap
        hit += 1
        break
assert hit == 1, "cap"

hit = 0
for i, l in enumerate(lines):
    if l == "            self.pre_register_plan(msg)":
        lines.insert(i, "            claimed += 1")
        hit += 1
        break
assert hit == 1, "incr"

hit = 0
for i, l in enumerate(lines):
    if l == "        return {\"paused\": False, \"results\": results}":
        lines[i] = "        return {\"paused\": False, \"results\": results, \"claimed\": claimed, \"max_n\": max_n}"
        hit += 1
        break
assert hit == 1, "ret"

main_insert = None
for i, l in enumerate(lines):
    if l == "        return _crash_and_soak(args.root, args.cycles)":
        main_insert = i
        break
assert main_insert is not None
# allow one or two blanks after crash_test return
k = main_insert + 1
while k < len(lines) and lines[k] == "":
    k += 1
assert lines[k].startswith("def _crash_and_soak"), repr(lines[main_insert:main_insert+5])
insert = [
    "    if args.once:",
    "        max_n = int(os.environ.get(\"WITNESS_ONCE_MAX\", \"1\"))",
    "        r = w.cycle(max_n=max_n)",
    "        print(json.dumps(r, indent=1, ensure_ascii=False))",
    "        return 0",
    "    max_n = int(os.environ.get(\"WITNESS_ONCE_MAX\", \"1\"))",
    "    for i in range(args.cycles):",
    "        w.cycle(max_n=max_n)",
    "        if i + 1 < args.cycles:",
    "            time.sleep(args.interval)",
    "    return 0",
    "",
]
lines[main_insert + 1 : main_insert + 2] = [""] + insert

dead_start = None
for i, l in enumerate(lines):
    if l == "    return 0 if not dup else 1":
        dead_start = i
        break
assert dead_start is not None
j = dead_start + 1
while j < len(lines) and not lines[j].startswith("if __name__"):
    j += 1
lines[dead_start + 1 : j] = ["", ""]

text = "\n".join(lines) + "\n"
(iso / "octopus_witness_worker.py").write_text(text, encoding="utf-8", newline="\n")
print("patched lines", len(lines), "bytes", (iso / "octopus_witness_worker.py").stat().st_size)

stub = (
    "# Isolated stub — not 182 production.\n"
    "def validate_envelope(msg, policy):\n"
    "    return {\"valid\": True, \"classification\": \"verification_accepted\", \"reasons\": []}\n"
    "\n"
    "def sha256_hex(obj):\n"
    "    return \"0\" * 64\n"
)
(iso / "octopus_verifier.py").write_text(stub, encoding="utf-8", newline="\n")
print("stub ok")
