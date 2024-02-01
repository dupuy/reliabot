# Contributing to Reliabot

🙏Thanks in advance for your contributions ❤️

There are _many_ ways to contribute – one of the best is just using Reliabot
for your projects – and no contribution is too small or too large.

- [Ask a question](#asking-a-question) about using Reliabot.
- [Open an issue][1] about a problem, or for a way to improve Reliabot.
- [Improve the docs](#improving-the-documentation) by fixing typos and broken
  links, or writing a HowTo.
- [Write code](#contributing-code-and-bug-fixes) to add a feature or support
  for a distribution packager.

See the [Table of contents](#table-of-contents) for different ways to help and
details about how to contribute to Reliabot. _Please read the relevant section
before contributing_. This makes the process easier and improves the experience
for everyone.

👀 Looking forward to your contributions 🎉

> If you use or like the project, but don't have time to contribute, that's OK.
> Here are some easy ways to support Reliabot and show your appreciation.
>
> - Star the Reliabot GitHub project
> - Refer to Reliabot in your project's README
> - Link to Reliabot in social media

#### Table of contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=2 -->

- [Asking a question](#asking-a-question)
- [Reporting problems](#reporting-problems)
  - [Before submitting a problem report](#before-submitting-a-problem-report)
  - [How to submit a good problem report](#how-to-submit-a-good-problem-report)
- [Suggesting enhancements](#suggesting-enhancements)
  - [Before suggesting an enhancement](#before-suggesting-an-enhancement)
  - [Writing a good enhancement suggestion](#writing-a-good-enhancement-suggestion)
- [Becoming a contributor](#becoming-a-contributor)
  - [First contributions](#first-contributions)
  - [Pre-commit setup](#pre-commit-setup)
  - [Contributing code and bug fixes](#contributing-code-and-bug-fixes)
  - [Improving the documentation](#improving-the-documentation)
- [Style guides](#style-guides)
  - [Commit messages](#commit-messages)
  - [Python code](#python-code)
  - [Shell code](#shell-code)
  - [Markdown documentation](#markdown-documentation)
  - [Configuration files](#configuration-files)
- [Attribution](#attribution)

<!-- mdformat-toc end -->

## Asking a question

> 💡 If you have a Reliabot question, take a look at the [README][2] and its
> [FAQ][3] to see if it's answered there.

Before asking a question, search for [existing issues][4] that are similar. If
you find a relevant issue but still need clarification, ask your question in
that issue. A few internet search queries may also turn up an answer quickly.

If you don't find an answer or an existing issue, follow these steps to ask
your question:

- [Create a new issue][5], labeling it as a 🟣 **question**.
- Provide as much context as you can for your question.
  - Reliabot version
  - Whether you're running Reliabot with pre-commit or on the command line
  - Operating System (distribution) and Python versions
- Explain what you're trying to do, and what you don't understand.

Someone should respond to the issue as soon as possible. Be patient. 🕗😊

## Reporting problems

### Before submitting a problem report

A good problem report shouldn't force others to contact you for critical
missing information. Please investigate carefully, find examples and
counter-examples, and describe the problem in detail. Completing the following
steps in advance helps to fix any potential bug as fast as possible.

- To see if other users have experienced (and perhaps already solved) your
  problem, search the [bug tracker][6] for similar issues or error messages.
- Searching the internet (especially Stack Overflow) can help you find any
  users of other tools, or in other forums, who have run into a similar
  problem.
- Make sure you are using the latest Reliabot version.
- Confirm that your problem is really a bug and not an error on your part, such
  as using Reliabot with unsupported environments or versions. Reading the
  [documentation][2] can help. If you need help, consider just
  [asking a question](#asking-a-question) first.
- Collect information about the problem:
  - Specific Reliabot command line and context.
  - Reliabot output, including error messages, warnings, and stack traces.
    Setting `PYTHONWARNINGS=default` in the environment can show extra
    diagnostics.
  - Your `.pre-commit-config.yml`, `dependabot.yml`, and `.gitignore` files.
  - If your GitHub repository is private, output from `tree` or `ls -R`.
  - Versions of Reliabot, Python, and your Operating System (distribution).
  - Output from `reliabot.py --self-test` (if relevant).
  - Can you reliably reproduce the problem? And can you also reproduce it with
    older Reliabot versions?

### How to submit a good problem report

> ⚠️Don't report security related issues or vulnerabilities, or include
> sensitive information in reports on the issue tracker, or elsewhere in
> public. Instead, [open a draft security advisory][7] and provide the
> vulnerability information there. See the [Reliabot security policy][8] for
> more details.

The Reliabot project uses [GitHub issues][4] for tracking bugs. If you found a
problem using Reliabot:

- [Create an issue using the problem template][9]. It may not be clear yet
  whether it's a bug, so please don't label the issue.
- Describe the behavior you expect and the differences in the actual behavior.
- Please provide as much context as possible and describe the *reproduction
  steps* that others can follow to recreate the issue. This may include your
  GitHub repository, probably its `pre-commit-config.yaml`, and definitely your
  `dependabot.yml` file.
- For the best problem reports and fastest fixes, try to isolate the problem
  and create a reduced test case.
- Provide the information you collected in the previous section.
- If you would like to develop a fix for the problem, or already have a
  proposed change, please mention this in the problem report.

Once you have created the issue:

- Someone reviews it, labeling the issue with one of these:
  - 🔴 **bug** – if it's really a Reliabot bug or error
  - ⚪️ **duplicate** – if there's already an issue for this
  - 🔵 **enhancement** – if Reliabot works as intended, but could work better
  - 🔵 **help wanted** – if they aren't sure what to label it
  - ⚪️ **invalid** if this is spam or nonsense or not even a question
  - 🟣 **question** – if it's not a bug, and you should do something differently
  - ⚪️ **wontfix** – if Reliabot is working as intended, and won't change
- They try to reproduce the problem using your provided steps. If there are no
  steps or obvious way to reproduce it, they may ask you for those steps and
  mark the issue as **help wanted** or **invalid**. Until someone can reproduce
  the problem, they won't try to fix it.
- Once they can reproduce the problem, they'll assign it to someone to
  [implement a fix](#becoming-a-contributor). If you indicate interest in
  working on a fix, or that you already have a proposed fix, they may assign it
  to you.

## Suggesting enhancements

This section shows you how to submit an enhancement suggestion for Reliabot,
**including completely new features and minor improvements to existing
capabilities**. Following these guidelines helps others understand your
suggestion and how it relates to other approaches.

### Before suggesting an enhancement

- Make sure you are using the latest Reliabot version.
- Read the [documentation][2] to see if Reliabot can already do what you want.
- [Search the issues][4] to see if somebody already suggested this enhancement.
  If so, add a comment to that existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's
  up to you to make a strong case for the merits of this feature. Keep in mind
  that features should be useful to many users and not just a few of them.

### Writing a good enhancement suggestion

The Reliabot project tracks [enhancement suggestions][10] with GitHub issues.
To suggest an enhancement for Reliabot:

- [Create an issue using the enhancement template][11], labeling it as an 🔵
  **enhancement**.
- Use a **clear and descriptive title** to identify the enhancement.
- Describe any problem the enhancement would solve, and explain how.
- Provide a clear and concise **description of the suggested enhancement**.
- **Describe the current behavior** and **explain the behavior you'd like to
  see instead.** You can also describe alternative solutions that aren't as
  good, and explain why.
- **Explain why this enhancement would be useful** to many reliabot users.

## Becoming a contributor

> #### Legal Notice
>
> By contributing code or documentation to this project, you are certifying,
> per the [Developer Certificate of Origin][12] version 1.1 or later, that you
> have the necessary rights to the content you contribute, and that they allow
> distribution under the [Reliabot project license][13],
>
> You do this by ["signing off" your commits][14]. "Signing off" isn't
> cryptographic, it's just a line like "Signed-off-by: your name
> <your.email@example.org>" at the end of a commit message. You can add it
> manually when squash merging a PR, or by giving the `-s` or `--signoff`
> option to `git commit`.

### First contributions

Unsure where to start contributing? Start by looking at Reliabot issues labeled
[**good first issue**][15] or [**help wanted**][16].

- **good first issue** – should only require a few lines of code and a test.
- **help wanted** – more complex, requiring code design and Python experience.

### Pre-commit setup

Reliabot uses [pre-commit][17] to perform style checks and fixes. Whether you
are contributing code or documentation, you should [install pre-commit][18] on
your system, and then enable it for your local copy of the Reliabot repository:

```console
$ cd reliabot && pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

If you don't (or can't) install pre-commit on your system (say, if you're using
the GitHub file editor in the web UI to fix a small typo), once you create a
PR, the [pre-commit.ci][19] service runs the pre-commit checks for you and
pushes fixes to your PRs for many style / formatting issues. Run `git pull` on
your PR branch after the **pre-commit.ci - pr** checks are no longer pending,
and show either success or failure.

### Contributing code and bug fixes

<!-- TODO include env setup, IDE and typical getting started instructions? -->

### Improving the documentation

The documentation for Reliabot currently consists of a number of Markdown files
in standard locations (README.md, CONTRIBUTING.md, SECURITY.md).

There is configuration and a Makefile for using [Vale][20] for checking prose
style and suggest improvements to the documentation, as well as text in the
GitHub issue templates. There is no CI integration for Vale, you have to
install it yourself:

- `brew install vale` on macOS

Once you have installed Vale, you can run it with `make`.

<!-- TODO: Integrate Vale into a CI pipeline -->

## Style guides

[Pre-commit checks](#pre-commit-setup) cover most of the style guides below,
and often auto-fix style issues, either as local changes in your copy of the
Reliabot repository, or as commits that pre-commit.ci adds to your PR.

### Commit messages

- Limit the first line to 72 or fewer characters.
- Start the first line with a [conventional commit type][21], like these
  examples: `feat:` or `ci(pre-commit):`.
  - _You can use [commitizen][22] or similar tools to help manage this._
- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to…" not "Moves cursor to…").
- Reference issues and pull requests liberally after the first line.

### Python code

Reliabot code uses [Black][22] style formatting. Pre-commit checks enforce this
and some PEP code styles.

### Shell code

Reliabot pre-commit hooks format shell scripts with `shfmt -i 2 -ci`, and lint
them with [`shellcheck`][17].

### Markdown documentation

Reliabot documentation uses GitHub Flavored Markdown, following the
[Markdown style guide][23] implemented by [Executable Books mdformat][24], with
some non-default `mdformat` style settings:

- "Consecutive" numbering for [ordered lists][25] for compatibility with the
  [markdownlint][26] checker, like this:
  ```markdown
  1. first
  2. second
  3. etcetera
  ```
- Word wrapping at 79 columns.
- A pre-commit hook based on a Python script from a [decade-old blog post][27]
  rewrites all [reference links][28] with numeric tags ordered by appearance in
  the text. This doesn't affect inline links like `[shell](#shell-code)`, used
  for any references to anchors in the same file but not anything else.

While these settings don't minimize Git diffs in line-by-line diff mode, they
do maximize readability of the Markdown source files, and the
`--word-diff=color` option for `git diff` generates usable diffs in most cases.

Reliabot uses several `mdformat` plugins to auto-generate tables of contents,
format Markdown tables, and to format code blocks with shell, Python, and
configuration language tags.

### Configuration files

Reliabot uses [Prettier][29] to automatically format CFG, INI, JSON, TOML, and
YAML configuration files. The only non-standard setting is to use single quotes
in preference to double quotes for formats that allow this.

## Attribution

The **contributing-gen** generator created the initial version of this file.
[Make your own CONTRIBUTING.md][30] 📝

[1]: https://github.com/dupuy/reliabot/issues/new
[2]: https://github.com/dupuy/reliabot#reliabot--maintain-github-dependabot-configuration
[3]: https://github.com/dupuy/reliabot#faq
[4]: https://github.com/dupuy/reliabot/issues?q=is%3Aissue+sort%3Aupdated-desc
[5]: https://github.com/dupuy/reliabot/issues/new?assignees=&labels=question&projects=&template=question.md&title=Question+about+...
[6]: https://github.com/dupuy/reliabot/issues?q=label%3Abug
[7]: https://github.com/dupuy/reliabot/security/advisories/new
[8]: https://github.com/dupuy/reliabot/security/policy
[9]: https://github.com/dupuy/reliabot/issues/new?template=problem.md&title=Problem+with+%E2%80%A6
[10]: https://github.com/dupuy/reliabot/issues?q=label%3Aenhancement
[11]: https://github.com/dupuy/reliabot/issues/new?template=enhancement.md&title=Enhancement+to+https://github.com/dupuy/reliabot/issues/new?template=problem.md&title=Problem+with+%E2%80%A6
[12]: https://developercertificate.org/
[13]: https://github.com/dupuy/reliabot/blob/main/LICENSE
[14]: https://stackoverflow.com/a/14044024
[15]: https://github.com/dupuy/reliabot/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22+sort%3Acomments-desc
[16]: https://github.com/dupuy/reliabot/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22+sort%3Acomments-desc
[17]: https://pre-commit.com/
[18]: https://pre-commit.com/#install
[19]: https://pre-commit.ci
[20]: https://vale.sh/
[21]: https://www.conventionalcommits.org/en/v1.0.0/#summary
[22]: https://commitizen-tools.github.io/commitizen/
[23]: https://mdformat.readthedocs.io/en/stable/users/style.html
[24]: https://github.com/executablebooks/mdformat
[25]: https://mdformat.readthedocs.io/en/stable/users/style.html#ordered-lists
[26]: https://github.com/markdownlint/markdownlint
[27]: https://leancrew.com/all-this/2012/09/tidying-markdown-reference-links/
[28]: https://mdformat.readthedocs.io/en/stable/users/style.html#reference-links
[29]: https://prettier.io/docs/en/
[30]: https://github.com/bttger/contributing-gen
