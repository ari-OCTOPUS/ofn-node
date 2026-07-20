#!/usr/bin/env python3
"""store.py — Project-F · DataSpine (لایهٔ ۲، 2026-07-16).

منبعِ حقیقتِ یکپارچه برای چهار قابلیتِ Layer 2:

  - ``FanDB``      → fans (segments, tags, LTV, last-contact) · صفر PII (fan_id = هش)
  - ``VaultBank``  → content assets (tags, metrics) · جایگزینِ هوک‌های نمونه
  - ``KPIRollup``  → rollup هفتگی از fans + record_kpi
  - ``OctopusState`` → heartbeat/tick مشترک با orchestrator

طراحی:
  - JSON file-based (restart-safe) · atomic write · fail-soft
  - صفر PII: fan_id = sha1(nickname)[:12]، هرگز نام/یوزرنیم واقعی ذخیره نمی‌شود
  - صفر اکشنِ بیرونی · stdlib-only · propose-only (فقط state نگه می‌دارد)

هر کلاس سبک و مستقل است؛ DataSpine فقط قراردادِ مسیرهاست. هر چهار کلاس در
`langar/` (کنارِ state files موجود) persistence می‌کنند تا در یک‌جا قابل پایش باشند.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from collections import defaultdict

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
DEFAULT_STORE_DIR = _PROJECT_ROOT / "langar"   # کنارِ langar_log/cost_meter/guards state

# آستانه‌های segmentation (قابل‌بازنویسی).
VIP_LTV_THRESHOLD = 50.0          # USD/LTV → vip
CHURN_DAYS = 30                    # روزِ بدونِ contact → churned候选
DEFAULT_LURKER_DAYS = 14           # روزِ بدونِ تعامل → lurker


def _now() -> float:
    return time.time()


def _load_json(path: Path, default):
    """fail-soft loader — فایل غایب/خراب = default."""
    try:
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            return d if isinstance(d, type(default)) else default
    except (json.JSONDecodeError, OSError):
        pass
    return default


def _save_json(path: Path, data) -> None:
    """atomic write — fail-soft (هرگز crash ندهد)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def _fan_id(nickname_or_ref: str) -> str:
    """fan_id از nickname/ref با sha1 → ۱۲ hex. صفر PII: نام واقعی هرگز ذخیره نمی‌شود.

    آری یک نام مستعار یا مرجعِ کوتاه می‌دهد (مثلاً «fan-reddit-1» یا «vip-7»)؛
    ما فقط هشِ آن را نگه می‌داریم. نام/یوزرنیم واقعیِ پلتفرم هرگز وارد نمی‌شود."""
    return "F-" + hashlib.sha1((nickname_or_ref or "").encode("utf-8")).hexdigest()[:12]


