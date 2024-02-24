# Contributing to Reliabot

🙏Thanks in advance for your contributions ❤️

There are _many_ ways to contribute – one of the best is just using Reliabot
for your projects. [Open an issue][4] if you have a problem, or if you think of
a way to improve Reliabot. Fix a typo or broken URL in the docs, or add support
for a software distribution packager – no contribution is too small or large.

See the [Table of contents][1] for different ways to help and details about how
this project handles them. _Please read the relevant section before
contributing_. This makes it easier for the team and improves the experience
for everyone.

👀 Looking forward to your contributions 🎉

> If you use or like the project, but don't have time to contribute, that's OK.
> Here are some easy ways to support Reliabot and show your appreciation.
>
> - Star the Reliabot GitHub project
> - Refer to Reliabot in your project's README
> - Mention Reliabot in social media

## Table of contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=2 -->

- [Table of contents](#table-of-contents)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Legal Notice](#legal-notice)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
  - [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)
- [Attribution](#attribution)

<!-- mdformat-toc end -->

## I Have a Question

> If you want to ask a question, we assume that you have read the available
> [Documentation][2].

Before you ask a question, it is best to search for existing [Issues][3] that
might help you. In case you have found a suitable issue and still need
clarification, you can write your question in this issue. It is also advisable
to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we
recommend the following:

- Open an [Issue][4].
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (nodejs, npm, etc), depending on what
  seems relevant.

We will then take care of the issue as soon as possible.

<!--
You might want to create a separate issue tag for questions and include it in this description. People should then tag their issues accordingly.

Depending on how large the project is, you may want to outsource the questioning, e.g. to Stack Overflow or Gitter. You may add additional contact and information possibilities:
- IRC
- Slack
- Gitter
- Stack Overflow tag
- Blog
- FAQ
- Roadmap
- E-Mail List
- Forum
-->

## I Want To Contribute

> ### Legal Notice
>
> When contributing to this project, you must agree that you have authored 100%
> of the content, that you have the necessary rights to the content and that
> the content you contribute may be provided under the project license.

### Reporting Bugs

#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more
information. Therefore, we ask you to investigate carefully, collect
information and describe the issue in detail in your report. Please complete
the following steps in advance to help us fix any potential bug as fast as
possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g.
  using incompatible environment components/versions (Make sure that you have
  read the [documentation][2]. If you are looking for support, you might want
  to check [this section][5]).
- To see if other users have experienced (and potentially already solved) the
  same issue you are having, check if there is not already a bug report
  existing for your bug or error in the [bug tracker][6].
- Also make sure to search the internet (including Stack Overflow) to see if
  users outside of the GitHub community have discussed the issue.
- Collect information about the bug:
  - Stack trace (Traceback)
  - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  - Version of the interpreter, compiler, SDK, runtime environment, package
    manager, depending on what seems relevant.
  - Possibly your input and the output
  - Can you reliably reproduce the issue? And can you also reproduce it with
    older versions?

#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs
> including sensitive information to the issue tracker, or elsewhere in public.
> Instead sensitive bugs must be sent by email to \<>.

<!-- You may add a PGP key to allow the messages to be sent encrypted as well. -->

We use GitHub issues to track bugs and errors. If you run into an issue with
the project:

- Open an [Issue][4]. (Since we can't be sure at this point whether it is a bug
  or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction
  steps* that someone else can follow to recreate the issue on their own. This
  usually includes your code. For good bug reports you should isolate the
  problem and create a reduced test case.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will try to reproduce the issue with your provided steps. If
  there are no reproduction steps or no obvious way to reproduce the issue, the
  team will ask you for those steps and mark the issue as `needs-repro`. Bugs
  with the `needs-repro` tag will not be addressed until they are reproduced.
- If the team is able to reproduce the issue, it will be marked `needs-fix`, as
  well as possibly other tags (such as `critical`), and the issue will be left
  to be [implemented by someone][7].

<!-- You might want to create an issue template for bugs and errors that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for
reliabot, **including completely new features and minor improvements to
existing functionality**. Following these guidelines will help maintainers and
the community to understand your suggestion and find related suggestions.

#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation][2] carefully and find out if the functionality is
  already covered, maybe by an individual configuration.
- Perform a [search][3] to see if the enhancement has already been suggested.
  If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's
  up to you to make a strong case to convince the project's developers of the
  merits of this feature. Keep in mind that we want features that will be
  useful to the majority of our users and not just a small subset. If you're
  just targeting a minority of users, consider writing an add-on/plugin
  library.

#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues][3].

- Use a **clear and descriptive title** for the issue to identify the
  suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as
  many details as possible.
- **Describe the current behavior** and **explain which behavior you expected
  to see instead** and why. At this point you can also tell which alternatives
  do not work for you.
- You may want to **include screenshots and animated GIFs** which help you
  demonstrate the steps or point out the part which the suggestion is related
  to. You can use [this tool][8] to record GIFs on macOS and Windows, and
  [this tool][9] on Linux.
      <!-- this should only be included if the project has a GUI -->
- **Explain why this enhancement would be useful** to most reliabot users. You
  may also want to point out the other projects that solved it better and which
  could serve as inspiration.

<!-- You might want to create an issue template for enhancement suggestions that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->

### Your First Code Contribution

<!-- TODO
include Setup of env, IDE and typical getting started instructions?

-->

### Improving The Documentation

<!-- TODO
Updating, improving and correcting the documentation

-->

## Styleguides

### Commit Messages

<!-- TODO

-->

## Join The Project Team

<!-- TODO -->

## Attribution

This guide is based on the **contributing-gen**. [Make your own][10]!

[1]: #table-of-contents
[2]: https://github.com/dupuy/reliabot/blob/main/README.md
[3]: https://github.com/dupuy/reliabot/issues
[4]: https://github.com/dupuy/reliabot/issues/new
[5]: #i-have-a-question
[6]: https://github.com/dupuy/reliabot/issues?q=label%3Abug
[7]: #your-first-code-contribution
[8]: https://www.cockos.com/licecap/
[9]: https://github.com/colinkeenan/silentcast
[10]: https://github.com/bttger/contributing-gen
