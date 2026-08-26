# 3. Progressive disclosure

"Progressive disclosure" just means: don't make the agent read something
until it needs it. Every skill you install costs a little context up front
(the frontmatter) and potentially a lot of context when it triggers (the
full `SKILL.md` body, plus whatever it's told to open). Bloat compounds
across a whole team's worth of skills.

## The three tiers, and their approximate cost

1. **Always loaded** — `name` + `description` for every installed skill.
   Tens of tokens each. Fifty skills here still only costs a few thousand
   tokens total — this tier is cheap by design.
2. **Loaded on trigger** — the full `SKILL.md` body. This is where cost
   actually lives. A 500-line file loads in full every single time the
   skill fires, whether or not the current task touches all 500 lines.
3. **Loaded on demand** — anything in `references/`, `scripts/`, `assets/`.
   Free until `SKILL.md` explicitly tells the agent to open it.

The lesson: push as much as you can from tier 2 into tier 3.

## How this repo's example applies it

Look at
[`.agents/skills/python-code-review/SKILL.md`](../.agents/skills/python-code-review/SKILL.md).
It never explains *why* a bare `except` is a problem — that rationale lives
in
[`references/style-guide.md`](../.agents/skills/python-code-review/references/style-guide.md)
and is only pulled in "if any violation touches a rule you don't recognize."
For the common case — the agent already knows the four rules from a prior
turn in the same session — that file is never read at all.

Similarly, the exact shape of the review write-up isn't described in prose
inside `SKILL.md` (which would take several paragraphs and be one more thing
for the agent to reconstruct imperfectly); it's a literal template in
[`assets/review-template.md`](../.agents/skills/python-code-review/assets/review-template.md)
that `SKILL.md` just points to.

## Practical rules

- **Explicit pathing.** Tell the agent exactly which file to read and when
  ("see `references/style-guide.md` for rule rationale") — it will not
  proactively explore the skill folder looking for context.
- **Relative, forward-slash paths.** Regardless of the OS the agent is
  running on.
- **One level deep.** `references/style-guide.md`, never
  `references/python/2026/style-guide.md`. If you need that much structure,
  you probably need a second skill, not a deeper folder.
- **Prefer a script to a paragraph.** If a rule can be checked
  mechanically (see `scripts/check_style.py`), do that instead of asking the
  agent to hold four style rules in its head and apply them by pattern
  matching. This is also what makes the rest of this repo's benchmark
  possible — a script's output is something you can score.
