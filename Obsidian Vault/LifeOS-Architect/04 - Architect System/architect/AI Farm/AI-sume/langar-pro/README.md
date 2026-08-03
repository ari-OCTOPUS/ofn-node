# LANGAR Pro — استکِ حرفه‌ای (مهاجرتِ فازی)

نسخه‌ی production از LANGAR: Agentic RAG + Graph Memory + Constitutional Gate +
Human Feedback + Audit Ledger، روی استکِ FastAPI/Postgres.

> ⚠️ این کد روی دستگاهِ من (sandbox) تست نشده چون به Postgresِ در‌حال‌اجرا نیاز دارد.
> با `docker compose up` روی دستگاهِ خودت اجرا و تأیید کن.

## قانونِ طلایی (hard-coded در طراحی)
```
No source → no fact.
No consent → no action.
No feedback → no learning.
No audit → no trust.
No uncertainty → no verdict.
AI may recommend; the final value judgment stays with the human.
```

## اجرا (فاز ۱)
```bash
cp .env.example .env     # رمز و کلیدها را بگذار
docker compose up --build
# تست:
curl http://localhost:8000/health
```
schema خودکار هنگامِ ساختِ کانتینرِ Postgres اجرا می‌شود (`db/schema.sql`).

## نقشه‌ی فازها
- **فاز ۱ (همین):** FastAPI + Postgres(pgvector) + Redis · schema کامل · endpointهای health/goals/research/verdict (اسکلت). ← اجرا و تأیید کن.
- **فاز ۲:** مهاجرتِ منطقِ `researcher/` و `core/constitution` به بک‌اند؛ وصل‌کردنِ `/research` واقعی (search → source scoring → synthesize → gate → decision).
- **فاز ۳:** Graph Memory روی جدول‌های `claims`/`claim_edges` (بدونِ Neo4j) + جست‌وجوی معنایی با pgvector.
- **فاز ۴:** Celery + Redis برای کارهای async (crawl/پژوهشِ طولانی) + Skeptic agent.
- **فاز ۵:** باتِ تلگرامِ فعلی به‌عنوان کلاینتِ این API (به‌جای SQLiteِ محلی) + داشبوردِ Next.js (اختیاری).
- **فاز ۶ (فقط اگر لازم شد):** Neo4j/Qdrant مستقل وقتی مقیاسِ داده توجیهش کند.

## رابطه با باتِ فعلی
باتِ SQLiteِ موجود سرِ پا می‌ماند و کار می‌کند. این استک به‌موازات بالا می‌آید؛
وقتی فاز ۲ آماده شد، بات به این API وصل می‌شود و SQLite فقط cache/آفلاین می‌ماند.

## یادداشتِ مهندسی
برای یک کاربر، این استک عامدانه «بزرگ» است. هر سرویسِ اضافه (Neo4j/Qdrant/Celery)
فقط وقتی روشن شود که نبودش دردِ واقعی ساخته باشد — وگرنه بارِ نگه‌داری بی‌دلیل است.
