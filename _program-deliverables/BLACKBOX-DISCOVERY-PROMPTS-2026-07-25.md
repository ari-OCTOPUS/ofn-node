---
type: deliverable
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [discovery, archaeology, blackbox]
created: 2026-07-25
updated: 2026-07-25
---

# پرامپتِ کشفِ جعبه‌سیاه‌های تودرتو — برای دو ایجنتِ موازی

> ساخته شد ۲۰۲۶-۰۷-۲۵. هر بلوکِ زیر **خودبسنده** است: کپی کن، به ایجنت بده، تمام.
> کارِ دو ایجنت **هم‌پوشانی ندارد**. خروجی را همان‌طور که برمی‌گردانند به من بده.

---

## ⚠️ پیش‌متنِ مشترک — این را در **هر دو** پرامپت بگذار

```
You are doing a READ-ONLY archaeological survey of directories on drive F: of a
Windows 11 machine. You are mapping unknown archives. You will report facts, not
opinions.

HARD RULES — violating any one invalidates your entire report:
1. READ-ONLY. Create nothing, edit nothing, move nothing, delete nothing. Run no
   git command that writes (no init/add/commit/checkout/clean). `git log`,
   `git status`, `git rev-parse` are fine.
2. NEVER open, read, list the contents of, or quote from:
   - any path containing "Partner", "PII", "Identity", "identity"
   - any .env file, any file named like *secret*, *credential*, *wallet*, *seed*,
     *.key, *.pem, id_rsa*
   - any file named OWNER-PROFILE* (the owner's own code classifies these private)
   - any image or video file
   If you encounter one, record ONLY its path and size and move on. Never quote a
   line from it.
3. NEVER print an API key, token, password, private key, seed phrase, wallet
   address, bank/BSB/account number, or any personal identifier, even if you find
   one in plain sight. If you find one, report: "credential-shaped string found at
   <path>:<line-number>" and NOTHING about its content or which service it is for.
4. Do not execute any script, notebook, or binary you find. Reading source is fine.
5. If a directory is very large, DO NOT run a full recursive size scan that takes
   minutes. Sample: list top-level entries, count files per top-level subdir, and
   take the size of the 20 largest files. Say that you sampled.

ANTI-HALLUCINATION — this matters more than completeness:
- Every factual claim must name the file path you personally opened. If you did not
  open it, say "not opened".
- Never invent a line number. If you cite a line, you read that line.
- "I could not determine X" is a valuable answer. A guess presented as a fact
  poisons the whole survey and will be caught.
- Distinguish clearly: (a) what the file SAYS about itself, (b) what you VERIFIED
  by reading code/data, (c) what you are INFERRING. Label each.

OUTPUT FORMAT — return exactly this, one block per directory you surveyed:

### <directory path>
- **what_it_is**: one sentence. If you cannot tell, say so.
- **evidence**: the 1-3 file paths you opened that justify the sentence above.
- **size_and_shape**: total size (sampled or exact — say which), file count, the
  3 largest files with sizes, dominant file types.
- **last_alive**: newest file mtime, and what that newest file is. If mtimes look
  uniform (a batch copy), say so explicitly — it means the history was destroyed.
- **version_control**: is there a .git? If yes: last commit hash/date/subject,
  branch, and whether the working tree is dirty. If no: say "NO GIT — no history".
- **unique_or_duplicate**: is this content also present elsewhere on F:? Check by
  comparing filenames + sizes against the other directories in your list, and for
  up to 5 candidate files compare a hash (certutil -hashfile <path> SHA256 or
  python hashlib). Report: byte-identical duplicate / same-name-different-content /
  appears unique.
- **irreplaceable**: is there anything here that exists in NO other copy and that a
  reasonable person would be upset to lose? Name the specific paths. This is the
  single most important field in your report.
- **already_superseded**: is there a note/readme/log inside that says this was
  retired, moved, or replaced? Quote the sentence and give the path.
- **math_or_mechanism**: does this contain any equations, algorithms, proofs,
  derivations, benchmark results, or measurement data? If yes, name them
  specifically (e.g. "a PSLQ integer-relation engine at X/engine_a.py", "a claims
  ledger with N rows at Y.json"). This field feeds a research ledger — be precise
  and do not pad it.
- **exposure**: any credential-shaped strings (path + line only, no content), any
  PII-class paths (path only), any file that looks like it should not be on a
  shared drive. Report the count and the paths, never the contents.
- **not_verified**: everything you did NOT check and would need to, to be confident.
```

---

## 🅰️ ایجنتِ اول — جعبه‌های بزرگ و باینری

