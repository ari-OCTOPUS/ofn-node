---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [scout, architecture, orchestration, governance, track-a]
status: done
created: 2026-07-03
updated: 2026-07-04
---

# SCOUT-A — الگوهای Orchestration & Governance

> خروجی ترک A از پرامپت Architecture Scout. مقایسه با baseline: پایپ‌لاین ترتیبی Fusion MVP (researcher → analyst → guardrail → panel → grounding → HITL → finalize) + kernel امنیتی IGK + گیت‌های HITL + kill-switch سراسری + لاگ hash-chained «Anchor Ledger».
> روش: ۵ ایجنت موازی، ~۴۶ جستجو، ~۴۸ منبع اولیه fetch شده. تگ‌ها: [Verified] = منبع واقعاً باز شد؛ [Unverified] = منبع اصلی باز نشد؛ [Inferred] = سنتز خودمان.

## خلاصه اجرایی — پنج یافته‌ای که مستقیم ضعف ما را می‌زنند

1. **گیت HITL باینری ما از دو طرف رد شده است.** داده Anthropic نشان می‌دهد کاربران ۹۳٪ promptها را به‌هرحال approve می‌کنند (approval fatigue)؛ طراحی‌های production فقط ۵–۱۵٪ اکشن‌ها را gate می‌کنند. راه‌حل: نردبان مجوز چندسطحی + بودجه denial + schema چهارحالته (approve / **edit** / respond / ignore).
2. **kernel داخل همان process، enforcement نیست.** اجماع ۲۰۲۵–۲۶: kernel باید جایی باشد که کد ایجنت به آن نمی‌رسد — یا زیر process (bubblewrap/seccomp، حذف network namespace) یا آن‌سوی یک hop شبکه (gateway/PDP که همه کلیدها را نگه می‌دارد). دقیقاً همان ضعف «مسیر import دور بزند» که در پرامپت حدس زده بودیم.
3. **hash chain محلیِ تنها، با کنترل دیسک بازنویسی می‌شود.** فیکس ارزان: انکر خارجی (OpenTimestamps + git remote) و امضای verdict انسانی با کلید سخت‌افزاری FIDO2؛ فیکس کامل: tlog با witness cosigning رایگان.
4. **crash وسط پایپ‌لاین نباید کل run را بسوزاند.** durable execution به‌صورت کتابخانه (DBOS روی SQLite) یا الگوی checkpoint-per-step روی همان SBC می‌نشیند — Temporal لازم نیست.
5. **kill-switch باید fail-safe باشد نه fail-operational:** نبودِ سیگنال = توقف (dead-man heartbeat + hardware watchdog + boot در حالت halted-safe)، نه منتظرِ فرمانِ توقف ماندن.

---

## کارت‌های الگو

### گروه ۱ — توپولوژی Orchestration و failure-surfacing

#### A1. Durable Interrupt + Checkpoint
- **Track:** A
- **Source:** LangGraph interrupts + persistence (SQLite checkpointer) — https://docs.langchain.com/oss/python/langgraph/interrupts · https://docs.langchain.com/oss/python/langgraph/persistence [Verified]
- **مسئله:** توقف/escalation فقط در ایستگاه‌های ثابت پایپ‌لاین ممکن است و state با مرگ process می‌پرد.
- **برتری:** failure-surfacing + autonomy-without-losing-control — `interrupt(payload)` از هر نقطه‌ای (حتی وسط node، مشروط به شرط مثل confidence پایین) اجرا را pause می‌کند، state کامل روی SQLite ذخیره می‌شود، انسان با payload تایپ‌شده (tool، args) روبه‌رو می‌شود و resume دقیقاً از همان نقطه — ساعت‌ها/روزها بعد و بعد از restart. Time-travel: replay هر checkpoint با state ویرایش‌شده (baseline ما هیچ replay ندارد).
- **Portability:** S–M — Python + SQLite، کاملاً روی Orange Pi. مکانیزم بدون خود LangGraph هم قابل بازسازی است.
- **License/Lock-in:** MIT؛ فرمت checkpoint مختص LangGraph (lock-in متوسط اگر فریمورک را بگیریم، صفر اگر فقط الگو را).
- **Verdict:** **BORROW NOW** — الگوی «pause شرطی → persist → payload تایپ‌شده → resume».

#### A2. Tripwire Guardrails + Predicate-Gated Tool Approval
- **Track:** A
- **Source:** OpenAI Agents SDK (جانشین Swarm) — https://openai.github.io/openai-agents-python/guardrails/ · /human_in_the_loop/ [Verified]
- **مسئله:** گاردریل ما یک مرحله ثابت وسط پایپ‌لاین است؛ approve هم per-stage است نه per-call.
- **برتری:** correctness/safety + failure-surfacing — guardrail ورودی/خروجی/tool با `tripwire_triggered` یک exception تایپ‌شده بالا می‌آورد و run همان‌جا halt می‌شود (در حالت blocking، قبل از خرج شدن توکن). `needs_approval` یک predicate async per tool-call است → confidence-gated routing واقعی؛ تاییدها batch و serializable (`RunState.to_json()`).
- **Portability:** S — Python خالص، provider-neutral (LiteLLM adapter)، SBC-fine.
- **License/Lock-in:** MIT؛ جاذبه ملایم به سمت OpenAI defaults.
- **Verdict:** **BORROW NOW** — semantics tripwire و گیت predicate مستقیم روی IGK قابل map است.

