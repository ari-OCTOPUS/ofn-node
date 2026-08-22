#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daemon.py — حلقهٔ بستهٔ دکتر: چشم ⟶ فهم ⟶ پیشنهاد ⟶ رأی ⟶ اجرا ⟶ رأی ⟶ merge.

این چیزی است که «ماژول» را به **عضوِ زندهٔ ارگانیسم** تبدیل می‌کند: تا وقتی کسی باید
دستی دستور بزند، دکتر یک ابزار است. وقتی خودش هر روز می‌بیند، می‌فهمد، می‌پرسد و
منتظرِ رأی می‌ماند — بخشی از اختاپوس است.

چرخهٔ عمرِ یک ماموریت:

    proposed ──✅ نیت──▶ running ──سوئیت سبز──▶ awaiting-merge ──✅ دیف──▶ merged
        │                   │                                        │
        └──❌──▶ rejected    └──قرمز──▶ failed                        └──❌──▶ rejected

پنج انضباط که در کد اجرا می‌شوند:
  ۱ **هم‌زمان فقط یک ماموریتِ باز.** بدونِ این، دکتر تبدیل به سیلِ کارت می‌شود.
  ۲ هر گام فقط با رأیِ صریحِ مالک جلو می‌رود. `None` (بی‌رأی) با «رد» یکی نیست.
  ۳ `dry_run` پیش‌فرض **روشن** است — چرخه کامل می‌چرخد و هیچ merge نمی‌شود.
  ۴ merge علاوه بر رأی، به `OCTOPUS_DOCTOR_MAY_MERGE=1` هم نیاز دارد.
  ۵ حیاتی‌های خودِ دکتر با **منشأ** ثبت می‌شوند — چون از فردا درون‌زادند (‏R-07).

stdlib-only. تزریقِ وابستگی، تا کلِ حلقه بدونِ شبکه و بدونِ git تست شود.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from channel import Card, TelegramChannel

__all__ = ["Daemon", "Mission", "STATES"]

STATES = ("proposed", "running", "awaiting-merge", "merged", "rejected", "failed")


@dataclass
class Mission:
    mission_id: str
    title: str
    state: str = "proposed"
    risk: str = "medium"
    created: float = 0.0
    patch: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def open(self) -> bool:
        return self.state in ("proposed", "running", "awaiting-merge")

    def as_dict(self) -> dict:
        return {"schema": "doctor-mission.v1", **self.__dict__}


