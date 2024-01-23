#!/usr/bin/python3
"""Tidy numbering and ordering of all Markdown reference links in FILEs.

Number _all_ reference links in the order they appear in the text and place
them at the end of the file.

If no files are given, read stdin and print tidied Markdown to stdout.

Original script by Dr. Drang – https://github.com/drdrang/
Posted at:
https://leancrew.com/all-this/2012/09/tidying-markdown-reference-links/ or
https://web.archive.org/web/20120920012828/http://www.leancrew.com/all-this/
WayBack machine archive link.
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import Optional
from typing import TextIO

# The regex for finding reference links in the text. Don't find
# footnotes by mistake.
link = re.compile(r"\[([^\]]+)\]\[([^^\]]+)\]")

# The regex for finding the label. Again, don't find footnotes
# by mistake.
label = re.compile(r"^\[([^^\]]+)\]:\s+(.+)$", re.MULTILINE)


def tidy(text: str) -> str:
    """Find all the links and references in the text and reorder them."""

    def refrepl(m: re.Match) -> str:
        """Rewrite reference links with the reordered link numbers."""
        return "[%s][%d]" % (m.group(1), order.index(m.group(2)) + 1)

    links = link.findall(text)
    if not links:
        return text

    labels = dict(label.findall(text))

    # Determine the order of the links in the text. If a link is used
    # more than once, its order is its first position.
    order: list[str] = []
    for i in links:
        if order.count(i[1]) == 0:
            order.append(i[1])

    # Make a list of the references in order of appearance.
    newlabels = [
        "[%d]: %s" % (i + 1, labels[j]) for (i, j) in enumerate(order)
    ]

    # Remove the old references and put the new ones at the end of the text.
    text = label.sub("", text).rstrip() + "\n" * 2 + "\n".join(newlabels)

    # Rewrite the links with the new reference numbers.
    text = link.sub(refrepl, text) + "\n"

    return text


def tidy_file(input_file: TextIO, output_file: Optional[TextIO]) -> bool:
    """Tidy a file, returning True if the output is identical."""
    original = input_file.read()
    tidied = tidy(original)
    if output_file is None:
        if original == tidied:
            return True
        input_file.seek(0)
        output_file = input_file
    print(tidied, end="", file=output_file)
    if output_file == input_file:
        output_file.truncate()
    return original == tidied


def main() -> int:
    """Tidy Markdown file arguments' reference links, or stdin if no files."""
    docstring = sys.modules[__name__].__doc__ or ""
    description = docstring.split("\n", 1)[0]
    epilog = """
    Returns exit code 1 if any files were modified, 2 for bad arguments, and
    zero (success) if all files were already tidy.

    If no FILE arguments are present, reads stdin and writes stdout, always
    returning success, even if input was not tidy. To get exit code 1 for untidy
    stdin, provide '-' as the filename."""
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, allow_abbrev=False
    )
    parser.add_argument(
        "files",
        help="(multiple) Markdown file(s) for reference link tidying",
        metavar="FILE",
        nargs="*",
        type=argparse.FileType("r+"),
    )
    args = parser.parse_args()
    if not args.files:
        tidy_file(sys.stdin, sys.stdout)
        return 0
    modified = False
    for in_file in args.files:
        out_file = None
        if in_file == sys.stdin:
            out_file = sys.stdout
        if not tidy_file(in_file, out_file):
            modified = True
    return 1 if modified else 0


if __name__ == "__main__":
    sys.exit(main())
