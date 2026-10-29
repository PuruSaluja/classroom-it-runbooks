"""A runbook page, read into its front matter and sections; and new runbooks from the template.

A runbook is a Markdown file in a runbook category's folder (``docs/runbooks/av/``),
named by its identifier in lower case and a slug of its title:
``rb-av-001-projector-shows-no-signal.md``. It starts with YAML front matter between
two ``---`` lines, with the keys in ``FIELDS``:

- ``id``: ``RB-``, the category's prefix and a three-digit number (``RB-AV-001``).
  Numbers are never reused, so a ticket that quotes one always means the same runbook;
- ``title``: the fault as an instructor would report it, also the page's heading;
- ``equipment``: the ids in ``inventory/equipment.toml`` that the runbook covers;
- ``status``: one of ``STATUSES``. A retired runbook stays where it is, so its number
  is never given to another;
- ``reviewed``: the date it was last checked against the equipment, ``YYYY-MM-DD``.

Then the title as the page's ``#`` heading, a short introduction, and the ``##``
sections in ``SECTIONS``' order. ``templates/runbook.md`` is the template, and
``docs/contributing/runbook-template.md`` explains each part.

``python -m classroom_runbooks.runbook new AV "Projector shows no signal" --equipment
laser-projector`` writes a draft from the template with the category's next number.
``catalog`` lists the runbooks in the categories' folders, with their front matter
checked, for the pages that link to them.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from classroom_runbooks import inventory, structure

FIELDS = ("id", "title", "equipment", "status", "reviewed")
STATUSES = ("draft", "current", "retired")
SECTIONS = ("Symptoms", "Before you start", "Checks", "Fix", "Escalate", "Close the ticket")
DEFAULT_TEMPLATE = Path("templates/runbook.md")
MAX_TITLE = 80
"""The longest title, in characters: a fault in a few words, as it would be reported."""
MAX_SLUG = 50
_ID = re.compile(r"RB-([A-Z]{2,4})-([0-9]{3})")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# An ATX heading: up to three spaces, the #s, then its text without any closing #s.
_HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))??(?:[ \t]+#+)?[ \t]*")


class RunbookError(ValueError):
    """A runbook cannot be read, or a new one cannot be written."""


@dataclass(frozen=True)
class Page:
    meta: dict
    """The front matter, as YAML reads it."""
    heading: str | None
    """The text of the ``#`` heading before the first section, if there is one."""
    sections: tuple[tuple[str, str], ...]
    """Each ``##`` heading and the text under it, in order."""


class CatalogError(RunbookError):
    """The runbooks cannot be listed; ``problems`` lists each one, with its file."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("\n".join(self.problems))


@dataclass(frozen=True)
class Entry:
    """A runbook, as the pages that link to it list it."""

    id: str
    title: str
    equipment: tuple[str, ...]
    status: str
    path: Path
    """Its file, relative to the docs folder: ``runbooks/av/rb-av-001-....md``."""


class _Loader(yaml.SafeLoader):
    """YAML's safe loader, except that a key given twice is an error, not the last one."""


