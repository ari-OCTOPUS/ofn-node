# GITHUB-DELIVERY-REALITY — 2026-09-03 07:5x UTC

- main = 6e2bfd50 «feat(agents): repair_api — the board's self-healing pharmacy» (pushed 07:11:52Z) — **#150 مرج شد؛ داروخانهٔ خودترمیم روی main است ولی 138 هنوز 60dce961 را اجرا می‌کند (SHA_MISMATCH).**
- ۸ PR باز:
  | PR | head | وضعیت | طبقه |
  |---|---|---|---|
  | #136 clock_bind | MERGEABLE | kernel-pure P1 | آمادهٔ ریویو انسانی |
  | #135 verify-report | MERGEABLE | «report class is not verification» | آماده |
  | #134 attest-manifest | MERGEABLE | kernel-pure attest | آماده |
  | #127 mint-append | MERGEABLE | mint fence | آماده |
  | #126 unknown-seal | MERGEABLE | UNKNOWN-seal | آماده |
  | #125 split-view | MERGEABLE | دو منبع هم‌رتبه | آماده |
  | #113 capability-token | PARKED | send-auth primitive | BLOCKED_BY_POLICY (رأی مالک) |
  | #71 release/p0 | CONFLICTING | از D-31 | نیاز rebase تصمیم‌دار |
- الگوی حاکم (GOV-V6): merge فقط با review انسانی معتبر روی head تازه؛ check سبز ≠ مجوز merge؛ ۶ PRِ MERGEABLE یعنی فشار روی یک گلوگاه انسانی (الهه).
- protect-main: enforced (مالک 09-02 قفل کامل کرد؛ enforce_admins=true). CODEOWNERS `* @Elahe-z`.
- deployment_evidence: هیچ PRی deployment receipt ندارد (deploy = دستی روی 138؛ خارج از CI) — «merge ≠ deployed» در عمل.
