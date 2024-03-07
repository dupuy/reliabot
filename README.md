[![pre-commit enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/dupuy/reliabot/main.svg)](https://results.pre-commit.ci/latest/github/dupuy/reliabot/main)
[![Python build workflow status](https://img.shields.io/github/actions/workflow/status/dupuy/reliabot/python-app.yaml)](https://github.com/dupuy/reliabot/actions/workflows/python-app.yaml)
[![CodeQL status](https://github.com/dupuy/reliabot/workflows/CodeQL/badge.svg)](https://github.com/dupuy/reliabot/security/)

[![OpenSSF scorecard](https://api.securityscorecards.dev/projects/github.com/dupuy/reliabot/badge)](https://securityscorecards.dev/viewer/?uri=github.com/dupuy/reliabot)
[![OpenSSF best practices](https://www.bestpractices.dev/projects/8459/badge)](https://www.bestpractices.dev/projects/8459)
![PyPI Version](https://img.shields.io/pypi/v/reliabot)
[![GitHub Release](https://img.shields.io/github/v/release/dupuy/reliabot)](https://github.com/dupuy/reliabot/releases)

[![GitHub License](https://img.shields.io/github/license/dupuy/reliabot)](LICENSE)
![GitHub repository size](https://img.shields.io/github/repo-size/dupuy/reliabot)
![GitHub repository file+folder count](https://img.shields.io/github/directory-file-count/dupuy/reliabot)
![Lines of code](https://img.shields.io/tokei/lines/github/dupuy/reliabot)
![Lines of code](https://tokei.rs/b1/github/dupuy/reliabot)
![GitHub top language](https://img.shields.io/github/languages/top/dupuy/reliabot)

# Reliabot – Maintain Dependabot configuration

Reliabot is a tool that helps maintain Dependabot configurations in your GitHub
repository. This is especially helpful for [Terraform][1] “Infrastructure as
Code” repositories or any sort of "mono-repo" with many folders that may
require version updates.

> [_Quis renovatores ipsos renovat?_][2] :octocat:🤖🧑🏽‍🔧

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=2 -->

- [Usage](#usage)
  - [Examples](#examples)
- [Installation](#installation)
  - [From PyPI for direct use](#from-pypi-for-direct-use)
  - [As a `pre-commit` hook](#as-a-pre-commit-hook)
- [Pre-commit hook](#pre-commit-hook)
  - [Using with other pre-commit checks](#using-with-other-pre-commit-checks)
- [Reliabot script](#reliabot-script)
  - [Options](#options)
- [FAQ](#faq)
  - [Does Reliabot work with Renovate?](#does-reliabot-work-with-renovate)
  - [Can you install Reliabot with Homebrew?](#can-you-install-reliabot-with-homebrew)
  - [Can Reliabot generate a PR to update Dependabot configuration?](#can-reliabot-generate-a-pr-to-update-dependabot-configuration)
- [Configuring Reliabot behavior](#configuring-reliabot-behavior)
  - [Keeping Dependabot configuration](#keeping-dependabot-configuration)
  - [Ignoring directories for Reliabot](#ignoring-directories-for-reliabot)
  - [Reliabot directory matching](#reliabot-directory-matching)
  - [Indentation](#indentation)
  - [Suppressing YAML start markers](#suppressing-yaml-start-markers)
  - [YAML version](#yaml-version)
- [Reliabot configuration summary](#reliabot-configuration-summary)

<!-- mdformat-toc end -->

GitHub's [Dependabot][3] can [automatically update dependency versions][4] in
your GitHub repositories. Enabling version updates requires a `dependabot.yml`
configuration file in your repository. While creating this file isn't so hard,
in a large repository with multiple applications or types of code, it’s easy to
forget to keep the `dependabot.yml` configuration file up to date with newly
added or removed code.

The `reliabot` Python script and its pre‑commit hook can automatically maintain
Dependabot configurations, adding and removing entries in `dependabot.yml` as
you add or remove code in your repository.

You can run Reliabot directly to create a `dependabot.yml` configuration file
for your GitHub repository, but it's most convenient to run the reliabot hook
from the [pre‑commit][5] framework, or optionally, with the [pre-commit.ci][6]
continuous integration service.

## Usage

The `reliabot` script takes one argument: a Git repository path, and creates or
updates the `dependabot.yml` configuration file for the repository based on the
files tracked in Git, including both committed and staged files.

```console
reliabot$ ./reliabot/reliabot.py
Usage: reliabot.py [--re] --update | [--] GIT_REPO
(use '--' if GIT_REPO starts with '-', or see script source)
```

<!-- $?=2 -->

### Examples

Here is the console output from running Reliabot on its own source sub-folder
to create a new configuration:

```console
reliabot$ rm -fr reliabot/.github && mkdir -p reliabot/.github reliabot/.git

reliabot$ ./reliabot/reliabot.py reliabot
Creating 'reliabot/.github/dependabot.yml'...
reliabot$ cat reliabot/.github/dependabot.yml
---
version: 2
updates:
  - directory: /
    package-ecosystem: pip
    schedule:
        interval: monthly
```

Here is the console output from running Reliabot to update an existing
configuration in its own source sub-folder (copied from the root folder):

```console
reliabot$ rm -fr reliabot/.github && mkdir -p reliabot/.github reliabot/.git

reliabot$ grep -v keep= .github/dependabot.yml >reliabot/.github/dependabot.yml

reliabot$ ./reliabot/reliabot.py reliabot
Removed obsolete 'github-actions' entry in '/'
Updating 'reliabot/.github/dependabot.yml'...
reliabot$ cat -n reliabot/.github/dependabot.yml
 1	---
 2	# reliabot: mapping=4 offset=2 sequence=4
 3	# reliabot: ignore=./reliabot # already tracked in repository root
 4	# reliabot: ignore=testdir/
 5	version: 2
 6	updates:
 7	  - directory: /
 8	    package-ecosystem: pip
 9	    schedule:
 10	        interval: daily
```

## Installation

### From PyPI for direct use

Use `pip3` to install the `reliabot` Python script on your system or
virtualenv.

```shell
pip3 install reliabot
```

#### Installing with RE2

You can improve the reliability and performance of Reliabot, and prevent
warning messages, by installing a Python RE2 regular expression package. These
require installation of the C++ RE2 library (run `brew install re2`, or use
Linux/BSD tools to install the `re2` package).

> ⚠️The `re2-wheels` extra (which depends on [pyre2-updated][7]) only works for
> Python 3.7 to 3.12. If you have to use another Python version and the `pyre2`
> extra doesn't work, use the [`--re` option][8] to turn off warnings about
> failure to load `re2`.

```shell
pip3 install 'reliabot[re2-wheels]'
```

Alternately, you can try the original `pyre2` to build from source. This
requires you to have installed a C++ compiler, header files, and libraries.

```shell
pip3 install 'reliabot[re2]'
```

Once installed, you can add the Python binary directory to your `PATH`.

### As a `pre-commit` hook

> Note: installation from PyPI is _not_ required for use as a `pre‑commit`
> hook. The `pre‑commit` command takes care of installing Reliabot in a Python
> virtual environment for executions from Git hooks or the `pre‑commit`
> command.

The [pre‑commit documentation][9] has detailed instructions for installing and
configuring `pre‑commit`. After you:

1. install `pre‑commit`,

2. add a `.pre‑commit-config.yaml` configuration, for example by running:

   ```shell
   pre-commit sample-config > .pre-commit-config.yaml
   ```

   and

3. install the Git hooks for your repository,

add the following to the `repos` entry in `.pre‑commit‑config.yaml`
([Installing with RE2][10] explains the motivation for the
`additional_dependencies` line, which also requires the C++ RE2 library):

```yaml
  - repo: https://github.com/dupuy/reliabot
    rev: v0.1.1 # Specify any revision you want
    hooks:
      - id: reliabot
        additional_dependencies: [pyre2-updated] # or just `pyre2` or omit this
```

After that, Reliabot runs automatically on any Git commit that involves
`dependabot.yml` or files where Dependabot could update their dependencies.

## Pre-commit hook

After installing and configuring pre‑commit with a Reliabot entry, you can run
Reliabot with `pre-commit run --all reliabot`. You'll rarely need to do so,
since any Git commit that could require an update to the Dependabot
configuration should invoke Reliabot automatically.

### Using with other pre-commit checks

If you also configure a YAML checker in `.pre-commit-config.yaml`, it should
come before Reliabot. And if you configure a YAML formatter, it should come
after Reliabot. Pre-commit processes all hooks in the order they appear in the
configuration, and this order provides the best results:

1. YAML checker
2. Reliabot
3. YAML formatter

## Reliabot script

### Options

- `--re` – As the first argument, this option disables any attempt to use RE2,
  along with error or warning messages when those attempts fail.

- `--self-test`– As the only argument this runs the `doctest` unit tests.

- `--update` – As the only argument, this runs `reliabot` on the current
  directory, returning exit code 4 if it made any changes to the file.

## FAQ

### Does Reliabot work with Renovate?

No. [Renovate][11] detects all supported dependency information in repositories
and manages them unless `packageRules` configure it to ignore them, so Reliabot
isn't needed. As [Renovate configuration][12] is quite complex, creating a tool
to manage that would be challenging.

### Can you install Reliabot with Homebrew?

There is no [Homebrew][13] formula for Reliabot yet, but any contributions for
one are welcome. To install it for the command line, use `pip`, `poetry` or any
other Python package manager. If you only use it for `pre-commit` checks, you
don't need to install anything, just add it to `.pre-commit-config.yaml`.

### Can Reliabot generate a PR to update Dependabot configuration?

Generally, it's better to update the Dependabot configuration in the same PR
that makes dependency management changes, so Reliabot just makes changes that
you can add to the current PR. The pre-commit.ci continuous integration service
does that if you configure Reliabot in `.pre-commit-config.yaml`. A GitHub
Action could create a separate PR, and any contributions for such an action are
also welcome.

## Configuring Reliabot behavior

Reliabot uses the `ruamel.yaml` parser to read and write `dependabot.yml`,
preserving comments when updating it. You can add YAML comments starting with
`# reliabot:` to configure Reliabot and `ruamel.yaml` settings when updating
Dependabot configuration.

> ⚠️**Important**: Reliabot only checks comments _after_ any explicit “document
> start” line (`‑‑‑`) and _before_ the first line with YAML data, such as
> `version: 2`.

### Keeping Dependabot configuration

If Reliabot removes your Dependabot configuration for a directory for any
reason, such as a new package ecosystem it doesn't yet support, you can prevent
that by adding a Reliabot comment with `keep=`_directory_ to `dependabot.yml`,
as in this example:

```
---
# reliabot: keep=example_dir
version: 2
```

This keeps Reliabot from removing any Dependabot configuration for
`example_dir`. To also keep Reliabot from removing configuration in
subdirectories of `example_dir`, use `keep=example_dir/`. To keep Reliabot from
removing _any_ Dependabot configuration in your repository, use `keep=/`.

> ⭐️**Note**: A "keep" comment doesn't prevent Reliabot from _adding_
> Dependabot configuration for the directory.

### Ignoring directories for Reliabot

If Reliabot generates Dependabot configuration entries for directories that you
don't want Dependabot to update, you can prevent this by adding a Reliabot
comment with `ignore=`_directory_ to `dependabot.yml`:

```
# reliabot: ignore=testdir/example
```

> ⚠️**Important**: Reliabot **removes** any existing Dependabot configuration
> for ignored directories unless you turn that off with a matching "keep"
> comment, like the following:

```
# reliabot: ignore=archive/ keep=archive/
```

This prevents Reliabot from modifying any Dependabot configuration for
directories in or under the `archive` directory.

> ⭐️**Note**: You can put Reliabot settings on separate lines or together.
> Reliabot combines multiple `ignore` and `keep` settings, ignoring or keeping
> all matched directories.

### Reliabot directory matching

In addition to the special meaning of trailing `/`, Reliabot directory matching
supports some other special cases:

- The path `*` matches all subdirectories but not the root.
- The path `.` matches the root directory only.
- The path `/` matches all directories.
- Paths ending in `*` match as a prefix, but not exactly.
- Paths ending in `/*` match subdirectories only.
- Paths ending in `/` match the directory and all subdirectories.

Full details are in [the implementation][14].

### Indentation

Reliabot modifies the `ruamel.yaml` indentation settings to generate Dependabot
configuration that's mostly compatible with the `prettier` formatter. If you
prefer a different style, you can change the indentation with Reliabot comments
modifying `ruamel.yaml`’s `mapping`, `offset`, and `sequence` settings:

```
---
# reliabot: mapping=4
# reliabot: offset=2 sequence=4
```

> ⭐️**Note**: When configuring indentation settings, choose values so that
> `sequence` > `offset` or Reliabot may fail.

The `ruamel.yaml` indentation settings are hard to explain or understand, but
this reformatted copy of an example from GitHub Docs may help:

```
# reliabot: mapping=9 offset=4 sequence=7
# Use `allow` to specify which dependencies to maintain

version: 2
updates:
    -  package-ecosystem: npm
       directory: /
       schedule:
                interval: weekly
       allow:
      # Allow updates for Lodash
           -  dependency-name: lodash
      # Allow updates for React and any packages starting "react"
           -  dependency-name: react*
```

- `offset` sets the indent for the `-` sequence indicator under `updates`:

  ```
  ⎵⎵⎵⎵-  package-ecosystem: npm
  ```

- `sequence` sets the indent for the values in the `updates` sequence,
  including the first item:

  ```
  ⎵⎵⎵⎵-⎵⎵package-ecosystem: npm
  ⎵⎵⎵⎵⎵⎵⎵directory: /
  ```

- `mapping` sets the indent for the values in the `schedule` mapping:

  ```
         schedule:
         ⎵⎵⎵⎵⎵⎵⎵⎵⎵interval: weekly
  ```

If any indentation setting appears more than once, Reliabot uses the last one.

> ⚠️**Important**: Indentation settings are **ignored** for comment lines,
> which keep whatever indentation they already had. If you change indentation
> settings, you may have to correct the indentation of comments, manually or
> with a YAML formatter. This is one reason YAML formatters in your
> `.pre-commit-config.yaml` should come _after_ Reliabot.

If you need more control of the formatting of your `.pre‑commit-config.yaml`
configuration file, this is best done by configuring pre-commit to use a
formatter like [prettier][15], the [Golang version of `yamlfmt`][16], or the
[Python version of `yamlfmt`][17] (which also uses `ruamel.yaml` and its
undocumented configuration settings for formatting).

> ⛔️**Warning**: Some combinations of indentation values can generate invalid
> YAML output that `ruamel.yaml` can't parse. Reliabot checks that it can parse
> the updated `dependabot.yml` contents; if not, it doesn't update the file and
> instead fails with an exit code of 3, printing an error message like the
> following:
>
> ```
> YAML (indent?) error: {'mapping': 2, 'offset': 2, 'sequence': 2}:
> while parsing a block collection ...
> ```

### Suppressing YAML start markers

YAML files can have a [“document start” line][18] with three hyphens (`---`)
before the YAML content of the file. This marks the start of a YAML document.
Although YAML checkers may complain if it's missing, it isn't required.
Reliabot adds this line to `dependabot.yml` if you leave it out—if that's a
problem, you can have Reliabot remove it instead, by adding a Reliabot comment
like the following at the start of `dependabot.yml`:

Reliabot always removes YAML “document end” lines with three dots (`...`) at
the end of a `dependabot.yml` file as these files have no reason to use one.

```
# reliabot: yaml-start=off
```

If the YAML start setting appears more than once, Reliabot uses the last one.

### YAML version

The `ruamel.yaml` parser [follows the YAML 1.2 specification][19], but if you
need to use YAML 1.1 features you can do so by specifying the YAML version
before the document start marker, like this:

```
%YAML 1.1
---
```

## Reliabot configuration summary

| Comment tag        | Affects           | Repeats  | Notes                    |
| ------------------ | ----------------- | :------: | ------------------------ |
| `ignore`=_path_    | adding entries    |  Append  | ignores `/` at start/end |
| `keep`=_path_      | removing entries  |  Append  | ignores `/` at start/end |
| `mapping`=_int_    | mapping indent    | Override | int>0 (default 4)        |
| `offset`=_int_     | seq. mark indent  | Override | int≥0 (default 2)        |
| `sequence`=_int_   | seq. value indent | Override | int>`offset` (default 4) |
| `width`=_int_      | line width wrap   | Override | + indent? (default 80)   |
| `yaml-start`=`off` | initial `---`     | Override | or `false`/`true` (`on`) |

[1]: https://www.terraform.io/use-cases/infrastructure-as-code
[2]: https://translate.google.com/?sl=la&tl=en&text=Quis%20renovatores%20ipsos%20renovat%3F&op=translate
[3]: https://docs.github.com/en/code-security/dependabot
[4]: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates
[5]: https://pre-commit.com/
[6]: https://pre-commit.ci/
[7]: https://pypi.org/project/pyre2-updated
[8]: #options
[9]: https://pre-commit.com/#quick-start
[10]: #installing-with-re2
[11]: https://docs.renovatebot.com/
[12]: https://docs.renovatebot.com/configuration-options
[13]: https://brew.sh/
[14]: https://github.com/search?q=repo%3Adupuy%2Freliabot%20%20Exclusions.add&type=code
[15]: https://prettier.io/docs/en/precommit#option-2-pre-commithttpsgithubcompre-commitpre-commit
[16]: https://github.com/google/yamlfmt
[17]: https://github.com/jumanjihouse/pre-commit-hook-yamlfmt
[18]: https://www.yaml.info/learn/document.html#start
[19]: https://yaml.readthedocs.io/en/latest/pyyaml/#defaulting-to-yaml-12-support
