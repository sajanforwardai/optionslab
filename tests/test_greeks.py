"""Greeks validated against finite differences.

The analytic formula and a numerical derivative of the price are INDEPENDENT
implementations. Agreement between them is evidence; agreement between a formula
and itself is not.

Tolerances are loose here on purpose: the central difference carries its own
O(h^2) truncation error, so demanding 1e-9 would be testing the approximation
rather than the greek.
"""
import math

import pytest

from optionslab.core import greeks as gk
from optionslab.core.bs import call_price, price, put_price

BASE = dict(S=100.0, K=100.0, T=0.5, r=0.05, sigma=0.25)


def central(f, x, h):
    return (f(x + h) - f(x - h)) / (2.0 * h)


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("K", [80.0, 100.0, 120.0])
def test_delta_matches_finite_difference(kind, K):
    a = dict(BASE, K=K)
    fd = central(lambda S: price(kind, S, a["K"], a["T"], a["r"], a["sigma"]), a["S"], 1e-4)
    assert gk.delta(kind, **a) == pytest.approx(fd, abs=1e-6)


@pytest.mark.parametrize("K", [80.0, 100.0, 120.0])
def test_gamma_matches_second_difference(K):
    a = dict(BASE, K=K)
    h, S = 1e-3, a["S"]
    f = lambda x: call_price(x, a["K"], a["T"], a["r"], a["sigma"])
    fd = (f(S + h) - 2 * f(S) + f(S - h)) / (h * h)
    assert gk.gamma(**a) == pytest.approx(fd, abs=1e-5)


def test_gamma_is_identical_for_call_and_put():
    """Calls and puts differ by a linear term, which has zero curvature."""
    h, S = 1e-3, BASE["S"]
    args = {k: v for k, v in BASE.items() if k != "S"}
    fc = lambda x: call_price(x, **args)
    fp = lambda x: put_price(x, **args)
    gc = (fc(S + h) - 2 * fc(S) + fc(S - h)) / (h * h)
    gp = (fp(S + h) - 2 * fp(S) + fp(S - h)) / (h * h)
    assert gc == pytest.approx(gp, abs=1e-7)


@pytest.mark.parametrize("kind", ["call", "put"])
def test_vega_matches_finite_difference(kind):
    fd = central(lambda s: price(kind, BASE["S"], BASE["K"], BASE["T"], BASE["r"], s),
                 BASE["sigma"], 1e-5)
    assert gk.raw_vega(**BASE) == pytest.approx(fd, abs=1e-4)


@pytest.mark.parametrize("kind", ["call", "put"])
def test_theta_matches_finite_difference(kind):
    """Theta is dV/dT with a sign flip: time to expiry SHRINKS as the clock runs."""
    fd = central(lambda T: price(kind, BASE["S"], BASE["K"], T, BASE["r"], BASE["sigma"]),
                 BASE["T"], 1e-5)
    assert gk.raw_theta(kind, **BASE) == pytest.approx(-fd, abs=1e-4)


@pytest.mark.parametrize("kind", ["call", "put"])
def test_rho_matches_finite_difference(kind):
    fd = central(lambda r: price(kind, BASE["S"], BASE["K"], BASE["T"], r, BASE["sigma"]),
                 BASE["r"], 1e-6)
    assert gk.raw_rho(kind, **BASE) == pytest.approx(fd, abs=1e-4)


# --- qualitative facts a trader would know without computing anything ---

def test_atm_call_delta_slightly_exceeds_half():
    """Because d1 carries +sigma^2*T/2: the lognormal's mean sits above its median."""
    d = gk.delta("call", **BASE)
    assert 0.50 < d < 0.60


def test_gamma_peaks_slightly_BELOW_the_strike():
    """Not at the strike, which is the intuitive-but-wrong answer.

    Gamma = pdf(d1) / (S*sigma*sqrt(T)). Two effects push the peak down:
    pdf(d1) is maximal where d1 = 0, i.e. where ln(S/K) = -(r + sigma^2/2)T,
    which is below K for positive rates; and the explicit 1/S term lowers it
    further. For K=100, r=5%, sigma=25%, T=0.5 the peak sits near 95.
    """
    args = {k: v for k, v in BASE.items() if k != "S"}
    grid = {S: gk.gamma(S, **args) for S in range(85, 116)}
    peak = max(grid, key=grid.get)
    assert 90 <= peak < BASE["K"], f"expected the peak below the strike, got {peak}"
    # and it is still very much a peak: far wings are an order of magnitude smaller
    assert grid[peak] > 5 * gk.gamma(140.0, **args)


def test_vega_decays_as_sqrt_T():
    """Vega -> 0 at expiry, but only as sqrt(T), which is slower than intuition
    suggests: at one calendar day left an ATM option still has meaningful vega.
    Quartering the time only halves the vega."""
    args = {k: v for k, v in BASE.items() if k != "T"}
    v = [gk.raw_vega(T=T, **args) for T in (1.0, 0.5, 0.1, 0.01, 1e-4)]
    assert v == sorted(v, reverse=True)
    assert v[-1] < 0.5                       # genuinely negligible only very near expiry
    # halving T multiplies vega by ~1/sqrt(2)
    assert v[1] / v[0] == pytest.approx(1 / math.sqrt(2), rel=0.05)


def test_long_option_theta_is_negative():
    assert gk.theta("call", **BASE) < 0
    assert gk.theta("put", **BASE) < 0
