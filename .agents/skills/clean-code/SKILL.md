---
name: clean-code
description: Use when writing, editing, reviewing, testing, or refactoring code in any language or framework; when creating files or deciding where code belongs; when designing or changing module boundaries, layers, and dependencies; when starting a new project; or when auditing or cleaning up an existing one. Covers naming, functions, comments, error handling, tests, concurrency, security, code placement, single responsibility, code smells, SOLID, the dependency rule, component boundaries, layering, testability, architectural drift, and verified surgical or whole-project refactoring.
license: MIT
compatibility: Works with no tooling. Optional scripts in scripts/ need Python 3.8+ and read-only filesystem access; they write only to .clean/ and never use the network.
metadata:
  version: "3.0.0"
---

# Clean Code And Clean Architecture

Clean code makes intent, behavior, boundaries, and failure modes easy for the next maintainer to
understand and safely change. Clean architecture keeps the cost of a change proportional to its
scope instead of its shape.

Written for AI coding agents of any vendor, and language-agnostic: adapt every rule to the project's
language, framework, runtime, and local style. Three agent-specific truths shape everything below:

1. You read faster than humans but forget context between sessions. Structure, names, placement,
   and written-down decisions are how your work survives you.
2. Your most common failures are not syntax errors. They are code in the wrong place, duplicated
   knowledge, mixed responsibilities, invented APIs, and unverified claims of success.
3. You are prone to a specific architectural failure: wiring the shortest path between two points.
   That is how a controller ends up calling a repository directly and skipping the only
   authorization check in the system.

## When To Use

Any coding work in any language: features, fixes, refactors, tests, reviews, scripts, SQL,
infrastructure as code, UI, services, libraries. Specifically whenever you are about to create a
file or directory, add behavior to an existing unit, decide where logic belongs, add a dependency,
cross a boundary, introduce a layer, start a project, or clean one up.

Use a lighter touch for trivial edits, but still avoid unrelated changes.

## Start Here: Load Project Context

You may have no memory of this project. Recover what you need from disk before deciding anything.

1. Read `.clean/context.json` if it exists: language, frameworks, test command, layout.
   If it is missing or stale, run `scripts/detect_stack.py --write`, or answer its questions by
   inspection.
2. Read `.clean/architecture.md` if it exists: the declared layers and which dependencies are
   allowed. This is the project's intended design, and it overrides your instincts.
3. Read `.clean/decisions.md` and `.clean/ledger.md` if they exist: past decisions and any cleanup
   campaign already in progress. Never re-litigate a recorded decision; never restart a campaign
   that is mid-flight.
4. Read the project's own instructions — `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`,
   `ARCHITECTURE.md`, `README.md`. Project instructions outrank this skill.

If none of these exist, work from the code itself and offer to create them at the end. See
`references/memory-protocol.md`.

## Operating Loop

### 1. Frame The Change

Before editing, identify the exact behavior or maintainability problem being solved, the assumptions
that could change the implementation, the smallest useful scope, and the verification that will
prove the change.

Ask a question only when ambiguity changes the implementation. Otherwise state the assumption and
proceed.

### 2. Read Local Context

Inspect the surrounding project before changing it: naming vocabulary and casing, directory layout,
module and file boundaries, how files are registered or wired, error-handling style, test style,
framework idioms — and whether the logic you are about to write already exists.

Search before you write. Local consistency beats generic preference.

### 3. Put Code In Its Place

Decide where the change belongs before writing it, at both scales: which unit owns this
responsibility (see "Where Code Lives" and "One Job Per Unit"), and which side of which boundary it
sits on (see "Architecture Rules"). Prefer extending the existing owner of a concern over creating
a new home for it.

### 4. Change The Smallest Slice

Every changed line should trace to the request or to cleanup caused by the request.

Do: keep the diff narrow and reviewable; prefer targeted edits over regenerating whole files;
remove imports, variables, functions, or files your change made unused; leave the lines you touched
slightly cleaner than you found them without widening the diff; mention unrelated smells instead of
fixing them silently.