# ──────────────────────────────────────────────────────────────────────────
# FanDB — پایهٔ CRM
# ──────────────────────────────────────────────────────────────────────────
class FanDB:
    """پایگاهِ هواداران (صفر PII). segments خودکار از LTV + recency.

    schema (fan_db.json):
      {"fans": {"F-xxxx": {"id", "alias", "channel", "segment", "tags": [],
                           "ltv_usd", "first_seen", "last_contact", "ppv_count",
                           "notes": ""}, ...},
       "updated_at": ts}
    """

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else (DEFAULT_STORE_DIR / "fan_db.json")

    def _state(self) -> dict:
        s = _load_json(self._path, {"fans": {}, "updated_at": None})
        s.setdefault("fans", {})
        s.setdefault("updated_at", None)
        return s

    def _save(self, state: dict) -> None:
        state["updated_at"] = _now()
        _save_json(self._path, state)

    def _recompute_segment(self, fan: dict) -> str:
        """segment خودکار: vip / regular / lurker / churned."""
        ltv = float(fan.get("ltv_usd", 0))
        last = float(fan.get("last_contact", 0) or 0)
        days_since = (_now() - last) / 86400.0 if last else 9999.0
        if ltv >= VIP_LTV_THRESHOLD:
            base = "vip"
        elif ltv > 0:
            base = "regular"
        else:
            base = "lurker"
        # churned: هر segment اگه > CHURN_DAYS بدون contact → churnedCandidate
        if days_since > CHURN_DAYS and base != "lurker":
            return "churned"
        return base

    def add(self, alias: str, channel: str = "of", note: str = "") -> dict:
        """اضافه/به‌روزِ یک fan. اگه alias تکراری باشد، update می‌شود."""
        fid = _fan_id(alias)
        s = self._state()
        fans = s["fans"]
        if fid not in fans:
            fans[fid] = {"id": fid, "alias": str(alias)[:40], "channel": channel[:16],
                         "segment": "lurker", "tags": [], "ltv_usd": 0.0,
                         "first_seen": _now(), "last_contact": 0, "ppv_count": 0,
                         "notes": str(note)[:200]}
        else:
            # update: refresh last_contact + merge note
            fans[fid]["last_contact"] = _now()
            if note:
                old = fans[fid].get("notes", "")
                fans[fid]["notes"] = (old + " | " + note)[:200] if old else note[:200]
        fans[fid]["segment"] = self._recompute_segment(fans[fid])
        self._save(s)
        return {"ok": True, "id": fid, "alias": fans[fid]["alias"],
                "segment": fans[fid]["segment"]}

    def record_purchase(self, alias: str, amount_usd: float, kind: str = "ppv") -> dict:
        """ثبتِ خرید (PPV/sub/tip) → LTV و segment به‌روز می‌شوند."""
        fid = _fan_id(alias)
        s = self._state()
        fan = s["fans"].get(fid)
        if not fan:
            # fan جدید با خریدِ اول
            self.add(alias, note=f"first purchase {kind}")
            s = self._state()
            fan = s["fans"][fid]
        fan["ltv_usd"] = round(float(fan.get("ltv_usd", 0)) + max(0.0, float(amount_usd)), 2)
        fan["ppv_count"] = int(fan.get("ppv_count", 0)) + (1 if kind == "ppv" else 0)
        fan["last_contact"] = _now()
        fan["segment"] = self._recompute_segment(fan)
        self._save(s)
        return {"ok": True, "id": fid, "ltv_usd": fan["ltv_usd"],
                "segment": fan["segment"]}

    def touch(self, alias: str, note: str = "") -> dict:
        """ثبتِ تماس (DM رد/دریافت) → last_contact به‌روز، segment recompute."""
        fid = _fan_id(alias)
        s = self._state()
        fan = s["fans"].get(fid)
        if not fan:
            self.add(alias, note=note)
            return {"ok": True, "id": fid, "created": True}
        fan["last_contact"] = _now()
        if note:
            old = fan.get("notes", "")
            fan["notes"] = (old + " | " + note)[:200] if old else note[:200]
        fan["segment"] = self._recompute_segment(fan)
        self._save(s)
        return {"ok": True, "id": fid, "segment": fan["segment"]}

    def tag(self, alias: str, tag: str) -> dict:
        fid = _fan_id(alias)
        s = self._state()
        fan = s["fans"].get(fid)
        if not fan:
            return {"ok": False, "error": "fan not found — /fan_add first"}
        tag = str(tag)[:24].lower().strip()
        if tag and tag not in fan["tags"]:
            fan["tags"].append(tag)
            self._save(s)
        return {"ok": True, "id": fid, "tags": fan["tags"]}

    def get(self, alias: str) -> dict | None:
        return self._state()["fans"].get(_fan_id(alias))

    def all(self) -> list[dict]:
        return list(self._state()["fans"].values())

    def by_segment(self, segment: str) -> list[dict]:
        seg = segment.lower().strip()
        return [f for f in self.all() if f.get("segment") == seg]

    def summary(self) -> dict:
        fans = self.all()
        segs = defaultdict(int)
        total_ltv = 0.0
        for f in fans:
            segs[f.get("segment", "?")] += 1
            total_ltv += float(f.get("ltv_usd", 0))
        return {"total": len(fans), "segments": dict(segs),
                "total_ltv_usd": round(total_ltv, 2)}


