# Clean-Code Chapter Map

This is an agent-oriented synthesis of the full clean-code source structure: 17 chapters, the deeper concurrency appendix, the SerialDate appendix, and the cross-reference appendix. It is not a replacement for the source text. Use it as a checklist so no major clean-code area is skipped during writing, refactoring, or review.

## How To Use This Map

- For a narrow task, jump to the relevant chapter area.
- For a review, scan chapters 2-13 plus the chapter 17 smell groups.
- For refactoring, scan chapters 3, 5, 10, 12, 14, 16, and 17. For whole-project cleanup, follow `project-refactor.md` and use this map inside each batch.
- For concurrent code, scan chapter 13 and Appendix A.
- For tests, scan chapter 9 and the tests smell group in chapter 17.
- For "where does this code or file belong" questions, combine chapter 10 (cohesion), G6, G17, G24, and the Where Code Lives section of the skill.

## Chapter 1: Clean Code

Core agent lesson: clean code is a professional obligation because mess compounds cost.

Apply this as:

- Treat code as read more than written.
- Prefer maintainable clarity over clever completion.
- Do not excuse mess because schedules are tight; "clean it later" almost always means never.
- **LeBlanc's law**: later equals never.
- Recognize that redesign pressure often comes from accumulated small neglect.
- Write for future maintainers as an author writes for readers.

### The Boy Scout Rule, and where this skill departs from it

The source rule is to leave the code a little cleaner than you found it — change one variable name
for the better, break up one function that is slightly too large, remove one small duplication —
every time you check code in.

**This skill deliberately narrows that rule, and you should know it is a departure.** An agent
applies it at a scale and speed the rule was not written for: a human improving one name while
passing through produces a two-line diff, whereas an agent doing the same across every file it opens
produces an unreviewable diff, drags unrelated and possibly untested code into the change, and buries
the actual fix. The reviewer then cannot tell which lines were the task.

So the rule here is: **clean the lines your task already touches, and report the rest.** A better
name, a removed dead branch, a clarified condition — inside the diff you already have, never by
widening it. Unrelated mess is named in your summary so a human can schedule it, or handled properly
under campaign mode in `project-refactor.md`, which exists precisely so that broad cleanup gets a
baseline, batches, and review.

The intent of the original is preserved — leave it better, never worse. What is dropped is the
license to widen the change surface, because for an agent that license costs more than it returns.

Agent questions:

- Does this change reduce or add future ownership cost?
- Am I improving only the touched path, or drifting into unrelated cleanup?
- Would a maintainer understand why this code exists six months from now?

## Chapter 2: Meaningful Names

Core agent lesson: names are the primary documentation layer.

Cover these concerns:

- intention-revealing names
- avoiding misleading names and false distinctions
- pronounceable, searchable names
- avoiding type or member encodings unless idiomatic locally
- avoiding mental mapping from terse names to meaning
- noun-like names for types and objects; verb-like names for behavior
- one consistent word per concept
- solution-domain terms when the implementation concept matters
- problem-domain terms when the business concept matters
- enough context without bloated prefixes everywhere

Agent questions:

- Does the name say why the value exists, not only what type it is?
- Are two names different only because of filler words?
- Would search find all uses of this domain concept?
- Does a function name disclose side effects such as persist, enqueue, notify, delete, mutate, or publish?

## Chapter 3: Functions

Core agent lesson: functions should be small, focused, and readable top to bottom.

Cover these concerns:

- small blocks and clear indentation
- one thing per function
- one abstraction level per function
- top-to-bottom stepdown flow
- careful handling of switch or selector logic
- descriptive function names
- few arguments, with related values grouped into real concepts
- avoiding flag arguments and output arguments
- avoiding hidden side effects
- separating commands from queries
- using idiomatic exceptions or error flows instead of ignorable status codes
- extracting error-handling blocks when they obscure the main path
- keeping error handling as one responsibility
- using structured control flow without clever jumps

Agent questions:

- Can I summarize this function without using "and"?
- Does each line sit at the same abstraction level?
- Does a boolean argument mean this is really two functions?
- Is the function secretly changing input, global state, or external systems?

## Chapter 4: Comments

Core agent lesson: comments are useful when they explain intent, constraints, warnings, or public contracts; they are harmful when they compensate for unclear code.

Keep comments for:

- legal requirements when needed
- useful context that code cannot express directly
- intent behind a non-obvious decision
- clarification of unavoidable ambiguity
- warnings about consequences
- TODOs with actionable context
- amplification of a subtle point
- public API documentation where the ecosystem expects it

