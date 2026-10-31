"""The information architecture: the sections of ``docs/``, and a check that the tree follows it.

``structure.toml`` at the repository's root lists every section: its folder under
``docs/``, its title, who reads it and what goes in it. A runbook section also has a
category prefix, which its runbooks' identifiers carry (``RB-AV-001``). The file is the
one place the layout is set: the site's navigation and, later, the validator read it.

``python -m classroom_runbooks.structure`` checks ``docs/`` against it:

- every section's folder is there, with an ``index.md`` whose first line is
  ``# <title>``;
- every folder under ``docs/`` is a section (or an ``assets`` folder for images);
- a section's parent folder is itself a section, so nothing hangs off nowhere;
- the home page, ``docs/index.md``, links to every top-level section, and every
  section's index links to each section directly under it.

It prints the tree and each problem, and exits 1 if there is any.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

DEFAULT_STRUCTURE = Path("structure.toml")
DEFAULT_DOCS = Path("docs")
ASSETS = "assets"
"""A folder of this name, anywhere, holds images and other files a page links to."""
AUDIENCES = ("technicians", "new technicians", "leads", "authors")
# Matched whole (fullmatch), since "$" would also match before a final newline.
_SECTION_PATH = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*")
_PREFIX = re.compile(r"[A-Z]{2,4}")
# A Markdown link's target: [text](target) or [text](target "title").
_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
# A code span: a run of backticks, then text, then a run of the same length.
_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LIST_ITEM = re.compile(r" {0,3}(?:[-*+]|[0-9]{1,9}[.)])(?:[ \t]|$)")
# An ATX heading or a thematic break (---, ***, ___): neither leaves a paragraph open.
_HEADING_OR_BREAK = re.compile(r" {0,3}(?:#{1,6}(?:[ \t]|$)|([-*_])[ \t]*(?:\1[ \t]*){2,}$)")


class StructureError(ValueError):
    """``structure.toml`` cannot be read, or does not describe a usable layout."""


@dataclass(frozen=True)
class Section:
    path: str
    """The section's folder under ``docs/``, with ``/`` between parts."""
    title: str
    audience: tuple[str, ...]
    purpose: str
    prefix: str | None = None
    """For a runbook section, the category in its runbooks' identifiers."""

    @property
    def parent(self) -> str | None:
        parent = str(PurePosixPath(self.path).parent)
        return None if parent == "." else parent


