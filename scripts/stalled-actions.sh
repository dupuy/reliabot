#!/bin/sh
#
# This information is also available at:
#
# https://github.com/dupuy/reliabot/actions?query=is%3Aaction_required%2Cpending%2Cwaiting
#

status() {
  gh run list --status "$1" --json url -q '.[].url' | sed 's/$/ '"$1"'/'
}
status action_required
status pending
status waiting