#### A3. Evaluator-Optimizer Loop
- **Track:** A
- **Source:** Anthropic "Building Effective Agents" (Dec 2024، URL canonical) — https://www.anthropic.com/engineering/building-effective-agents [Verified] + گسترش ۲۰۲۵: gather-context→act→verify-work، ترجیح feedback قاعده‌مند بر LLM-judge — https://claude.com/blog/building-agents-with-the-claude-agent-sdk [Verified]
- **مسئله:** drift کیفیت فقط در مرحله grounding (آخر کار) گیر می‌افتد.
- **برتری:** correctness — حلقه generator+evaluator با rubric مشخص، خطا را همان وسطِ مرحله می‌گیرد؛ eval-fail یک تریگر طبیعی برای escalation انسانی است.
- **Portability:** S — دو پرامپت و یک شمارنده حلقه.
- **License/Lock-in:** ندارد.
- **Verdict:** **BORROW NOW**.

#### A4. Orchestrator-Workers با Effort-Scaling
- **Track:** A
- **Source:** Anthropic multi-agent research system — https://www.anthropic.com/engineering/multi-agent-research-system [Verified]
- **مسئله:** برای کارهای breadth-first (تحقیق)، ترتیبی‌بودن ما هم کند است هم شکننده.
- **برتری:** correctness (+۹۰.۲٪ در eval داخلی نسبت به تک‌agent Opus 4) و latency (−۹۰٪) — به قیمت ~۱۵× توکن. قرارداد delegation صریح (objective، فرمت خروجی، مرزها) + قاعده effort-scaling (۱ ایجنت ساده / ۲–۴ مقایسه‌ای / ۱۰+ پیچیده).
- **Portability:** M–L — خود orchestration سبک است؛ هزینه توکن قاتل بودجه solo است.
- **License/Lock-in:** الگو آزاد؛ پرامپت‌ها در Anthropic Cookbook.
- **Verdict:** **PROTOTYPE** — فقط برای مراحل research؛ ترتیبی‌بودن بقیه پایپ‌لاین حفظ شود.

#### A5. MAST — واژگان استاندارد شکست multi-agent
- **Track:** A
- **Source:** arXiv:2503.13657 (Berkeley؛ ۱۶۰۰+ trace، ۱۴ حالت شکست در ۳ خوشه، κ=0.88) — https://arxiv.org/abs/2503.13657 [Verified]
- **مسئله:** escalationهای ما برچسب ساخت‌یافته ندارند؛ الگوی شکست قابل تحلیل نیست.
- **برتری:** failure-surfacing — شواهد تجربی که «task verification» یکی از سه خوشه اصلی شکست است؛ برچسب‌های MAST را روی رکوردهای Anchor Ledger و verdictهای HITL بزنیم تا آمار شکست قابل query شود.
- **Portability:** S — taxonomy + dataset باز (CC BY-NC-ND).
- **License/Lock-in:** ندارد (داده non-commercial).
- **Verdict:** **BORROW NOW** — به‌عنوان واژگان لاگ و گیت.

#### A6. Harness نظرات‌دار (deepagents)
- **Track:** A
- **Source:** https://github.com/langchain-ai/deepagents — v0.6.11 (Jun 2026)، ۲۵.۱k ستاره [Verified]
- **مسئله:** برنامه ایجنت (plan) برای انسان وسط run قابل بازرسی نیست.
- **برتری:** autonomy-without-losing-control + maintainability — الگوی Claude-Code-style: فایل todos/plan قابل خواندن و ویرایش توسط انسان وسط اجرا، subagentهای context-isolated، HITL سه‌حالته (approve/edit/reject) روی tool. با مدل‌های local (Ollama) هم کار می‌کند.
- **Portability:** S–M — MIT، فوت‌پرینت solo.
- **License/Lock-in:** MIT؛ وابستگی به اکوسیستم LangChain.
- **Verdict:** **PROTOTYPE**.

#### A7. Microsoft Agent Framework (جانشین AutoGen + Semantic Kernel)
- **Track:** A
- **Source:** https://learn.microsoft.com/en-us/agent-framework/overview/ [Verified] — AutoGen/SK در حالت maintenance [Unverified]؛ نسخه 1.0 در Apr 2026 [Unverified]؛ fork جامعه: ag2ai/ag2 [Unverified]
- **مسئله:** —
- **برتری:** maintainability (workflow گرافیِ typed + checkpoint + HITL + telemetry) — اما مثال‌ها Azure-محور.
- **Portability:** M — Python/.NET؛ مستندات cloud-leaning.
- **License/Lock-in:** MIT [Unverified]؛ جاذبه Azure متوسط.
- **Verdict:** **WATCH**.

