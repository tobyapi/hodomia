# Memory Protocol

You forget everything between sessions. The project does not. This file defines the small set of
files that carry a project's design intent forward, so an agent with no memory and no conversation
history can reconstruct what it needs from the repository alone.

Everything lives in a `.clean/` directory at the project root. Templates are in
`assets/templates/`.

| File | Holds | Written by | Read when |
| --- | --- | --- | --- |
| `context.json` | detected stack, frameworks, test command, layout | `scripts/detect_stack.py --write`, or hand-written — it is only a cache of what you can read off the project | every session, first |
| `architecture.md` | declared layers and allowed dependencies | a human or an agent, with the user's agreement | every session; enforced by `check_boundaries.py` |
| `decisions.md` | decisions made and why, append-only | any session that made a real choice | before proposing a design change |
| `ledger.md` | state of a cleanup campaign in progress | campaign mode only | before starting or resuming a campaign |

## Rules

**Read before deciding.** All four files, at the start of the session, before touching code. A
recorded decision is settled: do not re-open it because you would have chosen differently. If it now
looks wrong, say so and let the user decide.

**`architecture.md` outranks your instincts.** It is the project's stated intent. If the code
disagrees with it, that is a finding to report, not a licence to follow the code.

**Write only what the next session cannot re-derive.** Do not record what the code already shows.
Record the *reasoning* that the code cannot: why this boundary and not that one, what was rejected,
what constraint forced an unusual choice.

**Never invent history.** If you do not know why something is the way it is, write that down as an
open question rather than a plausible-sounding reason. A confident wrong entry is worse than no
entry, because the next session will trust it.

**Append; do not rewrite.** `decisions.md` is a log. Supersede an entry with a new one that
references it, rather than editing the past.

**Ask before creating `.clean/`.** It is a new convention in someone's repository. Offer at the end
of a session; do not silently add it.

**Default to untracked.** Add `.clean/` to the project's `.gitignore` unless the user wants the
design intent committed. `architecture.md` is the one file usually worth committing, because it is a
shared decision and it drives a check in CI.

## What to record, and what not to

Record:

- a choice between real alternatives, and why the loser lost
- a deliberate deferral, and the condition that should trigger revisiting it
- a constraint discovered the hard way (an API limit, a migration hazard, a load-bearing quirk)
- a deviation from this skill or from the project's own conventions, and its justification
- a boundary decision: where the line is and which side owns the interface
- an open question the user needs to answer

Do not record:

- what the code plainly shows
- a summary of what you changed — that is the commit message's job
- restatements of this skill's rules
- anything you are guessing about

## Formats

### `decisions.md`

Append-only. Newest last. One entry per decision:

```markdown
## <date> - <short title>
**Decision**: <what was decided, in one sentence>
**Context**: <what forced the choice>
**Alternatives**: <what else was considered, and why it lost>
**Consequences**: <what this makes easy, and what it makes hard>
**Revisit if**: <the condition that would change the answer, or "n/a">
```

### `ledger.md`

Campaign state. The one file that makes a multi-session cleanup survivable — see
`project-refactor.md`. Keep it current *during* the campaign, not at the end: an accurate ledger and
an interrupted campaign is a good outcome, while a finished campaign with a stale ledger is not.

Sections: Contract, Baseline, Batches (a checklist with commit references), Found But Not Fixed,
Deferred.

### `architecture.md`

Prose for humans, plus one fenced `clean-architecture` block that tools can read. Layers are
declared innermost first; the default rule is that a layer may depend only on itself and on layers
declared before it. See `assets/templates/architecture.md` for the full format and
`architecture.md` in this directory for the reasoning behind it.

## If the host has session hooks

Some hosts can run a command when a session starts. Where that exists, printing `.clean/context.json`
and the layer declaration at session start is the single highest-value hook available, because it
removes the chance that an agent simply forgets to look. See `host-matrix.md` and
`assets/hooks/`.

Where it does not exist, step 1 of `session-protocol.md` is the substitute — which is why it is step
1.
