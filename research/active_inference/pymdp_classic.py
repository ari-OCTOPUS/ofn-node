#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pymdp_classic.py — لایهٔ سازگاری رابط کلاسیک pymdp برای efe_dashboard.

چرا این فایل: در این محیط (۲۰۲۶) پکیج PyPI «pymdp 0.0.1» پروژهٔ متفاوتی است و
HEAD گیت‌هاب infer-actively/pymdp به معماری JAX ریفکتور شده که رابط کلاسیک
(utils.obj_array/onehot/Agent.infer_qs) را ندارد. این لایه همان رابط کلاسیک را
با ریاضیاتِ دقیق برای خانوادهٔ مدلِ داشبورد (حالت‌های عاملی، A/B/C/D دسته‌ای)
پیاده می‌کند — برای این مدل (f1 کاملاً مشهود + f2 ایستا) یک گذر mean-field
دقیقاً پسین صحیح را می‌دهد. وقتی نسخهٔ کلاسیک در دسترس شد، داشبورد با عوض‌کردن
import به آن برمی‌گردد (رابط یکسان)."""
from __future__ import annotations

import numpy as np


def obj_array(n: int) -> list[np.ndarray]:
    return [np.zeros(0) for _ in range(n)]


def onehot(i: int, n: int) -> np.ndarray:
    v = np.zeros(n)
    v[i] = 1.0
    return v


def norm(v: np.ndarray) -> np.ndarray:
    return v / (v.sum() + 1e-16)


class Agent:
    """عامل با رابط کلاسیک: infer_qs(obs) → پسین حالت‌ها؛ advance(action)."""

    def __init__(self, A, B, C, D, control_fac_idx=None, policy_len: int = 1):
        self.A, self.B, self.C, self.D = A, B, C, D
        self.control_fac_idx = control_fac_idx or [0]
        self.policy_len = policy_len
        self.qs = [norm(np.asarray(d, dtype=float).copy()) for d in D]

    def infer_qs(self, obs) -> list[np.ndarray]:
        """یک به‌روزرسانی بیزی exact برای این ساختار:
        q(f) ∝ prior(f) · Π_m E_{q(f̄)}[A_m[obs_m | f, f̄]]"""
        q1, q2 = self.qs[0], self.qs[1]
        o1 = int(np.argmax(obs[0]))
        o2 = int(np.argmax(obs[1]))
        L1 = self.A[0][o1]          # (f1 × f2) — مستقل از f2 در این مدل
        L2 = self.A[1][o2]          # (f1 × f2) — پیام at_goal
        l1 = L1 @ q2                # برامarginal بر f2
        l2 = L2.T @ q1              # اطلاعات دربارهٔ f2 با q(f1) فعلی
        q1_new = norm(q1 * l1)
        q2_new = norm(q2 * l2)
        self.qs = [q1_new, q2_new]
        return self.qs

    def advance(self, action_idx: int) -> list[np.ndarray]:
        """انتقال prior با B برای فاکتور کنترل‌شده."""
        for f in self.control_fac_idx:
            self.qs[f] = norm(self.B[f][:, :, action_idx] @ self.qs[f])
        return self.qs
