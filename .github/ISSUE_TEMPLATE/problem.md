---
name: Problem
about: Report a problem you have with Reliabot
title: Problem with …
labels: ''
assignees: ''
---

> Before reporting a problem, search for similar issues:
> \
> https://github.com/dupuy/reliabot/issues?q=is%3Aissue+sort%3Acomments-desc

> If you find one, please add a comment in that issue. For more help, see
> \
> https://github.com/dupuy/reliabot/blob/main/CONTRIBUTING.md#reporting-problems.

> ⚠️**Don't report security related issues or vulnerabilities here**. See
> \
> https://github.com/dupuy/reliabot/security/policy for secure reporting.

## Describe the problem

_Briefly describe the expected behavior and Reliabot's actual behavior._

## How you can reproduce the problem

_Outline the steps to show the problem you are having._

1. Set `PYTHONWARNINGS=default` in your environment

2. _Provide the Reliabot command line (or `pre-commit run -v reliabot`) output,
   including all warnings, error messages, and stack traces._

3. _Attach `.pre-commit-config.yml`, `dependabot.yml`, and `.gitignore` files._

4. _Link to a public GitHub repository or provide `tree` or `ls -R` output._

## Screenshots

_If applicable, add screenshots to help explain your problem._

## Context

_Add any other context about the problem here._

- Reliabot version

- Python version

- Operating system (distribution) version

- Output from `reliabot.py --self-test` (if relevant)
