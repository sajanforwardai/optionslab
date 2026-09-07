"""Boundary behaviour of the pricer, where the answer is known without a model."""
import math

import pytest

from optionslab.core.bs import call_price, put_price


@pytest.mark.parametrize("S,K", [(120, 100), (100, 100), (80, 100)])
def test_at_expiry_price_is_payoff(S, K):
    assert call_price(S, K, 0.0, 0.05, 0.2) == pytest.approx(max(S - K, 0.0))
    assert put_price(S, K, 0.0, 0.05, 0.2) == pytest.approx(max(K - S, 0.0))


def test_zero_vol_is_discounted_intrinsic():
    S, K, T, r = 110.0, 100.0, 1.0, 0.05
    assert call_price(S, K, T, r, 0.0) == pytest.approx(S - K * math.exp(-r * T))
    assert put_price(S, K, T, r, 0.0) == pytest.approx(0.0)


def test_deep_itm_call_approaches_intrinsic():
    S, K, T, r = 1000.0, 100.0, 0.25, 0.05
    assert call_price(S, K, T, r, 0.2) == pytest.approx(S - K * math.exp(-r * T), rel=1e-9)


def test_deep_otm_is_worthless():
    assert call_price(10.0, 1000.0, 0.25, 0.05, 0.2) == pytest.approx(0.0, abs=1e-12)


def test_price_increases_with_volatility():
    prices = [call_price(100, 100, 0.5, 0.03, s) for s in (0.1, 0.2, 0.4, 0.8)]
    assert prices == sorted(prices)


def test_price_is_bounded():
    """No-arbitrage: a call is worth less than the stock, more than its intrinsic."""
    S, K, T, r, sigma = 100.0, 90.0, 0.75, 0.04, 0.35
    c = call_price(S, K, T, r, sigma)
    assert max(S - K * math.exp(-r * T), 0.0) <= c <= S


def test_percentage_volatility_is_rejected():
    """24 is not 24%. A silent order-of-magnitude error is the failure this prevents."""
    with pytest.raises(ValueError, match="percentage"):
        call_price(100, 100, 0.25, 0.05, 24.0)


@pytest.mark.parametrize("bad", [dict(S=0), dict(K=-5), dict(T=-1)])
def test_invalid_inputs_raise(bad):
    args = dict(S=100.0, K=100.0, T=0.25, r=0.05, sigma=0.2)
    args.update(bad)
    with pytest.raises(ValueError):
        call_price(**args)
