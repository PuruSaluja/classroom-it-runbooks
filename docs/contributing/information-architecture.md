# Information architecture

How this site is organised, and why. The layout is defined in one file,
`structure.toml` at the repository's root, and checked on every change.

## Principles

- **Start from the call, not the org chart.** A technician arrives with a
  room and a symptom, so the two ways in are the room (what is installed
  there) and the fault (what to do about it). Policy and process sit in
  their own section, linked from the runbooks that need them.
- **One fault per runbook.** "Projector shows no signal" and "projector
  will not power on" are two runbooks, not two headings of a projector
  page, so each can be linked from a ticket, exported on its own, and kept
  short enough to follow on a phone in a classroom.
- **The inventory is data.** Rooms and their equipment are kept as data and
  rendered into pages, so the same source feeds the pages and the check
  that every installed device has a runbook.
- **Every section says who it is for.** A page written for a technician on
  shift reads differently from one written for a lead or an author.

## Sections

| Section | Folder | Readers | Purpose |
| --- | --- | --- | --- |
| Start here | `start/` | new technicians | Orientation and the onboarding path |
| Rooms | `rooms/` | technicians, leads | Each building's rooms and their equipment, linked to runbooks |
| Runbooks | `runbooks/` | technicians, new technicians | One fault per runbook, grouped by category |
| Audio-visual | `runbooks/av/` | technicians, new technicians | Projectors, displays, audio, cabling, control systems (`AV`) |
| Network | `runbooks/network/` | technicians, new technicians | Wall ports, the lectern's link, Wi-Fi (`NET`) |
| Peripherals | `runbooks/peripherals/` | technicians, new technicians | Document cameras, input devices, presenters, webcams, hubs (`PER`) |
| Account access | `runbooks/accounts/` | technicians, new technicians | Signing in at the lectern and to room systems (`ACC`) |
| Procedures | `procedures/` | technicians, leads | Escalation matrix, shift handoff, tickets |
| Reference | `reference/` | leads, authors | Knowledge-base export format and taxonomy mapping |
| Contributing | `contributing/` | authors | This page, the template and conventions |

## How pages link

- The home page links every top-level section, and each section's index
  links every section directly under it, so every page is reachable by
  following links down from the home page.
- A room's page links, for each piece of equipment in the room, the
  runbooks that cover it.
- A runbook ends with an escalation step that links into Procedures, so a
  fault its runbook cannot fix always has a next owner.
- Start here links into the other sections in the order a new technician
  should read them.

## Identifiers

- A runbook's identifier is `RB-`, its category's prefix and a three-digit
  number: `RB-AV-001`. Numbers are never reused, so a ticket that quotes an
  identifier always means the same runbook.
- A runbook's file is named by its identifier in lower case and a short
  slug: `runbooks/av/rb-av-001-projector-no-signal.md`.
- Room identifiers are set with the inventory.

## What is checked

`python -m classroom_runbooks.structure` reads `structure.toml` and checks
`docs/` against it: every section's folder exists with an `index.md` titled
as the section is; no folder is outside the structure (an `assets` folder,
anywhere, holds images); and the home page and each parent index link the
sections below them. It runs in CI with the tests.

To add a section, add it to `structure.toml`, create its folder with an
`index.md` whose first line is `# <title>`, and link it from the page above.
