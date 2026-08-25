---
name: reliabot-testing
description: Use when modifying reliabot code or tests, to run the Reliabot doctest suite and pre-commit checks, and avoid GitHub CI failures.
---

Use this skill to run checks and tests after making code changes.

In addition to automatic pre-commit checks invoked by `git commit` or
`pre-commit run`, test changes to Python code or library updates. Reliabot
tests are implemented as doctests in the reliabot.py script: unit tests are in
the function/method docstrings, and broader tests are in the docstrings of
entries in `__test__` map.

Running `reliabot.py --self-test` exercises all doctests, but running just
specific tests is possible using this doctest command:

```shell
FUNCTION=some_function
python -c "
  import doctest, reliabot
  doctest.run_docstring_examples(
    reliabot.$FUNCTION, globals(), verbose=True, name='$FUNCTION')"
```

The `testdir/` folder has various directories with configuration files as test
harnesses that are used in doctests.

To also test other Python development tool scripts, use `tox -e py`.

Pre-commit checks may modify or reformat files; check the output from
pre-commit and be sure to stage changed files with `git add` before committing
or running pre-commit again.

When using any features that have been newly introduced or changed in recent
Python versions, run `tox -a` to check against all supported Python versions.

After any significant refactoring, as a final check, run
`SKIP=markdown-link-check,pre-commit-update pre-commit run -a` to run
pre-commit checks on all files as changes can affect unmodified files.

If there are changes to output or `dedup_warn` messages, also run
`tox -e doctest-cli`, which checks documentation for consistency with
user-visible warning messages or output change.

Fix problems reported by tests whenever possible (for doctest-cli you should
change documentation to match the implementation). If tests are still failing
after a couple of attempts, just report the test failures as it can be tricky
to write tests in doctest strings.

If you need to skip particular pre-commit checks to commit a change, list the
checks that were skipped and include the error output from those checks in a
final response.

Summarize coverage changes from the tox report (`cobertura.xml`), and if
coverage drops close to the `--fail-under` threshold, create additional tests
for new features or recently modified code.
