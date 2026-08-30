"""
patch_manager.py — خودبهبودِ کد در دو سطحِ امن (سطح ۳ عمداً وجود ندارد).

LEVEL 1 (suggest)  : پیشنهادِ متنیِ بهبود (بدونِ کد).
LEVEL 2 (patch)    : تولیدِ unified diff با کمکِ brain و ذخیره در patches/؛
                     انسان diff را می‌بیند و خودش با git/ویرایشگر اعمال می‌کند.
LEVEL 3 (execute)  : ❌ پیاده‌سازی نشده — به‌عمد. بات هرگز کدِ خودش را اجرا/بازنویسی نمی‌کند.

این مرز یک تصمیمِ ایمنی است: اجازه‌ندادن به سیستم برای تغییر و اجرای کدِ خودش.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

LEVEL_SUGGEST = 1
LEVEL_PATCH = 2
# LEVEL_EXECUTE = 3  ← عمداً تعریف نشده

_PATCH_DIR = Path(__file__).resolve().parent.parent / "patches"

_DIFF_SYSTEM = (
    "تو یک مهندسِ نرم‌افزارِ محتاطی. یک unified diff (git-style) برای بهبودِ "
    "خواسته‌شده بده. فقط diff را خروجی بده، بدونِ توضیحِ اضافه. تغییرات باید کوچک و امن باشند."
)


class PatchManager:
    """db اختیاری است (برای ثبتِ رجیستری)؛ brain برای سطح ۲ لازم است."""

    def __init__(self, brain=None, db=None):
        self.brain = brain
        self.db = db
        _PATCH_DIR.mkdir(parents=True, exist_ok=True)

    # --- سطح ۱ ---
    def suggest(self, issue: str) -> dict:
        sug = {"level": LEVEL_SUGGEST, "issue": issue,
               "suggestion": f"پیشنهاد برای: {issue} — ابتدا یک تستِ کوچک بنویس، بعد تغییرِ کمینه."}
        if self.db:
            try:
                self.db.save_patch(issue, None, "suggested")
            except Exception:
                pass
        return sug

    # --- سطح ۲ ---
    def generate_patch(self, issue: str) -> dict:
        """با brain یک diff می‌سازد و در patches/ ذخیره می‌کند. اجرا نمی‌کند."""
        if self.brain is None or getattr(self.brain, "name", "offline") == "offline":
            return {"ok": False, "reason": "برای تولیدِ diff به یک brainِ LLM نیاز است (offline نمی‌تواند)."}
        try:
            diff = self.brain.ask(_DIFF_SYSTEM, {"domain": "patch", "label": "patch", "data": issue})
        except Exception as e:
            return {"ok": False, "reason": f"خطا در تولیدِ diff: {e}"}
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = _PATCH_DIR / f"patch_{stamp}.diff"
        path.write_text(diff, encoding="utf-8")
        pid = None
        if self.db:
            try:
                pid = self.db.save_patch(issue, str(path), "generated")
            except Exception:
                pass
        return {"ok": True, "level": LEVEL_PATCH, "path": str(path), "id": pid,
                "note": "diff ذخیره شد. خودت بازبینی و با git/ویرایشگر اعمال کن. بات اجرا نمی‌کند."}

    # --- سطح ۳ ---
    def apply_patch(self, *a, **k):
        raise NotImplementedError(
            "سطح ۳ (اجرای خودکارِ patch) عمداً پیاده‌سازی نشده. diff را دستی بازبینی و اعمال کن."
        )
