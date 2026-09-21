English | [日本語](README.md)

# Stop AI Slop (Japanese Edition)

A Claude Skill for removing AI tells from Japanese prose.

This is the Japanese-language port of [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop).

> The skill content (`SKILL.md`, `references/*.md`) is written in Japanese. This English README exists for discoverability. If you write in Japanese with the help of an LLM, this is for you.

## What AI slop is

"AI slop" is the casual name for low-quality, hollow content churned out with generative AI.

In writing especially, the output often reads smoothly, but much of it is air: words lined up to look like substance, with nothing behind them.

This skill is for fixing that kind of writing. What it can't fix is the absent writer, so the surest way out of slop, I think, is to put as many of your own words on the page as you can.

See the note article [「その文章、AIに書かせただろ」](https://note.com/ikora/n/n0bbb2828b91e) for the longer version (Japanese).

## Overview

Use this Claude Skill to review and revise Japanese text drafted with an LLM before publishing.

It catches things like:

- Missing human agency: 課題が浮き彫りになる, 文化が醸成される
- Overbuilt headings: ○○が私たちに教えてくれること
- Small personal stories inflated into 真理, 美学, 境地
- Repeated structures: AではなくBだ, 3つの観点から
- Paragraphs with the same length, tone, and landing
- Full-width dashes, gratuitous 「」, leftover `**`, decorative emoji

The core problem is not the vocabulary list. It is prose with no visible writer. The skill pushes the model back toward who saw what, what bothered them, and what they are willing to say.

## Skill structure

```
stop-ai-slop-jp/
├── SKILL.md              # Core rules + quick checks + scoring
├── references/
│   ├── phrases.md        # Phrases to remove
│   ├── structures.md     # Structural patterns to avoid
│   └── examples.md       # AI / human transformation pairs
├── CHANGELOG.md
├── README.md
└── LICENSE
```

## Quick start

**Claude Code (personal)**
```bash
git clone https://github.com/iKora128/stop-ai-slop-jp ~/.claude/skills/stop-ai-slop-jp
```

**Claude Code (project)**
```bash
git clone https://github.com/iKora128/stop-ai-slop-jp <project>/.claude/skills/stop-ai-slop-jp
```

**Claude Projects**: Upload `SKILL.md` and `references/` to project knowledge.

**API**: Include `SKILL.md` in the system prompt. References load on demand.

## How to use

After installation, ask Claude to use `stop-ai-slop-jp`. Being explicit is more reliable.

### Review only

Paste the text and ask for findings first.

```text
Review this text using stop-ai-slop-jp.
List the issues in severity order across stance, agency, structure, vocabulary, and symbols.
For each issue, show: passage / why it smells / how to fix it.
Do not rewrite it yet.
```

### Rewrite

Use this when you want the prose fixed without changing the meaning.

```text
Remove the AI smell from this Japanese text.
Keep the meaning the same. Prioritize stance and agency.
Fix vocabulary and symbols last.
After the rewrite, list only the top three changes.
```

### Draft from notes

When drafting from notes, make Claude check the claim before writing the article.

```text
I want to draft an article from these notes.
Using stop-ai-slop-jp, first check:

- What am I actually claiming?
- Is the claim concrete enough to argue against?
- How is this different from the average article on the same topic?

After that, write the draft.
```

### Final check

For a light pass before publishing, narrow the scope.

```text
Run a light stop-ai-slop-jp pre-publish check.
Only check false agency, proposition-style H2s, overgeneralization, AI-favored nouns, full-width dashes, and gratuitous 「」.
If there are no major issues, reply only: "No major issues."
```

Revision priority: stance → agency → structure → vocabulary → symbols. Fixing dashes and emoji alone will not remove the smell if the prose still has no visible writer.

## Files

**SKILL.md**  
Principles, core rules, quick checks, and scoring.

**references/phrases.md**  
Words and phrases to consider removing: AI-favored nouns, translationese, hedges, IT metaphors, emoji.

**references/structures.md**  
Deeper patterns: false agency, proposition-style H2s, hook-and-reversal openings, uniform rhythm, both-sides-ism.

**references/examples.md**  
Before/after examples showing how to rewrite actual passages.

## Scoring

Rate 1–10 on each dimension. Below 35/50: revise.

| Dimension | Question |
|---|---|
| Stance | Is there a falsifiable, specific claim? |
| Rhythm | Varied length, tone, conclusion? |
| Agency | Is "who did what" explicit? (no false agency) |
| Specificity | Descends from abstractions to the actual context? |
| Reduction | Anything cuttable? |

## Credits

- Inspired by: [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)
- Japanese pattern catalog and worked examples: [note "その文章、AIに書かせただろ"](https://note.com/ikora/n/n0bbb2828b91e) (だいち | GENSHI AI)

## Author

Daichi Nagashima

## License

MIT. See `LICENSE`.
