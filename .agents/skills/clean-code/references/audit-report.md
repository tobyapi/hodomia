# Audit Report Protocol

For a request like "review this project", "how clean is this codebase", "where is the architectural
debt", or "give me a cleanup report". The deliverable is a **report, not a diff**: change no code
unless the user asks afterwards.

An audit is worth reading only if every claim is checkable. Cite a file and line for each finding, or
say plainly that you could not verify it.

## Gather evidence first

1. **Context** — `scripts/detect_stack.py`, or determine by inspection: languages, frameworks, test
   command, source and test layout, quality tooling.
2. **Measurements** — `scripts/scan_repo.py --json`, or by inspection: largest files, sibling-variant
   filenames, junk-drawer directories, debug output in production code, commented-out code, skipped
   tests, areas with no test files.
3. **Dependency direction** — `scripts/check_boundaries.py` if the project declares layers. If it
   does not, infer the intended layering from the directory names, state that you inferred it, and
   propose a declaration as a finding in its own right.
4. **Baseline** — run the test suite and record the result verbatim, including failures. An audit
   that does not know whether the suite is green is guessing.
5. **History, if available** — which files change most often, and which change together. Frequently
   co-changing files in different modules are evidence of a missing boundary.

Never report a number you did not measure. If a check could not run, the report says so.

## Report structure

```markdown
# Clean Code And Architecture Audit: <project>

**Date**: <date>   **Commit**: <sha>   **Scope**: <what was and was not examined>

## Verdict
<Three to five sentences. The single most important structural fact, the biggest risk, and
whether the codebase is currently safe to change quickly. No hedging.>

## Baseline
- Test command: <command>
- Result: <pass/fail, counts, verbatim summary>
- Coverage or untested areas: <what has no tests>
- What could not be verified: <explicitly>

## Findings

### Critical - wrong behavior or security risk
### High - blocks safe change
### Medium - raises the cost of every change
### Low - readability and consistency

<Each finding, in this shape:>
**<Short title>** - `path/to/file.ext:120`
- What: <the observable fact>
- Why it matters: <the concrete failure it causes or permits>
- Fix: <the specific change, and its rough size>
- Effort: <hours or days>   Risk of fixing: <low/medium/high>

## Architecture assessment
- Declared layering: <from .clean/architecture.md, or "none declared">
- Dependency direction: <violations found, with counts and examples>
- Boundaries: <where they are, where they are missing>
- Details leaking into policy: <ORM types, framework annotations, HTTP objects in business rules>
- Testability: <can business rules be tested without infrastructure?>
- Component cycles: <any, with the edge to invert>

## Metrics
| Measure | Value | Note |
|---|---|---|
| Files / lines | | |
| Largest file | | |
| Test files vs production files | | |
| Areas with no tests | | |
| Dependency-rule violations | | |
| Sibling-variant files | | |

## Recommended sequence
<Ordered, each with the reason it comes at that position. First item should be
independently valuable, so the work survives being stopped after one step.>

## What is already good
<Genuine strengths. An audit that lists only faults gets discounted as noise, and the
strengths tell the next agent what patterns to imitate.>
```

## Rules for the findings

- **Severity is about consequence, not ugliness.** A 900-line file nobody touches is Low. A skipped
  authorization layer is Critical no matter how tidy the code is.
- **One finding per line item.** If the fix differs, it is a different finding.
- **No finding without a location.** "Naming is inconsistent" is not a finding; three cited examples
  are.
- **Count instead of listing** when there are many instances: "47 occurrences, worst three cited".
- **Separate what you measured from what you inferred.** Both are useful; conflating them is not.
- **Say what the fix costs.** A finding with no effort estimate cannot be prioritized, so it will be
  ignored.
- **Do not pad.** Ten real findings beat sixty with fifty stylistic nits. Formatting belongs to the
  formatter.

## Ordering the recommendations

Order by risk reduced per unit of effort, not by severity alone:

1. Anything that can cause wrong behavior or a security hole.
2. Anything that makes verification impossible — because until this is fixed, every other fix is
   unsafe. Missing tests for the areas you are about to change come first.
3. Declaring the architecture, if it is undeclared. It is cheap, and it turns every later
   architectural finding from an opinion into a check.
4. Wrong-way dependencies and cycles, which compound.
5. Duplicated knowledge that is genuinely true duplication.
6. Readability.

## After the report

Offer, do not act:

- Fix the Critical findings now, one at a time with verification between them.
- Run the Onboard workflow (`project-refactor.md`) for anything larger — baseline, batches, ledger.
- Write `.clean/architecture.md` so the architectural findings become automated checks.
- Re-run the audit after the first batch, so improvement is measured rather than asserted.

If the user asks for fixes immediately, switch to `project-refactor.md` and treat this report as its
Phase 1 inventory. Do not begin editing directly from an audit: the report is a map, not a mandate.
