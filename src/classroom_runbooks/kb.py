"""The knowledge-base export: the runbooks, and the pages they link to, as ServiceNow
knowledge articles, in the XML format ServiceNow exports and imports records in.

Each runbook becomes a ``kb_knowledge`` record and each section it is filed under a
``kb_category`` record, all in one ``<unload>`` document:

- ``short_description`` is the page's ``#`` heading, its title; ``text`` is the rest
  of the page as HTML, front matter left out, with a last line naming the runbook it
  was generated from;
- ``kb_category`` is the page's section (``Audio-visual``), under one top category
  (``TOP``) in the knowledge base;
- ``workflow_state`` is the runbook's status as ``STATES`` maps it; a page that is not a
  runbook has no status and goes in as a draft, for the knowledge base's reviewers;
- ``meta``, the article's search keywords, holds the runbook's identifier, so a ticket
  that quotes ``RB-AV-001`` finds it, and the names of the equipment it covers.

Every record's ``sys_id`` is made (``uuid5``) from the knowledge base's and a key: a
runbook's identifier, which a new title leaves as it is, or another page's path. So
exporting again gives the same ones and an import updates the articles it made
before rather than adding copies. A link to another exported page becomes a link to
its article, ``#anchor`` kept; a link to a page that is not exported keeps its text
and loses its target, and the export lists it. Every ``#anchor`` must name an id in
the article it reaches, or the export fails.

``python -m classroom_runbooks.kb --knowledge-base SYS_ID --out kb.xml`` writes it;
``docs/reference/kb-export-format.md`` describes the format and
``docs/reference/taxonomy-mapping.md`` the mapping.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from classroom_runbooks import inventory, runbook, structure, validate

TOP = "Classroom technology"
"""The knowledge-base category every exported section is filed under."""
STATES = {"draft": "draft", "current": "published", "retired": "retired"}
"""A runbook's status, and the article's ``workflow_state`` for it."""
UNFILED_STATE = "draft"
"""The ``workflow_state`` of a page that is not a runbook, which has no status."""
ARTICLE_LINK = "/kb_view.do?sys_kb_id={}"
NAMESPACE = uuid.UUID("6f1d3c2e-4b5a-4e8f-9a7b-2c1d0e9f8a6b")
"""Fixed, so a page's ``sys_id`` is the same in every export."""
_SYS_ID = re.compile(r"[0-9a-f]{32}")
_ID_ATTR = re.compile(r'\sid="([^"]+)"')
_HREF = re.compile(r'\shref="([^"]+)"')


class ExportError(ValueError):
    """The pages cannot be exported; ``problems`` lists each one, with its file."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("\n".join(self.problems))


@dataclass(frozen=True)
class Category:
    sys_id: str
    label: str
    value: str
    parent: str | None
    """The parent category's ``sys_id``; ``None`` for the top one, under the base."""


@dataclass(frozen=True)
class Article:
    sys_id: str
    source: Path
    """The page, relative to the docs folder."""
    runbook: str | None
    """The runbook's identifier; ``None`` for a page that is not a runbook."""
    title: str
    category: Category
    state: str
    keywords: tuple[str, ...]
    html: str


@dataclass(frozen=True)
class Export:
    knowledge_base: str
    categories: tuple[Category, ...]
    articles: tuple[Article, ...]
    unlinked: tuple[tuple[Path, str], ...]
    """Each link to a page outside the export, kept as text: its page and target."""


def sys_id(knowledge_base: str, key: str) -> str:
    """A record's ``sys_id``, 32 hex digits, made from the knowledge base and ``key``."""
    return uuid.uuid5(NAMESPACE, f"{knowledge_base}/{key}").hex


