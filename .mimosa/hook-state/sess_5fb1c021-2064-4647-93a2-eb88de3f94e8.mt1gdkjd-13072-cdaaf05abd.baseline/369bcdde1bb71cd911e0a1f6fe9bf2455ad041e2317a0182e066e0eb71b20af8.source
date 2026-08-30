#!/usr/bin/env python3
"""
CryptoQuant CORS Proxy
======================
مشکل: مرورگر اجازه فراخوانی مستقیم api.cryptoquant.com را نمی‌دهد (CORS block)
راه‌حل: این اسکریپت روی localhost:8787 اجرا می‌شود و درخواست‌ها را forward می‌کند
       با header های CORS مناسب.

نحوه استفاده:
1. مطمئن شو Python 3 نصب است:  python --version
2. در ترمینال:  python cors_proxy.py
3. در صفحه index.html فیلد "Proxy URL" را روی  http://localhost:8787/v1  بگذار
4. Token را وارد کن و «شروع دریافت» را بزن
5. وقتی کار تمام شد Ctrl+C برای توقف proxy

نکته امنیتی: این proxy فقط روی 127.0.0.1 (lokahost) listen می‌کند
            — از بیرون قابل دسترسی نیست. Token شما به هیچ سرویس بیرونی نمی‌رود.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.error
import sys

UPSTREAM = "https://api.cryptoquant.com"
PORT = 8787

class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Browser CORS preflight
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = UPSTREAM + self.path
        req = urllib.request.Request(url, method="GET")
        # Forward Authorization header from browser
        auth = self.headers.get("Authorization")
        if auth:
            req.add_header("Authorization", auth)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "CryptoQuantLocalProxy/1.0")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                self.send_response(resp.status)
                self._cors_headers()
                # Pass through some upstream headers
                ctype = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                # Pass through retry headers if any
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    self.send_header("Retry-After", retry_after)
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            self.send_response(e.code)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            retry_after = e.headers.get("Retry-After") if e.headers else None
            if retry_after:
                self.send_header("Retry-After", retry_after)
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.URLError as e:
            msg = f'{{"error":"upstream_unreachable","reason":"{e.reason}"}}'.encode()
            self.send_response(502)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
        except Exception as e:
            msg = f'{{"error":"proxy_error","reason":"{str(e)}"}}'.encode()
            self.send_response(500)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def _cors_headers(self):
        # Allow requests from any origin (only localhost can reach us anyway)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Max-Age", "3600")

    def log_message(self, fmt, *args):
        # Cleaner log format
        try:
            line = fmt % args
        except Exception:
            line = " ".join(str(a) for a in args)
        sys.stdout.write(f"[{self.log_date_time_string()}] {line}\n")
        sys.stdout.flush()


def main():
    print("=" * 60)
    print(f"  CryptoQuant CORS Proxy")
    print("=" * 60)
    print(f"  Listening on:  http://localhost:{PORT}")
    print(f"  Forwarding to: {UPSTREAM}")
    print(f"  Browser:       use http://localhost:{PORT}/v1 as BASE_URL")
    print(f"  Stop:          Ctrl+C")
    print("=" * 60)
    try:
        HTTPServer(("127.0.0.1", PORT), ProxyHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")


if __name__ == "__main__":
    main()
