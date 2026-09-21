# Cleanup Ledger

<!--
Copy to .clean/ledger.md when a campaign starts. See references/project-refactor.md.

This is the file that makes a multi-session cleanup survivable. Keep it current DURING the
campaign, not at the end: an accurate ledger with an interrupted campaign is a good
outcome; a finished campaign with a stale ledger is not.

Re-read this file at the start of every session and before every batch.
-->

**Campaign**: <what is being cleaned up>
**Started**: <date>   **Last updated**: <date>
**Status**: <planning | in progress | paused | closed>

## Contract

Agreed before any editing began:

- **Depth**: <naming and dead code only | structural extraction | architectural re-layering>
- **Breadth**: <whole project | named modules | one pilot slice>
- **Behavior policy**: batches are behavior-preserving. Bugs found are logged below, not silently
  fixed.
- **Checkpoints**: <one commit per batch | other>
- **No-go zones**: <generated code, vendored code, another person's in-flight work, ...>

## Baseline

Recorded before the first change, verbatim:

- **Verify command**: <command>
- **Result**: <pass/fail with counts, quoted from the actual run>
- **Known-failing before we started**: <list, so nothing is blamed on this campaign>
- **Untested risky areas**: <where a change cannot be verified; reduce depth here>

## Batches

One batch = one intent. Never mix a mechanical sweep with structural edits in the same diff.

- [ ] 1. <module or smell family> - <what changes> - commit: <sha>
- [ ] 2. <module or smell family> - <what changes> - commit: <sha>
- [ ] 3. ...

## Found but not fixed

Bugs and risks discovered while refactoring. Logged, not fixed, because a refactor batch must not
change behavior.

| What | Where | Severity | Note |
| --- | --- | --- | --- |
| | | | |

## Deferred

Deliberately out of scope for this campaign, with the reason.

| What | Why deferred | Revisit when |
| --- | --- | --- |
| | | |

## Close-out

Filled in at the end:

- **Final verification**: <command and result, compared against the baseline>
- **Done**: <what was completed>
- **Remaining**: <what a future campaign should pick up first>
