# Style guide rationale

Referenced from `SKILL.md` only when a violation's rule name needs
explaining. Four rules, checked by `scripts/check_style.py`:

## `bare-except`

`except:` with no exception type catches everything, including
`KeyboardInterrupt` and `SystemExit`, and silently hides bugs that should
have crashed loudly. Always name the exception type being handled, even if
that type is `Exception`.

## `missing-docstring`

Every public function (name not starting with `_`) needs a one-line
docstring stating what it does. This is what lets a reviewer — human or
agent — understand a function's contract without reading its body.

## `mutable-default-arg`

`def f(items=[])` — the list is created once, at function definition time,
and shared across every call that doesn't pass its own `items`. This is a
well-known Python foot-gun. Use `None` as the default and create the
mutable object inside the function body instead.

## `missing-type-hints`

Every public function's parameters and return value should be annotated.
Type hints are the fastest way for both humans and agents to know what a
function expects and returns without reading its implementation.
