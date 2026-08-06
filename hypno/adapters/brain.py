import json, urllib.request, re
from hypno.kernel.safety import script, mode_prompt
from hypno.kernel import edge

# ── نمره‌گیری از متن کاربر ───────────────────────────────────────────────────
# کلمات کلیدی فارسی/انگلیسی که ممکن است با یک عدد ۰-۱۰ بیاییند. نیم‌فاصله‌ها و
# مترادف‌ها را پوشش می‌دهیم. خروجی: dict نرمال‌شده به کلید‌های canonical که
# edge.py می‌فهمد، یا None اگر کمتر از ۲ نمره پیدا شد.
_KEYMAP = {
    # بدن
    'خواب': 'H', 'sleep': 'H', 'خوابیدن': 'H',
    'هوس': 'C', 'craving': 'C', 'پرخوری': 'C', 'binge': 'C',
    'مصرف': 'C', 'weed': 'C', 'دوز': 'C',
    'استرس': 'stress', 'stress': 'stress', 'اضطراب': 'stress',
    # خود بازتابی
    'ارزش': 'V', 'value': 'V', 'هماهنگی': 'V',
    'پیش‌تعهد': 'P', 'پیشتعهد': 'P', 'precommit': 'P', 'ازقبل': 'P',
    'پذیرش': 'K', 'هزینه': 'K', 'cost': 'K',
    'پایداری': 'D', 'تأخیر': 'D', 'delay': 'D', 'ماندگاری': 'D',
    # ابرموجود
    'ترند': 'E', 'trend': 'E', 'محرک': 'E', 'external': 'E', 'پلتفرم': 'E',
    'فومو': 'F', 'fomo': 'F', 'مقایسه': 'F',
    'پول': 'M', 'money': 'M', 'خانواده': 'M', 'فشار': 'M',
    'فوریت': 'U', 'urgent': 'U', 'هیجان': 'U',
    # روانزشتی خواب
    'بدهی': 'sleep_debt', 'sleepdebt': 'sleep_debt', 'خواب‌بدهی': 'sleep_debt',
    # جنبه‌های روزانه (B/C/X)
    'بدن': 'B', 'body': 'B',
    'حلقه': 'C_daily', 'بستن': 'C_daily', 'خروجی': 'C_daily', 'output': 'C_daily',
    'هزینهٔپنهان': 'X', 'هزینهٔ': 'X', 'پنهان': 'X',
}
_SCORE_RE = re.compile(
    r'([آ-یa-zA-Z‌\u200c]+)\s*[:：=]?\s*(\d{1,2})', re.UNICODE)

# حداقل این تعداد کلید canonical باید پیدا شود تا محاسبهٔ معنی‌دار باشد.
_MIN_FOR_DECISION = 4   # برای decision_source نیاز به مجموعه‌ای از ۱۲ متغیر است
_MIN_FOR_DAILY = 3      # برای daily_verdict فقط B, C, X


def _extract_scores(text):
    """نمره‌های ۰-۱۰ را از متن کاربر بکش و به کلیدهای canonical نگاشت کن.

    خروجی: dict (مثل {'H':3,'C':7,'stress':8,'E':6}) یا None.
    هر ارزش باید ۰ ≤ v ≤ ۱۰ باشد.
    """
    if not text:
        return None
    out = {}
    for m in _SCORE_RE.finditer(text):
        word = m.group(1).lower()
        try:
            val = int(m.group(2))
        except ValueError:
            continue
        if not (0 <= val <= 10):
            continue
        canon = _KEYMAP.get(word)
        if canon:
            out[canon] = val
    return out if out else None


def _edge_reply_from_scores(scores):
    """از نمره‌ها، یک جواب فارسی ساده بساز (بدون کلمهٔ فنی).

    اگر نمره‌ها کافی برای daily_verdict (B/C/X) بود، آن را محاسبه کن.
    در غیر این‌صورت اگر برای decision_source کافی بود، آن را.
    در غیر این‌صورت None برگردان.
    """
    if not scores:
        return None
    # daily: B, C_daily (یا C), X
    b = scores.get('B')
    c_daily = scores.get('C_daily') if 'C_daily' in scores else scores.get('C')
    x = scores.get('X')
    if b is not None and c_daily is not None and x is not None:
        v = edge.daily_verdict(b, c_daily, x)
        head = f"امروز — بدن {int(b)}، بستن‌حلقه {int(c_daily)}، هزینهٔ‌پنهان {int(x)}.\n"
        return head + f"حکم: {v.verdict}.\n{v.advice}"
    # decision: دست‌کم ۴ کلید از مجموعهٔ ۱۲ تا
    decision_keys = ('V', 'P', 'K', 'D', 'H', 'E', 'F', 'M', 'U', 'C',
                     'sleep_debt', 'stress')
    present = [k for k in decision_keys if k in scores]
    if len(present) >= _MIN_FOR_DECISION:
        defaults = {k: 5 for k in decision_keys}   # نمرهٔ خنثی برای متغیرهای غایب
        defaults.update(scores)
        r = edge.decision_source(
            defaults['V'], defaults['P'], defaults['K'], defaults['D'],
            defaults['H'], defaults['E'], defaults['F'], defaults['M'],
            defaults['U'], defaults['C'], defaults['sleep_debt'],
            defaults['stress'],
        )
        pct = lambda v: f"{int(round(v * 100))}٪"
        return (
            f"تجزیهٔ تصمیم:\n"
            f"  سهم خودت: {pct(r.dec.a_self)}\n"
            f"  سهم موجِ بیرون (بازار/ترند/فشار): {pct(r.dec.a_super)}\n"
            f"  سهم بدن (خستگی/هوس/گرسنگی): {pct(r.dec.a_body)}\n"
            f"{r.verdict}"
        )
    return None


