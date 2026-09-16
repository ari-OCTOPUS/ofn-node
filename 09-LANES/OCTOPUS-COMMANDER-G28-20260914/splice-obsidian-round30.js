const fs = require("fs");
const BLOCK = fs.readFileSync(
  "09-LANES/OCTOPUS-COMMANDER-G28-20260914/evidence/obsidian_blocks/round30-20260914.md",
  "utf8").replace(/\r\n/g, "\n").replace(/\n+$/, "");
const MARKER = "OCTOPUS-COMMANDER-ROUND30";
if (!BLOCK.includes(MARKER)) { console.error("marker missing"); process.exit(2); }
const eol = (t) => (t.includes("\r\n") ? "\r\n" : "\n");
let v = fs.readFileSync("01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md", "utf8");
if (!v.includes(MARKER)) {
  const lines = v.split(/\r\n|\n/);
  const h1 = lines.findIndex((l) => l.startsWith("# "));
  lines.splice(h1 + 1, 0, "", ...BLOCK.split("\n"));
  v = lines.join(eol(v)).replace(/^updated: .*$/m, "updated: 2026-09-14");
  fs.writeFileSync("01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md", v, "utf8");
  console.log("vital: inserted");
}
for (const [p, l] of [
  ["06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md", "truth"],
  ["ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907.md", "season"]]) {
  let t = fs.readFileSync(p, "utf8");
  if (!t.includes(MARKER)) {
    t = t.replace(/\s*$/, "") + eol(t) + eol(t) + BLOCK.split("\n").join(eol(t)) + eol(t);
    fs.writeFileSync(p, t, "utf8");
    console.log(l + ": appended");
  }
}
console.log("done");