Do not: rewrite a module because it could be cleaner; add layers, factories, managers, config
systems, caches, queues, or plugin points unless required; change public behavior without tests or
an explicit reason; mix refactoring and behavior change in one step when separating them is safer;
defer trivial in-scope cleanup with a TODO.

### 5. Verify The Claim

Match verification to risk: a focused unit test or direct command for a small pure function; a
reproducer test first for a bug fix; tests before and after for a refactor; an integration or
contract check for an API or boundary change; a component or browser check for UI; a deterministic
race-focused test for concurrency.

If verification cannot be run, say exactly what was not run and what risk remains. Never claim
success from memory of what the code should do.

### 6. Review The Diff

Scan for unrelated edits and speculative abstractions; files created in the wrong place or
duplicating existing ones; units that now do more than one job; dependencies that now point the
wrong way; unclear names; comments compensating for confusing code; swallowed errors; hidden shared
state; missing edge-case tests; new code nothing references or wiring never completed.

## Where Code Lives

Misplaced files and misplaced logic are among the most common agent failures. Placement is a design
decision, not an afterthought.

### Placement Procedure

1. Find two or three existing artifacts most similar to what you are adding.
2. Mirror their directory, file naming pattern, internal structure, and registration.
3. Create a new file only when no cohesive home exists — a file is cohesive when its contents change
   for the same reason.
4. Wire the file in completely: imports, exports, barrel or index files, module lists, route tables,
   DI registration, build config, migrations. An unreferenced file is dead code, not a feature.
5. If two homes are plausible, choose the one closest to the code that uses it, and say why.

### Placement Rules

- Resolve paths from the project root and its source layout, never from whatever directory happens
  to be current. Confirm the target directory matches the project's convention before creating it.
- Never default to the repository root. Root-level files are for project-wide concerns only.
- Put tests where the project keeps tests, mirroring its convention.
- Place logic by responsibility, not by convenience: domain rules do not go in controllers, views,
  route handlers, or scripts; I/O does not go in pure domain modules; UI state does not go in data
  access code.
- Do not grow junk drawers. Adding to `utils`, `helpers`, `common`, or `misc` requires the same
  justification as creating a new module: name the domain concept instead.
- Never create sibling variants of an existing file: no `_v2`, `_new`, `_final`, `_enhanced`,
  `_improved`, `_copy`, or date-suffixed names. Improve the original; version control keeps history.
- Scratch files, experiments, and one-off scripts go outside the project tree, or are deleted before
  completion. Leave no debug output or abandoned drafts in the repo.
- Default to the narrowest access modifier the language offers. Every public type is a potential
  inbound dependency, and a package whose types are all public is a folder, not a boundary.

## One Job Per Unit

Mixed responsibility is the smell agents produce most. Enforce it at every scale: function, class,
module, file, directory, service.

**The one-sentence test.** Describe the unit's job in one sentence without "and", "also", or "then".
If you cannot, it has more than one job.

**Kinds of responsibility** that belong in distinct units, however the project separates them:
parsing and input validation; domain decisions and business rules; persistence and data access;
calls to external systems; presentation and formatting; orchestration; logging and metrics;
construction and wiring. An orchestrator may sequence several concerns, but then it contains no
business rules of its own.

- New behavior goes to the unit that owns that responsibility, not the file you happen to be
  editing. Resist nearest-file gravity: code landing "where the cursor is" is how god files grow.
- If a requirement changes a unit's one-sentence job, extract a collaborator instead of inflating it.
- Keep construction separate from use: wiring, config reading, and object-graph assembly stay out of
  business logic.
- Dependency check: a module importing the web framework, the database driver, and the mailer at
  once is probably doing all three jobs.
- Test-pain check: needing to mock three unrelated systems to test one function means the function
  mixes concerns.
- At module scale, ask *which actor can demand this change*. Code answering to different actors
  belongs in different modules, even when it looks identical today. See SRP in
  `references/architecture.md`.

## Architecture Rules

