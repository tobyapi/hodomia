# Canon

Every named rule this skill draws on, what it means operationally, and where the detail lives. Use it
two ways: to find the right rule when you know only its name, and to cite a finding precisely — a
review that says "G30, and the arity is polyadic" is checkable in a way that "this function is messy"
is not.

Names are the established vocabulary of the field. The operational readings are this project's.

## Code level

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **Boy Scout Rule** | Leave code cleaner than you found it. **This skill narrows it deliberately**: clean the lines your task already touches, report the rest | `chapter-map.md` Ch1 |
| **LeBlanc's law** | Later equals never. A deferred cleanup is a cancelled one | `chapter-map.md` Ch1 |
| **Intention-revealing names** | The name answers why the thing exists, not what type it is | `principles.md` |
| **Avoid mental mapping** | The reader should not have to translate a terse name into the concept | `principles.md` |
| **One word per concept** | One term per idea across the codebase, and never one term for two ideas | `principles.md` |
| **Verbs and keywords** | Encode argument order and meaning into the name: `assertExpectedEqualsActual` | `principles.md` |
| **Do One Thing** | A function does one thing at one level of abstraction. A function-level rule — *not* the SRP | `principles.md` |
| **The Stepdown Rule** | The file reads top-down: callers above callees, each level one step more detailed | `principles.md` |
| **Function arity** | Niladic → monadic → dyadic → triadic → polyadic. Three arguments needs special justification; more needs an object | `principles.md` |
| **Flag argument** | A boolean parameter means the function does two things. Split it | `principles.md` |
| **Output argument** | A parameter mutated as a return channel. Return a value instead | `principles.md` |
| **Command Query Separation** | Answer a question or change state, never both | `principles.md` |
| **DRY** | One authoritative home per piece of knowledge — but only for *true* duplication | `principles.md`, `architecture.md` |
| **Newspaper metaphor** | The file opens with high-level intent; detail descends below it | `principles.md` |
| **Vertical distance** | Related things stay close: declarations near use, caller near callee | `principles.md` |
| **Conceptual affinity** | Code that reads as one idea belongs together, even with no call between | `principles.md` |
| **Dummy scope** | An empty body hidden behind a semicolon. Make it visible or remove it | `principles.md` |
| **Data/object anti-symmetry** | Objects hide data and expose behavior; data structures do the reverse. Code treating one as the other is the defect | `principles.md` |
| **Law of Demeter** | Ask a collaborator for a decision; do not navigate its internals | `principles.md` |
| **Train wreck** | `a.b().c().d()` — coupling to every link in the chain (smell G36) | `principles.md` |
| **Hybrid** | A type exposing fields while pretending to protect invariants. Pick one | `chapter-map.md` Ch6 |
| **DTO** | A structure for transport, with no behavior implied | `chapter-map.md` Ch6 |
| **Special Case pattern** | Model an expected alternate outcome as a value or object, not an exception | `principles.md` |
| **Checked vs unchecked exceptions** | Prefer unchecked: a checked exception forces every intermediate signature to change, which breaks encapsulation along the whole call chain | `principles.md` |
| **Dependency magnet** | A shared error enum or constant class that every user must recompile against. Prefer distinct exception types | `principles.md` |
| **Learning test** | A small test written to probe an unfamiliar library, which then catches breaking upgrades | `principles.md` |
| **Three Laws of TDD** | No production code before a failing test; no more test than fails; no more code than passes | `tests.md` |
| **F.I.R.S.T.** | Fast, Independent, Repeatable, Self-validating, Timely | `tests.md` |
| **BUILD-OPERATE-CHECK** | The three visible parts of a readable test | `tests.md` |
| **Single concept per test** | One idea per test; minimize asserts rather than obeying a hard one-assert rule | `tests.md` |
| **Domain-specific testing language** | Helpers refactored into existence so a test reads as the behavior it describes | `tests.md` |
| **Dual standard** | Tests may trade efficiency for clarity, never clarity for cleverness | `tests.md` |
| **Structural test coupling** | A test class per production class. Makes tests fragile and production code rigid | `tests.md` |
| **Four rules of simple design** | In order: all tests pass; no duplication; expresses intent; fewest elements | `principles.md` |
| **Successive refinement** | Make it work, then make it right, in small verified steps — not a giant rewrite | `chapter-map.md` Ch14 |

