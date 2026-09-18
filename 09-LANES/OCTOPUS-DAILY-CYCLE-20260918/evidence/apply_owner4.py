#!/usr/bin/env python3
"""Apply the owner's four answers (2026-09-18, ZCode chat):
 1) standing send authorization 14d/<=10day  -> i7 hold off + money_tools honours it
 2) organic demand channel                    -> campaign plan + progress ledger
 3) ziman limited release                     -> scope recorded
 4) repo public authorized                    -> (handled outside, noted here)
Pre-image + receipt for every write."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
I7 = RD / "i7-runtime.json"
MT = RD / "money_tools.py"
REC = RD / "receipts.jsonl"
DEC = RD / "owner-decisions.jsonl"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


pre = {}
for p in (I7, MT):
    shutil.copy2(p, str(p) + ".pre-owner4-" + TS)
    pre[str(p)] = sha(p)

# ---- 1. i7 hold OFF, scoped by the standing authorization ----
i7 = json.loads(I7.read_text(encoding="utf-8"))
auth = json.loads((RD / "standing-authorization.json").read_text(encoding="utf-8"))
i7_before = dict(i7)
i7["mode"] = "standing_authorized"
i7["no_auto_customer_send"] = False
i7["customer_send"] = True
i7["standing_authorization"] = {"granted_at": auth["granted_at"],
                                "expires_at": auth["scope"]["expires_at"],
                                "daily_cap": auth["scope"]["daily_cap"],
                                "recipients": auth["scope"]["recipients"],
                                "ziman": auth["scope"]["ziman"],
                                "source": auth["source"] if "source" in auth else auth["granted_by"],
                                "revoke": auth["revoke"]}
I7.write_text(json.dumps(i7, ensure_ascii=False, indent=1), encoding="utf-8")
print("i7: mode %s->%s  no_auto_customer_send %s->%s" % (
    i7_before.get("mode"), i7["mode"], i7_before.get("no_auto_customer_send"),
    i7["no_auto_customer_send"]))

# ---- 2. money_tools honours the standing authorization ----
s = MT.read_text(encoding="utf-8")
HELPER = '''def _standing_authorization():
    """Owner standing authorization (2026-09-18): 14 days, <=10 sends/day, approved
    templates, existing leads only. Returns (ok, why). Revocable at any time."""
    import json as _j, time as _t, pathlib as _p
    base = _p.Path(__file__).resolve().parent
    if (base / "AUTH-REVOKED").exists():
        return False, "REVOKED"
    try:
        d = _j.loads((base / "standing-authorization.json").read_text(encoding="utf-8"))
    except Exception:
        return False, "NO_AUTH_FILE"
    sc = d.get("scope") or {}
    if _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()) > str(sc.get("expires_at") or ""):
        return False, "EXPIRED"
    cap = int(sc.get("daily_cap") or 0)
    today = _t.strftime("%Y-%m-%d", _t.gmtime())
    n = 0
    try:
        for line in (base / "sent-log.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = _j.loads(line)
            if str(r.get("at", "")).startswith(today):
                n += 1
    except Exception:
        pass
    if cap and n >= cap:
        return False, "DAILY_CAP_REACHED(%d)" % n
    return True, "STANDING_AUTH"


def execute_money_batch(packets, email_authorized):'''
assert s.count("def execute_money_batch(packets, email_authorized):") == 1
s = s.replace("def execute_money_batch(packets, email_authorized):", HELPER)
old_gate = "    if email_authorized:"
new_gate = ('    _sa_ok, _sa_why = _standing_authorization()\n'
            '    if not email_authorized and _sa_ok:\n'
            '        email_authorized = True\n'
            '        receipt("STANDING_AUTH_USED", why=_sa_why)\n'
            '    if email_authorized:')
assert s.count(old_gate) == 1
s = s.replace(old_gate, new_gate)
MT.write_text(s, encoding="utf-8", newline="\n")
print("money_tools patched:", pre[str(MT)][:12], "->", sha(MT)[:12])

# ---- 3. record the four decisions + receipt ----
with DEC.open("a", encoding="utf-8") as fh:
    for row in [
        {"at": NOW, "decision": "STANDING_SEND_AUTH_GRANTED", "kind": "owner-chat",
         "meaning": "14 days, <=10 emails/day, approved templates, existing leads only; revocable",
         "source": "owner 4-option answer (ZCode chat 2026-09-18)", "verbatim": "۱۴ روز، ≤۱۰/روز (پیشنهاد)"},
        {"at": NOW, "decision": "DEMAND_CHANNEL=ORGANIC_SELF_BUILT", "kind": "owner-chat",
         "meaning": "agent builds the organic channel itself, no paid ads",
         "source": "owner 4-option answer", "verbatim": "کانال ارگانیک را خودم بسازم"},
        {"at": NOW, "decision": "ZIMAN=LIMITED_RELEASE", "kind": "owner-chat",
         "meaning": "hold lifted, limited to existing ziman emails under the standing authorization",
         "source": "owner 4-option answer", "verbatim": "آزادسازی محدود (پیشنهاد)"},
        {"at": NOW, "decision": "REPO_PUBLIC_AUTHORIZED", "kind": "owner-chat",
         "meaning": "owner authorises keeping the repo public and publishing vault content",
         "source": "owner 4-option answer", "verbatim": "همه چیو فعلا عمومی کن اجازه می‌دم"}]:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

REC.parent.mkdir(parents=True, exist_ok=True)
with REC.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"schema": "octopus.fix-receipt.v1", "id": "OWNER4-" + TS,
                         "at": NOW, "node": "138",
                         "what": "owner's four answers applied: i7 send-hold OFF under a scoped "
                                 "standing authorization (14d, cap 10/day, existing leads), "
                                 "money_tools consults it (STANDING_AUTH_USED receipt, "
                                 "AUTH-REVOKED/expiry/cap all enforced), ziman scope recorded, "
                                 "repo-public authorization noted",
                         "files": [{"file": str(I7), "sha_before": pre[str(I7)], "sha_after": sha(I7)},
                                   {"file": str(MT), "sha_before": pre[str(MT)], "sha_after": sha(MT)}],
                         "rollback": "cp <preimage> <file>",
                         "preimages": [str(I7) + ".pre-owner4-" + TS, str(MT) + ".pre-owner4-" + TS]},
                        ensure_ascii=False, sort_keys=True) + "\n")

# ---- 4. organic channel: campaign plan + ledger ----
camp = RD / "campaign"
camp.mkdir(exist_ok=True)
(camp / "ORGANIC-CHANNEL-PLAN.md").write_text(
    "# کانال ارگانیک — تصمیم مالک 2026-09-18 (بدون هزینه)\n\n"
    "## هدف\nبازدید/سفارش از دو کسب‌وکار (نقاشی B2B + آتلیه) از مسیرهای بدون پرداخت.\n\n"
    "## گام‌های اول (فهرست اجرا)\n"
    "1. پروفایل Google Business (معلق به لاگین مالک) — بزرگ‌ترین اهرم محلی. [owner-login]\n"
    "2. فهرست‌شدن در دایرکتوری‌های صنفی (YP/Hotfrog) — مسیر معدود ولی رایگان; کپچاها ثبت‌شده.\n"
    "3. محتوای قابل جستجو برای آتلیه (توضیح محصول، قیمت شفاف، عکس) — پیش‌نیاز ایندکس شدن.\n"
    "4. ارجاع از مشتری موجود پس از اولین پروژه (referral).\n"
    "5. انتشار برگهٔ خدمات نقاشی با نمونه‌کار در لینکدین/انجمن‌های استراتا.\n\n"
    "## سنجه\n`state/revenue-drive/campaign/progress.jsonl` — هر اقدام: {at, step, url, result}.\n"
    "نرخ موفقیت = بازدید/تماس ورودی؛ نه تعداد فعالیت.\n", encoding="utf-8")
(camp / "progress.jsonl").write_text(json.dumps(
    {"at": NOW, "step": "plan-created", "url": "campaign/ORGANIC-CHANNEL-PLAN.md",
     "result": "owner chose organic; plan written"}, ensure_ascii=False) + "\n",
    encoding="utf-8")
print("campaign plan + progress ledger written")
print("DONE")
