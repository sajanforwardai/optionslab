"""Implied volatility by bisection.

Bisection rather than Newton-Raphson: vega vanishes for deep in- and out-of-the-money
options, which makes Newton divide by ~0 and diverge exactly where a solver is most
likely to be asked to work. Bisection always converges on a bracketed root. It is
slower and it does not fail silently, which is the correct trade for a number a person
may act on.
"""
from __future__ import annotations

import math

from .bs import price

SIGMA_MIN = 1e-6
SIGMA_MAX = 4.999  # just inside the validator's ceiling


class NoSolution(ValueError):
    """Raised when no volatility reproduces the observed price.

    This is deliberately an exception rather than a returned None or a clamped
    guess: a price outside the no-arbitrage bounds is bad data, and silently
    returning a number would launder it into the rest of the system.
    """


def implied_vol(
    observed: float, kind: str, S: float, K: float, T: float, r: float,
    q: float = 0.0, tol: float = 1e-8, max_iter: int = 200,
) -> float:
    """Volatility that reproduces `observed`. Raises NoSolution if none exists."""
    if observed < 0:
        raise NoSolution(f"observed price cannot be negative, got {observed}")
    if T <= 0:
        raise NoSolution("cannot imply a volatility at expiry")

    lo_price = price(kind, S, K, T, r, SIGMA_MIN, q)
    hi_price = price(kind, S, K, T, r, SIGMA_MAX, q)

    if observed < lo_price - tol:
        raise NoSolution(
            f"price {observed:.6f} is below the zero-vol floor {lo_price:.6f} "
            "(intrinsic) — no volatility can produce it"
        )
    # An option with no time value carries NO information about volatility: many
    # sigmas reproduce its price to within tolerance, so the inverse problem is
    # ill-posed. Returning a number here would invent precision that the data does
    # not contain — which is the exact failure this project exists to avoid.
    if abs(observed - lo_price) <= max(tol, 1e-10):
        raise NoSolution(
            f"price {observed:.6f} equals the zero-volatility floor: the option has "
            "no time value, so implied volatility is not recoverable from it"
        )
    if observed > hi_price + tol:
        raise NoSolution(
            f"price {observed:.6f} exceeds the price at {SIGMA_MAX:.0%} vol "
            f"({hi_price:.6f}) — outside the solvable range"
        )

    lo, hi = SIGMA_MIN, SIGMA_MAX
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        diff = price(kind, S, K, T, r, mid, q) - observed
        if abs(diff) < tol or (hi - lo) < tol:
            return mid
        if diff > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
