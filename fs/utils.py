import numpy as np
from random import randint


def lerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Linear interpolation."""
    return (a * (1 - t) + b * t).astype(int)


def de_casteljau(points: list[np.ndarray], t: float) -> np.ndarray:
    """De Casteljau's algorithm for bezier curves.

    Returns a point on the bezier curve defined by the `points` at time `t`.
    """
    if len(points) == 2:
        return lerp(points[0], points[1], t)
    return de_casteljau(
        [lerp(p_0, p_1, t) for p_0, p_1 in zip(points[:-1], points[1:])], t
    )


def bezier(
    degree: int,
    x_bounds: tuple[int, int],
    y_bounds: tuple[int, int],
    dt: float,
) -> list[np.ndarray]:
    """Generate a bezier curve as a list of points."""
    points = [np.array([randint(*x_bounds), randint(*y_bounds)]) for _ in range(degree)]
    return [de_casteljau(points, t.item()) for t in np.arange(0, 1, dt)]
