// Splice the 2026-09-14 G28-arc block into the three Obsidian surfaces.
// Per-file EOL detection; guard marker must literally appear in the block.
// VITAL: insert right after the H1 line (newest block on top) + bump `updated:`.
// CURRENT-TRUTH + ACTIVE-SEASON: append at tail.
const fs = require("fs");

const BLOCK = fs.readFileSync(
  "09-LANES/OCTOPUS-COMMANDER-G28-20260914/evidence/obsidian_blocks/g28-arc-20260914.md",
  "utf8").replace(/\r\n/g, "\n").replace(/\n+$/, "");
const MARKER = "OCTOPUS-COMMANDER-G28-20260914";
if (!BLOCK.includes(MARKER)) { console.error("marker missing in block"); process.exit(2); }

function eolOf(text) { return text.includes("\r\n") ? "\r\n" : "\n"; }

function spliceVital(path) {
  let t = fs.readFileSync(path, "utf8");
  const E = eolOf(t);
  if (t.includes(MARKER)) { console.log("vital: marker present, skip"); return; }
  const lines = t.split(/\r\n|\n/);
  let h1 = lines.findIndex((l) => l.startsWith("# "));
  if (h1 < 0) { console.error("vital: no H1"); process.exit(1); }
  lines.splice(h1 + 1, 0, "", ...BLOCK.split("\n"));
  t = lines.join(E);
  t = t.replace(/^updated: .*$/m, "updated: 2026-09-14");
  fs.writeFileSync(path, t, "utf8");
  console.log("vital: inserted after H1, updated: bumped");
}

function appendTail(path, label) {
  let t = fs.readFileSync(path, "utf8");
  const E = eolOf(t);
  if (t.includes(MARKER)) { console.log(label + ": marker present, skip"); return; }
  t = t.replace(/\s*$/, "") + E + E + BLOCK.split("\n").join(E) + E;
  fs.writeFileSync(path, t, "utf8");
  console.log(label + ": appended at tail");
}

spliceVital("01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md");
appendTail("06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md", "truth");
appendTail("ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907.md", "season");
console.log("done");