def _mapping(loader: _Loader, node: yaml.MappingNode, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    seen: list = []  # a list, as a key may be a list
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"the key {key!r} is given twice", key_node.start_mark
            )
        seen.append(key)
    return loader.construct_mapping(node, deep=deep)


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def parse(text: str) -> Page:
    """A runbook's text, read into its front matter, heading and sections."""
    if text.startswith("\N{BYTE ORDER MARK}"):
        raise RunbookError("the file starts with a byte-order mark; save it as UTF-8 without one")
    lines = structure.split_lines(text)
    if not lines or lines[0] != "---":
        raise RunbookError("a runbook starts with front matter: its first line is '---'")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise RunbookError("the front matter has no closing '---' line") from None
    try:
        # A blank first line in place of the opening '---', so YAML's line numbers are the
        # file's.
        meta = yaml.load("\n" + "\n".join(lines[1:end]), Loader=_Loader)  # a SafeLoader
    except yaml.YAMLError as exc:
        raise RunbookError(f"the front matter is not YAML: {exc}") from None
    except (ValueError, TypeError, AttributeError, RecursionError) as exc:
        # YAML's constructors raise these for a value it cannot build, such as the date
        # 2026-02-30 or `!!float abc`, and nesting too deep raises RecursionError.
        raise RunbookError(f"the front matter has a value YAML cannot read: {exc}") from None
    if not isinstance(meta, dict):
        raise RunbookError("the front matter is not a set of keys and values")
    heading, sections = None, []
    body = lines[end + 1 :]
    for line, code in zip(body, structure.code_lines(body), strict=True):
        found = None if code else _HEADING.fullmatch(line)
        level = len(found.group(1)) if found else 0
        if level == 2:
            sections.append((found.group(2) or "", []))
        elif level == 1 and heading is None and not sections:
            heading = found.group(2) or ""
        elif sections:
            sections[-1][1].append(line)
    return Page(
        meta, heading, tuple((name, "\n".join(text).strip("\n")) for name, text in sections)
    )


def read(path: Path) -> Page:
    if Path(path).is_dir():
        # Windows would say only "Permission denied".
        raise RunbookError(f"{path} is a folder, not a page")
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RunbookError(f"{path} is missing") from None
    except UnicodeDecodeError:
        raise RunbookError(f"{path} is not UTF-8 text") from None
    except OSError as exc:
        raise RunbookError(f"{path} cannot be read: {exc.strerror or exc}") from None
    try:
        return parse(text)
    except RunbookError as exc:
        raise RunbookError(f"{path}: {exc}") from None


def slug(title: str) -> str:
    """A title's words in lower case joined by hyphens, cut at a word to ``MAX_SLUG``.

    Accents are dropped (``Écran`` is ``ecran``), and letters with no ASCII form are left out.
    """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", ascii_title.lower())
    kept: list[str] = []
    for word in words:
        if len("-".join([*kept, word])) > MAX_SLUG:
            break
        kept.append(word)
    return "-".join(kept) or (words[0][:MAX_SLUG] if words else "")


def next_number(folder: Path, prefix: str) -> int:
    """One more than the highest number of a runbook file in ``folder``, or 1."""
    pattern = re.compile(rf"^rb-{re.escape(prefix.lower())}-([0-9]{{3}})(?:-.*)?\.md$")
    numbers = [int(m.group(1)) for p in Path(folder).iterdir() if (m := pattern.match(p.name))]
    return max(numbers, default=0) + 1


def _title_problem(title: object) -> str | None:
    """Why ``title`` cannot be a runbook's title, or None if it can."""
    # Control characters and line or paragraph separators (U+2028, U+0085) would not
    # read back as written: YAML and Markdown treat some of them as line breaks.
    if (
        not isinstance(title, str)
        or not title
        or title != title.strip()
        or any(unicodedata.category(c) in ("Cc", "Zl", "Zp") for c in title)
    ):
        return "a title is one line of text without spaces at its ends or control characters"
    if len(title) > MAX_TITLE:
        return f"a title is at most {MAX_TITLE} characters; this is {len(title)}"
    if not slug(title):
        return f"a title needs a letter or digit to name the file by: {title!r}"
    return None


def _equipment_problem(equipment: object, known: Collection[str]) -> str | None:
    """Why ``equipment`` cannot be the list of what a runbook covers, or None if it can."""
    if not equipment:
        return "name the equipment the runbook covers, by its inventory id"
    if not isinstance(equipment, (list, tuple)) or not all(isinstance(e, str) for e in equipment):
        return f"equipment is a list of inventory ids, not {equipment!r}"
    unknown = [e for e in equipment if e not in known]
    if unknown:
        return f"not in the inventory's equipment: {', '.join(unknown)}"
    if len(set(equipment)) != len(equipment):
        return "an equipment id is given twice"
    return None


