---
id: RB-ACC-003
title: "Files or apps are missing after signing in"
equipment: [lectern-computer, lab-workstations]
status: draft
reviewed: 2026-10-29
---

# Files or apps are missing after signing in

Someone signs in at the lectern computer or a lab workstation, but their
desktop is empty, their cloud files or network drive are not there, or an
app the course needs is missing. If they cannot sign in at all, follow
[Instructor cannot sign in at the lectern computer](rb-acc-001-instructor-cannot-sign-in-at-the-lectern-computer.md)
or [Student cannot sign in at a lab workstation](rb-acc-002-student-cannot-sign-in-at-a-lab-workstation.md).

## Symptoms

- "All my files are gone", "my H: drive isn't there", "the software for
  this class isn't on the computer".
- A message that a temporary profile is in use, or that settings could not
  be loaded.
- The desktop is the default one, with none of the user's shortcuts.

## Before you start

- **Time:** about 10 minutes.
- **Bring:** the course's software list, if the ticket names an app.
- **Safety:** do not look through the user's files; check only that they
  are there.
- **Do not:** install software, copy files between accounts, or delete a
  profile. Software and profiles are for the service desk.

## Checks

1. Look for a message about a temporary profile, near the clock or in a
   window after signing in. **Expected:** none. If there is one, go to step
   1 of [Fix](#fix).
2. Ask the user to open their cloud storage in the web browser.
   **Expected:** their files are there. If they are, the files are not
   lost: go to step 2 of [Fix](#fix).
3. For a missing app, look for it in the Start menu by name, and compare it
   with the course's software list. **Expected:** it is there. If it is not
   on the list, it was never installed in this room: go to
   [Escalate](#escalate). If it is on the list and missing, go to step 3 of
   [Fix](#fix).

## Fix

1. Ask the user to save nothing to this desktop, sign out, and sign in
   again after a minute. **Expected:** their own desktop loads. If the
   temporary profile comes back, escalate.
2. Show the user their files in the browser, or wait a few minutes after
   signing in for the network drive to connect, and open it from the file
   explorer. **Expected:** the user can open the file they need.
3. Sign the user out and restart the computer, as some software is added
   at start-up. **Expected:** after signing in again, the app is in the
   Start menu. If it is not, escalate.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
the service desk, through the [escalation matrix](../../procedures/escalation-matrix.md),
with the computer's name or the lab workstation's number, the message
shown, and for software, the app and the course that needs it.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
