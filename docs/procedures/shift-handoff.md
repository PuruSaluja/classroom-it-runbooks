# Shift handoff

How one shift hands classroom support to the next, so that no open
ticket, workaround or piece of equipment taken out of a room is lost
between them. The shift lead makes sure it happens; every technician on
the shift writes their part.

## Start of a shift

1. Read the last shift's handoff note in the team's shift log, all of it,
   before taking a call. Ask the technician who wrote it about anything
   unclear while they are still there.
2. Open the team's ticket queue with the shift lead. Every open ticket
   gets an owner on this shift, and every ticket waiting on another team
   is checked against its urgency in the
   [escalation matrix](escalation-matrix.md).
3. Check the kit bag (below) and restock what the note says was used.
4. Visit first the rooms with a workaround in place and a class early in
   the shift: a borrowed speaker or cable may need to be set up again.

## The kit bag

Everything the runbooks ask a technician to bring, kept in one bag so a
call never waits on a trip back to the office:

- a laptop with HDMI, USB-C and wired network ports (or adapters), that
  has shared its screen to a room's wireless receiver before, with a
  short video or sound file on it;
- short known-good HDMI and network cables;
- USB-C to HDMI and Mini DisplayPort to HDMI adapters;
- fresh AA and AAA batteries;
- a USB drive that you know works, with nothing on it you would mind a
  lectern computer reading;
- a microfiber cloth;
- a phone with a speed-test or Wi-Fi analyzer app approved by the network
  team.

Spare wireless microphones, assistive listening receivers and earpiece
covers stay in the AV store; the runbooks that need them say so.

## During a shift

- Update the ticket before you leave the room, as each runbook's Close
  the ticket section says: the room, what you found, what you did, and
  the runbook's identifier.
- When you escalate, say in the ticket who has it now and how urgent it
  is.
- Anything taken out of a room (a faulty wireless microphone) or lent to
  one (a portable speaker, a cable) is recorded in its ticket, with where
  it is now.

## End of a shift: the handoff note

Each technician adds their open work to the shift's note before leaving;
the shift lead reads it through and adds the queue's state. Write it in
the shift log, not in a chat, so the next shift finds it in one place:

```markdown
## Handoff: <date>, <start>-<end>, from <shift lead> to the next shift

### Open tickets
- <ticket>, <room>: <what has been done>; next step: <what>; owner: <role>.

### Workarounds in place
- <room>: <what is set up instead>, until <the fix or a date>.

### Equipment out of rooms or lent to them
- <item>, <from or to room>: now <where>; ticket <ticket>.

### Waiting on other teams
- <ticket>: with <role> since <time>; urgency <Now, Today or Planned>.

### Kit
- Used or missing: <what to restock>.
```

- Every open ticket appears once, under the heading that fits it best.
- A ticket marked Now is handed over by the shift lead in person or by
  phone as well, never only in the note.
- If no shift follows (the last shift of the day), the note is for the
  next morning's shift lead, and anything marked Now stays with the
  current shift lead until AV engineering or another owner has it.
- A note never holds a password, PIN, code or account name, any more than
  a runbook does.
