#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schumann_rx.py — گیرندهٔ شومان با گیتِ کیفیتِ درونی.

جایگزینِ اسکریپتِ اولیه. تفاوت‌های اصلی (هرکدام یک باگِ سنجیده‌شده را می‌بندد):

  1. فاز/دامنه از *وسطِ* پنجره خوانده می‌شود، نه [-1].
     اندازه‌گیری: خطای میانهٔ فاز از ۲۹.۱° به ۲.۷° می‌رسد (۱۰.۸ برابر بهتر).
  2. برچسبِ زمانِ دستگاه مبناست، نه زمانِ رسیدنِ بسته.
     لرزشِ ۲۰ms در WiFi = ۵۶° خطای فاز؛ بدونِ timestamp فاز بی‌معناست.
  3. دامنه روی پنجرهٔ ۶۰ ثانیه‌ای، نه ۱ ثانیه. SNR از ~۵ به ~۳۹ می‌رسد.
  4. خروجی در **پیکوتسلا** است، نه شمارندهٔ ADC. بدونِ ثابتِ کالیبراسیون
     ماژول عدد نمی‌دهد (fail-closed) — چون tanh(شمارندهٔ خام) همیشه ۱.۰ اشباع می‌شود.
  5. هر خروجی یک **کیفیتِ w_q ∈ [0,1]** دارد. w_q پایین ⇒ مصرف‌کننده باید نادیده بگیرد.
     w_q از چهار چیزِ سنجیدنی می‌آید: نردبانِ هارمونیک، SNR، لرزشِ ساعت، سنِ کالیبراسیون.
  6. `verdict()` دو تستِ ابطال را اجرا می‌کند: نردبانِ هارمونیک، و UTC-در-برابر-محلی.
     تا هر دو سبز نشوند، `is_proven` برابر False می‌ماند.

فلسفه: این ماژول یک **ابزارِ اندازه‌گیری** است، نه یک منبعِ الهام. اگر نمی‌داند
چه چیزی را اندازه گرفته، عدد نمی‌دهد.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import butter, filtfilt, hilbert, welch

FS_DEFAULT = 256.0
F0 = 7.83
# نردبانِ کاواکِ زمین-یونوسفر. توجه: سریِ صحیح نیست (۲×۷.۸۳=۱۵.۷ ≠ ۱۴.۳).
# همین «غیرصحیح بودن» است که امضایش را جعل‌ناپذیر می‌کند.
SR_LADDER = (7.83, 14.3, 20.8, 27.3, 33.8)


@dataclass
class Reading:
    ts_utc: float
    amplitude_pT: float | None
    phase_rad: float | None
    snr: float
    w_q: float                      # وزنِ کیفیت ∈ [0,1] — مصرف‌کننده باید در این ضرب کند
    reasons: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        return self.amplitude_pT is not None and self.w_q >= 0.5


