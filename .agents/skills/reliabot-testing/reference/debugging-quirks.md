## Unusual aspects of test structure

The `reliabot --self-test` command runs every doctest in the module in a single
Python process, and Reliabot's end-user warnings go through `dedup_warn()`,
which prints a message with a given non-empty key only once per
`warning_scope()` (`main()` opens a new scope for each run). Any doctests that
call functions other than `main()` directly aren't in a scope unless they open
one with `with warning_scope():`, so their keyed warnings are never
de-duplicated, and doctests that capture standard error
(`sys.stderr = sys.stdout`) see every warning. Warnings printed with no key are
never de-duplicated.

If `--self-test` fails, and there are no code changes near the failing example,
re-run with `tox -e py312` or compare against a clean CI run before concluding
it's a real regression.
