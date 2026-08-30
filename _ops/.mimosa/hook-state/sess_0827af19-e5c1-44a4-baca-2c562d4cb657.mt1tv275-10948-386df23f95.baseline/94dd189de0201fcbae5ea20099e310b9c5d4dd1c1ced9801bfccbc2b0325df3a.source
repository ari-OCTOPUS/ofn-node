"""board_cp/server.py — شنوندهٔ اختصاصی TLS برای برد (فقط pull/ack).

چرا جدا از miniapp_gateway؟ دیوارِ مینی‌اپ روی 127.0.0.1:8774 می‌ماند
بسته؛ برد از LAN فقط به همین دو مسیر با Bearer می‌رسد. fail-closed:
فلگ خاموش یا Gate 0 بسته ⇒ pull می‌گوید 503 و هیچ فرمانی خارج نمی‌شود.

راز (Authorization/Bearer) هرگز لاگ نمی‌شود. مسیرها:
  GET  /api/board-cp/pull   — Bearer برد
  POST /api/board-cp/ack    — Bearer برد
هر چیز دیگر 404. پروتکل: HTTPS (گواهی self-signed، برد fingerprint را pin می‌کند).

env (همان قرارداد RESTART-PROCESS.ps1):
  OCTOPUS.env + OCTOPUS-flags.cmd در startup خوانده می‌شوند (setdefault).
  OCTOPUS_BOARD_CP_PORT (پیش‌فرض 8801) · OCTOPUS_BOARD_CP_BIND (پیش‌فرض 0.0.0.0)
  OCTOPUS_BOARD_CP_TLS_DIR (پیش‌فرض _ops/state/board_cp/tls)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/board_cp
_OPS = _HERE.parent                               # _ops
# اجرای مستقیم، دایرکتوریِ اسکریپت را sys.path[0] می‌کند و board_cp/http.py
# روی پکیجِ استاندلب http سایه می‌اندازد — اول خودش را حذف کن، بعد استاندلب.
while str(_HERE) in sys.path:
    sys.path.remove(str(_HERE))
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ssl  # noqa: E402 — بعد از پاک‌سازیِ path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402

_ALLOWED = frozenset({"/api/board-cp/pull", "/api/board-cp/ack"})
_MAX_BODY = 1_000_000


def _load_env_files() -> None:
    """KEY=VALUE از OCTOPUS.env و `set KEY=VALUE` از OCTOPUS-flags.cmd.

    setdefault — یعنی envِ صریحِ پروسه (مثل OCTOPUS_BOARD_CP_DB تست) مقدم است.
    """
    env_file = _OPS / "OCTOPUS.env"
    try:
        for ln in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", ln.strip())
            if m:
                os.environ.setdefault(m.group(1), m.group(2))
    except OSError:
        pass
    flags_file = _OPS / "OCTOPUS-flags.cmd"
    try:
        for ln in flags_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*set\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$", ln)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip())
    except OSError:
        pass


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "board-cp/1"
    sys_version = ""  # نسخهٔ پایتون در پاسخها لو نرود

    def _hdrs(self, body: bytes) -> dict:
        h: dict = {}
        for k, v in self.headers.items():
            h[k] = v
        h["_body"] = body
        return h

    def _send(self, status: int, payload: bytes,
              ctype: str = "application/json; charset=utf-8") -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _dispatch(self, method: str) -> None:
        p = str(self.path or "").split("?", 1)[0]
        if p not in _ALLOWED:
            self._send(404, b'{"ok":false,"reason":"not_found"}')
            return
        if method not in ("GET", "POST"):
            self._send(405, b"", "text/plain; charset=utf-8")
            return
        body = b""
        if method == "POST":
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n > 0:
                    body = self.rfile.read(min(n, _MAX_BODY))
            except (ValueError, OSError):
                body = b""
        from board_cp import http as bhttp  # noqa: WPS433 — بعد از load env
        hit = bhttp.dispatch(method, p, self._hdrs(body), owner_ok=False)
        if hit is None:
            self._send(404, b'{"ok":false,"reason":"not_found"}')
            return
        status, payload, ctype = hit
        self._send(status, payload, str(ctype))

    def do_GET(self) -> None:  # noqa: N802 — قرارداد BaseHTTPRequestHandler
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def log_message(self, fmt: str, *args) -> None:  # noqa: WPS125
        # فقط method/path/status — Authorization هرگز.
        if os.environ.get("OCTOPUS_BOARD_CP_DEBUG", "0") == "1":
            super().log_message(fmt, *args)


def _tls_context(cert: Path, key: Path) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(cert), str(key))
    return ctx


def make_server(bind: str, port: int, cert: Path, key: Path) -> ThreadingHTTPServer:
    """ساختِ سرور بدون serve — تست‌ها همین را صدا می‌زنند (port=0 → ephemeral)."""
    srv = ThreadingHTTPServer((bind, port), _Handler)
    srv.socket = _tls_context(cert, key).wrap_socket(srv.socket, server_side=True)
    return srv


def main() -> int:
    _load_env_files()
    from board_cp import config  # noqa: WPS433

    port = int(os.environ.get("OCTOPUS_BOARD_CP_PORT", "8801"))
    bind = str(os.environ.get("OCTOPUS_BOARD_CP_BIND", "0.0.0.0"))
    tls_dir = Path(os.environ.get("OCTOPUS_BOARD_CP_TLS_DIR", "").strip() or
                   (_OPS / "state" / "board_cp" / "tls"))
    cert, key = tls_dir / "cert.pem", tls_dir / "key.pem"
    if not (cert.exists() and key.exists()):
        print("board-cp: گواهی TLS نیست — fail-closed. (بساز: make-cert در RESTART-BOARDCP.ps1)")
        return 2
    try:
        srv = make_server(bind, port, cert, key)
    except OSError as exc:
        print(f"board-cp: bind روی {bind}:{port} شکست خورد — {exc}")
        return 0  # نمونهٔ دیگری زنده است؛ خروجِ تمیز (الگوی gateway)
    print(f"board-cp: https://{bind}:{port} — فقط pull/ack · "
          f"flag={'ON' if config.flag_on() else 'OFF'} · "
          f"gate0={'ready' if config.gate0_ready() else 'not-ready'}")
    try:
        import opslib  # noqa: WPS433
        opslib.heartbeat(f"board-cp=START bind={bind} port={port}")
    except Exception:  # noqa: BLE001
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            srv.server_close()
        except Exception:  # noqa: BLE001
            pass
        try:
            import opslib  # noqa: WPS433
            opslib.heartbeat(f"board-cp=STOP port={port}")
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
