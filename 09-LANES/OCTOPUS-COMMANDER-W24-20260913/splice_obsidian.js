// Splice the season block into the 3 agent-facing Obsidian surfaces.
// Conventions (from prior syncs): per-file EOL detection, marker guard that must
// literally appear in the inserted text, additive-only, newest block above older.
const fs = require("fs");
const path = require("path");
const V = "F:/backup";
const BLOCK = fs.readFileSync(path.join(V, "09-LANES/OCTOPUS-COMMANDER-W24-20260913/obsidian_block.md"), "utf8");
const MARKER = "W24-COMMANDER-20260913-R6";
if (!BLOCK.includes(MARKER)) throw new Error("guard marker not present in the block itself");

const jobs = [
  { file: "01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md", mode: "after-h1", bump: true },
  { file: "06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md", mode: "tail" },
  { file: "ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907.md", mode: "tail" },
];

for (const j of jobs) {
  const p = path.join(V, j.file);
  let s = fs.readFileSync(p, "utf8");
  if (s.includes(MARKER)) { console.log("SKIP (marker already present):", j.file); continue; }
  const eol = s.includes("\r\n") ? "\r\n" : "\n";
  const block = BLOCK.replace(/\r?\n/g, eol);
  const pre = require("crypto").createHash("sha256").update(s).digest("hex").slice(0, 16);
  if (j.mode === "after-h1") {
    const lines = s.split(eol);
    const h1 = lines.findIndex(l => /^#\s/.test(l));
    if (h1 < 0) throw new Error("no H1 in " + j.file);
    lines.splice(h1 + 1, 0, "", block.trimEnd());
    s = lines.join(eol);
    if (j.bump) s = s.replace(/^(updated:\s*).*$/m, `$1${new Date().toISOString().slice(0, 10)}`);
  } else {
    s = s.replace(/\s*$/, "") + eol + eol + block.trimEnd() + eol;
  }
  fs.writeFileSync(p, s, "utf8");
  const post = require("crypto").createHash("sha256").update(s).digest("hex").slice(0, 16);
  console.log(`OK ${j.file}  eol=${JSON.stringify(eol)}  ${pre} -> ${post}  marker=${s.includes(MARKER)}`);
}