# ──────────────────────────────────────────────────────────────────────────
# VaultBank — بانکِ محتوا (جایگزینِ هوک‌های نمونه)
# ──────────────────────────────────────────────────────────────────────────
class VaultBank:
    """بانکِ assetهای محتوایِ certify‌شده. acquisition_pipeline از این draft می‌زند.

    schema (vault.json):
      {"assets": {"V-xxxx": {"id", "tag", "hook", "caption", "channel", "cert",
                             "used_count", "last_used", "metrics": {...}}, ...},
       "updated_at": ts}
    """

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else (DEFAULT_STORE_DIR / "vault.json")

    def _state(self) -> dict:
        s = _load_json(self._path, {"assets": {}, "updated_at": None})
        s.setdefault("assets", {})
        s.setdefault("updated_at", None)
        return s

    def _save(self, state: dict) -> None:
        state["updated_at"] = _now()
        _save_json(self._path, state)

    def add(self, tag: str, hook: str, caption: str = "",
            channel: str = "reddit", cert: dict | None = None) -> dict:
        """اضافه‌کردنِ یک asset. cert = self-certification (faceless/feet_only/...)."""
        import uuid
        vid = "V-" + uuid.uuid4().hex[:10]
        s = self._state()
        s["assets"][vid] = {
            "id": vid, "tag": str(tag)[:40], "hook": str(hook)[:120],
            "caption": str(caption or hook)[:280], "channel": channel[:16],
            "cert": cert or {}, "used_count": 0, "last_used": 0,
            "metrics": {}, "created": _now(),
        }
        self._save(s)
        return {"ok": True, "id": vid, "tag": tag}

    def pick(self, channel: str = "", n: int = 3) -> list[dict]:
        """انتخابِ n asset برای draft. کم‌استفاده‌ترین اول (fair rotation)."""
        s = self._state()
        assets = list(s["assets"].values())
        if channel:
            assets = [a for a in assets if a.get("channel") == channel]
        # sort: کم‌استفاده‌ترین، سپس قدیمی‌ترین last_used
        assets.sort(key=lambda a: (a.get("used_count", 0), a.get("last_used", 0)))
        return assets[:max(1, int(n))]

    def mark_used(self, vid: str) -> None:
        """ثبتِ استفاده در یک draft."""
        s = self._state()
        a = s["assets"].get(vid)
        if a:
            a["used_count"] = int(a.get("used_count", 0)) + 1
            a["last_used"] = _now()
            self._save(s)

    def record_metric(self, vid: str, upvotes: int = 0, comments: int = 0,
                      unlocks: int = 0) -> None:
        """ثبتِ metric یک asset بعد از پست."""
        s = self._state()
        a = s["assets"].get(vid)
        if a:
            m = a.setdefault("metrics", {})
            m["upvotes"] = m.get("upvotes", 0) + int(upvotes)
            m["comments"] = m.get("comments", 0) + int(comments)
            m["unlocks"] = m.get("unlocks", 0) + int(unlocks)
            self._save(s)

    def all(self) -> list[dict]:
        return list(self._state()["assets"].values())

    def by_tag(self, tag: str) -> list[dict]:
        t = tag.lower().strip()
        return [a for a in self.all() if a.get("tag", "").lower() == t]

    def summary(self) -> dict:
        assets = self.all()
        return {"total": len(assets), "channels": sorted({a.get("channel") for a in assets}),
                "tags": sorted({a.get("tag") for a in assets})}


