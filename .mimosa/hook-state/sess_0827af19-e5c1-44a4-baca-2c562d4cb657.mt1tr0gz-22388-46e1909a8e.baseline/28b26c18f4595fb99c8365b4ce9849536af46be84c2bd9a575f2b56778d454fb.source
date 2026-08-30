"""command_registry.py — بارگذار و طبقه‌بندِ رجیستریِ واحدِ فرمان‌ها.

منبعِ حقیقت: 00-Control/command-registry.yaml (سطحِ repo). هر دو adapterِ تلگرام
و داشبورد از همین می‌خوانند. طبقه‌بندی → (group, risk, mode, roles).

fail-closed: فرمانِ ناشناخته = RED/deny با نقشِ خالی؛ فایلِ گم‌شده = نسخهٔ امبدد.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

RISK_LADDER = ("GREEN", "YELLOW", "ORANGE", "RED")

# نسخهٔ امبددِ کمینه — اگر فایلِ YAML پیدا نشد، رفتارِ ایمنِ پیش‌فرض.
_EMBEDDED = {
    "version": 1,
    "risk_ladder": list(RISK_LADDER),
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
    """با بالا رفتن از مسیرِ جاری، 00-Control/command-registry.yaml را می‌یابد."""
    here = Path(start).resolve() if start else Path(__file__).resolve()
    for base in [here, *here.parents]:
        cand = base / "00-Control" / "command-registry.yaml"
        if cand.exists():
            return cand
    return None


class CommandRegistry:
    def __init__(self, data: dict):
        self.version = data.get("version", 1)
        self.groups = data.get("groups", {}) or {}
        self.aliases = data.get("aliases", {}) or {}
        self.approval_syntax = data.get("approval_syntax", "")
        self._index: dict[str, str] = {}
        for gname, g in self.groups.items():
            for c in (g.get("commands") or []):
                self._index[c] = gname

    @classmethod
    def load(cls, path: Optional[Path | str] = None) -> "CommandRegistry":
        p = Path(path) if path else find_registry()
        if not p or not Path(p).exists():
            return cls(_EMBEDDED)
        try:
            import yaml
            data = yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001 — هر خطای خواندن/پارس → امبددِ امن
            return cls(_EMBEDDED)
        if not data.get("groups"):
            return cls(_EMBEDDED)
        return cls(data)

    def canonical(self, command: str) -> str:
        """aliasِ /ziman_* را به فرمانِ canonical تبدیل می‌کند."""
        return self.aliases.get(command, command)

    def classify(self, command: str) -> dict:
        c = self.canonical(command)
        g = self._index.get(c)
        if not g:
            return {"command": c, "group": None, "risk": "RED",
                    "mode": "deny", "roles": [], "known": False}
        grp = self.groups[g]
        return {"command": c, "group": g, "risk": grp.get("risk", "RED"),
                "mode": grp.get("mode", "approval"),
                "roles": list(grp.get("roles") or []), "known": True}

    def role_allowed(self, command: str, role: str) -> bool:
        info = self.classify(command)
        return (role or "").strip().lower() in [r.lower() for r in info["roles"]]

    def all_commands(self) -> list[str]:
        return sorted(self._index.keys())

    def commands_for_group(self, group: str) -> list[str]:
        return list((self.groups.get(group) or {}).get("commands") or [])
