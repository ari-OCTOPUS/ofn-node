from dataclasses import dataclass
@dataclass(frozen=True)
class Decision: allow:bool; level:str; message:str
CRISIS=('خودکشی','خودمو بکشم','suicide','kill myself','self harm')
UNSAFE=('رانندگی','پشت فرمان','driving','drive','کار با دستگاه','شنا','در آب')
CLINICAL=('روانپریشی','روان‌پریشی','psychosis','schizophrenia','تشنج','صرع','seizure','فلش بک','flashback','mania')
COERCE=('کنترل ذهن','کنترلم کن','mind control','پاک کردن حافظه','erase memory','مجبورم کن')
RULE='من فقط خودهیپنوتیزمی داوطلبانه، قابل‌قطع و آموزشی ارائه می‌دهم؛ نه درمان پزشکی و نه کنترل ذهن. اگر رانندگی/کار با دستگاه/در آب هستی تمرین را شروع نکن.'
def classify(text):
    t=(text or '').lower()
    if any(k.lower() in t for k in CRISIS): return Decision(False,'crisis','اگر احتمال آسیب به خودت یا دیگری هست، همین حالا با اورژانس یا یک فرد امن محلی تماس بگیر. جلسه هیپنوتیزم را شروع نمی‌کنم، ولی می‌توانم برای قدم امن بعدی کنار تو بمانم.')
    if any(k.lower() in t for k in UNSAFE): return Decision(False,'unsafe_context','برای خودهیپنوتیزمی باید در جای امن باشی؛ نه رانندگی، نه دستگاه، نه آب. وقتی امن شدی بگو «آماده‌ام».')
    if any(k.lower() in t for k in COERCE): return Decision(False,'coercion','این اپ کنترل ذهن، اجبار، پیشنهاد پنهان یا پاک‌کردن حافظه انجام نمی‌دهد؛ فقط تمرین داوطلبانه و قابل‌قطع.')
    if any(k.lower() in t for k in CLINICAL): return Decision(True,'clinical_caution','با این پیش‌زمینه فقط تمرین‌های کوتاه، چشم‌باز و آرام‌سازی عمومی پیشنهاد می‌دهم؛ برای درمان با متخصص هماهنگ کن.')
    return Decision(True,'ok',RULE)
def mode_prompt(m):
    return {'calm':'آرام‌سازی و تنظیم توجه','sleep':'آماده‌سازی خواب بدون وعده درمان','focus':'تمرکز و شروع کار','learn':'آموزش مرحله‌به‌مرحله','custom':'هدف شخصی با ایمنی کامل'}.get((m or 'calm').lower(),'آرام‌سازی')
def script(mode='calm',minutes=5):
    minutes=max(2,min(15,int(minutes or 5)))
    return f'''جلسه امن {minutes} دقیقه‌ای ({mode}):
۱) تأیید کن در جای امنی و هر لحظه می‌توانی چشم‌ها را باز کنی.
۲) سه نفس آرام؛ بازدم کمی طولانی‌تر از دم.
۳) توجه را روی یک حس بدن/صدا/نقطه نگه دار؛ لازم نیست اتفاق خاصی بیفتد.
۴) پیشنهاد مالکانه: «من انتخاب می‌کنم آرام‌تر شوم» و «هر لحظه می‌توانم توقف کنم».
۵) نشانه آرامش: لمس شست و اشاره فقط وقتی خودت بخواهی.
۶) خروج: از ۱ تا ۵ بشمار، بدن را حرکت بده، چشم‌ها را باز کن، آب بنوش.'''
