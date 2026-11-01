"""The site's build hooks, which ``mkdocs.yml`` names under ``hooks:``.

- ``on_config`` sets the navigation from ``structure.toml``: the home page, then each
  section in the file's order, its index first, then its pages in the order the index
  links them (any it does not link after, by file name), then the sections under it;
- ``on_page_markdown`` gives each page a new ``validate.Slugs`` for its heading ids,
  so they are GitHub's anchors, the ones the validator checks every ``#anchor``
  against, a repeated heading numbered from ``-1`` as GitHub numbers it; and a page
  written from the inventory (the room pages) gets no edit button, as an edit to it
  would be overwritten.

``mkdocs build --strict`` then fails on a link or ``#anchor`` that reaches nothing,
a page left out of the navigation, or any other warning.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import unquote

from classroom_runbooks import inventory, structure, validate


def _pages(folder: Path, docs: Path) -> list[str]:
    """A section's pages other than its index, in the order its index links them."""
    index = folder / "index.md"
    pages = sorted(p for p in folder.glob("*.md") if p != index)
    linked: list[Path] = []
    if index.is_file():
        for _, target in structure.targets(index.read_text(encoding="utf-8")):
            path = target.split("#", 1)[0]
            if not path or structure.external(path):
                continue
            page = Path(os.path.normpath(folder / unquote(path)))
            if page in pages and page not in linked:
                linked.append(page)
    ordered = linked + [p for p in pages if p not in linked]
    return [p.relative_to(docs).as_posix() for p in ordered]


def nav(sections: Sequence[structure.Section], docs: Path) -> list:
    """The navigation: the home page, then each top-level section, as MkDocs takes it."""
    docs = Path(docs)

    def entries(section: structure.Section) -> list:
        children = [s for s in sections if s.parent == section.path]
        return [
            f"{section.path}/index.md",
            *_pages(docs / section.path, docs),
            *({child.title: entries(child)} for child in children),
        ]

    return ["index.md", *({s.title: entries(s)} for s in sections if s.parent is None)]


def on_config(config):
    root = Path(config.config_file_path).parent
    config.nav = nav(structure.load(root / structure.DEFAULT_STRUCTURE), Path(config.docs_dir))
    return config


def on_page_markdown(markdown, page, config, files):
    # MkDocs renders each page with a new Markdown, which reads this then.
    config.mdx_configs.setdefault("toc", {})["slugify"] = validate.Slugs()
    if inventory.GENERATED in markdown:
        page.edit_url = None  # written from the inventory: an edit here is overwritten
    return markdown
