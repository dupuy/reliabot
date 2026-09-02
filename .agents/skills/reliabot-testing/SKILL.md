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

## Running tests

Always work from the repository root. If no local clone is available,
`git clone https://github.com/dupuy/reliabot.git` first. See
`reference/repo-layout.md` for locations of all test-related configuration.

When inspecting a specific commit, PR, or fork (especially `dupuyarc/reliabot`
or other forks), prefer `git clone` / `git fetch` over fetching GitHub web
pages — web views can return cached/stale content, and some raw/tree URLs are
blocked. Use `git ls-remote https://github.com/$FORK_OWNER/reliabot.git` to
check what's actually pushed before trying to fetch a specific SHA.

**Quick check — just the embedded doctests:**

```console
$ ./reliabot/reliabot.py --self-test 2>/dev/null | tail -5
149 tests in 43 items.
149 passed and 0 failed.
Test passed.
```

This is the fast inner loop. Run it after any change to `reliabot.py`.

Running `reliabot.py --self-test` exercises all doctests, but running just one
specific test is possible using this doctest command:

```shell
FUNCTION=some_function
python -c "
  import doctest, reliabot
  doctest.run_docstring_examples(
    reliabot.$FUNCTION, globals(), verbose=True, name='$FUNCTION')"
```

**Full suite (what CI runs):**

```console
$ make tests     # == tox
```

or `tox -e py312` etc. to target one environment. `tox` needs installing first
if missing — `make tox` (or `make devtools` for all development tools) does
that via `pipx`.

The `envlist` (see `setup.cfg`) is:

- `py`, `py312` etc. — run the doctest suite and test `tidy-md-refs.py` with a
  coverage gate (`--fail-under=85`).
- `ci-skip` — run tests of `Makefile` and `git-cliff` release notes generation
  to ensure that any commits with CI skip directives are modified so that
  CHANGELOG generation does not skip the release workflows.
- `doctest-cli` — run <code>\`\`\`console</code> code blocks in `*.md` files
  (README.md, CONTRIBUTING.md, etc.) as literal shell transcripts; only targets
  Python 3.12 because of a `pyre2-updated` wheel constraint.
- `pre-commit` — run `pre-commit run --all-files`

Run just one label:

````console
$ tox -e doctest-cli     # after editing any ```console block in a .md file
$ tox -e pre-commit
````

**Coverage** is measured with `coverage` + the `covdefaults` plugin (see
`[coverage:run]` in `setup.cfg`) and must stay ≥85%. If a change drops
coverage, add a doctest that exercises the new/changed branch rather than
disabling the check. See `reference/writing-tests.md` for more details.

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

Fix problems reported by tests whenever possible (for doctest-cli you should
change documentation to match the implementation). If tests are still failing
after a couple of attempts, just report the test failures as it can be tricky
to write tests in doctest strings. See `reference/debugging-quirks.md` for a
few "gotchas" to look out for.

Summarize coverage changes from the tox report (`cobertura.xml`), and if
coverage drops close to the `--fail-under` threshold, create additional tests
for new features or recently modified code.

If there is an existing problem or misfeature that should be addressed (but not
in the current commit or PR) `reference/filing-issues.md` has instructions for
[creating Reliabot issues](https://github.com/dupuy/reliabot/issues/new/choose).

## Resolving doctest-cli tests and pre-commit checks

For changes to <code>\`\`\`console</code> blocks inside `README.md` or
`CONTRIBUTING.md`, edit the Markdown directly, then run `tox -e doctest-cli` —
it executes each shell prompt line and compares the following lines to actual
output. In most cases fixing the documentation is the right thing to do.

Any changes involving Markdown files (documentation or otherwise) may fail Vale
or `markdownlint` pre-commit checks – `reference/markdown-style.md` has tips
for dealing with those checks.

Pre-commit checks may modify or reformat files; check the output from
pre-commit and be sure to stage changed files with `git add` before committing
or running pre-commit again.

After any significant refactoring, as a final check, run
`SKIP=markdown-link-check,pre-commit-update pre-commit run -a` to run
pre-commit checks on all files as changes can affect unmodified files.

If you need to skip particular pre-commit checks to commit a change, list any
checks that were skipped and include the error output from those checks in a
final response.
