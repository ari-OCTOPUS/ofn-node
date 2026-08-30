# Rollback (isolated worktree only)
git -C "F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\pc-worker\worktree" checkout 441af7632dd6e248ccdb4b95f08aebf4f0cca2d6
# This latch commit:
git -C "F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\pc-worker\worktree" checkout 8fe57d68dc595c19df953d09744166ba8b15f97a
Does not touch 180 production or 30f60773.
