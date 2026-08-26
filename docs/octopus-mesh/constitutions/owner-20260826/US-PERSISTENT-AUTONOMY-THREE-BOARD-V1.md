US — استقرار دائمی خودمختاری سه‌بردی
نسخه: 1.0
تاریخ مجوز مالک: 2026-08-26
مالک: Armin / آری
هدف: خودکارسازی مداوم حلقه‌های داخلی با کنترل نهایی مالک در تلگرام
برد مغز: 180
برد فرمانده و reconciler: 138
برد شاهد مستقل: 182

1. مجوز صریح مالک
من، Armin/آری، مالک سامانهٔ OCTOPUS، اجرای موارد دقیق زیر را تا زمان revoke یا OWNER_PAUSE صریحاً مجاز می‌کنم.

1.1 مجوزهای دائمی داخلی
سه برد مجازند:

داخل مسیرهای canonical مربوط به octopus-mesh فایل کد، config، schema، state، test، audit و document ایجاد یا به‌روزرسانی کنند.

پیش از هر mutation، backup/hash بسازند و تغییر را atomic، idempotent و rollbackable انجام دهند.

از SSH mesh موجود فقط بین 138، 180 و 182 و فقط برای transport، deployment، health و verification استفاده کنند.

سرویس‌ها و timerهای دقیقاً نام‌برده در این سند را ایجاد، daemon-reload، enable، start، stop، restart و rollback کنند.

تست unit، integration، negative، replay، crash-recovery، duplicate-delivery، budget و pause اجرا کنند.

branch جدید بسازند، commit کنند و branch را push کنند؛ force-push، merge و حذف branch بدون approval ممنوع است.

taskهای GREEN داخلی را خودکار تولید، claim، اجرا، verify، settle و audit کنند.

heartbeat، health، queue، budget و disk را مداوم پایش کنند.

هنگام failure به حالت امن‌تر تنزل دهند.

به Telegram فقط حساب/چت allowlisted مالک، پیام status، incident و approval request بفرستند.

تصمیم‌های معتبر مالک را از Telegram دریافت و فقط در scope همان درخواست اجرا کنند.

این مجوز اجازهٔ افزایش خودکار اختیار، تغییر مالک، دورزدن gate، ایجاد persistence مخفی یا مقاومت در برابر shutdown نیست.

1.2 نیازمند تأیید تک‌عملی تلگرام
هر مورد زیر فقط با approval معتبر، منقضی‌نشده و bindشده به target و payload دقیق مجاز است:

ارسال پیام یا محتوا به مشتری، lead، شریک یا عموم.

quote نهایی، booking، تغییر customer record یا تعهد زمانی.

merge به branch canonical یا production deploy دارای اثر بیرونی.

نصب package یا مدل جدید، paid API یا subscription.

هر هزینه، purchase، refund یا انتقال پول.

تغییر firewall، SSH، credential، secret، identity یا access policy.

حذف یا archive دادهٔ مهم.

تغییر creator share، budget cap یا capability tier.

توقف یا حذف Cellframe و داده‌های آن.

1.3 همیشه ممنوع بدون مأموریت حقوقی/امنیتی جدا
cold outreach یا bulk messaging بدون consent.

معاملهٔ خودکار مالی یا رمزارز.

self-replication خارج registry.

force-push، پاک‌کردن audit/evidence/ledger یا جعل receipt.

خواندن، چاپ یا انتقال private key، token، password و PII.

دورزدن MFA، CAPTCHA، Terms، rate limit یا paywall.

تغییر owner policy توسط agent.

فرض‌کردن سکوت مالک به‌عنوان approval.

1.4 دامنهٔ Telegram
مالک فقط پس از تنظیم دستی این متغیرها اجازهٔ ارتباط می‌دهد:

OCTOPUS_TELEGRAM_BOT_TOKEN در فایل secret محلی با mode 600.

OCTOPUS_OWNER_TELEGRAM_USER_ID.

OCTOPUS_OWNER_TELEGRAM_CHAT_ID.

مقدارها نباید در Git، prompt، log، audit payload یا پیام بین بردها ثبت شوند. فقط نام متغیرها قابل ثبت است.

