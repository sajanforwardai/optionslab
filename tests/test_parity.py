"""M0 — put-call parity. The primary oracle.

Parity is an arbitrage identity, not a model result: it holds for ANY arbitrage-free
price, Black-Scholes or otherwise. That independence is why it can check the pricer
without being part of it.
"""
import math

import pytest

from optionslab.core.bs import call_price, put_price

BASE = dict(S=100.0, K=100.0, T=0.25, r=0.05, sigma=0.20)


def test_parity_at_the_money():
    c = call_price(**BASE)
    p = put_price(**BASE)
    expected = BASE["S"] - BASE["K"] * math.exp(-BASE["r"] * BASE["T"])
    assert c - p == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("K", [50, 80, 95, 100, 105, 120, 200])
@pytest.mark.parametrize("T", [0.01, 0.25, 1.0, 5.0])
@pytest.mark.parametrize("sigma", [0.05, 0.20, 0.80])
def test_parity_across_the_grid(K, T, sigma):
    """Parity must hold everywhere. Testing only at the money would miss an error
    that happens to cancel there."""
    S, r = 100.0, 0.05
    c = call_price(S, K, T, r, sigma)
    p = put_price(S, K, T, r, sigma)
    assert c - p == pytest.approx(S - K * math.exp(-r * T), abs=1e-9)


@pytest.mark.parametrize("q", [0.0, 0.02, 0.06])
def test_parity_with_dividends(q):
    """With a dividend yield the spot leg is discounted too."""
    S, K, T, r, sigma = 100.0, 105.0, 0.5, 0.04, 0.3
    c = call_price(S, K, T, r, sigma, q)
    p = put_price(S, K, T, r, sigma, q)
    expected = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert c - p == pytest.approx(expected, abs=1e-9)