## Concurrency

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **Producer-Consumer** | Bounded queue between producers and consumers; failures are lost signals and unbounded blocking | `concurrency.md` |
| **Readers-Writers** | Many readers, few writers; decide deliberately which side may starve | `concurrency.md` |
| **Dining Philosophers** | Competition for several shared resources; failures are deadlock, livelock, starvation. Fix with resource ordering | `concurrency.md` |
| **The four deadlock conditions** | Mutual exclusion, hold-and-wait, no preemption, circular wait — break any one | `concurrency.md` |
| **Segregation of mutability** | Push work into immutable components; confine mutation to few named places | `concurrency.md`, `architecture.md` |
| **Client-side vs server-side locking** | Where the atomic sequence is enforced. Choose it; do not stumble into it | `concurrency.md` |

## Architecture level

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **The Dependency Rule** | Source dependencies point only inward, toward higher-level policy. Inner code never names anything outer | `architecture.md` |
| **Level** | Distance from the inputs and outputs — not call order | `architecture.md` |
| **SRP** | A module is responsible to one, and only one, **actor**. Not "does one thing" | `architecture.md` |
| **OCP** | Open for extension, closed for modification. To protect A from B, make B depend on A | `architecture.md` |
| **LSP** | A subtype is usable wherever the base is. A call site that must know the implementation is the violation | `architecture.md` |
| **ISP** | Do not depend on things you do not use; transitive baggage sets your recompile and failure radius | `architecture.md` |
| **DIP** | Depend on abstractions. The test is **volatility**, not abstractness | `architecture.md` |
| **REP** | The granule of reuse is the granule of release | `architecture.md` |
| **CCP** | Gather what changes for the same reasons at the same times. SRP for components | `architecture.md` |
| **CRP** | Do not force users to depend on what they do not need. ISP for components | `architecture.md` |
| **ADP** | No cycles in the component dependency graph | `architecture.md` |
| **SDP** | Depend in the direction of stability. `I` decreases along dependencies | `architecture.md` |
| **SAP** | A component should be as abstract as it is stable | `architecture.md` |
| **Instability `I`** | `Fan-out / (Fan-in + Fan-out)`; 0 is maximally stable | `architecture.md` |
| **Abstractness `A`** | Abstract types / total types in a component | `architecture.md` |
| **Main Sequence, distance `D`** | `D = \|A + I - 1\|`; investigate above ~0.1 | `architecture.md` |
| **Zone of Pain / Uselessness** | Stable-and-concrete; abstract-with-no-dependents | `architecture.md` |
| **Entity** | Critical business rules and data that would exist without any software | `architecture.md` |
| **Use case** | Application-specific rules orchestrating entities. Depends on entities; never the reverse | `architecture.md` |
| **Humble Object** | Split hard-to-test from easy-to-test; the humble half holds no decisions | `architecture.md` |
| **Screaming architecture** | The top-level structure names the domain, not the framework | `architecture.md` |
| **Main as the ultimate detail** | All wiring and configuration in the dirtiest, lowest-level component | `architecture.md` |
| **Asymmetric marriage** | You commit to a framework; it commits nothing to you. Use it, do not marry it | `architecture.md` |
| **Partial boundary** | Skip-the-last-step, one-dimensional, or facade — each with its own failure mode | `architecture.md` |
| **Decoupling modes** | Source, deployment, service. Stay in one address space as long as possible, reversibly | `architecture.md` |
| **The decoupling fallacy** | A process boundary does not decouple what shares a data record | `architecture.md` |
| **True vs accidental duplication** | True: must always change together. Accidental: changes at different rates for different reasons | `architecture.md` |
| **Organization vs encapsulation** | If every type is public, packages are folders and no architecture is enforced | `architecture.md` |
| **Cross-cutting concern** | A policy that spans modules; isolate it rather than scattering it | `architecture.md` |

## Smell IDs

Cite these directly in findings. Full catalogue and the cross-reference table are in
`chapter-map.md`; the usual response for each is in `smell-triage.md`.

| Group | Range | Covers |
| --- | --- | --- |
| **C** | C1-C5 | Comments |
| **E** | E1-E2 | Environment: multi-step build or test |
| **F** | F1-F4 | Functions: arguments, output args, flags, dead functions |
| **G** | G1-G36 | General — the largest group |
| **J** | J2-J3 | Language-specific that generalize (J1 intentionally omitted) |
| **N** | N1-N7 | Naming |
| **T** | T1-T9 | Tests |
