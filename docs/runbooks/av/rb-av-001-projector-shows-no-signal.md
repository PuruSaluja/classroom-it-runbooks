---
id: RB-AV-001
title: "Projector shows no signal"
equipment: [laser-projector, short-throw-projector, presentation-switcher]
status: draft
reviewed: 2026-10-29
---

# Projector shows no signal

The projector is on but shows "No signal", a blank blue or black screen, or
its own logo, whatever source is chosen. If the lectern computer's picture
appears and only a laptop's does not, follow
[Laptop shows no picture through the HDMI or USB-C cable](rb-av-012-laptop-shows-no-picture-through-the-hdmi-or-usb-c.md);
if the projector will not turn on at all, follow
[Projector will not turn on](rb-av-002-projector-will-not-turn-on.md).

## Symptoms

- "The projector is on but nothing comes up", "it says no signal".
- The projector's image shows a "No signal" or "Searching" message, its
  logo, or a plain blue or black screen.
- The touch panel or button panel shows a source as selected.

## Before you start

- **Time:** about 10 minutes.
- **Bring:** a laptop with HDMI and USB-C outputs, and a short known-good
  HDMI cable.
- **Safety:** do not look into the projector's lens. Ceiling projectors are
  out of reach: nothing in this runbook needs a ladder.
- **Do not:** open the projector or the switcher, or change settings in the
  projector's service menu. Those are for AV engineering.

## Checks

1. Look at the touch panel or button panel and see which source is
   selected. **Expected:** the source the instructor is using (the lectern
   computer, or the laptop input). If another source is selected, go to
   step 1 of [Fix](#fix).
2. Look at the lectern computer's own monitor. **Expected:** the desktop is
   on the monitor and the computer is awake. If the monitor is dark, move the
   mouse or press a key; if it stays dark, go to step 2 of [Fix](#fix).
3. Look at the front of the presentation switcher (in the lectern, or in
   the rack behind the lectern door). **Expected:** the light for the
   selected input is lit, and so is the output light. If no input light is
   lit, go to step 3 of [Fix](#fix).
4. Plug your laptop into the lectern's HDMI input with your own cable and
   select the laptop source. **Expected:** your laptop's picture appears. If
   it does, the fault is with the computer's connection: go to step 3 of
   [Fix](#fix). If it does not, the fault is between the switcher and the
   projector: go to step 4 of [Fix](#fix).

## Fix

1. Select the source the instructor needs on the touch panel or button
   panel. **Expected:** the picture appears within about 10 seconds.
2. Wake the lectern computer: press its power button once, briefly, if it
   is asleep or off. **Expected:** the desktop appears on the monitor and,
   a few seconds later, on the screen.
3. At the switcher, check that the cable from the lectern computer is
   seated: unplug it and plug it back in firmly. **Expected:** the input
   light comes on and the picture appears.
4. Turn the projector off from the touch panel or button panel, wait until
   its fan stops (about a minute), and turn it on again. Select the source.
   **Expected:** the projector warms up and shows the picture.
5. If there is still no picture, leave the projector on and escalate.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
AV engineering, through the [escalation matrix](../../procedures/escalation-matrix.md).
Say which source was selected, which lights were lit on the switcher, and
whether your own laptop worked through the lectern input.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
