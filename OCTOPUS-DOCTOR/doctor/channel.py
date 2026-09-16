#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""channel.py — صدای دکتر در تلگرام.

مسئلهٔ واقعی که این ماژول حل می‌کند **ارسالِ پیام نیست** — ارسال ساده است.
مسئله این است: اختاپوس همین حالا یک poller زنده دارد. اگر دکتر روی همان توکن
`getUpdates` بزند، **آپدیت‌ها را از او می‌دزدد** و باتِ اصلی کور می‌شود، بی‌سروصدا.

پس دو حالت داریم، و انتخابش دستِ محیط است نه حدسِ کد:

    OUTBOX  (پیش‌فرض، صفرریسک) — دکتر کارت را در صف می‌نویسد؛ **پروسهٔ زندهٔ موجود**
            آن را می‌فرستد و رأی را در صفِ ورودی برمی‌گرداند. هیچ اتصالِ دومی نیست.

    DIRECT  — دکتر خودش می‌فرستد و می‌خواند. **فقط** وقتی مجاز است که توکن مالِ خودش
            باشد (باتِ دوم) و قفل را گرفته باشد. `getUpdates` بدونِ هر دو شرط،
            استثنا می‌دهد — نه هشدار، نه تلاشِ محتاطانه. استثنا.

سه قاعدهٔ دیگر که در کد اجرا می‌شوند:
  · توکن هرگز چاپ/لاگ نمی‌شود — فقط اثرِ انگشتِ ۱۲ کاراکتریِ SHA-256
  · فقط `OCTOPUS_OWNER_ID` حق رأی دارد؛ رأیِ دیگران ثبت و بی‌اثر می‌شود
  · هر رأی **یک بار** اعمال می‌شود؛ تکرارِ همان callback بی‌اثر است

stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["TelegramChannel", "Vote", "Card", "ChannelError",
           "HttpTransport", "mask", "MODE_OUTBOX", "MODE_DIRECT"]

MODE_OUTBOX = "outbox"
MODE_DIRECT = "direct"
API = "https://api.telegram.org"


class ChannelError(RuntimeError):
    pass


