---
id: RB-AV-007
title: "No sound from the room speakers"
equipment: [ceiling-speakers, audio-processor]
status: draft
reviewed: 2026-10-29
---

# No sound from the room speakers

A video or the computer's sound plays, but nothing comes out of the
room's ceiling speakers. For a microphone that cannot be heard while
program sound works, follow
[Microphone cannot be heard in the room](rb-av-008-microphone-cannot-be-heard-in-the-room.md).

## Symptoms

- "The video plays but there's no sound", "the speakers aren't working".
- The touch panel's volume shows a level, or shows **Muted**.
- Sound may come from the lectern computer's own small speaker or a
  laptop's, but not from the ceiling.

## Before you start

- **Time:** about 10 minutes.
- **Bring:** a laptop and a short video or sound file to test with.
- **Safety:** turn the room's volume down before you unmute or change a
  source, so sound does not blast out when it returns.
- **Do not:** open the rack or change settings in the audio processor's
  software. The processor's settings are for AV engineering.

## Checks

1. Look at the touch panel or button panel's volume. **Expected:** not
   muted, and above the lowest level. If muted or at the bottom, go to step 1
   of [Fix](#fix).
2. On the lectern computer, open the sound settings and look at the output
   device. **Expected:** the output is the room system (it is usually named
   after the display or the switcher's HDMI output), not the computer's own
   speaker or headphones, and not muted. If not, go to step 2 of
   [Fix](#fix).
3. Play your test file from your laptop through the lectern's HDMI input,
   with the laptop source selected. **Expected:** sound from the ceiling. If
   your laptop is heard but the lectern computer is not, the fault is the
   computer's output: go to step 2 of [Fix](#fix). If neither is heard, go
   to step 3 of [Fix](#fix).

## Fix

1. Unmute on the panel and raise the volume a few steps while the sound
   plays. **Expected:** sound from the ceiling speakers.
2. Set the computer's output device to the room system and raise the
   computer's own volume to about three quarters. **Expected:** sound from
   the ceiling, controlled from the panel.
3. Turn the room's system off from the panel, wait a minute, and turn it on
   again; select the source and play the sound. **Expected:** sound from
   the ceiling. If there is still none from any source, the processor or
   amplifier has failed: escalate.

## Escalate

Escalate if the checks do not find the fault or the fix does not hold: to
AV engineering, through the [escalation matrix](../../procedures/escalation-matrix.md).
Say which sources you tried, and whether the panel showed the volume
changing.

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