Read `references/architecture.md` before any task that adds a dependency, crosses or creates a
boundary, introduces a layer, or adopts a framework or database. The essentials:

**The Dependency Rule — source code dependencies must point only inward, toward higher-level
policies.** Nothing in an inner circle may know anything about an outer circle: not a class, a
function, a variable, an annotation, or a data format. Before every dependency ask: which direction
does this line cross, and why?

- **Level is distance from the inputs and outputs**, not call order. Business rules are highest
  level; the database, web, UI, framework, and delivery mechanism are details.
- **Policy must not name a detail.** When policy needs something from a detail, declare the
  interface on the policy side and implement it outside. This is how control flow and source
  dependency legitimately run in opposite directions.
- **Confine details to their layer.** All SQL lives in the data-access layer. Rows, result sets,
  ORM types, and framework request or response objects never travel inward. Pass simple structures
  shaped for the inner side, and copy the fields even when they overlap.
- **Frameworks are details, not architecture.** Never derive a business object from a framework base
  class or annotate one; use a proxy in an outer layer. Confine dependency-injection wiring to
  `main`, the dirtiest and lowest-level component.
- **Keep the component graph acyclic.** A cycle fuses components into one release unit. Break it by
  inverting a dependency or extracting a shared component.
- **Depend in the direction of stability**, and make stable things abstract.
- **Split hard-to-test from easy-to-test** rather than harnessing untestable code. The untestable
  half should be humble: no decisions in it. That split is usually where the real boundary is.
- **Deduplicate only true duplication** — copies that must always change together. Copies that
  change at different rates for different reasons are not duplicates, and merging them is hard to
  undo.
- **Do not add a boundary you cannot justify now**, and do not assume a partial boundary maintains
  itself. Prefer compile-time enforcement over discipline.

If the project declares layers in `.clean/architecture.md`, that declaration wins. Check compliance
with `scripts/check_boundaries.py`, or by reading the imports of every file you changed and asking
which layer each one names.

## Code Principles

Summary only. Full detail in `references/principles.md`.

- **Names** reveal intent in domain vocabulary, disclose side effects, and use one word per concept.
- **Functions** do one thing at one level of abstraction; prefer early exits, few parameters, and
  command-query separation over flags and nested conditionals.
- **Comments** explain why, never what or how, and never address the reviewer.
- **Formatting** follows the project's formatter; never hand-format against it.
- **Data and objects** are opposites: objects hide data and expose behavior, data structures do the
  reverse. Keep public surfaces smaller than internals; be exact with money, time, and units.
- **Errors** are designed with the happy path: handle where a decision can be made, preserve causes,
  model expected outcomes as values, never swallow.
- **Boundaries** get validation, an interface you own, and explicit serialization and nullability.
- **Tests** follow the Three Laws of TDD and F.I.R.S.T.: written first, behavior-focused,
  deterministic, asserting outcomes not structure. Never weaken or skip a failing test to get green.
- **Concurrency** makes ownership and ordering visible; prefer immutability and confine mutation.
- **Security** validates at boundaries, keeps authorization next to the protected operation, and
  keeps secrets out of code and logs.
- **Performance** is measured before it is optimized.
- **When rules conflict**, decide in this order: tests pass; no duplicated knowledge (**DRY**, and
  only for true duplication); intent is expressed; fewest elements.

## Workflows

Four named workflows. Follow the matching file rather than improvising; each one works with no
tooling at all.

| Workflow | Use when | Follow |
| --- | --- | --- |
| **Session** | default for any coding task in an existing project | this file, plus `references/session-protocol.md` for the full loop and handoff |
| **Onboard** | asked to assess, clean up, or refactor an existing project | `references/project-refactor.md` |
| **Bootstrap** | starting a new project or a new major module | `references/new-project.md` |
| **Audit** | asked for a report, review, or health check without changing code | `references/audit-report.md` |

## Tools

Optional accelerators in `scripts/`, standard-library Python only, no network. Where a workflow step
names a script it also names the manual equivalent, so do that instead when Python is unavailable or
your host blocks shell execution. Script output is evidence for your judgement, never a verdict.

