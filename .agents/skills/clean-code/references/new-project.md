# New Project Protocol

Starting a project, or a new major module inside one. The goal is not to build the grandest possible
structure — it is to make the first correct decisions cheap and the later ones possible.

The governing idea: **a good architect maximizes the number of decisions not made.** Everything below
is about deferring what can be deferred while keeping the domain independent of what you defer.

## Phase 0 — Understand before designing

**1. Clarify the requirements.** What must the system do, for whom, and what makes it valuable? Ask
about the two or three requirements most likely to change, because those decide where the boundaries
go.

**2. Define the scope.** What is explicitly *not* in version one. Write it down; it is the main
defence against speculative structure.

**3. Identify the actors.** Which groups of people can demand a change — finance, operations,
compliance, the end user, another team? Code answering to different actors belongs in different
modules. This single question prevents the most expensive class of later rework.

**4. Name the domain vocabulary.** Agree the terms for the core concepts now and use them everywhere:
in types, files, directories, and tests. One word per concept, one concept per word.

Ask the user for anything above that you cannot infer. Guessing the domain is far more damaging than
asking.

## Phase 1 — Design the shape

**5. Design the architecture before the code.** Decide the levels: what is policy, what is detail.
Business rules are highest level; the database, web, UI, framework, and delivery mechanism are
details.

**6. Define the domain model.** The Critical Business Rules and Critical Business Data — the things
that would exist even if the work were done on paper. These become the innermost layer and depend on
nothing.

**7. Define module boundaries.** Draw them where the axes of change are, one boundary per axis. Give
each component one public entry point.

**8. Define the dependency rules explicitly.** Write them into `.clean/architecture.md` using the
template in `assets/templates/architecture.md`, innermost layer first. This file is the project's
constitution: it is what later sessions read, and what `scripts/check_boundaries.py` enforces.

**9. Choose the decoupling mode deliberately.** Start at source level — components in one address
space, communicating by function calls. Structure it so a service *could* be extracted later, then
do not extract one until something forces it. Keep the move reversible in both directions.

**10. Create the project structure.** Top-level directories named for the domain and its use cases,
not for the framework or for technical layers. A newcomer reading the directory listing should learn
what the system is *for*.

## Phase 2 — Set the standards

**11. Establish coding standards by choosing tools, not writing prose.** A formatter, a linter, an
`.editorconfig`. Let the tools own formatting so no human or agent argues about it.

**12. Design for testability from the first commit.** Business rules must be testable with no
database, no web server, no UI, no external service. If that is not true on day one, it never becomes
true. Split hard-to-test behavior from easy-to-test behavior: keep the untestable half humble, with
no decisions in it.

**13. Automate the quality checks.** A test command, the linter, and — once layers are declared — a
dependency-direction check, all runnable with one command and wired into CI. Add the pre-commit hook
from `assets/hooks/` if the team wants enforcement locally.

**14. Set up the memory files.** Create `.clean/` from `assets/templates/`: `architecture.md`,
`decisions.md`, and a `context.json` from `scripts/detect_stack.py --write` — or hand-write the same
facts, since you are the one who just chose them. Record the Phase 0 and Phase 1 decisions in
`decisions.md` while the reasoning is still fresh.

## Phase 3 — Build

**15. Implement vertical slices.** One complete use case end to end, through every layer, before
starting the next. A slice proves the architecture; a finished layer proves nothing.

**16. Keep abstractions minimal.** Add an interface when there is a second implementation or a real
boundary to protect, not in anticipation of one. An abstraction with a single implementation and no
boundary is a cost with no benefit.

**17. Prefer simplicity, and resist the three temptations.** No premature optimization: measure
first. No premature generalization: build for the requirement in front of you. No premature
distribution: a network boundary is not a design.

**18. Keep the domain pure.** No framework annotations, no ORM base classes, no HTTP types in the
domain. When a framework wants inside, wrap it in a proxy at the edge instead.

**19. Confine wiring to `main`.** Configuration reading, dependency injection, and framework binding
happen in one dirty low-level component that nothing else depends on. Prefer a separate `main` per
environment over configuration branches inside policy code.

**20. Review architectural consistency, then scale only when needed.** At each milestone, check that
dependencies still point inward, that no cycle has appeared, and that the structure still screams the
domain. Add a boundary, a service, or a cache when a measured need arrives — not before.

## What "done" means for version one

- A newcomer can tell from the directory names what the system does.
- The business rules can be tested with no infrastructure running.
- Every source dependency points inward, and the dependency check passes.
- One command runs the tests; one command runs the linter.
- `.clean/architecture.md` and `.clean/decisions.md` exist and are accurate.
- Nothing has been built for a requirement that does not exist yet.

## Anti-patterns specific to greenfield work

| Temptation | Why it costs |
| --- | --- |
| Scaffolding every layer before any feature works | You have proven nothing and now must maintain it all |
| Choosing the database and ORM first | The most deferrable decision, made at the moment you know least |
| Micro-services from day one | Expensive, coarse-grained, and hard to reverse; development time is the scarce resource, not CPU |
| A `utils` or `common` module in the first commit | It becomes the place where design goes to die |
| Generic `BaseEntity` / `BaseService` / `AbstractManager` classes | Inheritance is the most rigid dependency; you are committing before you know the shape |
| Copying a reference architecture wholesale | Structure without the reasoning behind it cannot be maintained or adapted |
| Configuration systems, plugin points, and feature flags before the second case exists | Speculative flexibility that ossifies into required complexity |