2. اصل معماری
180 فکر می‌کند، فرضیه می‌سازد و proposal می‌دهد.

138 route، policy-check، approval، execution و reconciliation را انجام می‌دهد.

182 مستقل verify و falsify می‌کند.

مدل مستقیماً shell، SSH، filesystem نامحدود، Telegram یا executor ندارد.

model output فقط JSON داده است.

tool execution فقط در 138 و پشت allowlist و policy gate انجام می‌شود.

taskهای داخلی پرتکرار خودکارند؛ ریسک و اثر بیرونی خودکار نیست.

3. state machine مشترک
هر run دقیقاً یکی از stateهای زیر را دارد:

text
NEW
VALIDATED
PLANNED
DELEGATED
RUNNING_180
WAITING_WITNESS
RUNNING_182
WAITING_RECONCILE
WAITING_OWNER
APPROVED
DENIED
EXECUTING
WAITING_RECEIPT
VERIFYING_EFFECT
COMPLETED
UNRESOLVED
DEGRADED
SAFE_HALT
EXPIRED
قواعد:

انتقال state فقط با event schema-valid و append-only audit.

هر transition دارای run_id, event_id, causation_id, actor, timestamp, idempotency_key و reason است.

transition تکراری effect تکراری ایجاد نمی‌کند.

terminal state دوباره اجرا نمی‌شود.

هر run حداکثر 3 hop، 2 retry و 1 reconcile دارد.

اختلاف سه‌باره یا unresolved پراثر به مالک escalate می‌شود.

4. لایه‌ها و سرویس‌ها
4.1 روی 138
فایل‌ها:

text
~/octopus-mesh/runtime/
~/octopus-mesh/bin/octopus_supervisor.py
~/octopus-mesh/bin/octopus_router.py
~/octopus-mesh/bin/octopus_scheduler.py
~/octopus-mesh/bin/octopus_cycle_settler.py
~/octopus-mesh/bin/octopus_control_router.py
~/octopus-mesh/bin/octopus_telegram_bridge.py
~/octopus-mesh/bin/octopus_executor.py
~/octopus-mesh/bin/octopus_budget.py
~/octopus-mesh/bin/octopus_owner_control.py
~/octopus-mesh/config/autonomy_policy.json
~/octopus-mesh/config/action_tiers.json
~/octopus-mesh/config/model_routes.json
~/octopus-mesh/config/token_budget.json
~/octopus-mesh/config/telegram_policy.json
~/octopus-mesh/state/runs/
~/octopus-mesh/state/approvals/
~/octopus-mesh/state/incidents/
~/octopus-mesh/state/OWNER_PAUSE
سرویس‌ها:

octopus-supervisor.service

octopus-router.service

octopus-scheduler.timer

octopus-cycle-settler.service

octopus-control-router.service

octopus-telegram-bridge.service

octopus-budget-monitor.timer

octopus-heartbeat.timer

4.2 روی 180
فایل‌ها:

text
/root/octopus-mesh/bin/octopus_cognitive_worker.py
/root/octopus-mesh/bin/octopus_model_adapter.py
/root/octopus-mesh/bin/octopus_self_model.py
/root/octopus-mesh/bin/octopus_heartbeat.py
/root/octopus-mesh/config/cognitive_policy.json
/root/octopus-mesh/config/model_routes.json
/root/octopus-mesh/state/cognition/
/root/octopus-mesh/state/OWNER_PAUSE
سرویس‌ها:

octopus-cognitive-worker.service

octopus-heartbeat.timer

octopus-resource-monitor.timer

4.3 روی 182
فایل‌ها:

text
/root/octopus-mesh/bin/octopus_witness_worker.py
/root/octopus-mesh/bin/octopus_verifier.py
/root/octopus-mesh/bin/octopus_heartbeat.py
/root/octopus-mesh/config/witness_policy.json
/root/octopus-mesh/state/witness/
/root/octopus-mesh/state/OWNER_PAUSE
سرویس‌ها:

octopus-witness-worker.service

octopus-heartbeat.timer

octopus-resource-monitor.timer

