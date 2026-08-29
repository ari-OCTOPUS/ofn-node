# شناخت و مدل‌ها: مسیر زبان، provenance و failure

## مسیر واقعی ask

```text
متن مالک + grounding اندازه‌گیری‌شده
        |
        v
1) deterministic intent/rule
        | miss
        v
2) SQLite ask_cache (request hash namespaced)
        | miss/error
        v
3) local Qwen via llama.cpp loopback
        | answer => LOW_CONFIDENCE + cache
        | unavailable/empty
        v
4) optional allowlisted teacher learning
        | unavailable/denied
        v
5) NEEDS_OWNER
```

`[LOCAL-CODE] /opt/octopus/lab/ofn/organism/cognition/backend.py:20-23,38-76,140-224,304-467`.

قانون deterministic ابتدا اجرا می‌شود. cache key علاوه بر text، grounding را در namespace شامل organism/model/policy hash می‌کند. inference با lock serial می‌شود و پس از miss دوباره cache بررسی می‌گردد. `[LOCAL-CODE] cognition/backend.py:140-193,304-379`.

## قشر محلی واقعی

`LocalCortex` فقط URL عددی loopback و port `8081` را می‌پذیرد، proxy و redirect را غیرفعال می‌کند و خروجی empty/invalid را `DEGRADED` می‌نامد. پاسخ معتبر مدل نیز عمداً `LOW_CONFIDENCE` است، نه fact قطعی. `[LOCAL-CODE] cognition/backend.py:25-137`.

runtime فاز ۲:

- service llama active، restart count صفر
- listener فقط `127.0.0.1:8081`
- model محلی Qwen3-0.6B حدود 410M
- public cortex status `AVAILABLE`

`[RUNTIME-VERIFIED] service/listener/model stat؛ /etc/systemd/system/octopus-llama-lab.service:11-28`.

### استعارهٔ «قشر زبان»

A) **Vibe Coding:** Qwen دهان/قشر زبانی است که دفتر محلی را به جمله تبدیل می‌کند.  
B) **ترجمهٔ مهندسی:** inference engine اختیاری با grounding، confidence label و fail-closed fallback.  
C) **محدودیت:** مدل زبان هویت، حافظهٔ رویدادی، انگیزه یا آگاهی نیست؛ خاموشی آن chain را نابود نمی‌کند.

## anti-fabrication

policy و system instruction می‌گویند فقط factهای اندازه‌گیری‌شده استفاده شود و host/sensor/memory/capability ساخته نشود. موضوع‌های live یا خطرناک مانند weather/price/geo/secret/actuator از teacher learning رد می‌شوند. `[LOCAL-CODE] cognition/backend.py:78-97؛ cognition/policy.py:7-22`.

artifact ارزیابی موجود، ۷/۷ case را برای source split، WAN fail-closed، geo عدم‌جعل، closed hands و عدم ادعای AGI pass ثبت کرده است؛ این report محتوای prompt/utterance را بازنشر نمی‌کند. `[LOCAL-OFFLINE-LAB] /opt/octopus/lab/evidence/TRANSFORMATION-EVAL.json:1-4,61-64`.

## teacher و provenance

teacher status فقط readiness را از secret loader می‌گیرد؛ report هیچ secret value را نخوانده یا منتشر نکرد. source allowlist را به یک host محدود و redirect را رد می‌کند. پاسخ موفق با hash response، model track و claim `LEARNED_FROM_MODEL` در `learned_topics` ذخیره می‌شود. `[LOCAL-CODE] cognition/teacher.py:16-54,57-138؛ cognition/learn.py:65-144`.

DB فعلی چهار learned topic دارد: سه `deepseek_flash` و یک `deepseek_deep`، همه با claim `LEARNED_FROM_MODEL`. محتوای topic/summary بررسی یا گزارش نشد. `[RUNTIME-VERIFIED] SQLite learned_topics grouped metadata`.

public snapshot label برابر `LEARN_ONLY_DEEPSEEK` بود. این یعنی config/path برای یادگیری مفهومی فعال است؛ این مأموریت readiness یا network execution را با call تأیید نکرد و هیچ external system را تماس نداد. `[LOCAL-LIVE] sanitized ORGANISM-PUBLIC snapshot؛ start-organism.sh:35-40`.

## general WAN: کد حاضر، مسیر ناقص

`cognition/wan.py` برای HTTPS public fetch و جدول `wan_fetches` نوشته شده، اما:

- `AskCascade` آن را import/call نمی‌کند؛ search فقط routeهای rule/cache/local/teacher/owner را نشان داد. `[IMPLEMENTED_DISCONNECTED] cognition/backend.py:304-467`.
- source `answer_wan()` در branch world، `complete_deep(prompt, mode="wan")` را صدا می‌زند، ولی امضای واقعی فقط یک positional prompt دارد. `[CONFLICT] cognition/wan.py:411-433؛ cognition/teacher.py:156-168`.
- source DB جدول `wan_fetches` را تعریف می‌کند، live DB ندارد. `[CONFLICT] persistence/db.py:154-165؛ SQLite schema snapshot`.
- process فعلی قبل از آخرین تغییر wan/db شروع شده است. `[CONFLICT] runtime/file timestamp evidence`.

بنابراین **WAN Learning** (teacher) و **general WAN fetch** دو چیز متفاوت‌اند: اولی `LIVE_WITH_GAP` و دارای provenance قبلی است؛ دومی `IMPLEMENTED_DISCONNECTED` و فعلاً ناسازگار.

## failure behavior

- rule hit: مدل اصلاً لازم نیست.
- cache hit: پاسخ قبلی با route/hash provenance برمی‌گردد.
- cache error: cascade ادامه می‌دهد.
- Qwen empty/down: health `DEGRADED` و ask به teacher مجاز یا `NEEDS_OWNER` می‌رود.
- teacher denied/unconfigured/fails: `NEEDS_OWNER`؛ fact زنده اختراع نمی‌شود.
- failure مدل: `model_failure_is_organism_failure=False`.

`[LOCAL-CODE] cognition/backend.py:319-467؛ runtime/app.py:175-215`.

## Vault

Vault یک projection Markdown از snapshot است و در پایان life tick export می‌شود. برای انسان/agent مفید است، ولی source of truth نیست و می‌تواند از DB عقب بماند. `[LOCAL-CODE] runtime/life_cycle.py:385-409؛ /opt/octopus/lab/vault/board-life-001`.

### استعارهٔ «کتابخانه»

A) **Vibe Coding:** Vault کتابخانهٔ خواندنی شهر است.  
B) **ترجمهٔ مهندسی:** export فایل Markdown از state/DB برای مصرف انسانی.  
C) **محدودیت:** کتابخانه همان event store نیست؛ وجود فایل activation یا consistency لحظه‌ای را تضمین نمی‌کند.

مقایسهٔ حافظه‌ها در [03_EVENT_AND_MEMORY_TOUR_FA.md](03_EVENT_AND_MEMORY_TOUR_FA.md) است.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
