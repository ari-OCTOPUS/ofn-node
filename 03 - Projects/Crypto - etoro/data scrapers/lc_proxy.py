#!/usr/bin/env python3
"""
LunarCrush CORS Proxy
=====================
Runs on localhost:8788, forwards to https://lunarcrush.com

نحوه استفاده:
1. python lc_proxy.py
2. در lc_index.html فیلد Base URL را روی  http://localhost:8788/api4  بگذار
3. Ctrl+C برای توقف
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.error
import sys

UPSTREAM = "https://lunarcrush.com"
PORT = 8788

class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = UPSTREAM + self.path
        req = urllib.request.Request(url, method="GET")
        auth = self.headers.get("Authorization")
        if auth:
            req.add_header("Authorization", auth)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "LunarCrushLocalProxy/1.0")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                self.send_response(resp.status)
                self._cors_headers()
                ctype = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                for h in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"):
                    v = resp.headers.get(h)
                    if v:
                        self.send_header(h, v)
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            self.send_response(e.code)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if e.headers:
                for h in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"):
                    v = e.headers.get(h)
                    if v:
                        self.send_header(h, v)
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After")
        self.send_header("Access-Control-Max-Age", "3600")

    def log_message(self, fmt, *args):
        try:
            line = fmt % args
        except Exception:
            line = " ".join(str(a) for a in args)
        sys.stdout.write(f"[{self.log_date_time_string()}] {line}\n")
        sys.stdout.flush()


def main():
    print("=" * 60)
    print(f"  LunarCrush CORS Proxy")
    print("=" * 60)
    print(f"  Listening on:  http://localhost:{PORT}")
    print(f"  Forwarding to: {UPSTREAM}")
    print(f"  Browser:       use http://localhost:{PORT}/api4 as Base URL")
    print(f"  Stop:          Ctrl+C")
    print("=" * 60)
    try:
        HTTPServer(("127.0.0.1", PORT), ProxyHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")


if __name__ == "__main__":
    main()