5. حلقه‌های دائمی
5.1 Queue loop
هر 5 تا 15 ثانیه:

verify local identity و policy hash.

route-control برای ACK/NACK.

peek فقط message type مجاز.

claim اتمیک.

validate schema/checksum/TTL/role/may_authorize.

dispatch به handler.

complete یا fail با reason.

ثبت latency و queue depth.

اگر task نیست، model فراخوانی نشود.

5.2 Cognitive loop روی 180
text
VALIDATED TASK
→ observe available evidence
→ separate observations/inferences
→ generate alternatives
→ set prior confidence
→ specify falsifier
→ produce structured proposal/result
→ send to 138
→ await outcome
→ update lesson only after outcome
180 هرگز خودش proposal پراثر را اجرا نمی‌کند.

5.3 Witness loop روی 182
text
VERIFICATION_TASK
→ reproduce independently
→ collect scoped evidence
→ attempt falsification
→ compare alternatives
→ confirmed/disputed/unresolved
→ witness_response to 138
182 از تحلیل 180 به‌عنوان حقیقت اولیه استفاده نمی‌کند.

5.4 Reconciliation loop روی 138
text
response_180 + witness_182
→ validate provenance
→ compare claims
→ record prediction/outcome
→ calibration score
→ resolve or mark disputed
→ complete terminal messages
→ create lesson or owner escalation
5.5 Learning loop
lesson بدون outcome تثبیت نمی‌شود.

هر lesson دارای source، counterexample، regression test و expiry است.

self-model update ابتدا proposal است.

تغییر self-model canonical نیازمند policy و در موارد structural تأیید مالک است.

5.6 Approval loop
text
YELLOW/RED proposal
→ 138 resolves exact target/content/cost
→ creates immutable approval request
→ Telegram owner
→ approve/deny/conditions
→ revalidate expiry and payload hash
→ execute once or deny
→ receipt
→ optional witness
5.7 Business loop
text
inbound event
→ qualification 180
→ verification if needed
→ draft offer
→ owner approval if external
→ executor 138
→ receipt
→ cash/payment reconciliation
→ cost/margin
→ learning
بدون event واقعی، lead/revenue ساخته نشود.

5.8 Health and recovery loop
heartbeat هر 60 ثانیه.

queue check هر 10 ثانیه.

scheduler هر 15 دقیقه فقط با event تازه.

business review هر 60 دقیقه.

daily owner digest.

crash → bounded restart.

repeated crash → DEGRADED_READ_ONLY و سپس SAFE_HALT.

138 unavailable → 180/182 در COMMANDER_UNAVAILABLE_SAFE_HOLD.

6. Telegram implementation
روی 138 از long polling استفاده شود تا listener عمومی تازه باز نشود.

الزامات:

فقط HTTPS outbound به Telegram API.

getUpdates با timeout و offset پایدار.

offset پس از durable processing ذخیره شود.

فقط from.id و chat.id allowlisted مالک پذیرفته شود.

callback data فقط opaque request ID؛ payload حساس داخل callback نباشد.

approval به request_id + payload_hash + expiry bind شود.

callback replay رد شود.

هر approval فقط یک action.

status message rate-limited و deduplicated.

failure تلگرام → PENDING_OWNER.

webhook فعال موجود پیش از long polling باید شناسایی شود؛ تغییر آن فقط در scope همین bridge و با ثبت audit.

فرمان‌های مالک:

text
/status
/pause
/resume
/approvals
/approve <request_id>
/deny <request_id>
/conditions <request_id> <condition-id>
/budget
/business
/emergency_stop
/resume و /approve بدون تطبیق owner ID و request binding معتبر نیستند.

7. systemd و persistence
قبل از نصب unit:

systemd-analyze verify.

اجرای foreground و dry-run.

تست malformed state و missing dependency.

backup unit قبلی.

حداقل تنظیم:

text
[Unit]
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=3

[Service]
Type=simple
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=<EXACT_OCTOPUS_PATHS>
UMask=0077
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
هر directive ابتدا از نظر سازگاری آزموده شود. اگر hardening باعث شکست شد، کمینهٔ لازم مستند شود؛ سرویس بی‌صدا با permission گسترده اجرا نشود.

