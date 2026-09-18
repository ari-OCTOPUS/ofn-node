# Evidence — owner_digest output on live board138 DB (2026-09-05 02:35 UTC)

DB: `/home/ari/.local/share/ofn/painting.sqlite` (55 rows, all stage=researched)
Command: `python3 owner_digest.py --db /home/ari/.local/share/ofn/painting.sqlite --summary --include-no-phone --top 30`

Counts: Total: 55 | Direct+phone: 26 | Direct (no phone): 0 | Panel/Sub: 9 | Other: 20

## Callable (APPROACH: Direct + phone), relevance DESC — "Call Today"

 1. [9/10] Whelan Property Group  —  02 9219 4111
 2. [9/10] Excel Building Management  —  (02) 9518 8577 | after-hours 1300 985 000
 3. [9/10] National Facilities Management  —  1300 820 330 | mail@nationalfm.com.au
 4. [9/10] Montano Strata  —  (02) 9053 7637
 5. [9/10] IB Property  —  (02) 9221 3333 | info@ibproperty.com.au
 6. [9/10] Strata Republic  —  1300 884 104
 7. [9/10] CF Strata Management  —  (02) 9313 6255
 8. [8/10] Civium Strata NSW  —  (02) 9715 3999 | enquiries@civium.com.au
 9. [8/10] Strata United  —  1300 445 900 | info@strataunited.com.au
10. [8/10] Strata Excellence  —  1300 16 16 37
11. [8/10] Progressive Strata Services  —  (02) 9389 9599
12. [8/10] Sydney Strata Specialists  —  02 8005 3850 | info@sydstrata.com.au
13. [8/10] Michael Roberts Strata Management  —  (02) 8567 5900
14. [8/10] Nation  —  02 9090 4606
15. [8/10] Absolute Strata  —  02 9553 0244 | 1300 012 800 | info@absolutestrata.com.au
16. [8/10] Strata Real Estate Services  —  1300 997 905
17. [8/10] Strata Sense  —  1300 859 044
18. [8/10] Elevated Strata Communities  —  1300 951 203 | hello@elevatedsm.com.au
19. [8/10] Guardian Strata  —  02 8030 8950 | admin@guardianstrata.com.au
20. [7/10] Neighbourly Strata (VJ Ray)  —  02 8880 1040
21. [7/10] Ace Body Corporate Management  —  02 9818 6842 (official) | 0400 549 724 (directory, unverified)
22. [7/10] Foreshew Strata Agency  —  02 8379 6631 (official) | 1300 774 784 (not on site)
23. [7/10] Proactive Strata Services  —  02 9807 9255
24. [7/10] Platinum Strata Management  —  (02) 9922 4117
25. [7/10] News Corp Australia  —  (02) 9288 3000
26. [6/10] Opera Australia  —  (02) 9699 1099 (The Opera Centre)

## Panel/Tender + Subcontractor Pathway (9) — not cold-call; registration/tender path

- [9/10] Downer Group | Subcontractor Pathway | 1800 369 637 (official) | +61 2 9468 9700
- [8/10] Dexus | Panel/Tender | +61 2 9017 1100
- [8/10] Delux Building Management Group | Subcontractor Pathway | 1300 606 666
- [8/10] RD Facilities Management | Subcontractor Pathway | 1800 507 552
- [8/10] City of Parramatta | Panel/Tender | 1300 617 058
- [7/10] Woolworths Group | Panel/Tender | +61 2 8885 0000
- [7/10] Sydney Water | Panel/Tender | Suppliers: 1300 690 399 (Business Connect)
- [7/10] City of Canterbury Bankstown | Panel/Tender | 02 9707 9000
- [7/10] NSW DPHI | Panel/Tender | 1300 305 695 (Planning Portal enquiries)

## Other (20) — whale groups ("Direct or Vendor Panel") + intel/watch/referral

- [10/10] Strata Choice | Direct or Vendor Panel | 1300 322 213 | (02) 9249 9800
- [9/10] Bright and Duggan Group | Direct or Vendor Panel | 1300 092 863 (after-hours)
- [9/10] Smarter Communities | Direct or Vendor Panel | 1800 519 642 (group sales) | (02) 9266 2600
- [9/10] BCS Strata Sydney (PICA Group) | Direct or Vendor Panel | 1300 889 227
- [9/10] Savills Australia | Direct or Vendor Panel | +61 2 8215 8888
- [9/10] CBRE Advisory Charter Hall | Direct or Vendor Panel | +61 2 9333 3333 (confirm on call)
- [9/10] Strata Title Management (STM) | Direct or Vendor Panel | (02) 9266 2600 | 1800 519 642
- [9/10] Core Talent (Premium strata ~90 lots — undisclosed) | Intel-Only | Olivia 0406 560 343
- [8/10] Cushman and Wakefield Sydney | Direct or Vendor Panel | +61 2 8243 9999
- [8/10] SGCH | Direct or Vendor Panel | 1800 573 370
- [8/10] Mission Australia | Direct or Vendor Panel | 1800 951 123
- [8/10] ESR Group | Direct or Vendor Panel | Main: +61 2 9186 4700
- [6/10] Sydney Olympic Park Authority | Watch | (02) 9714 7888
- [5/10] Bond Services | Partnership/Referral | (02) 8117 8184
- [5/10] Complete Staff Solutions | Intel-Only | 1800 308 308
- [5/10] Capstone Recruitment | Intel-Only | Phil O Keeffe 0404 041 904
- [4/10] Hays Property | Intel-Only | 02 8226 9600
- [4/10] TalentWeb Property | Intel-Only | stored mobile unverified
- [3/10] Siemens Australia — Smart Infrastructure | Intel-Only | 1300 782 379
- [2/10] BPS Strata and Insurance Restoration | Intel-Only | 1300 724 814

## Digest limitation found (PR #201 feedback, not fixed in this lane)

`owner_digest.py` matches `approach == "Direct"` exactly, so the highest-value group
accounts tagged "Direct or Vendor Panel" (Strata Choice 10/10, Smarter Communities,
BCS/PICA, Bright & Duggan, STM, Savills, CBRE-Charter Hall, C&W, SGCH, Mission, ESR)
fall into "Other" and never appear in "Call Today". Suggested one-line fix (owner/PR review
decision): `r["approach"].startswith("Direct")` in the three bucket comprehensions.

## Programmatic kernel scores after overlay (b2b_account_score, score_inputs supplied)

22 HIGH_FIT (≥0.78) / 25 QUALIFY (0.52–0.78) / 8 BACKLOG (<0.52). Uniform 0.375/BACKLOG before overlay.
Full per-row receipts: transcript of `update_verified_leads.py` run (saved in lane session log); rerunnable:
`PYTHONPATH=/home/ari/ofn python3 ~/lanes/painting-b2b-20260905/update_verified_leads.py` (idempotent).
