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
>>> if os.path.islink("testdir") and os.readlink("testdir") == "../testdir/":
...     _ = isdir(".git") or os.mkdir(".git")
"""
from __future__ import annotations

import os
import subprocess
import sys
import warnings
from collections import defaultdict
from enum import IntEnum
from io import SEEK_SET
from io import StringIO
from os.path import basename
from os.path import exists
from os.path import isdir
from os.path import join
from os.path import split
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import TextIO
from typing import Union

from ruamel.yaml import YAML  # ruamel.yaml preserves comments, PyYAML doesn't.
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.parser import ParserError


class Err(IntEnum):
    """Error exit codes for reliabot."""

    RUNTIME = 1  # Nonexistent or inappropriate repository path.
    USAGE = 2  # Invalid options, argument types, or number of arguments.
    CONFIG = 3  # Invalid Dependabot (or pre-commit) configuration in file.
    UPDATED = 4  # Dependabot configuration was or would be modified.
    INTERNAL = 9  # You found a bug in this program!


def usage() -> None:
    """Print usage message for invalid command args; exit with status 2.

    >>> usage()
    Traceback (most recent call last):
    ...
    SystemExit: 2
    """
    command = basename(sys.argv[0])
    dedup_warn(f"Usage: {command} [--re] --update | [--] GIT_REPO")
    dedup_warn("(use '--' if GIT_REPO starts with '-', or see script source)")
    # "Internal" options:
    # --self-test – run doctests in sources
    # --update-pre-commit-files – update pre-commit-* reliabot* files: entries.
    sys.exit(int(Err.USAGE))


def error(message: str) -> None:
    """Report a bug (internal error) in reliabot and exit with status 9.

    :param message: Information about the internal error.
    >>> os.environ[DOCTEST_OPT] = ""
    >>> error("testing error reporting")
    Traceback (most recent call last):
    ...
    SystemExit: 9
    >>> del os.environ[DOCTEST_OPT]
    """
    dedup_warn(f"Internal error - {message}")
    if DOCTEST_OPT in os.environ or sys.argv[len(sys.argv) - 1] != DOCTEST_OPT:
        print(f"  Diagnose with {sys.argv[0]} {DOCTEST_OPT}", file=sys.stderr)
        sys.exit(int(Err.INTERNAL))


def dedup_warn(message: str, key: Optional[str] = None) -> None:
    """Print warning to stderr if non-empty key has not been warned before.

    These stderr messages for end-users do not use Python Warnings, which are
    intended for developers.

    :param message: message to print to stderr.
    :param key: de-duplication key: only warns first instance of key value.
    """
    if key is None or key not in WARN_KEYS:
        print(message, file=sys.stderr)
        if key:
            WARN_KEYS.add(key)


RE2 = False
RE_OPTION = "--re"
RE_WARNING = """

  Reliabot works better with the 're2' regular expression package.
  See https://github.com/dupuy/reliabot/#installation for install instructions,
  or use initial '--re' option to use system 're' and suppress this warning."""

if len(sys.argv) > 1 and sys.argv[1] == RE_OPTION:
    sys.argv.pop(1)
else:
    try:
        # Avoids terrible consequences for pathological RE matching.
        import re2 as re

        RE2 = True
    except ImportError:
        dedup_warn(f"Can't import 're2', falling back to 're'.{RE_WARNING}")
    else:  # Generate fallback warning if re2 package can't handle regexp
        re.set_fallback_notification(re.FALLBACK_WARNING)

if not RE2:
    import re

COMMENT_PREFIX = "# reliabot:"
COMMENT_PREFIX_MATCH = re.compile(rf"\s*{COMMENT_PREFIX}")

DEPENDABOT_CONFIG = b"dependabot.yml"

DOCTEST_OPT = "--self-test"  # Command line option for running doctests.
DOCTEST_OPTION_FLAGS = 0  # This is modified in the re.error exception handler.

DOT_YAML = r"[.]ya?ml"
DOT_YAML_REGEX = re.compile(rf"{DOT_YAML}$")  # used for search, not full match

# Based on dependabot-core; replace GITHUB_ACTIONS with ecosystem in this URL:
# https://github.com/search?q=org:dependabot+path:GITHUB_ACTIONS+required_files_message&type=code
# to find the relevant code, and see the current list of package ecosystems at:
# https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file#package-ecosystem
# More ecosystem support (including beta ones) and filenames can be seen at
# https://github.com/search?q=org:dependabot+required_files_message&type=code,
# which also shows ones whose source folders don't match their names, like
# https://github.com/search?q=org:dependabot+path:GIT_SUBMODULES+required_files_message&type=code

ECOS = {  # This map is modified below to wrap each RE in a named group.
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
ECOSYSTEM_FILE_PATTERNS = list(ECOS.values())
ECOSYSTEM_FILE_PATTERNS.append(ECOSYSTEM_FILE_ACTIONS)
ECOSYSTEM_FILE_PATTERNS.append(ECOSYSTEM_FILE_DEPENDABOT)
ECOSYSTEM_INDENT = "\n  "
ECOSYSTEM_JOIN = f"|{ECOSYSTEM_INDENT}"
ECOSYSTEM_RE_FILES = (
    f"(?x)(^|/)({ECOSYSTEM_INDENT}"
    + ECOSYSTEM_JOIN.join(ECOSYSTEM_FILE_PATTERNS)
    + f"{ECOSYSTEM_INDENT})$"
)

# Convert regexes to named groups with ecosystem names.
ECOS = {k: f"(?P<{k}>{v})" for k, v in ECOS.items()}
ECOSYSTEM_RE_PATTERN = "|".join(ECOS.values())

ECOSYSTEM_REGEX: Union[re.Pattern, None] = None
try:  # It's easy to mess up these regexes. Don't let that break the self test.
    ECOSYSTEM_REGEX = re.compile(ECOSYSTEM_RE_PATTERN)
except re.error:  # pragma: no cover
    print("Internal error - bad regex in ECOS map", file=sys.stderr)
    if len(sys.argv) != 2 or sys.argv[1] != DOCTEST_OPT:
        print(f"  Diagnose with {sys.argv[0]} {DOCTEST_OPT}", file=sys.stderr)
        sys.exit(int(Err.INTERNAL))
    import doctest

    DOCTEST_OPTION_FLAGS = doctest.FAIL_FAST  # Reduce noise from broken tests.

EMITTER_INDENTS = {"mapping": 4, "offset": 2, "sequence": 4}
EMITTER_SETTINGS = {**EMITTER_INDENTS, **{"width": 76, "yaml-start": True}}
# TODO(Once 3.8 is EOL): EMITTER_INDENTS | {"width": 76, "yaml-start": True}
EXCLUSIONS: dict[str, set[str]] = {"ignore": set(), "keep": set()}

FS_ENCODING = sys.getfilesystemencoding()

GITHUB = b".github"
GITHUB_ACTIONS = b"github-actions"
GITHUB_DEPENDABOT = join(GITHUB, DEPENDABOT_CONFIG)
GITHUB_WORKFLOWS = join(GITHUB, b"workflows")

GIT_CMD = "/usr/bin/git"
GIT_DIR = b".git"
GIT_LS = [GIT_CMD, "ls-files"]

OPT_UPDATE = "--update"  # For pre-commit, returning Err.UPDATE on changes.
OPT_UPDATE_PRE_COMMIT = "--update-pre-commit"  # To update pre-commit configs.
# OPT_USES_MAP is updated just after each function in it is defined.
OPT_USES_MAP: dict[str, Callable] = {}  # Mapping from options to functions.

PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"
PRE_COMMIT_HOOKS = ".pre-commit-hooks.yaml"

PURE = True  # Use pure Python parser

TESTDIR = b"testdir"  # dead:disable
TEST_CONFIGURED = b"configured"  # dead:disable
TEST_GIT = b"git"  # dead:disable
TEST_GITHUB = b"github"  # dead:disable
TEST_NOT_DIR = b"not-dir"  # dead:disable
TEST_NOT_GIT = b"not-git"  # dead:disable

TRUTHY = {"false": 0, "off": 0, "on": 1, "true": 1}

U_FFFC = "\ufffc"  # Unicode object replacement character

WARN_KEYS: set[str] = set()


# pylint: disable=too-many-locals
def main(optargv: Optional[list[str]] = None) -> int:  # noqa: MC0001
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
    >>> main(["reliabot.py", OPT_UPDATE]) # Updated dependabot config required,
    0
    >>> main(["reliabot.py", OPT_UPDATE_PRE_COMMIT]) # also pre-commit config.
    0
    >>> test_dir = "testdir/github/"
    >>> test_conf = f"{test_dir}/.github/{fsdecode(DEPENDABOT_CONFIG)}"
    >>> _ = not exists(test_conf) or os.unlink(test_conf)
    >>> os.chdir(test_dir)
    >>> main(["reliabot.py", OPT_UPDATE])
    4
    >>> os.chdir("../..")
    >>> _ = not exists(test_conf) or os.unlink(test_conf)
    """
    check = False
    modified = False
    update_status = "Updating"
    conf: Union[CommentedMap, dict] = {}

    argv = optargv or sys.argv
    try:
        if argv[1] == "--":  # "end of options"
            argv.pop(1)
        elif argv[1] == OPT_UPDATE:
            argv[1] = "."
            check = True
        elif argv[1] in OPT_USES_MAP:
            return OPT_USES_MAP[argv[1]]()
        elif argv[1].startswith("-"):
            dedup_warn(f"Unknown option '{argv[1]}'", argv[1])
            usage()

        if len(argv) != 2:
            usage()
    except IndexError:
        usage()

    repo_dir = argv[1].encode(FS_ENCODING, "surrogatepass")
    dconf = join(repo_dir, GITHUB_DEPENDABOT)

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

        # TODO(once 3.8 is EOL): EMITTER_SETTINGS | EXCLUSIONS
        settings = extract_settings(conf, {**EMITTER_SETTINGS, **EXCLUSIONS})

        exclude = configure_exclusions(settings)

        ecosystems = find_ecosystems(repo_dir, exclude.matcher("ignore"))

        if update_dependabot_config(conf, ecosystems, exclude.matcher("keep")):
            modified = True
            action = "write"
            dedup_warn(f"{update_status} '{fsdecode(dconf)}'...")
            with open(dconf, "w+" if new else "r+", encoding="utf-8") as dfile:
                safe_dump(conf, settings, dfile)
    except OSError as os_err:
        filename = fsdecode(os_err.filename)
        cwd = ""
        if not filename.startswith(os.pathsep):
            cwd = f" in '{os.getcwd()}'"
        err = f"{os_err.strerror}: '{filename}'{cwd}"
        dedup_warn(f"Failed to {action} configuration file:\n  {err}")
        return Err.RUNTIME
    except RuntimeError as rt_err:
        dedup_warn(str(rt_err))
        return Err.RUNTIME
    except ValueError as value_err:
        dedup_warn(value_err.args[0])
        return Err.CONFIG

    return int(Err.UPDATED) if check and modified else 0