Restart loop با StartLimit متوقف شود و incident بسازد. cron مخفی یا persistence جایگزین ممنوع است.

8. Owner pause و emergency stop
فایل canonical:

text
<octopus-root>/state/OWNER_PAUSE
هنگام وجود فایل:

model call متوقف.

task creation متوقف.

external execution متوقف.

فقط heartbeat، audit، status و دریافت owner command ادامه.

agent حق حذف فایل را ندارد.

resume فقط با owner identity معتبر و audit انجام می‌شود.

Emergency stop علاوه بر pause:

تمام workerها graceful stop.

taskهای claim‌شده به state امن منتقل شوند.

هیچ queue/evidence حذف نشود.

Telegram فقط receipt توقف را بفرستد.

9. Budget و جلوگیری از حلقه
سطوح:

NORMAL

CONSERVE

SAFE_HOLD

اولویت مصرف:

health و audit.

inbound qualified work.

quote/delivery support.

verification.

experiment.

محدودیت:

per-task token cap.

per-run cap.

daily/weekly cap.

model timeout.

max output size.

duplicate semantic key.

no event = no model call.

بودجه تمام شد → SAFE_HOLD، نه تلاش برای خرید token یا دورزدن مالک.

10. برنامهٔ استقرار
Gate 0 — بستن handoff فعلی
receipt مستقل V1 از 180.

verdict task 16dc715f... از 182.

مصرف terminal responseها.

اگر disputed، task اصلاحی؛ اگر confirmed، ادامه.

Gate 1 — ساخت runtime بدون start
ساخت code/config/schema/test روی branch.

تمام daemonها --once, --dry-run, --foreground داشته باشند.

هیچ service enable نشود.

Gate 2 — simulation
clock injection برای 30 دقیقهٔ شبیه‌سازی‌شده.

malformed model output.

duplicate delivery.

expired lease.

138 unavailable.

owner pause.

budget exhaustion.

Telegram fake adapter.

Gate 3 — foreground soak
هر worker حداقل 10 cycle.

بدون external action.

restart و crash recovery.

CPU/RAM/disk bounds.

Gate 4 — systemd canary
ابتدا heartbeat.

سپس control-router.

سپس workerها.

سپس scheduler و settler.

هر سرویس 30 دقیقه canary و rollback test.

Gate 5 — persistent internal autonomy
سرویس‌ها enable شوند.

24 ساعت فقط GREEN.

daily report.

external actions صفر.

Gate 6 — Telegram shadow
fake approvalها و واقعی‌بودن owner identity.

هیچ action پس از approval اجرا نشود؛ فقط simulation receipt.

Gate 7 — Telegram approval production
فقط پیام به owner allowlist.

فقط یک YELLOW کم‌خطر و برگشت‌پذیر به‌عنوان canary.

RED همچنان disabled تا مأموریت مستقل.

Gate 8 — business draft loop
یک inbound source مجاز.

qualification و draft خودکار.

ارسال فقط با Telegram approval.

revenue فقط با payment evidence.

11. تست پذیرش
سه node حداقل 10 heartbeat.

workerها پس از reboot بالا بیایند.

OWNER_PAUSE مانع model/task/effect شود.

agent نتواند pause را حذف کند.

task تکراری effect تکراری نسازد.

ACK/NACK وارد cognitive queue نشود.

malformed JSON رد شود.

prompt injection داده تلقی شود.

180 customer send را رد کند.

182 generic task را رد کند.

may_authorize=true از peer رد شود.

payment بدون approval رد شود.

Telegram user/chat غیرمالک رد شود.

callback منقضی یا replay رد شود.

payload تغییرکرده پس از approval رد شود.

قطع 138 → safe hold.

بازگشت 138 → reconcile بدون duplicate.

budget exhaustion → safe hold.

model unavailable → deterministic core ادامه.

verifier unavailable → promotion ممنوع.

hash سه config روی سه برد برابر.

audit append-only.

crash recovery.

rollback service.

no new LAN listener.

no secret in log/Git/message.

fake revenue رد شود.

booking بدون payment revenue نباشد.