Avoid comments that are:

- redundant with code
- misleading or stale
- mandated noise
- journal logs
- decorative markers
- closing-brace labels caused by oversized functions
- attributions that belong in version control
- commented-out code
- too much nonlocal background
- function headers for obvious private helpers

Agent questions:

- Can clearer names or extraction remove this comment?
- Does the comment explain why, or merely restate what?
- Could this comment become false when nearby code changes?

## Chapter 5: Formatting

Core agent lesson: formatting communicates structure before the reader understands the code.

Cover these concerns:

- the **newspaper metaphor**: the file opens with high-level intent, details descend below it
- **vertical openness** — blank lines separate concepts, not every line
- **vertical density** — related lines stay adjacent
- **vertical distance** — declare variables near use; keep dependent functions close, caller above
  callee
- **conceptual affinity** — code that reads as one idea belongs together even without a call between
- **vertical ordering** — the direction of dependency runs down the file
- horizontal openness and density show grouping; **skip alignment theater**
- **indentation reflects scope honestly** — no collapsing a short block onto one line, and no
  **dummy scopes** (an empty body hiding behind a semicolon)
- team formatter rules override personal preference

The formatter owns whitespace. It does not own **ordering** — vertical distance, vertical ordering,
and conceptual affinity are design decisions no tool makes for you. See `principles.md`.

Agent questions:

- Did I preserve local formatter behavior?
- Did I reformat unrelated code?
- Are related lines close enough that a reader does not hunt?

## Chapter 6: Objects And Data Structures

Core agent lesson: objects hide data behind behavior; data structures expose data for external behavior. Mixing both casually creates confusion.

Cover these concerns:

- data abstraction instead of leaking representation
- object/data tradeoff: adding new types vs adding new operations
- Law of Demeter and avoiding train-wreck navigation
- avoiding hybrids that expose fields while pretending to protect invariants
- DTOs for plain transport data
- Active Record patterns when the framework uses them, with domain behavior kept clear

Agent questions:

- Is this value just data, or does it protect behavior and invariants?
- Am I reaching through object internals instead of asking for behavior?
- Is a framework model becoming a dumping ground for unrelated logic?

## Chapter 7: Error Handling

Core agent lesson: error handling must preserve clarity in the happy path and context in the failure path.

Cover these concerns:

- prefer idiomatic exceptions/results over ignorable codes
- design the failure path first: sketch the error skeleton for a risky operation before filling in the happy path
- design try/catch or error branches around the caller's needs
- preserve context and original cause
- distinguish normal alternative flows from true failures; model expected alternate outcomes (not found, empty, declined) as values, result types, or special-case objects so callers do not need exceptional control flow for ordinary cases
- avoid returning or passing null-like values when the language has safer options
- keep error handling localized and cohesive

Agent questions:

- Can the caller make a useful decision from this error?
- Did I hide the original cause?
- Did I replace a real failure with a silent default?
- Is nullability or absence explicit in the type or contract?

## Chapter 8: Boundaries

Core agent lesson: external boundaries should be wrapped, learned, and tested so third-party change does not leak everywhere.

Cover these concerns:

- isolating third-party APIs behind local adapters
- learning tests for unfamiliar libraries
- contract tests for boundary behavior
- interfaces for code that does not exist yet
- keeping framework/vendor types out of core domains when possible
- validating serialization, time, encoding, and units at the edge

Agent questions:

- How many files know this third-party API shape?
- Is there a narrow local interface around the boundary?
- What happens when the vendor changes, times out, or returns malformed data?

## Chapter 9: Unit Tests

Core agent lesson: tests are production assets that enable change.

Cover these concerns:

- the **Three Laws of TDD**: no production code before a failing test; no more test than needed to
  fail; no more production code than needed to pass
- keep test code clean, readable, and maintainable — it is production code
- a **domain-specific testing language**: helpers that let a test read as the behavior it describes
- the **dual standard**: tests may trade efficiency for clarity, never clarity for cleverness
- **single concept per test**; minimize assertions rather than obeying a hard one-assert rule
- **BUILD-OPERATE-CHECK** as the default test shape
- **F.I.R.S.T.**: Fast, Independent, Repeatable, Self-validating, Timely

Full detail, including where each of these fails in practice, is in `tests.md`.

Agent questions:

- Would this test fail for the right reason?
- Is the fixture readable?
- Does this test describe behavior or mirror implementation?
- Are boundary cases and near-bug cases covered?

## Chapter 10: Classes

Core agent lesson: classes and modules should be small, cohesive, and organized around one reason to change.

