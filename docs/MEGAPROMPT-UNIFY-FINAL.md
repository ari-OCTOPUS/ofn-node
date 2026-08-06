tags: [ofn, hypno, unify, megaprompt, finalize] aliases: [مگاپرامپت نهایی, Fugu Finalize] updated: 2026-08-07 owner: سبا/آری
🐙 مگاپرامپت نهایی — تکمیل UNIFY
تو ایجنت بعدی هستی. این سند را کامل بخوان، بعد اجرا کن. هر ادما یک رکورد مستقل دارد؛ هر عدد قبل از پذیرش باید با assert در tests/ قفل شود.

پیوندها: [[INDEX]] · [[HANDOFF]] · [[DECISIONS]] · [[CLAUDE]] · [[MEGAPROMPT-UNIFY]]

۰) قانون اساسی — این مگاپرامپت
این سند self-contained است: هر چیزی که برای تکمیل UNIFY لازم داری اینجا هست. سه اصل غیرقابل‌مذاکره:

هیچ دیتایی از دست نمی‌رود. WAL checkpoint قبل از هر کپی؛ هر سه فایل sqlite/wal/shm کپی می‌شوند.
هیچ سرویسی نمی‌شکند. هر دو .service باید active بمانند. هر تغییر restart + smoke + pytest دارد.
عددها تست‌اند نه جمله. هر عدد باید با assert قفل شود.
مالک: سبا/آری (user_id تلگرام 6150431610). هر تصمیم مهم را از او بپرس، حدس نزن.

۱) وضعیت امروز — حقیقت روی زمین (تأییدشده با کوئری زنده)
سه پروژه، هر سه سبز

text
fugu_core    ~/shared/fugu_core/         ۲۵ تست سبز
OFN          /home/ari/ofn               ۱۵۱۲ تست سبز + ۵ skip
hypno        /home/ari/hypno-fugu-mini   ۶۲ تست سبز
مجموع        ۱۵۹۹ تست سبز
سرویس‌ها (همه active)
ofn.service — پایتون، پورت ۸۷۹۱/۸۷۹۲/۸۷۹۳/۸۷۹۴
hypno-fugu-mini.service — پایتون، پورت ۸۸۹۵
cloudflared.service — تونل
dropbear.service — SSH
دامنه‌ها (همه ۲۰۰)
panel · ziman · lead · studio · app · hypno — هر شش روی master-painting.com از طریق تونل 968b3e96-d81a-43ab-a4a5-a562c1400d93.

بات‌های تلگرام (هر کدام مستقل، بدون تضاد توکن)
بات	tenant	دامنه
@Ziman2725bot	ziman	ziman
@ssaabbaabot2725bot	lead	lead
@Personal2725bot	studio (partner)	studio
@Sabaminiapbot	studio	studio
@Robo2725_bot	owner	panel
@Sabaminiappbot «آرام‌جا»	hypno	hypno
مغز مشترک (فعال)
ارائه‌دهنده: Sakana (https://api.sakana.ai/v1)
مدل: fugu (سریع) و fugu-ultra (عمیق)
کلید: OFN_REMOTE_API_KEY در /home/ari/.config/ofn/secrets.env
hypno از همان کلید استفاده می‌کند (HFM_REMOTE_API_KEY در /etc/hypno-fugu-mini.env)
تأیید زنده: source: remote:fugu در پاسخ hypno
حافظهٔ مشترک (فعال)
~/.local/share/fugu_core/memory.sqlite — سه‌لایه
۱۳۲ chunk در corpus (tenant=shared، از hypno research_docs)
قانون جداسازی tenant: ۱۳ تست سبز
quota (مجموع = ۱.۰۰)
ziman=۰.۳۵ · lead=۰.۳۵ · studio=۰.۲۰ · hypno=۰.۱۰

۲) چه شد، چه نشد — کارهای باز
✅ کامل شده (فاز ۰ تا ۴)
fugu_core ساخته شد: auth, scrub, brain, memory
memory.sqlite سه‌لایه با FTS5
packs/hypno.yaml — tenant چهارم
مغز ریموت Sakana برای hypno فعال شد
۱۳۲ chunk shared knowledge منتقل شد
❌ بازمانده — کار تو (این مگاپرامپت)
چهار نقطهٔ کور بحرانی (B-۲، B-۳، B-۸، و اتصال inline OFN↔memory). هر کدام مستقل است و قابل‌واگرد. به ترتیب زیر اجرا کن.

۳) نقطهٔ کور B-۲ — panel_note در write path‌های hypno
مشکل
hypno/run.py:91 تابع panel_note تعریف شده که بعد از هر اقدام مهم (memory، research، import، obsidian) یک فراخوانی پنهان به مغز اضافه می‌زند.