### گروه ۲ — Durable Execution و بقای پایپ‌لاین

#### A8. DBOS Transact — durable workflow به‌صورت کتابخانه
- **Track:** A
- **Source:** https://github.com/dbos-inc/dbos-transact-py [Verified] + فیچرهای Mar 2026 (اجرای OpenAI Agents SDK روی SQLite/Postgres) — https://www.dbos.dev/blog/dbos-new-features-march-2026 [Verified]
- **مسئله:** crash وسط پایپ‌لاین ۷ مرحله‌ای = از دست رفتن کل run؛ retryها ad-hoc.
- **برتری:** crash-safety + maintainability — بدون سرور جدا: دکوراتور `@DBOS.workflow()` / `@DBOS.step()`، checkpoint هر step روی SQLite/Postgres، durable sleep چند-روزه، `DBOS.recv()` برای انتظار سیگنال انسانی با timeout durable، `list_workflows(status="ERROR")` و `fork_workflow(id, step)` برای ادامه از step دلخواه.
- **Portability:** S — in-process؛ مسیر SQLite = صفر daemon اضافه؛ SBC-friendly.
- **License/Lock-in:** MIT (control-plane ابری‌شان proprietary ولی لازم نیست)؛ lock-in پایین — یک لایه decorator.
- **Verdict:** **BORROW NOW** — ارزان‌ترین ماشین‌آلاتی که مسئله بقا را کامل حل می‌کند.

#### A9. الگوی Durable HITL Wait (signal + wait_condition + timeout-verdict)
- **Track:** A
- **Source:** Temporal AI cookbook — https://docs.temporal.io/ai-cookbook/human-in-the-loop-python [Verified] · https://temporal.io/blog/human-in-the-loop-approvals [Verified]
- **مسئله:** انتظارِ verdict ما in-process است و با مرگ process می‌میرد؛ گیت بی‌جواب، run را برای همیشه معلق می‌کند.
- **برتری:** failure-surfacing — گیتی که همیشه terminate می‌شود: approve / reject / **timeout→escalate/auto-reject**، با timer که از crash جان به در می‌برد و هزینه compute صفر هنگام انتظار. **پلتفرم Temporal برای SBC سنگین است (SKIP)؛ الگو را با `DBOS.recv(timeout=)` یا جدول pending-approvals روی SQLite پیاده کنیم.**
- **Portability:** S (الگو) / L (پلتفرم).
- **License/Lock-in:** MIT؛ الگو آزاد.
- **Verdict:** **BORROW NOW** (الگو)، SKIP (سرور Temporal).

#### A10. لاگ اجرای event-sourced روی SQLite (DIY)
- **Track:** A
- **Source:** Gunnar Morling — https://www.morling.dev/blog/building-durable-execution-engine-with-sqlite/ [Verified]
- **مسئله:** اگر DBOS هم زیادی بزرگ بود، حداقلِ ممکن چیست؟
- **برتری:** maintainability + هم‌افزایی با Anchor Ledger — یک جدول `execution_log` (flowId، step، status، attempts، params، return_value)؛ replay = memoization؛ موتور کامل <۱۰۰۰ خط. حفره شناخته‌شده: crash بین انجام step و ثبت لاگ → duplicate؛ فیکس: idempotency key. لاگ durable execution و لاگ audit می‌توانند یکی شوند.
- **Portability:** S — SBC-native.
- **License/Lock-in:** ندارد (الگوی وبلاگی).
- **Verdict:** **PROTOTYPE** — schema را کپی کنیم اگر مسیر DBOS انتخاب نشد.

#### A11. Restate / Inngest — سرورهای DE سبک
- **Track:** A
- **Source:** https://github.com/restatedev/restate (تک‌باینری Rust، v1.6.2 Feb 2026؛ دایرکتوری اعلام‌نشده `lite/` در repo) [Verified] · Inngest self-host (`inngest start`، system event `inngest/function.failed` → تریگر فانکشن escalation) — https://www.inngest.com/docs/self-hosting [Verified]
- **مسئله:** همان A8 با تضمین exactly-once قوی‌تر.
- **برتری:** exactly-once step execution + suspend/resume با یک process اضافه. هشدار Inngest: صف پیش‌فرض = Redis درون‌حافظه‌ای embedded با snapshot دوره‌ای — ضمانت crash ضعیف‌تر از تبلیغات.
- **Portability:** M — باینری Rust احتمالاً روی Orange Pi 5 می‌نشیند؛ عدد RAM روی ARM جایی منتشر نشده [Unverified].
- **License/Lock-in:** Restate = **BSL 1.1** (استفاده production داخلی مجاز؛ بعد از ۴ سال Apache-2.0)؛ Inngest سرور OSS. جایگزین OSS خالص: DBOS.
- **Verdict:** **WATCH** — دوباره چک وقتی `lite` منتشر شد.

