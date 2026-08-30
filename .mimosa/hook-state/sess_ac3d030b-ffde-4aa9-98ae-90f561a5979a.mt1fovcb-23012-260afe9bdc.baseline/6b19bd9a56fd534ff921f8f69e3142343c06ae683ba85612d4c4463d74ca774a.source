#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""efe_dashboard.py — شبیه‌سازی تعاملی Active Inference در grid-world (DISC-20260820-02).

دستور مالک #۹ · D-THEORY («فقط طراحی و شبیه‌سازی آفلاین») · cost=zero_aud.

معماری:
  - حالت‌های پنهان عاملی: موقعیت عامل (۱۶ خانه) × خانهٔ هدف (۱۶) — هدف مجهول است.
  - مشاهده: جای فعلی عامل + پیام «در هدف هستم/نیستم».
  - pymdp برای ساخت مدل مولد (A/B/C/D) و به‌روزرسانی باور (infer_qs)؛
    تجزیهٔ EFE به مؤلفهٔ epistemic (کاهش آنتروپی باور دربارهٔ هدف) و
    pragmatic (لوگ-ترجیح مشاهده) دستی محاسبه می‌شود تا وزن‌ها با اسلایدر
    قابل‌تنظیم باشند: score(π) = w_e·epistemic(π) + w_p·pragmatic(π).
  - داشبورد: اسلایدر w_e/w_p/speed + نمودارهای زندهٔ آنتروپی باور،
    آنتروپی سیاست، پاداش تجمعی. حالت headless برای اسموک‌تست.

اجرا: python research/active_inference/efe_dashboard.py [--interactive|--headless]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

try:  # رابط کلاسیک pymdp؛ در این محیط با لایهٔ سازگار دقیق (pymdp_classic)
    import pymdp_classic as pymdp_utils
    Agent = None  # عامل از pymdp_classic ساخته می‌شود
except ImportError as e:  # pragma: no cover
    raise SystemExit(f"pymdp classic layer required ({e})")


def _new_agent(A, B, C, D):
    import pymdp_classic
    return pymdp_classic.Agent(A=A, B=B, C=C, D=D,
                               control_fac_idx=[0], policy_len=1)

GRID = 4
N_POS = GRID * GRID
ACTIONS = ["up", "down", "left", "right", "stay"]
N_ACT = len(ACTIONS)


def _pos_index(r: int, c: int) -> int:
    return r * GRID + c


def _rc(idx: int) -> tuple[int, int]:
    return idx // GRID, idx % GRID


