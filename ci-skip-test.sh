#!/bin/sh
# Check that wide-scope CI skip directives in a commit message cannot reach the
# release commit message, where GitHub would honor them and disable all checks
# on the release PR. See "Git commit messages" in CONTRIBUTING.md.
#
# Two independent layers neutralize the directives, and this script tests both:
#
# 1. The git-cliff commit_preprocessors entry in pyproject.toml, which rewrites
#    the directives while generating changelog entries and release notes.
# 2. The $(NO_CI_SKIP) sed expression in the `release` Makefile recipe, which
#    rewrites them again while building the release commit message. This script
#    reads that expression out of the Makefile, so it tests what really runs.
#
# Both layers must defang the directive rather than drop it (so that the
# changelog still records what the commit said), and both must leave the
# focused directives that CONTRIBUTING.md recommends alone.

set -eu

REPO=$(git rev-parse --show-toplevel)
WORK=$(mktemp -d)
# shellcheck disable=SC2064 # expand WORK now, while it is still set
trap "rm -rf '$WORK'" 0

# The five skip directives GitHub Actions honors, plus case, separator and
# padding variants, one commit subject per line.
cat >"$WORK/skipped" <<'EOF'
fix: no ci first [no ci]
fix: skip ci next [skip ci]
fix: ci skip reversed [ci skip]
fix: skip actions too [skip actions]
fix: actions skip as well [actions skip]
fix: shouting is honored [SKIP CI]
fix: so are other separators [Skip-CI]
fix: and padding [ ci_skip ]
EOF

# Focused directives, which CONTRIBUTING.md recommends and both layers keep.
cat >"$WORK/kept" <<'EOF'
fix: one workflow only [skip test-coverage]
fix: one service only [skip pre-commit.ci]
EOF

# git-cliff ignores a pyproject.toml outside the repository it is scanning, so
# copy the real configuration into a throwaway repository of synthetic commits.
cp "$REPO/pyproject.toml" "$WORK/pyproject.toml"
cd "$WORK"
git init -q .
git config user.email 'reliabot@example.com'
git config user.name 'Reliabot Test'
cat skipped kept | while IFS= read -r subject; do
  git commit -q --allow-empty -m "$subject"
done

GITHUB_TOKEN=XX git-cliff --offline --config pyproject.toml --tag v9.9.9 >notes

NO_CI_SKIP=$(sed -n 's/^NO_CI_SKIP=//p' "$REPO/Makefile")
if [ -z "$NO_CI_SKIP" ]; then
  echo "ci-skip-test.sh: no NO_CI_SKIP expression in $REPO/Makefile" >&2
  exit 1
fi
# Run the Makefile expression over the raw subjects, not over the git-cliff
# output, so that this layer is tested even when the other one already worked.
sed -E -e "$NO_CI_SKIP" skipped >sedded
sed -E -e "$NO_CI_SKIP" kept >sedded-kept

STATUS=0

# Deliberately not the expression under test: any bracketed pair of the four
# keywords is a wide-scope directive, however it is spelled or separated.
DIRECTIVE='\[[ _-]*(no|skip|actions|ci)[ _-]+(no|skip|actions|ci)[ _-]*\]'

check_neutralized() { # $1: file of processed text, $2: name of the layer
  if grep -Ein "$DIRECTIVE" "$1"; then
    echo "FAIL: $2 left the CI skip directives shown above" >&2
    STATUS=1
  elif ! grep -Eq '\(skip ci\)$' "$1"; then
    echo "FAIL: $2 did not rewrite '[skip ci]' as exactly '(skip ci)'" >&2
    STATUS=1
  fi
}

check_focused_kept() { # $1: file of processed text, $2: name of the layer
  for focused in '[skip test-coverage]' '[skip pre-commit.ci]'; do
    if ! grep -Fq "$focused" "$1"; then
      echo "FAIL: $2 rewrote the focused directive '$focused'" >&2
      STATUS=1
    fi
  done
}

check_neutralized notes 'git-cliff commit_preprocessors in pyproject.toml'
check_focused_kept notes 'git-cliff commit_preprocessors in pyproject.toml'
check_neutralized sedded 'NO_CI_SKIP sed expression in the Makefile'
check_focused_kept sedded-kept 'NO_CI_SKIP sed expression in the Makefile'

exit "$STATUS"
