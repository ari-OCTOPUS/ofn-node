"""command_registry.py (ziman-agent) — همان رجیستریِ واحدِ سطحِ repo را می‌خواند.

منبعِ حقیقتِ مشترک: 00-Control/command-registry.yaml. این کپیِ سبک فقط برای
adapterِ تلگرامِ زیمان است (طبقه‌بندیِ ریسک + رفعِ alias). فایلِ YAML یکی است؛
منطقِ بارگذار در دو کدپایهٔ مستقل تکرار می‌شود (اشکالی ندارد — منبع یکی است).
fail-closed: فرمانِ ناشناخته = RED/deny.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

_EMBEDDED = {
    "groups": {
        "read_status": {"risk": "GREEN", "mode": "auto",
                        "roles": ["owner", "admin", "operator", "viewer", "agent"],
                        "commands": ["/status", "/summary", "/health", "/risks",
                                     "/projects", "/queue", "/incidents", "/focus"]},
        "data_catalog": {"risk": "YELLOW", "mode": "propose",
                         "roles": ["owner", "admin", "operator"],
                         "commands": ["/product", "/photo", "/variant",
                                      "/reconcile", "/catalog"]},
        "control": {"risk": "ORANGE", "mode": "approval",
                    "roles": ["owner", "admin"],
                    "commands": ["/policy", "/pause", "/resume", "/mode"]},
        "approval": {"risk": "RED", "mode": "red_gate", "roles": ["owner"],
                     "commands": ["/approve", "/reject", "/defer",
                                  "/rollback", "/halt_ziman"]},
    },
    "aliases": {
        "/ziman_status": "/status", "/ziman_inventory": "/summary",
        "/ziman_products": "/product", "/ziman_photos": "/photo",
        "/ziman_experiments": "/risks", "/ziman_content": "/catalog",
        "/ziman_decisions": "/queue",
    },
}


def find_registry(start: Optional[Path] = None) -> Optional[Path]:
    here = Path(start).resolve() if start else Path(__file__).resolve()
    for base in [here, *here.parents]:
        cand = base / "00-Control" / "command-registry.yaml"
        if cand.exists():
            return cand
    return None


class ZimanCommandRegistry:
    def __init__(self, data: dict):
        self.groups = data.get("groups", {}) or {}
        self.aliases = data.get("aliases", {}) or {}
        self._index: dict[str, str] = {}
        for gname, g in self.groups.items():
            for c in (g.get("commands") or []):
                self._index[c] = gname

    @classmethod
    def load(cls, path: Optional[Path | str] = None) -> "ZimanCommandRegistry":
        p = Path(path) if path else find_registry()
        if not p or not Path(p).exists():
            return cls(_EMBEDDED)
        try:
            import yaml
            data = yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            return cls(_EMBEDDED)
        return cls(data if data.get("groups") else _EMBEDDED)

    def canonical(self, command: str) -> str:
        return self.aliases.get(command, command)

    def classify(self, command: str) -> dict:
        c = self.canonical(command)
        g = self._index.get(c)
        if not g:
            return {"command": c, "risk": "RED", "mode": "deny", "known": False}
        grp = self.groups[g]
        return {"command": c, "risk": grp.get("risk", "RED"),
                "mode": grp.get("mode", "approval"), "known": True}
