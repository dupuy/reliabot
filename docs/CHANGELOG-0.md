# Changelog

This file documents notable changes to Reliabot.

It uses the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format,
and follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for
releases.

## [Unreleased]

### Details

#### Added

- Add gitleaks pre-commit checking by @dupuy in
  [#57](https://github.com/dupuy/reliabot/pull/57)
- Add CODEOWNERS by @dupuy in [#55](https://github.com/dupuy/reliabot/pull/55)

#### Changed

- Pre-commit hook for tidy numbering & ordering of Markdown reference links by
  @dupuy in [#35](https://github.com/dupuy/reliabot/pull/35)
- Add @drdrang as reviewer for tidy-md-refs.py by @dupuy in
  [#65](https://github.com/dupuy/reliabot/pull/65)
- Cleanup checks and workflows by @dupuy in
  [#60](https://github.com/dupuy/reliabot/pull/60)
- Workflow files by @dupuy in [#59](https://github.com/dupuy/reliabot/pull/59)
- StepSecurity Bot <bot@stepsecurity.io> by @step-security-bot in
  [#56](https://github.com/dupuy/reliabot/pull/56)
- CodeQL & OpenSSF scorecard + best practices badges by @dupuy in
  [#53](https://github.com/dupuy/reliabot/pull/53)
- Create ossf-scorecard.yaml workflow by @dupuy
- Expand CONTRIBUTING.md by @dupuy in
  [#23](https://github.com/dupuy/reliabot/pull/23)
- Switch order of poetry lock and poetry check
- Update Google styles for Vale by @dupuy in
  [#45](https://github.com/dupuy/reliabot/pull/45)
- Ignore length error on pre-commit.ci auto update by @dupuy in
  [#44](https://github.com/dupuy/reliabot/pull/44)
- Replace many pre-commit checks/etc. with ruff by @dupuy in
  [#38](https://github.com/dupuy/reliabot/pull/38)

#### Fixed

- Codeql.yaml cron string by @dupuy in
  [#64](https://github.com/dupuy/reliabot/pull/64)
- Self-test from module wrapper __main__ by @dupuy in
  [#47](https://github.com/dupuy/reliabot/pull/47)

## New Contributors

- @step-security-bot made their first contribution in
  [#56](https://github.com/dupuy/reliabot/pull/56)

## [0.1.2] - 2024-02-06

### Details

#### Added

- Add first GH workflow (stale) by @dupuy in
  [#13](https://github.com/dupuy/reliabot/pull/13)

#### Changed

- Rewrite Makefile for installing tools by @dupuy in
  [#42](https://github.com/dupuy/reliabot/pull/42)
- Reformat for CI by @dupuy in [#40](https://github.com/dupuy/reliabot/pull/40)
- Use pre-commit-shfmt downloading hook by @dupuy in
  [#36](https://github.com/dupuy/reliabot/pull/36)
- Docs: improve issue templates by @dupuy in
  [#34](https://github.com/dupuy/reliabot/pull/34)
- Create Placeholder for CONTRIBUTING.md by @dupuy in
  [#33](https://github.com/dupuy/reliabot/pull/33)
- Configure gitlint (for CI as well) by @dupuy in
  [#31](https://github.com/dupuy/reliabot/pull/31)
- Improve doctest-cli wrapper by @dupuy in
  [#26](https://github.com/dupuy/reliabot/pull/26)
- Explain reliabot options and verify console examples by @dupuy in
  [#25](https://github.com/dupuy/reliabot/pull/25)
- Provide better error when ruamel.yaml isn't available by @appills in
  [#18](https://github.com/dupuy/reliabot/pull/18)
- Vale configuration with vocabulary accept list by @dupuy in
  [#19](https://github.com/dupuy/reliabot/pull/19)

#### Fixed

- Apply many improvements suggested by ruff checks by @dupuy in
  [#39](https://github.com/dupuy/reliabot/pull/39)
- Better gitlint configuration by @dupuy in
  [#32](https://github.com/dupuy/reliabot/pull/32)
- Generate required schedule.interval for updates by @dupuy in
  [#22](https://github.com/dupuy/reliabot/pull/22)
- Handle no comments in dependabot.yml by @dupuy in
  [#21](https://github.com/dupuy/reliabot/pull/21)
- Provide better warning when re2 isn't available by @dupuy in
  [#20](https://github.com/dupuy/reliabot/pull/20)

## New Contributors

- @appills made their first contribution in
  [#18](https://github.com/dupuy/reliabot/pull/18)

## [0.1.1] - 2024-01-04

### Details

#### Added

- Add FAQ section to README.md by @dupuy in
  [#3](https://github.com/dupuy/reliabot/pull/3)

#### Changed

- v0.1.0 reliabot script by @dupuy

#### Fixed

- Ignore dotfiles for terraform by @dupuy in
  [#11](https://github.com/dupuy/reliabot/pull/11)
- Refactor to use Exclusions for kept folders too by @dupuy in
  [#10](https://github.com/dupuy/reliabot/pull/10)
- Don't use re2 for configuration file patterns by @dupuy
- Correctly remove dependabot configurations and truncate by @dupuy
- Resolve PyCharm warnings by @dupuy
- Handle no argument passed to main by @dupuy
- Repair buggy fixes by @dupuy in
  [#9](https://github.com/dupuy/reliabot/pull/9)
- Ignore dotfiles like .tflint.hcl by @dupuy in
  [#7](https://github.com/dupuy/reliabot/pull/7)
- Resolve TypeError: main() missing … 'argv' by @dupuy in
  [#6](https://github.com/dupuy/reliabot/pull/6)
- Fallback to re if re2 not present by @dupuy in
  [#2](https://github.com/dupuy/reliabot/pull/2)

<!-- generated by git-cliff on 2024-03-05 -->

[0.1.1]: https://github.com/dupuy/reliabot/compare/v0.1.0..v0.1.1
[0.1.2]: https://github.com/dupuy/reliabot/compare/v0.1.1..v0.1.2
[unreleased]: https://github.com/dupuy/reliabot/compare/v0.1.2..HEAD