| Script | Answers |
| --- | --- |
| `detect_stack.py` | what language, framework, test command, and layout is this? |
| `scan_repo.py` | where are the oversized files, sibling variants, junk drawers, debug output, skipped tests, and untested areas? |
| `check_boundaries.py` | does the code obey the declared dependency direction? |

## Scope Modes

**Surgical mode (default).** Everything above, applied to the smallest slice that solves the task.
Unrelated smells are reported, not fixed.

**Campaign mode (explicit request only).** When the user asks for a project-wide or module-wide
cleanup, the cleanup is the task — but it still needs structure or it degrades into an unreviewable
rewrite. Follow `references/project-refactor.md`. In short:

1. Inventory and baseline first: map the code, run the full verification suite, record what passes
   before touching anything.
2. Propose a prioritized plan batched by module or by smell; get agreement on order and depth.
3. Refactor in small verified batches — one module or one smell family at a time, behavior-
   preserving, tests green after each batch, one commit or checkpoint per batch.
4. Never mix behavior changes into a refactor batch; park discovered bugs in the ledger instead of
   silently fixing them.
5. Keep a written ledger of done, remaining, and found-but-deferred so progress survives context
   loss and session boundaries.
6. Stop and report rather than push through when the baseline is red, tests are missing for a risky
   area, or a batch balloons.

## Agent Failure Modes

The failure patterns most specific to AI-generated code. Check yourself against them before
completion.

| Failure | Counter-behavior |
| --- | --- |
| Invented API: calling functions, methods, options, or config keys that do not exist | Verify against the actual codebase, dependency versions, and lockfile — not memory |
| Reinvented helper: writing logic that already exists in the project or its libraries | Search for existing implementations before writing; extend rather than duplicate |
| Wrong-place file: new files at the repo root, in the current directory, or outside conventions | Follow the Placement Procedure; mirror similar artifacts |
| Sibling-variant file: `service_v2.py`, `utils_new.ts`, `final_component.tsx` | Edit the original; version control keeps history |
| Nearest-file gravity: logic added to whatever file was open, growing god files | Route behavior to the unit that owns the responsibility |
| Shortest-path wiring: injecting a repository into a controller because it is fewer steps | Go through the layer that owns the rule; the skipped layer may hold the only authorization check |
| Detail leaking inward: an ORM type, framework annotation, or HTTP object in a business rule | Keep the name of every outer-circle thing out of inner-circle code |
| Framework as architecture: structure named after the stack, business objects derived from framework classes | Name packages after the domain; wrap the framework at the edge |
| Regeneration loss: rewriting a whole file and silently dropping error handling, comments, or edge cases | Make targeted edits; when a rewrite is necessary, diff it against the original before finishing |
| Patch-without-understanding: changing code whose behavior you have not traced | Read callers, tests, and data flow first |
| Premature abstraction: a layer, boundary, or service introduced for a need nobody has yet | Leave the option open instead; build the boundary at the inflection point |
| Eager deduplication: merging two similar blocks owned by different actors or changing at different rates | Confirm it is true duplication first; accidental duplication is harder to unmerge than to leave |
| Placeholder as done: stubs, `pass`, "in a real implementation...", hardcoded demo values | Ship working code or state plainly what is unfinished |
| Test-blessing: weakening assertions or skipping tests until the suite passes | Fix the code or report the conflict; never bury the signal |
| Unwired artifact: a new file, route, or migration that nothing references | Complete registration and imports; prove reachability |
| Scope creep: drive-by renames, reformatting, dependency bumps | Trace every changed line back to the request |
| False completion: "this should work now" without running anything | Run the verification, quote the result, name what was not run |

## Smell Triage

When you see a smell, decide whether it is in scope before you touch it. Fix now only if it blocks
the requested change, creates immediate risk, or was introduced by your work. Otherwise mention it
separately. In campaign mode, log it in the ledger and handle it in its batch.

