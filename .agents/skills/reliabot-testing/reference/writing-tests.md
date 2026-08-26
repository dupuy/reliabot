## Writing a new test

Reliabot's own testing convention (from CONTRIBUTING.md):

- **Typical usage** goes in the function's docstring as a doctest — keep it
  minimal and illustrative, since the docstring is also user-facing help.
- **Bug-fix regressions and corner cases** go in the `__test__` dict at the
  bottom of `reliabot/reliabot.py`, keyed by a descriptive `SCREAMING_CASE`
  name near the function they cover (like `VALIDATE_DEPENDABOT_CONFIG`). This
  keeps docstrings readable while still giving full doctest coverage.
- For a bug fix: write the test first, confirm it **fails** against the current
  code, then fix the code and confirm it passes.
- Follow the existing doctest style exactly: `>>> ` and `... ` prompts, real
  expected output below (doctest compares verbatim), and `# doctest: +ELLIPSIS`
  / `# doctest: +IGNORE_EXCEPTION_DETAIL` directives where outputs are
  variable.
- If a test needs a directory that can't be committed to Git for some reason
  (like containing a nested `.git/`), create it dynamically. See the module
  docstring at the start of `reliabot/reliabot.py`, which builds `testdir/`
  subdirectories with `os.mkdir` before running the doctests that need them.
- For changes to `tidy-md-refs.py`, add or adjust fixtures in `tests/untidy.md`
  (input) and `tests/tidied.md` (expected output) — `setup.cfg`'s `[testenv]`
  diffs the generated output against `tests/tidied.md` with
  `git diff --exit-code`.
