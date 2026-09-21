# Tests

Tests are not scaffolding around the system. They are part of it, and they are the component that
decides whether any of the other rules in this skill can be applied at all: without tests you cannot
refactor, and without refactoring code rots. Read this when writing tests, changing tested behavior,
or deciding how much verification a change needs.

## The Three Laws of TDD

1. Write no production code until you have written a failing test.
2. Write no more of that test than is sufficient to fail — including failing to compile.
3. Write no more production code than is sufficient to pass the currently failing test.

The cycle is on the order of tens of seconds, and the tests and the production code grow together.

**Apply it without the escape hatch.** "Write tests first when feasible" is not the rule; the reason
the laws are stated as laws is that "when feasible" becomes never under time pressure. Where you
genuinely cannot go test-first — an unfamiliar API whose behavior you must probe, a spike you intend
to throw away, a change in code with no test harness at all — say so explicitly and say what you did
instead. That is an honest deviation. Silence is not.

For an agent specifically: the failing test is what stops you from claiming success from memory. A
test you watched fail and then pass is evidence. A test written afterwards, against code you already
wrote, mostly re-asserts your own assumptions.

## Why clean tests matter more than clean production code

Tests preserve and enhance the flexibility, maintainability and reusability of the production code —
the *-ilities*. The logic is direct: tests are what let you change code without fear, so the higher
your test quality, the less you fear change, and the more you improve the design.

The inverse runs faster than people expect. Dirty tests are hard to change, so they rot as the
production code evolves; then they fail for the wrong reasons; then they get deleted or skipped; and
then the production code can no longer be changed safely. **A test suite abandoned for being
unmaintainable takes the production code's flexibility with it.**

So: test code is production code. It does not get a lower standard.

## Readability, and the dual standard

Readability is what makes a test useful — clarity, simplicity, density of expression. A test should
say the maximum with the minimum.

Tests get a **dual standard**: they may be less efficient than production code, because they run in a
controlled environment where memory and cycles rarely matter. They may not be less *clear*. Trading
efficiency for readability in a test is correct; trading readability for cleverness is not.

## BUILD-OPERATE-CHECK

The default shape of a test, in three visible parts:

1. **Build** the data and world the test needs.
2. **Operate** on it — the single action under test.
3. **Check** that the outcome is what was expected.

Keeping the three parts visually distinct is most of what makes a test readable. When the build step
grows large enough to obscure the other two, that is the signal to extract it into a helper — which
is how a testing language gets started.

## A domain-specific testing language

Tests read best when written in a vocabulary built for the tests themselves: helper functions and
builders that let each test state the behavior it describes rather than the mechanics of arranging
it. This language is refactored into existence over time, not designed up front — you notice the
same setup three times and give it a name.

The point is not brevity. It is that a reader can tell what the test asserts without decoding how it
got there.

## One assert, and single concept per test

The commonly quoted rule is one assert per test. Treat it as a direction, not a law: the number of
asserts in a test should be **minimized**, and the real rule underneath it is **one concept per
test**.

- Multiple asserts checking one concept are fine — an outcome with several fields is one concept.
- One assert per test is worth reaching for when it splits a test that was checking two things.
- A test whose name needs "and" is testing two concepts. Split it, exactly as with functions.

The failure this prevents: a test that checks three concepts fails for three reasons, so its failure
tells you almost nothing, and the second and third concepts are never checked once the first breaks.

## The F.I.R.S.T. properties

- **Fast.** Slow tests get run rarely; rarely-run tests stop catching things, and then rot.
- **Independent.** No test sets up the world for another. Order dependence means one failure
  cascades, and the cause is hidden.
- **Repeatable.** Same result in any environment, including offline and on a laptop. A test that only
  passes in one place will be ignored when it fails elsewhere.
- **Self-validating.** A boolean outcome — pass or fail. If judging the result requires reading a log
  or comparing files by eye, evaluation becomes subjective and the test becomes optional.
- **Timely.** Written just before the production code they cover. Written afterwards, the production
  code tends to be shaped in a way that resists testing.

## What to test, matched to risk

| Change | Verification that actually proves it |
| --- | --- |
| Pure function | Focused unit test on behavior and boundaries |
| Bug fix | A test that reproduces the bug first, then goes green |
| Refactor | The existing tests, run before and after; add characterization tests first if there are none |
| API or boundary change | Contract or integration test at the boundary |
| Concurrency change | See `concurrency.md` — a normal unit test proves very little here |
| Legacy code with no tests | Characterization tests capturing what it does now, including its oddities |

Boundary conditions and the code near a bug you just found deserve extra attention: defects cluster,
and the place a bug appeared is the place the next one will.

## Failure modes to avoid

- **Structural coupling to production code** — a test class per production class, a test method per
  production method. This is one of the strongest and most insidious forms of coupling: it makes
  tests fragile and production code rigid, and it blocks the divergence that should happen as
  production code grows more general while tests grow more specific.
- **Driving business rules through the UI.** The GUI is the most volatile surface in the system, so a
  suite that reaches business rules through it is fragile by construction. Test through the use case;
  keep the view humble (see `architecture.md`).
- **Weakening, skipping or deleting a failing test to get green.** A failing test is information
  about the code. Burying it converts a known problem into an unknown one — and it is the single most
  damaging thing an agent can do to a codebase, because it removes the signal that everything else
  depends on.
- **Broad snapshots as the only assertion.** They pass until everything changes at once, then tell
  you nothing about what broke.
- **Sleeps and timing guesses.** Flaky by design; see `concurrency.md`.
- **Excessive mocking of your own code.** A test that mocks three of your own modules is asserting
  your design, not your behavior.
- **Tests that duplicate implementation logic.** They agree with the code by construction, including
  when the code is wrong.
- **Sporadic failures dismissed as noise.** Treat them as candidate defects, usually threading.

## Where tests sit architecturally

Tests are a system component in the outermost circle: maximally detailed, depending inward, depended
on by nothing. The first rule of design applies to them too — do not depend on volatile things.

When the suite is large enough that tests need privileged access to force states, bypass security, or
avoid expensive resources, that is a **testing API**: a superset of what the UI uses, whose job is to
hide the application's structure from the tests. Keep it, and its dangerous implementation, in a
separately deployable component. See `architecture.md`.

## Related

- `principles.md` — the summary rules and the rest of the code-level detail.
- `concurrency.md` — why threaded code needs a different testing strategy.
- `architecture.md` — the test boundary, the humble object, and designing for testability.
- `chapter-map.md` — the T1-T9 test smells.
