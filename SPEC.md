# OptionsLab — an options pricing and position simulator

**Purpose.** Build the greeks into your hands before Group One teaches them. The deliverable is a
tested pricing library plus a simulator that makes option behaviour visible — how a position's
greeks move as spot, vol and time change.

**Written** 2026-09-06. Target: working core before ~2026-09-20.

---

## 1. The design principle everything follows from

**The oracle goes in before the thing it checks.**

This project's predecessor in this workspace (`group-one-research/praxis/phase1/`) shipped 23,357
lines and 1,533 green tests while asserting a value that did not exist in its source document. It
failed because the only thing checking its claims lived four lines away from the claims themselves.

Options pricing hands you three oracles for free, and they come from mathematics rather than from
anything you wrote:

| Oracle | The invariant | What it catches |
|---|---|---|
| **Put-call parity** | `C - P = S - K*exp(-rT)` | Any error in either pricing path |
| **Finite differences** | `(V(S+h) - V(S-h)) / 2h` -> analytic delta | Any error in a greek |
| **IV round-trip** | price at sigma -> solve -> get sigma back | Any error in the solver |

None can be edited into agreement, because none of them is your opinion. **Write these as tests
before writing the code they test.**

---

## 2. Architecture

```
optionslab/
  core/            <- pure functions. no I/O, no printing, no display.
    bs.py            price(), d1(), d2()
    greeks.py        delta, gamma, vega, theta, rho
    iv.py            implied_vol()   [root-finding]
    position.py      Leg, Position, aggregate greeks
  display/         <- renders. NEVER computes.
    text.py          CLI output
    plots.py         matplotlib figures
  app/             <- the simulator surface
  tests/
```

**The load-bearing rule: `display/` may not contain arithmetic.** Every number it shows is computed
in `core/` and passed in. This keeps the test suite covering 100% of the math and makes it
structurally impossible for the UI to invent a number the tests never saw.

---

## 3. Decisions you should make before I write code

These are real forks with real consequences. Your answers shape the schema.

**(a) Time convention.** `T` in years. Calendar days / 365, or trading days / 252? An option 30
calendar days out is ~21 trading days. The two give visibly different prices and theta. Which is
right, and does the answer change between pricing and risk?

**(b) Volatility units.** Store 0.24 or 24? Whichever you pick, the other must be impossible to pass
by accident. *(Two systems in this workspace this week produced mixed-scale numbers that were
unreadable side by side. Pick one, name the field so the unit is obvious, validate at the boundary.)*

**(c) Contract multiplier.** Is your unit one option, or one contract of 100? Where does the x100
live — in the price, in the position, or only at display? Getting this wrong is the single most
common P&L error a new analyst makes.

**(d) Rates and dividends.** Continuous `r` and `q`, or discrete dividends? Continuous is simpler and
standard for index options. Do you need discrete for single names?

**(e) Float vs Decimal.** The fee project needed `Decimal` because it reconciles to the cent. Pricing
needs `exp()`, `log()` and `sqrt()`, which are float operations. **My recommendation: float for
pricing math, Decimal only if you later reconcile against real cash amounts.** Do you agree, and can
you say why the two problems differ?

---

## 4. Milestones

Each is small, testable, and ends with something you can run.

| # | Milestone | Done when |
|---|---|---|
| **M0** | **Parity test, no pricer** | A failing test asserting `C - P == S - K*exp(-rT)`. It must fail for the right reason: the functions don't exist yet. |
| **M1** | Black-Scholes price | Calls and puts. **M0 passes.** Plus: deep ITM call -> intrinsic; deep OTM -> ~0; T=0 -> payoff. |
| **M2** | Greeks, analytic | Each validated by finite difference to a stated tolerance. Sanity: ATM call delta slightly > 0.50 — and you can say why. |
| **M3** | Implied vol solver | Round-trip: price at 0.24, solve, recover 0.24. Handle no-solution (price below intrinsic) by raising, never by returning a guess. |
| **M4** | Payoff and P&L curves | Payoff at expiry (kinked) and value before expiry (curved), on one axis. The gap between them is time value — that picture teaches more than any paragraph. |
| **M5** | Multi-leg positions | Straddle, vertical, calendar. Greeks aggregate. **Test: a conversion (long stock + short call + long put) has delta ~0 and is rate-sensitive** — that is your groundwork self-test item 5, executable. |
| **M6** | Simulator surface | See §5. |
| **M7** | *(stretch)* Real surface | SPX snapshots with bid/ask and greeks from BigQuery. Compare your model IV against theirs. **Filter the partition column — it bills by bytes scanned.** |

