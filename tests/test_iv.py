"""Implied volatility. The round-trip is the oracle."""
import pytest

from optionslab.core.bs import call_price, price, put_price
from optionslab.core.iv import NoSolution, implied_vol


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("sigma", [0.05, 0.15, 0.24, 0.60, 1.50])
@pytest.mark.parametrize("K", [80.0, 100.0, 130.0])
def test_round_trip_recovers_the_input(kind, sigma, K):
    """Price at a known sigma, solve, get sigma back.

    Skips combinations with no time value: at 5% vol a 30-point-away option is worth
    its intrinsic to fifteen decimal places, so no solver can recover the vol. That is
    a property of the data, not a defect in the method — see the dedicated test below.
    """
    S, T, r = 100.0, 0.5, 0.04
    observed = price(kind, S, K, T, r, sigma)
    floor = price(kind, S, K, T, r, 1e-6)
    if abs(observed - floor) < 1e-8:
        pytest.skip("no time value at this strike/vol — implied vol is not recoverable")
    assert implied_vol(observed, kind, S, K, T, r) == pytest.approx(sigma, abs=1e-5)


@pytest.mark.parametrize("kind,K", [("put", 80.0), ("call", 130.0), ("put", 130.0)])
def test_no_time_value_raises_rather_than_guessing(kind, K):
    """The honest failure. A deep option at low vol prices to its intrinsic, and
    many volatilities reproduce that price. Returning any one of them would invent
    precision the data does not contain."""
    S, T, r = 100.0, 0.5, 0.04
    observed = price(kind, S, K, T, r, 0.05)
    with pytest.raises(NoSolution, match="no time value"):
        implied_vol(observed, kind, S, K, T, r)


def test_price_below_intrinsic_raises():
    """Bad data must not be laundered into a number."""
    with pytest.raises(NoSolution, match="below"):
        implied_vol(0.5, "call", 120.0, 100.0, 0.5, 0.05)


def test_price_above_solvable_range_raises():
    with pytest.raises(NoSolution, match="exceeds"):
        implied_vol(99.9, "call", 100.0, 100.0, 0.5, 0.05)


def test_negative_price_raises():
    with pytest.raises(NoSolution):
        implied_vol(-1.0, "call", 100.0, 100.0, 0.5, 0.05)


def test_at_expiry_raises():
    with pytest.raises(NoSolution, match="expiry"):
        implied_vol(5.0, "call", 100.0, 100.0, 0.0, 0.05)
