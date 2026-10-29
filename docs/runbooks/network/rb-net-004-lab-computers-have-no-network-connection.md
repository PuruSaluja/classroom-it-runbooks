---
id: RB-NET-004
title: "Lab computers have no network connection"
equipment: [room-switch, lab-workstations]
status: draft
reviewed: 2026-10-29
---

# Lab computers have no network connection

Several or all student workstations in a computer lab cannot reach the
network, so students cannot sign in or nothing loads. For the lectern
computer alone, follow
[Lectern computer has no network connection](rb-net-001-lectern-computer-has-no-network-connection.md).

## Symptoms

- "None of the lab computers have internet", "students can't log in".
- The sign-in screen says there is no network or the domain is not
  available.
- A row of workstations, or the whole room, fails at once.

## Before you start

- **Time:** about 15 minutes.
- **Bring:** a laptop with a wired network port or adapter, and a short
  known-good network cable.
- **Safety:** the room's network switch is in a locked cabinet or under a
  bench: do not move it, and keep clear of the power strips beside it.
- **Do not:** unplug, restart or re-cable the room switch beyond the checks
  below, and do not sign in to workstations as an administrator. The switch
  is for the network team; the workstations are for the service desk.

## Checks

1. Count the workstations affected. **Expected:** only one or two, with the
   rest of the room working: go to step 1 of [Fix](#fix). If a whole row or
   the whole room is affected, go on to the next check.
2. Look at the room switch's lights, through its cabinet's door if it is
   locked. **Expected:** its power light is on and its port lights blink. If
   its power light is off, go to step 2 of [Fix](#fix); if all port lights
   are dark, go to [Escalate](#escalate).
3. Plug your laptop into a workstation's network cable in place of the
   workstation. **Expected:** your laptop connects. If it does, the fault
   is with the workstations: go to step 3 of [Fix](#fix). If it does not,
   go to [Escalate](#escalate).

## Fix

1. At each affected workstation, seat its network cable at both ends until
   it clicks, and restart the workstation. **Expected:** it shows the
   sign-in screen with no network warning.
2. Check that the switch's power cable is seated in its power strip, and
   that the strip is switched on; do not switch anything off. **Expected:**
   the switch's lights come on and, after a few minutes, the workstations
   connect. If not, escalate.
3. If your laptop connects but the workstations do not, escalate to the
   service desk: it is likely their configuration, not the network.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
the network team when the room switch or the cabling has failed, or to the
service desk for the workstations, through the
[escalation matrix](../../procedures/index.md). Say how many workstations
failed, which ones, and what the switch's lights showed. If a class is in
the room, ask the shift lead about moving it.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
