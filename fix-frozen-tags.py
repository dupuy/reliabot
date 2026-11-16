#!/usr/bin/env python3
# pylint: disable=invalid-name
"""Verify and fix `# frozen: <tag>` comments on SHA-pinned pre-commit revs.

`pre-commit autoupdate --freeze` writes `rev: <sha>  # frozen: <tag>`, but
pre-commit-update bumps the SHA without updating the tag comment. This script
looks up each pinned SHA's tags on the remote (with `git ls-remote`, no clone)
and rewrites the comment to a tag pointing at that commit.

Usage: fix-frozen-tags.py [--check] [FILE ...]

FILE defaults to .pre-commit-config.yaml. With --check, nothing is written and
the exit status is 1 if any comment is missing, wrong, or unverifiable.
Edits are line-based, so the rest of the file's formatting is left untouched.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from functools import cache

GIT_CMD = "/usr/bin/git" if os.name == "posix" else "git"
GIT_PREFIX = "https://github.com/"

REPO_RE = re.compile(r"^\s*-?\s*repo:\s*['\"]?(?P<repo>[^'\"\s#]+)")
REV_RE = re.compile(
    r"""^(?P<head>\s*-?\s*rev:\s*)
        (?P<q>['"]?)(?P<sha>[0-9a-f]{40})?(?P=q)
        (?P<gap>\s*)
        (?:\#\s*frozen:\s*(?P<tag>\S+))?
        (?P<rest>.*?)$""",
    re.VERBOSE,
)


@cache
def tags_by_commit(url: str) -> dict[str, list[str]]:
    """Map commit SHA -> tag names for a remote, peeling annotated tags."""
    output = subprocess.run(
        [GIT_CMD, "ls-remote", "--tags", url],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    direct: dict[str, str] = {}  # tag -> object the ref points at
    peeled: dict[str, str] = {}  # tag -> commit (annotated tags only)
    for line in output.splitlines():
        sha, ref = line.split("\t", 1)
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            direct[name] = sha
    result: dict[str, list[str]] = {}
    for name, sha in direct.items():
        result.setdefault(peeled.get(name, sha), []).append(name)
    return result


def version_key(tag: str) -> tuple:
    """Sort version parts numerically, pre-releases come first."""
    parts = re.split(r"[.\-+_]", tag.lstrip("vV"))
    key = [(1, int(p), "") if p.isdigit() else (0, 0, p) for p in parts]
    return tuple(key), not re.search(r"(alpha|beta|rc)", tag, re.IGNORECASE)


def pick_tag(candidates: list[str], current: str | None) -> str:
    """Prefer existing tag or matching v-prefix with the highest version."""
    if current in candidates and current is not None:
        return current
    if current:  # keep the same style (`v1.2.3` vs `1.2.3`) if possible
        prefixed = current[:1] in "vV"
        same = [t for t in candidates if (t[:1] in "vV") == prefixed]
        candidates = same or candidates
    return max(candidates, key=version_key)


def update_tag_comments(path: str, *, check: bool) -> bool:
    """Return True if no changes to the file were (or would be) needed."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    ok = True
    changed = False
    is_frozen = False
    unfrozen = {}
    url = None
    for lineno, line in enumerate(lines):
        if repo := REPO_RE.match(line):
            url = repo["repo"]
            continue
        rev = REV_RE.match(line.rstrip("\n"))
        if not rev or url in (None, "local", "meta"):
            continue
        if not rev["sha"]:
            unfrozen[url.removeprefix(GIT_PREFIX)] = rev["rest"]
            continue

        is_frozen = True
        where = f"{path}:{lineno + 1}: {url.removeprefix(GIT_PREFIX)}"
        new_line = resolve_rev(line, rev, url, where)
        if new_line:
            ok = False
            if new_line != line:
                changed = True
            lines[lineno] = new_line

    if changed and not check:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    if unfrozen:
        report_unfrozen(unfrozen, has_frozen=is_frozen)
        ok = False
    return ok


def report_unfrozen(unfrozen: dict[str, str], *, has_frozen: bool) -> None:
    """Generate error output if there are any unfrozen repositories."""
    print(
        f"{'Un' if has_frozen else 'No '}frozen pre-commit checks found!",
        file=sys.stderr,
    )
    if has_frozen:
        for url, tag in unfrozen.items():
            print(f" {url}: {tag}", file=sys.stderr)
    else:
        print("Run `pre-commit autoupdate --freeze` to freeze SHA pins")


def resolve_rev(line: str, rev: re.Match[str], url: str, where: str) -> str:
    """Verify and update the frozen tag comment for a pinned revision line.

    :returns: An empty string if the current line is correct, or a replacement
        (which can be identical if it cannot find a matching tag).
    """
    sha, current = rev["sha"], rev["tag"]
    try:
        candidates = tags_by_commit(url).get(sha, [])
    except subprocess.CalledProcessError as e:
        print(
            f"{where}: git ls-remote failed: {e.stderr.strip()}",
            file=sys.stderr,
        )
        return line

    if not candidates:
        old = current or "without tag"
        print(f"{where} untagged {sha[:7]}, kept {old}", file=sys.stderr)
        return line

    tag = pick_tag(candidates, current)
    if tag == current:
        return ""  # No update necessary, empty string means all OK

    extra = ", ".join(t for t in candidates if t != tag)
    print(
        f"{where}: {sha[:7]} is {tag}"
        + (f", not {current[:7]}" if current else "")
        + (f" (but also: {extra})" if extra else ""),
        file=sys.stderr,
    )
    return format_rev_line(rev, sha, tag)


def format_rev_line(rev: re.Match[str], sha: str, tag: str) -> str:
    """Generate the formatted rev: line with updated tag."""
    gap = rev["gap"] if rev["tag"] else " "  # prefer single-spaced comment
    rest = rev["rest"].lstrip()
    new = f"{rev['head']}{rev['q']}{sha}{rev['q']}{gap}# frozen: {tag}"
    new += f" {rest}\n" if rest else "\n"
    return new


def main() -> int:
    """Parse arguments and update tags (when possible and desired)."""
    docstring_header = (__doc__ or "").split("\n\n", maxsplit=1)[0]
    parser = argparse.ArgumentParser(description=docstring_header)
    parser.add_argument(
        "files", nargs="*", default=[".pre-commit-config.yaml"]
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report inaccuracy without rewriting files",
    )
    args = parser.parse_args()
    results = [update_tag_comments(f, check=args.check) for f in args.files]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
