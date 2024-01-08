# Publishing Reliabot

There are currently two ways for people to use Reliabot: as a `pre-commit` hook
or by installing it with Python packaging tools for direct command line use.
Pushing a new main branch tag to GitHub effectively publishes a new Reliabot
version for `pre-commit`, but distributing a new Reliabot version for Python
requires building a new package distribution and uploading it to PyPI.

## Publishing to PyPI

### Publish pre-release to TestPyPI and test it

Use the commands below to create a pre-release, publish it to TestPyPI, and
test that it downloads and installs successfully.

```shell
poetry version prerelease
poetry publish -r test-pypi
python3 -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ reliabot
```

If the preceding commands succeed, you can create a new release with the
commands below:

```shell
BUMP=patch # or minor or major
poetry version "$BUMP"
VERSION=`poetry version | sed 's/reliabot /v/'`
git commit -m "chore: release '$VERSION'"
git push --tags
```

## Bootstrapping GitHub Action workflow as trusted publisher

The Reliabot GitHub repository has GitHub Actions workflows
([`publish.yml`][1]) (and similar `test-publish.yml`) for publishing new
releases without credentials, using ["Trusted Publisher"][2] configuration for
Open ID Connect (OIDC) authentication. You can configure a "pending" publisher
for the project by following the instructions for
[Creating a PyPI Project with a Trusted Publisher][3], or
[Configuring Trusted Publishing][4] in the Python Packaging User Guide. The
latter is part of the overall architecture used for publishing Reliabot to
PyPI.

[1]: https://github.com/dupuy/reliabot/blob/main/.github/workflows/publish.yml
[2]: https://docs.pypi.org/trusted-publishers/
[3]: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
[4]: https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/#configuring-trusted-publishing