`references/smell-triage.md` lists every smell with its usual response and the order to fix them in.
Cite IDs from `references/chapter-map.md` (G17, N7, T5...) so findings stay unambiguous.

## Framework And Language Adaptation

Before applying a rule, adapt it to the ecosystem. Read `references/framework-map.md` when working
in an unfamiliar language or stack. Clean code should look idiomatic to a senior maintainer of that
stack, and the project's existing layout always overrides the ecosystem default.

Examples: in Go, small interfaces at consumers beat deep hierarchies. In Rust, encode invariants in
types and ownership rather than defensive runtime checks.

## Anti-Loopholes

Stop and reassess when you catch yourself thinking:

| Rationalization | Reality |
| --- | --- |
| "I will clean this up while I am here." | Unrelated work unless the task needs it; report it instead. |
| "A framework will make this cleaner." | A dependency is a cost, and a one-sided commitment; prove the need. |
| "This abstraction will help later." | Later requirements can pay for later abstraction. |
| "The code is bad, so a rewrite is cleaner." | Rewrites need explicit scope, tests, and migration risk control. The team that made the mess usually rebuilds it. |
| "There are no tests, so verification is impossible." | Use the best available check and report remaining risk. |
| "I will put it here for now." | "For now" placements become permanent. Place it correctly once. |
| "The user asked for cleanup, so everything is in scope." | Campaign mode has a protocol: baseline, batches, ledger, verification. |
| "Clean code means following this skill over local style." | Local, idiomatic style wins unless it is unsafe or broken. |
| "It is only one import; the layering still basically holds." | One inward-facing name is the violation. Layering is a rule, not a tendency. |
| "Splitting it into services will decouple it." | A process boundary is not a boundary. Coupling through shared data survives it. |
| "These two blocks are identical, so I will extract a helper." | Only if they must always change together. Check who owns each one. |
| "We will clean it up after the deadline." | The pressure that created the shortcut never abates. |

## Completion Checklist

Before saying the work is complete, confirm:

- The change solves the stated task, and every changed line traces to it.
- New files sit in conventional locations, follow local naming, and are fully wired in.
- No duplicate implementation or sibling-variant file was introduced.
- Each new or grown unit passes the one-sentence test.
- Every dependency you added points inward, and no detail leaked into a policy module.
- Names and structure reveal intent; errors, boundaries, and state are explicit enough for the risk.
- Tests or checks match the behavior changed; no test was weakened to pass.
- No dead code, scratch files, or debug output introduced by the change remains.
- Verification results are reported honestly, including what did not run.
- Decisions worth keeping are recorded in `.clean/decisions.md`; in campaign mode the ledger is
  current and the batch is verified and checkpointed.

## References

- `canon.md` — every named rule from both books, one line each. Start here when you know the name.
- `architecture.md` — dependency rule, SOLID, component principles, boundaries, systems, packaging,
  testability, decoupling modes.
- `principles.md` — naming, functions, formatting, errors, data, security, performance in full.
- `tests.md` — the Three Laws of TDD, F.I.R.S.T., BUILD-OPERATE-CHECK, test failure modes.
- `concurrency.md` — execution models, deadlock conditions, and how to actually catch a race.
- `examples.md` — worked before-and-after cases and output templates.
- `smell-triage.md` — every smell with its usual response, and the order to fix them in.
- `project-refactor.md` — campaign protocol for whole-project or module-wide cleanup.
- `new-project.md` — greenfield protocol: architecture and standards before code.
- `session-protocol.md` — per-session loop, context recovery, and clean handoff.
- `audit-report.md` — how to produce a cleaning and architecture report.
- `review-checklist.md` — finding-first checklist for reviews and diff review.
- `chapter-map.md` — code-level chapter map and the full smell catalogue with IDs.
- `architecture-map.md` — architectural topic map, from question to governing rule.
- `framework-map.md` — per-language and per-stack adaptation notes.
- `memory-protocol.md` — what to persist in `.clean/` so the next session can resume.
- `host-matrix.md` — per-host capabilities: hooks, commands, permissions, install paths.
