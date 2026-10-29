# Authoring conventions

How runbooks on this site are written, so that any technician can follow
any of them in a classroom, on a phone, with an instructor waiting. The
parts of a runbook are set by the [runbook template](runbook-template.md);
these are the rules for what goes in them.

## One fault, named as it is reported

- A runbook covers one fault. If two faults share most of their steps,
  write two runbooks and link them, rather than one that branches.
- Title it with the symptom as an instructor or a ticket would put it:
  "Projector shows no signal", not the cause ("HDMI handshake failure") or
  the device ("Projector").
- Titles are in sentence case, without a full stop, and at most 80
  characters.
- The introduction says what the runbook does not cover, and links the
  runbook that does.

## Write for the room

- Speak to the technician, in the imperative: "Press **Input** on the
  switcher", not "The input should be selected".
- One action per numbered step, followed by **Expected:** and what the
  technician sees when it has worked.
- Call equipment what the room inventory calls it ("Presentation
  switcher"), and buttons and menu items what their labels say, in bold:
  **Input**, **Settings > Display**.
- Say where things are: "on the left side of the lectern", "behind the
  rack door".
- Use plain words. Spell out an abbreviation the first time a page uses
  it: "EDID (the description a display gives of what it can show)".
- Use US English, as the equipment's labels and the knowledge base do.
- Keep it short enough to follow on a phone: if Checks and Fix together
  run past about fifteen steps, the runbook probably covers two faults.

## Checks before fixes

- Order checks by how quick they are and how likely they are to find the
  fault: the cable and the selected input before the firmware.
- A check changes nothing. Anything that changes a setting, a cable or
  power belongs in Fix.
- Each check says where to go if it fails: a step of Fix, another
  runbook, or Escalate.

## Safety and remit

- Before you start names anything that can hurt the technician or the
  equipment: ladders and lifts, hot lamps and vents, mains power.
- A runbook never asks a technician to open a projector, display or
  amplifier, or to touch mains wiring, and work at height (a ceiling
  projector, a speaker) is never done alone.
- It states what a technician must not do, and who does it instead: the
  service desk resets passwords and unlocks accounts; facilities handles
  power and furniture.
- **No credentials, ever.** No passwords, PINs, admin codes or account
  names, not even a shared one. Say who holds them and how an authorized
  person asks.

## Escalate and close

- Every runbook ends with Escalate, linking the escalation matrix in
  Procedures, so a fault its runbook cannot fix always has a next owner.
- Close the ticket says what to record, including the runbook's
  identifier, so repeat faults in a room or on a device can be found.

## Identifiers, files and status

- Start a runbook with `python -m classroom_runbooks.runbook new`, as the
  [template page](runbook-template.md#starting-a-runbook) shows: it takes
  the category's next number and names the file.
- A runbook's identifier never changes, and its number is never given to
  another runbook. To retire one, set `status: retired` and link its
  replacement in the introduction; do not delete the file.
- A new runbook is `draft` until a second author has followed it on the
  equipment it covers; then it is `current`.
- `reviewed` is the date the steps were last checked against the
  equipment. A draft's is the day it was written, as `runbook new` fills
  it in; set it when a second author first follows the steps. Check each
  current runbook at least once a year, and again whenever the equipment
  it covers changes.

## Links and images

- Link other pages by relative path. Link a room by its building's page
  and the room's heading: `../../rooms/ald.md#ald-104` from a runbook.
- Put images in an `assets` folder beside the page, and give each one alt
  text that says what it shows ("The switcher's input buttons, HDMI 1
  lit"), not "image".

## Review

- Every new runbook, and every change to a current one, is reviewed by a
  second author before it is published, following the steps on the
  equipment where they can.
- The reviewer checks the rules on this page by reading the runbook.
  What the site checks automatically is set out in
  [Information architecture](information-architecture.md#what-is-checked).