```
<PASTE THE SHARED PREAMBLE ABOVE FIRST, THEN THIS>

Survey these directories, in this order of priority:

1. F:\_______Black Box          <- HIGHEST PRIORITY. 2.8 GB in only 599 files,
                                   no git, newest file 2026-07-16. 2.8GB across
                                   599 files means large binaries. Find out WHAT
                                   they are. A doc inside claims this is an "NBB
                                   Control Plane / Second Brain Super-Governor"
                                   relocated on 2026-07-11 and that it should be a
                                   standalone git repo with 171 passing tests and a
                                   history bundle at _history/nbb-cp-full-history.bundle.
                                   VERIFY OR REFUTE each of those four claims:
                                   (a) is it a git repo? (b) do 171 tests exist?
                                   (c) does the bundle exist and is it readable
                                   (`git bundle verify` is read-only)? (d) what are
                                   the 2.8GB actually made of — a venv? model
                                   weights? logs? node_modules?
2. F:\old BOX BLACK
3. F:\OLD 4D
4. F:\OLD OCTOPUS
5. F:\4d_system                 <- only ~178 KB / 22 files
6. F:\backup\4d_system          <- a DIFFERENT tree with the same name, much larger.
                                   Compare the two directly: which is newer, which
                                   is a subset of the other, do any same-named files
                                   differ in content? This name collision is itself
                                   a finding — say which one a future reader should
                                   treat as canonical, and on what evidence.

Cross-cutting question to answer at the end, once, after all six:
- Draw the relationship: which of these is an ancestor / snapshot / fork / rename of
  which? Base it on file overlap and mtimes, not on names. If two are unrelated
  despite similar names, say that loudly.
- Rank all six by "irreplaceability": which single directory, if deleted, would lose
  something that exists nowhere else? Justify with paths.
```

---

## 🅱️ ایجنتِ دوم — اسنپ‌شات‌ها، فورک‌ها و worktreeها

```
<PASTE THE SHARED PREAMBLE ABOVE FIRST, THEN THIS>

Survey these, in this order of priority:

1. F:\backup-Archive
2. F:\backup-SAFE-2026-07-19
3. F:\backup-deploy-lab
4. F:\backup-snapshot-20260723-121256
5. F:\backup_snapshots
6. F:\octopus-phase0-isolated
7. F:\octopus-phase0-A-halt
8. F:\octopus-phase0-reports
9. F:\octopus-test-runs
10. F:\octopus-untracked-safety-2026-07-22
11. F:\claude-export
12. F:\this      <- odd name; find out what it is
13. F:\zz        <- odd name; find out what it is
14. F:\tmp
15. C:\Users\Armin\.claude\worktrees\   <- list the worktrees, and for EACH say:
    is it still attached to a live git worktree (`git -C F:\backup worktree list`
    is read-only and will tell you), or is it an orphan whose branch is gone?

The live working tree is F:\backup — treat it as the reference, do NOT survey it,
and never claim a file is "missing" without checking F:\backup first.

Cross-cutting questions to answer at the end, once:
- Which of these snapshots contain commits or files that are NOT in F:\backup?
  Use `git -C <dir> log --oneline -5` where a .git exists, and
  `git -C F:\backup cat-file -e <hash>` (read-only) to test whether F:\backup knows
  that commit. A snapshot holding an unmerged commit is the most valuable thing you
  can find here — name the hash and the subject line.
- Total reclaimable size if every byte-identical duplicate were removed. Give the
  number, list the top 10 offenders by size, and say explicitly that you are only
  MEASURING — the owner's rules forbid deleting, only moving.
- Any directory whose newest file is older than 2026-07-01 AND which has no unique
  content: list them. These are the safe archive candidates.
```

---

## بعد از برگشتنِ خروجی

من دو گزارش را ادغام می‌کنم و سه چیز می‌سازم:
1. یک نقشهٔ واحد از رابطهٔ این مخزن‌ها (کدام نیای کدام است).
2. فهرستِ «بی‌جایگزین» — چیزی که فقط یک نسخه دارد و گیت ندارد. `F:\romajan` امروز
   همین وضع را داشت (۹۹۵ فایلِ پژوهشی با صفر تاریخچه) و گیت‌دار شد؛ `F:\_______Black Box`
   با ۲.۸ گیگ و صفر گیت الان بزرگ‌ترین موردِ همان الگو است.
3. ردیف‌های نامزدِ دفترِ تز از فیلدِ `math_or_mechanism` — هر معادله/بنچمارکی که
   شرطِ ابطال بپذیرد، ردیفِ دفتر می‌شود (`_ops/state/thesis/thesis-ledger.json`).
