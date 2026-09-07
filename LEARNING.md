# How we work — the learning protocol

## The failure this is designed against
Reading code that makes sense feels identical to understanding it, and is not. The gap only shows up
when you try to write it unaided, which — if we are careless — is at Group One, in front of someone.

Everything below exists to force the difference into the open early, while it is cheap.

---

## 1. Name the mode at the start of every session

Two legitimate modes. The danger is drifting between them without noticing.

| Mode | Who types | Use when |
|---|---|---|
| **LEARN** | Sajan | The concept is load-bearing: pricing math, greeks, anything financial |
| **BUILD** | Claude | Plumbing: file I/O, CLI scaffolding, matplotlib boilerplate, Streamlit layout |

Say which at the start. "Learn mode" means I will not write the code even if asked twice — I will
hint. "Build mode" means I write it and you review it.

**Default is LEARN for anything in `core/`, BUILD for anything in `display/`.**

## 2. Attempt before explanation — always

Before I show you anything, you attempt it. Five minutes of a wrong attempt is worth more than
thirty minutes of a correct explanation, because the attempt creates the hook the explanation
attaches to. Explanation without a prior attempt slides off.

A wrong attempt is not a waste. It is the mechanism.

## 3. The hint ladder

When stuck, say which level you want. If you do not say, I start at L1 and escalate roughly every
ten minutes.

| Level | What you get |
|---|---|
| **L1** | A question back. *"What should this return when T is zero?"* |
| **L2** | The concept named, not applied. *"This is root-finding. Bisection always converges."* |
| **L3** | The shape. Function signature, pseudocode, the structure with the logic missing. |
| **L4** | Working code, with an explanation of the parts that matter. |

**Ask for L4 whenever you want it.** The ladder is a default, not a gate. But notice if you are
always asking for L4 — that is the illusion forming.

## 4. The explain-back gate

You do not start milestone N+1 until you can explain milestone N **without looking at the code**.

Not "roughly what it does" — actually explain it: what it takes, what it returns, why that approach,
what breaks it. Out loud or written, but unaided.

If you cannot, that is not a failure. It is the signal that we go back, and it is exactly the signal
this protocol exists to generate. **The gate failing is the system working.**

## 5. You write the log, not me

`LOG.md` in this directory. After every session, in your own words, no looking:

- What we built
- What I did not understand at first
- The one thing I would tell someone else about this

That is retrieval practice, and it is the highest-return ten minutes in the session. It is also what
lets you resume cold after a week of not touching this, which will happen once the co-op starts.

**Notes I write for you are reference. Notes you write are learning.** Both have a place; only one
of them is the point.

## 6. Debug before rescue

When something breaks, you diagnose first. I hint at L1-L2.

More learning is concentrated in one bug you fixed than in five features you watched get built. If I
rewrite it the moment it breaks, I have taken the most valuable part of the session.

Exception: if you are stuck past twenty minutes with no new information, we escalate. Productive
struggle has a shelf life.

## 7. Session shape

**Pre-start (now to ~Sep 20): 60-90 min blocks.**
**During the co-op: 30-45 min. Milestones must fit one sitting.**

1. **(5 min)** Read your own last `LOG.md` entry. Before anything else. Recall first.
2. **(10 min)** I state the objective and design. You ask questions.
3. **(20-40 min)** You attempt. I hint.
4. **(10 min)** Run the test. Watch it pass or fail.
5. **(10 min)** You write the log entry, unaided.

Step 1 and step 5 are the ones people skip and the ones that make it stick.

## 8. Weekly review, 15 minutes

Once the co-op starts: one 15-minute pass per week over prior milestones. Re-derive one result from
memory — put-call parity, or why an ATM call's delta exceeds 0.50.

Spaced retrieval beats a marathon. This is also the only part of the protocol that survives a
genuinely bad week at work.

## 9. The generation limit

**Generate at the rate you can verify, not the rate you can produce.**

The predecessor project in this workspace produced 23,357 lines in about two days and blocked partly
because nobody could hold it in their head. It passed 1,533 tests while asserting a value absent from
its source document.

Hard limit for this project: **if you cannot explain every line in a file, that file does not grow.**

---

## What this project is NOT competing with

M1-M3 **are** Layers 04 and 05 of `group-one-research/08-OPTIONS-GROUNDWORK.md` — pricing and the
greeks, and volatility as a price. Building the pricer *is* the options study, not a substitute for
it and not a distraction from it.

Layers 01-03 — mental arithmetic, contract mechanics, put-call parity as a reflex — are separate and
still daily. Ten minutes of Zetamac is not replaced by anything here.
