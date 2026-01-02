#!/bin/sh
# The awk | sed pipeline in this shell script is unfortunately too complex.
#
# The awk program extracts ```console code blocks and HTML comments with
# doctest-cli exit status checks ($?=<exit code>) and omits everything else.
# The ! in the HTML comments is escaped in case the shell uses it for history.
#
# The sed program uses three sed commands to process the awk output:
# 1. Two substitutions on lines with prompts ending with $ followed by a space
#    (the two 's' substitutions are grouped with {<cmd>;<cmd>;} syntax):
#    A. /^[^ ]*\$ / selects prompt lines, matching initial non-space to $ space.
#    B. s//>>> / (using an empty regex to reuse the last regex – in A above)
#       replaces the matched prompt with >>> for doctest-cli compatibility.
#    C. s/$/ 2>\&1/ replaces the end of line with (appended) 2>&1 so that
#       all output is on stdout and doctest-cli matches it without ! for stderr.
#       Sed expands & in a replacement to the matched text (empty here), so the
#       command must escape the & here.
# 2. /^```/d' deletes the code block delimiter lines with triple backticks (```)
#    that would otherwise be interpreted by the shell as command substitutions.
# 3. The substitution s/^<\!-- \(\$\?=[1-9][0-9]*\) -->$/\1/ matches $?=<digits>
#    in a regex group within the HTML comment <!-- ... --> markers and replaces
#    the HTML comment with its contents for doctest-cli to check the exit code.
#    Again here the ! is escaped in case the shell uses it for history.
#
# TODO: fork doctest-cli to add Markdown code block and HTML comment extraction
# (and multiple files, smarter prompt string matching, stderr to stdout merging)
# so we can remove this hairy shell pipeline and let doctest-cli do all the work
# in more comprehensible Python code.

grep -l '^```console' "$@" |
  # Ignore any files with newlines in their name. They could be handled safely
  # with find -print0 and xargs -0 re-invoking this script, but not worth it.
  grep '^\./.*\.md$' |
  (
    STATUS=0
    while IFS= read -r mdtest; do
      awk '/^```console$/,/^```$/
          /^<\!-- \$\?=[1-9][0-9]* -->$/' "$mdtest" |
        sed -e '/^[^ ]*\$ /{s//>>> /;s/$/ 2>\&1/;}' \
          -e '/^```/d' \
          -e 's/^<\!-- \(\$\?=[1-9][0-9]*\) -->$/\1/' >"$mdtest.sh"
      PYTHONWARNINGS=default doctest-cli "$mdtest.sh" || STATUS=$?
      rm "$mdtest.sh"
    done
    exit "$STATUS"
  )
exit $?
