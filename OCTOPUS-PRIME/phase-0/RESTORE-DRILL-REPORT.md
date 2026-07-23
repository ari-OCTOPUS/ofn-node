# RESTORE-DRILL-REPORT — OCTOPUS Phase-0 safety backup

- **source backup:** `F:\octopus-untracked-safety-2026-07-22`
- **files in manifest:** 459
- **restore target (temp, throwaway):** `C:\Users\Armin\AppData\Local\Temp\restore-drill-zep1sib3`
- **files restored + SHA-256 re-verified:** 459/459
- **hash mismatches:** 0 
- **app trees present:** ziman_os=41 files, pf_os=21 files
- **sensitive files (by name):** 2 — classified in manifest, values never recorded
- **verdict:** PASS — every backed-up file restores byte-identical

Method: copy each manifest file to a temp dir, recompute SHA-256, compare to the
manifest hash. No live path touched; the temp restore dir is disposable.
