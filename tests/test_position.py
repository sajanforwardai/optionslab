"""Multi-leg positions. The conversion is the headline test."""
import math

import pytest

from optionslab.core.position import (Leg, Position, conversion, straddle,
                                      vertical_call_spread)

MKT = dict(S=100.0, T=0.25, r=0.05, sigma=0.20)


def test_conversion_has_zero_delta():
    """Long stock, short call, long put at one strike. Perfectly hedged."""
    g = conversion(100.0).greeks(**MKT)
    assert g["delta"] == pytest.approx(0.0, abs=1e-9)
    assert g["gamma"] == pytest.approx(0.0, abs=1e-12)
    assert g["vega"] == pytest.approx(0.0, abs=1e-12)


def test_conversion_value_is_the_discounted_strike():
    """The conversion IS a loan. You pay this today and receive K*multiplier at
    expiry regardless of where the stock goes, so its price is a discount factor
    and its return is the interest rate. This is put-call parity, tradeable."""
    K, mult = 100.0, 100.0
    value = conversion(K).value(**MKT)
    assert value == pytest.approx(K * math.exp(-MKT["r"] * MKT["T"]) * mult, abs=1e-6)
    implied_rate = -math.log(value / (K * mult)) / MKT["T"]
    assert implied_rate == pytest.approx(MKT["r"], abs=1e-9)


def test_multiplier_lives_in_the_position_not_the_pricer():
    one = Position([Leg("call", 1.0, 100.0, multiplier=1.0)])
    hundred = Position([Leg("call", 1.0, 100.0, multiplier=100.0)])
    assert hundred.value(**MKT) == pytest.approx(100.0 * one.value(**MKT))


def test_short_leg_flips_every_greek():
    long_ = Position([Leg("call", 1.0, 100.0)])
    short = Position([Leg("call", -1.0, 100.0)])
    for k, v in long_.greeks(**MKT).items():
        assert short.greeks(**MKT)[k] == pytest.approx(-v)


def test_straddle_is_delta_light_and_gamma_heavy():
    g = straddle(100.0).greeks(**MKT)
    assert abs(g["delta"]) < 20.0     # small against 100-delta legs
    assert g["gamma"] > 0
    assert g["theta"] < 0


def test_vertical_spread_payoff_is_capped():
    v = vertical_call_spread(100.0, 110.0)
    assert v.payoff_at_expiry(90.0) == pytest.approx(0.0)
    assert v.payoff_at_expiry(105.0) == pytest.approx(500.0)
    assert v.payoff_at_expiry(110.0) == pytest.approx(1000.0)
    assert v.payoff_at_expiry(200.0) == pytest.approx(1000.0)   # capped


def test_payoff_needs_no_model():
    """payoff_at_expiry is arithmetic, so it is an independent check on the pricer:
    as T -> 0 the model price must converge to it."""
    v = vertical_call_spread(100.0, 110.0)
    for S in (95.0, 105.0, 115.0):
        near = v.value(S=S, T=1e-9, r=0.05, sigma=0.2)
        assert near == pytest.approx(v.payoff_at_expiry(S), abs=1e-3)


def test_bad_leg_raises():
    with pytest.raises(ValueError, match="strike"):
        Leg("call", 1.0)
    with pytest.raises(ValueError, match="call, put or stock"):
        Leg("swaption", 1.0, 100.0)
