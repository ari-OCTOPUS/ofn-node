"""
langfuse_sink.py — فاز ۲: قلاب اختیاری Langfuse (ابزار رصد واقعی ۲۰۲۶).

اگر این متغیرها در .env باشند، رویدادهای ممیزی به Langfuse هم ارسال می‌شوند:
    LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST (اختیاری)
اگر نباشند یا پکیج نصب نباشد، کاملاً بی‌صدا غیرفعال می‌شود و چیزی نمی‌شکند.
(audit log محلی همیشه مستقل کار می‌کند — Langfuse فقط یک لایه‌ی اضافه است.)
"""
from __future__ import annotations
import os


class LangfuseSink:
    """رابط امن: اگر فعال نباشد، emit() یک no-op است."""

    def __init__(self):
        self.enabled = False
        self._client = None
        self._trace = None
        pub = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
        sec = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
        if not (pub and sec):
            return
        try:
            from langfuse import Langfuse
            self._client = Langfuse(
                public_key=pub, secret_key=sec,
                host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            self.enabled = True
            print("🛰️  Langfuse فعال شد — رویدادها به داشبورد ابری هم می‌روند.")
        except Exception as e:
            print(f"ℹ️  Langfuse غیرفعال ماند ({e}) — فقط audit log محلی استفاده می‌شود.")

    def start_run(self, topic: str) -> None:
        if not self.enabled:
            return
        try:
            self._trace = self._client.trace(name="fusion-run", input={"topic": topic})
        except Exception:
            self._trace = None

    def emit(self, event: str, actor: str, data: dict) -> None:
        if not self.enabled:
            return
        try:
            target = self._trace or self._client
            target.event(name=f"{actor}:{event}", metadata=data)
        except Exception:
            pass  # هرگز اجرای اصلی را نشکن

    def flush(self) -> None:
        if self.enabled:
            try:
                self._client.flush()
            except Exception:
                pass
