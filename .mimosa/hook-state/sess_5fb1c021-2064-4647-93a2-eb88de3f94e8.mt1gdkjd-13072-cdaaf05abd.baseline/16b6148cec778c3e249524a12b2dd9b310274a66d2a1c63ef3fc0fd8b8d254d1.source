"""
prompt_store.py — انبارِ نسخه‌دارِ پرامپت ایجنت‌ها (پایه‌ی خوداپدیتی).

پرامپت هر ایجنت با تاریخچه‌ی کامل نسخه‌ها در prompts.json نگه‌داری می‌شود.
این یعنی هر تغییری «قابل بازگشت» (rollback) و «قابل ممیزی» است — اصل فیوژن:
هیچ تغییری بی‌ردپا و بی‌بازگشت نباشد.
"""
from __future__ import annotations
import json, os, time

import config


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


class PromptStore:
    def __init__(self, path: str | None = None, seed: dict[str, str] | None = None):
        # مسیر را در زمان ساخت می‌خوانیم (نه import) تا override/تست درست کار کند.
        self.path = path or config.PROMPTS_PATH
        self.data = self._load()
        if seed:
            for agent, prompt in seed.items():
                if agent not in self.data:
                    self._add(agent, prompt, note="baseline", score=None)
            self._save()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _add(self, agent: str, prompt: str, note: str, score):
        rec = self.data.setdefault(agent, {"active": 0, "versions": []})
        v = len(rec["versions"]) + 1
        rec["versions"].append({"v": v, "prompt": prompt, "ts": _now(),
                                "note": note, "score": score})
        rec["active"] = v
        return v

    # --- API ---
    def get_active(self, agent: str) -> str:
        rec = self.data.get(agent)
        if not rec:
            return ""
        return rec["versions"][rec["active"] - 1]["prompt"]

    def active_version(self, agent: str) -> int:
        return self.data.get(agent, {}).get("active", 0)

    def get_score(self, agent: str):
        rec = self.data.get(agent)
        if not rec:
            return None
        return rec["versions"][rec["active"] - 1].get("score")

    def new_version(self, agent: str, prompt: str, note: str, score) -> int:
        v = self._add(agent, prompt, note, score)
        self._save()
        return v

    def set_score(self, agent: str, score) -> None:
        rec = self.data[agent]
        rec["versions"][rec["active"] - 1]["score"] = score
        self._save()

    def rollback(self, agent: str) -> int:
        """active را به نسخه‌ی قبلی برمی‌گرداند (بدون حذف تاریخچه)."""
        rec = self.data.get(agent)
        if not rec or rec["active"] <= 1:
            return rec["active"] if rec else 0
        rec["active"] -= 1
        self._save()
        return rec["active"]

    def history(self, agent: str) -> list[dict]:
        return self.data.get(agent, {}).get("versions", [])
