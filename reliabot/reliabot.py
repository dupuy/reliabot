#!/usr/bin/env python3
# pylint: disable=too-many-lines # > 1000
"""Reliabot - maintain GitHub Dependabot configuration.

This creates and updates Dependabot configuration for a Git repository.

Exit status codes are defined in the Err enumeration class below.

Use `--self-test` argument to run doctests. This creates additional directories
in the `testdir` hierarchy that cannot be added to the Git repository:

>>> _ = isdir("testdir/badlink/.git") or os.mkdir("testdir/badlink/.git")
>>> _ = isdir("testdir/configured/.git") or os.mkdir("testdir/configured/.git")
>>> _ = isdir("testdir/git") or os.mkdir("testdir/git")
>>> _ = isdir("testdir/git/.git") or os.mkdir("testdir/git/.git")
>>> _ = isdir("testdir/github/.git") or os.mkdir("testdir/github/.git")
>>> _ = isdir("testdir/not-git") or os.mkdir("testdir/not-git")
>>> _ = isdir("testdir/worktree") or os.mkdir("testdir/worktree")
>>> if not exists("testdir/worktree/.git"):
...     with open("testdir/worktree/.git", "w", encoding="utf-8") as wt_git:
...         print("gitdir: ../git/.git", file=wt_git)
>>> _ = isdir("testdir/worktree-bad-prefix") or os.mkdir(
...     "testdir/worktree-bad-prefix"
... )
>>> if not exists("testdir/worktree-bad-prefix/.git"):
...     with open(
...         "testdir/worktree-bad-prefix/.git", "w", encoding="utf-8"
...     ) as wt_bad:
...         print("not-a-gitdir-line", file=wt_bad)
>>> _ = isdir("testdir/worktree-missing") or os.mkdir(
...     "testdir/worktree-missing"
... )
>>> if not exists("testdir/worktree-missing/.git"):
...     with open(
...         "testdir/worktree-missing/.git", "w", encoding="utf-8"
...     ) as wt_miss:
...         print("gitdir: ../does-not-exist", file=wt_miss)
>>> if os.path.islink("testdir") and os.readlink("testdir") == "../testdir/":
...     _ = isdir(".git") or os.mkdir(".git")
"""

from __future__ import annotations

import _thread
import argparse
import contextlib
import os

# noinspection unused-imports
import re  # noqa: TC003  # init_regex_engine() may re-bind to re2
import signal
import subprocess
import sys
import tempfile
import threading
import traceback
import warnings
from collections import defaultdict
from contextvars import Context, ContextVar
from enum import IntEnum
from io import SEEK_SET, StringIO
from os.path import (
    basename,
    dirname,
    exists,
    isabs,
    isdir,
    join,
    normpath,
    split,
)
from typing import IO, TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Iterator
    from types import FrameType


class Err(IntEnum):
    """Error exit codes for reliabot."""

    RUNTIME = 1  # Nonexistent or inappropriate repository path.
    USAGE = 2  # dead:disable # argparse errors
    CONFIG = 3  # Invalid Dependabot (or pre-commit) configuration in file.
    UPDATED = 4  # Dependabot configuration was or would be modified.
    INTERNAL = 9  # You found a bug in this program!


class TimeLimitError(Exception):
    """Exception raised when a time limit is exceeded."""


def error(message: str, *, debug_hint: bool = True) -> None:
    """Report a bug (internal error) in reliabot and exit with status 9.

    :param message: Information about the internal error.
    :param debug_hint: Whether to suggest --self-test for debugging.
    >>> os.environ[DOCTEST_OPT] = ""
    >>> error("testing error reporting")
    Traceback (most recent call last):
    ...
    SystemExit: 9
    """
    dedup_warn(f"Internal error - {message}")
    if DOCTEST_OPT in os.environ or sys.argv[len(sys.argv) - 1] != DOCTEST_OPT:
        if debug_hint:
            print(f"Debug with {sys.argv[0]} {DOCTEST_OPT}", file=sys.stderr)
        sys.exit(int(Err.INTERNAL))


def dedup_warn(message: str, key: str | None = None) -> None:
    r"""Print warning to stderr if non-empty key has not been warned before.

    These stderr messages for end-users do not use Python Warnings, which are
    intended for developers.

    Keys are only de-duplicated within a `warning_scope()` (`main()` makes one
    for each run). Outside a scope, or with no key (or an empty one), every
    message is printed.

    :param message: message to print to stderr.
    :param key: de-duplication key: only warns first instance of key value.

    >>> err = StringIO()
    >>> with contextlib.redirect_stderr(err), warning_scope():
    ...     dedup_warn("A", "k")
    ...     dedup_warn("B", "k")  # Same key, so not printed.
    ...     dedup_warn("C", "other")
    ...     dedup_warn("D")  # No key, always printed.
    ...     dedup_warn("E")
    >>> err.getvalue()
    'A\nC\nD\nE\n'
    >>> err = StringIO()  # No de-duplication outside a scope or across scopes.
    >>> with contextlib.redirect_stderr(err):
    ...     dedup_warn("F", "k")
    ...     dedup_warn("G", "k")
    ...     with warning_scope():
    ...         dedup_warn("H", "k")
    ...     with warning_scope():
    ...         dedup_warn("I", "k")
    >>> err.getvalue()
    'F\nG\nH\nI\n'
    """
    # WARN_KEYS may not exist yet if error() is called during import.
    if key and (warned := WARN_KEYS.get(None)) is not None:
        if key in warned:
            return
        warned.add(key)
    print(message, file=sys.stderr)


@contextlib.contextmanager
def warning_scope() -> Generator[None]:
    """Run a block in which `dedup_warn()` remembers the keys it has seen.

    Each scope starts with no keys, so one run's warnings never suppress
    another's in the same process (tests, fuzzing, other callers of `main()`).

    >>> WARN_KEYS.get(None) is None
    True
    >>> with warning_scope():
    ...     WARN_KEYS.get(None)
    set()
    >>> WARN_KEYS.get(None) is None
    True
    """
    token = WARN_KEYS.set(set())
    try:
        yield
    finally:
        WARN_KEYS.reset(token)


@contextlib.contextmanager
def time_limit(seconds: float) -> Generator[None]:
    """Context manager to raise TimeLimitError after *seconds* seconds.

    For portability, uses signal.setitimer() and signal.SIGALRM on POSIX systems,
    and _thread.interrupt_main() to raise KeyboardInterrupt on others.
    Because of this, it only works in the main thread.

    Timeouts may be blocked in certain system calls or other situations, see
    https://github.com/python/cpython/issues/80719 for one example.

    :param seconds: number of seconds after which to raise TimeLimitError.

    >>> import time
    >>> with time_limit(0.2):  # doctest: +IGNORE_EXCEPTION_DETAIL
    ...     # Busy loop to ensure interruption
    ...     end = time.time() + 1.0
    ...     while time.time() < end:
    ...         pass  # busy loop since may not interrupt sleep() call
    Traceback (most recent call last):
    ...
    reliabot.TimeLimitError: ...
    """
    # TODO: use https://pypi.org/project/stopit/ to support non-main thread
    if threading.current_thread() != threading.main_thread():
        not_main_thread = "Timelimit context manager only works in main thread"
        raise NotImplementedError(not_main_thread)

    timeout_error = f"Exceeded time limit of {seconds} seconds"
    if hasattr(signal, "setitimer"):

        def handler(_signum: int, _frame: FrameType | None) -> None:
            raise TimeLimitError(timeout_error)

        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)

    else:
        timer = threading.Timer(seconds, _thread.interrupt_main)
        timer.start()
        try:
            yield
        except KeyboardInterrupt:
            if not timer.is_alive():
                raise TimeLimitError(timeout_error) from None
            raise
        finally:
            timer.cancel()


# "GLOBAL_CONSTANTS" are initialized only once (not always where declared)
# but they appear in this file in LANG=C sorted order, This can be verified
# with the following commands that should return an empty diff:
#
# $ grep -E '^[A-Z_0-9]+(:| =)' reliabot/reliabot.py > "/tmp/G$$"
# $ LANG=C sort /tmp/G > "/tmp/Gs$$"
# $ diff /tmp/G "/tmp/Gs$$"

COMMENT_PREFIX = "# reliabot:"
COMMENT_PREFIX_MATCH: re.Pattern  # Compiled by init_regex_engine().

DEFAULT_INTERVAL = "monthly"

DEPENDABOT_CONFIG = b"dependabot.yml"

DOCTEST_OPT = "--self-test"  # Command line option for running doctests.
DOCTEST_OPTION_FLAGS = 0  # Modified by init_regex_engine() on re.error.

DOT_YAML = r"[.]ya?ml"
DOT_YAML_RE: re.Pattern  # Search, not match; compiled by init_regex_engine().