class SchumannReceiver:
    def __init__(self, fs: float = FS_DEFAULT,
                 cal_pT_per_count: float | None = None,
                 amp_window_s: float = 60.0,
                 max_jitter_ms: float = 8.0,
                 hop: int | None = None):
        self.fs = fs
        self.cal = cal_pT_per_count          # None ⇒ fail-closed، هیچ عددِ فیزیکی
        self.amp_window_s = amp_window_s
        self.max_jitter_ms = max_jitter_ms
        n = int(fs * amp_window_s)
        self.buf: deque[float] = deque(maxlen=n)
        self.ts: deque[float] = deque(maxlen=n)
        self._jitter_ms = 0.0
        self._b, self._a = butter(3, [7.0 / (fs / 2), 9.0 / (fs / 2)], btype="band")
        # زمان‌بندِ hop — با شمارندهٔ **مستقلِ یکنوا**، نه با len(buf).
        self.hop = max(1, int(hop or fs))       # پیش‌فرض: یک بار در ثانیه
        self._n_seen = 0                         # هرگز ری‌ست نمی‌شود
        self._n_last = -1

    # ---------- زمان‌بندِ پردازش ----------
    def should_process(self) -> bool:
        """آیا وقتِ یک پردازشِ نو است؟

        ⛔ باگی که این متد جلویش را می‌گیرد (و یک ممیزیِ بیرونی درست گرفت):

            if len(buf) % HOP != 0: continue        # ← غلط

        وقتی `deque` پر شد، `len(buf)` **ثابت** می‌ماند. اگر `BUFFER % HOP == 0` باشد
        شرط همیشه False است و **هر نمونه** یک پردازشِ کامل راه می‌اندازد؛ اگر ناصفر
        باشد **هرگز** پردازش نمی‌شود. هر دو حالت بی‌سروصداست: یکی CPU را می‌سوزاند،
        دیگری سیستم را لال می‌کند، و هیچ‌کدام خطا نمی‌دهند.

        شمارندهٔ مستقل هر دو را حذف می‌کند.
        """
        if len(self.buf) < int(self.fs * 8):
            return False
        k = self._n_seen // self.hop
        if k == self._n_last:
            return False
        self._n_last = k
        return True

    # ---------- ورودی ----------
    def ingest(self, device_ts: float, samples) -> None:
        """یک بستهٔ نمونه با برچسبِ زمانِ *دستگاه* (ثانیهٔ epoch، از ساعتِ ESP32).

        زمانِ رسیدنِ بسته عمداً استفاده نمی‌شود — لرزشِ WiFi فاز را نابود می‌کند.
        """
        samples = np.asarray(samples, dtype=float).ravel()
        if samples.size == 0:
            return
        dt = 1.0 / self.fs
        if self.ts:
            expected = self.ts[-1] + dt
            self._jitter_ms = 0.9 * self._jitter_ms + 0.1 * abs(device_ts - expected) * 1000.0
        for i, v in enumerate(samples):
            self.buf.append(float(v))
            self.ts.append(device_ts + i * dt)
        self._n_seen += int(samples.size)        # یکنوا، مستقل از پر شدنِ بافر

    # ---------- سنجه‌ها ----------
    def _ladder_peaks(self, x: np.ndarray) -> list[float]:
        nper = int(min(len(x), self.fs * 32))
        if nper < self.fs * 8:
            return []
        f, P = welch(x, fs=self.fs, nperseg=nper)
        band = (f > 4) & (f < 40)
        fb, Pb = f[band], 10 * np.log10(np.maximum(P[band], 1e-30))
        Pb = Pb - np.median(Pb)
        out = []
        for target in SR_LADDER:
            i = int(np.argmin(np.abs(fb - target)))
            local = Pb[max(0, i - 6): i + 7]
            out.append(float(Pb[i] - np.median(local)))
        return out

    def read(self) -> Reading:
        now = self.ts[-1] if self.ts else 0.0
        need = int(self.fs * 8)
        if len(self.buf) < need:
            return Reading(now, None, None, 0.0, 0.0, ["پنجره هنوز پر نشده"])

        x = np.asarray(self.buf, dtype=float)
        x = x - x.mean()
        band = filtfilt(self._b, self._a, x)
        an = hilbert(band)

        mid = len(an) // 2                      # باگ ۱: وسطِ پنجره، نه [-1]
        phase = float(np.angle(an)[mid])
        env = np.abs(an)
        amp_counts = float(np.median(env))       # median ⇒ مقاوم به تک‌ضربه

        reasons: list[str] = []

        peaks = self._ladder_peaks(x)
        n_hits = sum(1 for p in peaks if p > 3.0)
        q_ladder = min(1.0, n_hits / 3.0)
        if n_hits < 3:
            reasons.append(f"نردبانِ هارمونیک ضعیف ({n_hits}/5 قله)")

        # SNR = برجستگیِ قلهٔ اصلی نسبت به کفِ *مجاورِ خودش* در طیف.
        # اشتباهِ رایج (و باگی که خودآزمون گرفت): تقسیمِ باندِ ۷–۹ بر «هرچیزِ بیرونِ باند» —
        # آن‌وقت هارمونیک‌های ۱۴.۳/۲۰.۸/… که خودشان سیگنال‌اند، نویز شمرده می‌شوند.
        snr_db = peaks[0] if peaks else 0.0
        snr = float(10 ** (snr_db / 20.0))
        q_snr = float(np.clip((snr_db - 3.0) / 12.0, 0.0, 1.0))
        if snr_db < 6.0:
            reasons.append(f"برجستگیِ قلهٔ ۷.۸۳ کم است ({snr_db:.1f} dB)")

        # ⚠️ SNR **بدونِ زمانِ انباشت بی‌معناست** — و این نکته‌ای است که یک گیتِ
        # «SNR > 6 dB» را می‌تواند از روزِ اول غیرقابلِ‌عبور کند.
        # حسابِ نظری با N=8000، μ_eff=200، B=1pT، R≈2.2kΩ:
        #     پهنای‌باند ۱ هرتز   (۱ ثانیه انباشت)  ⇒ SNR ≈  4.3 dB   ← زیرِ گیت!
        #     پهنای‌باند ۰.۱      (۱۰ ثانیه)        ⇒ SNR ≈ 14.3 dB
        #     پهنای‌باند ۰.۰۱     (۱۰۰ ثانیه)       ⇒ SNR ≈ 24.3 dB
        # یعنی گیتِ ۶ dB فقط با انباشتِ **بیش از ~۲ ثانیه** معنا پیدا می‌کند، و برای
        # حاشیهٔ ایمن ~۱۰۰ ثانیه لازم است. پس زمانِ انباشت را کنارِ عدد گزارش می‌کنیم؛
        # SNRِ لخت، عددِ بی‌معناست.
        integ_s = len(self.buf) / self.fs
        res_hz = (self.fs / min(len(self.buf), int(self.fs * 32))) if self.buf else 0.0
        reasons.append(f"[انباشت] {integ_s:.0f}s · تفکیک ≈{res_hz:.3f}Hz")
        if integ_s < 30.0:
            reasons.append("انباشت کمتر از ۳۰ ثانیه — حکمِ SNR حاشیهٔ کافی ندارد")
            q_snr *= 0.5

        q_jit = float(np.clip(1.0 - self._jitter_ms / self.max_jitter_ms, 0.0, 1.0))
        if self._jitter_ms > self.max_jitter_ms:
            reasons.append(f"لرزشِ ساعت {self._jitter_ms:.1f}ms — فاز نامعتبر")

        if self.cal is None:
            reasons.append("کالیبراسیون تنظیم نشده — دامنهٔ فیزیکی گزارش نمی‌شود")
            return Reading(now, None, phase if q_jit > 0.5 else None,
                           snr, 0.0, reasons)

        w_q = float(q_ladder * q_snr * q_jit)    # ضربی: هر ضعفی کلِ وزن را می‌کشد
        return Reading(now, amp_counts * self.cal,
                       phase if q_jit > 0.5 else None, snr, w_q, reasons)

    # ---------- تستِ ابطال ----------
    def verdict(self, hourly_amplitude_utc: dict[int, float] | None = None) -> dict:
        """آیا ثابت شده که این ابزار شومان می‌سنجد؟ هر دو تست باید سبز شوند."""
        x = np.asarray(self.buf, dtype=float)
        peaks = self._ladder_peaks(x - x.mean()) if len(x) > self.fs * 8 else []
        t1 = sum(1 for p in peaks if p > 3.0) >= 3

        t2, note = None, "دادهٔ ۲۴ ساعته لازم است"
        if hourly_amplitude_utc and len(hourly_amplitude_utc) >= 20:
            h = np.array([hourly_amplitude_utc.get(i, np.nan) for i in range(24)], float)
            if np.isfinite(h).sum() >= 20:
                hh = h - np.nanmean(h)
                # قله‌های کارنگی: آسیا ۰۸، آفریقا ۱۴، آمریکا ۲۰ (UTC)
                carnegie = np.cos(2 * np.pi * (np.arange(24) - 16) / 24)
                m = np.isfinite(hh)
                r = float(np.corrcoef(hh[m], carnegie[m])[0, 1])
                t2 = r > 0.4
                note = f"همبستگی با منحنیِ کارنگی (UTC) = {r:+.2f}"

        return {"ladder_ok": t1, "ladder_peaks_db": [round(p, 1) for p in peaks],
                "carnegie_ok": t2, "carnegie_note": note,
                "is_proven": bool(t1 and t2 is True)}


