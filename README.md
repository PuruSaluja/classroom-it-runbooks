# Classroom IT Runbooks

Runbooks, a room inventory and support procedures for the technology in a
campus's classrooms (projectors, displays, audio, control systems, network,
peripherals and account access), written in Markdown, with Python tools that
check them and export them to ServiceNow's knowledge base.

> **Status:** in progress. The site's sections and the check that keeps
> `docs/` to them are in place; the content and the other tools are built in
> the order of [Parts](#parts).

## What this repository is, and is not

The runbooks are written as a student technician on a classroom support team
would use them: one fault, its symptoms, the checks in order, the fix, and
when to hand it on. They are general to the equipment, not copied from any
institution's knowledge base.

**The room inventory is illustrative.** Buildings, room numbers and the
equipment in each room are made up to resemble a large campus; they are not
any university's real inventory, which would not be published.

What the repository can show is what it contains: how many rooms and
runbooks there are, and whether every piece of equipment in every room has a
runbook, which its tools check. It cannot show what happened when runbooks
like these were used by a real support team (fewer repeat tickets, faster
onboarding); where those are mentioned they are reported, not demonstrated
here.

## How the site is organised

The pages live in [`docs/`](docs/index.md), in sections laid out by
[`structure.toml`](structure.toml): each section's folder, title, readers and
purpose, and for each runbook category the prefix its runbooks' identifiers
carry (`RB-AV-001`).

| Section | For | What is in it |
| --- | --- | --- |
| Start here | new technicians | Orientation and the onboarding path |
| Rooms | technicians, leads | Each building's rooms and their equipment, linked to runbooks |
| Runbooks: audio-visual (AV), network (NET), peripherals (PER), account access (ACC) | technicians | One fault per runbook |
| Procedures | technicians, leads | Escalation matrix, shift handoff, tickets |
| Reference | leads, authors | Knowledge-base export format and taxonomy mapping |
| Contributing | authors | How the site is organised, the template and conventions |

[`docs/contributing/information-architecture.md`](docs/contributing/information-architecture.md)
explains the layout: why the two ways in are the room and the fault, why
each runbook covers one fault, how pages link, and how identifiers are
formed.

```bash
python -m classroom_runbooks.structure    # check docs/ against structure.toml
```

The check prints the outline and fails if a section's folder or titled
index page is missing, a folder under `docs/` is not a section, or a page
does not link the sections below it. CI runs it with the tests, which also
check that every relative link in `docs/` reaches a file.

## Parts

| Part | State |
| --- | --- |
| Repository scaffold and information architecture | done |
| Room inventory: 200+ classrooms with equipment profiles | to come |
| Runbook template and authoring conventions | to come |
| AV runbooks: projectors, displays, audio, cabling, control systems | to come |
| Network, peripheral and account-access runbooks | to come |
| Escalation matrix, shift handoff and the onboarding path for new technicians | to come |
| Validator: required sections, room-to-runbook coverage, dead cross-links | to come |
| ServiceNow knowledge-base export and taxonomy mapping | to come |
| MkDocs Material site, with the validator in CI | to come |
| Published site | to come |

## Development

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -c constraints.txt -e ".[dev]"   # bin/ on Linux and macOS
pytest
ruff check . && ruff format --check .
```

## License

MIT; see [LICENSE](LICENSE).
