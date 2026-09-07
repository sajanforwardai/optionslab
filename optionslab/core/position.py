"""Multi-leg positions and aggregate risk.

The contract multiplier lives HERE, not in the pricer. Black-Scholes returns a
per-unit price; a Leg knows how many units a contract represents. Baking 100 into
the math would mean a different multiplier requires editing the pricing code, which
is the one place edits are dangerous.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import greeks as gk
from .bs import price

MULTIPLIER_DEFAULT = 100.0


@dataclass(frozen=True)
class Leg:
    """One line of a position.

    kind:       'call', 'put', or 'stock'
    quantity:   signed. +1 long one contract, -1 short one contract.
    strike:     required for options, ignored for stock
    multiplier: units per contract. 100 for standard equity/index options.
                Stock legs use 1.0 unless you are trading in round lots.
    """
    kind: str
    quantity: float
    strike: float | None = None
    multiplier: float = MULTIPLIER_DEFAULT

    def __post_init__(self) -> None:
        k = self.kind.lower()
        if k not in ("call", "put", "stock"):
            raise ValueError(f"kind must be call, put or stock, got {self.kind!r}")
        if k in ("call", "put") and self.strike is None:
            raise ValueError(f"{k} leg requires a strike")

    @property
    def is_option(self) -> bool:
        return self.kind.lower() in ("call", "put")

    def value(self, S, T, r, sigma, q=0.0) -> float:
        if not self.is_option:
            return S * self.quantity * self.multiplier
        unit = price(self.kind, S, self.strike, T, r, sigma, q)
        return unit * self.quantity * self.multiplier

    def greeks(self, S, T, r, sigma, q=0.0) -> dict:
        scale = self.quantity * self.multiplier
        if not self.is_option:
            # Stock: delta 1 per unit, every other greek zero.
            return {"delta": scale, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
        g = gk.all_greeks(self.kind, S, self.strike, T, r, sigma, q)
        return {k: v * scale for k, v in g.items()}


@dataclass
class Position:
    legs: list[Leg] = field(default_factory=list)

    def add(self, leg: Leg) -> "Position":
        self.legs.append(leg)
        return self

    def value(self, S, T, r, sigma, q=0.0) -> float:
        return sum(leg.value(S, T, r, sigma, q) for leg in self.legs)

    def greeks(self, S, T, r, sigma, q=0.0) -> dict:
        total = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
        for leg in self.legs:
            for k, v in leg.greeks(S, T, r, sigma, q).items():
                total[k] += v
        return total

    def payoff_at_expiry(self, S: float) -> float:
        """Terminal value. No model, no discounting — pure arithmetic on the payoff."""
        out = 0.0
        for leg in self.legs:
            scale = leg.quantity * leg.multiplier
            if not leg.is_option:
                out += S * scale
            elif leg.kind.lower() == "call":
                out += max(S - leg.strike, 0.0) * scale
            else:
                out += max(leg.strike - S, 0.0) * scale
        return out


# --- constructors for the standard structures ---

def vertical_call_spread(lower: float, upper: float, qty: float = 1.0, mult: float = MULTIPLIER_DEFAULT) -> Position:
    return Position([Leg("call", qty, lower, mult), Leg("call", -qty, upper, mult)])


def straddle(strike: float, qty: float = 1.0, mult: float = MULTIPLIER_DEFAULT) -> Position:
    return Position([Leg("call", qty, strike, mult), Leg("put", qty, strike, mult)])


def conversion(strike: float, qty: float = 1.0, mult: float = MULTIPLIER_DEFAULT) -> Position:
    """Long stock, short call, long put — all at one strike.

    Delta is approximately zero and the value is an interest rate: this is the
    synthetic that makes put-call parity tradeable.
    """
    return Position([
        Leg("stock", qty * mult, None, 1.0),
        Leg("call", -qty, strike, mult),
        Leg("put", qty, strike, mult),
    ])