def _front_matter_problems(
    page: Page, prefix: str, name: str, known: Collection[str], today: datetime.date
) -> list[str]:
    """What is wrong with a runbook's front matter and heading; ``name`` is its file's."""
    meta, problems = page.meta, []
    missing = [f for f in FIELDS if f not in meta]
    if missing:
        problems.append(f"the front matter has no {', '.join(missing)}")
    others = [repr(k) for k in meta if k not in FIELDS]
    if others:
        problems.append(f"the front matter has keys a runbook does not: {', '.join(others)}")
    if "id" in meta:
        runbook_id = meta["id"]
        found = _ID.fullmatch(runbook_id) if isinstance(runbook_id, str) else None
        if not found or found.group(2) == "000":
            problems.append(f"id {runbook_id!r} is not RB-, a category's prefix and 001 to 999")
        elif found.group(1) != prefix:
            problems.append(f"id {runbook_id} is not in this folder's category, RB-{prefix}")
        elif not name.startswith(f"{runbook_id.lower()}-"):
            problems.append(f"the file's name does not start with its id, {runbook_id.lower()}-")
    if "title" in meta:
        # YAML reads an unquoted yes, 42 or 2026-10-29 as something other than text.
        problem = (
            _title_problem(meta["title"])
            if isinstance(meta["title"], str)
            else f"title {meta['title']!r} is not text; put the title in double quotes"
        )
        if problem:
            problems.append(problem)
        elif page.heading is None:
            problems.append("the page has no # heading; it is the title")
        elif page.heading != meta["title"]:
            problems.append(f"the heading is not the title: {page.heading!r}")
    if "equipment" in meta:
        problem = _equipment_problem(meta["equipment"], known)
        if problem:
            problems.append(problem)
    if "status" in meta and meta["status"] not in STATUSES:
        problems.append(f"status {meta['status']!r} is not one of {', '.join(STATUSES)}")
    if "reviewed" in meta:
        reviewed = meta["reviewed"]
        if isinstance(reviewed, str) and _ISO_DATE.fullmatch(reviewed):
            # YAML reads a quoted date as text.
            problems.append(f"reviewed {reviewed!r} is in quotes; write the date without them")
        # A date with a time reads as a datetime, which is a date too.
        elif type(reviewed) is not datetime.date:
            problems.append(f"reviewed {reviewed!r} is not a date, YYYY-MM-DD")
        # A day's grace, for a date written where it is already tomorrow.
        elif reviewed > today + datetime.timedelta(days=1):
            problems.append(f"reviewed {reviewed} is in the future")
    return problems


def catalog(
    docs: Path,
    sections: Sequence[structure.Section],
    known: Collection[str],
    today: datetime.date | None = None,
) -> tuple[Entry, ...]:
    """Every runbook in the runbook categories' folders under ``docs``, in their order.

    A runbook is any page in a category's folder other than its ``index.md``. Its front
    matter is checked: every field and no others, an identifier of the folder's category
    that the file's name starts with, a title that is also the heading, equipment in
    ``known``, a status and a date no later than ``today`` (by default, the computer's).
    Runbooks are listed by category, in ``sections``' order, then by number; a category
    whose folder is missing has none.
    Raises ``CatalogError`` listing every problem, each with its file.
    """
    today = today or datetime.date.today()
    problems: list[str] = []
    entries: list[Entry] = []
    for section in (s for s in sections if s.prefix):
        for path in sorted((Path(docs) / section.path).glob("*.md")):
            if path.name == "index.md":
                continue
            try:
                page = read(path)
            except RunbookError as exc:
                problems.append(str(exc))
                continue
            found = _front_matter_problems(page, section.prefix, path.name, known, today)
            problems += [f"{path}: {problem}" for problem in found]
            if not found:
                meta = page.meta
                entries.append(Entry(meta["id"], meta["title"], tuple(meta["equipment"]),
                                     meta["status"], Path(section.path) / path.name))  # fmt: skip
    ids = Counter(e.id for e in entries)
    for entry in entries:
        if ids[entry.id] > 1:
            problems.append(f"{Path(docs) / entry.path}: id {entry.id} is another runbook's too")
    if problems:
        raise CatalogError(problems)
    return tuple(entries)


