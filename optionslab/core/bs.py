"""Black-Scholes-Merton pricing for European options.

Conventions (see DECISIONS.md):
  T      years to expiry, CALENDAR / 365
  sigma  DECIMAL volatility: 0.24 means 24%
  q      continuous dividend yield, default 0.0
  All prices are PER UNIT. The contract multiplier lives in position.py.
"""
from __future__ import annotations

import math

SQRT_2 = math.sqrt(2.0)
SQRT_2PI = math.sqrt(2.0 * math.pi)


def _norm_cdf(x: float) -> float:
    """Standard normal CDF. math.erf is in the stdlib and accurate to ~1e-16."""
    return 0.5 * (1.0 + math.erf(x / SQRT_2))


def _norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _validate(S: float, K: float, T: float, sigma: float) -> None:
    if S <= 0:
        raise ValueError(f"spot must be positive, got {S}")
    if K <= 0:
        raise ValueError(f"strike must be positive, got {K}")
    if T < 0:
        raise ValueError(f"time to expiry cannot be negative, got {T}")
    # Rejects a mis-scaled percentage (24 for 24%) while admitting a plausible 500% vol.
    if sigma < 0 or sigma >= 5:
        raise ValueError(
            f"sigma must be a decimal in [0, 5), got {sigma}. "
            "Did you pass a percentage? 24% is 0.24, not 24."
        )


def d1(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    _validate(S, K, T, sigma)
    if T <= 0 or sigma <= 0:
        raise ValueError("d1 is undefined at T=0 or sigma=0; the caller handles those cases")
    return (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    return d1(S, K, T, r, sigma, q) - sigma * math.sqrt(T)


def call_price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Price of a European call, per unit of underlying."""
    _validate(S, K, T, sigma)
    if T <= 0:
        return max(S - K, 0.0)
    if sigma <= 0:
        # No uncertainty: the forward is known, so the option is its discounted intrinsic.
        return max(S * math.exp(-q * T) - K * math.exp(-r * T), 0.0)
    a, b = d1(S, K, T, r, sigma, q), d2(S, K, T, r, sigma, q)
    return S * math.exp(-q * T) * _norm_cdf(a) - K * math.exp(-r * T) * _norm_cdf(b)


def put_price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Price of a European put, per unit of underlying."""
    _validate(S, K, T, sigma)
    if T <= 0:
        return max(K - S, 0.0)
    if sigma <= 0:
        return max(K * math.exp(-r * T) - S * math.exp(-q * T), 0.0)
    a, b = d1(S, K, T, r, sigma, q), d2(S, K, T, r, sigma, q)
    return K * math.exp(-r * T) * _norm_cdf(-b) - S * math.exp(-q * T) * _norm_cdf(-a)


def price(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Dispatch on 'call' or 'put'."""
    k = kind.lower()
    if k == "call":
        return call_price(S, K, T, r, sigma, q)
    if k == "put":
        return put_price(S, K, T, r, sigma, q)
    raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")


def forward(S: float, T: float, r: float, q: float = 0.0) -> float:
    """Forward price of the underlying."""
    return S * math.exp((r - q) * T)
