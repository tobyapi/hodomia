# Host Matrix

This skill is one folder of Markdown and a few standard-library Python scripts, which is all the
Agent Skills standard guarantees. Everything *beyond* that — hooks, slash commands, tool
permissions, persistent memory, session startup behavior — is host-specific and not part of the
standard. This file records what each host offers and what to do where it offers nothing.

**The rule for portable behavior: never depend on a host capability for correctness.** Use one when
it is there, because deterministic enforcement beats an instruction the model might skip. Fall back
to the prose step when it is not.

## Skill discovery paths

Where each host looks for skills. Project-scoped roots are relative to the repository.

Where each host looks. Project roots are relative to the repository. Every path below was taken
from the vendor's own documentation; where a vendor documents no path, the row says so rather than
guessing.

| Host | Personal | Project |
| --- | --- | --- |
| Claude Code | `~/.claude/skills` | `.claude/skills` (also nested, and inside each `--add-dir`) |
| OpenAI Codex CLI | `~/.agents/skills`, `/etc/codex/skills` (admin) | `.agents/skills`, scanned from the cwd up to the repo root |
| Codex App (ChatGPT desktop / web) | in-product only | in-product only |
| GitHub Copilot (CLI and VS Code) | `~/.copilot/skills`, `~/.agents/skills` | `.github/skills`, `.claude/skills`, `.agents/skills` |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `.gemini/skills`, `.agents/skills` |
| Google Antigravity | `~/.gemini/config/skills` | `.agents/skills` (legacy alias `.agent/skills`) |
| Cursor | `~/.agents/skills`, `~/.cursor/skills`, `~/.claude/skills`, `~/.codex/skills` | `.agents/skills`, `.cursor/skills`, `.claude/skills`, `.codex/skills` |
| Amp | `~/.agents/skills`, `~/.config/agents/skills` | `.agents/skills` |
| OpenCode | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` | `.opencode/skills`, `.claude/skills`, `.agents/skills` |
| Factory Droid | `~/.factory/skills`, `~/.agents/skills` | `.factory/skills`, `.agents/skills` |
| Devin CLI | `~/.agents/skills`, `~/.config/devin/skills` | `.agents/skills`, `.devin/skills`, `.windsurf/skills` |
| Kimi Code | `~/.kimi-code/skills`, `~/.agents/skills` | `.kimi-code/skills`, `.agents/skills` |
| Grok Build CLI | `~/.grok/skills`, `~/.agents/skills` | `.grok/skills` |
| Hermes Agent | `~/.hermes/skills` | `.hermes/skills`, `.agents/skills` |
| pi | `~/.pi/agent/skills`, `~/.agents/skills` | `.pi/skills`, `.agents/skills` |

**`.agents/skills` is the shared root, read project-side by every host above except Claude Code,
Grok Build CLI, and the Codex App.** That is why `scripts/install.sh` writes the whole skill there
under the `agents` profile, rather than only dropping an instruction block.

Three exceptions worth knowing, because a generic installer gets them wrong:

- **Claude Code** uses `.claude/skills` and `~/.claude/skills`; it does not read the shared root.
- **Grok Build CLI** reads `~/.agents/skills` personally but only `.grok/skills` inside a project.
- **Antigravity**'s personal root is `~/.gemini/config/skills`, *not* `~/.agents/skills`. Its
  project root is the shared one.

The **Codex App** has no documented on-disk skill directory. Skills are managed in-product — the
Plugins → Skills tab, or uploaded as a folder or zip — so install it there rather than by writing
files. Its underlying Codex binary reads the Codex paths above.

## Frontmatter

Only these fields are in the standard, and only these are safe to rely on:

| Field | Required | Limit |
| --- | --- | --- |
| `name` | yes | 64 chars, lowercase, digits and hyphens, must match the directory name |
| `description` | yes | 1024 chars; this is what every host matches against to decide relevance |
| `license` | no | short |
| `compatibility` | no | 500 chars; environment requirements |
| `metadata` | no | string-to-string map |

`allowed-tools` is experimental and inconsistently implemented — **never depend on it for
correctness.** Fields such as `user-invocable`, `disable-model-invocation`, `context`, and
`argument-hint` are single-host extensions. Hosts that do not understand a field ignore it, so
adding one is safe; *relying* on one is not.

Body budget: keep `SKILL.md` under 500 lines and roughly 5,000 tokens. Reference files load on
demand, so depth belongs in `references/`, not in the main file.

## Capability support

| Capability | Where it exists | Portable substitute |
| --- | --- | --- |
| Session-start hook | Claude Code (`SessionStart`) and some others | Step 1 of `session-protocol.md`: read `.clean/` before anything else |
| Post-edit hook | Claude Code (`PostToolUse` on edits) | Step 16: check dependency direction during diff review |
| Pre-commit enforcement | git, on every host | none needed — this is the portable path, see `assets/hooks/pre-commit` |
| Slash commands | varies — see the invocation table below | invoke the workflow by name: "run the audit workflow" |
| Tool permissions | every host, all differently | declare needs in `compatibility`; keep scripts read-only |
| Persistent memory | a few hosts | `.clean/` on disk — works everywhere, and survives host changes |
| Subagents | several hosts | do the work inline |

## How a user forces a skill

Every host activates a skill automatically by matching the request against the `description`. What
differs is the explicit form, and it differs more than most documentation admits:

| Host | Explicit invocation |
| --- | --- |
| Claude Code | `/clean-code`, or `/clean-code-skills:clean-code` when installed as a plugin |
| Codex CLI and IDE extension | `$clean-code`, or `/skills` to browse |
| Codex App | `@clean-code` |
| Kimi Code | `/skill:clean-code`, and it accepts arguments after the name |
| Grok Build CLI, Devin CLI, Hermes Agent, Copilot CLI | `/clean-code` |
| Hermes Agent | also stacks: `/skill-one /skill-two <instruction>` |
| Gemini CLI | no user syntax — the model calls an `activate_skill` tool and asks you to approve |
| OpenCode | no user syntax — the agent calls a native `skill` tool |
| Cursor, Antigravity, Factory Droid, pi | no documented syntax; name the skill in plain language |

Where there is no explicit form, "Use the clean-code skill for this" works everywhere, because it
puts the skill's own name in the request the description is matched against.

Grok Build CLI, Cursor, and Factory Droid all document a `disable-model-invocation` opt-out. This
skill does not set it — automatic activation is the point.

## Recommended setup per host

**Any host, first choice:** install the git pre-commit hook from `assets/hooks/pre-commit`. It needs
no host support at all, runs the dependency check and a scan of changed files, and is the only
enforcement that works identically everywhere.

**Claude Code:** merge `assets/hooks/claude-settings.json` into `.claude/settings.json` for a
session-start context print and a post-edit scan. Optionally expose the four workflows as commands in
`.claude/commands/`.

**Codex CLI, Copilot, Gemini CLI, Cursor, Amp, OpenCode, Factory Droid, Devin CLI, Kimi Code,
Antigravity, pi:** the `agents` profile of `scripts/install.sh` installs the whole skill into
`.agents/skills/clean-code`, which every one of these reads project-side. Add the pre-commit hook and
you are done.

**Grok Build CLI:** use the `grok` profile — its project root is `.grok/skills`, not the shared one.

**Antigravity, installed globally:** use the `antigravity` profile, which targets
`~/.gemini/config/skills`. Its project side needs nothing beyond the `agents` profile.

**Codex App:** nothing to install on disk. Upload the skill in-product, from Plugins → Skills, or use
the `clean-code.zip` release asset.

The managed instruction block that `scripts/install.sh` writes into `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `.cursor/rules/`, `.windsurf/rules/`, `.clinerules/`, and the Copilot instruction files
keeps the non-negotiable rules visible even when the skill itself is not loaded — which is the
fallback for any host not listed here.

