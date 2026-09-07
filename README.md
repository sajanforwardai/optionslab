# OptionsLab

An options pricing library and position simulator. Built to learn the greeks by implementing them.

## Status

In progress. Specification and conventions are complete; the first milestone is a deliberately
failing test. See `SPEC.md`.

## Design principle

**The oracle goes in before the thing it checks.**

Options pricing supplies three checks that come from mathematics rather than from anything in this
repository, so none of them can be edited into agreement with the code they test:

| Oracle | Invariant | Catches |
|---|---|---|
| Put–call parity | `C - P = S - K*exp(-rT)` | Any error in either pricing path |
| Finite differences | `(V(S+h) - V(S-h)) / 2h` → analytic delta | Any error in a greek |
| IV round-trip | price at σ → solve → recover σ | Any error in the solver |

Milestone 0 is therefore a parity test written against functions that do not exist yet. It fails on
`ImportError`, and that failing test is the specification for the pricer.

## Layout

```
optionslab/
  core/          pure functions — no I/O, no display
    bs.py          price, d1, d2
    greeks.py      delta, gamma, vega, theta, rho
    iv.py          implied vol — root finding
    position.py    Leg, Position, aggregate greeks
  display/       renders — never computes
tests/
```

`display/` contains no arithmetic. Every number it shows is computed in `core/` and passed in, so
the test suite covers all of the mathematics and the interface cannot produce a number the tests
never saw. The same rule rules out re-implementing the pricing math in JavaScript for a browser
build — Python computes a grid, the browser interpolates it.

## Conventions

Full reasoning in `DECISIONS.md`.

| Decision | Choice |
|---|---|
| Time — discounting | calendar / 365 |
| Time — volatility | trading / 252 (surfaces as the rule of 16) |
| Volatility units | decimal: `0.24` means 24%, validated `0 < σ < 5` |
| Contract multiplier | 100, applied at the position, not in the pricer |
| Numeric type | `float` — pricing is a model output, not a reconciliation |

## Running

```bash
./run test         # pytest
./run app          # streamlit on 8888
./run py <file>    # python, correct venv
```

Requires a virtualenv at `.venv` with `matplotlib streamlit pytest numpy`.

## License

Educational project. Closed-form models and public information only. No market data, no firm data,
and nothing here is investment advice or a pricing recommendation.
