---
id: RB-ACC-002
title: "Student cannot sign in at a lab workstation"
equipment: [lab-workstations]
status: draft
reviewed: 2026-10-29
---

# Student cannot sign in at a lab workstation

A student's campus account is refused at one of a computer lab's
workstations, or signing in never finishes, while other students sign in.
If many workstations fail at once, follow
[Lab computers have no network connection](../network/rb-net-004-lab-computers-have-no-network-connection.md);
for the instructor's lectern computer, follow
[Instructor cannot sign in at the lectern computer](rb-acc-001-instructor-cannot-sign-in-at-the-lectern-computer.md).

## Symptoms

- "I can't log in on this computer", "it says I don't have access".
- The sign-in screen says the password is incorrect, the account is
  locked, or the student is not allowed to sign in at this computer.
- Signing in stays on "Preparing" or "Welcome".

## Before you start

- **Time:** about 5 minutes.
- **Bring:** nothing.
- **Safety:** look away while the student types, and never write down or
  repeat a password or code.
- **Do not:** sign a student in with your account or a shared one, reset or
  unlock an account, or give a student access to a lab. Accounts and lab
  access are for the service desk.

## Checks

1. Read the sign-in screen's message. **Expected:** none, or "incorrect
   password". If it says the account is locked or disabled, or the student
   is not allowed to sign in here, go to [Escalate](#escalate).
2. Look at the keyboard's caps lock light and the input language on the
   sign-in screen. **Expected:** caps lock off, the student's language. If
   not, go to step 1 of [Fix](#fix).
3. Ask the student to try another workstation in the lab. **Expected:**
   they sign in there, which shows the first workstation is the fault: go
   to step 2 of [Fix](#fix). If they cannot sign in there either, the
   account is the fault: go to [Escalate](#escalate).

## Fix

1. Turn caps lock off or set the language back, and let the student type
   their password again. **Expected:** they are signed in.
2. Let the student use the working workstation, and put an "Out of order:
   reported" note on the other one with the date. Then restart it from the
   sign-in screen's power menu. **Expected:** after the restart, its
   sign-in screen shows no warning. If it still refuses sign-ins, escalate.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
the service desk, through the [escalation matrix](../../procedures/index.md).
A student with an account problem contacts the service desk themselves;
a workstation fault is reported with the workstation's number and the
message on its screen.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
