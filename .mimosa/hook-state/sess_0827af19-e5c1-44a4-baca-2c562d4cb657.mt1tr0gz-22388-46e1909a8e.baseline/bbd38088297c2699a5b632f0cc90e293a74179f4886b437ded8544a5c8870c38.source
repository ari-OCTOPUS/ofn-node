# -*- coding: utf-8 -*-
"""پنل‌های ساده مغز دوم — برای کسانی که با تکنولوژی راحت نیستند.

UI = چند دکمهٔ بزرگ فارسی روی گوشی. پشت صحنه = موتور واقعی:
  /z → پنل زیمان (تولید): ساخت DM/کپشن با موتور LLM (DeepSeek)، گارد ظرفیت D4، شمارندهٔ موجودی
  /f → پنل Project-F (صبا): قفل GATE 0 → تا باز نشدن فقط صفحهٔ انتظار؛ بعدش چک‌لیست شوت/تحویل/بافر

امنیت و استحکام (نامرئی برای کاربر):
  PIN جدا برای هر پنل (از .env: PANEL_PIN_Z / PANEL_PIN_F) · کوکی امضاشده
  sqlite برای state · events.jsonl append-only (audit) · فایل STOP = خاموشی تمیز
  هیچ secret ای در UI/لاگ · GATE 0 فقط خواندنی (بازکردنش دست آری است)

اجرا:  python panel_server.py   [--selftest]
"""
import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent
LIVE = ROOT.parent
CB = LIVE / "control-brain"
ZA = LIVE / "ziman-agent"
GATE = LIVE / "projectf-agent" / "GATE.yaml"
DB = ROOT / "state.db"
EVENTS = ROOT / "events.jsonl"
STOP = ROOT / "STOP"
SALT = "second-brain-panels-v1"


# ---------- زیرساخت ----------
def load_env():
    env = CB / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def pin_for(panel):
    return os.environ.get(f"PANEL_PIN_{panel.upper()}", "1111" if panel == "z" else "2222")


def token_for(panel):
    return hashlib.sha256((pin_for(panel) + SALT).encode()).hexdigest()[:24]


def audit(panel, action, detail=""):
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "panel": panel,
           "action": action, "detail": str(detail)[:200]}
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, panel TEXT, title TEXT,
                  done INTEGER DEFAULT 0, ts TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS deliveries
                 (id INTEGER PRIMARY KEY, ts TEXT, note TEXT)""")
    return c


def kv_get(c, k, default="0"):
    r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return r[0] if r else default


def kv_set(c, k, v):
    c.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=?", (k, str(v), str(v)))
    c.commit()


def gate_locked():
    if not GATE.exists():
        return True
    t = GATE.read_text(encoding="utf-8")
    return not any(line.strip().startswith("gate0:") and "closed" in line for line in t.splitlines())


def venv_python():
    for c in [CB / ".venv" / "Scripts" / "python.exe", CB / ".venv" / "bin" / "python"]:
        if c.exists():
            return str(c)
    return sys.executable


def ziman_make(kind, n=3):
    """اجرای موتور واقعی زیمان؛ خروجی = متن تازه‌ترین draft."""
    args = {"dm": ["--dm", str(n)], "posts": ["--posts", str(n)], "once": ["--once"]}[kind]
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([venv_python(), "worker.py", *args], cwd=str(ZA),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180, env=env)
    drafts = sorted((ZA / "drafts").glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if drafts:
        return True, drafts[0].read_text(encoding="utf-8")[:6000]
    return r.returncode == 0, (r.stdout + r.stderr)[-2000:]


def seed_f_tasks(c):
    if c.execute("SELECT COUNT(*) FROM tasks WHERE panel='f'").fetchone()[0] == 0:
        for t in ["آماده‌سازی نور و جای عکاسی", "ست اول: ۱۰ عکس طبق چک‌لیست",
                  "ست دوم: ۵ ویدیوی کوتاه", "دو نسخه ذخیره کن (با واترمارک / بدون)",
                  "ارسال فایل‌ها برای آری"]:
            c.execute("INSERT INTO tasks(panel,title,ts) VALUES('f',?,?)",
                      (t, datetime.now().isoformat(timespec="seconds")))
        c.commit()


# ---------- UI ----------
def page(title, body, panel=None):
    return f"""<!doctype html><html dir="rtl" lang="fa"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>
