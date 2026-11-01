import datetime
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from classroom_runbooks import inventory, kb, runbook, structure

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = structure.load(ROOT / "structure.toml")
ROOMS = inventory.load(ROOT / "inventory", [s.prefix for s in SECTIONS if s.prefix])
BASE = "0123456789abcdef0123456789abcdef"
WHEN = datetime.datetime(2026, 10, 31, 12, 0, tzinfo=datetime.UTC)
NO_SIGNAL = Path("runbooks/av/rb-av-001-projector-shows-no-signal.md")


@pytest.fixture(scope="module")
def exported() -> kb.Export:
    return kb.export(ROOT / "docs", SECTIONS, ROOMS, BASE)


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    """A copy of the repository's docs, to change."""
    shutil.copytree(ROOT / "docs", tmp_path / "docs")
    return tmp_path / "docs"


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def article(exported: kb.Export, source: Path) -> kb.Article:
    return next(a for a in exported.articles if a.source == source)


def test_sys_ids_are_stable_hex_and_differ_by_knowledge_base() -> None:
    first = kb.sys_id(BASE, "kb_knowledge/runbooks/av/x.md")
    assert re.fullmatch(r"[0-9a-f]{32}", first)
    assert kb.sys_id(BASE, "kb_knowledge/runbooks/av/x.md") == first
    assert kb.sys_id("f" * 32, "kb_knowledge/runbooks/av/x.md") != first


def test_every_runbook_and_the_page_they_all_link_is_an_article(exported: kb.Export) -> None:
    entries = runbook.catalog(ROOT / "docs", SECTIONS, [e.id for e in ROOMS.equipment])
    runbooks = [a for a in exported.articles if a.runbook]
    assert [(a.runbook, a.source) for a in runbooks] == [(e.id, e.path) for e in entries]
    others = [a.source.as_posix() for a in exported.articles if not a.runbook]
    assert others == ["procedures/escalation-matrix.md"]
    assert len({a.sys_id for a in exported.articles}) == len(exported.articles)


def test_categories_are_the_sections_under_one_top_category(exported: kb.Export) -> None:
    top, *below = exported.categories
    assert (top.label, top.parent) == (kb.TOP, None)
    assert [c.label for c in below] == [
        "Audio-visual", "Network", "Peripherals", "Account access", "Procedures"
    ]  # fmt: skip
    assert {c.parent for c in below} == {top.sys_id}
    assert article(exported, NO_SIGNAL).category.label == "Audio-visual"


def test_an_article_is_the_page_without_front_matter_or_title(exported: kb.Export) -> None:
    found = article(exported, NO_SIGNAL)
    assert found.title == "Projector shows no signal"
    assert found.state == "draft"
    assert found.keywords[:2] == ("RB-AV-001", "Laser projector")
    assert "<h1" not in found.html and "reviewed:" not in found.html
    assert found.html.startswith("<p>The projector is on")
    assert '<h2 id="close-the-ticket">Close the ticket</h2>' in found.html
    assert found.html.endswith(
        "<p><em>Generated from RB-AV-001; change the runbook, not this article.</em></p>"
    )


def test_links_between_pages_become_links_between_articles(exported: kb.Export) -> None:
    hrefs = [h for a in exported.articles for h in re.findall(r'href="([^"]*)"', a.html)]
    assert hrefs and not [h for h in hrefs if ".md" in h]
    found = article(exported, NO_SIGNAL)
    laptop = article(exported, Path("runbooks/av/rb-av-012-laptop-shows-no-picture-through-"
                                    "the-hdmi-or-usb-c.md"))  # fmt: skip
    matrix = article(exported, Path("procedures/escalation-matrix.md"))
    assert f'href="/kb_view.do?sys_kb_id={laptop.sys_id}"' in found.html
    assert f'href="/kb_view.do?sys_kb_id={matrix.sys_id}"' in found.html
    assert 'href="#fix"' in found.html and '<h2 id="fix">' in found.html


def test_a_link_to_a_page_not_exported_keeps_its_text(exported: kb.Export) -> None:
    unlinked = [(page.as_posix(), target) for page, target in exported.unlinked]
    assert unlinked == [
        ("procedures/escalation-matrix.md", "../rooms/index.md"),
        ("procedures/escalation-matrix.md", "shift-handoff.md"),
    ]
    matrix = article(exported, Path("procedures/escalation-matrix.md"))
    assert "<span>Shift handoff</span>" in matrix.html


