# -*- coding: utf-8 -*-
"""مغز دوم — Setup Wizard + گزارش اتصال.

اجرا:  python setup_wizard.py   (یا START-HERE.bat)
- فرم فارسی RTL روی http://localhost:8877 — کلیدها فقط در control-brain/.env (هرگز چاپ/لاگ نمی‌شوند)
- 📡 گزارش اتصال: تلگرام (getMe)، DeepSeek، Sakana Fugu، KeePass، Node/Python، ماژول‌ها، پورت‌ها
- دکمه‌های selftest / تست دمو / روشن کردن کل ساختار (مغز کنترل + پنل‌های گوشی)
"""
import json
import os
import re
import socket
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent
CB = ROOT / "control-brain"
ZA = ROOT / "ziman-agent"
ENV = CB / ".env"
WIZARD_PORT = 8877

FIELDS = [
    ("TELEGRAM_TOKEN", "توکن ربات تلگرامِ مغز دوم (نو، از BotFather — قدیمی‌ها افشا شده‌اند)", "password", "", True),
    ("OWNER_CHAT_ID", "Chat ID عددی خودت (از @userinfobot)", "text", "", True),
    ("SABA_CHAT_ID", "Chat ID تلگرام صبا (از @userinfobot — نقش: operator فقط Project-F)", "text", "", False),
    ("MOM_CHAT_ID", "Chat ID تلگرام مامان (گیرندهٔ پیام‌های زیمان — رکن B)", "text", "", False),
    ("DEEPSEEK_API_KEY", "کلید DeepSeek ‏(platform.deepseek.com) — موتور اصلی تولید زنده؛ خالی = آفلاین", "password", "", False),
    ("SAKANA_API_KEY", "کلید Sakana Fugu ‏(شرکت ژاپنی Sakana AI) — طبق verdict: فقط escalation پشت سقف بودجه، ضریب هزینهٔ پنهان ۵–۱۵×", "password", "", False),
    ("PAINTING_TELEGRAM_TOKEN", "توکن تلگرام ربات نقاشی (نو — جدا از توکن مغز)", "password", "", False),
    ("ACCOUNTING_TELEGRAM_TOKEN", "توکن تلگرام ربات حسابداری (نو)", "password", "", False),
    ("TAVILY_API_KEY", "کلید Tavily (جستجوی وب ربات نقاشی)", "password", "", False),
    ("DASHBOARD_PORT", "پورت داشبورد وب", "text", "8770", False),
    ("PANEL_PIN_Z", "رمز ۴ رقمی پنل زیمان (برای تولیدکننده)", "text", "1111", False),
    ("PANEL_PIN_F", "رمز ۴ رقمی پنل Project-F (برای صبا)", "text", "2222", False),
    ("PANEL_PORT", "پورت پنل‌های گوشی", "text", "8899", False),
    ("KEEPASS_DB", "مسیر KeePassXC ‏(.kdbx) — اختیاری؛ اگر بدهی جای .env می‌نشیند", "text", "", False),
    ("KEEPASS_KEYFILE", "مسیر keyfile ‏KeePass — اختیاری", "text", "", False),
    ("CONTROL_STATE_DIR", "پوشهٔ state (بیرون از vault)", "text", str(Path.home() / ".second-brain-state"), False),
]


def read_env():
    vals = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                vals[k.strip()] = v.strip()
    return vals


def env_status():
    return {k: bool(v) for k, v in read_env().items()}


