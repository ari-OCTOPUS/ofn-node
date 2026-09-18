import os

cands = [
    "/home/ari/ofn/data/state",
    "/home/ari/octopus-mesh/state",
]
hits = []
for root in cands:
    if not os.path.isdir(root):
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            low = fn.lower()
            if any(s in low for s in ("outbox", "telegram", "journal")) and low.endswith(
                (".json", ".jsonl", ".log")
            ):
                p = os.path.join(dirpath, fn)
                try:
                    n = os.path.getsize(p)
                except OSError:
                    n = -1
                hits.append((p, n))
        if len(hits) > 40:
            break
    if len(hits) > 40:
        break
print("N", len(hits))
for p, n in hits[:40]:
    print("FILE", n, p)
