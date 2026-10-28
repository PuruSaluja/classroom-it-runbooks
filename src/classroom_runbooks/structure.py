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
_SECTION_PATH = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$")
_PREFIX = re.compile(r"^[A-Z]{2,4}$")
# A Markdown link's target: [text](target) or [text](target "title").
_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")


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
        if not _SECTION_PATH.match(path):
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
        if prefix is not None and (not isinstance(prefix, str) or not _PREFIX.match(prefix)):
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


def links(markdown: str) -> set[str]:
    """The relative targets a page links to, without any ``#anchor``, as written."""
    targets = set()
    for target in _LINK.findall(markdown):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue
        targets.add(target.split("#", 1)[0])
    return targets


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
        first = text.splitlines()[0] if text else ""
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
