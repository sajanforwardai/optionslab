"""Matplotlib figures for the simulator.

This module RENDERS. It performs no pricing arithmetic: every number it draws comes
from optionslab.core and is passed in or fetched through a core call. Nothing here
computes a greek or a price from first principles.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LIGHT = dict(fg="#111827", mut="#5b6472", line="#e3e6ea", bg="#ffffff",
             acc="#0e7490", acc2="#1d4ed8", bad="#be123c")
DARK = dict(fg="#e7edf7", mut="#93a2bf", line="#1e2c48", bg="#0b1220",
            acc="#38bdf8", acc2="#60a5fa", bad="#fb7185")


def _style(ax, c, xlabel="spot"):
    ax.set_facecolor(c["bg"])
    ax.figure.patch.set_facecolor(c["bg"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(c["line"])
    ax.tick_params(colors=c["mut"], labelsize=8)
    ax.set_xlabel(xlabel, color=c["mut"], fontsize=8)
    ax.grid(True, color=c["line"], linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def pnl_figure(spots, value_today, payoff_expiry, cost, spot_now, dark=False):
    """P&L against spot: the kinked expiry payoff and the smooth pre-expiry value."""
    c = DARK if dark else LIGHT
    fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=140)
    _style(ax, c)
    pnl_now = np.asarray(value_today) - cost
    pnl_exp = np.asarray(payoff_expiry) - cost
    ax.axhline(0, color=c["mut"], linewidth=0.9)
    ax.plot(spots, pnl_exp, color=c["mut"], linewidth=1.5, linestyle="--", label="at expiry")
    ax.plot(spots, pnl_now, color=c["acc"], linewidth=2.0, label="today")
    ax.axvline(spot_now, color=c["line"], linewidth=1.0)
    ax.set_ylabel("P&L ($)", color=c["mut"], fontsize=8)
    leg = ax.legend(frameon=False, fontsize=8, loc="upper left")
    for t in leg.get_texts():
        t.set_color(c["mut"])
    fig.tight_layout()
    return fig


def greeks_figure(spots, delta, gamma, spot_now, dark=False):
    """Delta and gamma against spot, on twin axes because their scales differ."""
    c = DARK if dark else LIGHT
    fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=140)
    _style(ax, c)
    ax.axhline(0, color=c["mut"], linewidth=0.9)
    ax.plot(spots, delta, color=c["acc"], linewidth=2.0, label="delta")
    ax.set_ylabel("delta", color=c["acc"], fontsize=8)
    ax2 = ax.twinx()
    ax2.plot(spots, gamma, color=c["acc2"], linewidth=2.0, label="gamma")
    ax2.set_ylabel("gamma", color=c["acc2"], fontsize=8)
    ax2.tick_params(colors=c["mut"], labelsize=8)
    for s in ("top", "left", "bottom"):
        ax2.spines[s].set_visible(False)
    ax2.spines["right"].set_color(c["line"])
    ax.axvline(spot_now, color=c["line"], linewidth=1.0)
    fig.tight_layout()
    return fig


def breakeven_figure(days, theta_cost, gamma_pnl, dark=False):
    """Daily theta cost against the gamma P&L of a one-sigma move.

    Where they cross is the gamma/theta breakeven: you break even on a day the
    underlying moves exactly its implied daily move.
    """
    c = DARK if dark else LIGHT
    fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=140)
    _style(ax, c, xlabel="calendar days to expiry")
    ax.plot(days, theta_cost, color=c["bad"], linewidth=2.0, label="theta cost / day")
    ax.plot(days, gamma_pnl, color=c["acc"], linewidth=2.0, label="gamma P&L, 1-sigma move")
    ax.set_ylabel("$ per day", color=c["mut"], fontsize=8)
    ax.invert_xaxis()
    leg = ax.legend(frameon=False, fontsize=8, loc="upper left")
    for t in leg.get_texts():
        t.set_color(c["mut"])
    fig.tight_layout()
    return fig
