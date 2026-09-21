# Session Protocol

The default workflow: one coding task in an existing project. Use it for features, fixes, small
refactors, and anything else that is not a full campaign, a greenfield start, or a report.

It assumes you remember nothing. Every step either reads state from disk or writes state to disk, so
the next session — yours or another agent's — can pick up where you stopped.

## Before

**1. Load context.** Read `.clean/context.json`, `.clean/architecture.md`, `.clean/decisions.md`,
and `.clean/ledger.md` if they exist, then the project's own instructions (`AGENTS.md`,
`CLAUDE.md`, `CONTRIBUTING.md`, `README.md`). Project instructions outrank this skill. If
`.clean/` is absent, run `scripts/detect_stack.py` or derive the same facts by inspection: primary
language, frameworks, test command, source and test layout.

**2. Review previous decisions.** A recorded decision is settled. Do not re-open it because you
would have chosen differently; if it now looks wrong, say so and let the user decide.

**3. Confirm the goal.** State in one sentence what will be true when you are done, and what check
will prove it. If the request is ambiguous in a way that changes the implementation, ask. Otherwise
state your assumption and proceed.

**4. Check the constraints.** Note the declared layers and dependency rules, the naming conventions,
and any no-go areas (generated code, vendored code, another person's in-flight work).

**5. Inspect the related code.** Read the units you are about to change, their callers, and their
tests. Search for an existing implementation of what you are about to write. Trace the behavior
before altering it.

**6. Plan the edit.** Decide which unit owns the responsibility, which side of which boundary the
change sits on, and what the smallest diff looks like. For anything non-trivial, write the plan down
before editing.

## During

**7. Prefer what exists.** Extend the current owner of a concern rather than creating a new home for
it. A new dependency, layer, or file needs a reason you can state.

**8. Make small changes.** One intent per edit. Targeted edits, not whole-file regeneration.

**9. Keep the change focused.** Every changed line traces to the request or to cleanup the request
caused. Report unrelated smells; do not fix them silently.

**10. Stay consistent.** Match local naming, error style, test style, and framework idiom, even where
you would personally choose otherwise.

**11. Refactor as you go, inside the diff.** Improve the lines you already touched — a clearer name,
a removed dead branch — without widening the change.

**12. Remove the duplication you just created.** Copy-paste inside your own diff is the easiest kind
to catch and the cheapest to fix. Check that it is true duplication before merging it away.

**13. Validate assumptions against the code.** Confirm every API, option, and config key you
reference actually exists in this codebase and these dependency versions. Never trust memory.

## After

**14. Run the checks.** The narrowest meaningful check first, then broader ones as risk demands. Use
the project's real command, from `.clean/context.json` or the project's own docs.

**15. Review the impact.** Who calls what you changed? What did you orphan? Is anything now
unreferenced, half-wired, or newly duplicated?

**16. Verify architecture compliance.** Did every dependency you added point inward? Did any detail
— an ORM type, a framework annotation, an HTTP object, a raw row — leak into a policy module? Run
`scripts/check_boundaries.py` when the project declares layers, or check the imports you added by
hand.

**17. Update documentation** that your change made wrong. Do not add new documentation nobody asked
for.

**18. Leave it cleaner than you found it** — within the diff you already have, never by widening it.

**19. Record decisions worth keeping.** Append to `.clean/decisions.md` when you chose between real
alternatives, deferred something deliberately, or discovered a constraint the next session would
otherwise have to rediscover. See `memory-protocol.md`.

**20. Hand off cleanly.** Report: what changed and why; what command you ran and its result; what you
did *not* run and what risk remains; what you found but deliberately left alone. If work is
unfinished, write the remaining steps into `.clean/ledger.md` so the next session resumes instead of
restarting.

## Honesty rules

These are not negotiable, and they matter more than any style rule in this skill.

- Never claim a check passed without running it. "This should work" is not a result.
- Name what you skipped. An honest gap is useful; a silent one is a defect.
- Never weaken, skip, or delete a failing test to make a suite green. A failing test is information.
- Never present a stub, a placeholder, or a hardcoded demo value as finished work.
- If you could not do what was asked, say that plainly rather than delivering something adjacent.

## When to stop and ask

- The baseline is already broken and you cannot tell whether you caused a failure.
- The change needs a decision only the user can make: a behavior change, a public API break, a new
  dependency, a schema migration.
- Following this skill would conflict with the project's own conventions in a way that is not
  obviously a bug.
- The task keeps growing past the scope you agreed, or your remaining context is too small to finish
  the current slice safely.