def new(
    template: str,
    folder: Path,
    prefix: str,
    title: str,
    equipment: Sequence[str],
    known: Collection[str],
    today: datetime.date,
) -> Path:
    """Write a draft runbook from ``template`` into ``folder``; its path."""
    problem = _title_problem(title) or _equipment_problem(equipment, known)
    if problem:
        raise RunbookError(problem)
    number = next_number(folder, prefix)
    if number > 999:
        raise RunbookError(f"RB-{prefix} has used all 999 numbers")
    runbook_id = f"RB-{prefix}-{number:03d}"
    values = {
        "id: RB-XX-000": f"id: {runbook_id}",
        'title: "The fault, as an instructor would report it"':
            f"title: {json.dumps(title, ensure_ascii=False)}",
        "# The fault, as an instructor would report it": f"# {title}",
        "equipment: [equipment-id]": f"equipment: [{', '.join(equipment)}]",
        "reviewed: YYYY-MM-DD": f"reviewed: {today.isoformat()}",
    }  # fmt: skip
    for old in values:
        if template.count(old) != 1:
            raise RunbookError(f"the template no longer has the line {old!r} once")
    # In one pass over the template, so a title is never itself replaced.
    placeholders = re.compile("|".join(map(re.escape, values)))
    filled = placeholders.sub(lambda m: values[m.group(0)], template)
    path = Path(folder) / f"{runbook_id.lower()}-{slug(title)}.md"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as f:
            f.write(filled)
    except FileExistsError:
        raise RunbookError(f"{path} is already there; it is not overwritten") from None
    return path


def _template(path: Path) -> str:
    if path.is_dir():
        raise RunbookError(f"{path} is a folder; the template is a file, {DEFAULT_TEMPLATE}")
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RunbookError(f"{path} is missing") from None
    except UnicodeDecodeError:
        raise RunbookError(f"{path} is not UTF-8 text") from None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m classroom_runbooks.runbook",
        description="Start a runbook from the template",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("new", help="write a draft runbook with the next free number")
    start.add_argument("category", help="the runbook category's prefix, such as AV")
    start.add_argument("title", help="the fault, as an instructor would report it")
    start.add_argument("--equipment", nargs="+", required=True, metavar="ID",
                       help="the inventory ids of the equipment it covers")  # fmt: skip
    start.add_argument("--structure", type=Path, default=structure.DEFAULT_STRUCTURE)
    start.add_argument("--docs", type=Path, default=structure.DEFAULT_DOCS)
    start.add_argument("--inventory", type=Path, default=inventory.DEFAULT_INVENTORY)
    start.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args(argv)
    try:
        sections = structure.load(args.structure)
        categories = {s.prefix: s for s in sections if s.prefix}
        if args.category not in categories:
            raise RunbookError(
                f"{args.category!r} is not a runbook category ({', '.join(categories)})"
            )
        known = [e.id for e in inventory.load(args.inventory, list(categories)).equipment]
        template = _template(args.template)
        folder = args.docs / categories[args.category].path
        if not folder.is_dir():
            raise RunbookError(f"{folder} is not a folder; is --docs the site's docs folder?")
        path = new(template, folder, args.category, args.title, args.equipment, known,
                   datetime.date.today())  # fmt: skip
    except (structure.StructureError, RunbookError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except inventory.InventoryError as exc:
        print(f"error: the inventory has {len(exc.problems)} problems; "
              "python -m classroom_runbooks.inventory lists them", file=sys.stderr)  # fmt: skip
        return 1
    print(f"wrote {path}")
    print(f"link it from {folder / 'index.md'}, and fill in each section")
    return 0


if __name__ == "__main__":
    sys.exit(main())
