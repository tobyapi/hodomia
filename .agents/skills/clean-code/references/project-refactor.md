# Project Refactor Protocol (Campaign Mode)

Use this protocol when the task itself is cleanup: "clean up this project", "refactor this module to clean code", "apply clean code everywhere". Surgical-mode scope rules are suspended — the cleanup is the scope — but discipline is not. A campaign without structure degrades into an unreviewable rewrite that changes behavior nobody asked to change.

The protocol is designed for how agents actually fail at large refactors: context windows overflow mid-task, sessions end before the work does, early batches get forgotten by late batches, and enthusiasm at file 3 becomes inconsistency by file 30. Every step below exists to make progress durable and verifiable.

## Phase 0: Contract

Agree with the user before touching code:

- **Depth**: naming-and-dead-code pass? structural extraction? architectural re-layering? Each level multiplies risk.
- **Breadth**: whole project, selected modules, or one vertical slice as a pilot.
- **Behavior policy**: campaign batches are behavior-preserving. Bugs found along the way are logged, not silently fixed — a silent fix inside a rename batch is invisible to review. Confirm the user agrees, or carve out an explicit bug-fix lane.
- **Checkpoint style**: one commit per batch (preferred), or staged diffs for user review.
- **No-go zones**: generated code, vendored code, files with pending changes by others, anything the user marks off-limits.

If the user just said "clean it up", propose a contract with your recommended depth and breadth and let them confirm or adjust. Do not start editing while the contract is open.

## Phase 1: Inventory And Baseline

1. Map the project: layout, entry points, module boundaries, test locations, build and verification commands, formatter and linter configuration. `scripts/detect_stack.py --write` does this and caches the answers in `.clean/context.json`; otherwise establish the same facts by inspection.
2. Run the full available verification: tests, build, typecheck, lint. Record the results verbatim.
3. The recorded result is the **baseline**. A red baseline is not a blocker, but it must be written down — otherwise pre-existing failures get attributed to your refactor, or worse, your breakage hides among them.
4. Where risky code has no tests, add characterization tests first: capture what the code currently does (including its oddities), so refactoring has a safety net. If characterization is impractical, mark the area high-risk in the plan and reduce depth there.
5. Sweep for smells using `smell-triage.md` and the `chapter-map.md` heuristics. `scripts/scan_repo.py` gathers the measurable part — oversized files, sibling variants, junk drawers, debug output, skipped tests, untested areas — and the rest needs reading. Record findings as a list with file paths; this becomes the ledger.
6. Take the architectural inventory, because it determines what the later batches can safely do:
   - Is the intended layering written down? If `.clean/architecture.md` exists, that is the contract. If not, infer the layering from the structure, show the user what you inferred, and get it confirmed — an undeclared architecture cannot be violated, which also means it cannot be defended.
   - Which dependencies point the wrong way? `scripts/check_boundaries.py` answers this once layers are declared; otherwise check the imports of the modules you believe are innermost.
   - Are there cycles between components, and which edge would you invert?
   - Do details reach inward — ORM types, framework annotations, HTTP objects, raw rows inside business rules?
   - Can the business rules be tested with no infrastructure running? If not, that is the finding that gates everything else, because it decides whether a re-layering batch can be verified at all.

## Phase 2: Plan In Batches

Split the campaign into batches sized so that one batch fits comfortably in one session and one review. Two batching strategies work; pick per campaign:

- **By module**: all smells within one module or directory. Best when modules are independent and you want visible module-by-module completion.
- **By smell family**: one mechanical change across many files (rename a concept everywhere, normalize error wrapping, delete dead code, fix import order). Best when consistency across the codebase matters more than local completeness. Keep mechanical sweeps separate from structural batches — a rename sweep plus extractions in the same diff is unreviewable.

Order batches by risk and value:

1. Safety first: dead code removal, obvious duplication with a single caller, formatting via the project's formatter. Low risk, shrinks the problem.
2. Naming and readability: renames, explanatory variables, comment cleanup. Low risk with tooling support.
3. Structure: extractions, responsibility splits, moving code to its proper module. Medium risk; needs tests.
4. Boundaries and error handling: wrapping third-party APIs, normalizing failure paths. Higher risk; needs contract awareness.
5. Architecture: re-layering, dependency direction fixes. Highest risk; only within the agreed depth.

Write the plan into the ledger before starting batch 1.

