# Reliabot – Agent Instructions

This is a Python tool that maintains Dependabot configurations for GitHub
repositories. It is distributed as both a CLI script and a pre-commit hook.

## Project Overview

- **Language**: Python (primary), with shell scripts and Markdown docs
- **Package manager**: Poetry (`pyproject.toml`, `poetry.lock`)
- **Test runner**: `tox` (run with `make tests`)
- **Pre-commit**: Extensive hook suite — always run `pre-commit` and add any
  automatically applied changes to files before committing

## Git Commits

All commit messages **must** follow
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format:

```
type(optional-scope): short imperative summary

Optional body with more detail. Reference any relevant GitHub issues with `#123` style references.
```

**Rules:**

- First line: 72 characters or fewer (ideally no more than 50)
- `type` must be one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
  `test`, `build`, `ci`, `chore`, `revert`
- Use **present tense, imperative mood**: "Add feature" not "Added feature"
- Examples of valid messages:
  - `fix: handle missing dependabot.yml gracefully`
  - `ci(pre-commit): add conventional-pre-commit commit-msg hook`
  - `docs: update FAQ with Renovate comparison`
- The `conventional-pre-commit` hook runs at the `commit-msg` stage and
  **rejects** non-conforming messages. Do not use `-n`, `--no-verify`, or
  `SKIP` environment variable to disable checks.

## Refactoring Guidelines

Before refactoring any code:

1. **Run the tests first** (`make tests` or `tox`) to establish a baseline.
2. **Keep refactoring commits separate** from feature or fix commits. Use
   `refactor:` as the commit type.
3. **Do not change behavior** in a refactoring commit. If a behavior change is
   also needed, make it in a separate `fix:` or `feat:` commit.
4. **Preserve doctests**: `reliabot.py` uses doctests embedded in docstrings
   and the `__test__` map. Do not remove or alter them unless the behavior they
   document is intentionally changing.
5. **Suppressing linter warnings is acceptable** using `# noqa: BXXX` (Ruff) or
   `# pylint: disable=...` (Pylint) when the code must do something unusual —
   but add a brief comment explaining why.
6. **Run `pre-commit run --all-files`** after refactoring to catch any
   formatting or lint regressions before committing. Always accept and add any
   changes made by pre-commit checks.

## Code Style

- **Formatter**: Ruff (Black-compatible). Pre-commit enforces this — do not
  manually reformat in ways that contradict it.
- **Linter**: Ruff + Prospector (Pylint). Both run in pre-commit.
- **Shell scripts**: formatted with `shfmt -i 2 -ci`, linted with `shellcheck`.
- **Import style**: follow existing patterns in the file being modified.

## Documentation Style

- Markdown files use GitHub Flavored Markdown, formatted by `mdformat`.
- Word wrap at **79 columns**.
- Ordered lists use consecutive numbering (`1.`, `2.`, `3.`), not `1.` for
  every item.
- Vale prose linter runs in pre-commit — errors block commits, warnings should
  be addressed. Add unknown but correct words to
  `styles/config/vocabularies/Reliabot/accept.txt`.
- Reference links use numeric tags ordered by appearance (managed by
  `tidy-md-refs.py` hook). Use inline links only for same-file anchors.

## Configuration Files

- TOML, YAML, JSON, INI/CFG files are formatted by **Prettier** with single
  quotes preferred where the format allows.
- YAML indentation in `dependabot.yml` follows `ruamel.yaml` settings defined
  in Reliabot comments (`# reliabot: mapping=4 offset=2 sequence=4`).

## What Not To Do

- Do not run `git commit --no-verify` or bypass pre-commit hooks.
- Do not add dependencies without updating `pyproject.toml` and `poetry.lock`.
- Do not modify `CHANGELOG.md` directly — it is managed by the release process.
- Do not push directly to `main`. Work on a branch and open a PR.
