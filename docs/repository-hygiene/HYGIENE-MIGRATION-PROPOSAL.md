# Hygiene migration proposal (NOT EXECUTED — awaits owner 4-option decision)
Based on audit of 49 root entries: {'MOVE': 32, 'KEEP_ROOT': 8, 'ARCHIVE': 9}
Proposed phases (each its own PR, never mixed with runtime changes):
1. git mv MEGAPROMPT-*.md, AGENT-NEXT-*.md → docs/agent-context/ (link repair + hygiene test)
2. archive *.bak-*, *.rar → archive/ (or untrack if regenerated)
3. untrack .obsidian/, .tmp-test*/ (gitignore + rm --cached)
4. corpus decision (saba_rag_seed.txt + data/) — owner-only
Forbidden until owner decision: rotation, history rewrite, deletion.
