"""خواندن رجیستریِ پروژه‌ها از فایل پیکربندی (projects.yaml)."""
from pathlib import Path
from typing import List, Optional

import yaml

from .models import Project


class Registry:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.base = self.path.parent.parent
        self.owner_chat_id: int = 0
        self._items = {}
        self.reload()

    def reload(self) -> None:
        with open(self.path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        self.owner_chat_id = int(raw.get("owner_chat_id", 0) or 0)
        self._items = {}
        for p in raw.get("projects", []):
            proj = Project(
                id=str(p["id"]),
                name=p.get("name", p["id"]),
                workdir=p["workdir"],
                start=list(p.get("start", [])),
                test=list(p.get("test", [])),
                health=list(p.get("health", [])),
                enabled=bool(p.get("enabled", False)),
                secrets=dict(p.get("secrets", {}) or {}),
                owner=str(p.get("owner", "") or ""),
                allowed=list(p.get("allowed", []) or []),
            )
            self._items[proj.id] = proj

    def all(self) -> List[Project]:
        return list(self._items.values())

    def get(self, pid: str) -> Optional[Project]:
        return self._items.get(pid)