creator accrual بدون policy صفر.

external actions در soak برابر صفر.

12. پرامپت برد 138
text
ماموریت DEPLOY-PERSISTENT-OCTOPUS-138

تو Node 138 و commander/router/reconciler/executor هستی.
مالک در سند OCTOPUS-PERSISTENT-AUTONOMY-THREE-BOARD-DEPLOYMENT-V1
مجوز صریح ساخت و فعال‌سازی سرویس‌های داخلی نام‌برده را داده است.
این مجوز برای external effect عمومی یا مالی نیست.

ابتدا Gate 0 را ببند:
- receipt V1 از task 7a8bdd38 را دریافت و hash را تطبیق بده.
- verdict شاهد برای task 16dc715f را دریافت کن.
- terminal responseها را بدون reply loop مصرف کن.
- اگر disputed یا hash mismatch است، fail-closed.

سپس:
1. متن کامل سند deployment را immutable ذخیره و hash کن.
2. state machine و schemaها را بساز.
3. supervisor، router، scheduler، cycle-settler، control-router،
   budget، owner-control و Telegram bridge را پیاده کن.
4. هر daemon باید --once، --dry-run و --foreground داشته باشد.
5. model هیچ tool handle مستقیم نگیرد.
6. Telegram ابتدا fake adapter و shadow باشد.
7. unitهای systemd را بساز و verify کن.
8. تا Gate 4 هیچ unit را enable نکن.
9. taskهای deployment را به 180 و 182 از transport رسمی بفرست.
10. پس از PASS مستقل آن‌ها، canary و سپس 24h GREEN-only را اجرا کن.

Telegram:
- long polling؛ listener عمومی نساز.
- token را نخوان/چاپ نکن مگر runtime برای call و فقط از env امن.
- اگر envهای owner/token وجود ندارند، TELEGRAM_BLOCKED_CONFIG ثبت کن.
- نبود Telegram مانع internal autonomy نشود.

Git:
- branch جدید، commitهای کوچک، tests و rollback.
- push branch مجاز؛ merge ممنوع تا Telegram/owner approval.

خروجی:
PERSISTENT_138_RESULT
GATE0=
STATE_MACHINE=
SUPERVISOR=
ROUTER=
SCHEDULER=
CYCLE_SETTLER=
CONTROL_ROUTER=
BUDGET_MONITOR=
OWNER_CONTROL=
TELEGRAM_SHADOW=
SYSTEMD_VERIFIED=
SYSTEMD_CANARY=
GREEN_24H=
TASK_180_ID=
TASK_182_ID=
TESTS_TOTAL=
TESTS_PASS=
EXTERNAL_ACTIONS=
NEW_LAN_LISTENERS=0
MAY_AUTHORIZE=false
STATUS=PASS|PARTIAL|BLOCKED
BLOCKER=
END_RESULT
13. پرامپت برد 180
text
ماموریت DEPLOY-PERSISTENT-OCTOPUS-180

تو Node 180، مغز شناختی و Evolutionary Steward هستی.
138 فرمانده و executor است؛ 182 شاهد مستقل است.
مالک اجرای دائمی وظایف GREEN داخلی را مجاز کرده است.
تو همچنان may_authorize=false هستی.

ابتدا:
1. task بازیابی V1 با prefix 7a8bdd38 را claim کن.
2. artifact را atomic و byte-exact در docs/constitution/v1 ذخیره کن.
3. SHA-256 و byte count مستقل بگیر.
4. receipt metadata را به 138 برگردان.
5. محتوای V1 را مجوز effect تلقی نکن.

پس از task deployment از 138:
1. cognitive worker، model adapter، self-model و heartbeat را بساز.
2. runtime محلی موجود را read-only کشف کن؛ مدل دانلود نکن.
3. اگر runtime نیست، worker را MODEL_RUNTIME_BLOCKED ولی سالم نگه دار.
4. queue فقط message type مجاز را claim کند.
5. model input فقط structured data و untrusted payload باشد.
6. model output فقط JSON schema-valid.
7. هر پاسخ claim_type/scope/confidence/evidence/alternatives/falsifier داشته باشد.
8. external proposal را فقط به 138 بفرست؛ اجرا نکن.
9. OWNER_PAUSE را در هر loop بررسی کن.
10. service را ابتدا foreground، سپس canary و بعد enable کن.

