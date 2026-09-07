"""OptionsLab simulator.

Streamlit surface. Contains NO pricing arithmetic — every number shown is computed
in optionslab.core. The only maths here is building a spot grid with numpy and
calling core on each point.
"""
from __future__ import annotations

import math

import numpy as np
import streamlit as st

from optionslab.core.bs import forward
from optionslab.core.position import MULTIPLIER_DEFAULT, Leg, Position
from optionslab.display import plots

TRADING_DAYS = 252.0
CALENDAR_DAYS = 365.0

st.set_page_config(page_title="OptionsLab", layout="wide")

PRESETS = {
    "Long call": [("call", 1.0, 100.0)],
    "Long put": [("put", 1.0, 100.0)],
    "Long straddle": [("call", 1.0, 100.0), ("put", 1.0, 100.0)],
    "Short straddle": [("call", -1.0, 100.0), ("put", -1.0, 100.0)],
    "Call spread (100/110)": [("call", 1.0, 100.0), ("call", -1.0, 110.0)],
    "Put spread (100/90)": [("put", 1.0, 100.0), ("put", -1.0, 90.0)],
    "Iron condor": [("put", -1.0, 90.0), ("put", 1.0, 85.0),
                    ("call", -1.0, 110.0), ("call", 1.0, 115.0)],
    "Conversion (100)": [("stock", 100.0, None), ("call", -1.0, 100.0), ("put", 1.0, 100.0)],
}

# ---------------- sidebar: market and position ----------------
with st.sidebar:
    st.markdown("### Market")
    S = st.slider("spot", 50.0, 150.0, 100.0, 0.5)
    vol_pct = st.slider("volatility %", 1.0, 120.0, 20.0, 0.5)
    days = st.slider("calendar days to expiry", 1, 365, 91)
    rate_pct = st.slider("rate %", 0.0, 10.0, 5.0, 0.05)
    div_pct = st.slider("dividend yield %", 0.0, 8.0, 0.0, 0.05)

    st.markdown("### Position")
    preset = st.selectbox("structure", list(PRESETS), index=4)
    dark = st.toggle("dark theme", value=False)

# Units are converted ONCE, here at the edge. core/ only ever sees decimals.
sigma = vol_pct / 100.0
r = rate_pct / 100.0
q = div_pct / 100.0
T = days / CALENDAR_DAYS

legs = []
for kind, qty, strike in PRESETS[preset]:
    if kind == "stock":
        legs.append(Leg("stock", qty, None, 1.0))
    else:
        legs.append(Leg(kind, qty, strike, MULTIPLIER_DEFAULT))
pos = Position(legs)

# ---------------- header ----------------
st.markdown("## OptionsLab")
st.caption(f"{preset} · spot {S:.2f} · {vol_pct:.1f}% vol · {days} days · "
           f"forward {forward(S, T, r, q):.2f}")

value = pos.value(S, T, r, sigma, q)
g = pos.greeks(S, T, r, sigma, q)
daily_move = S * sigma / math.sqrt(TRADING_DAYS)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("value", f"${value:,.0f}")
c2.metric("delta", f"{g['delta']:+,.2f}")
c3.metric("gamma", f"{g['gamma']:+,.3f}")
c4.metric("vega", f"{g['vega']:+,.2f}", help="per 1 vol point")
c5.metric("theta", f"{g['theta']:+,.2f}", help="per calendar day")
c6.metric("1-sigma day", f"±{daily_move:.2f}",
          help="rule of 16: annual vol / sqrt(252) — the move the option is priced for")

# ---------------- curves ----------------
lo, hi = S * 0.7, S * 1.3
spots = np.linspace(lo, hi, 160)
value_today = [pos.value(float(x), T, r, sigma, q) for x in spots]
payoff_exp = [pos.payoff_at_expiry(float(x)) for x in spots]
delta_curve = [pos.greeks(float(x), T, r, sigma, q)["delta"] for x in spots]
gamma_curve = [pos.greeks(float(x), T, r, sigma, q)["gamma"] for x in spots]

left, right = st.columns(2)
with left:
    st.markdown("**P&L vs spot**")
    st.pyplot(plots.pnl_figure(spots, value_today, payoff_exp, value, S, dark), clear_figure=True)
with right:
    st.markdown("**Greeks vs spot**")
    st.pyplot(plots.greeks_figure(spots, delta_curve, gamma_curve, S, dark), clear_figure=True)

# ---------------- gamma / theta breakeven ----------------
st.markdown("**Gamma / theta breakeven**")
st.caption("Where the lines cross, a one-sigma day exactly pays for one day of decay. "
           "Above the crossing the position wants movement; below it, stillness.")

day_grid = np.arange(max(days, 5), 0, -1, dtype=float)
theta_cost, gamma_pnl = [], []
for d in day_grid:
    t = float(d) / CALENDAR_DAYS
    gg = pos.greeks(S, t, r, sigma, q)
    theta_cost.append(-gg["theta"])                       # cost is positive on the chart
    move = S * sigma / math.sqrt(TRADING_DAYS)
    gamma_pnl.append(0.5 * gg["gamma"] * move * move)     # 0.5 * gamma * (dS)^2
st.pyplot(plots.breakeven_figure(day_grid, theta_cost, gamma_pnl, dark), clear_figure=True)

with st.expander("legs"):
    for leg in pos.legs:
        tag = "stock" if not leg.is_option else f"{leg.kind} {leg.strike:g}"
        st.write(f"`{leg.quantity:+g} × {tag}` — multiplier {leg.multiplier:g}")
