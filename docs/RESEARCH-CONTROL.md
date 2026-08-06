# Research Control Panel

Endpointهای اضافه‌شده:

- `GET /api/research/stats`
- `GET /api/research/list?q=&category=&limit=`
- `POST /api/research/import`
- `POST /api/research/rebuild`

در پیام‌های شروع جلسه/هیپنوتیزم، backend به جای ۵ قطعه، ۱۲ قطعه مرتبط از RAG را به مغز می‌دهد تا قبل از پاسخ priming پژوهشی انجام شود.
