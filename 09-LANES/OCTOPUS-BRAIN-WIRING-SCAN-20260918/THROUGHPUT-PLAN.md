# THROUGHPUT-PLAN — ۲۰ آیتم برای بالا بردن بازده (رتبه‌بندی‌شده)

| # | کار | برد | اثر تخمینی | هزینه | Class | رأی مالک؟ |
|---|---|---|---|---|---|---|
| TP-01 | write a reader for painting_call_log + v_account_last_call so the CRM stage updates | 138 | removes W-001/002/018 dangling edges; first CRM data visible | low | A | no |
| TP-02 | install the staged systemd units on 114 (evaluator) and 160 (ingestion) | 114,160 | +2 always-on lanes; kills the reboot-orphan risk (F-003) | low | B(witness) | no |
| TP-03 | move heavy batch jobs (enrichment/digest/NPU probes) from 138 to 100 | 100,138 | frees the revenue node; 100 sits at load 0.02 | med | A | no |
| TP-04 | wire think_pool provider-health into the broker route (orphan BR-17/W-038) | 138 | stops routing to exhausted providers (the fugu 429 defect) | low | A | no |
| TP-05 | measure NPU usable capacity on 138+193 and publish a consumer | 138,193 | unknown→known; potential free local inference (F-056) | med | A | no |
| TP-06 | give the local tier (BR-06) a real consumer for the cheap classification tasks | 138 | cut paid calls for trivial work | low | A | no |
| TP-07 | revive cognition_factory (BR-15) or archive it — 877 idle lines | 138 | either +1 brain or remove dead weight (verified decision) | low | A | no |
| TP-08 | same decision for durability (09-15) and of-draft-queue (09-16) | 138 | state tier stops growing tombstones | low | A | no |
| TP-09 | trace the octopus-mesh services' I/O and register their receipts | 138 | 6 running daemons currently WIRED-DARK | med | A | no |
| TP-10 | persist packet send_status on send (fixes 0-vs-39) | 138 | funnel becomes measurable end-to-end | low | A | no |
| TP-11 | give fleet-memory / fleet-nodes (frozen 09-16) a consumer or retire them | 138 | memory layer honesty | low | A | no |
| TP-12 | autofill + publish DASHBOARD on the 6h cycle (W-022 dark) | 138 | orientation data stops being 3 days stale | low | A | no |
| TP-13 | add JetStream consumers for the job bus types with none (F-042) | 138 | job durability stops being decorative | med | B | no |
| TP-14 | create state/legs/lead-inbox/ so glass error writes land (W-029) | 138 | error path becomes observable | trivial | A | no |
| TP-15 | route research/hypothesis jobs to 193 and coding sandbox runs to 100 | 193,100 | uses the two most idle boards deliberately | low | A | no |
| TP-16 | run the restore drill (F-006) while spare capacity exists on 100 | 100 | biggest hidden risk retired | med | B(witness) | no |
| TP-17 | second channel for Critical owner cards (Telegram single-point) | 138 | decisions survive a TG outage | low | A | yes |
| TP-18 | standing send-authorization policy card | 138 | removes the release-gate stall measured today | low | A | yes |
| TP-19 | witness/audit load review on 182 (27 services, load 1.68) | 182 | witness must not become the bottleneck | low | A | no |
| TP-20 | publish a weekly brain-cost table from the ledger (BR-30) | 138 | $/day per brain visible; waste ends | trivial | A | no |

**ترتیب پیشنهادی اجرا:** TP-14 → TP-10 → TP-01 → TP-04 → TP-02 → TP-03 → TP-15 (همه Class A سبک، بدون رأی) سپس TP-05/TP-09/TP-12 و در آخر دارندگان رأی (TP-17/TP-18).
