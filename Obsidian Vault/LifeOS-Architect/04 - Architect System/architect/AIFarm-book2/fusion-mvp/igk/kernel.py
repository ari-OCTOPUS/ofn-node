"""
kernel.py — هسته‌ی IGK (Immutable Grounding Kernel).

این کد *درونِ process کرنل* اجرا می‌شود (daemon.py آن را میزبانی می‌کند).
کلیدِ امضا فقط در همین process زندگی می‌کند و در سطحِ importِ ایجنت‌ها نیست.

مسئولیت‌ها (frozen):
  - audit امضاشده (HMAC) + زنجیره — جعل بدون کلید ناممکن.
  - permit با fail-closed: اگر STOP باشد یا قید نقض شود، permit صادر نمی‌شود.
  - grounding-validity: یک ادعا فقط اگر با سیگنالِ held-out (که ecology دستش به آن
    نمی‌رسد) سازگار باشد valid است. internal coherence لازم است نه کافی.
  - invariantها frozen-اند؛ هیچ verbـی برای تغییرشان در پروتکل وجود ندارد.
"""
from __future__ import annotations
import hmac, hashlib, json, os, time, secrets

CANON = {  # قیدهای سختِ frozen — صرفاً برای ثبت/شفافیت؛ تغییرناپذیر از بیرون
    "no_one_sided_victory": "هیچ پیروزی یک‌طرفه؛ قدرت از محدودیت.",
    "human_above": "override انسانی بالای همه؛ kill خارج از دسترسِ ایجنت.",
    "self_model_descriptive": "self-model فقط توصیفی، هرگز هدف.",
    "anchor_required": "هیچ به‌روزرسانی بی‌لنگرِ held-out معتبر نیست.",
}


def _canon(d: dict) -> bytes:
    return json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")


