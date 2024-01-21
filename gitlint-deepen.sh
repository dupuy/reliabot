#!/bin/sh -e
# Script to deepen a shallow copy of a branch back to the trunk so that gitlint
# can run on those commits.
REPO=https://github.com/dupuy/reliabot.git
LIMIT=5 # Number of deepening attempts, increasing depth in Fibonacci sequence
SHALLOW=${GIT_DIR:-.git}/shallow
if [ ! -e "${SHALLOW}" ]; then
  exit
fi
TRUNK=${1:-main}
REFMAP=+refs/heads/$TRUNK:refs/remotes/origin/$TRUNK
git fetch --refmap="$REFMAP" "$REPO" "$TRUNK"
TRUNK=$(git rev-parse "origin/$TRUNK")
GRAFT=$(cat "$SHALLOW")
for DEEPER in $(seq "$LIMIT"); do
  if git log --pretty=format:%H | grep -q "$TRUNK"; then
    exit 0
  fi
  git fetch --deepen="$DEEPER" # Total commit depths: 2 4 7 11 16 21 28 …
  if [ ! -e "$SHALLOW" ]; then
    exit 0
  fi
  DEEPER=$(cat "$SHALLOW")
  if [ "$GRAFT" = "$DEEPER" ]; then
    exit 0
  fi
  GRAFT=$DEEPER
done
exit 0
