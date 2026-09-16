from pathlib import Path
ob=Path(r"F:\backup\07 - Knowledge\octopus\76-OCTOPUS-CONTINUOUS-CHECKPOINT-2026-08-23.md")
print(ob.read_text(encoding="utf-8", errors="replace"))
print("\n==== BLOCKER.json ====")
print(Path(r"F:\backup\06-EVIDENCE\OCTOPUS-A18-BLOCKER-2026-08-23\BLOCKER.json").read_text(encoding="utf-8", errors="replace")[:2000])
print("\n==== CURRENT-TRUTH head 80 lines ====")
ct=Path(r"F:\backup\OCTOPUS\CURRENT-TRUTH.md").read_text(encoding="utf-8", errors="replace").splitlines()
for i,l in enumerate(ct[:80],1):
    print(f"{i}|{l}")
