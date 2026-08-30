"""
test_grounding.py — گیتِ grounding-validity: ادعای درست عبور، متناقض/بی‌لنگر رد.
"""
import sys, os, tempfile, shutil, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import KernelClient

results = []
def check(n, c): results.append((n, c)); print(f"  {'✅' if c else '❌'} {n}")

d = tempfile.mkdtemp(prefix="grnd_")
shutil.copy(os.path.join(os.path.dirname(__file__), "held_out.json"),
            os.path.join(d, "held_out.json"))
k = KernelClient(d)

# ۱) ادعای درست (متنی) → ok
g = k.ground(["پایتخت استرالیا کانبرا است"], "researcher")
check("۱: ادعای درست عبور می‌کند (ok)", g["ok"] is True and g["grounding_ratio"] == 1.0)

# ۲) ادعای متناقض → contradicted، رد
g = k.ground(["پایتخت استرالیا سیدنی است"], "researcher")
check("۲: ادعای متناقض رد می‌شود (contradicted)",
      g["ok"] is False and g["bad"][0]["verdict"] == "contradicted")

# ۳) ادعای بی‌ربط به held-out → unverifiable، رد
g = k.ground(["قیمت قهوه امروز بالا رفت"], "researcher")
check("۳: ادعای بی‌لنگر رد می‌شود (unverifiable)",
      g["ok"] is False and g["bad"][0]["verdict"] == "unverifiable")

# ۴) ترکیبی → ratio کسری
g = k.ground(["پایتخت فرانسه پاریس است", "پایتخت استرالیا سیدنی است"], "researcher")
check("۴: مجموعه‌ی نیمه‌درست ratio=0.5 و رد", g["grounding_ratio"] == 0.5 and g["ok"] is False)

# ۵) claimِ ساختاریافته (dict) → تطبیقِ مستقیم
g_ok = k.ground([{"subject": "نقطه جوش آب", "value": "صد"}], "researcher")
g_no = k.ground([{"subject": "نقطه جوش آب", "value": "نود"}], "researcher")
check("۵: claimِ ساختاریافته‌ی درست/غلط درست داوری می‌شود",
      g_ok["ok"] is True and g_no["ok"] is False)
k.close()

print("\n" + "=" * 50)
ok = sum(1 for _, c in results if c)
print(f"نتیجه: {ok}/{len(results)} سبز")
sys.exit(0 if ok == len(results) else 1)