### گروه ۳ — جداسازی Kernel امنیتی از ایجنت‌ها

#### A12. Sandbox با enforcement سطح OS (Anthropic sandbox-runtime)
- **Track:** A
- **Source:** https://github.com/anthropic-experimental/sandbox-runtime [Verified]
- **مسئله:** IGK کدِ import-شدنی در همان process است؛ تغییر config/import می‌تواند دورش بزند.
- **برتری:** correctness/safety — enforcement از پایتونِ قابل‌import به syscall کرنل منتقل می‌شود: bubblewrap + seccomp BPF، **حذف کامل network namespace ایجنت**؛ تنها مسیر شبکه، پراکسی‌های HTTP/SOCKS5 روی host با allowlist دامنه است. deny-path اجباری روی `.bashrc`، `.git/hooks`، `.mcp.json` = دفاع مستقیم در برابر config-tamper. ایجنت از داخل، هیچ سوکتی دور از kernel نمی‌تواند باز کند.
- **Portability:** S — npm install؛ باینری seccomp پیش‌ساخته arm64؛ بدون کانتینر؛ روی لینوکس bubblewrap+socat می‌خواهد. هشدار README: allowlist را باریک نگه دار (ریسک domain-fronting و exfil از دامنه‌های وسیع مثل github.com).
- **License/Lock-in:** Apache-2.0؛ جایگزین: bubblewrap/firejail خام.
- **Verdict:** **BORROW NOW** — هر ایجنت پایپ‌لاین داخل `srt` wrap شود.

#### A13. PDP Sidecar — سیاست به‌صورت process جدا (OPA/Rego یا Cedar)
- **Track:** A
- **Source:** https://tianpan.co/blog/2026-04-25-policy-as-code-agent-permissions-opa-rego [Verified]؛ AWS Cedar به‌عنوان Bedrock AgentCore Policy (Mar 2026) [Unverified — از همین منبع]
- **مسئله:** تصمیم allow/deny داخل کد ایجنت است؛ نه version-controlled است نه جداگانه تست‌پذیر.
- **برتری:** correctness/safety + maintainability — policy engine به‌صورت process/سایدکار جدا؛ gateway ابزار، هر tool-call را (principal، actor، tool، args) sub-millisecond می‌پرسد؛ «ایجنت اصلاً حق رأی ندارد». لاگ تصمیم ساخت‌یافته، فرقِ «policy رد کرد» و «مدل رد کرد» را ثبت می‌کند — چیزی که مرحله guardrail ما تولید نمی‌کند.
- **Portability:** S–M — OPA تک‌باینری Go (ده‌ها MB RAM)، روی SBC راحت.
- **License/Lock-in:** OPA Apache-2.0 (CNCF)؛ Cedar Apache-2.0 (طعم AWS)؛ جایگزین YAML-محور: Cerbos.
- **Verdict:** **BORROW NOW** — الگو + باینری OPA.

#### A14. قواعد مجوز Tool در پراکسی LLM (LiteLLM)
- **Track:** A
- **Source:** https://docs.litellm.ai/docs/proxy/guardrails/tool_permission [Verified]
- **مسئله:** ایجنت خودش کلید API دارد؛ هر enforcement دیگری دورزدنی است.
- **برتری:** cost + safety — اگر ایجنت‌ها فقط virtual-key پراکسی را داشته باشند (egress firewall فقط پراکسی را باز بگذارد)، tool_callهای غیرمجاز با allow/deny regex روی نام tool و `allowed_param_patterns` روی آرگومان‌ها (مثلاً `to[]` فقط دامنه خودمان) **قبل از رسیدن به ایجنت** حذف/بازنویسی می‌شوند؛ `default_action: deny`.
- **Portability:** S — یک بلوک YAML روی LiteLLM.
- **License/Lock-in:** MIT.
- **Verdict:** **BORROW NOW** — ارزان‌ترین upgrade منفرد.

#### A15. CaMeL — control-flow که داده untrusted نمی‌تواند عوضش کند
- **Track:** A
- **Source:** Google DeepMind + ETH — arXiv:2503.18813 · https://arxiv.org/abs/2503.18813 [Verified]؛ کد: github.com/google-research/camel-prompt-injection
- **مسئله:** prompt injection از طریق داده‌های بازیابی‌شده می‌تواند اکشن بعدی ایجنت را انتخاب کند.
- **برتری:** correctness/safety در سطح طراحی (نه detection) — LLM مورداعتماد از query کاربر یک plan به Python محدود می‌نویسد؛ داده untrusted هرگز control flow را تعیین نمی‌کند؛ capability روی مقادیر، dataflow غیرمجاز را هنگام tool-call می‌بندد. ۷۷٪ تسک‌های AgentDojo با امنیت **اثبات‌پذیر** (undefended: ۸۴٪).
- **Portability:** L — کد پژوهشی؛ بازسازی پایپ‌لاین لازم دارد.
- **License/Lock-in:** paper CC-BY؛ لایسنس repo چک نشده [Unverified].
- **Verdict:** **WATCH** — ولی قاعده «داده untrusted هرگز اکشن بعدی را انتخاب نمی‌کند» را همین حالا در IGK بگنجانیم.