# Based on dependabot-core; replace GITHUB_ACTIONS with ecosystem in this URL:
# https://github.com/search?q=org:dependabot+path:GITHUB_ACTIONS+required_files_message&type=code
# to find the relevant code, and see the current list of package ecosystems at:
# https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file#package-ecosystem
# More ecosystem support (including beta ones) and filenames can be seen at
# https://github.com/search?q=org:dependabot+required_files_message&type=code,
# which also shows ones whose source folders don't match their names, like
# https://github.com/search?q=org:dependabot+path:GIT_SUBMODULES+required_files_message&type=code

ECOS = {  # Final overall pattern wraps each RE in a group named by the key.
    "bundler": r"gem(s[.]rb|file)|[\w.-]*[.]gemspec",
    "cargo": r"cargo[.]toml",
    "composer": r"composer[.]json",
    "docker": rf"(?i:[\w.-]*dockerfile[\w.-]*|values[\w.-]*{DOT_YAML})",
    "elm": r"elm(-package)?[.]json",
    "github_actions": r"action[.]yml",  # hyphen (-) not allowed in group name.
    "gitsubmodule": r"[.]gitmodules",
    "gomod": r"go[.]mod",
    "gradle": r"build[.]gradle([.]kts)?",
    "hex": r"mix[.]exs",
    "maven": r"pom[.]xml",
    "npm": r"package[.]json",
    "nuget": r"nuget[.]config",
    "pip": r"requirements[.]txt|pyproject[.]toml",
    "pub": r"pubspec[.]yaml",
    "terraform": r"\w[\w.-]*[.](?:hcl|tf)",
}
# Combine regexes into pre-commit file pattern
ECOSYSTEM_FILE_ACTIONS = f"[.]github/workflows/[^/]*{DOT_YAML}"
ECOSYSTEM_FILE_DEPENDABOT = "[.]github/dependabot[.]yml"
ECOSYSTEM_FILE_PATTERNS = [
    *ECOS.values(),
    ECOSYSTEM_FILE_ACTIONS,
    ECOSYSTEM_FILE_DEPENDABOT,
]
ECOSYSTEM_INDENT = "\n  "
ECOSYSTEM_JOIN = f"|{ECOSYSTEM_INDENT}"
ECOSYSTEM_PATHS_RE = (
    f"(?x)(^|/)({ECOSYSTEM_INDENT}"
    + ECOSYSTEM_JOIN.join(ECOSYSTEM_FILE_PATTERNS)
    + f"{ECOSYSTEM_INDENT})$"
)

ECOSYSTEM_RE: re.Pattern  # See init_regex_engine() below.

# Convert regexes to named groups with ecosystem names.
ECOSYSTEM_RE_GROUPS = {k: f"(?P<{k}>{v})" for k, v in ECOS.items()}
ECOSYSTEM_RE_MATCHER = "|".join(ECOSYSTEM_RE_GROUPS.values())

EMITTER_INDENTS = {"mapping": 4, "offset": 2, "sequence": 4}
EMITTER_SETTINGS: dict = EMITTER_INDENTS | {"width": 76, "yaml-start": True}
EXCLUSIONS: dict[str, set[str]] = {"ignore": set(), "keep": set()}

FS_ENCODING = sys.getfilesystemencoding()

GITDIR_PREFIX = b"gitdir:"  # Marks a `.git` *file* in a Git worktree.

GITHUB = b".github"
GITHUB_ACTIONS = b"github-actions"
GITHUB_DEPENDABOT = join(GITHUB, DEPENDABOT_CONFIG)
GITHUB_WORKFLOWS = join(GITHUB, b"workflows")

GIT_CMD = "/usr/bin/git" if os.name == "posix" else "git"
GIT_DIR = b".git"
GIT_LS = [GIT_CMD, "ls-files"]

NLSP = "\n "

OPT_INSECURE = "--insecure"  # To follow symlinks on update.
OPT_UPDATE = "--update"  # For pre-commit, returning Err.UPDATE on changes.
OPT_UPDATE_PRE_COMMIT = "--update-pre-commit"  # To update pre-commit configs.

PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"
PRE_COMMIT_HOOKS = ".pre-commit-hooks.yaml"

PURE = True  # Use pure Python parser

RE_INITIALIZED = False  # Set by init_regex_engine() once it has run.
RE_OPTION = "--re"
RE_WARNING = f"""

  Reliabot works better with the 're2' regular expression package.
  See https://github.com/dupuy/reliabot/#installation for install instructions,
  or use initial '{RE_OPTION}' option to force system 're' and suppress this.
"""

RUAMEL_YAML_NOT_FOUND_ERROR_MESSAGE = """

  Reliabot requires ruamel.yaml to preserve comments in dependabot.yml files.
  See https://github.com/dupuy/reliabot/#installation for install instructions.
"""
try:
    # ruamel.yaml preserves comments, PyYAML doesn't.
    from ruamel.yaml import YAML
except ModuleNotFoundError as module_not_found:
    error(
        f"{module_not_found} {RUAMEL_YAML_NOT_FOUND_ERROR_MESSAGE}",
        debug_hint=False,
    )
else:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    from ruamel.yaml.error import YAMLError
    from ruamel.yaml.parser import ParserError
    from ruamel.yaml.reader import ReaderError

SECURE_MAX_MODE = 0o666  # Maximum file mode (rw-rw-rw-) unless --insecure

TESTDIR = b"testdir"  # dead:disable
TEST_CONFIGURED = b"configured"  # dead:disable
TEST_GIT = b"git"  # dead:disable
TEST_GITHUB = b"github"  # dead:disable
TEST_NOT_DIR = b"not-dir"  # dead:disable
TEST_NOT_GIT = b"not-git"  # dead:disable
TEST_WORKTREE = b"worktree"  # dead:disable
TEST_WORKTREE_BAD_PREFIX = b"worktree-bad-prefix"  # dead:disable
TEST_WORKTREE_MISSING = b"worktree-missing"  # dead:disable

TRUTHY = {"false": 0, "off": 0, "on": 1, "true": 1}

U_FFFC = "\ufffc"  # Unicode object replacement character

# De-duplication keys already warned about in the current run (a set made by
# warning_scope(), unset outside any scope); the ContextVar itself is constant.
WARN_KEYS: ContextVar[set[str]] = ContextVar("WARN_KEYS")


