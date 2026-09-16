"""
memory/chunk_ids.py — B3: شناسه‌ی پایدارِ chunk برای RAG (خالص و تست‌پذیر).

چرا: ID قبلی اندیسِ **سراسریِ** chunk در کلِ vault را در خود داشت
(md5(source#i#content)). ویرایش/افزودن/حذفِ هر یادداشت، i همه‌ی chunkهای
بعدی را شیفت می‌داد → IDهای نو ساخته می‌شد ولی IDهای کهنه هرگز پاک نمی‌شدند:
رشدِ بی‌پایانِ chroma_db + نتایجِ جست‌وجوی کهنه.

اینجا ID فقط از (source, hash محتوا, occurrence) ساخته می‌شود — مستقل از
بقیه‌ی vault. occurrence فقط برای chunkهای بایت‌به‌بایت یکسانِ «همان» فایل
است تا ID تکراری به chroma ندهیم.

بدونِ هیچ وابستگی‌ای جز stdlib — جدا از vectorstore تا در هر محیطی تست شود.
"""
from __future__ import annotations

import hashlib


def chunk_id(source: str, content: str, occurrence: int = 0) -> str:
    """ID قطعی و پایدار برای یک chunk."""
    h = hashlib.sha1(content.encode("utf-8")).hexdigest()
    raw = f"{source}#{h}#{occurrence}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def ids_for_chunks(pairs: list) -> list:
    """IDهای یکتا برای فهرستی از (source, content).

    ترتیبِ فایل‌های دیگر هیچ اثری روی ID یک chunk ندارد؛ فقط تکرارِ
    محتوای یکسان در همان source شمارنده می‌گیرد.
    """
    seen: dict = {}
    out = []
    for src, content in pairs:
        key = (src, hashlib.sha1(content.encode("utf-8")).hexdigest())
        occ = seen.get(key, 0)
        seen[key] = occ + 1
        out.append(chunk_id(src, content, occ))
    return out
