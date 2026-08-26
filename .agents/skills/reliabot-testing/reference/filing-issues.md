## Filing a GitHub issue for a bug found while testing

Use the `gh` command-line tool on `dupuy/reliabot` for new issues (search open
[issues](https://github.com/dupuy/reliabot/issues?q=is%3Aissue+sort%3Acomments-desc)
first). Match the **Problem** template (`.github/ISSUE_TEMPLATE/problem.md`)
structure: describe expected vs. actual behavior, reproduction steps, and
context (Reliabot version, Python version, OS, and `reliabot.py --self-test`
output if relevant). **_Never_** file security vulnerabilities as public issues
— point to `https://github.com/dupuy/reliabot/security/policy` instead.

```console
$ gh issue create --repo dupuy/reliabot \
    --title "Problem with ..." \
    --body-file problem-body.md
```

If `gh` isn't authenticated or available, draft the issue body in the same
structure and give it to the user to file manually.
