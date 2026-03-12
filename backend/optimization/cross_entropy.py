"""
Cross-Entropy Method (CEM) for derivative-free optimization.

Uniform distribution variant; updates mean and std from elite samples.
See Al-Zawqari et al. (2024) UCE Antenna.
"""

from typing import Callable, List, Tuple, Optional
import numpy as np


def cross_entropy_optimize(
    func: Callable[[np.ndarray], float],
    bounds: List[Tuple[float, float]],
    n_samples: int = 30,
    elite_frac: float = 0.15,
    n_iterations: int = 15,
    mu_init: Optional[np.ndarray] = None,
    sigma_init: Optional[np.ndarray] = None,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, float, List[float]]:
    """
    Minimize func(x) over box bounds using the Cross-Entropy Method with uniform sampling.

    Args:
        func: Scalar objective to minimize. Signature: x (1D array) -> float.
        bounds: List of (low, high) per dimension. len(bounds) = dim.
        n_samples: Number of samples per iteration.
        elite_frac: Fraction of samples kept as elite (0 < elite_frac < 1).
        n_iterations: Number of CEM iterations.
        mu_init: Initial mean (length = dim). If None, use center of bounds.
        sigma_init: Initial std (length = dim). If None, use (high-low)/(2*sqrt(12)).
        rng: Random generator. If None, use np.random.default_rng().

    Returns:
        best_x: Best solution found (1D array).
        best_score: func(best_x).
        loss_history: List of best score per iteration (length = n_iterations).
    """
    rng = rng or np.random.default_rng()
    bounds = [ (float(lo), float(hi)) for lo, hi in bounds ]
    dim = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])

    if mu_init is None:
        mu = (low + high) / 2.0
    else:
        mu = np.clip(np.asarray(mu_init, dtype=float).ravel()[:dim], low, high)
    if sigma_init is None:
        sigma = (high - low) / (2 * np.sqrt(12))
    else:
        sigma = np.maximum(np.asarray(sigma_init, dtype=float).ravel()[:dim], 1e-9)

    n_elite = max(1, int(np.ceil(elite_frac * n_samples)))
    loss_history: List[float] = []
    best_x = mu.copy()
    best_score = float("inf")

    for _ in range(n_iterations):
        # Uniform [A, B] with mean mu and std sigma => A = mu - sigma*sqrt(12)/2, B = mu + sigma*sqrt(12)/2
        half = sigma * np.sqrt(12) / 2.0
        A = np.clip(mu - half, low, high)
        B = np.clip(mu + half, low, high)
        # Ensure A <= B
        A, B = np.minimum(A, B), np.maximum(A, B)
        B = np.where(B > A, B, A + 1e-9)

        samples = np.zeros((n_samples, dim))
        for d in range(dim):
            samples[:, d] = rng.uniform(A[d], B[d], size=n_samples)

        scores = np.array([func(samples[i]) for i in range(n_samples)])

        elite_idx = np.argsort(scores)[:n_elite]
        elite_samples = samples[elite_idx]
        if scores[elite_idx[0]] < best_score:
            best_score = float(scores[elite_idx[0]])
            best_x = samples[elite_idx[0]].copy()

        loss_history.append(best_score)

        mu = np.mean(elite_samples, axis=0)
        sigma = np.std(elite_samples, axis=0)
        sigma = np.where(sigma >= 1e-9, sigma, 1e-9)

    return best_x, best_score, loss_history
