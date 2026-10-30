# Runbook template

Every runbook is one Markdown file built from the same template, so a
technician finds the same parts in the same place on every page, and each
part can become a field of a knowledge-base article.

## Starting a runbook

```bash
python -m classroom_runbooks.runbook new AV "Projector shows no signal" --equipment laser-projector short-throw-projector
```

This writes a draft into the category's folder with the category's next
number, named by its identifier and its title:
`runbooks/av/rb-av-001-projector-shows-no-signal.md`. The equipment ids
must be ones the room inventory lists. It never overwrites a file. Then
fill in each section, link the runbook from its category's index page,
and follow the [authoring conventions](authoring-conventions.md).

## Front matter

The lines between the two `---` at the top are the runbook's details, in
YAML. They are not shown on the page; the site and the export read them.

| Key | What it holds | Example |
| --- | --- | --- |
| `id` | `RB-`, the category's prefix and a three-digit number; never changed, never reused | `RB-AV-001` |
| `title` | The fault as an instructor would report it; the page's heading repeats it | `"Projector shows no signal"` |
| `equipment` | The inventory ids of the equipment the runbook covers | `[laser-projector, short-throw-projector]` |
| `status` | `draft` until a second author has followed it on the equipment, then `current`; `retired` when it no longer applies (it stays, so its number is not given to another) | `current` |
| `reviewed` | The date the steps were last checked against the equipment | `2026-10-28` |

## Sections

After the heading and a sentence or two on what the runbook fixes (and
what it does not, with a link to the runbook that does), the sections
come in this order, each under a `##` heading of exactly this name.

| Section | What goes in it |
| --- | --- |
| Symptoms | What the instructor reports, in their words, and what you see in the room |
| Before you start | Time it takes, what to bring, what can hurt you or the equipment, and what is not yours to do |
| Checks | Numbered checks that change nothing, quickest and likeliest first, each with what you see if that part works and where to go if it does not |
| Fix | Numbered actions, one per step, each with what you see when it has worked |
| Escalate | When the runbook has not fixed it, and who takes it next, from the [escalation matrix](../procedures/escalation-matrix.md) in Procedures |
| Close the ticket | What to record, including the runbook's identifier, so a repeat fault can be traced |

## The template

The file is `templates/runbook.md` at the repository's root; `new` copies
it. Its links are written for a runbook's folder, two levels below the
site's root.

````markdown
---
id: RB-XX-000
title: "The fault, as an instructor would report it"
equipment: [equipment-id]
status: draft
reviewed: YYYY-MM-DD
---

# The fault, as an instructor would report it

One or two sentences: what this runbook fixes, and what it does not (with a
link to the runbook that does).

## Symptoms

- What the instructor reports, in their words.
- What you see in the room: lights, messages, sounds.

## Before you start

- **Time:** about N minutes.
- **Bring:** what to take to the room.
- **Safety:** anything that can hurt you or the equipment.
- **Do not:** anything outside a technician's remit.

## Checks

1. One check. **Expected:** what you see if this part is working. If not,
   go to step 1 of [Fix](#fix).
2. The next check.

## Fix

1. One action. **Expected:** what you see when it has worked.
2. The next action.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: who
takes it and how, from the [escalation matrix](../../procedures/escalation-matrix.md).

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
````
