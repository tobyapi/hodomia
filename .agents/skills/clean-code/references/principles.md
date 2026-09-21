# Code-Level Principles

The detail behind the one-line rules in `SKILL.md`. Read the section you need when a decision is
not obvious; the summary in SKILL.md is enough for routine work.

Every rule here is subordinate to the project's own idiom. Clean code should look like it was
written by a senior maintainer of *that* stack. See `framework-map.md` when the ecosystem is
unfamiliar.

## Meaningful Names

Names should reveal intent without requiring mental decoding.

Use:

- domain vocabulary from the project
- searchable names for important concepts; name length proportional to scope
- one word per concept across the codebase — and never one word for two different concepts
- boolean names that read as predicates
- units in names when values carry units
- names that disclose side effects: a function that saves, deletes, publishes, or mutates should
  say so

Avoid:

- misleading names and false distinctions
- generic names like `data`, `manager`, `helper`, `util`, `info`, `process`, or `result` when a
  domain name exists
- type encodings unless the language ecosystem expects them
- abbreviations that are not established in the project
- names that differ only by noise words
- mental mapping: a name the reader has to translate back into the concept

**Verbs and keywords.** Where argument order or meaning could be misread, put it in the name.
`assertExpectedEqualsActual(expected, actual)` cannot be called backwards by accident;
`assertEquals(a, b)` can.

## Small Focused Functions

A function should do one thing at one level of abstraction. (This is the rule commonly misattributed
to the Single Responsibility Principle. It is a real rule and worth following — it is simply not
the SRP, which is about actors. See `architecture.md`.)

Prefer:

- early exits for invalid or terminal cases when idiomatic
- extraction when a block has a clear independent purpose
- **the Stepdown Rule**: the file reads top-down, callers above callees, each level descending exactly
  one step in detail
- few parameters — the **arity** ladder is niladic (none, ideal), monadic (one), dyadic (two, fine
  when the two are naturally ordered), triadic (three, needs special justification), polyadic (more,
  which means the arguments are an unnamed object waiting to be created)
- command-query separation: either answer a question or cause a change, not both
- explanatory variables that name intermediate steps of a computation
- positive, encapsulated conditionals: name a complex condition instead of inlining a tangle of
  negations

Avoid:

- boolean flags and mode selectors that make one function do unrelated jobs
- functions that validate, transform, persist, log, notify, and render at once
- hidden mutation of inputs or global state; mutating parameters as outputs
- nested conditionals that hide the main path
- copy-pasted branches with tiny differences
- the same type-switch or if/else chain repeated in multiple places — route variation through one
  dispatch point (polymorphism, a handler map, pattern matching) when the language supports it

Decompose until every unit can be falsified by a test. Code that cannot be tested by design is an
architectural defect, not a coverage gap. And remember what tests can prove: they show the presence
of bugs, never their absence. Correctness is demonstrated by failing to prove incorrectness.

## Comments And Documentation

Good comments explain why the code must be this way.

Keep comments for: non-obvious constraints, legal requirements, algorithmic tradeoffs, external
system quirks, warnings of consequences, and TODOs with context and ownership where the project
uses them.

Remove or avoid comments that: repeat the code, go stale and lie, explain names that should be
clearer, preserve commented-out code, narrate your editing process ("added this function to..."),
or add banners the project does not use.

Never leave a comment that explains where the code came from, why your change is correct, or what
the next line does. That is a message to a reviewer, and it becomes noise the moment the change
merges.

## Formatting And Layout

The formatter owns whitespace. It does **not** own ordering, and ordering is where the design shows.

- Match the project's formatter and import order; never hand-format against it.
- Do not reformat a file while making a small change unless formatting is the requested change.
- **The newspaper metaphor**: the file opens with the highest-level intent and descends into detail.
  A reader should be able to stop after the first screen and know what the file is for.
- **Vertical distance** — keep related things close. Declare a variable near its first use; keep a
  caller adjacent to the function it calls, caller first.
