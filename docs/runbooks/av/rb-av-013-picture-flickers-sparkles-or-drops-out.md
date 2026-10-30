---
id: RB-AV-013
title: "Picture flickers, sparkles or drops out"
equipment: [hdbaset-extender, lectern-inputs, table-inputs]
status: draft
reviewed: 2026-10-29
---

# Picture flickers, sparkles or drops out

The picture on the projector or a display appears, but flickers, shows
sparkles or lines, or goes black for a few seconds and comes back. This is
usually a cable or extender that cannot carry the signal reliably. If there
is no picture at all, follow
[Projector shows no signal](rb-av-001-projector-shows-no-signal.md) or
[Laptop shows no picture through the HDMI or USB-C cable](rb-av-012-laptop-shows-no-picture-through-the-hdmi-or-usb-c.md).

## Symptoms

- "The screen keeps going black", "there are white dots all over my
  slides".
- The picture drops out for a second or two, often when someone moves the
  laptop or its cable.
- It happens with video and moving images more than with still slides.

## Before you start

- **Time:** about 15 minutes.
- **Bring:** a short known-good HDMI cable and a laptop.
- **Safety:** nothing beyond the room's usual care. The HDBaseT extenders
  (the boxes that carry video over network-style cable to the projector)
  are in the rack or the ceiling: do not reach for a ceiling one.
- **Do not:** unplug or swap cables inside the rack or the floor boxes, or
  replace a building cable. Those are for AV engineering.

## Checks

1. Ask whether it happens with every source. **Expected:** it happens with
   one source only. If it happens with every source, the fault is between
   the switcher and the screen: go to step 3 of [Fix](#fix).
2. Move the source's cable gently at the laptop end while watching the
   screen. **Expected:** the picture stays steady. If it drops out when the
   cable moves, go to step 1 of [Fix](#fix).
3. On the laptop, look at the resolution and refresh rate for the room's
   screen. **Expected:** the recommended resolution, at 60 Hz. If higher, go
   to step 2 of [Fix](#fix).
4. Look at the lights on the HDBaseT extender in the rack, if you can see
   them without opening anything. **Expected:** its link and video lights
   steady. If they blink or go out when the picture drops, go to
   [Escalate](#escalate).

## Fix

1. Plug the laptop in with your known-good HDMI cable at the switcher or
   table input, if it has a socket you can reach. **Expected:** the picture
   stays steady. If it does, the room's cable is worn: escalate, and leave
   your cable for the class if that is allowed.
2. Set the laptop's output to the recommended resolution at 60 Hz.
   **Expected:** the picture stays steady.
3. Turn the room's system off from the panel, wait a minute, and turn it on.
   **Expected:** a steady picture from every source. If the dropouts come
   back, escalate.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
AV engineering, through the [escalation matrix](../../procedures/escalation-matrix.md).
Say which sources drop out, how often, and what the extender's lights did.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
