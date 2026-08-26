## Repository layout (what matters for testing)

- `Makefile`

  `make tests` runs `tox` tests; `make devtools` installs tox

- `reliabot/reliabot.py`

  Reliabot tool **and** its doctests (module/function docstrings and a
  `__test__` dict at the end of the file)

- `setup.cfg`

  `[testenv]`: test commands are here, _not_ in `tox.ini` or `pyproject.toml`.

- `testdir/`

  Fixture directory tree that reliabot scans in doctests (`configured/`,
  `badlink/`, `github/`, `not-dir/`, …).

- `styles`

  Grammar style check rules used by Vale pre-commit

- `tests/`

  Fixtures for testing `tidy-md-refs.py` (Markdown link tidying helper script);
  `untidy.md` is the test source file; expected tidy output is in `tidied.md`.

- `fuzz/`

  Atheris fuzzing harness + corpus, not part of `tox` tests

- `.github/ISSUE_TEMPLATE/problem.md`

  Template for filing bugs found by tests

- `.mdl-style.rb`

  Configuration for markdownlint pre-commit check

- `.pre-commit-config.yaml`

  Full suite of pre-commit checks

- `.pre-commit-hooks.yaml`

  Reliabot pre-commit checks for use in other repositories

- `.prospector.yaml`

  Configuration for prospector pre-commit (this is largely replaced by Ruff).

- `.vale.ini`

  Vale style checking pre-commit configuration file
