# Clean-Code Review Checklist

Use this for code reviews and final diff reviews. Findings should be specific, behavior-grounded, and ordered by severity. Cite smell IDs from `chapter-map.md` (G17, N7, T5...) when they apply, so findings stay unambiguous and cross-referenceable.

## Correctness

- Does the code solve the requested behavior without changing unrelated behavior?
- Are boundary cases handled: empty input, nullability, limits, invalid data, permissions, time zones, encodings, retries, cancellation?
- Are external assumptions tested or localized?

## Simplicity

- Is there a smaller solution that satisfies the same requirement?
- Are new abstractions justified by repeated complexity or a real invariant?
- Did the change add configuration, dependency injection, caching, background work, or extension points before they were needed?

## Placement And Structure

- Are new files in the directories the project's conventions predict, named by local patterns, and fully wired in (imports, exports, registration, build config)?
- Does any new code duplicate an existing helper, utility, or module instead of extending it?
- Were any sibling-variant files created (`_v2`, `_new`, `_final`, `_copy`) instead of editing the original?
- Did logic land in the layer that owns it, or in whatever file was convenient?
- Are there leftover scratch files, debug output, or unreferenced artifacts?

## Responsibility

- Does each new or changed unit pass the one-sentence test (its job described without "and", "also", "then")?
- Are parsing, domain decisions, persistence, external calls, presentation, and wiring kept in their established homes?
- Did any function or class absorb a new concern it should have delegated?
- Would testing a changed unit require mocking several unrelated systems?

## Readability

- Do names explain intent using project vocabulary?
- Does each function or module stay at one abstraction level?
- Are comments explaining why, not restating what?
- Is the main path easy to follow?

## Maintainability

- Are dependencies explicit?
- Are invariants protected by types, validation, or boundaries?
- Will the next related change touch one obvious place or many scattered places?
- Did the change create dead code, unused imports, or orphaned tests?

## Error Handling

- Are failures handled where a meaningful decision can be made?
- Is useful context preserved?
- Are broad catches, silent defaults, and ignored return values avoided?
- Are sensitive values kept out of logs and error messages?

## Tests And Verification

- Do tests cover the changed behavior and relevant edge cases?
- Are tests deterministic and behavior-focused?
- Did verification actually run?
- If tests were not added or run, is the residual risk clear?

## Concurrency And State

- Is shared mutable state controlled?
- Are lifecycles, cancellation, cleanup, ordering, and idempotency clear?
- Could retries, duplicate events, or parallel calls corrupt state?

## Review Output Format

Lead with findings. For each finding, include:

- severity
- file and line or smallest useful location
- exact risk
- suggested fix or verification

Then list open questions, test gaps, and a short summary only after findings.

## Full Clean-Code Scan

When the review is broad or the user asks for comprehensive clean-code coverage, also scan `chapter-map.md` and group findings by root cause:

- naming and intent
- functions and abstraction level
- comments and formatting
- data/object boundaries
- errors and external boundaries
- tests and verification
- class/module cohesion
- placement and responsibility ownership
- system construction and dependency wiring
- emergent design and duplication
- concurrency and shared state
- successive refinement and legacy safety
- chapter 17 smell groups

If the findings are numerous enough that fixing them becomes a project of its own, do not fix them inline. Recommend a campaign and point to `project-refactor.md`.
