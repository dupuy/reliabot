#!/bin/sh
status() {
  gh run list --status "$1" --json url -q '.[].url' | sed 's/$/ '"$1"'/'
}
status action_required
status pending
status waiting
