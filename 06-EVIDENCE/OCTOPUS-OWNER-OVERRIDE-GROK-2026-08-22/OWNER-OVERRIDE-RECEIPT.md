# Owner override receipt — Grok/ari — 2026-08-22

- owner directive: Authorize Grok/ari on the real live tree F:/backup only. Continue existing Wave-A work. Do not restart implementation. Do not treat E:/germline/octopus.git or /workspace as canonical. Do not modify live runtimes cortex/miniapp_gateway/live_server/octopus_mcp. Previous writer session absent.
- old lock sha256: `3b815d4845268090e8152e1e9159d48960c4cb67c4d402f763ae03531409aa4a`
- archive: `F:\backup\_ops\state\locks\octopus-writer.lock.archived.20260822T095407+1000`
- branch/HEAD: `rescue/octopus-live-tree-20260821` / `66c713084b972be1f40742312fdf0f205778edd8`
- source digest: `b9f1d6fee47bb97385f6923059612a426c4660c42c91596c59c4be2169e84577` (2022 files, two windows equal)
- new owner: `grok-ari-single-writer` session `sess_830e364e-8cd7-4046-ade3-9862f40ec726`
- new lock sha256: `afcbdaea54a1551a28ce86ee8083615bb26783a7221511c6cfb765025055072b`
- timestamp: 2026-08-22T09:54:07.626960+10:00
- recovery: To restore previous lease bytes: copy octopus-writer.lock.archived.20260822T095407+1000 over octopus-writer.lock. To release this lease: python _ops/writer_lease.py release --agent grok-ari-single-writer --session sess_830e364e-8cd7-4046-ade3-9862f40ec726. Do not git reset --hard / git clean / force-push. Do not live-send Telegram.
