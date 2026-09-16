"""
محیط شبیه‌سازی «اتاق‌های تودرتو» (Deceptive Maze Arena)
=====================================================
عرصه [0,1]^2 با دیوارهای مستطیلی و ستون‌های دایره‌ای. رسیدن به اتاق‌های بالایی
از راه دو گلوگاه (دهانه راست، سپس دهانه چپ) انجام می‌شود.
این یک مسئله اسباب‌بازی برای مطالعه کاوش است، نه مدل محیط واقعی OCTOPUS.

هر «جعبه‌سیاه» یک MLP واکنشی است: ۵ فاصله‌سنج + ساعت داخلی → (سرعت، نرخ چرخش).
تمام افراد یک نسل به‌صورت برداری (batch) و همزمان شبیه‌سازی می‌شوند.
"""
import numpy as np

ARENA = (0.0, 1.0)
START = np.array([0.06, 0.06])
START_THETA = np.pi / 2.0
EPS = 1e-9

# دیوارهای مستطیلی: (x0, y0, x1, y1)
WALLS = np.array([
    [0.00, 0.30, 0.72, 0.335],   # دیوار اول، دهانه در سمت راست
    [0.28, 0.62, 1.00, 0.655],   # دیوار دوم، دهانه در سمت چپ
    [0.46, 0.655, 0.495, 0.86],  # تیغه عمودی: تقسیم اتاق بالا، عبور فقط از بالای تیغه
])
# ستون‌های دایره‌ای: (cx, cy, r)
PILLARS = np.array([
    [0.30, 0.15, 0.075],
    [0.78, 0.48, 0.085],
    [0.16, 0.85, 0.070],
    [0.80, 0.86, 0.070],
])

SENSOR_ANGLES = np.deg2rad(np.array([-90.0, -40.0, 0.0, 40.0, 90.0]))
SENSOR_RANGE = 0.30
V_MAX = 0.013
TURN_MAX = 0.45
T_STEPS = 320
ACTIVITY_PATH = 0.50  # طول مسیر لازم برای ضریب فعالیت کامل؛ واحد طول عرصه

# --- معماری جعبه‌سیاه (MLP) ---
N_IN = len(SENSOR_ANGLES) + 1
N_HID = 8
N_OUT = 2
GENOME_DIM = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT   # 74

LAYER_SLICES = {
    "W1": (0, N_IN * N_HID, (N_IN, N_HID)),
    "b1": (N_IN * N_HID, N_IN * N_HID + N_HID, (N_HID,)),
    "W2": (N_IN * N_HID + N_HID, N_IN * N_HID + N_HID + N_HID * N_OUT, (N_HID, N_OUT)),
    "b2": (GENOME_DIM - N_OUT, GENOME_DIM, (N_OUT,)),
}
INPUT_NAMES = ["prox_-90", "prox_-40", "prox_0", "prox_+40", "prox_+90", "clock"]
OUTPUT_NAMES = ["speed", "turn"]


def unpack(genomes):
    g = np.atleast_2d(np.asarray(genomes, dtype=np.float64))
    if g.ndim != 2 or g.shape[1] != GENOME_DIM or not np.isfinite(g).all():
        raise ValueError(f"Expected finite (N,{GENOME_DIM}) genomes")
    n = g.shape[0]
    a, b, _ = LAYER_SLICES["W1"]; W1 = g[:, a:b].reshape(n, N_IN, N_HID)
    a, b, _ = LAYER_SLICES["b1"]; b1 = g[:, a:b].reshape(n, 1, N_HID)
    a, b, _ = LAYER_SLICES["W2"]; W2 = g[:, a:b].reshape(n, N_HID, N_OUT)
    a, b, _ = LAYER_SLICES["b2"]; b2 = g[:, a:b].reshape(n, 1, N_OUT)
    return W1, b1, W2, b2