def build_agent():
    """مدل مولد: f1=موقعیت عامل (کنترل‌شده) · f2=خانهٔ هدف (ایستا، مجهول).
    obs1 = موقعیت · obs2 = at_goal."""
    A = pymdp_utils.obj_array(2)
    A[0] = np.zeros((N_POS, N_POS, N_POS))            # obs1 × f1 × f2
    for f1 in range(N_POS):
        A[0][f1, f1, :] = 1.0
    A[1] = np.zeros((2, N_POS, N_POS))                # at_goal? × f1 × f2
    for f1 in range(N_POS):
        for f2 in range(N_POS):
            A[1][1 if f1 == f2 else 0, f1, f2] = 1.0

    B = pymdp_utils.obj_array(2)
    B_f1 = np.zeros((N_POS, N_POS, N_ACT))
    for s in range(N_POS):
        r, c = _rc(s)
        for a, (dr, dc) in enumerate([(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]):
            nr, nc = max(0, min(GRID - 1, r + dr)), max(0, min(GRID - 1, c + dc))
            B_f1[_pos_index(nr, nc), s, a] = 1.0
    B[0] = B_f1
    B[1] = np.eye(N_POS).reshape(N_POS, N_POS, 1).repeat(1, axis=2)  # ایستا
    B[1] = np.tile(np.eye(N_POS).reshape(N_POS, N_POS, 1), (1, 1, 1))

    C = pymdp_utils.obj_array(2)
    C[0] = np.zeros(N_POS)
    C[1] = np.array([-2.0, 2.0])                      # ترجیح بودن در هدف

    D = pymdp_utils.obj_array(2)
    d1 = np.zeros(N_POS); d1[0] = 1.0                 # شروع از گوشه
    d2 = np.ones(N_POS) / N_POS                       # هدف: باور یکنواخت
    D[0], D[1] = d1, d2
    return A, B, C, D


def efe_decomposed(qs, A, B_f1, C1, action_seqs, w_e: float, w_p: float):
    """برای هر سیاست تک‌گامی، با انتقال قطعیِ B:
      pragmatic = E[log P(o2|C)]
      epistemic = کاهش آنتروپی باور هدف در «هر دو» رصد:
        hit  (at_goal=1): پسین ∝ q2·δ(next)     → H_hit
        miss (at_goal=0): پسین ∝ q2·(1−δ(next)) → H_miss
        epi = p_hit·(H0−H_hit) + (1−p_hit)·(H0−H_miss)
    (رصد miss هم فایدهٔ اطلاعاتی دارد — خانهٔ رد‌شده حذف می‌شود.)"""
    q_goal = qs[1]
    H0 = float(-(q_goal * np.log(q_goal + 1e-16)).sum())
    eye = np.eye(N_POS)
    scores, details = [], []
    for a in range(N_ACT):
        q_next_pos = B_f1[:, :, a] @ qs[0]
        nxt = int(np.argmax(q_next_pos)) if q_next_pos.max() > 0.999 else None
        p_hit = float((q_next_pos * q_goal).sum())
        prag = p_hit * C1[1] + (1 - p_hit) * C1[0]
        if nxt is not None:
            ph = q_goal * eye[nxt]
            sh = ph.sum()
            H_hit = 0.0 if sh <= 1e-12 else float(-(ph / sh * np.log(ph / sh + 1e-16)).sum())
            pm = q_goal * (1.0 - eye[nxt])
            sm = pm.sum()
            H_miss = H0 if sm <= 1e-12 else float(-(pm / sm * np.log(pm / sm + 1e-16)).sum())
            epi = p_hit * (H0 - H_hit) + (1 - p_hit) * (H0 - H_miss)
        else:
            epi = 0.0
        scores.append(w_e * epi + w_p * prag)
        details.append({"action": ACTIONS[a], "pragmatic": round(float(prag), 4),
                        "epistemic": round(float(epi), 4)})
    return np.array(scores), details


def policy_entropy(scores: np.ndarray, tau: float = 1.0) -> float:
    z = scores / tau
    z = z - z.max()
    p = np.exp(z); p = p / p.sum()
    return float(-(p * np.log(p + 1e-16)).sum())


def run_episode(w_e: float, w_p: float, steps: int = 60, seed: int = 3,
                tau: float = 0.35):
    """یک episode کامل؛ خروجی: مسیر + سری آنتروپی باور/سیاست + پاداش."""
    rng = np.random.default_rng(seed)
    A, B, C, D = build_agent()
    agent = _new_agent(A, B, C, D)
    true_goal = int(rng.integers(N_POS))
    qs = [D[0].copy(), D[1].copy()]
    log = {"steps": [], "true_goal": true_goal, "w_e": w_e, "w_p": w_p}
    cum = 0.0
    for t in range(steps):
        pos = int(np.argmax(qs[0]))
        at_goal = 1 if pos == true_goal else 0
        obs = pymdp_utils.obj_array(2)
        obs[0] = pymdp_utils.onehot(pos, N_POS)
        obs[1] = pymdp_utils.onehot(at_goal, 2)
        qs = agent.infer_qs(obs)
        scores, det = efe_decomposed(qs, A, B[0], C[1], None, w_e, w_p)
        z = scores / tau; z -= z.max()
        p = np.exp(z); p /= p.sum()
        act = int(rng.choice(N_ACT, p=p))
        cum += 1.0 if at_goal else 0.0
        q_goal = qs[1]
        log["steps"].append({
            "t": t, "pos": pos, "at_goal": bool(at_goal),
            "goal_belief_entropy": round(float(-(q_goal * np.log(q_goal + 1e-16)).sum()), 4),
            "goal_belief_top": int(np.argmax(q_goal)),
            "policy_entropy": round(policy_entropy(scores), 4),
            "action": ACTIONS[act], "cum_reward": round(cum, 1),
            "efe": det[act]})
        # انتقال واقعی
        r, c = _rc(pos)
        dr, dc = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)][act]
        nr, nc = max(0, min(GRID - 1, r + dr)), max(0, min(GRID - 1, c + dc))
        qs = agent.advance(act)
    log["final_cum_reward"] = round(cum, 1)
    log["goal_found"] = bool(any(s["at_goal"] for s in log["steps"]))
    log["belief_converged_to_goal"] = bool(int(np.argmax(qs[1])) == true_goal)
    return log