# ----------------------------------------------------------------------
if __name__ == "__main__":
    np.random.seed(3)
    fs = FS_DEFAULT
    rx = SchumannReceiver(fs=fs, cal_pT_per_count=1.0)

    dur, t = 90.0, None
    t = np.arange(0, dur, 1 / fs)
    x = 0.7 * np.random.randn(t.size)
    for i, f in enumerate(SR_LADDER):
        x += (1.0 / (1 + i * 0.6)) * np.sin(2 * np.pi * f * t + np.random.rand() * 6.28)

    step = int(fs)            # بسته‌های ۱ ثانیه‌ای با برچسبِ زمانِ دستگاه
    for s in range(0, t.size - step, step):
        rx.ingest(float(t[s]), x[s:s + step])

    r = rx.read()
    print("=" * 62)
    print("خودآزمونِ schumann_rx")
    print("=" * 62)
    print(f"  دامنه   : {r.amplitude_pT:.3f} pT (واحدِ مصنوعی)")
    print(f"  فاز     : {r.phase_rad:+.3f} rad")
    print(f"  SNR     : {r.snr:.2f}")
    print(f"  w_q     : {r.w_q:.3f}   قابل‌استفاده: {r.usable}")
    print(f"  دلایل   : {r.reasons or '—'}")

    v = rx.verdict()
    print("\n  نردبان  :", v["ladder_peaks_db"], "→ ok =", v["ladder_ok"])
    print("  کارنگی  :", v["carnegie_note"], "→", v["carnegie_ok"])
    print("  اثبات‌شده:", v["is_proven"], " (تا دادهٔ ۲۴ساعته نیاید False می‌ماند — درست)")

    # نمونهٔ منفی: مزاحمِ محلی با هارمونیکِ صحیح، بدونِ نردبانِ شومان
    rx2 = SchumannReceiver(fs=fs, cal_pT_per_count=1.0)
    y = 0.7 * np.random.randn(t.size)
    for f in (6.0, 12.0, 18.0):
        y += 1.2 * np.sin(2 * np.pi * f * t + np.random.rand() * 6.28)
    for s in range(0, t.size - step, step):
        rx2.ingest(float(t[s]), y[s:s + step])
    r2 = rx2.read()
    print("\n  --- نمونهٔ منفی (مزاحمِ محلی، بدونِ شومان) ---")
    print(f"  w_q = {r2.w_q:.3f}   قابل‌استفاده: {r2.usable}   دلایل: {r2.reasons}")
    print("\n  → ابزار باید موردِ اول را بپذیرد و دومی را رد کند.")