def _raycast(pos, theta):
    """(N,2),(N,) -> (N,5) فاصله نرمال‌شده تا نزدیک‌ترین سطح، ۱ = مسیر باز"""
    ang = theta[:, None] + SENSOR_ANGLES[None, :]
    dx, dy = np.cos(ang), np.sin(ang)
    x = pos[:, 0:1]; y = pos[:, 1:2]
    inf = np.inf
    with np.errstate(divide="ignore", invalid="ignore"):
        idx = 1.0 / np.where(np.abs(dx) < EPS, np.where(dx < 0, -EPS, EPS), dx)
        idy = 1.0 / np.where(np.abs(dy) < EPS, np.where(dy < 0, -EPS, EPS), dy)

        # دیوارهای بیرونی عرصه
        tx = np.where(dx > 0, (ARENA[1] - x) * idx, np.where(dx < 0, (ARENA[0] - x) * idx, inf))
        ty = np.where(dy > 0, (ARENA[1] - y) * idy, np.where(dy < 0, (ARENA[0] - y) * idy, inf))
        t = np.minimum(np.where(np.isfinite(tx), tx, inf), np.where(np.isfinite(ty), ty, inf))

        # مستطیل‌ها (روش slab)
        for x0, y0, x1, y1 in WALLS:
            t1 = (x0 - x) * idx; t2 = (x1 - x) * idx
            t3 = (y0 - y) * idy; t4 = (y1 - y) * idy
            tmin = np.maximum(np.minimum(t1, t2), np.minimum(t3, t4))
            tmax = np.minimum(np.maximum(t1, t2), np.maximum(t3, t4))
            t_hit = np.where(tmin > 0, tmin, tmax)
            valid = (tmax >= np.maximum(tmin, 0.0)) & (t_hit > 0)
            t = np.where(valid, np.minimum(t, t_hit), t)

        # دایره‌ها
        for cx, cy, r in PILLARS:
            ox = x - cx; oy = y - cy
            bq = dx * ox + dy * oy
            cq = ox ** 2 + oy ** 2 - r ** 2
            disc = bq ** 2 - cq
            sq = np.sqrt(np.where(disc > 0, disc, 0.0))
            t_hit = -bq - sq
            valid = (disc > 0) & (t_hit > 0)
            t = np.where(valid, np.minimum(t, t_hit), t)

    return np.clip(t / SENSOR_RANGE, 0.0, 1.0)


def _blocked(pos):
    out = (pos[:, 0] < ARENA[0]) | (pos[:, 0] > ARENA[1]) | \
          (pos[:, 1] < ARENA[0]) | (pos[:, 1] > ARENA[1])
    for x0, y0, x1, y1 in WALLS:
        out |= (pos[:, 0] > x0) & (pos[:, 0] < x1) & (pos[:, 1] > y0) & (pos[:, 1] < y1)
    for cx, cy, r in PILLARS:
        out |= ((pos[:, 0] - cx) ** 2 + (pos[:, 1] - cy) ** 2) < r ** 2
    return out


def free_mask(grid):
    """آزادبودن مرکز سلول؛ تقریب هندسی، نه اثبات دسترسی کنترلر در ۳۲۰ گام."""
    c = (np.arange(grid) + 0.5) / grid
    X, Y = np.meshgrid(c, c, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel()], axis=1)
    return (~_blocked(pts)).reshape(grid, grid)


def segment_blocked(start, end):
    """Swept point collision: endpoints alone miss thin obstacles and corners."""
    delta = end - start
    blocked = _blocked(end)
    for x0, y0, x1, y1 in WALLS:
        lo = np.zeros(len(start))
        hi = np.ones(len(start))
        possible = np.ones(len(start), dtype=bool)
        for axis, lower, upper in ((0, x0, x1), (1, y0, y1)):
            parallel = np.abs(delta[:, axis]) < EPS
            safe = np.where(parallel, 1.0, delta[:, axis])
            a = (lower - start[:, axis]) / safe
            b = (upper - start[:, axis]) / safe
            possible &= ~parallel | ((start[:, axis] > lower) & (start[:, axis] < upper))
            lo = np.maximum(lo, np.where(parallel, -np.inf, np.minimum(a, b)))
            hi = np.minimum(hi, np.where(parallel, np.inf, np.maximum(a, b)))
        blocked |= possible & (hi > lo + EPS)
    norm2 = (delta * delta).sum(axis=1)
    for cx, cy, radius in PILLARS:
        rel = start - np.array([cx, cy])
        t = np.clip(-(rel * delta).sum(axis=1) / np.maximum(norm2, EPS**2), 0, 1)
        closest = rel + t[:, None] * delta
        blocked |= (closest * closest).sum(axis=1) < radius**2
    return blocked


