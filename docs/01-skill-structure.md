# 1. Skill folder structure

A skill is a folder, not a file. The folder name **is** the skill's identity,
so treat it as an API contract:

```
skill-name/
├── SKILL.md        # required — the only thing loaded by default
├── scripts/        # small, deterministic CLIs the agent shells out to
├── references/     # detail the agent reads only when it needs to
└── assets/         # templates/schemas the agent copies into its output
```

Look at the working example in this repo:
[`.agents/skills/python-code-review/`](../.agents/skills/python-code-review/).

## Why this split exists

An agent doesn't load your whole skill folder every time. It sees the
`name`/`description` from every installed skill's frontmatter up front
(cheap — tens of tokens each), and only pulls in the full `SKILL.md` body
once it decides the skill applies. Everything under `references/`,
`scripts/`, and `assets/` is invisible until `SKILL.md` explicitly tells the
agent to open it. That staged loading is what keeps ten or fifty installed
skills from silently eating your context budget — see
[`03-progressive-disclosure.md`](03-progressive-disclosure.md).

## What goes where

- **`SKILL.md`** — navigation and procedure, not reference material. It
  should read like a short runbook: numbered steps, decision points, and
  pointers to files. Keep it under ~500 lines; if it's growing past that,
  something belongs in `references/` instead.
- **`scripts/`** — code for the *fragile, repetitive* parts: parsing,
  validation, anything where you'd rather the agent run a tested script than
  re-derive the logic from a prompt every time. Each script should behave
  like a tiny CLI: takes arguments, prints clear stdout/stderr, exits
  non-zero on failure with a message the agent can act on. This is **not**
  a place for general library code — a skill's `scripts/` folder ships with
  the skill; your actual application code lives in your normal repo
  structure (here, that's `app/`).
- **`references/`** — the material a human would call documentation:
  schemas, cheatsheets, the rationale behind a rule. Keep these **one level
  deep** (`references/style-guide.md`, not `references/rules/2026/style.md`)
  so the agent can find them without guessing a path.
- **`assets/`** — static output shapes: a template, a JSON schema, a
  boilerplate file the agent copies from rather than reconstructing from
  a paragraph of prose.

## What does *not* belong in a skill folder

- `README.md`, `CHANGELOG.md`, install guides — a skill folder is read by an
  agent, not a human browsing GitHub. Put human-facing documentation at the
  repo root (like this file) or in your normal docs, never inside the skill.
- Logic the agent already reliably does unassisted. If a step in `SKILL.md`
  never changes the agent's behavior, delete it — every line costs tokens on
  every trigger.
- Deeply nested reference material. If you find yourself writing
  `references/api/v2/errors/codes.md`, flatten it.

## Naming rule

The `name` in the frontmatter must exactly match the parent folder name.
`.agents/skills/python-code-review/SKILL.md` must declare
`name: python-code-review`. Agents route to skills by matching on this field
programmatically — a mismatch means the skill silently never loads.

## Worked example: `python-code-review`, file by file

This is the actual tree in this repo:

```
.agents/skills/python-code-review/
├── SKILL.md
├── scripts/
│   └── check_style.py
├── references/
│   └── style-guide.md
└── assets/
    └── review-template.md
```

- **`SKILL.md`** — `name: python-code-review` matches the folder name
  exactly, as required. The body is six numbered steps and one error-handling
  section, nothing else. It never explains *why* a bare `except` is wrong or
  *what* the review report should look like — it just says "run this script"
  and "use that template." That's the "brain, not encyclopedia" role in
  practice: every fact needed to act is one hop away, not inlined.

- **`scripts/check_style.py`** — the fragile, repetitive part: parsing a
  Python file with `ast` and checking four rules mechanically. This is
  exactly the kind of logic the top-level guidance warns against asking an
  agent to "remember" and re-derive from a prompt each time — a parser that
  hallucinates a violation, or misses one, is a worse outcome than a tested
  script. Note what's *not* here: no Flask code, no application logic. The
  toy app in `app/` that this script analyzes is a normal part of the repo,
  not part of the skill — the skill only ships the checking logic, never the
  code it checks.

- **`references/style-guide.md`** — one file, one level deep, and only
  reached via step 3 in `SKILL.md` ("read this if a rule name is
  unfamiliar"). On a session where the agent already explained
  `mutable-default-arg` once, it has no reason to open this file again — the
  reference exists for the cold-start case, not every run.

- **`assets/review-template.md`** — a literal Markdown skeleton
  (`## Summary`, `## Violations Found`, `## Fixes Applied`,
  `## Remaining Issues`) that step 6 tells the agent to fill in verbatim.
  Compare that to writing three paragraphs of prose describing the desired
  report shape inside `SKILL.md` — the template is shorter, unambiguous, and
  loaded only when a review is actually being written up.

- **What's absent is as deliberate as what's present** — no `README.md`
  inside the skill folder (that's this file, at the repo root instead), no
  `CHANGELOG.md`, and no general-purpose library code sitting in `scripts/`
  waiting to be imported from elsewhere. Everything in this folder exists
  because `SKILL.md` points to it by name.