## Phase 3: Execute Batch By Batch

For each batch:

1. Re-read the target files fresh. Do not edit from memory of an earlier read — earlier batches may have changed them, and stale context is how agents reintroduce deleted code.
2. Make the changes, applying the full skill: placement, one job per unit, naming, error handling.
3. Run the verification relevant to the batch, then the broader suite at least every few batches. Compare against the baseline: no new failures.
4. Update the ledger: what was done, what was found and deferred, anything discovered that changes the plan.
5. Checkpoint: commit with a message describing the batch, or present the diff, per the contract.
6. Report honestly if the batch went sideways; revert to the checkpoint rather than patching forward on top of a mess.

Batch hygiene:

- One batch, one intent. The commit message should pass the one-sentence test.
- If a batch balloons past its intent, stop, checkpoint what is coherent, and re-plan the remainder.
- Never carry uncommitted work from one batch into the next.

## Phase 4: Consistency Sweep And Close

After the planned batches:

1. Sweep for consistency debts the batches created: old and new naming coexisting, half-migrated patterns, imports of moved code. Half-done renames are worse than none — one concept, one name, everywhere in scope.
2. Run the full verification suite; compare to baseline; record the final state.
3. Close the ledger: done, deferred (with reasons), bugs found (for the user to prioritize), and recommended next campaigns.
4. Summarize for the user: batches completed, verification evidence, behavior risks taken (ideally none), and the deferred list.

## The Ledger

The ledger is a plain markdown file that survives context loss and session ends. The default home is `.clean/ledger.md`, started from `assets/templates/ledger.md`; keep it wherever the user prefers, and do not commit it unless asked. See `memory-protocol.md` for how it fits with the project's other durable state. Structure:

```markdown
# Cleanup Ledger: <project> — <date>

## Contract
depth / breadth / behavior policy / checkpoint style / no-go zones

## Baseline
command outputs, pass/fail counts, pre-existing failures

## Batches
- [x] 1. Delete dead exports in src/billing (commit abc123)
- [ ] 2. Rename `mgr` -> `subscriptionScheduler` across src/
...

## Found, Not Fixed
- src/billing/invoice.ts:88 rounding bug when currency=JPY (behavior change — needs user decision)

## Deferred
- src/legacy/: no tests, characterization impractical; recommend pilot slice first
```

Re-read the ledger at the start of every session and before every batch. If you lose context mid-campaign, the ledger is the recovery point.

## Stop Conditions

Pause and report instead of pushing through when:

- the baseline cannot be established (build broken, tests cannot run) — fixing the build is its own task and needs the user's go-ahead
- a batch requires a behavior change to proceed
- a risky area has no tests and characterization is impractical
- the same conflict keeps recurring between local style and clean-code rules — surface it once, get a ruling, apply it consistently
- remaining context is too small to finish the current batch safely — checkpoint first, then continue in a fresh session from the ledger

## What This Protocol Is Not

- Not a license to rewrite: preserve public behavior and contracts unless explicitly contracted otherwise. A rewrite is not the remedy for a mess; the team that produced the mess generally reproduces it.
- Not a style crusade: the project's formatter, linter, and idioms define style; the campaign enforces them, it does not replace them.
- Not all-at-once: an agent that edits thirty files in one pass produces thirty unreviewable diffs. Small batches are the only way a large cleanup stays safe.
- Not an architecture redesign in disguise: re-layering is the highest-risk depth and only happens inside the agreed contract. If the inventory shows the architecture is the real problem, say so and let the user decide — do not smuggle it in as batch 7.

## Leaving it better than a checklist would

A campaign that only removes smells produces a tidier version of the same design. These are the
changes that actually lower the future cost of change, in the order they are usually worth doing:

1. **Declare the architecture** in `.clean/architecture.md`. Cheapest possible batch, and it converts
   every later architectural argument into an automated check.
2. **Add the tests that make the risky areas verifiable.** Everything else is safer afterwards.
3. **Fix dependency direction** on the worst offenders — the inner modules that name outer ones.
4. **Remove the cycles**, so components can be built and released independently again.
5. **Pull details out of policy**: get ORM types, framework annotations, and HTTP objects out of the
   business rules, behind interfaces the business rules own.
6. **Then** the code-level work: naming, function size, duplication, dead code.

Record what you decided and why in `.clean/decisions.md` as you go. The next agent inherits the
reasoning, not just the result.