def headless(out_dir: Path) -> dict:
    """اسموک‌تست + مقایسهٔ سه رژیم وزن‌دهی + ذخیرهٔ نمودار."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out_dir.mkdir(parents=True, exist_ok=True)
    regimes = {"explorative (w_e=1,w_p=0.3)": (1.0, 0.3),
               "balanced (w_e=1,w_p=1)": (1.0, 1.0),
               "goal-directed (w_e=0.2,w_p=1.5)": (0.2, 1.5)}
    fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
    summary = {}
    for ax, (name, (we, wp)) in zip(axes, regimes.items()):
        log = run_episode(we, wp)
        Hs = [s["goal_belief_entropy"] for s in log["steps"]]
        cum = [s["cum_reward"] for s in log["steps"]]
        ax.plot(Hs, label="goal belief entropy", color="tab:blue")
        ax2 = ax.twinx()
        ax2.plot(cum, label="cum reward", color="tab:green")
        ax.set_title(f"{name} — found_goal={log['goal_found']} "
                     f"reward={log['final_cum_reward']}")
        ax.set_ylabel("entropy")
        ax2.set_ylabel("reward")
        summary[name] = {"found": log["goal_found"],
                         "reward": log["final_cum_reward"],
                         "final_entropy": Hs[-1]}
    axes[-1].set_xlabel("step")
    fig.tight_layout()
    fig.savefig(out_dir / "efe_regimes.png", dpi=130)
    (out_dir / "efe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def interactive():
    """داشبورد تعاملی: اسلایدرهای w_e/w_p + نمودارهای زنده (بلوک‌کننده)."""
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider, Button
    A, B, C, D = build_agent()
    agent = Agent(A=A, B=B, C=C, D=D, control_fac_idx=[0], policy_len=1)
    rng = np.random.default_rng(3)
    true_goal = int(rng.integers(N_POS))
    qs = [D[0].copy(), D[1].copy()]
    hist = {"ent": [], "pent": [], "rew": []}
    cum = 0.0
    fig = plt.figure(figsize=(11, 7))
    axg = fig.add_axes([0.05, 0.45, 0.35, 0.5])
    ax1 = fig.add_axes([0.48, 0.72, 0.45, 0.22])
    ax2 = fig.add_axes([0.48, 0.45, 0.45, 0.22])
    ax3 = fig.add_axes([0.48, 0.18, 0.45, 0.22])
    sax = fig.add_axes([0.08, 0.28, 0.28, 0.03])
    sax2 = fig.add_axes([0.08, 0.22, 0.28, 0.03])
    bax = fig.add_axes([0.08, 0.10, 0.12, 0.05])
    s_w_e = Slider(sax, "epistemic w_e", 0.0, 2.0, valinit=1.0)
    s_w_p = Slider(sax2, "pragmatic w_p", 0.0, 2.0, valinit=1.0)

    def step_fn(_=None):
        nonlocal qs, cum
        pos = int(np.argmax(qs[0]))
        at_goal = 1 if pos == true_goal else 0
        obs = pymdp_utils.obj_array(2)
        obs[0] = pymdp_utils.onehot(pos, N_POS)
        obs[1] = pymdp_utils.onehot(at_goal, 2)
        qs = agent.infer_qs(obs)
        scores, _ = efe_decomposed(qs, A, B[0], C[1], None,
                                   s_w_e.val, s_w_p.val)
        z = scores - scores.max(); p = np.exp(z); p /= p.sum()
        act = int(rng.choice(N_ACT, p=p))
        cum += 1.0 if at_goal else 0.0
        qg = qs[1]
        hist["ent"].append(float(-(qg * np.log(qg + 1e-16)).sum()))
        hist["pent"].append(policy_entropy(scores))
        hist["rew"].append(cum)
        r, c = _rc(pos)
        dr, dc = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)][act]
        nr, nc = max(0, min(GRID - 1, r + dr)), max(0, min(GRID - 1, c + dc))
        qs = agent.advance(act)
        # رندر
        axg.clear()
        bel = qs[1].reshape(GRID, GRID)
        axg.imshow(bel, cmap="viridis")
        axg.set_title(f"goal belief (هـ=true: {_rc(true_goal)}) — agent="
                      f"{_rc(int(np.argmax(qs[0])))}")
        ax1.clear(); ax1.plot(hist["ent"], color="tab:blue")
        ax1.set_ylabel("belief entropy")
        ax2.clear(); ax2.plot(hist["pent"], color="tab:orange")
        ax2.set_ylabel("policy entropy")
        ax3.clear(); ax3.plot(hist["rew"], color="tab:green")
        ax3.set_ylabel("cum reward"); ax3.set_xlabel("step")
        fig.canvas.draw_idle()

    btn = Button(bax, "step")
    btn.on_clicked(step_fn)
    timer = fig.timer  # noqa: F841 — (matplotlib>=3.6) interactive loop via button
    plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interactive", action="store_true")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    if args.interactive:
        interactive()
    else:
        s = headless(Path(__file__).resolve().parent / "out")
        print(json.dumps(s, ensure_ascii=False, indent=1))