# pylint: disable=global-statement,import-outside-toplevel
def init_regex_engine(
    *, force_re: bool = False, self_testing: bool = False
) -> None:
    """Select the regular expression engine and compile this module's regexes.

    Deferred from import time to avoid side effects. `main()` calls this first;
    multiple calls are harmless. External callers that don't run main() must
    call this function first, before any reliabot functions that use regexes,
    or any attempt to use the compiled regular expressions.

    Uses the 're2' package if it can be imported, unless *force_re* is true.

    :param force_re: use the system 're' without trying 're2' (`--re` option).
    :param self_testing: running the self-test, so a regex failure is diagnosed by
        the tests rather than exiting (`--self-test` option).

    >>> init_regex_engine(force_re=True, self_testing=True)
    >>> RE_INITIALIZED and ECOSYSTEM_RE is not None
    True
    """
    # noinspection global-undefined
    global re, RE_INITIALIZED  # noqa: PLW0603
    global COMMENT_PREFIX_MATCH  # noqa: PLW0603
    global DOT_YAML_RE, ECOSYSTEM_RE  # noqa: PLW0603
    global DOCTEST_OPTION_FLAGS  # noqa: PLW0603

    if RE_INITIALIZED:
        return
    RE_INITIALIZED = True

    if not force_re:
        try:  # to avoid terrible consequences for pathological RE matching.
            # noinspection unused-imports
            import re2  # noqa: PLC0415
        except ImportError:
            dedup_warn(
                f"Can't import 're2', falling back to 're'.{RE_WARNING}"
            )
        else:  # Generate fallback warning if re2 package can't handle regexp
            re2.set_fallback_notification(re2.FALLBACK_WARNING)
            re = re2

    COMMENT_PREFIX_MATCH = re.compile(rf"\s*{COMMENT_PREFIX}")
    DOT_YAML_RE = re.compile(rf"{DOT_YAML}$")
    try:  # It's easy to mess up the regexes. Don't let it break the self test.
        ECOSYSTEM_RE = re.compile(ECOSYSTEM_RE_MATCHER)
    except re.error:  # pragma: no cover
        print("Internal error - bad regex in ECOS map", file=sys.stderr)
        if not self_testing:
            print(
                f"  Diagnose with {sys.argv[0]} {DOCTEST_OPT}", file=sys.stderr
            )
            sys.exit(int(Err.INTERNAL))
        # pylint: disable-next=import-outside-toplevel
        import doctest  # noqa: PLC0415

        # Reduce noise from broken tests
        DOCTEST_OPTION_FLAGS = doctest.FAIL_FAST


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command line arguments and options, in any order.

    Invalid arguments or option combinations exit with status 2 (`Err.USAGE`).

    :param argv: command name and arguments.
    :returns: namespace with `force_re`, `insecure`, `command` (None, or one of
        `OPT_UPDATE`, `OPT_UPDATE_PRE_COMMIT` or `DOCTEST_OPT`) and `git_repo`.

    >>> parse_args(["reliabot.py", "--insecure", "--re", "repo"])
    Namespace(force_re=True, insecure=True, command=None, git_repo='repo')
    >>> parse_args(["reliabot.py", "--", "-repo"]).git_repo
    '-repo'
    >>> parse_args(["reliabot.py", "--re", OPT_UPDATE]).command
    '--update'
    >>> parse_args(["reliabot.py", "--insecure", OPT_UPDATE]).insecure
    True
    >>> parse_args(["reliabot.py", DOCTEST_OPT, "--re"]).command
    '--self-test'
    >>> for bad in (
    ...     [],  # No repository.
    ...     ["repo", "repo2"],  # Too many arguments.
    ...     ["--unknown", "repo"],  # Unknown option.
    ...     ["--self_test"],  # Unknown option, with a hint to use dashes.
    ...     ["--update", DOCTEST_OPT],  # Mutually exclusive commands.
    ...     [OPT_UPDATE_PRE_COMMIT, DOCTEST_OPT],
    ...     [DOCTEST_OPT, "--insecure"],  # Internal command with an option.
    ... ):
    ...     try:
    ...         parse_args(["reliabot.py", *bad])
    ...     except SystemExit as exit_err:
    ...         print(exit_err.code)
    2
    2
    2
    2
    2
    2
    2
    """
    parser = argparse.ArgumentParser(
        prog=basename(argv[0]),
        usage=(
            "%(prog)s [-h] [--re] [--insecure]\n"
            "       [--update | --self-test] [--] [GIT_REPO]"
        ),
        description="Create or update Dependabot configuration in a Git repo.",
        epilog="Use '--' before GIT_REPO if its name starts with '-'.",
        allow_abbrev=False,  # Don't match --update as an abbreviation of others.
    )
    parser.add_argument(
        RE_OPTION,
        dest="force_re",
        action="store_true",
        help="use the system 're' package instead of trying 're2'",
    )
    parser.add_argument(
        OPT_INSECURE,
        action="store_true",
        help="follow symlinks and write the configuration file in place",
    )
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument(
        OPT_UPDATE,
        dest="command",
        action="store_const",
        const=OPT_UPDATE,
        help="exit code 4 if modified; GIT_REPO defaults to current directory",
    )
    commands.add_argument(
        OPT_UPDATE_PRE_COMMIT,
        dest="command",
        action="store_const",
        const=OPT_UPDATE_PRE_COMMIT,
        help=argparse.SUPPRESS,  # update patterns in .pre-commit-config.yaml
    )
    commands.add_argument(
        DOCTEST_OPT,
        dest="command",
        action="store_const",
        const=DOCTEST_OPT,
        help="run the self-diagnostics (doctests)",
    )
    parser.add_argument(
        "git_repo",
        metavar="GIT_REPO",
        nargs="?",
        help="path of the Git repository (parent of the '.git' directory)",
    )

    args, unknown = parser.parse_known_args(argv[1:])
    if unknown:
        msg = f"unrecognized arguments: {' '.join(unknown)}"
        for arg in unknown:
            if arg.startswith("-") and "_" in arg:  # an easy error to make
                msg += f"\n  Did you mean '{arg.replace('_', '-')}' (dashes)?"
        parser.error(msg)
    if args.command is None:
        if args.git_repo is None:
            parser.error("GIT_REPO is required")
    elif args.command != OPT_UPDATE and args.git_repo is not None:
        parser.error(f"{args.command} does not take a GIT_REPO argument")
    elif args.command != OPT_UPDATE and args.insecure:
        parser.error(f"{args.command} cannot be used with {OPT_INSECURE}")
    return args


def main(optargv: list[str] | None = None) -> int:
    """Create or update Dependabot configuration in a Git repo.

    This function parses arguments and options and handles exceptions,
    calling other functions to do the real work.

    :param optargv: command name and arguments.
    :returns: exit code – 0 for success, 1–9 for different failures.

    >>> sys.argv = ["--"]
    >>> main()
    Traceback (most recent call last):
    ...
    SystemExit: 2
    >>> main(
    ...     ["reliabot.py", OPT_UPDATE]
    ... )  # Updated dependabot config required,
    0
    >>> main(["reliabot.py", OPT_UPDATE_PRE_COMMIT])  # also pre-commit config.
    0
    >>> test_dir = "testdir/github/"
    >>> test_conf = f"{test_dir}/.github/{fsdecode(DEPENDABOT_CONFIG)}"
    >>> if exists(test_conf):
    ...     os.unlink(test_conf)
    >>> os.chdir(test_dir)
    >>> main(["reliabot.py", OPT_UPDATE])
    4
    >>> os.chdir("../..")
    >>> if exists(test_conf):
    ...     os.unlink(test_conf)
    >>> WARN_KEYS.get(None) is None  # No de-duplication state outlives a run.
    True
    """
    with warning_scope():
        return _run(optargv)


# FIXME: Too many branches (22/15) Ruff limit is 12
# FIXME: Too many local variables (32/15) Ruff limit is >=32 ?
# FIXME: Too many return statements (10/6)
# FIXME: Too many statements (97/60) Ruff limit is 50 but counts 92 statements
# pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements
def _run(optargv: list[str] | None) -> int:
    """Implement `main()` (see there) inside its warning scope."""
    modified = False
    update_status = "Updating"
    conf: CommentedMap | dict = {}

    args = parse_args(list(optargv or sys.argv))
    # Regex setup needs the parsed options, so it can't be done any sooner.
    init_regex_engine(
        force_re=args.force_re, self_testing=args.command == DOCTEST_OPT
    )
    if args.command in X_OPTION_MAP:
        return X_OPTION_MAP[args.command]()
    check = args.command == OPT_UPDATE
    secure = not args.insecure

    if not sys.warnoptions:
        warnings.simplefilter("ignore")

    repo_dir = (args.git_repo or ".").encode(FS_ENCODING, "surrogatepass")
    dconf = join(repo_dir, GITHUB_DEPENDABOT)
    d_name = fsdecode(dconf)

    action = "read"
    new = False
    try:
        check_git_repository(repo_dir)  # Necessary for git ls-files to work.
        try:
            conf = load_dependabot_config(dconf)
        except (FileNotFoundError, NotADirectoryError) as missing_err:
            if exists(missing_err.filename):
                raise
            update_status = "Creating"
            new = True
        except (
            NotImplementedError,  # comment handling corner cases
            ReaderError,  # empty (or short?) strings
            ValueError,  # unparsable numerics (like ".")
            YAMLError,  # many invalid YAML cases
        ) as ruamel_err:
            err_msg = (
                ruamel_err.args[0]
                if (ruamel_err.args and ruamel_err.args[0] is not None)
                else getattr(ruamel_err, "problem", None) or "Invalid YAML"
            )
            dedup_warn(err_msg)
            return Err.CONFIG
        except AssertionError:
            # AssertionError raised when unable to move old comment
            dedup_warn("YAML parser unable to track comments for this file")
            return Err.CONFIG
        except IndexError:
            # IndexError raised from an empty string for processing version
            dedup_warn("Configuration parse error (bad YAML version?)")
            return Err.CONFIG
        except RecursionError:
            # RecursionError can occur when there is an anchor loop
            dedup_warn("Configuration parse error (YAML anchor loop?)")
            return Err.CONFIG
        except TypeError:
            # TypeError occurs if top-level is unhashable, like CommentedSeq
            dedup_warn("Configuration parse error (bad top level?)")
            return Err.CONFIG

        settings = extract_settings(
            conf, EMITTER_SETTINGS | {key: set() for key in EXCLUSIONS}
        )

        exclude = configure_exclusions(settings)

        ecosystems = find_ecosystems(repo_dir, exclude.matcher("ignore"))

        if update_dependabot_config(conf, ecosystems, exclude.matcher("keep")):
            modified = True
            action = "write"
            dedup_warn(f"{update_status} '{d_name}'...")
            if secure:
                temp_dir = dirname(dconf) or b"."
                temp_path = None
                try:
                    # py < 3.14: https://github.com/python/cpython/issues/66305
                    with time_limit(2.0):
                        fd, temp_path = tempfile.mkstemp(
                            dir=temp_dir,
                            prefix=b".reliabot-",
                            suffix=b".tmp",
                        )
                    with open(fd, "w", encoding="utf-8") as dfile:
                        safe_dump(conf, settings, dfile)
                    try:
                        orig_mode = os.stat(dconf).st_mode & SECURE_MAX_MODE
                    except OSError:  # probably file doesn't exist yet
                        current_umask = os.umask(0o177)  # securest sane umask
                        os.umask(current_umask)  # restore original umask fast
                        orig_mode = SECURE_MAX_MODE & ~current_umask
                    os.chmod(temp_path, orig_mode)
                    os.replace(temp_path, dconf)
                except BaseException as exc:
                    err = str(exc)
                    if temp_path is not None and exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except OSError:
                            tmp_name = fsdecode(temp_path)
                            dedup_warn(f"Failed to remove '{tmp_name}'")
                    dedup_warn(
                        f"Could not securely {action} '{d_name}':{NLSP}{err}"
                    )
                    dedup_warn("Fix permissions or try with --insecure")
                    raise
            else:
                mode = "w+" if new else "r+"
                with open(dconf, mode, encoding="utf-8") as dfile:
                    safe_dump(conf, settings, dfile)
    except (OSError, TimeLimitError) as os_exc:
        if isinstance(os_exc, OSError):
            d_name = fsdecode(os_exc.filename)
            err = f"{os_exc.strerror or 'OS Error'}"
        else:
            err = type(os_exc).__name__
        dedup_warn(err)
        cwd = ""
        if not d_name.startswith(os.pathsep):
            cwd = f" in '{os.getcwd()}'"
        err += f": '{d_name}'{cwd}"
        dedup_warn(f"Failed to {action} configuration file:{NLSP}{err}")
        return Err.RUNTIME
    except RuntimeError as rt_err:
        dedup_warn(str(rt_err))
        return Err.RUNTIME
    except ValueError as value_err:
        dedup_warn(value_err.args[0])
        return Err.CONFIG

    return int(Err.UPDATED) if check and modified else 0


def resolve_gitdir_file(git_file: bytes, repo_path: bytes) -> bytes:
    """Resolve the real Git directory referenced by a worktree `.git` file.

    In a Git worktree checkout, `.git` is a *file* (not a directory)
    containing a single newline-terminated line of the form
    ``gitdir: <path>``, pointing at the real Git directory for that worktree
    (normally under the main repository's ``.git/worktrees/<name>``). A
    relative ``<path>`` is resolved relative to the directory containing
    `git_file`, matching Git's own behavior.

    :param git_file: Path of the (non-directory) `.git` entry to read.
    :param repo_path: Directory containing `git_file`, to resolve relative
        paths against.
    :returns: Resolved Git directory path, or None if `git_file` isn't a
        well-formed single-line ``gitdir:`` pointer file.

    >>> fsdecode(
    ...     resolve_gitdir_file(
    ...         join(TESTDIR, TEST_WORKTREE, GIT_DIR),
    ...         join(TESTDIR, TEST_WORKTREE),
    ...     )
    ... )
    'testdir/git/.git'
    >>> resolve_gitdir_file(join(TESTDIR, TEST_NOT_DIR), TESTDIR)  # empty file
    b''
    >>> resolve_gitdir_file(join(TESTDIR, TEST_GIT), TESTDIR)  # a directory
    b''
    """
    try:
        with open(git_file, "rb") as gitdir_file:
            lines = gitdir_file.readlines()
    except OSError:
        return b""
    if len(lines) != 1 or not lines[0].endswith(b"\n"):
        return b""
    line = lines[0][:-1]
    if not line.startswith(GITDIR_PREFIX):
        return b""
    target = line[len(GITDIR_PREFIX) :].strip()
    if not target:
        return b""
    if not isabs(target):
        target = join(repo_path, target)
    return normpath(target)


def check_git_repository(path: bytes) -> None:
    """Check that path argument is a Git repository.

    This only does a basic sanity check and doesn't actually verify the index.
    In a Git worktree, `.git` is a file rather than a directory; that case is
    followed to the real Git directory via `resolve_gitdir_file` and checked
    the same way as an ordinary `.git` directory.

    :param path: filesystem path.
    :raises RuntimeError: if path isn't a folder with a `.git` sub-folder, or
        a `.git` file pointing to one (as in a Git worktree).

    >>> check_git_repository(join(TESTDIR, b"git/"))
    >>> stderr = sys.stderr
    >>> sys.stderr = sys.stdout  # also capture dedup_warn() worktree notice
    >>> check_git_repository(
    ...     join(TESTDIR, TEST_WORKTREE)
    ... )  # doctest: +ELLIPSIS
    On worktree 'testdir/worktree' of 'testdir/git/.git'
    >>> sys.stderr = stderr
    """
    path_str = fsdecode(path)
    msg = f"'{path_str}' "
    if not exists(path):
        msg += "does not exist."
        raise RuntimeError(msg)
    if not isdir(path):
        msg += "is not a directory."
        raise RuntimeError(msg)
    git_dir = join(path, GIT_DIR)
    if not exists(git_dir):
        msg += "is not a Git repository."
        raise RuntimeError(msg)
    if not isdir(git_dir):
        real_git_dir = resolve_gitdir_file(git_dir, path)
        if real_git_dir != b"":
            real_git_str = fsdecode(real_git_dir)
            dedup_warn(f"On worktree '{path_str}' of '{real_git_str}'")
            if isdir(real_git_dir):
                return
            msg = (
                f"Bad Git repo '{path_str}': worktree gitdir "
                f"'{real_git_str}' is not a directory."
            )
            raise RuntimeError(msg)
        git_str = fsdecode(git_dir)
        msg = f"Bad Git repo '{path_str}': '{git_str}' is not a directory."
        raise RuntimeError(msg)


def load_dependabot_config(config_yml: bytes) -> CommentedMap | dict:
    """Load `dependabot.yml` configuration file, if present.

    Using ruamel.yaml, this preserves YAML comments and vertical whitespace.
    See https://yaml.readthedocs.io/en/latest/example.html for details.

    TODO: Convert to Dependabot class static method (generator).

    :param config_yml: Path name of Dependabot configuration.
    :returns: YAML dict with all configuration from `dependabot.yml`.

    >>> dependabot_yml = join(TESTDIR, b"configured", GITHUB_DEPENDABOT)
    >>> load_dependabot_config(dependabot_yml)  # doctest: +ELLIPSIS
    {'version': 2, 'updates': [{'package-ecosystem': ...
    """
    with open(config_yml, encoding="utf-8") as dependabot_file:
        try:
            with time_limit(15.0):
                config = YAML(pure=PURE).load(dependabot_file)
        except TimeLimitError:
            # decode bytes filename for f-string
            msg = f"Configuration parse timed out for '{fsdecode(config_yml)}'"
            raise ValueError(msg) from None
    if not isinstance(config, (CommentedMap, dict)):
        msg = f"'{fsdecode(config_yml)}' is a {type(config).__name__}, not map"
        raise ValueError(msg)
    return config


# noinspection type-hints
def extract_settings(
    config: CommentedMap | CommentedSeq | dict, defaults: dict[str, Any]
) -> dict[str, Any]:
    """Extract settings from Reliabot YAML comments in ruamel.yaml config.

    Reliabot comments start with "# reliabot: " (possibly indented) and end
    with a newline or a '#' following a space. All settings are given as
    "name=value" with no escapes or quotation, and are separated by spaces
    without any punctuation. So " foo=bar, baz=quuz" sets foo to "bar,".

    :param config: Parsed YAML configuration.
    :param defaults: Default values for all settings.
    :returns: Settings extracted from the comments
    """
    settings = dict(defaults)
    has_config = False
    try:
        if config.ca.comment is not None:  # type: ignore[union-attr]
            has_config = True
        # fmt: off
        comments = [comment.value for comment  # attribute/type errors handled
                    in config.ca.comment[1]]  # type: ignore[union-attr]
        # fmt: on
    except (AttributeError, IndexError, TypeError):
        if has_config:
            warnings.warn(
                f"{NLSP} extract_settings() couldn't get comments"
                f"{NLSP}{traceback.format_exc()}",
                stacklevel=1,
            )
        return settings

    for comment in comments:
        match = COMMENT_PREFIX_MATCH.match(comment)
        if match:
            get_comment_settings(settings, comment[match.end() :])
    return settings


def get_comment_settings(settings: dict, comment: str) -> None:
    """Extract settings from one Reliabot YAML comment.

    Reliabot comments end with a newline or a '#' following a space. Settings
    are space-separated "key=value" without punctuation, escapes, or quotation.
    So "foo=bar, baz=quux" sets foo to "bar," (including the comma).

    :param settings: Reliabot configuration settings.
    :param comment: Reliabot comment (without prefix).
    """
    setting = f"'{COMMENT_PREFIX}' setting"
    bad_setting = f"Bad {setting}"
    for word in comment.split():
        if word.startswith("#"):
            break
        if "=" not in word:
            dedup_warn(f"{bad_setting}: must be X=Y: '{word}'", "=")
            continue
        key, value = word.split("=", 1)
        if key in settings:
            if isinstance(settings[key], bool):
                value = value.lower()
                if value in TRUTHY:
                    settings[key] = bool(TRUTHY[value])
                else:
                    dedup_warn(f"{bad_setting}: '{word}'", key)
            elif isinstance(settings[key], set):
                settings[key].add(value)
            elif isinstance(settings[key], int):
                try:
                    settings[key] = int(value)
                except ValueError:
                    dedup_warn(f"{bad_setting}: '{word}'", key)
            else:
                vtyp = str(type(settings[key]))
                dedup_warn(f"{bad_setting} type: {vtyp}", vtyp)
        else:
            dedup_warn(f"Unknown {setting}: '{word}'", key)


def configure_exclusions(settings: dict[str, Any]) -> Exclusions:
    r"""Handle reliabot configuration options given as initial YAML comments.

    :param settings: Reliabot settings extracted from YAML comments.
    :returns: Exclusion sets for ignoring and keeping.

    >>> test_settings = {
    ...     "ignore": ["archived", "tests"],
    ...     "keep": ["archived"],
    ...     "mapping": "1",
    ...     "offset": "2",
    ... }
    >>> str(configure_exclusions(test_settings))
    "{'ignore': {'archived', 'tests'}, 'keep': {'archived'}}"
    """
    exclusions = Exclusions(EXCLUSIONS)
    for key, value in settings.items():
        if key in exclusions:
            for val in value:
                exclusions.add(key, val)
    return exclusions


class Exclusions:
    """Collection of sets of directory paths to exclude."""

    def __init__(self, keys: Iterable[str]) -> None:
        """Create a dict of named sets of strings."""
        # Sets of exact match strings for directory paths.
        self.match: dict[str, set[str]] = {key: set() for key in keys}
        # Sets of prefix match strings for directory paths.
        self.prefix: dict[str, set[str]] = {key: set() for key in keys}
        # Sets of path specifiers exactly as added.
        self.specs: dict[str, set[str]] = {key: set() for key in keys}

    def __getitem__(self, key: str) -> set[str]:
        return self.specs[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.specs)

    def __repr__(self) -> str:
        return f"({self.specs!r}, {self.match!r}, {self.prefix!r}"

    def __str__(self) -> str:
        """Generate dict repr with sorted keys and set values for doctests."""
        set_vals = []
        for key in sorted(self.specs.keys()):
            vals = ", ".join([repr(val) for val in sorted(self.specs[key])])
            set_vals.append(f"{key!r}: {{{vals}}}")
        return f"{{{', '.join(set_vals)}}}"

    def add(self, key: str, path_spec: str) -> None:
        """Add a path specifier to an exclusion set.

        - The paths `*` and `./*` match all subdirectories but not the root.
        - The path `.` matches the root directory only.
        - The paths `/` and `./` match all directories.
        - Other paths with `.` only match dirs containing `.`.
        - Paths with `//` won't match anything.
        - Other leading `/` in paths are ignored.
        - Paths that don't end with `*` or `/` only match directories exactly.
        - Paths ending in `*` match as a prefix, but not exactly.
        - Paths with `*` anywhere but the end only match dirs containing `*`.
        - Paths ending in `/*` match subdirectories only.
        - Paths ending in `/` match the directory and all subdirectories.

        :param key: Exclusion set name.
        :param path_spec: Path specifier to add to the exclusion set.
        """
        self.specs[key].add(path_spec)
        if path_spec == ".":  # "." matches root directory only.
            path_spec = ""
        elif path_spec in ("/", "./"):  # "./" is the same as "/"
            path_spec = "/"  # "/" matches everything (empty prefix)
        elif path_spec.startswith("/"):  # and path_spec != "//":
            path_spec = path_spec[1:]  # Strip leading "/" before path.
        elif path_spec.startswith("./"):
            path_spec = path_spec[2:]  # Strip leading "./" before path.
        if path_spec.endswith("*"):  # Trailing '*' is a general prefix match.
            path_spec = path_spec[: len(path_spec) - 1]
            self.prefix[key].add(path_spec)
            return  # Paths ending in '*' only match as prefix, not exactly.
        if path_spec.endswith("/"):  # Trailing '/' is a dir prefix match.
            self.prefix[key].add(path_spec)
            path_spec = path_spec[: len(path_spec) - 1]
        self.match[key].add(path_spec)

    def match_path(self, key: str, dir_path: str) -> bool:
        """Check whether an exclusion set matches a path.

        :param key: Exclusion set name.
        :param dir_path: Directory path to check against the exclusion set.
        :returns: True if the path matches the exclusion set, otherwise False.
        """
        dir_path = dir_path.removeprefix("/")
        matched = dir_path in self.match[key]
        if not matched:
            for prefix in self.prefix[key]:
                if dir_path.startswith(prefix) and dir_path != prefix:
                    matched = True
                    break
        return matched

    def matcher(self, key: str) -> Callable[[str], bool]:
        """Return a bound matcher function for one of the sets."""
        return lambda path: self.match_path(key, path)


def find_ecosystems(
    path: bytes, ignored: Callable[[str], bool]
) -> dict[str, set[str]]:
    """Find all Dependabot ecosystems in a Git repository.

    :param path: Git repository (parent of `.git` directory) folder path.
    :param ignored: Matching function that returns whether dir path is ignored.
    :returns: A map of relative directory paths to sets of ecosystem types.

    >>> ECOSYSTEM_RE is not None  # Regex fail check for FAIL_FAST self-test
    True
    >>> config_dir = join(TESTDIR, b"configured")
    >>> dont_ignore = lambda dir_path: False
    >>> find_ecosystems(config_dir, dont_ignore)  # doctest: +ELLIPSIS
    defaultdict(<class 'set'>, {'/': {'github-actions'}, '/bundler':...)
    """
    ecosystems = defaultdict(set)
    workflows = GITHUB_WORKFLOWS.decode("utf-8")
    any_files = False
    for file in subprocess.check_output(GIT_LS, cwd=path).lower().splitlines():
        any_files = True
        dir_name, filename = split(file.decode("utf-8"))  # Use fsdecode()?
        if ignored(dir_name):
            continue
        match = ECOSYSTEM_RE.fullmatch(filename)
        if match:
            for key, val in match.groupdict().items():
                if val is not None:
                    ecosystems[join("/", dir_name)].add(key.replace("_", "-"))
        if DOT_YAML_RE.search(filename.lower()) and dir_name == workflows:
            ecosystems["/"].add(fsdecode(GITHUB_ACTIONS))
    if not any_files:
        msg = f"'{fsdecode(path)}' has no files tracked by Git."
        raise RuntimeError(msg)
    return ecosystems


# FIXME: Too many local variables (17/15)
# pylint: disable=too-many-locals
def update_dependabot_config(
    config: dict, ecosystems: dict[str, Any], kept: Callable[[str], bool]
) -> bool:
    """Update Dependabot configuration with discovered ecosystems.

    Existing configuration is preserved to the greatest extent possible,
    removing entries only if not matched in keepers or found ecosystems.

    :param config: YAML object, with parsed YAML, comments, etc. for updating.
    :param ecosystems: Mapping of folder paths to package ecosystem names.
    :param kept: Matching function that returns whether dir path is kept.
    :returns: True if this function makes changes to the configuration.
    :raises ValueError: if configuration is invalid or is an unknown version.

    >>> test_conf = {}
    >>> ecos = {"/": {"npm"}}
    >>> dont_keep = lambda dir_path: False
    >>> update_dependabot_config(test_conf, ecos, dont_keep)
    True
    >>> test_conf["version"]
    2
    >>> len(test_conf["updates"])
    1
    >>> list(test_conf["updates"][0].keys())
    ['directory', 'package-ecosystem', 'schedule']
    >>> update_dependabot_config(test_conf, ecos, dont_keep)
    False
    >>> ecos2 = {
    ...     "/": {"pip"},
    ...     "/test": {"npm"},
    ...     "schedule": {"interval": "monthly"},
    ... }
    >>> update_dependabot_config(test_conf, ecos2, dont_keep)
    True
    >>> test_conf["updates"][1]
    {'directory': '/test', 'package-ecosystem': 'npm', 'schedule': {'interval': 'monthly'}}
    >>> ecos3 = {"/": {"pub"}}
    >>> exclusions = Exclusions(keys=["kept"])
    >>> exclusions.add("kept", "/tes*")
    >>> update_dependabot_config(test_conf, ecos3, exclusions.matcher("kept"))
    True
    >>> test_conf["updates"][0]
    {'directory': '/test', 'package-ecosystem': 'npm', 'schedule': {'interval': 'monthly'}}
    >>> test_conf["updates"][1]
    {'directory': '/', 'package-ecosystem': 'pub', 'schedule': {'interval': 'monthly'}}
    >>> len(test_conf["updates"])
    2
    """
    if config == {}:
        config["version"] = 2
        config["updates"] = create_dependabot_config(ecosystems)
        empty = len(config["updates"]) == 0
        if empty:
            dedup_warn("Not creating Dependabot config that would be empty.")
        return not empty

    validate_dependabot_config(config)
    confs = config["updates"]

    try:
        changed = False
        for directory, ecosystem_list in sorted(ecosystems.items()):
            for ecosystem in ecosystem_list:
                if not find_conf(confs, directory, ecosystem):
                    add_conf(config, directory, ecosystem)
                    changed = True
        obsolete = []
        for conf in confs:
            pkg_dir = conf["directory"]
            if kept(pkg_dir):
                continue
            pkg_eco = conf["package-ecosystem"]
            if pkg_dir not in ecosystems or pkg_eco not in ecosystems[pkg_dir]:
                obsolete.append(conf)
        # Separate removal loop necessary to avoid modifying live iterator.
        for conf in obsolete:
            folder = conf["directory"]
            eco = conf["package-ecosystem"]
            confs.remove(conf)
            dedup_warn(f"Removed obsolete '{eco}' entry in '{folder}'")
            changed = True

    except (KeyError, TypeError) as config_err:
        msg = "Invalid Dependabot configuration"
        raise ValueError(msg) from config_err
    return changed


def validate_dependabot_config(config: CommentedMap | dict) -> None:
    """Sanity check parsed Dependabot configuration.

    This does not attempt to fully validate the dependabot.yml schema
    (you can use jsonschema and the schemastore dependabot JSON schema)
    but merely checks that required structure is present with correct types.

    :param config: Parsed Dependabot configuration.
    :raises ValueError: if the configuration fails basic sanity checks

    >>> minimal_conf = {
    ...     "version": 3,
    ...     "updates": [
    ...         {
    ...             "directory": "D",
    ...             "package-ecosystem": "P",
    ...             "schedule": {"interval": "I"},
    ...         }
    ...     ],
    ... }
    >>> validate_dependabot_config(minimal_conf)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: ...Dependabot config... version ...
    >>> minimal_conf["version"] = 2
    >>> validate_dependabot_config(minimal_conf)
    """
    msg = None
    try:
        vers = config["version"]
        if vers != 2:
            msg = f"Dependabot config version '{vers}' – must be 2"
            raise ValueError(msg)
        confs = config["updates"]
        if not isinstance(confs, (CommentedSeq, list)):
            msg = ": 'updates' isn't a list"
        else:
            for conf in confs:
                for str_prop in ["directory", "package-ecosystem"]:
                    if not isinstance(conf[str_prop], str):
                        msg = f": update '{str_prop}' isn't a string"
                        break
                if not isinstance(conf["schedule"], (CommentedMap, dict)):
                    msg = ": update 'schedule' isn't a dict"
                    break
                if not isinstance(conf["schedule"]["interval"], str):
                    msg = ": update 'schedule.interval' isn't a string"
                    break
    except TypeError:
        warnings.warn(f"{traceback.format_exc()}", stacklevel=1)
        msg = ""
    except KeyError as key:
        msg = f"Dependabot configuration lacks '{key.args[0]}'"
        raise ValueError(msg) from None
    if msg is not None:
        msg = f"Invalid Dependabot configuration{msg}"
        raise ValueError(msg)


def create_dependabot_config(ecosystems: dict[str, set]) -> list[dict]:
    """Create a new Dependabot configuration for discovered ecosystems.

    TODO: Use a template mechanism for configuring each ecosystem type

    :param ecosystems: mapping of folder paths to package ecosystem names.
    :returns: list of updates entries for parsed YAML Dependabot configuration.

    >>> updates = create_dependabot_config({"/test": {"npm", "docker"}})
    >>> updates[0]
    {'directory': '/test', 'package-ecosystem': 'docker', 'schedule': {'interval': 'monthly'}}
    >>> updates[1]
    {'directory': '/test', 'package-ecosystem': 'npm', 'schedule': {'interval': 'monthly'}}
    """
    config: dict[str, list[dict]] = {"updates": []}
    for directory, ecosystem_list in sorted(ecosystems.items()):
        for ecosystem in sorted(ecosystem_list):
            add_conf(config, directory, ecosystem)
    return config["updates"]


# noinspection type-hints
def safe_dump(
    config: CommentedMap | CommentedSeq | dict | list,
    settings: dict[str, Any],
    config_stream: IO[Any],  # in practice, always TextIO, but mypy can't tell
) -> None:
    """Safely dump YAML configuration file.

    Dump file to string, and parse it again to ensure that settings are OK.

    If parse fails, dedup_warn and try again with default emitter settings.

    If parse with default settings fails, report an internal error.

    :param config: Parsed and updated YAML structure.
    :param settings: Reliabot settings extracted from YAML comments.
    :param config_stream: IO stream of YAML output file.
    :raises OSError: If there are errors writing the file.
    """
    io_string = StringIO()
    tries = 0
    while tries < 2:
        emitter = YAML(pure=True)
        indents = config_emitter(emitter, settings)
        reset(io_string)
        emitter.dump(config, io_string)
        io_string.seek(0, SEEK_SET)
        try:
            emitter.load(io_string)
        except ParserError as parser_err:
            mapping = indents["mapping"]
            offset = indents["offset"]
            sequence = indents["sequence"]
            indent = f"mapping={mapping} offset={offset} sequence={sequence}"
            if settings == EMITTER_SETTINGS:
                error(f"Can't re-parse YAML with default settings ({indent})")
            else:
                err = "YAML (indent?) error:"
                dedup_warn(f"{err} {indent}:{NLSP}{parser_err!s}")
                settings = EMITTER_SETTINGS
        else:
            emitter.dump(config, config_stream)
            config_stream.truncate()
            break
        tries += 1
    else:
        sys.exit(int(Err.INTERNAL))  # pragma: no cover # error() fail-safe.


def reset(stream: TextIO) -> None:
    """Empty stream (truncate to zero) and rewind to start.

    :param stream: IO stream to reset.
    """
    stream.seek(0, SEEK_SET)
    stream.truncate(0)


def find_conf(update_confs: list[dict], folder: str, ecosystem: str) -> bool:
    """Find any update config with matching name and directory.

    :param update_confs: list of Dependabot update configurations.
    :param folder: directory name to match in update configuration.
    :param ecosystem: package-ecosystem name to match in update.
    :returns: True if a matching update configuration is found, else False.
    """
    for uc in update_confs:  # pylint: disable=invalid-name
        if uc["package-ecosystem"] == ecosystem and uc["directory"] == folder:
            return True
    return False


def add_conf(config: dict, folder: str, eco: str) -> None:
    """Add new Dependabot config updates entry for folder and ecosystem.

    This adds the entry to the updates list unconditionally; caller should
    check first that this does not duplicate an existing entry.

    TODO: Add template support for additional configuration, like `assignees`.

    :param config: parsed Dependabot configuration.
    :param folder: directory for Dependabot checks.
    :param eco: package ecosystem type.

    >>> conf = {"updates": []}
    >>> add_conf(conf, "/", "pub")
    >>> conf["updates"]
    [{'directory': '/', 'package-ecosystem': 'pub', 'schedule': {'interval': 'monthly'}}]
    """
    config["updates"].append(
        {
            "directory": folder,
            "package-ecosystem": eco,
            "schedule": {"interval": DEFAULT_INTERVAL},
        }
    )


def update_pre_commit_files(folder: str = ".") -> int:
    """Update reliabot file patterns in folder's pre-commit configurations.

    :param folder: path of folder containing `.pre-commit-{config,hooks}.yaml`.
    :returns: one (1) if files were updated, otherwise zero (0).
    """
    modified = 0
    config_files = [PRE_COMMIT_CONFIG, PRE_COMMIT_HOOKS]
    for file in config_files:
        config_file = join(folder, file)
        try:
            with open(config_file, "r+", encoding="utf-8") as pre_commit:
                if update_pre_commit_file_patterns(pre_commit):
                    dedup_warn(f"Updated '{config_file}'")  # TODO: test for it
                    modified = 1
        except (KeyError, TypeError) as config_err:
            warnings.warn(f"{traceback.format_exc()}", stacklevel=1)
            msg = f"Invalid pre-commit: '{file}'"
            raise ValueError(msg) from config_err
    return Err.UPDATED if modified else 0


def update_reliabot_file_pattern(hook: CommentedMap) -> bool:
    """Update reliabot file pattern in a pre-commit hook.

    :param hook: hook entry in a configuration file.
    :returns: True if it updates the hook, otherwise False.
    :raises KeyError: if the hook lacks 'id' or 'files'.
    """
    if hook["id"] == "reliabot" and hook["files"] != ECOSYSTEM_PATHS_RE:
        hook["files"] = ECOSYSTEM_PATHS_RE
        return True
    return False


def update_pre_commit_file_patterns(config_file: TextIO) -> bool:
    r"""Update reliabot file patterns in folder's pre-commit configuration.

    :param config_file: configuration file text stream.
    :returns: True if the file was modified, otherwise False.
    :raises AttributeError: if file is empty.
    :raises KeyError: if list lacks 'id', map lacks 'repos', 'repo' or 'hooks'.

    >>> import re as pcre  # Python PCRE needed for (?x) in YAML configs.
    >>> _ = pcre.compile(ECOSYSTEM_PATHS_RE)
    >>> ECOSYSTEM_FILE_ACTIONS in ECOSYSTEM_PATHS_RE
    True
    >>> "?P<" not in ECOSYSTEM_PATHS_RE  # Ensure it doesn't have named groups.
    True
    >>> minimal = StringIO("- id: something-else\n")
    >>> update_pre_commit_file_patterns(minimal)
    False
    """
    modified = False
    config = YAML(pure=PURE).load(config_file)
    local = "local"
    if isinstance(config, CommentedMap):
        # Find reliabot hook in pre-commit-config
        repos = config["repos"]
        for repo in repos:
            if repo["repo"] == local:
                for hook in repo["hooks"]:
                    if update_reliabot_file_pattern(hook):
                        modified = True
                        break
                break
    elif isinstance(config, CommentedSeq):
        # Find reliabot hook in pre-commit-hooks
        for hook in config:
            if update_reliabot_file_pattern(hook):
                modified = True
                break
    else:
        unexpected_type = f"Unexpected type '{type(config).__name__}'"
        raise TypeError(unexpected_type)
    if modified:
        reset(config_file)
        settings = extract_settings(config, EMITTER_SETTINGS)
        safe_dump(config, settings, config_file)
    return modified


def config_emitter(emitter: YAML, settings: dict[str, Any]) -> dict[str, int]:
    r"""Apply reliabot YAML format settings to a YAML parser/emitter.

    :param emitter: A ruamel.yaml parser/emitter.
    :param settings: Emitter settings (indentation, width, etc.)
    :returns: dict with indentation settings (mapping, offset, sequence).

    >>> test_emitter = YAML(pure=PURE)
    >>> test_settings = {
    ...     "keep": ["archived"],
    ...     "mapping": 1,
    ...     "offset": 2,
    ...     "sequence": 3,
    ...     "width": 45,
    ...     "yaml-start": False,
    ... }
    >>> config_emitter(test_emitter, test_settings)
    {'mapping': 1, 'offset': 2, 'sequence': 3}
    >>> test_emitter.width
    45
    >>> test_emitter.explicit_start
    False
    """
    indents = dict(EMITTER_INDENTS)
    for key in indents:
        indents[key] = settings[key]
    emitter.explicit_end = False
    emitter.explicit_start = settings["yaml-start"]
    emitter.indent(**indents)
    emitter.preserve_quotes = True
    emitter.width = settings["width"]
    return indents


def fsdecode(path: bytes) -> str:
    """Safely decode filesystem paths, warning of invalid encodings.

    Returns decoded path, or if decoding raises an exception, the Unicode
    object replacement character \ufffc. Most systems that support non-ASCII
    filenames don't raise UnicodeDecodeError, but instead return surrogate
    characters (see PEP 383, https://peps.python.org/pep-0383/ for details).

    TODO: Remove this and refactor as `git ls-files` output is always UTF-8(?)
    The only other filenames used are provided in this code as constants so
    all(?) uses of bytes in this module could be converted to Unicode strings.

    :param path: file path to be decoded.
    :returns: Unicode path string, or U+FFFC if it could not be decoded.

    >>> invalid_bytes = bytes.fromhex("d800f5fd00d8")
    >>> decoded = fsdecode(invalid_bytes)
    >>> decoded == U_FFFC or os.fsencode(decoded) == invalid_bytes
    True
    """
    try:
        if b"/" in path:  # git ls-files output
            return path.decode("utf-8", errors="surrogateescape")
        return os.fsdecode(path)
    except UnicodeDecodeError:  # pragma: no cover
        dedup_warn(f"Bad encoding for '{path.decode(errors='replace')}'")
        return U_FFFC


def self_test() -> int:
    """Run doctests on this script.

    :returns: Zero (0) if all tests passed, otherwise one (1).
    """
    if not sys.warnoptions:
        warnings.simplefilter("default")  # Generate all warnings.
        os.environ["PYTHONWARNINGS"] = "default"  # Also affect subprocesses

    # pylint: disable=import-outside-toplevel,redefined-outer-name
    import doctest  # noqa: PLC0415

    flags = DOCTEST_OPTION_FLAGS
    mod = None
    # Run doctests in an empty context so they start outside any warning scope.
    (failed, tests) = Context().run(doctest.testmod, mod, optionflags=flags)
    if tests == 0:  # pragma: no cover
        # self_test from module wrapper __main__
        mod = sys.modules["reliabot"].reliabot
        (failed, tests) = Context().run(
            doctest.testmod, mod, optionflags=flags
        )
    print(f"Passed {tests - failed} of {tests} doctests.")
    return 1 if failed else 0


X_OPTION_MAP: dict[str, Callable] = {  # Mapping from options to functions.
    DOCTEST_OPT: self_test,
    OPT_UPDATE_PRE_COMMIT: update_pre_commit_files,
}

_CHECK_GIT_REPOSITORY = "check_git_repository"
_CONFIG_EMITTER = "config_emitter"
_EXCLUSIONS_MATCH = "Exclusions.match"
_FIND_ECOSYSTEMS = "find_ecosystems"
_MAIN = "main"
_SAFE_DUMP = "safe_dump"
_UPDATE_PRE_COMMIT_FILE_PATTERNS = "update_pre_commit_file_patterns"
_VALIDATE_DEPENDABOT_CONFIG = "validate_dependabot_config"

__test__ = {
    _CHECK_GIT_REPOSITORY: """
>>> check_git_repository(join(TESTDIR, TEST_NOT_DIR))  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: 'testdir/not-dir'...
>>> check_git_repository(join(TESTDIR, TEST_NOT_GIT))  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: 'testdir/not-git' ... Git...
>>> check_git_repository(join(TESTDIR, TEST_WORKTREE_BAD_PREFIX))  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: ... is not a directory.
>>> stderr = sys.stderr
>>> sys.stderr = sys.stdout  # also capture dedup_warn() worktree notice
>>> try:
...     check_git_repository(join(TESTDIR, TEST_WORKTREE_MISSING))
... except RuntimeError as rt_err:
...     print(rt_err)  # doctest: +ELLIPSIS
On worktree 'testdir/worktree-missing' of 'testdir/does-not-exist'
Bad Git repo ...: worktree gitdir ... is not a directory.
>>> sys.stderr = stderr
""",
    _CONFIG_EMITTER: r"""
>>> test_file = "testdir/github/action.yml"
>>> with open(test_file, "r", encoding="utf-8") as yaml_file:
...     config = YAML(pure=PURE).load(yaml_file)
>>> emitter = YAML(pure=PURE)
>>> # It doesn't seem possible to check stderr warnings from extract_settings.
>>> settings = extract_settings(config, EMITTER_SETTINGS)
>>> indents = config_emitter(emitter, settings)
>>> indents
{'mapping': 9, 'offset': 4, 'sequence': 7}
>>> emitter.width
50
>>> slop = emitter.width + indents["sequence"] / 2  # Wrapping is sloppy.
>>> io_string = StringIO()
>>> emitter.dump(config, io_string)
>>> output = io_string.getvalue()
>>> wrap_regex = "\n[^\n]{" + f"{slop}" + "}\n"
>>> re.compile(wrap_regex).search(output)  # Check width wrap.
""",
    _EXCLUSIONS_MATCH: r"""
>>> dirs = [
...     "",  # root
...     ".hidden-subdir",
...     ".hidden-subdir/sub-subdir",
...     "subdir",
...     "subdir*2",
...     "subdir/sub-subdir",
...     "subdir/sub-subdir2",
...     "subdir2",
...     "subdir2/sub2-subdir",
... ]
>>> hidden_subdirs = ["hidden/sub-subdir"]
>>> not_root = list(dirs).remove("")
>>> subdir2 = ["subdir2", "subdir2/sub2-subdir"]
>>> subdir_subdirs = ["subdir/sub-subdir", "subdir/sub-subdir2"]
>>> path_matches = {
...     "*": not_root,
...     "./*": not_root,
...     ".": [""],
...     "./": dirs,
...     ".hidden-subdir": [".hidden-subdir"],
...     ".hidden-subdir/*": hidden_subdirs,
...     "/": dirs,
...     "/.hidden-subdir//": [],
...     "//": [],
...     "//subdir": [],
...     "/subdir": ["subdir"],
...     "/subdir/": ["subdir"] + subdir_subdirs,
...     "subdir": ["subdir"],
...     "subdir*": subdir_subdirs + subdir2,
...     "subdir*/": [],
...     "subdir*2": ["subdir*2"],
...     "subdir/*": subdir_subdirs,
...     "subdir2/": subdir2,
... }
""",
    # Regex compilation failure test first, for FAIL_FAST self-diagnostic
    _FIND_ECOSYSTEMS: """
>>> for name, regex in ECOS.items():
...     try: _ = re.compile(regex)
...     except re.error as r: print(f"Bad ECOS[{name}] regex: {r}")
>>> dont_ignore = lambda dir_path: False
>>> find_ecosystems(join(TESTDIR, TEST_GIT), dont_ignore)  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: 'testdir/git' ... Git...
>>> find_ecosystems(fsdecode(join(TESTDIR, TEST_GITHUB)), dont_ignore)
defaultdict(<class 'set'>, {'/': {'github-actions'}})
>>> ecos = find_ecosystems(join(TESTDIR, TEST_CONFIGURED), dont_ignore)
>>> ecos["/"] == {"github-actions"}
True
>>> for subdir in ("bundler", "cargo",  "composer", "docker",
...                "elm", "gitsubmodule", "github-actions",
...                "gomod", "gradle", "hex", "maven",
...                "npm", "nuget", "pip", "pub", "terraform"):
...     if subdir not in ecos["/" + subdir]:
...         print(f"'{subdir}' not found in /{subdir}")
""",
    _MAIN: r"""
>>> stderr = sys.stderr
>>> sys.stderr = sys.stdout  # also capture dedup_warn() stderr messages
>>> main(["reliabot"])
Traceback (most recent call last):
...
SystemExit: 2
>>> main(["reliabot", "-not-a-valid-option"])
Traceback (most recent call last):
...
SystemExit: 2
>>> main(["reliabot", "--"])
Traceback (most recent call last):
...
SystemExit: 2
>>> main(["reliabot", "too-many", "args"])
Traceback (most recent call last):
...
SystemExit: 2
>>> main(["reliabot", "--", "too-many", "args"])
Traceback (most recent call last):
...
SystemExit: 2
>>> try:
...     os.remove("testdir/git/.github/dependabot.yml")
... except (FileNotFoundError, NotADirectoryError):
...     pass
>>> main(["reliabot", "--", "testdir/git"])
'testdir/git' has no files tracked by Git.
<Err.RUNTIME: 1>
>>> if not sys.warnoptions:
...     sys.warnoptions = ["default"]
>>> sys.warnoptions
['default']
>>> badlink = "testdir/badlink/.github/dependabot.yml"
>>> if os.path.exists(badlink) or os.path.islink(badlink):
...     os.unlink(badlink)
>>> os.symlink("notdir/notfile", badlink)
>>> main(["reliabot", "--insecure", "testdir/badlink"])  # doctest: +ELLIPSIS
Creating 'testdir/badlink/.github/dependabot.yml'...
Failed to write configuration file:
 No such file or directory: 'testdir/badlink/.github/dependabot.yml' in ...
<Err.RUNTIME: 1>
>>> os.unlink(badlink)
>>> os.symlink("notdir/notfile", badlink)
>>> main(["reliabot", "testdir/badlink"])  # doctest: +ELLIPSIS
Creating 'testdir/badlink/.github/dependabot.yml'...
0
>>> os.path.islink(badlink)  # Broken symlink replaced with regular file
False
>>> os.unlink(badlink)
>>> target_file = "testdir/target.yml"
>>> with open(target_file, "w", encoding="utf-8") as tf:
...     lines = ["version: 2"]
...     lines.append("updates:")
...     lines.append("- directory: /")
...     lines.append("  package-ecosystem: npm")
...     lines.append("  schedule:")
...     lines.append("    interval: monthly")
...     valid_target = "\n".join(lines)
...     _ = tf.write(valid_target)
>>> os.symlink("../../target.yml", badlink)
>>> main(["reliabot", "testdir/badlink"])  # doctest: +ELLIPSIS
Removed obsolete 'npm' entry in '/'
Updating 'testdir/badlink/.github/dependabot.yml'...
0
>>> os.path.islink(badlink)  # Symlink was replaced with a new regular file
False
>>> with open(target_file, "r", encoding="utf-8") as tf:
...     tf.read() == valid_target  # Target file was not modified
True
>>> os.unlink(badlink)
>>> os.symlink("../../target.yml", badlink)
>>> main(["reliabot", "--insecure", "testdir/badlink"])  # doctest: +ELLIPSIS
Removed obsolete 'npm' entry in '/'
Updating 'testdir/badlink/.github/dependabot.yml'...
0
>>> os.path.islink(badlink)  # Insecure update preserved symlink
True
>>> with open(target_file, "r", encoding="utf-8") as tf:
...     "package-ecosystem: terraform" in tf.read()  # Target file was modified
True
>>> os.unlink(badlink)
>>> os.unlink(target_file)
>>> invalid_file = "testdir/github/.github/dependabot.yml"
>>> bad_yaml = "secret_password_12345: {invalid_yaml\n"
>>> with open(invalid_file, "w", encoding="utf-8") as f:
...     _ = f.write(bad_yaml)
>>> main(["reliabot", "testdir/github"])  # doctest: +ELLIPSIS
while parsing a flow mapping
<Err.CONFIG: 3>
>>> with open(invalid_file, "r", encoding="utf-8") as f:
...     f.read() == bad_yaml  # No data written on parse error
True
>>> sys.stderr = stderr
>>> os.unlink(invalid_file)
""",
    _SAFE_DUMP: r"""
>>> stderr = sys.stderr
>>> sys.stderr = sys.stdout  # also capture dedup_warn() stderr messages
>>> io_string = StringIO()
>>> test_config = load_dependabot_config(b".pre-commit-config.yaml")
>>> test_config = { "a": [{"b": 1, "c": {"d": 2}}], "e": 4}
>>> bad_defaults = {
...     "mapping": 2, "offset": 2, "sequence": 2,
...     "width": 76, "yaml-start": False
... }
>>> safe_dump(test_config, bad_defaults, io_string)
YAML (indent?) error: mapping=2 offset=2 sequence=2:
 while parsing a block collection
  in "<file>", line 2, column 3
expected <block end>, but found '?'
  in "<file>", line 3, column 3
>>> sys.stderr = stderr
>>> io_string.getvalue()  # Should be generated with fallback defaults.
'---\na:\n  - b: 1\n    c:\n        d: 2\ne: 4\n'
>>> test_file = "testdir/github/action.yml"
>>> with open(test_file, "r", encoding="utf-8") as yaml_file:
...     loaded = yaml_file.read()
...     _ = yaml_file.seek(0, SEEK_SET)
...     config = YAML(pure=PURE).load(yaml_file)
>>> settings = EMITTER_SETTINGS | {"width": 500}  # A new dict, not an alias.
>>> reset(io_string)
>>> spaces = re.compile(" +")
>>> safe_dump(config, settings, io_string)
>>> spaces.sub(" ", io_string.getvalue()) + "...\n" == spaces.sub(" ", loaded)
True
""",
    _UPDATE_PRE_COMMIT_FILE_PATTERNS: r"""
>>> err1 = StringIO()
>>> update_pre_commit_file_patterns(err1)
Traceback (most recent call last):
...
TypeError: Unexpected type 'NoneType'
>>> err2 = StringIO('key: value\n')
>>> update_pre_commit_file_patterns(err2)
Traceback (most recent call last):
...
KeyError: 'repos'
>>> err3 = StringIO('repos: string\n')
>>> update_pre_commit_file_patterns(err3)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
...
TypeError: string indices must be integers, not 'str'
>>> pre_commits = ['''
... # pre-commit-hooks.yaml
... - id: reliabot
...   name: MUST_NOT_REMOVE
...   files: MUST_REPLACE
... ''', '''
... # pre-commit-config.yaml
... repos:
... - repo: https://example.com/
... - repo: local
...   hooks:
...   - id: reliabot-pre-commit-files
...     files: MUST_NOT_REMOVE
...   - id: reliabot
...     files: MUST_REPLACE
... ''']
>>> for hook in pre_commits:
...   print(hook.split('\n')[1])
...   config_str = StringIO(hook)
...   print(f"    update: {update_pre_commit_file_patterns(config_str)}")
...   result = config_str.getvalue()
...   print(f"    regex-seen: {ECOSYSTEM_PATHS_RE[:10] in result}")
...   print(f"    must-replace: {'MUST_REPLACE' not in result}")
...   print(f"    must-not-remove: {'MUST_NOT_REMOVE' in result}")
# pre-commit-hooks.yaml
    update: True
    regex-seen: True
    must-replace: True
    must-not-remove: True
# pre-commit-config.yaml
    update: True
    regex-seen: True
    must-replace: True
    must-not-remove: True
""",
    _VALIDATE_DEPENDABOT_CONFIG: """
>>> test_conf = {"version": 2}
>>> validate_dependabot_config(test_conf)  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
ValueError: ...Dependabot config...
>>> test_conf["updates"] = [{}]
>>> validate_dependabot_config(test_conf)  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
ValueError: ...Dependabot config...
>>> test_conf["updates"] = [{"directory": "example"}]
""",
}

if __name__ == "__main__":
    sys.exit(main(sys.argv))
