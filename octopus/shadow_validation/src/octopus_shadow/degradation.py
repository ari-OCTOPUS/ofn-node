from __future__ import annotations

from collections.abc import Iterator
from random import Random


def degradation_ladder(
    truth: list[list[float]],
    levels: tuple[float, ...] = (0.0, 0.05, 0.10, 0.20, 0.40),
    seed: int = 42,
) -> Iterator[dict]:
    """Deterministic noise direction; only amplitude grows. No host stress."""

    rng = Random(seed)
    direction = [[rng.gauss(0.0, 1.0) for _ in row] for row in truth]
    for noise_level in levels:
        prediction = [
            [value + noise_level * delta for value, delta in zip(row, dir_row, strict=True)]
            for row, dir_row in zip(truth, direction, strict=True)
        ]
        yield {"noise": noise_level, "prediction": prediction}