# ── سیستم‌پرامپت‌ها ───────────────────────────────────────────────────────────
_BASE_SYSTEM = (
    'دستیار فارسی خودهیپنوتیزمی آری هستی. امن، علمی، رضایت‌محور، قابل‌قطع. '
    'درمان یا کنترل ذهن ادعا نکن. منبع‌هایی که در بافت آمده‌اند را طبیعی ذکر کن.'
)

EDGE_SYSTEM_PROMPT = (
    'تو دستیار فارسیِ خودهیپنوتیزمی و خودمدیریتِ آری هستی. دو بال داری:\n'
    '\n'
    '۱. خودهیپنوتیزمی: امن، علمی، رضایت‌محور، قابل‌قطع. جلسات کوتاه، '
    'چشم‌باز، با خروج مشخص. درمان یا کنترل ذهن ادعا نکن.\n'
    '\n'
    '۲. مدل لبهٔ سیستم: تصمیم‌های آری از سه منبع می‌آیند — بدن '
    '(خواب/هوس/خستگیری)، خود بازتابی (ارزش/برنامه/پایداری)، و ابرموجود '
    '(بازار/ترند/فشار). وقتی کاربر دربارهٔ تصمیم، خواب، فروش، فلو، مصرف، '
    'پرخوری، پول یا نقاشی حرف می‌زند، با این سه قطب فکر کن.\n'
    '\n'
    'قوانین:\n'
    '- اگر در بافت یک «تجزیهٔ تصمیم» آمده، آن را با زبان ساده تکرار کن: '
    '«سهم بدنت در این تصمیم بیشتر بود»، نه «BI=0.61».\n'
    '- هیچ‌وقت از کلمهٔ «RAG»، «model»، «token»، «API»، «schema»، «payload» '
    'استفاده نکن.\n'
    '- اگر نشانهٔ بحران (آسیب به خود، ناامیدی شدید) دیدی، فوراً به کمک '
    'واقعی ارجاع بده و جلسه را شروع نکن.\n'
    '- لحن گرم، مهربان و غیرفنی نگه دار.'
)


class Brain:
    def __init__(self, cfg): self.cfg = cfg

    def answer(self, text, mode, memories, passages, safety, edge_scores=None):
        """اگر edge_scores (dict از _extract_scores) داده شد، ابتدا تجزیهٔ مدل
        لبه را بساز و در بافت قرار بده؛ مغز می‌تواند به آن ارجاع دهد."""
        edge_reply = _edge_reply_from_scores(edge_scores)
        if self.cfg.api_key:
            try:
                return self.remote(text, mode, memories, passages, safety,
                                   edge_reply)
            except Exception:
                pass
        return self.rules(text, mode, memories, passages, safety, edge_reply)

    def rules(self, text, mode, memories, passages, safety, edge_reply=None):
        if edge_reply:
            out = edge_reply
        elif any(w in text for w in ('شروع', 'هیپنوتیز', 'جلسه')):
            out = script(mode, 5)
        elif any(w in text for w in ('یاد بده', 'چطور', 'آموزش')):
            out = ('روش پایه: هدف یک‌جمله‌ای، جای امن، تنفس آرام، پیشنهاد به '
                   'زبان انتخاب، نشانه آرامش، خروج با شمارش ۱ تا ۵، سپس ثبت نتیجه.')
        elif 'حافظه' in text:
            out = 'حافظه‌های فعلی:\n' + ('\n'.join('- ' + m for m in memories)
                                         or '- هنوز چیزی ثبت نشده')
        else:
            out = mode_prompt(mode) + '؛ اول یک هدف کوچک بنویس یا دکمهٔ شروع '
            'جلسهٔ امن را بزن.'
        if passages:
            out += '\n\nمنبع‌های مرتبط: ' + '؛ '.join(
                p['title'] for p in passages[:3])
        src = 'rules+مدل' if edge_reply else 'rules+دانش'
        r = {'reply': out, 'source': src, 'citations': passages[:3]}
        if edge_reply:
            r['edge'] = True
        return r

    def remote(self, text, mode, memories, passages, safety, edge_reply=None):
        ctx = 'حافظه:\n' + '\n'.join(memories)
        if passages:
            ctx += '\nدانش مرتبط:\n' + '\n'.join(
                f"[{p['title']}] {p.get('text', '')}" for p in passages)
        if edge_reply:
            ctx += '\nتجزیهٔ مدل لبهٔ سیستم (به این ارجاع بده):\n' + edge_reply
        system = EDGE_SYSTEM_PROMPT if edge_reply else _BASE_SYSTEM
        payload = {
            'model': self.cfg.model, 'temperature': 0.35,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': (
                    ctx + '\nایمنی: ' + safety + '\nحالت: ' + mode
                    + '\nپیام: ' + text
                )},
            ],
        }
        req = urllib.request.Request(
            self.cfg.base_url.rstrip('/') + '/chat/completions',
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + self.cfg.api_key},
        )
        obj = json.loads(urllib.request.urlopen(req, timeout=18).read().decode())
        r = {'reply': obj['choices'][0]['message']['content'].strip(),
             'source': 'remote:' + self.cfg.model,
             'citations': passages[:5]}
        if edge_reply:
            r['edge'] = True
            r['edge_analysis'] = edge_reply
        return r
