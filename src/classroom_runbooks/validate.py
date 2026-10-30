"""The validator: every runbook against the template and the escalation matrix, and
every room's equipment against the runbooks.

``python -m classroom_runbooks.validate`` reads the room inventory and the runbooks in
the categories' folders (their front matter checked as ``runbook.catalog`` checks it)
and checks, for each runbook, its **sections**:

- the template's sections, in order, each filled in, and none still holding a line of
  the template's example text;
- each numbered check says what to expect (``**Expected:**``) and links where to go
  if it fails; each numbered action of Fix says what to expect or hands the fault on;
- each "step N of [Fix]" names a step that Fix has;
- Escalate links the escalation matrix and names a role the matrix defines, and each
  role the matrix defines is named by some runbook;
- the category's index lists it by identifier and title.

Then **coverage**: every piece of equipment in every room has a runbook of its own
category that is not retired. It counts the rooms, pieces and kinds of equipment
covered, and names each kind that is not, with the rooms that have it.

It prints each problem with its file, then what it checked, and exits 1 if there is
any problem.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from classroom_runbooks import inventory, runbook, structure

MATRIX = Path("procedures/escalation-matrix.md")
"""The escalation matrix, within the docs folder."""
# A numbered step's text, up to the next step or the section's end.
_STEP = re.compile(r"^[0-9]+\. (.*?)(?=^[0-9]+\. |\Z)", re.MULTILINE | re.DOTALL)
# "go to step 2 of [Fix](#fix)", which a line may break anywhere in.
_FIX_STEP = re.compile(r"step\s+([0-9]+)\s+of\s+\[Fix\]")
_KEPT = "Close the ticket"
"""The template section whose wording a runbook keeps as it is."""


def roles(matrix: str) -> list[str]:
    """The roles an escalation matrix defines: its ``###`` headings under ``## The roles``."""
    found, under = [], False
    lines = structure.split_lines(matrix)
    for line, code in zip(lines, structure.code_lines(lines), strict=True):
        if code:
            continue
        if line.startswith("## "):
            under = line[3:].strip() == "The roles"
        elif under and line.startswith("### "):
            found.append(line[4:].strip())
    return found


def names(text: str, role: str) -> bool:
    """Whether ``text`` names ``role``, in any case and across a line break."""
    words = r"\s+".join(map(re.escape, role.lower().split()))
    return re.search(rf"\b{words}\b", text.lower()) is not None


def _placeholders(template: runbook.Page) -> set[str]:
    """The template's example lines, which a finished runbook has replaced."""
    return {line.strip() for name, body in template.sections if name != _KEPT
            for line in body.splitlines() if line.strip()}  # fmt: skip


def _matrix_roles(docs: Path, problems: list[str]) -> list[str] | None:
    path = docs / MATRIX
    if not path.is_file():
        problems.append(f"{path} is missing: the escalation matrix runbooks escalate through")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        problems.append(f"{path} is not UTF-8 text")
        return None
    except OSError as exc:
        problems.append(f"{path} cannot be read: {exc.strerror or exc}")
        return None
    found = roles(text)
    if not found:
        problems.append(f"{path} defines no roles: a '### ' heading under '## The roles'")
    return found


def _steps(name: str, body: str, expect: bool) -> list[str]:
    steps = _STEP.findall(body)
    if not steps:
        return [f"{name} has no numbered steps"]
    problems = []
    for number, step in enumerate(steps, 1):
        if expect:
            if "**Expected:**" not in step:
                problems.append(f"{name} step {number} does not say what to expect")
            if "](" not in step:
                problems.append(f"{name} step {number} does not link where to go if it fails")
        elif "**Expected:**" not in step and "escalate" not in step.lower():
            problems.append(f"{name} step {number} neither says what to expect nor escalates")
    return problems


def _runbook_problems(
    page: runbook.Page, placeholders: set[str], matrix: str, defined: Sequence[str] | None
) -> list[str]:
    headings = tuple(name for name, _ in page.sections)
    if headings != runbook.SECTIONS:
        return [f"its sections are {list(headings)}, not {list(runbook.SECTIONS)} in order"]
    problems = []
    sections = dict(page.sections)
    for name, body in page.sections:
        if not body.strip():
            problems.append(f"{name} is empty")
        for line in body.splitlines():
            if line.strip() in placeholders:
                problems.append(f"{name} still has the template's line {line.strip()!r}")
    problems += _steps("Checks", sections["Checks"], expect=True)
    problems += _steps("Fix", sections["Fix"], expect=False)
    actions = len(_STEP.findall(sections["Fix"]))
    for name, body in page.sections:
        for number in _FIX_STEP.findall(body):
            if not 1 <= int(number) <= actions:
                problems.append(f"{name} names step {number} of Fix, which has {actions}")
    escalate = sections["Escalate"]
    if not any(target.split("#", 1)[0] == matrix for target in structure.links(escalate)):
        problems.append(f"Escalate does not link the escalation matrix ({matrix})")
    if defined and not any(names(escalate, role) for role in defined):
        problems.append(f"Escalate names none of the matrix's roles: {', '.join(defined)}")
    return problems