def test_an_anchor_on_another_page_is_kept_and_must_name_an_id(docs: Path) -> None:
    page = docs / NO_SIGNAL
    edit(page, "(rb-av-002-projector-will-not-turn-on.md)",
         "(rb-av-002-projector-will-not-turn-on.md#fix)")  # fmt: skip
    found = article(kb.export(docs, SECTIONS, ROOMS, BASE), NO_SIGNAL)
    assert re.search(r'href="/kb_view\.do\?sys_kb_id=[0-9a-f]{32}#fix"', found.html)
    edit(page, "on.md#fix)", "on.md#no-such-heading)")
    with pytest.raises(kb.ExportError) as error:
        kb.export(docs, SECTIONS, ROOMS, BASE)
    assert error.value.problems == (
        f"{NO_SIGNAL.as_posix()}: the link /kb_view.do?sys_kb_id="
        f"{kb.sys_id(BASE, 'kb_knowledge/RB-AV-002')}"
        "#no-such-heading names no id in its article",
    )


def test_an_anchor_on_the_same_page_must_name_an_id(docs: Path) -> None:
    edit(docs / NO_SIGNAL, "step 1 of [Fix](#fix)", "step 1 of [Fix](#fixes)")
    with pytest.raises(kb.ExportError, match="the link #fixes names no id"):
        kb.export(docs, SECTIONS, ROOMS, BASE)


def test_a_repeated_heading_is_numbered_as_github_numbers_it(docs: Path) -> None:
    edit(docs / NO_SIGNAL, "## Escalate\n", "## Fix\n\nAgain.\n\n## Escalate\n")
    edit(docs / NO_SIGNAL, "step 1 of [Fix](#fix)", "step 1 of [Fix](#fix-1)")
    found = article(kb.export(docs, SECTIONS, ROOMS, BASE), NO_SIGNAL)
    assert '<h2 id="fix">' in found.html and '<h2 id="fix-1">' in found.html


def test_status_sets_the_workflow_state(docs: Path) -> None:
    edit(docs / NO_SIGNAL, "status: draft", "status: current")
    other = docs / "runbooks/av/rb-av-002-projector-will-not-turn-on.md"
    edit(other, "status: draft", "status: retired")
    states = {a.runbook: a.state for a in kb.export(docs, SECTIONS, ROOMS, BASE).articles}
    assert (states["RB-AV-001"], states["RB-AV-002"], states["RB-AV-003"]) == (
        "published", "retired", "draft"
    )  # fmt: skip


def test_a_linked_page_without_a_title_or_section_is_refused(docs: Path) -> None:
    edit(docs / "procedures/escalation-matrix.md", "# Escalation matrix\n", "")
    with pytest.raises(kb.ExportError, match="escalation-matrix.md has no '# ' heading"):
        kb.export(docs, SECTIONS, ROOMS, BASE)
    edit(docs / NO_SIGNAL, "\n## Symptoms", "\nSee [the home page](../../index.md).\n\n## Symptoms")
    with pytest.raises(kb.ExportError, match=r"index\.md is linked from a runbook but is in no"):
        kb.export(docs, SECTIONS, ROOMS, BASE)


def test_a_knowledge_base_that_is_not_a_sys_id_is_refused() -> None:
    for bad in ("", "0123456789ABCDEF0123456789ABCDEF", BASE + "0", "kb_it"):
        with pytest.raises(kb.ExportError, match="is not a sys_id"):
            kb.export(ROOT / "docs", SECTIONS, ROOMS, bad)