- **Conceptual affinity** — code that reads as one idea belongs together even when nothing calls
  across it: a family of overloads, a set of related constants.
- **Vertical ordering** — dependency runs down the file, so reading top to bottom never requires
  knowing what comes later.
- **Vertical openness and density** — blank lines separate concepts; adjacency signals that lines
  belong to one thought. Neither is decoration.
- Horizontal spacing shows grouping. **Skip alignment theater** — aligned columns of assignments
  break the moment a name changes and draw the eye to the wrong axis.
- **Indentation reflects scope honestly.** No collapsing a block onto one line to look compact, and
  no **dummy scopes** — an empty loop or `if` body hiding behind a bare semicolon. Make the body
  visible or delete the construct.

## Data, Objects, And Modules

- Use plain data structures for plain data; use objects, records, or types to protect real
  invariants. **Data/object anti-symmetry**: an object hides data and exposes behavior; a data
  structure exposes data and implies no behavior. They are opposites, and each makes easy what the
  other makes hard — adding a new *type* is cheap with objects and expensive with data structures,
  while adding a new *operation* is the reverse. Code that treats one as the other is where "anemic"
  and "god object" designs both come from.
- Avoid the **hybrid**: public fields *and* behavior pretending to protect invariants. It takes the
  disadvantages of both. Pick one.
- **The Law of Demeter** — ask a collaborator for a decision rather than navigating its internals. A
  method should talk to what it directly holds, not to what those things return.
- A **train wreck** (`a.b().c().d()`) couples you to every link in the chain, so a change to any of
  them breaks you (smell G36). Splitting it across named locals does not fix it — the coupling is the
  problem, not the line length.
- Keep public APIs smaller than internal implementation details. Default to the narrowest access
  modifier the language offers; every public type is a potential inbound dependency.
- Prefer explicit dependencies over hidden globals and singletons.
- Be precise: money, time, time zones, encodings, identity, and units deserve exact types and
  explicit handling, not floats and strings by default.
- Keep configurable values at the top levels of the system, passed down — not buried as literals in
  low-level functions.

## Error Handling

Errors are part of the design, not a cleanup afterthought.

Do:

- design the failure path when you write the happy path, not after; for risky operations, sketch the
  error contract first
- handle errors at the level that can make a meaningful decision
- preserve context and original causes when wrapping
- model expected alternate outcomes (not found, empty, declined) as values, result types, or
  special-case objects — the **Special Case pattern**. Reserve exceptions for genuine failures, so
  the caller never needs exceptional control flow for an ordinary case
- **prefer unchecked exceptions** where the language distinguishes them. A checked exception forces
  every signature between the throw and the handler to declare it, so adding one low down breaks
  encapsulation all the way up the call chain. Use checked exceptions only where a caller genuinely
  must handle the case and the API is stable
- avoid the **dependency magnet**: one shared error enum or constant class that every caller imports.
  Every new error value forces everything to recompile, and nobody can extend it without touching
  shared code. Prefer distinct exception types, or wrap a third-party API so only your wrapper knows
  its error vocabulary
- make retry, fallback, timeout, and cancellation behavior explicit
- keep the happy path readable: extract error handling when it drowns the main logic

Do not:

- swallow errors silently or catch broadly without rethrowing, wrapping, or reporting
- return null-like values or ignorable sentinels where the language has safer options
- pass null where an absence type or overload is available
- log secrets, tokens, personal data, or sensitive payloads

## Boundaries

Boundaries are where bugs multiply: external APIs, databases, file systems, clocks, queues, UI
events, network calls, subprocesses, generated code.

- Validate inputs at trust boundaries.
- Keep third-party API assumptions localized behind an interface you own; do not let a vendor type
  spread through the codebase. Declare that interface on *your* side of the boundary — the API is
  owned by its user, not its implementer.
- Write a small learning test when adopting an unfamiliar library — it documents your assumptions
  and catches upgrades that break them.
