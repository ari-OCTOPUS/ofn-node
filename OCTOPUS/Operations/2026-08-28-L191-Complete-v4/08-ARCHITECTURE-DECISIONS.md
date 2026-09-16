# ARCHITECTURE DECISIONS — v4 (13 ADR؛ همه PROPOSED مگر تصریح؛ قالب: ADR-AI-AGENT-TEMPLATE)

**ADR-01 Cloud-Brain-on-191** — مغز ابری فقط روی ۱۹۱ (egress واحد). گزینه رد: کلید روی بورد. شاهد: L6 (هیچ guard پولی در ofn-node نیست→گیت باید در 191 باشد). Rollback: حذف router سرویس. Confidence HIGH.

**ADR-02 T0-Lock-180-8081** — T0=llama-server:8081 با ExecStartPre sha-golden؛ FA=auto ثبت صادقانه، سرویس به‌خاطر auto ری‌استارت نمی‌شود (فرمان §2.1). گزینه رد: restart/تغییر flag بدون اثبات خرابی. Confidence HIGH.

**ADR-03 Census-Evidence-Levels** — LIVE فقط با لنگر L3 (systemd entrypoint)؛ dynamic-dispatch دیده‌نشده=SHADOW نه DEAD؛ absolute-DEAD ممنوع. شاهد: اجرای واقعی census (228 ماژول؛ 90 SHADOW به‌خاطر registry-dispatch). Confidence HIGH.

**ADR-04 Durable-State-Replay** — سایه‌ی ledger روی صف + rebuild غیرخودکار thinking (ضد double-charge؛ worker.py PROVEN). گزینه رد: صف صرفاً حافظه‌ای. Confidence HIGH.

**ADR-05 Idempotency-Leases** — کلید = sha256(run_id+step_id+artifact_sha+capability_class)؛ model_id ممنوع در کلید (fallback≠task جدید)؛ FileLeaseStore مسلح در موج ۶. Confidence HIGH.

**ADR-06 Vendor-Identity-vs-Dialect** — vendor_id مستقل از URL/dialect؛ DeepSeek@anthropic-endpoint→deepseek. شاهد تله: brainport.py provider=env. Confidence HIGH.

**ADR-07 Prefix-Cache-Units** — واحد prefix = request-boundary کامل؛ exact-from-token-zero؛ مرجع: lab 44/48 PARTIAL به‌عنوان regression fixture (نه success). Confidence MEDIUM (شبیه‌ساز≠provider).

**ADR-08 Budget-Reserve-Reconcile** — reservation قبل از تماس (debit)، reconciliation بعد؛ crash بین دو→BLOCKED_UNTRACKED_SPEND_RISK. گزینه رد: post-hoc accounting. Confidence HIGH.

**ADR-09 Cross-Vendor-Review** — reviewer.vendor_id≠author همیشه؛ reviewer همان artifact_sha+rubric_sha را می‌بیند؛ اختلاف→tiebreak نه T3 خودکار. Confidence HIGH.

**ADR-10 Sandbox-Egress-Separation** — T3 sandbox بی‌شبکه/بی‌secret؛ فقط داخل Evidence Bundle. MISSING امروز→مسلح پیش از Wave-7. Confidence HIGH.

**ADR-11 Witness-Receipt-Semantics** — STRUCTURAL_PASS≠EXECUTABLE_PASS؛ ACK≠receipt؛ roundtrip فقط با receipt محتوایی ۱۸۲. Confidence HIGH.

**ADR-12 GitHub-Obsidian-Publication** — push بدون force + Draft PR با body استاندارد؛ Obsidian: پوشه مأموریت، بدون overwrite نوت موجود، secret هرگز وارد vault نشود. RATIFIED-BY-OWNER (GO-C+GO-D این فرمان). Confidence HIGH.

**ADR-13 Coding-Agent-Exit-Criteria** — ۱۰ چرخه معتبر+۷روز+chaos(receipt)؛ چرخه=hash یکتا+artifact+receipt کامل؛ NO-OP نمی‌شود. Confidence HIGH.

## Contradiction Resolutions (CTR-01..04)

**CTR-01 audit/zcode visibility** — claim_a: owner GitHub دید @678975bb؛ claim_b: فهرست 138 محلی+origin ندارد. Precedence: REMOTE_FULL_SHA_OVER_STALE_LOCAL. Resolution: شاخه روی origin موجود (owner-probe) و در 138 در این لحظه fetch-prune شده — UNRESOLVED_TIL_WAVE3: `git ls-remote origin | grep zcode` از خود 138 (یک فرمان read-only). Fix: LOCAL_DOC.

**CTR-02 main 2533aa3c≠388594e0** — Resolution: canonical=origin/main(388594e0)؛ local stale، مبنا نگیر. Fix: LOCAL_DOC (registry). Authority: LOCAL_DOC.

**CTR-03 180 arch x86 vs rk35xx** — Precedence: LIVE_OVER_CONTEXT. Resolution: kernel vendor-rk35xx زنده است؛ رجیستری «x86» غلط — اصلاح رجیستری (بدون identity جدید). Authority: LOCAL_DOC. **RESOLVED**.

**CTR-04 heartbeat 3× drift** — Resolution: CONCURRENT_DRIFT ساختاری شاخه‌ی خودکار؛ حکم محتوایی DEFERRED همیشگی؛ ثبت SHA start/end در هر census. **RESOLVED (as-policy)**.
