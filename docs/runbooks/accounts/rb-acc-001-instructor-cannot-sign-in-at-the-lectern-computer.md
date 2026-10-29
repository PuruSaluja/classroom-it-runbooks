---
id: RB-ACC-001
title: "Instructor cannot sign in at the lectern computer"
equipment: [lectern-computer]
status: draft
reviewed: 2026-10-29
---

# Instructor cannot sign in at the lectern computer

An instructor's campus account is refused at the lectern computer's
sign-in screen, or signing in never finishes. This runbook tells a fault
in the room from a problem with the account, and hands the second to the
service desk. A technician never asks for, types or resets anyone's
password. If the computer has no network, follow
[Lectern computer has no network connection](../network/rb-net-001-lectern-computer-has-no-network-connection.md).

## Symptoms

- "It won't let me log in", "it says my password is wrong", "it's stuck on
  'Welcome'".
- The sign-in screen says the password is incorrect, the account is
  locked or disabled, or the domain is not available.
- A sign-in approval does not arrive on the instructor's phone.

## Before you start

- **Time:** about 10 minutes.
- **Bring:** nothing; the instructor uses their own phone for any
  sign-in approval.
- **Safety:** look away from the keyboard while the instructor types, and
  never write down or repeat a password, a code or an approval number.
- **Do not:** sign the instructor in with your own account or any shared
  one, reset, unlock or change a password, or ask the instructor to tell
  you theirs. Accounts are for the service desk.

## Checks

1. Read the sign-in screen's message, without the instructor's password on
   screen. **Expected:** none, or "incorrect password". If it says the
   account is locked or disabled, or the password has expired, go to
   [Escalate](#escalate): only the service desk can change that. If it is
   waiting for the instructor to approve the sign-in on their phone, go to
   the next check; otherwise skip it.
2. Ask the instructor whether the approval request has reached their
   phone. **Expected:** it arrives within a minute. If it has not, go to
   step 3 of [Fix](#fix).
3. Look at the keyboard's caps lock light, and the input language shown on
   the sign-in screen. **Expected:** caps lock off, and the language the
   instructor types in. If not, go to step 1 of
   [Fix](#fix).
4. Look at the sign-in screen's network icon. **Expected:** connected. If it
   shows no network, follow
   [Lectern computer has no network connection](../network/rb-net-001-lectern-computer-has-no-network-connection.md).
5. Ask the instructor whether they can sign in to campus services on their
   own phone or laptop. **Expected:** they can. If they cannot sign in
   anywhere, the fault is the account: go to [Escalate](#escalate). If they
   can, go to step 2 of [Fix](#fix).

## Fix

1. Turn caps lock off, or set the input language back, and let the
   instructor type their password again. **Expected:** they are signed in.
2. Restart the lectern computer from the sign-in screen's power menu, and
   let the instructor sign in again. **Expected:** they are signed in, and
   the desktop appears within a couple of minutes.
3. If the sign-in approval does not arrive, ask the instructor to open
   their authenticator app themselves, or to choose another approval method
   the screen offers. **Expected:** they approve on their phone and are
   signed in. If not, escalate.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
the service desk, through the [escalation matrix](../../procedures/index.md).
The instructor contacts the service desk themselves to prove who they are;
the ticket gives the room, the time and the exact message on the screen,
never a password or code. Offer a cable for their laptop in the meantime,
if the room has one.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
