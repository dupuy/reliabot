## Unusual aspects of test structure

The `reliabot --self-test` command runs every doctest in the module in a single
Python process, and Reliabot's end-user warnings go through `dedup_warn()`,
which only prints a given `(message, key)` once per *process* via a global
`WARN_KEYS` set. If the local environment (missing `re2`, a different Python
minor version, etc.) causes `--self-test` to run doctests in a different order,
a warning like `Removed obsolete 'npm' entry in '/'` may appear in a different
part of output than the doctest expects, producing a spurious
`N passed and 2 failed` result even though nothing is actually broken.

If `--self-test` fails, and there are no code changes near the failing example,
re-run with `tox -e py312` or compare against a clean CI run before concluding
it's a real regression.