def _text(entry: dict, key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StructureError(f"{where}: {key} must be text")
    if value != value.strip():
        raise StructureError(f"{where}: {key} has spaces at an end: {value!r}")
    return value


def parse(text: str) -> tuple[Section, ...]:
    """The sections ``structure.toml``'s text lists, checked."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise StructureError(f"not TOML: {exc}") from None
    unknown = sorted(set(data) - {"section"})
    if unknown:
        raise StructureError(f"unknown keys {', '.join(unknown)}; sections are [[section]]")
    entries = data.get("section")
    if not isinstance(entries, list) or not entries:
        raise StructureError("no [[section]] entries")
    sections: list[Section] = []
    for i, entry in enumerate(entries, 1):
        where = f"section {i}"
        if not isinstance(entry, dict):
            raise StructureError(f"{where} is not a table of keys: {entry!r}")
        extra = sorted(set(entry) - {"path", "title", "audience", "purpose", "prefix"})
        if extra:
            raise StructureError(f"{where}: unknown keys {', '.join(extra)}")
        path = _text(entry, "path", where)
        where = f"section {path!r}"
        if not _SECTION_PATH.fullmatch(path):
            raise StructureError(
                f"{where}: a path is lower-case words joined by hyphens, folders by /"
            )
        if any(part == ASSETS for part in path.split("/")):
            raise StructureError(f"{where}: {ASSETS!r} is kept for images, not a section")
        audience = entry.get("audience")
        if (
            not isinstance(audience, list)
            or not audience
            or any(a not in AUDIENCES for a in audience)
            or len(set(audience)) != len(audience)
        ):
            raise StructureError(
                f"{where}: audience is a list of {', '.join(map(repr, AUDIENCES))}, each once"
            )
        prefix = entry.get("prefix")
        if prefix is not None and (not isinstance(prefix, str) or not _PREFIX.fullmatch(prefix)):
            raise StructureError(f"{where}: a prefix is 2 to 4 capital letters, not {prefix!r}")
        sections.append(
            Section(path, _text(entry, "title", where), tuple(audience),
                    _text(entry, "purpose", where), prefix)
        )  # fmt: skip
    _check_together(sections)
    return tuple(sections)


def _check_together(sections: list[Section]) -> None:
    paths = [s.path for s in sections]
    for name, values in (("path", paths), ("title", [s.title for s in sections])):
        repeated = sorted({v for v in values if values.count(v) > 1})
        if repeated:
            raise StructureError(f"two sections have the {name} {', '.join(repeated)}")
    prefixes = [s.prefix for s in sections if s.prefix]
    repeated = sorted({p for p in prefixes if prefixes.count(p) > 1})
    if repeated:
        raise StructureError(f"two sections have the prefix {', '.join(repeated)}")
    for s in sections:
        if s.parent is not None and s.parent not in paths:
            raise StructureError(f"section {s.path!r} is under {s.parent!r}, which is not one")


def load(path: Path = DEFAULT_STRUCTURE) -> tuple[Section, ...]:
    if Path(path).is_dir():
        raise StructureError(
            f"{path} is a folder; the structure is a file, such as {DEFAULT_STRUCTURE}"
        )
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise StructureError(f"{path} is missing") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise StructureError(f"{path} cannot be read: {exc}") from None
    try:
        return parse(text)
    except StructureError as exc:
        raise StructureError(f"{path}: {exc}") from None


def split_lines(text: str) -> list[str]:
    """A page's lines, broken only where Markdown breaks them: at LF, CRLF or CR.

    ``str.splitlines`` also breaks at form feeds, U+2028 and other separators, which in
    Markdown are characters within a line.
    """
    lines = re.split(r"\r\n|\r|\n", text)
    return lines[:-1] if lines and lines[-1] == "" else lines


def code_lines(lines: Sequence[str]) -> list[bool]:
    """For each line, whether it is in a code block, a fenced block's fences included.

    A fence opens with three or more backticks or tildes, indented at most three spaces,
    and closes on a line of only at least as many of the same character; one left open
    runs to the end, as Markdown has it. An indented block is lines indented four spaces
    or a tab where no paragraph is open (at the top, after a blank line, a heading or a
    fenced block), running across blank lines; in a list such lines are the item's text.
    """
    flags, fence = [], None
    indented, paragraph, in_list = False, False, False
    for line in lines:
        if fence is not None:
            flags.append(True)
            mark = re.escape(fence[0])
            if re.fullmatch(rf" {{0,3}}{mark}{{{len(fence)},}}[ \t]*", line):
                fence = None
        elif opened := _FENCE.match(line):
            fence = opened.group(1)
            flags.append(True)
            indented = paragraph = in_list = False
        elif not line.strip():
            flags.append(indented)
            paragraph = False
        elif line.expandtabs(4).startswith("    "):
            # Lines in a block change neither, so the block runs on by the same test.
            indented = not (paragraph or in_list)
            flags.append(indented)
        else:
            flags.append(False)
            indented = False
            paragraph = not _HEADING_OR_BREAK.match(line)
            if _LIST_ITEM.match(line):
                in_list = True
            elif not line.startswith(" "):
                in_list = False
    return flags


def prose(markdown: str) -> str:
    """A page's text with its code taken out: code lines blanked and code spans cut down
    to their line breaks, so the text keeps the page's line numbers."""
    lines = split_lines(markdown)
    text = "\n".join("" if code else line for line, code in zip(lines, code_lines(lines),
                                                                 strict=True))  # fmt: skip
    return _CODE_SPAN.sub(lambda span: "\n" * span.group(0).count("\n"), text)


def targets(markdown: str) -> list[tuple[int, str]]:
    """Every link's line number (from 1) and target, as written, ``#anchor`` included.

    A link in a code block or a code span is shown, not followed, so it is not one.
    """
    text = prose(markdown)
    return [(text.count("\n", 0, found.start()) + 1, found.group(1))
            for found in _LINK.finditer(text)]  # fmt: skip


def external(target: str) -> bool:
    """Whether a link's target is a URL with a scheme (``https:``, ``mailto:``)."""
    return re.match(r"^[a-z][a-z0-9+.-]*:", target) is not None


def links(markdown: str) -> set[str]:
    """The relative targets a page links to, without any ``#anchor``, as written."""
    return {target.split("#", 1)[0] for _, target in targets(markdown)
            if not external(target) and not target.startswith("#")}  # fmt: skip


def _page(path: Path, problems: list[str]) -> str | None:
    """A page's text, or None with the reason added to ``problems``."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        problems.append(f"{path} is not UTF-8 text")
    except OSError as exc:
        problems.append(f"{path} cannot be read: {exc.strerror or exc}")
    return None


def _links_to(page: Path, markdown: str, target: Path) -> bool:
    return any((page.parent / t).resolve() == target.resolve() for t in links(markdown))


def check(sections: Sequence[Section], docs: Path = DEFAULT_DOCS) -> list[str]:
    """Every way ``docs`` departs from ``sections``; empty when it follows them."""
    docs = Path(docs)
    if not docs.is_dir():
        return [f"{docs} is not a folder"]
    problems = []
    home = docs / "index.md"
    pages: dict[str, str] = {}
    if not home.is_file():
        problems.append(f"{home} is missing: the home page")
    for s in sections:
        index = docs / s.path / "index.md"
        if not index.is_file():
            problems.append(f"{index} is missing: section {s.title!r} has no index page")
            continue
        text = _page(index, problems)
        if text is None:
            continue
        pages[s.path] = text
        first = split_lines(text)[0] if text else ""
        if first != f"# {s.title}":
            problems.append(f"{index} starts {first!r}, not '# {s.title}'")
    known = {s.path for s in sections}
    for folder in sorted(p for p in docs.rglob("*") if p.is_dir()):
        relative = folder.relative_to(docs).as_posix()
        if ASSETS in relative.split("/"):
            continue
        if relative not in known:
            problems.append(f"{folder} is not a section in the structure")
    text = _page(home, problems) if home.is_file() else None
    if text is not None:
        for s in sections:
            if s.parent is None and not _links_to(home, text, docs / s.path / "index.md"):
                problems.append(f"{home} does not link to {s.path}/index.md ({s.title})")
    for s in sections:
        if s.parent in pages and not _links_to(
            docs / s.parent / "index.md", pages[s.parent], docs / s.path / "index.md"
        ):
            problems.append(
                f"{docs / s.parent / 'index.md'} does not link to {s.path}/index.md ({s.title})"
            )
    return problems


def tree(sections: Sequence[Section]) -> list[str]:
    """The sections as an indented outline."""
    lines = []
    for s in sections:
        depth = s.path.count("/")
        prefix = f"  [{s.prefix}]" if s.prefix else ""
        lines.append(f"{'  ' * depth}{s.path}/  {s.title}{prefix}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m classroom_runbooks.structure",
        description="Check docs/ against the information architecture in structure.toml",
    )
    parser.add_argument("--structure", type=Path, default=DEFAULT_STRUCTURE)
    parser.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    args = parser.parse_args(argv)
    try:
        sections = load(args.structure)
    except StructureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("\n".join(tree(sections)))
    problems = check(sections, args.docs)
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    print(f"{len(sections)} sections; {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