**Hosted or sandboxed agents with no shell:** every workflow works with zero tooling. Each step that
names a script also names the manual equivalent. Do that instead, and say in your report that the
automated checks did not run.

## Writing for every model, not just the strongest one

This skill is read by models of very different capability. What survives that range:

- **Imperative numbered steps** outperform prose. A weaker model follows "1. Read `.clean/context.json`"
  reliably and "consider the project's context" almost never.
- **Deterministic checks beat instructions.** If code can answer a question, let code answer it —
  that is what `scripts/` are for. Reserve model judgement for the parts that genuinely need
  judgement.
- **No host-specific vocabulary.** Never name a host's tools, panels, or UI verbs in skill content.
  Say "read the file", not "use the Read tool".
- **No absolute paths, no personal paths.** Everything relative to the project or the skill root.
- **Capability conditionals, not assumptions.** "If you can run shell commands, run X; otherwise
  check Y by reading Z."
- **Concrete over abstract.** "No `_v2` files" is followed; "maintain good file hygiene" is not.
- **State the failure each rule prevents.** A rule with a reason attached survives paraphrase and
  summarization; a bare prohibition does not.

## Verifying portability before release

Smoke-test on at least two hosts, checking five things: the skill is discovered; it activates on a
relevant request; a reference file loads on demand; a script runs under that host's real permission
model; and the output is actually useful. A skill that only works where it was written is a
single-host skill regardless of its frontmatter.