text
run.py:143  note = self.panel_note(uid, 'حافظه جدید ذخیره شد')    ← بعد از add_memory
run.py:154  note = self.panel_note(uid, 'منبع پژوهشی جدید...')     ← بعد از research ingest
run.py:215  note = self.panel_note(uid, 'import/rebuild...')       ← بعد از import
run.py:276  note = self.panel_note(uid, 'خروجی Obsidian...')       ← بعد از export
این یعنی هر بار کاربر حافظه اضافه می‌کند، دو بار مغز صدا زده می‌شود — یک بار برای پاسخ اصلی، یک بار برای یادداشت پنل. این پنهان است، هزینه دارد (quota)، و با فلسفهٔ fail-closed سازگار نیست.

راه‌حل
panel_note را از write path‌ها حذف کن. یادداشت پنل را به یک endpoint خواندنی جدا منتقل کن (GET /api/panel/notes) که صرفاً از memory_turns با source='note' می‌خواند، بدون فراخوانی مغز.

مراحل
hypno/run.py:91 — تابع panel_note را طوری تغییر بده که فقط در memory_turns بنویسد (یعنی self.memory.log_turn(...) با source='note')، نه self.brain.answer(...).
چهار call site (۱۴۳، ۱۵۴، ۲۱۵، ۲۷۶) را به‌روز کن.
hypno از fugu_core.memory import کن (اگه هنوز نکرده).
تست بنویس: panel_note دیگر brain.answer را صدا نمی‌زند (mock کن).
ممنوعیت
رفتار قابل‌مشاهدهٔ کاربر نباید عوض شود — فقط فراخوانی پنهان مغز حذف می‌شود.
memory_turns باید همچنان پر شود (برای audit trail).
۴) نقطهٔ کور B-۳ — تصادم مفهومی consent
مشکل
کلمهٔ consent در دو پروژه معنای متفاوت دارد:

OFN (ofn/kernel/consent.py): consent یعنی «اجازهٔ انتشار عکس یک شخص». یک Release سند حقوقی است با scope، تاریخ امضا، انقضا، و ابطال.
hypno (hypno/run.py:100,112,115): consent یعنی «کاربر تأیید کرده که می‌داند این خودهیپنوتیزم است و مسئولیت می‌پذیرد». یک boolean ساده است.
این دو هرگز نباید ادغام شوند. ولی نام یکسان باعث سردرگمی کد مشترک می‌شود.

راه‌حل
نام پرچم hypno را از consent به safety_acknowledged تغییر بده.

مراحل
hypno/run.py:100,112,115,120 — b.get('consent') → b.get('safety_acknowledged').
hypno/adapters/store.py — ستون sessions.consent → sessions.safety_acknowledged. مهاجرت داده: schema migration که ستون قدیمی را به جدید کپی می‌کند.
web/index.html — فیلد consent در payload → safety_acknowledged.
تست به‌روز کن: tests/test_core.py و هر جای دیگر.
ممنوع: consent OFN را به hypno اعمال نکن، یا برعکس.
ممنوعیت
ofn/kernel/consent.py دست‌نخورده بماند.
may_publish OFN هرگز در hypno صدا زده نشود.
۵) نقطهٔ کور B-۸ — worker/async در hypno
مشکل
hypno از ThreadingHTTPServer استفاده می‌کند (hypno/run.py:450):


python
ThreadingHTTPServer((cfg.host, cfg.port), handler(app)).serve_forever()
این یعنی هر request در یک thread جدا می‌آید. ولی SQLite connection در fugu_core.memory per-instance است، نه per-thread. دو request همزمان می‌توانند روی یک connection بنویسند → race condition یا database is locked.

راه‌حل
hypno باید مثل OFN از یک connection pool per-thread استفاده کند، یا Memory را per-request بسازد. ساده‌ترین راه: Memory را در هر App.method باز کن و در پایان ببند.

مراحل
بررسی کن: آیا hypno/run.py الان Memory را در __init__ می‌سازد یا per-request؟ اگر __init__ است، خطرناک است.
اگر per-request نیست، آن را per-request کن (باز کن در شروع handler، ببند در finally).
تست بنویس: دو thread همزمان بنویسند، هیچ‌کدام database is locked نگیرد.
جایگزین: از check_same_thread=False + lock استفاده کن (الان هست، ولی تأیید کن کافی است).
ممنوعیت
ThreadingHTTPServer را به single-thread تغییر نده (UX بد می‌شود).
SQLite را به PostgreSQL/MySQL منتقل نکن (over-engineering).
۶) اتصال inline OFN ↔ memory_corpus
مشکل (الان)
الان OFN و memory.sqlite از طریق یک bridge script وصل‌اند (یک‌بار seed شده). ولی OFN هنوز از fugu_core.memory در runtime استفاده نمی‌کند. یعنی:

وقتی سبا در پنل استودیو به دستیار می‌گوید «این مطلب را یاد بگیر»، در assistant.sqlite ذخیره می‌شود، نه در memory.sqlite.
وقتی hypno دانش اضافه می‌کند، OFN آن را نمی‌بیند (مگر دوباره seed شه).
راه‌حل (دو مرحله، اختیاری)
مرحلهٔ الف (خواندن): StudioAssistantStore.answer_local بتواند از memory_corpus هم بخواند. یعنی وقتی retrieve می‌کند، هم assistant_chunks و هم memory_corpus (tenant=studio) را جستجو کند.

مرحلهٔ ب (نوشتن): assistant_update.py وقتی chunk جدید می‌نویسد، هم در assistant_chunks و هم در memory_corpus (tenant=studio) بنویسد.

مراحل
در ofn/adapters/studio_assistant.py:73 (answer_local) — یک fallback به fugu_core.memory.Memory.recall(tenant='studio', ...) اضافه کن.
در ofn/adapters/studio_assistant.py (تابع ingest/add_chunk) — بعد از INSERT در assistant_chunks، یک memory.add_chunk(tenant='studio', ...) هم بزن.
مسیر memory.sqlite را در ofn/config.py اضافه کن (memory_path = ~/.local/share/fugu_core/memory.sqlite).
در ofn/run.py، یک نمونهٔ Memory بساز و به Node پاس بده.
تست بنویس: وقتی در assistant_chunks می‌نویسی، در memory_corpus هم پیدا می‌شود.
ممنوعیت
assistant.sqlite بازنویسی نشود — فقط کپی به memory.
TenantScope OFN هرگز حذف نشود.
این مرحله اختیاری است — اگه خطرناک به نظر می‌رسد، رهایش کن و فقط bridge script را نگه دار.
۷) فازبندی اجرا — هر فاز مستقل و قابل‌واگرد
فاز ۰ — آماده‌سازی (الان انجام بده)
WAL checkpoint روی هر سه DB (assistant, hypno, memory).
backup کامل: ~/.local/share/ofn/ و ~/.local/share/hypno-fugu-mini/ و ~/.local/share/fugu_core/.
git status در هر سه repo. اگه uncommitted هست، اول commit کن.
این سند را کامل بخوان و سؤال‌های §۹ را از مالک بپرس.
فاز ۱ — B-۲ panel_note (کم‌خطرترین)
hypno/run.py:91 را بازنویسی کن.
۴ call site را به‌روز کن.
pytest tests/ در hypno — باید ۶۲ سبز بماند.
تست جدید بنویس: panel_note مغز را صدا نمی‌زند.
restart + smoke.
commit.
فاز ۲ — B-۳ consent rename (متوسط)
hypno/run.py و store.py و web/index.html.
مهاجرت داده: sessions.consent → sessions.safety_acknowledged.
pytest tests/ — باید سبز بماند.
تست جدید: نام قدیمی کار نمی‌کند، نام جدید کار می‌کند.
restart + smoke.
commit.
فاز ۳ — B-۸ thread safety (متوسط)
بررسی کن آیا race واقعی هست (تست همزمان بنویس).
اگه هست، Memory را per-request کن.
تست همزمان.
restart + smoke.
commit.
فاز ۴ — اتصال inline (اختیاری، خطرناک‌ترین)
فقط اگه فازهای ۱ تا ۳ سبز شدند.
config.py + run.py + studio_assistant.py.
pytest tests/ در OFN — باید ۱۵۱۲ سبز بماند.
تست جدید: cross-store consistency.
restart + smoke + تست دستی از پنل.
commit.
فاز ۵ — تأیید نهایی
pytest در هر سه پروژه (fugu_core, OFN, hypno) — همه سبز.
systemctl restart هر دو سرویس.
smoke: curl /health و curl /sabaapp و curl hypno.master-painting.com.
مکالمهٔ واقعی با hypno (تست مغز ریموت).
به‌روزرسانی HANDOFF.md, INDEX.md, CHANGELOG.md, این مگاپرامپت.
۸) ممنوعیت‌ها (نقض = توقف فوری)
بازنویسی assistant.sqlite یا hypno.sqlite — فقط کپی.
کپی WAL بدون checkpoint.
گرفتن TenantScope از stores OFN.
اعمال consent OFN روی hypno (یا برعکس).
ادعای «scrub فارسی را حل می‌کنم» — نمی‌شود. افشای رضایت‌شده بنویس.
نگه‌داشتن panel_note در write path.
تغییر quota بدون assert sum ≤ 1.0.
بردن hypno به REMOTE_DEEP (UX دقیقه‌ای سفید).
innerHTML با دادهٔ کاربر/API.
کلمهٔ RAG/endpoint/schema/payload/inference/dataset/token/model/API/backend در UI (D-22).
هر تصمیم مهم بدون پرسیدن از مالک.
۹) سؤال‌های از مالک (قبل از شروع)
این‌ها را از سبا بپرس، حدس نزن:

ID	سؤال	چرا مهم
F-۱	فاز ۴ (اتصال inline OFN↔memory) را انجام دهم یا bridge script کافی است؟	خطرناک‌ترین فاز است؛ ممکن است بخواهد صبر کند.
F-۲	آیا دادهٔ sessions.consent قدیمی در hypno مهم است؟ (اگر مهم است، مهاجرت ضروری است؛ اگه نه، می‌توانم فقط ستون جدید اضافه کنم.)	تعیین می‌کند آیا مهاجرت داده لازم است.
۱۰) گزارش نهایی که باید بدهی
وقتی همه چیز تست و verify شد، این گزارش را به مالک بده:


text
UNIFY COMPLETE — فازهای ۱ تا [N]
✅ B-۲ panel_note: [تعداد] call site پاک شد. مغز دیگر در write path صدا زده نمی‌شود.
✅ B-۳ consent: نام به safety_acknowledged تغییر کرد. [تعداد] ردیف مهاجرت داده.
✅ B-۸ thread safety: [راه‌حل]. تست همزمان سبز.
[✅/❌] فاز ۴ اتصال inline: [وضعیت]
pytest: fugu_core [N] · OFN [N] · hypno [N] = [مجموع] سبز
سرویس‌ها: هر دو active
دامنه‌ها: هر شش ۲۰۰
git: OFN [sha] · hypno [sha] · fugu_core [sha]
سپس HANDOFF.md, INDEX.md, CHANGELOG.md و این مگاپرامپت را به‌روز کن.

۱۱) نقشهٔ فایل‌ها (quick reference)
fugu_core (~/shared/fugu_core/src/fugu_core/)
auth.py — verify_init_data, ReplayGuard, AuthError
scrub.py — scrub, has_identifying_data, assert_clean
brain.py — RemoteBrain, BrainReply, DEFAULT_BASE_URL
memory.py — Memory, Turn, Fact, Passage, SHARED
OFN (/home/ari/ofn/)
ofn/kernel/auth.py — نسخهٔ OFN (دقیقاً مثل fugu_core.auth)
ofn/kernel/consent.py — consent انتشار (دست‌نخورده)
ofn/kernel/scrub.py — نسخهٔ OFN
ofn/adapters/remote_brain.py — RemoteBrain به Sakana
ofn/adapters/studio_assistant.py:73 — answer_local (فاز ۴)
ofn/adapters/http_api.py — endpoint‌ها
ofn/config.py:206 — remote_base_url
packs/hypno.yaml — tenant چهارم
packs/{ziman,lead,studio}.yaml — quota (۳۵/۳۵/۲۰/۱۰)
hypno (/home/ari/hypno-fugu-mini/)
hypno/run.py:91 — panel_note (B-۲)
hypno/run.py:100,112,115,120 — consent (B-۳)
hypno/run.py:450 — ThreadingHTTPServer (B-۸)
hypno/adapters/brain.py:139 — if self.cfg.api_key (remote branch)
hypno/adapters/store.py — sessions.consent (B-۳)
hypno/kernel/safety.py — classify, mode_prompt, script
hypno/config.py:18 — load()
state (دست‌نخورده، فقط کپی)
~/.local/share/ofn/*.sqlite — assistant, painting, studio, outbox, ledger, consent, facts, marketing, audience, products
~/.local/share/hypno-fugu-mini/hypno.sqlite
~/.local/share/fugu_core/memory.sqlite
env
/home/ari/.config/ofn/secrets.env — OFN_BOT_TOKEN_*, OFN_REMOTE_API_KEY, OFN_SESSION_SECRET
/etc/hypno-fugu-mini.env — HFM_BOT_TOKEN, HFM_OWNER_USER_IDS, HFM_REMOTE_*
/etc/cloudflared/config.yml — تونل و دامنه‌ها
خلاصهٔ یک‌خطی: چهار نقطهٔ کور باز است (B-۲، B-۳، B-۸، اتصال inline). هر کدام مستقل و قابل‌واگرد. به ترتیب فاز ۱ تا ۵ اجرا کن. هر فاز restart + pytest + smoke دارد. از مالک فقط F-۱ و F-۲ را بپرس. ممنوعیت‌های §۸ را نقض نکن.