def mask(token: str | None) -> str:
    """اثرِ انگشتِ توکن. خودِ توکن هرگز از این تابع بیرون نمی‌آید."""
    if not token:
        return "—"
    return "tg:" + hashlib.sha256(token.encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Card:
    mission_id: str
    gate: str                    # "intent" | "diff"
    text: str
    buttons: bool = True

    def payload(self, chat_id: str, topic_id: int | None) -> dict:
        d: dict = {"chat_id": chat_id, "text": self.text,
                   "parse_mode": "Markdown", "disable_web_page_preview": True}
        if topic_id:
            d["message_thread_id"] = int(topic_id)
        if self.buttons:
            d["reply_markup"] = {"inline_keyboard": [[
                {"text": "✅ تأیید", "callback_data": f"ok:{self.gate}:{self.mission_id}"},
                {"text": "❌ رد",    "callback_data": f"no:{self.gate}:{self.mission_id}"},
            ]]}
        return d


@dataclass(frozen=True)
class Vote:
    mission_id: str
    gate: str
    approved: bool
    voter_id: int
    callback_id: str
    ts: float = 0.0

    @classmethod
    def parse(cls, cb: dict) -> "Vote | None":
        data = str((cb or {}).get("data", ""))
        parts = data.split(":")
        if len(parts) != 3 or parts[0] not in ("ok", "no"):
            return None
        return cls(mission_id=parts[2], gate=parts[1], approved=parts[0] == "ok",
                   voter_id=int(((cb.get("from") or {}).get("id")) or 0),
                   callback_id=str(cb.get("id", "")), ts=time.time())


class HttpTransport:
    """urllib خالص. تنها جایی که واقعاً به شبکه دست می‌زند."""

    def __init__(self, token: str, timeout: float = 40.0):
        self._t = token
        self.timeout = timeout

    def post(self, method: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{API}/bot{self._t}/{method}", data=body, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # ⛔ متنِ خطا ممکن است URL را با توکن داخلش echo کند
            raise ChannelError(f"{method} ⇒ HTTP {e.code}") from None
        except Exception as e:                                   # noqa: BLE001
            raise ChannelError(f"{method} ⇒ {type(e).__name__}") from None


class TelegramChannel:
    def __init__(self, state_dir: Path | str, *,
                 token_env: str = "OCTOPUS_DOCTOR_BOT_TOKEN",
                 chat_id: str | None = None,
                 topic_id: int | None = None,
                 owner_id: int | None = None,
                 mode: str | None = None,
                 transport=None):
        self.state = Path(state_dir)
        self.state.mkdir(parents=True, exist_ok=True)
        self.token_env = token_env
        self.chat_id = chat_id or os.environ.get("OCTOPUS_DOCTOR_CHAT_ID", "")
        self.topic_id = topic_id or (int(os.environ["OCTOPUS_DOCTOR_TOPIC_ID"])
                                     if os.environ.get("OCTOPUS_DOCTOR_TOPIC_ID") else None)
        self.owner_id = int(owner_id or os.environ.get("OCTOPUS_OWNER_ID", "0") or 0)
        self.mode = (mode or os.environ.get("OCTOPUS_DOCTOR_TG_MODE", MODE_OUTBOX)).lower()
        self._transport = transport
        # transportِ تزریق‌شده = تستِ دوبل، یا کلاینتِ خودِ پروسهٔ زنده. در هر دو حالت
        # ما توکن را در دست نداریم و **نباید** داشته باشیم؛ ولی هویتِ قفل لازم است.
        self._injected = transport is not None
        self.outbox = self.state / "tg-outbox.jsonl"
        self.inbox = self.state / "tg-inbox.jsonl"
        self.seen_f = self.state / "tg-seen.json"
        self.lock_f = self.state / "tg-poll.lock"
        self.offset_f = self.state / "tg-offset.json"

    # ------------------------------------------------------------- identity
    @property
    def token(self) -> str | None:
        return (os.environ.get(self.token_env) or "").strip() or None

    @property
    def fingerprint(self) -> str:
        if self.token:
            return mask(self.token)
        return "tg:injected" if self._injected else "—"

    @property
    def transport(self):
        if self._transport is not None:
            return self._transport
        if not self.token:
            raise ChannelError(f"{self.token_env} تنظیم نیست — fail-closed")
        self._transport = HttpTransport(self.token)
        return self._transport

    def health(self) -> dict:
        """وضعیت، **بدونِ** هیچ رازی. برای کارتِ تشخیص و لاگ."""
        return {"mode": self.mode, "token_env": self.token_env,
                "token": self.fingerprint, "chat_id": bool(self.chat_id),
                "topic_id": self.topic_id, "owner_set": bool(self.owner_id),
                "may_poll": self._may_poll()[0], "why": self._may_poll()[1],
                "outbox_pending": self.pending()}

    # ---------------------------------------------------------------- send
    def send(self, card: Card) -> dict:
        """در حالتِ outbox فقط صف می‌نویسد. در حالتِ direct واقعاً می‌فرستد.

        ارسال هرگز آپدیتی مصرف نمی‌کند ⇒ در هر دو حالت با poller زنده تداخل ندارد.
        """
        rec = {"ts": time.time(), "mission_id": card.mission_id, "gate": card.gate,
               "payload": card.payload(self.chat_id, self.topic_id)}
        if self.mode != MODE_DIRECT:
            self._append(self.outbox, rec)
            return {"queued": True, "mode": self.mode}
        if not self.chat_id:
            raise ChannelError("chat_id تنظیم نیست")
        res = self.transport.post("sendMessage", rec["payload"])
        rec["result_ok"] = bool(res.get("ok"))
        self._append(self.outbox, rec)              # رسید، حتی وقتی مستقیم رفت
        return res

    def pending(self) -> int:
        """کارت‌هایی که هنوز رأی نگرفته‌اند."""
        voted = {v.mission_id + ":" + v.gate for v in self.votes()}
        sent = {r["mission_id"] + ":" + r["gate"] for r in self._read(self.outbox)}
        return len(sent - voted)

    # ---------------------------------------------------------------- poll
    def _may_poll(self) -> tuple[bool, str]:
        if self.mode != MODE_DIRECT:
            return False, f"حالتِ {self.mode} — خواندن کارِ پروسهٔ زنده است"
        if os.environ.get("OCTOPUS_DOCTOR_OWNS_POLLING") != "1":
            return False, "OCTOPUS_DOCTOR_OWNS_POLLING=1 نیست — توکن مالِ دکتر اعلام نشده"
        if not self.token and not self._injected:
            return False, f"{self.token_env} تنظیم نیست"
        try:
            lk = json.loads(self.lock_f.read_text("utf-8"))
            if lk.get("token") != self.fingerprint:
                return False, "قفل مالِ توکنِ دیگری است — دو poller روی یک توکن ممنوع"
            if lk.get("pid") not in (os.getpid(), None) and \
                    time.time() - float(lk.get("ts", 0)) < 300:
                return False, f"قفلِ زنده از pid={lk.get('pid')}"
        except (OSError, ValueError):
            pass
        return True, "ok"

    def acquire_poll_lock(self) -> None:
        self.lock_f.write_text(json.dumps(
            {"pid": os.getpid(), "token": self.fingerprint, "ts": time.time()}),
            encoding="utf-8")

    def poll_votes(self, timeout: int = 25) -> list[Vote]:
        """⛔ فقط وقتی توکن مالِ خودِ دکتر است. وگرنه استثنا — نه تلاشِ محتاطانه."""
        ok, why = self._may_poll()
        if not ok:
            raise ChannelError(f"getUpdates ممنوع: {why}")
        self.acquire_poll_lock()
        off = 0
        try:
            off = int(json.loads(self.offset_f.read_text("utf-8")).get("offset", 0))
        except (OSError, ValueError):
            pass
        res = self.transport.post("getUpdates", {
            "timeout": timeout, "offset": off or None,
            "allowed_updates": ["callback_query"]})
        out: list[Vote] = []
        last = off
        for up in (res.get("result") or []):
            last = max(last, int(up.get("update_id", 0)) + 1)
            v = Vote.parse(up.get("callback_query") or {})
            if v:
                out.append(v)
        self.offset_f.write_text(json.dumps({"offset": last}), encoding="utf-8")
        return self.accept(out)

    # ---------------------------------------------------------------- votes
    def accept(self, votes: list[Vote]) -> list[Vote]:
        """گیتِ مالک + ضدِ تکرار. هر دو **در کد**، نه در اعتماد."""
        seen = self._seen()
        kept: list[Vote] = []
        for v in votes:
            if self.owner_id and v.voter_id != self.owner_id:
                self._append(self.inbox, {**v.__dict__, "ignored": "غیرِ مالک"})
                continue
            if v.callback_id and v.callback_id in seen:
                continue
            seen.add(v.callback_id)
            self._append(self.inbox, v.__dict__)
            kept.append(v)
        self.seen_f.write_text(json.dumps(sorted(seen)), encoding="utf-8")
        return kept

    def ingest_external(self, raw: list[dict]) -> list[Vote]:
        """رأی‌هایی که **پروسهٔ زنده** جمع کرده و به ما داده — حالتِ outbox."""
        vs = [v for v in (Vote.parse(c) for c in raw) if v]
        return self.accept(vs)

    def votes(self) -> list[Vote]:
        out = []
        for r in self._read(self.inbox):
            if r.get("ignored"):
                continue
            try:
                out.append(Vote(r["mission_id"], r["gate"], bool(r["approved"]),
                                int(r["voter_id"]), str(r["callback_id"]),
                                float(r.get("ts", 0))))
            except (KeyError, ValueError, TypeError):
                continue
        return out

    def verdict(self, mission_id: str, gate: str) -> bool | None:
        """آخرین رأیِ معتبر. `None` = هنوز رأی نداده — و این با «رد» یکی نیست."""
        vs = [v for v in self.votes() if v.mission_id == mission_id and v.gate == gate]
        return vs[-1].approved if vs else None

    # ------------------------------------------------------------------ io
    def _seen(self) -> set[str]:
        try:
            return set(json.loads(self.seen_f.read_text("utf-8")))
        except (OSError, ValueError):
            return set()

    def _append(self, p: Path, rec: dict) -> None:
        try:
            with p.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    @staticmethod
    def _read(p: Path) -> list[dict]:
        try:
            return [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]
        except (OSError, ValueError):
            return []