def sections(docs: Path, entries: Sequence[runbook.Entry], template: runbook.Page) -> list[str]:
    """Every way the runbooks in ``entries`` depart from the template and the matrix."""
    docs = Path(docs)
    problems: list[str] = []
    defined = _matrix_roles(docs, problems)
    placeholders = _placeholders(template)
    texts = []
    for entry in entries:
        path = docs / entry.path
        try:
            page = runbook.read(path)
            texts.append(path.read_text(encoding="utf-8"))
        except (runbook.RunbookError, OSError, UnicodeDecodeError) as exc:
            problems.append(str(exc))
            continue
        # The matrix as a link from the runbook's folder, written with "/".
        matrix = Path(*[".."] * len(entry.path.parent.parts), MATRIX).as_posix()
        found = _runbook_problems(page, placeholders, matrix, defined)
        problems += [f"{path}: {problem}" for problem in found]
        index = path.parent / "index.md"
        row = f"| {entry.id} | [{entry.title}]({path.name}) |"
        try:
            listed = row in index.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            listed = False
        if not listed:
            problems.append(f"{path}: {index} has no row '{row}'")
    for role in defined or ():
        if not any(names(text, role) for text in texts):
            problems.append(f"{docs / MATRIX}: no runbook names the role {role!r}")
    return problems


@dataclass(frozen=True)
class Coverage:
    """How much of the inventory's equipment has a runbook: (covered, of all) for each."""

    rooms: tuple[int, int]
    """Rooms whose every piece of equipment is covered."""
    pieces: tuple[int, int]
    kinds: tuple[int, int]
    """Kinds of equipment that some room has."""


def coverage(
    rooms: inventory.Inventory, entries: Sequence[runbook.Entry]
) -> tuple[Coverage, list[str]]:
    """What the runbooks in ``entries`` cover of the equipment in ``rooms``, and the gaps.

    A kind of equipment is covered by a runbook of its own category that lists it and is
    not retired; a runbook of another category may list it too, but does not count.
    """
    categories: dict[str, set[str]] = {}
    for entry in (e for e in entries if e.status != "retired"):
        for item in entry.equipment:
            categories.setdefault(item, set()).add(entry.id.split("-")[1])
    covered = {e.id for e in rooms.equipment if e.category in categories.get(e.id, set())}
    having: dict[str, list[str]] = {}
    pieces = [0, 0]
    whole = 0
    for room in rooms.rooms:
        for item, count in room.equipment:
            having.setdefault(item, []).append(room.id)
            pieces[1] += count
            pieces[0] += count if item in covered else 0
        whole += all(item in covered for item, _ in room.equipment)
    problems = []
    for e in (e for e in rooms.equipment if e.id in having and e.id not in covered):
        found = having[e.id]
        shown = ", ".join(found[:3]) + (f" and {len(found) - 3} more" if len(found) > 3 else "")
        problems.append(
            f"coverage: {e.name} ({e.id}), in {len(found)} rooms ({shown}), "
            f"has no {e.category} runbook that is not retired"
        )
    kinds = (len(covered & set(having)), len(having))
    return Coverage((whole, len(rooms.rooms)), (pieces[0], pieces[1]), kinds), problems


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m classroom_runbooks.validate",
        description="Check the runbooks against the template and the escalation matrix",
    )
    parser.add_argument("--structure", type=Path, default=structure.DEFAULT_STRUCTURE)
    parser.add_argument("--inventory", type=Path, default=inventory.DEFAULT_INVENTORY)
    parser.add_argument("--docs", type=Path, default=structure.DEFAULT_DOCS)
    parser.add_argument("--template", type=Path, default=runbook.DEFAULT_TEMPLATE)
    args = parser.parse_args(argv)
    try:
        layout = structure.load(args.structure)
        rooms = inventory.load(args.inventory, [s.prefix for s in layout if s.prefix])
        template = runbook.read(args.template)
    except (structure.StructureError, runbook.RunbookError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except inventory.InventoryError as exc:
        for problem in exc.problems:
            print(f"problem: {problem}", file=sys.stderr)
        print(f"{len(exc.problems)} problems in the inventory")
        return 1
    if not args.docs.is_dir():
        print(f"error: {args.docs} is not a folder", file=sys.stderr)
        return 1
    try:
        entries = runbook.catalog(args.docs, layout, [e.id for e in rooms.equipment])
    except runbook.CatalogError as exc:
        for problem in exc.problems:
            print(f"problem: {problem}", file=sys.stderr)
        print(f"{len(exc.problems)} problems in the runbooks' front matter")
        return 1
    problems = sections(args.docs, entries, template)
    covers, gaps = coverage(rooms, entries)
    problems += gaps
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    print(f"sections: {len(entries)} runbooks checked against the template and the matrix")
    print(
        f"coverage: {covers.rooms[0]:,} of {covers.rooms[1]:,} rooms have a runbook for every "
        f"piece of equipment; {covers.pieces[0]:,} of {covers.pieces[1]:,} pieces and "
        f"{covers.kinds[0]} of {covers.kinds[1]} kinds of equipment are covered"
    )
    print(f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