#### A16. MCP Gateway (چوک‌پوینت ابزارها) — Lasso / Invariant
- **Track:** A
- **Source:** https://github.com/lasso-security/mcp-gateway (MIT، pip؛ secret-masking، Presidio PII، reputation-scan) [Verified] · https://github.com/invariantlabs-ai/invariant-gateway (Apache-2.0؛ قواعد جریان‌داده مثل «اگر فایل untrusted خواندی، send_email را ببند»؛ فقط با تغییر base URL) [Verified]
- **مسئله:** هر ایجنت مستقیم به MCP/tool وصل است؛ نقطه واحد مدیریت نیست.
- **برتری:** safety + maintainability — یک نقطه میانجی برای همه toolها با ماسک‌کردن secretها. **هشدار:** Lasso از داخل `mcp.json` خود ایجنت launch می‌شود — همان کلاس دورزدن config مگر با A12 جفت شود. Invariant: ۷۴ ستاره، بدون release؛ ریسک maintenance [Unverified: وضعیت Snyk].
- **Portability:** S (Lasso، pure Python) / M (Invariant، Docker).
- **License/Lock-in:** MIT / Apache-2.0؛ جایگزین سنگین‌تر: IBM ContextForge، Docker MCP Gateway.
- **Verdict:** **PROTOTYPE** — فقط روی enforcement سطح OS.

#### A17. LlamaFirewall / NeMo Guardrails — detector، نه kernel
- **Track:** A
- **Source:** arXiv:2505.03574 (PromptGuard 2 + AlignmentCheck + CodeShield) — https://arxiv.org/abs/2505.03574 [Verified]؛ NeMo v0.22 + NIM [Unverified]
- **مسئله:** کیفیت detectorهای guardrail ما دست‌ساز است.
- **برتری:** detectorهای بهتر از دست‌ساز — ولی از نظر معماری همان مدل ماست (in-process و importable). اردوگاه PDP صریحاً می‌گوید چک in-process اصلاً enforcement نیست — همان شک خود ما.
- **Portability:** M — مدل‌های detector ممکن است CPU-bound روی SBC سنگین باشند [Unverified].
- **License/Lock-in:** MIT (LlamaFirewall) / Apache-2.0 (NeMo).
- **Verdict:** **SKIP** به‌عنوان kernel؛ **BORROW** فقط PromptGuard 2 به‌عنوان scanner داخل gateway.

### گروه ۴ — Anchor Ledger: tamper-evidence با ماشین‌آلات کمتر

#### A18. امضای verdict انسانی با کلید سخت‌افزاری (FIDO2)
- **Track:** A
- **Source:** معماری HITL با CIBA + YubiKey (Yubico، Mar 2026) — yubico.com blog [Verified]؛ نسخه حداقلی solo: کلید SSH `sk-ed25519` + `ssh-keygen -Y sign` روی JSON verdict [Inferred]
- **مسئله:** «verdict انسانی root-of-trust برگشت‌ناپذیر است» — ولی الان هیچ‌چیز رمزنگارانه‌ای آن را غیرقابل‌جعل نمی‌کند؛ ایجنتی که به دیسک برسد می‌تواند self-approve کند.
- **برتری:** tamper-evidence + correctness — لمس فیزیکی کلید = proof-of-presence؛ verdict حتی با box روت‌شده غیرقابل جعل. هزینه: یک کلید ~$30 و چند خط کد.
- **Portability:** S.
- **License/Lock-in:** استاندارد باز FIDO2؛ صفر.
- **Verdict:** **BORROW NOW**.

#### A19. انکر خارجی سرِ زنجیره (OpenTimestamps + git + RFC 3161)
- **Track:** A
- **Source:** کلاینت OTS زنده و رایگان (v0.7.2، Dec 2024؛ calendar serverهای رایگان) — https://github.com/opentimestamps/opentimestamps-client [Verified]؛ TSA self-host: github.com/sigstore/timestamp-authority [Unverified]
- **مسئله:** hash chain محلی را صاحب دیسک می‌تواند truncate/بازنویسی کند — هیچ انکر خارجی نداریم.
- **برتری:** tamper-evidence با ~۱۰ خط کد + cron — هر ساعت: `ots stamp` روی head hash (انکر Bitcoin، بدون اکانت، رایگان) + push head به git remote خارج از box + در صورت تمایل RFC 3161. سه ریشه اعتماد مستقل. هشدار: تایید OTS چند ساعت طول می‌کشد (پنجره بازنویسی) و verify کامل، node هرس‌شده Bitcoin می‌خواهد.
- **Portability:** S.
- **License/Lock-in:** OSS؛ صفر.
- **Verdict:** **BORROW NOW** — ارزان‌ترین فیکس معتبر برای ضعف اصلی Ledger.

