#!/usr/bin/env python3
"""
brain/telegram_bot_unified.py — باتِ تلگرامِ یکپارچهٔ OCTOPUS.

هدف: دو رابطِ تلگرامِ مجزا (4d_system brain + _ops approval) را در یک باتِ واحد ادغام کند.
(CH-04: Telegram bot unify → 4d_system/brain/telegram_bot_unified.py)

قابلیت‌ها:
  • /status_brain /goal /pending /pause /resume /portrait — مغز (4d_system)
  • /start /overview /money /doctor /brain /blueprint /school /safety /alerts /queue
    /lead /stop /status — ارگانیسم (_ops)
  • /u /unified — وضعیتِ یکپارچه (ادغامِ organism + brain)
  • callback دکمه‌ها: approve/reject proposals (brain) + approve/deny effects (_ops)
  • event emission به هر دو سیستم (brain/events.py + _ops/events.py)
  • long-polling استاندارد (no webhook) — $0-idle

security:
  • فقط TELEGRAM_CHAT_IDِ مالک → هر پیامِ دیگر نادیده
  • token فقط از env (TELEGRAM_BOT_TOKEN) — هرگز hardcode
  • HTTP = stdlib-only (urllib) — همان الگوی approval_channel.py
  • URL/token هرگز لاگ/echo نمی‌شود
  • fail-soft: خطای هر update = skip + log، نه crash

اجرا:
    python -m brain.telegram_bot_unified
    # یا
    python 4d_system/brain/telegram_bot_unified.py

وابستگی‌ها:
    • استاندارد کتابخانهٔ Python (urllib, json, logging, threading, …)
    • approval_channel_merge.py (در _ops/budget/)
    • (optional) brain/self_code.py برای approve/reject proposals
    • (optional) brain/daemon.py برای pause/resume
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Any

# ── bootstrap مسیر ─────────────────────────────────────────────────────────
_4D_ROOT = Path(__file__).resolve().parent.parent
_OPS_ROOT = _4D_ROOT.parent / "_ops"
_OPS_BUDGET = _OPS_ROOT / "budget"

if str(_OPS_BUDGET) not in sys.path:
    sys.path.insert(0, str(_OPS_BUDGET))

if str(_4D_ROOT / "brain") not in sys.path:
    sys.path.insert(0, str(_4D_ROOT / "brain"))

# approval_channel_merge را وارد کن (آن خودش TelegramApprovalChannel را می‌آورد)
from approval_channel_merge import (
    UnifiedApprovalChannel,
    _load_offset,
    _save_offset,
    _mask_token,
    TELEGRAM_API_BASE,
)

logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────
API = "https://api.telegram.org/bot{token}/{method}"
DEFAULT_LONGPOLL_TIMEOUT = 30
OWNER_ENV = "TELEGRAM_CHAT_ID"
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"

# مسیرِ offset persistence (restart-safe)
OFFSET_PATH = _4D_ROOT / "outputs" / "telegram_unified_offset.json"

# ── config helpers ─────────────────────────────────────────────────────────


def _env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def is_configured() -> bool:
    return bool(_env_str(TOKEN_ENV) and _env_str(OWNER_ENV))


def _owner_id() -> int | None:
    v = _env_str(OWNER_ENV)
    if v:
        try:
            return int(v)
        except ValueError:
            pass
    return None


def _token() -> str:
    return _env_str(TOKEN_ENV, "")


# ── HTTP helpers (stdlib-only) ─────────────────────────────────────────────


def _http_get(url: str, timeout_s: float) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-unified/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s + 5) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _http_post(url: str, body: dict, timeout_s: float = 10.0) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "octopus-unified/0.1",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


# ─── UnifiedBot: wrapper + long-poll loop ─────────────────────────────────


class UnifiedBot:
    """باتِ تلگرامِ یکپارچهٔ OCTOPUS.

    این کلاس یک نمونهٔ UnifiedApprovalChannel نگه می‌دارد و حلقهٔ long-pollِ اختصاصی‌اش
    را اجرا می‌کند. offset persistence در ۴d_system/outputs ذخیره می‌شود (جدا از _ops/state
    تا هر دو نمونه بتوانند مستقل اجرا شوند، ولی در عمل فقط یکی اجرا می‌شود).
    """

    def __init__(
        self,
        token: str | None = None,
        owner_chat_id: int | None = None,
        longpoll_timeout: int | None = None,
    ):
        self._token = token if token is not None else _token()
        self._owner = (
            int(owner_chat_id) if owner_chat_id is not None else (_owner_id() or None)
        )
        self._lp = int(
            longpoll_timeout
            if longpoll_timeout is not None
            else _env_int("TELEGRAM_LONGPOLL_TIMEOUT", DEFAULT_LONGPOLL_TIMEOUT)
        )
        self._offset: int = self._load_offset()
        self._stop = False
        self._lk = Lock()

        # کانالِ یکپارچهٔ _ops/brain
        self._channel = UnifiedApprovalChannel(
            token=self._token,
            owner_chat_id=self._owner,
            http_get=_http_get,
            http_post=_http_post,
            longpoll_timeout=self._lp,
            # state_dir: _ops/state برای approval_channel، offset اما اینجا manage می‌شود
            state_dir=str(_OPS_ROOT / "state"),
        )

        # ثبتِ callbacks مغز (optional — اگر daemon/self_code در دسترس باشند)
        self._register_brain_callbacks()

    def _register_brain_callbacks(self) -> None:
        """اگر مغز در دسترس است، callbacks pause/resume را ثبت کن."""
        try:
            from brain.daemon import _pause_path

            def _set_pause(on: bool) -> None:
                p = _pause_path()
                if on:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("paused", encoding="utf-8")
                elif p.exists():
                    p.unlink()

            self._channel.register_brain_callback("pause", _set_pause)
            self._channel.register_brain_callback("resume", _set_pause)
        except Exception:
            pass

    # ── offset persistence (restart-safe) ─────────────────────────────────
    def _load_offset(self) -> int:
        try:
            if OFFSET_PATH.exists():
                d = json.loads(OFFSET_PATH.read_text("utf-8"))
                return int(d.get("offset", 0))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
        return 0

    def _save_offset(self) -> None:
        try:
            OFFSET_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = OFFSET_PATH.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(
                    {"offset": self._offset, "saved_at": _now_iso()},
                    ensure_ascii=False,
                ),
                "utf-8",
            )
            tmp.replace(OFFSET_PATH)
        except OSError:
            pass

    # ── build URL (secret-safe) ───────────────────────────────────────────
    def _url(self, method: str, params: dict | None = None) -> str:
        q = urllib.parse.urlencode(params or {})
        return f"{TELEGRAM_API_BASE}/bot{self._token}/{method}?{q}"

    # ── send helpers ───────────────────────────────────────────────────────
    def send_text(
        self, text: str, reply_markup: dict | None = None, parse_mode: str = "HTML"
    ) -> bool:
        if not self._token or self._owner is None:
            return False
        body = {
            "chat_id": self._owner,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            body["reply_markup"] = reply_markup
        try:
            self._http_post(self._url("sendMessage"), body)
            return True
        except Exception as e:
            logger.warning("send_text failed: %s", type(e).__name__)
            return False

    # ─── poll once ─────────────────────────────────────────────────────────
    def poll_once(self) -> int:
        """یک دورِ getUpdates + پردازش. تعداد updateهای پردازش‌شده را برمی‌گرداند."""
        if not self._token or self._owner is None:
            return 0
        if self._stop:
            return 0

        params = {
            "offset": self._offset,
            "timeout": self._lp,
            "allowed_updates": json.dumps(["message", "callback_query"]),
        }
        try:
            data = self._http_get(self._url("getUpdates", params), float(self._lp))
        except Exception as e:  # noqa: BLE001
            logger.debug("poll network error: %s", type(e).__name__)
            return 0

        if not isinstance(data, dict) or not data.get("ok"):
            # تشخیصِ 409 conflict (poller دوم)
            if isinstance(data, dict) and data.get("error_code") == 409:
                logger.warning(
                    "Telegram 409 Conflict — another poller is consuming updates!"
                )
            return 0

        processed = 0
        offset_dirty = False
        for upd in data.get("result", []):
            uid = upd.get("update_id")
            if isinstance(uid, int) and uid + 1 > self._offset:
                self._offset = uid + 1
                offset_dirty = True

            try:
                self._process_update(upd)
            except Exception as e:
                logger.error("update handling error: %s", e)

            processed += 1

        if offset_dirty:
            self._save_offset()
            # sync به approval_channel_merge (تا approval_channel هم از offset جدید بداند)
            try:
                self._channel._offset = self._offset
            except Exception:
                pass
        return processed

    def _process_update(self, upd: dict) -> None:
        """یک update را پردازش کن: message یا callback_query."""
        is_callback = "callback_query" in upd
        cbq = upd.get("callback_query") if is_callback else {}
        msg = upd.get("message") or cbq.get("message") or {}
        chat_id = msg.get("chat", {}).get("id") or cbq.get("message", {}).get("chat", {}).get("id")
        from_id = (msg.get("from") or cbq.get("from") or {}).get("id")
        cbq_id = cbq.get("id")

        # allowlist: فقط owner
        if chat_id != self._owner:
            return

        # quarantine (audit trail)
        try:
            self._quarantine_log(upd)
        except Exception:
            pass

        if is_callback:
            text = cbq.get("data") or ""
            reply = self._channel.dispatch_callback(str(text))
            if cbq_id:
                self._answer_callback(cbq_id, "✅")
            if isinstance(reply, dict):
                self.send_text(
                    reply.get("text", ""), reply_markup=reply.get("reply_markup")
                )
            elif reply:
                self.send_text(str(reply))
        else:
            text = msg.get("text") or ""
            reply = self._channel.handle_command(str(text))
            if reply is not None:
                if isinstance(reply, dict):
                    self.send_text(
                        reply.get("text", ""),
                        reply_markup=reply.get("reply_markup"),
                        parse_mode="HTML",
                    )
                else:
                    self.send_text(str(reply), parse_mode="HTML")

    def _answer_callback(self, callback_query_id: str, text: str = "") -> None:
        try:
            body = {
                "callback_query_id": callback_query_id,
                "text": str(text)[:200],
                "cache_time": 0,
            }
            self._http_post(self._url("answerCallbackQuery"), body)
        except Exception as e:
            logger.warning("answerCallbackQuery failed: %s", type(e).__name__)

    def _quarantine_log(self, upd: dict) -> None:
        """ثبتِ audit trail در outputs/telegram_quarantine.jsonl."""
        qpath = _4D_ROOT / "outputs" / "telegram_quarantine.jsonl"
        try:
            qpath.parent.mkdir(parents=True, exist_ok=True)
            rec = {
                "ts": _now_iso(),
                "update_id": upd.get("update_id"),
                "type": "callback_query" if "callback_query" in upd else "message",
            }
            with open(qpath, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    # ─── run loop ──────────────────────────────────────────────────────────
    def run(self) -> None:
        if not self._token or self._owner is None:
            print("🤖 باتِ یکپارچه تنظیم نشده — TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID را در .env بگذار.")
            return
        print("🤖 Unified Telegram Bot روشن شد. در تلگرام /start یا /u بزن. (Ctrl+C برای توقف)")
        # پیامِ خوش‌آمد + unified status
        try:
            greeting = (
                "🤖 <b>Unified OCTOPUS Bot</b> online.\n\n"
                + self._channel.status_report_v2()
            )
            self.send_text(greeting, reply_markup=self._channel.MENU_KEYBOARD)
        except Exception as e:
            logger.warning("startup greeting failed: %s", e)

        while not self._stop:
            try:
                self.poll_once()
            except KeyboardInterrupt:
                print("\n🛑 Unified Bot خاموش شد.")
                break
            except Exception as e:
                logger.error("poll loop error: %s", e)
                time.sleep(5)

    def stop(self) -> None:
        self._stop = True
        try:
            self._channel.stop()
        except Exception:
            pass

    # ─── HTTP post wrapper (for _url method) ───────────────────────────────
    def _http_post(self, url: str, body: dict, timeout: float = 10.0) -> dict:
        return _http_post(url, body, timeout)

    def _http_get(self, url: str, timeout: float) -> dict:
        return _http_get(url, timeout)


# ─── helpers ───────────────────────────────────────────────────────────────

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ─── event emission bridge ─────────────────────────────────────────────────

def emit_unified_event(
    event_name: str,
    agent_id: str,
    *,
    status: str = "ok",
    summary: str = "",
    next_action: str = "",
    approval_state: str = "unknown",
) -> None:
    """یک رویداد به هر دو event system بفرست (brain + _ops)."""
    # _ops/events.py
    try:
        sys.path.insert(0, str(_OPS_ROOT))
        import events as ops_events  # noqa: E402
        ops_events.emit(
            event_name,
            agent_id,
            status=status,
            summary=summary,
            next_action=next_action,
            approval_state=approval_state,
        )
    except Exception:
        pass
    # brain/events.py
    try:
        sys.path.insert(0, str(_4D_ROOT / "brain"))
        import events as brain_events  # noqa: E402
        brain_events.emit(
            event_name=event_name,
            agent_id=agent_id,
            status=status,
            summary=summary,
            next_action=next_action,
            approval_state=approval_state,
        )
    except Exception:
        pass


# ─── main entrypoint ───────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not is_configured():
        print("""
⚠️  تلگرام تنظیم نشده.

لطفاً این متغیرهای محیطی را set کن:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...

سپس اجرا کن:
  python -m brain.telegram_bot_unified
""")
        return
    bot = UnifiedBot()
    bot.run()


if __name__ == "__main__":
    main()