def save_env(form):
    existing = read_env()
    lines = ["# ساخته‌شده توسط setup_wizard مغز دوم — این فایل را جایی نفرست. gitignore هست."]
    for key, *_ in FIELDS:
        new = form.get(key, [""])[0].strip()
        lines.append(f"{key}={new if new else existing.get(key, '')}")
    cid = form.get("OWNER_CHAT_ID", [""])[0].strip() or existing.get("OWNER_CHAT_ID", "")
    # ربات نقاشی chat_id را با این نام می‌خواند (به فرزندها به ارث می‌رسد):
    lines.append(f"TELEGRAM_CHAT_ID={cid}")
    # مسیریابی DeepSeek (تصمیم آری: بدون Anthropic — endpoint سازگار DeepSeek):
    ds = form.get("DEEPSEEK_API_KEY", [""])[0].strip() or existing.get("DEEPSEEK_API_KEY", "")
    if ds:
        lines.append(f"ANTHROPIC_API_KEY={ds}")  # کد قدیمی همین نام را می‌خواند؛ مقصدش DeepSeek است
        lines.append("ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic")
        lines.append("LLM_MODEL=deepseek-v4-flash")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if cid.isdigit():
        p1 = CB / "config" / "projects.yaml"
        p1.write_text(re.sub(r"^owner_chat_id:\s*\d+", f"owner_chat_id: {cid}",
                             p1.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")
        p2 = CB / "config" / "users.yaml"
        p2.write_text(re.sub(r"(\s*telegram_chat_id:\s*)\d+", r"\g<1>" + cid,
                             p2.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")
    # chat_id صبا و مامان → users.yaml (صبا: operator فقط Project-F · مامان: viewer/گیرنده زیمان)
    for fkey, uid in (("SABA_CHAT_ID", "saba"), ("MOM_CHAT_ID", "mom")):
        val = form.get(fkey, [""])[0].strip() or existing.get(fkey, "")
        if val.isdigit():
            p2 = CB / "config" / "users.yaml"
            t = p2.read_text(encoding="utf-8")
            t = re.sub(rf"(-\s*id:\s*{uid}[\s\S]*?telegram_chat_id:\s*)\d+", r"\g<1>" + val, t, count=1)
            p2.write_text(t, encoding="utf-8")
    sd = form.get("CONTROL_STATE_DIR", [""])[0].strip()
    if sd:
        Path(sd).mkdir(parents=True, exist_ok=True)


def venv_python():
    for c in [CB / ".venv" / "Scripts" / "python.exe", CB / ".venv" / "bin" / "python"]:
        if c.exists():
            return str(c)
    return sys.executable


def utf8_env():
    """کنسول ویندوز cp1252 است و emoji ی workerها را می‌کُشد — UTF-8 اجباری."""
    return {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run_cmd(args, cwd, timeout=120):
    try:
        r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=utf8_env())
        return (r.returncode == 0), (r.stdout + "\n" + r.stderr).strip()[-4000:]
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def port_open(port):
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", int(port))) == 0


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:  # noqa: BLE001
        return "127.0.0.1"


def http_get(url, headers=None, timeout=7):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(2000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:120]


# ---------- 📡 گزارش اتصال ----------
def tg_check(token, label):
    if not token:
        return (label, "warn", "توکن داده نشده")
    code, body = http_get(f"https://api.telegram.org/bot{token}/getMe")
    if code == 200:
        try:
            uname = json.loads(body).get("result", {}).get("username", "?")
            return (label, "ok", f"متصل ✔ ربات: @{uname}")
        except Exception:  # noqa: BLE001
            return (label, "ok", "متصل ✔")
    if code == 401:
        return (label, "no", "توکن نامعتبر (401)")
    return (label, "warn", f"دسترسی نشد ({code or 'شبکه'})")


def build_report():
    env = read_env()
    rows = []
    rows.append(tg_check(env.get("TELEGRAM_TOKEN", ""), "تلگرام — مغز دوم"))
    rows.append(tg_check(env.get("PAINTING_TELEGRAM_TOKEN", ""), "تلگرام — ربات نقاشی"))
    rows.append(tg_check(env.get("ACCOUNTING_TELEGRAM_TOKEN", ""), "تلگرام — ربات حسابداری"))
    # DeepSeek — موتور اصلی (Anthropic عمداً حذف شد — تصمیم آری)
    k = env.get("DEEPSEEK_API_KEY", "")
    if k:
        code, _ = http_get("https://api.deepseek.com/models",
                           {"Authorization": f"Bearer {k}"})
        rows.append(("DeepSeek (موتور اصلی)", "ok" if code == 200 else "no",
                     "متصل ✔ مدل: deepseek-v4-flash" if code == 200 else f"کلید رد شد ({code or 'شبکه'})"))
    else:
        rows.append(("DeepSeek (موتور اصلی)", "warn", "کلید نیست → حالت آفلاین"))
    # Sakana Fugu
    k = env.get("SAKANA_API_KEY", "")
    if k:
        code, _ = http_get("https://api.sakana.ai/", timeout=6)
        rows.append(("Sakana Fugu", "ok" if code else "warn",
                     "کلید ذخیره شد ✔" + ("، سرور در دسترس" if code else "، سرور جواب نداد (اعتبار کلید موقع مصرف معلوم می‌شود)")))
    else:
        rows.append(("Sakana Fugu", "warn", "کلید نیست (escalation غیرفعال)"))
    # Tavily
    rows.append(("Tavily (جستجو)", "ok" if env.get("TAVILY_API_KEY") else "warn",
                 "کلید ذخیره شد ✔" if env.get("TAVILY_API_KEY") else "کلید نیست"))
    # KeePass
    kdbx = env.get("KEEPASS_DB", "")
    rows.append(("KeePassXC", "ok" if (kdbx and Path(kdbx).exists()) else "warn",
                 "فایل موجود ✔" if (kdbx and Path(kdbx).exists()) else ("مسیر اشتباه" if kdbx else "تنظیم نشده → از .env استفاده می‌شود")))
    # runtimes
    okp, outp = run_cmd([venv_python(), "--version"], ROOT, 20)
    rows.append(("Python (venv)", "ok" if okp else "no", outp.splitlines()[0] if okp else "پیدا نشد"))
    okn, outn = run_cmd(["node", "--version"], ROOT, 20)
    rows.append(("Node.js (ربات حسابداری)", "ok" if okn else "no",
                 outn.splitlines()[0] if okn else "نصب نیست → ربات حسابداری روشن نمی‌شود"))
    # ماژول‌ها
    try:
        import yaml  # از venv (PyYAML در requirements هست)
        reg = yaml.safe_load((CB / "config" / "projects.yaml").read_text(encoding="utf-8"))
        for p in reg.get("projects", []):
            wd = (CB / p["workdir"]).resolve()
            ok = wd.exists()
            rows.append((f"ماژول: {p['name']}",
                         "ok" if (ok and p.get("enabled")) else ("warn" if ok else "no"),
                         ("enabled ✔ مسیر ✔" if p.get("enabled") else "مسیر ✔ ولی خاموش") if ok else "مسیر پیدا نشد"))
    except Exception as e:  # noqa: BLE001
        rows.append(("خواندن projects.yaml", "no", str(e)[:100]))
    # صبا (Project-F)
    try:
        ut = (CB / "config" / "users.yaml").read_text(encoding="utf-8")
        msab = re.search(r"-\s*id:\s*saba[\s\S]*?telegram_chat_id:\s*(\d+)", ut)
        sid_ok = bool(msab and msab.group(1) != "0")
        rows.append(("صبا ↔ تلگرام (Project-F)", "ok" if sid_ok else "warn",
                     "ثبت شد ✔ operator فقط Project-F — باید به ربات /start بدهد" if sid_ok
                     else "Chat ID صبا هنوز ثبت نشده (فیلد فرم)"))
    except Exception:  # noqa: BLE001
        pass
    # GATE 0
    g = (ROOT / "projectf-agent" / "GATE.yaml")
    locked = "closed" not in (g.read_text(encoding="utf-8") if g.exists() else "")
    rows.append(("Project-F — GATE 0", "warn" if locked else "ok",
                 "🔒 باز — ماژول status-only، صفر اجرا (verdict انسان)" if locked else "🟢 بسته — Branch ثبت شده"))
    # داشبورد
    dp = env.get("DASHBOARD_PORT", "8770") or "8770"
    rows.append((f"داشبورد وب (پورت {dp})", "ok" if port_open(dp) else "warn",
                 "🟢 روشن" if port_open(dp) else "⚫ خاموش — بعد از 🚀 روشن می‌شود"))
    # پنل‌های گوشی
    pp = env.get("PANEL_PORT", "8899") or "8899"
    lan = lan_ip()
    rows.append((f"پنل‌های گوشی (پورت {pp})", "ok" if port_open(pp) else "warn",
                 f"🟢 روشن — روی گوشی: http://{lan}:{pp}/z و /f" if port_open(pp)
                 else f"⚫ خاموش — بعد از 🚀؛ آدرس گوشی: http://{lan}:{pp}"))
    ok_n = sum(1 for _, s, _ in rows if s == "ok")
    return rows, ok_n, len(rows)


def page(body):
    return f"""<!doctype html><html dir="rtl" lang="fa"><head><meta charset="utf-8">
<title>مغز دوم — راه‌اندازی</title><style>
body{{font-family:Segoe UI,Tahoma,sans-serif;background:#0f1420;color:#e8ecf4;max-width:800px;margin:24px auto;padding:0 16px}}
h1{{font-size:22px}} .card{{background:#1a2233;border:1px solid #2a3550;border-radius:12px;padding:18px;margin:14px 0}}
label{{display:block;margin:10px 0 4px;font-size:14px;color:#aeb9d0}}
input{{width:100%;box-sizing:border-box;padding:9px;border-radius:8px;border:1px solid #2a3550;background:#0f1420;color:#e8ecf4;direction:ltr;text-align:left}}
button{{background:#3b82f6;color:#fff;border:0;border-radius:8px;padding:10px 22px;font-size:15px;cursor:pointer;margin:6px 4px 0 0}}
button.g{{background:#16a34a}} button.o{{background:#d97706}} button.p{{background:#7c3aed}}
.ok{{color:#4ade80}} .no{{color:#f87171}} .warn{{color:#fbbf24}}
pre{{background:#0a0e18;padding:12px;border-radius:8px;direction:ltr;text-align:left;overflow:auto;font-size:12px;white-space:pre-wrap}}
table{{width:100%;border-collapse:collapse;font-size:14px}} td{{padding:7px 6px;border-bottom:1px solid #2a3550}}
.bar{{height:10px;background:#2a3550;border-radius:99px;overflow:hidden}} .fill{{height:100%;background:linear-gradient(90deg,#16a34a,#4ade80)}}
.badge{{font-size:12px;padding:2px 10px;border-radius:99px;background:#233;margin-right:6px}} a{{color:#7db3ff}}</style>
</head><body>{body}</body></html>"""


def form_html():
    st = env_status()
    rows = ""
    for key, label, typ, default, req in FIELDS:
        filled = '<span class="badge ok">✔ ذخیره شده — خالی بگذاری همان می‌ماند</span>' if st.get(key) else ""
        star = ' <span class="no">*</span>' if req else ""
        rows += (f'<label>{label}{star} {filled}</label>'
                 f'<input name="{key}" type="{typ}" value="{"" if typ == "password" or st.get(key) else default}" '
                 f'placeholder="{default if st.get(key) else ""}" autocomplete="off">')
    dp = read_env().get("DASHBOARD_PORT", "8770") or "8770"
    running = '<span class="ok">🟢 روشن</span>' if port_open(dp) else '<span class="no">⚫ خاموش</span>'
    return page(f"""
<h1>🧠 مغز دوم — راه‌اندازی کامل ساختار</h1>
<div class="card">وضعیت مغز (داشبورد پورت {dp}): {running}
 &nbsp;|&nbsp; <a href="http://localhost:{dp}" target="_blank">داشبورد</a>
 &nbsp;|&nbsp; ماژول‌ها: مغز کنترل · زیمان · ربات نقاشی · ربات حسابداری · Project-F 🔒 · پنل‌های گوشی 📱 · دمو</div>
<div class="card"><form method="post" action="/save">{rows}
<button type="submit">💾 ذخیرهٔ امن (فقط روی همین لپ‌تاپ)</button></form>
<p style="font-size:12px;color:#8b96ad">کلیدها فقط در <code>control-brain/.env</code> — gitignore، بدون log، بدون echo.</p></div>
<div class="card"><b>بعد از ذخیره:</b><br>
<form method="post" action="/report" style="display:inline"><button class="p">📡 گزارش اتصال — به چند جا وصلیم؟</button></form>
<form method="post" action="/selftest" style="display:inline"><button class="o">🧪 Selftest زیمان</button></form>
<form method="post" action="/testdemo" style="display:inline"><button class="o">🔬 تست دمو</button></form>
<form method="post" action="/launch" style="display:inline"><button class="g">🚀 روشن کردن کل ساختار</button></form>
</div>""")


def report_html():
    rows, ok_n, total = build_report()
    pct = int(ok_n * 100 / total) if total else 0
    tr = "".join(
        f'<tr><td>{name}</td><td class="{cls}">{"🟢" if cls == "ok" else ("🟡" if cls == "warn" else "🔴")}</td><td class="{cls}">{msg}</td></tr>'
        for name, cls, msg in rows)
    return page(f"""
<h1>📡 گزارش اتصال مغز دوم</h1>
<div class="card"><b>{ok_n} از {total} اتصال سبز — {pct}٪</b>
<div class="bar" style="margin-top:8px"><div class="fill" style="width:{pct}%"></div></div></div>
<div class="card"><table>{tr}</table></div>
<div class="card" style="font-size:13px;color:#8b96ad">🟢 وصل و تأییدشده · 🟡 اختیاری/در انتظار · 🔴 مشکل واقعی — هیچ مقدار کلیدی در این گزارش نیست.</div>
<p><a href="/">⬅ برگشت</a></p>""")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # حریم کلیدها — بدون لاگ
        pass

    def _send(self, html, code=200):
        b = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(report_html() if self.path == "/report" else form_html())

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(n).decode("utf-8"))
        back = '<p><a href="/">⬅ برگشت</a></p>'
        if self.path == "/save":
            save_env(form)
            self._send(page(f'<div class="card"><h1 class="ok">✔ ذخیره شد</h1>'
                            f'<p>فایل: <code>{ENV}</code>. حالا 📡 گزارش اتصال را بزن.</p>'
                            f'<form method="post" action="/report"><button class="p">📡 گزارش اتصال</button></form>{back}</div>'))
        elif self.path == "/report":
            self._send(report_html())
        elif self.path == "/selftest":
            ok, out = run_cmd([venv_python(), "worker.py", "--selftest"], ZA)
            self._send(page(f'<div class="card"><h1 class="{"ok" if ok else "no"}">{"✔ selftest سبز" if ok else "✗ selftest خطا"}</h1><pre>{out}</pre>{back}</div>'))
        elif self.path == "/testdemo":
            ok, out = run_cmd([venv_python(), "app.py", "test", "demo"], CB)
            self._send(page(f'<div class="card"><h1 class="{"ok" if ok else "no"}">{"✔ دمو سبز" if ok else "✗ دمو خطا"}</h1><pre>{out}</pre>{back}</div>'))
        elif self.path == "/launch":
            env = read_env()
            # ۱) مغز کنترل (داشبورد + ربات تلگرام + ماژول‌ها)
            # گارد ضد-Conflict: اگر داشبورد از قبل جواب می‌دهد، نمونهٔ دوم ساخته نمی‌شود.
            # نکتهٔ ویندوز: عنوانِ start حتماً باید داخل کوتیشن باشد وگرنه به‌جای title، command فرض می‌شود.
            dp = env.get("DASHBOARD_PORT", "8770") or "8770"
            brain_note = "مغز کنترل از قبل روشن بود — نمونهٔ دوم اجرا نشد (ضد Conflict تلگرام)."
            if not port_open(dp):
                if os.name == "nt":
                    subprocess.Popen('start "SecondBrain" cmd /k start.bat', shell=True,
                                     cwd=str(CB), env=utf8_env())
                else:
                    subprocess.Popen([venv_python(), "app.py"], cwd=str(CB), env=utf8_env())
                brain_note = "مغز کنترل در پنجرهٔ جدید روشن شد."
            # ۲) پنل‌های گوشی (اگر روشن نیستند)
            pp = env.get("PANEL_PORT", "8899") or "8899"
            panels_note = "پنل‌های گوشی از قبل روشن بودند."
            if not port_open(pp):
                if os.name == "nt":
                    subprocess.Popen(f'start "Panels" cmd /k ""{venv_python()}" panel_server.py"',
                                     shell=True, cwd=str(ROOT / "panels"), env=utf8_env())
                else:
                    subprocess.Popen([venv_python(), "panel_server.py"],
                                     cwd=str(ROOT / "panels"), env=utf8_env())
                panels_note = "پنل‌های گوشی هم روشن شدند (پنجرهٔ دوم)."
            threading.Timer(6, lambda: webbrowser.open(f"http://localhost:{dp}")).start()
            self._send(page(f'<div class="card"><h1 class="ok">🚀 مغز دوم در حال روشن شدن…</h1>'
                            f'<p>{brain_note} ربات تلگرام + همهٔ ماژول‌های enabled. داشبورد: <a href="http://localhost:{dp}">localhost:{dp}</a></p>'
                            f'<p>📱 {panels_note} آدرس روی گوشی (همان وای‌فای): <code>http://{lan_ip()}:{pp}/z</code> و <code>/f</code></p>'
                            f'<p>۳۰ ثانیه بعد دوباره 📡 گزارش اتصال بزن تا وضعیت زنده را ببینی.</p>{back}</div>'))
        else:
            self._send(page("<h1>?</h1>"), 404)


if __name__ == "__main__":
    print("مغز دوم — Setup wizard → http://localhost:%d  (Ctrl+C خروج)" % WIZARD_PORT)
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{WIZARD_PORT}")).start()
    HTTPServer(("127.0.0.1", WIZARD_PORT), H).serve_forever()
