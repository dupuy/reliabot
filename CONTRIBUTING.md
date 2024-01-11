# Contributing to Reliabot

🙏Thanks in advance for your contributions ❤️

There are _many_ ways to contribute – one of the best is just using Reliabot
for your projects – and no contribution is too small or too large.

- [Ask a question][1] about using Reliabot.
- [Open an issue][2] about a problem, or for a way to improve Reliabot.
- [Improve the docs][3] by fixing typos and broken links, or writing a HowTo.
- [Write code][4] to add a feature or support for a distribution packager.

See the [Table of contents][5] for different ways to help and details about how
to contribute to Reliabot. _Please read the relevant section before
contributing_. This makes the process easier and improves the experience for
everyone.

👀 Looking forward to your contributions 🎉

> If you use or like the project, but don't have time to contribute, that's OK.
> Here are some easy ways to support Reliabot and show your appreciation.
>
> - Star the Reliabot GitHub project
> - Refer to Reliabot in your project's README
> - Link to Reliabot in social media

## Table of contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=2 -->

- [Table of contents](#table-of-contents)
- [Asking a question](#asking-a-question)
- [Reporting bugs](#reporting-bugs)
  - [Before submitting a bug report](#before-submitting-a-bug-report)
  - [How to submit a good bug report](#how-to-submit-a-good-bug-report)
- [Suggesting enhancements](#suggesting-enhancements)
  - [Before suggesting an enhancement](#before-suggesting-an-enhancement)
  - [Writing a good enhancement issue](#writing-a-good-enhancement-issue)
- [Becoming a contributor](#becoming-a-contributor)
  - [Contributing code and bug fixes](#contributing-code-and-bug-fixes)
  - [Improving the documentation](#improving-the-documentation)
- [Style guides](#style-guides)
  - [Commit messages](#commit-messages)
- [Attribution](#attribution)

<!-- mdformat-toc end -->

## Asking a question

> ℹ️ If you have a Reliabot question, take a look at the [README][6] and its
> [FAQ][7] to see if it's answered there.

Before asking a question, search for [existing issues][8] that are similar. If
you find a relevant issue but still need clarification, ask your question in
that issue. A few internet search queries may also turn up an answer quickly.

If you don't find an answer or an existing issue, follow these steps to ask
your question:

- [Create a new issue][2], labeling it as a 🟣 **question**.
- Provide as much context as you can for your question.
  - Reliabot version
  - Whether you're running Reliabot with pre-commit or on the command line
  - OS type and CPU architecture, and versions for the OS and Python runtime
- Explain what you're trying to do, and what you don't understand.

Someone should respond to the issue as soon as possible. Be patient. 🕗😊

## Reporting bugs

### Before submitting a bug report

A good bug report shouldn't force others to contact you for critical missing
information. Please investigate carefully, find examples and counter-examples,
and describe the problem in detail. Completing the following steps in advance
helps to fix any potential bug as fast as possible.

- Make sure you are using the latest Reliabot version.
- Confirm that your problem is really a bug and not an error on your part, such
  as using Reliabot with unsupported environments or versions. Reading the
  [documentation][6] can help. If you need support, consider just
  [asking a question][1] first.
- To see if other users have experienced (and perhaps already solved) the same
  problem as you, search the [bug tracker][9] for similar issues or error
  messages.
- Searching the internet (especially Stack Overflow) can help you find any
  users of other tools, or in other forums, who have run into a similar
  problem.
- Collect information about the bug:
  - Specific Reliabot command line and context.
  - All error messages and warnings, including stack traces. Setting
    `PYTHONWARNINGS=default` in the environment can show extra diagnostics.
  - OS type and CPU architecture, and versions for the OS and Python runtime
  - Possibly your input and the output
  - Can you reliably reproduce the problem? And can you also reproduce it with
    older Reliabot versions?

### How to submit a good bug report

> Don't report security related issues or vulnerabilities, or include sensitive
> information in reports on the issue tracker, or elsewhere in public. Instead,
> [contact the author by email][10]. If you can encrypt the email using
> [their public key][11], or chat using Keybase, that's even better.

The Reliabot project uses [GitHub issues][8] for tracking bugs. If you found a
problem using Reliabot:

- [Create an issue][2]. At first, it may not be clear whether it's a bug, so
  please don't label the issue.
- Describe the behavior you expect and the differences in the actual behavior.
- Please provide as much context as possible and describe the *reproduction
  steps* that others can follow to recreate the issue. This may include your
  GitHub repository, probably its `pre-commit-config.yaml`, and definitely your
  `dependabot.yml` file.
- For the best bug reports and fastest fixes, try to isolate the problem and
  create a reduced test case.
- Provide the information you collected in the previous section.
- If would like to develop a fix for the bug, or already have a proposed
  change, please mention this in the bug report.

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
  [implement a fix][12]. If you indicated interest in working on a fix, or that
  you already have a proposed fix, they may assign it to you.

<!--  TODO: create an issue template for bugs to provide the necessary information -->

## Suggesting enhancements

This section shows you how to submit an enhancement suggestion for Reliabot,
**including completely new features and minor improvements to existing
capabilities**. Following these guidelines helps others understand your
suggestion and how it relates to other approaches.

### Before suggesting an enhancement

- Make sure you are using the latest Reliabot version.
- Read the [documentation][6] carefully and see if the feature is already
  provided
- [Search the issues][8] to see if somebody already suggested this enhancement.
  If so, add a comment to that existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's
  up to you to make a strong case for the merits of this feature. Keep in mind
  that features should be useful to the majority of users and not just a small
  subset.

### Writing a good enhancement issue

The Reliabot project tracks [enhancement suggestions][13] with GitHub issues.
To suggest an enhancement for Reliabot:

- [Create an issue][2], labeling it as an 🔵 **enhancement**.
- Use a **clear and descriptive title** to identify the enhancement.
- Provide a **step-by-step description of the suggested enhancement** with as
  many details as possible.
- **Describe the current behavior** and **explain which behavior you expected
  to see instead** and why. You can also describe alternatives that don't work
  for you.
- You may want to **include screenshots** to demonstrate the steps or show
  details of the enhancement.
- **Explain why this enhancement would be useful** to most reliabot users. You
  may also want to point out other projects that solved it better and which
  could serve as inspiration.

<!-- TODO: create an issue template for enhancement suggestions -->

## Becoming a contributor

> #### Legal Notice
>
> By contributing code or documentation to this project, you certify, per the
> [Developer Certificate of Origin][14] version 1.1 or later, that you have the
> necessary rights to the content you contribute, and that they allow
> distribution under the [Reliabot project license][15],

### Contributing code and bug fixes

<!-- TODO include env setup, IDE and typical getting started instructions? -->

### Improving the documentation

<!-- TODO
Updating, improving and correcting the documentation

-->

## Style guides

### Commit messages

<!-- TODO

-->

## Attribution

The **contributing-gen** generator created the initial version of this file.
[Make your own CONTRIBUTING.md][16] 📝

[1]: #asking-a-question
[2]: https://github.com/dupuy/reliabot/issues/new
[3]: #improving-the-documentation
[4]: #contributing-code-and-bug-fixes
[5]: #table-of-contents
[6]: https://github.com/dupuy/reliabot#reliabot--maintain-github-dependabot-configuration
[7]: https://github.com/dupuy/reliabot#faq
[8]: https://github.com/dupuy/reliabot/issues?q=is%3Aissue
[9]: https://github.com/dupuy/reliabot/issues?q=label%3Abug
[10]: mailto:alex@dupuy.us
[11]: https://keybase.io/dupuy
[12]: #becoming-a-contributor
[13]: https://github.com/dupuy/reliabot/issues?q=label%3Aenhancement
[14]: https://developercertificate.org/
[15]: https://github.com/dupuy/reliabot/blob/main/LICENSE
[16]: https://github.com/bttger/contributing-gen