# ──────────────────────────────────────────────────────────────────────────
# KPIRollup — rollup هفتگی
# ──────────────────────────────────────────────────────────────────────────
class KPIRollup:
    """rollup هفتگی از FanDB + record_kpi. برای /kpi واقعی.

    schema (kpi.json):
      {"weeks": [{"week_start", "fans_total", "new_fans", "revenue_usd",
                  "ppv_unlocks", "posts", "delivery_rate", "segments"}, ...],
       "last_kpi": {...raw last record_kpi...},
       "updated_at": ts}
    """

    SECONDS_PER_WEEK = 7 * 86400

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else (DEFAULT_STORE_DIR / "kpi.json")

    def _state(self) -> dict:
        s = _load_json(self._path, {"weeks": [], "last_kpi": {}, "updated_at": None})
        s.setdefault("weeks", [])
        s.setdefault("last_kpi", {})
        s.setdefault("updated_at", None)
        return s

    def _save(self, state: dict) -> None:
        state["updated_at"] = _now()
        _save_json(self._path, state)

    def record(self, revenue_usd: float = 0, ppv_unlocks: int = 0,
               posts: int = 0, delivery_rate: float = 0,
               new_fans: int = 0, fan_summary: dict | None = None,
               clicks: int = 0, follows: int = 0,
               free_subs: int = 0, paid_conversions: int = 0) -> dict:
        """ثبتِ دادهٔ هفتگی (آری هر جمعه).

        2026-07-20 (backlog #4): فیلدهای funnel اضافه شد تا معیارهای kill/‏G1/G2
        (کلیک→follow→free-sub→paid) بالاخره **قابل‌سنجش** شوند. ورود داده دستی است
        (داشبورد پلتفرم → ‏/kpi_record یا ‏/kpi_import) — هیچ pull زندهٔ پلتفرمی."""
        s = self._state()
        now = _now()
        # bucket هفتگی: شنبه هر هفته
        week_start = now - (now % self.SECONDS_PER_WEEK)
        # پیدا/ساختِ bucket جاری
        weeks = s["weeks"]
        cur = None
        for w in weeks:
            if abs(w.get("week_start", 0) - week_start) < self.SECONDS_PER_WEEK:
                cur = w
                break
        if cur is None:
            cur = {"week_start": week_start, "fans_total": 0, "new_fans": 0,
                   "revenue_usd": 0.0, "ppv_unlocks": 0, "posts": 0,
                   "delivery_rate": 0.0, "segments": {},
                   "clicks": 0, "follows": 0, "free_subs": 0,
                   "paid_conversions": 0}
            weeks.append(cur)
        # جمع (نه replace) — آری ممکن است چند بار در هفته ثبت کند
        cur["revenue_usd"] = round(cur.get("revenue_usd", 0) + max(0, float(revenue_usd)), 2)
        cur["ppv_unlocks"] = cur.get("ppv_unlocks", 0) + max(0, int(ppv_unlocks))
        cur["posts"] = cur.get("posts", 0) + max(0, int(posts))
        cur["new_fans"] = cur.get("new_fans", 0) + max(0, int(new_fans))
        cur["clicks"] = cur.get("clicks", 0) + max(0, int(clicks))
        cur["follows"] = cur.get("follows", 0) + max(0, int(follows))
        cur["free_subs"] = cur.get("free_subs", 0) + max(0, int(free_subs))
        cur["paid_conversions"] = cur.get("paid_conversions", 0) + max(0, int(paid_conversions))
        if delivery_rate > 0:
            cur["delivery_rate"] = float(delivery_rate)
        if fan_summary:
            cur["fans_total"] = fan_summary.get("total", cur.get("fans_total", 0))
            cur["segments"] = fan_summary.get("segments", cur.get("segments", {}))
        # آخرین raw را نگه دار
        s["last_kpi"] = {"revenue_usd": revenue_usd, "ppv_unlocks": ppv_unlocks,
                         "posts": posts, "clicks": clicks, "ts": now}
        # فقط ۲۶ هفته نگه دار (۶ ماه)
        s["weeks"] = weeks[-26:]
        self._save(s)
        return {"ok": True, "week_start": week_start, "current": cur}

    # فرمت CSV دستی (بدون شبکه — paste از داشبورد پلتفرم):
    #   revenue_usd,ppv_unlocks,posts,delivery_rate,new_fans,clicks,follows,free_subs,paid_conversions
    CSV_COLUMNS = ("revenue_usd", "ppv_unlocks", "posts", "delivery_rate",
                   "new_fans", "clicks", "follows", "free_subs", "paid_conversions")

    def import_csv(self, csv_text: str, fan_summary: dict | None = None) -> dict:
        """importِ دستی KPI از متن CSV (2026-07-20، backlog #4). هر سطر یک record.

        سطر header (اگر بود) skip می‌شود؛ سطرهای خراب شمرده و رد می‌شوند —
        هیچ استثنایی به caller نمی‌رسد، هیچ شبکه‌ای صدا زده نمی‌شود."""
        imported, skipped = 0, 0
        for line in (csv_text or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().replace(" ", "").startswith("revenue_usd"):
                continue   # header
            parts = [p.strip() for p in line.split(",")]
            try:
                vals = {}
                for i, col in enumerate(self.CSV_COLUMNS):
                    if i < len(parts) and parts[i] != "":
                        vals[col] = float(parts[i]) if col in ("revenue_usd", "delivery_rate") \
                            else int(float(parts[i]))
                if not vals:
                    skipped += 1
                    continue
                self.record(fan_summary=fan_summary, **vals)
                imported += 1
            except (ValueError, TypeError):
                skipped += 1
        return {"ok": imported > 0 or skipped == 0, "imported": imported,
                "skipped": skipped}

    def current_week(self) -> dict:
        s = self._state()
        weeks = s.get("weeks", [])
        return weeks[-1] if weeks else {}

    def trend(self, weeks_back: int = 4) -> list[dict]:
        """آخرین N هفته برای نمایشِ trend."""
        return self._state().get("weeks", [])[-max(1, int(weeks_back)):]

    def summary(self) -> dict:
        s = self._state()
        weeks = s.get("weeks", [])
        if not weeks:
            return {"total_weeks": 0, "total_revenue_usd": 0, "current": {}}
        total_rev = sum(w.get("revenue_usd", 0) for w in weeks)
        return {"total_weeks": len(weeks), "total_revenue_usd": round(total_rev, 2),
                "current": weeks[-1]}


# ──────────────────────────────────────────────────────────────────────────
# LinkState — کدهای tracking پست‌های دستی (2026-07-20، backlog #3)
# ──────────────────────────────────────────────────────────────────────────
class LinkState:
    """نگاشتِ آیتمِ ready → کدِ کوتاه tracking برای پستِ دستی.

    وقتی /pf_ready یک payload می‌دهد، یک کد (مثل ``L-a1b2c3``) می‌گیرد؛ آری آن
    کد را در لینک/UTM دستی می‌گذارد و بعداً کلیک‌ها را با /kpi_import برمی‌گرداند.
    این تنها راهِ measurable شدنِ G1 (کلیک→follow) بدونِ هیچ pull زنده است.

    schema (link_state.json):
      {"links": {"L-xxxxxx": {"code", "item_id", "channel", "assigned",
                              "clicks", "last_import"}}, "updated_at": ts}
    idempotent: یک item همیشه همان کد را می‌گیرد. صفر PII، صفر شبکه."""

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else (DEFAULT_STORE_DIR / "link_state.json")

    def _state(self) -> dict:
        s = _load_json(self._path, {"links": {}, "updated_at": None})
        s.setdefault("links", {})
        return s

    def _save(self, state: dict) -> None:
        state["updated_at"] = _now()
        _save_json(self._path, state)

    @staticmethod
    def _code_for(item_id: str) -> str:
        return "L-" + hashlib.sha1((item_id or "").encode("utf-8")).hexdigest()[:6]

    def assign(self, item_id: str, channel: str = "reddit") -> str:
        """کد tracking برای یک آیتمِ ready — idempotent."""
        code = self._code_for(item_id)
        s = self._state()
        if code not in s["links"]:
            s["links"][code] = {"code": code, "item_id": str(item_id)[:24],
                                "channel": str(channel)[:16], "assigned": _now(),
                                "clicks": 0, "last_import": None}
            self._save(s)
        return code

    def record_clicks(self, code: str, clicks: int) -> dict:
        """ثبتِ کلیکِ import شده (دستی) روی یک کد."""
        s = self._state()
        link = s["links"].get(str(code).strip())
        if not link:
            return {"ok": False, "error": "unknown code"}
        link["clicks"] = int(link.get("clicks", 0)) + max(0, int(clicks))
        link["last_import"] = _now()
        self._save(s)
        return {"ok": True, "code": link["code"], "clicks": link["clicks"]}

    def get(self, code: str) -> dict | None:
        return self._state()["links"].get(str(code).strip())

    def all(self) -> list[dict]:
        return list(self._state()["links"].values())

    def summary(self) -> dict:
        links = self.all()
        return {"total": len(links),
                "total_clicks": sum(int(l.get("clicks", 0)) for l in links),
                "channels": sorted({l.get("channel") for l in links})}


# ──────────────────────────────────────────────────────────────────────────
# OctopusState — heartbeat مشترک
# ──────────────────────────────────────────────────────────────────────────
class OctopusState:
    """state اتصال به orchestrator. heartbeat + last_tick + sync status.

    schema (octopus.json):
      {"beat": 0, "last_tick": null, "protective": false, "pain": 0,
       "brain_loaded": false, "neural_available": false, "history": [...],
       "updated_at": ts}
    """

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else (DEFAULT_STORE_DIR / "octopus.json")

    def _state(self) -> dict:
        s = _load_json(self._path, {"beat": 0, "last_tick": None, "protective": False,
                                    "pain": 0.0, "brain_loaded": False,
                                    "neural_available": False, "history": [],
                                    "updated_at": None})
        for k, dflt in (("beat", 0), ("last_tick", None), ("protective", False),
                        ("pain", 0.0), ("brain_loaded", False),
                        ("neural_available", False), ("history", [])):
            s.setdefault(k, dflt)
        return s

    def _save(self, state: dict) -> None:
        state["updated_at"] = _now()
        _save_json(self._path, state)

    def record_tick(self, beat: int, protective: bool, pain: float,
                    brain_loaded: bool, neural_available: bool) -> dict:
        """ثبتِ یک tick از orchestrator (اگه موجود باشد)."""
        s = self._state()
        s["beat"] = int(beat)
        s["last_tick"] = _now()
        s["protective"] = bool(protective)
        s["pain"] = round(float(pain), 3)
        s["brain_loaded"] = bool(brain_loaded)
        s["neural_available"] = bool(neural_available)
        history = s.get("history", [])
        history.append({"beat": beat, "ts": _now(), "pain": round(float(pain), 3),
                        "protective": bool(protective)})
        s["history"] = history[-50:]   # آخرین ۵۰ tick
        self._save(s)
        return {"ok": True, "beat": beat}

    def mark_isolated(self, reason: str = "neural modules unavailable") -> dict:
        """وقتی orchestrator موجود نیست، heartbeat isolated ثبت کن."""
        s = self._state()
        s["last_tick"] = _now()
        s["neural_available"] = False
        s["brain_loaded"] = False
        s["beat"] = s.get("beat", 0) + 1
        history = s.get("history", [])
        history.append({"beat": s["beat"], "ts": _now(), "isolated": True,
                        "reason": reason[:80]})
        s["history"] = history[-50:]
        self._save(s)
        return {"ok": True, "isolated": True, "reason": reason}

    def snapshot(self) -> dict:
        s = self._state()
        return {"beat": s.get("beat", 0), "last_tick": s.get("last_tick"),
                "protective": s.get("protective", False),
                "pain": s.get("pain", 0.0),
                "brain_loaded": s.get("brain_loaded", False),
                "neural_available": s.get("neural_available", False)}


# ──────────────────────────────────────────────────────────────────────────
# DataSpine — container مشترک
# ──────────────────────────────────────────────────────────────────────────
class DataSpine:
    """container یکپارچه برای همهٔ stores. یک نقطهٔ دسترسی.

    استفاده:
        spine = DataSpine()
        spine.fans.add("fan-1", "of")
        spine.vault.add("pedicure", "nice arch", "reddit")
        spine.kpi.record(revenue_usd=15, ppv_unlocks=1)
    """

    def __init__(self, store_dir: str | Path | None = None):
        d = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
        d.mkdir(parents=True, exist_ok=True)
        self.fans = FanDB(path=d / "fan_db.json")
        self.vault = VaultBank(path=d / "vault.json")
        self.kpi = KPIRollup(path=d / "kpi.json")
        self.links = LinkState(path=d / "link_state.json")
        self.octopus = OctopusState(path=d / "octopus.json")

    def full_snapshot(self) -> dict:
        """خلاصهٔ همهٔ stores برای /status مرکزی."""
        return {
            "fans": self.fans.summary(),
            "vault": self.vault.summary(),
            "kpi": self.kpi.summary(),
            "links": self.links.summary(),
            "octopus": self.octopus.snapshot(),
        }
