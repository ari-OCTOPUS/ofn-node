// splice_obsidian.js — insert the three additive blocks (RTL-safe, per-file EOL).
const fs = require("fs");
const path = require("path");

const ROOT = "F:/backup";
const BLOCKS = path.join(ROOT, "09-LANES/API-BUDGET-ACTIVATION-20260913/evidence/obsidian_blocks");
const today = new Date().toISOString().slice(0, 10);

const TARGETS = [
  [path.join(ROOT, "01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md"), path.join(BLOCKS, "vital.md"), "after_h1"],
  [path.join(ROOT, "06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md"), path.join(BLOCKS, "truth.md"), "tail"],
  [path.join(ROOT, "ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907.md"), path.join(BLOCKS, "season.md"), "tail"],
];

for (const [file, blockFile, mode] of TARGETS) {
  if (!fs.existsSync(file)) { console.log("MISSING:", file); continue; }
  const raw = fs.readFileSync(file, "utf8");
  const eol = raw.includes("\r\n") ? "\r\n" : "\n";
  let lines = raw.split(eol);

  if (lines.some((l) => l.includes("MULTI_PROVIDER_COGNITION_ACTIVE"))) {
    console.log("ALREADY PRESENT, skipped:", path.basename(file));
    continue;
  }

  const block = fs.readFileSync(blockFile, "utf8")
    .split(/\r?\n/)
    .filter((_, i, arr) => !(i >= arr.length - 1 && arr[i] === ""));

  if (mode === "after_h1") {
    let idx = lines.findIndex((l) => l.startsWith("# "));
    if (idx < 0) idx = 0;
    lines = [...lines.slice(0, idx + 1), "", ...block, ...lines.slice(idx + 1)];
    for (let i = 0; i < Math.min(20, lines.length); i++) {
      if (lines[i].startsWith("updated:")) { lines[i] = "updated: " + today; break; }
    }
  } else {
    while (lines.length && lines[lines.length - 1].trim() === "") lines.pop();
    lines = [...lines, "", "", ...block];
  }

  fs.writeFileSync(file, lines.join(eol) + eol, "utf8");
  console.log(`spliced ${mode.padEnd(8)} -> ${path.basename(file)}`);
}