**M0 before M1 is not ceremony.** It is the entire lesson of the failed predecessor, and here it
costs you twenty minutes.

---

## 5. How the simulator is displayed

Three surfaces, same core, built in this order.

### 5.1 CLI (M1-M3) — the development surface
Text output showing inputs, price, all greeks, and the parity residual on every call. If the residual
is not ~0, it prints loudly. You will run this hundreds of times.

### 5.2 Notebook (M4-M5) — the exploration surface
Jupyter, matplotlib. Where you build intuition and generate the plots. Standard in finance and
expected in a portfolio.

### 5.3 The simulator (M6) — the artifact

**A single page. Four panels. One position.**

```
┌─ INPUTS ─────────────────┬─ POSITION ──────────────────────┐
│ Spot      [====o=====]   │ Legs: +1 SPX 5000 C  -1 5100 C  │
│ Vol   %   [===o======]   │                                  │
│ Days      [=====o====]   │ Value      $ 1,240               │
│ Rate  %   [==o=======]   │ Delta        +0.18   Gamma +0.002│
│                          │ Vega         +2.10   Theta -0.85 │
├─ P&L vs SPOT ────────────┼─ GREEKS vs SPOT ────────────────┤
│      ╱‾‾‾‾‾              │  delta ___/‾‾‾                  │
│  ___╱                    │  gamma  _/‾\_                   │
│  ── at expiry            │                                  │
│  ── today                │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

**What makes it a learning tool rather than a calculator:** every control is a slider, and the greeks
and both curves update live. You *watch* gamma peak at the money and collapse away from it. You
*watch* theta accelerate into expiry. You *watch* the "today" curve fall toward the kinked expiry
payoff as days tick down. That is the intuition mock-trading sessions test, and it is very hard to
get from a textbook.

**One panel worth building deliberately: the gamma/theta breakeven.** Show the daily theta cost
beside the gamma P&L from a one-standard-deviation move. When they cross, you have shown that you
break even on a day the stock moves exactly its implied daily move — groundwork self-test item 10,
made visible.

**Technology:** Streamlit if you want sliders cheaply (you already run Streamlit apps on the host).
Static HTML + inline JS if you want it deployable to `forwardai.dev/sajan/` as a portfolio artifact.
**Start with Streamlit locally; port to static later only if you want it public.**

**If it goes public it must follow the house dashboard standard:** white background with near-black
text by default and a toggle to dark, tokens copied verbatim from `/workspace/.library/dashboard-theme.html`,
verified with `dashboard-lint` before deploy. And a specific trap for plotting: canvas visuals using
`globalCompositeOperation='lighter'` are **invisible on white** — use `source-over` and darken fills
in light mode.

---

## 6. Python concepts, by milestone

| Milestone | What to learn |
|---|---|
| M0-M1 | `math` module, functions, type hints, `pytest` basics, `pytest.approx` for float comparison |
| M2 | Closures or partials for the bump-and-reprice helper; why `==` is wrong for floats |
| M3 | Root-finding (bisection first — it always converges; Newton second — it's fast and can diverge); raising exceptions rather than returning `None` |
| M4 | matplotlib figure/axes API; numpy vectorisation over a spot grid |
| M5 | `@dataclass` for `Leg`; list comprehensions; `sum()` over legs |
| M6 | Streamlit's rerun model — the whole script re-executes on every slider move, which surprises everyone once |

**Not needed:** classes beyond dataclasses, async, decorators, ORMs, inheritance.

---

## 7. Test cases where the answer is known independently

- **Parity**, every strike and expiry. Non-negotiable.
- **T -> 0**: value converges to payoff.
- **sigma -> 0**: value converges to discounted intrinsic.
- **Deep ITM call**: delta -> 1. **Deep OTM**: delta -> 0.
- **Gamma is maximal ATM** and symmetric in log-moneyness.
- **Vega -> 0** as T -> 0.
- **Published reference values** — take a worked example from Hull or Natenberg and match it. An
  external textbook answer is an oracle you did not write.
- **A conversion has ~zero delta** and its value is an interest rate. (Self-test item 5.)

---

## 8. First task

**Write M0.** A single test file asserting put-call parity, importing functions that do not exist.
Run it. Watch it fail with `ImportError`.

That failing test is the specification for M1, and it is in place before any code it can be
compromised by.
