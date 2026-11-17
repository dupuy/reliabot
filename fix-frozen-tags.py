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

Edits are line-based, so the rest of the file's formatting is left untouched,
but YAML that's invalid or doesn't follow the pre-commit schema may be mangled.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import cache
from re import Match
from typing import ClassVar
from warnings import warn_explicit

GIT_CMD = "/usr/bin/git" if os.name == "posix" else "git"
GITHUB_PREFIX = "https://github.com/"

REPO_RE = re.compile(r"^\s*-?\s*repo:\s*['\"]?(?P<repo>[^'\"\s#]+)")
REV_RE = re.compile(
    r"""^(?P<head>\s*-?\s*rev:\s*)
        (?P<q>['"]?)(?P<sha>[0-9a-f]{7,80})?(?P=q)
        (?P<gap>\s*)
        (?:\#\s*frozen:\s*(?P<tag>\S+))?
        (?P<rest>.*?)$""",
    re.VERBOSE,
)


@cache
def tags_by_commit(url: str) -> dict[str, set[str]]:
    """Map commit SHA -> tag names for a remote, peeling annotated tags."""
    git_cmd_args = (GIT_CMD, "ls-remote", "--tags", url)
    try:
        git_cmd = subprocess.run(
            git_cmd_args,
            capture_output=True,
            check=True,
            shell=False,
            text=True,
            timeout=5,  # seconds
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as spe:
        print(" ".join(git_cmd_args), file=sys.stderr)
        print(spe.stderr, file=sys.stderr)
        raise

    output = git_cmd.stdout
    direct: dict[str, str] = {}  # tag -> object the ref points at
    peeled: dict[str, str] = {}  # tag -> commit (annotated tags only)
    for line in output.splitlines():
        sha, ref = line.split("\t", 1)
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            direct[name] = sha
    result: dict[str, set[str]] = {}
    for name, sha in direct.items():
        # if the name is also in peeled, prefer that commit SHA
        result.setdefault(peeled.get(name, sha), set()).add(name)
        if sha not in result:  # "direct" unpeeled SHA was not used, add it too
            result[sha] = {name, "@"}  # mark annotated tag SHA with @
    return result


def version_key(tag: str) -> tuple:
    """Sort version parts numerically, pre-releases come first."""
    parts = re.split(r"[.\-+_]", tag.lstrip("vV"))
    key = [(1, int(p), "") if p.isdigit() else (0, 0, p) for p in parts]
    return tuple(key), not re.search(r"(alpha|beta|rc)", tag, re.IGNORECASE)


def pick_tag(candidates: set[str], current: str | None) -> str:
    """Prefer existing tag or matching v-prefix with the highest version."""
    if current in candidates and current is not None:
        return current
    if current:  # keep the same style (`v1.2.3` vs `1.2.3`) if possible
        prefixed = current[:1] in "vV"
        same = {t for t in candidates if (t[:1] in "vV") == prefixed}
        candidates = same or candidates
    return max(candidates, key=version_key)


@dataclass
class WarnArgs:
    """Class to generate warnings for pre-commit-config.yaml errors."""

    file: str
    lineno: int
    warn_type: ClassVar[type[Warning]] = UserWarning

    def __init__(self, file: str, lineno: int) -> None:
        """Initialize WarnArgs with the given file and line number."""
        self.file = file
        self.lineno = lineno

    def warning(self, message: str) -> None:
        """Print a warning message."""
        warn_explicit(message, self.warn_type, self.file, self.lineno)


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
        repo_name = url.removeprefix(GITHUB_PREFIX).removeprefix("https://")
        sha = rev["sha"]
        if sha is None:
            unfrozen[repo_name] = rev["rest"]
            continue
        warn_args = WarnArgs(path, lineno + 1)
        if len(sha) != 40:
            warn_args.warning(f"{sha[:7]} isn't 40 chars")
            continue

        is_frozen = True
        new_line = fix_rev(line, rev, url, warn_args)
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
            print(f"  {url}: {tag}", file=sys.stderr)
    else:
        print("Run `pre-commit autoupdate --freeze` to freeze SHA pins")


def fix_rev(line: str, rev: Match[str], url: str, warn_args: WarnArgs) -> str:
    """Verify and update the frozen tag comment for a pinned revision line.

    :returns: An empty string if the current line is correct, or a replacement
        (which can be identical if it cannot find a matching tag).
    """
    sha, current = rev["sha"], rev["tag"]
    try:
        tag_map = tags_by_commit(url)
    except subprocess.SubprocessError:
        return line
    except OSError as e:
        print(e.strerror, file=sys.stderr)
        return line

    candidates = tag_map.get(sha, set())
    if not candidates:
        old = current or "without tag"
        warn_args.warning(f"untagged {sha[:7]}, kept {old}")
        return line

    tag = pick_tag(candidates, current)
    if "@" in candidates:  # the SHA is for the annotated tag, not the commit
        improve = f"{sha[:7]} is tag, use commit"
        better = "SHA"
        for pin, tags in tag_map.items():
            if tag in tags and "@" not in tags:
                better = pin
                break
        warn_args.warning(f"{improve} {better}")

    if tag == current:
        return ""  # No update necessary, empty string means all OK

    extra = ", ".join(t for t in candidates if t not in (tag, "@"))
    if current or extra:
        warn_args.warning(
            f"{sha[:7]} is {tag}"
            + (f", not {current[:7]}" if current else "")
            + (f" (but also: {extra})" if extra else "")
        )
    return format_rev_line(rev, sha, tag)


def format_rev_line(rev: Match[str], sha: str, tag: str) -> str:
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
