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
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import unicodedata
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
    lines = text.splitlines()
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
    if not isinstance(meta, dict):
        raise RunbookError("the front matter is not a set of keys and values")
    heading, sections = None, []
    body = lines[end + 1 :]
    for line, code in zip(body, structure.code_lines(body), strict=True):
        if not code and line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif not code and line.startswith("# ") and heading is None and not sections:
            heading = line[2:].strip()
        elif sections:
            sections[-1][1].append(line)
    return Page(
        meta, heading, tuple((name, "\n".join(text).strip("\n")) for name, text in sections)
    )


def read(path: Path) -> Page:
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
    if title != title.strip() or not title or "\n" in title or "\r" in title:
        raise RunbookError("a title is one line of text without spaces at its ends")
    if len(title) > MAX_TITLE:
        raise RunbookError(f"a title is at most {MAX_TITLE} characters; this is {len(title)}")
    if not slug(title):
        raise RunbookError(f"a title needs a letter or digit to name the file by: {title!r}")
    if not equipment:
        raise RunbookError("name the equipment the runbook covers, by its inventory id")
    unknown = [e for e in equipment if e not in known]
    if unknown:
        raise RunbookError(f"not in the inventory's equipment: {', '.join(unknown)}")
    if len(set(equipment)) != len(equipment):
        raise RunbookError("an equipment id is given twice")
    number = next_number(folder, prefix)
    if number > 999:
        raise RunbookError(f"RB-{prefix} has used all 999 numbers")
    runbook_id = f"RB-{prefix}-{number:03d}"
    filled = template
    for old, value in (
        ("id: RB-XX-000", f"id: {runbook_id}"),
        ('title: "The fault, as an instructor would report it"',
         f"title: {json.dumps(title, ensure_ascii=False)}"),
        ("# The fault, as an instructor would report it", f"# {title}"),
        ("equipment: [equipment-id]", f"equipment: [{', '.join(equipment)}]"),
        ("reviewed: YYYY-MM-DD", f"reviewed: {today.isoformat()}"),
    ):  # fmt: skip
        if filled.count(old) != 1:
            raise RunbookError(f"the template no longer has the line {old!r} once")
        filled = filled.replace(old, value)
    path = Path(folder) / f"{runbook_id.lower()}-{slug(title)}.md"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as f:
            f.write(filled)
    except FileExistsError:
        raise RunbookError(f"{path} is already there; it is not overwritten") from None
    return path


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
        template = args.template.read_text(encoding="utf-8")
        folder = args.docs / categories[args.category].path
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