- Make serialization, time zones, encodings, units, and nullability explicit at the edge.
- Add contract or integration tests when boundary behavior matters.

For which direction dependencies may cross a boundary, and what data may cross it, see
`architecture.md`.

## Tests

Tests should make behavior easy to understand and safe to change. Treat test code as production
code — it is a system component, not scaffolding.

**`tests.md` holds the full discipline**: the Three Laws of TDD, F.I.R.S.T., BUILD-OPERATE-CHECK, the
dual standard, single concept per test, and the testing language. Read it when writing tests. The
summary below is enough for judging existing ones.

Prefer tests that:

- use behavior-focused names and test one concept each
- assert outcomes, not implementation details
- cover the changed edge cases and the boundaries where bugs were just found
- are deterministic, isolated, and fast enough to run constantly
- use readable fixtures and fail for the right reason

Avoid:

- broad snapshots as the only assertion
- sleeps and timing guesses
- excessive mocking of your own code
- tests that duplicate implementation logic
- a test class per production class and a test method per production method — this structural
  coupling makes tests fragile and production code rigid
- driving business rules through the GUI, which is the most volatile surface in the system
- weakening, skipping, or deleting a failing test to make the suite pass — a failing test is
  information about the code, not an obstacle

## Concurrency And State

Concurrent code must make ownership and ordering visible. **`concurrency.md` holds the detail** —
the execution models, the four deadlock conditions, locking discipline, and the seven tactics that
actually catch a race. Read it before writing threaded code; a normal unit test proves very little
there.

Check: shared mutable state, cancellation and timeout behavior, lock ordering, idempotency under
retries, lifecycle cleanup, event ordering and backpressure, race-prone tests.

Prefer immutability, message passing, transactions, actor-like isolation, or language-native
concurrency guarantees when idiomatic. Keep concurrency policy separate from business logic. Treat
sporadic test failures as possible concurrency bugs, not noise to retry away.

Race conditions, deadlocks, and concurrent-update defects all trace to mutable variables — there
are no deadlocks without mutable locks. So default to immutable data and derive new values, and
confine mutation to small, named, deliberately chosen components. Compare-and-swap on a single cell
is not safe once several interdependent values must change together.

## Security As Clean Code

- Validate and encode at boundaries; use parameterized queries and safe APIs.
- Keep authorization checks close to protected operations or centralized in an enforced policy
  layer. Be especially careful with a shortcut that bypasses a layer: the logic being skipped is
  sometimes the only per-record authorization in the system.
- Do not log secrets or sensitive data; do not hardcode credentials. Read secrets from the
  environment or a secret store.
- Prefer well-maintained standard libraries for crypto, parsing, auth, and serialization.
- Make privilege, trust, and data retention explicit.

## Performance

- Measure before optimizing non-obvious bottlenecks.
- Keep algorithmic complexity visible; avoid hidden N+1 access patterns at boundaries.
- Avoid premature caches, pools, indexes, and background jobs.
- When optimizing, record the measured reason and keep the simpler behavior covered by tests.
- Match conversation shape to boundary cost: a chatty exchange that is free in-process becomes a
  performance failure when the same boundary turns into a network call.

## Simple Design Priorities

When design choices conflict, decide in this order:

1. All tests pass — correctness outranks elegance.
2. No duplicated knowledge — **DRY**, one authoritative home per rule or fact. Confirm the
   duplication is *true* duplication first: copies that change for different reasons at different
   rates are not duplicates, and merging them is harder to undo than leaving them apart.
3. Intent is expressed — a reader can tell what and why.
4. Fewest elements — no class, layer, or indirection that the first three rules do not require.

The order is the tie-breaker. Never remove duplication in a way that breaks tests, and never add an
element the first three rules do not demand.

**LeBlanc's law — later equals never.** A cleanup deferred to "after the deadline" is a cleanup
cancelled, because the pressure that produced the shortcut does not abate. This is why in-scope
cleanup happens now and out-of-scope cleanup gets reported rather than promised.