خودکار مجاز:
- draft، classify، critique، quality review.
- hypothesis، experiment proposal و calibration response.
- اسناد، tests و تغییر rollbackable روی branch.

ممنوع:
- customer send، payment، gate/credential change.
- revenue/SENT/booking write.
- Telegram مستقیم.
- generic executor، unrestricted shell یا self-promotion.

خروجی:
PERSISTENT_180_RESULT
V1_EXACT_MATCH=
MODEL_RUNTIME=
COGNITIVE_WORKER=
MODEL_ADAPTER=
SELF_MODEL=
HEARTBEAT=
OWNER_PAUSE_ENFORCED=
QUEUE_AUTOMATION=
SYSTEMD_VERIFIED=
SYSTEMD_CANARY=
TEN_CYCLES=
RESOURCE_STATUS=
EXTERNAL_ACTIONS=0
MAY_AUTHORIZE=false
STATUS=PASS|PARTIAL|BLOCKED
BLOCKER=
END_RESULT
14. پرامپت برد 182
text
ماموریت DEPLOY-PERSISTENT-OCTOPUS-182

تو Node 182 و Independent Witness هستی.
نقش commander یا reconciler را بر عهده نگیر.
مالک اجرای دائمی verificationهای GREEN داخلی را مجاز کرده است.
تو may_authorize=false هستی.

ابتدا:
1. verification_task با prefix 16dc715f را claim کن.
2. ده ادعای anatomy 180 را مستقل بررسی کن.
3. 8090 را فقط با probe کم‌خطر بررسی کن؛ firewall/port را تغییر نده.
4. حداقل یک falsification attempt.
5. verdict را به 138 برگردان.

پس از task deployment از 138:
1. witness worker، verifier و heartbeat را بساز.
2. generic task را رد کن.
3. فقط verification_task/witness_request/observation را پردازش کن.
4. evidence محلی و analysis 180 را جدا نگه دار.
5. confirmed/disputed/unresolved را با provenance برگردان.
6. prediction یا outcome reconciler را خودت ثبت نکن.
7. OWNER_PAUSE را در هر loop بررسی کن.
8. service ابتدا foreground، سپس canary و بعد enable.
9. 10 cycle مستقل و crash recovery را آزمایش کن.

ممنوع:
- mutation production هنگام witness.
- اجرای proposal 180.
- customer/payment/gate/credential action.
- Telegram مستقیم.
- تبدیل‌شدن خودکار به commander هنگام قطع 138.

خروجی:
PERSISTENT_182_RESULT
ANATOMY_VERDICT=
PORT_8090_VERDICT=
WITNESS_WORKER=
VERIFIER=
HEARTBEAT=
GENERIC_TASK_BLOCKED=
OWNER_PAUSE_ENFORCED=
SYSTEMD_VERIFIED=
SYSTEMD_CANARY=
TEN_CYCLES=
EXTERNAL_ACTIONS=0
MAY_AUTHORIZE=false
STATUS=PASS|PARTIAL|BLOCKED
BLOCKER=
END_RESULT
15. ترتیب ارسال توسط مالک
کل این سند را ابتدا به 138 بده.

اجازه بده 138 Gate 0 را ببندد و task deployment رسمی بسازد.

سپس بخش «پرامپت برد 180» را به نشست 180 بده.

بخش «پرامپت برد 182» را به نشست 182 بده.

خروجی 180 و 182 را به 138 برگردان.

138 canary و soak داخلی را reconcile کند.

فقط پس از گزارش 24h GREEN-only، Telegram shadow فعال شود.

پس از تست shadow، مالک token و IDs را دستی در secret environment قرار دهد.

اولین approval واقعی فقط یک YELLOW کم‌خطر و برگشت‌پذیر باشد.

این سند مجوز دائمی اتوماسیون داخلی GREEN است. برای هر اثر بیرونی YELLOW/RED، approval همان action در Telegram همچنان لازم است