def check_git_repository(path: bytes) -> None:
    """Check that path argument is a Git repository.

    This only does a basic sanity check and doesn't actually verify the index.

    :param path: filesystem path.
    :raises RuntimeError: if path isn't a folder with a `.git` sub-folder.

    >>> check_git_repository(join(TESTDIR, b"git/"))
    """
    path_str = fsdecode(path)
    if not exists(path):
        raise RuntimeError(f"'{path_str}' does not exist.")
    if not isdir(path):
        raise RuntimeError(f"'{path_str}' is not a directory.")
    git_dir = join(path, GIT_DIR)
    if not exists(git_dir):
        raise RuntimeError(f"'{path_str}' is not a Git repository.")
    if not isdir(git_dir):
        git_str = fsdecode(git_dir)
        raise RuntimeError(
            f"Bad Git repo '{path_str}': '{git_str}' is not a directory."
        )


def load_dependabot_config(config_yml: bytes) -> CommentedMap:
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
    with open(config_yml, "r", encoding="utf-8") as dependabot_file:
        config = YAML(pure=PURE).load(dependabot_file)
    if not isinstance(config, (CommentedMap, dict)):
        raise ValueError(f"'{dependabot_file}' is a {type(config)}, not a map")
    return config


def extract_settings(
    config: CommentedMap, defaults: dict[str, Any]
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

    try:
        comments = [comment.value for comment in config.ca.comment[1]]
    except (AttributeError, IndexError):
        return settings

    for comment in comments:
        offset = COMMENT_PREFIX_MATCH.match(comment)
        if offset is None:
            continue
        setting = f"'{COMMENT_PREFIX}' setting"
        bad_setting = f"Bad {setting}"
        for word in comment[offset.end() :].split():
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
    return settings


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
        return f"({repr(self.specs)}, {repr(self.match)}, {repr(self.prefix)}"

    def __str__(self) -> str:
        """Generates dict repr with sorted keys and set values for doctests."""
        set_vals = []
        for key in sorted(self.specs.keys()):
            vals = ", ".join([repr(val) for val in sorted(self.specs[key])])
            set_vals.append(f"{repr(key)}: {{{vals}}}")
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
        if dir_path.startswith("/"):
            dir_path = dir_path[1:]
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

    >>> ECOSYSTEM_REGEX is not None  # Regex fail check for FAIL_FAST self-test
    True
    >>> config_dir = join(TESTDIR, b"configured")
    >>> dont_ignore = lambda dir_path: False
    >>> find_ecosystems(config_dir, dont_ignore)   # doctest: +ELLIPSIS
    defaultdict(<class 'set'>, {'/': {'github-actions'}, '/bundler':...)
    """
    ecosystems = defaultdict(set)
    workflows = GITHUB_WORKFLOWS.decode("utf-8")
    any_files = False
    for file in subprocess.check_output(GIT_LS, cwd=path).lower().splitlines():
        any_files = True
        dirname, filename = split(file.decode("utf-8"))  # Use fsdecode()?
        if ignored(dirname):
            continue
        # ignored = dirname in ignore_set
        # for ignore in ignore_set:
        #     if ignore and not ignore.endswith("/"):  # preserve "" ignore all
        #         ignore += "/"
        #     if ignored or dirname.startswith(ignore):
        #         ignored = True
        #         break
        # if ignored:
        #     continue
        match = ECOSYSTEM_REGEX.fullmatch(filename)  # type: ignore[union-attr]
        if match:
            for key, val in match.groupdict().items():
                if val is not None:
                    ecosystems[join("/", dirname)].add(key.replace("_", "-"))
        if dirname == workflows and DOT_YAML_REGEX.search(filename.lower()):
            ecosystems["/"].add(fsdecode(GITHUB_ACTIONS))
    if not any_files:
        raise RuntimeError(f"'{fsdecode(path)}' has no files tracked by Git.")
    return ecosystems


def update_dependabot_config(
    config: dict, ecosystems: dict[str, set[str]], kept: Callable[[str], bool]
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
    >>> test_conf
    {'version': 2, 'updates': [{'directory': '/', 'package-ecosystem': 'npm'}]}
    >>> update_dependabot_config(test_conf, ecos, dont_keep)
    False
    >>> ecos2 = {"/": {"pip"}, "/test": {"npm"}}
    >>> update_dependabot_config(test_conf, ecos2, dont_keep)
    True
    >>> test_conf["updates"][1]
    {'directory': '/test', 'package-ecosystem': 'npm'}
    >>> ecos3 = {"/": {"pub"}}
    >>> exclusions = Exclusions(keys=["kept"])
    >>> exclusions.add("kept", "/tes*")
    >>> update_dependabot_config(test_conf, ecos3, exclusions.matcher("kept"))
    True
    >>> test_conf["updates"][0]
    {'directory': '/test', 'package-ecosystem': 'npm'}
    >>> test_conf["updates"][1]
    {'directory': '/', 'package-ecosystem': 'pub'}
    >>> len(test_conf['updates'])
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
        for directory, ecosystem_list in sorted(list(ecosystems.items())):
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
        raise ValueError("Invalid Dependabot configuration") from config_err
    return changed


def validate_dependabot_config(config: Union[CommentedMap, dict]) -> None:
    """Sanity check parsed Dependabot configuration.

    :param config: Parsed Dependabot configuration.
    :raises ValueError: if the configuration fails basic sanity checks

    >>> test_conf = {"version": 3}
    >>> validate_dependabot_config(test_conf)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: ...Dependabot config... version ...
    >>> test_conf["updates"] = [{"directory": "example"}]
    """
    msg = None
    try:
        vers = config["version"]
        if vers != 2:
            raise ValueError(f"Dependabot config version '{vers}' – must be 2")
        confs = config["updates"]
        if not isinstance(confs, (CommentedSeq, list)):
            msg = "Invalid Dependabot config: 'updates' not a list"
        else:
            for conf in confs:
                if not isinstance(conf["directory"], str):
                    msg = "Invalid Dependabot config: 'directory' not a string"
    except TypeError:
        msg = "Invalid Dependabot config"
    except KeyError as k:
        msg = f"Dependabot configuration is missing '{k.args[0]}'"
    if msg:
        raise ValueError(msg)


def create_dependabot_config(ecosystems: dict[str, set]) -> list[dict]:
    """Create a new Dependabot configuration for discovered ecosystems.

    TODO: Use a template mecbanism for configuring each ecosystem type

    :param ecosystems: mapping of folder paths to package ecosystem names.
    :returns: list of updates entries for parsed YAML Dependabot configuration.

    >>> updates = create_dependabot_config({"/test": {"npm", "docker"}})
    >>> updates[0]
    {'directory': '/test', 'package-ecosystem': 'docker'}
    >>> updates[1]
    {'directory': '/test', 'package-ecosystem': 'npm'}
    """
    config: dict[str, list[dict]] = {"updates": []}
    for directory, ecosystem_list in sorted(list(ecosystems.items())):
        for ecosystem in sorted(list(ecosystem_list)):
            add_conf(config, directory, ecosystem)
    return config["updates"]


def safe_dump(
    config: Union[CommentedMap, CommentedSeq, dict, list],
    settings: dict[str, Any],
    config_stream: TextIO,
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
                dedup_warn(f"{err} {indent}:\n{str(parser_err)}")
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
    [{'directory': '/', 'package-ecosystem': 'pub'}]
    """
    config["updates"].append({"directory": folder, "package-ecosystem": eco})


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
            raise ValueError(f"Invalid pre-commit: '{file}'") from config_err
    return Err.UPDATED if modified else 0


OPT_USES_MAP[OPT_UPDATE_PRE_COMMIT] = update_pre_commit_files


def update_pre_commit_file_patterns(config_file: TextIO) -> bool:
    r"""Update reliabot file patterns in folder's pre-commit configuration.

    :param config_file: configuration file text stream.
    :returns: True if files were updated, otherwise False.
    :raises AttributeError: if file is empty.
    :raises KeyError: if list lacks 'id', map lacks 'repos', 'repo' or 'hooks'.

    >>> import re as pcre  # Python PCRE needed for (?x) in YAML configs.
    >>> _ = pcre.compile(ECOSYSTEM_RE_FILES)
    >>> ECOSYSTEM_FILE_ACTIONS in ECOSYSTEM_RE_FILES
    True
    >>> "?P<" not in ECOSYSTEM_RE_FILES  # Ensure it doesn't have named groups.
    True
    >>> minimal = StringIO("- id: something-else\n")
    >>> update_pre_commit_file_patterns(minimal)
    False
    """
    modified = False
    config = YAML(pure=PURE).load(config_file)
    local = "local"
    repos: list[dict[str, CommentedSeq]]
    # pre-commit-hooks.yaml has no repos or hooks structure, make it so.
    if isinstance(config, CommentedSeq):
        repos = [{"repo": local, "hooks": config}]
    else:
        repos = config["repos"]

    for repo in repos:
        if repo["repo"] != local:
            continue

        for hook in repo["hooks"]:
            if hook["id"] == "reliabot":
                if hook["files"] != ECOSYSTEM_RE_FILES:
                    modified = True
                    hook["files"] = ECOSYSTEM_RE_FILES
    if modified:
        reset(config_file)
        settings = extract_settings(config, EMITTER_SETTINGS)
        safe_dump(config, settings, config_file)
    return modified


def config_emitter(emitter: YAML, settings: dict[str, Any]) -> dict[str, int]:
    r"""Apply reliabot YAML format settings to a YAML parser/emitter.

    :param emitter: A ruamel.yaml parser/emitter.
    :param settings: Emitter settings (indentation, etcetera.)
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

    # pylint: disable=import-outside-toplevel,redefined-outer-name
    import doctest

    (failed, tests) = doctest.testmod(optionflags=DOCTEST_OPTION_FLAGS)
    print(f"Passed {tests - failed} of {tests} doctests.")
    if not failed:  # pragma: no cover
        doctest.testmod(verbose=True)
    return 1 if failed else 0


OPT_USES_MAP[DOCTEST_OPT] = self_test

CHECK_GIT_REPOSITORY = "check_git_repository"
CONFIG_EMITTER = "config_emitter"
EXCLUSIONS_MATCH = "Exclusions.match"
FIND_ECOSYSTEMS = "find_ecosystems"
MAIN = "main"
SAFE_DUMP = "safe_dump"
UPDATE_PRE_COMMIT_FILE_PATTERNS = "update_pre_commit_file_patterns"
VALIDATE_DEPENDABOT_CONFIG = "validate_dependabot_config"

__test__ = {
    CHECK_GIT_REPOSITORY: """
>>> check_git_repository(join(TESTDIR, TEST_NOT_DIR))  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: 'testdir/not-dir'...
>>> check_git_repository(join(TESTDIR, TEST_NOT_GIT))  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: 'testdir/not-git' ... Git...
""",
    CONFIG_EMITTER: r"""
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
    EXCLUSIONS_MATCH: r"""
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
    FIND_ECOSYSTEMS: """
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
    MAIN: """
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
>>> badlink = "testdir/badlink/.github/dependabot.yml"
>>> if os.path.exists(badlink):
...     os.unlink(badlink)
>>> os.symlink("notdir/notfile", badlink)
>>> main(["reliabot", "testdir/badlink"])  # doctest: +ELLIPSIS
Creating 'testdir/badlink/.github/dependabot.yml'...
Failed to write configuration file:
  No such file or directory: 'testdir/badlink/.github/dependabot.yml' in ...
<Err.RUNTIME: 1>
>>> sys.stderr = stderr
>>> os.unlink(badlink)
""",
    SAFE_DUMP: r"""
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
>>> settings = EMITTER_SETTINGS
>>> settings["width"] = 500
>>> reset(io_string)
>>> spaces = re.compile(" +")
>>> safe_dump(config, EMITTER_SETTINGS, io_string)
>>> spaces.sub(" ", io_string.getvalue()) + "...\n" == spaces.sub(" ", loaded)
True
""",
    UPDATE_PRE_COMMIT_FILE_PATTERNS: r"""
>>> err1 = StringIO()
>>> update_pre_commit_file_patterns(err1)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
...
TypeError: 'NoneType' object is not subscriptable
>>> err2 = StringIO('key: value\n')
>>> update_pre_commit_file_patterns(err2)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
...
KeyError: 'repos'
>>> err3 = StringIO('repos: string\n')
>>> update_pre_commit_file_patterns(err3)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
...
TypeError: string indices must be integers
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
...   print(f"    regex-seen: {ECOSYSTEM_RE_FILES[:10] in result}")
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
    VALIDATE_DEPENDABOT_CONFIG: """
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