#### A20. Tessera — tlog واقعی روی دایرکتوری POSIX
- **Track:** A
- **Source:** https://github.com/transparency-dev/tessera [Verified]؛ Rekor v2 روی همین استک GA شد (Oct 2025) — blog.sigstore.dev [Verified]
- **مسئله:** کد Merkle/chain دست‌ساز = ریسک صحت.
- **برتری:** correctness + tamper-evidence — کتابخانه Go که لاگ tlog-tiles (c2sp.org/tlog-tiles) را مستقیم روی **دایرکتوری POSIX ساده** می‌نویسد؛ نه Trillian، نه MySQL. inclusion/consistency proof واقعی خانواده RFC 6962 با یک دهه کد سخت‌شده. ادغام کامل توسط Filippo در ~۲۵۰ خط.
- **Portability:** S — یک دایرکتوری روی SBC.
- **License/Lock-in:** Apache-2.0؛ صفر.
- **Verdict:** **PROTOTYPE** — هسته زنجیره Anchor Ledger با این عوض شود.

#### A21. Witness Cosigning — قاتل truncation
- **Track:** A
- **Source:** words.filippo.io/keyserver-tlog/ (Dec 2025) [Verified] · github.com/FiloSottile/torchwood (`litewitness`: witness روی SQLite + ssh-agent، BSD-3) [Verified] · witness-network.org [Unverified]
- **مسئله:** حتی tlog محلی هم در برابر مالک دیسک، split-view/truncation دارد.
- **برتری:** tamper-evidence با هزینه ~۰ — witnessهای عمومی رایگان (TrustFabric، Mullvad، Geomys) consistency proof را verify و checkpoint را cosign می‌کنند (c2sp.org/tlog-witness)؛ Tessera پشتیبانی native دارد (`WithWitnesses`). یک witness = اثبات append-only؛ quorum = دفاع split-view. `litewitness` روی دستگاه دوم (حتی ESP32-جایگزین: یک SBC دوم) هم شدنی.
- **Portability:** S.
- **License/Lock-in:** BSD-3/آزاد.
- **Verdict:** **BORROW NOW** (جفتِ A20؛ witness بدون checkpoint واقعی معنا ندارد).

#### A22. گزینه‌های رد شده: immudb / QLDB / CCF / journald-FSS
- **Track:** A
- **Source:** QLDB: پایان پشتیبانی AWS در 2025-07-31 [Unverified: InfoQ]؛ CCF نیازمند TEE (SGX/SEV-SNP) که روی RK3588 وجود ندارد [Unverified]؛ immudb: Apache-2.0، تایید سمت-کلاینت، build ARM [Unverified]؛ FSS: eprint.iacr.org/2023/867 — جعل entryهای seal-شده قبلی، fix در systemd 255 [Verified]؛ نقد louwrentius: epoch ۱۵ دقیقه‌ای، detection-only [Verified]
- **مسئله/درس:** مرگ بی‌سروصدای QLDB = درسِ ضد-lock-in برای ledgerهای managed. FSS حتی بعد از patch، حذف داخل پنجره را نمی‌گیرد.
- **Verdict:** immudb **WATCH**؛ QLDB/CCF **SKIP**؛ FSS **SKIP** به‌عنوان شواهد اصلی.

### گروه ۵ — HITL و Kill-Switch

#### A23. نردبان مجوز چندسطحی + Classifier-as-Approver
- **Track:** A
- **Source:** Anthropic "How we built Claude Code auto mode" (Mar 2026) — https://www.anthropic.com/engineering/claude-code-auto-mode [Verified]
- **مسئله:** گیت باینری ما یا همه‌چیز را می‌پرسد (fatigue → ۹۳٪ approve کورکورانه) یا هیچ.
- **برتری:** autonomy-without-losing-control — ۳ سطح: allowlist استاتیک امن → نوشتن داخل project خودکار → اکشن ریسکی به classifier دومرحله‌ای (فیلتر سریع + بازچک CoT). classifier عمداً reasoning-blind است (فقط پیام کاربر + tool call را می‌بیند → ایجنت نمی‌تواند متقاعدش کند). deny-and-continue؛ ۳ رد پیاپی یا ۲۰ رد کل → escalate به انسان. اعداد صادقانه: FPR ۰.۴٪، FNR ۱۷٪ → classifier gate نشت دارد؛ مکملِ non-leaky = سقف‌های سخت (بودجه/watchdog).
- **Portability:** M — الگو کامل مستند است؛ با یک LLM ارزان per risky-action روی SBC/API قابل بازسازی.
- **License/Lock-in:** محصول proprietary، طراحی منتشرشده؛ مسیر OSS: pre-tool hook خودمان.
- **Verdict:** **BORROW NOW** (نردبان + بودجه denial).

