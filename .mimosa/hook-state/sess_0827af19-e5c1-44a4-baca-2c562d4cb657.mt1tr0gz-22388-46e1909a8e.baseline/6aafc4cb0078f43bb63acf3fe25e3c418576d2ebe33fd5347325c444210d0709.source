#!/usr/bin/env python3
"""sensory_bus.py — CP-1: مسیرِ afferentِ واحد (propose-only، no-PII، $0).

نگاشتِ observationهای پاها به topicِ School + رویدادِ لجر. یک classifier ساده/stub
که ورودیِ خام را به {topic_ids, ledger_event} تبدیل می‌کند — بدونِ PII (فقط topic
label، هرگز رکوردِ خام).

متریکِ afferent_internal_ratio = (نرخِ ورودیِ حسیِ واقعی)/(نرخِ رویدادِ درونی).
آلارم اگر نسبت < آستانه («سیستم دارد رؤیا می‌بیند» — all internal، no reality).

خطِ قرمز: بدونِ PII — فقط topic label · Accounting فقط محلی، هرگز LLM · propose-only،
هیچ اثر · read-only ingestion · بدونِ import از *_gate/chrono/money production.
هیچ فایلِ خامِ مشتری هرگز وارد نمی‌شود — classifier فقط metadata/label می‌بیند.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from collections import deque

# آستانه‌های afferent
AFFERENT_RATIO_ALARM = 0.15   # اگر < این → سیستم all-internal (رؤیا)
RATIO_WINDOW = 50             # پنجرهٔ نرخ (آخرین N رویداد)

# لیستِ سیاهِ PII — این کلمات هرگز نباید در observation بیایند
PII_PATTERNS = ("invoice#", "invoice number", "abn:", "tax file number", "tfn",
                "passport", "credit card", "bank account", "bsb", "medicare",
                "license number", "driver license", "address:", "phone:",
                "email@", "password", "api_key", "token=", "secret=")


@dataclass
class Observation:
    """یک ورودیِ حسی از پا. **نه رکوردِ خام** — فقط metadata/label.
    raw_data هرگز ذخیره نمی‌شود؛ classifier فقط نوع/برچسب می‌بیند."""
    source: str               # leg_id (e.g. "lead-naghshi", "crypto")
    obs_type: str             # "lead", "error", "payment", "status", "market"
    label: str                # sanitized label (no PII)
    intensity: float = 0.5    # 0..1
    ts: float = field(default_factory=time.time)


@dataclass
class AfferentEvent:
    """خروجیِ sensory bus: topic_ids + ledger_event. propose-only، no-PII."""
    source: str
    obs_type: str
    topic_ids: list[str]
    ledger_event_type: str
    intensity: float
    afferent: bool = True     # real sensory input (not internal)
    ts: float = field(default_factory=time.time)


def _contains_pii(text: str) -> bool:
    """چکِ PII در text. اگر هست → True (رد)."""
    t = str(text).lower()
    return any(p in t for p in PII_PATTERNS)


def classify(obs: Observation) -> AfferentEvent:
    """classifier ساده/stub: observation → {topic_ids, ledger_event_type}.
    نگاشتِ observation type به topicهای School Memory.
    ⚑ برای معمار: classifier واقعی با LLM/embedding — فعلاً rule-based.
    PII check: اگر label حاوی PII است → topic خالی (رد)."""
    if _contains_pii(obs.label):
        return AfferentEvent(source=obs.source, obs_type=obs.obs_type,
                             topic_ids=[], ledger_event_type="OBSERVE",
                             intensity=0.0, afferent=False)
    # rule-based mapping
    mapping = {
        "lead": (["A01", "B01", "C02"], "OBSERVE"),         # attention, trust, markets
        "error": (["E03", "E04"], "NOTE"),                   # ai-agency, attention-economy
        "payment": (["C02", "C03"], "MONEY_ATTRIBUTION"),    # markets, inequality
        "status": (["E01", "F08"], "NOTE"),                  # platforms, resilience
        "market": (["C02", "E02"], "OBSERVE"),               # markets, recommender-loops
    }
    topics, event_type = mapping.get(obs.obs_type, (["A01"], "OBSERVE"))
    return AfferentEvent(source=obs.source, obs_type=obs.obs_type,
                         topic_ids=topics, ledger_event_type=event_type,
                         intensity=obs.intensity)


class SensoryBus:
    """مسیرِ afferentِ واحد. observation → classify → publish (advisory).
    متریکِ afferent_ratio = real_sensory / total_events.
    آلارم اگر < AFFERENT_RATIO_ALARM (سیستم دارد رؤیا می‌بیند)."""

    def __init__(self, window: int = RATIO_WINDOW):
        self.window = window
        self._events: deque[AfferentEvent] = deque(maxlen=window)
        self._internal_events: deque[bool] = deque(maxlen=window)  # True=afferent
        self._alarms: list[dict] = []

    def ingest(self, obs: Observation) -> AfferentEvent:
        """یک observation را classify + record. خروجی: AfferentEvent.
        PII → afferent=False (رد)."""
        event = classify(obs)
        self._events.append(event)
        self._internal_events.append(event.afferent)
        return event

    def ingest_internal(self, source: str = "system", detail: str = "") -> None:
        """ثبتِ یک رویدادِ درونی (نه حسی). برای محاسبهٔ ratio."""
        self._internal_events.append(False)
        self._events.append(AfferentEvent(source=source, obs_type="internal",
                                          topic_ids=[], ledger_event_type="NOTE",
                                          intensity=0.0, afferent=False))

    @property
    def afferent_ratio(self) -> float:
        """نسبتِ رویدادِ حسیِ واقعی به کل. < آستانه = رؤیا."""
        if not self._internal_events:
            return 0.0
        return sum(1 for a in self._internal_events if a) / len(self._internal_events)

    def check_alarm(self) -> dict | None:
        """آلارم اگر afferent_ratio < آستانه (all-internal، رؤیا)."""
        if len(self._internal_events) < 5:   # کم‌داده
            return None
        r = self.afferent_ratio
        if r < AFFERENT_RATIO_ALARM:
            alarm = {"type": "afferent-deficit", "ratio": round(r, 3),
                     "threshold": AFFERENT_RATIO_ALARM,
                     "detail": "سیستم all-internal است — ورودیِ حسیِ واقعی کم",
                     "ts": time.time()}
            self._alarms.append(alarm)
            return alarm
        return None

    @property
    def alarms(self) -> list[dict]:
        return list(self._alarms)

    def publish_advisory(self, event: AfferentEvent, bus=None) -> bool:
        """publish روی unified_bus (advisory، propose-only).
        اگر bus نباشد → False (no-op)."""
        if bus is None:
            return False
        try:
            bus.publish(event.ledger_event_type, {
                "source": event.source, "obs_type": event.obs_type,
                "topic_ids": event.topic_ids, "intensity": event.intensity,
                "afferent": event.afferent}, actor="sensory-bus")
            return True
        except Exception:  # noqa: BLE001
            return False

    def status(self) -> dict:
        """snapshot فقط‌خواندنی."""
        return {"total_events": len(self._events),
                "afferent_ratio": round(self.afferent_ratio, 3),
                "alarms_count": len(self._alarms),
                "window": self.window}