*{{box-sizing:border-box}} body{{font-family:Segoe UI,Tahoma,sans-serif;background:#101622;color:#f0f3fa;
max-width:480px;margin:0 auto;padding:16px;font-size:19px}}
h1{{font-size:24px;text-align:center;margin:12px 0 18px}}
.card{{background:#1b2436;border-radius:18px;padding:18px;margin:12px 0;box-shadow:0 2px 10px #0006}}
.btn{{display:block;width:100%;padding:20px;margin:10px 0;font-size:22px;font-weight:700;border:0;
border-radius:16px;background:#3b82f6;color:#fff;cursor:pointer;text-align:center;text-decoration:none}}
.btn.g{{background:#16a34a}} .btn.o{{background:#d97706}} .btn.r{{background:#dc2626}} .btn.gray{{background:#374151}}
.big{{font-size:44px;font-weight:800;text-align:center;margin:6px 0}}
.hint{{color:#9aa7bf;font-size:15px;text-align:center}}
pre{{white-space:pre-wrap;font-size:17px;background:#0c111c;padding:14px;border-radius:12px}}
input{{width:100%;padding:18px;font-size:26px;text-align:center;border-radius:14px;border:1px solid #334;
background:#0c111c;color:#fff;letter-spacing:8px}}
.bar{{height:14px;background:#2a3550;border-radius:99px;overflow:hidden}}
.fill{{height:100%;background:linear-gradient(90deg,#16a34a,#4ade80)}}
.done{{text-decoration:line-through;color:#7a8699}}
.row{{display:flex;gap:10px}} .row .btn{{flex:1}}</style></head><body>{body}
{'<p class="hint">🔒 امن — فقط توی خانه/وای‌فای خودمان</p>' if panel else ''}</body></html>"""


def pin_page(panel, err=""):
    err_html = '<p style="color:#f28b82;text-align:center">رمز اشتباه بود — دوباره</p>' if err else ''
    if panel == "z":
        return z_page(f"""
<div class="hero"><div class="logo">🎁</div><h1>Ziman Gift</h1>
<div class="sub">هدایای دست‌ساز لوکس · سیدنی</div></div>
<div class="card"><h2 style="text-align:center">رمز ۴ رقمی‌ات را بزن</h2>{err_html}
<form method="post" action="/z/login">
<input name="pin" type="tel" inputmode="numeric" maxlength="6" autofocus>
<button class="btn" type="submit">ورود</button></form></div>""")
    return page("ورود Project-F", f"""
<h1>📦 Project-F</h1>
<div class="card"><p style="text-align:center">رمز ۴ رقمی‌ات را بزن</p>{err_html}
<form method="post" action="/{panel}/login">
<input name="pin" type="tel" inputmode="numeric" maxlength="6" autofocus>
<button class="btn g" type="submit">ورود</button></form></div>""")


def ziman_cfg():
    """خواندن سبک اعداد/مناسبت‌ها از ziman.yaml — بدون وابستگی به PyYAML."""
    cfg = {"ceiling": 30, "occasions": [], "anchors": []}
    y = ZA / "ziman.yaml"
    if not y.exists():
        return cfg
    import re as _re
    txt = y.read_text(encoding="utf-8")
    m = _re.search(r"units_per_week_ceiling:\s*(\d+)", txt)
    if m:
        cfg["ceiling"] = int(m.group(1))
    m = _re.search(r'occasions:\s*\[(.*?)\]', txt)
    if m:
        cfg["occasions"] = [s.strip().strip('"').strip("'") for s in m.group(1).split(",")]
    for name, month in _re.findall(r'\{name:\s*"([^"]+)",\s*month:\s*(\d+)\}', txt):
        cfg["anchors"].append((name, int(month)))
    return cfg


def near_anchors(cfg, k=2):
    """نزدیک‌ترین مناسبت‌های تقویمی + فاصلهٔ ماه."""
    now_m = date.today().month
    out = []
    for name, m in cfg.get("anchors", []):
        d = (m - now_m) % 12
        out.append((d, name))
    out.sort()
    return [(n, d) for d, n in out[:k]]


def recent_drafts(n=4):
    out = []
    for f in sorted((ZA / "drafts").glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:n]:
        try:
            body = f.read_text(encoding="utf-8")
            out.append((f.stem[:40], body[:2500]))
        except Exception:  # noqa: BLE001
            pass
    return out


def z_page(body):
    """قالب لوکس زیمان — طلایی/کهربایی، فونت وزیرمتن، اسپینر و کپی یک‌لمسه."""
    return f"""<!doctype html><html dir="rtl" lang="fa"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ziman Gift</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
<style>
*{{box-sizing:border-box}}
body{{font-family:Vazirmatn,Segoe UI,Tahoma,sans-serif;margin:0;color:#f3ead9;font-size:18px;
background:radial-gradient(1200px 500px at 50% -10%, #2b2118 0%, #171210 55%, #100d0b 100%);min-height:100vh}}
.wrap{{max-width:470px;margin:0 auto;padding:14px 14px 40px}}
.hero{{text-align:center;padding:22px 10px 14px}}
.hero .logo{{font-size:44px}}
.hero h1{{margin:4px 0 2px;font-size:26px;font-weight:800;
background:linear-gradient(90deg,#e9c87c,#c9973f,#f1dcae);-webkit-background-clip:text;background-clip:text;color:transparent}}
.hero .sub{{color:#b9a684;font-size:14px;letter-spacing:1px}}
.card{{background:linear-gradient(160deg,#241c14,#1b1510);border:1px solid #3a2f20;border-radius:22px;
padding:18px;margin:12px 0;box-shadow:0 6px 22px #0009}}
.card h2{{margin:0 0 10px;font-size:18px;color:#e9c87c}}
.stats{{display:flex;gap:10px}}
.stat{{flex:1;text-align:center;background:#171210;border:1px solid #3a2f20;border-radius:18px;padding:12px 6px}}
.stat .n{{font-size:30px;font-weight:800;color:#f1dcae}}
.stat .l{{font-size:12.5px;color:#b9a684;margin-top:2px}}
.ring{{width:84px;height:84px;margin:0 auto;display:block}}
.btn{{display:block;width:100%;padding:17px;margin:9px 0;font-size:19px;font-weight:700;border:0;border-radius:16px;
cursor:pointer;text-align:center;text-decoration:none;color:#1b1510;
background:linear-gradient(90deg,#e9c87c,#cfa04d);box-shadow:0 4px 14px #0007;transition:transform .08s}}
.btn:active{{transform:scale(.985)}}
.btn.dark{{background:#2c2318;color:#f1dcae;border:1px solid #4a3b26}}
.btn.copy{{background:#3f6b3f;color:#eaf5ea;font-size:17px;padding:13px}}
.chip{{display:inline-block;background:#2c2318;border:1px solid #4a3b26;color:#e9c87c;border-radius:99px;
padding:6px 14px;margin:4px 3px;font-size:14px}}
pre{{white-space:pre-wrap;font-size:16px;line-height:1.9;background:#12100c;border:1px solid #3a2f20;
padding:14px;border-radius:14px;color:#f3ead9}}
details{{background:#171210;border:1px solid #3a2f20;border-radius:14px;padding:10px 14px;margin:8px 0}}
summary{{cursor:pointer;color:#e9c87c;font-weight:700}}
.hint{{color:#8f7f63;font-size:13.5px;text-align:center;margin-top:14px}}
input{{width:100%;padding:18px;font-size:26px;text-align:center;border-radius:14px;border:1px solid #4a3b26;
background:#12100c;color:#f1dcae;letter-spacing:8px;font-family:inherit}}
#ov{{display:none;position:fixed;inset:0;background:#0c0a08ee;z-index:9;align-items:center;justify-content:center;flex-direction:column}}
.spin{{width:54px;height:54px;border-radius:50%;border:5px solid #3a2f20;border-top-color:#e9c87c;animation:r 1s linear infinite}}
@keyframes r{{to{{transform:rotate(360deg)}}}}
#toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#3f6b3f;color:#fff;
padding:12px 26px;border-radius:99px;display:none;z-index:10;font-weight:700}}
.msg{{text-align:center;background:#233a23;border:1px solid #3f6b3f;border-radius:14px;padding:10px;margin:10px 0;color:#c9e8c9}}
</style></head><body><div class="wrap">{body}</div>
<div id="ov"><div class="spin"></div><p style="color:#e9c87c;margin-top:14px">زیمان دارد می‌نویسد… ✨</p></div>
<div id="toast">کپی شد ✔</div>
<script>
function busy(){{document.getElementById('ov').style.display='flex';return true}}
function cpy(){{var d=document.getElementById('draft');if(!d)return;
var ta=document.createElement('textarea');ta.value=d.innerText;document.body.appendChild(ta);
ta.select();try{{document.execCommand('copy')}}catch(e){{}}document.body.removeChild(ta);
var t=document.getElementById('toast');t.style.display='block';setTimeout(()=>t.style.display='none',1800)}}
</script></body></html>"""


def z_home(msg="", draft=""):
    c = db()
    today = date.today().isoformat()
    made = int(kv_get(c, f"z_made_{today}", "0"))
    inv = int(kv_get(c, "z_inventory", "20"))
    week_used = int(kv_get(c, f"z_week_{date.today().isocalendar()[1]}", "0"))
    c.close()
    cfg = ziman_cfg()
    ceil_ = max(1, cfg["ceiling"])
    pct = min(100, int(week_used * 100 / ceil_))
    dash = 264 * pct / 100  # محیط حلقه r=42
    ring = f"""<svg class="ring" viewBox="0 0 100 100">
<circle cx="50" cy="50" r="42" fill="none" stroke="#3a2f20" stroke-width="9"/>
<circle cx="50" cy="50" r="42" fill="none" stroke="#e9c87c" stroke-width="9" stroke-linecap="round"
 stroke-dasharray="{dash:.0f} 264" transform="rotate(-90 50 50)"/>
<text x="50" y="47" text-anchor="middle" fill="#f1dcae" font-size="19" font-weight="800">{week_used}</text>
<text x="50" y="64" text-anchor="middle" fill="#8f7f63" font-size="10">از {ceil_}</text></svg>"""
    occ = "".join(f'<span class="chip">🎉 {o}</span>' for o in cfg["occasions"][:4])
    anch = "".join(
        f'<span class="chip">📅 {n} — {"همین ماه!" if d == 0 else f"{d} ماه دیگر"}</span>'
        for n, d in near_anchors(cfg))
    msg_html = f'<div class="msg">{msg}</div>' if msg else ""
    draft_html = ""
    if draft:
        draft_html = (f'<div class="card"><h2>✨ متن آماده است</h2><pre id="draft">{draft}</pre>'
                      f'<button class="btn copy" onclick="cpy()">📋 کپی متن</button></div>')
    hist = "".join(f"<details><summary>🗂 {name}</summary><pre>{body}</pre></details>"
                   for name, body in recent_drafts())
    hist_html = f'<div class="card"><h2>متن‌های قبلی</h2>{hist}</div>' if hist else ""
    return z_page(f"""
<div class="hero"><div class="logo">🎁</div><h1>Ziman Gift</h1>
<div class="sub">هدایای دست‌ساز لوکس · سیدنی</div></div>
{msg_html}{draft_html}
<div class="stats">
<div class="stat">{ring}<div class="l">ظرفیت این هفته</div></div>
<div class="stat"><div class="n">{inv}</div><div class="l">موجودی آماده</div></div>
<div class="stat"><div class="n">{made}</div><div class="l">متنِ امروز</div></div>
</div>
<div class="card"><h2>✍️ چه متنی برایت بنویسم؟</h2>
<form method="post" action="/z/make" onsubmit="busy()"><input type="hidden" name="kind" value="dm">
<button class="btn">💬 پیام برای مشتری‌ها</button></form>
<form method="post" action="/z/make" onsubmit="busy()"><input type="hidden" name="kind" value="posts">
<button class="btn dark">📸 کپشن اینستاگرام</button></form>
<form method="post" action="/z/make" onsubmit="busy()"><input type="hidden" name="kind" value="once">
<button class="btn dark">💡 ایدهٔ امروز</button></form>
<p class="hint">چند ثانیه صبر کن — زیمان خودش می‌نویسد</p></div>
<div class="card"><h2>📦 موجودی</h2>
<div class="stats">
<form method="post" action="/z/inv" style="flex:1"><input type="hidden" name="d" value="1">
<button class="btn" style="margin:0">+۱ ساختم</button></form>
<form method="post" action="/z/inv" style="flex:1"><input type="hidden" name="d" value="-1">
<button class="btn dark" style="margin:0">−۱ فروختم</button></form>
</div></div>
<div class="card"><h2>مناسبت‌های ما</h2>{anch}{occ}</div>
{hist_html}
<p class="hint">🔒 امن — فقط توی خانه/وای‌فای خودمان</p>""")


def f_home(msg=""):
    if gate_locked():
        return page("Project-F", """
<h1>📦 Project-F</h1>
<div class="card" style="text-align:center">
<div style="font-size:56px">💛</div>
<p><b>همه‌چیز آماده است — فقط منتظر یک تأیید هستیم.</b></p>
<p>فعلاً هیچ کاری لازم نیست انجام بدهی.<br>هر وقت باز شد، همین‌جا کارهای روزت را می‌بینی.</p>
<a class="btn" href="https://t.me/" target="_blank">💬 پیام به آری</a></div>""", "f")
    c = db()
    seed_f_tasks(c)
    tasks = c.execute("SELECT id,title,done FROM tasks WHERE panel='f' ORDER BY id").fetchall()
    buf = int(kv_get(c, "f_buffer_days", "0"))
    deliv = c.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    c.close()
    rows = ""
    for tid, title, done in tasks:
        cls = "done" if done else ""
        btn = "" if done else (f'<form method="post" action="/f/done" style="flex:0 0 130px">'
                               f'<input type="hidden" name="id" value="{tid}">'
                               f'<button class="btn g" style="padding:12px;font-size:17px">انجام شد ✅</button></form>')
        rows += f'<div class="row" style="align-items:center;margin:8px 0"><div style="flex:1" class="{cls}">{title}</div>{btn}</div>'
    msg_html = f'<div class="card" style="text-align:center">{msg}</div>' if msg else ""
    return page("Project-F", f"""
<h1>📦 Project-F — کارهای من</h1>
{msg_html}
<div class="card"><b>📋 کارهای این هفته:</b>{rows}</div>
<div class="card"><b>🗂 ذخیرهٔ محتوا:</b><div class="big">{buf} روز</div>
<p class="hint">هدف: همیشه ۷ روز یا بیشتر</p>
<form method="post" action="/f/buffer"><input type="hidden" name="d" value="1">
<button class="btn g">+۱ روز محتوا آماده کردم</button></form></div>
<div class="card"><b>📤 تحویل‌ها: {deliv}</b>
<form method="post" action="/f/deliver"><button class="btn o">📤 امروز فایل‌ها را فرستادم</button></form></div>""", "f")


# ---------- HTTP ----------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, html, cookies=None):
        b = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        for ck in cookies or []:
            self.send_header("Set-Cookie", ck)
        self.end_headers()
        self.wfile.write(b)

    def _authed(self, panel):
        ck = self.headers.get("Cookie", "")
        return f"sb_{panel}={token_for(panel)}" in ck.replace(" ", "")

    def do_GET(self):
        p = self.path.split("?")[0].rstrip("/") or "/"
        if p == "/":
            self._send(page("مغز دوم", """
<h1>🧠 مغز دوم</h1>
<a class="btn" href="/z">🎁 زیمان</a>
<a class="btn o" href="/f">📦 Project-F</a>"""))
        elif p in ("/z", "/f"):
            panel = p[1]
            if not self._authed(panel):
                self._send(pin_page(panel))
            else:
                self._send(z_home() if panel == "z" else f_home())
        else:
            self._send(page("؟", '<div class="card">پیدا نشد — <a href="/">برگرد خانه</a></div>'))

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(n).decode("utf-8"))
        p = self.path.rstrip("/")
        panel = p[1] if len(p) > 1 else ""
        if p.endswith("/login"):
            if form.get("pin", [""])[0].strip() == pin_for(panel):
                audit(panel, "login")
                self._send('<meta http-equiv="refresh" content="0;url=/%s">' % panel,
                           [f"sb_{panel}={token_for(panel)}; Path=/; Max-Age=604800; HttpOnly"])
            else:
                audit(panel, "login-fail")
                time.sleep(1.5)  # ضد حدس زدن
                self._send(pin_page(panel, err="1"))
            return
        if not self._authed(panel):
            self._send(pin_page(panel))
            return
        if p == "/z/make":
            kind = form.get("kind", ["once"])[0]
            audit("z", "make", kind)
            ok, out = ziman_make(kind)
            if ok:  # فقط ساخت موفق در ظرفیت/آمار شمرده می‌شود
                c = db()
                today = date.today().isoformat()
                kv_set(c, f"z_made_{today}", int(kv_get(c, f"z_made_{today}", "0")) + 1)
                wk = f"z_week_{date.today().isocalendar()[1]}"
                kv_set(c, wk, int(kv_get(c, wk, "0")) + 1)
                c.close()
            self._send(z_home(msg="" if ok else "⚠️ ساخت متن مشکل داشت — دوباره بزن",
                              draft=out if ok else ""))
        elif p == "/z/inv":
            d = int(form.get("d", ["0"])[0])
            c = db()
            kv_set(c, "z_inventory", max(0, int(kv_get(c, "z_inventory", "20")) + d))
            c.close()
            audit("z", "inventory", d)
            self._send(z_home(msg="ثبت شد ✅"))
        elif p == "/f/done" and not gate_locked():
            c = db()
            c.execute("UPDATE tasks SET done=1 WHERE id=? AND panel='f'", (int(form.get("id", ["0"])[0]),))
            c.commit(); c.close()
            audit("f", "task-done", form.get("id", [""])[0])
            self._send(f_home(msg="آفرین! ثبت شد ✅"))
        elif p == "/f/buffer" and not gate_locked():
            c = db()
            kv_set(c, "f_buffer_days", int(kv_get(c, "f_buffer_days", "0")) + 1)
            c.close()
            audit("f", "buffer+1")
            self._send(f_home(msg="ثبت شد ✅"))
        elif p == "/f/deliver" and not gate_locked():
            c = db()
            c.execute("INSERT INTO deliveries(ts,note) VALUES(?,?)",
                      (datetime.now().isoformat(timespec="seconds"), "panel"))
            c.commit(); c.close()
            audit("f", "delivery")
            self._send(f_home(msg="تحویل ثبت شد ✅ دستت درد نکنه"))
        else:
            self._send(f_home() if panel == "f" else z_home())


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:  # noqa: BLE001
        return "127.0.0.1"


def main():
    load_env()
    if "--selftest" in sys.argv:
        c = db(); seed_f_tasks(c); c.close()
        assert token_for("z") != token_for("f")
        print(f"selftest ok — gate0 {'locked' if gate_locked() else 'open'} · db OK")
        return 0
    port = int(os.environ.get("PANEL_PORT", "8899"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    print(f"پنل‌ها روشن → روی گوشی (همان وای‌فای): http://{lan_ip()}:{port}/z  و  /f")

    def watch_stop():
        while True:
            if STOP.exists():
                srv.shutdown()
                return
            time.sleep(5)
    threading.Thread(target=watch_stop, daemon=True).start()
    srv.serve_forever()
    print("STOP — خاموش شد.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
