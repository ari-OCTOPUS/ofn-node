"""مدل‌های داده — پروژه و وضعیت آن."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class State(str, Enum):
    RUNNING = "running"   # روشن
    STOPPED = "stopped"   # خاموش
    UNKNOWN = "unknown"   # ناشناخته


@dataclass
class Project:
    """یک پروژه در رجیستری. مغزِ کنترل از روی همین‌ها کار می‌کند."""
    id: str
    name: str
    workdir: str
    start: List[str]
    test: List[str] = field(default_factory=list)
    health: List[str] = field(default_factory=list)
    enabled: bool = False
    # نگاشتِ رمزها:  نامِ متغیرِ محیطی → عنوانِ ورودی در KeePassXC
    secrets: Dict[str, str] = field(default_factory=dict)
    # مالکیتِ چند-کاربره (فاز ۱): خالی = مالِ ادمین
    owner: str = ""
    allowed: List[str] = field(default_factory=list)


@dataclass
class ProjectStatus:
    id: str
    name: str
    enabled: bool
    state: State
    pid: Optional[int] = None
    healthy: Optional[bool] = None
    detail: str = ""