class Kernel:
    def __init__(self, state_dir: str, stop_path: str | None = None):
        self.dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        self.audit_path = os.path.join(state_dir, "audit.jsonl")
        # کلیدِ قطعِ بیرونی: انسان این فایل را می‌سازد. (پیش‌فرض داخلِ state_dir)
        self.stop_path = stop_path or os.path.join(state_dir, "STOP")
        self.key = self._load_or_make_key()
        self.held_out = self._load_held_out()
        self._used_nonces: set[str] = set()
        self._seq, self._prev = self._tail()

    # --- کلیدِ کرنل: فقط داخل همین process. (هشدار: ایزولاسیونِ واقعی نیازمند
    #     جداسازیِ کاربر/TEE است؛ این MVP مرز را در سطحِ process می‌گذارد.) ---
    def _load_or_make_key(self) -> bytes:
        p = os.path.join(self.dir, ".kernel_key")
        if os.path.exists(p):
            return open(p, "rb").read()
        k = secrets.token_bytes(32)
        with open(p, "wb") as f:
            f.write(k)
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass
        return k

    def _load_held_out(self) -> dict:
        p = os.path.join(self.dir, "held_out.json")
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
        return {}

    def _sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def _tail(self):
        seq, prev = 0, "GENESIS"
        if os.path.exists(self.audit_path):
            for line in open(self.audit_path, encoding="utf-8"):
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    seq, prev = rec["seq"], rec["sig"]
        return seq, prev

    # ---------- verbهای مجازِ پروتکل ----------
    def audit(self, event: str, actor: str, data: dict) -> dict:
        self._seq += 1
        rec = {"seq": self._seq, "ts": int(time.time()), "event": event,
               "actor": actor, "data": data, "prev": self._prev}
        rec["sig"] = self._sign(_canon(rec))
        self._prev = rec["sig"]
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return {"ok": True, "seq": rec["seq"], "sig": rec["sig"]}

    def verify(self) -> dict:
        prev, n, bad = "GENESIS", 0, None
        if os.path.exists(self.audit_path):
            for i, line in enumerate(open(self.audit_path, encoding="utf-8"), 1):
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                sig = rec.pop("sig")
                if rec["prev"] != prev:
                    bad = f"خط {i}: زنجیره می‌شکند"; break
                if not hmac.compare_digest(self._sign(_canon(rec)), sig):
                    bad = f"خط {i}: امضا نامعتبر (جعل/دستکاری)"; break
                prev, n = sig, n + 1
        return {"ok": bad is None, "count": n, "error": bad}

    def stopped(self) -> bool:
        return os.path.exists(self.stop_path)

    def permit(self, action: str, actor: str) -> dict:
        # fail-closed: STOP → هیچ permit. (kill خارج از کنترلِ ایجنت)
        if self.stopped():
            self.audit("permit_denied", actor, {"action": action, "reason": "STOP فعال"})
            return {"ok": False, "reason": "KILL-SWITCH فعال است (STOP)"}
        nonce = secrets.token_hex(8)
        tok = {"action": action, "actor": actor, "nonce": nonce,
               "exp": int(time.time()) + 30}
        tok["sig"] = self._sign(_canon({k: tok[k] for k in tok if k != "sig"}))
        self.audit("permit_issued", actor, {"action": action, "nonce": nonce})
        return {"ok": True, "token": tok}

    def consume(self, token: dict) -> dict:
        # درست پیش از actuation صدا زده می‌شود؛ دوباره STOP را چک می‌کند.
        if not isinstance(token, dict) or "sig" not in token:
            return {"ok": False, "reason": "token غایب/بدشکل"}
        sig = token.get("sig")
        body = {k: token[k] for k in token if k != "sig"}
        if not hmac.compare_digest(self._sign(_canon(body)), sig or ""):
            return {"ok": False, "reason": "امضای permit نامعتبر (جعل)"}
        if token["nonce"] in self._used_nonces:
            return {"ok": False, "reason": "permit قبلاً مصرف شده (replay)"}
        if time.time() > token["exp"]:
            return {"ok": False, "reason": "permit منقضی"}
        if self.stopped():
            return {"ok": False, "reason": "KILL-SWITCH فعال شد"}
        self._used_nonces.add(token["nonce"])
        self.audit("actuation", token["actor"], {"action": token["action"]})
        return {"ok": True}

    def ground(self, claims, actor: str) -> dict:
        # grounding-validity: هر ادعا در برابرِ held-out یکی از سه حکم می‌گیرد:
        #   ok           → subject را نام برد و value درستش را داشت
        #   contradicted → subject را نام برد ولی value نادرست/غایب بود (تناقضِ مکانیکی)
        #   unverifiable → به هیچ subjectـی از held-out مربوط نبود (بی‌لنگر = null)
        # ادعا می‌تواند رشته یا dict {"subject","value"} باشد.
        facts = self.held_out.get("facts", [])
        verdicts, bad = [], []
        for c in claims:
            v = self._judge(facts, c)
            verdicts.append(v)
            if v["verdict"] != "ok":
                bad.append({"claim": c, "verdict": v["verdict"]})
        valid = len(bad) == 0 and len(claims) > 0
        ratio = round(sum(1 for v in verdicts if v["verdict"] == "ok") / max(1, len(claims)), 3)
        self.audit("grounding", actor, {"valid": valid, "ratio": ratio, "bad": bad})
        return {"ok": valid, "grounding_ratio": ratio, "bad": bad, "verdicts": verdicts}

    @staticmethod
    def _judge(facts: list, claim) -> dict:
        # claimِ ساختاریافته: تطبیقِ مستقیمِ subject→value
        if isinstance(claim, dict):
            subj, val = claim.get("subject", "").lower(), str(claim.get("value", "")).lower()
            for f in facts:
                if f["subject"].lower() == subj:
                    return {"verdict": "ok" if str(f["value"]).lower() == val else "contradicted"}
            return {"verdict": "unverifiable"}
        # claimِ متنی: آیا subjectـی را نام می‌برد؟ اگر آری، value درست باید حاضر باشد.
        low = str(claim).lower()
        about_any = False
        for f in facts:
            subj_tokens = f["subject"].lower().split()
            if subj_tokens and all(t in low for t in subj_tokens):
                about_any = True
                if str(f["value"]).lower() not in low:
                    return {"verdict": "contradicted"}
        return {"verdict": "ok" if about_any else "unverifiable"}