class Daemon:
    def __init__(self, ops: str | Path, vault_root: str | Path, *,
                 doctor=None, channel: TelegramChannel | None = None,
                 runner=None, scan_fn=None, dry_run: bool = True,
                 open_timeout_s: float | None = None):
        self.ops = Path(ops)
        self.root = Path(vault_root)
        self.state = self.root / "90-_meta" / "state"
        self.state.mkdir(parents=True, exist_ok=True)
        self.mfile = self.state / "missions.json"
        self.vitals_f = self.state / "doctor-vitals.json"
        self.dry_run = bool(dry_run)
        self.runner = runner
        self.channel = channel or TelegramChannel(self.state)
        if open_timeout_s is None:
            try:
                open_timeout_s = float(os.environ.get(
                    "OCTOPUS_DOCTOR_OPEN_TIMEOUT_S", str(7 * 86400)))
            except (TypeError, ValueError):
                open_timeout_s = 7 * 86400
        self.open_timeout_s = float(open_timeout_s)
        if doctor is None:
            from diagnose import Doctor                          # noqa: PLC0415
            doctor = Doctor(self.root)
        self.doctor = doctor
        if scan_fn is None:
            from scanner import scan                             # noqa: PLC0415
            scan_fn = scan
        self.scan_fn = scan_fn
        from mind import Mind                                    # noqa: PLC0415
        self.mind = Mind(self.state)

    # ------------------------------------------------------------ missions
    _FIELDS = ("mission_id", "title", "state", "risk", "created", "patch", "notes")

    def missions(self) -> list[Mission]:
        """بارگذاریِ مقاوم. کلیدِ ناشناخته (مثلِ `schema`) ماموریت‌ها را دور نمی‌ریزد —
        یک‌بار این باگ باعث شد کلِ حلقه بی‌حافظه شود و هر چرخه از صفر شروع کند."""
        try:
            rows = json.loads(self.mfile.read_text("utf-8"))
        except (OSError, ValueError):
            return []
        out = []
        for d in rows if isinstance(rows, list) else []:
            if isinstance(d, dict) and d.get("mission_id"):
                out.append(Mission(**{k: v for k, v in d.items() if k in self._FIELDS}))
        return out

    def _save(self, ms: list[Mission]) -> None:
        self.mfile.write_text(json.dumps([m.as_dict() for m in ms],
                                         ensure_ascii=False, indent=2), encoding="utf-8")

    def open_mission(self) -> Mission | None:
        return next((m for m in self.missions() if m.open), None)

    # --------------------------------------------------------------- cycle
    def cycle(self, now: float | None = None) -> dict:
        """یک پاسِ کاملِ **غیرمسدودکننده**. هر بار صدا زده شود، حلقه یک قدم جلو می‌رود."""
        now = now or time.time()
        log: list[str] = []
        ms = self.missions()

        # ۱ — چشم (فقط‌خواندنی) و ورودِ والت
        scan = self.scan_fn(self.ops, run_suite=False)
        if not scan.get("metrics"):
            log.append("⛔ ارگانیسم خوانده نشد — چرخه متوقف")
            return self._out(log, ms, scan, now)
        try:
            from ingest import ingest_scan                       # noqa: PLC0415
            from vault import Vault                              # noqa: PLC0415
            wrote = ingest_scan(Vault(self.root), scan)
            log.append(f"والت: {len(wrote['written'])} نوت · "
                       f"{len(wrote['flagged_metrics'])} سنجهٔ درون‌زاد flag شد")
        except Exception as e:                                   # noqa: BLE001
            log.append(f"ورودِ والت شکست خورد: {type(e).__name__}")

        # ۱٫۵ — خوراندنِ اپیزود به لایه‌های فکر (L1 ⟶ L2)
        from mind import Episode                                 # noqa: PLC0415
        for f in (scan.get("findings") or []):
            self.mind.perceive(Episode(now, "finding", f.get("title", ""),
                                       actor="scanner", outcome="red",
                                       exogenous=True))

        # ۲ — رأی‌های تازه (رأیِ انسان = برون‌زادترین شاهدی که داریم)
        for v in self.channel.votes():
            ms = self._apply_vote(ms, v, log)
            t = next((x.title for x in ms if x.mission_id == v.mission_id), v.mission_id)
            self.mind.perceive(Episode(v.ts or now, "verdict", t, actor="owner",
                                       outcome="approved" if v.approved else "rejected",
                                       exogenous=True))

        # ۳ — پیشبردِ ماموریتِ باز
        ms = self._advance(ms, log)

        # ۳.۵ — یک ماموریتِ باز + timeout (S-D01). بن‌بست awaiting-merge را می‌شکند.
        ms = self._expire_stale(ms, now, log)

        # ۴ — اگر هیچ ماموریتِ بازی نیست و شاهدِ نو هست ⇒ پیشنهادِ تازه
        if not any(m.open for m in ms):
            ms = self._maybe_propose(ms, scan, log)
        else:
            log.append(f"ماموریتِ باز: {self.open_mission().mission_id} — "
                       "پیشنهادِ نو ساخته نمی‌شود (انضباطِ ۱)")

        # ۵ — تأمل: اپیزودها ⟶ الگو ⟶ کهن‌الگو (L2 ⟶ L3 ⟶ L4)
        try:
            mind_report = self.mind.reflect(now)
            if mind_report["archetypes_voting"]:
                log.append(f"ناخودآگاه: {mind_report['archetypes_voting']} کهن‌الگوی "
                           f"رأی‌دار · {mind_report['archetypes_muted']} ساکت")
            if mind_report["shadow"]:
                log.append(f"سایه: {len(mind_report['shadow'])} مضمونِ تکراریِ ردشده")
        except Exception as e:                                   # noqa: BLE001
            mind_report = {"error": type(e).__name__}
            log.append(f"تأمل شکست خورد: {type(e).__name__}")

        self._save(ms)
        out = self._out(log, ms, scan, now)
        out["mind"] = mind_report
        return out

    # ---------------------------------------------------------------- vote
    def _apply_vote(self, ms: list[Mission], v, log: list[str]) -> list[Mission]:
        m = next((x for x in ms if x.mission_id == v.mission_id), None)
        if m is None or not m.open:
            return ms
        if v.gate == "intent" and m.state == "proposed":
            m.state = "running" if v.approved else "rejected"
            log.append(f"رأیِ نیت روی {m.mission_id}: {'✅' if v.approved else '❌'}")
            if m.state == "rejected":
                self._ingest_outcome(m, log)
        elif v.gate == "diff" and m.state == "awaiting-merge":
            if not v.approved:
                m.state = "rejected"
                log.append(f"رأیِ دیف روی {m.mission_id}: ❌ — worktree پاک، صفر اثر")
                self._ingest_outcome(m, log)
            else:
                m.state = self._merge(m, log)
        return ms

    # ---------------------------------------------------------- procedural
    def _ingest_outcome(self, m: Mission, log: list[str]) -> None:
        """۲۰۲۶-۰۸-۰۶ (دیپ‌اسکنِ RAG/حافظه): تا این خط، دکتر «چی خراب بود» را یاد
        می‌گرفت (ingest.py → یافته‌ها) ولی هرگز «چی امتحان کردیم که درست/غلط شد»
        را — چون نتیجهٔ نهاییِ ماموریت فقط در `missions.json` زیرِ `90-_meta`
        می‌ماند، پوشه‌ای که `Vault.load()` عمداً رد می‌کند (vault.py:88-89).
        این متد وقتی ماموریتی به حالتِ پایانی می‌رسد (merged/rejected/failed) یک
        نوتِ رویه‌ای می‌نویسد تا `diagnose.bundle()` بعداً آن را ببیند. فقط
        `daemon.py` تغییر کرد — `vault.py`/`ingest.py`/`propose.py` دست‌نخورده."""
        try:
            from vault import Vault  # noqa: PLC0415
            vault = Vault(self.root)
            body = ([f"# {m.mission_id} — {m.title} ({m.state})", "",
                     f"- **ریسک:** {m.risk}", "- **یادداشت‌ها:**"]
                    + [f"  - {n}" for n in m.notes]
                    + ["", "---", "[[MOC-اسکن‌ها]]"])
            vault.write(f"70-نسخه‌ها/{m.mission_id}.md",
                       {"type": "mission-outcome", "mission_id": m.mission_id,
                        "state": m.state, "risk": m.risk, "tags": ["ماموریت"]},
                       "\n".join(body))
        except Exception as e:  # noqa: BLE001 — ثبتِ رویه‌ای هرگز چرخه را نمی‌کشد
            log.append(f"ثبتِ رویه‌ایِ {m.mission_id} شکست خورد: {type(e).__name__}")

    def _merge(self, m: Mission, log: list[str]) -> str:
        if self.dry_run:
            m.notes.append("dry_run — merge انجام نشد")
            log.append(f"✅ رأیِ دیف روی {m.mission_id} ولی dry_run روشن است ⇒ merge نشد")
            return "awaiting-merge"
        if os.environ.get("OCTOPUS_DOCTOR_MAY_MERGE") != "1":
            m.notes.append("OCTOPUS_DOCTOR_MAY_MERGE=1 نیست")
            log.append(f"✅ رأی گرفت ولی flagِ merge خاموش است ⇒ {m.mission_id} منتظر ماند")
            return "awaiting-merge"
        if self.runner is None:
            m.notes.append("runner تزریق نشده")
            return "awaiting-merge"
        try:
            ps = self._patchset(m)
            res = self.runner.merge(m.mission_id, ps.as_apply(),      # type: ignore[attr-defined]
                                    files=sorted({p.file for p in ps.patches}))
            m.notes.append(f"commit={(res or {}).get('commit', '?')}")
            log.append(f"🎉 {m.mission_id} merge شد — {(res or {}).get('commit', '?')}")
            m.state = "merged"
            self._ingest_outcome(m, log)
            return "merged"
        except Exception as e:                                   # noqa: BLE001
            m.notes.append(f"merge شکست: {type(e).__name__}: {e}")
            log.append(f"⛔ merge شکست خورد: {m.mission_id}")
            m.state = "failed"
            self._ingest_outcome(m, log)
            return "failed"

    @staticmethod
    def _patchset(m: Mission):
        from propose import Patch, PatchSet                      # noqa: PLC0415
        return PatchSet(m.mission_id, m.title, m.patch.get("rationale", ""),
                        [Patch(**p) for p in m.patch.get("patches", [])],
                        risk=m.risk, rollback=m.patch.get("rollback", ""))

    # ------------------------------------------------------------- advance
    def _advance(self, ms: list[Mission], log: list[str]) -> list[Mission]:
        m = next((x for x in ms if x.state == "running"), None)
        if m is None:
            return ms
        if self.runner is None:
            m.notes.append("runner تزریق نشده — ماموریت اجرا نشد")
            log.append(f"{m.mission_id}: runner نیست، در حالتِ running ماند")
            return ms
        try:
            res = self.runner.run(m.mission_id, self._patchset(m).as_apply())
        except Exception as e:                                   # noqa: BLE001
            m.state = "failed"
            m.notes.append(f"{type(e).__name__}: {e}")
            log.append(f"⛔ {m.mission_id} در اجرا شکست خورد: {type(e).__name__}")
            self._ingest_outcome(m, log)
            return ms
        card_text = res.card()
        if getattr(res, "may_merge", False):
            m.state = "awaiting-merge"
            log.append(f"{m.mission_id}: سوئیت سبز ⇒ کارتِ دیف فرستاده شد")
            self.channel.send(Card(m.mission_id, "diff", card_text))
        else:
            m.state = "failed"
            m.notes.append("سوئیت سبز نشد یا درختِ زنده تغییر کرد")
            self._ingest_outcome(m, log)
            log.append(f"⛔ {m.mission_id}: کارتِ قرمز — merge ممنوع")
            self.channel.send(Card(m.mission_id, "diff", card_text, buttons=False))
        return ms

    def _expire_stale(self, ms: list[Mission], now: float, log: list[str]) -> list[Mission]:
        """S-D01: one open mission + timeout. created<=0 is not expired (unknown age)."""
        timeout = self.open_timeout_s
        if timeout <= 0:
            return ms
        for m in ms:
            if not m.open or not m.created:
                continue
            try:
                age = now - float(m.created)
            except (TypeError, ValueError):
                continue
            if age >= timeout:
                m.state = "failed"
                m.notes.append(
                    f"quarantine: open-mission timeout after {int(age)}s "
                    f"(limit {int(timeout)}s) — slot freed")
                log.append(f"⌛ {m.mission_id} timeout age_s={int(age)}")
                self._ingest_outcome(m, log)
        return ms

    # ------------------------------------------------------------- propose
    def _maybe_propose(self, ms: list[Mission], scan: dict, log: list[str]) -> list[Mission]:
        auto = scan.get("findings") or []
        done = {m.mission_id for m in ms}
        if not auto:
            log.append("هیچ یافتهٔ خودکارِ تازه‌ای نیست — سکوت")
            return ms
        goal = ("مهم‌ترین یافتهٔ امروز را با یک تغییرِ کوچک و افزایشی درمان کن: "
                + " · ".join(f["title"] for f in auto[:3]))
        ps, why, used = self.doctor.propose(goal)
        if ps is None:
            log.append("پیشنهاد ساخته نشد: " + " · ".join(why[:2]))
            return ms
        if ps.empty:
            log.append("مغز صادقانه گفت شاهد کافی ندارد — پیشنهادی نداد")
            return ms
        if ps.mission_id in done:
            log.append(f"{ps.mission_id} قبلاً وجود دارد — تکرار نمی‌شود")
            return ms
        m = Mission(ps.mission_id, ps.title, "proposed", ps.risk, time.time(),
                    {"rationale": ps.rationale, "rollback": ps.rollback,
                     "patches": [p.__dict__ for p in ps.patches], "evidence": used})
        ms.append(m)
        self.channel.send(Card(ps.mission_id, "intent", ps.card()))
        log.append(f"📩 کارتِ نیت برای {ps.mission_id} در صف/ارسال")
        return ms

    # -------------------------------------------------------------- request
    def request(self, goal: str, actor: str = "owner") -> dict:
        """ماموریتی که **تو** خواسته‌ای — نه چیزی که دکتر خودش دیده.

        این مسیرِ «در تلگرام می‌نویسم، اختاپوس می‌سازد» است. همان دو گیت را دارد؛
        تنها تفاوتش این است که سایه جلویش را نمی‌گیرد — چون مالک صریحاً گفته.
        ولی اگر سایه مخالف باشد، **به تو می‌گوید** که قبلاً چند بار ردش کرده‌ای.
        """
        ms = self.missions()
        if any(m.open for m in ms):
            return {"ok": False, "why": f"ماموریتِ باز هست: {self.open_mission().mission_id}"}

        warn = ""
        try:
            n = self.mind.cu.shadow.rejected_count(goal)
            if n >= 2:
                warn = f"⚠️ چیزی شبیه این را {n} بار رد کرده‌ای — این بار مطمئنی؟"
        except Exception:                                        # noqa: BLE001
            pass

        ps, why, used = self.doctor.propose(goal)
        if ps is None:
            return {"ok": False, "why": " · ".join(why)}
        if ps.empty:
            return {"ok": False, "why": "مغز شاهد کافی نداشت — پیشنهادی نداد",
                    "rationale": ps.rationale}
        m = Mission(ps.mission_id, ps.title, "proposed", ps.risk, time.time(),
                    {"rationale": ps.rationale, "rollback": ps.rollback,
                     "patches": [p.__dict__ for p in ps.patches], "evidence": used,
                     "requested_by": actor, "goal": goal})
        ms.append(m)
        self._save(ms)
        self.channel.send(Card(ps.mission_id, "intent",
                               (warn + "\n\n" if warn else "") + ps.card()))
        return {"ok": True, "mission_id": ps.mission_id, "warn": warn,
                "files": sorted({p.file for p in ps.patches}),
                "creates": sorted({p.file for p in ps.patches if p.create})}

    # -------------------------------------------------------------- vitals
    def vitals(self, ms: list[Mission] | None = None) -> dict:
        """حیاتی‌های **خودِ دکتر**، با منشأ — چون از فردا عضوِ ارگانیسم است (‏R-07).

        فقط رأیِ مالک و کدِ خروجیِ سوئیت برون‌زادند: هر دو بیرونِ دکتر تولید می‌شوند و
        اگر دکتر بمیرد هم وجود دارند. بقیه درون‌زادند و حق رأی در فیتنسِ اختاپوس ندارند.
        """
        ms = ms if ms is not None else self.missions()
        votes = self.channel.votes()
        return {
            "missions_total":   {"value": len(ms), "provenance": "درون‌زاد"},
            "missions_open":    {"value": sum(1 for m in ms if m.open),
                                 "provenance": "درون‌زاد"},
            "missions_merged":  {"value": sum(1 for m in ms if m.state == "merged"),
                                 "provenance": "برون‌زاد",
                                 "receipt": "git log — کامیت واقعی، نه ادعا"},
            "owner_approvals":  {"value": sum(1 for v in votes if v.approved),
                                 "provenance": "برون‌زاد", "receipt": "رأیِ انسان"},
            "owner_rejections": {"value": sum(1 for v in votes if not v.approved),
                                 "provenance": "برون‌زاد", "receipt": "رأیِ انسان"},
            "cards_pending":    {"value": self.channel.pending(), "provenance": "درون‌زاد"},
            "channel":          self.channel.health(),
            "dry_run":          self.dry_run,
        }

    # ----------------------------------------------------------------- out
    def _out(self, log: list[str], ms: list[Mission], scan: dict, now: float) -> dict:
        v = self.vitals(ms)
        try:
            self.vitals_f.write_text(json.dumps(
                {"ts": now, "schema": "doctor-vitals.v1", **v},
                ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
        return {"log": log, "beat": scan.get("beat"),
                "findings": len(scan.get("findings") or []),
                "unknown": scan.get("unknown") or [],
                "missions": [m.as_dict() for m in ms], "vitals": v}