Cover these concerns:

- organization of public surface, internals, and helpers
- encapsulation without hiding important design facts
- small classes or modules
- Single Responsibility Principle
- cohesion among fields and methods
- splitting classes when cohesion drops
- organizing for change
- isolating from change through narrow dependencies

Agent questions:

- Why would this class or module change?
- Do its methods use the same state and concepts?
- Is it a real domain role or a vague manager bucket?
- Is it easy to test without unrelated collaborators?

## Chapter 11: Systems

Core agent lesson: construction, wiring, runtime policy, and domain behavior should not be tangled.

Cover these concerns:

- separate system construction from system use
- keep main/wiring code distinct from domain logic
- use factories and dependency injection only when they clarify construction
- scale architecture incrementally rather than upfront
- isolate cross-cutting concerns
- test-drive architecture decisions where possible
- make decisions at the last responsible moment
- use standards only when they add demonstrable value
- build domain-specific language where it makes repeated intent clearer

Agent questions:

- Is wiring mixed into business behavior?
- Is the abstraction justified by real construction complexity?
- Does this framework feature buy clarity or only ceremony?

## Chapter 12: Emergence

Core agent lesson: clean design emerges through four simple rules applied in strict priority order.

Cover these concerns, in order of importance:

1. runs all tests — correctness outranks every aesthetic concern
2. contains no duplication — one authoritative home per piece of knowledge
3. expresses the intent of the programmer — a reader can tell what and why
4. minimizes classes, methods, and moving parts — subject to the first three

Use the order as a tie-breaker: never remove duplication in a way that breaks tests, and never add elements that rules 1-3 do not require.

Agent questions:

- Are tests strong enough to allow cleanup?
- What duplication represents shared knowledge rather than accidental similarity?
- Can I remove a construct without losing clarity or behavior?

## Chapter 13: Concurrency

Core agent lesson: concurrency creates correctness risks that require explicit ownership, data scope, lifecycle, and testing.

Cover these concerns:

- myths that concurrency is simple or only a performance concern
- separating concurrency policy from business logic
- limiting shared data scope
- using copies or immutable data when useful
- keeping threads/tasks independent when possible
- knowing library concurrency primitives
- the named execution models: **Producer-Consumer**, **Readers-Writers**, **Dining Philosophers**
- avoiding dependencies between synchronized methods
- keeping critical sections small
- designing shutdown carefully
- treating sporadic failures as possible concurrency bugs, never as noise to retry away
- testing with stress, instrumentation, different platforms, and varied schedules

Full detail, including the seven distinct tactics for actually catching a race, is in
`concurrency.md`.

Agent questions:

- Who owns this state?
- What can run at the same time?
- How does cancellation or shutdown complete safely?
- Can retries or duplicate events corrupt data?

## Chapter 14: Successive Refinement

Core agent lesson: good code is often produced by making a rough version work, then refining in small verified steps.

Apply this as:

- Start with a simple passing implementation.
- Stop when code starts resisting change and clean it immediately.
- Refine incrementally, not by giant rewrite.
- Keep tests green through each refinement.
- Add argument or input variants one at a time with tests.

Agent questions:

- Am I attempting the final architecture before the behavior is proven?
- Can this refactor be split into smaller green steps?
- Did I preserve the tests that let refinement continue safely?

## Chapter 15: JUnit Internals

Core agent lesson: code written by experts, already working and already respected, still carries
obvious debt — and the cleanup is unglamorous rename-and-extract work, not redesign.

The case study cleans a string-comparison class, and the specific defects it finds are the ones that
recur everywhere:

- **Redundant member prefixes.** Every field carrying the same prefix means the prefix belongs to the
  class, not the fields. Drop it.
- **Names that do not say what the value is.** Encoded or abbreviated member names get renamed to the
  concept they hold, and the code becomes readable without comment.
- **Hidden temporal coupling through member variables.** Methods that must run in a particular order
  because each leaves state behind for the next. Make the sequence explicit — pass values, or return
  them — so the order cannot be got wrong silently.
- **Negative conditionals and unclear boundary checks** rewritten positively, which is where the
  remaining edge-case bugs become visible.
- **Functions that do slightly more than their name admits**, split until each does one thing.

Apply this beyond the case study as:

- Expect to clean working code you did not write, without changing what it does.
- Rename first: most structural problems become obvious once the names are honest.
- Treat "these methods must be called in this order" as a defect to be designed away.
- Keep test and framework infrastructure to the same standard as production code — it is read more
  often.

Agent questions:

- Do these fields share a prefix that belongs to the type instead?
- Does any method depend on state a previous call left behind?
- Would users of this internal API understand a failure it reports?

## Chapter 16: Refactoring SerialDate

Core agent lesson: legacy code cleanup should first protect behavior, then improve names, structure, tests, and responsibility.

Apply this as:

- First make behavior observable with tests or characterization checks.
- Then make names accurate and domain-specific.
- Remove misleading comments and dead code only when covered or clearly unused.
- Move misplaced constants, calculations, or responsibilities to clearer homes.
- Keep refactor steps small enough to review.

Agent questions:

- Do I know current behavior before changing it?
- Is this rename behavior-preserving?
- Am I cleaning legacy code or silently changing its contract?

## Chapter 17: Smells And Heuristics

Core agent lesson: smells are review prompts, not automatic rewrite permission.

Use these groups as a review scan. The IDs follow the standard clean-code heuristic numbering so findings can cite a stable code (for example "G17 misplaced responsibility" or "N7 name hides side effects").

### Comment Smells (C)

- C1: comment carries background that belongs elsewhere (tickets, history, metadata)
- C2: obsolete comment that no longer matches the code
- C3: redundant comment that restates the code
- C4: sloppy or unclear comment
- C5: commented-out code

### Environment Smells (E)

- E1: build requires more than one step
- E2: tests require more than one step

### Function Smells (F)

- F1: too many arguments
- F2: output arguments that mutate parameters
- F3: flag arguments selecting behaviors
- F4: dead, never-called functions

### General Smells (G)

- G1: mixed languages or paradigms in one file without need
- G2: obvious expected behavior left unimplemented
- G3: incorrect behavior at boundaries and edge cases
- G4: disabled or overridden safeguards (ignored warnings, skipped tests, silenced linters)
- G5: duplication of knowledge
- G6: code at the wrong abstraction level
- G7: base classes depending on their derivatives — a base class naming or reaching into a subclass. (Broader layering violations are architectural; see the structural smells in `smell-triage.md`, not G7.)
- G8: too much exposed information; wide interfaces
- G9: dead code
- G10: poor vertical separation; related code far apart
- G11: inconsistency; same idea done different ways
- G12: clutter that earns no keep
- G13: artificial coupling between things that do not belong together
- G14: feature envy; code operating on another module's internals
- G15: selector arguments that switch behavior
- G16: obscured intent
- G17: misplaced responsibility; code living where it does not belong
- G18: inappropriate static/global behavior
- G19: missing explanatory variables
- G20: function names that do not say what the function does
- G21: algorithm not understood before changing it
- G22: logical dependency not represented physically
- G23: repeated conditionals that want a single dispatch structure (polymorphism, handler map)
- G24: ignored standard conventions
- G25: magic values without domain names
- G26: imprecision in assumptions, types, or comparisons (money in floats, naive time math)
- G27: relying on convention where explicit structure is needed
- G28: unencapsulated complex conditionals
- G29: negative conditionals where positive ones read clearer
- G30: functions doing more than one thing
- G31: hidden temporal coupling
- G32: arbitrary, unjustified structural choices
- G33: boundary conditions not encapsulated in one place
- G34: functions descending more than one abstraction level
- G35: configurable data buried at low levels instead of the top
- G36: transitive navigation through object graphs (train wrecks)

### Language-Specific Smells (J and equivalents)

The source numbers these J1-J3 for Java. Two generalize to any language and keep their IDs:

- J2: do not inherit constants. Pulling constants in through a base type or interface hides where
  they come from; name the source explicitly instead.
- J3: prefer typed enumerations over bare integer or string constants. An enum carries meaning,
  exhaustiveness, and a compiler check; a loose constant carries none.

J1 (avoid long import lists by using wildcards) is genuinely Java-specific and is **intentionally
omitted** so the numbering stays auditable — the local formatter and linter own import style.

Also, whatever the language: never translate another language's idiom in literally. Apply the
principle, not the syntax.

### Naming Smells (N)

- N1: non-descriptive names
- N2: names at the wrong abstraction level
- N3: missing standard nomenclature the team or ecosystem already uses
- N4: ambiguous names
- N5: short names for long scopes, long names for short scopes inverted
- N6: unnecessary encodings and prefixes
- N7: names that hide side effects

### Test Smells (T)

- T1: insufficient tests; untested reachable behavior
- T2: no coverage signal where coverage would reveal gaps
- T3: skipped trivial tests that would document behavior
- T4: ignored tests that encode unresolved ambiguity
- T5: missing boundary tests
- T6: no extra coverage near recent bugs
- T7: failure patterns not investigated
- T8: coverage patterns not inspected
- T9: slow tests that discourage frequent runs

