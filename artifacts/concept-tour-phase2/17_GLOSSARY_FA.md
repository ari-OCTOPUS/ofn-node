# واژه‌نامه و قرارداد استعاره

## vocabulary حضور

- `LIVE`: implementation و activation محلی با evidence runtime.
- `LIVE_WITH_GAP`: فعال است، ولی guarantee/اتصال/حفاظت مهم کم دارد.
- `IMPLEMENTED_DISCONNECTED`: کد دارد، wiring runtime ندارد.
- `SCAFFOLD`: قطعات اولیه بدون daemon/orchestration.
- `OFFLINE_TESTED`: test/artifact محلی دارد، runtime production نیست.
- `OFFLINE_UNTESTED`: فقط کد آفلاین بدون test evidence.
- `BLOCKED_NO_GPU`: اجرای موردنظر به GPU سازگار نیاز دارد و موجود نیست.
- `BLOCKED_DEPENDENCY`: dependency نرم‌افزاری غایب است.
- `DOCUMENT_ONLY`: فقط سند/design.
- `UNKNOWN`: evidence برای طبقه‌بندی قوی‌تر کافی نیست.

## واژه‌های مهندسی

- **Canonical event:** serialization قطعی برای hash.
- **EventKernel:** commit/duplicate/outbox/replay coordinator.
- **Outbox:** delivery ledger پایدار پس از commit.
- **Episode:** projection یک event با salience/outcome و provenance.
- **Identity ledger:** hash-chain append-only داخلی.
- **External anchor:** checkpoint مستقل بیرون DB برای کشف rollback/truncation.
- **Homeostasis:** نگاشت signalهای منابع به state سلامت.
- **Afferent:** مسیر ورودی LAN/state/alert به runtime.
- **Cortex:** inference engine زبان؛ identity نیست.
- **APC:** reuse محاسبهٔ KV برای prefix کامل مشترک.
- **Cache salt:** extra hash برای جداسازی tenantها.
- **Block size:** تعداد token در واحد تخصیص منطقی KV.
- **Pareto frontier:** candidateهایی که هیچ candidate دیگر در همهٔ objectiveها بر آن‌ها غالب نیست.
- **WBE:** مدل allometric شبکهٔ توزیع زیستی.
- **Active Inference:** inference حالت و policy با مدل مولد و EFE.
- **Δθ:** metric مهندسی salience/تغییر؛ تجربه نیست.

## استعاره‌های core با سه جزء اجباری

### بدن
A) برد بدن کشتی است.  
B) RAM/thermal/disk signal و threshold مهندسی‌اند.  
C) hardware بدن زیستی یا تجربهٔ درد نیست.

### فانوس L0
A) gateway فانوس بندر است.  
B) observe/serve، heartbeat، mirror و state cache است.  
C) authority، قصد یا فرمان‌روایی ندارد.

### قلب رویداد
A) EventKernel ضربان را اول در دفتر ثبت می‌کند.  
B) transaction events+outbox و سپس dispatch/replay است.  
C) SQLite حیات یا انگیزه ایجاد نمی‌کند.

### دفترخانه SQLite
A) دفترخانه سندهای شهر را نگه می‌دارد.  
B) schema، FK، uniqueness، WAL و durability است.  
C) database حقیقت مطلق یا consciousness نیست و backup مستقل می‌خواهد.

### صندوق پست outbox
A) نامهٔ ثبت‌شده تا تحویل گم نمی‌شود.  
B) status pending/done و replay بعد از crash/queue saturation است.  
C) exactly-once effect بیرونی را به‌تنهایی تضمین نمی‌کند.

### شناسنامه
A) هر صفحه مهر صفحهٔ قبل را دارد.  
B) sequence + previous hash + canonical SHA-256 است.  
C) شخص، public PKI و tail-truncation proof نیست.

### خاطره
A) episode خاطره‌ای با رسید رویداد است.  
B) source_event FK، type match، salience و provenance است.  
C) summary تجربهٔ ذهنی نیست و بدون source پذیرفته نمی‌شود.

### کتابخانه Vault
A) کتابخانهٔ عمومی شهر است.  
B) Markdown projection از snapshot/DB است.  
C) source of truth یا activation proof نیست.

### تب/گرسنگی
A) برد حال بدنش را می‌سنجد.  
B) RAM/PSI/temp/disk به state machine می‌روند.  
C) عدد sensor احساس یا نیاز زیستی نیست.

### اعصاب آوران
A) خبر پیرامون را وارد می‌کند.  
B) allowlist probe، hysteresis و alert letter است.  
C) ping ادراک یا رابطهٔ اجتماعی نیست و side effect دارد.

### قشر زبان
A) Qwen دهان/قشر برای جمله‌سازی است.  
B) rule→cache→local inference→fallback است.  
C) مدل هویت، حافظهٔ پایدار یا آگاهی نیست.

### ضربان ۲۱۰ ثانیه‌ای
A) شهر دوره‌ای خودش را مرور می‌کند.  
B) periodic thread و persistent interval policy است.  
C) heartbeat زیستی، WBE law یا نشانهٔ consciousness نیست.

### کشتی L4 روی خشک‌کن
A) قطعات آینده هنوز در آب نیستند.  
B) contract/store/body/homeostat/arbiter/theta بدون daemon است.  
C) file presence runtime activation نیست.

### شبکهٔ WBE
A) شبکهٔ شاخه‌ای منابع را می‌رساند.  
B) allometric scaling تحت فرض‌های زیستی خاص است.  
C) OCTOPUS vasculature نیست و exponent timer/threshold نمی‌شود.

### نقشه‌کش Active Inference
A) نقشه‌های احتمالی را با حس تازه وزن می‌کند.  
B) A/B/C/D/E، belief update و EFE است.  
C) probability و optimization تجربه یا قصد نیست.

### ساعت Δθ
A) تغییر مهم ساعت مفهومی را جلو می‌برد.  
B) weighted engineering score و cognition gate پیشنهادی است.  
C) inner subjective time یا consciousness نیست.

### قفسهٔ APC
A) آغاز مشترک درخواست از قفسه reuse می‌شود.  
B) hash chain blockهای کامل KV است.  
C) episodic memory یا identity نیست.

### نمک cache
A) هر tenant کلید قفسهٔ خودش را دارد.  
B) tenant-specific extra hash برای isolation است.  
C) salt جای auth، encryption یا secret hygiene را نمی‌گیرد.

### جعبهٔ block
A) tokenها در جعبه‌های ثابت جا می‌گیرند.  
B) allocation/fragmentation/overhead trade-off است.  
C) اندازهٔ بهتر بدون model/GPU/workload واقعی وجود ندارد.

### انبار Hybrid/Mamba
A) کالاهای متفاوت قفسه‌های متفاوت می‌خواهند.  
B) KV group/page size برای attention typeهای مختلف است.  
C) Mamba state حافظهٔ زندگی یا cognition مستقل نیست.

### دروازهٔ مالک
A) پیشنهاد پشت در می‌ماند تا مالک اجازه دهد.  
B) explicit approval reference، thermal/metrics/safety gate و `PROPOSE_ONLY` است.  
C) approval flag جای threat model یا supervision واقعی را نمی‌گیرد.

Evidence labelها در [16_EVIDENCE_INDEX.md](16_EVIDENCE_INDEX.md) تعریف شده‌اند.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
