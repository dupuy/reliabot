#!/bin/sh
set -e

if command -v npm >/dev/null 2>&1; then
  prefix=$(npm config get prefix)
  export PATH="${PATH}:${prefix}/bin"
fi

if ! command -v markdown-link-check >/dev/null 2>&1; then
  echo >&2 "markdown-link-check is not available on this system."
  echo >&2 "Please install it by running 'npm install -g markdown-link-check'"
  exit 1
fi

TMP_CONFIG="$(mktemp)"
trap 'rm -f "$TMP_CONFIG";' EXIT

cat >"$TMP_CONFIG" <<EOF
{
  "aliveStatusCodes": [200, 403, 429],
  "httpHeaders": [
    {
      "urls": [
        "https://apple.stackexchange.com/",
        "https://serverfault.com/",
        "https://stackexchange.com/",
        "https://stackoverflow.com/",
        "https://superuser.com/",
        "https://unix.stackexchange.com/"
      ],
      "headers": {
        "User-Agent": "markdown-link-check/reliabot"
      }
    }
  ],
  "replacementPatterns": [
    {
      "pattern": "^/",
      "replacement": "file://$(pwd)/"
    }
  ],
  "retryCount": 1,
  "retryOn429": true
}
EOF

for file in "$@"; do
  markdown-link-check -c "$TMP_CONFIG" "$file"
done

exit 0