Agent questions:

- Is this smell in the scope of the requested task?
- Does it create immediate risk?
- Did my change introduce it?
- Can I fix it safely with current tests?

## Appendix A: Concurrency II

Core agent lesson: concurrency correctness depends on execution paths, library guarantees, lock strategy, throughput tradeoffs, deadlock prevention, and testing tools.

Cover these concerns:

- client/server threading tradeoffs
- number of possible execution paths
- library support such as executors, nonblocking solutions, and thread-safe collections
- non-thread-safe classes
- dependencies between methods that break under parallel calls
- client-side vs server-side locking tradeoffs
- throughput calculations and bottlenecks
- deadlock conditions: mutual exclusion, hold-and-wait, no preemption, circular wait
- strategies for breaking deadlock conditions
- tools and instrumentation for forcing timing failures

Agent questions:

- Can two valid calls interleave into invalid state?
- Which component owns locking?
- What throughput gain justifies the added correctness risk?
- How can tests force the rare interleaving?

## Appendix B: SerialDate Source

Core agent lesson: before abstracting a rule, read real code. Preserve public behavior unless the
task explicitly changes it, and make date, time, calendar, locale, and boundary assumptions
explicit.

## Appendix C: Cross References Of Heuristics

Core agent lesson: findings are interconnected. One root cause surfaces as several smells, so fixing
the symptom you noticed first often leaves the cause in place — or trades one smell for another.

Use this table when a finding is confirmed: check the related IDs before deciding what to fix, and
report the root cause rather than the symptom.

| You found | Also check | Because the shared root cause is usually |
| --- | --- | --- |
| G30 function does more than one thing | G34, F1, F3, G16, N1 | one function absorbing several responsibilities, which then needs more arguments and a vaguer name |
| F1 too many arguments | G30, G20, N1, primitive obsession | a missing concept: the arguments are an unnamed object |
| G5 duplication of knowledge | G23, G11, G6, N3 | one rule with no authoritative home, so each site reimplements it slightly differently |
| G23 repeated conditionals | G5, G6, G13, N3 | a missing dispatch point or a missing type |
| G17 misplaced responsibility | G6, G14, G22, G13 | a boundary that was never drawn, so behavior settled where it was convenient |
| G14 feature envy | G17, G36, G8 | data and the behavior that belongs to it living in different modules |
| G36 train wreck | G14, G8, Law of Demeter | a caller navigating structure instead of asking for a decision |
| G8 too much exposed information | G36, G14, ISP | a wide public surface leaking internals as transitive dependencies |
| C1-C5 comment smells | G16, N1, G30 | a comment compensating for code that should have been clearer or smaller |
| C5 commented-out code | G9 dead code | uncertainty preserved instead of resolved; version control already keeps it |
| N1 non-descriptive name | G16, G20, G30 | the unit's job is unclear, so no name fits it |
| N7 name hides side effects | G31, command-query separation | a function both answering and changing |
| T1 insufficient tests | T5, T6, G3, G33 | untested boundaries, which is exactly where G3 defects live |
| T5 missing boundary tests | G3, G26, G33 | boundary conditions never encapsulated in one place |
| T9 slow tests | E2, T1 | tests coupled to infrastructure, so they run rarely and coverage decays |
| E1/E2 multi-step build or test | T9, T1 | friction that suppresses the feedback loop the other rules depend on |
| G31 hidden temporal coupling | N7, G18, G22 | order-dependent state that the API does not express |
| G18 inappropriate static or global | G31, T1 | shared mutable state, which also makes tests order-dependent |
| G25 magic value | N1, G26, G35 | a domain concept with no name and no home |
| G35 buried configuration | G25, G6 | a tunable value decided at the wrong level |
| G9 dead code | F4, C5, G12 | a change that orphaned code nobody deleted |

## Coverage Pressure Scenarios

Use these scenarios to test whether an agent applies the full map:

| Scenario | Must Consult |
| --- | --- |
| Rename a confusing API | Meaningful Names, Comments, Tests, Smells |
| Split a large service | Functions, Classes, Systems, Emergence, Smells |
| Wrap a vendor SDK | Boundaries, Error Handling, Tests, Systems |
| Refactor legacy date logic | Successive Refinement, SerialDate, Tests, Names |
| Fix flaky parallel job | Concurrency, Appendix A, Error Handling, Tests |
| Review a large PR | Chapters 2-13 plus Chapter 17 smell groups |
