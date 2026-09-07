# Conventions — decided 2026-09-06

Locked. Changing any of these later means re-deriving every test fixture, so they are recorded here
rather than left implicit in the code.

## D1 — Time: TWO clocks, not one

Sajan chose trading days. **Correct for volatility, wrong for discounting** — and the distinction
matters enough to encode.

`T` appears twice in Black-Scholes and means something different each time:

| Where | Clock | Why |
|---|---|---|
| `exp(-r*T)` — discounting | **calendar / 365** | Interest accrues on weekends. Money does not stop over a Saturday. |
| `sigma*sqrt(T)` — vol scaling | **trading / 252** | Variance accumulates only while the market is open. A closed market generates (almost) no variance. |

**Implementation decision: use calendar/365 for `T` inside the pricer.** Reason: implied vol quoted
in the market is backed out using calendar time, so a calendar-time pricer is consistent with quoted
IV and keeps put-call parity exact against the discount factor. Mixing clocks inside one formula
breaks parity, and parity is our primary oracle — we do not sacrifice the oracle for realism.

**Trading days reappear where they belong: the rule of 16.** `sqrt(252) = 15.87 ~ 16`, so
`daily_move ~ annual_vol / 16`. That lives in the simulator's daily-move display, not in the pricer.

Both conventions are therefore present, each doing the job it is right for. Name the fields so the
clock is unambiguous: `T_years_calendar`, and `TRADING_DAYS_PER_YEAR = 252` as a named constant.

## D2 — Volatility units: DECIMAL

`sigma = 0.24` means 24%. Never `sigma = 24`.

**The failure this prevents** is silent, not loud: passing `24` into a function expecting `0.24`
produces a price that is wrong by orders of magnitude and raises nothing. It looks like a number.

**Guard:** validate at the boundary. `if not 0 < sigma < 5: raise ValueError`. That admits a
plausible 500% vol and rejects a mis-scaled 24. Percent-to-decimal conversion happens once, at the
UI edge, and never inside `core/`.

*(Precedent: two systems in this workspace produced confidences on mixed scales this week --
0.78 sitting beside 68 in one table, where the 0.78 read as least-confident when it was most.
Same bug class, cheaper here.)*

## D3 — Multiplier: 100, applied at the POSITION, not in the pricer

Sajan is right that 100 is the standard equity/index option multiplier. The architectural question
was *where the x100 lives*, and the answer is: not in the math.

- `core/bs.py` returns a **per-unit** price. It knows nothing about contracts.
- `Leg` carries `quantity` and `multiplier`.
- `Position.value()` performs `price * quantity * multiplier`.

**Why:** the multiplier is a property of the *contract*, not of the *model*. Bake 100 into the pricer
and a contract with a different multiplier requires editing the pricing math — which is the one place
edits are dangerous. It also keeps every pricer test in clean units, so a textbook reference value
can be compared directly without dividing by 100 first.

`MULTIPLIER_DEFAULT = 100`, overridable per leg.

## D4 — Dividends: deferred, but the parameter exists NOW

`q` (continuous dividend yield) is a parameter from day one, defaulting to `0.0`.

**Why now:** adding a parameter later changes every call signature and every test. Adding it now with
a zero default costs one line and changes nothing about the results.

Discrete dividends are out of scope. Revisit only if single-name options are needed.

## D5 — Float, not Decimal

Correct, and here is the reasoning, since it is the more useful half.

**The rule: use Decimal when your number must equal someone else's number. Use float when your
number is your own estimate.**

- The **fee project** reconciles to an exact cent. A counterparty independently computed that figure
  and the two must match. `0.1 + 0.2 != 0.3` in binary floating point, and that error compounds
  across millions of contracts into real dollars. Decimal.
- **Pricing** produces a model output. There is no external correct answer to match — the model is
  already an approximation of a market that does not obey it. Black-Scholes needs `exp`, `log` and
  `sqrt`, which are float operations. And precision past ~10 significant figures is meaningless when
  the vol input is uncertain in the second decimal place.

**Consequence for testing:** never compare floats with `==`. Use `pytest.approx` with an explicit
tolerance, and choose the tolerance deliberately — `1e-9` for parity (it should hold nearly exactly),
`1e-4` for finite-difference greeks (the approximation itself has error).