def _value(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def _split(text: str) -> tuple[str | None, str]:
    """A page's ``#`` heading, and the rest of it after any front matter."""
    lines = structure.split_lines(text)
    if lines and lines[0] == "---" and "---" in lines[1:]:
        lines = lines[lines.index("---", 1) + 1 :]
    while lines and not lines[0].strip():
        lines = lines[1:]
    title = None
    if lines and lines[0].startswith("# "):
        title, lines = lines[0][2:].strip(), lines[1:]
    return title, "\n".join(lines) + "\n"


class _Links(Treeprocessor):
    """Points each link to another page at its article, or keeps only its text."""

    def __init__(self, md: markdown.Markdown, page: Path, ids: dict[Path, str],
                 unlinked: list[tuple[Path, str]]) -> None:  # fmt: skip
        super().__init__(md)
        self.page, self.ids, self.unlinked = page, ids, unlinked

    def run(self, root: ET.Element) -> None:
        for link in root.iter("a"):
            href = link.get("href", "")
            if not href or href.startswith("#") or structure.external(href):
                continue
            path, _, name = href.partition("#")
            target = Path(os.path.normpath(self.page.parent / unquote(path)))
            if target in self.ids:
                anchor = f"#{name}" if name else ""
                link.set("href", ARTICLE_LINK.format(self.ids[target]) + anchor)
            else:
                self.unlinked.append((self.page, href))
                link.tag = "span"
                del link.attrib["href"]


class _LinksExtension(Extension):
    def __init__(self, page: Path, ids: dict[Path, str], unlinked: list) -> None:
        super().__init__()
        self.page, self.ids, self.unlinked = page, ids, unlinked

    def extendMarkdown(self, md: markdown.Markdown) -> None:  # noqa: N802 (the API's name)
        # After the inline links are made (priority 20) and before they are serialised.
        md.treeprocessors.register(_Links(md, self.page, self.ids, self.unlinked), "kb-links", 5)


def html(body: str, page: Path, ids: dict[Path, str], unlinked: list) -> str:
    """A page's Markdown as an article's HTML, headings given the anchors GitHub gives
    them (a repeated one numbered from ``-1``), so the page's ``#anchor`` links still
    reach them."""
    return markdown.markdown(
        body,
        extensions=["tables", "sane_lists", "toc", _LinksExtension(page, ids, unlinked)],
        extension_configs={"toc": {"slugify": validate.Slugs()}},
    )


def _anchor_problems(articles: Sequence[Article]) -> list[str]:
    ids = {a.sys_id: set(_ID_ATTR.findall(a.html)) for a in articles}
    problems = []
    for article in articles:
        for href in _HREF.findall(article.html):
            if href.startswith("#"):
                target, name = article.sys_id, href[1:]
            elif href.startswith(ARTICLE_LINK.format("")) and "#" in href:
                target, name = href[len(ARTICLE_LINK.format("")) :].split("#", 1)
            else:
                continue
            if name not in ids.get(target, set()):
                problems.append(
                    f"{article.source.as_posix()}: the link {href} names no id in its article"
                )
    return problems


def export(
    docs: Path,
    sections: Sequence[structure.Section],
    rooms: inventory.Inventory,
    knowledge_base: str,
) -> Export:
    """The runbooks under ``docs``, and the pages they link to, as articles and categories.

    Raises ``runbook.CatalogError`` if a runbook's front matter is wrong, and
    ``ExportError`` listing every page that cannot be read and every ``#anchor`` that
    names nothing in its article.
    """
    if not _SYS_ID.fullmatch(knowledge_base):
        raise ExportError([f"{knowledge_base!r} is not a sys_id: 32 hex digits in lower case"])
    docs = Path(docs)
    entries = runbook.catalog(docs, sections, [e.id for e in rooms.equipment])
    names = {e.id: e.name for e in rooms.equipment}
    pages: dict[Path, runbook.Entry | None] = {e.path: e for e in entries}
    problems: list[str] = []
    texts: dict[Path, str] = {}
    for entry in entries:
        texts[entry.path] = (docs / entry.path).read_text(encoding="utf-8")
        for target in sorted(structure.links(texts[entry.path])):
            linked = Path(os.path.normpath(entry.path.parent / unquote(target)))
            if linked.suffix == ".md" and linked not in pages:
                pages[linked] = None
    for path in (p for p, e in pages.items() if e is None):
        try:
            texts[path] = (docs / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            problems.append(f"{docs / path} cannot be read: {exc}")
    if problems:
        raise ExportError(problems)

    def section(path: Path) -> structure.Section | None:
        return max((s for s in sections if Path(s.path) in path.parents),
                   key=lambda s: len(s.path), default=None)  # fmt: skip

    outside = [path for path in pages if section(path) is None]
    if outside:
        raise ExportError([f"{docs / path} is linked from a runbook but is in no section, "
                           "so it has no category" for path in outside])  # fmt: skip

    top = Category(sys_id(knowledge_base, f"kb_category/{TOP}"), TOP, _value(TOP), None)
    filed = {section(path).path for path in pages}
    categories = [top] + [
        Category(sys_id(knowledge_base, f"kb_category/{TOP}/{s.title}"), s.title, _value(s.title),
                 top.sys_id)
        for s in sections if s.path in filed
    ]  # fmt: skip
    by_section = {c.label: c for c in categories[1:]}
    # A runbook by its identifier, which a new title and file name leave as it is.
    keys = {path: entry.id if entry else path.as_posix() for path, entry in pages.items()}
    ids = {path: sys_id(knowledge_base, f"kb_knowledge/{keys[path]}") for path in pages}
    unlinked: list[tuple[Path, str]] = []
    articles = []
    for path, entry in pages.items():
        title, body = _split(texts[path])
        if entry is not None:
            body += f"\n*Generated from {entry.id}; change the runbook, not this article.*\n"
            state = STATES[entry.status]
            keywords = (entry.id, *(names[e] for e in entry.equipment))
        else:
            body += f"\n*Generated from {path.as_posix()}; change the page, not this article.*\n"
            state, keywords = UNFILED_STATE, ()
        if title is None:
            problems.append(f"{docs / path} has no '# ' heading to be the article's title")
            continue
        articles.append(Article(ids[path], path, entry.id if entry else None, title,
                                by_section[section(path).title], state, keywords,
                                html(body, path, ids, unlinked)))  # fmt: skip
    problems += _anchor_problems(articles)
    if problems:
        raise ExportError(problems)
    return Export(knowledge_base, tuple(categories), tuple(articles), tuple(unlinked))


def _field(record: ET.Element, name: str, value: str, **attrs: str) -> None:
    ET.SubElement(record, name, attrs).text = value


def unload(exported: Export, when: datetime.datetime) -> bytes:
    """The export as ServiceNow's XML record format: one ``<unload>`` holding a
    ``kb_category`` record per category, parents first, then a ``kb_knowledge`` record
    per article, each to be inserted or, if its ``sys_id`` is there, updated."""
    root = ET.Element("unload", unload_date=when.strftime("%Y-%m-%d %H:%M:%S"))
    labels = {c.sys_id: c.label for c in exported.categories}
    for category in exported.categories:
        record = ET.SubElement(root, "kb_category", action="INSERT_OR_UPDATE")
        _field(record, "sys_id", category.sys_id)
        _field(record, "label", category.label)
        _field(record, "value", category.value)
        if category.parent is None:
            _field(record, "parent_table", "kb_knowledge_base")
            _field(record, "parent_id", exported.knowledge_base)
        else:
            _field(record, "parent_table", "kb_category")
            _field(record, "parent_id", category.parent)
        _field(record, "active", "true")
    for article in exported.articles:
        record = ET.SubElement(root, "kb_knowledge", action="INSERT_OR_UPDATE")
        _field(record, "sys_id", article.sys_id)
        _field(record, "short_description", article.title)
        _field(record, "kb_knowledge_base", exported.knowledge_base)
        path = f"{labels[article.category.parent]} > {article.category.label}"
        _field(record, "kb_category", article.category.sys_id, display_value=path)
        _field(record, "workflow_state", article.state)
        _field(record, "article_type", "text")
        _field(record, "meta", ", ".join(article.keywords))
        _field(record, "text", article.html)
    ET.indent(root)
    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    return (declaration + ET.tostring(root, encoding="unicode") + "\n").encode()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m classroom_runbooks.kb",
        description="Export the runbooks as ServiceNow knowledge articles (XML records)",
    )
    parser.add_argument("--knowledge-base", required=True, metavar="SYS_ID",
                        help="the sys_id of the knowledge base the articles go in")  # fmt: skip
    parser.add_argument("--out", type=Path, required=True, help="the XML file to write")
    parser.add_argument("--structure", type=Path, default=structure.DEFAULT_STRUCTURE)
    parser.add_argument("--inventory", type=Path, default=inventory.DEFAULT_INVENTORY)
    parser.add_argument("--docs", type=Path, default=structure.DEFAULT_DOCS)
    args = parser.parse_args(argv)
    try:
        layout = structure.load(args.structure)
        rooms = inventory.load(args.inventory, [s.prefix for s in layout if s.prefix])
        exported = export(args.docs, layout, rooms, args.knowledge_base)
        args.out.write_bytes(unload(exported, datetime.datetime.now(datetime.UTC)))
    except structure.StructureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (inventory.InventoryError, runbook.CatalogError, ExportError) as exc:
        for problem in exc.problems:
            print(f"problem: {problem}", file=sys.stderr)
        print(f"{len(exc.problems)} problems; nothing was written")
        return 1
    except OSError as exc:
        print(f"error: {args.out} cannot be written: {exc.strerror or exc}", file=sys.stderr)
        return 1
    runbooks = sum(1 for a in exported.articles if a.runbook)
    linked = len(exported.articles) - runbooks
    pages = "page" if linked == 1 else "pages"
    print(f"{len(exported.articles)} articles in {len(exported.categories)} categories: "
          f"{runbooks} runbooks and {linked} {pages} they link to")  # fmt: skip
    for page, target in exported.unlinked:
        print(f"kept as text: {page.as_posix()} links {target}, which is not exported")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