#### A24. Schema چهارحالته interrupt (approve / edit / respond / ignore)
- **Track:** A
- **Source:** https://github.com/langchain-ai/agent-inbox [Verified]
- **مسئله:** verdict ما فقط approve/reject است؛ اصلاح کوچک آرگومان‌ها یک دور کامل reject می‌خواهد.
- **برتری:** autonomy-without-losing-control — `HumanInterrupt{action_request, config{allow_accept/edit/respond/ignore}}`؛ **edit-and-approve** آرگومان را همان‌جا فیکس می‌کند. نگاشت ۱:۱ به دکمه‌های inline تلگرام.
- **Portability:** S — schema را بگیر، اپ Next.js را نه.
- **License/Lock-in:** MIT.
- **Verdict:** **BORROW NOW**.

#### A25. Approval-Token — گیت در لایه اجرا، نه لایه prompt
- **Track:** A
- **Source:** https://automatic.co/approval-gates [Verified] (vendor consultancy؛ فقط مفاهیم)
- **مسئله:** گیت ما قرارداد نرم است؛ چیزی مانع فنیِ fire شدن اکشن بدون تایید نیست.
- **برتری:** bypass-resistance — tool-call گیت‌شده **بدون token تایید معتبر نمی‌تواند اجرا شود** (HMAC-signed verdict که executor چک می‌کند)؛ risk-classifier روی پارامترهای ساخت‌یافته نه روایت مدل؛ هر گیت معلق حتماً resolve می‌شود (escalate → approver جایگزین → expiry → auto-reject/hold). ادعا: سیستم tuned فقط ۵–۱۵٪ اکشن‌ها را gate می‌کند.
- **Portability:** S برای ایده token.
- **License/Lock-in:** بدون OSS؛ فقط مفهوم را بردار.
- **Verdict:** **BORROW NOW** (token + سیاست expiry)؛ SKIP خود vendor.

#### A26. Autonomy تدریجی + تنزل خودکار scope
- **Track:** A
- **Source:** AWS Agentic AI Security Scoping Matrix (Nov 2025) — https://aws.amazon.com/blogs/security/the-agentic-ai-security-scoping-matrix-a-framework-for-securing-autonomous-ai-systems/ [Verified]؛ scoring مکمل: AURA — arXiv:2510.15739 [Verified: abstract]
- **مسئله:** kill-switch ما باینری و سراسری است — یا همه‌چیز یا هیچ.
- **برتری:** autonomy-without-losing-control — scopeهای ۱–۴ (بدون/تجویزشده/تحت‌نظارت/کامل) × ۶ بعد کنترل، **per-tool**؛ حرکت کلیدی: هنگام anomaly به‌جای kill باینری، scope خودکار تنزل می‌کند (HITL دوباره سفت می‌شود). Scope 4 لازم می‌کند override طوری باشد که ایجنت نتواند خاموشش کند.
- **Portability:** S — فریمورک vendor-neutral.
- **License/Lock-in:** آزاد / CC-BY (AURA).
- **Verdict:** **BORROW NOW**.

#### A27. Breaker بودجه fail-closed + heartbeat مرد-مرده
- **Track:** A
- **Source:** LiteLLM budgets (`max_budget`، پنجره‌های پشته‌ای، `fail_closed_budget_enforcement: true` → 503 وقتی spend قابل‌تایید نیست) — https://docs.litellm.ai/docs/proxy/users [Verified]؛ AgentWallet (heartbeat؛ شواهد ضعیف — پست HN تک‌امتیازی) [Verified: لینک، ضعیف: اعتبار]
- **مسئله:** kill-switch به سلامت خود supervisor وابسته است؛ خرج runaway هم breaker خودکار ندارد.
- **برتری:** cost + safety — تصمیم kill به یک process/user جدا (پراکسی) منتقل می‌شود؛ **غیابِ سیگنال = توقف** (fail-safe) به‌جای انتظار برای فرمان توقف.
- **Portability:** S–M — LiteLLM روی VPS کوچک (Postgres می‌خواهد).
- **License/Lock-in:** MIT.
- **Verdict:** **BORROW NOW** (LiteLLM به‌عنوان spend-breaker)؛ WATCH (AgentWallet).

#### A28. زنجیره Watchdog سخت‌افزاری + boot در حالت halted-safe
- **Track:** A
- **Source:** Dries Buytaert — https://dri.es/keeping-your-raspberry-pi-online-with-watchdogs [Verified]؛ زنجیره systemd `WatchdogSec=` per-service [Inferred — با docs freedesktop verify شود]
- **مسئله:** اگر خود supervisor یا کرنل بمیرد، kill-switch ما هم مرده است.
- **برتری:** safety — enforcement زیر OS: WDT سخت‌افزاری SoC (`RuntimeWatchdogSec=10s`)؛ freeze → reboot اجباری. نکته containment: unitهای ایجنت **auto-start نباشند** — reboot به حالت halted-safe می‌نشیند و فقط supervisor + بات تلگرام بالا می‌آیند؛ ادامه کار نیازمند فرمان انسان.
- **Portability:** S — روی SBCهای کلاس Pi/Orange Pi مجانی و in-kernel (RK3588 هم WDT دارد [Inferred]).
- **License/Lock-in:** ندارد.
- **Verdict:** **BORROW NOW** — جواب مستقیم «kill-switch وقتی supervisor خودش مریض است».

