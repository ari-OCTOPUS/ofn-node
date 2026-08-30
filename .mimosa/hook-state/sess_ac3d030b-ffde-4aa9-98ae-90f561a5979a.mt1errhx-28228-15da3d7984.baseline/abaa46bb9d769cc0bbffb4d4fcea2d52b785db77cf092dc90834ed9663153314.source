# -*- coding: utf-8 -*-
"""
OCTOPUS — Beat Ownership Lease
==============================

هدف: در هر لحظه دقیقاً یک میزبان حق beat زدن دارد.
Purpose: at any instant exactly ONE host is allowed to beat.

این ماژول تنها چیزی است که بین «یک ارگانیسم» و «دو ارگانیسم موازی که هر دو
بودجه خرج می‌کنند» ایستاده است. طبق INV-8 fail-closed است: هر خطا،
هر ابهام، هر تأخیر مشکوک → از دست دادن مالکیت، نه ادامه دادن.

Fencing SoT for migration. The HMAC prototype in
`_ops/octopus_v3/beat_lease.py` does not increment a token on renew and
must not be wired. organism.py / chrono.py are NOT imported here.

Design contract
---------------
1. FENCING TOKEN. هر lease یک revision یکنواخت‌صعودی دارد. هر نوشتنی به
   state/ledger/budget باید token را همراه ببرد. نویسندهٔ قدیمی که از خواب
   بیدار شده، token کهنه دارد و نوشتنش رد می‌شود. TTL به‌تنهایی کافی نیست —
   یک پروسهٔ pause شده می‌تواند بعد از انقضا بیدار شود و بنویسد.
2. MONOTONIC CLOCK محلی برای تصمیم «آیا هنوز مالکم؟». ساعت دیواری فقط برای
   نمایش و برای مقایسه بین میزبان‌ها با حاشیهٔ اطمینان.
3. SAFETY MARGIN. مالک قبل از انقضای واقعی «خودش را بازنشسته می‌کند» تا
   هرگز پنجره‌ای نباشد که دو نفر خود را مالک بدانند.
4. FAIL-CLOSED. خطای I/O، خطای شبکه، انحراف ساعت → surrender فوری.
5. FREEZE FILE. مالک انسانی می‌تواند با یک فایل، همه را از beat زدن منع کند.

Backends
--------
FileLeaseStore   → فاز M0/M1: یک میزبان، یا چند پروسه روی همان دیسک محلی.
NatsKvLeaseStore → فاز M2 به بعد: چند برد. از revision خودِ NATS KV به‌عنوان
                   fencing token استفاده می‌کند (CAS اتمیک سمت سرور).

هرگز FileLeaseStore را روی یک share شبکه‌ای (SMB/NFS) نگذار. قفل‌های آن
روی شبکه تضمین‌شده نیستند و دقیقاً همان split-brain را می‌سازد که این
ماژول برای جلوگیری از آن نوشته شده.
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional, Protocol

__all__ = [
    "LeaseRecord",
    "LeaseLost",
    "LeaseFrozen",
    "LeaseConflict",
    "LeaseStore",
    "FileLeaseStore",
    "NatsKvLeaseStore",
    "BeatLease",
]

DEFAULT_TTL_S = 60.0
DEFAULT_SAFETY_MARGIN_S = 10.0
DEFAULT_RENEW_DIVISOR = 3.0  # renew every TTL/3


# --------------------------------------------------------------------------
# errors
# --------------------------------------------------------------------------


class LeaseLost(RuntimeError):
    """مالکیت از دست رفت. هیچ نوشتنی مجاز نیست."""


class LeaseFrozen(RuntimeError):
    """فایل freeze فعال است — مالک انسانی beat را متوقف کرده."""


class LeaseConflict(RuntimeError):
    """CAS شکست خورد؛ کس دیگری مالک است."""


# --------------------------------------------------------------------------
# record
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class LeaseRecord:
    owner: str          # پایدار: "arm1" | "laptop" | "legs-board"
    holder_id: str      # یکتا برای هر اجرا (uuid4) — دو پروسه با یک owner را جدا می‌کند
    host: str
    pid: int
    revision: int       # FENCING TOKEN — یکنواخت صعودی، هرگز تکرار نمی‌شود
    acquired_wall: float
    expires_wall: float

    @property
    def vacant(self) -> bool:
        """رکورد رهاشده: مالک آگاهانه کنار رفته، ولی revision حفظ شده است."""
        return self.holder_id == ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @staticmethod
    def from_json(raw: str) -> "LeaseRecord":
        return LeaseRecord(**json.loads(raw))


# --------------------------------------------------------------------------
# store protocol
# --------------------------------------------------------------------------


class LeaseStore(Protocol):
    def read(self) -> Optional[LeaseRecord]: ...
    def compare_and_set(
        self, expected_revision: Optional[int], new: LeaseRecord
    ) -> LeaseRecord:
        """اتمیک. اگر revision فعلی برابر expected نبود → LeaseConflict."""
        ...


def _is_unc_or_url(path: str) -> bool:
    p = path.replace("\\", "/")
    return p.startswith("//") or p.startswith("smb:") or p.startswith("nfs:")


# --------------------------------------------------------------------------
# file backend (M0 / M1 — single host)
# --------------------------------------------------------------------------


class FileLeaseStore:
    """
    CAS با یک قفل مشورتیِ قابل‌حمل (O_CREAT|O_EXCL) + نوشتن اتمیک.
    روی Windows و Linux کار می‌کند. فقط برای دیسک محلی.
    """

    def __init__(self, path: str | os.PathLike, lock_timeout_s: float = 5.0):
        raw = os.fspath(path)
        if _is_unc_or_url(raw):
            raise RuntimeError(
                "FileLeaseStore refuses UNC/SMB/NFS paths — that is the split-brain "
                "this module exists to prevent. Use NatsKvLeaseStore for multi-host."
            )
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.lock_timeout_s = lock_timeout_s
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # -- lock -------------------------------------------------------------

    def _acquire_lock(self) -> int:
        deadline = time.monotonic() + self.lock_timeout_s
        while True:
            try:
                return os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                # قفل یتیم؟ اگر بیش از دو برابر timeout قدیمی است، بشکنش.
                try:
                    age = time.time() - self.lock_path.stat().st_mtime
                    if age > self.lock_timeout_s * 2:
                        self.lock_path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"lease lock busy: {self.lock_path}")
                time.sleep(0.02)

    def _release_lock(self, fd: int) -> None:
        try:
            os.close(fd)
        finally:
            self.lock_path.unlink(missing_ok=True)

    # -- io ---------------------------------------------------------------

    def _read_unlocked(self) -> Optional[LeaseRecord]:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        if not raw.strip():
            return None
        try:
            return LeaseRecord.from_json(raw)
        except Exception:
            # فایل خراب = هیچ‌کس مالک نیست. fail-closed یعنی دست نگه داریم،
            # ولی اجازهٔ acquire تازه می‌دهیم چون revision از صفر شروع نمی‌شود.
            # Remaining hole: a fully unreadable file still restarts at revision=1.
            return None

    def _write_atomic(self, rec: LeaseRecord) -> None:
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(rec.to_json())
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    # -- api --------------------------------------------------------------

    def read(self) -> Optional[LeaseRecord]:
        return self._read_unlocked()

    def compare_and_set(
        self, expected_revision: Optional[int], new: LeaseRecord
    ) -> LeaseRecord:
        fd = self._acquire_lock()
        try:
            cur = self._read_unlocked()
            cur_rev = cur.revision if cur else None
            if cur_rev != expected_revision:
                raise LeaseConflict(
                    f"revision mismatch: on-disk={cur_rev} expected={expected_revision}"
                )
            self._write_atomic(new)
            return new
        finally:
            self._release_lock(fd)


# --------------------------------------------------------------------------
# NATS KV backend (M2+ — multi-board)
# --------------------------------------------------------------------------


class NatsKvLeaseStore:
    """
    از revision سمت سرورِ NATS JetStream KV به‌عنوان fencing token استفاده
    می‌کند. update(key, value, last=revision) یک CAS اتمیک است، پس دو برد
    نمی‌توانند همزمان برنده شوند.

    ساخت:
        js = nc.jetstream()
        kv = await js.create_key_value(bucket="octopus_lease")
        store = NatsKvLeaseStore(kv_sync_adapter)

    این کلاس عمداً sync است تا با حلقهٔ beat موجود جور باشد؛ آداپتور
    async→sync را خودت بده (asyncio.run_coroutine_threadsafe).
    """

    KEY = "beat.owner"

    def __init__(self, kv):
        self._kv = kv  # آداپتور sync با متدهای get/create/update/purge

    def read(self) -> Optional[LeaseRecord]:
        entry = self._kv.get(self.KEY)
        if entry is None:
            return None
        rec = LeaseRecord.from_json(entry.value.decode("utf-8"))
        # revision معتبر همان چیزی است که سرور می‌گوید، نه چیزی که در payload است
        return LeaseRecord(**{**asdict(rec), "revision": int(entry.revision)})

    def compare_and_set(
        self, expected_revision: Optional[int], new: LeaseRecord
    ) -> LeaseRecord:
        payload = new.to_json().encode("utf-8")
        try:
            if expected_revision is None:
                rev = self._kv.create(self.KEY, payload)
            else:
                rev = self._kv.update(self.KEY, payload, last=expected_revision)
        except Exception as exc:  # نگاشت خطای CAS سرور
            raise LeaseConflict(str(exc)) from exc
        return LeaseRecord(**{**asdict(new), "revision": int(rev)})


# --------------------------------------------------------------------------
# the lease
# --------------------------------------------------------------------------


class BeatLease:
    """
    استفادهٔ معمول:

        lease = BeatLease(FileLeaseStore("_ops/state/octopus.lease"),
                          owner="laptop", on_event=ledger_append)

        if not lease.acquire():
            log("someone else owns the beat"); return

        try:
            while running:
                lease.assert_valid()          # قبل از هر beat
                token = lease.token           # با هر نوشتن ارسال شود
                do_one_beat(fencing_token=token)
                time.sleep(1)
        except LeaseLost:
            emergency_stop()
        finally:
            lease.release()

    یا کوتاه‌تر:

        with BeatLease(store, owner="arm1") as lease:
            ...
    """

    def __init__(
        self,
        store: LeaseStore,
        owner: str,
        ttl_s: float = DEFAULT_TTL_S,
        safety_margin_s: float = DEFAULT_SAFETY_MARGIN_S,
        freeze_file: Optional[str | os.PathLike] = None,
        on_event: Optional[Callable[[str, dict], None]] = None,
        clock_monotonic: Callable[[], float] = time.monotonic,
        clock_wall: Callable[[], float] = time.time,
    ):
        if ttl_s <= safety_margin_s * 2:
            raise ValueError("ttl_s must be > 2 × safety_margin_s")

        self._store = store
        self._owner = owner
        self._ttl = float(ttl_s)
        self._margin = float(safety_margin_s)
        self._freeze_file = Path(freeze_file) if freeze_file else None
        self._on_event = on_event or (lambda kind, data: None)
        self._mono = clock_monotonic
        self._wall = clock_wall

        self._holder_id = uuid.uuid4().hex
        self._host = socket.gethostname()
        self._rec: Optional[LeaseRecord] = None
        self._valid_until_mono: float = 0.0
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # -- properties -------------------------------------------------------

    @property
    def token(self) -> int:
        """FENCING TOKEN. با هر نوشتنی ارسال شود. اگر مالک نیستی → LeaseLost."""
        self.assert_valid()
        assert self._rec is not None
        return self._rec.revision

    @property
    def held(self) -> bool:
        with self._lock:
            return self._rec is not None and self._mono() < self._valid_until_mono

    # -- freeze -----------------------------------------------------------

    def _check_freeze(self) -> None:
        if self._freeze_file and self._freeze_file.exists():
            raise LeaseFrozen(f"freeze file present: {self._freeze_file}")

    # -- acquire ----------------------------------------------------------

    def acquire(self, blocking: bool = False, timeout_s: float = 0.0) -> bool:
        deadline = self._mono() + timeout_s
        while True:
            try:
                self._check_freeze()
                if self._try_acquire_once():
                    return True
            except LeaseFrozen:
                raise
            except Exception as exc:
                self._emit("lease.acquire.error", {"error": repr(exc)})
                if not blocking:
                    return False
            if not blocking or self._mono() >= deadline:
                return False
            time.sleep(min(1.0, self._ttl / 10.0))

    def _try_acquire_once(self) -> bool:
        cur = self._store.read()
        now_wall = self._wall()

        if cur is not None and not cur.vacant:
            # مالک زنده؟ حاشیه را به نفع مالک فعلی در نظر بگیر (انحراف ساعت)
            if now_wall < cur.expires_wall + self._margin:
                if not (cur.owner == self._owner and cur.holder_id == self._holder_id):
                    self._emit(
                        "lease.acquire.denied",
                        {"current_owner": cur.owner, "current_host": cur.host},
                    )
                    return False

        expected = cur.revision if cur else None
        new_rev = (cur.revision + 1) if cur else 1
        t0 = self._mono()
        rec = LeaseRecord(
            owner=self._owner,
            holder_id=self._holder_id,
            host=self._host,
            pid=os.getpid(),
            revision=new_rev,
            acquired_wall=now_wall,
            expires_wall=now_wall + self._ttl,
        )
        try:
            rec = self._store.compare_and_set(expected, rec)
        except LeaseConflict as exc:
            self._emit("lease.acquire.conflict", {"error": str(exc)})
            return False

        with self._lock:
            self._rec = rec
            # اعتبار محلی از لحظهٔ *قبل* از نوشتن حساب می‌شود، نه بعد از آن:
            # هزینهٔ خودِ نوشتن از سهم ما کم می‌شود، نه از حاشیهٔ ایمنی.
            self._valid_until_mono = t0 + self._ttl - self._margin
        self._emit(
            "lease.acquired",
            {"owner": self._owner, "revision": rec.revision, "host": self._host},
        )
        return True

    # -- renew ------------------------------------------------------------

    def renew(self) -> bool:
        with self._lock:
            rec = self._rec
        if rec is None:
            return False
        try:
            self._check_freeze()
        except LeaseFrozen:
            self._surrender("frozen")
            raise

        cur = self._store.read()
        if cur is None or cur.vacant or cur.revision != rec.revision or cur.holder_id != rec.holder_id:
            # کس دیگری برد. این یعنی ما در پنجرهٔ خطر بودیم.
            self._surrender("preempted")
            return False

        now_wall = self._wall()
        t0 = self._mono()
        new = LeaseRecord(
            owner=rec.owner,
            holder_id=rec.holder_id,
            host=rec.host,
            pid=rec.pid,
            revision=rec.revision + 1,
            acquired_wall=rec.acquired_wall,
            expires_wall=now_wall + self._ttl,
        )
        try:
            new = self._store.compare_and_set(rec.revision, new)
        except LeaseConflict:
            self._surrender("conflict")
            return False
        except Exception as exc:
            self._emit("lease.renew.error", {"error": repr(exc)})
            return False  # هنوز مالکیم تا انقضای محلی؛ دفعهٔ بعد دوباره تلاش

        with self._lock:
            self._rec = new
            self._valid_until_mono = t0 + self._ttl - self._margin
        self._emit("lease.renewed", {"revision": new.revision})
        return True

    # -- validity ---------------------------------------------------------

    def assert_valid(self) -> None:
        """قبل از هر beat و قبل از هر نوشتن صدا بزن. fail-closed."""
        self._check_freeze()
        with self._lock:
            if self._rec is None:
                raise LeaseLost("no lease held")
            remaining = self._valid_until_mono - self._mono()
            if remaining <= 0:
                rec = self._rec
                self._rec = None
                self._emit(
                    "lease.expired",
                    {"revision": rec.revision, "overshoot_s": round(-remaining, 3)},
                )
                raise LeaseLost(
                    f"lease expired {abs(remaining):.1f}s ago — refusing to beat"
                )

    # -- release ----------------------------------------------------------

    def _surrender(self, reason: str) -> None:
        with self._lock:
            rec, self._rec, self._valid_until_mono = self._rec, None, 0.0
        if rec is not None:
            self._emit("lease.surrendered", {"reason": reason, "revision": rec.revision})

    def release(self) -> None:
        """
        رکورد را **حذف نمی‌کند** — آن را «رهاشده» علامت می‌زند و revision را
        نگه می‌دارد. این تنها راه تضمین یکنواختی صعودیِ fencing token در طول
        عمر سیستم است. اگر فایل را پاک کنیم، مالک بعدی از revision=1 شروع
        می‌کند و یک نویسندهٔ کهنه با token=2 می‌تواند او را دور بزند.
        """
        self.stop_renewer()
        with self._lock:
            rec = self._rec
        if rec is None:
            return
        vacated = LeaseRecord(
            owner=rec.owner,
            holder_id="",           # علامت رهاشدن
            host=rec.host,
            pid=rec.pid,
            revision=rec.revision + 1,
            acquired_wall=rec.acquired_wall,
            expires_wall=0.0,        # فوراً منقضی
        )
        try:
            self._store.compare_and_set(rec.revision, vacated)
            self._emit("lease.released", {"revision": vacated.revision})
        except Exception as exc:
            # نتوانستیم رها کنیم؛ TTL خودش کار را تمام می‌کند.
            self._emit("lease.release.error", {"error": repr(exc)})
        finally:
            with self._lock:
                self._rec = None
                self._valid_until_mono = 0.0

    # -- background renewer ----------------------------------------------

    def start_renewer(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        interval = self._ttl / DEFAULT_RENEW_DIVISOR

        def loop() -> None:
            while not self._stop.wait(interval):
                try:
                    self.renew()
                except LeaseFrozen:
                    return
                except Exception as exc:
                    self._emit("lease.renewer.error", {"error": repr(exc)})

        self._thread = threading.Thread(
            target=loop, name="beat-lease-renewer", daemon=True
        )
        self._thread.start()

    def stop_renewer(self) -> None:
        self._stop.set()
        t, self._thread = self._thread, None
        if t is not None:
            t.join(timeout=2.0)

    # -- context manager --------------------------------------------------

    def __enter__(self) -> "BeatLease":
        if not self.acquire():
            raise LeaseLost(f"could not acquire beat lease for owner={self._owner}")
        self.start_renewer()
        return self

    def __exit__(self, *exc) -> None:
        self.release()

    # -- events -----------------------------------------------------------

    def _emit(self, kind: str, data: dict) -> None:
        try:
            self._on_event(kind, {"ts": self._wall(), "holder": self._holder_id, **data})
        except Exception:
            pass  # لجر نباید حلقهٔ beat را بکشد؛ خطای لجر جای دیگری fail-closed است
