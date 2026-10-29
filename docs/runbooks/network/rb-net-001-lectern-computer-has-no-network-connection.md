---
id: RB-NET-001
title: "Lectern computer has no network connection"
equipment: [lectern-network]
status: draft
reviewed: 2026-10-29
---

# Lectern computer has no network connection

The lectern computer cannot reach the internet or the campus network:
web pages, the learning platform and video meetings do not load. If the
computer cannot be signed in to at all, follow
[Instructor cannot sign in at the lectern computer](../accounts/rb-acc-001-instructor-cannot-sign-in-at-the-lectern-computer.md);
if a laptop in the room has no connection either, the fault may be wider:
follow [Wi-Fi is slow or keeps dropping in the classroom](rb-net-003-wi-fi-is-slow-or-keeps-dropping-in-the-classroom.md)
for wireless, or [Wall port gives no network connection](rb-net-002-wall-port-gives-no-network-connection.md)
for a wired one.

## Symptoms

- "The internet isn't working on the computer", "nothing loads".
- The computer's network icon shows no connection, a warning sign, or "No
  internet".
- Pages load on a phone or laptop in the room but not on the lectern
  computer.

## Before you start

- **Time:** about 10 minutes.
- **Bring:** a short known-good network cable and a laptop with a wired
  network port or adapter.
- **Safety:** the lectern's network socket may be inside the lectern
  cabinet; keep clear of the power strips there.
- **Do not:** change the computer's network settings, sign in to it as an
  administrator, or patch cables in a network closet. Network equipment
  outside the room is for the network team.

## Checks

1. Look at the network icon on the lectern computer. **Expected:** a wired
   connection with no warning. If it shows a cable unplugged, go to step 1
   of [Fix](#fix); if it shows a warning or "No internet", go to step 2 of
   [Fix](#fix).
2. Look at the network socket at the back of the computer. **Expected:** a
   cable clipped in, with a lit or blinking light beside the socket. If no
   light is lit, go to step 1 of [Fix](#fix).
3. Plug your laptop into the lectern's network cable in place of the
   computer. **Expected:** your laptop connects. If it does, the fault is
   the lectern computer: go to step 3 of [Fix](#fix). If it does not, the
   fault is the lectern's network link: go to [Escalate](#escalate).

## Fix

1. Unplug the network cable at the computer and plug it back in until it
   clicks; if the cable is damaged, replace it with your known-good one.
   **Expected:** the socket's light comes on and, within a minute, the
   network icon shows a connection.
2. Restart the lectern computer from its Start menu, once the instructor
   has saved their work. **Expected:** after signing in, pages load.
3. If the computer still has no connection while your laptop has one on
   the same cable, escalate to the service desk for the computer.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold:
to the network team when no device connects on the lectern's cable, or
to the service desk when only the lectern computer fails, through the
[escalation matrix](../../procedures/index.md). Say what the network icon
and the socket's light showed.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