def test_the_xml_holds_every_record_and_reads_back(exported: kb.Export) -> None:
    data = kb.unload(exported, WHEN)
    assert data.startswith(b'<?xml version="1.0" encoding="UTF-8"?>\n<unload unload_date=')
    root = ET.fromstring(data)
    assert (root.tag, root.get("unload_date")) == ("unload", "2026-10-31 12:00:00")
    assert [r.tag for r in root] == ["kb_category"] * 6 + ["kb_knowledge"] * 30
    assert {r.get("action") for r in root} == {"INSERT_OR_UPDATE"}
    categories = {r.findtext("sys_id"): r for r in root.iter("kb_category")}
    top = categories[exported.categories[0].sys_id]
    assert (top.findtext("parent_table"), top.findtext("parent_id")) == ("kb_knowledge_base", BASE)
    for record, expected in zip(root.iter("kb_knowledge"), exported.articles, strict=True):
        assert record.findtext("sys_id") == expected.sys_id
        assert record.findtext("short_description") == expected.title
        assert record.findtext("text") == expected.html
        assert record.findtext("kb_knowledge_base") == BASE
        assert record.findtext("workflow_state") == expected.state
        assert record.findtext("meta") == ", ".join(expected.keywords)
        category = record.find("kb_category")
        assert category.text in categories
        assert category.get("display_value") == f"{kb.TOP} > {expected.category.label}"


def test_exporting_again_gives_the_same_xml(exported: kb.Export) -> None:
    again = kb.export(ROOT / "docs", SECTIONS, ROOMS, BASE)
    assert kb.unload(again, WHEN) == kb.unload(exported, WHEN)


def test_the_command_writes_the_xml(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    out = tmp_path / "kb.xml"
    assert kb.main(["--knowledge-base", BASE, "--out", str(out)]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == "30 articles in 6 categories: 29 runbooks and 1 page they link to"
    assert printed[1] == ("kept as text: procedures/escalation-matrix.md links "
                          "../rooms/index.md, which is not exported")  # fmt: skip
    assert printed[-1] == f"wrote {out}"
    assert len(ET.parse(out).getroot().findall("kb_knowledge")) == 30


def test_the_command_writes_nothing_when_there_are_problems(
    tmp_path: Path, docs: Path, capsys, monkeypatch
) -> None:
    monkeypatch.chdir(ROOT)
    edit(docs / NO_SIGNAL, "(#fix)", "(#fixes)")
    out = tmp_path / "kb.xml"
    assert kb.main(["--knowledge-base", BASE, "--out", str(out), "--docs", str(docs)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "1 problems; nothing was written\n"
    assert "the link #fixes names no id" in captured.err
    assert not out.exists()
    assert kb.main(["--knowledge-base", "KB0001", "--out", str(out)]) == 1
    assert "'KB0001' is not a sys_id" in capsys.readouterr().err
    assert not out.exists()


def test_a_runbook_s_article_is_keyed_on_its_identifier_not_its_file(docs: Path) -> None:
    before = {a.runbook: a.sys_id for a in kb.export(docs, SECTIONS, ROOMS, BASE).articles}
    old = docs / "runbooks/av/rb-av-002-projector-will-not-turn-on.md"
    edit(old, "Projector will not turn on", "Projector does not power up")
    edit(old, "# Projector will not turn on", "# Projector does not power up")
    old.rename(docs / "runbooks/av/rb-av-002-projector-does-not-power-up.md")
    for page in (docs / "runbooks/av").glob("rb-*.md"):
        text = page.read_text(encoding="utf-8")
        text = text.replace(old.name, "rb-av-002-projector-does-not-power-up.md")
        page.write_text(text, encoding="utf-8", newline="\n")
    after = kb.export(docs, SECTIONS, ROOMS, BASE)
    assert {a.runbook: a.sys_id for a in after.articles} == before
    assert before["RB-AV-002"] == kb.sys_id(BASE, "kb_knowledge/RB-AV-002")
    matrix = article(after, Path("procedures/escalation-matrix.md"))
    assert matrix.sys_id == kb.sys_id(BASE, "kb_knowledge/procedures/escalation-matrix.md")


def test_a_docs_folder_that_is_missing_or_has_no_runbooks_is_refused(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    with pytest.raises(kb.ExportError, match="is not a folder"):
        kb.export(tmp_path / "docs", SECTIONS, ROOMS, BASE)
    (tmp_path / "docs").mkdir()
    with pytest.raises(kb.ExportError, match="has no runbooks in the categories' folders"):
        kb.export(tmp_path / "docs", SECTIONS, ROOMS, BASE)
    monkeypatch.chdir(ROOT)
    out = tmp_path / "kb.xml"
    args = ["--knowledge-base", BASE, "--out", str(out), "--docs", str(tmp_path / "nowhere")]
    assert kb.main(args) == 1
    assert "is not a folder" in capsys.readouterr().err
    assert not out.exists()
