## Markdown style checking and formatting

### Vale checks

`pre-commit` runs Vale on Markdown files (config in `.vale.ini`, styles in
`styles/`). `MinAlertLevel = suggestion` means that only error-level findings
block pre-commit checks, but in that case, both suggestions and warnings are
also reported. It may be worth rewording any warnings that are reported.

Most errors are unrecognized technical terms — resolve them by adding the term
to `styles/Vocab/Reliabot/accept.txt` (one word/phrase per line) rather than
rewording around them, unless the rewording is a genuine improvement. Some
Google-style rules (`Colons`, `EmDash`, and `Headings`) are turned off, so
don't fight those if they seem to fire anyway — check `.vale.ini` first.

### Other checks

Both `markdownlint` and `mdformat` run on any Markdown files, and `mdformat` is
quite aggressive and there is no way to turn it off for just part of a file.
Accept and `git add` its changes and move on.
