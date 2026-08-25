---
name: reliabot-testing
description: Run, write, and debug tests for the [Reliabot project](https://github.com/dupuy/reliabot), a Python tool that maintains GitHub Dependabot configuration files. Use this whenever the user wants to run Reliabot's test suite, add or fix a doctest in reliabot.py, investigate a failing tox environment, work with the `testdir/` fixture tree, check coverage, run the Markdown console-doctest checks, or file a GitHub issue in dupuy/reliabot for a bug found while testing. Trigger on mentions of 'reliabot', 'self-test', 'tox', 'testdir/', 'dependabot.yml testing', or a failing CI run, even if the user doesn't say the word "test" explicitly.
---

# Reliabot Testing

Reliabot is a single-file Python script (`reliabot/reliabot.py`) that reads a
Git repository's tracked files and generates/updates `.github/dependabot.yml`.
Its test suite is unusual: almost everything lives as **doctests embedded in
the source**, run through `tox`, not a separate `pytest` suite. Know this
before touching anything.

## Repository layout (what matters for testing)

```
reliabot/reliabot.py    # the tool AND its doctests (module/function docstrings
                         # + a __test__ dict at the end of the file)
testdir/                # fixture directory tree reliabot scans in doctests
                         # (configured/, badlink/, github/, not-dir/, ...)
tests/untidy.md          # fixtures for tidy-md-refs.py (Markdown link tidying)
tests/tidied.md
tidy-md-refs.py          # separate helper script, tested via tests/*.md
fuzz/                    # Atheris fuzzing harness + corpus, not part of `tox`
setup.cfg                # [testenv] — the REAL tox commands live here, not
                          # in a tox.ini or pyproject.toml
Makefile                 # `make tests` == `tox`; `make devtools` installs tox
.github/ISSUE_TEMPLATE/problem.md   # template for filing bugs
```

## Running tests

Always work from the repository root. If no local clone is available,
`git clone https://github.com/dupuy/reliabot.git` first.

**Quick check — just the embedded doctests:**

```console
$ ./reliabot/reliabot.py --self-test 2>/dev/null | tail -5
149 tests in 43 items.
149 passed and 0 failed.
Test passed.
```

This is the fast inner loop. Run it after any change to `reliabot.py`.

**Full suite (what CI runs):**

```console
$ make tests     # == tox
```

or `tox -e py312` etc. to target one environment. `tox` needs installing first
if missing — `make tox` (or `make devtools` for all development tools) does
that via `pipx`.

The `envlist` (see `setup.cfg`) is:

- `py`, `py310`–`py314` — runs the doctest suite, plus `tidy-md-refs.py`
  round-trip checks against `tests/untidy.md`/`tests/tidied.md`,
  `ci-skip-test.sh`, and a coverage gate (`--fail-under=85`)
- `pre-commit` — runs `pre-commit run --all-files`
- `doctest-cli` — runs \`\`\`console fenced code blocks in `*.md` files
  (README.md, CONTRIBUTING.md, etc.) as literal shell transcripts; only targets
  Python 3.12 because of a `pyre2-updated` wheel constraint Run just one label:

````console
$ tox -e doctest-cli     # after editing any ```console block in a .md file
$ tox -e pre-commit
````

**Coverage** is measured with `coverage` + the `covdefaults` plugin (see
`[coverage:run]` in `setup.cfg`) and must stay ≥85%. If a change drops
coverage, add a doctest that exercises the new/changed branch rather than
disabling the check.

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
- Follow the existing doctest style exactly: `>>> `/`... ` prompts, real
  expected output below (doctest compares verbatim), and `# doctest: +ELLIPSIS`
  / `# doctest: +IGNORE_EXCEPTION_DETAIL` directives where output/tracebacks
  are variable.
- If a test needs a directory that can't be committed to Git for some reason
  (like containing a nested `.git/`), create it dynamically. See the module
  docstring at the start of `reliabot/reliabot.py`, which builds `testdir/`
  subdirectories with `os.mkdir` before running the doctests that need them.
  For changes to `tidy-md-refs.py`, add/adjust fixtures in `tests/untidy.md`
  (input) and `tests/tidied.md` (expected output) — `setup.cfg`'s `[testenv]`
  diffs the generated output against `tests/tidied.md` with
  `git diff --exit-code`.

For changes to <code>\`\`\`console</code> blocks inside `README.md` or
`CONTRIBUTING.md`, edit the Markdown directly, then run `tox -e doctest-cli` —
it executes each shell prompt line and compares the following lines to actual
output. In most cases fixing the documentation is the right thing to do.

## Debugging a failing test

1. Reproduce narrowly first: `./reliabot/reliabot.py --self-test` for doctests,
   `tox -e doctest-cli` for Markdown console blocks, `tox -e pre-commit` for
   lint/format issues — don't run the full matrix while iterating.
2. Failures in doctests print expected vs. actual output — diff them carefully,
   ruamel.yaml/indentation-sensitive output can be a source of mismatches (see
   `# reliabot:` comment handling in `reliabot.py`).
3. If a fixture directory under `testdir/` seems wrong or missing, check
   whether it's supposed to be created dynamically (see module docstring)
   before assuming it's a checked-in fixture problem.
4. `PYTHONWARNINGS=default` surfaces deprecation and regular expression
   warnings that are otherwise suppressed — CONTRIBUTING.md and the issue
   template both ask for `PYTHONWARNINGS=default` output when reporting
   problems.
5. **Known local-environment quirk:** `--self-test` runs every doctest in the
   module in a single Python process, and Reliabot's end-user warnings go
   through `dedup_warn()`, which only prints a given `(message, key)` once per
   *process* via a global `WARN_KEYS` set. If the local environment (missing
   `re2`, a different Python minor version, etc.) causes directories to be
   scanned in a different order than the reference environment, a warning like
   `Removed obsolete 'npm' entry in '/'` may be suppressed in a different part
   of output than the doctest expects, producing a spurious
   `N passed and 2 failed` result even though nothing is actually broken. If
   `--self-test` fails, and there are no code changes near the failing example,
   re-run with `tox -e py312`or compare against a clean CI run before
   concluding it's a real regression.

## Filing a GitHub issue for a bug found while testing

Use the `gh` command-line tool on `dupuy/reliabot` for new issues (search open
[issues](https://github.com/dupuy/reliabot/issues?q=is%3Aissue+sort%3Acomments-desc)
first. Match the **Problem** template (`.github/ISSUE_TEMPLATE/problem.md`)
structure: describe expected vs. actual behavior, reproduction steps, and
context (Reliabot version, Python version, OS, and `reliabot.py --self-test`
output if relevant). NEVER file security vulnerabilities as public issues —
point to `https://github.com/dupuy/reliabot/security/policy` instead.

```console
$ gh issue create --repo dupuy/reliabot \
    --title "Problem with ..." \
    --body-file problem-body.md
```

If `gh` isn't authenticated or available, draft the issue body in the same
structure and give it to the user to file manually.
