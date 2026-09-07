"""Analytic greeks for European options.

All greeks are PER UNIT of underlying. Scaling to a contract is position.py's job.

Reporting conventions, applied at the boundary and stated so they cannot surprise you:
  vega   is quoted per ONE VOL POINT   (a move from 20% to 21%), i.e. raw/100
  theta  is quoted per CALENDAR DAY    (raw annual / 365)
  rho    is quoted per ONE PERCENT rate move, i.e. raw/100
The raw_* functions return the untransformed partial derivatives, which is what
finite-difference tests must compare against.
"""
from __future__ import annotations

import math

from .bs import _norm_cdf, _norm_pdf, _validate, d1, d2

DAYS_PER_YEAR = 365.0


def delta(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """dV/dS. Call in (0,1), put in (-1,0)."""
    _validate(S, K, T, sigma)
    k = kind.lower()
    if T <= 0 or sigma <= 0:
        itm = (S > K) if k == "call" else (S < K)
        return (1.0 if k == "call" else -1.0) if itm else 0.0
    a = d1(S, K, T, r, sigma, q)
    disc = math.exp(-q * T)
    if k == "call":
        return disc * _norm_cdf(a)
    if k == "put":
        return disc * (_norm_cdf(a) - 1.0)
    raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")


def gamma(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """d2V/dS2. Identical for calls and puts — they differ by a linear term."""
    _validate(S, K, T, sigma)
    if T <= 0 or sigma <= 0:
        return 0.0
    a = d1(S, K, T, r, sigma, q)
    return math.exp(-q * T) * _norm_pdf(a) / (S * sigma * math.sqrt(T))


def raw_vega(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """dV/dsigma for a full 1.00 (100 vol point) move. Same for calls and puts."""
    _validate(S, K, T, sigma)
    if T <= 0 or sigma <= 0:
        return 0.0
    a = d1(S, K, T, r, sigma, q)
    return S * math.exp(-q * T) * _norm_pdf(a) * math.sqrt(T)


def vega(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Vega per ONE vol point (20% -> 21%)."""
    return raw_vega(S, K, T, r, sigma, q) / 100.0


def raw_theta(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """dV/dT as an ANNUAL rate of decay (negative for most long options)."""
    _validate(S, K, T, sigma)
    k = kind.lower()
    if T <= 0 or sigma <= 0:
        return 0.0
    a, b = d1(S, K, T, r, sigma, q), d2(S, K, T, r, sigma, q)
    decay = -(S * math.exp(-q * T) * _norm_pdf(a) * sigma) / (2.0 * math.sqrt(T))
    if k == "call":
        return decay - r * K * math.exp(-r * T) * _norm_cdf(b) + q * S * math.exp(-q * T) * _norm_cdf(a)
    if k == "put":
        return decay + r * K * math.exp(-r * T) * _norm_cdf(-b) - q * S * math.exp(-q * T) * _norm_cdf(-a)
    raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")


def theta(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Theta per CALENDAR day."""
    return raw_theta(kind, S, K, T, r, sigma, q) / DAYS_PER_YEAR


def raw_rho(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """dV/dr for a full 1.00 (100 bp x 100) move."""
    _validate(S, K, T, sigma)
    k = kind.lower()
    if T <= 0 or sigma <= 0:
        return 0.0
    b = d2(S, K, T, r, sigma, q)
    if k == "call":
        return K * T * math.exp(-r * T) * _norm_cdf(b)
    if k == "put":
        return -K * T * math.exp(-r * T) * _norm_cdf(-b)
    raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")


def rho(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Rho per ONE PERCENT move in rates."""
    return raw_rho(kind, S, K, T, r, sigma, q) / 100.0


def all_greeks(kind: str, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> dict:
    """Every greek in reporting units, for display."""
    return {
        "delta": delta(kind, S, K, T, r, sigma, q),
        "gamma": gamma(S, K, T, r, sigma, q),
        "vega": vega(S, K, T, r, sigma, q),
        "theta": theta(kind, S, K, T, r, sigma, q),
        "rho": rho(kind, S, K, T, r, sigma, q),
    }
