# Knowledge-base export format

The runbooks are written here and exported to a ServiceNow knowledge base,
so the articles are never edited by hand and cannot drift from the pages.
The export holds every runbook and every page a runbook links to; today
that is the 29 runbooks and the [escalation matrix](../procedures/escalation-matrix.md),
which every runbook's Escalate section links. How the site's categories,
statuses and equipment become the knowledge base's is in the
[taxonomy mapping](taxonomy-mapping.md).

```bash
python -m classroom_runbooks.kb --knowledge-base 0123456789abcdef0123456789abcdef --out kb.xml
```

`--knowledge-base` is the `sys_id` of the knowledge base the articles go
in (32 hex digits, from the knowledge base's record). The command prints
what it exported and each link it had to drop, and writes nothing if
there is a problem: a docs folder that is missing or has no runbooks, a
runbook's front matter that does not check, a linked page with no `#`
title, a character XML cannot hold (a control character such as a form
feed, or U+FFFE), an `#anchor` that names nothing in its article, a link
to a page written in HTML rather than Markdown, or an image.

**Not yet loaded into an instance.** The file uses the field names of
ServiceNow's `kb_knowledge` and `kb_category` tables and its XML record
format, but it has not been imported into a ServiceNow instance from this
repository. Load it into a sub-production instance first and check the
articles there.

## The file

One `<unload>` element, as ServiceNow writes when it exports records to
XML, holding a `kb_category` record for each category, parents first, then
a `kb_knowledge` record for each article. Every record has
`action="INSERT_OR_UPDATE"`: it is added, or updated if a record with its
`sys_id` is there.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<unload unload_date="2026-10-31 18:00:00">
  <kb_category action="INSERT_OR_UPDATE">
    <sys_id>…</sys_id>
    <label>Audio-visual</label>
    …
  </kb_category>
  <kb_knowledge action="INSERT_OR_UPDATE">
    <sys_id>…</sys_id>
    <short_description>Projector shows no signal</short_description>
    …
  </kb_knowledge>
</unload>
```

`unload_date` is when the file was written, in UTC.

### An article: `kb_knowledge`

| Field | Value | From |
| --- | --- | --- |
| `sys_id` | 32 hex digits | the knowledge base and the runbook's identifier (see [Identifiers](#identifiers)) |
| `short_description` | `Projector shows no signal` | the page's `#` heading, which is a runbook's `title` |
| `kb_knowledge_base` | the `--knowledge-base` given | |
| `kb_category` | the category's `sys_id`, with `display_value="Classroom technology > Audio-visual"` | the page's section |
| `workflow_state` | `draft`, `published` or `retired` | a runbook's `status`; a page that is not a runbook is `draft` |
| `article_type` | `text` | always: the body is HTML |
| `meta` | `RB-AV-001, Laser projector, Short-throw projector, Presentation switcher` | the runbook's `id` and the names of its `equipment`; empty for a page that is not a runbook |
| `text` | HTML | the page after its front matter and `#` heading |

The article's number (`KB0010001`) is not in the file; the instance gives
each new article one. A ticket finds a runbook by its identifier, which is
in `meta` and in the article's last line.

### A category: `kb_category`

| Field | Value |
| --- | --- |
| `sys_id` | 32 hex digits, from the knowledge base and the category's label |
| `label` | `Audio-visual` |
| `value` | the label in lower case, words joined by `_`: `audio_visual` |
| `parent_table`, `parent_id` | `kb_knowledge_base` and the knowledge base's `sys_id` for the top category; `kb_category` and the top category's `sys_id` for the others |
| `active` | `true` |

## The article's text

The page's Markdown is turned into HTML, with tables, as the site renders
it. The front matter is left out, and so is the `#` heading, which is the
article's title. Each heading gets the id GitHub gives it
(`## Close the ticket` is `id="close-the-ticket"`, a repeated heading
`-1`, `-2`, the title counted), so a runbook's `[Fix](#fix)` still
reaches its Fix section. The last line says where the
article came from and that the page, not the article, is what to change:
*Generated from RB-AV-001; change the runbook, not this article.*

Links:

- a link to another exported page, inline or by reference, becomes a link
  to its article, `/kb_view.do?sys_kb_id=` and its `sys_id`, keeping any
  `#anchor`; one to a page's title is a link to its article, which shows
  the title;
- a link to a page that is not exported keeps its text and loses its
  target, and the command lists it. Today there are two, both on the
  escalation matrix: to the room inventory and to the shift handoff;
- a link with a scheme (`https:`, `mailto:`) is kept as it is.

Every `#anchor` must name an id in the article it reaches, or the export
fails. A link written in HTML (`<a href="…">`) is not pointed at an
article, so one to a page fails the export too. Links and ids shown as
code are text, and are not checked.

## Identifiers

Every `sys_id` is made from the knowledge base's `sys_id` and the record's
key, as a version 5 UUID written without hyphens. A runbook's key is its
identifier (`RB-AV-001`), which never changes, so a runbook given a new
title, and with it a new file name, updates its article. Another page's
key is its path in `docs/` (`procedures/escalation-matrix.md`), and a
category's is its label. Exporting again gives the same ones, so importing
a new export updates the articles the last one made instead of adding
copies; exporting to another knowledge base gives different ones.

## What is not exported

The room pages, the section indexes and every page no runbook links to;
a runbook's `reviewed` date; and images, which no page has yet: a page
that shows one fails the export, as the article would show a broken
image.