---

## کاندیدهای FOLLOW (خوراک سنتز نهایی)

- **Filippo Valsorda** — words.filippo.io + torchwood + specهای C2SP؛ مرجع عملی tlog حداقلی.
- **blog.transparency.dev** — Tessera/TesseraCT/شبکه witness.
- **Anthropic engineering blog** — تنها منبعی که FNR/FPR واقعی گیت‌ها را منتشر می‌کند (auto mode، multi-agent).
- **DBOS blog (Qian Li / Peter Kraft)** — سری «Postgres is all you need».
- **langchain-ai/deepagents + agent-inbox** — سریع‌ترین تکامل primitives HITL.
- **گروه MAST برکلی (Mert Cemri)** — تنها dataset تجربی شکست MAS.
- **Restate engineering blog** — منتظر `lite/`.
- **OWASP Agentic Security + CoSAI** — محل فرود استانداردهای tiering.

## GAPS — فرضیه‌های قابل‌جستجو برای run بعدی

1. رسپی کامل «bubblewrap + OPA + MCP gateway روی یک ARM SBC برای solo operator» جایی منتشر نشده — جستجو: `srt bubblewrap OPA mcp gateway raspberry pi`.
2. latency مدل‌های PromptGuard-کلاس روی CPU ARM — هیچ benchmark پیدا نشد.
3. RAM/CPU واقعی Restate/Inngest/Temporal-dev روی ARM64 — جستجو: `restate idle memory ARM64 benchmark`.
4. «two-person rule برای solo operator»: فرضیه — قفل تاخیری (verdict بعد از N ساعت cooling اجرا می‌شود مگر cancel شود) به‌عنوان approver دوم؛ writeup مختص ایجنت پیدا نشد.
5. KILLBENCH (arXiv:2511.13725) — benchmark امکان‌سنجی kill-switch خارجی؛ PDF خوانده نشد [Unverified] — نسخه HTML را fetch کن.
6. confidence کالیبره برای gating escalation در production — snippetها می‌گویند confidence خام LLM بدکالیبره است؛ جستجو: conformal prediction + agent routing.
7. سیاست پذیرش Witness Network برای لاگ‌های خصوصی کوچک — لیست prod vs testing نامشخص.
8. heartbeat مخصوص stepهای LLM (liveness از روی token stream) — ظاهراً ناکاویده.
9. ESAA (append-only لاگ intentions ایجنت) — arXiv:2602.23193 [Unverified]؛ شواهد adoption صفر.
10. بازچک: تاریخ launch دقیق OpenAI Agents SDK، وضعیت maintenance AutoGen/SK، لایسنس MS Agent Framework، وضعیت Invariant/Snyk.

## CONTRADICTIONS — اختلاف منابع معتبر

- **Anthropic با خودش:** Building Effective Agents می‌گوید «ساده‌ترین را بساز، workflow برای کار پیش‌بینی‌پذیر»؛ پست multi-agent ادعای +۹۰.۲٪ دارد. آشتی فقط با نوع تسک (breadth-first موازی) و هزینه ۱۵×. MAST هم می‌گوید سود MAS «اغلب حداقلی» است.
- **«گیت غیرقابل‌دورزدن» vendorها vs FNR ۱۷٪ Anthropic:** گیت‌های classifier نشت دارند؛ لایه non-leaky فقط سقف‌های سخت‌اند (budget/watchdog/allowlist). هر دو لایه لازم.
- **۹۳٪ approval (Anthropic) vs «فقط ۵–۱۵٪ را gate کن» (Automatic):** از دو جهت مخالف، هر دو طراحی gate-everything باینری ما را محکوم می‌کنند.
- **معنای "deterministic replay":** Temporal history را replay می‌کند؛ LangGraph nodeها را **دوباره اجرا** می‌کند (interruptها دوباره تریگر می‌شوند) — هنگام طراحی resume نباید این دو را قاطی کرد.
- **srt:** README ادعای ایزولاسیون قوی؛ دو writeup مستقل ۲۰۲۵–۲۶ [Unverified] ادعای bypass allowlist/exfiltration؛ خود README هم domain-fronting را می‌پذیرد → allowlist باریک شرط اعتبار است.
- **FSS journald:** معرفی‌شده به‌عنوان جایگزین remote logging؛ KIT (eprint 2023/867) شکست رمزنگارانه (fix در systemd 255) و louwrentius ماهیت detection-only را نشان می‌دهند.
- **CaMeL در مطبوعات vs مقاله:** press «۶۷٪ دفاع» را نقل می‌کند؛ متریک اصلی مقاله «۷۷٪ تکمیل تسک با امنیت اثبات‌پذیر» است — بدون خواندن بخش eval نقل‌قول نکن.

---
*مرحله بعد طبق پرامپت: Track B (CPU/ARM edge-mining) پس از تایید مالک.*