def quality(path_len, effort, collision_rate):
    """Activity-weighted smoothness; not shortest-path optimality or intelligence."""
    activity = np.clip(np.asarray(path_len) / ACTIVITY_PATH, 0, 1)
    return activity * np.clip(1 - .6 * np.asarray(effort) - .4 * np.asarray(collision_rate), 0, 1)


def evaluate(genomes, record_traj=False):
    """
    خروجی:
      fitness (N,) = min(path_len/0.5,1) * (1 - 0.6*effort - 0.4*collision_rate)
      bd      (N,2) = موقعیت نهایی (توصیفگر رفتاری)
      info    dict  = آماره‌های کمکی (+ traj اختیاری)
    """
    g = np.atleast_2d(np.asarray(genomes, dtype=np.float64))
    n = g.shape[0]
    W1, b1, W2, b2 = unpack(g)

    pos = np.tile(START, (n, 1)).astype(np.float64)
    theta = np.full(n, START_THETA)
    path_len = np.zeros(n); turn_cost = np.zeros(n); collisions = np.zeros(n)
    max_y = pos[:, 1].copy()
    traj = [pos.copy()] if record_traj else None

    for step in range(T_STEPS):
        sens = _raycast(pos, theta)
        clock = np.full((n, 1), step / T_STEPS)
        inp = np.concatenate([1.0 - sens, clock], axis=1).reshape(n, 1, N_IN)
        h = np.tanh(np.matmul(inp, W1) + b1)
        out = np.tanh(np.matmul(h, W2) + b2)[:, 0, :]

        speed = (out[:, 0] + 1.0) * 0.5 * V_MAX
        turn = out[:, 1] * TURN_MAX
        turn_cost += np.abs(out[:, 1])

        theta = theta + turn
        cand = pos + np.stack([speed * np.cos(theta), speed * np.sin(theta)], axis=1)
        bad = segment_blocked(pos, cand)
        collisions += bad
        theta = np.where(bad, theta + 0.6, theta)     # واکنش لغزشی به برخورد
        pos = np.where(bad[:, None], pos, cand)
        path_len += np.where(bad, 0.0, speed)
        max_y = np.maximum(max_y, pos[:, 1])
        if record_traj:
            traj.append(pos.copy())

    coll_rate = collisions / T_STEPS
    effort = turn_cost / T_STEPS
    fitness = quality(path_len, effort, coll_rate)

    info = {
        "path_len": path_len,
        "collision_rate": coll_rate,
        "turn_effort": effort,
        "displacement": np.linalg.norm(pos - START, axis=1),
        "max_y": max_y,
    }
    if record_traj:
        info["traj"] = np.asarray(traj)
    return fitness, pos.copy(), info


def reachable_mask(grid):
    """Grid-center flood-fill only; NOT true dynamic reachability."""
    from collections import deque
    free = free_mask(grid)
    si = int(np.clip(START[0] * grid, 0, grid - 1)); sj = int(np.clip(START[1] * grid, 0, grid - 1))
    seen = np.zeros_like(free)
    if not free[si, sj]:
        return free
    q = deque([(si, sj)]); seen[si, sj] = True
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < grid and 0 <= b < grid and free[a, b] and not seen[a, b]:
                seen[a, b] = True; q.append((a, b))
    return seen
